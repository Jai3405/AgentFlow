"""initial schema

Revision ID: 001
Revises:
Create Date: 2025-11-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create conversations table
    op.create_table('conversations',
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('workflow_type', sa.Enum('EMAIL_PROCESSING', 'DATA_PIPELINE', 'APPROVAL_WORKFLOW', 'NOTIFICATION_SYSTEM', name='workflowtypeenum'), nullable=True),
        sa.Column('entities', sa.JSON(), nullable=True),
        sa.Column('requirements', sa.JSON(), nullable=True),
        sa.Column('progress', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('conversation_id')
    )
    op.create_index(op.f('ix_conversations_conversation_id'), 'conversations', ['conversation_id'], unique=False)

    # Create messages table
    op.create_table('messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=True),
        sa.Column('role', sa.Enum('USER', 'ASSISTANT', 'SYSTEM', name='messageroleenum'), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.conversation_id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create workflows table
    op.create_table('workflows',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('steps', sa.JSON(), nullable=True),
        sa.Column('connections', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.conversation_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('conversation_id')
    )


def downgrade() -> None:
    op.drop_table('workflows')
    op.drop_table('messages')
    op.drop_index(op.f('ix_conversations_conversation_id'), table_name='conversations')
    op.drop_table('conversations')
    # Drop enums
    sa.Enum(name='workflowtypeenum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='messageroleenum').drop(op.get_bind(), checkfirst=True)
