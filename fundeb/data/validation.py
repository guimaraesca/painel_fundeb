"""Verificações automáticas de integridade e proveniência.

As verificações provam consistência interna da fonte (somas que fecham, regras de
habilitação coerentes, faixas válidas). Anomalias da fonte NÃO são corrigidas:
são listadas para transparência.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from fundeb.data.repository import COND_COLS, DataRepository
from fundeb.data.sources import FONTE_POR_ARQUIVO

OK, ALERTA, FALHA = "ok", "alerta", "falha"
_ID = ["ibge", "uf", "nome", "rede"]


@dataclass(frozen=True)
class Verificacao:
    nome: str
    status: str
    detalhe: str
    excecoes: pd.DataFrame | None = field(default=None, compare=False)


def _v(nome: str, falhas: pd.DataFrame, detalhe: str, nivel: str = FALHA, cols: list[str] | None = None) -> Verificacao:
    status = OK if falhas.empty else nivel
    exc = None if falhas.empty else falhas[_ID + (cols or [])]
    return Verificacao(nome, status, detalhe, exc)


def verificar(df: pd.DataFrame) -> list[Verificacao]:
    out: list[Verificacao] = []
    dup = df[df["ibge"].duplicated(keep=False)]
    out.append(_v("Código IBGE único por rede", dup, f"{len(df):,} redes".replace(",", ".")))

    n_est = int((df["rede"] == "Estadual").sum())
    out.append(Verificacao("27 redes estaduais (26 UFs + DF)", OK if n_est == 27 else FALHA, f"{n_est} encontradas"))

    soma = df[(df["vaaf"] + df["vaat"] + df["vaar"] - df["uniao_total"]).abs() > 1.0]
    out.append(_v("VAAF + VAAT + VAAR = Complementação total (tolerância R$ 1)", soma,
                  "Fecha linha a linha", cols=["vaaf", "vaat", "vaar", "uniao_total"]))

    split = df[(df["vaar_atend"] + df["vaar_aprend"] - df["vaar"]).abs() > 1.0]
    out.append(_v("VAAR = parcela Atendimento + parcela Aprendizagem", split, "Fecha linha a linha",
                  cols=["vaar", "vaar_atend", "vaar_aprend"]))

    a, p = df["vaar_atend"].sum(), df["vaar_aprend"].sum()
    share = a / (a + p) if (a + p) else 0
    out.append(Verificacao("Repartição nacional do VAAR 50% / 50%", OK if abs(share - 0.5) < 1e-3 else FALHA,
                           f"Atendimento {share:.4%} · Aprendizagem {1 - share:.4%}"))

    out.append(_v("Beneficiária ⇒ habilitada", df[df["beneficiario"] & ~df["habilitado"]],
                  "Nenhuma rede recebe sem estar habilitada"))

    todas = df[list(COND_COLS)].all(axis=1)
    out.append(_v("Habilitada ⇔ cumpre as 5 condicionalidades", df[df["habilitado"] != todas],
                  "Divergências entre o status publicado e as condicionalidades publicadas", ALERTA,
                  cols=list(COND_COLS) + ["habilitado", "pendencia"]))

    out.append(_v("VAAR > 0 ⇔ beneficiária", df[(df["vaar"] > 0) != df["beneficiario"]],
                  "Divergência entre valor publicado e situação de beneficiária", ALERTA, cols=["vaar", "beneficiario"]))

    out.append(_v("Parcela Aprendizagem > 0 ⇒ evoluiu em aprendizagem",
                  df[(df["vaar_aprend"] > 0) & ~df["evoluiu_aprend"]],
                  "Redes com valor na parcela sem a marcação de evolução", ALERTA,
                  cols=["vaar_aprend", "ind_aprend", "evoluiu_aprend"]))
    out.append(_v("Parcela Atendimento > 0 ⇒ evoluiu em atendimento",
                  df[(df["vaar_atend"] > 0) & ~df["evoluiu_atend"]],
                  "Redes com valor na parcela sem a marcação de evolução", ALERTA,
                  cols=["vaar_atend", "ind_atend", "evoluiu_atend"]))

    for col, lo, hi, rot in (("ideb_ai", 0, 10, "Ideb AI"), ("ideb_af", 0, 10, "Ideb AF"), ("ideb_em", 0, 10, "Ideb EM"),
                             ("aprov_fund", 0, 100, "Aprovação EF"), ("aband_fund", 0, 100, "Abandono EF"),
                             ("inse", 1, 8, "INSE"), ("net_aprend_pct", 0, 100, "Internet p/ aprendizagem")):
        s = df[col]
        fora = df[s.notna() & ((s < lo) | (s > hi))]
        out.append(_v(f"Faixa válida — {rot} [{lo}, {hi}]", fora, f"{int(s.notna().sum()):,} valores".replace(",", "."),
                      cols=[col]))
    return out


def cobertura(df: pd.DataFrame) -> pd.DataFrame:
    grupos = {
        "Ideb anos iniciais": "ideb_ai", "Ideb anos finais": "ideb_af", "Ideb ensino médio": "ideb_em",
        "Taxas de rendimento (EF)": "aprov_fund", "INSE": "inse", "Conectividade": "net_aprend_pct",
        "Série de matrículas do IEE": "mat_iee_2023", "Matrícula total 2023": "mat_eb_2023",
    }
    linhas = []
    for rotulo, col in grupos.items():
        for rede in ("Estadual", "Municipal"):
            sub = df[df["rede"] == rede]
            linhas.append({"Indicador": rotulo, "Rede": rede, "Com dado": int(sub[col].notna().sum()),
                           "Total": len(sub), "Cobertura": sub[col].notna().mean()})
    return pd.DataFrame(linhas)


def _registros(p: Path) -> int | None:
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    if isinstance(d, dict) and "recs" in d:
        return len(d["recs"])
    return len(d) if isinstance(d, (dict, list)) else None


def proveniencia(repo: DataRepository) -> pd.DataFrame:
    linhas = []
    for p in repo.arquivos():
        rel = p.relative_to(p.parents[1]) if p.parent.name == "geo" else Path(p.name)
        fonte = FONTE_POR_ARQUIVO.get(str(rel).replace("\\", "/"))
        existe = p.exists()
        linhas.append({
            "Arquivo": str(rel), "Conteúdo": fonte.conteudo if fonte else "", "Origem": fonte.origem if fonte else "",
            "Registros": _registros(p) if existe else None,
            "Tamanho (KB)": round(p.stat().st_size / 1024) if existe else None,
            "SHA-256": hashlib.sha256(p.read_bytes()).hexdigest() if existe else "AUSENTE",
        })
    return pd.DataFrame(linhas)
