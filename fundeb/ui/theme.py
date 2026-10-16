"""Estilos CSS e temas para visualização widescreen e modo apresentação."""
import streamlit as st

CUSTOM_CSS = """
<style>
/* 1. Otimização Widescreen e Resoluções Variadas */
.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 98% !important;
}

@media (max-width: 1366px) {
    .block-container {
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
        max-width: 100% !important;
    }
}

@media (max-width: 768px) {
    .block-container {
        padding-top: 0.8rem !important;
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
    }
}

/* 2. Remoção Estrita de Sombreamento em Textos (Todas as Abas e Componentes) */
*, *::before, *::after {
    text-shadow: none !important;
    -webkit-font-smoothing: antialiased !important;
    -moz-osx-font-smoothing: grayscale !important;
}

h1, h2, h3, h4, h5, h6, p, span, div, label, input, button, select, textarea,
[data-testid="stMetricValue"], [data-testid="stMetricLabel"], [data-testid="stMarkdownContainer"] * {
    text-shadow: none !important;
    filter: none !important;
}

/* 3. Tipografia moderna e títulos nítidos */
h1, h2, h3, h4 {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: #0F172A !important;
}

/* 4. Cards de Métricas Premium (Alta Nitidez e Contraste Sóbrio) */
.metric-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 14px 18px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    transition: transform 0.15s ease, border-color 0.15s ease;
    margin-bottom: 10px;
}
.metric-card:hover {
    border-color: #CBD5E1;
    transform: translateY(-1px);
}
.metric-card .title {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    color: #64748B;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
    text-shadow: none !important;
}
.metric-card .value {
    font-size: 1.65rem;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.2;
    text-shadow: none !important;
}
.metric-card .subtitle {
    font-size: 0.78rem;
    color: #64748B;
    margin-top: 4px;
    text-shadow: none !important;
}

@media (max-width: 1200px) {
    .metric-card .value {
        font-size: 1.35rem !important;
    }
}

/* 5. Badges e Pílulas de Status Nítidas */
.badge {
    display: inline-block;
    padding: 3px 8px;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 9999px;
    margin-right: 4px;
    text-shadow: none !important;
}
.badge-green { background-color: #DCFCE7; color: #166534; border: 1px solid #86EFAC; }
.badge-amber { background-color: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; }
.badge-red   { background-color: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }
.badge-blue  { background-color: #DBEAFE; color: #1E40AF; border: 1px solid #93C5FD; }
.badge-gray  { background-color: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; }

/* 6. Fórmulas e boxes explicativos */
.formula-box {
    background: #F8FAFC;
    border-left: 4px solid #2563EB;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 12px 0;
    border-top: 1px solid #E2E8F0;
    border-right: 1px solid #E2E8F0;
    border-bottom: 1px solid #E2E8F0;
}

/* 7. Modo Apresentação / Impressão */
@media print {
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    header, footer, [data-testid="stSidebar"] {
        display: none !important;
    }
}

/* 8. Prevenção Sistêmica de Truncamento em Métricas e Cards (Issue #5) */
[data-testid="stMetric"] {
    width: 100% !important;
    overflow: visible !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.82rem !important;
    line-height: 1.25 !important;
    white-space: normal !important;
    word-break: break-word !important;
}
[data-testid="stMetricLabel"] p {
    font-size: 0.82rem !important;
    white-space: normal !important;
    word-break: break-word !important;
}
[data-testid="stMetricValue"] {
    font-size: clamp(1.02rem, 1.35vw, 1.45rem) !important;
    white-space: normal !important;
    word-break: break-word !important;
    overflow: visible !important;
    text-overflow: clip !important;
    line-height: 1.2 !important;
}
[data-testid="stMetricValue"] div {
    font-size: inherit !important;
    white-space: normal !important;
    word-break: break-word !important;
    overflow: visible !important;
    text-overflow: clip !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.78rem !important;
    white-space: normal !important;
    word-break: break-word !important;
}
[data-testid="stMetricDelta"] div {
    white-space: normal !important;
    word-break: break-word !important;
}
</style>
"""


def apply_theme() -> None:
    """Aplica os estilos CSS na sessão Streamlit."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
