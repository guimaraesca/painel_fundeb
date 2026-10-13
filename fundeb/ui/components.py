"""Componentes visuais reutilizáveis de alta fidelidade e ergonomia (SOLID - SRP)."""
from __future__ import annotations

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
) -> None:
    """Renderiza um card moderno de métrica formatado em HTML."""
    delta_html = ""
    if delta:
        cor = "#16A34A" if delta_color == "normal" and not delta.startswith("-") else "#DC2626"
        delta_html = f"<div style='font-size: 0.8rem; font-weight: 600; color: {cor}; margin-top: 4px;'>{delta}</div>"

    html = f"""
    <div class="metric-card">
        <div class="title">{title}</div>
        <div class="value">{value}</div>
        {delta_html}
        <div class="subtitle">{subtitle}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def status_badge(status: str) -> str:
    """Retorna tag HTML de badge colorida com base no status."""
    s = str(status).strip()
    if s in ("Habilitado", "Beneficiário", "Manteve", "Cumprida", "OK", "Sim"):
        cls = "badge-green"
    elif s in ("Pendente", "Atenção", "Cuidado"):
        cls = "badge-amber"
    elif s in ("Não habilitado", "Perdeu", "Reprovada", "Crítica", "Não", "Fora"):
        cls = "badge-red"
    elif s in ("Entrou", "Estadual", "Municipal"):
        cls = "badge-blue"
    else:
        cls = "badge-gray"
    return f"<span class='badge {cls}'>{s}</span>"
