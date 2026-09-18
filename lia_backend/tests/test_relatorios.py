import unittest
from types import SimpleNamespace

from app.api.routes.relatorios import agendamentos_com_custo_material


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


if __name__ == "__main__":
    unittest.main()
