from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.procedimento import ProcedimentoDto
from app.domain.interfaces.interface_procedimento import ProcedimentoInterface
from app.infrastructure.database.models.models import ProcedimentoModel


class ProcedimentoRepository(ProcedimentoInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_procedimento(self, procedimento: ProcedimentoDto) -> ProcedimentoDto:
        try:
            procedimento_model = ProcedimentoModel(
                nome=procedimento.nome,
                descricao=procedimento.descricao,
                preco=procedimento.preco,
                duracao=procedimento.duracao,
                indicacoes=procedimento.indicacoes,
                contraindicacoes=procedimento.contraindicacoes,
                cuidados=procedimento.cuidados,
            )
            self.session.add(procedimento_model)
            await self.session.commit()
            await self.session.refresh(procedimento_model)
            return ProcedimentoDto.model_validate(procedimento_model)
        except Exception:
            await self.session.rollback()
            raise

    async def get_procedimento_by_id(self, procedimento_id: int) -> ProcedimentoDto:
        try:
            procedimento = await self.session.get(ProcedimentoModel, procedimento_id)
            if procedimento is None:
                raise ValueError(f"Procedimento com ID {procedimento_id} não encontrado.")
            return ProcedimentoDto.model_validate(procedimento)
        except Exception:
            await self.session.rollback()
            raise

    async def update_procedimento(self, procedimento: ProcedimentoDto) -> ProcedimentoDto:
        try:
            procedimento_update = await self.session.get(ProcedimentoModel, procedimento.id)
            if procedimento_update is None:
                raise ValueError(f"Procedimento com ID {procedimento.id} não encontrado.")

            procedimento_update.nome = procedimento.nome
            procedimento_update.descricao = procedimento.descricao
            procedimento_update.preco = procedimento.preco
            procedimento_update.duracao = procedimento.duracao
            procedimento_update.indicacoes = procedimento.indicacoes
            procedimento_update.contraindicacoes = procedimento.contraindicacoes
            procedimento_update.cuidados = procedimento.cuidados

            await self.session.commit()
            await self.session.refresh(procedimento_update)
            return ProcedimentoDto.model_validate(procedimento_update)
        except Exception:
            await self.session.rollback()
            raise

    async def delete_procedimento(self, procedimento_id: int) -> None:
        try:
            procedimento = await self.session.get(ProcedimentoModel, procedimento_id)
            if procedimento is None:
                raise ValueError(f"Procedimento com ID {procedimento_id} não encontrado.")
            await self.session.delete(procedimento)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def list_procedimentos(self) -> list[ProcedimentoDto]:
        try:
            result = await self.session.execute(select(ProcedimentoModel))
            procedimentos = result.scalars().all()
            return [ProcedimentoDto.model_validate(item) for item in procedimentos]
        except Exception:
            await self.session.rollback()
            raise

    async def list_procedimentos_by_name(self, nome: str) -> list[ProcedimentoDto]:
        try:
            result = await self.session.execute(
                select(ProcedimentoModel).where(ProcedimentoModel.nome.ilike(f"%{nome}%"))
            )
            procedimentos = result.scalars().all()
            return [ProcedimentoDto.model_validate(item) for item in procedimentos]
        except Exception:
            await self.session.rollback()
            raise



