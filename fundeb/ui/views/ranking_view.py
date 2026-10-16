"""Ranking de Unidades da Federação com cores, números nas células e gráficos por linha."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from fundeb.services.analytics import AnalyticsService
from fundeb.domain.territorio import REGIOES
from fundeb.ui.charts import chart_ranking_horizontal, chart_deviation
from fundeb.ui.components import format_currency_full, format_percent, format_int


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

    # Visualização Stephen Few: Ranking e Desvio com controle de densidade
    c_tipo, c_tam = st.columns([3, 2])
    with c_tipo:
        modo_grafico = st.segmented_control(
            "Perspectiva Visual:",
            options=["Ranking por Volume (VAAR 2026)", "Análise de Desvio (Variação 2025 ➔ 2026)"],
            default="Ranking por Volume (VAAR 2026)",
        )
    with c_tam:
        qtd_ufs = st.segmented_control(
            "Profundidade do Gráfico:",
            options=["Top 10", "Top 20", "Todas as UFs"],
            default="Todas as UFs",
        )

    limite_n = 10 if qtd_ufs == "Top 10" else (20 if qtd_ufs == "Top 20" else len(df_rank))
    df_grafico = df_rank.head(limite_n)

    if modo_grafico == "Ranking por Volume (VAAR 2026)":
        fig = chart_ranking_horizontal(
            df_grafico,
            categoria_col="uf",
            valor_col="vaar_2026",
            titulo=f"UFs por Volume de Recursos VAAR 2026 ({qtd_ufs} — Base Zero, Cores por Região)",
            destacar_primeiro=False,
            cor_col="regiao",
            formato_rotulo="R$ %{x:,.2s}",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig_dev = chart_deviation(
            df_grafico,
            categoria_col="uf",
            delta_col="delta_vaar",
            titulo=f"Desvio Líquido de Recursos do VAAR (2025 ➔ 2026 — {qtd_ufs})",
            formato_rotulo="R$ %{x:+,.2s}",
        )
        st.plotly_chart(fig_dev, use_container_width=True)

    st.markdown("##### 📋 Tabela Estruturada com Micrográficos por Linha (Alta Densidade de Dados)")

    # Preparar DataFrame para exibição interativa no padrão estrito ABNT
    df_display = df_rank.copy()
    df_display["progresso_hab"] = df_display["pct_habilitadas"] / 100.0
    df_display["progresso_benef"] = df_display["pct_beneficiarias"] / 100.0

    df_display["total_redes_str"] = df_display["total_redes"].map(format_int)
    df_display["habilitadas_str"] = df_display["habilitadas"].map(format_int)
    df_display["beneficiarias_str"] = df_display["beneficiarias"].map(format_int)
    df_display["vaar_2026_str"] = df_display["vaar_2026"].map(format_currency_full)
    df_display["vaar_2025_str"] = df_display["vaar_2025"].map(format_currency_full)
    df_display["delta_vaar_str"] = df_display["delta_vaar"].map(lambda v: f"{'+' if v >= 0 else ''}{format_currency_full(v)}")
    df_display["uniao_total_str"] = df_display["uniao_total"].map(format_currency_full)
    df_display["reprov_c3_str"] = df_display["reprov_c3"].map(format_int)
    df_display["reprov_c1_str"] = df_display["reprov_c1"].map(format_int)

    st.dataframe(
        df_display[[
            "uf",
            "regiao",
            "total_redes_str",
            "habilitadas_str",
            "progresso_hab",
            "beneficiarias_str",
            "progresso_benef",
            "vaar_2026_str",
            "vaar_2025_str",
            "delta_vaar_str",
            "uniao_total_str",
            "reprov_c3_str",
            "reprov_c1_str",
        ]],
        column_config={
            "uf": st.column_config.TextColumn("UF", width="small"),
            "regiao": st.column_config.TextColumn("Região", width="small"),
            "total_redes_str": st.column_config.TextColumn("Total Redes"),
            "habilitadas_str": st.column_config.TextColumn("Habilitadas"),
            "progresso_hab": st.column_config.ProgressColumn(
                "% Habilitadas",
                format="percent",
                min_value=0.0,
                max_value=1.0,
            ),
            "beneficiarias_str": st.column_config.TextColumn("Beneficiárias"),
            "progresso_benef": st.column_config.ProgressColumn(
                "% Beneficiárias",
                format="percent",
                min_value=0.0,
                max_value=1.0,
            ),
            "vaar_2026_str": st.column_config.TextColumn("VAAR 2026 (R$)"),
            "vaar_2025_str": st.column_config.TextColumn("VAAR 2025 (R$)"),
            "delta_vaar_str": st.column_config.TextColumn("Variação (R$)"),
            "uniao_total_str": st.column_config.TextColumn("Total União (R$)"),
            "reprov_c3_str": st.column_config.TextColumn("Reprov. Cond. III"),
            "reprov_c1_str": st.column_config.TextColumn("Reprov. Cond. I"),
        },
        use_container_width=True,
        hide_index=True,
        height=550,
    )

    st.caption(
        "📌 **Notas Metodológicas e Esclarecimentos sobre UFs:**  \n"
        "• **Rio de Janeiro (93 redes auditadas — 0% de habilitação):** Dado oficial auditado das Portarias FNDE. "
        "Nenhuma das 93 redes do estado (1 estadual + 92 municipais) cumpriu a **Condicionalidade IV (Lei Estadual do ICMS Educacional — "
        "Art. 14, § 1º, IV da Lei nº 14.113/2020)**. Como a habilitação exige o cumprimento cumulativo das 5 condicionalidades, a ausência de legislação estadual em conformidade no prazo legal desabilitou em cascata todas as redes fluminenses.  \n"
        "• **Distrito Federal (1 rede):** Conformidade constitucional. O art. 32 da Constituição Federal de 1988 veda expressamente a divisão do DF em municípios, "
        "operando uma rede única e centralizada (esfera distrital/estadual). No ciclo 2026, o DF reprovou nas Condicionalidades II (participação Saeb < 80%) e III."
    )
