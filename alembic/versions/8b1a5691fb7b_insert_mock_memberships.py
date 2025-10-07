"""insert mock memberships

Revision ID: 8b1a5691fb7b
Revises: 3a45fada884b
Create Date: 2025-10-07 19:55:08.083658

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b1a5691fb7b'
down_revision: Union[str, Sequence[str], None] = '3a45fada884b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()

    # Insert mock membership records
    conn.execute(sa.text("""
        INSERT INTO memberships (user_id, club_id, role, joined_at, approver)
        VALUES
        (1, 1, 1, now(), 2);
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        DELETE FROM memberships
        WHERE (user_id, club_id) IN ((1,1), (2,1), (3,2), (4,2));
    """))

