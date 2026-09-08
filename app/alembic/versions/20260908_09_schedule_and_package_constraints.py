"""Add integrity constraints for professional schedules and package items.

Revision ID: 20260908_09
Revises: 20260809_08
Create Date: 2026-09-08
"""

from alembic import op


revision = "20260908_09"
down_revision = "20260809_08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_horarios_profissionais_profissional_weekday",
        "horarios_profissionais",
        ["profissional_id", "weekday"],
    )
    op.create_unique_constraint(
        "uq_pacotes_procedimentos_pacote_procedimento",
        "pacotes_procedimentos",
        ["pacote_id", "procedimento_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_pacotes_procedimentos_pacote_procedimento", "pacotes_procedimentos", type_="unique")
    op.drop_index("ix_horarios_profissionais_profissional_weekday", table_name="horarios_profissionais")
