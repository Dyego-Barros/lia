from app.application.services.agendamento_service import AgendamentoService

class ListarAgendamentos:
    def __init__(self, service: AgendamentoService): self.service = service
    async def execute(self): return await self.service.listar()
