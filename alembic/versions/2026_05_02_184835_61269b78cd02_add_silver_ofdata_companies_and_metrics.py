"""add_silver_ofdata_companies_and_metrics

Revision ID: 61269b78cd02
Revises: 
Create Date: 2026-05-02 18:48:35.337958

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP


# revision identifiers, used by Alembic.
revision: str = '61269b78cd02'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'silver_ofdata_companies',
        sa.Column('inn', sa.String(length=20), nullable=False, primary_key=True),
        sa.Column('ogrn', sa.String(length=20), nullable=True),
        sa.Column('kpp', sa.String(length=10), nullable=True),
        sa.Column('short_name', sa.String(length=255), nullable=True),
        sa.Column('full_name', sa.Text(), nullable=True),
        sa.Column('reg_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=255), nullable=True),
        sa.Column('region_code', sa.String(length=10), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('okved_code', sa.String(length=20), nullable=True),
        sa.Column('okved_description', sa.Text(), nullable=True),
        sa.Column('directors', JSONB(), nullable=True),
        sa.Column('founders', JSONB(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        schema='silver'
    )
    
    op.create_index('silver_ofdata_companies_status_idx', 'silver_ofdata_companies', ['status'], schema='silver')
    op.create_index('silver_ofdata_companies_region_code_idx', 'silver_ofdata_companies', ['region_code'], schema='silver')
    op.create_index('silver_ofdata_companies_okved_code_idx', 'silver_ofdata_companies', ['okved_code'], schema='silver')

    op.create_table(
        'silver_pipeline_metrics',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('pipeline_name', sa.String(length=50), nullable=False, server_default='silver'),
        sa.Column('total_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('new_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id', name='silver_pipeline_metrics_pkey'),
        schema='silver'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('silver_pipeline_metrics', schema='silver')
    op.drop_table('silver_ofdata_companies', schema='silver')
