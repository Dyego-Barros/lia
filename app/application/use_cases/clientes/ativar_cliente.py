from app.application.services.cliente_service import ClienteService

class AtivarCliente:
    def __init__(self, service: ClienteService): self.service = service
    async def execute(self, cliente_id: int): return await self.service.ativar(cliente_id)
