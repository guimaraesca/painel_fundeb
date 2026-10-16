"""Visualização do Boletim Executivo Estratégico (Relatório de 2 Páginas).

Incorpora os 8 Princípios Fundamentais de Stephen Few:
- Simplifique (Design sem ruído, alta proporção dado-tinta)
- Comparar (Benchmarks lado a lado: Ente vs UF vs Brasil)
- Atenção (Atributos pré-atentivos em gargalos e perdas financeiras)
- Explorar (Seletores instantâneos O(1) de qualquer Estado ou Município)
- Visão Diversificada (Visão integrada legal, contábil, pedagógica e infraestrutura)
- Pergunte por quê (Diagnóstico causal explícito de causas-raiz)
- Seja cético (Simulação contrafactual com 6 hipóteses auditadas)
- Responder e Compartilhar (Exportação A4 em Retrato e Paisagem)
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

from fundeb.services.simulator import SimulatorService
from fundeb.services.boletim import BoletimService, DadosBoletim
from fundeb.ui.components import (
    metric_card,
    format_currency,
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
        Documento executivo de **alta densidade e síntese estratégica** desenhado sob os **8 Princípios de Stephen Few**.
        Permite diagnosticar a rede, comparar lado a lado com as médias estadual e nacional, e prescrever ações imediatas:
        * **Página 1:** Radiografia Oficial, Auditoria das 5 Condicionalidades e Comparativo Lado a Lado (Ente vs UF vs Brasil).
        * **Página 2:** Simulação Contrafactual de Potencial, Diagnóstico Causal de Causa-Raiz e Plano Prescritivo de Ações.
        """
    )

    boletim_service = BoletimService(df, simulator)

    # -------------------------------------------------------------------------
    # 1. SELEÇÃO DO ENTE E FORMATO DO RELATÓRIO
    # -------------------------------------------------------------------------
    st.markdown("#### 1. Seleção do Ente Federado e Orientação (Stephen Few: Explorar)")

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
    # 2. CARDS RESUMO & BARRA DE AÇÕES RÁPIDAS (Stephen Few: Atenção)
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown(f"### 🏛️ {dados.nome} • {dados.uf}")

    # Banner Pré-atentivo
    al = dados.alerta_preattentive
    if al.tipo == "perigo":
        st.error(f"**{al.titulo}** — {al.descricao} | **{al.valor_destaque}**")
    elif al.tipo == "alerta":
        st.warning(f"**{al.titulo}** — {al.descricao} | **{al.valor_destaque}**")
    else:
        st.success(f"**{al.titulo}** — {al.descricao} | **{al.valor_destaque}**")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            label="Situação Habilitação VAAR",
            value="Elegível (Habilitado)" if dados.habilitado else "Inabilitado",
            delta=f"{5 - dados.n_reprovacoes}/5 Condic. Cumpridas",
            delta_color="normal" if dados.habilitado else "inverse",
        )
    with c2:
        st.metric(
            label="VAAR Recebido (2026)",
            value=format_currency_full(dados.vaar_2026_rs),
            delta=f"{'+' if dados.delta_vaar_historico_rs >= 0 else ''}{format_currency(dados.delta_vaar_historico_rs)} vs 2025",
        )
    with c3:
        st.metric(
            label="Potencial Máximo Estimado",
            value=format_currency_full(dados.melhor_potencial_rs),
            delta=f"+{format_currency(dados.custo_inacao_rs)} potencial",
        )
    with c4:
        st.metric(
            label="Plano de Ação Propositivo",
            value=f"{len(dados.acoes_prescritivas)} Medidas",
            delta=f"{sum(1 for a in dados.acoes_prescritivas if a.prioridade == 'Alta')} de Alta Prioridade",
            delta_color="off",
        )

    # Barra de Ferramentas de Exportação (Stephen Few: Responder e Compartilhar)
    col_down, col_print, col_info = st.columns([1.2, 1.2, 2.6])
    nome_slug = dados.nome.lower().replace(" ", "_").replace("—", "").replace("-", "_")
    orient_slug = "paisagem" if orientacao_cod == "landscape" else "retrato"
    nome_arquivo = f"boletim_vaar_2pag_{orient_slug}_{dados.uf.lower()}_{dados.ibge}_{nome_slug}.html"

    with col_down:
        st.download_button(
            label="💾 Baixar Boletim em HTML",
            data=html_boletim,
            file_name=nome_arquivo,
            mime="text/html",
            help="Baixa o documento HTML autocontido com as 2 páginas formatadas para envio por e-mail, compartilhamento ou impressão.",
            use_container_width=True,
        )

    with col_print:
        st.info(
            "🖨️ Para gerar o PDF, use o botão **Imprimir / Salvar em PDF** no topo da "
            "pré-visualização do documento (aba abaixo) — ele imprime as 2 páginas A4 "
            "exatas, sem a interface do painel.",
            icon=None,
        )

    with col_info:
        st.caption(
            f"📌 **Autenticação:** Código `{dados.hash_autenticacao}` • Formato: **{orientacao_sel}** (Paginado em 2 páginas exatas sem cortes)."
        )

    # -------------------------------------------------------------------------
    # 3. ABAS DE EXPLORAÇÃO DO BOLETIM (Stephen Few: Visão Diversificada)
    # -------------------------------------------------------------------------
    tab_doc, tab_bench, tab_sim, tab_acoes = st.tabs([
        "📑 Documento Oficial (2 Páginas A4)",
        "⚖️ Comparativo Lado a Lado (Few: Comparar)",
        "📊 Trilha de Potencial & Sensibilidade (Few: Seja Cético)",
        "🎯 Plano Prescritivo & Causa-Raiz (Few: Pergunte Por Quê)",
    ])

    with tab_doc:
        st.markdown(f"##### 📄 Pré-visualização do Relatório Oficial ({orientacao_sel})")
        st.caption(
            "O documento abaixo é renderizado exatamente com o CSS oficial de impressão. "
            "Ao clicar em **Imprimir / Salvar em PDF** acima (ou pressionar `Ctrl+P` / `Cmd+P`), "
            "as 2 páginas serão paginadas automaticamente sem cortes."
        )

        altura_preview = 1350 if orientacao_cod == "portrait" else 920
        components.html(html_boletim, height=altura_preview, scrolling=True)

    with tab_bench:
        st.markdown("##### ⚖️ Benchmarks Comparativos Lado a Lado (Princípio de Stephen Few: Comparar)")
        st.caption(
            "Transferindo o esforço da memória para a visão: comparação simultânea dos resultados do ente "
            f"com a média estadual ({dados.uf}) e com a média nacional do Brasil."
        )

        registros_bench = []
        for b in dados.benchmarks:
            v_e = format_decimal(b.ente_val, 1) if b.ente_val is not None else "—"
            v_u = format_decimal(b.uf_val, 1) if b.uf_val is not None else "—"
            v_b = format_decimal(b.br_val, 1) if b.br_val is not None else "—"
            un = f" {b.unidade}" if b.unidade in ("%", "pts") else ""
            registros_bench.append({
                "Indicador": b.metrica,
                f"Resultado ({dados.nome})": f"{v_e}{un}",
                f"Média Estadual ({dados.uf})": f"{v_u}{un}",
                "Média Brasil": f"{v_b}{un}",
                "Posição Relativa": f"{b.simbolo} {b.status_relativo}",
            })

        df_bench = pd.DataFrame(registros_bench)
        st.dataframe(df_bench, use_container_width=True, hide_index=True)

    with tab_sim:
        st.markdown("##### 📈 Simulação Contrafactual: Da Situação Atual ao Teto Teórico (Few: Seja Cético)")
        st.markdown(
            "O gráfico lollipop demonstra a progressão do repasse financeiro do VAAR sob 6 hipóteses contrafactuais "
            "auditadas, do baseline oficial até o teto teórico máximo:"
        )

        fig_loll = chart_lollipop_hipoteses(dados.trilha_cenarios, dados.nome)
        st.plotly_chart(fig_loll, use_container_width=True)

        df_cen = pd.DataFrame(dados.trilha_cenarios)
        max_pot = float(df_cen["valor_rs"].max()) if not df_cen.empty else 0.0
        df_cen["progresso_potencial"] = (df_cen["valor_rs"] / max_pot) if max_pot > 0 else 0.0
        df_cen["valor_formatado"] = df_cen["valor_rs"].apply(format_currency_full)
        df_cen["delta_formatado"] = df_cen["delta_rs"].apply(lambda v: f"+{format_currency_full(v)}" if v > 0 else "Baseline")

        st.dataframe(
            df_cen[[
                "cenario",
                "valor_formatado",
                "progresso_potencial",
                "delta_formatado",
            ]],
            column_config={
                "cenario": st.column_config.TextColumn("Cenário de Desempenho"),
                "valor_formatado": st.column_config.TextColumn("Repasse Estimado"),
                "progresso_potencial": st.column_config.ProgressColumn(
                    "% Potencial Máximo",
                    format="percent",
                    min_value=0.0,
                    max_value=1.0,
                ),
                "delta_formatado": st.column_config.TextColumn("Ganho Líquido (Δ)"),
            },
            use_container_width=True,
            hide_index=True,
        )

        if dados.custo_inacao_rs > 0:
            st.warning(
                f"🚨 **Custo Anual da Inação:** A rede deixa de captar **{format_currency_full(dados.custo_inacao_rs)}** anuais "
                f"enquanto permanecer inabilitada ou aquém de suas metas pedagógicas."
            )
        else:
            st.success("🏆 A rede já se encontra no patamar máximo de captação teórica dos coeficientes atuais.")

    with tab_acoes:
        st.markdown("##### 🔍 Diagnóstico Causal de Causa-Raiz (Few: Pergunte Por Quê)")
        st.caption("Identificação rigorosa do porquê dos resultados e bloqueios administrativos:")

        for diag in dados.diagnosticos_causais:
            with st.expander(f"❓ {diag.pergunta}", expanded=True):
                st.markdown(f"**Explicação Causal:** {diag.resposta}")
                st.markdown(f"**Evidência nos Dados:** `{diag.evidencia}` • <span style='color:#dc2626;'>**Impacto:** {diag.impacto_financeiro}</span>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("##### 🎯 Matriz Propositiva de Ações Prescritivas para o Ente (Como Agir)")

        for acao in dados.acoes_prescritivas:
            cor_card = {"Alta": "#FEE2E2", "Média": "#FEF3C7", "Preventiva": "#DBEAFE"}.get(acao.prioridade, "#F1F5F9")
            cor_borda = {"Alta": "#DC2626", "Média": "#D97706", "Preventiva": "#2563EB"}.get(acao.prioridade, "#CBD5E1")

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
                                    {acao.eixo} • Prazo: <strong>{acao.prazo}</strong>
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
