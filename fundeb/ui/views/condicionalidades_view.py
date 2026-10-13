"""Visão Detalhada das Condicionalidades e Análise de Perda de Habilitação."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from fundeb.services.analytics import AnalyticsService
from fundeb.ui.components import metric_card, format_int, format_percent


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
    cols = st.columns(len(gargalos_ordem))
    for col, g in zip(cols, gargalos_ordem):
        with col:
            metric_card(
                title=g.codigo,
                value=f"{format_int(g.reprovacoes_nao_habilitadas)} redes",
                subtitle=f"{format_percent(g.pct_sobre_nao_habilitadas)} das não habilitadas",
                delta=f"{g.nome_curto.split('—')[1].strip() if '—' in g.nome_curto else g.nome_curto}",
                delta_color="red",
            )

    st.markdown("---")

    # Gráfico de barras horizontal do funil de perdas
    col_chart, col_tabela = st.columns([3, 2])

    with col_chart:
        st.markdown("##### 📊 Funil de Reprovações nas Redes Desabilitadas (Ranking por Impacto)")
        df_chart = pd.DataFrame([
            {
                "Condicionalidade": f"{g.codigo}: {g.nome_curto.split('—')[1].strip() if '—' in g.nome_curto else g.nome_curto}",
                "Reprovações": g.reprovacoes_nao_habilitadas,
                "Percentual (%)": round(g.pct_sobre_nao_habilitadas, 1),
            }
            for g in gargalos_ranking
        ])

        fig = px.bar(
            df_chart,
            x="Reprovações",
            y="Condicionalidade",
            orientation="h",
            text="Reprovações",
            color="Reprovações",
            color_continuous_scale=["#FCA5A5", "#DC2626"],
        )
        fig.update_layout(
            height=320,
            margin=dict(l=10, r=20, t=10, b=10),
            yaxis=dict(autorange="reversed"),
            coloraxis_showscale=False,
            font=dict(size=12),
        )
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col_tabela:
        st.markdown("##### 📋 Síntese Numérica por Condicionalidade")
        df_tabela = pd.DataFrame([
            {
                "Condicionalidade": g.codigo,
                "Inciso Legal": g.artigo,
                "Redes Desabilitadas": f"{g.reprovacoes_nao_habilitadas:,}".replace(",", "."),
                "% s/ Não Hab.": f"{g.pct_sobre_nao_habilitadas:.1f}%",
                "Total Geral Reprov.": f"{g.total_reprovacoes:,}".replace(",", "."),
            }
            for g in gargalos_ordem
        ])
        st.dataframe(df_tabela, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Expansão detalhada de cada Condicionalidade LISTADA ESTRITAMENTE NA ORDEM LEGAL (I a V)
    st.subheader("📖 Detalhamento Normativo e Guia de Ação por Condicionalidade")
    st.caption("As condicionalidades estão dispostas na ordem legal dos incisos I a V do § 1º do art. 14 da Lei nº 14.113/2020:")

    for g in gargalos_ordem:
        with st.expander(f"🔹 {g.codigo} — {g.nome_curto} ({format_int(g.reprovacoes_nao_habilitadas)} redes reprovadas)", expanded=(g.codigo == "Cond. I")):
            c_info1, c_info2 = st.columns([3, 2])
            with c_info1:
                st.markdown("**Texto Oficial da Lei nº 14.113/2020 (Art. 14, § 1º):**")
                st.markdown(f"> *\"{g.descricao_tecnica}\"*")
            with c_info2:
                st.markdown("**Como Agir para Não Perder Habilitação:**")
                st.info(g.como_agir)
