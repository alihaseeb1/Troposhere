"""add approver to memberships

Revision ID: 3a45fada884b
Revises: 710e4d6a1c6d
Create Date: 2025-10-07 19:37:03.246580

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a45fada884b'
down_revision: Union[str, Sequence[str], None] = '710e4d6a1c6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.add_column("memberships", sa.Column("approver", sa.Integer(), sa.ForeignKey("users.id")))

def downgrade():
    op.drop_column("memberships", "approver")