from app.application.services.cliente_service import ClienteService

class ListarClientes:
    def __init__(self, service: ClienteService): self.service = service
    async def execute(self): return await self.service.listar()
