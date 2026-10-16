"""Testes de integração dos serviços e integridade de dados."""
import unittest
from fundeb.data.repository import JsonDataRepository
from fundeb.services.analytics import AnalyticsService
from fundeb.services.simulator import SimulatorService
from fundeb.data.validation import verificar, cobertura, proveniencia, OK


class TestServicesIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = JsonDataRepository()
        cls.df = cls.repo.entes()

    def test_repositorio_entes(self):
        self.assertEqual(len(self.df), 5596)
        self.assertIn("ibge", self.df.columns)
        self.assertIn("habilitado", self.df.columns)
        self.assertIn("beneficiario", self.df.columns)

    def test_analytics_resumo_nacional(self):
        analytics = AnalyticsService(self.df)
        res = analytics.resumo_nacional()

        self.assertEqual(res.total_entes, 5596)
        self.assertEqual(res.total_estados, 27)
        self.assertEqual(res.total_municipios, 5569)
        self.assertEqual(res.habilitados, 3076)
        self.assertEqual(res.nao_habilitados, 2520)
        self.assertGreater(res.total_vaar_reais, 0)

    def test_analytics_gargalos_condicionalidade(self):
        analytics = AnalyticsService(self.df)
        gargalos = analytics.gargalos_condicionalidade()

        # Verifica os gargalos exatos citados nos requisitos do usuário
        d_gargalos = {g.codigo: g.reprovacoes_nao_habilitadas for g in gargalos}
        self.assertEqual(d_gargalos["Cond. III"], 1930)
        self.assertEqual(d_gargalos["Cond. I"], 575)
        self.assertEqual(d_gargalos["Cond. II"], 417)
        self.assertEqual(d_gargalos["Cond. IV"], 93)

    def test_simulador_estadual_vs_municipal(self):
        sim = SimulatorService(self.df)

        # Rede Municipal (Teresina ou SP Capital)
        sp_mun = sim.simular_ente("3550308", delta_atendimento_pct=10.0)
        self.assertIsNotNone(sp_mun)
        self.assertEqual(sp_mun.esfera, "Municipal")
        self.assertIn("Educação Infantil", sp_mun.etapa_atendimento)
        self.assertEqual(len(sp_mun.memoria_calculo), 6)

        # Rede Estadual (SP Estado ou PI Estado)
        pi_est = sim.simular_ente("22", delta_atendimento_pct=10.0)
        self.assertIsNotNone(pi_est)
        self.assertEqual(pi_est.esfera, "Estadual")
        self.assertIn("Ensino Médio", pi_est.etapa_atendimento)
        self.assertEqual(len(pi_est.memoria_calculo), 6)

        # Regressão Issue #3 e #4: Validação de formatação pt-BR e fórmulas completas
        for passo in pi_est.memoria_calculo:
            formula = passo["formula"]
            self.assertNotIn("R ", formula, "Símbolo de real não deve perder o cifrão (R$)")
            self.assertNotIn("Status_Condicionalidades ∈", formula, "Passo 1 não pode estar truncado")
            self.assertNotIn("e .", formula, "Passo 5 não pode terminar de forma truncada")
            # Verifica que valores em R$ usam vírgula decimal pt-BR
            if "R$" in formula:
                self.assertRegex(formula, r"R\$\s?[\d\.]+(?:,\d{2})?", "Valores em R$ devem estar em formato pt-BR")



    def test_auditoria_qualidade_dados(self):
        verifs = verificar(self.df)
        self.assertGreater(len(verifs), 0)
        # Verifica que o fechamento contábil e unicidade IBGE estão OK
        unicidade = next(v for v in verifs if "Código IBGE único" in v.nome)
        self.assertEqual(unicidade.status, OK)

        fechamento = next(v for v in verifs if "VAAF + VAAT + VAAR" in v.nome)
        self.assertEqual(fechamento.status, OK)

        split = next(v for v in verifs if "50% / 50%" in v.nome)
        self.assertEqual(split.status, OK)

        df_prov = proveniencia(self.repo)
        self.assertGreater(len(df_prov), 0)
        self.assertIn("SHA-256", df_prov.columns)

        df_cob = cobertura(self.df)
        self.assertGreater(len(df_cob), 0)

    def test_chart_ranking_horizontal_regioes(self):
        from fundeb.ui.charts import chart_ranking_horizontal
        import pandas as pd
        df_teste = pd.DataFrame([
            {"nome": "Rede 1", "valor": 100, "regiao": "Nordeste"},
            {"nome": "Rede 2", "valor": 80, "regiao": "Sudeste"},
        ])
        fig = chart_ranking_horizontal(
            df_teste,
            categoria_col="nome",
            valor_col="valor",
            titulo="Teste de Ranking Regional",
            cor_col="regiao"
        )
        self.assertIsNotNone(fig)
        self.assertGreater(len(fig.data), 0)



if __name__ == "__main__":
    unittest.main()

