from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AgendamentoDto(BaseModel):
    id: Optional[int] = None
    cliente_id: int
    procedimento_id: int
    profissional_id: Optional[int] = None
    data_hora: datetime
    status: str = "pendente"  # pendente, confirmado, cancelado
    valor_cobrado: Optional[float] = None
    forma_pagamento: Optional[str] = None
    status_pagamento: str = "pendente"

    model_config = {
        "from_attributes": True,
        "validate_assignment": True
    }
