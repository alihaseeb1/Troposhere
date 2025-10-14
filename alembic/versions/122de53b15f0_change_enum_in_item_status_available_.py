"""Change enum in item status (available/unavailable) to upper case

Revision ID: 122de53b15f0
Revises: b997c76f8895
Create Date: 2025-10-14 00:51:48.744679

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '122de53b15f0'
down_revision: Union[str, Sequence[str], None] = 'b997c76f8895'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


"""Shrink itemstatus to two values: available/unavailable

Revision ID: b997c76f8895
Revises: 3195e202ddc9
Create Date: 2025-10-14 00:43:48.875207

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b997c76f8895'
down_revision: Union[str, Sequence[str], None] = '3195e202ddc9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()

    op.execute("ALTER TYPE itemstatus RENAME TO itemstatus_old;")
    op.execute("CREATE TYPE itemstatus AS ENUM ('AVAILABLE', 'UNAVAILABLE');")
    op.execute("ALTER TABLE items ALTER COLUMN status DROP DEFAULT;")
    op.execute("""
        ALTER TABLE items
        ALTER COLUMN status TYPE itemstatus
        USING (
            CASE
              WHEN LOWER(status::text) = 'available' THEN 'AVAILABLE'::itemstatus
              ELSE 'UNAVAILABLE'::itemstatus
            END
        );
    """)
    op.execute("ALTER TABLE items ALTER COLUMN status SET DEFAULT 'AVAILABLE';")
    op.execute("DROP TYPE itemstatus_old;")


def downgrade():
    op.execute("CREATE TYPE itemstatus_old AS ENUM ('available', 'unavailable');")

    op.execute("ALTER TABLE items ALTER COLUMN status DROP DEFAULT;")

    op.execute("""
        ALTER TABLE items
        ALTER COLUMN status TYPE itemstatus_old
        USING (
            CASE
              WHEN status::text = 'AVAILABLE' THEN 'available'::itemstatus_old
              ELSE 'unavailable'::itemstatus_old
            END
        );
    """)

    op.execute("ALTER TABLE items ALTER COLUMN status SET DEFAULT 'available';")

    op.execute("ALTER TYPE itemstatus RENAME TO itemstatus_new;")
    op.execute("ALTER TYPE itemstatus_old RENAME TO itemstatus;")
    op.execute("DROP TYPE itemstatus_new;")
