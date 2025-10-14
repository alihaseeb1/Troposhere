"""Upgrade enum to uppecase

Revision ID: 8e041e43deb5
Revises: 2653d1161a5d
Create Date: 2025-10-14 00:12:57.648320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e041e43deb5'
down_revision: Union[str, Sequence[str], None] = '2653d1161a5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1️⃣ Rename old enum
    op.execute("ALTER TYPE itemstatus RENAME TO itemstatus_old;")

    # 2️⃣ Create new uppercase enum
    op.execute("""
        CREATE TYPE itemstatus AS ENUM (
            'AVAILABLE',
            'OUT_OF_SERVICE',
            'PENDING_BORROWAL',
            'BORROWED',
            'PENDING_RETURN'
        );
    """)

    # 3️⃣ Update the table column to use new enum with uppercase values
    op.execute("""
        ALTER TABLE items
            ALTER COLUMN status DROP DEFAULT,
            ALTER COLUMN status TYPE itemstatus
            USING UPPER(status::text)::itemstatus;
    """)

    # 4️⃣ Set default back to AVAILABLE
    op.execute("ALTER TABLE items ALTER COLUMN status SET DEFAULT 'AVAILABLE';")

    # 5️⃣ Drop the old enum type
    op.execute("DROP TYPE itemstatus_old;")

def downgrade():
    # Revert back to lowercase enum if needed
    op.execute("ALTER TYPE itemstatus RENAME TO itemstatus_new;")
    op.execute("""
        CREATE TYPE itemstatus AS ENUM (
            'available',
            'out_of_service',
            'pending_borrowal',
            'borrowed',
            'pending_return'
        );
    """)
    op.execute("""
        ALTER TABLE items
            ALTER COLUMN status DROP DEFAULT,
            ALTER COLUMN status TYPE itemstatus
            USING LOWER(status::text)::itemstatus;
    """)
    op.execute("ALTER TABLE items ALTER COLUMN status SET DEFAULT 'available';")
    op.execute("DROP TYPE itemstatus_new;")