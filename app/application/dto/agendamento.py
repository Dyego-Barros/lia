from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AgendamentoDto(BaseModel):
    id: Optional[int] = None
    cliente_id: int
    procedimento_id: int
    data_hora: datetime
    status: str = "pendente"  # pendente, confirmado, cancelado

    model_config = {
        "from_attributes": True,
        "validate_assignment": True
    }
