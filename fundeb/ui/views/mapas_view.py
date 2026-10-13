"""Visualização Geográfica em 3 Fases: Brasil, Regiões e Municípios com sincronização total de métricas."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from fundeb.data.repository import DataRepository
from fundeb.domain.territorio import REGIOES, REGIAO_POR_UF, UF_CODIGO, CODIGO_UF
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

# Fundo cartográfico neutro e elegante (elimina o branco estéril e melhora a percepção visual)
BG_MAPA = "#F1F5F9"

# 1. Escalas Multi-Tom de Alto Contraste (Stephen Few & Cynthia Brewer / ColorBrewer YlGnBu e Multi-Hue)
# Combinam variação de luminosidade com transição de matizes (amarelo/ouro ➔ esmeralda ➔ azul marinho)
# para evitar que valores intermediários pareçam apenas variações difusas de uma mesma cor.
ESCALA_TAXA_MULTIHUE = [
    [0.00, "#CBD5E1"],  # Cinza ardósia claro para zero / inabilitado
    [0.01, "#FEF08A"],  # Amarelo/Ouro suave (taxa incipiente 1-25%)
    [0.35, "#F59E0B"],  # Âmbar aquecido (taxa baixa-média 25-50%)
    [0.65, "#10B981"],  # Verde esmeralda vivo (taxa média-alta 50-75%)
    [0.85, "#0D9488"],  # Azul petróleo / Teal (taxa alta 75-85%)
    [1.00, "#1E3A8A"],  # Azul marinho profundo / Índigo (excelência >85%)
]

ESCALA_RECURSOS_MULTIHUE = [
    [0.00, "#CBD5E1"],  # Cinza ardósia para zero / sem repasse
    [0.01, "#FED7AA"],  # Pêssego / Âmbar claro (repasse inicial)
    [0.30, "#38BDF8"],  # Azul celeste vibrante (repasse intermediário)
    [0.65, "#2563EB"],  # Azul royal sólido (repasse robusto)
    [1.00, "#0F172A"],  # Azul meia-noite executivo (topo nacional)
]

# 2. Escalas Clássicas Monocromáticas (para comparação ou preferência sóbria)
ESCALA_TAXA_CLASSICA = [
    [0.0, "#CBD5E1"],
    [0.25, "#6EE7B7"],
    [0.50, "#10B981"],
    [0.75, "#047857"],
    [1.00, "#064E3B"],
]

ESCALA_RECURSOS_CLASSICA = [
    [0.0, "#CBD5E1"],
    [0.25, "#93C5FD"],
    [0.50, "#3B82F6"],
    [0.75, "#1D4ED8"],
    [1.00, "#0F172A"],
]


def render_mapas_view(df: pd.DataFrame, repo: DataRepository) -> None:
    st.subheader("🗺️ Análise Espacial em 3 Fases (Sincronização Multi-Escala)")
    st.markdown(
        "Explore a distribuição territorial dos recursos e da habilitação do FUNDEB e VAAR 2026. "
        "Ao alternar a métrica abaixo, **todos os mapas e indicadores selecionados são atualizados em tempo real**."
    )

    # ------------------------------------------------------------- CONTROLES DE SINCRONIZAÇÃO
    c_metr, c_fases, c_disp = st.columns([4, 3, 4])
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
            "📐 Disposição Visual:",
            options=[
                "Linha 1: País e Região (Lado a Lado) • Linha 2: Municípios Abaixo",
                "Em Abas (Tela Cheia por Escala)",
                "Em Linha (Sequencial Expandido)",
            ],
            default="Linha 1: País e Região (Lado a Lado) • Linha 2: Municípios Abaixo",
        )

    # Controles Cartográficos Secundários (Paleta de Cores e Alinhamento Stephen Few)
    c_pal, c_dica = st.columns([4, 7])
    with c_pal:
        paleta_escolhida = st.selectbox(
            "🎨 Esquema de Cores do Degradê:",
            options=[
                "Multi-Tom Contrastante (Amarelo ➔ Esmeralda ➔ Azul)",
                "Viridis Perceptual (Científico / Acessível)",
                "Bicromático Clássico (Ardósia ➔ Azul/Verde)",
            ],
            index=0,
            help="Escalas multi-tom são a melhor prática cartográfica (Few & Brewer) para distinguir patamares com precisão visual.",
        )
    with c_dica:
        st.caption(
            "💡 **Princípio Cartográfico de Stephen Few & Cynthia Brewer (ColorBrewer):** "
            "Degradês de uma única cor costumam causar ambiguidade em valores intermediários. "
            "A paleta **Multi-Tom** combina transição de matizes com intensidade luminosa, "
            "tornando cada patamar quantitativo perceptível de forma instantânea e sem confusão."
        )

    st.markdown("---")

    # Mapeamento e Configuração da Métrica Escolhida
    is_hab = metrica_escolhida == "% Habilitadas"
    is_ben = metrica_escolhida == "% Beneficiárias"
    is_vaar = metrica_escolhida == "Valor Total VAAR (R$)"
    is_uniao = metrica_escolhida == "Total Complementação União (R$)"
    is_taxa = is_hab or is_ben

    # Seleção da Escala de Cor conforme configuração
    if "Multi-Tom" in paleta_escolhida:
        cor_escala = ESCALA_TAXA_MULTIHUE if is_taxa else ESCALA_RECURSOS_MULTIHUE
    elif "Viridis" in paleta_escolhida:
        cor_escala = px.colors.sequential.Viridis
    else:
        cor_escala = ESCALA_TAXA_CLASSICA if is_taxa else ESCALA_RECURSOS_CLASSICA

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

    # ------------------------------------------------------------- FUNÇÕES DE DESENHO DE MAPA
    def desenhar_fase_1(parent, altura: int = 440) -> None:
        parent.markdown("##### 🇧🇷 Fase 1: Brasil (Visão Nacional Completa)")
        val_nac = (
            f"{format_percent(df['habilitado'].mean() * 100)} ({format_int(df['habilitado'].sum())} redes)"
            if is_hab
            else f"{format_percent(df['beneficiario'].mean() * 100)} ({format_int(df['beneficiario'].sum())} redes)"
            if is_ben
            else format_currency(df["vaar"].sum())
            if is_vaar
            else format_currency(df["uniao_total"].sum())
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
        fig.update_traces(marker_line_width=1.2, marker_line_color="#FFFFFF")
        fig.update_geos(fitbounds="locations", visible=False, bgcolor=BG_MAPA)
        fig.update_layout(
            separators=",.",  # Padrão numérico ABNT
            paper_bgcolor=BG_MAPA,
            plot_bgcolor=BG_MAPA,
            height=altura,
            margin=dict(l=10, r=10, t=10, b=10),
            coloraxis_colorbar=dict(
                title=dict(text=rotulo_metrica, font=dict(size=11, color="#1E293B")),
                thickness=12,
                tickfont=dict(color="#1E293B", size=10),
            ),
        )
        parent.plotly_chart(fig, use_container_width=True)

    def desenhar_fase_2(parent, altura: int = 440) -> None:
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
            f"{format_percent(df_reg['habilitado'].mean() * 100)} ({format_int(df_reg['habilitado'].sum())} redes)"
            if is_hab
            else f"{format_percent(df_reg['beneficiario'].mean() * 100)} ({format_int(df_reg['beneficiario'].sum())} redes)"
            if is_ben
            else format_currency(df_reg["vaar"].sum())
            if is_vaar
            else format_currency(df_reg["uniao_total"].sum())
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
        fig_reg.update_traces(marker_line_width=1.2, marker_line_color="#FFFFFF")
        fig_reg.update_geos(fitbounds="locations", visible=False, bgcolor=BG_MAPA)
        fig_reg.update_layout(
            separators=",.",  # Padrão numérico ABNT
            paper_bgcolor=BG_MAPA,
            plot_bgcolor=BG_MAPA,
            height=altura,
            margin=dict(l=10, r=10, t=10, b=10),
            coloraxis_colorbar=dict(
                title=dict(text=rotulo_metrica, font=dict(size=11, color="#1E293B")),
                thickness=12,
                tickfont=dict(color="#1E293B", size=10),
            ),
        )
        parent.plotly_chart(fig_reg, use_container_width=True)

        # Se for modo abas ou linha, exibe ranking horizontal
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

    def desenhar_fase_3(parent, altura: int = 460) -> None:
        parent.markdown("##### 🏙️ Fase 3: Municípios por UF")
        # Sincronização em cascata: filtra apenas UFs pertencentes à região selecionada na Fase 2
        regiao_atual = st.session_state.get("mapa_regiao_sel", "Nordeste")
        ufs_da_regiao = sorted([uf for uf, r in REGIAO_POR_UF.items() if r == regiao_atual])
        if not ufs_da_regiao:
            ufs_da_regiao = sorted(list(UF_CODIGO.keys()))

        # Sanitização preventiva de sessão: previne StreamlitAPIException se UF anterior não pertencer à nova região
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
            st.caption(f"ℹ️ Exibindo apenas estados pertencentes à **Região {regiao_atual}**. Alterne a região acima para carregar outros estados.")

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
            else format_currency(df_mun["vaar"].sum())
            if is_vaar
            else format_currency(df_mun["uniao_total"].sum())
        )
        parent.caption(f"**Total Municípios {uf_sel} ({rotulo_metrica}):** {val_uf_total}")

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
            fig_mun.update_traces(marker_line_width=0.6, marker_line_color="#CBD5E1")
            fig_mun.update_geos(fitbounds="locations", visible=False, bgcolor=BG_MAPA)
            fig_mun.update_layout(
                separators=",.",  # Padrão numérico ABNT
                paper_bgcolor=BG_MAPA,
                plot_bgcolor=BG_MAPA,
                height=altura,
                margin=dict(l=10, r=10, t=10, b=10),
                coloraxis_colorbar=dict(
                    title=dict(text=rotulo_metrica, font=dict(size=11, color="#1E293B")),
                    thickness=12,
                    tickfont=dict(color="#1E293B", size=10),
                ),
            )
            parent.plotly_chart(fig_mun, use_container_width=True)

    # ------------------------------------------------------------- RENDERIZAÇÃO CONFORME DISPOSIÇÃO
    tem_f1 = any("Fase 1" in f for f in fases_ativas)
    tem_f2 = any("Fase 2" in f for f in fases_ativas)
    tem_f3 = any("Fase 3" in f for f in fases_ativas)

    if modo_disp == "Linha 1: País e Região (Lado a Lado) • Linha 2: Municípios Abaixo":
        # Linha 1: País e Região Lado a Lado na MESMA linha
        if tem_f1 and tem_f2:
            col_pais, col_reg = st.columns(2)
            with col_pais:
                with st.container(border=True):
                    desenhar_fase_1(col_pais, altura=440)
            with col_reg:
                with st.container(border=True):
                    desenhar_fase_2(col_reg, altura=440)
        elif tem_f1:
            with st.container(border=True):
                desenhar_fase_1(st, altura=460)
        elif tem_f2:
            with st.container(border=True):
                desenhar_fase_2(st, altura=460)

        # Linha 2: Abaixo, linha exclusiva para Município
        if tem_f3:
            with st.container(border=True):
                desenhar_fase_3(st, altura=500)

    elif modo_disp == "Em Abas (Tela Cheia por Escala)":
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
                    desenhar_fase_1(abas[a_idx], altura=520)
            a_idx += 1
        if tem_f2:
            with abas[a_idx]:
                with st.container(border=True):
                    desenhar_fase_2(abas[a_idx], altura=500)
            a_idx += 1
        if tem_f3:
            with abas[a_idx]:
                with st.container(border=True):
                    desenhar_fase_3(abas[a_idx], altura=500)
            a_idx += 1

    else:
        # Modo em Linha (Seções Expandidas Sequenciais)
        if tem_f1:
            with st.container(border=True):
                desenhar_fase_1(st, altura=500)
        if tem_f2:
            with st.container(border=True):
                desenhar_fase_2(st, altura=460)
        if tem_f3:
            with st.container(border=True):
                desenhar_fase_3(st, altura=460)

    # ------------------------------------------------------------- FICHA TÉCNICA DO MUNICÍPIO (Se Fase 3 estiver ativa)
    if tem_f3:
        st.markdown("---")
        st.markdown("##### 🔍 Ficha Técnica Detalhada do Município")
        uf_ativa = st.session_state.get("mapa_uf_sel", "PI")
        df_mun_lista = df[(df["uf"] == uf_ativa) & (df["rede"] == "Municipal")].sort_values(by="nome")
        mun_ibges = df_mun_lista["ibge"].tolist()

        # Sanitização preventiva do município selecionado
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
                    st.markdown("**💰 Repasses 2026**")
                    st.markdown(f"- **VAAR 2026:** {format_currency_full(m_dados['vaar'])}")
                    st.markdown(f"- **VAAR 2025:** {format_currency_full(m_dados['vaar_2025'])}")
                    st.markdown(f"- **Total União:** {format_currency_full(m_dados['uniao_total'])}")
                    st.markdown(f"- **VAAF:** {format_currency_full(m_dados['vaaf'])}")
                    st.markdown(f"- **VAAT:** {format_currency_full(m_dados['vaat'])}")

                with g2:
                    st.markdown("**📈 Indicadores VAAR**")
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
