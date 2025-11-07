from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import uuid

from database.models import ConversationDB, MessageDB, WorkflowDB, MessageRoleEnum
from models.conversation import ConversationState, Message, MessageRole


class ConversationRepository:
    """Repository for conversation database operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Retrieve conversation from database and convert to domain model"""
        db_conv = self.db.query(ConversationDB).filter(
            ConversationDB.conversation_id == conversation_id
        ).first()

        if not db_conv:
            return None

        # Convert database model to domain model
        messages = [
            Message(
                role=MessageRole(msg.role.value),
                content=msg.content,
                timestamp=msg.timestamp,
                metadata=msg.metadata if isinstance(msg.metadata, dict) else {}
            )
            for msg in db_conv.messages
        ]

        state = ConversationState(
            conversation_id=db_conv.conversation_id,
            messages=messages,
            workflow_type=db_conv.workflow_type.value if db_conv.workflow_type else None,
            entities=db_conv.entities or {},
            requirements=db_conv.requirements or {},
            progress=db_conv.progress,
            confidence_score=db_conv.confidence_score,
            created_at=db_conv.created_at,
            updated_at=db_conv.updated_at
        )

        return state

    def save_conversation(self, state: ConversationState) -> ConversationDB:
        """Save or update conversation state to database"""
        conversation_id = state.conversation_id or str(uuid.uuid4())

        # Check if conversation exists
        db_conv = self.db.query(ConversationDB).filter(
            ConversationDB.conversation_id == conversation_id
        ).first()

        if db_conv:
            # Update existing conversation
            db_conv.entities = state.entities
            db_conv.requirements = state.requirements
            db_conv.progress = state.progress
            db_conv.confidence_score = state.confidence_score
            db_conv.updated_at = datetime.now()
            if state.workflow_type:
                db_conv.workflow_type = state.workflow_type
        else:
            # Create new conversation
            db_conv = ConversationDB(
                conversation_id=conversation_id,
                workflow_type=state.workflow_type,
                entities=state.entities,
                requirements=state.requirements,
                progress=state.progress,
                confidence_score=state.confidence_score,
                created_at=state.created_at or datetime.now(),
                updated_at=datetime.now()
            )
            self.db.add(db_conv)

        self.db.commit()
        self.db.refresh(db_conv)
        return db_conv

    def add_message(self, conversation_id: str, message: Message) -> MessageDB:
        """Add a message to a conversation"""
        db_message = MessageDB(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=MessageRoleEnum(message.role.value),
            content=message.content,
            timestamp=message.timestamp or datetime.now(),
            metadata=message.metadata
        )

        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        return db_message

    def get_messages(self, conversation_id: str, limit: int = 100) -> List[Message]:
        """Get messages for a conversation"""
        db_messages = self.db.query(MessageDB).filter(
            MessageDB.conversation_id == conversation_id
        ).order_by(MessageDB.timestamp).limit(limit).all()

        return [
            Message(
                role=MessageRole(msg.role.value),
                content=msg.content,
                timestamp=msg.timestamp,
                metadata=msg.metadata
            )
            for msg in db_messages
        ]

    def save_workflow(self, conversation_id: str, workflow_data: dict) -> WorkflowDB:
        """Save or update workflow for a conversation"""
        db_workflow = self.db.query(WorkflowDB).filter(
            WorkflowDB.conversation_id == conversation_id
        ).first()

        if db_workflow:
            # Update existing workflow
            db_workflow.steps = workflow_data.get('steps', [])
            db_workflow.connections = workflow_data.get('connections')
            db_workflow.metadata = workflow_data.get('metadata')
            db_workflow.updated_at = datetime.now()
        else:
            # Create new workflow
            db_workflow = WorkflowDB(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                name=workflow_data.get('name', 'Untitled Workflow'),
                description=workflow_data.get('description'),
                steps=workflow_data.get('steps', []),
                connections=workflow_data.get('connections'),
                metadata=workflow_data.get('metadata'),
                status='draft',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.db.add(db_workflow)

        self.db.commit()
        self.db.refresh(db_workflow)
        return db_workflow

    def get_workflow(self, conversation_id: str) -> Optional[WorkflowDB]:
        """Get workflow for a conversation"""
        return self.db.query(WorkflowDB).filter(
            WorkflowDB.conversation_id == conversation_id
        ).first()

    def list_conversations(self, limit: int = 50, offset: int = 0) -> List[ConversationDB]:
        """List all conversations with pagination"""
        return self.db.query(ConversationDB).order_by(
            ConversationDB.updated_at.desc()
        ).limit(limit).offset(offset).all()

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all associated data"""
        db_conv = self.db.query(ConversationDB).filter(
            ConversationDB.conversation_id == conversation_id
        ).first()

        if not db_conv:
            return False

        self.db.delete(db_conv)
        self.db.commit()
        return True
