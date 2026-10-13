"""Visão Detalhada das Condicionalidades e Análise de Perda de Habilitação."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from fundeb.services.analytics import AnalyticsService
from fundeb.ui.components import metric_card, format_int, format_percent
from fundeb.ui.charts import chart_ranking_horizontal


def render_condicionalidades_view(analytics: AnalyticsService) -> None:
    st.subheader("⚖️ Perda de Habilitação ao VAAR 2026 — Por Condicionalidade")
    st.markdown(
        """
        Para receber a Complementação VAAR, a rede de ensino precisa ser previamente **habilitada**,
        cumprindo **cumulativamente todas as 5 condicionalidades** do Art. 14, § 1º da Lei nº 14.113/2020.
        A reprovação em **qualquer uma** delas desabilita a rede do rateio de recursos.
        """
    )

    gargalos_ranking = analytics.gargalos_condicionalidade()
    gargalos_ordem = analytics.condicionalidades_ordem_legal()
    total_nao_hab = len(analytics.df[~analytics.df["habilitado"]])

    st.markdown(
        f"**Universo analisado:** Total de **{format_int(total_nao_hab)} redes não habilitadas** que reprovaram em cada condicionalidade *(uma rede pode reprovar em mais de uma condicionalidade)*."
    )

    # 5 Colunas na ordem legal das condicionalidades (I a V)
    cols = st.columns(len(gargalos_ordem))
    for col, g in zip(cols, gargalos_ordem):
        with col:
            metric_card(
                title=g.codigo,
                value=f"{format_int(g.reprovacoes_nao_habilitadas)} redes",
                subtitle=f"{format_percent(g.pct_sobre_nao_habilitadas)} das não habilitadas",
                delta=f"{g.nome_curto.split('—')[1].strip() if '—' in g.nome_curto else g.nome_curto}",
                delta_color="red",
            )

    st.markdown("---")

    # Gráfico de barras horizontal do funil de perdas
    col_chart, col_tabela = st.columns([3, 2])

    with col_chart:
        st.markdown("##### 📊 Funil de Reprovações nas Redes Desabilitadas (Ranking por Impacto)")
        df_chart = pd.DataFrame([
            {
                "Condicionalidade": f"{g.codigo}: {g.nome_curto.split('—')[1].strip() if '—' in g.nome_curto else g.nome_curto}",
                "Reprovações": g.reprovacoes_nao_habilitadas,
            }
            for g in gargalos_ranking
        ])

        fig = chart_ranking_horizontal(
            df_chart,
            categoria_col="Condicionalidade",
            valor_col="Reprovações",
            titulo="Redes Não Habilitadas que Reprovaram em Cada Condicionalidade",
            destacar_primeiro=True,
            cor_destaque="#DC2626",
            formato_rotulo="%{x:,.0f} redes",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_tabela:
        st.markdown("##### 📋 Síntese Numérica por Condicionalidade")
        df_tabela = pd.DataFrame([
            {
                "Condicionalidade": g.codigo,
                "Inciso Legal": g.artigo,
                "Redes Desabilitadas": f"{g.reprovacoes_nao_habilitadas:,}".replace(",", "."),
                "% s/ Não Hab.": f"{g.pct_sobre_nao_habilitadas:.1f}%",
                "Total Geral Reprov.": f"{g.total_reprovacoes:,}".replace(",", "."),
            }
            for g in gargalos_ordem
        ])
        st.dataframe(df_tabela, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Expansão detalhada de cada Condicionalidade LISTADA ESTRITAMENTE NA ORDEM LEGAL (I a V)
    st.subheader("📖 Detalhamento Normativo e Guia de Ação por Condicionalidade")
    st.caption("As condicionalidades estão dispostas na ordem legal dos incisos I a V do § 1º do art. 14 da Lei nº 14.113/2020:")

    for g in gargalos_ordem:
        with st.expander(f"🔹 {g.codigo} — {g.nome_curto} ({format_int(g.reprovacoes_nao_habilitadas)} redes reprovadas)", expanded=(g.codigo in ("Cond. I", "Cond. V"))):
            c_info1, c_info2 = st.columns([3, 2])
            with c_info1:
                st.markdown("**Texto Oficial da Lei nº 14.113/2020 (Art. 14, § 1º):**")
                st.markdown(f"> *\"{g.descricao_tecnica}\"*")
            with c_info2:
                st.markdown("**Como Agir para Não Perder Habilitação:**")
                st.info(g.como_agir)

            if g.codigo == "Cond. V":
                st.markdown("---")
                st.markdown("#### 📘 Especificações Técnicas de Alinhamento Curricular à BNCC (MEC/SEB)")
                st.caption("O alinhamento normativo e pedagógico exige a comprovação formal dos seguintes blocos estruturantes:")

                tab_bncc, tab_anexos, tab_homolog = st.tabs([
                    "1. BNCC Geral (Núcleo Comum)",
                    "2. Anexos e Cadernos Obrigatórios",
                    "3. Homologação & Simec",
                ])

                with tab_bncc:
                    st.markdown(
                        """
                        **Componentes Obrigatórios da BNCC Geral:**
                        - **10 Competências Gerais da Educação Básica:** Devem permear todo o currículo, articulando conhecimentos, habilidades cognitivas, atitudes e valores socioemocionais e cidadãos.
                        - **Educação Infantil:**
                          * **6 Direitos de Aprendizagem e Desenvolvimento:** *Conviver, Brincar, Participar, Explorar, Expressar e Conhecer-se*.
                          * **5 Campos de Experiências:** (1) O eu, o outro e o nós; (2) Corpo, gestos e movimentos; (3) Traços, sons, cores e formas; (4) Escuta, fala, pensamento e imaginação; (5) Espaços, tempos, quantidades, relações e transformações.
                          * **Objetivos de Aprendizagem:** Definidos para 3 grupos etários: bebês (0 a 1a6m), crianças bem pequenas (1a7m a 3a11m) e crianças pequenas (4a a 5a11m).
                        - **Ensino Fundamental (1º ao 9º ano):**
                          * 5 Áreas do Conhecimento (Linguagens, Matemática, Ciências da Natureza, Ciências Humanas, Ensino Religioso) com seus componentes curriculares.
                          * Matriz vertical com Unidades Temáticas, Objetos de Conhecimento e **Habilidades codificadas progressivas** (ex: `EF01LP01` a `EF09MA06`).
                        - **Ensino Médio (Redes Estaduais):**
                          * Formação Geral Básica (FGB) estruturada nas 4 grandes áreas do conhecimento articulada aos Itinerários Formativos (aprofundamento acadêmico e Formação Técnica e Profissional - FTP), conforme a Lei nº 13.415/2017 e a Lei nº 14.945/2024.
                        """
                    )

                with tab_anexos:
                    st.markdown(
                        """
                        **Cadernos Anexos e Temas Transversais Obrigatórios:**
                        - **♿ Anexo de Educação Especial na Perspectiva Inclusiva:**
                          * Diretrizes para o Atendimento Educacional Especializado (AEE) e Salas de Recursos Multifuncionais (SRM);
                          * Aplicação dos princípios do **Desenho Universal para a Aprendizagem (DUA)** no planejamento pedagógico;
                          * Protocolos de acessibilidade pedagógica, adaptação e flexibilização curricular para estudantes com deficiência, Transtorno do Espectro Autista (TEA) e altas habilidades/superdotação.
                        - **✊ Anexo / Matriz de Educação para as Relações Étnico-Raciais (ERER):**
                          * Cumprimento mandatório das **Leis Federais nº 10.639/2003 e nº 11.645/2008**;
                          * Integração curricular explícita de História e Cultura Afro-Brasileira e dos Povos Indígenas nos componentes de História, Arte, Língua Portuguesa e Geografia;
                          * Matriz formativa antirracista e valorização da identidade e diversidade cultural brasileira.
                        - **🌾 Anexo de Modalidades Específicas do Território:**
                          * Cadernos curriculares contextualizados para **Educação do Campo** (pedagogia da alternância e saberes da terra), **Educação Escolar Indígena** (bilinguismo e cosmologias próprias), **Educação Escolar Quilombola** e Educação de Jovens e Adultos (EJA), conforme a realidade local da rede.
                        - **💻 Anexo de Educação Digital e Computação:**
                          * Alinhamento às Diretrizes sobre Computação na Educação Básica (**Resolução CNE/CEB nº 1/2022**), estruturado nos eixos: Cultura Digital, Mundo Digital e Pensamento Computacional.
                        """
                    )

                with tab_homolog:
                    st.markdown(
                        """
                        **Rito Normativo de Homologação e Comprovação no Simec:**
                        1. **Apreciação e Parecer pelo Conselho de Educação:**
                           - **Para Sistemas Próprios Municipais:** Emissão de Parecer favorável e **Resolução Normativa do Conselho Municipal de Educação (CME)** aprovando o Documento Curricular da rede;
                           - **Para Redes Estaduais ou Municípios Vinculados:** Homologação pelo **Conselho Estadual de Educação (CEE)** do Currículo Referência Estadual (pelo regime ProBNCC), com ato de adesão formal emitido pelo Executivo Municipal.
                        2. **Publicação em Diário Oficial:**
                           - Publicação compulsória da Resolução do Conselho em Diário Oficial do Município (DOM) ou Estado (DOE), com número, data de circulação e ementa explícita.
                        3. **Submissão e Validação no Simec (MEC/SEB):**
                           - Upload do Documento Curricular Completo (com todos os anexos e matrizes);
                           - Cópia autenticada da Resolução/Parecer do Conselho e página do Diário Oficial;
                           - Declaração de conformidade e Plano de Ação de formação continuada de professores e revisão dos Projetos Político-Pedagógicos (PPP) das escolas da rede.
                        """
                    )
