"""create_gold_temp_tables

Revision ID: b6c61e371340
Revises: 
Create Date: 2026-05-18 11:50:52.144466

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP


# revision identifiers, used by Alembic.
revision: str = 'b6c61e371340'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'ofdata_gold_entities',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('inn', sa.String(20), unique=True, nullable=False),
        sa.Column('ogrn', sa.String(20)),
        sa.Column('kpp', sa.String(10)),
        sa.Column('short_name', sa.String(255)),
        sa.Column('full_name', sa.Text),
        sa.Column('reg_date', sa.Date),
        sa.Column('status', sa.String(255)),
        sa.Column('okved_code', sa.String(20)),
        sa.Column('created_at', TIMESTAMP(precision=0), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', TIMESTAMP(precision=0), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_table(
        'dadata_gold_entities',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('inn', sa.String(12), unique=True, nullable=False),
        sa.Column('ogrn', sa.String(15)),
        sa.Column('kpp', sa.String(9)),
        sa.Column('short_name', sa.String(255)),
        sa.Column('company_name', sa.String(500)),
        sa.Column('status', sa.String(50)),
        sa.Column('registration_date', TIMESTAMP(precision=0)),
        sa.Column('okved_code', sa.String(20)),
        sa.Column('created_at', TIMESTAMP(precision=0), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', TIMESTAMP(precision=0), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_index('idx_dadata_inn', 'dadata_gold_entities', ['inn'])
    op.create_index('idx_ofdata_inn', 'ofdata_gold_entities', ['inn'])



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('dadata_gold_entities')
    op.drop_table('ofdata_gold_entities')
