"""create_gold_layer_tables_pipeline_ofdata

Revision ID: da68b5377f85
Revises: 
Create Date: 2026-05-03 15:43:34.782010

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da68b5377f85'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'ofdata_founder_types',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('type_code', sa.String(10), unique=True, nullable=False),
        sa.Column('type_name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    op.create_table(
        'ofdata_legal_entities',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('inn', sa.String(20), nullable=False, unique=True),
        sa.Column('ogrn', sa.String(20), nullable=True),
        sa.Column('kpp', sa.String(10), nullable=True),
        sa.Column('short_name', sa.String(255), nullable=False),
        sa.Column('full_name', sa.Text(), nullable=False),
        sa.Column('reg_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(255), nullable=False),
        sa.Column('region_code', sa.String(10), nullable=False),
        sa.Column('okved_code', sa.String(20), nullable=False),
        sa.Column('okved_description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    op.create_table(
        'ofdata_addresses',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('legal_entity_id', sa.BigInteger(), sa.ForeignKey('ofdata_legal_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('index', sa.String(20), nullable=True),
        sa.Column('region', sa.String(255), nullable=False),
        sa.Column('city', sa.String(255), nullable=False),
        sa.Column('street', sa.String(255), nullable=False),
        sa.Column('house', sa.String(255), nullable=False),
        sa.Column('full_address', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    op.create_table(
        'ofdata_directors',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('legal_entity_id', sa.BigInteger(), sa.ForeignKey('ofdata_legal_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('inn', sa.String(20), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('position', sa.String(100), nullable=False),
        sa.Column('is_disqualified', sa.Boolean(), default=False, nullable=False),
        sa.Column('is_inaccurate', sa.Boolean(), default=False, nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    op.create_table(
        'ofdata_founders',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('legal_entity_id', sa.BigInteger(), sa.ForeignKey('ofdata_legal_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('founder_type_id', sa.BigInteger(), sa.ForeignKey('ofdata_founder_types.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('inn', sa.String(20), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('ogrn', sa.String(20), nullable=True),
        sa.Column('kpp', sa.String(10), nullable=True),
        sa.Column('is_inaccurate', sa.Boolean(), default=False, nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    op.create_table(
        'pipeline_metrics',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('pipeline_name', sa.String(50), nullable=False),
        sa.Column('total_records', sa.Integer(), nullable=False, default=0),
        sa.Column('new_records', sa.Integer(), nullable=False, default=0),
        sa.Column('updated_records', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    op.create_index('idx_founder_types_code', 'ofdata_founder_types', ['type_code'])
    op.create_index('idx_addresses_region', 'ofdata_addresses', ['region'])
    op.create_index('idx_addresses_city', 'ofdata_addresses', ['city'])
    op.create_index('idx_legal_entities_inn', 'ofdata_legal_entities', ['inn'])
    op.create_index('idx_legal_entities_ogrn', 'ofdata_legal_entities', ['ogrn'])
    op.create_index('idx_legal_entities_region_code', 'ofdata_legal_entities', ['region_code'])
    op.create_index('idx_legal_entities_okved_code', 'ofdata_legal_entities', ['okved_code'])
    op.create_index('idx_legal_entities_status', 'ofdata_legal_entities', ['status'])
    op.create_index('idx_directors_inn', 'ofdata_directors', ['inn'])
    op.create_index('idx_directors_legal_entity_id', 'ofdata_directors', ['legal_entity_id'])
    op.create_index('idx_directors_position', 'ofdata_directors', ['position'])
    op.create_index('idx_founders_inn', 'ofdata_founders', ['inn'])
    op.create_index('idx_founders_legal_entity_id', 'ofdata_founders', ['legal_entity_id'])
    op.create_index('idx_founders_type_id', 'ofdata_founders', ['founder_type_id'])
    op.create_index('idx_pipeline_metrics_name', 'pipeline_metrics', ['pipeline_name'])
    op.create_index('idx_pipeline_metrics_created_at', 'pipeline_metrics', ['created_at'])



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_pipeline_metrics_created_at', table_name='pipeline_metrics')
    op.drop_index('idx_pipeline_metrics_name', table_name='pipeline_metrics')
    op.drop_index('idx_founders_type_id', table_name='ofdata_founders')
    op.drop_index('idx_founders_legal_entity_id', table_name='ofdata_founders')
    op.drop_index('idx_founders_inn', table_name='ofdata_founders')
    op.drop_index('idx_directors_position', table_name='ofdata_directors')
    op.drop_index('idx_directors_legal_entity_id', table_name='ofdata_directors')
    op.drop_index('idx_directors_inn', table_name='ofdata_directors')
    op.drop_index('idx_legal_entities_status', table_name='ofdata_legal_entities')
    op.drop_index('idx_legal_entities_okved_code', table_name='ofdata_legal_entities')
    op.drop_index('idx_legal_entities_region_code', table_name='ofdata_legal_entities')
    op.drop_index('idx_legal_entities_ogrn', table_name='ofdata_legal_entities')
    op.drop_index('idx_legal_entities_inn', table_name='ofdata_legal_entities')
    op.drop_index('idx_addresses_city', table_name='ofdata_addresses')
    op.drop_index('idx_addresses_region', table_name='ofdata_addresses')
    op.drop_index('idx_founder_types_code', table_name='ofdata_founder_types')

    op.drop_table('pipeline_metrics')
    op.drop_table('ofdata_founders')
    op.drop_table('ofdata_directors')
    op.drop_table('ofdata_legal_entities')
    op.drop_table('ofdata_addresses')
    op.drop_table('ofdata_founder_types')
