from pydantic import BaseModel, Field


class WhatsAppTestRequest(BaseModel):
    provider: str = "meta"
    telefone: str = Field(min_length=8)
    mensagem: str = Field(min_length=1, max_length=1000)


class AITestRequest(BaseModel):
    mensagem: str = Field(default="Responda apenas: OK", min_length=1, max_length=500)
