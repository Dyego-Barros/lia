from pydantic import BaseModel
from typing import Optional


class ProcedimentoDto(BaseModel):
    id: Optional[int] = None
    nome: str
    descricao: Optional[str] = None
    preco: float
    custo_materiais: float = 0
    duracao: int  # duração em minutos
    indicacoes: Optional[str] = None
    contraindicacoes: Optional[str] = None
    cuidados: Optional[str] = None

    model_config = {
        "from_attributes": True,
        "validate_assignment": True
    }
