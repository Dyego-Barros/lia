from pydantic import BaseModel, EmailStr,field_validator
from typing import Optional
from app.domain.exceptions.domainException import DomainException

class Cliente(BaseModel):
    id: Optional[int] = None
    nome: str
    email: Optional[EmailStr] = None
    status: Optional[bool] = True
    telefone: Optional[str] = None  
    
    
    
    model_config = {
        "from_attributes": True,
        "validate_assignment": True
    }
    
    @field_validator("nome")
    @classmethod
    def validar_nome(cls, nome):
        if not nome or len(nome) < 3:
            raise ValueError("O nome do cliente é muito curto. Deve ter pelo menos 3 caracteres.")
        return nome
    
    
    @field_validator("email")
    @classmethod
    def validar_email(cls, email):
        if email and "@" not in email:
            raise ValueError("O email do cliente é inválido.")
        return email
    
        
    def normalizar_telefone(self):
        # Lógica para normalizar o telefone do cliente
        if self.telefone:
            # Remove espaços, traços e parênteses
            self.telefone = ''.join(filter(str.isdigit, self.telefone))
            
    def ativar(self):
        self.status = True
        
    def desativar(self):
        self.status = False