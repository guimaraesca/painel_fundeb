"""Simulador VAAR interativo com diferenciação rigorosa entre Rede Estadual e Municipal."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from fundeb.services.simulator import SimulatorService
from fundeb.domain.territorio import UF_CODIGO
from fundeb.ui.components import (
    metric_card,
    format_currency,
    format_currency_full,
    format_percent,
    format_int,
    status_badge,
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
        ente_ibge = st.selectbox(
            "Selecione o Estado:",
            options=df_esf["ibge"].tolist(),
            format_func=lambda ib: f"{df_esf[df_esf['ibge'] == ib]['nome'].iloc[0]} (IBGE {ib})",
        )
    else:
        st.info("🏫 **Metodologia Rede Municipal:** Etapa de expansão de atendimento avaliada na **Educação Infantil (Creche e Pré-Escola)**. Aprendizagem avaliada no Ensino Fundamental (Anos Iniciais e Finais).")
        col_uf, col_mun = st.columns(2)
        with col_uf:
            uf_filtro = st.selectbox("Selecione a UF:", options=sorted(list(UF_CODIGO.keys())), index=sorted(list(UF_CODIGO.keys())).index("PI") if "PI" in UF_CODIGO else 0)
        df_mun_uf = df[(df["rede"] == "Municipal") & (df["uf"] == uf_filtro)].sort_values(by="nome")
        with col_mun:
            ente_ibge = st.selectbox(
                "Selecione o Município:",
                options=df_mun_uf["ibge"].tolist(),
                format_func=lambda ib: f"{df_mun_uf[df_mun_uf['ibge'] == ib]['nome'].iloc[0]} (IBGE {ib})",
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
                "Simular caso regularize as 5 condicionalidades (Elegibilidade Plena)",
                value=True,
                help="Se ativado, calcula a estimativa de repasse caso a rede vença os gargalos normativos.",
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
            subtitle=f"Variação percentual: {resultado.delta_pct:+.2f}%",
            delta=f"{resultado.delta_pct:+.2f}%",
            delta_color="normal" if resultado.delta_rs >= 0 else "red",
        )

    st.markdown("---")

    # ------------------------------------------------------------- MEMÓRIA DE CÁLCULO E FÓRMULAS
    st.markdown("#### 4. Memória de Cálculo Passo a Passo (Fórmulas Matemáticas)")
    st.markdown(
        """
        Transparência metodológica: acompanhe como cada etapa da legislação e da fórmula do Inep
        converte as taxas escolares no peso da matrícula e no valor financeiro em Reais.
        """
    )

    for item in resultado.memoria_calculo:
        with st.container(border=True):
            col_m1, col_m2 = st.columns([1, 2])
            with col_m1:
                st.markdown(f"**{item['passo']}**")
                if "$" in item["formula"] or "\\" in item["formula"]:
                    st.latex(item["formula"])
                else:
                    st.caption(item["formula"])
            with col_m2:
                st.markdown(item["descricao"])

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
                    "IEE Calculado": f"{c['iee']:.4f}" if c["iee"] else "—",
                    "Evoluiu (IEE >= 1.0)": "✅ Sim" if c["evolui"] else "❌ Não",
                    "Fórmula de Composição": c["formula"],
                }
                for c in resultado.cenarios_iee
            ])
            st.dataframe(df_iee_tabela, use_container_width=True, hide_index=True)
