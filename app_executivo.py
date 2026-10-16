"""Painel FUNDEB & VAAR 2026 — Edição Executiva.

Versão enxuta e direta da aplicação completa (``app.py``), com o mesmo propósito
e as MESMAS bases de dados auditadas (reutiliza ``JsonDataRepository`` e
``AnalyticsService``). Três telas de decisão em vez de oito, conclusão antes da
evidência (BLUF) e foco em "onde agir e quanto custa não agir".

Executar:  streamlit run app_executivo.py
"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from fundeb.data.repository import JsonDataRepository
from fundeb.services.analytics import AnalyticsService
from fundeb.ui.exec_theme import apply_exec_theme
from fundeb.ui.views.executivo_view import render_executivo_view

st.set_page_config(
    page_title="FUNDEB & VAAR 2026 — Executivo",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_exec_theme()


@st.cache_resource(show_spinner=False)
def carregar_repositorio() -> JsonDataRepository:
    return JsonDataRepository()


@st.cache_data(show_spinner="Carregando base auditada do FUNDEB...")
def carregar_dataframe() -> pd.DataFrame:
    return carregar_repositorio().entes()


@st.cache_resource(show_spinner=False)
def carregar_analytics(_df: pd.DataFrame) -> AnalyticsService:
    return AnalyticsService(_df)


def main() -> None:
    df = carregar_dataframe()
    analytics = carregar_analytics(df)

    with st.sidebar:
        st.markdown("## 🎯 FUNDEB & VAAR")
        st.caption("Edição Executiva · Ciclo 2026 · FNDE/Inep")

        secao = st.radio(
            "Navegação:",
            options=[
                "📌 Sumário Executivo",
                "🗺️ Prioridades por UF",
                "✅ Plano de Ação & Gargalos",
            ],
            index=0,
        )

        st.markdown("---")
        st.caption(
            "Mesma base auditada da versão completa — 5.596 redes, dados oficiais, "
            "zero valores sintéticos. Para metodologia, simulador e mapas, use o painel completo (`app.py`)."
        )

    render_executivo_view(analytics, secao)


if __name__ == "__main__":
    main()
