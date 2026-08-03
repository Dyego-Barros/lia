"""create initial application tables

Revision ID: 20260803_00
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "20260803_00"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "procedimentos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("descricao", sa.String(), nullable=True),
        sa.Column("preco", sa.Float(), nullable=False),
        sa.Column("duracao", sa.Integer(), nullable=False),
        sa.Column("indicacoes", sa.String(), nullable=True),
        sa.Column("contraindicacoes", sa.String(), nullable=True),
        sa.Column("cuidados", sa.String(), nullable=True),
        sa.Column("data_criacao", sa.DateTime(), nullable=False),
        sa.Column("data_atualizacao", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "clientes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("telefone", sa.String(), nullable=True),
        sa.Column("status", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("data_criacao", sa.DateTime(), nullable=False),
        sa.Column("data_atualizacao", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "agendamentos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clientes.id"), nullable=False),
        sa.Column("procedimento_id", sa.Integer(), sa.ForeignKey("procedimentos.id"), nullable=False),
        sa.Column("data_hora", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pendente"),
        sa.Column("data_criacao", sa.DateTime(), nullable=False),
        sa.Column("data_atualizacao", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "tempos_trabalho",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("data_inicio", sa.DateTime(), nullable=False),
        sa.Column("data_fim", sa.DateTime(), nullable=False),
        sa.Column("data_criacao", sa.DateTime(), nullable=False),
        sa.Column("data_atualizacao", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("agendamentos")
    op.drop_table("tempos_trabalho")
    op.drop_table("clientes")
    op.drop_table("procedimentos")
