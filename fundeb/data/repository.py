"""Repositório de dados.

``DataRepository`` é a abstração (Protocol) de que os serviços e a interface dependem
(inversão de dependência). ``JsonDataRepository`` é a implementação que lê os arquivos
processados em ``data/processed``. Nenhum valor é inventado: campos ausentes na fonte
viram ``NaN`` e são contabilizados na página de Qualidade.
"""
from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path
from typing import Any, Protocol

import numpy as np
import pandas as pd

from fundeb.config import DATA_DIR
from fundeb.domain.territorio import REGIAO_POR_UF
from fundeb.data.sources import FONTES

ANOS_IEE = tuple(range(2017, 2024))
COND_COLS = ("c1", "c2", "c3", "c4", "c5")


class DataRepository(Protocol):
    def entes(self) -> pd.DataFrame: ...
    def geo_uf(self) -> dict: ...
    def geo_municipios(self, codigo_uf: str) -> dict: ...
    def arquivos(self) -> list[Path]: ...


# ---------------------------------------------------------------- helpers puros
def _sim(v: Any) -> bool:
    return str(v or "").strip().lower().startswith("s")


def _num(v: Any) -> float:
    return float(v) if v is not None else np.nan


def _area(ring: list) -> float:
    s = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        s += x1 * y2 - x2 * y1
    return s / 2.0


def rebobinar_para_d3(polys: list) -> list:
    """Garante o sentido de anel esperado pelo d3-geo (Plotly): externo horário, buracos anti-horários."""
    out = []
    for poly in polys:
        aneis = []
        for i, ring in enumerate(poly):
            horario = _area(ring) < 0
            if horario != (i == 0):
                ring = ring[::-1]
            aneis.append(ring)
        out.append(aneis)
    return out


def _feature(fid: str, polys: list, **props) -> dict:
    return {"type": "Feature", "id": fid, "properties": props,
            "geometry": {"type": "MultiPolygon", "coordinates": rebobinar_para_d3(polys)}}


# ---------------------------------------------------------------- implementação
class JsonDataRepository:
    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self._dir = Path(data_dir)

    def _load(self, nome: str, opcional: bool = False) -> Any:
        p = self._dir / nome
        if opcional and not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    def arquivos(self) -> list[Path]:
        return [self._dir / f.arquivo for f in FONTES]

    def entes(self) -> pd.DataFrame:
        recs = self._load("base_clean.json")["recs"]
        v25 = self._load("v2025.json")
        ideb, rend = self._load("ideb.json"), self._load("rend.json")
        inse, con = self._load("inse.json"), self._load("conect.json")
        sim = self._load("sim_atend.json", opcional=True)

        linhas = []
        for o in recs:
            ib = str(o["IBGE"])
            I, R, N, K, S = (d.get(ib, {}) for d in (ideb, rend, inse, con, sim))
            linha = {
                "ibge": ib, "uf": o["UF"], "regiao": REGIAO_POR_UF.get(o["UF"]),
                "nome": o["Entidade"].title() if o["Rede"] == "Municipal" else f"Rede estadual — {o['UF']}",
                "rede": o["Rede"],
                # Financiamento (FNDE). VAAR/VAAT ausentes na publicação = não recebido (0).
                "receita_contrib": _num(o["Receita_Contrib"]),
                "vaaf": o["Compl_VAAF"] or 0.0, "vaat": o["Compl_VAAT"] or 0.0,
                "vaar": o["Compl_VAAR"] or 0.0, "uniao_total": o["Compl_Uniao_Total"] or 0.0,
                "vaar_atend": o["Est_VAAR_atend"] or 0.0, "vaar_aprend": o["Est_VAAR_aprend"] or 0.0,
                "vaar_2025": float(v25.get(ib) or 0.0),
                "vaat_ei": o["Compl_VAAT_EI"] or 0.0,
                "vaat_antes": _num(o["VAAT_antes"]), "vaat_com_compl": _num(o["VAAT_com_compl"]),
                "iei": _num(o["IEI_pct"]), "pond_nse": _num(o["Pond_NSE"]), "pond_drec": _num(o["Pond_Drec"]),
                # VAAR — indicadores e condicionalidades
                "ind_atend": _num(o["VAAR_ind_atend"]), "ind_aprend": _num(o["VAAR_ind_aprend"]),
                "evoluiu_atend": _sim(o["VAAR_evoluiu_atend"]), "evoluiu_aprend": _sim(o["VAAR_evoluiu_aprend"]),
                **{c: _sim(o[f"Cond_{r}"]) for c, r in zip(COND_COLS, ("I", "II", "III", "IV", "V"))},
                "habilitado": str(o["Habilitado_VAAR"]).lower().startswith("habilit"),
                "beneficiario": str(o["Benef_VAAR"]).lower().startswith("benef"),
                "pendencia": (o["Pend_VAAR"] or "").strip(),
                # Inep
                "ideb_ai": _num(I.get("ai_ideb")), "ideb_af": _num(I.get("af_ideb")), "ideb_em": _num(I.get("em_ideb")),
                "saeb_ai_mt": _num(I.get("ai_mat")), "saeb_ai_lp": _num(I.get("ai_lp")),
                "saeb_af_mt": _num(I.get("af_mat")), "saeb_af_lp": _num(I.get("af_lp")),
                "saeb_em_mt": _num(I.get("em_mat")), "saeb_em_lp": _num(I.get("em_lp")),
                "aprov_fund": _num(R.get("ap_fun")), "reprov_fund": _num(R.get("rp_fun")),
                "aband_fund": _num(R.get("ab_fun")), "aprov_med": _num(R.get("ap_med")),
                "aband_med": _num(R.get("ab_med")), "inse": _num(N.get("inse_mun")),
                # Conectividade
                "net_pct": _num(K.get("cn_net")), "net_aprend_pct": _num(K.get("cn_aprend")),
                "download_mbps": _num(K.get("cn_down")), "escolas_medidas": _num(K.get("cn_n")),
                # Série do IEE (Simulador-VAAR-PI)
                "mat_eb_2023": _num(S.get("mat_eb")) if S.get("mat_eb") else np.nan,
                "iee_ciclo2024": _num(S.get("iee")),
                **{f"mat_iee_{a}": (_num(S.get(f"m{a % 100}")) if S else np.nan) for a in ANOS_IEE},
            }
            linhas.append(linha)

        df = pd.DataFrame(linhas)
        recebeu25, recebe26 = df["vaar_2025"] > 0, df["vaar"] > 0
        df["transicao"] = np.select(
            [recebeu25 & recebe26, recebeu25 & ~recebe26, ~recebeu25 & recebe26],
            ["Manteve", "Perdeu", "Entrou"], default="Fora")
        df["n_reprovacoes"] = (~df[list(COND_COLS)]).sum(axis=1)
        return df

    @cached_property
    def _geo_uf_raw(self) -> dict:
        return self._load("geo/uf_simpl.json")

    @cached_property
    def _geo_mun_raw(self) -> dict:
        return self._load("geo/mun_simpl.json")

    def geo_uf(self) -> dict:
        return {"type": "FeatureCollection",
                "features": [_feature(cod, v["g"], sigla=v["s"]) for cod, v in self._geo_uf_raw.items()]}

    def geo_municipios(self, codigo_uf: str) -> dict:
        return {"type": "FeatureCollection",
                "features": [_feature(ib, polys) for ib, polys in self._geo_mun_raw.items()
                             if ib.startswith(codigo_uf)]}
