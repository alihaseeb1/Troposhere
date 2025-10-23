"""add image path column to club

Revision ID: cc2003f0be37
Revises: c8068e9970a8
Create Date: 2025-10-22 13:33:33.803726

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc2003f0be37'
down_revision: Union[str, Sequence[str], None] = 'c8068e9970a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('clubs', sa.Column('image_path', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('clubs', 'image_path')
