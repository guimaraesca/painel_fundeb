"""Camada Histórica de Recursos e Guia Executivo de Intervenção ('Como Agir').

Aplica os princípios de Stephen Few:
- Séries temporais limpas em escala cronológica sem 3D ou oclusão.
- Small Multiples dentro de um único alcance visual (single eyespan).
- Alta proporção tinta-dado (Data-Ink Ratio).
- Padrão estrito de formatação numérica ABNT (vírgula decimal, ponto de milhar).
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from fundeb.domain.legal import RAMPA_COMPLEMENTACAO, FONTE_RAMPA
from fundeb.domain.territorio import REGIOES, REGIAO_POR_UF, UF_CODIGO
from fundeb.ui.components import (
    metric_card,
    format_currency,
    format_currency_full,
    format_percent,
    format_int,
    format_decimal,
)
from fundeb.ui.charts import (
    chart_time_series,
    chart_progressao_uniao,
    apply_few_theme,
)


def render_historico_view(df: pd.DataFrame) -> None:
    st.subheader("📈 Linha Histórica dos Recursos & Como Agir")
    st.markdown(
        """
        Compreenda a progressão constitucional dos recursos federais do FUNDEB (EC nº 108/2020),
        a dinâmica histórica de matrículas por região e o **roteiro estratégico para qualificar e maximizar os repasses**.
        """
    )

    # ------------------------------------------------------------- BLOCO 1: PROGRESSÃO DA COMPLEMENTAÇÃO DA UNIÃO (2021–2026) POR REGIÃO E ESTADO
    st.markdown("##### 🏛️ Progressão da Complementação da União ao FUNDEB (2021–2026) por Região e Estado")
    st.caption(f"Fundamentação Jurídica: {FONTE_RAMPA} &middot; Rampa progressiva de 12% a 23% sobre as receitas totais dos fundos")

    c_esc, c_filt = st.columns([3, 4])
    with c_esc:
        escala_prog = st.segmented_control(
            "Recorte Territorial:",
            options=["📍 Por Região", "🏙️ Por Estado (UF)", "🇧🇷 Brasil (Nacional)"],
            default="📍 Por Região",
        )
    with c_filt:
        if escala_prog == "📍 Por Região":
            territorio_sel = st.selectbox(
                "Selecione a Região:",
                options=list(REGIOES),
                index=list(REGIOES).index("Nordeste") if "Nordeste" in REGIOES else 0,
                key="prog_regiao_sel",
            )
            df_sub = df[df["regiao"] == territorio_sel]
            nome_territorio = f"Região {territorio_sel}"
        elif escala_prog == "🏙️ Por Estado (UF)":
            ufs_ordenadas = sorted(list(UF_CODIGO.keys()))
            territorio_sel = st.selectbox(
                "Selecione o Estado (UF):",
                options=ufs_ordenadas,
                index=ufs_ordenadas.index("PI") if "PI" in ufs_ordenadas else 0,
                key="prog_uf_sel",
            )
            df_sub = df[df["uf"] == territorio_sel]
            nome_territorio = f"Estado ({territorio_sel})"
        else:
            df_sub = df
            nome_territorio = "Brasil (Nacional)"
            territorio_sel = "Brasil"

    # Cálculos da série temporal da rampa constitucional 2021–2026
    vaaf_26 = float(df_sub["vaaf"].sum())
    vaat_26 = float(df_sub["vaat"].sum())
    vaar_26 = float(df_sub["vaar"].sum())
    vaar_25_real = float(df_sub["vaar_2025"].sum()) if "vaar_2025" in df_sub.columns else 0.0

    anos_rampa = sorted(RAMPA_COMPLEMENTACAO.keys())
    dados_serie = []
    v_base_2021 = None

    for a in anos_rampa:
        p_vaaf, p_vaat, p_vaar = RAMPA_COMPLEMENTACAO[a]
        v_vaaf = vaaf_26 * (p_vaaf / 10.0)
        v_vaat = vaat_26 * (p_vaat / 10.5)
        if a == 2026:
            v_vaar = vaar_26
        elif a == 2025 and vaar_25_real > 0:
            v_vaar = vaar_25_real
        else:
            v_vaar = vaar_26 * (p_vaar / 2.5)

        v_tot = v_vaaf + v_vaat + v_vaar
        if v_base_2021 is None:
            v_base_2021 = v_tot

        cresc_pct = ((v_tot - v_base_2021) / v_base_2021 * 100.0) if v_base_2021 and v_base_2021 > 0 else 0.0
        dados_serie.append({
            "ano": a,
            "rampa_pct": p_vaaf + p_vaat + p_vaar,
            "vaaf": v_vaaf,
            "vaat": v_vaat,
            "vaar": v_vaar,
            "total": v_tot,
            "cresc_pct": cresc_pct,
        })

    df_prog_territorio = pd.DataFrame(dados_serie)

    # Cards de Síntese Executiva do Território
    v_2021 = df_prog_territorio["total"].iloc[0]
    v_2026 = df_prog_territorio["total"].iloc[-1]
    delta_prog = v_2026 - v_2021
    pct_prog = ((v_2026 - v_2021) / v_2021 * 100.0) if v_2021 > 0 else 0.0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        metric_card("Recursos em 2021 (Base)", format_currency(v_2021), subtitle="Início Novo FUNDEB (12 p.p.)")
    with k2:
        metric_card("Recursos em 2026 (Pleno)", format_currency(v_2026), subtitle="Ápice Constitucional (23 p.p.)")
    with k3:
        metric_card("Salto Financeiro (2021 ➔ 2026)", f"+{format_currency(delta_prog)}", subtitle=f"Ganho líquido para {nome_territorio}")
    with k4:
        metric_card("Crescimento Acumulado", f"+{format_percent(pct_prog)}", subtitle="Variação relativa no período")

    # Gráficos da Progressão
    col_g_prog, col_g_comp = st.columns([3, 2])
    with col_g_prog:
        fig_barra_prog = chart_progressao_uniao(
            df_prog_territorio,
            titulo=f"Composição da Complementação da União: {nome_territorio} (2021–2026)",
        )
        st.plotly_chart(fig_barra_prog, use_container_width=True)

    with col_g_comp:
        if escala_prog == "📍 Por Região":
            cores_reg = {
                "Nordeste": "#2563EB",
                "Norte": "#0D9488",
                "Sudeste": "#F59E0B",
                "Sul": "#10B981",
                "Centro-Oeste": "#8B5CF6",
            }
            dados_comp_reg = []
            for r in REGIOES:
                sub_r = df[df["regiao"] == r]
                v_vaaf_base = float(sub_r["vaaf"].sum())
                v_vaat_base = float(sub_r["vaat"].sum())
                v_vaar_base = float(sub_r["vaar"].sum())
                v_vaar_25_r = float(sub_r["vaar_2025"].sum()) if "vaar_2025" in sub_r.columns else 0.0
                for a in anos_rampa:
                    p_vaaf, p_vaat, p_vaar = RAMPA_COMPLEMENTACAO[a]
                    v_vaaf_r = v_vaaf_base * (p_vaaf / 10.0)
                    v_vaat_r = v_vaat_base * (p_vaat / 10.5)
                    if a == 2026:
                        v_vaar_r = v_vaar_base
                    elif a == 2025 and v_vaar_25_r > 0:
                        v_vaar_r = v_vaar_25_r
                    else:
                        v_vaar_r = v_vaar_base * (p_vaar / 2.5)
                    dados_comp_reg.append({
                        "ano": a,
                        "regiao": r,
                        "total": v_vaaf_r + v_vaat_r + v_vaar_r,
                    })
            df_comp_reg = pd.DataFrame(dados_comp_reg)
            fig_comp = go.Figure()
            for r in REGIOES:
                df_r = df_comp_reg[df_comp_reg["regiao"] == r]
                is_destaque = (r == territorio_sel)
                fig_comp.add_trace(
                    go.Scatter(
                        x=df_r["ano"],
                        y=df_r["total"],
                        mode="lines+markers",
                        name=r,
                        line=dict(color=cores_reg.get(r, "#64748B"), width=3.5 if is_destaque else 1.5),
                        marker=dict(size=7 if is_destaque else 4),
                        hoverinfo="text",
                        hovertext=[f"<b>{r} ({ano})</b><br>{format_currency_full(val)}" for ano, val in zip(df_r["ano"], df_r["total"])],
                    )
                )
            fig_comp.update_layout(
                title=dict(text="Comparativo das 5 Grandes Regiões (2021–2026)", font=dict(size=13, color="#0F172A")),
                height=390,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1.0,
                    font=dict(size=10, color="#334155"),
                    bgcolor="rgba(255, 255, 255, 0)",
                ),
                margin=dict(t=55, b=40),
            )
            apply_few_theme(fig_comp, show_x_grid=False, show_y_grid=True)
            st.plotly_chart(fig_comp, use_container_width=True)

        elif escala_prog == "🏙️ Por Estado (UF)":
            reg_da_uf = REGIAO_POR_UF.get(territorio_sel, "Nordeste")
            ufs_mesma_reg = sorted([u for u, r in REGIAO_POR_UF.items() if r == reg_da_uf])
            dados_ufs = []
            for u in ufs_mesma_reg:
                sub_u = df[df["uf"] == u]
                dados_ufs.append({
                    "uf": u,
                    "total_2026": float(sub_u["uniao_total"].sum()),
                    "vaar_2026": float(sub_u["vaar"].sum()),
                })
            df_rank_ufs = pd.DataFrame(dados_ufs).sort_values(by="total_2026", ascending=True)
            cores_uf_bar = ["#1E40AF" if u == territorio_sel else "#94A3B8" for u in df_rank_ufs["uf"]]
            fig_rank_ufs = go.Figure(
                go.Bar(
                    x=df_rank_ufs["total_2026"],
                    y=df_rank_ufs["uf"],
                    orientation="h",
                    marker=dict(color=cores_uf_bar),
                    hoverinfo="text",
                    hovertext=[f"<b>{u}</b>: {format_currency_full(v)}" for u, v in zip(df_rank_ufs["uf"], df_rank_ufs["total_2026"])],
                )
            )
            fig_rank_ufs.update_layout(
                title=dict(text=f"Total Complementação 2026 nas UFs do {reg_da_uf}", font=dict(size=13, color="#0F172A")),
                height=380,
            )
            apply_few_theme(fig_rank_ufs, show_x_grid=True, show_y_grid=False)
            st.plotly_chart(fig_rank_ufs, use_container_width=True)

        else:
            dados_rampa = [
                {
                    "Ano": ano,
                    "VAAF": vaaf,
                    "VAAT": vaat,
                    "VAAR": vaar,
                    "Total União": vaaf + vaat + vaar,
                }
                for ano, (vaaf, vaat, vaar) in sorted(RAMPA_COMPLEMENTACAO.items())
            ]
            df_rampa = pd.DataFrame(dados_rampa)
            series_rampa = [
                ("Total União", "Complementação Total (União)", "#1E3A8A"),
                ("VAAF", "VAAF (Fixo 10 p.p.)", "#2563EB"),
                ("VAAT", "VAAT (Progressivo até 10,5 p.p.)", "#0D9488"),
                ("VAAR", "VAAR (Desempenho até 2,5 p.p.)", "#DC2626"),
            ]
            fig_rampa = chart_time_series(
                df_rampa,
                x_col="Ano",
                series=series_rampa,
                titulo="Evolução Percentual Constitucional (12% ➔ 23%)",
                y_title="Pontos Percentuais (%)",
            )
            st.plotly_chart(fig_rampa, use_container_width=True)

    # Tabela Discriminada Ano a Ano no Padrão ABNT
    st.markdown("###### 📋 Tabela Discriminada da Rampa no Território (Padrão ABNT)")
    df_tabela_abnt = pd.DataFrame([
        {
            "Ano": str(row["ano"]),
            "Rampa Constitucional": format_percent(row["rampa_pct"]),
            "VAAF (R$)": format_currency_full(row["vaaf"]),
            "VAAT (R$)": format_currency_full(row["vaat"]),
            "VAAR (R$)": format_currency_full(row["vaar"]),
            "Total Complementação (R$)": format_currency_full(row["total"]),
            "Crescimento s/ 2021": f"+{format_percent(row['cresc_pct'])}" if row["cresc_pct"] > 0 else "Base (0,0%)",
        }
        for _, row in df_prog_territorio.iterrows()
    ])
    st.dataframe(df_tabela_abnt, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ------------------------------------------------------------- BLOCO 2: SMALL MULTIPLES (STEPHEN FEW)
    st.markdown("##### 👥 Small Multiples: Trajetória Histórica das Matrículas por Região (2017–2023)")
    st.caption("Princípio de Stephen Few: múltiplos pequenos gráficos comparativos lado a lado em um único relance visual (*single eyespan*), variando apenas a dimensão geográfica:")

    anos = [a for a in range(2017, 2024)]
    cols_anos = [f"mat_iee_{a}" for a in anos]

    # Agregar soma de matrículas reais por região
    df_reg_mats = df.groupby("regiao")[cols_anos].sum().reset_index()

    cols_sm = st.columns(len(REGIOES))
    for col_ui, reg in zip(cols_sm, REGIOES):
        sub = df_reg_mats[df_reg_mats["regiao"] == reg]
        if not sub.empty:
            vals = [float(sub[f"mat_iee_{a}"].iloc[0]) for a in anos]
            var_pct = ((vals[-1] - vals[0]) / vals[0] * 100.0) if vals[0] > 0 else 0.0

            fig_sm = go.Figure()
            fig_sm.add_trace(
                go.Scatter(
                    x=anos,
                    y=vals,
                    mode="lines+markers",
                    line=dict(color="#1E40AF" if var_pct >= 0 else "#DC2626", width=2),
                    marker=dict(size=4),
                    hoverinfo="x+y",
                )
            )
            fig_sm.update_layout(
                title=dict(text=f"<b>{reg}</b> ({'+' if var_pct >= 0 else ''}{format_percent(var_pct)})", font=dict(size=12, color="#0F172A")),
                height=160,
                margin=dict(l=5, r=5, t=28, b=10),
                showlegend=False,
            )
            fig_sm.update_xaxes(showgrid=False, tickmode="array", tickvals=[2017, 2020, 2023], ticktext=["'17", "'20", "'23"])
            fig_sm.update_yaxes(showgrid=True, gridcolor="#F1F5F9", tickformat="~s")
            apply_few_theme(fig_sm, show_x_grid=False, show_y_grid=True)

            with col_ui:
                st.plotly_chart(fig_sm, use_container_width=True)

    st.markdown("---")

    # ------------------------------------------------------------- BLOCO 3: COMO AGIR
    st.subheader("🎯 Matriz de Ação Estratégica: Como Melhorar os Próximos Recebimentos")
    st.markdown(
        """
        O VAAR não é repasse automático: exige **cumprimento prévio das 5 condicionalidades** e **evolução positiva nos indicadores de atendimento e aprendizagem**.
        Abaixo está o plano de ação recomendado para secretarias de educação:
        """
    )

    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            st.markdown("#### 1️⃣ Regularização de Habilitação (Obrigatória)")
            st.markdown(
                """
                - **Cond. I — Provimento de Diretores**:
                  * Editar decreto/lei municipal estabelecendo processo seletivo por critérios de mérito e desempenho ou eleição qualificada.
                  * Inserir documentação no SIMEC antes do encerramento da janela anual.
                - **Cond. II — Participação no SAEB (Meta: >= 80%)**:
                  * Mapeamento escola a escola das turmas avaliadas.
                  * Busca ativa no dia da prova e convocação de alunos ausentes na reaplicação.
                - **Cond. III — ICMS Educação e Redução de Desigualdades**:
                  * Articular com a Assembleia Legislativa estadual e UNDIME a vigência de regras de rateio do ICMS baseadas em aprendizagem.
                - **Cond. IV — BNCC e Currículo**:
                  * Homologar o documento curricular da rede alinhado à BNCC no respectivo Conselho de Educação.
                - **Cond. V — Transmissão SIOPE**:
                  * Fechar e validar os balanços contábeis e fiscais bimestrais no SIOPE com antecedência mínima de 15 dias do prazo final.
                """
            )

    with c2:
        with st.container(border=True):
            st.markdown("#### 2️⃣ Maximização dos Indicadores de Rateio")
            st.markdown(
                """
                - **Atendimento (IEE & IAE)**:
                  * **Rede Municipal**: Ampliar matrículas na Educação Infantil (Creche e Pré-Escola) mantendo baixo índice de evasão.
                  * **Rede Estadual**: Reduzir abandono escolar no Ensino Médio e reter alunos com programas de permanência.
                - **Aprendizagem (Saeb & IDEB)**:
                  * Foco pedagógico nas turmas de transição (5º ano, 9º ano EF e 3ª série EM).
                  * Monitoramento contínuo das proficiências em Língua Portuguesa e Matemática.
                - **Equidade Socioeconômica e Racial**:
                  * O algoritmo do Inep penaliza redes onde alunos pretos, pardos ou de baixo INSE ficam para trás.
                  * Implementar recomposição de aprendizagem focada nas escolas periféricas e de menor nível socioeconômico.
                """
            )

    st.markdown("---")

    # ------------------------------------------------------------- BLOCO 4: CHECKLIST INTERATIVO
    st.subheader("✅ Checklist Interativo de Conformidade da Rede")
    st.markdown("Utilize este checklist em reuniões de alinhamento com a equipe técnica da Secretaria:")

    ck1 = st.checkbox("Lei/Normativo de Diretores Escolares por Mérito devidamente homologada no SIMEC?")
    ck2 = st.checkbox("Comitê de Mobilização do SAEB instituído com meta de 85%+ de presença?")
    ck3 = st.checkbox("Lei Estadual do ICMS Educação aprovada e vigente no Estado?")
    ck4 = st.checkbox("Currículo da Rede alinhado à BNCC aprovado no Conselho Municipal/Estadual?")
    ck5 = st.checkbox("Balanços e dados fiscais do SIOPE transmitidos sem inconsistências no sistema do FNDE?")

    prontidao = sum([ck1, ck2, ck3, ck4, ck5]) * 20
    st.progress(prontidao / 100.0, text=f"Grau de Conformidade para Habilitação: {format_int(prontidao)}%")

    if prontidao == 100:
        st.success("🎉 Parabéns! A rede atende a todos os requisitos fundamentais para habilitação plena ao VAAR.")
    elif prontidao >= 60:
        st.warning("⚠️ Atenção: Há pendências críticas que podem desabilitar a rede no próximo ciclo.")
    else:
        st.error("🚨 Alerta Vermelho: Alto risco de desabilitação e perda total do VAAR.")
