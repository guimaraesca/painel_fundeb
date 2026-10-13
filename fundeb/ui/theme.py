"""Estilos CSS e temas para visualização widescreen e modo apresentação."""
import streamlit as st

CUSTOM_CSS = """
<style>
/* Otimização Widescreen: Reduz espaços em branco laterais e verticais */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 98% !important;
}

/* Tipografia moderna e títulos */
h1, h2, h3 {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}

/* Cards de Métricas Premium */
.metric-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    margin-bottom: 12px;
}
.metric-card:hover {
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    transform: translateY(-1px);
}
.metric-card .title {
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    color: #64748B;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
}
.metric-card .value {
    font-size: 1.75rem;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.2;
}
.metric-card .subtitle {
    font-size: 0.8rem;
    color: #64748B;
    margin-top: 4px;
}

/* Badges e Pílulas de Status */
.badge {
    display: inline-block;
    padding: 3px 8px;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 9999px;
    margin-right: 4px;
}
.badge-green { background-color: #DCFCE7; color: #166534; }
.badge-amber { background-color: #FEF3C7; color: #92400E; }
.badge-red   { background-color: #FEE2E2; color: #991B1B; }
.badge-blue  { background-color: #DBEAFE; color: #1E40AF; }
.badge-gray  { background-color: #F1F5F9; color: #475569; }

/* Fórmulas e boxes explicativos */
.formula-box {
    background: #F8FAFC;
    border-left: 4px solid #2563EB;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 12px 0;
}

/* Modo Apresentação / Slide */
@media print {
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    header, footer, [data-testid="stSidebar"] {
        display: none !important;
    }
}
</style>
"""


def apply_theme() -> None:
    """Aplica os estilos CSS na sessão Streamlit."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
