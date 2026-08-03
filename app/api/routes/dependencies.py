from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.db import get_session
from app.infrastructure.repositories.repositorie_cliente import ClienteRepository
from app.infrastructure.repositories.repositorie_procedimento import ProcedimentoRepository
from app.infrastructure.repositories.repositorie_agendamento import AgendamentoRepository

def cliente_repository(session: AsyncSession = Depends(get_session)):
    return ClienteRepository(session)

def procedimento_repository(session: AsyncSession = Depends(get_session)):
    return ProcedimentoRepository(session)

def agendamento_repository(session: AsyncSession = Depends(get_session)):
    return AgendamentoRepository(session)
