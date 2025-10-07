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
    conn.execute(sa.text(f"""
        INSERT INTO item_borrowing_request (item_id, issued_date, set_return_date)
        VALUES
        (1, now(), '{(datetime.now() + timedelta(days=7)).isoformat()}'),
        (2, now(), '{(datetime.now() + timedelta(days=3)).isoformat()}')
    """))

def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM item_borrowing_request"))