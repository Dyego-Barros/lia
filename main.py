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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://frontend:3000"
        ).split(",")
        if origin.strip()
    ],
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
