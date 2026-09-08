from app.application.services.procedimento_service import ProcedimentoService

class ExcluirProcedimento:
    def __init__(self, service: ProcedimentoService): self.service = service
    async def execute(self, procedimento_id: int): return await self.service.remover(procedimento_id)
