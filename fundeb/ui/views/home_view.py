"""Página Inicial: Guia Executivo de Leitura e Apresentação do Painel FUNDEB/VAAR."""
from __future__ import annotations

import streamlit as st
import pandas as pd

from fundeb.services.analytics import AnalyticsService
from fundeb.ui.components import metric_card, format_currency, format_percent, format_int


def render_home_view(analytics: AnalyticsService) -> None:
    resumo = analytics.resumo_nacional()

    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%); padding: 28px 32px; border-radius: 12px; color: white; margin-bottom: 24px;">
            <div style="font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; opacity: 0.85;">
                Painel Estratégico &middot; Ciclo de Distribuição 2026
            </div>
            <h1 style="color: white; margin: 8px 0 12px 0; font-size: 2.2rem; font-weight: 800;">
                FUNDEB &amp; Complementação VAAR
            </h1>
            <p style="font-size: 1.05rem; opacity: 0.95; max-width: 950px; line-height: 1.5; margin: 0;">
                Diagnóstico de habilitação, análise de condicionalidades (Art. 14, § 1º da Lei nº 14.113/2020),
                evolução histórica dos recursos e simulador de impacto financeiro por rede estadual e municipal.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Botões rápidos para tópicos / Modo Apresentação
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown(
            "**Guia de Leitura Rápida:** Navegue pelos tópicos abaixo ou utilize a barra superior de abas."
        )
    with col_t2:
        modo_apresentacao = st.checkbox("💻 Modo Slide / Apresentação", value=False)

    if modo_apresentacao:
        st.info("💡 **Modo Apresentação ativado:** Utilize F11 no navegador para tela cheia. O layout expande os gráficos para projeção em reuniões e slides executivos.")

    # Linha 1 de KPIs Nacionais Executivos
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        metric_card(
            title="Complementação VAAR 2026",
            value=format_currency(resumo.total_vaar_reais),
            subtitle=f"{format_int(resumo.beneficiarios)} redes beneficiárias ({format_percent(resumo.pct_beneficiarios)})",
        )
    with k2:
        metric_card(
            title="Redes Habilitadas",
            value=f"{format_int(resumo.habilitados)} / {format_int(resumo.total_entes)}",
            subtitle=f"{format_percent(resumo.pct_habilitados)} de aprovação nas 5 condicionalidades",
        )
    with k3:
        metric_card(
            title="Gargalo de Habilitação",
            value=f"{format_int(resumo.nao_habilitados)} redes",
            subtitle=f"{format_percent(resumo.pct_nao_habilitados)} reprovadas em ao menos 1 condicionalidade",
            delta="Perderam elegibilidade",
            delta_color="red",
        )
    with k4:
        metric_card(
            title="Total Complementação União",
            value=format_currency(resumo.total_uniao_reais),
            subtitle=f"VAAF: {format_currency(resumo.total_vaaf_reais)} | VAAT: {format_currency(resumo.total_vaat_reais)}",
        )

    st.markdown("---")

    # Mapa mental dos tópicos do painel
    st.subheader("📌 Tópicos e Estrutura do Painel")

    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown(
            """
            #### 1. Condicionalidades & Funil
            * **Art. 14, § 1º (I a V)**: Funil oficial das 2.506 redes não habilitadas.
            * **Identificação de Gargalos**: Cond. III (1.930 reprovações) e Cond. I (575 reprovações).
            * **Texto da Lei & Como Cumprir**: Orientações normativas para cada inciso.
            """
        )
        st.markdown(
            """
            #### 2. Mapas Interativos em 3 Fases
            * **Fase 1 (Brasil)**: Visão de todas as UFs.
            * **Fase 2 (Regiões)**: Análise comparativa regional.
            * **Fase 3 (Municípios)**: Visualização detalhada e enxuta por ente municipal.
            """
        )

    with t2:
        st.markdown(
            """
            #### 3. Ranking de UFs com Micrográficos
            * Tabela comparativa com mapa de calor por cores e números nas células.
            * Métricas acionáveis e filtros para isolar vulnerabilidades por estado.
            * Taxa de retenção vs perda de repasses do ciclo 2025 para 2026.
            """
        )
        st.markdown(
            """
            #### 4. Série Histórica & Como Agir
            * **Rampa da EC 108/2020**: Evolução de 12% para 23% da complementação federal.
            * **Censo Escolar 2017–2023**: Série histórica real de matrículas.
            * **Matriz de Intervenção**: Passos práticos para recuperar o VAAR nos próximos ciclos.
            """
        )

    with t3:
        st.markdown(
            r"""
            #### 5. Simulador VAAR (Estadual vs Municipal)
            * **Diferenciação Estrita**:
              * **Estadual**: Etapa de atendimento avaliada no Ensino Médio.
              * **Municipal**: Etapa avaliada na Educação Infantil.
            * **Cenários do IEE & Sliders**: Sensibilidade matemática alinhada ao Simulador-VAAR-PI (NT 23/2022).
            * **Memória de Cálculo**: Fórmulas $w = 2 - e^{-4 \cdot \text{IND}}$ explicadas passo a passo.
            """
        )
        st.markdown(
            """
            #### 6. Qualidade & Proveniência
            * **Transparência Radical**: 100% dados oficiais (FNDE, Inep, SIOPE, Censo).
            * **Zero Imputação Fake**: Campos sem publicação permanecem `—`.
            * **Auditoria Criptográfica**: Hash SHA-256 e testes de fechamento contábil.
            """
        )

    st.markdown("---")

    # Resumo da Transição 2025 -> 2026
    st.subheader("🔄 Dinâmica de Transição dos Entes (Ciclo 2025 ➔ 2026)")
    c_tr1, c_tr2, c_tr3, c_tr4 = st.columns(4)
    with c_tr1:
        metric_card(
            "Manteve VAAR",
            f"{format_int(resumo.transicao_manteve)} redes",
            "Receberam em 2025 e mantiveram em 2026",
            delta="Estabilidade",
        )
    with c_tr2:
        metric_card(
            "Perdeu VAAR",
            f"{format_int(resumo.transicao_perdeu)} redes",
            "Receberam em 2025, mas perderam em 2026",
            delta="Atenção",
            delta_color="red",
        )
    with c_tr3:
        metric_card(
            "Entrou no VAAR",
            f"{format_int(resumo.transicao_entrou)} redes",
            "Não recebiam em 2025 e conquistaram em 2026",
            delta="Novo Repasse",
        )
    with c_tr4:
        metric_card(
            "Sem VAAR (Fora)",
            f"{format_int(resumo.transicao_fora)} redes",
            "Não receberam em 2025 nem em 2026",
            subtitle="Potencial de captação futura",
        )
