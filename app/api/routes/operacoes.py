from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_user, require_admin
from app.api.schemas.operacoes import BlockCreate, PackageCreate, PackageItemCreate, PaymentCreate, ProfessionalCreate, ProfessionalUpdate, ReviewCreate, ScheduleCreate, ScheduleUpdate, StockProductCreate, UserCreate, WaitlistCreate, WaitlistPromote, WaitlistStatusUpdate
from app.infrastructure.database.db import get_session
from app.infrastructure.database.models.models import AgendamentoModel, AvaliacaoModel, BloqueioAgendaModel, EstoqueProdutoModel, HorarioProfissionalModel, ListaEsperaModel, PacoteModel, PacoteProcedimentoModel, PagamentoModel, ProfissionalModel, UserModel
from app.infrastructure.security.auth import hash_password

router = APIRouter(prefix="/operacoes", tags=["Operações"], dependencies=[Depends(get_current_user)])


@router.post("/usuarios", status_code=status.HTTP_201_CREATED)
async def criar_usuario(payload: UserCreate, session: AsyncSession = Depends(get_session), _: UserModel = Depends(require_admin)):
    user = UserModel(nome=payload.nome, email=payload.email.lower().strip(), password_hash=hash_password(payload.password), role=payload.role)
    session.add(user); await session.commit(); await session.refresh(user)
    return {"id": user.id, "nome": user.nome, "email": user.email, "role": user.role}


@router.get("/usuarios")
async def listar_usuarios(session: AsyncSession = Depends(get_session), _: UserModel = Depends(require_admin)):
    users = (await session.execute(select(UserModel))).scalars().all()
    return [{"id": user.id, "nome": user.nome, "email": user.email, "role": user.role, "ativo": user.ativo} for user in users]


@router.post("/profissionais", status_code=status.HTTP_201_CREATED)
async def criar_profissional(payload: ProfessionalCreate, session: AsyncSession = Depends(get_session)):
    item = ProfissionalModel(**payload.model_dump()); session.add(item); await session.commit(); await session.refresh(item); return item


@router.get("/profissionais")
async def listar_profissionais(session: AsyncSession = Depends(get_session)):
    return (await session.execute(select(ProfissionalModel).order_by(ProfissionalModel.nome))).scalars().all()


@router.put("/profissionais/{professional_id}")
async def atualizar_profissional(professional_id: int, payload: ProfessionalUpdate, session: AsyncSession = Depends(get_session), _: UserModel = Depends(require_admin)):
    item = await session.get(ProfissionalModel, professional_id)
    if not item: raise HTTPException(404, "Profissional não encontrado")
    for key, value in payload.model_dump().items(): setattr(item, key, value)
    await session.commit(); await session.refresh(item)
    return item


@router.patch("/profissionais/{professional_id}/status")
async def alterar_status_profissional(professional_id: int, ativo: bool, session: AsyncSession = Depends(get_session), _: UserModel = Depends(require_admin)):
    item = await session.get(ProfissionalModel, professional_id)
    if not item: raise HTTPException(404, "Profissional não encontrado")
    item.ativo = ativo; await session.commit()
    return {"id": item.id, "ativo": item.ativo}


@router.delete("/profissionais/{professional_id}")
async def remover_profissional(professional_id: int, session: AsyncSession = Depends(get_session), _: UserModel = Depends(require_admin)):
    item = await session.get(ProfissionalModel, professional_id)
    if not item: raise HTTPException(404, "Profissional não encontrado")
    appointments = (await session.execute(select(AgendamentoModel.id).where(AgendamentoModel.profissional_id == professional_id).limit(1))).scalar_one_or_none()
    if appointments:
        item.ativo = False
        await session.commit()
        return {"id": item.id, "ativo": False, "message": "Profissional desativado para preservar o histórico."}
    await session.delete(item); await session.commit()
    return {"id": professional_id, "removido": True}


@router.post("/horarios", status_code=status.HTTP_201_CREATED)
async def criar_horario(payload: ScheduleCreate, session: AsyncSession = Depends(get_session)):
    item = HorarioProfissionalModel(**payload.model_dump()); session.add(item); await session.commit(); await session.refresh(item); return item


@router.get("/horarios")
async def listar_horarios(session: AsyncSession = Depends(get_session)):
    return (await session.execute(select(HorarioProfissionalModel))).scalars().all()


@router.put("/horarios/{schedule_id}")
async def atualizar_horario(schedule_id: int, payload: ScheduleUpdate, session: AsyncSession = Depends(get_session), _: UserModel = Depends(require_admin)):
    item = await session.get(HorarioProfissionalModel, schedule_id)
    if not item: raise HTTPException(404, "Horário não encontrado")
    for key, value in payload.model_dump().items(): setattr(item, key, value)
    await session.commit(); await session.refresh(item)
    return item


@router.delete("/horarios/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_horario(schedule_id: int, session: AsyncSession = Depends(get_session), _: UserModel = Depends(require_admin)):
    item = await session.get(HorarioProfissionalModel, schedule_id)
    if not item: raise HTTPException(404, "Horário não encontrado")
    await session.delete(item); await session.commit()


@router.post("/bloqueios", status_code=status.HTTP_201_CREATED)
async def criar_bloqueio(payload: BlockCreate, session: AsyncSession = Depends(get_session)):
    if payload.fim <= payload.inicio: raise HTTPException(400, "O fim deve ser posterior ao início")
    item = BloqueioAgendaModel(**payload.model_dump()); session.add(item); await session.commit(); await session.refresh(item); return item


@router.get("/bloqueios")
async def listar_bloqueios(session: AsyncSession = Depends(get_session)):
    return (await session.execute(select(BloqueioAgendaModel).order_by(BloqueioAgendaModel.inicio))).scalars().all()


@router.post("/lista-espera", status_code=status.HTTP_201_CREATED)
async def entrar_lista_espera(payload: WaitlistCreate, session: AsyncSession = Depends(get_session)):
    item = ListaEsperaModel(**payload.model_dump()); session.add(item); await session.commit(); await session.refresh(item); return item


@router.get("/lista-espera")
async def listar_lista_espera(session: AsyncSession = Depends(get_session)):
    return (await session.execute(select(ListaEsperaModel).order_by(ListaEsperaModel.data_criacao.desc()))).scalars().all()


@router.patch("/lista-espera/{waitlist_id}")
async def atualizar_status_lista_espera(waitlist_id: int, payload: WaitlistStatusUpdate, session: AsyncSession = Depends(get_session)):
    item = await session.get(ListaEsperaModel, waitlist_id)
    if not item: raise HTTPException(404, "Registro da lista de espera não encontrado")
    item.status = payload.status; await session.commit()
    return item


@router.delete("/lista-espera/{waitlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_lista_espera(waitlist_id: int, session: AsyncSession = Depends(get_session)):
    item = await session.get(ListaEsperaModel, waitlist_id)
    if not item: raise HTTPException(404, "Registro da lista de espera não encontrado")
    await session.delete(item); await session.commit()


@router.post("/lista-espera/{waitlist_id}/promover")
async def promover_lista_espera(waitlist_id: int, payload: WaitlistPromote, session: AsyncSession = Depends(get_session)):
    item = await session.get(ListaEsperaModel, waitlist_id)
    if not item: raise HTTPException(404, "Registro da lista de espera não encontrado")
    if item.status not in ("aguardando", "notificado"): raise HTTPException(409, "Este registro não está disponível para promoção")
    if payload.data_hora <= datetime.now(): raise HTTPException(400, "A data do agendamento deve ser futura")
    if payload.profissional_id:
        professional = await session.get(ProfissionalModel, payload.profissional_id)
        if not professional or not professional.ativo: raise HTTPException(400, "Profissional inválido ou inativo")
    appointment = AgendamentoModel(cliente_id=item.cliente_id, procedimento_id=item.procedimento_id, profissional_id=payload.profissional_id, data_hora=payload.data_hora, status="pendente")
    session.add(appointment); item.status = "convertido"
    await session.commit(); await session.refresh(appointment)
    return {"agendamento_id": appointment.id, "lista_espera_id": item.id, "status": item.status}


@router.post("/pagamentos", status_code=status.HTTP_201_CREATED)
async def registrar_pagamento(payload: PaymentCreate, session: AsyncSession = Depends(get_session)):
    item = PagamentoModel(**payload.model_dump()); session.add(item)
    appointment = await session.get(AgendamentoModel, payload.agendamento_id)
    if not appointment: raise HTTPException(404, "Agendamento não encontrado")
    appointment.valor_cobrado = payload.valor; appointment.forma_pagamento = payload.forma; appointment.status_pagamento = payload.status
    await session.commit(); await session.refresh(item); return item


@router.get("/pagamentos")
async def listar_pagamentos(session: AsyncSession = Depends(get_session)):
    return (await session.execute(select(PagamentoModel).order_by(PagamentoModel.pago_em.desc()))).scalars().all()


@router.post("/pacotes", status_code=status.HTTP_201_CREATED)
async def criar_pacote(payload: PackageCreate, session: AsyncSession = Depends(get_session)):
    item = PacoteModel(**payload.model_dump()); session.add(item); await session.commit(); await session.refresh(item); return item


@router.get("/pacotes")
async def listar_pacotes(session: AsyncSession = Depends(get_session)):
    return (await session.execute(select(PacoteModel))).scalars().all()


@router.post("/pacotes/procedimentos", status_code=status.HTTP_201_CREATED)
async def adicionar_procedimento_pacote(payload: PackageItemCreate, session: AsyncSession = Depends(get_session)):
    item = PacoteProcedimentoModel(**payload.model_dump()); session.add(item); await session.commit(); await session.refresh(item); return item


@router.get("/pacotes/procedimentos")
async def listar_procedimentos_pacotes(session: AsyncSession = Depends(get_session)):
    return (await session.execute(select(PacoteProcedimentoModel))).scalars().all()


@router.post("/avaliacoes", status_code=status.HTTP_201_CREATED)
async def criar_avaliacao(payload: ReviewCreate, session: AsyncSession = Depends(get_session)):
    item = AvaliacaoModel(**payload.model_dump()); session.add(item); await session.commit(); await session.refresh(item); return item


@router.get("/avaliacoes")
async def listar_avaliacoes(session: AsyncSession = Depends(get_session)):
    return (await session.execute(select(AvaliacaoModel).order_by(AvaliacaoModel.data_criacao.desc()))).scalars().all()


@router.post("/estoque/produtos", status_code=status.HTTP_201_CREATED)
async def criar_produto_estoque(payload: StockProductCreate, session: AsyncSession = Depends(get_session)):
    item = EstoqueProdutoModel(**payload.model_dump()); session.add(item); await session.commit(); await session.refresh(item); return item


@router.get("/estoque/produtos")
async def listar_produtos_estoque(session: AsyncSession = Depends(get_session)):
    return (await session.execute(select(EstoqueProdutoModel).order_by(EstoqueProdutoModel.nome))).scalars().all()
