from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://lash:lash@localhost:5432/lash")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Database:
    def get_session(self):
        try:
            db = SessionLocal()
            yield db
        except Exception as e:
            print("Ocorreu um erro ao criar a sessão do banco de dados:", e)
            db.close()