from pydantic import BaseModel, Field


class WhatsAppIntegrationCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    tipo: str = Field(pattern="^(meta|ultramsg|evolution|openwa|twilio)$")
    credenciais: dict[str, str] = Field(min_length=1)
    webhook_token: str | None = None
    prioridade: int = Field(default=1, ge=1)
    ativo: bool = True


class WhatsAppIntegrationUpdate(WhatsAppIntegrationCreate):
    credenciais: dict[str, str] | None = None


class AIIntegrationCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    tipo: str = Field(pattern="^(openai|groq|ollama|anthropic|custom)$")
    modelo: str = Field(min_length=1, max_length=150)
    base_url: str | None = None
    api_key: str = Field(min_length=1)
    prioridade: int = Field(default=1, ge=1)
    ativo: bool = True


class AIIntegrationUpdate(AIIntegrationCreate):
    api_key: str | None = None


class ConversationStatusUpdate(BaseModel):
    status: str = Field(pattern="^(aberta|pendente|humano|encerrada)$")


class ConversationMessageCreate(BaseModel):
    conteudo: str = Field(min_length=1, max_length=4000)
