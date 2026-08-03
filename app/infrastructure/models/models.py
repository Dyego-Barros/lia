from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, registry, mapped_column

table_registry = registry()

@table_registry.mapped_as_dataclass
class Procedimento:
    __tablename__ = "procedimentos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(nullable=True)
    preco: Mapped[float] = mapped_column(nullable=False)
    duracao: Mapped[int] = mapped_column(nullable=False)  # duração em minutos
    data_criacao: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    data_atualizacao: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    

@table_registry.mapped_as_dataclass
class Cliente:
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[Optional[str]] = mapped_column(nullable=True)
    telefone: Mapped[Optional[str]] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(nullable=False, default="ativo")
    data_criacao: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    data_atualizacao: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
@table_registry.mapped_as_dataclass
class Agendamento:
    __tablename__ = "agendamentos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    procedimento_id: Mapped[int] = mapped_column(ForeignKey("procedimentos.id"), nullable=False)
    data_hora: Mapped[datetime] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="pendente")  # pendente, confirmado, cancelado
    data_criacao: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    data_atualizacao: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
@table_registry.mapped_as_dataclass
class TempoTrabalho:
    __tablename__ = "tempos_trabalho"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    data_inicio: Mapped[datetime] = mapped_column(nullable=False)
    data_fim: Mapped[datetime] = mapped_column(nullable=False)
    data_criacao: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    data_atualizacao: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
