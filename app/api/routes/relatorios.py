from datetime import date, datetime, time, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_user
from app.infrastructure.database.db import get_session
from app.infrastructure.database.models.models import AgendamentoModel, ProcedimentoModel

router = APIRouter(prefix="/relatorios", tags=["Relatórios"], dependencies=[Depends(get_current_user)])


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
    material_costs = {item.id: item.custo_materiais for item in procedures}
    realizados = [item for item in appointments if item.status == "concluido"]
    faturamento = sum(item.valor_cobrado if item.valor_cobrado is not None else prices.get(item.procedimento_id, 0) for item in realizados)
    custos_materiais = sum(material_costs.get(item.procedimento_id, 0) for item in realizados)
    por_procedimento = {}
    for item in realizados:
        entry = por_procedimento.setdefault(item.procedimento_id, {"procedimento_id": item.procedimento_id, "quantidade": 0, "faturamento": 0, "custos_materiais": 0, "lucro": 0})
        entry["quantidade"] += 1
        valor = item.valor_cobrado if item.valor_cobrado is not None else prices.get(item.procedimento_id, 0)
        custo = material_costs.get(item.procedimento_id, 0)
        entry["faturamento"] += valor
        entry["custos_materiais"] += custo
        entry["lucro"] += valor - custo
    clientes_do_dia = len({item.cliente_id for item in appointments if item.status != "cancelado"})
    return {"inicio": inicio, "fim": fim, "atendimentos_realizados": len(realizados), "clientes_do_dia": clientes_do_dia, "agendamentos": len(appointments), "faturamento": faturamento, "custos_materiais": custos_materiais, "lucro": faturamento - custos_materiais, "por_procedimento": list(por_procedimento.values())}
