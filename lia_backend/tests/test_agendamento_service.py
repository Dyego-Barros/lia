import asyncio
import unittest
from datetime import datetime, timedelta

from app.application.dto.agendamento import AgendamentoDto
from app.application.services.agendamento_service import AgendamentoService
from app.domain.entities.agendamentos import Agendamento
from app.domain.exceptions.agendamentos import InvalidAgendamentoDateTimeException
from app.domain.interfaces.interface_agendamento import AgendamentoInterface


class FakeAgendamentoRepository(AgendamentoInterface):
    def __init__(self):
        self.atualizado = None

    async def create_agendamento(self, agendamento):
        return agendamento

    async def get_agendamento_by_id(self, agendamento_id):
        raise NotImplementedError

    async def update_agendamento(self, agendamento):
        self.atualizado = agendamento
        return agendamento

    async def delete_agendamento(self, agendamento_id):
        raise NotImplementedError

    async def list_agendamentos(self):
        return []

    async def get_agendamento_data_hora(self, data_hora, profissional_id=None):
        return []


class AgendamentoServiceTest(unittest.TestCase):
    def setUp(self):
        self.agendamento_passado = AgendamentoDto(
            id=4,
            cliente_id=1,
            procedimento_id=2,
            profissional_id=3,
            data_hora=datetime.now() - timedelta(days=1),
            status="concluido",
            valor_cobrado=150.0,
            forma_pagamento="pix",
            status_pagamento="pago",
        )

    def test_novo_agendamento_no_passado_continua_proibido(self):
        with self.assertRaises(InvalidAgendamentoDateTimeException):
            Agendamento.model_validate(self.agendamento_passado)

    def test_atualizacao_de_pagamento_em_agendamento_passado(self):
        repository = FakeAgendamentoRepository()
        resultado = asyncio.run(
            AgendamentoService(repository).atualizar(self.agendamento_passado)
        )

        self.assertEqual(resultado.valor_cobrado, 150.0)
        self.assertEqual(resultado.forma_pagamento, "pix")
        self.assertEqual(resultado.status_pagamento, "pago")
        self.assertEqual(repository.atualizado, resultado)


if __name__ == "__main__":
    unittest.main()
