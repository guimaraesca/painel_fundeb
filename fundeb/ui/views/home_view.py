"""Página Inicial: Guia Executivo de Leitura, Estrutura Temática e Acesso Rápido a Dados."""
from __future__ import annotations

import textwrap
import streamlit as st
import pandas as pd

from fundeb.services.analytics import AnalyticsService
from fundeb.ui.components import (
    metric_card,
    format_currency,
    format_currency_full,
    format_percent,
    format_int,
    status_badge,
)


def render_home_view(analytics: AnalyticsService) -> None:
    resumo = analytics.resumo_nacional()
    df = analytics.df
    gargalos = analytics.gargalos_condicionalidade()

    # Banner Institucional de Boas-Vindas
    st.markdown(
        textwrap.dedent(
            """
            <div style="background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%); padding: 24px 30px; border-radius: 12px; color: white; margin-bottom: 20px;">
                <div style="font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; opacity: 0.85;">
                    Painel Estratégico &middot; Ciclo de Distribuição FUNDEB 2026
                </div>
                <h1 style="color: white; margin: 6px 0 10px 0; font-size: 2.1rem; font-weight: 800;">
                    Diagnóstico Nacional do FUNDEB &amp; Complementação VAAR
                </h1>
                <p style="font-size: 1.02rem; opacity: 0.95; max-width: 980px; line-height: 1.5; margin: 0;">
                    Ambiente analítico integrado para monitoramento da complementação federal por desempenho (VAAR),
                    auditoria das condicionalidades do Art. 14 da Lei nº 14.113/2020, avaliação histórica dos fundos e
                    simulação de impacto financeiro orientada a evidências para redes estaduais e municipais.
                </p>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------- ZERO CLIQUES: PANORAMA NACIONAL
    st.markdown("### 📊 Panorama Consolidado do Ciclo 2026 (Visão Imediata)")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card(
            title="Complementação VAAR 2026",
            value=format_currency(resumo.total_vaar_reais),
            subtitle=f"{format_int(resumo.beneficiarios)} redes contempladas ({format_percent(resumo.pct_beneficiarios)} do país)",
        )
    with col2:
        metric_card(
            title="Redes Habilitadas",
            value=f"{format_int(resumo.habilitados)} / {format_int(resumo.total_entes)}",
            subtitle=f"{format_percent(resumo.pct_habilitados)} de conformidade nas 5 condicionalidades",
        )
    with col3:
        metric_card(
            title="Gargalo de Elegibilidade",
            value=f"{format_int(resumo.nao_habilitados)} redes",
            subtitle=f"{format_percent(resumo.pct_nao_habilitados)} reprovadas em ao menos uma exigência",
            delta="Perderam o VAAR",
            delta_color="red",
        )
    with col4:
        metric_card(
            title="Complementação Total da União",
            value=format_currency(resumo.total_uniao_reais),
            subtitle=f"VAAF: {format_currency(resumo.total_vaaf_reais)} &bull; VAAT: {format_currency(resumo.total_vaat_reais)}",
        )

    # Dinâmica de Transição 2025 -> 2026
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    c_tr1, c_tr2, c_tr3, c_tr4 = st.columns(4)
    with c_tr1:
        metric_card(
            title="Manteve VAAR",
            value=f"{format_int(resumo.transicao_manteve)} redes",
            subtitle="Receberam em 2025 e mantiveram em 2026",
            delta="Estabilidade",
        )
    with c_tr2:
        metric_card(
            title="Perdeu VAAR",
            value=f"{format_int(resumo.transicao_perdeu)} redes",
            subtitle="Receberam em 2025, mas perderam em 2026",
            delta="Atenção",
            delta_color="red",
        )
    with c_tr3:
        metric_card(
            title="Conquistou VAAR",
            value=f"{format_int(resumo.transicao_entrou)} redes",
            subtitle="Não recebiam em 2025 e ingressaram em 2026",
            delta="Novo Repasse",
        )
    with c_tr4:
        metric_card(
            title="Fora do VAAR",
            value=f"{format_int(resumo.transicao_fora)} redes",
            subtitle="Não receberam em 2025 nem em 2026",
        )

    st.markdown("---")

    # ------------------------------------------------------------- 1 CLIQUE: BUSCA DIRETA DE QUALQUER REDE
    st.subheader("🔍 Consulta Direta de Rede (Granularidade em 1 Clique)")
    st.caption("Consulte a situação contábil, educacional e de condicionalidades de qualquer uma das 5.596 redes sem precisar trocar de página:")

    col_b1, col_b2 = st.columns([1, 2])
    with col_b1:
        filtro_esfera = st.selectbox("Filtrar Esfera:", options=["Todas", "Rede Municipal", "Rede Estadual"])
    with col_b2:
        df_busca = df.copy()
        if filtro_esfera == "Rede Municipal":
            df_busca = df_busca[df_busca["rede"] == "Municipal"]
        elif filtro_esfera == "Rede Estadual":
            df_busca = df_busca[df_busca["rede"] == "Estadual"]

        ente_selecionado = st.selectbox(
            "Selecione ou digite o nome/IBGE da rede:",
            options=df_busca["ibge"].tolist(),
            format_func=lambda ib: f"{df_busca[df_busca['ibge'] == ib]['nome'].iloc[0]} ({df_busca[df_busca['ibge'] == ib]['uf'].iloc[0]} - IBGE {ib})",
            index=0,
        )

    if ente_selecionado:
        row = df[df["ibge"] == ente_selecionado].iloc[0]
        with st.container(border=True):
            col_cab1, col_cab2 = st.columns([3, 1])
            with col_cab1:
                st.markdown(
                    f"### {row['nome']} &nbsp; <small style='color:#64748B;'>UF: {row['uf']} &middot; Esfera: {row['rede']} &middot; IBGE: {row['ibge']}</small>",
                    unsafe_allow_html=True,
                )
            with col_cab2:
                hab_txt = status_badge("Habilitado" if row["habilitado"] else "Não habilitado")
                ben_txt = status_badge("Beneficiário" if row["beneficiario"] else "Não beneficiário")
                st.markdown(f"**{hab_txt}** &nbsp; **{ben_txt}**")

            # Grid 4 colunas de informações imediatas
            g1, g2, g3, g4 = st.columns(4)
            with g1:
                st.markdown("**💰 Recursos Financeiros 2026**")
                st.markdown(f"- **VAAR 2026:** {format_currency_full(row['vaar'])}")
                st.markdown(f"- **VAAR 2025:** {format_currency_full(row['vaar_2025'])}")
                st.markdown(f"- **Complementação União:** {format_currency_full(row['uniao_total'])}")
                st.markdown(f"- **VAAF:** {format_currency_full(row['vaaf'])}")
                st.markdown(f"- **VAAT:** {format_currency_full(row['vaat'])}")
            with g2:
                st.markdown("**📈 Indicadores de Rateio**")
                st.markdown(f"- **IND Atendimento:** {row['ind_atend']:.4f}" if pd.notna(row['ind_atend']) else "- **IND Atendimento:** —")
                st.markdown(f"- **Evoluiu Atendimento:** {'Sim' if row['evoluiu_atend'] else 'Não'}")
                st.markdown(f"- **IND Aprendizagem:** {row['ind_aprend']:.4f}" if pd.notna(row['ind_aprend']) else "- **IND Aprendizagem:** —")
                st.markdown(f"- **Evoluiu Aprendizagem:** {'Sim' if row['evoluiu_aprend'] else 'Não'}")
                st.markdown(f"- **Total Reprovações:** {row['n_reprovacoes']} de 5")
            with g3:
                st.markdown("**🎓 Desempenho Educacional (Inep)**")
                st.markdown(f"- **Ideb Anos Iniciais:** {row['ideb_ai']:.1f}" if pd.notna(row['ideb_ai']) else "- **Ideb (AI):** —")
                st.markdown(f"- **Ideb Anos Finais:** {row['ideb_af']:.1f}" if pd.notna(row['ideb_af']) else "- **Ideb (AF):** —")
                st.markdown(f"- **Saeb Matemática (AI):** {row['saeb_ai_mt']:.1f}" if pd.notna(row['saeb_ai_mt']) else "- **Saeb MT:** —")
                st.markdown(f"- **Saeb Língua Port. (AI):** {row['saeb_ai_lp']:.1f}" if pd.notna(row['saeb_ai_lp']) else "- **Saeb LP:** —")
                st.markdown(f"- **INSE Municipal:** {row['inse']:.2f}" if pd.notna(row['inse']) else "- **INSE:** —")
            with g4:
                st.markdown("**⚖️ Status das 5 Condicionalidades**")
                st.markdown(f"- **Cond. I (Diretores por Mérito):** {'✅ Aprovada' if row['c1'] else '❌ Reprovada'}")
                st.markdown(f"- **Cond. II (Saeb >= 80%):** {'✅ Aprovada' if row['c2'] else '❌ Reprovada'}")
                st.markdown(f"- **Cond. III (ICMS / Red. Desigualdades):** {'✅ Aprovada' if row['c3'] else '❌ Reprovada'}")
                st.markdown(f"- **Cond. IV (Currículo BNCC):** {'✅ Aprovada' if row['c4'] else '❌ Reprovada'}")
                st.markdown(f"- **Cond. V (SIOPE / Fiscal):** {'✅ Aprovada' if row['c5'] else '❌ Reprovada'}")

    st.markdown("---")

    # ------------------------------------------------------------- EXPLICAÇÃO DOS TÓPICOS COM FRASES LONGAS E NEGRITOS
    st.subheader("📌 Tópicos e Estrutura do Painel: Guia Detalhado de Leitura")
    st.caption("Abaixo apresentamos a fundamentação conceitual, metodológica e institucional de cada um dos eixos estruturantes do painel:")

    col_t1, col_t2 = st.columns(2)

    with col_t1:
        with st.container(border=True):
            st.markdown(
                """
                #### ⚖️ 1. Condicionalidades & Funil de Desabilitação
                **O cumprimento cumulativo das condicionalidades do Art. 14, § 1º da Lei nº 14.113/2020 constitui requisito jurídico indispensável** para que qualquer rede de ensino participe da distribuição da Complementação VAAR.
                Nesta seção, **o painel evidencia que a Condicionalidade III (Redução de Desigualdades e vigência de lei estadual redistributiva de ICMS Educação) representou o maior gargalo nacional**, respondendo isoladamente pela desabilitação de **1.930 redes de ensino**.
                Adicionalmente, **a Condicionalidade I (provimento de diretores por mérito e desempenho) gerou 575 reprovações**, enquanto **a Condicionalidade II (presença mínima de 80% no Saeb) desabilitou 417 redes**.
                A tela fornece **o texto oficial de cada dispositivo normativo e um roteiro operacional de providências administrativas** para que as secretarias de educação corrijam suas pendências antes dos prazos de corte do próximo ciclo.
                """
            )

        with st.container(border=True):
            st.markdown(
                """
                #### 🗺️ 2. Mapas Interativos em 3 Fases (Brasil, Região e Município)
                **A visualização espacial foi arquitetada em três escalas territoriais contínuas para assegurar clareza cognitiva em apresentações e reuniões de trabalho.**
                Na **Fase 1 (Brasil)**, é possível diagnosticar de imediato a disparidade macrorregional nos índices de habilitação e nos volumes totais captados por cada Unidade da Federação.
                Na **Fase 2 (Regiões do País)**, o gestor pode isolar blocos regionais homogêneos (Norte, Nordeste, Centro-Oeste, Sudeste ou Sul) e comparar a eficiência relativa entre os estados vizinhos.
                Por fim, na **Fase 3 (Municípios)**, o painel projeta a malha cartográfica detalhada da UF selecionada e oferece uma **Ficha Técnica Enxuta**, desenhada para **apresentar todas as variáveis financeiras, pedagógicas e cadastrais em um único quadro compacto sem poluição visual**.
                """
            )

        with st.container(border=True):
            st.markdown(
                """
                #### 🏆 3. Ranking por Unidade da Federação com Micrográficos
                **Esta seção organiza a classificação estruturada de todas as 27 Unidades da Federação em uma tabela analítica com mapa de calor numérico e barras visuais de progresso.**
                Cada linha integra **micrográficos com a taxa efetiva de redes habilitadas e a proporção de municípios contemplados**, permitindo identificar instantaneamente quais estados alcançaram maior sucesso institucional.
                A ferramenta possibilita **filtrar exclusivamente as UFs que sofreram perda líquida de recursos em relação a 2025**, viabilizando análises direcionadas de risco fiscal e priorização de suporte técnico.
                """
            )

    with col_t2:
        with st.container(border=True):
            st.markdown(
                """
                #### 📈 4. Linha Histórica de Recursos & Matriz Estratégica "Como Agir"
                **A Emenda Constitucional nº 108/2020 determinou uma progressão escalonada da participação federal no FUNDEB**, elevando a complementação total da União de 12% da receita dos fundos em 2021 para 23% em 2026.
                Nesse contexto, **a parcela do VAAR expandiu-se expressivamente de 0,00% nos ciclos de 2021 e 2022 para 0,75% em 2023, 1,50% em 2024, 2,00% em 2025 e atingiu sua cota plena de 2,50% em 2026**, representando um volume superior a R$ 7,5 bilhões.
                Para apoiar os gestores públicos, **esta aba reúne uma matriz de intervenção prática que detalha as ações de curto e médio prazo necessárias para regularizar a habilitação e maximizar os indicadores de atendimento e aprendizagem**, incluindo um **Checklist Interativo de Prontidão** para reuniões de gabinete.
                """
            )

        with st.container(border=True):
            st.markdown(
                r"""
                #### 🧮 5. Simulador VAAR com Diferenciação Rigorosa (Estadual vs Municipal)
                **O simulador matemático reproduz fielmente as diretrizes da Nota Técnica Inep nº 23/2022 e do modelo de referência Simulador-VAAR-PI**, respeitando as competências constitucionais de cada ente federativo.
                Para **redes municipais**, a expansão do atendimento escolar no Índice de Expansão da Educação Infantil (IEE) é avaliada obrigatoriamente na **Educação Infantil (Creche e Pré-Escola)**, e os ganhos pedagógicos recaem sobre o Ensino Fundamental.
                Para **redes estaduais**, a avaliação de atendimento concentra-se exclusivamente no **Ensino Médio**, medindo tanto a evolução de matrículas quanto a redução das taxas de abandono escolar.
                O mecanismo calcula **o peso ponderado das matrículas através da função exponencial $w = 2 - e^{-4 \cdot \text{IND}}$ (onde $w \in [1, 2]$)** e exibe **a memória descritiva do cálculo passo a passo com equações em LaTeX e estimativa do impacto financeiro em Reais**.
                """
            )

        with st.container(border=True):
            st.markdown(
                """
                #### 🛡️ 6. Qualidade dos Dados, Transparência & Verificação SHA-256
                **O compromisso primordial do painel é com a integridade absoluta dos dados: nenhuma variável é inventada, estimada aleatoriamente ou preenchida com valores artificiais.**
                Todos os registros derivam diretamente das publicações oficiais do **FNDE (Portarias e Resoluções de rateio), INEP (Censo Escolar, Ideb, proficiências Saeb e INSE) e NIC.br/SIMET (Conectividade Escolar)**.
                A aba de auditoria executa **testes automáticos em tempo real demonstrando que a soma das parcelas fecha perfeitamente com o total da União ($\text{VAAF} + \text{VAAT} + \text{VAAR} = \text{Total}$) em 100% dos 5.596 entes avaliados**, além de listar as **assinaturas criptográficas SHA-256** de todos os arquivos de dados para auditoria pública independente.
                """
            )
