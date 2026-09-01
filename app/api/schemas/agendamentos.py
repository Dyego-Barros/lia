from datetime import datetime
from pydantic import BaseModel
from app.domain.enums.status_agendamento import StatusAgendamento

class AgendamentoCreate(BaseModel):
    cliente_id: int
    procedimento_id: int
    profissional_id: int | None = None
    data_hora: datetime
    status: StatusAgendamento = StatusAgendamento.PENDENTE
    valor_cobrado: float | None = None
    forma_pagamento: str | None = None
    status_pagamento: str = "pendente"

class AgendamentoUpdate(AgendamentoCreate):
    id: int
