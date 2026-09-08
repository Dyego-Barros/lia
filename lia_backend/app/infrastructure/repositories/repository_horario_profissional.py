from datetime import date, time
import unicodedata

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.models import HorarioProfissionalModel, ProfissionalModel


class HorarioProfissionalRepository:
    """Consulta a agenda semanal e os profissionais que podem ser agendados."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def buscar_profissional_ativo(self, profissional_id: int) -> ProfissionalModel | None:
        result = await self.session.execute(
            select(ProfissionalModel).where(
                ProfissionalModel.id == profissional_id,
                ProfissionalModel.ativo.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def listar_profissionais_ativos(self) -> list[ProfissionalModel]:
        result = await self.session.execute(
            select(ProfissionalModel)
            .where(ProfissionalModel.ativo.is_(True))
            .order_by(ProfissionalModel.nome)
        )
        return list(result.scalars().all())

    async def buscar_profissionais_por_nome(self, nome: str) -> list[ProfissionalModel]:
        """Busca internamente sem expor identificadores ao cliente final."""
        def normalizar(valor: str) -> str:
            return "".join(
                caractere for caractere in unicodedata.normalize("NFD", valor.casefold().strip())
                if unicodedata.category(caractere) != "Mn"
            )

        consulta = normalizar(nome)
        if not consulta:
            return []
        profissionais = await self.listar_profissionais_ativos()
        exatos = [item for item in profissionais if normalizar(item.nome) == consulta]
        return exatos or [item for item in profissionais if consulta in normalizar(item.nome)]

    async def listar_horarios(self, profissional_id: int, weekday: int | None = None) -> list[HorarioProfissionalModel]:
        statement = select(HorarioProfissionalModel).where(HorarioProfissionalModel.profissional_id == profissional_id)
        if weekday is not None:
            statement = statement.where(HorarioProfissionalModel.weekday == weekday)
        result = await self.session.execute(statement.order_by(HorarioProfissionalModel.weekday, HorarioProfissionalModel.inicio))
        return list(result.scalars().all())

    async def janelas_do_dia(self, profissional_id: int, dia: date) -> list[tuple[time, time]]:
        horarios = await self.listar_horarios(profissional_id, dia.weekday())
        return [(item.inicio, item.fim) for item in horarios]
