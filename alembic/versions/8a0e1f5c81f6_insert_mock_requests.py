"""insert mock requests

Revision ID: 8a0e1f5c81f6
Revises: ffc5b46a03a2
Create Date: 2025-10-07 19:32:06.006414

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta

# revision identifiers, used by Alembic.
revision: str = '8a0e1f5c81f6'
down_revision: Union[str, Sequence[str], None] = 'ffc5b46a03a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()
    return_date_1 = (datetime.now() + timedelta(days=7)).isoformat()
    return_date_2 = (datetime.now() + timedelta(days=3)).isoformat()

    conn.execute(sa.text(f"""
        INSERT INTO item_borrowing_requests (item_id, borrower_id, return_date, created_at)
        VALUES
        (1, 1, '{return_date_1}', now()),
        (2, 2, '{return_date_2}', now());
    """))

def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM item_borrowing_requests"))