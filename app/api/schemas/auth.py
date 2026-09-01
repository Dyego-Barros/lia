from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)


class UserResponse(BaseModel):
    id: int
    nome: str
    email: str
    role: str


class LoginResponse(BaseModel):
    token_type: str = "bearer"
    user: UserResponse
