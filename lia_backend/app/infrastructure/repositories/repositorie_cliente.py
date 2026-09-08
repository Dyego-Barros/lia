from app.domain.interfaces.interface_cliente import ClienteInterface
from sqlalchemy.ext.asyncio import AsyncSession
from app.application.dto.cliente import ClienteDto
from app.infrastructure.database.models.models import ClienteModel
from sqlalchemy import select


class ClienteRepository(ClienteInterface):
    def __init__(self, session:AsyncSession):
        self.session = session
       
        
        
    async def create_cliente(self, cliente: ClienteDto) -> ClienteDto:
        try:
            cliente_model = ClienteModel(
                nome=cliente.nome,
                email=cliente.email,
                telefone=cliente.telefone
            )
            self.session.add(cliente_model)
            await self.session.commit()
            await self.session.refresh(cliente_model)
            return ClienteDto.model_validate(cliente_model)
        except Exception as e:
            print("Ocorreu um erro ao criar o cliente:", e)
            await self.session.rollback()
            raise e
    
    async def get_cliente_by_id(self, cliente_id: int) -> ClienteDto:
        try:
            cliente = await self.session.get(ClienteModel, cliente_id)
            if cliente is None:
                raise ValueError(f"Cliente com ID {cliente_id} não encontrado.")
            return ClienteDto.model_validate(cliente)
        except Exception as e:
            print("Ocorreu um erro ao buscar o cliente:", e)
            await self.session.rollback()
            raise e
        
    async def update_cliente(self,  cliente: ClienteDto) -> ClienteDto:
        try:
            cliente_update = await self.session.get(ClienteModel, cliente.id)
            if cliente_update is None:
                raise ValueError(f"Cliente com ID {cliente.id} não encontrado.")
            cliente_update.nome = cliente.nome
            cliente_update.email = cliente.email
            cliente_update.telefone = cliente.telefone
            cliente_update.status = cliente.status
            await self.session.commit()
            await self.session.refresh(cliente_update)
            return ClienteDto.model_validate(cliente_update)
        except Exception as e:
            print("Ocorreu um erro ao atualizar o cliente:", e)
            await self.session.rollback()
            raise e
        
    async def delete_cliente(self, cliente_id: int) -> None:
        try:
            cliente = await self.session.get(ClienteModel, cliente_id)
            if cliente is None:
                raise ValueError(f"Cliente com ID {cliente_id} não encontrado.")
            await self.session.delete(cliente)
            await self.session.commit()
        except Exception as e:
            print("Ocorreu um erro ao deletar o cliente:", e)
            await self.session.rollback()
            raise e
        
    async def list_clientes(self) -> list[ClienteDto]:
        try:
            result = await self.session.execute(
                select(ClienteModel)
            )
            clientes = result.scalars().all()
            return [ClienteDto.model_validate(cliente) for cliente in clientes]
        except Exception as e:
            print("Ocorreu um erro ao listar os clientes:", e)
            await self.session.rollback()
            raise e
        
    async def get_cliente_by_email(self, email: str) -> ClienteDto:
        try:
            result = await self.session.execute(
                select(ClienteModel).where(ClienteModel.email == email)
            )
            cliente = result.scalar_one_or_none()
            if cliente is None:
                raise ValueError(f"Cliente com email {email} não encontrado.")
            return ClienteDto.model_validate(cliente)
        except Exception as e:
            print("Ocorreu um erro ao buscar o cliente por email:", e)
            await self.session.rollback()
            raise e

    async def get_cliente_by_telefone(self, telefone: str) -> ClienteDto | None:
        result = await self.session.execute(
            select(ClienteModel).where(ClienteModel.telefone == telefone)
        )
        cliente = result.scalar_one_or_none()
        return ClienteDto.model_validate(cliente) if cliente else None
        
    async def active_cliente(self, cliente_id: int) -> None:
        try:
            cliente = await self.session.get(ClienteModel, cliente_id)
            if cliente is None:
                raise ValueError(f"Cliente com ID {cliente_id} não encontrado.")
            cliente.status = True
            await self.session.commit()
        except Exception as e:
            print("Ocorreu um erro ao ativar o cliente:", e)
            await self.session.rollback()
            raise e
        
    async def inactive_cliente(self, cliente_id: int) -> None:
        try:
            cliente = await self.session.get(ClienteModel, cliente_id)
            if cliente is None:
                raise ValueError(f"Cliente com ID {cliente_id} não encontrado.")
            cliente.status = False
            await self.session.commit()
        except Exception as e:
            print("Ocorreu um erro ao desativar o cliente:", e)
            await self.session.rollback()
            raise e
