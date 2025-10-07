"""create logging table

Revision ID: 54dfddca1528
Revises: d3b17db42289
Create Date: 2025-10-07 18:12:28.278965
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '54dfddca1528'
down_revision: Union[str, Sequence[str], None] = 'd3b17db42289'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'logging',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('tstamp', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('tablename', sa.Text, nullable=False),
        sa.Column('operation', sa.Text, nullable=False),
        sa.Column('who', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('new_val', sa.JSON, nullable=False),
        sa.Column('old_val', sa.JSON, nullable=False)
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('logging')
