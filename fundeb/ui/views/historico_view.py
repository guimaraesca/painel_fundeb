"""Camada Histórica de Recursos e Guia Executivo de Intervenção ('Como Agir').

Aplica os princípios de Stephen Few:
- Séries temporais limpas em escala cronológica sem 3D ou oclusão.
- Small Multiples dentro de um único alcance visual (single eyespan).
- Alta proporção tinta-dado (Data-Ink Ratio).
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from fundeb.domain.legal import RAMPA_COMPLEMENTACAO, FONTE_RAMPA
from fundeb.domain.territorio import REGIOES
from fundeb.ui.charts import chart_time_series, apply_few_theme


def render_historico_view(df: pd.DataFrame) -> None:
    st.subheader("📈 Linha Histórica dos Recursos & Como Agir")
    st.markdown(
        """
        Compreenda a progressão constitucional dos recursos federais do FUNDEB (EC nº 108/2020),
        a dinâmica histórica de matrículas por região e o **roteiro estratégico para qualificar e maximizar os repasses**.
        """
    )

    # ------------------------------------------------------------- BLOCO 1: RAMPA CONSTITUCIONAL
    st.markdown("##### 🏛️ Progressão da Complementação da União ao FUNDEB (2021–2026)")
    st.caption(f"Fonte Oficial: {FONTE_RAMPA} &middot; Proporção sobre a receita total dos fundos")

    dados_rampa = [
        {
            "Ano": ano,
            "VAAF": vaaf,
            "VAAT": vaat,
            "VAAR": vaar,
            "Total União": vaaf + vaat + vaar,
        }
        for ano, (vaaf, vaat, vaar) in sorted(RAMPA_COMPLEMENTACAO.items())
    ]
    df_rampa = pd.DataFrame(dados_rampa)

    col_g, col_t = st.columns([3, 2])
    with col_g:
        series_rampa = [
            ("Total União", "Complementação Total (União)", "#1E3A8A"),
            ("VAAF", "VAAF (Fixo 10 p.p.)", "#2563EB"),
            ("VAAT", "VAAT (Progressivo até 10,5 p.p.)", "#0D9488"),
            ("VAAR", "VAAR (Desempenho até 2,5 p.p.)", "#DC2626"),
        ]
        fig_rampa = chart_time_series(
            df_rampa,
            x_col="Ano",
            series=series_rampa,
            titulo="Evolução Percentual dos Recursos Federais (2021 ➔ 2026)",
            y_title="Pontos Percentuais (%)",
        )
        st.plotly_chart(fig_rampa, use_container_width=True)

    with col_t:
        st.dataframe(
            df_rampa.rename(columns={
                "VAAF": "VAAF (p.p.)",
                "VAAT": "VAAT (p.p.)",
                "VAAR": "VAAR (p.p.)",
                "Total União": "Total União (p.p.)",
            }),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    # ------------------------------------------------------------- BLOCO 2: SMALL MULTIPLES (STEPHEN FEW)
    st.markdown("##### 👥 Small Multiples: Trajetória Histórica das Matrículas por Região (2017–2023)")
    st.caption("Princípio de Stephen Few: múltiplos pequenos gráficos comparativos lado a lado em um único relance visual (*single eyespan*), variando apenas a dimensão geográfica:")

    anos = [a for a in range(2017, 2024)]
    cols_anos = [f"mat_iee_{a}" for a in anos]

    # Agregar soma de matrículas reais por região
    df_reg_mats = df.groupby("regiao")[cols_anos].sum().reset_index()

    cols_sm = st.columns(len(REGIOES))
    for col_ui, reg in zip(cols_sm, REGIOES):
        sub = df_reg_mats[df_reg_mats["regiao"] == reg]
        if not sub.empty:
            vals = [float(sub[f"mat_iee_{a}"].iloc[0]) for a in anos]
            # Variação acumulada 2017 -> 2023
            var_pct = ((vals[-1] - vals[0]) / vals[0] * 100.0) if vals[0] > 0 else 0.0

            fig_sm = go.Figure()
            fig_sm.add_trace(
                go.Scatter(
                    x=anos,
                    y=vals,
                    mode="lines+markers",
                    line=dict(color="#1E40AF" if var_pct >= 0 else "#DC2626", width=2),
                    marker=dict(size=4),
                    hoverinfo="x+y",
                )
            )
            fig_sm.update_layout(
                title=dict(text=f"<b>{reg}</b> ({var_pct:+.1f}%)", font=dict(size=12, color="#0F172A")),
                height=160,
                margin=dict(l=5, r=5, t=28, b=10),
                showlegend=False,
            )
            fig_sm.update_xaxes(showgrid=False, tickmode="array", tickvals=[2017, 2020, 2023], ticktext=["'17", "'20", "'23"])
            fig_sm.update_yaxes(showgrid=True, gridcolor="#F1F5F9", tickformat="~s")
            apply_few_theme(fig_sm, show_x_grid=False, show_y_grid=True)

            with col_ui:
                st.plotly_chart(fig_sm, use_container_width=True)

    st.markdown("---")

    # ------------------------------------------------------------- BLOCO 3: COMO AGIR
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

    # ------------------------------------------------------------- BLOCO 4: CHECKLIST INTERATIVO
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
