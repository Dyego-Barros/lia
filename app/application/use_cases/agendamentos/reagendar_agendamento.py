from app.application.services.agendamento_service import AgendamentoService

class ReagendarAgendamento:
    def __init__(self, service: AgendamentoService): self.service = service
    async def execute(self, agendamento_id: int, nova_data_hora):
        return await self.service.reagendar(agendamento_id, nova_data_hora)
