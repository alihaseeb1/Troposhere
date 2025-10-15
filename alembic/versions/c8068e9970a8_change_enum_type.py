"""Change enum type

Revision ID: c8068e9970a8
Revises: f305b805f415
Create Date: 2025-10-14 23:58:00.881969

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8068e9970a8'
down_revision: Union[str, Sequence[str], None] = 'f305b805f415'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    with op.batch_alter_table("memberships") as batch_op:
        batch_op.alter_column(
            "role",
            existing_type=sa.String(),
            type_=sa.Integer(),
            postgresql_using=(
                "CASE "
                "WHEN role = 'ADMIN' THEN 3 "
                "WHEN role = 'MODERATOR' THEN 2 "
                "WHEN role = 'MEMBER' THEN 1 "
                "ELSE NULL END"
            ),
        )

        batch_op.create_check_constraint(
            "chk_membership_role_valid", "role IN (1, 2, 3)"
        )

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "global_role",
            existing_type=sa.String(),
            type_=sa.Integer(),
            postgresql_using=(
                "CASE "
                "WHEN global_role = 'SUPERUSER' THEN 1 "
                "WHEN global_role = 'USER' THEN 0 "
                "ELSE NULL END"
            ),
        )

        batch_op.create_check_constraint(
            "chk_user_global_role_valid", "global_role IN (0, 1)"
        )


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("chk_user_global_role_valid", type_="check")
        batch_op.alter_column(
            "global_role",
            existing_type=sa.Integer(),
            type_=sa.String(),
            postgresql_using=(
                "CASE "
                "WHEN global_role = 1 THEN 'SUPERUSER' "
                "WHEN global_role = 0 THEN 'USER' "
                "ELSE NULL END"
            ),
        )

    with op.batch_alter_table("memberships") as batch_op:
        batch_op.drop_constraint("chk_membership_role_valid", type_="check")
        batch_op.alter_column(
            "role",
            existing_type=sa.Integer(),
            type_=sa.String(),
            postgresql_using=(
                "CASE "
                "WHEN role = 3 THEN 'ADMIN' "
                "WHEN role = 2 THEN 'MODERATOR' "
                "WHEN role = 1 THEN 'MEMBER' "
                "ELSE NULL END"
            ),
        )
