
import os


class BaseConfig:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://lash:lash@localhost:5432/lash",
    )
    POOL_SIZE = 5
    MAX_OVERFLOW = 10
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 1800


class ProductionConfig(BaseConfig):
    pass


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI= os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://lash:lash@postgres:5432/lash",
    )
