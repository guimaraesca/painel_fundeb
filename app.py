"""Painel Estratégico FUNDEB & Complementação VAAR 2026.

Entrypoint principal para execução local e deployment no Streamlit Community Cloud (streamlit.app).
Arquitetura orientada a princípios SOLID (DIP, SRP, ISP).
"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from fundeb.data.repository import JsonDataRepository
from fundeb.services.analytics import AnalyticsService
from fundeb.services.simulator import SimulatorService
from fundeb.ui.theme import apply_theme
from fundeb.ui.views.home_view import render_home_view
from fundeb.ui.views.condicionalidades_view import render_condicionalidades_view
from fundeb.ui.views.mapas_view import render_mapas_view
from fundeb.ui.views.ranking_view import render_ranking_view
from fundeb.ui.views.historico_view import render_historico_view
from fundeb.ui.views.simulador_view import render_simulador_view
from fundeb.ui.views.boletim_view import render_boletim_view
from fundeb.ui.views.qualidade_view import render_qualidade_view

# 1. Configuração da Página Streamlit (Widescreen nativo)
st.set_page_config(
    page_title="Painel FUNDEB & VAAR 2026",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Aplicação do Tema Visual Moderno e CSS Responsivo
apply_theme()


# 3. Cache de Infraestrutura e Dados (IoC / Dependency Injection)
@st.cache_resource(show_spinner=False)
def carregar_repositorio() -> JsonDataRepository:
    return JsonDataRepository()


@st.cache_data(show_spinner="Carregando base auditada do FUNDEB...")
def carregar_dataframe() -> pd.DataFrame:
    repo = carregar_repositorio()
    return repo.entes()


@st.cache_resource(show_spinner=False)
def carregar_servicos(_df: pd.DataFrame) -> tuple[AnalyticsService, SimulatorService]:
    analytics = AnalyticsService(_df)
    simulator = SimulatorService(_df)
    return analytics, simulator


def main() -> None:
    repo = carregar_repositorio()
    df = carregar_dataframe()
    analytics, simulator = carregar_servicos(df)

    # Sidebar: Navegação Executiva
    with st.sidebar:
        st.markdown("## 📊 FUNDEB & VAAR")
        st.caption("Ciclo de Distribuição 2026 &middot; Dados Oficiais FNDE/Inep")

        menu = st.radio(
            "Navegação:",
            options=[
                "🏠 Início & Guia de Leitura",
                "📄 Boletim Executivo (2 Páginas)",
                "⚖️ Condicionalidades & Funil",
                "🗺️ Mapas em 3 Fases",
                "🏆 Ranking por UF",
                "📈 Linha Histórica & Como Agir",
                "🧮 Simulador VAAR (Estadual vs Municipal)",
                "🛡️ Observabilidade & Qualidade dos Dados",
            ],
            index=0,
        )

        st.markdown("---")
        st.markdown(
            """
            **Auditabilidade & Observabilidade dos Dados:**
            - 5.596 Entes avaliados (26 Estados + DF + 5.569 Municípios)
            - 5 Pilares: Freshness, Volume, Distribution, Schema e Lineage
            - Lei nº 14.113/2020 &bull; EC 108/2020
            - NT Inep 23/2022 &amp; NT 5/2024
            - Zero dados sintéticos ou populados artificialmente
            """
        )

    # Roteamento de Visualizações
    if "Início" in menu:
        render_home_view(analytics)
    elif "Boletim Executivo" in menu:
        render_boletim_view(df, simulator)
    elif "Condicionalidades" in menu:
        render_condicionalidades_view(analytics)
    elif "Mapas" in menu:
        render_mapas_view(df, repo)
    elif "Ranking" in menu:
        render_ranking_view(analytics)
    elif "Linha Histórica" in menu:
        render_historico_view(df)
    elif "Simulador" in menu:
        render_simulador_view(simulator, df)
    elif "Observabilidade" in menu or "Qualidade" in menu:
        render_qualidade_view(repo)


if __name__ == "__main__":
    main()
