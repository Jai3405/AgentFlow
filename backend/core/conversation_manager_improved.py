import json
import os
from typing import Dict, List, Optional
from models.conversation import ConversationState, Message, MessageRole
from services.intent_classifier import IntentClassifier
from services.entity_extractor import EntityExtractor
from datetime import datetime

# Try to import langchain_openai at module level
try:
    from langchain_openai import OpenAI
    LANGCHAIN_AVAILABLE = True
except (ImportError, AttributeError) as e:
    LANGCHAIN_AVAILABLE = False
    print(f"Warning: langchain_openai not available ({e}). Using enhanced rule-based responses.")

class ConversationManagerImproved:
    def __init__(self):
        self.conversations: Dict[str, ConversationState] = {}
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        
        # Initialize OpenAI if API key is available
        api_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPEN_API_KEY')
        if api_key and LANGCHAIN_AVAILABLE:
            try:
                self.llm = OpenAI(temperature=0.7, openai_api_key=api_key)
                self.llm_enabled = True
                print("✓ OpenAI LLM initialized successfully")
            except Exception as e:
                print(f"Warning: OpenAI LLM initialization failed: {e}")
                self.llm_enabled = False
        else:
            if not api_key:
                print("Warning: No OpenAI API key found. Using enhanced rule-based responses.")
            if not LANGCHAIN_AVAILABLE:
                print("Warning: LangChain not available. Using enhanced rule-based responses.")
            self.llm_enabled = False
    
    async def process_message(self, conversation_id: str, message: str) -> Dict:
        """Process a user message and return response with progressive workflow building"""
        
        # Get or create conversation state
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ConversationState()
        
        state = self.conversations[conversation_id]
        
        # Add user message
        state.add_message(Message(
            role=MessageRole.USER,
            content=message,
            timestamp=datetime.now()
        ))
        
        # Extract intent and entities
        intent = await self.intent_classifier.classify(message)
        entities = await self.entity_extractor.extract(message)
        
        # Update state with new entities
        state.entities.update(entities)
        
        # Set workflow type if not already set
        if not state.workflow_type and intent != "general":
            from models.conversation import WorkflowType
            workflow_type_map = {
                "email_automation": WorkflowType.EMAIL_PROCESSING,
                "data_processing": WorkflowType.DATA_PIPELINE,
                "approval_workflow": WorkflowType.APPROVAL_WORKFLOW,
                "notification_system": WorkflowType.NOTIFICATION_SYSTEM
            }
            state.workflow_type = workflow_type_map.get(intent)
        
        # Calculate progress based on conversation depth and entities
        progress = self._calculate_progress(state, intent)
        
        # Generate response
        response = await self._generate_contextual_response(state, intent, entities, message)
        
        # Generate or update workflow preview based on current context
        workflow_preview = self._generate_or_update_workflow(state, intent, entities, message)
        
        # Add assistant response to conversation
        state.add_message(Message(
            role=MessageRole.ASSISTANT,
            content=response,
            timestamp=datetime.now()
        ))
        
        return {
            "response": response,
            "progress": progress,
            "next_questions": self._generate_smart_questions(state, intent, progress),
            "workflow_preview": workflow_preview
        }
    
    def _calculate_progress(self, state: ConversationState, intent: str) -> float:
        """Calculate progress based on conversation context and entities"""
        base_progress = 0.1  # Starting progress for intent classification
        
        # Progress based on entities found
        entity_weight = 0.15
        entity_progress = len(state.entities) * entity_weight
        
        # Progress based on conversation depth
        user_messages = len(state.get_user_messages())
        conversation_progress = min(user_messages * 0.2, 0.6)  # Max 60% from conversation
        
        total_progress = min(base_progress + entity_progress + conversation_progress, 1.0)
        return round(total_progress, 2)
    
    async def _generate_contextual_response(self, state: ConversationState, intent: str, entities: Dict, message: str) -> str:
        """Generate natural, contextual response based on conversation history"""
        user_messages = state.get_user_messages()
        message_count = len(user_messages)
        current_workflow = state.requirements.get('current_workflow', {})
        
        # Extract specific details mentioned by user
        specific_details = self._extract_specific_details(message, entities)
        
        # First message - natural welcome
        if message_count == 1:
            if intent == "email_automation":
                email_details = f" for {', '.join(entities.get('email_addresses', []))}" if entities.get('email_addresses') else ""
                return f"Got it! Email automation{email_details} - I love helping with that. I'm already setting up the foundation with email monitoring and smart classification. What kind of actions do you want to happen with these emails?"
            elif intent == "data_processing":
                data_types = entities.get('file_types', [])
                data_mention = f" {', '.join(data_types)} files" if data_types else " data"
                return f"Nice! Processing{data_mention} automatically sounds super useful. I've started your workflow with data input and validation steps. Where is this data coming from exactly?"
            elif intent == "approval_workflow":
                return f"Perfect! Approval workflows save so much time and headache. I'm building the basic request handling and review logic. What kinds of things need approval in your setup?"
            elif intent == "notification_system":
                return f"Smart! Good notifications make all the difference. I've got event monitoring and filtering started. What kinds of events do you want people to know about?"
            else:
                return f"Awesome! I'm always excited to help automate repetitive work. Let me start building something based on what you described. Can you tell me a bit more about the specific steps involved?"
        
        # Follow-up messages - acknowledge specifics and build
        else:
            # Acknowledge what they just added
            acknowledgment = self._generate_acknowledgment(message, specific_details, current_workflow)
            
            # Suggest next steps naturally
            if intent == "email_automation":
                suggestions = self._get_email_suggestions(current_workflow, message)
            elif intent == "data_processing":
                suggestions = self._get_data_suggestions(current_workflow, message)
            elif intent == "approval_workflow":
                suggestions = self._get_approval_suggestions(current_workflow, message)
            elif intent == "notification_system":
                suggestions = self._get_notification_suggestions(current_workflow, message)
            else:
                suggestions = "What else should happen in this process?"
            
            return f"{acknowledgment} {suggestions}"
    
    def _extract_specific_details(self, message: str, entities: Dict) -> Dict:
        """Extract specific details mentioned by the user"""
        details = {}
        
        # Email addresses
        if entities.get('email_addresses'):
            details['emails'] = entities['email_addresses']
        
        # Team mentions
        if entities.get('team_mentions'):
            details['teams'] = entities['team_mentions']
        
        # Time expressions
        if entities.get('time_expressions'):
            details['timing'] = entities['time_expressions']
        
        # Urgency
        if entities.get('urgency_indicators'):
            details['urgency'] = entities['urgency_indicators']
        
        # File types
        if entities.get('file_types'):
            details['files'] = entities['file_types']
        
        # Look for specific systems/tools mentioned
        message_lower = message.lower()
        if 'slack' in message_lower:
            details['slack'] = True
        if 'teams' in message_lower and 'microsoft' in message_lower:
            details['teams'] = True
        if 'gmail' in message_lower:
            details['gmail'] = True
        if 'outlook' in message_lower:
            details['outlook'] = True
        if any(word in message_lower for word in ['crm', 'salesforce', 'hubspot']):
            details['crm'] = True
        
        return details
    
    def _generate_acknowledgment(self, message: str, details: Dict, workflow: Dict) -> str:
        """Generate natural acknowledgment of what user just said"""
        acknowledgments = [
            "Nice!",
            "Perfect!",
            "Great addition!",
            "I love that detail!",
            "Exactly!",
            "That makes sense!",
            "Smart thinking!",
            "Good call!"
        ]
        
        import random
        base_ack = random.choice(acknowledgments)
        
        # Add specific acknowledgments
        if details.get('emails'):
            return f"{base_ack} I've updated the workflow to monitor {', '.join(details['emails'])}."
        elif details.get('slack'):
            return f"{base_ack} Added Slack integration to your workflow."
        elif details.get('teams'):
            return f"{base_ack} I see you want to route things to different teams - added that routing logic."
        elif 'urgent' in message.lower() or 'priority' in message.lower():
            return f"{base_ack} Priority handling is crucial - I've added that to your workflow."
        elif 'automatic' in message.lower() or 'auto' in message.lower():
            return f"{base_ack} Automation is where the magic happens - added that capability."
        else:
            return f"{base_ack} I've updated your workflow with that information."
    
    def _get_email_suggestions(self, workflow: Dict, message: str) -> str:
        """Get natural suggestions for email workflows"""
        suggestions = [
            "Should I add automatic responses for common questions?",
            "Want to set up any escalation rules for urgent emails?", 
            "How about adding templates for different types of responses?",
            "Should certain types of emails get flagged for human review?",
            "Want to add any forwarding rules to other team members?"
        ]
        
        # Filter out suggestions for things already added
        steps = workflow.get('steps', [])
        step_ids = [s.get('id', '') for s in steps]
        
        if 'auto_response' in step_ids:
            suggestions = [s for s in suggestions if 'automatic responses' not in s]
        if 'urgent_alert' in step_ids:
            suggestions = [s for s in suggestions if 'escalation' not in s]
        
        import random
        return random.choice(suggestions)
    
    def _get_data_suggestions(self, workflow: Dict, message: str) -> str:
        """Get natural suggestions for data workflows"""
        suggestions = [
            "Where should the processed data end up?",
            "Want to add any data validation rules?",
            "Should I include error handling for bad data?",
            "How about adding data backup or archiving?",
            "Want to set up any alerts when processing completes?"
        ]
        
        import random
        return random.choice(suggestions)
    
    def _get_approval_suggestions(self, workflow: Dict, message: str) -> str:
        """Get natural suggestions for approval workflows"""
        suggestions = [
            "What happens if someone doesn't respond within 24 hours?",
            "Should there be different approval limits for different people?",
            "Want to add email reminders for pending approvals?",
            "How about escalation to managers for large amounts?",
            "Should approved items automatically get processed?"
        ]
        
        import random
        return random.choice(suggestions)
    
    def _get_notification_suggestions(self, workflow: Dict, message: str) -> str:
        """Get natural suggestions for notification workflows"""
        suggestions = [
            "Should people be able to acknowledge notifications?",
            "Want to add quiet hours when notifications are paused?",
            "How about different notification priorities?",
            "Should I track who has read each notification?",
            "Want to add escalation if notifications aren't acknowledged?"
        ]
        
        import random
        return random.choice(suggestions)
    
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
            # Customize descriptions based on user details
            email_sources = entities.get('email_addresses', [])
            monitor_desc = f"Monitor incoming emails from {', '.join(email_sources)}" if email_sources else "Monitor incoming emails from your specified sources"
            
            return {
                "steps": [
                    {
                        "id": "email_monitor",
                        "type": "email",
                        "name": "Email Monitor",
                        "description": monitor_desc
                    },
                    {
                        "id": "email_classify",
                        "type": "process",
                        "name": "Smart Classifier",
                        "description": "Analyze email content for categories, urgency, and routing decisions"
                    }
                ],
                "metadata": {
                    "intent": intent,
                    "created": True,
                    "last_modified": "Initial creation",
                    "user_details": entities
                }
            }
        elif intent == "data_processing":
            file_types = entities.get('file_types', [])
            data_desc = f"Collect {', '.join(file_types)} data from your sources" if file_types else "Collect data from various sources"
            
            return {
                "steps": [
                    {
                        "id": "data_input",
                        "type": "data", 
                        "name": "Data Input",
                        "description": data_desc
                    },
                    {
                        "id": "data_validate",
                        "type": "process",
                        "name": "Data Validation", 
                        "description": "Validate and clean incoming data for quality and consistency"
                    }
                ],
                "metadata": {
                    "intent": intent,
                    "created": True,
                    "last_modified": "Initial creation",
                    "user_details": entities
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
        """Update email workflow based on user input with specific details"""
        step_ids = [step["id"] for step in steps]
        
        # Add routing if mentioned teams, managers, or routing
        if message_count >= 2 and "email_route" not in step_ids and any(word in message for word in ["route", "send", "team", "manager", "forward"]):
            teams = entities.get('team_mentions', [])
            if teams:
                route_desc = f"Route emails to {', '.join(teams)} teams based on content and priority"
            elif "manager" in message:
                route_desc = "Route high-priority emails directly to managers"
            else:
                route_desc = "Route emails to appropriate teams based on content and priority"
            
            steps.append({
                "id": "email_route",
                "type": "decision",
                "name": "Smart Router",
                "description": route_desc
            })
        
        # Add priority alerts if urgent/critical/priority mentioned
        if "urgent_alert" not in step_ids and (entities.get('urgency_indicators') or any(word in message for word in ["urgent", "critical", "priority", "alert", "immediate"])):
            urgency_words = entities.get('urgency_indicators', [])
            if urgency_words:
                alert_desc = f"Send immediate alerts for {', '.join(urgency_words)} emails"
            elif "manager" in message:
                alert_desc = "Send immediate alerts to managers for urgent emails"
            else:
                alert_desc = "Send immediate notifications for high-priority emails"
            
            steps.append({
                "id": "urgent_alert", 
                "type": "notification",
                "name": "Priority Alert",
                "description": alert_desc
            })
        
        # Add specific integrations mentioned
        if "slack" in message and "slack_notify" not in step_ids:
            # Look for specific Slack details
            if "channel" in message:
                slack_desc = "Send notifications to specific Slack channels"
            elif "critical" in message or "urgent" in message:
                slack_desc = "Send urgent notifications to Slack for critical issues"
            else:
                slack_desc = "Send notifications to Slack channels"
            
            steps.append({
                "id": "slack_notify",
                "type": "notification", 
                "name": "Slack Integration",
                "description": slack_desc
            })
        
        # Add Teams integration if mentioned
        if any(word in message for word in ["teams", "microsoft teams"]) and "teams_notify" not in step_ids:
            steps.append({
                "id": "teams_notify",
                "type": "notification", 
                "name": "Microsoft Teams",
                "description": "Send notifications to Microsoft Teams channels"
            })
        
        # Add auto-response if mentioned
        if any(word in message for word in ["respond", "reply", "auto", "automatic"]) and "auto_response" not in step_ids:
            if "common" in message or "question" in message:
                response_desc = "Send automatic responses to common questions"
            else:
                response_desc = "Send automatic acknowledgment responses"
            
            steps.append({
                "id": "auto_response",
                "type": "action",
                "name": "Auto Response", 
                "description": response_desc
            })
            
        # Add email templates/rules if mentioned
        if any(word in message for word in ["template", "rule", "common", "question"]) and "email_templates" not in step_ids:
            steps.append({
                "id": "email_templates",
                "type": "process",
                "name": "Smart Templates",
                "description": "Use AI to generate responses from predefined templates"
            })
        
        # Add CRM integration if mentioned
        if any(word in message for word in ["crm", "salesforce", "hubspot"]) and "crm_sync" not in step_ids:
            crm_type = "CRM"
            if "salesforce" in message:
                crm_type = "Salesforce"
            elif "hubspot" in message:
                crm_type = "HubSpot"
            
            steps.append({
                "id": "crm_sync",
                "type": "action",
                "name": f"{crm_type} Integration",
                "description": f"Sync email interactions with {crm_type}"
            })
            
        return steps
    
    def _update_data_workflow(self, steps: List[Dict], entities: Dict, message: str, message_count: int) -> List[Dict]:
        """Update data workflow based on user input with specific details"""
        step_ids = [step["id"] for step in steps]
        
        # Add transformation step if processing/transform mentioned
        if message_count >= 2 and "data_transform" not in step_ids and any(word in message for word in ["transform", "process", "clean", "format", "convert"]):
            if "clean" in message:
                transform_desc = "Clean and standardize data for consistency"
            elif "validate" in message:
                transform_desc = "Validate data against business rules and requirements"
            elif "format" in message:
                transform_desc = "Format data for downstream systems"
            else:
                transform_desc = "Apply transformations and business rules"
            
            steps.append({
                "id": "data_transform",
                "type": "process",
                "name": "Data Transform",
                "description": transform_desc
            })
        
        # Add output/destination step if mentioned
        if "data_output" not in step_ids and any(word in message for word in ["send", "export", "save", "output", "crm", "database", "system"]):
            if "crm" in message:
                output_desc = "Send processed data to CRM system"
            elif "database" in message:
                output_desc = "Store processed data in database"
            elif "export" in message:
                output_desc = "Export processed data to files"
            else:
                output_desc = "Send processed data to destination systems"
            
            steps.append({
                "id": "data_output",
                "type": "action", 
                "name": "Data Output",
                "description": output_desc
            })
        
        # Add error handling if mentioned
        if any(word in message for word in ["error", "fail", "exception", "handle"]) and "error_handler" not in step_ids:
            steps.append({
                "id": "error_handler",
                "type": "decision",
                "name": "Error Handler",
                "description": "Handle data processing errors and send alerts"
            })
        
        # Add data backup if mentioned
        if any(word in message for word in ["backup", "archive", "store"]) and "data_backup" not in step_ids:
            steps.append({
                "id": "data_backup",
                "type": "action",
                "name": "Data Backup",
                "description": "Backup processed data for recovery purposes"
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
    
    
    def _generate_smart_questions(self, state: ConversationState, intent: str, progress: float) -> List[str]:
        """Generate contextual questions that don't repeat"""
        user_messages = state.get_user_messages()
        message_count = len(user_messages)
        
        if message_count <= 1:
            # First follow-up questions
            questions = {
                "email_automation": ["What email addresses should I monitor?", "How should urgent emails be handled?"],
                "data_processing": ["What's your data source?", "What format is your data in?"],
                "approval_workflow": ["What dollar amount requires approval?", "Who are the approvers?"],
                "notification_system": ["Which communication channels should I use?", "How quickly should notifications be sent?"]
            }
        elif message_count == 2:
            # Second round questions
            questions = {
                "email_automation": ["Should I create automatic responses?", "Which team members should get copies?"],
                "data_processing": ["Where should processed data be sent?", "How often should this run?"],
                "approval_workflow": ["What happens if no response in 24 hours?", "Should there be escalation rules?"],
                "notification_system": ["Should there be different notification priorities?", "Any quiet hours?"]
            }
        else:
            # Later questions - refinement
            questions = {
                "email_automation": ["Want to add any custom email filters?", "Should I log all email actions?"],
                "data_processing": ["Need any error handling steps?", "Want to schedule regular runs?"],
                "approval_workflow": ["Should managers auto-approve small amounts?", "Want email reminders for pending approvals?"],
                "notification_system": ["Need acknowledgment tracking?", "Want notification analytics?"]
            }
        
        return questions.get(intent, ["What else should I include in your workflow?", "Any specific requirements I should know about?"])
    
    async def get_conversation(self, conversation_id: str):
        """Get conversation by ID"""
        return self.conversations.get(conversation_id)