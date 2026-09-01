from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.routes.dependencies import agendamento_repository, procedimento_repository, tempo_trabalho_repository
from app.api.routes.auth import get_current_user
from app.api.schemas.agendamentos import AgendamentoCreate
from app.application.dto.agendamento import AgendamentoDto
from app.application.services.agendamento_service import AgendamentoService
from app.application.use_cases.agendamentos.cadastrar_agendamento import CadastrarAgendamento
from app.application.use_cases.agendamentos.buscar_agendamento import BuscarAgendamento
from app.application.use_cases.agendamentos.listar_agendamentos import ListarAgendamentos
from app.application.use_cases.agendamentos.atualizar_agendamento import AtualizarAgendamento
from app.application.use_cases.agendamentos.excluir_agendamento import ExcluirAgendamento
from app.infrastructure.repositories.repositorie_agendamento import AgendamentoRepository
from app.infrastructure.repositories.repositorie_procedimento import ProcedimentoRepository
from app.infrastructure.repositories.repositorie_tempo_trabalho import TempoTrabalhoRepository
from app.domain.exceptions.agendamentos import AgendamentoConflictException

router = APIRouter(prefix="/agendamentos", tags=["Agendamentos"], dependencies=[Depends(get_current_user)])

@router.post("/", response_model=AgendamentoDto, status_code=status.HTTP_201_CREATED)
async def criar(payload: AgendamentoCreate, repository: AgendamentoRepository = Depends(agendamento_repository), procedimentos: ProcedimentoRepository = Depends(procedimento_repository), tempos: TempoTrabalhoRepository = Depends(tempo_trabalho_repository)):
    try:
        procedimento = await procedimentos.buscar(payload.procedimento_id)
        fim = payload.data_hora + timedelta(minutes=procedimento.duracao)
        bloqueios = await tempos.listar_bloqueios_por_dia(payload.data_hora.date())
        if any(payload.data_hora < bloqueio_fim and fim > bloqueio_inicio for bloqueio_inicio, bloqueio_fim in bloqueios):
            raise HTTPException(409, "O horário está dentro de um bloqueio de agenda.")
        return await CadastrarAgendamento(AgendamentoService(repository)).execute(AgendamentoDto(**payload.model_dump()))
    except AgendamentoConflictException as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

@router.get("/", response_model=list[AgendamentoDto])
async def listar(repository: AgendamentoRepository = Depends(agendamento_repository)):
    return await ListarAgendamentos(AgendamentoService(repository)).execute()

@router.get("/{agendamento_id}", response_model=AgendamentoDto)
async def buscar(agendamento_id: int, repository: AgendamentoRepository = Depends(agendamento_repository)):
    try: return await BuscarAgendamento(AgendamentoService(repository)).execute(agendamento_id)
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc

@router.put("/{agendamento_id}", response_model=AgendamentoDto)
async def atualizar(agendamento_id: int, payload: AgendamentoCreate, repository: AgendamentoRepository = Depends(agendamento_repository), procedimentos: ProcedimentoRepository = Depends(procedimento_repository), tempos: TempoTrabalhoRepository = Depends(tempo_trabalho_repository)):
    try:
        procedimento = await procedimentos.buscar(payload.procedimento_id)
        fim = payload.data_hora + timedelta(minutes=procedimento.duracao)
        bloqueios = await tempos.listar_bloqueios_por_dia(payload.data_hora.date())
        if any(payload.data_hora < bloqueio_fim and fim > bloqueio_inicio for bloqueio_inicio, bloqueio_fim in bloqueios):
            raise HTTPException(409, "O horário está dentro de um bloqueio de agenda.")
        return await AtualizarAgendamento(AgendamentoService(repository)).execute(AgendamentoDto(id=agendamento_id, **payload.model_dump()))
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc

@router.delete("/{agendamento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover(agendamento_id: int, repository: AgendamentoRepository = Depends(agendamento_repository)):
    try: await ExcluirAgendamento(AgendamentoService(repository)).execute(agendamento_id)
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc
