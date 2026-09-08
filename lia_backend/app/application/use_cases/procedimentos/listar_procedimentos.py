from app.application.services.procedimento_service import ProcedimentoService

class ListarProcedimentos:
    def __init__(self, service: ProcedimentoService): self.service = service
    async def execute(self): return await self.service.listar()
