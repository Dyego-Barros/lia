from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import Optional
from app.application.dto.agendamento import AgendamentoDto
from app.application.dto.cliente import ClienteDto
from app.application.dto.procedimento import ProcedimentoDto

class IdentificarClienteRequest(BaseModel):
    telefone: str = Field(min_length=8)
    nome: Optional[str] = None
    email: Optional[str] = None

class CriarAgendamentoRequest(BaseModel):
    telefone: str = Field(min_length=8)
    nome: Optional[str] = None
    email: Optional[str] = None
    procedimento_id: int
    data_hora: datetime

class ReagendarRequest(BaseModel):
    data_hora: datetime

class DisponibilidadeResponse(BaseModel):
    procedimento_id: int
    data: date
    horarios: list[datetime]

class InformacoesProcedimentoResponse(BaseModel):
    procedimento: ProcedimentoDto
    mensagem_agente: str
