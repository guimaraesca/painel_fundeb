"""Testes do gráfico de Pareto de prioridade (retorno de VAAR × esforço)."""
import unittest

import pandas as pd

from fundeb.ui.charts import chart_pareto_vaar


class TestParetoVaar(unittest.TestCase):
    def test_minoria_vital_80(self):
        # Um ente concentra 80% do ganho; os demais, 20%.
        df = pd.DataFrame({
            "nome": ["A", "B", "C", "D"],
            "ganho": [800.0, 100.0, 60.0, 40.0],
            "reprov": [1, 2, 3, 1],
        })
        fig, n_vital, n_total = chart_pareto_vaar(df, "nome", "ganho", "reprov", "t")
        self.assertEqual(n_total, 4)
        self.assertEqual(n_vital, 1)  # só "A" já cruza 80%
        self.assertTrue(fig.data)

    def test_ignora_ganho_nao_positivo(self):
        df = pd.DataFrame({
            "nome": ["A", "B", "C"],
            "ganho": [500.0, 0.0, -10.0],
            "reprov": [1, 0, 2],
        })
        _, n_vital, n_total = chart_pareto_vaar(df, "nome", "ganho", "reprov", "t")
        self.assertEqual(n_total, 1)
        self.assertEqual(n_vital, 1)

    def test_duas_series_barras_e_linha(self):
        df = pd.DataFrame({"nome": list("ABCDE"), "ganho": [5, 4, 3, 2, 1.0], "reprov": [1, 1, 2, 3, 1]})
        fig, _, _ = chart_pareto_vaar(df, "nome", "ganho", "reprov", "t")
        tipos = sorted(tr.type for tr in fig.data)
        self.assertIn("bar", tipos)
        self.assertIn("scatter", tipos)


if __name__ == "__main__":
    unittest.main()
