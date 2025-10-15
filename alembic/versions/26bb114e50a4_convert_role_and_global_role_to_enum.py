"""Convert role and global_role to ENUM

Revision ID: 26bb114e50a4
Revises: 278f22327585
Create Date: 2025-10-14 23:49:52.047148

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26bb114e50a4'
down_revision: Union[str, Sequence[str], None] = '278f22327585'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # --- Define ENUM types ---
    global_roles_enum = sa.Enum('USER', 'SUPERUSER', name='globalroles')
    club_roles_enum = sa.Enum('MEMBER', 'MODERATOR', 'ADMIN', name='clubroles')

    # --- Create ENUMs in DB ---
    global_roles_enum.create(op.get_bind(), checkfirst=True)
    club_roles_enum.create(op.get_bind(), checkfirst=True)

    # --- Alter tables ---
    op.alter_column(
        'users', 'global_role',
        existing_type=sa.Integer(),
        type_=global_roles_enum,
        postgresql_using=(
            "CASE "
            "WHEN global_role = 0 THEN 'USER' "
            "WHEN global_role = 1 THEN 'SUPERUSER' "
            "END::globalroles"
        )
    )

    op.alter_column(
        'memberships', 'role',
        existing_type=sa.Integer(),
        type_=club_roles_enum,
        postgresql_using=(
            "CASE "
            "WHEN role = 1 THEN 'MEMBER' "
            "WHEN role = 2 THEN 'MODERATOR' "
            "WHEN role = 3 THEN 'ADMIN' "
            "END::clubroles"
        )
    )


def downgrade():
    op.alter_column(
        'users', 'global_role',
        existing_type=sa.Enum('USER', 'SUPERUSER', name='globalroles'),
        type_=sa.Integer(),
        postgresql_using=(
            "CASE "
            "WHEN global_role = 'USER' THEN 0 "
            "WHEN global_role = 'SUPERUSER' THEN 1 "
            "END::integer"
        )
    )

    op.alter_column(
        'memberships', 'role',
        existing_type=sa.Enum('MEMBER', 'MODERATOR', 'ADMIN', name='clubroles'),
        type_=sa.Integer(),
        postgresql_using=(
            "CASE "
            "WHEN role = 'MEMBER' THEN 1 "
            "WHEN role = 'MODERATOR' THEN 2 "
            "WHEN role = 'ADMIN' THEN 3 "
            "END::integer"
        )
    )

    # Drop ENUMs
    sa.Enum('USER', 'SUPERUSER', name='globalroles').drop(op.get_bind(), checkfirst=True)
    sa.Enum('MEMBER', 'MODERATOR', 'ADMIN', name='clubroles').drop(op.get_bind(), checkfirst=True)
