from app.application.dto.agendamento import AgendamentoDto
from app.application.services.agendamento_service import AgendamentoService

class AtualizarAgendamento:
    def __init__(self, service: AgendamentoService): self.service = service
    async def execute(self, agendamento: AgendamentoDto): return await self.service.atualizar(agendamento)
