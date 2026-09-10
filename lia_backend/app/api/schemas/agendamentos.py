from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator
from app.domain.enums.status_agendamento import StatusAgendamento

class AgendamentoCreate(BaseModel):
    cliente_id: int
    procedimento_id: int
    profissional_id: int | None = None
    data_hora: datetime
    status: StatusAgendamento = StatusAgendamento.PENDENTE
    valor_cobrado: float | None = Field(default=None, ge=0)
    forma_pagamento: str | None = None
    status_pagamento: Literal["pendente", "pago", "nao_pago"] = "pendente"

    @model_validator(mode="after")
    def validar_pagamento_pago(self):
        if self.status == StatusAgendamento.NAO_COMPARECEU:
            self.status_pagamento = "nao_pago"
            self.forma_pagamento = None
        if self.status_pagamento == "pago" and (self.valor_cobrado is None or not self.forma_pagamento):
            raise ValueError("Informe valor e forma de pagamento para registrar um pagamento como pago.")
        return self

class AgendamentoUpdate(AgendamentoCreate):
    id: int
