"""Camada Histórica de Recursos e Guia Executivo de Intervenção ('Como Agir')."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from fundeb.domain.legal import RAMPA_COMPLEMENTACAO, FONTE_RAMPA
from fundeb.ui.components import metric_card


def render_historico_view(df: pd.DataFrame) -> None:
    st.subheader("📈 Linha Histórica dos Recursos & Como Agir")
    st.markdown(
        """
        Compreenda a progressão constitucional dos recursos federais do FUNDEB (EC nº 108/2020)
        e adote uma **estratégia estruturada para garantir e maximizar os repasses nos próximos ciclos**.
        """
    )

    # ------------------------------------------------------------- BLOCO 1: RAMPA CONSTITUCIONAL
    st.markdown("##### 🏛️ Progressão da Complementação da União ao FUNDEB (2021–2026)")
    st.caption(f"Fonte Oficial: {FONTE_RAMPA}")

    dados_rampa = [
        {"Ano": ano, "VAAF (p.p.)": vaaf, "VAAT (p.p.)": vaat, "VAAR (p.p.)": vaar, "Total União (p.p.)": vaaf + vaat + vaar}
        for ano, (vaaf, vaat, vaar) in sorted(RAMPA_COMPLEMENTACAO.items())
    ]
    df_rampa = pd.DataFrame(dados_rampa)

    col_g, col_t = st.columns([3, 2])
    with col_g:
        fig_rampa = px.line(
            df_rampa,
            x="Ano",
            y=["VAAF (p.p.)", "VAAT (p.p.)", "VAAR (p.p.)", "Total União (p.p.)"],
            markers=True,
            title="Evolução Percentual sobre a Receita dos Fundos",
            labels={"value": "Pontos Percentuais (%)", "variable": "Modalidade"},
            color_discrete_map={
                "VAAF (p.p.)": "#3B82F6",
                "VAAT (p.p.)": "#10B981",
                "VAAR (p.p.)": "#F59E0B",
                "Total União (p.p.)": "#1E3A8A",
            },
        )
        fig_rampa.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_rampa, use_container_width=True)

    with col_t:
        st.dataframe(df_rampa, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ------------------------------------------------------------- BLOCO 2: COMO AGIR
    st.subheader("🎯 Matriz de Ação Estratégica: Como Melhorar os Próximos Recebimentos")
    st.markdown(
        """
        O VAAR não é repasse automático: exige **cumprimento prévio das 5 condicionalidades** e **evolução positiva nos indicadores de atendimento e aprendizagem**.
        Abaixo está o plano de ação recomendado para secretarias de educação:
        """
    )

    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            st.markdown("#### 1️⃣ Regularização de Habilitação (Obrigatória)")
            st.markdown(
                """
                - **Cond. I — Provimento de Diretores**:
                  * Editar decreto/lei municipal estabelecendo processo seletivo por critérios de mérito e desempenho ou eleição qualificada.
                  * Inserir documentação no SIMEC antes do encerramento da janela anual.
                - **Cond. II — Participação no SAEB (Meta: >= 80%)**:
                  * Mapeamento escola a escola das turmas avaliadas.
                  * Busca ativa no dia da prova e convocação de alunos ausentes na reaplicação.
                - **Cond. III — ICMS Educação e Redução de Desigualdades**:
                  * Articular com a Assembleia Legislativa estadual e UNDIME a vigência de regras de rateio do ICMS baseadas em aprendizagem.
                - **Cond. IV — BNCC e Currículo**:
                  * Homologar o documento curricular da rede alinhado à BNCC no respectivo Conselho de Educação.
                - **Cond. V — Transmissão SIOPE**:
                  * Fechar e validar os balanços contábeis e fiscais bimestrais no SIOPE com antecedência mínima de 15 dias do prazo final.
                """
            )

    with c2:
        with st.container(border=True):
            st.markdown("#### 2️⃣ Maximização dos Indicadores de Rateio")
            st.markdown(
                """
                - **Atendimento (IEE & IAE)**:
                  * **Rede Municipal**: Ampliar matrículas na Educação Infantil (Creche e Pré-Escola) mantendo baixo índice de evasão.
                  * **Rede Estadual**: Reduzir abandono escolar no Ensino Médio e reter alunos com programas de permanência.
                - **Aprendizagem (Saeb & IDEB)**:
                  * Foco pedagógico nas turmas de transição (5º ano, 9º ano EF e 3ª série EM).
                  * Monitoramento contínuo das proficiências em Língua Portuguesa e Matemática.
                - **Equidade Socioeconômica e Racial**:
                  * O algoritmo do Inep penaliza redes onde alunos pretos, pardos ou de baixo INSE ficam para trás.
                  * Implementar recomposição de aprendizagem focada nas escolas periféricas e de menor nível socioeconômico.
                """
            )

    st.markdown("---")

    # ------------------------------------------------------------- BLOCO 3: CHECKLIST INTERATIVO
    st.subheader("✅ Checklist Interativo de Conformidade da Rede")
    st.markdown("Utilize este checklist em reuniões de alinhamento com a equipe técnica da Secretaria:")

    ck1 = st.checkbox("Lei/Normativo de Diretores Escolares por Mérito devidamente homologada no SIMEC?")
    ck2 = st.checkbox("Comitê de Mobilização do SAEB instituído com meta de 85%+ de presença?")
    ck3 = st.checkbox("Lei Estadual do ICMS Educação aprovada e vigente no Estado?")
    ck4 = st.checkbox("Currículo da Rede alinhado à BNCC aprovado no Conselho Municipal/Estadual?")
    ck5 = st.checkbox("Balanços e dados fiscais do SIOPE transmitidos sem inconsistências no sistema do FNDE?")

    prontidao = sum([ck1, ck2, ck3, ck4, ck5]) * 20
    st.progress(prontidao / 100.0, text=f"Grau de Conformidade para Habilitação: {prontidao}%")

    if prontidao == 100:
        st.success("🎉 Parabéns! A rede atende a todos os requisitos fundamentais para habilitação plena ao VAAR.")
    elif prontidao >= 60:
        st.warning("⚠️ Atenção: Há pendências críticas que podem desabilitar a rede no próximo ciclo.")
    else:
        st.error("🚨 Alerta Vermelho: Alto risco de desabilitação e perda total do VAAR.")
