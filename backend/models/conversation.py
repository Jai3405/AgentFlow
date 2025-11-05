from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class WorkflowType(str, Enum):
    EMAIL_PROCESSING = "email_processing"
    DATA_PIPELINE = "data_pipeline"
    APPROVAL_WORKFLOW = "approval_workflow"
    NOTIFICATION_SYSTEM = "notification_system"

class ConversationState(BaseModel):
    conversation_id: Optional[str] = None
    messages: List[Message] = []
    workflow_type: Optional[WorkflowType] = None
    entities: Dict[str, Any] = {}
    requirements: Dict[str, Any] = {}
    progress: float = 0.0
    confidence_score: float = 0.0
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    
    def add_message(self, message: Message):
        """Add a message to the conversation"""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_user_messages(self) -> List[Message]:
        """Get only user messages"""
        return [msg for msg in self.messages if msg.role == MessageRole.USER]
    
    def get_latest_context(self, num_messages: int = 10) -> List[Message]:
        """Get recent conversation context"""
        return self.messages[-num_messages:]
