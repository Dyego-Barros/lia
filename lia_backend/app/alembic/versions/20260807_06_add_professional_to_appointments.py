"""link appointments to professionals"""

from alembic import op
import sqlalchemy as sa

revision = "20260807_06"
down_revision = "20260807_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agendamentos", sa.Column("profissional_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_agendamentos_profissional", "agendamentos", "profissionais", ["profissional_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_agendamentos_profissional", "agendamentos", type_="foreignkey")
    op.drop_column("agendamentos", "profissional_id")
