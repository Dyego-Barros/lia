from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from app.api.routes.dependencies import agendamento_repository, procedimento_repository, tempo_trabalho_repository
from app.api.routes.auth import get_current_user
from app.api.schemas.agendamentos import AgendamentoCreate
from app.application.dto.agendamento import AgendamentoDto
from app.application.services.agendamento_service import AgendamentoService
from app.application.use_cases.agendamentos.buscar_agendamento import BuscarAgendamento
from app.application.use_cases.agendamentos.listar_agendamentos import ListarAgendamentos
from app.application.use_cases.agendamentos.atualizar_agendamento import AtualizarAgendamento
from app.application.use_cases.agendamentos.excluir_agendamento import ExcluirAgendamento
from app.infrastructure.repositories.repositorie_agendamento import AgendamentoRepository
from app.infrastructure.repositories.repositorie_procedimento import ProcedimentoRepository
from app.infrastructure.repositories.repositorie_tempo_trabalho import TempoTrabalhoRepository
from app.application.services.atendimento_service import AtendimentoService
from app.domain.exceptions.agendamentos import AgendamentoConflictException
from app.infrastructure.database.models.models import ConsumoMaterialModel, EstoqueProdutoModel, PagamentoModel, ProcedimentoMaterialModel

router = APIRouter(prefix="/agendamentos", tags=["Agendamentos"], dependencies=[Depends(get_current_user)])
SAO_PAULO = ZoneInfo("America/Sao_Paulo")


def normalizar_data_hora(valor: datetime) -> datetime:
    """Mantém a agenda no horário local sem offset, como o banco atual armazena."""
    if valor.tzinfo is not None:
        valor = valor.astimezone(SAO_PAULO).replace(tzinfo=None)
    return valor


def dados_agendamento(payload: AgendamentoCreate, data_hora: datetime) -> dict:
    dados = payload.model_dump()
    dados["data_hora"] = data_hora
    return dados


async def registrar_consumo_ao_concluir(repository: AgendamentoRepository, agendamento_id: int, procedimento_id: int) -> None:
    session = repository.session
    if (await session.execute(select(ConsumoMaterialModel.id).where(ConsumoMaterialModel.agendamento_id == agendamento_id).limit(1))).scalar_one_or_none():
        return
    vinculos = (await session.execute(select(ProcedimentoMaterialModel).where(ProcedimentoMaterialModel.procedimento_id == procedimento_id))).scalars().all()
    produtos = {}
    for vinculo in vinculos:
        produto = await session.get(EstoqueProdutoModel, vinculo.produto_id, with_for_update=True)
        if not produto or produto.quantidade < vinculo.quantidade:
            nome = produto.nome if produto else f"#{vinculo.produto_id}"
            raise HTTPException(409, f"Estoque insuficiente para concluir: {nome}.")
        produtos[vinculo.produto_id] = produto
    for vinculo in vinculos:
        produto = produtos[vinculo.produto_id]
        produto.quantidade -= vinculo.quantidade
        session.add(ConsumoMaterialModel(agendamento_id=agendamento_id, produto_id=produto.id, quantidade=vinculo.quantidade, custo_unitario=produto.custo_unitario))


async def sincronizar_pagamento(repository: AgendamentoRepository, agendamento_id: int, payload: AgendamentoCreate) -> None:
    session = repository.session
    pagamento = (await session.execute(select(PagamentoModel).where(PagamentoModel.agendamento_id == agendamento_id))).scalar_one_or_none()
    if payload.status_pagamento != "pago":
        if pagamento:
            await session.delete(pagamento)
        return
    if pagamento:
        pagamento.valor = payload.valor_cobrado
        pagamento.forma = payload.forma_pagamento
        pagamento.status = "pago"
        pagamento.pago_em = datetime.now()
    else:
        session.add(PagamentoModel(agendamento_id=agendamento_id, valor=payload.valor_cobrado, forma=payload.forma_pagamento, status="pago"))

@router.post("/", response_model=AgendamentoDto, status_code=status.HTTP_201_CREATED)
async def criar(payload: AgendamentoCreate, repository: AgendamentoRepository = Depends(agendamento_repository), procedimentos: ProcedimentoRepository = Depends(procedimento_repository), tempos: TempoTrabalhoRepository = Depends(tempo_trabalho_repository)):
    try:
        if payload.profissional_id is None:
            raise HTTPException(400, "Selecione uma profissional para criar o agendamento.")
        data_hora = normalizar_data_hora(payload.data_hora)
        # Este endpoint alimenta a tela administrativa, que também é usada para
        # lançar horários livres (inclusive minutos fora da grade de sugestões
        # do bot), desde que estejam integralmente dentro da escala.
        motivo = await AtendimentoService(None, procedimentos, repository, tempos).motivo_indisponibilidade(
            payload.procedimento_id,
            data_hora,
            payload.profissional_id,
        )
        if motivo:
            raise HTTPException(409, motivo)
        criado = await AgendamentoService(repository).criar(
            AgendamentoDto(**dados_agendamento(payload, data_hora)),
            permitir_data_passada=True,
        )
        await sincronizar_pagamento(repository, criado.id, payload)
        await repository.session.commit()
        return criado
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
        if payload.profissional_id is None:
            raise HTTPException(400, "Selecione uma profissional para atualizar o agendamento.")
        data_hora = normalizar_data_hora(payload.data_hora)
        existente = await AgendamentoService(repository).buscar(agendamento_id)
        horario_foi_alterado = (
            normalizar_data_hora(existente.data_hora) != data_hora
            or existente.profissional_id != payload.profissional_id
            or existente.procedimento_id != payload.procedimento_id
        )

        # Alterar status ou pagamento não muda a reserva e, portanto, não deve
        # revalidar um horário que já passou ou uma escala alterada depois dela.
        if horario_foi_alterado:
            motivo = await AtendimentoService(None, procedimentos, repository, tempos).motivo_indisponibilidade(
                payload.procedimento_id, data_hora, payload.profissional_id, agendamento_id,
            )
            if motivo:
                raise HTTPException(409, motivo)
        if payload.status.value == "concluido" and existente.status != "concluido":
            await registrar_consumo_ao_concluir(repository, agendamento_id, payload.procedimento_id)
        await sincronizar_pagamento(repository, agendamento_id, payload)
        return await AtualizarAgendamento(AgendamentoService(repository)).execute(AgendamentoDto(id=agendamento_id, **dados_agendamento(payload, data_hora)))
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc

@router.delete("/{agendamento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover(agendamento_id: int, repository: AgendamentoRepository = Depends(agendamento_repository)):
    try: await ExcluirAgendamento(AgendamentoService(repository)).execute(agendamento_id)
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc
