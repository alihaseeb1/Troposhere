"""add qr_code column to items table

Revision ID: a79732a57455
Revises: 65a1ab6ee3a3
Create Date: 2025-10-13 22:29:50.391654

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a79732a57455'
down_revision: Union[str, Sequence[str], None] = '65a1ab6ee3a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('items', sa.Column('qr_code', sa.String(), nullable=True))

    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT id FROM items ORDER BY id"))
    rows = result.fetchall()

    start_qr = 100000 
    for i, row in enumerate(rows, start=1):
        qr_number = str(start_qr + i)
        conn.execute(sa.text("UPDATE items SET qr_code = :qr WHERE id = :id"), {"qr": qr_number, "id": row[0]})

    op.alter_column('items', 'qr_code', nullable=False)
    op.create_unique_constraint('uq_items_qr_code', 'items', ['qr_code'])


def downgrade() -> None:
    op.drop_constraint('uq_items_qr_code', 'items', type_='unique')
    op.drop_column('items', 'qr_code')
