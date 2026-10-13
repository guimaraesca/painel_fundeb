"""Ranking de Unidades da Federação com cores, números nas células e gráficos por linha."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from fundeb.services.analytics import AnalyticsService
from fundeb.domain.territorio import REGIOES
from fundeb.ui.charts import chart_ranking_horizontal, chart_deviation


def render_ranking_view(analytics: AnalyticsService) -> None:
    st.subheader("🏆 Ranking por Unidade da Federação (UF)")
    st.markdown(
        """
        Comparativo estadual de desempenho no VAAR 2026. A tabela inclui **mapa de calor por cores nas células**,
        números brutos auditados e **micrográfico em barra resumido por linha**.
        """
    )

    df_rank = analytics.ranking_por_uf()

    # Controles e filtros
    f1, f2 = st.columns([2, 2])
    with f1:
        reg_sel = st.selectbox("Filtrar por Região:", options=["Todas"] + list(REGIOES))
    with f2:
        apenas_perda = st.checkbox("Exibir apenas UFs com redução de repasse (2025 ➔ 2026)", value=False)

    if reg_sel != "Todas":
        df_rank = df_rank[df_rank["regiao"] == reg_sel]

    if apenas_perda:
        df_rank = df_rank[df_rank["delta_vaar"] < 0]

    # Visualização Stephen Few: Ranking e Desvio
    c_tipo, _ = st.columns([2, 2])
    with c_tipo:
        modo_grafico = st.segmented_control(
            "Perspectiva Visual:",
            options=["Ranking por Volume (VAAR 2026)", "Análise de Desvio (Variação 2025 ➔ 2026)"],
            default="Ranking por Volume (VAAR 2026)",
        )

    if modo_grafico == "Ranking por Volume (VAAR 2026)":
        fig = chart_ranking_horizontal(
            df_rank.head(12),
            categoria_col="uf",
            valor_col="vaar_2026",
            titulo="Top UFs por Volume de Recursos VAAR 2026 (Base Zero)",
            destacar_primeiro=True,
            formato_rotulo="R$ %{x:,.2s}",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig_dev = chart_deviation(
            df_rank.head(15),
            categoria_col="uf",
            delta_col="delta_vaar",
            titulo="Desvio Líquido de Recursos do VAAR (2025 ➔ 2026) com Referência Zero",
            formato_rotulo="R$ %{x:+,.2s}",
        )
        st.plotly_chart(fig_dev, use_container_width=True)

    st.markdown("##### 📋 Tabela Estruturada com Micrográficos por Linha (Alta Densidade de Dados)")

    # Preparar DataFrame para exibição interativa
    df_display = df_rank.copy()
    df_display["progresso_hab"] = df_display["pct_habilitadas"] / 100.0
    df_display["progresso_benef"] = df_display["pct_beneficiarias"] / 100.0

    st.dataframe(
        df_display[[
            "uf",
            "regiao",
            "total_redes",
            "habilitadas",
            "progresso_hab",
            "beneficiarias",
            "progresso_benef",
            "vaar_2026",
            "vaar_2025",
            "delta_vaar",
            "uniao_total",
            "reprov_c3",
            "reprov_c1",
        ]],
        column_config={
            "uf": st.column_config.TextColumn("UF", width="small"),
            "regiao": st.column_config.TextColumn("Região", width="small"),
            "total_redes": st.column_config.NumberColumn("Total Redes", format="%d"),
            "habilitadas": st.column_config.NumberColumn("Habilitadas", format="%d"),
            "progresso_hab": st.column_config.ProgressColumn(
                "% Habilitadas",
                format="%.1f%%",
                min_value=0.0,
                max_value=1.0,
            ),
            "beneficiarias": st.column_config.NumberColumn("Beneficiárias", format="%d"),
            "progresso_benef": st.column_config.ProgressColumn(
                "% Beneficiárias",
                format="%.1f%%",
                min_value=0.0,
                max_value=1.0,
            ),
            "vaar_2026": st.column_config.NumberColumn("VAAR 2026 (R$)", format="R$ %,.2f"),
            "vaar_2025": st.column_config.NumberColumn("VAAR 2025 (R$)", format="R$ %,.2f"),
            "delta_vaar": st.column_config.NumberColumn("Variação (R$)", format="R$ %,.2f"),
            "uniao_total": st.column_config.NumberColumn("Total União (R$)", format="R$ %,.2f"),
            "reprov_c3": st.column_config.NumberColumn("Reprov. Cond. III", format="%d"),
            "reprov_c1": st.column_config.NumberColumn("Reprov. Cond. I", format="%d"),
        },
        use_container_width=True,
        hide_index=True,
        height=550,
    )
