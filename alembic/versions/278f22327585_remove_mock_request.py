"""remove mock request

Revision ID: 278f22327585
Revises: 1d34dcc1109b
Create Date: 2025-10-14 23:47:34.670522

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '278f22327585'
down_revision: Union[str, Sequence[str], None] = '1d34dcc1109b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        DELETE FROM item_borrowing_requests
        WHERE id IN (1, 2);
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO item_borrowing_requests (id, item_id, borrower_id, return_date, created_at)
        VALUES 
            (1, 1, 1, now() + interval '7 day', now()),
            (2, 2, 2, now() + interval '3 day', now());
    """))
