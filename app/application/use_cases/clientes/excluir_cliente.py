from app.application.services.cliente_service import ClienteService

class ExcluirCliente:
    def __init__(self, service: ClienteService): self.service = service
    async def execute(self, cliente_id: int): return await self.service.remover(cliente_id)
