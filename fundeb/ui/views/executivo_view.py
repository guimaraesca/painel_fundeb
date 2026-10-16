"""Versão Executiva — painel de decisão direto (BLUF).

Reutiliza integralmente a camada de dados (``AnalyticsService`` sobre o mesmo
``JsonDataRepository`` da versão completa), garantindo paridade de bases. A
diferença é de apresentação: menos telas, conclusão antes da evidência e foco
em "onde agir" e "quanto custa não agir".
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from fundeb.services.analytics import AnalyticsService
from fundeb.ui.components import (
    format_currency,
    format_int,
    format_percent,
    metric_card,
)
from fundeb.ui.charts import (
    CORES_REGIAO,
    chart_ranking_horizontal,
    chart_part_to_whole_100,
)


# ------------------------------------------------------------------ utilidades
def _hero(titulo: str, subtitulo: str, tag: str) -> None:
    st.markdown(
        f"""
        <div class="exec-hero">
            <h1>{titulo}</h1>
            <p>{subtitulo}</p>
            <span class="tag">{tag}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _bluf(texto_html: str) -> None:
    st.markdown(f'<div class="exec-bluf">{texto_html}</div>', unsafe_allow_html=True)


def _section(titulo: str, subtitulo: str = "") -> None:
    st.markdown(f'<div class="exec-section-title">{titulo}</div>', unsafe_allow_html=True)
    if subtitulo:
        st.markdown(f'<div class="exec-section-sub">{subtitulo}</div>', unsafe_allow_html=True)


def _source(texto: str) -> None:
    st.markdown(f'<div class="exec-source">{texto}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ 1. Sumário
def _sumario_executivo(analytics: AnalyticsService) -> None:
    r = analytics.resumo_nacional()
    gargalos = analytics.gargalos_condicionalidade()
    g1 = gargalos[0]  # maior gargalo

    _hero(
        "FUNDEB &amp; VAAR 2026 — Leitura Executiva",
        "Diagnóstico direto da habilitação à Complementação-VAAR e das decisões que a destravam.",
        "DADOS OFICIAIS FNDE / INEP · CICLO 2026",
    )

    _bluf(
        f"<b>{format_int(r.nao_habilitados)}</b> de <b>{format_int(r.total_entes)}</b> redes "
        f"({format_percent(r.pct_nao_habilitados)}) ficaram fora do VAAR 2026. "
        f"<b>A causa dominante é uma só:</b> {format_int(g1.reprovacoes_nao_habilitadas)} delas "
        f"({format_percent(g1.pct_sobre_nao_habilitadas)} das não habilitadas) falham na "
        f"<b>{g1.codigo} — Redução de Desigualdades</b>. Atacá-la é a alavanca de maior retorno."
    )

    # KPIs essenciais (uma linha, leitura em 5 segundos)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card(
            "Redes habilitadas",
            f"{format_int(r.habilitados)}",
            f"{format_percent(r.pct_habilitados)} do total · {format_int(r.total_entes)} redes",
        )
    with c2:
        metric_card(
            "Fora do VAAR",
            f"{format_int(r.nao_habilitados)}",
            f"{format_percent(r.pct_nao_habilitados)} — potencial a recuperar",
            delta=f"-{format_int(r.nao_habilitados)}",
            delta_color="red",
        )
    with c3:
        metric_card(
            "VAAR distribuído",
            format_currency(r.total_vaar_reais),
            f"de {format_currency(r.total_uniao_reais)} da União (VAAF+VAAT+VAAR)",
        )
    with c4:
        metric_card(
            "Entraram vs. perderam",
            f"+{format_int(r.transicao_entrou)} / -{format_int(r.transicao_perdeu)}",
            f"{format_int(r.transicao_manteve)} mantiveram o benefício em 2026",
        )

    st.markdown("")

    # Evidência compacta: funil de gargalos + composição da União
    col_a, col_b = st.columns([1.15, 1.0])
    with col_a:
        _section("Onde as redes estão sendo barradas", "Reprovações entre as redes NÃO habilitadas, por condicionalidade (art. 14, § 1º).")
        df_g = pd.DataFrame(
            {
                "cond": [f"{g.codigo} — {g.nome_curto.split('—')[-1].strip()}" for g in gargalos],
                "qtd": [g.reprovacoes_nao_habilitadas for g in gargalos],
            }
        )
        fig = chart_ranking_horizontal(
            df_g, "cond", "qtd",
            "Reprovações por condicionalidade (redes não habilitadas)",
            formato_rotulo="%{x:,.0f}",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_b:
        _section("Para onde vão os recursos da União", "Composição dos R$ da Complementação da União em 2026.")
        fig2 = chart_part_to_whole_100(
            "União 2026",
            "VAAF + VAAT (base/socioeconômico)", r.total_vaaf_reais + r.total_vaat_reais,
            "VAAR (resultado)", r.total_vaar_reais,
            "Peso do VAAR no total da Complementação da União",
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        st.caption(
            f"VAAR é a menor fatia ({format_percent(r.total_vaar_reais / r.total_uniao_reais * 100)}) "
            "mas é a única condicionada a desempenho — e por isso a mais recuperável via gestão."
        )

    _source(
        "Base: 5.596 redes (26 estados + DF + 5.569 municípios) · FNDE (distribuição) e Inep (indicadores) · "
        "Lei nº 14.113/2020, EC 108/2020 · Mesma base auditada da versão completa do painel."
    )


# ------------------------------------------------------------------ 2. Prioridades
def _prioridades(analytics: AnalyticsService) -> None:
    _hero(
        "Prioridades por Unidade da Federação",
        "Onde está o maior volume de redes fora do VAAR — alvo para pactuação em regime de colaboração.",
        "RANKING EXECUTIVO",
    )

    rk = analytics.ranking_por_uf().copy()
    rk["nao_habilitadas"] = rk["total_redes"] - rk["habilitadas"]
    rk["pct_fora"] = (rk["nao_habilitadas"] / rk["total_redes"] * 100).round(1)

    tot_fora = int(rk["nao_habilitadas"].sum())
    top5 = rk.sort_values("nao_habilitadas", ascending=False).head(5)
    top5_fora = int(top5["nao_habilitadas"].sum())
    _bluf(
        f"As <b>5 UFs com mais redes fora</b> concentram <b>{format_int(top5_fora)}</b> das "
        f"{format_int(tot_fora)} redes não habilitadas ({format_percent(top5_fora / tot_fora * 100, 0)} do total). "
        "Priorizar essas secretarias estaduais maximiza o número de redes recuperadas por unidade de esforço."
    )

    col1, col2 = st.columns([1.0, 1.0])
    with col1:
        _section("Maior volume de redes fora do VAAR", "15 UFs com mais redes não habilitadas.")
        df_top = rk.sort_values("nao_habilitadas", ascending=False).head(15)
        fig = chart_ranking_horizontal(
            df_top, "uf", "nao_habilitadas",
            "Redes não habilitadas por UF",
            formato_rotulo="%{x:,.0f}",
            cor_col="regiao", escala_cores=CORES_REGIAO,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col2:
        _section("Maior VAAR já conquistado", "15 UFs que mais captaram VAAR em 2026.")
        df_v = rk.sort_values("vaar_2026", ascending=False).head(15)
        fig2 = chart_ranking_horizontal(
            df_v, "uf", "vaar_2026",
            "VAAR distribuído por UF (R$)",
            formato_rotulo="%{x:,.2s}",
            cor_col="regiao", escala_cores=CORES_REGIAO,
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    _section("Tabela de decisão", "Ordenada por redes fora do VAAR. Use como lista de abordagem.")
    tabela = rk.sort_values("nao_habilitadas", ascending=False)[
        ["uf", "regiao", "total_redes", "habilitadas", "nao_habilitadas", "pct_fora", "vaar_2026"]
    ].rename(
        columns={
            "uf": "UF", "regiao": "Região", "total_redes": "Redes",
            "habilitadas": "Habilitadas", "nao_habilitadas": "Fora do VAAR",
            "pct_fora": "% Fora", "vaar_2026": "VAAR 2026 (R$)",
        }
    )
    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
        column_config={
            "% Fora": st.column_config.ProgressColumn(
                "% Fora", format="%.1f%%", min_value=0, max_value=100
            ),
            "VAAR 2026 (R$)": st.column_config.NumberColumn("VAAR 2026 (R$)", format="R$ %.0f"),
        },
    )

    _source("Mesma base da versão completa · Agregação por UF via AnalyticsService.ranking_por_uf().")


# ------------------------------------------------------------------ 3. Ações
def _plano_acao(analytics: AnalyticsService) -> None:
    _hero(
        "Plano de Ação — o que destrava o VAAR",
        "Cada condicionalidade do art. 14 ordenada pelo número de redes que ela está impedindo.",
        "O QUE FAZER AGORA",
    )

    gargalos = analytics.gargalos_condicionalidade()
    _bluf(
        "As condicionalidades estão <b>ordenadas por impacto</b>: resolver as duas primeiras "
        "libera a maior parte das redes hoje barradas. O número à direita é "
        "<b>quantas redes a medida pode recuperar</b>."
    )

    acao_detalhe = {
        "Cond. I": "Prover gestores escolares por mérito, desempenho ou eleição e registrar no Simec dentro do prazo.",
        "Cond. II": "Garantir no mínimo 80% de participação por etapa no Saeb (mobilização de presença no dia da prova).",
        "Cond. III": "Reduzir o hiato socioeconômico e racial de aprendizagem no Saeb — foco pedagógico nas escolas mais vulneráveis.",
        "Cond. IV": "Aprovar lei estadual com cota de ICMS Educação ≥ 10% e formalizar o regime de colaboração.",
        "Cond. V": "Homologar currículo alinhado à BNCC no CME/CEE.",
    }

    for i, g in enumerate(gargalos, start=1):
        detalhe = acao_detalhe.get(g.codigo, g.como_agir)
        nome = g.nome_curto.split("—")[-1].strip()
        qtd = format_int(g.reprovacoes_nao_habilitadas)  # milhar ABNT (ponto)
        st.markdown(
            f"""
            <div class="exec-action">
                <div class="rank">{i}</div>
                <div class="body">
                    <div class="t">{g.codigo} — {nome}</div>
                    <div class="d">{detalhe}</div>
                </div>
                <div class="impact">
                    <div class="n">{qtd}</div>
                    <div class="l">redes a recuperar</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")
    _section("Sequência recomendada", "Leitura de uma frase.")
    g1, g2 = gargalos[0], gargalos[1]
    st.markdown(
        f"1. **Comece pela {g1.codigo}** — sozinha responde por "
        f"{format_percent(g1.pct_sobre_nao_habilitadas)} das redes fora.\n"
        f"2. **Em seguida a {g2.codigo}** — segundo maior bloqueio.\n"
        f"3. **Condicionalidades IV e V** são de baixo volume e majoritariamente **normativas** "
        "(lei e homologação): resolvem-se com ato administrativo, não com tempo pedagógico."
    )

    _source("Funil calculado sobre as redes não habilitadas · AnalyticsService.gargalos_condicionalidade().")


# ------------------------------------------------------------------ roteador
def render_executivo_view(analytics: AnalyticsService, secao: str) -> None:
    if "Prioridades" in secao:
        _prioridades(analytics)
    elif "Ações" in secao or "Plano" in secao:
        _plano_acao(analytics)
    else:
        _sumario_executivo(analytics)
