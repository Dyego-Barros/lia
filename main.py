from fastapi import FastAPI
from app.infrastructure.models.models import table_registry
from app.infrastructure.database.db import engine

app = FastAPI()

#Cria tabelas no banco de dados 
table_registry.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API de Agendamento de Procedimentos!"}


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
