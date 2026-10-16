"""Orquestrador do ETL completo (Extract → Transform → Load) com linhagem.

Estágios:
  1. EXTRACT  — fontes oficiais declaradas em ``src/sources.py`` (download roda na
     máquina do usuário; a rede do agente bloqueia gov.br/INEP). Os JSONs já
     processados em ``data/processed`` acompanham o projeto.
  2. TRANSFORM — ``consolidate.consolidar`` (reusa a base auditada do painel) e
     ``consolidate.tabela_fato`` (visão tidy multidimensional).
  3. LOAD     — grava artefatos analíticos em ``data/processed/warehouse`` e um
     ``manifest.json`` com proveniência (SHA-256), frescor, volumetria e o
     resultado das verificações de integridade.

Uso:
    python -m fundeb.etl.pipeline          # roda o ETL e grava o warehouse
    python -m fundeb.etl.pipeline --check  # roda e imprime o resumo de qualidade
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from fundeb.config import DATA_DIR
from fundeb.data.repository import JsonDataRepository
from fundeb.data.validation import verificar, cobertura, proveniencia
from fundeb.etl.consolidate import consolidar, tabela_fato, agregados
from fundeb.etl.indicadores import CATALOGO, DIMENSOES

WAREHOUSE = DATA_DIR / "warehouse"


def _resumo_verificacoes(df: pd.DataFrame) -> list[dict]:
    out = []
    for v in verificar(df):
        n_exc = 0 if v.excecoes is None else len(v.excecoes)
        out.append({"verificacao": v.nome, "status": v.status, "detalhe": v.detalhe, "excecoes": n_exc})
    return out


def executar(gravar: bool = True) -> dict:
    """Roda o pipeline e retorna o manifesto. Se ``gravar``, persiste os artefatos."""
    repo = JsonDataRepository()

    # TRANSFORM
    df = consolidar(repo)
    fato = tabela_fato(df)
    aggs = agregados(df)

    # Cobertura por indicador (freshness/qualidade das colunas não-financeiras)
    cob = cobertura(df)
    prov = proveniencia(repo)

    manifest = {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "versao_etl": "2.0",
        "volumetria": {
            "redes": int(len(df)),
            "estados": int((df["rede"] == "Estadual").sum()),
            "municipios": int((df["rede"] == "Municipal").sum()),
            "indicadores_catalogados": len(CATALOGO),
            "dimensoes": list(DIMENSOES),
            "linhas_tabela_fato": int(len(fato)),
        },
        "qualidade": _resumo_verificacoes(df),
        "cobertura_por_indicador": [
            {
                "indicador": r["Indicador"], "rede": r["Rede"],
                "com_dado": int(r["Com dado"]), "total": int(r["Total"]),
                "cobertura_pct": round(float(r["Cobertura"]) * 100, 1),
            }
            for _, r in cob.iterrows()
        ],
        "proveniencia": [
            {
                "arquivo": r["Arquivo"], "conteudo": r["Conteúdo"], "origem": r["Origem"],
                "registros": (int(r["Registros"]) if pd.notna(r["Registros"]) else None),
                "sha256": r["SHA-256"],
            }
            for _, r in prov.iterrows()
        ],
    }

    if gravar:
        WAREHOUSE.mkdir(parents=True, exist_ok=True)
        df.to_parquet(WAREHOUSE / "consolidado.parquet", index=False)
        fato.to_parquet(WAREHOUSE / "fato_indicadores.parquet", index=False)
        for nome, tab in aggs.items():
            tab.to_parquet(WAREHOUSE / f"agg_{nome}.parquet", index=False)
        (WAREHOUSE / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return manifest


def main() -> None:
    check = "--check" in sys.argv
    manifest = executar(gravar=True)
    v = manifest["volumetria"]
    print(f"ETL v{manifest['versao_etl']} concluído — {manifest['gerado_em']}")
    print(f"  {v['redes']} redes · {v['estados']} estaduais · {v['municipios']} municipais")
    print(f"  {v['indicadores_catalogados']} indicadores em {len(v['dimensoes'])} dimensões")
    print(f"  tabela-fato: {v['linhas_tabela_fato']:,} linhas".replace(",", "."))
    print(f"  artefatos em: {WAREHOUSE}")
    if check:
        print("\nQualidade:")
        for q in manifest["qualidade"]:
            marca = {"ok": "✓", "alerta": "!", "falha": "✗"}.get(q["status"], "?")
            extra = f" ({q['excecoes']} exceções)" if q["excecoes"] else ""
            print(f"  [{marca}] {q['verificacao']}{extra}")


if __name__ == "__main__":
    main()
