import logging

from fastapi import APIRouter, Depends, HTTPException

from app.agent.graph import run_agent
from app.api.routes.dependencies import (
    agendamento_repository,
    cliente_repository,
    procedimento_repository,
    tempo_trabalho_repository,
)
from app.api.routes.auth import get_current_user
from app.api.schemas.agente import AgenteMensagemRequest, AgenteMensagemResponse
from app.application.services.atendimento_service import AtendimentoService
from app.infrastructure.repositories.repositorie_agendamento import AgendamentoRepository
from app.infrastructure.repositories.repositorie_cliente import ClienteRepository
from app.infrastructure.repositories.repositorie_procedimento import ProcedimentoRepository
from app.infrastructure.repositories.repositorie_tempo_trabalho import TempoTrabalhoRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agente", tags=["Agente de IA"], dependencies=[Depends(get_current_user)])


@router.post("/mensagens", response_model=AgenteMensagemResponse)
async def conversar(
    payload: AgenteMensagemRequest,
    clientes: ClienteRepository = Depends(cliente_repository),
    procedimentos: ProcedimentoRepository = Depends(procedimento_repository),
    agendamentos: AgendamentoRepository = Depends(agendamento_repository),
    tempos_trabalho: TempoTrabalhoRepository = Depends(tempo_trabalho_repository),
):
    try:
        contexto = AtendimentoService(clientes, procedimentos, agendamentos, tempos_trabalho)
        resposta = await run_agent(payload.mensagem, payload.telefone, contexto)
        return {"telefone": payload.telefone, "resposta": resposta}
    except Exception as exc:
        logger.exception("Falha ao processar mensagem do agente de IA")
        raise HTTPException(503, "O agente de IA não está disponível no momento.") from exc
