"""Insert Mock Item

Revision ID: f305b805f415
Revises: 26bb114e50a4
Create Date: 2025-10-14 23:52:07.804770

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f305b805f415'
down_revision: Union[str, Sequence[str], None] = '26bb114e50a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO items (name, description, status, club_id, is_high_risk, qr_code)
        VALUES
            ('3D Printer', 'Prusa i3 MK3S for rapid prototyping', 'AVAILABLE', 2, FALSE, '200001'),
            ('Arduino Kit', 'Arduino Uno R3 complete starter set', 'AVAILABLE', 2, FALSE, '200002'),
            ('GoPro Camera', 'GoPro Hero 11 action camera', 'AVAILABLE', 2, FALSE, '200003'),
            ('Tripod', 'Professional adjustable aluminum tripod', 'AVAILABLE', 2, FALSE, '200004'),
            ('Wireless Mic', 'Rode Wireless Go II microphone set', 'AVAILABLE', 2, FALSE, '200005'),
            ('Projector', 'BenQ full-HD projector', 'AVAILABLE', 2, FALSE, '200006'),
            ('Light Stand', 'Adjustable LED light stand', 'AVAILABLE', 2, FALSE, '200007'),
            ('Monitor', 'Dell 24-inch monitor', 'AVAILABLE', 2, FALSE, '200008'),
            ('Power Supply', 'Adjustable DC power supply 30V 10A', 'AVAILABLE', 2, FALSE, '200009'),
            ('Oscilloscope', 'Digital 2-channel oscilloscope', 'AVAILABLE', 2, FALSE, '200010');
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        DELETE FROM items
        WHERE club_id = 2 AND qr_code BETWEEN '200001' AND '200010';
    """))