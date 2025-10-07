"""create item_borrowing_request table

Revision ID: 373a0dcf71c4
Revises: 54dfddca1528
Create Date: 2025-10-07 18:17:43.347653
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '373a0dcf71c4'
down_revision: Union[str, Sequence[str], None] = '54dfddca1528'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'item_borrowing_requests',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('item_id', sa.Integer, sa.ForeignKey('items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('borrower_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('return_date', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now() + interval '7 days'")),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('item_borrowing_requests')