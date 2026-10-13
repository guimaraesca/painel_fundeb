"""Visualização do Boletim Executivo Estratégico (Relatório de 2 Páginas).

Gera relatório executivo de 2 páginas A4 (Vertical ou Horizontal) para qualquer
Estado ou Município com diagnóstico legal, pedagógico, simulação de potencial
financeiro e plano de ação prescritivo automatizado.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

from fundeb.services.simulator import SimulatorService
from fundeb.services.boletim import BoletimService, DadosBoletim
from fundeb.ui.components import (
    metric_card,
    format_currency_full,
    format_percent,
    format_int,
    format_decimal,
)
from fundeb.ui.charts import chart_lollipop_hipoteses


def render_boletim_view(df: pd.DataFrame, simulator: SimulatorService) -> None:
    st.subheader("📄 Boletim Executivo & Plano de Ação Estratégico (2 Páginas)")
    st.markdown(
        """
        Documento executivo de **alta densidade e síntese estratégica** gerado automaticamente para qualquer rede
        estadual ou municipal de ensino. Estruturado em **duas páginas oficiais**:
        * **Página 1:** Radiografia do Ente, Auditoria das 5 Condicionalidades da Lei nº 14.113/2020 e Indicadores Pedagógicos.
        * **Página 2:** Simulação de Potencial Financeiro, Custo da Inação e Plano Propositivo Prescritivo de Ações.
        """
    )

    boletim_service = BoletimService(df, simulator)

    # -------------------------------------------------------------------------
    # 1. SELEÇÃO DO ENTE E FORMATO DO RELATÓRIO
    # -------------------------------------------------------------------------
    st.markdown("#### 1. Seleção do Ente Federado e Formato")

    c_esf, c_form = st.columns([1, 1])
    with c_esf:
        esfera = st.radio(
            "Esfera de Análise:",
            options=["Rede Municipal", "Rede Estadual"],
            horizontal=True,
            key="bol_esfera",
        )
    with c_form:
        orientacao_sel = st.radio(
            "Orientação do Boletim (2 Páginas A4):",
            options=["📄 Retrato (Vertical A4)", "🖥️ Paisagem (Horizontal A4 / Slides)"],
            horizontal=True,
            key="bol_orientacao",
        )
        orientacao_cod = "landscape" if "Paisagem" in orientacao_sel else "portrait"

    # Seleção do Ente com O(1)
    if esfera == "Rede Estadual":
        df_est = df[df["rede"] == "Estadual"].sort_values(by="uf")
        map_est = dict(zip(df_est["ibge"], df_est["nome"]))
        ibge_sel = st.selectbox(
            "Selecione o Estado:",
            options=df_est["ibge"].tolist(),
            format_func=lambda ib: f"{map_est.get(ib, ib)} (UF: {ib})",
            key="bol_ibge_est",
        )
    else:
        col_uf, col_mun = st.columns([1, 2])
        ufs = sorted(df[df["rede"] == "Municipal"]["uf"].dropna().unique().tolist())
        with col_uf:
            uf_padrao = "PI" if "PI" in ufs else ufs[0]
            uf_sel = st.selectbox("Selecione o Estado (UF):", options=ufs, index=ufs.index(uf_padrao), key="bol_uf_mun")

        df_mun = df[(df["rede"] == "Municipal") & (df["uf"] == uf_sel)].sort_values(by="nome")
        map_mun = dict(zip(df_mun["ibge"], df_mun["nome"]))
        with col_mun:
            ibge_sel = st.selectbox(
                f"Selecione o Município ({uf_sel}):",
                options=df_mun["ibge"].tolist(),
                format_func=lambda ib: f"{map_mun.get(ib, ib)} (IBGE: {ib})",
                key="bol_ibge_mun",
            )

    if not ibge_sel:
        st.warning("Selecione um ente para gerar o boletim executivo.")
        return

    # Geração dos Dados do Boletim
    dados = boletim_service.gerar_dados_boletim(ibge_sel)
    if not dados:
        st.error("Não foi possível carregar os dados para o ente selecionado.")
        return

    # Geração do HTML Oficial Autocontido
    html_boletim = boletim_service.gerar_html_boletim(dados, orientacao=orientacao_cod)

    # -------------------------------------------------------------------------
    # 2. CARDS RESUMO & BARRA DE AÇÕES RÁPIDAS
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown(f"### 🏛️ {dados.nome} &bull; {dados.uf}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            label="Situação Habilitação VAAR",
            value="Elegível (Habilitado)" if dados.habilitado else "Inabilitado",
            delta=f"{5 - dados.n_reprovacoes}/5 Condic. Aprovadas",
            delta_color="normal" if dados.habilitado else "inverse",
        )
    with c2:
        st.metric(
            label="VAAR Recebido (2026)",
            value=format_currency_full(dados.vaar_2026_rs),
            delta=f"{'+' if dados.delta_vaar_historico_rs >= 0 else ''}{format_currency_full(dados.delta_vaar_historico_rs)} vs 2025",
        )
    with c3:
        st.metric(
            label="Potencial Máximo Estimado",
            value=format_currency_full(dados.melhor_potencial_rs),
            delta=f"+{format_currency_full(dados.custo_inacao_rs)} potencial",
        )
    with c4:
        st.metric(
            label="Ações Prescritas no Plano",
            value=f"{len(dados.acoes_prescritivas)} Medidas",
            delta=f"{sum(1 for a in dados.acoes_prescritivas if a.prioridade == 'Alta')} de Alta Prioridade",
            delta_color="off",
        )

    # Barra de Ferramentas de Exportação
    col_down, col_print, col_info = st.columns([1.2, 1.2, 2.6])
    nome_slug = dados.nome.lower().replace(" ", "_").replace("—", "").replace("-", "_")
    nome_arquivo = f"boletim_vaar_2pag_{dados.uf.lower()}_{dados.ibge}_{nome_slug}.html"

    with col_down:
        st.download_button(
            label="💾 Baixar Boletim em HTML",
            data=html_boletim,
            file_name=nome_arquivo,
            mime="text/html",
            help="Baixa o documento HTML autocontido com as 2 páginas formatadas para envio por e-mail ou impressão.",
            use_container_width=True,
        )

    with col_print:
        # Script para acionar a impressão do navegador com foco na página
        st.markdown(
            """
            <a href="javascript:window.print()" class="btn-print" style="
                display: block;
                text-align: center;
                background-color: #2563EB;
                color: #FFFFFF !important;
                padding: 0.55rem 1rem;
                border-radius: 0.5rem;
                font-weight: 600;
                font-size: 0.875rem;
                text-decoration: none;
                margin-top: 1px;
            ">🖨️ Imprimir / Salvar em PDF</a>
            """,
            unsafe_allow_html=True,
        )

    with col_info:
        st.caption(
            f"📌 **Autenticação:** Código `{dados.hash_autenticacao}` &bull; Orientação configurada: **{orientacao_sel}** (2 páginas A4 estritas)."
        )

    # -------------------------------------------------------------------------
    # 3. ABAS DE EXPLORAÇÃO DO BOLETIM
    # -------------------------------------------------------------------------
    tab_doc, tab_sim, tab_acoes = st.tabs([
        "📑 Documento Oficial (2 Páginas A4)",
        "📊 Trilha de Potencial Financeiro",
        "🎯 Plano Prescritivo de Ações",
    ])

    with tab_doc:
        st.markdown("##### 📄 Pré-visualização do Relatório Oficial de 2 Páginas")
        st.caption(
            "O documento abaixo é renderizado exatamente com o CSS oficial de impressão. "
            "Ao clicar em **Imprimir / Salvar em PDF** acima (ou pressionar `Ctrl+P` / `Cmd+P`), "
            "as 2 páginas serão paginadas automaticamente sem cortes."
        )

        # Altura ajustada dinamicamente conforme orientação
        altura_preview = 1250 if orientacao_cod == "portrait" else 880
        components.html(html_boletim, height=altura_preview, scrolling=True)

    with tab_sim:
        st.markdown("##### 📈 Simulação Contrafactual: Da Situação Atual ao Teto Teórico")
        st.markdown(
            """
            O gráfico lollipop abaixo demonstra a progressão do repasse financeiro do VAAR conforme a rede supera
            barreiras de gestão e atinge metas superiores de permanência e rendimento:
            """
        )

        fig_loll = chart_lollipop_hipoteses(dados.trilha_cenarios, dados.nome)
        st.plotly_chart(fig_loll, use_container_width=True)

        # Tabela Detalhada
        df_cen = pd.DataFrame(dados.trilha_cenarios)
        df_cen["valor_formatado"] = df_cen["valor_rs"].apply(format_currency_full)
        df_cen["delta_formatado"] = df_cen["delta_rs"].apply(lambda v: f"+{format_currency_full(v)}" if v > 0 else "Baseline")
        df_cen_view = df_cen[["cenario", "valor_formatado", "delta_formatado"]].rename(
            columns={
                "cenario": "Cenário de Desempenho",
                "valor_formatado": "Repasse Anual Estimado",
                "delta_formatado": "Ganho Líquido (Δ)",
            }
        )
        st.dataframe(df_cen_view, use_container_width=True, hide_index=True)

        if dados.custo_inacao_rs > 0:
            st.warning(
                f"🚨 **Custo da Inação:** A rede deixa de captar anualmente **{format_currency_full(dados.custo_inacao_rs)}** "
                f"enquanto permanecer inabilitada ou no patamar mínimo de desempenho."
            )
        else:
            st.success("🏆 A rede já se encontra no patamar máximo de captação teórica dos coeficientes atuais.")

    with tab_acoes:
        st.markdown("##### 🎯 Matriz Propositiva de Ações Prescritivas para o Ente")
        st.markdown(
            "Ações geradas pelo motor analítico do painel para orientar o prefeito/governador, secretários de educação "
            "e gestores escolares no ciclo de planejamento:"
        )

        for acao in dados.acoes_prescritivas:
            cor_card = {
                "Alta": "#FEE2E2",
                "Média": "#FEF3C7",
                "Preventiva": "#DBEAFE",
            }.get(acao.prioridade, "#F1F5F9")

            cor_borda = {
                "Alta": "#DC2626",
                "Média": "#D97706",
                "Preventiva": "#2563EB",
            }.get(acao.prioridade, "#CBD5E1")

            with st.container():
                st.markdown(
                    f"""
                    <div style="
                        background-color: #FFFFFF;
                        border-left: 5px solid {cor_borda};
                        border-top: 1px solid #E2E8F0;
                        border-right: 1px solid #E2E8F0;
                        border-bottom: 1px solid #E2E8F0;
                        border-radius: 6px;
                        padding: 12px 16px;
                        margin-bottom: 12px;
                    ">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <div>
                                <span style="background-color:{cor_card}; color:{cor_borda}; font-weight:700; font-size:0.75rem; padding:2px 8px; border-radius:4px; text-transform:uppercase;">
                                    Prioridade {acao.prioridade}
                                </span>
                                <span style="margin-left:8px; font-weight:600; color:#64748B; font-size:0.8rem;">
                                    {acao.eixo} &bull; Prazo: <strong>{acao.prazo}</strong>
                                </span>
                            </div>
                        </div>
                        <h4 style="margin:4px 0 8px 0; color:#0F172A; font-size:1.05rem;">{acao.titulo}</h4>
                        <p style="margin:0 0 6px 0; font-size:0.88rem; color:#475569;">
                            <strong>🔍 Diagnóstico:</strong> {acao.diagnostico}
                        </p>
                        <p style="margin:0 0 8px 0; font-size:0.9rem; color:#1E293B;">
                            <strong>📋 Ação Prescritiva:</strong> {acao.acao_prescritiva}
                        </p>
                        <div style="border-top:1px dashed #E2E8F0; padding-top:6px; display:flex; justify-content:space-between; font-size:0.82rem; color:#64748B;">
                            <span><strong>Responsáveis:</strong> {acao.responsaveis}</span>
                            <span style="color:#166534; font-weight:600;"><strong>Impacto:</strong> {acao.impacto_estimado}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
