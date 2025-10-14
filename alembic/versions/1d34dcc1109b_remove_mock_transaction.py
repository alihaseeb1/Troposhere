"""remove mock transaction

Revision ID: 1d34dcc1109b
Revises: b997c76f8895
Create Date: 2025-10-14 23:44:34.561712

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d34dcc1109b'
down_revision: Union[str, Sequence[str], None] = 'b997c76f8895'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        DELETE FROM item_borrowing_transactions
        WHERE remarks IN ('Approved by admin', 'Awaiting condition check');
    """))

def downgrade():
    conn = op.get_bind()
    # (optional) — ถ้าอยากให้สามารถ rollback ได้
    conn.execute(sa.text("""
        INSERT INTO item_borrowing_transactions
        (item_borrowing_request_id, processed_at, operator_id, status, remarks)
        VALUES
        (1, now(), 1, 'approved', 'Approved by admin'),
        (2, now(), 1, 'pending_condition_check', 'Awaiting condition check');
    """))