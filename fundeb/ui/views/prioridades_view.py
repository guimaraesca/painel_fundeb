"""Tela — Prioridades (Pareto): maior retorno de VAAR com menor esforço.

Aplica a Lei de Pareto (80/20) ao ganho potencial de VAAR por município de um
estado: ordena as cidades pelo retorno possível e evidencia a "minoria vital"
que concentra a maior parte do ganho — cruzando com o ESFORÇO (nº de
condicionalidades a cumprir) para apontar os ganhos rápidos (quick wins).
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from fundeb.services.simulator import SimulatorService
from fundeb.domain.territorio import UF_CODIGO
from fundeb.ui.components import metric_card, format_currency, format_int
from fundeb.ui.charts import chart_pareto_vaar


def render_prioridades_view(simulator: SimulatorService, df: pd.DataFrame) -> None:
    st.markdown("## 🎯 Prioridades (Pareto) — maior retorno de VAAR, menor esforço")
    st.caption("Lei de Pareto aplicada ao ganho potencial de VAAR por município, cruzado com o esforço (condicionalidades a cumprir).")

    c1, c2 = st.columns([1, 1])
    with c1:
        esfera = st.radio("Esfera:", ["Municipal", "Estadual"], horizontal=True, index=0)
    uf = None
    if esfera == "Municipal":
        with c2:
            ufs = sorted(df[df["rede"] == "Municipal"]["uf"].unique())
            uf = st.selectbox("Estado (UF):", ufs, index=ufs.index("RN") if "RN" in ufs else 0)

    comp = simulator.comparativo_entes_potencial(esfera, uf)
    comp = comp.merge(df[["ibge", "n_reprovacoes"]], on="ibge", how="left")
    comp = comp.rename(columns={"delta_salto": "ganho_potencial"})

    titulo_loc = f"{uf}" if esfera == "Municipal" else "redes estaduais"
    d_pos = comp[comp["ganho_potencial"] > 0]
    total_pot = float(d_pos["ganho_potencial"].sum())
    quick_wins = d_pos[(d_pos["n_reprovacoes"] == 1)]

    fig, n_vital, n_total = chart_pareto_vaar(
        comp, "nome", "ganho_potencial", "n_reprovacoes",
        f"Pareto do ganho potencial de VAAR — {titulo_loc}",
    )

    pct_cidades = (n_vital / n_total * 100) if n_total else 0
    st.markdown(
        f"""
        <div style="background:#F8FAFC;border-left:4px solid #1E40AF;border-radius:0 8px 8px 0;
        padding:12px 16px;margin:6px 0 12px 0;">
        <b>Leitura de Pareto:</b> apenas <b>{n_vital}</b> de {n_total} cidades
        ({pct_cidades:.0f}%) concentram <b>80% de todo o ganho potencial de VAAR</b> em {titulo_loc}.
        Priorizar essas — começando pelas de <b>1 condicionalidade a cumprir</b> (verde) — entrega
        o maior retorno com o menor esforço.
        </div>
        """,
        unsafe_allow_html=True,
    )

    k1, k2, k3 = st.columns(3)
    with k1:
        metric_card("Ganho potencial total", format_currency(total_pot), f"em {titulo_loc}")
    with k2:
        metric_card("Minoria vital (80%)", f"{format_int(n_vital)} cidades", f"de {format_int(n_total)} com potencial")
    with k3:
        metric_card("Ganhos rápidos", f"{format_int(len(quick_wins))} cidades",
                    f"a 1 condicionalidade · {format_currency(float(quick_wins['ganho_potencial'].sum()))}")

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption("Barras coloridas por esforço: 🟢 1 condicionalidade (quick win) · 🟠 2 · 🔴 3+ · verde-escuro = já habilitada. Linha preta = % acumulado (referência pontilhada em 80%).")

    # Tabela de ganhos rápidos (maior retorno com menor esforço)
    st.markdown("### Ganhos rápidos — prioridade de abordagem")
    st.caption("Cidades fora do VAAR a apenas 1 condicionalidade, ordenadas pelo maior ganho potencial.")
    qw = quick_wins[quick_wins["vaar_atual"] == 0].sort_values("ganho_potencial", ascending=False).head(20)
    if qw.empty:
        st.info("Nenhuma cidade a exatamente 1 condicionalidade nesta seleção.")
    else:
        tabela = qw[["nome", "ganho_potencial"]].copy()
        tabela["ganho_potencial"] = tabela["ganho_potencial"].round(0)
        tabela = tabela.rename(columns={"nome": "Município", "ganho_potencial": "Ganho potencial VAAR (R$)"})
        st.dataframe(
            tabela, use_container_width=True, hide_index=True,
            column_config={"Ganho potencial VAAR (R$)": st.column_config.NumberColumn(format="R$ %.0f")},
        )
