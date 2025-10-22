"""create item images table

Revision ID: d758b9f43987
Revises: cc2003f0be37
Create Date: 2025-10-22 13:34:32.175136

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd758b9f43987'
down_revision: Union[str, Sequence[str], None] = 'cc2003f0be37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'item_images',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('item_id', sa.Integer(), sa.ForeignKey('items.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('image_url', sa.String(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('item_images')