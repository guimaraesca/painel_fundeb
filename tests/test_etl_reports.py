"""Testes da evolução: ETL multidimensional e geração de relatórios PDF."""
import tempfile
import unittest
from pathlib import Path

from fundeb.etl.consolidate import consolidar, tabela_fato, agregados
from fundeb.etl.indicadores import CATALOGO, DIMENSOES, CATALOGO_POR_COLUNA
from fundeb.etl.pipeline import executar
from fundeb.reports.geral import relatorio_geral
from fundeb.reports.especifico import relatorio_especifico


class TestETL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = consolidar()

    def test_consolidado_mantem_base(self):
        # A evolução NÃO altera a base auditada: mesma contagem de redes.
        self.assertEqual(len(self.df), 5596)
        self.assertEqual(int((self.df["rede"] == "Estadual").sum()), 27)

    def test_derivados_presentes(self):
        for col in ("delta_vaar", "pct_uniao_vaar", "pctl_ideb_ai"):
            self.assertIn(col, self.df.columns)

    def test_catalogo_colunas_existem(self):
        # Todo indicador catalogado deve existir na base consolidada.
        for ind in CATALOGO:
            self.assertIn(ind.coluna, self.df.columns, f"coluna ausente: {ind.coluna}")

    def test_dimensoes_cobertas(self):
        dims = {ind.dimensao for ind in CATALOGO}
        self.assertEqual(dims, set(DIMENSOES))

    def test_tabela_fato(self):
        fato = tabela_fato(self.df)
        # uma linha por (ente, indicador)
        self.assertEqual(len(fato), len(self.df) * len(CATALOGO))
        self.assertEqual(set(fato["dimensao"].unique()), set(DIMENSOES))

    def test_agregados(self):
        aggs = agregados(self.df)
        self.assertEqual(len(aggs["nacional"]), 1)
        self.assertEqual(len(aggs["por_uf"]), 27)
        self.assertEqual(len(aggs["por_regiao"]), 5)
        self.assertEqual(set(aggs["por_rede"]["rede"]), {"Estadual", "Municipal"})

    def test_pipeline_manifest(self):
        manifest = executar(gravar=False)
        self.assertEqual(manifest["volumetria"]["redes"], 5596)
        self.assertEqual(manifest["volumetria"]["indicadores_catalogados"], len(CATALOGO))
        self.assertTrue(manifest["qualidade"])
        self.assertTrue(manifest["proveniencia"])


class TestRelatorios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = consolidar()

    def test_relatorio_geral_gera_pdf(self):
        with tempfile.TemporaryDirectory() as d:
            p = relatorio_geral(self.df, Path(d) / "geral.pdf")
            self.assertTrue(p.exists())
            self.assertGreater(p.stat().st_size, 2000)
            self.assertEqual(p.read_bytes()[:4], b"%PDF")

    def test_relatorio_especifico_municipio(self):
        with tempfile.TemporaryDirectory() as d:
            p = relatorio_especifico(self.df, "3550308", Path(d) / "sp.pdf")
            self.assertTrue(p.exists())
            self.assertEqual(p.read_bytes()[:4], b"%PDF")

    def test_relatorio_especifico_estadual(self):
        with tempfile.TemporaryDirectory() as d:
            p = relatorio_especifico(self.df, "11", Path(d) / "ro.pdf")
            self.assertEqual(p.read_bytes()[:4], b"%PDF")

    def test_ente_inexistente(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                relatorio_especifico(self.df, "99999999", Path(d) / "x.pdf")


if __name__ == "__main__":
    unittest.main()
