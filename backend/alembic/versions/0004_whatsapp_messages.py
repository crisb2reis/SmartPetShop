"""Create whatsapp_messages table for Meta Cloud API integration and audit

Revision ID: 0004_whatsapp_messages
Revises: 0003_vaccine_models
Create Date: 2026-11-15 17:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0004_whatsapp_messages'
down_revision: Union[str, None] = '0003_vaccine_models'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'whatsapp_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', sa.String(length=150), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=False),
        sa.Column('direction', sa.String(length=20), server_default='INBOUND', nullable=False),
        sa.Column('message_type', sa.String(length=30), server_default='text', nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='received', nullable=False),
        sa.Column('tutor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('raw_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tutor_id'], ['tutors.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_whatsapp_messages_id', 'whatsapp_messages', ['id'], unique=False)
    op.create_index('ix_whatsapp_messages_tenant_id', 'whatsapp_messages', ['tenant_id'], unique=False)
    op.create_index('ix_whatsapp_messages_message_id', 'whatsapp_messages', ['message_id'], unique=True)
    op.create_index('ix_whatsapp_messages_phone', 'whatsapp_messages', ['phone'], unique=False)
    op.create_index('ix_whatsapp_messages_direction', 'whatsapp_messages', ['direction'], unique=False)
    op.create_index('ix_whatsapp_messages_status', 'whatsapp_messages', ['status'], unique=False)
    op.create_index('ix_whatsapp_messages_tutor_id', 'whatsapp_messages', ['tutor_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_whatsapp_messages_tutor_id', table_name='whatsapp_messages')
    op.drop_index('ix_whatsapp_messages_status', table_name='whatsapp_messages')
    op.drop_index('ix_whatsapp_messages_direction', table_name='whatsapp_messages')
    op.drop_index('ix_whatsapp_messages_phone', table_name='whatsapp_messages')
    op.drop_index('ix_whatsapp_messages_message_id', table_name='whatsapp_messages')
    op.drop_index('ix_whatsapp_messages_tenant_id', table_name='whatsapp_messages')
    op.drop_index('ix_whatsapp_messages_id', table_name='whatsapp_messages')
    op.drop_table('whatsapp_messages')

