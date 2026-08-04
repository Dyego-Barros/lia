from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.infrastructure.database.models.models import table_registry
from app.domain.exceptions.domainException import DomainException

app = FastAPI()
from app.api.routes import (
    agendamentos_router,
    clientes_router,
    procedimentos_router,
    atendimento_router,
    agente_router,
    whatsapp_router,
    ultramsg_router,
)

app.include_router(clientes_router)
app.include_router(procedimentos_router)
app.include_router(agendamentos_router)
app.include_router(atendimento_router)
app.include_router(agente_router)
app.include_router(whatsapp_router)
app.include_router(ultramsg_router)


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
