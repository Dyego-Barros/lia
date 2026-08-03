from app.application.dto.procedimento import ProcedimentoDto
from app.domain.entities.procedimentos import Procedimento
from app.domain.interfaces.interface_procedimento import ProcedimentoInterface


class ProcedimentoService:
    def __init__(self, repository: ProcedimentoInterface):
        self.repository = repository

    async def criar(self, procedimento: ProcedimentoDto) -> ProcedimentoDto:
        return await self.repository.create_procedimento(ProcedimentoDto.model_validate(Procedimento.model_validate(procedimento)))

    async def buscar(self, procedimento_id: int) -> ProcedimentoDto:
        return await self.repository.get_procedimento_by_id(procedimento_id)

    async def listar(self) -> list[ProcedimentoDto]:
        return await self.repository.list_procedimentos()

    async def atualizar(self, procedimento: ProcedimentoDto) -> ProcedimentoDto:
        entity = Procedimento.model_validate(procedimento)
        return await self.repository.update_procedimento(ProcedimentoDto.model_validate(entity))

    async def remover(self, procedimento_id: int) -> None:
        await self.repository.delete_procedimento(procedimento_id)
