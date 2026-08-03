from pydantic import BaseModel, field_validator
from typing import Optional
from app.domain.exceptions.domainException import DomainException


class Procedimento(BaseModel):
    id: Optional[int] = None
    nome: str
    descricao: Optional[str] = None
    preco: float
    duracao: int  # duração em minutos
    indicacoes: Optional[str] = None
    contraindicacoes: Optional[str] = None
    cuidados: Optional[str] = None

    model_config = {
        "from_attributes": True,
        "validate_assignment": True
    }

    @field_validator("preco")
    @classmethod
    def validar_preco(cls, preco):
        if preco < 0:
            raise DomainException("O preço do procedimento não pode ser negativo.")
        return preco
    
    @field_validator("duracao")
    @classmethod
    def validar_duracao(cls, duracao):     
        if duracao <= 0:
            raise DomainException("A duração do procedimento deve ser maior que zero.")
        return duracao
    
    def atualizar_preco(self, novo_preco: float):
        if novo_preco < 0:
            raise DomainException("O preço do procedimento não pode ser negativo.")
        self.preco = novo_preco
    
    def atualizar_duracao(self, nova_duracao: int):
        if nova_duracao <= 0:
            raise DomainException("A duração do procedimento deve ser maior que zero.")
        self.duracao = nova_duracao
       
