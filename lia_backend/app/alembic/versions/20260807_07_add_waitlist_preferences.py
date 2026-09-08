"""add waitlist period and professional preferences"""

from alembic import op
import sqlalchemy as sa

revision = "20260807_07"
down_revision = "20260807_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("lista_espera", sa.Column("periodo", sa.String(), nullable=True))
    op.add_column("lista_espera", sa.Column("profissional_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_lista_espera_profissional", "lista_espera", "profissionais", ["profissional_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_lista_espera_profissional", "lista_espera", type_="foreignkey")
    op.drop_column("lista_espera", "profissional_id")
    op.drop_column("lista_espera", "periodo")
