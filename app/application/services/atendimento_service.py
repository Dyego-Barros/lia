from datetime import date, datetime, time, timedelta
from app.application.dto.agendamento import AgendamentoDto
from app.application.dto.cliente import ClienteDto
from app.application.dto.procedimento import ProcedimentoDto
from app.application.services.agendamento_service import AgendamentoService
from app.application.services.cliente_service import ClienteService
from app.application.services.procedimento_service import ProcedimentoService
from app.domain.enums.status_agendamento import StatusAgendamento


class AtendimentoService:
    """Casos de uso compostos consumidos pelo agente de WhatsApp."""

    def __init__(self, clientes, procedimentos, agendamentos):
        self.clientes = ClienteService(clientes)
        self.procedimentos = ProcedimentoService(procedimentos)
        self.agendamentos = AgendamentoService(agendamentos)

    async def catalogo(self, busca: str | None = None) -> list[ProcedimentoDto]:
        procedimentos = await self.procedimentos.listar()
        if not busca:
            return procedimentos
        termo = busca.casefold()
        return [p for p in procedimentos if termo in p.nome.casefold() or termo in (p.descricao or '').casefold()]

    async def disponibilidade(self, procedimento_id: int, dia: date) -> list[datetime]:
        procedimento = await self.procedimentos.buscar(procedimento_id)
        agendamentos = await self.agendamentos.listar()
        inicio = datetime.combine(dia, time(8, 0))
        fim_expediente = datetime.combine(dia, time(18, 0))
        passo = timedelta(minutes=30)
        duracao = timedelta(minutes=procedimento.duracao)
        ativos = [a for a in agendamentos if a.status not in (StatusAgendamento.CANCELADO.value, StatusAgendamento.NAO_COMPARECEU.value)]
        livres = []
        slot = inicio
        while slot + duracao <= fim_expediente:
            slot_fim = slot + duracao
            ocupado = False
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
        return await self.agendamentos.criar(AgendamentoDto(
            cliente_id=cliente.id, procedimento_id=procedimento_id, data_hora=data_hora
        ))
