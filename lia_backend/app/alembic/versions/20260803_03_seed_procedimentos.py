"""seed example aesthetic procedures

Revision ID: 20260803_03
Revises: 20260803_02
"""

from datetime import datetime
import os

from alembic import op
import sqlalchemy as sa


revision = "20260803_03"
down_revision = "20260803_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if os.getenv("SEED_DEMO_DATA", "false").lower() != "true":
        return
    procedimentos = sa.table(
        "procedimentos",
        sa.column("nome", sa.String),
        sa.column("descricao", sa.String),
        sa.column("preco", sa.Float),
        sa.column("duracao", sa.Integer),
        sa.column("indicacoes", sa.String),
        sa.column("contraindicacoes", sa.String),
        sa.column("cuidados", sa.String),
        sa.column("data_criacao", sa.DateTime),
        sa.column("data_atualizacao", sa.DateTime),
    )
    agora = datetime.utcnow()

    op.bulk_insert(procedimentos, [
        {
            "nome": "Limpeza de pele",
            "descricao": "Higienização profunda da pele com extração de cravos e aplicação de máscara.",
            "preco": 150.00,
            "duracao": 60,
            "indicacoes": "Pele oleosa, poros obstruídos e necessidade de higienização profunda.",
            "contraindicacoes": "Infecções ativas, feridas abertas ou irritação intensa na pele.",
            "cuidados": "Evitar sol intenso e usar protetor solar após o procedimento.",
            "data_criacao": agora,
            "data_atualizacao": agora,
        },
        {
            "nome": "Peeling químico",
            "descricao": "Aplicação controlada de ativos para renovação e uniformização da pele.",
            "preco": 280.00,
            "duracao": 45,
            "indicacoes": "Manchas superficiais, textura irregular e linhas finas.",
            "contraindicacoes": "Gestação, lactação, herpes ativa ou uso recente de determinados ácidos.",
            "cuidados": "Usar protetor solar e seguir rigorosamente as orientações da profissional.",
            "data_criacao": agora,
            "data_atualizacao": agora,
        },
        {
            "nome": "Microagulhamento facial",
            "descricao": "Procedimento de estímulo da renovação da pele com microperfurações controladas.",
            "preco": 350.00,
            "duracao": 75,
            "indicacoes": "Cicatrizes de acne, textura irregular e linhas finas.",
            "contraindicacoes": "Acne inflamatória ativa, infecções, tendência a queloides ou pele sensibilizada.",
            "cuidados": "Não manipular a pele e evitar exposição solar durante a recuperação.",
            "data_criacao": agora,
            "data_atualizacao": agora,
        },
        {
            "nome": "Drenagem linfática",
            "descricao": "Massagem manual com movimentos suaves para auxiliar a circulação e reduzir retenção de líquidos.",
            "preco": 130.00,
            "duracao": 60,
            "indicacoes": "Retenção de líquidos e sensação de inchaço, conforme avaliação profissional.",
            "contraindicacoes": "Infecções, trombose, insuficiência cardíaca descompensada ou suspeita de doença aguda.",
            "cuidados": "Manter hidratação e informar previamente qualquer condição de saúde.",
            "data_criacao": agora,
            "data_atualizacao": agora,
        },
        {
            "nome": "Botox facial",
            "descricao": "Aplicação de toxina botulínica para suavização de linhas de expressão, mediante avaliação.",
            "preco": 800.00,
            "duracao": 45,
            "indicacoes": "Linhas de expressão em regiões avaliadas pela profissional habilitada.",
            "contraindicacoes": "Gestação, lactação, alergia aos componentes ou doenças neuromusculares específicas.",
            "cuidados": "Seguir as orientações pós-procedimento e não massagear as áreas tratadas sem orientação.",
            "data_criacao": agora,
            "data_atualizacao": agora,
        },
    ])


def downgrade() -> None:
    procedimentos = sa.table("procedimentos", sa.column("nome", sa.String))
    op.execute(
        sa.delete(procedimentos).where(
            procedimentos.c.nome.in_([
                "Limpeza de pele",
                "Peeling químico",
                "Microagulhamento facial",
                "Drenagem linfática",
                "Botox facial",
            ])
        )
    )
