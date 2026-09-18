"""separate WhatsApp ingestion from automatic AI replies"""

from alembic import op
import sqlalchemy as sa

revision = "20260918_13"
down_revision = "20260909_12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "whatsapp_integrations",
        sa.Column("ia_ativa", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("whatsapp_integrations", "ia_ativa")
