"""add payment fields to appointments"""

from alembic import op
import sqlalchemy as sa

revision = "20260807_02"
down_revision = "20260807_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agendamentos", sa.Column("valor_cobrado", sa.Float(), nullable=True))
    op.add_column("agendamentos", sa.Column("forma_pagamento", sa.String(), nullable=True))
    op.add_column("agendamentos", sa.Column("status_pagamento", sa.String(), nullable=False, server_default="pendente"))


def downgrade() -> None:
    op.drop_column("agendamentos", "status_pagamento")
    op.drop_column("agendamentos", "forma_pagamento")
    op.drop_column("agendamentos", "valor_cobrado")
