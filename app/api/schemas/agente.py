from pydantic import BaseModel, Field


class AgenteMensagemRequest(BaseModel):
    telefone: str = Field(min_length=8, max_length=20)
    mensagem: str = Field(min_length=1, max_length=4000)


class AgenteMensagemResponse(BaseModel):
    telefone: str
    resposta: str
