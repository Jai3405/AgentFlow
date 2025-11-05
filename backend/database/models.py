from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, JSON, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database.base import Base

class MessageRoleEnum(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class WorkflowTypeEnum(str, enum.Enum):
    EMAIL_PROCESSING = "email_processing"
    DATA_PIPELINE = "data_pipeline"
    APPROVAL_WORKFLOW = "approval_workflow"
    NOTIFICATION_SYSTEM = "notification_system"

class IntegrationTypeEnum(str, enum.Enum):
    EMAIL = "email"
    NOTIFICATION = "notification"
    WEBHOOK = "webhook"
    DATABASE = "database"
    FILE_STORAGE = "file_storage"

class IntegrationStatusEnum(str, enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"

class ConversationDB(Base):
    """Database model for conversation state"""
    __tablename__ = "conversations"

    conversation_id = Column(String, primary_key=True, index=True)
    workflow_type = Column(Enum(WorkflowTypeEnum), nullable=True)
    entities = Column(JSON, default=dict)
    requirements = Column(JSON, default=dict)
    progress = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    messages = relationship("MessageDB", back_populates="conversation", cascade="all, delete-orphan")
    workflow = relationship("WorkflowDB", back_populates="conversation", uselist=False, cascade="all, delete-orphan")

class MessageDB(Base):
    """Database model for conversation messages"""
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.conversation_id"))
    role = Column(Enum(MessageRoleEnum))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    metadata = Column(JSON, nullable=True)

    # Relationships
    conversation = relationship("ConversationDB", back_populates="messages")

class WorkflowDB(Base):
    """Database model for workflow specifications"""
    __tablename__ = "workflows"

    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.conversation_id"), unique=True)
    name = Column(String)
    description = Column(Text, nullable=True)
    steps = Column(JSON)
    connections = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    status = Column(String, default="draft")  # draft, ready, deployed, archived
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    conversation = relationship("ConversationDB", back_populates="workflow")

class IntegrationConfigDB(Base):
    """Database model for integration configurations"""
    __tablename__ = "integration_configs"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, index=True)  # gmail, slack, etc.
    integration_type = Column(Enum(IntegrationTypeEnum))
    provider = Column(String)  # gmail, outlook, slack, twilio, etc.
    status = Column(Enum(IntegrationStatusEnum), default=IntegrationStatusEnum.DISCONNECTED)
    credentials = Column(JSON)  # Encrypted credentials
    settings = Column(JSON, nullable=True)  # Additional settings
    metadata = Column(JSON, nullable=True)  # Provider-specific metadata
    is_active = Column(Boolean, default=True)
    last_connected_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class WebhookRegistrationDB(Base):
    """Database model for webhook registrations"""
    __tablename__ = "webhook_registrations"

    id = Column(String, primary_key=True)
    url = Column(String)
    events = Column(JSON)  # List of event types
    secret = Column(String, nullable=True)  # HMAC secret
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    retry_count = Column(String, default="3")
    timeout_seconds = Column(String, default="30")
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    events_log = relationship("WebhookEventDB", back_populates="webhook", cascade="all, delete-orphan")

class WebhookEventDB(Base):
    """Database model for webhook event logs"""
    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True)
    webhook_id = Column(String, ForeignKey("webhook_registrations.id"))
    event_type = Column(String)
    payload = Column(JSON)
    response_status = Column(String, nullable=True)
    response_body = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    triggered_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    webhook = relationship("WebhookRegistrationDB", back_populates="events_log")
