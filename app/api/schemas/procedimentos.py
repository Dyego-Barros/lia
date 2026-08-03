from pydantic import BaseModel
from typing import Optional

class ProcedimentoCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: float
    duracao: int
    indicacoes: Optional[str] = None
    contraindicacoes: Optional[str] = None
    cuidados: Optional[str] = None

class ProcedimentoUpdate(ProcedimentoCreate):
    pass
