"""Testes de conformidade das formatações numéricas ABNT e rampa progressiva."""
import unittest

from fundeb.ui.components import (
    format_currency,
    format_currency_full,
    format_percent,
    format_int,
    format_decimal,
)
from fundeb.domain.legal import RAMPA_COMPLEMENTACAO
from fundeb.domain.territorio import REGIOES, REGIAO_POR_UF


class TestFormattersABNT(unittest.TestCase):
    def test_format_currency_abnt(self):
        self.assertEqual(format_currency(0), "R$ 0,00")
        self.assertEqual(format_currency(1250.50), "R$ 1.250,50")
        self.assertEqual(format_currency(1500000.0), "R$ 1,50 mi")
        self.assertEqual(format_currency(2340000000.0), "R$ 2,34 bi")
        self.assertEqual(format_currency(-5000000.0), "-R$ 5,00 mi")

    def test_format_currency_full_abnt(self):
        self.assertEqual(format_currency_full(1234567.89), "R$ 1.234.567,89")
        self.assertEqual(format_currency_full(100.0), "R$ 100,00")
        self.assertEqual(format_currency_full(0.0), "R$ 0,00")
        self.assertEqual(format_currency_full(None), "—")

    def test_format_percent_abnt(self):
        self.assertEqual(format_percent(15.8), "15,8%")
        self.assertEqual(format_percent(100.0), "100,0%")
        self.assertEqual(format_percent(0.0), "0,0%")
        self.assertEqual(format_percent(12.345, decimais=2), "12,35%")
        self.assertEqual(format_percent(None), "—")

    def test_format_int_abnt(self):
        self.assertEqual(format_int(1234), "1.234")
        self.assertEqual(format_int(5570), "5.570")
        self.assertEqual(format_int(0), "0")
        self.assertEqual(format_int(None), "—")

    def test_format_decimal_abnt(self):
        self.assertEqual(format_decimal(3.14159, decimais=2), "3,14")
        self.assertEqual(format_decimal(1250.5, decimais=2), "1.250,50")
        self.assertEqual(format_decimal(0.8521, decimais=4), "0,8521")
        self.assertEqual(format_decimal(None), "—")

    def test_regioes_e_ufs_territorio(self):
        for reg in REGIOES:
            ufs_reg = [uf for uf, r in REGIAO_POR_UF.items() if r == reg]
            self.assertTrue(len(ufs_reg) > 0, f"Região {reg} deve possuir UFs")

        self.assertIn("PI", [uf for uf, r in REGIAO_POR_UF.items() if r == "Nordeste"])
        self.assertIn("SP", [uf for uf, r in REGIAO_POR_UF.items() if r == "Sudeste"])
        self.assertIn("PR", [uf for uf, r in REGIAO_POR_UF.items() if r == "Sul"])
        self.assertIn("AM", [uf for uf, r in REGIAO_POR_UF.items() if r == "Norte"])
        self.assertIn("GO", [uf for uf, r in REGIAO_POR_UF.items() if r == "Centro-Oeste"])

    def test_rampa_constitucional(self):
        self.assertEqual(RAMPA_COMPLEMENTACAO[2021], (10.0, 2.0, 0.0))
        self.assertEqual(RAMPA_COMPLEMENTACAO[2026], (10.0, 10.5, 2.5))
        self.assertEqual(sum(RAMPA_COMPLEMENTACAO[2026]), 23.0)


if __name__ == "__main__":
    unittest.main()
