from datetime import date, datetime, time, timedelta
from app.application.dto.agendamento import AgendamentoDto
from app.application.dto.cliente import ClienteDto
from app.application.dto.procedimento import ProcedimentoDto
from app.application.services.agendamento_service import AgendamentoService
from app.application.services.cliente_service import ClienteService
from app.application.services.procedimento_service import ProcedimentoService
from app.domain.enums.status_agendamento import StatusAgendamento
from sqlalchemy import select
from app.infrastructure.database.models.models import ListaEsperaModel


class AtendimentoService:
    """Casos de uso compostos consumidos pelo agente de WhatsApp."""

    def __init__(self, clientes, procedimentos, agendamentos, tempos_trabalho=None):
        self.clientes = ClienteService(clientes)
        self.procedimentos = ProcedimentoService(procedimentos)
        self.agendamentos = AgendamentoService(agendamentos)
        self.tempos_trabalho = tempos_trabalho

    async def catalogo(self, busca: str | None = None) -> list[ProcedimentoDto]:
        procedimentos = await self.procedimentos.listar()
        if not busca:
            return procedimentos
        termo = busca.casefold()
        tokens = termo.split()
        return [
            p for p in procedimentos
            if termo in p.nome.casefold()
            or termo in (p.descricao or '').casefold()
            or all(token in p.nome.casefold() or token in (p.descricao or '').casefold() for token in tokens)
        ]

    async def disponibilidade(self, procedimento_id: int, dia: date) -> list[datetime]:
        procedimento = await self.procedimentos.buscar(procedimento_id)
        agendamentos = await self.agendamentos.listar()
        passo = timedelta(minutes=30)
        duracao = timedelta(minutes=procedimento.duracao)
        if self.tempos_trabalho:
            janelas = await self.tempos_trabalho.listar_por_dia(dia)
            # O expediente é recorrente de segunda a sábado. Registros
            # específicos em tempos_trabalho continuam podendo sobrescrever
            # o horário padrão de uma data.
            if not janelas and dia.weekday() < 6:
                janelas = [
                    (
                        datetime.combine(dia, time(8, 0)),
                        datetime.combine(dia, time(18, 0)),
                    )
                ]
        else:
            janelas = [] if dia.weekday() == 6 else [
                (datetime.combine(dia, time(8, 0)), datetime.combine(dia, time(18, 0)))
            ]
        ativos = [a for a in agendamentos if a.status not in (StatusAgendamento.CANCELADO.value, StatusAgendamento.NAO_COMPARECEU.value)]
        bloqueios = await self.tempos_trabalho.listar_bloqueios_por_dia(dia) if self.tempos_trabalho else []
        livres = []
        for inicio, fim_expediente in janelas:
            slot = inicio
            while slot + duracao <= fim_expediente:
                slot_fim = slot + duracao
                ocupado = False
                if any(slot < bloqueio_fim and slot_fim > bloqueio_inicio for bloqueio_inicio, bloqueio_fim in bloqueios):
                    ocupado = True
                for agendamento in ativos:
                    outro = await self.procedimentos.buscar(agendamento.procedimento_id)
                    outro_fim = agendamento.data_hora + timedelta(minutes=outro.duracao)
                    if slot < outro_fim and slot_fim > agendamento.data_hora:
                        ocupado = True
                        break
                if not ocupado and slot > datetime.now():
                    livres.append(slot)
                slot += passo
        return livres

    async def iniciar_agendamento(self, cliente: ClienteDto, procedimento_id: int, data_hora: datetime):
        await self.procedimentos.buscar(procedimento_id)
        if data_hora not in await self.disponibilidade(procedimento_id, data_hora.date()):
            raise ValueError("O horário escolhido não está disponível ou está bloqueado.")
        return await self.agendamentos.criar(AgendamentoDto(
            cliente_id=cliente.id, procedimento_id=procedimento_id, data_hora=data_hora
        ))

    async def entrar_lista_espera(self, cliente: ClienteDto, procedimento_id: int, data_preferida: datetime | None = None, periodo: str | None = None, profissional_id: int | None = None):
        session = self.agendamentos.repository.session
        existente = (await session.execute(select(ListaEsperaModel).where(ListaEsperaModel.cliente_id == cliente.id, ListaEsperaModel.procedimento_id == procedimento_id, ListaEsperaModel.status.in_(("aguardando", "notificado"))))).scalar_one_or_none()
        if existente:
            return existente
        item = ListaEsperaModel(cliente_id=cliente.id, procedimento_id=procedimento_id, data_preferida=data_preferida, periodo=periodo, profissional_id=profissional_id, status="aguardando")
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item
