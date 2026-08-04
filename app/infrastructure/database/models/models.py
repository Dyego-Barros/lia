from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, registry, mapped_column
from zoneinfo import ZoneInfo

SAO_PAULO = datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)

table_registry = registry()

@table_registry.mapped_as_dataclass
class ProcedimentoModel:
    __tablename__ = "procedimentos"

    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(nullable=True)
    preco: Mapped[float] = mapped_column(nullable=False)
    duracao: Mapped[int] = mapped_column(nullable=False)  # duração em minutos
    indicacoes: Mapped[Optional[str]] = mapped_column(nullable=True)
    contraindicacoes: Mapped[Optional[str]] = mapped_column(nullable=True)
    cuidados: Mapped[Optional[str]] = mapped_column(nullable=True)
    data_criacao: Mapped[datetime] = mapped_column(default=SAO_PAULO, nullable=False)
    data_atualizacao: Mapped[datetime] = mapped_column(default=SAO_PAULO, onupdate=SAO_PAULO, nullable=False)


@table_registry.mapped_as_dataclass
class ClienteModel:
    __tablename__ = "clientes"

    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[Optional[str]] = mapped_column(nullable=True)
    telefone: Mapped[Optional[str]] = mapped_column(nullable=True)
    status: Mapped[bool] = mapped_column(nullable=False, default=True)
    data_criacao: Mapped[datetime] = mapped_column(default=SAO_PAULO, nullable=False)
    data_atualizacao: Mapped[datetime] = mapped_column(default=SAO_PAULO, onupdate=SAO_PAULO, nullable=False)

@table_registry.mapped_as_dataclass
class AgendamentoModel:
    __tablename__ = "agendamentos"

    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    procedimento_id: Mapped[int] = mapped_column(ForeignKey("procedimentos.id"), nullable=False)
    data_hora: Mapped[datetime] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="pendente")  # pendente, confirmado, cancelado
    data_criacao: Mapped[datetime] = mapped_column(default=SAO_PAULO, nullable=False)
    data_atualizacao: Mapped[datetime] = mapped_column(default=SAO_PAULO, onupdate=SAO_PAULO, nullable=False)

@table_registry.mapped_as_dataclass
class TempoTrabalhoModel:
    __tablename__ = "tempos_trabalho"

    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    data_inicio: Mapped[datetime] = mapped_column(nullable=False)
    data_fim: Mapped[datetime] = mapped_column(nullable=False)
    data_criacao: Mapped[datetime] = mapped_column(default=SAO_PAULO, nullable=False)
    data_atualizacao: Mapped[datetime] = mapped_column(default=SAO_PAULO, onupdate=SAO_PAULO, nullable=False)
