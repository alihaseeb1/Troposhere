"""Upgrade enum in item borrowing transactions to uppercase

Revision ID: 3195e202ddc9
Revises: 8e041e43deb5
Create Date: 2025-10-14 00:15:48.992441

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3195e202ddc9'
down_revision: Union[str, Sequence[str], None] = '8e041e43deb5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    op.execute("ALTER TYPE borrowstatus RENAME TO borrowstatus_old;")

    op.execute("""
        CREATE TYPE borrowstatus AS ENUM (
            'PENDING_APPROVAL',
            'APPROVED',
            'PENDING_CONDITION_CHECK',
            'COMPLETED',
            'REJECTED'
        );
    """)

    op.execute("""
        ALTER TABLE item_borrowing_transactions
            ALTER COLUMN status DROP DEFAULT,
            ALTER COLUMN status TYPE borrowstatus
            USING UPPER(status::text)::borrowstatus;
    """)

    op.execute("ALTER TABLE item_borrowing_transactions ALTER COLUMN status SET DEFAULT 'PENDING_APPROVAL';")

    op.execute("DROP TYPE borrowstatus_old;")


def downgrade():
    # Reverse migration (uppercase → lowercase)
    op.execute("ALTER TYPE borrowstatus RENAME TO borrowstatus_new;")

    op.execute("""
        CREATE TYPE borrowstatus AS ENUM (
            'pending_approval',
            'approved',
            'pending_condition_check',
            'completed',
            'rejected'
        );
    """)

    op.execute("""
        ALTER TABLE item_borrowing_transactions
            ALTER COLUMN status DROP DEFAULT,
            ALTER COLUMN status TYPE borrowstatus
            USING LOWER(status::text)::borrowstatus;
    """)

    op.execute("ALTER TABLE item_borrowing_transactions ALTER COLUMN status SET DEFAULT 'pending_approval';")

    op.execute("DROP TYPE borrowstatus_new;")