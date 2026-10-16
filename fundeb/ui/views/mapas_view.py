"""Visualização Geográfica em 3 Fases: Brasil, Regiões e Municípios com sincronização multi-escala."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from fundeb.data.repository import DataRepository
from fundeb.data.validation import verificar
from fundeb.domain.territorio import REGIOES, REGIAO_POR_UF, UF_CODIGO
from fundeb.ui.components import (
    metric_card,
    format_currency,
    format_currency_full,
    format_percent,
    format_int,
    format_decimal,
    status_badge,
)
from fundeb.ui.charts import chart_ranking_horizontal

# Fundo cartográfico limpo, neutro e elegante (elimina distorções de saturação)
BG_MAPA = "#FFFFFF"

# =============================================================================
# PALETAS CARTOGRÁFICAS DE ALTA FIDELIDADE (Stephen Few & Cynthia Brewer / ColorBrewer)
# =============================================================================

# 1. Paleta Oceano & Cobalto (Recomendada / Executiva)
ESCALA_TAXA_OCEANO = [
    [0.00, "#E2E8F0"],  # Cinza neutro suave para zero / inabilitado
    [0.01, "#CCFBF1"],  # Menta claro para taxas iniciais
    [0.25, "#5EEAD4"],  # Turquesa suave
    [0.50, "#0D9488"],  # Azul petróleo intermediário
    [0.75, "#1D4ED8"],  # Azul cobalto vivo
    [1.00, "#0F172A"],  # Azul marinho profundo executivo
]

ESCALA_RECURSOS_OCEANO = [
    [0.00, "#E2E8F0"],  # Cinza neutro para zero repasse
    [0.01, "#E0F2FE"],  # Azul gelo claro
    [0.25, "#38BDF8"],  # Azul celeste
    [0.50, "#2563EB"],  # Azul royal sólido
    [0.75, "#1E40AF"],  # Azul índigo forte
    [1.00, "#020617"],  # Meia-noite profundo
]

# 2. Paleta ColorBrewer YlGnBu (Padrão Oficial IBGE / Ipea / World Bank)
ESCALA_TAXA_YLGNBU = [
    [0.00, "#E2E8F0"],
    [0.01, "#FFFFCC"],  # Amarelo claro suave
    [0.25, "#A1DAB4"],  # Verde menta
    [0.50, "#41B6C4"],  # Azul turquesa
    [0.75, "#225EA8"],  # Azul clássico
    [1.00, "#081D58"],  # Azul ultramarino
]

ESCALA_RECURSOS_YLGNBU = [
    [0.00, "#E2E8F0"],
    [0.01, "#FEE391"],  # Ouro claro
    [0.25, "#FE9929"],  # Âmbar aquecido
    [0.50, "#D95F0E"],  # Laranja terra
    [0.75, "#993404"],  # Cobre profundo
    [1.00, "#450A0A"],  # Vinho escuro
]

# 3. Paleta Esmeralda Governamental (Verde Institucional)
ESCALA_TAXA_ESMERALDA = [
    [0.00, "#E2E8F0"],
    [0.01, "#DCFCE7"],  # Verde muito suave
    [0.25, "#86EFAC"],  # Verde claro
    [0.50, "#22C55E"],  # Verde esmeralda
    [0.75, "#15803D"],  # Verde bandeira
    [1.00, "#052E16"],  # Verde floresta profundo
]


def render_mapas_view(df: pd.DataFrame, repo: DataRepository) -> None:
    st.subheader("🗺️ Análise Espacial em 3 Fases (Sincronização Multi-Escala)")
    st.markdown(
        "Distribuição territorial cartográfica da habilitação e dos recursos do FUNDEB e Complementação VAAR 2026. "
        "Os mapas utilizam a **projeção cartográfica conformal de Mercator**, preservando o alinhamento reto e as "
        "formas geográficas autênticas do Brasil sem achatamentos."
    )

    # -------------------------------------------------------------------------
    # PAINEL RETRÁTIL DE CHECAGEM DE DADOS AUDITADOS
    # -------------------------------------------------------------------------
    with st.expander("🛡️ Checagem de Dados Auditados da Base (Auditoria Oficial em Tempo Real)", expanded=False):
        st.markdown(
            "Verificação contábil e de integridade da base oficial de dados do FNDE e Inep utilizada no painel:"
        )
        c_ch1, c_ch2, c_ch3, c_ch4 = st.columns(4)
        with c_ch1:
            st.metric("Total de Entes Auditados", f"{len(df):,} redes".replace(",", "."), "27 Estaduais + 5.569 Municipais")
        with c_ch2:
            st.metric("Habilitados no VAAR", f"{int(df['habilitado'].sum()):,} redes".replace(",", "."), f"{df['habilitado'].mean() * 100:.1f}% de habilitação")
        with c_ch3:
            st.metric("Beneficiários do VAAR", f"{int(df['beneficiario'].sum()):,} redes".replace(",", "."), f"{df['beneficiario'].mean() * 100:.1f}% contempladas")
        with c_ch4:
            st.metric("Volume Total VAAR 2026", format_currency(df["vaar"].sum()), f"+49,2% vs 2025 ({format_currency(df['vaar_2025'].sum())})")

        c_btn, c_res = st.columns([1.5, 3.5])
        with c_btn:
            rodar_auditoria = st.button("🔍 Executar Auditoria Contábil das 18 Regras", use_container_width=True)
        with c_res:
            st.caption("Verifica o fechamento contábil linha a linha (VAAF + VAAT + VAAR = Total União) e a repartição 50%/50%.")

        if rodar_auditoria:
            resultados = verificar(df)
            st.markdown("##### 📋 Resultado da Auditoria Contábil Linha a Linha:")
            linhas_v = []
            for r in resultados:
                status_icon = "✅ OK" if r.status == "ok" else "⚠️ ALERTA"
                linhas_v.append({"Regra de Auditoria": r.nome, "Status": status_icon, "Detalhamento / Evidência": r.detalhe})
            st.dataframe(pd.DataFrame(linhas_v), use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # CONTROLES DE SINCRONIZAÇÃO E CARTOGRAFIA
    # -------------------------------------------------------------------------
    c_metr, c_fases, c_disp = st.columns([3.8, 3.4, 3.8])
    with c_metr:
        metrica_escolhida = st.segmented_control(
            "🔘 Métrica Sincronizada:",
            options=["% Habilitadas", "% Beneficiárias", "VAAR (R$)", "Total União (R$)"],
            default="% Habilitadas",
            help="Métrica cartográfica sincronizada e aplicada simultaneamente em todas as escalas.",
        )
    with c_fases:
        fases_opcoes = ["Fase 1 (Brasil)", "Fase 2 (Regiões)", "Fase 3 (Municípios)"]
        fases_ativas = st.pills(
            "🗺️ Escalas Ativas:",
            options=fases_opcoes,
            default=fases_opcoes,
            selection_mode="multi",
            help="Ative ou desative as escalas de visualização cartográfica.",
        )
        if not fases_ativas:
            fases_ativas = fases_opcoes
    with c_disp:
        modo_disp = st.segmented_control(
            "📐 Disposição Visual:",
            options=["Lado a Lado", "Em Abas", "Sequencial"],
            default="Lado a Lado",
            help="Organização dos mapas: Lado a Lado (Fases 1 e 2 juntas, 3 abaixo), Em Abas (tela cheia por escala) ou Sequencial.",
        )

    # Controles Cartográficos Secundários (Cores e Resolução)
    c_pal, c_alt, c_info = st.columns([3.5, 3.5, 4])
    with c_pal:
        paleta_escolhida = st.selectbox(
            "🎨 Esquema de Cores do Degradê:",
            options=[
                "Oceano & Cobalto (Recomendada / Alto Contraste)",
                "ColorBrewer YlGnBu (Padrão Oficial IBGE / Ipea)",
                "Viridis Perceptual (Científico / Acessível)",
                "Esmeralda Governamental (Verde Institucional)",
            ],
            index=0,
            help="Escalas cartográficas calibradas para legibilidade e alta diferenciação visual entre patamares.",
        )
    with c_alt:
        altura_mapa = st.select_slider(
            "📏 Resolução / Altura dos Mapas:",
            options=[380, 460, 540, 620],
            value=460,
            format_func=lambda h: {380: "Compacto (380px)", 460: "Padrão (460px)", 540: "Confortável (540px)", 620: "Expandido (620px)"}[h],
            help="Ajuste a altura conforme a resolução do seu monitor ou tela do notebook.",
        )
    with c_info:
        st.caption(
            "📐 **Geometria Conformal de Mercator:** "
            "Elimina a distorção e o achatamento cartográfico do Brasil, "
            "mantendo as linhas estaduais e municipais com proporção e orientação corretas."
        )

    st.markdown("---")

    # Mapeamento e Configuração da Métrica Escolhida
    is_hab = metrica_escolhida == "% Habilitadas"
    is_ben = metrica_escolhida == "% Beneficiárias"
    is_vaar = metrica_escolhida in ("VAAR (R$)", "Valor Total VAAR (R$)")
    is_uniao = metrica_escolhida in ("Total União (R$)", "Total Complementação União (R$)")
    is_taxa = is_hab or is_ben

    # Seleção da Escala de Cor calibrada
    if "Oceano" in paleta_escolhida:
        cor_escala = ESCALA_TAXA_OCEANO if is_taxa else ESCALA_RECURSOS_OCEANO
    elif "YlGnBu" in paleta_escolhida:
        cor_escala = ESCALA_TAXA_YLGNBU if is_taxa else ESCALA_RECURSOS_YLGNBU
    elif "Viridis" in paleta_escolhida:
        cor_escala = px.colors.sequential.Viridis
    else:
        cor_escala = ESCALA_TAXA_ESMERALDA if is_taxa else ESCALA_RECURSOS_OCEANO

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

    # -------------------------------------------------------------------------
    # FUNÇÕES DE DESENHO DE MAPA (COM PROJEÇÃO MERCATOR CONFORME)
    # -------------------------------------------------------------------------
    def desenhar_fase_1(parent, altura: int = 460) -> None:
        parent.markdown("##### 🇧🇷 Fase 1: Brasil (Visão Nacional Completa)")
        val_nac = (
            f"{format_percent(df['habilitado'].mean() * 100)} ({format_int(df['habilitado'].sum())} de {len(df)} redes)"
            if is_hab
            else f"{format_percent(df['beneficiario'].mean() * 100)} ({format_int(df['beneficiario'].sum())} de {len(df)} redes)"
            if is_ben
            else format_currency_full(df["vaar"].sum())
            if is_vaar
            else format_currency_full(df["uniao_total"].sum())
        )
        parent.caption(f"**Total Brasil ({rotulo_metrica}):** {val_nac}")

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
        # Linhas estaduais nítidas em cinza ardósia e projeção Mercator alinhada
        fig.update_traces(marker_line_width=0.9, marker_line_color="#475569")
        fig.update_geos(
            projection_type="mercator",
            fitbounds="locations",
            visible=False,
            bgcolor="#FFFFFF",
        )
        fig.update_layout(
            separators=",.",  # Padrão numérico ABNT NBR
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            height=altura,
            margin=dict(l=6, r=6, t=6, b=6),
            coloraxis_colorbar=dict(
                title=dict(text=rotulo_metrica, font=dict(size=10, color="#1E293B")),
                thickness=11,
                tickfont=dict(color="#1E293B", size=9),
            ),
        )
        parent.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})

    def desenhar_fase_2(parent, altura: int = 460) -> None:
        parent.markdown("##### 📍 Fase 2: Regiões do País")
        regiao_sel = parent.selectbox(
            "Região Focal:",
            options=list(REGIOES),
            index=list(REGIOES).index(st.session_state.get("mapa_regiao_sel", "Nordeste")) if st.session_state.get("mapa_regiao_sel", "Nordeste") in REGIOES else 0,
            key="mapa_regiao_sel",
        )
        df_reg = df[df["regiao"] == regiao_sel]
        df_reg_uf = df_uf[df_uf["regiao"] == regiao_sel].copy()

        val_reg = (
            f"{format_percent(df_reg['habilitado'].mean() * 100)} ({format_int(df_reg['habilitado'].sum())} de {len(df_reg)} redes)"
            if is_hab
            else f"{format_percent(df_reg['beneficiario'].mean() * 100)} ({format_int(df_reg['beneficiario'].sum())} de {len(df_reg)} redes)"
            if is_ben
            else format_currency_full(df_reg["vaar"].sum())
            if is_vaar
            else format_currency_full(df_reg["uniao_total"].sum())
        )
        parent.caption(f"**Total Região {regiao_sel} ({rotulo_metrica}):** {val_reg}")

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
        fig_reg.update_traces(marker_line_width=1.0, marker_line_color="#475569")
        fig_reg.update_geos(
            projection_type="mercator",
            fitbounds="locations",
            visible=False,
            bgcolor="#FFFFFF",
        )
        fig_reg.update_layout(
            separators=",.",  # Padrão numérico ABNT NBR
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            height=altura,
            margin=dict(l=6, r=6, t=6, b=6),
            coloraxis_colorbar=dict(
                title=dict(text=rotulo_metrica, font=dict(size=10, color="#1E293B")),
                thickness=11,
                tickfont=dict(color="#1E293B", size=9),
            ),
        )
        parent.plotly_chart(fig_reg, use_container_width=True, config={"displayModeBar": False, "responsive": True})

        if "Em Abas" in modo_disp or "Em Linha" in modo_disp:
            fig_rank = chart_ranking_horizontal(
                df_reg_uf,
                categoria_col="uf",
                valor_col=var_col_uf,
                titulo=f"Classificação das UFs na Região {regiao_sel} ({rotulo_metrica})",
                destacar_primeiro=True,
                formato_rotulo="%{x:.1f}%" if is_taxa else "R$ %{x:,.2s}",
            )
            parent.plotly_chart(fig_rank, use_container_width=True)

    def desenhar_fase_3(parent, altura: int = 480) -> None:
        parent.markdown("##### 🏙️ Fase 3: Municípios por UF")
        regiao_atual = st.session_state.get("mapa_regiao_sel", "Nordeste")
        ufs_da_regiao = sorted([uf for uf, r in REGIAO_POR_UF.items() if r == regiao_atual])
        if not ufs_da_regiao:
            ufs_da_regiao = sorted(list(UF_CODIGO.keys()))

        if "mapa_uf_sel" in st.session_state and st.session_state["mapa_uf_sel"] not in ufs_da_regiao:
            st.session_state["mapa_uf_sel"] = "PI" if "PI" in ufs_da_regiao else ufs_da_regiao[0]

        uf_salva = st.session_state.get("mapa_uf_sel")
        idx_uf = ufs_da_regiao.index(uf_salva) if uf_salva in ufs_da_regiao else 0

        c_sel_uf, c_info_reg = parent.columns([2, 3])
        with c_sel_uf:
            uf_sel = st.selectbox(
                f"Estado (UF da Região {regiao_atual}):",
                options=ufs_da_regiao,
                index=idx_uf,
                key="mapa_uf_sel",
            )
        with c_info_reg:
            st.caption(f"ℹ️ Exibindo apenas estados da **Região {regiao_atual}**. Alterne a região acima para carregar outros estados.")

        df_mun = df[(df["uf"] == uf_sel) & (df["rede"] == "Municipal")].copy()

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
            else format_currency_full(df_mun["vaar"].sum())
            if is_vaar
            else format_currency_full(df_mun["uniao_total"].sum())
        )
        parent.caption(f"**Total Municípios {uf_sel} ({rotulo_metrica}):** {val_uf_total}")

        geo_mun = repo.geo_municipios(UF_CODIGO[uf_sel])
        if geo_mun.get("features"):
            col_mapa_f3, col_painel_f3 = parent.columns([3.2, 1.8])
            with col_mapa_f3:
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
                # Linhas municipais finas para evitar borrões de malha em alta densidade
                fig_mun.update_traces(marker_line_width=0.4, marker_line_color="#94A3B8")
                fig_mun.update_geos(
                    projection_type="mercator",
                    fitbounds="locations",
                    visible=False,
                    bgcolor="#FFFFFF",
                )
                fig_mun.update_layout(
                    separators=",.",  # Padrão numérico ABNT NBR
                    paper_bgcolor="#FFFFFF",
                    plot_bgcolor="#FFFFFF",
                    height=altura,
                    margin=dict(l=0, r=0, t=6, b=6),
                    coloraxis_colorbar=dict(
                        title=dict(text=rotulo_metrica, font=dict(size=10, color="#1E293B")),
                        thickness=11,
                        len=0.75,
                        x=1.0,
                        y=0.5,
                        tickfont=dict(color="#1E293B", size=9),
                    ),
                )
                st.plotly_chart(fig_mun, use_container_width=True, config={"displayModeBar": False, "responsive": True})

            with col_painel_f3:
                st.markdown(f"**Panorama Municipal — {uf_sel}**")
                n_mun = len(df_mun)
                n_hab_mun = int(df_mun["habilitado"].sum())
                n_ben_mun = int(df_mun["beneficiario"].sum())
                v_vaar_mun = float(df_mun["vaar"].sum())

                st.caption(
                    f"• **Total de Redes:** {format_int(n_mun)} municípios  \n"
                    f"• **Habilitados VAAR:** {format_int(n_hab_mun)} ({format_percent(n_hab_mun / n_mun * 100 if n_mun else 0)})  \n"
                    f"• **Beneficiados VAAR:** {format_int(n_ben_mun)} ({format_percent(n_ben_mun / n_mun * 100 if n_mun else 0)})  \n"
                    f"• **Total VAAR 2026:** {format_currency(v_vaar_mun)}"
                )

                top_mun = df_mun.sort_values(by="vaar", ascending=False).head(5)
                if not top_mun.empty and top_mun["vaar"].max() > 0:
                    st.markdown("###### Maiores Repasses na UF:")
                    df_top_view = pd.DataFrame({
                        "Município": top_mun["nome"],
                        "VAAR 2026": top_mun["vaar"].map(format_currency_full),
                    })
                    st.dataframe(df_top_view, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # RENDERIZAÇÃO RESPONSIVA CONFORME DISPOSIÇÃO
    # -------------------------------------------------------------------------
    tem_f1 = any("Fase 1" in f for f in fases_ativas)
    tem_f2 = any("Fase 2" in f for f in fases_ativas)
    tem_f3 = any("Fase 3" in f for f in fases_ativas)

    if modo_disp == "Lado a Lado":
        if tem_f1 and tem_f2:
            col_pais, col_reg = st.columns(2)
            with col_pais:
                with st.container(border=True):
                    desenhar_fase_1(st, altura=altura_mapa)
            with col_reg:
                with st.container(border=True):
                    desenhar_fase_2(st, altura=altura_mapa)
        elif tem_f1:
            with st.container(border=True):
                desenhar_fase_1(st, altura=altura_mapa)
        elif tem_f2:
            with st.container(border=True):
                desenhar_fase_2(st, altura=altura_mapa)

        if tem_f3:
            with st.container(border=True):
                desenhar_fase_3(st, altura=altura_mapa + 20)

    elif modo_disp == "Em Abas":
        abas_titulos = []
        if tem_f1:
            abas_titulos.append("🇧🇷 1. Brasil (Nacional)")
        if tem_f2:
            abas_titulos.append("📍 2. Regiões do País")
        if tem_f3:
            abas_titulos.append("🏙️ 3. Municípios por UF")

        abas = st.tabs(abas_titulos)
        a_idx = 0
        if tem_f1:
            with abas[a_idx]:
                with st.container(border=True):
                    desenhar_fase_1(st, altura=altura_mapa + 40)
            a_idx += 1
        if tem_f2:
            with abas[a_idx]:
                with st.container(border=True):
                    desenhar_fase_2(st, altura=altura_mapa + 40)
            a_idx += 1
        if tem_f3:
            with abas[a_idx]:
                with st.container(border=True):
                    desenhar_fase_3(st, altura=altura_mapa + 40)
            a_idx += 1

    else:
        # Modo Sequencial Expandido
        if tem_f1:
            with st.container(border=True):
                desenhar_fase_1(st, altura=altura_mapa + 20)
        if tem_f2:
            with st.container(border=True):
                desenhar_fase_2(st, altura=altura_mapa + 20)
        if tem_f3:
            with st.container(border=True):
                desenhar_fase_3(st, altura=altura_mapa + 20)

    # -------------------------------------------------------------------------
    # FICHA TÉCNICA AUDITADA DO MUNICÍPIO (Se Fase 3 estiver ativa)
    # -------------------------------------------------------------------------
    if tem_f3:
        st.markdown("---")
        st.markdown("##### 🔍 Ficha Técnica Auditada do Município")
        uf_ativa = st.session_state.get("mapa_uf_sel", "PI")
        df_mun_lista = df[(df["uf"] == uf_ativa) & (df["rede"] == "Municipal")].sort_values(by="nome")
        mun_ibges = df_mun_lista["ibge"].tolist()

        if "ficha_mun_sel" in st.session_state and st.session_state["ficha_mun_sel"] not in mun_ibges:
            st.session_state["ficha_mun_sel"] = mun_ibges[0] if mun_ibges else None

        map_mun_nomes = dict(zip(df_mun_lista["ibge"], df_mun_lista["nome"]))

        c_busca1, c_busca2 = st.columns([3, 1])
        with c_busca1:
            mun_selecionado = st.selectbox(
                f"Selecione um município de {uf_ativa} para auditar dados:",
                options=mun_ibges,
                format_func=lambda ib: f"{map_mun_nomes.get(ib, ib)} ({ib})",
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
                    st.markdown("**💰 Repasses Oficiais 2026**")
                    st.markdown(f"- **VAAR 2026:** {format_currency_full(m_dados['vaar'])}")
                    st.markdown(f"- **VAAR 2025:** {format_currency_full(m_dados['vaar_2025'])}")
                    st.markdown(f"- **Total União:** {format_currency_full(m_dados['uniao_total'])}")
                    st.markdown(f"- **VAAF:** {format_currency_full(m_dados['vaaf'])}")
                    st.markdown(f"- **VAAT:** {format_currency_full(m_dados['vaat'])}")

                with g2:
                    st.markdown("**📈 Indicadores de Habilitação**")
                    st.markdown(f"- **IND Atendimento:** {format_decimal(m_dados['ind_atend'], 4)}" if pd.notna(m_dados['ind_atend']) else "- **IND Atendimento:** —")
                    st.markdown(f"- **Evoluiu Atend:** {'Sim' if m_dados['evoluiu_atend'] else 'Não'}")
                    st.markdown(f"- **IND Aprendizagem:** {format_decimal(m_dados['ind_aprend'], 4)}" if pd.notna(m_dados['ind_aprend']) else "- **IND Aprendizagem:** —")
                    st.markdown(f"- **Evoluiu Aprend:** {'Sim' if m_dados['evoluiu_aprend'] else 'Não'}")
                    st.markdown(f"- **Reprovações:** {format_int(m_dados['n_reprovacoes'])} de 5")

                with g3:
                    st.markdown("**🎓 Qualidade & Desempenho**")
                    st.markdown(f"- **Ideb (Anos Iniciais):** {format_decimal(m_dados['ideb_ai'], 1)}" if pd.notna(m_dados['ideb_ai']) else "- **Ideb (AI):** —")
                    st.markdown(f"- **Ideb (Anos Finais):** {format_decimal(m_dados['ideb_af'], 1)}" if pd.notna(m_dados['ideb_af']) else "- **Ideb (AF):** —")
                    st.markdown(f"- **Saeb MT (AI):** {format_decimal(m_dados['saeb_ai_mt'], 1)}" if pd.notna(m_dados['saeb_ai_mt']) else "- **Saeb MT:** —")
                    st.markdown(f"- **Saeb LP (AI):** {format_decimal(m_dados['saeb_ai_lp'], 1)}" if pd.notna(m_dados['saeb_ai_lp']) else "- **Saeb LP:** —")
                    st.markdown(f"- **INSE Municipal:** {format_decimal(m_dados['inse'], 2)}" if pd.notna(m_dados['inse']) else "- **INSE:** —")

                with g4:
                    st.markdown("**⚖️ Status das 5 Condicionalidades**")
                    st.markdown(f"- **Cond. I (Diretor):** {'✅ Sim' if m_dados['c1'] else '❌ Não'}")
                    st.markdown(f"- **Cond. II (Saeb >= 80%):** {'✅ Sim' if m_dados['c2'] else '❌ Não'}")
                    st.markdown(f"- **Cond. III (Equidade):** {'✅ Sim' if m_dados['c3'] else '❌ Não'}")
                    st.markdown(f"- **Cond. IV (ICMS Educação):** {'✅ Sim' if m_dados['c4'] else '❌ Não'}")
                    st.markdown(f"- **Cond. V (BNCC):** {'✅ Sim' if m_dados['c5'] else '❌ Não'}")
