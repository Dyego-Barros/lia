from datetime import datetime, time
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    nome: str = Field(min_length=3)
    email: str
    password: str = Field(min_length=6)
    role: str = "atendente"


class ProfessionalCreate(BaseModel):
    nome: str = Field(min_length=3)
    email: str | None = None
    telefone: str | None = None
    especialidade: str | None = None
    ativo: bool = True


class ScheduleCreate(BaseModel):
    profissional_id: int
    weekday: int = Field(ge=0, le=6)
    inicio: time
    fim: time


class ProfessionalUpdate(BaseModel):
    nome: str = Field(min_length=3)
    email: str | None = None
    telefone: str | None = None
    especialidade: str | None = None
    ativo: bool = True


class ScheduleUpdate(ScheduleCreate):
    pass


class BlockCreate(BaseModel):
    profissional_id: int | None = None
    inicio: datetime
    fim: datetime
    motivo: str = Field(min_length=2)


class WaitlistCreate(BaseModel):
    cliente_id: int
    procedimento_id: int
    data_preferida: datetime | None = None
    periodo: str | None = Field(default=None, pattern="^(manha|manhã|tarde|noite)$")
    profissional_id: int | None = None


class WaitlistStatusUpdate(BaseModel):
    status: str = Field(pattern="^(aguardando|notificado|convertido|cancelado)$")


class WaitlistPromote(BaseModel):
    data_hora: datetime
    profissional_id: int | None = None


class PaymentCreate(BaseModel):
    agendamento_id: int
    valor: float = Field(gt=0)
    forma: str = Field(min_length=2)
    status: str = "pago"


class PackageCreate(BaseModel):
    nome: str = Field(min_length=2)
    descricao: str | None = None
    preco: float = Field(ge=0)
    ativo: bool = True


class PackageItemCreate(BaseModel):
    pacote_id: int
    procedimento_id: int
    quantidade: int = Field(gt=0)


class ReviewCreate(BaseModel):
    agendamento_id: int
    nota: int = Field(ge=1, le=5)
    comentario: str | None = None


class StockProductCreate(BaseModel):
    nome: str = Field(min_length=2)
    sku: str | None = None
    quantidade: int = Field(ge=0)
    estoque_minimo: int = Field(ge=0)
    custo_unitario: float = Field(ge=0)
    ativo: bool = True
