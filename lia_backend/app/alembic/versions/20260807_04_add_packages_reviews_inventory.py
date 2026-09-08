"""add packages reviews and inventory"""

from alembic import op
import sqlalchemy as sa

revision = "20260807_04"
down_revision = "20260807_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("pacotes", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("nome", sa.String(), nullable=False), sa.Column("descricao", sa.String(), nullable=True), sa.Column("preco", sa.Float(), nullable=False), sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_table("pacotes_procedimentos", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("pacote_id", sa.Integer(), sa.ForeignKey("pacotes.id"), nullable=False), sa.Column("procedimento_id", sa.Integer(), sa.ForeignKey("procedimentos.id"), nullable=False), sa.Column("quantidade", sa.Integer(), nullable=False, server_default="1"))
    op.create_table("avaliacoes", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("agendamento_id", sa.Integer(), sa.ForeignKey("agendamentos.id"), nullable=False), sa.Column("nota", sa.Integer(), nullable=False), sa.Column("comentario", sa.String(), nullable=True), sa.Column("data_criacao", sa.DateTime(), nullable=False))
    op.create_table("estoque_produtos", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("nome", sa.String(), nullable=False), sa.Column("sku", sa.String(), nullable=True), sa.Column("quantidade", sa.Integer(), nullable=False, server_default="0"), sa.Column("estoque_minimo", sa.Integer(), nullable=False, server_default="0"), sa.Column("custo_unitario", sa.Float(), nullable=False, server_default="0"), sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade() -> None:
    op.drop_table("estoque_produtos")
    op.drop_table("avaliacoes")
    op.drop_table("pacotes_procedimentos")
    op.drop_table("pacotes")
