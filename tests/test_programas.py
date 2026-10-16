"""Testes do módulo de programas suplementares (PNAE/PNATE)."""
import unittest

from fundeb.programas.suplementares import (
    PNAE_PER_CAPITA_DIA, PNAE_DIAS_ATENDIMENTO,
    PNATE_PER_CAPITA_ANO_MIN, PNATE_PER_CAPITA_ANO_MAX,
    pnae_custo_aluno_ano, pnae_faixa_aluno_ano, impacto_subcontagem,
)


class TestSuplementares(unittest.TestCase):
    def test_pnae_custo_por_etapa(self):
        # per capita/dia × 200 dias
        self.assertAlmostEqual(pnae_custo_aluno_ano("fundamental"), 0.57 * 200, places=2)
        self.assertAlmostEqual(pnae_custo_aluno_ano("creche"), 1.57 * 200, places=2)
        self.assertEqual(PNAE_DIAS_ATENDIMENTO, 200)

    def test_pnae_faixa(self):
        lo, hi = pnae_faixa_aluno_ano()
        self.assertAlmostEqual(lo, 114.0, places=2)   # fundamental/médio/eja
        self.assertAlmostEqual(hi, 314.0, places=2)   # creche

    def test_impacto_etapa_exata(self):
        imp = impacto_subcontagem(1000, etapa="fundamental", pct_rural=0.0)
        self.assertAlmostEqual(imp.pnae_min, 114_000.0, places=2)
        self.assertAlmostEqual(imp.pnae_max, 114_000.0, places=2)
        self.assertEqual(imp.pnate_min, 0.0)

    def test_impacto_faixa_e_rural(self):
        imp = impacto_subcontagem(4480, pct_rural=15.0)
        # PNAE: faixa fundamental..creche
        self.assertAlmostEqual(imp.pnae_min, 4480 * 114.0, places=2)
        self.assertAlmostEqual(imp.pnae_max, 4480 * 314.0, places=2)
        # PNATE: só sobre 15% rurais
        rurais = 4480 * 0.15
        self.assertAlmostEqual(imp.pnate_min, rurais * PNATE_PER_CAPITA_ANO_MIN, places=2)
        self.assertAlmostEqual(imp.pnate_max, rurais * PNATE_PER_CAPITA_ANO_MAX, places=2)
        self.assertGreater(imp.total_max, imp.total_min)

    def test_pct_rural_limites(self):
        # pct_rural fora de [0,100] é saturado
        self.assertEqual(impacto_subcontagem(100, etapa="medio", pct_rural=-5).pnate_min, 0.0)
        imp = impacto_subcontagem(100, etapa="medio", pct_rural=200)
        self.assertAlmostEqual(imp.pnate_min, 100 * PNATE_PER_CAPITA_ANO_MIN, places=2)


if __name__ == "__main__":
    unittest.main()
