
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config.config import DevelopmentConfig

DATABASE_URL = DevelopmentConfig.SQLALCHEMY_DATABASE_URI
async_engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

class Database:
    async def get_session(self):
        try:
            async with AsyncSessionLocal() as session:
                yield session
        except Exception:
            raise

get_session = Database().get_session
            
