from app.application.services.agendamento_service import AgendamentoService

class BuscarAgendamento:
    def __init__(self, service: AgendamentoService): self.service = service
    async def execute(self, agendamento_id: int): return await self.service.buscar(agendamento_id)
