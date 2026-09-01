from datetime import date
import logging
from fastapi import APIRouter, Depends, HTTPException
from app.api.routes.dependencies import cliente_repository, procedimento_repository, agendamento_repository, tempo_trabalho_repository
from app.api.routes.auth import get_current_user
from app.api.schemas.atendimento import (
    CriarAgendamentoRequest, DisponibilidadeResponse, IdentificarClienteRequest,
    InformacoesProcedimentoResponse,
    ReagendarRequest,
)
from app.application.services.atendimento_service import AtendimentoService
from app.application.services.agendamento_service import AgendamentoService
from app.application.services.cliente_service import ClienteService
from app.application.services.procedimento_service import ProcedimentoService
from app.application.use_cases.clientes.identificar_cliente import IdentificarCliente
from app.application.use_cases.agendamentos.cadastrar_agendamento import CadastrarAgendamento
from app.application.use_cases.agendamentos.confirmar_agendamento import ConfirmarAgendamento
from app.application.use_cases.agendamentos.cancelar_agendamento import CancelarAgendamento
from app.application.use_cases.agendamentos.reagendar_agendamento import ReagendarAgendamento
from app.application.dto.agendamento import AgendamentoDto
from app.application.dto.cliente import ClienteDto
from app.application.dto.procedimento import ProcedimentoDto
from app.infrastructure.repositories.repositorie_cliente import ClienteRepository
from app.infrastructure.repositories.repositorie_procedimento import ProcedimentoRepository
from app.infrastructure.repositories.repositorie_agendamento import AgendamentoRepository
from app.infrastructure.repositories.repositorie_tempo_trabalho import TempoTrabalhoRepository
from app.infrastructure.database.db import get_session
from app.api.routes.integracoes import notify_appointment_confirmed
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/atendimento", tags=["Atendimento do agente"], dependencies=[Depends(get_current_user)])

def atendimento(clientes, procedimentos, agendamentos, tempos_trabalho=None):
    return AtendimentoService(clientes, procedimentos, agendamentos, tempos_trabalho)

@router.get("/procedimentos", response_model=list[ProcedimentoDto])
async def catalogo(busca: str | None = None, clientes: ClienteRepository = Depends(cliente_repository), procedimentos: ProcedimentoRepository = Depends(procedimento_repository), agendamentos: AgendamentoRepository = Depends(agendamento_repository)):
    return await atendimento(clientes, procedimentos, agendamentos).catalogo(busca)

@router.get("/procedimentos/{procedimento_id}", response_model=InformacoesProcedimentoResponse)
async def informacoes_procedimento(procedimento_id: int, procedimentos: ProcedimentoRepository = Depends(procedimento_repository)):
    try:
        procedimento = await ProcedimentoService(procedimentos).buscar(procedimento_id)
        mensagem = f"{procedimento.nome}: R$ {procedimento.preco:.2f}. Duração aproximada: {procedimento.duracao} minutos."
        return {"procedimento": procedimento, "mensagem_agente": mensagem}
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc

@router.post("/clientes/identificar", response_model=ClienteDto)
async def identificar_cliente(payload: IdentificarClienteRequest, repository: ClienteRepository = Depends(cliente_repository)):
    return await IdentificarCliente(ClienteService(repository)).execute(payload.telefone, payload.nome, payload.email)

@router.get("/disponibilidade", response_model=DisponibilidadeResponse)
async def disponibilidade(procedimento_id: int, data: date, clientes: ClienteRepository = Depends(cliente_repository), procedimentos: ProcedimentoRepository = Depends(procedimento_repository), agendamentos: AgendamentoRepository = Depends(agendamento_repository), tempos_trabalho: TempoTrabalhoRepository = Depends(tempo_trabalho_repository)):
    if data < date.today(): raise HTTPException(400, "A data não pode estar no passado.")
    try:
        horarios = await atendimento(clientes, procedimentos, agendamentos, tempos_trabalho).disponibilidade(procedimento_id, data)
        return {"procedimento_id": procedimento_id, "data": data, "horarios": horarios}
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc

@router.post("/agendamentos", response_model=AgendamentoDto, status_code=201)
async def criar_agendamento(payload: CriarAgendamentoRequest, clientes: ClienteRepository = Depends(cliente_repository), procedimentos: ProcedimentoRepository = Depends(procedimento_repository), agendamentos: AgendamentoRepository = Depends(agendamento_repository)):
    fluxo = atendimento(clientes, procedimentos, agendamentos)
    try:
        cliente = await fluxo.clientes.identificar_por_telefone(payload.telefone, payload.nome, payload.email)
        return await fluxo.iniciar_agendamento(cliente, payload.procedimento_id, payload.data_hora)
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc

@router.post("/agendamentos/{agendamento_id}/confirmar", response_model=AgendamentoDto)
async def confirmar_agendamento(agendamento_id: int, repository: AgendamentoRepository = Depends(agendamento_repository), clientes: ClienteRepository = Depends(cliente_repository), procedimentos: ProcedimentoRepository = Depends(procedimento_repository), session: AsyncSession = Depends(get_session)):
    try:
        agendamento = await ConfirmarAgendamento(AgendamentoService(repository)).execute(agendamento_id)
        try:
            cliente = await clientes.get_cliente_by_id(agendamento.cliente_id)
            procedimento = await procedimentos.buscar(agendamento.procedimento_id)
            await notify_appointment_confirmed(session, cliente, procedimento, agendamento.data_hora)
        except Exception:
            logger.exception("Falha ao enviar notificação de confirmação do agendamento %s", agendamento_id)
        return agendamento
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc

@router.post("/agendamentos/{agendamento_id}/cancelar", response_model=AgendamentoDto)
async def cancelar_agendamento(agendamento_id: int, repository: AgendamentoRepository = Depends(agendamento_repository)):
    try: return await CancelarAgendamento(AgendamentoService(repository)).execute(agendamento_id)
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc

@router.post("/agendamentos/{agendamento_id}/reagendar", response_model=AgendamentoDto)
async def reagendar_agendamento(agendamento_id: int, payload: ReagendarRequest, repository: AgendamentoRepository = Depends(agendamento_repository)):
    try: return await ReagendarAgendamento(AgendamentoService(repository)).execute(agendamento_id, payload.data_hora)
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc
