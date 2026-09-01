"""add material cost to procedures"""

from alembic import op
import sqlalchemy as sa

revision = "20260809_08"
down_revision = "20260807_07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("procedimentos", sa.Column("custo_materiais", sa.Float(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("procedimentos", "custo_materiais")
