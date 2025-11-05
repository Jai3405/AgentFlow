"""
LangGraph state machine for conversation flow management
Handles multi-turn conversation states and transitions
"""

from typing import Dict, List, Optional, TypedDict, Annotated, Tuple
from langgraph.graph import StateGraph, END
import google.generativeai as genai
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
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.llm_enabled = True
        else:
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

        # Determine stage based on message count and completeness
        if message_count == 1:
            stage = "gather_details"
        elif completeness < 0.5:
            stage = "gather_details"
        elif completeness < 0.8:
            stage = "validate_requirements"
        else:
            stage = "generate_workflow"

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

        # Generate workflow based on intent
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

            response = self.model.generate_content(prompt)
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

    def _create_workflow_template(self, intent: str, entities: Dict) -> Dict:
        """Create workflow template based on intent and entities"""
        # Simplified workflow generation - to be enhanced
        if intent == "email_automation":
            return {
                "steps": [
                    {"id": "monitor", "type": "email", "name": "Email Monitor", "description": "Monitor incoming emails"},
                    {"id": "classify", "type": "process", "name": "Classify", "description": "Smart email classification"},
                    {"id": "route", "type": "decision", "name": "Route", "description": "Route to appropriate team"}
                ],
                "metadata": {"intent": intent, "entities": entities}
            }
        # Add other intent templates as needed
        return {"steps": [], "metadata": {"intent": intent}}

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
            "stage": result["stage"]
        }
