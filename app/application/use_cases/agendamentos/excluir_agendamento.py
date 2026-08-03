from app.application.services.agendamento_service import AgendamentoService

class ExcluirAgendamento:
    def __init__(self, service: AgendamentoService): self.service = service
    async def execute(self, agendamento_id: int): return await self.service.remover(agendamento_id)
