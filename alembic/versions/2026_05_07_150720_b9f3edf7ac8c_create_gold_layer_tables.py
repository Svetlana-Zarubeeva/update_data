"""create_gold_layer_tables

Revision ID: b9f3edf7ac8c
Revises: 
Create Date: 2026-05-07 15:07:20.765536

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'b9f3edf7ac8c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'legal_entities',
        sa.Column('id', sa.BigInteger, primary_key=True),
        sa.Column('inn', sa.String(12), unique=True, nullable=False),
        sa.Column('ogrn', sa.String(15)),
        sa.Column('kpp', sa.String(9)),
        sa.Column('short_name', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(500), nullable=False),
        sa.Column('registration_date', sa.Date),
        sa.Column('status', sa.String(255), nullable=False),
        sa.Column('okved_code', sa.String(20)),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['okved_code'], ['okved_it_codes.okved_code'], ondelete='SET NULL')
    )
    op.create_table(
        'founder_types',
        sa.Column('id', sa.BigInteger, primary_key=True),
        sa.Column('type_code', sa.String(10), unique=True, nullable=False),
        sa.Column('type_name', sa.String(100), nullable=False)
    )
    op.create_table(
        'addresses',
        sa.Column('id', sa.BigInteger, primary_key=True),
        sa.Column('legal_entity_id', sa.BigInteger, nullable=False),
        sa.Column('address_full', sa.Text, nullable=False),
        sa.Column('postal_code', sa.String(10)),
        sa.Column('region', sa.String(100), nullable=False),
        sa.Column('district', sa.String(100)),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('street', sa.String(255)),
        sa.Column('house', sa.String(50)),
        sa.Column('flat', sa.String(50)),
        sa.Column('latitude', sa.Float(precision=8)),
        sa.Column('longitude', sa.Float(precision=8)),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['legal_entity_id'], ['legal_entities.id'], ondelete='CASCADE')
    )
    op.create_table(
        'contact_info',
        sa.Column('id', sa.BigInteger, primary_key=True),
        sa.Column('legal_entity_id', sa.BigInteger, nullable=False),
        sa.Column('phones', JSONB),
        sa.Column('emails', JSONB),
        sa.Column('websites', JSONB),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['legal_entity_id'], ['legal_entities.id'], ondelete='CASCADE')
    )
    op.create_table(
        'finance',
        sa.Column('id', sa.BigInteger, primary_key=True),
        sa.Column('legal_entity_id', sa.BigInteger, nullable=False),
        sa.Column('employee_count', sa.Integer),
        sa.Column('revenue', sa.Float),
        sa.Column('income', sa.Float),
        sa.Column('expense', sa.Float),
        sa.Column('tax_system', sa.String(10)),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['legal_entity_id'], ['legal_entities.id'], ondelete='CASCADE')
    )
    op.create_table(
        'management',
        sa.Column('id', sa.BigInteger, primary_key=True),
        sa.Column('legal_entity_id', sa.BigInteger, nullable=False),
        sa.Column('name', sa.String(255)),
        sa.Column('post', sa.String(255)),
        sa.Column('start_date', sa.Date),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['legal_entity_id'], ['legal_entities.id'], ondelete='CASCADE')
    )
    op.create_table(
        'founders',
        sa.Column('id', sa.BigInteger, primary_key=True),
        sa.Column('legal_entity_id', sa.BigInteger, nullable=False),
        sa.Column('founder_type_id', sa.BigInteger, nullable=False),
        sa.Column('inn', sa.String(12)),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('is_inaccurate', sa.Boolean, default=False, nullable=False),
        sa.Column('reason', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['legal_entity_id'], ['legal_entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['founder_type_id'], ['founder_types.id'], ondelete='RESTRICT')
    )
    op.create_table(
        'pipeline_metrics',
        sa.Column('id', sa.BigInteger, primary_key=True),
        sa.Column('pipeline_name', sa.String(50), nullable=False),
        sa.Column('total_records', sa.Integer, nullable=False, default=0),
        sa.Column('new_records', sa.Integer, nullable=False, default=0),
        sa.Column('updated_records', sa.Integer, nullable=False, default=0),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
        
    op.create_index('idx_entities_inn', 'legal_entities', ['inn'])
    op.create_index('idx_entities_ogrn', 'legal_entities', ['ogrn'])
    op.create_index('idx_entities_status', 'legal_entities', ['status'])
    op.create_index('idx_entities_okved_code', 'legal_entities', ['okved_code'])
    
    op.create_index('idx_founder_types_code', 'founder_types', ['type_code'])
    
    op.create_index('idx_addresses_entity_id', 'addresses', ['legal_entity_id'])
    op.create_index('idx_addresses_postal_code', 'addresses', ['postal_code'])
    op.create_index('idx_addresses_district', 'addresses', ['district'])
    
    op.create_index('idx_contacts_entity_id', 'contact_info', ['legal_entity_id'])
    
    op.create_index('idx_finance_entity_id', 'finance', ['legal_entity_id'])
    
    op.create_index('idx_management_entity_id', 'management', ['legal_entity_id'])
    op.create_index('idx_management_name', 'management', ['name'])
    
    op.create_index('idx_founders_entity_id', 'founders', ['legal_entity_id'])
    op.create_index('idx_founders_type_id', 'founders', ['founder_type_id'])
    
    op.create_index('idx_pipeline_metrics_name', 'pipeline_metrics', ['pipeline_name'])
    op.create_index('idx_pipeline_metrics_created_at', 'pipeline_metrics', ['created_at'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_pipeline_metrics_created_at', table_name='pipeline_metrics')
    op.drop_index('idx_pipeline_metrics_name', table_name='pipeline_metrics')
    op.drop_index('idx_founders_type_id', table_name='founders')
    op.drop_index('idx_founders_entity_id', table_name='founders')
    op.drop_index('idx_management_name', table_name='management')
    op.drop_index('idx_management_entity_id', table_name='management')
    op.drop_index('idx_finance_entity_id', table_name='finance')
    op.drop_index('idx_contacts_entity_id', table_name='contact_info')
    op.drop_index('idx_addresses_postal_code', table_name='addresses')
    op.drop_index('idx_addresses_entity_id', table_name='addresses')
    op.drop_index('idx_addresses_district', table_name='addresses')
    op.drop_index('idx_founder_types_code', table_name='founder_types')
    op.drop_index('idx_entities_okved_code', table_name='legal_entities')
    op.drop_index('idx_entities_status', table_name='legal_entities')
    op.drop_index('idx_entities_ogrn', table_name='legal_entities')
    op.drop_index('idx_entities_inn', table_name='legal_entities')
    
    op.drop_table('pipeline_metrics')
    op.drop_table('founders')
    op.drop_table('management')
    op.drop_table('finance')
    op.drop_table('contact_info')
    op.drop_table('addresses')
    op.drop_table('founder_types')
    op.drop_table('legal_entities')