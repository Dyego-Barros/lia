"""mark no-show appointments as unpaid

Revision ID: 20260909_10
Revises: 20260908_09
"""

from alembic import op


revision = "20260909_10"
down_revision = "20260908_09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE agendamentos
        SET status_pagamento = 'nao_pago', forma_pagamento = NULL
        WHERE status = 'nao_compareceu'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE agendamentos
        SET status_pagamento = 'pendente'
        WHERE status = 'nao_compareceu' AND status_pagamento = 'nao_pago'
        """
    )
