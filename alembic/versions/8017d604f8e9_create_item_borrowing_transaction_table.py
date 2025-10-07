
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
    op.create_table('item_borrowing_transactions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('item_borrowing_request_id', sa.Integer, sa.ForeignKey('item_borrowing_requests.id', ondelete='CASCADE'),nullable=False),
        sa.Column('processed_at', sa.TIMESTAMP(timezone=True), nullable=False,server_default=sa.text('now()')),
        sa.Column('operator_id',sa.Integer,sa.ForeignKey('users.id', ondelete='SET NULL'),nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('remarks', sa.String(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('item_borrowing_transactions')