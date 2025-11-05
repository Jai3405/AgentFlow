import json
import os
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai
from sqlalchemy.orm import Session
from models.conversation import ConversationState, Message, MessageRole
from services.intent_classifier import IntentClassifier
from services.entity_extractor import EntityExtractor
from services.entity_extractor_gemini import EntityExtractorGemini
from services.confidence_scorer import ConfidenceScorer
from services.workflow_validator import WorkflowValidator
from services.conversation_metrics import ConversationMetrics
from database.repository import ConversationRepository
from database.base import SessionLocal
from core.conversation_graph import ConversationGraph
from datetime import datetime

class ConversationManagerGemini:
    def __init__(self, db: Optional[Session] = None, use_langgraph: bool = True, use_enhanced_services: bool = True):
        # Database session - can be injected or created
        self.db = db
        self.use_db = True  # Flag to enable/disable database persistence
        self.use_langgraph = use_langgraph  # Flag to use LangGraph state machine
        self.use_enhanced_services = use_enhanced_services  # Flag to use Phase 2 enhanced services

        # In-memory cache for backwards compatibility during transition
        self.conversations: Dict[str, ConversationState] = {}

        # Basic services (Phase 1)
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()

        # Enhanced services (Phase 2)
        if self.use_enhanced_services:
            self.entity_extractor_gemini = EntityExtractorGemini()
            self.confidence_scorer = ConfidenceScorer()
            self.workflow_validator = WorkflowValidator()
            self.conversation_metrics = ConversationMetrics()

        # Initialize LangGraph conversation state machine
        if self.use_langgraph:
            self.conversation_graph = ConversationGraph(use_enhanced_services=self.use_enhanced_services)

        # Initialize Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.llm_enabled = True
        else:
            print("Warning: GEMINI_API_KEY not found. Using rule-based responses.")
            self.llm_enabled = False

    def _get_db_session(self) -> Session:
        """Get database session (create if not injected)"""
        if self.db:
            return self.db
        return SessionLocal()

    def _close_db_session(self, db: Session):
        """Close database session if we created it"""
        if not self.db:  # Only close if we created it
            db.close()
    
    async def process_message(self, conversation_id: str, message: str) -> Dict:
        """Process a user message and return response using Gemini"""

        # Route to LangGraph if enabled
        if self.use_langgraph:
            return await self._process_with_langgraph(conversation_id, message)

        # Otherwise use legacy flow
        return await self._process_legacy(conversation_id, message)

    async def _process_with_langgraph(self, conversation_id: str, message: str) -> Dict:
        """Process message using LangGraph state machine"""
        db = self._get_db_session()
        repo = ConversationRepository(db)

        try:
            # Get or create conversation state
            if self.use_db:
                state = repo.get_conversation(conversation_id)
                if not state:
                    state = ConversationState(conversation_id=conversation_id)
                    repo.save_conversation(state)
            else:
                if conversation_id not in self.conversations:
                    self.conversations[conversation_id] = ConversationState()
                state = self.conversations[conversation_id]

            # Add user message
            user_message = Message(
                role=MessageRole.USER,
                content=message,
                timestamp=datetime.now()
            )
            state.add_message(user_message)

            if self.use_db:
                repo.add_message(conversation_id, user_message)

            # Process through LangGraph
            result = await self.conversation_graph.process_message(conversation_id, message, state)

            # Update state with results
            state.progress = result["progress"]
            state.confidence_score = result["confidence_score"]
            state.entities.update(result.get("entities", {}))

            # Add assistant response
            assistant_message = Message(
                role=MessageRole.ASSISTANT,
                content=result["response"],
                timestamp=datetime.now()
            )
            state.add_message(assistant_message)

            if self.use_db:
                repo.add_message(conversation_id, assistant_message)

            # Save workflow if generated
            workflow_preview = result.get("workflow_preview")
            if workflow_preview and self.use_db:
                repo.save_workflow(conversation_id, workflow_preview)

            # Enhanced Phase 2 features
            enhanced_data = {}
            if self.use_enhanced_services:
                # Get intent from result or classify
                intent = result.get("intent", "general")

                # Calculate detailed confidence breakdown
                confidence_breakdown = self.confidence_scorer.calculate_overall_confidence(
                    state, intent, state.entities, workflow_preview
                )
                enhanced_data['confidence_breakdown'] = confidence_breakdown
                enhanced_data['confidence_recommendations'] = self.confidence_scorer.get_recommendations(
                    confidence_breakdown, intent, state.entities
                )

                # Validate workflow if present
                if workflow_preview:
                    is_valid, errors, warnings = self.workflow_validator.validate_workflow(
                        workflow_preview, intent
                    )
                    completeness = self.workflow_validator.check_completeness(workflow_preview, intent)

                    enhanced_data['workflow_validation'] = {
                        'is_valid': is_valid,
                        'errors': errors,
                        'warnings': warnings,
                        'completeness': completeness,
                        'suggestions': self.workflow_validator.suggest_improvements(workflow_preview, intent)
                    }

                # Calculate conversation metrics
                metrics = self.conversation_metrics.analyze_conversation(state)
                enhanced_data['conversation_metrics'] = {
                    'quality_score': metrics.get('quality_score'),
                    'quality_level': metrics.get('quality_level'),
                    'message_count': metrics.get('message_count'),
                    'duration_minutes': metrics.get('duration_minutes'),
                    'information_density': metrics.get('information_density'),
                    'insights': self.conversation_metrics.get_insights(metrics),
                    'recommendations': self.conversation_metrics.get_recommendations(metrics)
                }

            # Update conversation state
            if self.use_db:
                repo.save_conversation(state)

            # Build response
            response_data = {
                "response": result["response"],
                "progress": result["progress"],
                "next_questions": result.get("next_questions", []),
                "workflow_preview": workflow_preview,
                "confidence_score": result["confidence_score"],
                "stage": result.get("stage")
            }

            # Add enhanced data if available
            if enhanced_data:
                response_data.update(enhanced_data)

            return response_data

        finally:
            self._close_db_session(db)

    async def _process_legacy(self, conversation_id: str, message: str) -> Dict:
        """Legacy processing without LangGraph"""
        db = self._get_db_session()
        repo = ConversationRepository(db)

        try:
            # Get or create conversation state from database
            if self.use_db:
                state = repo.get_conversation(conversation_id)
                if not state:
                    state = ConversationState(conversation_id=conversation_id)
                    repo.save_conversation(state)
            else:
                # Fallback to in-memory
                if conversation_id not in self.conversations:
                    self.conversations[conversation_id] = ConversationState()
                state = self.conversations[conversation_id]

            # Add user message
            user_message = Message(
                role=MessageRole.USER,
                content=message,
                timestamp=datetime.now()
            )
            state.add_message(user_message)

            # Save message to database
            if self.use_db:
                repo.add_message(conversation_id, user_message)

            # Extract intent and entities
            intent = await self.intent_classifier.classify(message)
            entities = await self.entity_extractor.extract(message)

            # Update state
            state.entities.update(entities)

            # Calculate progress
            progress = self._calculate_progress(state, intent)
            state.progress = progress

            # Generate response
            if self.llm_enabled:
                response = await self._generate_llm_response(state, intent, entities)
            else:
                response = self._generate_fallback_response(state, intent, entities, message)

            # Add assistant response to conversation
            assistant_message = Message(
                role=MessageRole.ASSISTANT,
                content=response,
                timestamp=datetime.now()
            )
            state.add_message(assistant_message)

            # Save assistant message to database
            if self.use_db:
                repo.add_message(conversation_id, assistant_message)

            # Generate or update workflow
            workflow_preview = self._generate_or_update_workflow(state, intent, entities, message)

            # Save workflow to database
            if self.use_db and workflow_preview:
                repo.save_workflow(conversation_id, workflow_preview)

            # Update conversation state in database
            if self.use_db:
                repo.save_conversation(state)

            return {
                "response": response,
                "progress": progress,
                "next_questions": self._generate_questions(intent, progress),
                "workflow_preview": workflow_preview
            }

        finally:
            self._close_db_session(db)
    
    async def _generate_llm_response(self, state: ConversationState, intent: str, entities: Dict) -> str:
        """Generate response using Gemini API"""
        try:
            # Build context from conversation history
            conversation_context = self._build_conversation_context(state)
            
            # Create prompt for Gemini
            prompt = self._create_workflow_prompt(conversation_context, intent, entities)
            
            # Generate response
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            print(f"Error generating LLM response: {e}")
            return self._generate_fallback_response(intent, entities)
    
    def _build_conversation_context(self, state: ConversationState) -> str:
        """Build conversation context for the prompt"""
        messages = state.get_latest_context(5)  # Last 5 messages for context
        context = []
        
        for msg in messages:
            role = "User" if msg.role == MessageRole.USER else "Assistant"
            context.append(f"{role}: {msg.content}")
        
        return "\n".join(context)
    
    def _create_workflow_prompt(self, context: str, intent: str, entities: Dict) -> str:
        """Create a structured prompt for Gemini"""
        entities_str = json.dumps(entities, indent=2) if entities else "None detected"
        
        prompt = f"""You are AgentFlow, an AI assistant that helps users build automation workflows through conversation.

Your role:
- Help users describe their automation needs
- Ask clarifying questions to understand their requirements
- Guide them toward building practical workflows
- Be conversational, helpful, and focused on workflow automation

Current conversation context:
{context}

Detected intent: {intent}
Extracted entities: {entities_str}

Based on this context, provide a helpful response that:
1. Acknowledges what the user wants to automate
2. Shows understanding of the details they've provided
3. Asks 1-2 specific questions to gather more information needed for their workflow
4. Maintains a conversational, encouraging tone

Keep your response concise (2-3 sentences) and focused on moving toward a concrete workflow solution.

Response:"""

        return prompt
    
    def _generate_fallback_response(self, state: ConversationState, intent: str, entities: Dict, message: str) -> str:
        """Generate natural fallback response when LLM is not available"""
        user_messages = state.get_user_messages()
        message_count = len(user_messages)
        
        import random
        
        # First message - natural welcome
        if message_count == 1:
            if intent == "email_automation":
                email_details = f" for {', '.join(entities.get('email_addresses', []))}" if entities.get('email_addresses') else ""
                return f"Awesome! Email automation{email_details} - that's going to save you tons of time. I'm setting up email monitoring and smart classification right now. What should happen with these emails once they come in?"
            elif intent == "data_processing":
                data_types = entities.get('file_types', [])
                data_mention = f" {', '.join(data_types)} files" if data_types else " data"
                return f"Perfect! Automating{data_mention} processing is such a game-changer. I've got your workflow started with data input and validation. Where exactly is this data coming from?"
            elif intent == "approval_workflow":
                return f"Smart choice! Approval workflows eliminate so much back-and-forth. I'm building the request handling and review process. What kinds of requests need approval in your world?"
            elif intent == "notification_system":
                return f"Yes! Good notifications are everything. I've started with event monitoring and smart filtering. What events do you want people to hear about?"
            else:
                return f"I love building automation! There's nothing better than eliminating repetitive work. Tell me more about what you want to automate and I'll start crafting your workflow."
        
        # Follow-up messages
        else:
            acknowledgments = ["Nice!", "Perfect!", "Great thinking!", "Love it!", "Smart move!", "Exactly right!"]
            ack = random.choice(acknowledgments)
            
            if "slack" in message.lower():
                return f"{ack} Slack integration added to your workflow. Should I set up any specific notification rules or just keep it simple?"
            elif any(word in message.lower() for word in ["urgent", "priority", "critical"]):
                return f"{ack} Priority handling is crucial - I've built that into your workflow. What else should the system watch out for?"
            elif any(word in message.lower() for word in ["manager", "team", "route"]):
                return f"{ack} Smart routing logic added! This is going to make everyone's life easier. Any other routing rules I should know about?"
            elif any(word in message.lower() for word in ["automatic", "auto", "respond"]):
                return f"{ack} Automation features are the best part! I've added that capability. What other repetitive tasks can we eliminate?"
            else:
                return f"{ack} I've updated your workflow with those details. This is looking really solid! What other scenarios should we handle?"
    
    def _calculate_progress(self, state: ConversationState, intent: str) -> float:
        """Calculate progress based on conversation depth and entities"""
        base_progress = 0.1  # Starting progress for intent classification
        
        # Progress based on entities found
        entity_weight = 0.15
        entity_progress = len(state.entities) * entity_weight
        
        # Progress based on conversation depth
        user_messages = len(state.get_user_messages())
        conversation_progress = min(user_messages * 0.2, 0.6)  # Max 60% from conversation
        
        total_progress = min(base_progress + entity_progress + conversation_progress, 1.0)
        return round(total_progress, 2)
    
    def _generate_or_update_workflow(self, state: ConversationState, intent: str, entities: Dict, message: str) -> Optional[Dict]:
        """Generate new workflow or update existing workflow based on conversation context"""
        user_messages = state.get_user_messages()
        message_count = len(user_messages)
        
        if message_count == 0:
            return None
        
        # Check if we have an existing workflow in state requirements
        existing_workflow = state.requirements.get('current_workflow')
        
        if existing_workflow is None:
            # First message - create initial workflow
            workflow = self._create_initial_workflow(intent, entities)
            state.requirements['current_workflow'] = workflow
            return workflow
        else:
            # Subsequent messages - modify existing workflow
            updated_workflow = self._update_existing_workflow(existing_workflow, intent, entities, message, message_count)
            state.requirements['current_workflow'] = updated_workflow
            return updated_workflow
    
    def _create_initial_workflow(self, intent: str, entities: Dict) -> Dict:
        """Create the initial workflow for the first message"""
        if intent == "email_automation":
            return {
                "steps": [
                    {
                        "id": "email_monitor",
                        "type": "email",
                        "name": "Email Monitor",
                        "description": "Monitor incoming emails from specified sources"
                    },
                    {
                        "id": "email_classify",
                        "type": "process",
                        "name": "Smart Classifier",
                        "description": "Analyze email content for categories and priority"
                    }
                ],
                "metadata": {
                    "intent": intent,
                    "created": True,
                    "last_modified": "Initial creation"
                }
            }
        elif intent == "data_processing":
            return {
                "steps": [
                    {
                        "id": "data_input",
                        "type": "data", 
                        "name": "Data Input",
                        "description": "Collect data from various sources"
                    },
                    {
                        "id": "data_validate",
                        "type": "process",
                        "name": "Data Validation", 
                        "description": "Validate and clean incoming data"
                    }
                ],
                "metadata": {
                    "intent": intent,
                    "created": True,
                    "last_modified": "Initial creation"
                }
            }
        elif intent == "approval_workflow":
            return {
                "steps": [
                    {
                        "id": "request_submit",
                        "type": "action",
                        "name": "Request Submission",
                        "description": "Receive and validate approval requests"
                    },
                    {
                        "id": "auto_review",
                        "type": "decision", 
                        "name": "Auto Review",
                        "description": "Check against automatic approval rules"
                    }
                ],
                "metadata": {
                    "intent": intent,
                    "created": True,
                    "last_modified": "Initial creation"
                }
            }
        elif intent == "notification_system":
            return {
                "steps": [
                    {
                        "id": "event_monitor",
                        "type": "process",
                        "name": "Event Monitor", 
                        "description": "Monitor for trigger events and conditions"
                    },
                    {
                        "id": "filter_events",
                        "type": "decision",
                        "name": "Event Filter",
                        "description": "Filter events based on notification rules"
                    }
                ],
                "metadata": {
                    "intent": intent,
                    "created": True,
                    "last_modified": "Initial creation"
                }
            }
        else:
            return {
                "steps": [
                    {
                        "id": "trigger",
                        "type": "process",
                        "name": "Workflow Trigger",
                        "description": "Monitor for events that start the workflow"
                    }
                ],
                "metadata": {
                    "intent": "general",
                    "created": True,
                    "last_modified": "Initial creation"
                }
            }
    
    def _update_existing_workflow(self, workflow: Dict, intent: str, entities: Dict, message: str, message_count: int) -> Dict:
        """Update existing workflow based on new user input"""
        steps = workflow.get("steps", [])
        message_lower = message.lower()
        
        # Determine what to add/modify based on message content and entities
        workflow_intent = workflow.get("metadata", {}).get("intent", intent)
        
        if workflow_intent == "email_automation":
            steps = self._update_email_workflow(steps, entities, message_lower, message_count)
        elif workflow_intent == "data_processing":
            steps = self._update_data_workflow(steps, entities, message_lower, message_count)
        elif workflow_intent == "approval_workflow":
            steps = self._update_approval_workflow(steps, entities, message_lower, message_count)
        elif workflow_intent == "notification_system":
            steps = self._update_notification_workflow(steps, entities, message_lower, message_count)
        else:
            steps = self._update_generic_workflow(steps, entities, message_lower, message_count)
        
        # Update workflow metadata
        workflow["steps"] = steps
        workflow["metadata"]["last_modified"] = f"Message {message_count}: {message[:50]}..."
        
        return workflow
    
    def _update_email_workflow(self, steps: List[Dict], entities: Dict, message: str, message_count: int) -> List[Dict]:
        """Update email workflow based on user input"""
        step_ids = [step["id"] for step in steps]
        
        # Add routing if mentioned teams, managers, or routing
        if message_count >= 2 and "email_route" not in step_ids and any(word in message for word in ["route", "send", "team", "manager", "forward"]):
            steps.append({
                "id": "email_route",
                "type": "decision",
                "name": "Smart Router",
                "description": f"Route emails to appropriate teams based on content and priority"
            })
        
        # Add priority alerts if urgent/critical/priority mentioned
        if "urgent_alert" not in step_ids and (entities.get('urgency_indicators') or any(word in message for word in ["urgent", "critical", "priority", "alert", "immediate"])):
            steps.append({
                "id": "urgent_alert", 
                "type": "notification",
                "name": "Priority Alert",
                "description": "Send immediate notifications for high-priority emails"
            })
        
        # Add specific integrations mentioned
        if "slack" in message and "slack_notify" not in step_ids:
            steps.append({
                "id": "slack_notify",
                "type": "notification", 
                "name": "Slack Integration",
                "description": "Send notifications to Slack channels"
            })
        
        # Add auto-response if mentioned
        if any(word in message for word in ["respond", "reply", "auto", "automatic"]) and "auto_response" not in step_ids:
            steps.append({
                "id": "auto_response",
                "type": "action",
                "name": "Auto Response", 
                "description": "Send automatic acknowledgment responses"
            })
            
        # Add email templates/rules if mentioned
        if any(word in message for word in ["template", "rule", "common", "question"]) and "email_templates" not in step_ids:
            steps.append({
                "id": "email_templates",
                "type": "process",
                "name": "Smart Templates",
                "description": "Use AI to generate responses from templates"
            })
            
        return steps
    
    def _update_data_workflow(self, steps: List[Dict], entities: Dict, message: str, message_count: int) -> List[Dict]:
        """Update data workflow based on user input"""
        step_ids = [step["id"] for step in steps]
        
        # Add transformation step if processing/transform mentioned
        if message_count >= 2 and "data_transform" not in step_ids and any(word in message for word in ["transform", "process", "clean", "format", "convert"]):
            steps.append({
                "id": "data_transform",
                "type": "process",
                "name": "Data Transform",
                "description": "Apply transformations and business rules"
            })
        
        # Add output/destination step if mentioned
        if "data_output" not in step_ids and any(word in message for word in ["send", "export", "save", "output", "crm", "database", "system"]):
            steps.append({
                "id": "data_output",
                "type": "action", 
                "name": "Data Output",
                "description": f"Send processed data to destination systems"
            })
        
        # Add error handling if mentioned
        if any(word in message for word in ["error", "fail", "exception", "handle"]) and "error_handler" not in step_ids:
            steps.append({
                "id": "error_handler",
                "type": "decision",
                "name": "Error Handler",
                "description": "Handle data processing errors and exceptions"
            })
            
        return steps
    
    def _update_approval_workflow(self, steps: List[Dict], entities: Dict, message: str, message_count: int) -> List[Dict]:
        """Update approval workflow based on user input"""
        step_ids = [step["id"] for step in steps]
        
        # Add approver assignment if mentioned
        if message_count >= 2 and "assign_approver" not in step_ids and any(word in message for word in ["approver", "manager", "assign", "route"]):
            steps.append({
                "id": "assign_approver",
                "type": "process",
                "name": "Assign Approver",
                "description": "Route to appropriate approver based on rules"
            })
        
        # Add escalation if mentioned
        if any(word in message for word in ["escalate", "escalation", "timeout", "24", "hours", "reminder"]) and "escalation" not in step_ids:
            steps.append({
                "id": "escalation",
                "type": "decision", 
                "name": "Escalation Logic",
                "description": "Escalate requests that exceed time limits"
            })
        
        # Add notification if mentioned
        if "notify_decision" not in step_ids and any(word in message for word in ["notify", "notification", "email", "inform"]):
            steps.append({
                "id": "notify_decision",
                "type": "notification",
                "name": "Decision Notification", 
                "description": "Notify all parties of approval decision"
            })
            
        return steps
    
    def _update_notification_workflow(self, steps: List[Dict], entities: Dict, message: str, message_count: int) -> List[Dict]:
        """Update notification workflow based on user input"""
        step_ids = [step["id"] for step in steps]
        
        # Add message formatting if mentioned
        if message_count >= 2 and "format_message" not in step_ids and any(word in message for word in ["format", "message", "customize", "personalize"]):
            steps.append({
                "id": "format_message",
                "type": "process",
                "name": "Format Message",
                "description": "Create personalized notification messages"
            })
        
        # Add delivery step
        if "send_notification" not in step_ids and any(word in message for word in ["send", "deliver", "email", "sms", "slack", "push"]):
            steps.append({
                "id": "send_notification",
                "type": "notification",
                "name": "Send Notification",
                "description": "Deliver notifications via chosen channels"
            })
        
        # Add acknowledgment tracking if mentioned  
        if any(word in message for word in ["track", "acknowledge", "confirm", "read"]) and "track_ack" not in step_ids:
            steps.append({
                "id": "track_ack",
                "type": "process",
                "name": "Track Acknowledgments",
                "description": "Track notification delivery and acknowledgments"
            })
            
        return steps
    
    def _update_generic_workflow(self, steps: List[Dict], entities: Dict, message: str, message_count: int) -> List[Dict]:
        """Update generic workflow based on user input"""
        step_ids = [step["id"] for step in steps]
        
        # Add processing step
        if message_count >= 2 and "process" not in step_ids:
            steps.append({
                "id": "process",
                "type": "process", 
                "name": "Process Data",
                "description": "Execute main workflow logic"
            })
        
        # Add action step
        if message_count >= 3 and "action" not in step_ids:
            steps.append({
                "id": "action",
                "type": "action",
                "name": "Take Action", 
                "description": "Complete the workflow with appropriate actions"
            })
            
        return steps
    
    async def get_conversation(self, conversation_id: str):
        """Get conversation by ID"""
        if self.use_db:
            db = self._get_db_session()
            try:
                repo = ConversationRepository(db)
                return repo.get_conversation(conversation_id)
            finally:
                self._close_db_session(db)
        else:
            return self.conversations.get(conversation_id)
    
    
    def _generate_questions(self, intent: str, progress: float) -> List[str]:
        """Generate follow-up questions based on intent and progress"""
        base_questions = {
            "email_automation": [
                "What email address should I monitor?",
                "How do you want to categorize the emails?",
                "Which team members should receive different types of emails?",
                "What actions should be taken for high-priority emails?"
            ],
            "data_processing": [
                "What format is your data in (CSV, JSON, database)?",
                "What processing steps do you need?",
                "Where should the processed data be sent?",
                "How often should this process run?"
            ],
            "approval_workflow": [
                "What types of requests need approval?",
                "Who are the approvers in your organization?",
                "What happens if a request is rejected?",
                "Are there different approval levels based on amount or type?"
            ],
            "notification_system": [
                "What events should trigger notifications?",
                "Which communication channels should be used (email, Slack, SMS)?",
                "Who should receive which types of notifications?",
                "Should there be escalation for critical alerts?"
            ]
        }
        
        questions = base_questions.get(intent, ["What would you like to automate?"])
        
        # Return relevant questions based on progress
        if progress < 0.3:
            return questions[:2]
        elif progress < 0.7:
            return questions[1:3]
        else:
            return questions[2:4]
    
