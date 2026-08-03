from abc import ABC, abstractmethod

class AgendamentoInterface(ABC):   
    @abstractmethod
    async def create_agendamento(self, agendamento):
        pass
    
    @abstractmethod
    async def get_agendamento_by_id(self, agendamento_id):
        pass
    
    @abstractmethod
    async def update_agendamento(self, agendamento):
        pass
    
    @abstractmethod
    async def delete_agendamento(self, agendamento_id):
        pass    
    
    @abstractmethod
    async def list_agendamentos(self):
        pass
    
    @abstractmethod
    async def get_agendamento_data_hora(self, data_hora):
        pass