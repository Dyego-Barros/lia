import os

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.auth import LoginRequest, LoginResponse, UserResponse
from app.infrastructure.database.db import get_session
from app.infrastructure.database.models.models import UserModel
from app.infrastructure.security.auth import create_token, decode_token, verify_password

router = APIRouter(prefix="/auth", tags=["Autenticação"])
bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    lia_session: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_session),
) -> UserModel:
    token = credentials.credentials if credentials else lia_session
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Autenticação necessária")
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except (ValueError, KeyError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido ou expirado")
    user = await session.get(UserModel, user_id)
    if not user or not user.ativo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário inativo")
    return user


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, http_response: Response, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(UserModel).where(UserModel.email == payload.email.lower().strip()))
    user = result.scalar_one_or_none()
    if not user or not user.ativo or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos")
    user_response = UserResponse(id=user.id, nome=user.nome, email=user.email, role=user.role)
    token = create_token(user.id, user.role)
    http_response.set_cookie(
        "lia_session",
        token,
        httponly=True,
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        samesite="strict",
        max_age=8 * 60 * 60,
        path="/",
    )
    return {"token_type": "bearer", "user": user_response}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie("lia_session", path="/")


@router.get("/me", response_model=UserResponse)
async def me(user: UserModel = Depends(get_current_user)):
    return UserResponse(id=user.id, nome=user.nome, email=user.email, role=user.role)


async def require_admin(user: UserModel = Depends(get_current_user)) -> UserModel:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Permissão de administrador necessária")
    return user
