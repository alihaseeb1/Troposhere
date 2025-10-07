"""insert mock transaction

Revision ID: 710e4d6a1c6d
Revises: 8a0e1f5c81f6
Create Date: 2025-10-07 19:33:43.258018

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '710e4d6a1c6d'
down_revision: Union[str, Sequence[str], None] = '8a0e1f5c81f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO item_borrowing_transaction (req_id, tstamp, operator_id, status)
        VALUES
        (1, now(), 1, 'borrowed'),
        (2, now(), 1, 'pending')
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM item_borrowing_transaction"))
