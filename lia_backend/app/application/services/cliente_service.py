from app.application.dto.cliente import ClienteDto
from app.domain.entities.clientes import Cliente
from app.domain.interfaces.interface_cliente import ClienteInterface


class ClienteService:
    def __init__(self, repository: ClienteInterface):
        self.repository = repository

    async def criar(self, cliente: ClienteDto) -> ClienteDto:
        entity = Cliente.model_validate(cliente)
        entity.telefone = entity.normalizar_telefone(entity.telefone)
        return await self.repository.create_cliente(ClienteDto.model_validate(entity))

    async def buscar(self, cliente_id: int) -> ClienteDto:
        return await self.repository.get_cliente_by_id(cliente_id)

    async def identificar_por_telefone(self, telefone: str, nome: str | None = None, email: str | None = None) -> ClienteDto:
        telefone_normalizado = Cliente(nome=nome or "Cliente", telefone=telefone, email=email).normalizar_telefone(telefone)
        cliente = await self.repository.get_cliente_by_telefone(telefone_normalizado)
        if cliente:
            nome_atualizado = nome.strip() if nome and nome.strip() else cliente.nome
            email_atualizado = email.strip() if email and email.strip() else cliente.email
            precisa_atualizar = (
                nome_atualizado != cliente.nome
                or email_atualizado != cliente.email
            )
            if precisa_atualizar:
                return await self.atualizar(ClienteDto(
                    id=cliente.id,
                    nome=nome_atualizado,
                    email=email_atualizado,
                    telefone=cliente.telefone,
                    status=cliente.status,
                ))
            return cliente
        if not nome or not nome.strip() or not email or not email.strip():
            raise ValueError(
                "Cliente novo exige nome completo e e-mail antes do cadastro."
            )
        return await self.criar(ClienteDto(nome=nome or "Cliente", email=email, telefone=telefone_normalizado))

    async def buscar_por_telefone(self, telefone: str) -> ClienteDto | None:
        telefone_normalizado = Cliente(nome="Cliente", telefone=telefone).normalizar_telefone(telefone)
        return await self.repository.get_cliente_by_telefone(telefone_normalizado)

    async def listar(self) -> list[ClienteDto]:
        return await self.repository.list_clientes()

    async def atualizar(self, cliente: ClienteDto) -> ClienteDto:
        entity = Cliente.model_validate(cliente)
        entity.telefone = entity.normalizar_telefone(entity.telefone)
        return await self.repository.update_cliente(ClienteDto.model_validate(entity))

    async def remover(self, cliente_id: int) -> None:
        await self.repository.delete_cliente(cliente_id)

    async def ativar(self, cliente_id: int) -> None:
        await self.repository.active_cliente(cliente_id)

    async def desativar(self, cliente_id: int) -> None:
        await self.repository.inactive_cliente(cliente_id)
