from app.domain.interfaces.interface_agendamento import AgendamentoInterface
from sqlalchemy.ext.asyncio import AsyncSession
from app.application.dto.agendamento import AgendamentoDto
from app.infrastructure.database.models.models import AgendamentoModel
from sqlalchemy import select

class AgendamentoRepository(AgendamentoInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_agendamento(self, agendamento: AgendamentoDto) -> AgendamentoDto:
        try:
            agendamento_model = AgendamentoModel(
                cliente_id=agendamento.cliente_id,
                procedimento_id=agendamento.procedimento_id,
                data_hora=agendamento.data_hora,
                status=agendamento.status
            )
            self.session.add(agendamento_model)
            await self.session.flush()
            await self.session.refresh(agendamento_model)
            return AgendamentoDto.model_validate(agendamento_model)
        except Exception as e:
            print("Ocorreu um erro ao criar o agendamento:", e)
            await self.session.rollback()
            raise e
    async def get_agendamento_by_id(self, agendamento_id: int) -> AgendamentoDto:
        try:
            agendamento = await self.session.get(AgendamentoModel, agendamento_id)
            if agendamento is None:
                raise ValueError(f"Agendamento com ID {agendamento_id} não encontrado.")
            return AgendamentoDto.model_validate(agendamento)
        except Exception as e:
            print("Ocorreu um erro ao buscar o agendamento:", e)
            await self.session.rollback()
            raise e
    async def update_agendamento(self, agendamento: AgendamentoDto) -> AgendamentoDto:
        try:
            agendamento_update = await self.session.get(AgendamentoModel, agendamento.id)
            if agendamento_update is None:
                raise ValueError(f"Agendamento com ID {agendamento.id} não encontrado.")
            agendamento_update.cliente_id = agendamento.cliente_id
            agendamento_update.procedimento_id = agendamento.procedimento_id
            agendamento_update.data_hora = agendamento.data_hora
            agendamento_update.status = agendamento.status
            await self.session.flush()
            await self.session.refresh(agendamento_update)
            return AgendamentoDto.model_validate(agendamento_update)
        except Exception as e:
            print("Ocorreu um erro ao atualizar o agendamento:", e)
            await self.session.rollback()
            raise e
    async def delete_agendamento(self, agendamento_id: int) -> None:
        try:
            agendamento = await self.session.get(AgendamentoModel, agendamento_id)
            if agendamento is None:
                raise ValueError(f"Agendamento com ID {agendamento_id} não encontrado.")
            await self.session.delete(agendamento)
            await self.session.flush()
        except Exception as e:
            print("Ocorreu um erro ao deletar o agendamento:", e)
            await self.session.rollback()
            raise e
    async def list_agendamentos(self) -> list[AgendamentoDto]:
        try:
            result = await self.session.execute(select(AgendamentoModel))
            agendamentos = result.scalars().all()
            return [AgendamentoDto.model_validate(agendamento) for agendamento in agendamentos]
        except Exception as e:
            print("Ocorreu um erro ao listar os agendamentos:", e)
            await self.session.rollback()
            raise e 
    async def get_agendamento_data_hora(self, data_hora) -> list[AgendamentoDto]:
        try:
            result = await self.session.execute(select(AgendamentoModel).where(AgendamentoModel.data_hora == data_hora))
            agendamentos = result.scalars().all()
            return [AgendamentoDto.model_validate(agendamento) for agendamento in agendamentos]
        except Exception as e:
            print("Ocorreu um erro ao buscar os agendamentos por data e hora:", e)
            await self.session.rollback()
            raise e
