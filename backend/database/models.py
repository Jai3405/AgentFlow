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

class ExecutionStatusEnum(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class TriggerTypeEnum(str, enum.Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"
    API = "api"

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

class WorkflowExecutionDB(Base):
    """Database model for workflow executions"""
    __tablename__ = "workflow_executions"

    execution_id = Column(String, primary_key=True, index=True)
    workflow_id = Column(String, ForeignKey("workflows.id"), index=True)
    status = Column(Enum(ExecutionStatusEnum), default=ExecutionStatusEnum.PENDING)
    trigger_type = Column(Enum(TriggerTypeEnum), default=TriggerTypeEnum.MANUAL)

    # Execution state
    current_step = Column(String, nullable=True)
    completed_steps = Column(JSON, default=list)
    failed_steps = Column(JSON, default=list)

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    execution_time_seconds = Column(Float, nullable=True)

    # Data
    input_data = Column(JSON, nullable=True)
    step_outputs = Column(JSON, nullable=True)
    variables = Column(JSON, nullable=True)

    # Logs and errors
    error_message = Column(Text, nullable=True)
    error_step = Column(String, nullable=True)

    # Metadata
    progress = Column(Float, default=0.0)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    workflow = relationship("WorkflowDB", backref="executions")
    logs = relationship("ExecutionLogDB", back_populates="execution", cascade="all, delete-orphan")

class ExecutionLogDB(Base):
    """Database model for execution logs"""
    __tablename__ = "execution_logs"

    id = Column(String, primary_key=True)
    execution_id = Column(String, ForeignKey("workflow_executions.execution_id"))
    timestamp = Column(DateTime, default=datetime.now)
    level = Column(String)  # info, warning, error, debug
    message = Column(Text)
    step_id = Column(String, nullable=True)
    metadata = Column(JSON, nullable=True)

    # Relationships
    execution = relationship("WorkflowExecutionDB", back_populates="logs")

class ScheduledJobDB(Base):
    """Database model for scheduled workflow jobs"""
    __tablename__ = "scheduled_jobs"

    job_id = Column(String, primary_key=True, index=True)
    workflow_id = Column(String, ForeignKey("workflows.id"))
    schedule_type = Column(String)  # cron, interval, once
    schedule_config = Column(JSON)  # cron expression, interval config, etc.
    input_data = Column(JSON, nullable=True)
    enabled = Column(Boolean, default=True)

    # Execution tracking
    last_execution = Column(DateTime, nullable=True)
    next_execution = Column(DateTime, nullable=True)
    execution_count = Column(String, default="0")
    failure_count = Column(String, default="0")

    # Metadata
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    workflow = relationship("WorkflowDB", backref="scheduled_jobs")
