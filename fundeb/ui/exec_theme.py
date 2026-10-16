"""Tema visual da versão Executiva.

Reaproveita o CSS base do painel completo (``theme.apply_theme``) e acrescenta
uma camada enxuta, de alto contraste e densidade informacional controlada,
voltada para leitura rápida por tomadores de decisão (BLUF — Bottom Line Up Front).
Nenhuma regra de negócio aqui; apenas apresentação.
"""
from __future__ import annotations

import streamlit as st

from fundeb.ui.theme import apply_theme as _apply_base_theme

EXEC_CSS = """
<style>
/* Faixa executiva: título-resumo de abertura */
.exec-hero {
    background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
    color: #F8FAFC;
    border-radius: 14px;
    padding: 22px 28px;
    margin: 4px 0 18px 0;
}
.exec-hero h1 {
    color: #FFFFFF !important;
    font-size: 1.55rem !important;
    margin: 0 0 4px 0 !important;
    letter-spacing: -0.02em !important;
}
.exec-hero p {
    color: #CBD5E1 !important;
    font-size: 0.95rem !important;
    margin: 0 !important;
}
.exec-hero .tag {
    display: inline-block;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.22);
    color: #E2E8F0;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 9999px;
    margin-top: 10px;
    letter-spacing: 0.04em;
}

/* Linha de leitura executiva (BLUF) — a conclusão vem antes da evidência */
.exec-bluf {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-left: 5px solid #1E40AF;
    border-radius: 0 10px 10px 0;
    padding: 14px 18px;
    margin: 6px 0 16px 0;
    font-size: 1.0rem;
    color: #0F172A;
    line-height: 1.5;
}
.exec-bluf b { color: #1E3A8A; }

/* Cartões de ação prioritária */
.exec-action {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
    display: flex;
    gap: 14px;
    align-items: flex-start;
}
.exec-action .rank {
    flex: 0 0 auto;
    width: 30px;
    height: 30px;
    border-radius: 8px;
    background: #1E40AF;
    color: #fff;
    font-weight: 800;
    font-size: 0.95rem;
    display: flex;
    align-items: center;
    justify-content: center;
}
.exec-action .body { flex: 1 1 auto; }
.exec-action .body .t {
    font-weight: 700;
    color: #0F172A;
    font-size: 0.98rem;
    margin-bottom: 2px;
}
.exec-action .body .d {
    color: #475569;
    font-size: 0.86rem;
    line-height: 1.45;
}
.exec-action .impact {
    flex: 0 0 auto;
    text-align: right;
    min-width: 92px;
}
.exec-action .impact .n {
    font-weight: 800;
    font-size: 1.15rem;
    color: #B91C1C;
}
.exec-action .impact .l {
    font-size: 0.7rem;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.exec-section-title {
    font-size: 1.05rem;
    font-weight: 800;
    color: #0F172A;
    margin: 18px 0 2px 0;
    letter-spacing: -0.01em;
}
.exec-section-sub {
    color: #64748B;
    font-size: 0.85rem;
    margin-bottom: 10px;
}

/* Rodapé de proveniência discreto */
.exec-source {
    color: #94A3B8;
    font-size: 0.75rem;
    border-top: 1px solid #E2E8F0;
    padding-top: 10px;
    margin-top: 22px;
}
</style>
"""


def apply_exec_theme() -> None:
    """Aplica o tema base e, em seguida, a camada executiva."""
    _apply_base_theme()
    st.markdown(EXEC_CSS, unsafe_allow_html=True)
