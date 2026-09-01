from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.models import BloqueioAgendaModel, TempoTrabalhoModel


class TempoTrabalhoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def listar_por_dia(self, dia: date) -> list[tuple[datetime, datetime]]:
        inicio = datetime.combine(dia, time.min)
        fim = inicio + timedelta(days=1)
        result = await self.session.execute(
            select(TempoTrabalhoModel)
            .where(TempoTrabalhoModel.data_inicio >= inicio)
            .where(TempoTrabalhoModel.data_inicio < fim)
            .order_by(TempoTrabalhoModel.data_inicio)
        )
        return [(item.data_inicio, item.data_fim) for item in result.scalars().all()]

    async def listar_bloqueios_por_dia(self, dia: date) -> list[tuple[datetime, datetime]]:
        inicio = datetime.combine(dia, time.min)
        fim = inicio + timedelta(days=1)
        result = await self.session.execute(
            select(BloqueioAgendaModel)
            .where(BloqueioAgendaModel.inicio < fim)
            .where(BloqueioAgendaModel.fim > inicio)
            .order_by(BloqueioAgendaModel.inicio)
        )
        return [(item.inicio, item.fim) for item in result.scalars().all()]
