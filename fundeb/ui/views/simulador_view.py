"""Simulador VAAR interativo com diferenciação rigorosa entre Rede Estadual e Municipal."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

import plotly.graph_objects as go
from fundeb.services.simulator import SimulatorService
from fundeb.domain.territorio import UF_CODIGO
from fundeb.ui.components import (
    metric_card,
    format_currency,
    format_currency_full,
    format_percent,
    format_int,
    format_decimal,
    status_badge,
)
from fundeb.ui.charts import (
    apply_few_theme,
    chart_part_to_whole_100,
    chart_lollipop_hipoteses,
    chart_dumbbell_comparativo,
)


def render_simulador_view(sim_service: SimulatorService, df: pd.DataFrame) -> None:
    st.subheader("🧮 Simulador VAAR: Impacto Financeiro e Sensibilidade")
    st.markdown(
        """
        Simulador metodológico calibrado com base na **Nota Técnica Inep nº 23/2022** e no repositório de referência
        [*guimaraesca/Simulador-VAAR-PI*](https://github.com/guimaraesca/Simulador-VAAR-PI).
        Permite estimar o ganho ou perda de recursos do VAAR sob diferentes cenários de atendimento escolar e aprendizagem.
        """
    )

    # ------------------------------------------------------------- DIFERENCIAÇÃO ESTADUAL VS MUNICIPAL
    st.markdown("#### 1. Seleção da Esfera e da Rede de Ensino")

    col_esf, col_sel = st.columns([1, 2])
    with col_esf:
        esfera_escolhida = st.radio(
            "Selecione a Esfera da Rede:",
            options=["Rede Municipal", "Rede Estadual"],
            horizontal=True,
        )

    # Filtrar entes conforme a esfera
    if esfera_escolhida == "Rede Estadual":
        st.info("🏛️ **Metodologia Rede Estadual:** Etapa de expansão de atendimento avaliada no **Ensino Médio** (matrículas e taxas de abandono do EM). Aprendizagem avaliada no Ensino Fundamental e Ensino Médio.")
        df_esf = df[df["rede"] == "Estadual"].sort_values(by="uf")
        map_est_nomes = dict(zip(df_esf["ibge"], df_esf["nome"]))
        ente_ibge = st.selectbox(
            "Selecione o Estado:",
            options=df_esf["ibge"].tolist(),
            format_func=lambda ib: f"{map_est_nomes.get(ib, ib)} (IBGE {ib})",
        )
    else:
        st.info("🏫 **Metodologia Rede Municipal:** Etapa de expansão de atendimento avaliada na **Educação Infantil (Creche e Pré-Escola)**. Aprendizagem avaliada no Ensino Fundamental (Anos Iniciais e Finais).")
        col_uf, col_mun = st.columns(2)
        with col_uf:
            uf_filtro = st.selectbox("Selecione a UF:", options=sorted(list(UF_CODIGO.keys())), index=sorted(list(UF_CODIGO.keys())).index("PI") if "PI" in UF_CODIGO else 0)
        df_mun_uf = df[(df["rede"] == "Municipal") & (df["uf"] == uf_filtro)].sort_values(by="nome")
        map_mun_nomes = dict(zip(df_mun_uf["ibge"], df_mun_uf["nome"]))
        with col_mun:
            ente_ibge = st.selectbox(
                "Selecione o Município:",
                options=df_mun_uf["ibge"].tolist(),
                format_func=lambda ib: f"{map_mun_nomes.get(ib, ib)} (IBGE {ib})",
            )

    if not ente_ibge:
        st.warning("Selecione uma rede para iniciar a simulação.")
        return

    ente = sim_service.get_ente(ente_ibge)
    if not ente:
        st.error("Ente não encontrado no banco de dados.")
        return

    st.markdown("---")

    # ------------------------------------------------------------- PARÂMETROS DE SIMULAÇÃO
    st.markdown("#### 2. Definição dos Cenários e Parâmetros da Simulação")

    c_par1, c_par2 = st.columns(2)
    with c_par1:
        st.markdown("##### 📐 Cenário de Atendimento (Expansão de Matrículas)")
        opcao_atend = st.radio(
            "Tipo de Cenário de Atendimento:",
            options=["Cenários Históricos do IEE (Simulador-VAAR-PI)", "Variação Percentual Livre (Slider)"],
        )

        cenario_iee = None
        slider_atend = 0.0

        if "Cenários Históricos" in opcao_atend:
            cenario_iee = st.selectbox(
                "Selecione o Cenário do IEE:",
                options=[
                    "IEE vigente",
                    "Cenário (a) — com 2021",
                    "Cenário (b) — sem 2021",
                    "Cenário (c) — 2 anos com 2021",
                    "Cenário (d) — 2 anos sem 2021",
                ],
            )
        else:
            slider_atend = st.slider(
                "Variação no Indicador de Atendimento (%):",
                min_value=-30.0,
                max_value=50.0,
                value=5.0,
                step=1.0,
                help="Variação simulada no indicador IND_Atendimento da rede.",
            )

    with c_par2:
        st.markdown("##### 📚 Cenário de Aprendizagem & Equidade")
        slider_aprend = st.slider(
            "Variação no Indicador de Aprendizagem (%):",
            min_value=-30.0,
            max_value=50.0,
            value=5.0,
            step=1.0,
            help="Simula o efeito do ganho de proficiência Saeb e redução das desigualdades de nível socioeconômico e raça.",
        )

        forcar_hab = False
        if not ente.get("habilitado"):
            forcar_hab = st.toggle(
                "Simular regularização das 5 condicionalidades",
                value=True,
                help="Elegibilidade Plena: calcula a estimativa de repasse caso a rede cumpra todos os requisitos normativos do Art. 14.",
            )

    # Executar a simulação
    resultado = sim_service.simular_ente(
        ibge=ente_ibge,
        delta_atendimento_pct=slider_atend,
        delta_aprendizagem_pct=slider_aprend,
        forcar_habilitacao=forcar_hab,
        cenario_iee_escolhido=cenario_iee,
    )

    if not resultado:
        st.error("Não foi possível processar a simulação para este ente.")
        return

    st.markdown("---")

    # ------------------------------------------------------------- RESULTADOS E IMPACTO FINANCEIRO
    st.markdown("#### 3. Projeção de Impacto Financeiro")

    k_res1, k_res2, k_res3 = st.columns(3)
    with k_res1:
        metric_card(
            title="VAAR Atual (Publicação FNDE)",
            value=format_currency(resultado.vaar_total_orig_rs),
            subtitle=f"{status_badge('Habilitado' if ente['habilitado'] else 'Não habilitado')}",
        )
    with k_res2:
        metric_card(
            title="VAAR Projetado (Simulado)",
            value=format_currency(resultado.vaar_total_sim_rs),
            subtitle=f"Atend: {format_currency(resultado.vaar_atend_sim_rs)} | Aprend: {format_currency(resultado.vaar_aprend_sim_rs)}",
        )
    with k_res3:
        metric_card(
            title="Impacto Líquido (Delta)",
            value=f"{'+' if resultado.delta_rs >= 0 else ''}{format_currency(resultado.delta_rs)}",
            subtitle=f"Variação percentual: {'+' if resultado.delta_pct >= 0 else ''}{format_percent(resultado.delta_pct, 2)}",
            delta=f"{'+' if resultado.delta_pct >= 0 else ''}{format_percent(resultado.delta_pct, 2)}",
            delta_color="normal" if resultado.delta_rs >= 0 else "red",
        )
    # Gráfico Stephen Few: Comparativo Antes x Depois e Parte-pelo-Todo (50/50)
    col_c1, col_c2 = st.columns([1, 1])
    with col_c1:
        # Comparação Direta com Base Zero (Stephen Few - Slide 87)
        fig_comp = go.Figure()
        fig_comp.add_trace(
            go.Bar(
                x=["VAAR Atual", "VAAR Projetado"],
                y=[resultado.vaar_total_orig_rs, resultado.vaar_total_sim_rs],
                marker=dict(color=["#64748B", "#1E40AF"]),
                text=[resultado.vaar_total_orig_rs, resultado.vaar_total_sim_rs],
                texttemplate="R$ %{y:,.2s}",
                textposition="outside",
            )
        )
        fig_comp.update_layout(
            title=dict(text="Comparativo de Repasse (Base Zero)", font=dict(size=13, color="#0F172A")),
            height=220,
        )
        apply_few_theme(fig_comp, show_x_grid=False, show_y_grid=True)
        st.plotly_chart(fig_comp, use_container_width=True)

    with col_c2:
        # Parte-pelo-Todo 100% (Stephen Few - Slide 103)
        fig_pw = chart_part_to_whole_100(
            rotulo="Distribuição Legal",
            parte_a_nome="Cota Atendimento",
            parte_a_val=resultado.vaar_atend_sim_rs,
            parte_b_nome="Cota Aprendizagem",
            parte_b_val=resultado.vaar_aprend_sim_rs,
            titulo="Repartição das Cotas Legais no Repasse Projetado",
        )
        st.plotly_chart(fig_pw, use_container_width=True)

    st.markdown("---")

    # ------------------------------------------------------------- 4. GRÁFICO LOLLIPOP DA TRILHA DE HIPÓTESES
    st.markdown("#### 🍭 4. Trilha de Hipóteses: Do Recebido Atual à Melhor Hipótese Teórica")
    st.markdown(
        f"Acompanhe visualmente a trajetória financeira de **{resultado.nome}** partindo do valor atualmente recebido até "
        "a melhor hipótese de captação teórica permitida pela fórmula legal do Inep:"
    )

    trilha_hipoteses = sim_service.simular_trilha_hipoteses(resultado.ibge)
    if trilha_hipoteses:
        fig_lolli = chart_lollipop_hipoteses(
            trilha_hipoteses,
            titulo=f"Trilha de Hipóteses Lollipop — {resultado.nome} ({resultado.uf})",
        )
        st.plotly_chart(fig_lolli, use_container_width=True)

    st.markdown("---")

    # ------------------------------------------------------------- 5. MEMÓRIA DE CÁLCULO E FÓRMULAS
    st.markdown("#### 5. Memória de Cálculo Passo a Passo (Fórmulas Matemáticas)")
    st.markdown(
        """
        Transparência metodológica: acompanhe como cada etapa da legislação e da fórmula do Inep
        converte as taxas escolares no peso da matrícula e no valor financeiro em Reais.
        """
    )

    for item in resultado.memoria_calculo:
        with st.container(border=True):
            col_m1, col_m2 = st.columns([1.1, 1.2])
            with col_m1:
                st.markdown(f"**{item['passo']}**")
                if "$" in item["formula"] or "\\" in item["formula"]:
                    st.latex(item["formula"])
                else:
                    st.caption(item["formula"])
            with col_m2:
                desc_escaped = str(item["descricao"]).replace("$", r"\$")
                st.markdown(desc_escaped)

    # Tabela Histórica do IEE da Rede
    if resultado.cenarios_iee:
        with st.expander("📊 Cenários de Expansão Escolar (IEE) da Rede", expanded=False):
            st.markdown(
                f"Série de expansão calculada sobre a etapa: **{resultado.etapa_atendimento}**"
            )
            df_iee_tabela = pd.DataFrame([
                {
                    "Cenário": c["cenario"],
                    "Período Base": c["periodo"],
                    "IEE Calculado": format_decimal(c["iee"], 4) if c["iee"] else "—",
                    "Evoluiu (IEE >= 1.0)": "✅ Sim" if c["evolui"] else "❌ Não",
                    "Fórmula de Composição": c["formula"],
                }
                for c in resultado.cenarios_iee
            ])
            st.dataframe(df_iee_tabela, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ------------------------------------------------------------- 6. COMPARATIVO TERRITORIAL LOLLIPOP
    st.markdown("#### 🗺️ 6. Comparativo Territorial Lollipop: Recebido Atual vs Melhor Hipótese")
    st.markdown(
        "Visualize lado a lado o contraste entre o **VAAR efetivamente recebido** (ponto cinza) e o "
        "**potencial na melhor hipótese** (ponto verde esmeralda) para redes estaduais ou municípios:"
    )

    c_esf_t, c_uf_t, c_top_t = st.columns([1, 1, 1])
    with c_esf_t:
        esfera_comp = st.radio(
            "Visualizar Território Por:",
            options=["Por Estado (27 Redes Estaduais)", "Por Municípios (Conforme Estado Escolhido)"],
            index=0 if esfera_escolhida == "Rede Estadual" else 1,
            horizontal=False,
            key="lolli_esfera_radio",
        )

    if "Por Estado" in esfera_comp:
        with st.spinner("Processando potencial de todas as 27 redes estaduais..."):
            df_comp_est = sim_service.comparativo_entes_potencial(esfera="Estadual")
        fig_dumb_est = chart_dumbbell_comparativo(
            df_comp_est,
            categoria_col="nome",
            val_atual_col="vaar_atual",
            val_potencial_col="vaar_melhor_hipotese",
            titulo="Comparativo das 27 Redes Estaduais: VAAR Recebido vs Melhor Hipótese Potencial",
            max_linhas=27,
        )
        st.plotly_chart(fig_dumb_est, use_container_width=True)
    else:
        with c_uf_t:
            uf_comp = st.selectbox(
                "Selecione o Estado (UF):",
                options=sorted(list(UF_CODIGO.keys())),
                index=sorted(list(UF_CODIGO.keys())).index(ente["uf"]) if ente["uf"] in UF_CODIGO else 0,
                key="lolli_uf_select",
            )
        with c_top_t:
            filtro_mun_tipo = st.selectbox(
                "Filtro de Municípios:",
                options=[
                    "Top 20 com Maior Potencial de Salto (+Δ)",
                    "Top 35 com Maior Potencial de Salto (+Δ)",
                    "Apenas Não Habilitados (Potencial de Entrada)",
                    "Todos os Municípios da UF",
                ],
                index=0,
                key="lolli_filtro_mun",
            )

        with st.spinner(f"Processando potencial dos municípios de {uf_comp}..."):
            df_comp_mun = sim_service.comparativo_entes_potencial(esfera="Municipal", uf=uf_comp)

        if "Não Habilitados" in filtro_mun_tipo:
            df_comp_mun = df_comp_mun[~df_comp_mun["habilitado"]]
            n_linhas = min(35, len(df_comp_mun))
        elif "Top 20" in filtro_mun_tipo:
            n_linhas = min(20, len(df_comp_mun))
        elif "Top 35" in filtro_mun_tipo:
            n_linhas = min(35, len(df_comp_mun))
        else:
            n_linhas = len(df_comp_mun)

        if df_comp_mun.empty:
            st.info(f"ℹ️ Não há municípios nesta categoria para o estado {uf_comp} (100% das redes municipais estão habilitadas!).")
        else:
            fig_dumb_mun = chart_dumbbell_comparativo(
                df_comp_mun,
                categoria_col="nome",
                val_atual_col="vaar_atual",
                val_potencial_col="vaar_melhor_hipotese",
                titulo=f"Municípios de {uf_comp}: VAAR Atual Recebido vs Melhor Hipótese Potencial",
                max_linhas=n_linhas,
            )
            st.plotly_chart(fig_dumb_mun, use_container_width=True)
