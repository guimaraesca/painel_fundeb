"""Visualização Geográfica em 3 Fases: Brasil, Regiões e Municípios com visualização enxuta."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from fundeb.data.repository import DataRepository
from fundeb.domain.territorio import REGIOES, UF_CODIGO, CODIGO_UF
from fundeb.ui.components import (
    metric_card,
    format_currency,
    format_currency_full,
    format_percent,
    format_int,
    status_badge,
)
from fundeb.ui.charts import chart_ranking_horizontal


def render_mapas_view(df: pd.DataFrame, repo: DataRepository) -> None:
    st.subheader("🗺️ Análise Espacial em 3 Fases")
    st.markdown("Explore a distribuição dos recursos do FUNDEB e do VAAR 2026 em escala macro e microterritorial.")

    # Fase Seletora
    fase = st.radio(
        "Selecione a Escala Territorial (3 Fases):",
        options=["Fase 1: Brasil (Nacional)", "Fase 2: Regiões do País", "Fase 3: Municípios por UF"],
        horizontal=True,
    )

    # Métrica acionável (botões)
    col_m, col_f = st.columns([3, 1])
    with col_m:
        metrica_escolhida = st.segmented_control(
            "Métrica no Mapa:",
            options=["% Habilitadas", "% Beneficiárias", "Valor Total VAAR (R$)", "Total Complementação União (R$)"],
            default="% Habilitadas",
        )

    # ------------------------------------------------------------- FASE 1: BRASIL
    if "Fase 1" in fase:
        st.markdown("##### 🇧🇷 Fase 1: Visão Panorâmica Nacional (Estados e DF)")

        # Agrupar dados por UF
        df_uf = (
            df.groupby("uf")
            .agg(
                total=("ibge", "count"),
                habilitadas=("habilitado", "sum"),
                beneficiarias=("beneficiario", "sum"),
                vaar=("vaar", "sum"),
                uniao=("uniao_total", "sum"),
            )
            .reset_index()
        )
        df_uf["pct_hab"] = (df_uf["habilitadas"] / df_uf["total"]) * 100.0
        df_uf["pct_benef"] = (df_uf["beneficiarias"] / df_uf["total"]) * 100.0
        df_uf["codigo_ibge"] = df_uf["uf"].map(UF_CODIGO)

        var_col = (
            "pct_hab" if metrica_escolhida == "% Habilitadas"
            else "pct_benef" if metrica_escolhida == "% Beneficiárias"
            else "vaar" if metrica_escolhida == "Valor Total VAAR (R$)"
            else "uniao"
        )
        cor_escala = "Greens" if "Habilitadas" in metrica_escolhida or "Beneficiárias" in metrica_escolhida else "Blues"

        fig = px.choropleth(
            df_uf,
            geojson=repo.geo_uf(),
            locations="codigo_ibge",
            color=var_col,
            color_continuous_scale=cor_escala,
            hover_name="uf",
            hover_data={
                "codigo_ibge": False,
                "pct_hab": ":.1f%",
                "pct_benef": ":.1f%",
                "vaar": ":,.2f",
                "uniao": ":,.2f",
            },
            labels={
                "pct_hab": "% Habilitadas",
                "pct_benef": "% Beneficiárias",
                "vaar": "Total VAAR (R$)",
                "uniao": "Total União (R$)",
            },
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(
            height=520,
            margin=dict(l=0, r=0, t=10, b=10),
            coloraxis_colorbar=dict(title=metrica_escolhida),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------- FASE 2: REGIÕES
    elif "Fase 2" in fase:
        st.markdown("##### 📍 Fase 2: Comparativo por Regiões do País")
        regiao_sel = st.selectbox("Selecione a Grande Região:", options=["Todas"] + list(REGIOES))

        df_reg = df if regiao_sel == "Todas" else df[df["regiao"] == regiao_sel]

        # Resumo regional
        r_cols = st.columns(4)
        with r_cols[0]:
            metric_card("Total de Redes na Região", format_int(len(df_reg)))
        with r_cols[1]:
            hab_r = int(df_reg["habilitado"].sum())
            metric_card("Habilitadas", f"{format_int(hab_r)} ({format_percent(hab_r / len(df_reg) * 100)})")
        with r_cols[2]:
            ben_r = int(df_reg["beneficiario"].sum())
            metric_card("Beneficiárias", f"{format_int(ben_r)} ({format_percent(ben_r / len(df_reg) * 100)})")
        with r_cols[3]:
            metric_card("VAAR Total da Região", format_currency(df_reg["vaar"].sum()))

        # Gráfico comparativo entre as UFs da região
        df_reg_uf = (
            df_reg.groupby("uf")
            .agg(
                total=("ibge", "count"),
                habilitadas=("habilitado", "sum"),
                vaar=("vaar", "sum"),
            )
            .reset_index()
        )
        df_reg_uf["pct_hab"] = (df_reg_uf["habilitadas"] / df_reg_uf["total"]) * 100.0

        fig_reg = chart_ranking_horizontal(
            df_reg_uf,
            categoria_col="uf",
            valor_col="pct_hab",
            titulo=f"Classificação das UFs na Região {regiao_sel} (% Redes Habilitadas)",
            destacar_primeiro=True,
            formato_rotulo="%{x:.1f}%",
        )
        st.plotly_chart(fig_reg, use_container_width=True)

    # ------------------------------------------------------------- FASE 3: MUNICÍPIOS
    else:
        st.markdown("##### 🏙️ Fase 3: Detalhamento Municipal por UF")

        c_uf_sel, c_busca = st.columns([1, 2])
        with c_uf_sel:
            uf_escolhida = st.selectbox("Selecione o Estado (UF):", options=sorted(list(UF_CODIGO.keys())), index=sorted(list(UF_CODIGO.keys())).index("PI") if "PI" in UF_CODIGO else 0)
        with c_busca:
            busca_mun = st.text_input("Filtrar município por nome ou IBGE:", placeholder="Ex: Teresina, Parnaíba...")

        df_uf_mun = df[(df["uf"] == uf_escolhida) & (df["rede"] == "Municipal")].copy()
        if busca_mun:
            df_uf_mun = df_uf_mun[df_uf_mun["nome"].str.contains(busca_mun, case=False, na=False) | df_uf_mun["ibge"].str.contains(busca_mun)]

        # Mapa dos municípios da UF
        cod_uf = UF_CODIGO[uf_escolhida]
        geo_mun = repo.geo_municipios(cod_uf)

        if geo_mun.get("features"):
            fig_mun = px.choropleth(
                df_uf_mun,
                geojson=geo_mun,
                locations="ibge",
                color="vaar",
                color_continuous_scale="Teal",
                hover_name="nome",
                hover_data={"ibge": True, "habilitado": True, "beneficiario": True, "vaar": ":,.2f"},
                labels={"vaar": "VAAR 2026 (R$)"},
            )
            fig_mun.update_geos(fitbounds="locations", visible=False)
            fig_mun.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=10))
            st.plotly_chart(fig_mun, use_container_width=True)

        st.markdown("---")

        # Seleção e VISUALIZAÇÃO ENXUTA (Economizando espaço sem perder informação)
        st.markdown("##### 🔍 Ficha Técnica Enxuta do Município")
        mun_selecionado = st.selectbox(
            "Selecione um município para exibir a ficha resumida:",
            options=df_uf_mun["ibge"].tolist(),
            format_func=lambda ib: f"{df_uf_mun[df_uf_mun['ibge'] == ib]['nome'].iloc[0]} ({ib})",
        )

        if mun_selecionado:
            m_dados = df_uf_mun[df_uf_mun["ibge"] == mun_selecionado].iloc[0]

            # Container Enxuto
            with st.container(border=True):
                h1, h2 = st.columns([3, 2])
                with h1:
                    st.markdown(
                        f"### {m_dados['nome']} &nbsp; <small style='color:#64748B;'>IBGE: {m_dados['ibge']} &middot; Rede Municipal &middot; {uf_escolhida}</small>",
                        unsafe_allow_html=True,
                    )
                with h2:
                    b_hab = status_badge('Habilitado' if m_dados['habilitado'] else 'Não habilitado')
                    b_ben = status_badge('Beneficiário' if m_dados['beneficiario'] else 'Não beneficiário')
                    b_tr = status_badge(m_dados['transicao'])
                    st.markdown(f"{b_hab} &nbsp; {b_ben} &nbsp; {b_tr}")

                # Grid 4 Colunas Enxuto
                g1, g2, g3, g4 = st.columns(4)
                with g1:
                    st.markdown("**💰 Repasses 2026**")
                    st.markdown(f"- **VAAR 2026:** {format_currency_full(m_dados['vaar'])}")
                    st.markdown(f"- **VAAR 2025:** {format_currency_full(m_dados['vaar_2025'])}")
                    st.markdown(f"- **Total União:** {format_currency_full(m_dados['uniao_total'])}")
                    st.markdown(f"- **VAAF:** {format_currency_full(m_dados['vaaf'])}")
                    st.markdown(f"- **VAAT:** {format_currency_full(m_dados['vaat'])}")

                with g2:
                    st.markdown("**📈 Indicadores VAAR**")
                    st.markdown(f"- **IND Atendimento:** {m_dados['ind_atend']:.4f}" if pd.notna(m_dados['ind_atend']) else "- **IND Atendimento:** —")
                    st.markdown(f"- **Evoluiu Atend:** {'Sim' if m_dados['evoluiu_atend'] else 'Não'}")
                    st.markdown(f"- **IND Aprendizagem:** {m_dados['ind_aprend']:.4f}" if pd.notna(m_dados['ind_aprend']) else "- **IND Aprendizagem:** —")
                    st.markdown(f"- **Evoluiu Aprend:** {'Sim' if m_dados['evoluiu_aprend'] else 'Não'}")
                    st.markdown(f"- **Reprovações:** {m_dados['n_reprovacoes']} de 5")

                with g3:
                    st.markdown("**🎓 Qualidade & Desempenho**")
                    st.markdown(f"- **Ideb (Anos Iniciais):** {m_dados['ideb_ai']:.1f}" if pd.notna(m_dados['ideb_ai']) else "- **Ideb (AI):** —")
                    st.markdown(f"- **Ideb (Anos Finais):** {m_dados['ideb_af']:.1f}" if pd.notna(m_dados['ideb_af']) else "- **Ideb (AF):** —")
                    st.markdown(f"- **Saeb MT (AI):** {m_dados['saeb_ai_mt']:.1f}" if pd.notna(m_dados['saeb_ai_mt']) else "- **Saeb MT:** —")
                    st.markdown(f"- **Saeb LP (AI):** {m_dados['saeb_ai_lp']:.1f}" if pd.notna(m_dados['saeb_ai_lp']) else "- **Saeb LP:** —")
                    st.markdown(f"- **INSE Municipal:** {m_dados['inse']:.2f}" if pd.notna(m_dados['inse']) else "- **INSE:** —")

                with g4:
                    st.markdown("**⚖️ Status das 5 Condicionalidades**")
                    st.markdown(f"- **Cond. I (Diretor):** {'✅ Sim' if m_dados['c1'] else '❌ Não'}")
                    st.markdown(f"- **Cond. II (Saeb >= 80%):** {'✅ Sim' if m_dados['c2'] else '❌ Não'}")
                    st.markdown(f"- **Cond. III (ICMS / Desig.):** {'✅ Sim' if m_dados['c3'] else '❌ Não'}")
                    st.markdown(f"- **Cond. IV (BNCC):** {'✅ Sim' if m_dados['c4'] else '❌ Não'}")
                    st.markdown(f"- **Cond. V (SIOPE):** {'✅ Sim' if m_dados['c5'] else '❌ Não'}")
