"""gis_migration

Revision ID: 55376fa327b8
Revises: 058accec9aa2
Create Date: 2025-08-20 11:06:41.242817

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "55376fa327b8"
down_revision: Union[str, Sequence[str], None] = "058accec9aa2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = "5fbd82629c7f"


def upgrade():
    op.execute("ALTER TABLE building ADD COLUMN coordinates geometry(Point, 4326)")

    op.execute(
        """
        UPDATE building
        SET coordinates = ST_SetSRID(ST_MakePoint(lat, long), 4326)
        WHERE lat IS NOT NULL AND long IS NOT NULL
        """
    )

    op.execute(
        "CREATE INDEX idx_building_coordinates ON building USING GIST (coordinates)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_building_coordinates")
    op.execute("ALTER TABLE building DROP COLUMN coordinates")
