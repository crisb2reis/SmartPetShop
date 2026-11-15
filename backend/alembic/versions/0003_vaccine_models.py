"""Create vaccine catalogs, batches and pet vaccination records

Revision ID: 0003_vaccine_models
Revises: 0002_multitenancy_rbac
Create Date: 2026-11-15 12:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0003_vaccine_models'
down_revision: Union[str, None] = '0002_multitenancy_rbac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tabela: vaccine_catalogs (Catálogo Oficial de Vacinas)
    op.create_table(
        'vaccine_catalogs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('species', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('type', sa.String(length=30), server_default='OBRIGATORIA', nullable=False),
        sa.Column('recommended_age_weeks', sa.Integer(), server_default='8', nullable=False),
        sa.Column('doses_required', sa.Integer(), server_default='1', nullable=False),
        sa.Column('booster_interval_days', sa.Integer(), server_default='365', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_vaccine_catalogs_id', 'vaccine_catalogs', ['id'], unique=False)
    op.create_index('ix_vaccine_catalogs_tenant_id', 'vaccine_catalogs', ['tenant_id'], unique=False)
    op.create_index('ix_vaccine_catalogs_species', 'vaccine_catalogs', ['species'], unique=False)
    op.create_index('ix_vaccine_catalogs_name', 'vaccine_catalogs', ['name'], unique=False)
    op.create_index('ix_vaccine_catalogs_type', 'vaccine_catalogs', ['type'], unique=False)

    # 2. Tabela: vaccine_batches (Controle de Estoque e Lote)
    op.create_table(
        'vaccine_batches',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vaccine_catalog_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('batch_number', sa.String(length=100), nullable=False),
        sa.Column('manufacturer', sa.String(length=150), nullable=False),
        sa.Column('expiration_date', sa.Date(), nullable=False),
        sa.Column('active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vaccine_catalog_id'], ['vaccine_catalogs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_vaccine_batches_id', 'vaccine_batches', ['id'], unique=False)
    op.create_index('ix_vaccine_batches_tenant_id', 'vaccine_batches', ['tenant_id'], unique=False)
    op.create_index('ix_vaccine_batches_vaccine_catalog_id', 'vaccine_batches', ['vaccine_catalog_id'], unique=False)
    op.create_index('ix_vaccine_batches_batch_number', 'vaccine_batches', ['batch_number'], unique=False)
    op.create_index('ix_vaccine_batches_expiration_date', 'vaccine_batches', ['expiration_date'], unique=False)

    # 3. Tabela: pet_vaccination_records (Caderneta de Vacinação do Pet)
    op.create_table(
        'pet_vaccination_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pet_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vaccine_catalog_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vaccine_batch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('application_date', sa.Date(), nullable=False),
        sa.Column('next_due_date', sa.Date(), nullable=True),
        sa.Column('vet_name', sa.String(length=150), nullable=False),
        sa.Column('vet_crmv', sa.String(length=50), nullable=False),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='APLICADA', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pet_id'], ['pets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vaccine_catalog_id'], ['vaccine_catalogs.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['vaccine_batch_id'], ['vaccine_batches.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['clinic_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pet_vaccination_records_id', 'pet_vaccination_records', ['id'], unique=False)
    op.create_index('ix_pet_vaccination_records_tenant_id', 'pet_vaccination_records', ['tenant_id'], unique=False)
    op.create_index('ix_pet_vaccination_records_pet_id', 'pet_vaccination_records', ['pet_id'], unique=False)
    op.create_index('ix_pet_vaccination_records_vaccine_catalog_id', 'pet_vaccination_records', ['vaccine_catalog_id'], unique=False)
    op.create_index('ix_pet_vaccination_records_vaccine_batch_id', 'pet_vaccination_records', ['vaccine_batch_id'], unique=False)
    op.create_index('ix_pet_vaccination_records_application_date', 'pet_vaccination_records', ['application_date'], unique=False)
    op.create_index('ix_pet_vaccination_records_next_due_date', 'pet_vaccination_records', ['next_due_date'], unique=False)
    op.create_index('ix_pet_vaccination_records_vet_crmv', 'pet_vaccination_records', ['vet_crmv'], unique=False)
    op.create_index('ix_pet_vaccination_records_clinic_id', 'pet_vaccination_records', ['clinic_id'], unique=False)
    op.create_index('ix_pet_vaccination_records_status', 'pet_vaccination_records', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('pet_vaccination_records')
    op.drop_table('vaccine_batches')
    op.drop_table('vaccine_catalogs')

