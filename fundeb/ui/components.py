"""Componentes visuais reutilizáveis de alta fidelidade e ergonomia (SOLID - SRP)."""
from __future__ import annotations

from typing import Any
import streamlit as st


def format_currency(valor: float | int | None) -> str:
    """Formata valor em Reais (BRL) no padrão ABNT (milhar '.', decimal ',')."""
    if valor is None or (isinstance(valor, float) and (valor != valor or valor == 0.0)):
        return "R$ 0,00"
    sinal = "-" if valor < 0 else ""
    abs_v = abs(valor)
    if abs_v >= 1e9:
        val_str = f"{abs_v / 1e9:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{sinal}R$ {val_str} bi"
    if abs_v >= 1e6:
        val_str = f"{abs_v / 1e6:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{sinal}R$ {val_str} mi"
    return format_currency_full(valor)


def format_currency_full(valor: float | int | None) -> str:
    """Formata valor monetário completo no padrão ABNT (ex: R$ 1.234.567,89)."""
    if valor is None or (isinstance(valor, float) and valor != valor):
        return "—"
    sinal = "-" if valor < 0 else ""
    abs_v = abs(valor)
    fmt = f"{abs_v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sinal}R$ {fmt}"


def format_percent(valor: float | int | None, decimais: int = 1) -> str:
    """Formata porcentagem no padrão ABNT com vírgula decimal (ex: 15,8%)."""
    if valor is None or (isinstance(valor, float) and valor != valor):
        return "—"
    fmt = f"{valor:,.{decimais}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{fmt}%"


def format_int(valor: int | float | None) -> str:
    """Formata número inteiro no padrão ABNT com ponto de milhar (ex: 1.234)."""
    if valor is None or (isinstance(valor, float) and valor != valor):
        return "—"
    return f"{int(round(valor)):,}".replace(",", ".")


def format_decimal(valor: float | int | None, decimais: int = 2) -> str:
    """Formata número decimal no padrão ABNT (ex: 3,14 ou 1.250,50)."""
    if valor is None or (isinstance(valor, float) and valor != valor):
        return "—"
    fmt = f"{valor:,.{decimais}f}"
    return fmt.replace(",", "X").replace(".", ",").replace("X", ".")


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
