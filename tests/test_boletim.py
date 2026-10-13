"""Testes automatizados do serviço gerador do Boletim Executivo Estratégico (2 Páginas)."""
from __future__ import annotations

import unittest
import pandas as pd

from fundeb.data.repository import JsonDataRepository
from fundeb.services.simulator import SimulatorService
from fundeb.services.boletim import BoletimService, DadosBoletim


class TestBoletimService(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = JsonDataRepository()
        cls.df = cls.repo.entes()
        cls.simulator = SimulatorService(cls.df)
        cls.service = BoletimService(cls.df, cls.simulator)

    def test_gerar_dados_boletim_estado(self) -> None:
        """Verifica a geração de dados do boletim para uma rede estadual (ex: PI ou MG)."""
        # Piauí: 2200000 ou buscar por rede Estadual
        df_est = self.df[self.df["rede"] == "Estadual"]
        self.assertFalse(df_est.empty)
        ibge_est = str(df_est.iloc[0]["ibge"])

        dados = self.service.gerar_dados_boletim(ibge_est)
        self.assertIsNotNone(dados)
        assert dados is not None
        self.assertEqual(dados.esfera, "Estadual")
        self.assertEqual(len(dados.condicionalidades_status), 5)
        self.assertGreater(len(dados.trilha_cenarios), 0)
        self.assertGreater(len(dados.acoes_prescritivas), 0)
        self.assertTrue(len(dados.hash_autenticacao) > 8)

    def test_gerar_dados_boletim_municipio(self) -> None:
        """Verifica a geração de dados do boletim para um município."""
        df_mun = self.df[self.df["rede"] == "Municipal"]
        self.assertFalse(df_mun.empty)
        ibge_mun = str(df_mun.iloc[0]["ibge"])

        dados = self.service.gerar_dados_boletim(ibge_mun)
        self.assertIsNotNone(dados)
        assert dados is not None
        self.assertEqual(dados.esfera, "Municipal")
        self.assertEqual(len(dados.condicionalidades_status), 5)
        self.assertGreaterEqual(dados.custo_inacao_rs, 0.0)

    def test_gerar_html_boletim_duas_paginas_portrait_e_landscape(self) -> None:
        """Verifica que o HTML contém exatamente as duas seções de página A4 e suporte a impressão."""
        ibge = str(self.df.iloc[0]["ibge"])
        dados = self.service.gerar_dados_boletim(ibge)
        self.assertIsNotNone(dados)
        assert dados is not None

        # Teste Retrato (Portrait)
        html_port = self.service.gerar_html_boletim(dados, orientacao="portrait")
        self.assertIn("A4 portrait", html_port)
        self.assertIn("Página 1 de 2", html_port)
        self.assertIn("Página 2 de 2", html_port)
        self.assertEqual(html_port.count('class="boletim-page"'), 2)
        self.assertIn(dados.hash_autenticacao, html_port)

        # Teste Paisagem (Landscape)
        html_land = self.service.gerar_html_boletim(dados, orientacao="landscape")
        self.assertIn("A4 landscape", html_land)
        self.assertEqual(html_land.count('class="boletim-page"'), 2)

    def test_ente_inexistente(self) -> None:
        """Verifica retorno seguro para código IBGE inválido."""
        dados = self.service.gerar_dados_boletim("999999999")
        self.assertIsNone(dados)


if __name__ == "__main__":
    unittest.main()
