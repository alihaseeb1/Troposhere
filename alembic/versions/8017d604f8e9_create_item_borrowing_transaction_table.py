
"""create item_borrowing_transaction table with operator_id

Revision ID: 8017d604f8e9
Revises: 373a0dcf71c4
Create Date: 2025-10-07 18:22:56.417295
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '8017d604f8e9'
down_revision: Union[str, Sequence[str], None] = '373a0dcf71c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'item_borrowing_transaction',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('req_id', sa.Integer, sa.ForeignKey('item_borrowing_request.id'), nullable=False),
        sa.Column('tstamp', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('operator_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('status', sa.String(), nullable=False)
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('item_borrowing_transaction')
