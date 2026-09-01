from pydantic import BaseModel
from typing import Optional


class ClienteDto(BaseModel):
    id: Optional[int] = None
    nome: str
    email: Optional[str] = None
    telefone: str
    status: Optional[bool] = True  # Default status is True (active)

    model_config = {
        "from_attributes": True,
        "validate_assignment": True
    }
