"""CLI de geração de relatórios PDF.

Uso:
    python -m fundeb.reports.generate --geral
    python -m fundeb.reports.generate --ente 3550308          # São Paulo (município)
    python -m fundeb.reports.generate --ente 35               # Rede estadual de SP
    python -m fundeb.reports.generate --uf SP --estaduais     # todas as redes estaduais da UF
    python -m fundeb.reports.generate --saida outputs/relatorios

Sem flag de conteúdo, gera o relatório geral.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from fundeb.config import ROOT
from fundeb.etl.consolidate import consolidar
from fundeb.reports.geral import relatorio_geral
from fundeb.reports.especifico import relatorio_especifico

SAIDA_PADRAO = ROOT / "outputs" / "relatorios"


def _slug(texto: str) -> str:
    import re
    s = re.sub(r"[^\w\s-]", "", texto, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s]+", "_", s)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Gera relatórios PDF do painel FUNDEB & VAAR 2026.")
    ap.add_argument("--geral", action="store_true", help="Relatório geral (panorama nacional / MEC).")
    ap.add_argument("--ente", metavar="IBGE", help="Relatório específico de uma rede (código IBGE).")
    ap.add_argument("--uf", metavar="UF", help="Filtra por UF (use com --estaduais).")
    ap.add_argument("--estaduais", action="store_true", help="Gera o relatório de cada rede estadual (da UF, se informada).")
    ap.add_argument("--saida", metavar="DIR", default=str(SAIDA_PADRAO), help="Diretório de saída dos PDFs.")
    args = ap.parse_args(argv)

    df = consolidar()
    saida = Path(args.saida)
    gerados: list[Path] = []

    if args.ente:
        ente = df[df["ibge"].astype(str) == str(args.ente)]
        nome = ente.iloc[0]["nome"] if not ente.empty else args.ente
        p = relatorio_especifico(df, str(args.ente), saida / f"ente_{args.ente}_{_slug(str(nome))}.pdf")
        gerados.append(p)
    elif args.estaduais:
        est = df[df["rede"] == "Estadual"]
        if args.uf:
            est = est[est["uf"] == args.uf.upper()]
        for _, row in est.iterrows():
            p = relatorio_especifico(df, str(row["ibge"]), saida / f"estadual_{row['uf']}_{row['ibge']}.pdf")
            gerados.append(p)
    else:
        p = relatorio_geral(df, saida / "relatorio_geral_fundeb_2026.pdf")
        gerados.append(p)

    print(f"{len(gerados)} relatório(s) gerado(s):")
    for p in gerados:
        print(f"  - {p}  ({p.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
