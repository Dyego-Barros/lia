from datetime import datetime
from app.application.dto.agendamento import AgendamentoDto
from app.domain.entities.agendamentos import Agendamento
from app.domain.enums.status_agendamento import StatusAgendamento
from app.domain.exceptions.agendamentos import AgendamentoConflictException
from app.domain.interfaces.interface_agendamento import AgendamentoInterface


class AgendamentoService:
    def __init__(self, repository: AgendamentoInterface):
        self.repository = repository

    @staticmethod
    def _carregar_existente(agendamento: AgendamentoDto) -> Agendamento:
        """Carrega um registro já existente sem tratá-lo como um novo horário."""
        return Agendamento.model_validate(
            agendamento,
            context={"permitir_data_passada": True},
        )

    async def criar(self, agendamento: AgendamentoDto) -> AgendamentoDto:
        entity = Agendamento.model_validate(agendamento)
        if await self.repository.get_agendamento_data_hora(entity.data_hora, entity.profissional_id):
            raise AgendamentoConflictException("A profissional já possui um agendamento neste horário.")
        return await self.repository.create_agendamento(AgendamentoDto.model_validate(entity))

    async def buscar(self, agendamento_id: int) -> AgendamentoDto:
        return await self.repository.get_agendamento_by_id(agendamento_id)

    async def listar(self) -> list[AgendamentoDto]:
        return await self.repository.list_agendamentos()

    async def atualizar(self, agendamento: AgendamentoDto) -> AgendamentoDto:
        entity = self._carregar_existente(agendamento)
        return await self.repository.update_agendamento(AgendamentoDto.model_validate(entity))

    async def remover(self, agendamento_id: int) -> None:
        await self.repository.delete_agendamento(agendamento_id)

    async def confirmar(self, agendamento_id: int) -> AgendamentoDto:
        agendamento = self._carregar_existente(await self.buscar(agendamento_id))
        agendamento.confirmar_agendamento()
        return await self.atualizar(AgendamentoDto.model_validate(agendamento))

    async def cancelar(self, agendamento_id: int) -> AgendamentoDto:
        agendamento = self._carregar_existente(await self.buscar(agendamento_id))
        agendamento.cancelar_agendamento()
        return await self.atualizar(AgendamentoDto.model_validate(agendamento))

    async def reagendar(self, agendamento_id: int, nova_data_hora) -> AgendamentoDto:
        agendamento = self._carregar_existente(await self.buscar(agendamento_id))
        agendamento.reagendar_agendamento(nova_data_hora)
        return await self.atualizar(AgendamentoDto.model_validate(agendamento))
