"""Visualização Geográfica em 3 Fases: Brasil, Regiões e Municípios com sincronização total de métricas."""
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
    st.subheader("🗺️ Análise Espacial em 3 Fases (Sincronização Multi-Escala)")
    st.markdown(
        "Explore a distribuição territorial dos recursos e da habilitação do FUNDEB e VAAR 2026. "
        "Ao alternar a métrica abaixo, **todos os mapas e indicadores selecionados são atualizados em tempo real**."
    )

    # ------------------------------------------------------------- CONTROLES DE SINCRONIZAÇÃO
    c_metr, c_fases, c_disp = st.columns([4, 4, 3])
    with c_metr:
        metrica_escolhida = st.segmented_control(
            "🔘 Métrica Sincronizada:",
            options=["% Habilitadas", "% Beneficiárias", "Valor Total VAAR (R$)", "Total Complementação União (R$)"],
            default="% Habilitadas",
        )
    with c_fases:
        fases_opcoes = ["Fase 1: Brasil (Nacional)", "Fase 2: Regiões do País", "Fase 3: Municípios por UF"]
        fases_ativas = st.pills(
            "🗺️ Escalas Ativas:",
            options=fases_opcoes,
            default=fases_opcoes,
            selection_mode="multi",
        )
        if not fases_ativas:
            fases_ativas = fases_opcoes
    with c_disp:
        modo_disp = st.segmented_control(
            "📐 Disposição:",
            options=["Lado a Lado (3 Colunas)", "Em Linha (Expandido)"],
            default="Lado a Lado (3 Colunas)" if len(fases_ativas) > 1 else "Em Linha (Expandido)",
        )

    st.markdown("---")

    # Mapeamento e Configuração da Métrica Escolhida
    is_hab = metrica_escolhida == "% Habilitadas"
    is_ben = metrica_escolhida == "% Beneficiárias"
    is_vaar = metrica_escolhida == "Valor Total VAAR (R$)"
    is_uniao = metrica_escolhida == "Total Complementação União (R$)"
    is_taxa = is_hab or is_ben

    cor_escala = "Greens" if is_taxa else "Blues"
    var_col_uf = "pct_hab" if is_hab else "pct_benef" if is_ben else "vaar" if is_vaar else "uniao"
    rotulo_metrica = (
        "% Redes Habilitadas" if is_hab
        else "% Redes Beneficiárias" if is_ben
        else "VAAR 2026 (R$)" if is_vaar
        else "Complementação União (R$)"
    )

    # Agregação Nacional e Estadual Base
    df_uf = (
        df.groupby("uf")
        .agg(
            total=("ibge", "count"),
            habilitadas=("habilitado", "sum"),
            beneficiarias=("beneficiario", "sum"),
            vaar=("vaar", "sum"),
            uniao=("uniao_total", "sum"),
            regiao=("regiao", "first"),
        )
        .reset_index()
    )
    df_uf["pct_hab"] = (df_uf["habilitadas"] / df_uf["total"]) * 100.0
    df_uf["pct_benef"] = (df_uf["beneficiarias"] / df_uf["total"]) * 100.0
    df_uf["codigo_ibge"] = df_uf["uf"].map(UF_CODIGO)

    # Função geradora do Mapa da Fase 1 (Brasil)
    def desenhar_fase_1(container, altura: int = 420) -> None:
        with container:
            st.markdown("##### 🇧🇷 Fase 1: Brasil (Nacional)")
            # KPI Nacional
            val_nac = (
                f"{format_percent(df['habilitado'].mean() * 100)} ({format_int(df['habilitado'].sum())} redes)"
                if is_hab
                else f"{format_percent(df['beneficiario'].mean() * 100)} ({format_int(df['beneficiario'].sum())} redes)"
                if is_ben
                else format_currency(df["vaar"].sum())
                if is_vaar
                else format_currency(df["uniao_total"].sum())
            )
            st.caption(f"**Total Brasil ({rotulo_metrica}):** {val_nac}")

            fig = px.choropleth(
                df_uf,
                geojson=repo.geo_uf(),
                locations="codigo_ibge",
                color=var_col_uf,
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
                height=altura,
                margin=dict(l=0, r=0, t=10, b=10),
                coloraxis_colorbar=dict(title=dict(text=rotulo_metrica, font=dict(size=10)), thickness=10),
            )
            st.plotly_chart(fig, use_container_width=True)

    # Função geradora do Mapa da Fase 2 (Regiões)
    def desenhar_fase_2(container, altura: int = 420) -> None:
        with container:
            st.markdown("##### 📍 Fase 2: Regiões do País")
            regiao_sel = st.selectbox(
                "Região Focal:",
                options=list(REGIOES),
                index=list(REGIOES).index("Nordeste") if "Nordeste" in REGIOES else 0,
                key="mapa_regiao_sel",
            )
            df_reg = df[df["regiao"] == regiao_sel]
            df_reg_uf = df_uf[df_uf["regiao"] == regiao_sel].copy()

            val_reg = (
                f"{format_percent(df_reg['habilitado'].mean() * 100)} ({format_int(df_reg['habilitado'].sum())} redes)"
                if is_hab
                else f"{format_percent(df_reg['beneficiario'].mean() * 100)} ({format_int(df_reg['beneficiario'].sum())} redes)"
                if is_ben
                else format_currency(df_reg["vaar"].sum())
                if is_vaar
                else format_currency(df_reg["uniao_total"].sum())
            )
            st.caption(f"**Total {regiao_sel} ({rotulo_metrica}):** {val_reg}")

            fig_reg = px.choropleth(
                df_reg_uf,
                geojson=repo.geo_uf(),
                locations="codigo_ibge",
                color=var_col_uf,
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
            fig_reg.update_geos(fitbounds="locations", visible=False)
            fig_reg.update_layout(
                height=altura,
                margin=dict(l=0, r=0, t=10, b=10),
                coloraxis_colorbar=dict(title=dict(text=rotulo_metrica, font=dict(size=10)), thickness=10),
            )
            st.plotly_chart(fig_reg, use_container_width=True)

            if modo_disp == "Em Linha (Expandido)":
                fig_rank = chart_ranking_horizontal(
                    df_reg_uf,
                    categoria_col="uf",
                    valor_col=var_col_uf,
                    titulo=f"Classificação das UFs na Região {regiao_sel} ({rotulo_metrica})",
                    destacar_primeiro=True,
                    formato_rotulo="%{x:.1f}%" if is_taxa else "R$ %{x:,.2s}",
                )
                st.plotly_chart(fig_rank, use_container_width=True)

    # Função geradora do Mapa da Fase 3 (Municípios)
    def desenhar_fase_3(container, altura: int = 420) -> None:
        with container:
            st.markdown("##### 🏙️ Fase 3: Municípios por UF")
            ufs_ordenadas = sorted(list(UF_CODIGO.keys()))
            uf_sel = st.selectbox(
                "Estado (UF):",
                options=ufs_ordenadas,
                index=ufs_ordenadas.index("PI") if "PI" in ufs_ordenadas else 0,
                key="mapa_uf_sel",
            )
            df_mun = df[(df["uf"] == uf_sel) & (df["rede"] == "Municipal")].copy()

            # Variável sincronizada no nível municipal
            if is_hab:
                df_mun["metrica_val"] = df_mun["habilitado"].astype(float) * 100.0
            elif is_ben:
                df_mun["metrica_val"] = df_mun["beneficiario"].astype(float) * 100.0
            elif is_vaar:
                df_mun["metrica_val"] = df_mun["vaar"]
            else:
                df_mun["metrica_val"] = df_mun["uniao_total"]

            val_uf_total = (
                f"{format_percent(df_mun['habilitado'].mean() * 100)} ({format_int(df_mun['habilitado'].sum())} de {len(df_mun)} mun.)"
                if is_hab
                else f"{format_percent(df_mun['beneficiario'].mean() * 100)} ({format_int(df_mun['beneficiario'].sum())} de {len(df_mun)} mun.)"
                if is_ben
                else format_currency(df_mun["vaar"].sum())
                if is_vaar
                else format_currency(df_mun["uniao_total"].sum())
            )
            st.caption(f"**Total {uf_sel} ({rotulo_metrica}):** {val_uf_total}")

            geo_mun = repo.geo_municipios(UF_CODIGO[uf_sel])
            if geo_mun.get("features"):
                fig_mun = px.choropleth(
                    df_mun,
                    geojson=geo_mun,
                    locations="ibge",
                    color="metrica_val",
                    color_continuous_scale=cor_escala,
                    hover_name="nome",
                    hover_data={
                        "ibge": True,
                        "habilitado": True,
                        "beneficiario": True,
                        "vaar": ":,.2f",
                        "uniao_total": ":,.2f",
                    },
                    labels={
                        "metrica_val": rotulo_metrica,
                        "vaar": "VAAR 2026 (R$)",
                        "uniao_total": "Total União (R$)",
                    },
                )
                fig_mun.update_geos(fitbounds="locations", visible=False)
                fig_mun.update_layout(
                    height=altura,
                    margin=dict(l=0, r=0, t=10, b=10),
                    coloraxis_colorbar=dict(title=dict(text=rotulo_metrica, font=dict(size=10)), thickness=10),
                )
                st.plotly_chart(fig_mun, use_container_width=True)

    # ------------------------------------------------------------- RENDERIZAÇÃO CONFORME DISPOSIÇÃO
    tem_f1 = any("Fase 1" in f for f in fases_ativas)
    tem_f2 = any("Fase 2" in f for f in fases_ativas)
    tem_f3 = any("Fase 3" in f for f in fases_ativas)

    if modo_disp == "Lado a Lado (3 Colunas)" and len(fases_ativas) > 1:
        cols = st.columns(len(fases_ativas))
        c_idx = 0
        if tem_f1:
            desenhar_fase_1(cols[c_idx], altura=430)
            c_idx += 1
        if tem_f2:
            desenhar_fase_2(cols[c_idx], altura=430)
            c_idx += 1
        if tem_f3:
            desenhar_fase_3(cols[c_idx], altura=430)
            c_idx += 1
    else:
        # Modo em Linha (Expandido verticalmente)
        if tem_f1:
            with st.container(border=True):
                desenhar_fase_1(st, altura=520)
        if tem_f2:
            with st.container(border=True):
                desenhar_fase_2(st, altura=480)
        if tem_f3:
            with st.container(border=True):
                desenhar_fase_3(st, altura=480)

    # ------------------------------------------------------------- FICHA TÉCNICA DO MUNICÍPIO (Se Fase 3 estiver ativa)
    if tem_f3:
        st.markdown("---")
        st.markdown("##### 🔍 Ficha Técnica Detalhada do Município")
        uf_ativa = st.session_state.get("mapa_uf_sel", "PI")
        df_mun_lista = df[(df["uf"] == uf_ativa) & (df["rede"] == "Municipal")].sort_values(by="nome")

        c_busca1, c_busca2 = st.columns([3, 1])
        with c_busca1:
            mun_selecionado = st.selectbox(
                f"Selecione um município de {uf_ativa} para auditar dados:",
                options=df_mun_lista["ibge"].tolist(),
                format_func=lambda ib: f"{df_mun_lista[df_mun_lista['ibge'] == ib]['nome'].iloc[0]} ({ib})",
                key="ficha_mun_sel",
            )

        if mun_selecionado:
            m_dados = df_mun_lista[df_mun_lista["ibge"] == mun_selecionado].iloc[0]
            with c_busca2:
                val_metr_kpi = (
                    "Habilitado" if m_dados["habilitado"] else "Não habilitado"
                    if is_hab
                    else "Beneficiário" if m_dados["beneficiario"] else "Não beneficiário"
                    if is_ben
                    else format_currency_full(m_dados["vaar"])
                    if is_vaar
                    else format_currency_full(m_dados["uniao_total"])
                )
                st.metric(
                    label=f"Métrica Atual ({rotulo_metrica}):",
                    value=val_metr_kpi,
                )

            with st.container(border=True):
                h1, h2 = st.columns([3, 2])
                with h1:
                    st.markdown(
                        f"### {m_dados['nome']} &nbsp; <small style='color:#64748B;'>IBGE: {m_dados['ibge']} &middot; Rede Municipal &middot; {uf_ativa}</small>",
                        unsafe_allow_html=True,
                    )
                with h2:
                    b_hab = status_badge('Habilitado' if m_dados['habilitado'] else 'Não habilitado')
                    b_ben = status_badge('Beneficiário' if m_dados['beneficiario'] else 'Não beneficiário')
                    b_tr = status_badge(m_dados['transicao'])
                    st.markdown(f"{b_hab} &nbsp; {b_ben} &nbsp; {b_tr}")

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
                    st.markdown(f"- **Cond. III (Equidade):** {'✅ Sim' if m_dados['c3'] else '❌ Não'}")
                    st.markdown(f"- **Cond. IV (ICMS Educação):** {'✅ Sim' if m_dados['c4'] else '❌ Não'}")
                    st.markdown(f"- **Cond. V (BNCC):** {'✅ Sim' if m_dados['c5'] else '❌ Não'}")
