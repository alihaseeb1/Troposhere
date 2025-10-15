"""Convert items.status column from VARCHAR to ENUM

Revision ID: 302d4c5d0fd1
Revises: a79732a57455
Create Date: 2025-10-13 23:24:22.933276

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '302d4c5d0fd1'
down_revision: Union[str, Sequence[str], None] = 'a79732a57455'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1. Create ENUM type if it doesn't exist
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_type t
            JOIN pg_namespace n ON n.oid = t.typnamespace
            WHERE t.typname = 'itemstatus' AND n.nspname = 'public'
        ) THEN
            CREATE TYPE public.itemstatus AS ENUM (
                'available',
                'out_of_service',
                'pending_borrowal',
                'borrowed',
                'pending_return'
            );
        END IF;
    END$$;
    """)

    # Step 2. Drop default temporarily
    op.execute("ALTER TABLE public.items ALTER COLUMN status DROP DEFAULT;")

    # Step 3. Convert VARCHAR → ENUM (case-insensitive cast)
    op.execute("""
        ALTER TABLE public.items
        ALTER COLUMN status
        TYPE public.itemstatus
        USING lower(status::text)::public.itemstatus;
    """)

    # Step 4. Set default to 'available'
    op.execute("ALTER TABLE public.items ALTER COLUMN status SET DEFAULT 'available';")


def downgrade() -> None:
    # Convert back to VARCHAR and drop ENUM
    op.execute("ALTER TABLE public.items ALTER COLUMN status DROP DEFAULT;")
    op.execute("""
        ALTER TABLE public.items
        ALTER COLUMN status TYPE varchar USING status::text;
    """)
    op.execute("ALTER TABLE public.items ALTER COLUMN status SET DEFAULT 'available';")

    op.execute("DROP TYPE IF EXISTS public.itemstatus;")
