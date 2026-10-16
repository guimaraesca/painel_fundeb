"""Visão Detalhada das Condicionalidades e Análise de Perda de Habilitação."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from fundeb.services.analytics import AnalyticsService
from fundeb.ui.components import metric_card, format_int, format_percent
from fundeb.ui.charts import chart_ranking_horizontal


def render_condicionalidades_view(analytics: AnalyticsService) -> None:
    st.subheader("⚖️ Perda de Habilitação ao VAAR 2026 — Por Condicionalidade")
    st.markdown(
        """
        Para receber a Complementação VAAR, a rede de ensino precisa ser previamente **habilitada**,
        cumprindo **cumulativamente todas as 5 condicionalidades** do Art. 14, § 1º da Lei nº 14.113/2020.
        A reprovação em **qualquer uma** delas desabilita a rede do rateio de recursos.
        """
    )

    gargalos_ranking = analytics.gargalos_condicionalidade()
    gargalos_ordem = analytics.condicionalidades_ordem_legal()
    total_nao_hab = len(analytics.df[~analytics.df["habilitado"]])

    st.markdown(
        f"**Universo analisado:** Total de **{format_int(total_nao_hab)} redes não habilitadas** que reprovaram em cada condicionalidade *(uma rede pode reprovar em mais de uma condicionalidade)*."
    )

    # 5 Colunas na ordem legal das condicionalidades (I a V)
    resumos_delta = {
        "Cond. I": "Gestor Escolar",
        "Cond. II": "Saeb >= 80%",
        "Cond. III": "Desigualdades",
        "Cond. IV": "ICMS Educação",
        "Cond. V": "BNCC & Currículo",
    }
    cols = st.columns(len(gargalos_ordem))
    for col, g in zip(cols, gargalos_ordem):
        with col:
            metric_card(
                title=g.codigo,
                value=f"{format_int(g.reprovacoes_nao_habilitadas)} redes",
                subtitle=f"{format_percent(g.pct_sobre_nao_habilitadas)} das não hab.",
                delta=resumos_delta.get(g.codigo, g.codigo),
                delta_color="red",
            )

    st.markdown("---")

    # Gráfico de barras horizontal do ranking de reprovações
    col_chart, col_tabela = st.columns([3, 2])

    with col_chart:
        st.markdown("##### 📊 Ranking de Reprovações por Impacto (Redes Não Habilitadas)")
        df_chart = pd.DataFrame([
            {
                "Condicionalidade": f"{g.codigo}: {resumos_delta.get(g.codigo, g.nome_curto)}",
                "Reprovações": g.reprovacoes_nao_habilitadas,
            }
            for g in gargalos_ranking
        ])

        fig = chart_ranking_horizontal(
            df_chart,
            categoria_col="Condicionalidade",
            valor_col="Reprovações",
            titulo="Ranking de Reprovações por Condicionalidade (Redes Desabilitadas)",
            destacar_primeiro=True,
            cor_destaque="#DC2626",
            formato_rotulo="%{x:,.0f} redes",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_tabela:
        st.markdown("##### 📋 Síntese Numérica por Condicionalidade")
        df_tabela = pd.DataFrame([
            {
                "Condicionalidade": g.codigo,
                "Inciso Legal": g.artigo,
                "Redes Desabilitadas": format_int(g.reprovacoes_nao_habilitadas),
                "% s/ Não Hab.": format_percent(g.pct_sobre_nao_habilitadas),
                "Total Geral Reprov.": format_int(g.total_reprovacoes),
            }
            for g in gargalos_ordem
        ])
        st.dataframe(df_tabela, use_container_width=True, hide_index=True)

    st.caption(
        "ℹ️ **Impacto Federativo em Destaque:** Na Condicionalidade IV (ICMS Educacional), a ausência de legislação estadual regulamentada "
        "no Rio de Janeiro inabilitou 100% das 93 redes do estado (Estado + 92 municípios). O Distrito Federal cumpriu as Cond. I, IV e V, "
        "mas restou desabilitado por reprovação nas Cond. II (Saeb < 80%) e III (Desigualdades)."
    )

    st.markdown("---")

    # Expansão detalhada de cada Condicionalidade LISTADA ESTRITAMENTE NA ORDEM LEGAL (I a V)
    st.subheader("📖 Detalhamento Normativo e Guia de Ação por Condicionalidade")
    st.caption("As condicionalidades estão dispostas na ordem legal dos incisos I a V do § 1º do art. 14 da Lei nº 14.113/2020:")

    for g in gargalos_ordem:
        with st.expander(f"🔹 {g.codigo} — {g.nome_curto} ({format_int(g.reprovacoes_nao_habilitadas)} redes reprovadas)", expanded=False):
            c_info1, c_info2 = st.columns([3, 2])
            with c_info1:
                st.markdown("**Texto Oficial da Lei nº 14.113/2020 (Art. 14, § 1º):**")
                st.markdown(f"> *\"{g.descricao_tecnica}\"*")
            with c_info2:
                st.markdown("**Como Agir para Não Perder Habilitação (Síntese Executiva):**")
                st.info(g.como_agir)
                st.caption("📖 Consulte o detalhamento completo dos requisitos, anexos e prazos na **Nota Técnica Nº 01/2026** (Página Inicial).")
