"""Convert items_borrowing_transactions.status column from VARCHAR to ENUM

Revision ID: 2653d1161a5d
Revises: 302d4c5d0fd1
Create Date: 2025-10-13 23:29:20.663052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2653d1161a5d'
down_revision: Union[str, Sequence[str], None] = '302d4c5d0fd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_type t
            JOIN pg_namespace n ON n.oid = t.typnamespace
            WHERE t.typname = 'borrowstatus' AND n.nspname = 'public'
        ) THEN
            CREATE TYPE public.borrowstatus AS ENUM (
                'pending_approval',
                'approved',
                'pending_condition_check',
                'completed',
                'rejected'
            );
        END IF;
    END$$;
    """)

    op.execute("ALTER TABLE public.item_borrowing_transactions ALTER COLUMN status DROP DEFAULT;")

    op.execute("""
        ALTER TABLE public.item_borrowing_transactions
        ALTER COLUMN status
        TYPE public.borrowstatus
        USING lower(status::text)::public.borrowstatus;
    """)

    op.execute("""
        ALTER TABLE public.item_borrowing_transactions
        ALTER COLUMN status SET DEFAULT 'pending_approval';
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE public.item_borrowing_transactions ALTER COLUMN status DROP DEFAULT;")
    op.execute("""
        ALTER TABLE public.item_borrowing_transactions
        ALTER COLUMN status TYPE varchar USING status::text;
    """)
    op.execute("ALTER TABLE public.item_borrowing_transactions ALTER COLUMN status SET DEFAULT 'pending_approval';")

    op.execute("DROP TYPE IF EXISTS public.borrowstatus;")
