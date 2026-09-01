"""add configurable whatsapp and ai integrations and conversation inbox"""

from alembic import op
import sqlalchemy as sa

revision = "20260807_05"
down_revision = "20260807_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("whatsapp_integrations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("credenciais_encriptadas", sa.Text(), nullable=False),
        sa.Column("webhook_token_encriptado", sa.Text(), nullable=True),
        sa.Column("prioridade", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("data_criacao", sa.DateTime(), nullable=False),
    )
    op.create_table("ai_integrations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("modelo", sa.String(), nullable=False),
        sa.Column("base_url", sa.String(), nullable=True),
        sa.Column("api_key_encriptada", sa.Text(), nullable=False),
        sa.Column("prioridade", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("data_criacao", sa.DateTime(), nullable=False),
    )
    op.create_table("whatsapp_conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("integration_id", sa.Integer(), sa.ForeignKey("whatsapp_integrations.id"), nullable=False),
        sa.Column("telefone", sa.String(), nullable=False),
        sa.Column("nome_contato", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="aberta"),
        sa.Column("ultima_mensagem_em", sa.DateTime(), nullable=False),
    )
    op.create_table("whatsapp_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("whatsapp_conversations.id"), nullable=False),
        sa.Column("external_id", sa.String(), nullable=True),
        sa.Column("direcao", sa.String(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False, server_default="text"),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("enviado_em", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("whatsapp_messages")
    op.drop_table("whatsapp_conversations")
    op.drop_table("ai_integrations")
    op.drop_table("whatsapp_integrations")
