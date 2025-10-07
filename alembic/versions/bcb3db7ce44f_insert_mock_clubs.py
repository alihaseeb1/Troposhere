"""insert mock clubs

Revision ID: bcb3db7ce44f
Revises: 6e730a908096
Create Date: 2025-10-07 19:28:40.917169

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bcb3db7ce44f'
down_revision: Union[str, Sequence[str], None] = '6e730a908096'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO clubs (name, description, created_at)
        VALUES
        ('Robotics Club', 'For building robots and automation projects.', now()),
        ('Photography Club', 'For photo lovers and camera enthusiasts.', now())
    """))

def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM clubs"))
