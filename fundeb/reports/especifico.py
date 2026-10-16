"""Relatório Específico por rede — público: secretaria municipal ou estadual.

Para um único ente (por código IBGE), apresenta identificação, situação no VAAR,
indicadores das cinco dimensões comparados às médias da própria rede e do país,
e um plano de ação objetivo ligado às condicionalidades reprovadas.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer

from fundeb.services.analytics import AnalyticsService
from fundeb.domain.legal import CONDICIONALIDADE_POR_CODIGO
from fundeb.programas.suplementares import impacto_subcontagem
from fundeb.etl.indicadores import (
    CATALOGO, DIMENSOES, FINANCEIRO, indicadores_da_dimensao,
)
from fundeb.reports.pdf_kit import (
    MARGEM, LARGURA_UTIL, ST,
    FaixaCapa, bluf, faixa_kpis, tabela, regua,
    rodape_callback, carimbo_data, moeda, pct, numero, valor_indicador,
    VERDE, VERMELHO,
)

FONTE_RODAPE = "Painel FUNDEB & VAAR 2026 · Dados oficiais FNDE/Inep · Relatório individual gerado automaticamente"


def _doc(caminho: Path, titulo: str) -> BaseDocTemplate:
    doc = BaseDocTemplate(
        str(caminho), pagesize=A4,
        leftMargin=MARGEM, rightMargin=MARGEM, topMargin=MARGEM, bottomMargin=20 * 2.83465,
        title=titulo, author="Painel FUNDEB",
    )
    frame = Frame(MARGEM, 16 * 2.83465, LARGURA_UTIL, A4[1] - MARGEM - 16 * 2.83465, id="corpo")
    doc.addPageTemplates([PageTemplate(id="padrao", frames=[frame], onPage=rodape_callback(FONTE_RODAPE))])
    return doc


def _media_rede(df: pd.DataFrame, rede: str, coluna: str) -> float:
    return float(df[df["rede"] == rede][coluna].mean())


def relatorio_especifico(df: pd.DataFrame, ibge: str, caminho: str | Path) -> Path:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    match = df[df["ibge"].astype(str) == str(ibge)]
    if match.empty:
        raise ValueError(f"Ente IBGE {ibge} não encontrado na base.")
    ente = match.iloc[0]
    analytics = AnalyticsService(df)
    plano = analytics.plano_de_acao_ente(str(ibge))

    titulo = f"Relatório — {ente['nome']} ({ente['uf']})"
    fl: list = []

    # ---------------------------------------------------------------- capa
    situacao = "Habilitada e beneficiária do VAAR" if ente["beneficiario"] else (
        "Habilitada ao VAAR" if ente["habilitado"] else "Não habilitada ao VAAR 2026")
    fl.append(FaixaCapa(
        ente["nome"],
        f"{ente['rede']} · {ente['uf']} · {ente['regiao']} · {situacao}",
        f"Relatório Individual · Rede {ente['rede']}",
    ))
    fl.append(Spacer(1, 10))
    fl.append(Paragraph(f"Código IBGE {ente['ibge']} · Emitido em {carimbo_data()}", ST["corpo_cinza"]))
    fl.append(Spacer(1, 8))

    # ---------------------------------------------------------------- BLUF individual
    reprov = int(ente["n_reprovacoes"])
    if ente["beneficiario"]:
        frase = (f"A rede está <b>habilitada e recebendo VAAR</b> ({moeda(ente['vaar'])} em 2026). "
                 "O foco passa a ser sustentar as condicionalidades e evoluir nos indicadores de aprendizagem.")
    elif reprov == 0:
        frase = "A rede cumpre as cinco condicionalidades. Verifique a publicação do coeficiente e a situação de beneficiária."
    else:
        pend = f" Pendência registrada: {ente['pendencia']}." if ente["pendencia"] else ""
        frase = (f"A rede está <b>fora do VAAR 2026</b> por reprovar <b>{reprov}</b> de 5 condicionalidades."
                 f"{pend} O plano de ação abaixo lista o que destrava a habilitação.")
    fl.append(bluf(frase))

    # ---------------------------------------------------------------- KPIs do ente
    fl.append(faixa_kpis([
        ("VAAR 2026", moeda(ente["vaar"]), f"2025: {moeda(ente['vaar_2025'])}"),
        ("Complementação União", moeda(ente["uniao_total"]), "VAAF+VAAT+VAAR"),
        ("Condicionalidades", f"{5 - reprov}/5", "cumpridas"),
        ("Transição", str(ente["transicao"]), "2025 → 2026"),
    ]))
    fl.append(Spacer(1, 10))

    # ---------------------------------------------------------------- Indicadores por dimensão (vs médias)
    fl.append(Paragraph("Indicadores por dimensão — rede vs. médias", ST["h1"]))
    media_nac_col = {ind.coluna: float(df[ind.coluna].mean()) for ind in CATALOGO
                     if ind.coluna in df.columns and ind.tipo != "bool"}

    for dim in DIMENSOES:
        if dim == FINANCEIRO:
            continue  # já coberto nos KPIs; evita duplicar valores monetários por ente
        inds = [i for i in indicadores_da_dimensao(dim) if i.coluna in df.columns and i.tipo != "bool"]
        if not inds:
            continue
        fl.append(Paragraph(dim, ST["h2"]))
        linhas = []
        for ind in inds:
            v = ente[ind.coluna]
            if v != v:  # NaN → sem dado na fonte
                continue
            m_rede = _media_rede(df, ente["rede"], ind.coluna)
            m_nac = media_nac_col.get(ind.coluna, float("nan"))
            # Sinal de comparação com a média da própria rede
            if ind.melhor == "maior":
                sinal = "▲ acima" if v >= m_rede else "▼ abaixo"
            elif ind.melhor == "menor":
                sinal = "▲ melhor" if v <= m_rede else "▼ pior"
            else:
                sinal = "—"
            linhas.append([
                ind.rotulo,
                valor_indicador(v, ind.unidade),
                valor_indicador(m_rede, ind.unidade),
                valor_indicador(m_nac, ind.unidade),
                sinal,
            ])
        if linhas:
            fl.append(tabela(
                ["Indicador", "Esta rede", f"Média {ente['rede'].lower()}", "Média Brasil", "Posição"],
                linhas,
                larguras=[LARGURA_UTIL * w for w in (0.38, 0.15, 0.17, 0.15, 0.15)],
                alinhar_dir=(1, 2, 3),
            ))
            fl.append(Spacer(1, 6))

    # ---------------------------------------------------------------- Plano de ação
    fl.append(Spacer(1, 2))
    fl.append(Paragraph("Plano de ação — condicionalidades", ST["h1"]))
    linhas_acao = []
    for c, rotulo in [("c1", "Cond. I"), ("c2", "Cond. II"), ("c3", "Cond. III"),
                      ("c4", "Cond. IV"), ("c5", "Cond. V")]:
        cumpriu = bool(ente[c])
        cond = CONDICIONALIDADE_POR_CODIGO[c]
        status = "Cumprida" if cumpriu else "REPROVADA"
        acao = "Manter comprovação vigente." if cumpriu else cond.como_cumprir
        linhas_acao.append([f"{rotulo} — {cond.titulo}", status, acao])
    fl.append(tabela(
        ["Condicionalidade", "Status", "O que fazer"],
        linhas_acao,
        larguras=[LARGURA_UTIL * w for w in (0.30, 0.13, 0.57)],
    ))

    # ---------------------------------------------------------------- PNAE/PNATE
    fl.append(Spacer(1, 6))
    fl.append(Paragraph("Programas suplementares — exposição à subcontagem", ST["h1"]))
    fl.append(Paragraph(
        "PNAE (alimentação) e PNATE (transporte rural) são repassados <b>por aluno do "
        "Censo Escolar</b>. Cada aluno não cadastrado no Educacenso deixa de gerar, por ano:",
        ST["corpo"]))
    fl.append(Spacer(1, 4))
    linhas_imp = []
    for n in (100, 500, 1000):
        imp = impacto_subcontagem(n, pct_rural=15.0)
        linhas_imp.append([
            f"{numero(n)} alunos",
            f"{moeda(imp.pnae_min)} – {moeda(imp.pnae_max)}",
            f"{moeda(imp.pnate_min)} – {moeda(imp.pnate_max)}",
            f"{moeda(imp.total_min)} – {moeda(imp.total_max)}",
        ])
    fl.append(tabela(
        ["Subcontagem", "PNAE/ano", "PNATE/ano (15% rural)", "Total PNAE+PNATE/ano"],
        linhas_imp, alinhar_dir=(1, 2, 3)))
    fl.append(Spacer(1, 4))
    fl.append(Paragraph(
        "Faixa do PNAE entre a menor etapa regular e a creche; PNATE sobre 15% rurais "
        "(per capita por município). Valores per capita: Res. CD/FNDE nº 1/2026 (PNAE) e "
        "nº 14/2026 (PNATE). A perda total inclui ainda Fundeb (VAAF/VAAT) e VAAR.",
        ST["corpo_cinza"]))

    fl.append(Spacer(1, 8))
    fl.append(regua())
    fl.append(Paragraph(
        "Comparações usam as médias da base auditada (FNDE 2026 + Inep 2025 + INSE 2023). "
        "Células com “—” indicam indicador não publicado pela fonte para esta rede; nenhum valor é estimado.",
        ST["rodape"]))

    _doc(caminho, titulo).build(fl)
    return caminho
