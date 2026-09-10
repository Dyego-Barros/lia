import asyncio
import unittest
from datetime import date, datetime, time, timedelta

from app.application.dto.agendamento import AgendamentoDto
from app.application.services.agendamento_service import AgendamentoService
from app.application.services.atendimento_service import AtendimentoService
from app.api.schemas.agendamentos import AgendamentoCreate
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


class FakeHorarioProfissionalRepository:
    async def janelas_do_dia(self, profissional_id, dia):
        return [(time(8), time(20))]

    async def buscar_profissional_ativo(self, profissional_id):
        return object()


class FakeTempoTrabalhoRepository:
    async def listar_por_dia(self, dia):
        return [(datetime.combine(dia, time(9)), datetime.combine(dia, time(18)))]

    async def listar_bloqueios_por_dia(self, dia, profissional_id=None):
        return []


class FakeProcedimentoRepository:
    async def get_procedimento_by_id(self, procedimento_id):
        from app.application.dto.procedimento import ProcedimentoDto
        return ProcedimentoDto(id=procedimento_id, nome="Procedimento", preco=50, duracao=10)


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

    def test_cadastro_administrativo_pode_registrar_atendimento_passado(self):
        repository = FakeAgendamentoRepository()
        resultado = asyncio.run(
            AgendamentoService(repository).criar(
                self.agendamento_passado,
                permitir_data_passada=True,
            )
        )
        self.assertEqual(resultado.data_hora, self.agendamento_passado.data_hora)

    def test_nao_comparecimento_define_pagamento_como_nao_pago(self):
        agendamento = Agendamento.model_validate(
            self.agendamento_passado.model_copy(update={"status": "confirmado"}),
            context={"permitir_data_passada": True},
        )
        agendamento.marcar_nao_compareceu()
        self.assertEqual(agendamento.status_pagamento, "nao_pago")
        self.assertIsNone(agendamento.forma_pagamento)

    def test_payload_nao_compareceu_nunca_permanece_pago(self):
        payload = AgendamentoCreate(
            cliente_id=1,
            procedimento_id=2,
            profissional_id=3,
            data_hora=datetime.now() + timedelta(days=1),
            status="nao_compareceu",
            valor_cobrado=150,
            forma_pagamento="pix",
            status_pagamento="pago",
        )
        self.assertEqual(payload.status_pagamento, "nao_pago")
        self.assertIsNone(payload.forma_pagamento)

    def test_escala_atual_nao_e_cortada_pelo_tempo_de_trabalho_legado(self):
        service = AtendimentoService(
            None,
            None,
            FakeAgendamentoRepository(),
            FakeTempoTrabalhoRepository(),
            FakeHorarioProfissionalRepository(),
        )
        dia = date(2026, 9, 10)
        janelas = asyncio.run(service._janelas_do_profissional(3, dia))
        self.assertEqual(
            janelas,
            [(datetime.combine(dia, time(8)), datetime.combine(dia, time(20)))],
        )

    def test_cadastro_manual_aceita_minuto_fora_da_grade_de_sugestoes(self):
        service = AtendimentoService(
            None,
            FakeProcedimentoRepository(),
            FakeAgendamentoRepository(),
            FakeTempoTrabalhoRepository(),
            FakeHorarioProfissionalRepository(),
        )
        disponivel = asyncio.run(
            service.horario_disponivel(2, datetime(2026, 9, 16, 14, 10), 3)
        )
        self.assertTrue(disponivel)

    def test_cadastro_manual_recusa_procedimento_que_ultrapassa_as_vinte(self):
        service = AtendimentoService(
            None,
            FakeProcedimentoRepository(),
            FakeAgendamentoRepository(),
            FakeTempoTrabalhoRepository(),
            FakeHorarioProfissionalRepository(),
        )
        disponivel = asyncio.run(
            service.horario_disponivel(2, datetime(2026, 9, 16, 19, 55), 3)
        )
        self.assertFalse(disponivel)

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
