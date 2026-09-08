from abc import ABC, abstractmethod


class ClienteInterface(ABC):
    
    @abstractmethod
    async def create_cliente(self, cliente):
        pass
    
    @abstractmethod
    async def get_cliente_by_id(self, cliente_id):
        pass
    
    @abstractmethod
    async def update_cliente(self, cliente):
        pass
    
    @abstractmethod
    async def delete_cliente(self, cliente_id):
        pass    
    
    @abstractmethod
    async def list_clientes(self):
        pass
    
    @abstractmethod
    async def get_cliente_by_email(self, email):
        pass

    @abstractmethod
    async def get_cliente_by_telefone(self, telefone):
        pass
    
    @abstractmethod
    async def active_cliente(self, cliente_id):
        pass
    
    @abstractmethod
    async def inactive_cliente(self, cliente_id):
        pass
