"""seed complete test data for scheduling flows

Revision ID: 20260803_04
Revises: 20260803_03
"""

from datetime import datetime, time, timedelta
import os

from alembic import op
import sqlalchemy as sa


revision = "20260803_04"
down_revision = "20260803_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if os.getenv("SEED_DEMO_DATA", "false").lower() != "true":
        return
    agora = datetime.utcnow().replace(second=0, microsecond=0)

    clientes = sa.table(
        "clientes",
        sa.column("nome", sa.String),
        sa.column("email", sa.String),
        sa.column("telefone", sa.String),
        sa.column("status", sa.Boolean),
        sa.column("data_criacao", sa.DateTime),
        sa.column("data_atualizacao", sa.DateTime),
    )
    op.bulk_insert(clientes, [
        {
            "nome": "Ana Souza",
            "email": "ana.souza@example.com",
            "telefone": "5511999000001",
            "status": True,
            "data_criacao": agora,
            "data_atualizacao": agora,
        },
        {
            "nome": "Beatriz Lima",
            "email": "beatriz.lima@example.com",
            "telefone": "5511999000002",
            "status": True,
            "data_criacao": agora,
            "data_atualizacao": agora,
        },
        {
            "nome": "Carla Mendes",
            "email": "carla.mendes@example.com",
            "telefone": "5511999000003",
            "status": True,
            "data_criacao": agora,
            "data_atualizacao": agora,
        },
    ])

    tempos_trabalho = sa.table(
        "tempos_trabalho",
        sa.column("data_inicio", sa.DateTime),
        sa.column("data_fim", sa.DateTime),
        sa.column("data_criacao", sa.DateTime),
        sa.column("data_atualizacao", sa.DateTime),
    )
    # Cada janela representa o expediente disponível para os agendamentos do dia.
    # O serviço de disponibilidade pode usar essas janelas para calcular a capacidade diária.
    janelas = []
    for dias_a_frente in range(1, 8):
        dia = (agora + timedelta(days=dias_a_frente)).date()
        if dia.weekday() < 5:  # segunda a sexta
            inicio = datetime.combine(dia, time(8, 0))
            fim = datetime.combine(dia, time(18, 0))
            janelas.append({
                "data_inicio": inicio,
                "data_fim": fim,
                "data_criacao": agora,
                "data_atualizacao": agora,
            })
    op.bulk_insert(tempos_trabalho, janelas)

    bind = op.get_bind()
    procedimento_ids = dict(bind.execute(sa.text(
        "SELECT nome, id FROM procedimentos WHERE nome IN "
        "('Limpeza de pele', 'Peeling químico', 'Microagulhamento facial', 'Drenagem linfática', 'Botox facial')"
    )).all())
    cliente_ids = dict(bind.execute(sa.text(
        "SELECT telefone, id FROM clientes WHERE telefone IN "
        "('5511999000001', '5511999000002', '5511999000003')"
    )).all())

    agendamentos = sa.table(
        "agendamentos",
        sa.column("cliente_id", sa.Integer),
        sa.column("procedimento_id", sa.Integer),
        sa.column("data_hora", sa.DateTime),
        sa.column("status", sa.String),
        sa.column("data_criacao", sa.DateTime),
        sa.column("data_atualizacao", sa.DateTime),
    )
    dias_uteis = []
    deslocamento = 1
    while len(dias_uteis) < 2:
        dia = (agora + timedelta(days=deslocamento)).date()
        if dia.weekday() < 5:
            dias_uteis.append(dia)
        deslocamento += 1
    amanha, depois_de_amanha = dias_uteis
    op.bulk_insert(agendamentos, [
        {
            "cliente_id": cliente_ids["5511999000001"],
            "procedimento_id": procedimento_ids["Limpeza de pele"],
            "data_hora": datetime.combine(amanha, time(9, 0)),
            "status": "confirmado",
            "data_criacao": agora,
            "data_atualizacao": agora,
        },
        {
            "cliente_id": cliente_ids["5511999000002"],
            "procedimento_id": procedimento_ids["Peeling químico"],
            "data_hora": datetime.combine(amanha, time(10, 30)),
            "status": "pendente",
            "data_criacao": agora,
            "data_atualizacao": agora,
        },
        {
            "cliente_id": cliente_ids["5511999000003"],
            "procedimento_id": procedimento_ids["Microagulhamento facial"],
            "data_hora": datetime.combine(depois_de_amanha, time(14, 0)),
            "status": "confirmado",
            "data_criacao": agora,
            "data_atualizacao": agora,
        },
        {
            "cliente_id": cliente_ids["5511999000001"],
            "procedimento_id": procedimento_ids["Drenagem linfática"],
            "data_hora": datetime.combine(depois_de_amanha, time(15, 30)),
            "status": "cancelado",
            "data_criacao": agora,
            "data_atualizacao": agora,
        },
    ])


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text(
        "DELETE FROM agendamentos WHERE cliente_id IN "
        "(SELECT id FROM clientes WHERE telefone IN "
        "('5511999000001', '5511999000002', '5511999000003'))"
    ))
    bind.execute(sa.text(
        "DELETE FROM tempos_trabalho WHERE data_inicio >= CURRENT_DATE "
        "AND data_inicio < CURRENT_DATE + INTERVAL '8 days'"
    ))
    bind.execute(sa.text(
        "DELETE FROM clientes WHERE telefone IN "
        "('5511999000001', '5511999000002', '5511999000003')"
    ))
