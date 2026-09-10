from datetime import date, datetime, time, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_user
from app.infrastructure.database.db import get_session
from app.infrastructure.database.models.models import AgendamentoModel, ConsumoMaterialModel, ProcedimentoMaterialModel, EstoqueProdutoModel, ProcedimentoModel

router = APIRouter(prefix="/relatorios", tags=["Relatórios"], dependencies=[Depends(get_current_user)])


@router.get("/volume-anual")
async def volume_anual(
    ano: int = Query(..., ge=2000, le=2100),
    session: AsyncSession = Depends(get_session),
):
    inicio = datetime(ano, 1, 1)
    fim = datetime(ano + 1, 1, 1)
    mes = func.extract("month", AgendamentoModel.data_hora)
    resultado = await session.execute(
        select(mes, func.count(AgendamentoModel.id))
        .where(
            AgendamentoModel.data_hora >= inicio,
            AgendamentoModel.data_hora < fim,
            AgendamentoModel.status == "concluido",
        )
        .group_by(mes)
        .order_by(mes)
    )
    quantidades = {int(numero_mes): quantidade for numero_mes, quantidade in resultado.all()}
    return {
        "ano": ano,
        "meses": [
            {"mes": numero_mes, "quantidade": quantidades.get(numero_mes, 0)}
            for numero_mes in range(1, 13)
        ],
    }


@router.get("/resumo")
async def resumo(
    inicio: date | None = Query(None),
    fim: date | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    inicio = inicio or date.today().replace(day=1)
    fim = fim or date.today()
    fim_exclusivo = datetime.combine(fim + timedelta(days=1), time.min)
    inicio_dt = datetime.combine(inicio, time.min)
    appointments = (await session.execute(select(AgendamentoModel).where(AgendamentoModel.data_hora >= inicio_dt, AgendamentoModel.data_hora < fim_exclusivo))).scalars().all()
    procedures = (await session.execute(select(ProcedimentoModel))).scalars().all()
    prices = {item.id: item.preco for item in procedures}
    recipe_rows = (await session.execute(select(ProcedimentoMaterialModel.procedimento_id, func.sum(ProcedimentoMaterialModel.quantidade * EstoqueProdutoModel.custo_unitario)).join(EstoqueProdutoModel, EstoqueProdutoModel.id == ProcedimentoMaterialModel.produto_id).group_by(ProcedimentoMaterialModel.procedimento_id))).all()
    material_costs = {procedure_id: cost for procedure_id, cost in recipe_rows}
    legacy_material_costs = {item.id: item.custo_materiais for item in procedures}
    consumption_rows = (await session.execute(select(ConsumoMaterialModel.agendamento_id, func.sum(ConsumoMaterialModel.quantidade * ConsumoMaterialModel.custo_unitario)).group_by(ConsumoMaterialModel.agendamento_id))).all()
    consumption_costs = {appointment_id: cost for appointment_id, cost in consumption_rows}
    realizados = [item for item in appointments if item.status == "concluido"]
    faturamento = sum(item.valor_cobrado if item.valor_cobrado is not None else prices.get(item.procedimento_id, 0) for item in realizados)
    def custo_do_atendimento(item):
        return consumption_costs.get(item.id, material_costs.get(item.procedimento_id, legacy_material_costs.get(item.procedimento_id, 0)))
    custos_materiais = sum(custo_do_atendimento(item) for item in realizados)
    por_procedimento = {}
    totais_por_dia = {}
    formas_pagamento = {}
    for item in realizados:
        entry = por_procedimento.setdefault(item.procedimento_id, {"procedimento_id": item.procedimento_id, "quantidade": 0, "faturamento": 0, "custos_materiais": 0, "lucro": 0})
        entry["quantidade"] += 1
        valor = item.valor_cobrado if item.valor_cobrado is not None else prices.get(item.procedimento_id, 0)
        custo = custo_do_atendimento(item)
        entry["faturamento"] += valor
        entry["custos_materiais"] += custo
        entry["lucro"] += valor - custo
        dia = item.data_hora.date().isoformat()
        total_dia = totais_por_dia.setdefault(dia, {"faturamento": 0, "lucro": 0})
        total_dia["faturamento"] += valor
        total_dia["lucro"] += valor - custo
        if item.status_pagamento == "pago" and item.forma_pagamento:
            pagamento = formas_pagamento.setdefault(item.forma_pagamento, {"quantidade": 0, "valor": 0})
            pagamento["quantidade"] += 1
            pagamento["valor"] += valor

    por_status = {}
    for item in appointments:
        por_status[item.status] = por_status.get(item.status, 0) + 1

    por_dia = []
    dia_atual = inicio
    while dia_atual <= fim:
        valores = totais_por_dia.get(dia_atual.isoformat(), {"faturamento": 0, "lucro": 0})
        por_dia.append({"data": dia_atual, **valores})
        dia_atual += timedelta(days=1)

    clientes_do_dia = len({item.cliente_id for item in appointments if item.status != "cancelado"})
    return {
        "inicio": inicio,
        "fim": fim,
        "atendimentos_realizados": len(realizados),
        "clientes_do_dia": clientes_do_dia,
        "agendamentos": len(appointments),
        "faturamento": faturamento,
        "custos_materiais": custos_materiais,
        "lucro": faturamento - custos_materiais,
        "por_procedimento": list(por_procedimento.values()),
        "por_dia": por_dia,
        "formas_pagamento": [
            {"forma": forma, **totais}
            for forma, totais in formas_pagamento.items()
        ],
        "por_status": [
            {"status": nome_status, "quantidade": quantidade}
            for nome_status, quantidade in por_status.items()
        ],
    }
