"""Tela — Programas Suplementares (PNAE/PNATE) e impacto da subcontagem.

PNAE e PNATE são repasses da União **proporcionais à matrícula do Censo Escolar
(Educacenso)**. Subcontagem de alunos reduz esses recursos — além do Fundeb/VAAR.
Esta tela expõe os valores per capita oficiais e um simulador do impacto
financeiro da subcontagem (reproduz o caso do RN).
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from fundeb.programas.suplementares import (
    PNAE_PER_CAPITA_DIA, PNAE_ETAPA_ROTULO, PNAE_DIAS_ATENDIMENTO,
    PNATE_PER_CAPITA_ANO_MIN, PNATE_PER_CAPITA_ANO_MAX,
    pnae_custo_aluno_ano, impacto_subcontagem,
)
from fundeb.ui.components import metric_card, format_currency, format_int, format_currency_full


def render_programas_view() -> None:
    st.markdown("## 🍎 Programas Suplementares — PNAE & PNATE")
    st.caption("Repasses da União proporcionais à matrícula do Censo Escolar (Educacenso).")

    st.markdown(
        """
        <div style="background:#F8FAFC;border-left:4px solid #1E40AF;border-radius:0 8px 8px 0;
        padding:12px 16px;margin:6px 0 14px 0;">
        <b>Por que isto importa:</b> o <b>PNAE</b> (alimentação escolar) e o <b>PNATE</b>
        (transporte escolar rural) são calculados <b>por aluno matriculado no Censo</b>.
        Quando a rede não cadastra corretamente seus estudantes no Educacenso, perde repasses
        nestes dois programas — <b>e também no Fundeb e no VAAR</b>. Foi o que ocorreu no Rio
        Grande do Norte (≈ 4,48 mil alunos não cadastrados em 2025).
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------------------------------- valores per capita oficiais
    st.markdown("### Quanto cada aluno gera por ano")
    col_a, col_b = st.columns([1.2, 1.0])
    with col_a:
        linhas = [
            {"Etapa / modalidade": PNAE_ETAPA_ROTULO[e],
             "Per capita/dia": format_currency_full(v),
             "PNAE por aluno/ano": format_currency_full(pnae_custo_aluno_ano(e))}
            for e, v in PNAE_PER_CAPITA_DIA.items() if e != "integral"
        ]
        st.markdown("**PNAE** — Res. CD/FNDE nº 1/2026 · base de " + f"{PNAE_DIAS_ATENDIMENTO} dias de atendimento")
        st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)
    with col_b:
        st.markdown("**PNATE** — Res. CD/FNDE nº 14/2026")
        st.markdown(
            f"Por **aluno rural transportado/ano**, entre "
            f"**{format_currency_full(PNATE_PER_CAPITA_ANO_MIN)}** e "
            f"**{format_currency_full(PNATE_PER_CAPITA_ANO_MAX)}** "
            "(varia por município pelo Fator de Necessidade de Recursos — FNRM)."
        )
        st.caption(
            "Observação: PNAE/PNATE são a parcela menor da perda por subcontagem; "
            "o Fundeb (VAAF/VAAT) e o VAAR costumam responder pela maior parte."
        )

    st.markdown("---")

    # ---------------------------------------------- simulador de subcontagem
    st.markdown("### Simulador — impacto da subcontagem no Educacenso")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        alunos = st.number_input("Alunos não cadastrados", min_value=0, max_value=5_000_000,
                                 value=4480, step=100)
    with c2:
        opcoes = {"Faixa (todas as etapas)": None,
                  "Ensino Fundamental": "fundamental", "Ensino Médio": "medio",
                  "Pré-escola": "pre", "Creche": "creche", "EJA": "eja"}
        etapa_lbl = st.selectbox("Etapa predominante", list(opcoes.keys()), index=0)
        etapa = opcoes[etapa_lbl]
    with c3:
        pct_rural = st.slider("% em área rural (PNATE)", 0, 100, 15)
    with c4:
        anos = st.number_input("Anos acumulados", min_value=1, max_value=10, value=3, step=1)

    imp = impacto_subcontagem(int(alunos), etapa=etapa, pct_rural=float(pct_rural))

    def _faixa(lo: float, hi: float) -> str:
        return format_currency(lo) if abs(hi - lo) < 1 else f"{format_currency(lo)} – {format_currency(hi)}"

    m1, m2, m3 = st.columns(3)
    with m1:
        metric_card("PNAE / ano", _faixa(imp.pnae_min, imp.pnae_max),
                    "alimentação escolar")
    with m2:
        metric_card("PNATE / ano", _faixa(imp.pnate_min, imp.pnate_max),
                    f"{pct_rural}% rural transportado")
    with m3:
        metric_card("PNAE + PNATE / ano", _faixa(imp.total_min, imp.total_max),
                    "perda anual estimada")

    metric_card(
        f"Acumulado em {anos} ano(s)",
        _faixa(imp.total_min * anos, imp.total_max * anos),
        "soma do período — apenas PNAE + PNATE (não inclui Fundeb/VAAR)",
    )

    st.caption(
        f"Base: {format_int(alunos)} alunos · "
        + ("faixa entre a menor etapa regular e a creche" if etapa is None
           else f"etapa {etapa_lbl.lower()} ({format_currency_full(pnae_custo_aluno_ano(etapa))}/aluno/ano)")
        + f" · PNATE sobre {pct_rural}% rurais. Valores per capita oficiais; "
        "o PNATE varia por município."
    )

    st.info(
        "Para a perda **total** (incluindo Fundeb/VAAF/VAAT e VAAR), consulte as telas de "
        "financiamento e o relatório específico do ente — o VAAR, inclusive, pode zerar quando "
        "a rede reprova condicionalidades ligadas à cobertura e participação (Saeb)."
    )
