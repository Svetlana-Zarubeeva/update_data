"""add okved_it_codes_table

Revision ID: deacbb4893f9
Revises: 
Create Date: 2026-04-25 15:12:51.530478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'deacbb4893f9'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'okved_it_codes',
        sa.Column('okved_code', sa.String(20), primary_key=True),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('section', sa.String(2), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_index('okved_it_codes_section_idx', 'okved_it_codes', ['section'])
    op.create_index('okved_it_codes_okved_code_idx', 'okved_it_codes', ['okved_code'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('okved_it_codes_okved_code_idx')
    op.drop_index('okved_it_codes_section_idx')
    op.drop_table('okved_it_codes')
