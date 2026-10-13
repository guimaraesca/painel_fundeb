"""Testes unitários das fórmulas matemáticas puras do VAAR."""
import math
import unittest
from fundeb.domain.formulas import (
    peso_indicador,
    razao,
    iee_cenarios,
    ind_atendimento,
    ind_aprendizagem,
    ipa,
    ind_atendimento_sir,
    delta_evolucao,
    peso_distribuicao_minmax,
    inad_normalizado,
    inad_ponderado,
    ind_aprendizagem_triade,
    coeficiente_distribuicao,
    repasse_reais,
)


class TestFormulasDomain(unittest.TestCase):
    def test_peso_indicador_limites(self):
        # Para IND = 0, peso = 2 - exp(0) = 1.0
        self.assertAlmostEqual(peso_indicador(0.0), 1.0, places=4)
        # Para IND alto, peso tende a 2.0
        self.assertAlmostEqual(peso_indicador(5.0), 2.0, places=2)
        # Para IND intermediário (ex: 0.5): 2 - exp(-2) = 2 - 0.135335 = 1.86466
        self.assertAlmostEqual(peso_indicador(0.5), 1.86466, places=4)
        # Se None ou NaN, retorna NaN
        self.assertTrue(math.isnan(peso_indicador(None)))
        self.assertTrue(math.isnan(peso_indicador(float("nan"))))

    def test_razao(self):
        self.assertAlmostEqual(razao(110, 100), 1.10, places=4)
        self.assertIsNone(razao(100, 0))
        self.assertIsNone(razao(None, 100))

    def test_iee_cenarios(self):
        mats = {2017: 1000, 2018: 1020, 2019: 1050, 2020: 1100, 2021: 1120, 2022: 1150, 2023: 1200}
        cenarios = iee_cenarios(mats)
        self.assertEqual(len(cenarios), 5)
        c1 = cenarios[0]
        self.assertEqual(c1["cenario"], "IEE vigente")
        self.assertAlmostEqual(c1["iee"], 1.10, places=4)
        self.assertTrue(c1["evolui"])

    def test_ind_atendimento(self):
        self.assertAlmostEqual(ind_atendimento(1.10, 0.05), 1.10 * 0.95, places=4)

    def test_ipa_e_aprendizagem(self):
        val_ipa = ipa(100.0, 100.0)
        self.assertAlmostEqual(val_ipa, 100.0, places=4)
        self.assertAlmostEqual(ind_aprendizagem(100.0, 0.90), 90.0, places=4)

    def test_especificacoes_tecnicas_canonicas(self):
        # Atendimento com SIR penalizado com fator 0.5
        atend = ind_atendimento_sir(abandono=10, sir=20, matriculas=100)
        self.assertAlmostEqual(atend, 0.80, places=4)

        # Delta de evolução
        self.assertAlmostEqual(delta_evolucao(0.85, 0.80), 0.05, places=4)

        # Reescalonamento linear Min-Max em [1, 2]
        self.assertAlmostEqual(peso_distribuicao_minmax(0.5, 0.0, 1.0), 1.5, places=4)
        self.assertAlmostEqual(peso_distribuicao_minmax(0.0, 0.0, 1.0), 1.0, places=4)
        self.assertAlmostEqual(peso_distribuicao_minmax(1.0, 0.0, 1.0), 2.0, places=4)

        # Inad normalizado de [-7, 10] para [0, 1]
        self.assertAlmostEqual(inad_normalizado(-7.0), 0.0, places=4)
        self.assertAlmostEqual(inad_normalizado(10.0), 1.0, places=4)
        self.assertAlmostEqual(inad_normalizado(1.5), 8.5 / 17.0, places=4)

        # Inad ponderado: 0.3 * IND + 0.7 * IAD
        inad_pond = inad_ponderado(ind=2.0, iad=4.0, tap=0.95)
        self.assertAlmostEqual(inad_pond, (0.3 * 2.0 + 0.7 * 4.0) * 0.95, places=4)

        # Aprendizagem tríade
        aprend_triade = ind_aprendizagem_triade(inad_norm=0.5, ip_saeb=0.9, ind_equi=0.8)
        self.assertAlmostEqual(aprend_triade, 0.5 * 0.9 * 0.8, places=4)

        # Coeficiente e Repasse
        coef = coeficiente_distribuicao(matricula=1000, peso=1.5, soma_matriculas_ponderadas=15000)
        self.assertAlmostEqual(coef, 0.1, places=4)
        repasse = repasse_reais(coeficiente=coef, montante_global_vaar=1000000.0, cota=0.5)
        self.assertAlmostEqual(repasse, 50000.0, places=2)


if __name__ == "__main__":
    unittest.main()
