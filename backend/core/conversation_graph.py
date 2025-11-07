"""
LangGraph state machine for conversation flow management
Handles multi-turn conversation states and transitions
"""

from typing import Dict, List, Optional, TypedDict, Annotated, Tuple
from langgraph.graph import StateGraph, END
from google import genai
import os

from models.conversation import ConversationState, Message, MessageRole
from services.intent_classifier import IntentClassifier
from services.entity_extractor import EntityExtractor
from services.entity_extractor_gemini import EntityExtractorGemini


class ConversationGraphState(TypedDict):
    """State schema for conversation graph"""
    conversation_id: str
    current_message: str
    intent: str
    entities: Dict  # Changed to support confidence scores: {entity_type: [(value, confidence)]}
    conversation_state: ConversationState
    response: str
    next_questions: List[str]
    workflow_preview: Optional[Dict]
    progress: float
    confidence_score: float
    stage: str  # initial_intent, gather_details, validate_requirements, generate_workflow


class ConversationGraph:
    """LangGraph-based conversation state machine for AgentFlow"""

    def __init__(self, use_enhanced_services: bool = True):
        self.use_enhanced_services = use_enhanced_services

        # Basic services
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()

        # Enhanced services (Phase 2)
        if self.use_enhanced_services:
            self.entity_extractor_gemini = EntityExtractorGemini()

        # Initialize Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            self.client = genai.Client(api_key=api_key)
            self.model_name = 'gemini-2.5-flash'
            self.llm_enabled = True
        else:
            self.client = None
            self.llm_enabled = False
            print("Warning: GEMINI_API_KEY not found. LangGraph using rule-based responses.")

        # Build the state graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the conversation state machine graph"""
        workflow = StateGraph(ConversationGraphState)

        # Add nodes (states)
        workflow.add_node("classify_intent", self._classify_intent_node)
        workflow.add_node("extract_entities", self._extract_entities_node)
        workflow.add_node("determine_stage", self._determine_stage_node)
        workflow.add_node("gather_details", self._gather_details_node)
        workflow.add_node("validate_requirements", self._validate_requirements_node)
        workflow.add_node("generate_workflow", self._generate_workflow_node)
        workflow.add_node("generate_response", self._generate_response_node)

        # Define edges (transitions)
        workflow.set_entry_point("classify_intent")

        workflow.add_edge("classify_intent", "extract_entities")
        workflow.add_edge("extract_entities", "determine_stage")

        # Conditional routing based on stage
        workflow.add_conditional_edges(
            "determine_stage",
            self._route_by_stage,
            {
                "gather_details": "gather_details",
                "validate_requirements": "validate_requirements",
                "generate_workflow": "generate_workflow",
            }
        )

        workflow.add_edge("gather_details", "generate_response")
        workflow.add_edge("validate_requirements", "generate_response")
        workflow.add_edge("generate_workflow", "generate_response")
        workflow.add_edge("generate_response", END)

        return workflow.compile()

    async def _classify_intent_node(self, state: ConversationGraphState) -> ConversationGraphState:
        """Node: Classify user intent"""
        intent = await self.intent_classifier.classify(state["current_message"])
        state["intent"] = intent
        return state

    async def _extract_entities_node(self, state: ConversationGraphState) -> ConversationGraphState:
        """Node: Extract entities from message"""
        # Use enhanced entity extractor if available
        if self.use_enhanced_services:
            # Enhanced extraction with confidence scores
            entities_with_confidence = await self.entity_extractor_gemini.extract(
                state["current_message"],
                intent=state.get("intent")
            )

            # Convert to simple format for conversation state (for backwards compatibility)
            entities_simple = {}
            for entity_type, values in entities_with_confidence.items():
                # Keep only high-confidence entities (>= 0.5) for conversation state
                high_conf_values = [value for value, conf in values if conf >= 0.5]
                if high_conf_values:
                    entities_simple[entity_type] = high_conf_values

            # Store both formats
            state["entities"] = entities_with_confidence  # Full format with confidence
            state["entities_simple"] = entities_simple   # Simple format for legacy code

            # Update conversation state with simple format
            conv_state = state["conversation_state"]
            conv_state.entities.update(entities_simple)

        else:
            # Legacy extraction without confidence scores
            entities = await self.entity_extractor.extract(state["current_message"])

            # Merge with existing entities
            conv_state = state["conversation_state"]
            conv_state.entities.update(entities)
            state["entities"] = conv_state.entities

        return state

    async def _determine_stage_node(self, state: ConversationGraphState) -> ConversationGraphState:
        """Node: Determine conversation stage"""
        conv_state = state["conversation_state"]
        user_messages = conv_state.get_user_messages()
        message_count = len(user_messages)

        # Calculate completeness
        required_entities = self._get_required_entities(state["intent"])
        gathered_entities = set(state["entities"].keys())
        completeness = len(gathered_entities.intersection(required_entities)) / len(required_entities) if required_entities else 0

        # Always generate workflow preview using Gemini for dynamic workflows
        if self.llm_enabled:
            state["workflow_preview"] = await self._generate_dynamic_workflow(state)
        else:
            state["workflow_preview"] = self._create_progressive_workflow(state["intent"], state["entities"], completeness)

        # Determine stage based on message count and completeness
        # Move to generate_workflow faster to avoid looping
        if message_count == 1:
            stage = "gather_details"
        elif completeness < 0.4:
            stage = "gather_details"
        elif message_count >= 3 or completeness >= 0.6:
            # After 3 messages or good completeness, generate final workflow
            stage = "generate_workflow"
        else:
            stage = "validate_requirements"

        state["stage"] = stage
        state["confidence_score"] = completeness
        state["progress"] = min(message_count * 0.15 + completeness * 0.5, 1.0)

        return state

    def _route_by_stage(self, state: ConversationGraphState) -> str:
        """Router: Route to appropriate node based on stage"""
        return state["stage"]

    def _get_required_entities(self, intent: str) -> set:
        """Get required entities for an intent"""
        requirements = {
            "email_automation": {"email_addresses", "team_mentions", "urgency_indicators"},
            "data_processing": {"file_types", "time_expressions"},
            "approval_workflow": {"team_mentions", "time_expressions"},
            "notification_system": {"team_mentions", "urgency_indicators"}
        }
        return requirements.get(intent, set())

    async def _gather_details_node(self, state: ConversationGraphState) -> ConversationGraphState:
        """Node: Gather more details from user"""
        required_entities = self._get_required_entities(state["intent"])
        gathered_entities = set(state["entities"].keys())
        missing_entities = required_entities - gathered_entities

        # Generate questions for missing entities
        state["next_questions"] = self._generate_entity_questions(state["intent"], list(missing_entities))

        return state

    async def _validate_requirements_node(self, state: ConversationGraphState) -> ConversationGraphState:
        """Node: Validate workflow requirements"""
        # Check if all required information is present
        required_entities = self._get_required_entities(state["intent"])
        gathered_entities = set(state["entities"].keys())

        if required_entities.issubset(gathered_entities):
            state["confidence_score"] = 0.9
        else:
            state["confidence_score"] = 0.6

        # Generate clarification questions
        state["next_questions"] = self._generate_clarification_questions(state["intent"], state["entities"])

        return state

    async def _generate_workflow_node(self, state: ConversationGraphState) -> ConversationGraphState:
        """Node: Generate workflow specification"""
        intent = state["intent"]
        entities = state["entities"]

        # Generate workflow using Gemini for dynamic, context-aware workflows
        if self.llm_enabled:
            workflow = await self._generate_dynamic_workflow(state)
        else:
            workflow = self._create_workflow_template(intent, entities)

        state["workflow_preview"] = workflow
        state["confidence_score"] = 0.95

        return state

    async def _generate_response_node(self, state: ConversationGraphState) -> ConversationGraphState:
        """Node: Generate final response to user"""
        if self.llm_enabled:
            response = await self._generate_llm_response(state)
        else:
            response = self._generate_rule_based_response(state)

        state["response"] = response
        return state

    async def _generate_llm_response(self, state: ConversationGraphState) -> str:
        """Generate response using Gemini LLM"""
        try:
            conv_state = state["conversation_state"]
            context = self._build_context(conv_state)

            prompt = f"""You are AgentFlow, an AI assistant that helps users build automation workflows.

Context:
{context}

Current Stage: {state['stage']}
Intent: {state['intent']}
Entities Gathered: {', '.join(state['entities'].keys()) if state['entities'] else 'None'}
Confidence Score: {state['confidence_score']:.0%}

Based on the conversation stage and gathered information:
1. Acknowledge the user's input naturally
2. {"Ask for missing information" if state['stage'] == 'gather_details' else "Confirm understanding and clarify if needed" if state['stage'] == 'validate_requirements' else "Summarize the workflow you'll build"}
3. Keep it conversational and encouraging (2-3 sentences)

Response:"""

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text

        except Exception as e:
            print(f"Error generating LLM response: {e}")
            return self._generate_rule_based_response(state)

    def _generate_rule_based_response(self, state: ConversationGraphState) -> str:
        """Fallback rule-based response"""
        stage = state['stage']
        intent = state['intent']

        if stage == "gather_details":
            return f"Great! I understand you want to build {intent.replace('_', ' ')}. Let me gather a few more details to make it perfect."
        elif stage == "validate_requirements":
            return f"Perfect! I have most of the information. Let me confirm a few details to ensure the workflow meets your needs."
        else:
            return f"Excellent! I have all the information needed. I'm building your {intent.replace('_', ' ')} workflow now."

    def _build_context(self, conv_state: ConversationState) -> str:
        """Build conversation context for LLM"""
        messages = conv_state.get_latest_context(5)
        context_parts = []

        for msg in messages:
            role = "User" if msg.role == MessageRole.USER else "Assistant"
            context_parts.append(f"{role}: {msg.content}")

        return "\n".join(context_parts)

    def _create_progressive_workflow(self, intent: str, entities: Dict, completeness: float) -> Dict:
        """Create progressive workflow with entity details"""
        # Extract entity values (handle both tuple and simple formats)
        def get_entity_values(entity_list):
            if not entity_list:
                return []
            if isinstance(entity_list[0], tuple):
                return [val for val, conf in entity_list]
            return entity_list

        email_addresses = get_entity_values(entities.get('email_addresses', []))
        teams = get_entity_values(entities.get('team_mentions', []))
        urgency = get_entity_values(entities.get('urgency_indicators', []))
        file_types = get_entity_values(entities.get('file_types', []))
        time_expr = get_entity_values(entities.get('time_expressions', []))
        tools = get_entity_values(entities.get('tools_services', []))

        if intent == "email_automation":
            steps = []
            # Monitor step - always present
            monitor_desc = f"Monitor incoming emails"
            if email_addresses:
                monitor_desc += f" from {', '.join(email_addresses)}"
            steps.append({
                "id": "monitor",
                "type": "email",
                "name": "Email Monitor",
                "description": monitor_desc,
                "details": {"emails": email_addresses} if email_addresses else {}
            })

            # Classify step - add when we have some info
            classify_desc = "Analyze and classify emails"
            if urgency:
                classify_desc += f" (prioritize {', '.join(urgency)})"
            steps.append({
                "id": "classify",
                "type": "process",
                "name": "Smart Classifier",
                "description": classify_desc,
                "details": {"urgency_keywords": urgency} if urgency else {}
            })

            # Route step - add when we have teams
            if teams or completeness > 0.3:
                route_desc = "Route emails to appropriate team"
                if teams:
                    route_desc += f": {', '.join(teams)}"
                steps.append({
                    "id": "route",
                    "type": "decision",
                    "name": "Smart Router",
                    "description": route_desc,
                    "details": {"teams": teams} if teams else {}
                })

            # Notification step - add if tools mentioned
            if tools:
                steps.append({
                    "id": "notify",
                    "type": "notification",
                    "name": "Notify Team",
                    "description": f"Send notifications via {', '.join(tools)}",
                    "details": {"channels": tools}
                })

            return {
                "steps": steps,
                "metadata": {"intent": intent, "completeness": completeness}
            }

        elif intent == "data_processing":
            steps = []
            # Input step
            input_desc = "Collect data"
            if file_types:
                input_desc += f" from {', '.join(file_types)} files"
            steps.append({
                "id": "input",
                "type": "data",
                "name": "Data Input",
                "description": input_desc,
                "details": {"file_types": file_types} if file_types else {}
            })

            # Process step
            steps.append({
                "id": "process",
                "type": "process",
                "name": "Process Data",
                "description": "Transform and validate data"
            })

            # Schedule step if time mentioned
            if time_expr or completeness > 0.4:
                schedule_desc = "Schedule processing"
                if time_expr:
                    schedule_desc += f" {', '.join(time_expr)}"
                steps.append({
                    "id": "schedule",
                    "type": "trigger",
                    "name": "Schedule",
                    "description": schedule_desc,
                    "details": {"schedule": time_expr} if time_expr else {}
                })

            # Output step if emails mentioned
            if email_addresses:
                steps.append({
                    "id": "output",
                    "type": "notification",
                    "name": "Send Report",
                    "description": f"Send results to {', '.join(email_addresses)}",
                    "details": {"recipients": email_addresses}
                })

            return {
                "steps": steps,
                "metadata": {"intent": intent, "completeness": completeness}
            }

        elif intent == "approval_workflow":
            steps = [
                {"id": "submit", "type": "action", "name": "Submit Request", "description": "Receive approval requests"},
                {"id": "review", "type": "decision", "name": "Review", "description": f"Route to {', '.join(teams)}" if teams else "Route to approvers", "details": {"approvers": teams} if teams else {}}
            ]
            if time_expr:
                steps.append({
                    "id": "escalate",
                    "type": "decision",
                    "name": "Escalation",
                    "description": f"Escalate if not approved {', '.join(time_expr)}",
                    "details": {"timeout": time_expr}
                })
            return {"steps": steps, "metadata": {"intent": intent, "completeness": completeness}}

        elif intent == "notification_system":
            steps = [
                {"id": "monitor", "type": "process", "name": "Event Monitor", "description": "Monitor for trigger events"},
                {"id": "filter", "type": "decision", "name": "Filter", "description": "Apply notification rules"}
            ]
            if tools or teams:
                notify_desc = "Send notifications"
                details = {}
                if tools:
                    notify_desc += f" via {', '.join(tools)}"
                    details["channels"] = tools
                if teams:
                    notify_desc += f" to {', '.join(teams)}"
                    details["recipients"] = teams
                steps.append({
                    "id": "notify",
                    "type": "notification",
                    "name": "Send Notification",
                    "description": notify_desc,
                    "details": details
                })
            return {"steps": steps, "metadata": {"intent": intent, "completeness": completeness}}

        # Default workflow
        return {
            "steps": [
                {"id": "trigger", "type": "process", "name": "Workflow Trigger", "description": "Start workflow"}
            ],
            "metadata": {"intent": intent, "completeness": completeness}
        }

    async def _generate_dynamic_workflow(self, state: ConversationGraphState) -> Dict:
        """Generate dynamic workflow using Gemini LLM"""
        try:
            conv_state = state["conversation_state"]
            intent = state["intent"]
            entities = state["entities"]

            # Calculate completeness
            required_entities = self._get_required_entities(intent)
            gathered_entities = set(entities.keys())
            completeness = len(gathered_entities.intersection(required_entities)) / len(required_entities) if required_entities else 0

            # Build conversation context
            messages = conv_state.get_latest_context(10)
            context = "\n".join([f"{msg.role}: {msg.content}" for msg in messages])

            # Extract entity values for prompt
            def get_entity_values(entity_list):
                if not entity_list:
                    return []
                if isinstance(entity_list[0], tuple):
                    return [val for val, conf in entity_list]
                return entity_list

            entities_str = "\n".join([f"- {key}: {', '.join(get_entity_values(values))}"
                                     for key, values in entities.items() if values])

            # Get previous workflow if it exists
            previous_workflow = state.get("workflow_preview")
            previous_workflow_str = ""
            if previous_workflow and previous_workflow.get("steps"):
                import json
                previous_workflow_str = f"\nPrevious Workflow (update and enhance this):\n{json.dumps(previous_workflow, indent=2)}"

            # Adjust workflow complexity based on completeness
            completeness_guidance = ""
            if completeness < 0.4:
                completeness_guidance = "Generate a PARTIAL workflow (2-3 core steps) since we're still gathering information. Mark missing details as 'TBD'."
            elif completeness < 0.7:
                completeness_guidance = "Generate a MOSTLY COMPLETE workflow (3-5 steps) with the information we have. Use placeholders for missing details."
            else:
                completeness_guidance = "Generate a COMPLETE workflow (4-6 steps) with all details filled in."

            prompt = f"""You are a workflow automation expert. Based on the conversation below, generate a detailed workflow specification.

Conversation:
{context}

Intent: {intent}
Information Completeness: {completeness:.0%}
Extracted Entities:
{entities_str}
{previous_workflow_str}

{completeness_guidance}

IMPORTANT: If there's a previous workflow, BUILD UPON IT by:
- Keeping existing steps that are still relevant
- UPDATING step details with new information from the conversation
- Adding new steps if needed based on new requirements
- Do NOT remove steps unless explicitly requested

Generate a workflow with specific steps. Return ONLY a JSON object with this exact structure:
{{
  "steps": [
    {{
      "id": "step_id",
      "type": "email|data|process|notification|decision|trigger|action",
      "name": "Step Name",
      "description": "Detailed description with specific entities",
      "details": {{"key": "value"}}
    }}
  ],
  "metadata": {{
    "intent": "{intent}",
    "completeness": 1.0
  }}
}}

IMPORTANT:
- Include ALL mentioned entities (emails, teams, tools, schedules, file types) in step descriptions and details
- Make descriptions specific to user's requirements
- Use appropriate step types
- Include 3-6 steps that form a complete automation workflow
- Put entity values in the "details" object for each step

JSON Response:"""

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            # Parse JSON response
            response_text = response.text.strip()

            # Extract JSON from markdown if needed
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()

            import json
            workflow = json.loads(response_text)

            # Ensure workflow has required structure
            if not isinstance(workflow.get('steps'), list):
                raise ValueError("Invalid workflow structure")

            return workflow

        except Exception as e:
            print(f"Error generating dynamic workflow with Gemini: {e}")
            # Fallback to template-based generation
            return self._create_progressive_workflow(state["intent"], entities, 1.0)

    def _create_workflow_template(self, intent: str, entities: Dict) -> Dict:
        """Create final workflow template - delegates to progressive builder"""
        return self._create_progressive_workflow(intent, entities, 1.0)

    def _generate_entity_questions(self, intent: str, missing_entities: List[str]) -> List[str]:
        """Generate questions for missing entities"""
        questions = []
        question_map = {
            "email_addresses": "What email address should I monitor?",
            "team_mentions": "Which teams should be involved in this workflow?",
            "urgency_indicators": "How should I identify urgent items?",
            "file_types": "What types of files will you be processing?",
            "time_expressions": "How often should this workflow run?"
        }

        for entity in missing_entities[:2]:  # Limit to 2 questions
            if entity in question_map:
                questions.append(question_map[entity])

        return questions

    def _generate_clarification_questions(self, intent: str, entities: Dict) -> List[str]:
        """Generate clarification questions"""
        return [
            "Does this cover all the scenarios you need?",
            "Should I add any additional conditions or rules?"
        ]

    async def process_message(self, conversation_id: str, message: str, conv_state: ConversationState) -> Dict:
        """Process a message through the state graph"""
        # Initialize state
        initial_state: ConversationGraphState = {
            "conversation_id": conversation_id,
            "current_message": message,
            "intent": "",
            "entities": {},
            "conversation_state": conv_state,
            "response": "",
            "next_questions": [],
            "workflow_preview": None,
            "progress": 0.0,
            "confidence_score": 0.0,
            "stage": "gather_details"
        }

        # Run through the graph
        result = await self.graph.ainvoke(initial_state)

        return {
            "response": result["response"],
            "progress": result["progress"],
            "confidence_score": result["confidence_score"],
            "next_questions": result["next_questions"],
            "workflow_preview": result["workflow_preview"],
            "stage": result["stage"],
            "entities_with_confidence": result.get("entities", {})
        }
