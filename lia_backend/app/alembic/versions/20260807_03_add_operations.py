"""add professionals, scheduling operations, waitlist and payments"""

from alembic import op
import sqlalchemy as sa

revision = "20260807_03"
down_revision = "20260807_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("profissionais", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("nome", sa.String(), nullable=False), sa.Column("email", sa.String(), nullable=True), sa.Column("telefone", sa.String(), nullable=True), sa.Column("especialidade", sa.String(), nullable=True), sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("data_criacao", sa.DateTime(), nullable=False))
    op.create_table("horarios_profissionais", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("profissional_id", sa.Integer(), sa.ForeignKey("profissionais.id"), nullable=False), sa.Column("weekday", sa.Integer(), nullable=False), sa.Column("inicio", sa.Time(), nullable=False), sa.Column("fim", sa.Time(), nullable=False))
    op.create_table("bloqueios_agenda", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("inicio", sa.DateTime(), nullable=False), sa.Column("fim", sa.DateTime(), nullable=False), sa.Column("motivo", sa.String(), nullable=False), sa.Column("profissional_id", sa.Integer(), sa.ForeignKey("profissionais.id"), nullable=True))
    op.create_table("lista_espera", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clientes.id"), nullable=False), sa.Column("procedimento_id", sa.Integer(), sa.ForeignKey("procedimentos.id"), nullable=False), sa.Column("data_preferida", sa.DateTime(), nullable=True), sa.Column("status", sa.String(), nullable=False, server_default="aguardando"), sa.Column("data_criacao", sa.DateTime(), nullable=False))
    op.create_table("pagamentos", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("agendamento_id", sa.Integer(), sa.ForeignKey("agendamentos.id"), nullable=False), sa.Column("valor", sa.Float(), nullable=False), sa.Column("forma", sa.String(), nullable=False), sa.Column("status", sa.String(), nullable=False, server_default="pago"), sa.Column("pago_em", sa.DateTime(), nullable=False))


def downgrade() -> None:
    op.drop_table("pagamentos")
    op.drop_table("lista_espera")
    op.drop_table("bloqueios_agenda")
    op.drop_table("horarios_profissionais")
    op.drop_table("profissionais")
