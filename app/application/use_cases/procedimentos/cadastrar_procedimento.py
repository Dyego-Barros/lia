from app.application.dto.procedimento import ProcedimentoDto
from app.application.services.procedimento_service import ProcedimentoService


class CadastrarProcedimento:
    def __init__(self, service: ProcedimentoService): self.service = service
    async def execute(self, procedimento: ProcedimentoDto): return await self.service.criar(procedimento)
