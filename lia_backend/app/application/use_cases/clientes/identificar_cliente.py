from app.application.services.cliente_service import ClienteService

class IdentificarCliente:
    def __init__(self, service: ClienteService): self.service = service
    async def execute(self, telefone: str, nome: str | None = None, email: str | None = None):
        return await self.service.identificar_por_telefone(telefone, nome, email)
