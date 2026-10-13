"""Componentes visuais reutilizáveis de alta fidelidade e ergonomia (SOLID - SRP)."""
from __future__ import annotations

from typing import Any
import streamlit as st


def format_currency(valor: float | int | None) -> str:
    """Formata valor em Reais (BRL)."""
    if valor is None or (isinstance(valor, float) and (valor != valor or valor == 0.0)):
        return "R$ 0,00"
    if abs(valor) >= 1e9:
        return f"R$ {valor / 1e9:,.2f} bi".replace(",", "X").replace(".", ",").replace("X", ".")
    if abs(valor) >= 1e6:
        return f"R$ {valor / 1e6:,.2f} mi".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_currency_full(valor: float | int | None) -> str:
    """Formata valor completo sem abreviação em milhões/bilhões."""
    if valor is None or (isinstance(valor, float) and valor != valor):
        return "—"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percent(valor: float | int | None, decimais: int = 1) -> str:
    """Formata porcentagem no padrão brasileiro."""
    if valor is None or (isinstance(valor, float) and valor != valor):
        return "—"
    return f"{valor:.{decimais}f}%".replace(".", ",")


def format_int(valor: int | float | None) -> str:
    """Formata número inteiro com separador de milhar."""
    if valor is None or (isinstance(valor, float) and valor != valor):
        return "—"
    return f"{int(valor):,}".replace(",", ".")


def metric_card(
    title: str,
    value: str,
    subtitle: str = "",
    delta: str | None = None,
    delta_color: str = "normal",
    **kwargs: Any,
) -> None:
    """Renderiza um card moderno de métrica nativo do Streamlit (sem vazamento de HTML)."""
    # Proteção caso subtitle tenha sido passado via kwargs ou duplicado
    sub = kwargs.get("sub", subtitle)
    with st.container(border=True):
        st.metric(
            label=title,
            value=value,
            delta=delta,
            delta_color="normal" if delta_color == "normal" else ("inverse" if delta_color == "red" else "off"),
        )
        if sub:
            st.caption(sub)


def status_badge(status: str) -> str:
    """Retorna indicador legível com emoji para status institucional."""
    s = str(status).strip()
    mapa = {
        "Habilitado": "✅ Habilitado",
        "Beneficiário": "🌟 Beneficiário",
        "Não beneficiário": "⚪ Não beneficiário",
        "Manteve": "🔄 Manteve VAAR",
        "Perdeu": "🔻 Perdeu VAAR",
        "Entrou": "🔺 Conquistou VAAR",
        "Fora": "⚪ Fora do VAAR",
        "Cumprida": "✅ Cumprida",
        "OK": "✅ Regular",
        "Sim": "✅ Sim",
        "Não": "❌ Não",
        "Não habilitado": "❌ Desabilitada",
        "Reprovada": "❌ Reprovada",
        "Crítica": "🚨 Crítica",
        "Pendente": "⚠️ Pendente",
        "Estadual": "🏛️ Rede Estadual",
        "Municipal": "🏫 Rede Municipal",
    }
    return mapa.get(s, s)
