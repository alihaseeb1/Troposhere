"""insert mock items

Revision ID: ffc5b46a03a2
Revises: bcb3db7ce44f
Create Date: 2025-10-07 19:31:24.545322

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ffc5b46a03a2'
down_revision: Union[str, Sequence[str], None] = 'bcb3db7ce44f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO items (name, description, club_id, is_high_risk, status, created_at)
        VALUES
        ('Robot Arm Kit', 'Robotics training set', 1, false, 'available', now()),
        ('DSLR Camera', 'Canon EOS 80D', 2, true, 'available', now())
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM items"))
