"""Testes do pipeline de reconstrução raw → processed (parsers FNDE/INEP).

Os dados brutos (``data/raw``) não são versionados. Quando ausentes, os testes
são PULADOS. Para rodá-los: ``python src/sources.py --download`` antes.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"

_TEM_RAW = (RAW / "fnde_receita_vaaf_2026.csv").exists() and (RAW / "ext").exists()


def _difs(novo: dict, velho: dict, campos, tol=0.01) -> int:
    comuns = set(novo) & set(velho)
    n = 0
    for k in comuns:
        for c in campos:
            a, b = novo[k].get(c), velho[k].get(c)
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                if abs(a - b) > tol:
                    n += 1
            elif (a is None) != (b is None):
                n += 1
    return n


@unittest.skipUnless(_TEM_RAW, "data/raw ausente — rode src/sources.py --download")
class TestParidadeParsers(unittest.TestCase):
    def test_fnde_base_clean(self):
        from src.parse.fnde import construir_base_clean
        novo = {r["IBGE"]: r for r in construir_base_clean(RAW)["recs"]}
        velho = {r["IBGE"]: r for r in json.load(open(PROC / "base_clean.json"))["recs"]}
        self.assertEqual(len(novo), 5596)
        self.assertEqual(set(novo), set(velho))
        campos = ["Receita_Contrib", "Compl_VAAF", "Compl_VAAT", "Compl_VAAR", "IEI_pct",
                  "Pond_NSE", "VAAR_ind_atend", "Cond_III", "Habilitado_VAAR", "Benef_VAAR"]
        self.assertEqual(_difs(novo, velho, campos), 0)

    def test_inep_ideb_rend_inse(self):
        from src.parse.inep import construir_ideb, construir_rend, construir_inse
        self.assertEqual(_difs(construir_ideb(RAW), json.load(open(PROC / "ideb.json")),
                               ["ai_ideb", "ai_mat", "af_ideb", "em_ideb"]), 0)
        self.assertEqual(_difs(construir_rend(RAW), json.load(open(PROC / "rend.json")),
                               ["ap_fun", "rp_fun", "ab_fun", "ap_med"]), 0)
        self.assertEqual(_difs(construir_inse(RAW), json.load(open(PROC / "inse.json")),
                               ["inse_mun", "inse_tot"]), 0)

    def test_agregados_painel_reconstruido(self):
        import shutil, tempfile
        from src.parse.build_all import construir, _agregados_painel
        tmp = Path(tempfile.mkdtemp()) / "processed"
        (tmp / "geo").mkdir(parents=True)
        for rel in ("conect.json", "sim_atend.json", "geo/uf_simpl.json", "geo/mun_simpl.json"):
            shutil.copy(PROC / rel, tmp / rel)
        construir(tmp)
        ag = _agregados_painel(tmp)
        self.assertEqual(ag["entes"], 5596)
        self.assertEqual(ag["habilitados"], 3076)
        self.assertEqual(ag["gargalo_cond3"], 1930)


if __name__ == "__main__":
    unittest.main()
