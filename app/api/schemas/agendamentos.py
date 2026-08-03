from datetime import datetime
from pydantic import BaseModel
from app.domain.enums.status_agendamento import StatusAgendamento

class AgendamentoCreate(BaseModel):
    cliente_id: int
    procedimento_id: int
    data_hora: datetime
    status: StatusAgendamento = StatusAgendamento.PENDENTE

class AgendamentoUpdate(AgendamentoCreate):
    id: int
