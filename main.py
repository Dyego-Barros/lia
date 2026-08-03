from fastapi import FastAPI
from app.infrastructure.database.models.models import table_registry

app = FastAPI()
from app.api.routes import agendamentos_router, clientes_router, procedimentos_router, atendimento_router

app.include_router(clientes_router)
app.include_router(procedimentos_router)
app.include_router(agendamentos_router)
app.include_router(atendimento_router)

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API de Agendamento de Procedimentos!"}


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
