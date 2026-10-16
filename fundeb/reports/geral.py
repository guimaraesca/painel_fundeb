"""Relatório Geral (panorama nacional) — público: MEC e gestão macro.

Consolida, em um único PDF, a leitura das cinco dimensões: financiamento,
fluxo escolar, aprendizagem (Ideb/Saeb), contexto e condicionalidades/VAAR —
indo além do recorte exclusivamente financeiro das versões anteriores.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer

from fundeb.services.analytics import AnalyticsService
from fundeb.etl.consolidate import agregados
from fundeb.reports.pdf_kit import (
    MARGEM, LARGURA_UTIL, ST,
    FaixaCapa, bluf, faixa_kpis, tabela, grafico_barras, regua,
    rodape_callback, carimbo_data, moeda, pct, numero,
    AZUL_CLARO, VERDE, VERMELHO, AMBAR,
)

FONTE_RODAPE = "Painel FUNDEB & VAAR 2026 · Dados oficiais FNDE/Inep · Lei nº 14.113/2020 · Relatório gerado automaticamente"


def _doc(caminho: Path) -> BaseDocTemplate:
    doc = BaseDocTemplate(
        str(caminho), pagesize=A4,
        leftMargin=MARGEM, rightMargin=MARGEM, topMargin=MARGEM, bottomMargin=20 * 2.83465,
        title="Relatório Geral FUNDEB & VAAR 2026", author="Painel FUNDEB",
    )
    frame = Frame(MARGEM, 16 * 2.83465, LARGURA_UTIL, A4[1] - MARGEM - 16 * 2.83465, id="corpo")
    doc.addPageTemplates([PageTemplate(id="padrao", frames=[frame], onPage=rodape_callback(FONTE_RODAPE))])
    return doc


def relatorio_geral(df: pd.DataFrame, caminho: str | Path) -> Path:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    analytics = AnalyticsService(df)
    r = analytics.resumo_nacional()
    aggs = agregados(df)
    gargalos = analytics.gargalos_condicionalidade()
    g1 = gargalos[0]

    fl: list = []
    # ---------------------------------------------------------------- capa
    fl.append(FaixaCapa(
        "Relatório Geral — FUNDEB & VAAR 2026",
        "Panorama nacional de financiamento, fluxo, aprendizagem e condicionalidades da "
        "Complementação-VAAR, por rede estadual e municipal.",
        "Panorama Nacional · MEC",
    ))
    fl.append(Spacer(1, 10))
    fl.append(Paragraph(f"Emitido em {carimbo_data()} · 5.596 redes (27 estaduais + 5.569 municipais)", ST["corpo_cinza"]))
    fl.append(Spacer(1, 8))

    # ---------------------------------------------------------------- BLUF
    fl.append(bluf(
        f"<b>{numero(r.nao_habilitados)}</b> redes ({pct(r.pct_nao_habilitados)}) ficaram fora do VAAR 2026. "
        f"A causa dominante é única: <b>{numero(g1.reprovacoes_nao_habilitadas)}</b> delas "
        f"({pct(g1.pct_sobre_nao_habilitadas)} das não habilitadas) falham na <b>{g1.codigo} — "
        "Redução de Desigualdades</b>. O VAAR responde por apenas "
        f"<b>{pct(r.total_vaar_reais / r.total_uniao_reais * 100)}</b> da Complementação da União, mas é a "
        "única parcela condicionada a desempenho — e, por isso, a mais sensível à gestão."
    ))

    # ---------------------------------------------------------------- KPIs
    fl.append(faixa_kpis([
        ("Redes habilitadas", numero(r.habilitados), f"{pct(r.pct_habilitados)} do total"),
        ("Fora do VAAR", numero(r.nao_habilitados), f"{pct(r.pct_nao_habilitados)} a recuperar"),
        ("VAAR distribuído", moeda(r.total_vaar_reais), f"de {moeda(r.total_uniao_reais)} da União"),
        ("Transição 2025→2026", f"+{r.transicao_entrou} / -{r.transicao_perdeu}", f"{r.transicao_manteve} mantiveram"),
    ]))
    fl.append(Spacer(1, 10))

    # ---------------------------------------------------------------- Financiamento
    fl.append(Paragraph("1. Financiamento — Complementação da União", ST["h1"]))
    reg = aggs["por_regiao"]
    fl.append(grafico_barras(
        list(reg["regiao"]), [v / 1e6 for v in reg["vaar"]],
        "VAAR por grande região (R$ milhões)", cor=AZUL_CLARO,
    ))
    fl.append(Spacer(1, 6))

    # ---------------------------------------------------------------- Fluxo escolar
    fl.append(Paragraph("2. Fluxo escolar — rendimento (Inep 2025)", ST["h1"]))
    rede = aggs["por_rede"].set_index("rede")
    linhas_fluxo = []
    for nome in ("Estadual", "Municipal"):
        if nome in rede.index:
            row = rede.loc[nome]
            linhas_fluxo.append([
                f"Rede {nome}", pct(row["aprov_fund"]), pct(row["aband_fund"]), pct(row["aband_med"]),
            ])
    fl.append(tabela(
        ["Recorte", "Aprovação EF", "Abandono EF", "Abandono EM"],
        linhas_fluxo, alinhar_dir=(1, 2, 3),
    ))
    fl.append(Spacer(1, 4))
    fl.append(Paragraph(
        "O abandono no Ensino Médio é o principal gargalo de fluxo da rede estadual; "
        "a aprovação no Fundamental tende a ser mais alta na rede municipal.", ST["corpo_cinza"]))
    fl.append(Spacer(1, 8))

    # ---------------------------------------------------------------- Aprendizagem
    fl.append(Paragraph("3. Aprendizagem — Ideb (Inep 2025)", ST["h1"]))
    linhas_ideb = []
    for nome in ("Estadual", "Municipal"):
        if nome in rede.index:
            row = rede.loc[nome]
            linhas_ideb.append([
                f"Rede {nome}", numero(row["ideb_ai"], 1), numero(row["ideb_af"], 1), numero(row["ideb_em"], 1),
            ])
    fl.append(tabela(
        ["Recorte", "Ideb Anos Iniciais", "Ideb Anos Finais", "Ideb Ensino Médio"],
        linhas_ideb, alinhar_dir=(1, 2, 3),
    ))
    fl.append(Spacer(1, 10))

    # ---------------------------------------------------------------- Condicionalidades
    fl.append(Paragraph("4. Condicionalidades — onde as redes são barradas", ST["h1"]))
    cats = [f"{g.codigo}" for g in gargalos]
    vals = [g.reprovacoes_nao_habilitadas for g in gargalos]
    fl.append(grafico_barras(cats, vals, "Reprovações entre redes NÃO habilitadas (art. 14, § 1º)",
                             cor=VERMELHO))
    fl.append(Spacer(1, 6))

    # ---------------------------------------------------------------- Ranking UF (top 12)
    fl.append(Paragraph("5. Prioridades por Unidade da Federação", ST["h1"]))
    uf = aggs["por_uf"].copy()
    uf["fora"] = uf["redes"] - uf["habilitadas"]
    top = uf.sort_values("fora", ascending=False).head(12)
    linhas_uf = [[
        row["uf"], numero(row["redes"]), numero(row["habilitadas"]),
        numero(row["fora"]), pct(row["pct_habilitadas"]), moeda(row["vaar"]),
    ] for _, row in top.iterrows()]
    fl.append(tabela(
        ["UF", "Redes", "Habilit.", "Fora", "% Habilit.", "VAAR 2026"],
        linhas_uf,
        larguras=[LARGURA_UTIL * w for w in (0.10, 0.14, 0.15, 0.13, 0.18, 0.30)],
        alinhar_dir=(1, 2, 3, 4, 5),
    ))
    fl.append(Spacer(1, 8))
    fl.append(regua())
    fl.append(Paragraph(
        "Metodologia: base única auditada (FNDE 2026 + Inep Ideb/Saeb/Rendimento 2025 + INSE 2023 + "
        "conectividade). Campos não publicados pela fonte permanecem nulos (—); nenhum valor é sintético.",
        ST["rodape"]))

    _doc(caminho).build(fl)
    return caminho
