import json
from typing import Dict, List, Optional
from langchain_openai import OpenAI
from langgraph.graph import StateGraph, END
from models.conversation import ConversationState, Message
from services.intent_classifier import IntentClassifier
from services.entity_extractor import EntityExtractor
from datetime import datetime

class ConversationManager:
    def __init__(self):
        self.conversations: Dict[str, ConversationState] = {}
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        # For now, create a simple response without LLM
        # self.llm = OpenAI(temperature=0.7)
    
    async def process_message(self, conversation_id: str, message: str) -> Dict:
        """Process a user message and return response"""
        
        # Get or create conversation state
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ConversationState()
        
        state = self.conversations[conversation_id]
        
        # Add user message
        from models.conversation import Message, MessageRole
        state.add_message(Message(
            role=MessageRole.USER,
            content=message,
            timestamp=datetime.now()
        ))
        
        # Simple response generation for now
        intent = await self.intent_classifier.classify(message)
        entities = await self.entity_extractor.extract(message)
        
        # Update state
        state.entities.update(entities)
        
        # Calculate progress
        required_info = ["email_addresses", "team_mentions", "urgency_indicators"]
        gathered_info = [key for key in required_info if key in entities]
        progress = len(gathered_info) / len(required_info) if required_info else 0.0
        
        # Generate response based on intent
        if intent == "email_automation":
            response = f"I understand you want to automate email processes. I can see you mentioned: {', '.join(entities.get('email_addresses', []))}. Let me help you build an email processing workflow. What specific actions do you want to take with these emails?"
        elif intent == "data_processing":
            response = "I can help you build a data processing workflow. What kind of data are you working with and what do you want to do with it?"
        else:
            response = "I'd be happy to help you build an automation workflow! Can you tell me more about what business process you'd like to automate?"
        
        return {
            "response": response,
            "progress": progress,
            "next_questions": self._generate_questions(intent),
            "workflow_preview": self._generate_preview(intent) if progress > 0.3 else None
        }
    
    async def get_conversation(self, conversation_id: str):
        """Get conversation by ID"""
        return self.conversations.get(conversation_id)
    
    def _generate_questions(self, intent: str) -> List[str]:
        """Generate follow-up questions based on intent"""
        questions = {
            "email_automation": [
                "What email address should I monitor?",
                "How do you want to categorize the emails?",
                "Which team members should receive different types of emails?"
            ],
            "data_processing": [
                "What format is your data in (CSV, JSON, database)?",
                "What processing steps do you need?",
                "Where should the processed data be sent?"
            ]
        }
        return questions.get(intent, ["What would you like to automate?"])
    
    def _generate_preview(self, intent: str) -> Dict:
        """Generate a simple workflow preview"""
        if intent == "email_automation":
            return {
                "steps": [
                    {"id": "monitor", "type": "email", "name": "Email Monitor", "description": "Monitor incoming emails"},
                    {"id": "classify", "type": "process", "name": "Classify", "description": "Categorize emails by type"},
                    {"id": "route", "type": "decision", "name": "Route", "description": "Send to appropriate team"}
                ]
            }
        return {"steps": []}
