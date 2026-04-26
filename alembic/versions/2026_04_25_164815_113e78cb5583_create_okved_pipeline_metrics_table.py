"""create_okved_pipeline_metrics_table

Revision ID: 113e78cb5583
Revises: 
Create Date: 2026-04-25 16:48:14.991310

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '113e78cb5583'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'okved_pipeline_metrics',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('pipeline_name', sa.String(255), nullable=False),
        sa.Column('downloaded_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('written_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
    )


def downgrade() -> None:
    """Downgrade schema."""    
    op.drop_table('okved_pipeline_metrics')
