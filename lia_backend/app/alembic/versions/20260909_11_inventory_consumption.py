"""link procedures to inventory and snapshot consumption"""
from alembic import op
import sqlalchemy as sa

revision = "20260909_11"
down_revision = "20260909_10"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.alter_column("estoque_produtos", "quantidade", existing_type=sa.Integer(), type_=sa.Float(), postgresql_using="quantidade::double precision")
    op.create_table("procedimentos_materiais", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("procedimento_id", sa.Integer(), sa.ForeignKey("procedimentos.id"), nullable=False), sa.Column("produto_id", sa.Integer(), sa.ForeignKey("estoque_produtos.id"), nullable=False), sa.Column("quantidade", sa.Float(), nullable=False), sa.UniqueConstraint("procedimento_id", "produto_id", name="uq_procedimento_material"))
    op.create_table("consumos_materiais", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("agendamento_id", sa.Integer(), sa.ForeignKey("agendamentos.id"), nullable=False), sa.Column("produto_id", sa.Integer(), sa.ForeignKey("estoque_produtos.id"), nullable=False), sa.Column("quantidade", sa.Float(), nullable=False), sa.Column("custo_unitario", sa.Float(), nullable=False), sa.UniqueConstraint("agendamento_id", "produto_id", name="uq_consumo_agendamento_produto"))

def downgrade() -> None:
    op.drop_table("consumos_materiais"); op.drop_table("procedimentos_materiais")
    op.alter_column("estoque_produtos", "quantidade", existing_type=sa.Float(), type_=sa.Integer(), postgresql_using="quantidade::integer")
