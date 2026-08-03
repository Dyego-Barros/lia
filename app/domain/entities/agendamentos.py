from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from app.domain.enums.status_agendamento import StatusAgendamento
from app.domain.exceptions.agendamentos import *
from app.domain.exceptions.clientes import InvalidClienteException
from app.domain.exceptions.procedimentos import InvalidProcedimentoException

class Agendamento(BaseModel):
    id: Optional[int] = None
    cliente_id: int
    procedimento_id: int
    data_hora: datetime  # Consider using datetime for better handling
    status: StatusAgendamento = StatusAgendamento.PENDENTE.value  # Default status is "pendente"

    model_config = {
        "from_attributes": True,
        "validate_assignment": True
    }
    
    @field_validator("status")
    @classmethod
    def validar_status(cls, status):
        
        if status not in [s.value for s in StatusAgendamento]:
            raise ValueError(f"Status inválido: {status}. Deve ser um dos seguintes: {[s.value for s in StatusAgendamento]}")
        return status
        
        
    @field_validator("data_hora")
    @classmethod
    def validar_data_hora(cls, data_hora):
        if data_hora < datetime.now():
            raise InvalidAgendamentoDateTimeException("A data e hora do agendamento não podem ser no passado.")
        return data_hora
    
    @field_validator("cliente_id")
    @classmethod
    def validar_cliente_id(cls, cliente_id):
        if cliente_id <= 0:
            raise InvalidClienteException("O ID do cliente deve ser um número positivo.")
        return cliente_id
    
    @field_validator("procedimento_id")
    @classmethod
    def validar_procedimento_id(cls, procedimento_id):
        if procedimento_id <= 0:
            raise InvalidProcedimentoException("O ID do procedimento deve ser um número positivo.")
        return procedimento_id
    
    @classmethod
    def criar_agendamento(cls, cliente_id: int, procedimento_id: int, data_hora: datetime, status: str = StatusAgendamento.PENDENTE.value):
        agora = datetime.now()
        if data_hora < agora:
            raise InvalidAgendamentoDateTimeException("A data e hora do agendamento não podem ser no passado.")
        if status not in [s.value for s in StatusAgendamento]:
            raise ValueError(f"Status inválido: {status}. Deve ser um dos seguintes: {[s.value for s in StatusAgendamento]}")
        
        agendamento = cls(
            cliente_id=cliente_id,
            procedimento_id=procedimento_id,
            data_hora=data_hora,
            status=status
        )
        return agendamento
    
    
    def cancelar_agendamento(self):
        if self.status in [StatusAgendamento.CONCLUIDO.value, StatusAgendamento.NAO_COMPARECEU.value, StatusAgendamento.CANCELADO.value]:
            raise InvalidAgendamentoStatusException(f"Não é possível cancelar um agendamento com status '{self.status}'.")
        
        self.status = StatusAgendamento.CANCELADO.value
        
    def confirmar_agendamento(self):
        if self.status != StatusAgendamento.PENDENTE.value:
            raise InvalidAgendamentoStatusException(f"Não é possível confirmar um agendamento com status '{self.status}'.")
        
        self.status = StatusAgendamento.CONFIRMADO.value
    
    def concluir_agendamento(self):
        if self.status != StatusAgendamento.CONFIRMADO.value:
            raise InvalidAgendamentoStatusException(f"Não é possível concluir um agendamento com status '{self.status}'.")
        self.status = StatusAgendamento.CONCLUIDO.value
    
    def marcar_nao_compareceu(self):
        if self.status != StatusAgendamento.CONFIRMADO.value:
            raise InvalidAgendamentoStatusException(f"Não é possível marcar como 'não compareceu' um agendamento com status '{self.status}'.")
        self.status = StatusAgendamento.NAO_COMPARECEU.value
        
    def reagendar_agendamento(self, nova_data_hora: datetime):
        if self.status in [StatusAgendamento.CONCLUIDO.value, StatusAgendamento.NAO_COMPARECEU.value, StatusAgendamento.CANCELADO.value]:
            raise InvalidAgendamentoStatusException(f"Não é possível reagendar um agendamento com status '{self.status}'.")
        
        agora = datetime.now()
        if nova_data_hora < agora:
            raise InvalidAgendamentoDateTimeException("A nova data e hora do agendamento não podem ser no passado.")
        
        self.data_hora = nova_data_hora