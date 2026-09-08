import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.infrastructure.database.models.models import table_registry
from app.domain.exceptions.domainException import DomainException

app = FastAPI()


def _configured_cors_origins() -> set[str]:
    raw_origins = os.getenv("CORS_ORIGINS", "").strip()
    if raw_origins:
        return {origin.strip().rstrip("/") for origin in raw_origins.split(",") if origin.strip()}
    if os.getenv("APP_ENV", "production").lower() in {"development", "dev", "test"}:
        return {"http://localhost:3000", "http://127.0.0.1:3000", "http://frontend:3000"}
    # Produção padrão: frontend e API no mesmo domínio, sem CORS aberto.
    return set()


def _trusted_origins(request: Request) -> set[str]:
    configured = _configured_cors_origins()
    # A instalação padrão usa o frontend e a API no mesmo domínio, através
    # do proxy reverso. Aceitar a origem efetiva evita depender de um domínio
    # fixo e continua rejeitando sites de terceiros.
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    scheme = (request.headers.get("x-forwarded-proto") or request.url.scheme).split(",")[0].strip()
    if host:
        configured.add(f"{scheme}://{host}".rstrip("/"))
    return configured


@app.middleware("http")
async def csrf_protection(request: Request, call_next):
    """Protege alterações autenticadas por cookie contra requisições cross-site."""
    unsafe_method = request.method in {"POST", "PUT", "PATCH", "DELETE"}
    cookie_session = request.cookies.get("lia_session")
    bearer_token = request.headers.get("authorization")
    if unsafe_method and cookie_session and not bearer_token:
        origin = request.headers.get("origin", "").rstrip("/")
        if not origin or origin not in _trusted_origins(request):
            return JSONResponse(status_code=403, content={"detail": "Origem não autorizada."})
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(_configured_cors_origins()),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



from app.api.routes import (
    agendamentos_router,
    clientes_router,
    procedimentos_router,
    atendimento_router,
    agente_router,
    auth_router,
    relatorios_router,
    operacoes_router,
    configuracoes_router,
    integracoes_router,
    integracoes_webhook_router,
)

app.include_router(clientes_router)
app.include_router(procedimentos_router)
app.include_router(agendamentos_router)
app.include_router(atendimento_router)
app.include_router(agente_router)
app.include_router(auth_router)
app.include_router(relatorios_router)
app.include_router(operacoes_router)
app.include_router(configuracoes_router)
app.include_router(integracoes_router)
app.include_router(integracoes_webhook_router)



@app.exception_handler(DomainException)
async def handle_domain_exception(request: Request, exc: DomainException):
    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc),
            "error": exc.__class__.__name__,
        },
    )

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API de Agendamento de Procedimentos!"}


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
