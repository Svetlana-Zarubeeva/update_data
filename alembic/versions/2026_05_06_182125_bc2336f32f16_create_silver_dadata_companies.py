"""create silver_dadata_companies

Revision ID: bc2336f32f16
Revises: 
Create Date: 2026-05-06 18:21:25.473269

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'bc2336f32f16'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'silver_dadata_companies',
        sa.Column('inn', sa.String(12), primary_key=True, nullable=False),
        sa.Column('ogrn', sa.String(15)),
        sa.Column('company_name', sa.String(500)),
        sa.Column('short_name', sa.String(255)),
        sa.Column('kpp', sa.String(9)),
        sa.Column('status', sa.String(50)),
        sa.Column('registration_date', sa.TIMESTAMP),
        sa.Column('actuality_date', sa.TIMESTAMP),
        sa.Column('address_full', sa.Text),
        sa.Column('postal_code', sa.String(10)),
        sa.Column('region', sa.String(100)),
        sa.Column('city', sa.String(100)),
        sa.Column('street', sa.String(255)),
        sa.Column('house', sa.String(50)),
        sa.Column('flat', sa.String(50)),
        sa.Column('latitude', sa.Float),
        sa.Column('longitude', sa.Float),
        sa.Column('phones', JSONB),
        sa.Column('emails', JSONB),
        sa.Column('websites', JSONB),
        sa.Column('employee_count', sa.Integer),
        sa.Column('revenue', sa.Float),
        sa.Column('income', sa.Float),
        sa.Column('expense', sa.Float),
        sa.Column('tax_system', sa.String(10)),
        sa.Column('management_name', sa.String(255)),
        sa.Column('management_post', sa.String(255)),
        sa.Column('management_start_date', sa.TIMESTAMP),
        sa.Column('okved_main', sa.String(20)),
        sa.Column('okveds', JSONB),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        schema='silver'
    )
    
    op.create_index('silver_dadata_companies_inn_idx', 'silver_dadata_companies', ['inn'], schema='silver')
    op.create_index('silver_dadata_companies_ogrn_idx', 'silver_dadata_companies', ['ogrn'], schema='silver')
    op.create_index('silver_dadata_companies_status_idx', 'silver_dadata_companies', ['status'], schema='silver')
    op.create_index('silver_dadata_companies_region_idx', 'silver_dadata_companies', ['region'], schema='silver')
    op.create_index('silver_dadata_companies_city_idx', 'silver_dadata_companies', ['city'], schema='silver')
    op.create_index('silver_dadata_companies_okved_main_idx', 'silver_dadata_companies', ['okved_main'], schema='silver')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('silver_dadata_companies', schema='silver')