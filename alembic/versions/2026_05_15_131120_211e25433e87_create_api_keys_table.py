"""create_api_keys_table

Revision ID: 211e25433e87
Revises: 
Create Date: 2026-05-15 13:11:20.385969

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP


# revision identifiers, used by Alembic.
revision: str = '211e25433e87'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'api_keys',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('service_name', sa.String(50), nullable=False),
        sa.Column('api_key', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('daily_limit', sa.Integer(), nullable=True),
        sa.Column('used_today', sa.Integer(), nullable=False, default=0),
        sa.Column('last_used_at', TIMESTAMP, nullable=True),
        sa.Column('created_at', TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    op.create_index('idx_api_keys_service_name', 'api_keys', ['service_name'])
    op.create_index('idx_api_keys_is_active', 'api_keys', ['is_active'])
    op.create_index('uq_api_keys_service_key', 'api_keys', ['service_name', 'api_key'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_api_keys_service_key', table_name='api_keys')
    op.drop_index('idx_api_keys_is_active', table_name='api_keys')
    op.drop_index('idx_api_keys_service_name', table_name='api_keys')
    op.drop_table('api_keys')