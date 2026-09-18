import unittest
from types import SimpleNamespace

from app.api.routes.relatorios import agendamentos_com_custo_material, custo_material_do_atendimento


class RelatoriosTest(unittest.TestCase):
    def test_custo_material_inclui_confirmados_e_concluidos(self):
        agendamentos = [
            SimpleNamespace(id=1, status="pendente"),
            SimpleNamespace(id=2, status="confirmado"),
            SimpleNamespace(id=3, status="concluido"),
            SimpleNamespace(id=4, status="cancelado"),
            SimpleNamespace(id=5, status="nao_compareceu"),
        ]

        resultado = agendamentos_com_custo_material(agendamentos)

        self.assertEqual([item.id for item in resultado], [2, 3])

    def test_custo_zero_da_receita_recua_para_custo_medio_do_procedimento(self):
        agendamento = SimpleNamespace(id=7, procedimento_id=12)

        custo = custo_material_do_atendimento(
            agendamento,
            consumption_costs={},
            material_costs={12: 0},
            legacy_material_costs={12: 18.5},
        )

        self.assertEqual(custo, 18.5)

    def test_consumo_real_positivo_tem_prioridade(self):
        agendamento = SimpleNamespace(id=7, procedimento_id=12)

        custo = custo_material_do_atendimento(
            agendamento,
            consumption_costs={7: 21.75},
            material_costs={12: 20},
            legacy_material_costs={12: 18.5},
        )

        self.assertEqual(custo, 21.75)


if __name__ == "__main__":
    unittest.main()
