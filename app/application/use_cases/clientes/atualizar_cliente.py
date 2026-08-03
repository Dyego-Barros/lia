from app.application.dto.cliente import ClienteDto
from app.application.services.cliente_service import ClienteService


class AtualizarCliente:
    def __init__(self, service: ClienteService):
        self.service = service

    async def execute(self, cliente: ClienteDto) -> ClienteDto:
        return await self.service.atualizar(cliente)
