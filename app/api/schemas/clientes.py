from pydantic import BaseModel
from typing import Optional

class ClienteCreate(BaseModel):
    nome: str
    email: Optional[str] = None
    telefone: Optional[str] = None

class ClienteUpdate(ClienteCreate):
    status: bool = True
