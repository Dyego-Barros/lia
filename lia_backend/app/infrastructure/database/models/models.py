from datetime import datetime, time
from typing import Optional
from sqlalchemy import ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, registry, mapped_column
from zoneinfo import ZoneInfo

SAO_PAULO = datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)

table_registry = registry()


@table_registry.mapped_as_dataclass
class UserModel:
    __tablename__ = "usuarios"

    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(nullable=False, default="atendente")
    ativo: Mapped[bool] = mapped_column(nullable=False, default=True)
    data_criacao: Mapped[datetime] = mapped_column(default=SAO_PAULO, nullable=False)


@table_registry.mapped_as_dataclass
class ProfissionalModel:
    __tablename__ = "profissionais"
    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    telefone: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    especialidade: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    ativo: Mapped[bool] = mapped_column(nullable=False, default=True)
    data_criacao: Mapped[datetime] = mapped_column(default=SAO_PAULO, nullable=False)


@table_registry.mapped_as_dataclass
class HorarioProfissionalModel:
    __tablename__ = "horarios_profissionais"
    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    profissional_id: Mapped[int] = mapped_column(ForeignKey("profissionais.id"), nullable=False)
    weekday: Mapped[int] = mapped_column(nullable=False)
    inicio: Mapped[time] = mapped_column(nullable=False)
    fim: Mapped[time] = mapped_column(nullable=False)


@table_registry.mapped_as_dataclass
class BloqueioAgendaModel:
    __tablename__ = "bloqueios_agenda"
    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    inicio: Mapped[datetime] = mapped_column(nullable=False)
    fim: Mapped[datetime] = mapped_column(nullable=False)
    motivo: Mapped[str] = mapped_column(nullable=False)
    profissional_id: Mapped[Optional[int]] = mapped_column(ForeignKey("profissionais.id"), default=None, nullable=True)


@table_registry.mapped_as_dataclass
class ListaEsperaModel:
    __tablename__ = "lista_espera"
    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    procedimento_id: Mapped[int] = mapped_column(ForeignKey("procedimentos.id"), nullable=False)
    data_preferida: Mapped[Optional[datetime]] = mapped_column(default=None, nullable=True)
    periodo: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    profissional_id: Mapped[Optional[int]] = mapped_column(ForeignKey("profissionais.id"), default=None, nullable=True)
    status: Mapped[str] = mapped_column(nullable=False, default="aguardando")
    data_criacao: Mapped[datetime] = mapped_column(default=SAO_PAULO, nullable=False)


@table_registry.mapped_as_dataclass
class PagamentoModel:
    __tablename__ = "pagamentos"
    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    agendamento_id: Mapped[int] = mapped_column(ForeignKey("agendamentos.id"), nullable=False)
    valor: Mapped[float] = mapped_column(nullable=False)
    forma: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="pago")
    pago_em: Mapped[datetime] = mapped_column(default=SAO_PAULO, nullable=False)


@table_registry.mapped_as_dataclass
class PacoteModel:
    __tablename__ = "pacotes"
    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(nullable=False)
    preco: Mapped[float] = mapped_column(nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    ativo: Mapped[bool] = mapped_column(nullable=False, default=True)


@table_registry.mapped_as_dataclass
class PacoteProcedimentoModel:
    __tablename__ = "pacotes_procedimentos"
    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    pacote_id: Mapped[int] = mapped_column(ForeignKey("pacotes.id"), nullable=False)
    procedimento_id: Mapped[int] = mapped_column(ForeignKey("procedimentos.id"), nullable=False)
    quantidade: Mapped[int] = mapped_column(nullable=False, default=1)


@table_registry.mapped_as_dataclass
class AvaliacaoModel:
    __tablename__ = "avaliacoes"
    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    agendamento_id: Mapped[int] = mapped_column(ForeignKey("agendamentos.id"), nullable=False)
    nota: Mapped[int] = mapped_column(nullable=False)
    comentario: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    data_criacao: Mapped[datetime] = mapped_column(default=SAO_PAULO, nullable=False)


@table_registry.mapped_as_dataclass
class EstoqueProdutoModel:
    __tablename__ = "estoque_produtos"
    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    quantidade: Mapped[int] = mapped_column(nullable=False, default=0)
    estoque_minimo: Mapped[int] = mapped_column(nullable=False, default=0)
    custo_unitario: Mapped[float] = mapped_column(nullable=False, default=0)
    ativo: Mapped[bool] = mapped_column(nullable=False, default=True)

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
    custo_materiais: Mapped[float] = mapped_column(nullable=False, default=0)
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
    profissional_id: Mapped[Optional[int]] = mapped_column(ForeignKey("profissionais.id"), default=None, nullable=True)
    status: Mapped[str] = mapped_column(nullable=False, default="pendente")  # pendente, confirmado, cancelado
    valor_cobrado: Mapped[Optional[float]] = mapped_column(default=None, nullable=True)
    forma_pagamento: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    status_pagamento: Mapped[str] = mapped_column(nullable=False, default="pendente")
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


@table_registry.mapped_as_dataclass
class ProcessedWebhookMessageModel:
    __tablename__ = "processed_webhook_messages"
    __table_args__ = (
        UniqueConstraint("provider", "message_id", name="uq_processed_webhook_provider_message"),
    )

    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(nullable=False)
    message_id: Mapped[str] = mapped_column(nullable=False)
    processed_at: Mapped[datetime] = mapped_column(default=SAO_PAULO, nullable=False)


@table_registry.mapped_as_dataclass
class WhatsAppIntegrationModel:
    __tablename__ = "whatsapp_integrations"
    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(nullable=False)
    tipo: Mapped[str] = mapped_column(nullable=False)
    credenciais_encriptadas: Mapped[str] = mapped_column(Text, nullable=False)
    webhook_token_encriptado: Mapped[Optional[str]] = mapped_column(Text, default=None, nullable=True)
    prioridade: Mapped[int] = mapped_column(nullable=False, default=1)
    ativo: Mapped[bool] = mapped_column(nullable=False, default=True)
    data_criacao: Mapped[datetime] = mapped_column(default=SAO_PAULO, nullable=False)


@table_registry.mapped_as_dataclass
class AIIntegrationModel:
    __tablename__ = "ai_integrations"
    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(nullable=False)
    tipo: Mapped[str] = mapped_column(nullable=False)
    modelo: Mapped[str] = mapped_column(nullable=False)
    api_key_encriptada: Mapped[str] = mapped_column(Text, nullable=False)
    base_url: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    prioridade: Mapped[int] = mapped_column(nullable=False, default=1)
    ativo: Mapped[bool] = mapped_column(nullable=False, default=True)
    data_criacao: Mapped[datetime] = mapped_column(default=SAO_PAULO, nullable=False)


@table_registry.mapped_as_dataclass
class WhatsAppConversationModel:
    __tablename__ = "whatsapp_conversations"
    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    integration_id: Mapped[int] = mapped_column(ForeignKey("whatsapp_integrations.id"), nullable=False)
    telefone: Mapped[str] = mapped_column(nullable=False)
    nome_contato: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    status: Mapped[str] = mapped_column(nullable=False, default="aberta")
    ultima_mensagem_em: Mapped[datetime] = mapped_column(default=SAO_PAULO, nullable=False)


@table_registry.mapped_as_dataclass
class WhatsAppMessageModel:
    __tablename__ = "whatsapp_messages"
    id: Mapped[Optional[int]] = mapped_column(init=False, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("whatsapp_conversations.id"), nullable=False)
    direcao: Mapped[str] = mapped_column(nullable=False)
    conteudo: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    tipo: Mapped[str] = mapped_column(nullable=False, default="text")
    enviado_em: Mapped[datetime] = mapped_column(default=SAO_PAULO, nullable=False)
