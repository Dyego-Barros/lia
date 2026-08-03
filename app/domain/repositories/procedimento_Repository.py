from abc import ABC, abstractmethod

class ProcedimentoRepository(ABC):
    @abstractmethod
    async def create_procedimento(self, procedimento):
        pass
    
    @abstractmethod
    async def get_procedimento_by_id(self, procedimento_id):
        pass
    
    @abstractmethod
    async def update_procedimento(self, procedimento):
        pass
    
    @abstractmethod
    async def delete_procedimento(self, procedimento_id):
        pass    
    
    @abstractmethod
    async def list_procedimentos(self):
        pass
    
    