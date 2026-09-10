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
from app.infrastructure.repositories.repository_horario_profissional import HorarioProfissionalRepository


class AtendimentoService:
    """Casos de uso compostos consumidos pelo agente de WhatsApp."""

    def __init__(self, clientes, procedimentos, agendamentos, tempos_trabalho=None, horarios_profissionais=None):
        self.clientes = ClienteService(clientes)
        self.procedimentos = ProcedimentoService(procedimentos)
        self.agendamentos = AgendamentoService(agendamentos)
        self.tempos_trabalho = tempos_trabalho
        # Os fluxos legados ainda constroem este serviço sem a dependência. O
        # repositório usa a mesma sessão da agenda, portanto todos os canais
        # (API, WhatsApp e agente) passam a enxergar a agenda real.
        self.horarios_profissionais = horarios_profissionais or HorarioProfissionalRepository(agendamentos.session)

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

    @staticmethod
    def _intersecao(janelas: list[tuple[datetime, datetime]], limites: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
        if not limites:
            return janelas
        resultado = []
        for inicio, fim in janelas:
            for limite_inicio, limite_fim in limites:
                novo_inicio, novo_fim = max(inicio, limite_inicio), min(fim, limite_fim)
                if novo_inicio < novo_fim:
                    resultado.append((novo_inicio, novo_fim))
        return resultado

    async def _janelas_do_profissional(self, profissional_id: int, dia: date) -> list[tuple[datetime, datetime]]:
        janelas_semanais = await self.horarios_profissionais.janelas_do_dia(profissional_id, dia)
        # A escala semanal cadastrada para a profissional é a fonte de verdade.
        # ``tempos_trabalho`` pertence ao fluxo legado e contém janelas de seed
        # (por exemplo, 09:00–18:00) que não podem limitar uma escala atual até
        # 20:00. Fechamentos e exceções reais são representados por bloqueios.
        return [(datetime.combine(dia, inicio), datetime.combine(dia, fim)) for inicio, fim in janelas_semanais]

    async def disponibilidade_por_profissional(self, procedimento_id: int, dia: date, profissional_id: int | None = None, ignorar_agendamento_id: int | None = None, incluir_horarios_passados: bool = False) -> list[dict]:
        procedimento = await self.procedimentos.buscar(procedimento_id)
        agendamentos = await self.agendamentos.listar()
        passo = timedelta(minutes=30)
        duracao = timedelta(minutes=procedimento.duracao)
        ativos = [a for a in agendamentos if a.status not in (StatusAgendamento.CANCELADO.value, StatusAgendamento.NAO_COMPARECEU.value) and a.id != ignorar_agendamento_id]
        if profissional_id is not None:
            profissional = await self.horarios_profissionais.buscar_profissional_ativo(profissional_id)
            if not profissional:
                raise ValueError("Profissional não encontrado ou inativo.")
            profissionais = [profissional]
        else:
            profissionais = await self.horarios_profissionais.listar_profissionais_ativos()

        opcoes = []
        for profissional in profissionais:
            bloqueios = await self.tempos_trabalho.listar_bloqueios_por_dia(dia, profissional.id) if self.tempos_trabalho else []
            horarios = []
            for inicio, fim_expediente in await self._janelas_do_profissional(profissional.id, dia):
                slot = inicio
                while slot + duracao <= fim_expediente:
                    slot_fim = slot + duracao
                    ocupado = any(slot < bloqueio_fim and slot_fim > bloqueio_inicio for bloqueio_inicio, bloqueio_fim in bloqueios)
                    for agendamento in ativos:
                        # Agendamentos antigos sem profissional bloqueiam todas
                        # as agendas até que sejam atribuídos manualmente.
                        if agendamento.profissional_id not in (None, profissional.id):
                            continue
                        outro = await self.procedimentos.buscar(agendamento.procedimento_id)
                        outro_fim = agendamento.data_hora + timedelta(minutes=outro.duracao)
                        if slot < outro_fim and slot_fim > agendamento.data_hora:
                            ocupado = True
                            break
                    if not ocupado and (incluir_horarios_passados or slot > datetime.now()):
                        horarios.append(slot)
                    slot += passo
            opcoes.append({"profissional_id": profissional.id, "profissional_nome": profissional.nome, "horarios": horarios})
        return opcoes

    async def disponibilidade(self, procedimento_id: int, dia: date, profissional_id: int | None = None, ignorar_agendamento_id: int | None = None, incluir_horarios_passados: bool = False) -> list[datetime]:
        """Compatibilidade para consumidores antigos; prefira a versão detalhada."""
        opcoes = await self.disponibilidade_por_profissional(
            procedimento_id, dia, profissional_id, ignorar_agendamento_id,
            incluir_horarios_passados,
        )
        return sorted({horario for opcao in opcoes for horario in opcao["horarios"]})

    async def iniciar_agendamento(self, cliente: ClienteDto, procedimento_id: int, data_hora: datetime, profissional_id: int):
        await self.procedimentos.buscar(procedimento_id)
        if data_hora not in await self.disponibilidade(procedimento_id, data_hora.date(), profissional_id):
            raise ValueError("O horário escolhido não está disponível ou está bloqueado.")
        return await self.agendamentos.criar(AgendamentoDto(
            cliente_id=cliente.id, procedimento_id=procedimento_id, data_hora=data_hora
            ,profissional_id=profissional_id
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
