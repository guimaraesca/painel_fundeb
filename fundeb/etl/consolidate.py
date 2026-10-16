"""Transformação: base consolidada multidimensional + tabela-fato tidy.

Reutiliza ``JsonDataRepository.entes`` como núcleo do *transform* (garantindo que
a evolução use EXATAMENTE a mesma base auditada do painel) e enriquece com:

- colunas derivadas (ex.: delta do VAAR, situação de transição, ranking percentil);
- uma tabela-fato longa (``ente × indicador``) útil para relatórios e BI;
- agregações por público-alvo (nacional/MEC, por UF, por região, por rede).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from fundeb.data.repository import DataRepository, JsonDataRepository
from fundeb.etl.indicadores import CATALOGO


def consolidar(repo: DataRepository | None = None) -> pd.DataFrame:
    """Base consolidada (uma linha por rede) com todas as dimensões + derivados."""
    repo = repo or JsonDataRepository()
    df = repo.entes().copy()

    # Derivados financeiros
    df["delta_vaar"] = df["vaar"] - df["vaar_2025"]
    df["pct_uniao_vaar"] = np.where(df["uniao_total"] > 0, df["vaar"] / df["uniao_total"] * 100, np.nan)

    # Percentis de aprendizagem/fluxo dentro da mesma rede (comparabilidade justa)
    for col in ("ideb_ai", "ideb_af", "ideb_em", "aprov_fund", "aband_fund"):
        df[f"pctl_{col}"] = (
            df.groupby("rede")[col].rank(pct=True) * 100
        )

    return df


def tabela_fato(df: pd.DataFrame) -> pd.DataFrame:
    """Tabela-fato longa: uma linha por (ente, indicador). Base para BI e relatórios."""
    ids = ["ibge", "uf", "regiao", "nome", "rede"]
    registros = []
    for ind in CATALOGO:
        if ind.coluna not in df.columns:
            continue
        sub = df[ids + [ind.coluna]].copy()
        sub = sub.rename(columns={ind.coluna: "valor"})
        sub["indicador"] = ind.coluna
        sub["dimensao"] = ind.dimensao
        sub["rotulo"] = ind.rotulo
        sub["unidade"] = ind.unidade
        sub["fonte"] = ind.fonte
        if ind.tipo == "bool":
            sub["valor"] = sub["valor"].astype(float)
        registros.append(sub)
    fato = pd.concat(registros, ignore_index=True)
    return fato[ids + ["dimensao", "indicador", "rotulo", "unidade", "fonte", "valor"]]


def _agg(grp: pd.DataFrame) -> dict:
    tot = len(grp)
    return {
        "redes": tot,
        "habilitadas": int(grp["habilitado"].sum()),
        "pct_habilitadas": float(grp["habilitado"].mean() * 100) if tot else 0.0,
        "beneficiarias": int(grp["beneficiario"].sum()),
        "vaar": float(grp["vaar"].sum()),
        "uniao_total": float(grp["uniao_total"].sum()),
        # Médias dos indicadores não-financeiros (ignorando ausentes)
        "ideb_ai": float(grp["ideb_ai"].mean()),
        "ideb_af": float(grp["ideb_af"].mean()),
        "ideb_em": float(grp["ideb_em"].mean()),
        "aprov_fund": float(grp["aprov_fund"].mean()),
        "aband_fund": float(grp["aband_fund"].mean()),
        "aband_med": float(grp["aband_med"].mean()),
        "inse": float(grp["inse"].mean()),
        "net_aprend_pct": float(grp["net_aprend_pct"].mean()),
    }


def agregados(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Agregações por público-alvo: nacional (MEC), por UF, por região, por rede."""
    nacional = pd.DataFrame([{"escopo": "Brasil", **_agg(df)}])

    por_uf = (
        df.groupby("uf", group_keys=False)
        .apply(lambda g: pd.Series(_agg(g)), include_groups=False)
        .reset_index()
        .sort_values("vaar", ascending=False)
    )
    por_regiao = (
        df.groupby("regiao", group_keys=False)
        .apply(lambda g: pd.Series(_agg(g)), include_groups=False)
        .reset_index()
        .sort_values("vaar", ascending=False)
    )
    por_rede = (
        df.groupby("rede", group_keys=False)
        .apply(lambda g: pd.Series(_agg(g)), include_groups=False)
        .reset_index()
    )
    return {"nacional": nacional, "por_uf": por_uf, "por_regiao": por_regiao, "por_rede": por_rede}
