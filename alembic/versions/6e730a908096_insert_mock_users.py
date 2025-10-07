"""insert mock users

Revision ID: 6e730a908096
Revises: 8017d604f8e9
Create Date: 2025-10-07 19:27:16.204458

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e730a908096'
down_revision: Union[str, Sequence[str], None] = '8017d604f8e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO users (email, name, created_at, provider_id, provider, picture, global_role)
        VALUES 
        ('6522780863@g.siit.tu.ac.th', 'Nawasawan Yenrompho', now(), '116354586614762566604', 'google', 
         'https://lh3.googleusercontent.com/a/ACg8ocLpwngsL77NVUBskHW4IUbl8XPPVCNUwtbyi99FwHUVWTMp1A=s96-c', 0),
        ('admin@siit.tu.ac.th', 'Admin User', now(), '123456789012345678901', 'google',
         'https://cdn-icons-png.flaticon.com/512/3135/3135715.png', 1);
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM users"))
