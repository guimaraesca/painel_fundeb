#!/usr/bin/env python3
"""Transform+Load — reconstrói ``data/processed`` a partir de ``data/raw``.

Reconstrói do zero, com paridade verificada, os cinco arquivos tabulares que
produzem todos os números do painel:
    base_clean.json · v2025.json · ideb.json · rend.json · inse.json

Mantém como inputs já preparados (proveniência documentada, sem URL simples):
    conect.json (NIC.br/SIMET via Base dos Dados) · sim_atend.json (Simulador-VAAR-PI)
    geo/*_simpl.json (malhas IBGE simplificadas)

Uso:
    python src/sources.py --download      # 1) baixa as fontes
    python -m src.parse.build_all         # 2) reconstrói data/processed
    python -m src.parse.build_all --check # 3) idem + relatório de paridade e agregados
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.parse.fnde import construir_base_clean, construir_v2025
from src.parse.inep import construir_ideb, construir_rend, construir_inse

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"

PRESERVADOS = ("conect.json", "sim_atend.json", "geo/uf_simpl.json", "geo/mun_simpl.json")


def _gravar(obj, nome: str, destino: Path) -> int:
    p = destino / nome
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return p.stat().st_size


def construir(destino: Path = PROC) -> dict[str, int]:
    """Gera os 5 arquivos tabulares em ``destino``. Retorna tamanhos em bytes."""
    tamanhos = {
        "base_clean.json": _gravar(construir_base_clean(RAW), "base_clean.json", destino),
        "v2025.json": _gravar(construir_v2025(RAW), "v2025.json", destino),
        "ideb.json": _gravar(construir_ideb(RAW), "ideb.json", destino),
        "rend.json": _gravar(construir_rend(RAW), "rend.json", destino),
        "inse.json": _gravar(construir_inse(RAW), "inse.json", destino),
    }
    return tamanhos


def _agregados_painel(proc_dir: Path) -> dict:
    """Carrega a base pelo repositório do painel e devolve agregados-chave."""
    from fundeb.data.repository import JsonDataRepository
    from fundeb.services.analytics import AnalyticsService
    df = JsonDataRepository(proc_dir).entes()
    a = AnalyticsService(df)
    r = a.resumo_nacional()
    g = {x.codigo: x.reprovacoes_nao_habilitadas for x in a.gargalos_condicionalidade()}
    return {
        "entes": r.total_entes, "estados": r.total_estados, "municipios": r.total_municipios,
        "habilitados": r.habilitados, "nao_habilitados": r.nao_habilitados,
        "vaar_bi": round(r.total_vaar_reais / 1e9, 3), "uniao_bi": round(r.total_uniao_reais / 1e9, 3),
        "gargalo_cond3": g.get("Cond. III"), "gargalo_cond1": g.get("Cond. I"), "gargalo_cond2": g.get("Cond. II"),
    }


def main() -> None:
    check = "--check" in sys.argv
    print("Reconstruindo data/processed a partir de data/raw...")
    tam = construir(PROC)
    for nome, b in tam.items():
        print(f"  ✓ {nome} ({b:,} bytes)".replace(",", "."))
    print("  (preservados: " + ", ".join(PRESERVADOS) + ")")
    if check:
        print("\nAgregados do painel sobre a base reconstruída:")
        ag = _agregados_painel(PROC)
        for k, v in ag.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
