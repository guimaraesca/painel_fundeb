"""Página Inicial: Guia Executivo de Leitura, Estrutura Temática e Acesso Rápido a Dados."""
from __future__ import annotations

import textwrap
from pathlib import Path
import streamlit as st
import pandas as pd

from fundeb.services.analytics import AnalyticsService
from fundeb.ui.components import (
    metric_card,
    format_currency,
    format_currency_full,
    format_percent,
    format_int,
    format_decimal,
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

    # ------------------------------------------------------------- NOTA TÉCNICA Nº 01/2026
    with st.expander("📑 NOTA TÉCNICA Nº 01/2026 — Metodologia, Dados Oficiais & Assinatura da Produção", expanded=False):
        st.markdown(
            r"""
            ### 🏛️ NOTA TÉCNICA Nº 01/2026
            **Assunto:** Metodologia de Cálculo, Auditoria Normativa e Consolidação dos Recursos do FUNDEB e da Complementação VAAR 2026  
            **Abrangência:** 5.596 Entes Federados (26 Redes Estaduais, Distrito Federal e 5.569 Redes Municipais)  
            **Exercício de Referência:** Ciclo Orçamentário e Financeiro de 2026  

            ---

            ## 1. Mapeamento Legal e Condicionalidades de Gestão (Habilitação)

            A participação na distribuição dos recursos da Complementação-VAAR exige o cumprimento prévio de condicionalidades de melhoria de gestão, estabelecidas no art. 14 da Lei nº 14.113/2020. O não cumprimento de qualquer uma destas condicionalidades inabilita o ente federado a receber o repasse, independentemente de seus resultados nos indicadores pedagógicos.

            ### 1.1. As 5 Condicionalidades de Gestão (Detalhamento Técnico e Ritos de Habilitação)

            1. **Provimento de Cargo de Gestor Escolar (Inciso I) — Critérios Técnicos de Mérito e Consulta Comunitária:**
               - **Fundamentação Legal:** Art. 14, § 1º, inciso I da Lei nº 14.113/2020 e Meta 19 do Plano Nacional de Educação (PNE - Lei nº 13.005/2014).
               - **Modelos de Provimento Aceitos:**
                 * *Opção A (Mérito e Desempenho Exclusivo):* Processo seletivo público impessoal baseado em exame de conhecimentos em gestão pedagógica, administrativa e financeira, prova de títulos e apresentação de Plano de Gestão Escolar;
                 * *Opção B (Eleição com Pré-Qualificação Técnica):* Consulta direta ou eleição qualificada com a comunidade escolar (professores, funcionários, estudantes e pais), realizada **obrigatoriamente** a partir de lista tríplice de candidatos previamente aprovados em avaliação técnica de mérito e desempenho.
               - **Vedações Absolutas:** Indicação política discricionária ou livre nomeação sem processo seletivo prévio inabilita imediatamente a rede de ensino.
               - **Comprovação no Simec:** Upload da Lei ou Decreto municipal/estadual regulamentador, edital do processo seletivo vigente, atas de apuração e termos de posse dos diretores.

            2. **Participação nas Avaliações do Saeb (Inciso II) — Quórum Mínimo de 80% e Busca Ativa:**
               - **Fundamentação Legal:** Art. 14, § 1º, inciso II da Lei nº 14.113/2020 e Portarias Normativas anuais do Inep.
               - **Regra de Corte Estrita:** A rede de ensino deve atingir taxa de participação mínima de **80% (fator $\ge 0{,}80$)** dos estudantes matriculados em **cada ano escolar avaliado** (2º ano, 5º ano e 9º ano do Ensino Fundamental; 3ª série do Ensino Médio), escola a escola e no agregado da rede. Não há arredondamento para cima (índice de 79,9% resulta em inabilitação).
               - **Fórmula de Aferição do Inep:**
                 $$\text{Taxa de Participação} = \frac{\text{Total de Estudantes Presentes nos Exames}}{\text{Matrículas Registradas no Censo Escolar Preliminar}}$$
               - **Ações Operacionais de Gestão:** Monitoramento prévio de listas de alunos, comitê de busca ativa escolar no dia da aplicação, garantia de transporte escolar e solicitação tempestiva de reaplicação nas hipóteses autorizadas de força maior.

            3. **Redução das Desigualdades Educacionais (Inciso III) — Equidade Socioeconômica e Racial:**
               - **Fundamentação Legal:** Art. 14, § 1º, inciso III da Lei nº 14.113/2020 e Resoluções MEC/Inep (ciclo metodológico da Nota Técnica nº 23/2022).
               - **Dimensões Estruturantes Avaliadas pelo Inep:**
                 * *Equidade Socioeconômica ($INE\text{-}S$):* Elevação na proporção de estudantes do estrato socioeconômico mais vulnerável (definido por recortes em quantis/mediana do INSE) que alcançam aprendizado adequado em Língua Portuguesa e Matemática;
                 * *Equidade Racial ($INE\text{-}R$):* Redução do hiato de proficiência entre estudantes autodeclarados Pretos, Pardos ou Indígenas (PPI) e os demais estratos populacionais;
                 * *Regime Amostral para Redes Pequenas:* Aplicação de modelos estatísticos de vizinhança ou média estadual para entes com amostras reduzidas, protegendo redes pequenas de exclusão randômica;
                 * *Tolerância por Porte:* Verificação de $\Delta \ge 0$ observada a Tabela de Margem de Erro por porte populacional.

            4. **Regime de Colaboração / ICMS Educacional (Inciso IV) — Cota-Parte Redistributiva e Equidade:**
               - **Fundamentação Legal:** Art. 14, § 1º, inciso IV da Lei nº 14.113/2020, Art. 158, parágrafo único, II da Constituição Federal e Art. 3º da Emenda Constitucional nº 108/2020.
               - **Obrigação Aplicável aos Estados:** Aprovação e vigência de lei estadual que regulamente o repasse da cota-parte municipal do ICMS (mínimo de 10%, podendo chegar a 35%) com base estrita em indicadores de melhoria na aprendizagem e de aumento da equidade educacional.
               - **Impacto sobre as Redes Municipais:** A elegibilidade dos municípios depende da existência da lei estadual regulamentada. Cabe aos municípios a colaboração técnica, articulação e fornecimento tempestivo de dados educacionais aos sistemas estaduais de avaliação.
               - **Validação no Simec:** Comprovação da lei estadual promulgada e das tabelas de rateio financeiro aferidas pelos órgãos de controle.

            5. **Referenciais Curriculares (Inciso V) — Alinhamento à BNCC, Anexos Obrigatórios e Homologação:**
               - **Fundamentação Legal:** Art. 14, § 1º, inciso V da Lei nº 14.113/2020, Resolução CNE/CP nº 2/2017 (BNCC Geral), LDB (Lei nº 9.394/1996) e marcos correlatos (como a Lei nº 14.945/2024 para o Ensino Médio).
               - **Estrutura Geral Obrigatória da BNCC:**
                 * *10 Competências Gerais da Educação Básica:* Transversais a todas as etapas, assegurando a mobilização integrada de conhecimentos, habilidades cognitivas e socioemocionais, atitudes e valores éticos;
                 * *Educação Infantil:* Garantia expressa dos **6 Direitos de Aprendizagem e Desenvolvimento** (*Conviver, Brincar, Participar, Explorar, Expressar e Conhecer-se*), estruturação pelos **5 Campos de Experiências** e objetivos de aprendizagem para os três grupos etários (bebês, crianças bem pequenas e crianças pequenas);
                 * *Ensino Fundamental (1º ao 9º ano):* 5 áreas do conhecimento, componentes curriculares, unidades temáticas, objetos de conhecimento e progressão vertical de habilidades codificadas (ex: `EF01LP01` a `EF09MA06`);
                 * *Ensino Médio (Redes Estaduais):* Formação Geral Básica (FGB) articulada às 4 áreas do conhecimento e aos Itinerários Formativos (aprofundamento acadêmico e Formação Técnica e Profissional - FTP), respeitando as diretrizes da Lei nº 13.415/2017 e da Lei nº 14.945/2024.
               - **Anexos e Cadernos Temáticos Obrigatórios:**
                 * *Anexo de Educação Especial na Perspectiva Inclusiva:* Diretrizes de Atendimento Educacional Especializado (AEE), princípios do Desenho Universal para a Aprendizagem (DUA), flexibilizações curriculares e eliminação de barreiras para estudantes com deficiência, TEA e altas habilidades/superdotação;
                 * *Anexo / Matriz de Educação para as Relações Étnico-Raciais (ERER):* Cumprimento obrigatório das **Leis Federais nº 10.639/2003 e nº 11.645/2008**, com inserção transversal da História e Cultura Afro-Brasileira e dos Povos Indígenas e objetivos formativos antirracistas;
                 * *Anexo de Modalidades Específicas do Território:* Cadernos curriculares contextualizados para Educação do Campo (saberes da terra/pedagogia da alternância), Educação Escolar Indígena (bilinguismo/processos próprios), Educação Escolar Quilombola e EJA, quando existentes no território;
                 * *Anexo de Educação Digital e Pensamento Computacional:* Alinhamento à Resolução CNE/CEB nº 1/2022 (eixos: cultura digital, mundo digital e pensamento computacional).
               - **Governança, Homologação e Comprovação no Simec:**
                 * *Ato Normativo do Conselho:* Parecer favorável e Resolução do **Conselho Municipal de Educação (CME)**, para sistemas municipais próprios; ou do **Conselho Estadual de Educação (CEE)**, para redes estaduais ou municípios vinculados (via regime ProBNCC / adesão formal ao Currículo Referência Estadual);
                 * *Publicação Oficial:* Publicação compulsória da Resolução de Homologação no Diário Oficial do Município (DOM) ou Estado (DOE);
                 * *Inserção no Simec (MEC/SEB):* Upload tempestivo do Documento Curricular integral com anexos, cópia do ato de homologação, comprovação no Diário Oficial e plano de revisão dos Projetos Político-Pedagógicos (PPP) das escolas.

            ### 1.2. Órgãos de Verificação, Prazos e Fluxo

            * **Fluxo de Habilitação:** Os entes declaram e comprovam o cumprimento no Sistema Integrado de Monitoramento Execução e Controle (**Simec**) do MEC.
            * **Órgãos Validadores:**
              * O **Inep** afere as condicionalidades 2 e 3 (via microdados do Saeb e Censo Escolar).
              * O **Ministério da Educação (Secretaria de Educação Básica - SEB)**, Conselhos de Educação e Secretarias Estaduais aferem as condicionalidades 1, 4 e 5.
            * **Prazos:** As resoluções do MEC estabelecem cronogramas anuais rígidos (geralmente até setembro do ano anterior ao repasse) para a inserção das leis, decretos e normativas no Simec.

            ### 1.3. Excepcionalidade e Calamidade Pública

            Situações de força maior ou estado de calamidade pública reconhecidos pelo Governo Federal (ex: desastres ambientais, inundações ou epidemias) disparam **gatilhos de neutralidade**. Nestes cenários, a avaliação de desempenho (como o cálculo de evolução de indicadores) é suspensa para não prejudicar o ente afetado. A rede é considerada tacitamente habilitada na respectiva condicionalidade, ou utiliza-se o último dado válido anterior ao evento crítico, garantindo a manutenção do repasse e a estabilidade financeira durante a recuperação da rede de ensino.

            ---

            ## 2. Metodologia do Indicador VAAR-Atendimento (50% do montante)

            Este módulo recompensa as redes que demonstram evolução na manutenção dos alunos no sistema de ensino, combatendo o abandono escolar.

            ### 2.1. Conceito e Variáveis Base

            O cálculo fundamenta-se nos dados de rendimento e movimento do Censo Escolar:
            * $M$: População de matrículas prioritárias (apenas matrículas regulares da rede, excluindo EJA e outras categorias não contabilizadas na base principal do VAAR, conforme regulamentação específica).
            * **Abandono Escolar:** Estudantes que deixaram de frequentar a escola no decorrer do ano letivo, sem solicitação de transferência.
            * $SIR$ **(Sem Informação de Rendimento ou Movimento):** Matrículas cujo status final não foi informado pela escola no encerramento do Censo. O normativo penaliza a omissão aplicando um **fator de desconto de 0,5** sobre essas ocorrências.
            * **Nacionalidade Estrangeira:** Alunos estrangeiros recém-ingressos no país possuem regras de transição temporal e, em determinados cenários normativos, são excluídos da base de cômputo negativo caso não possuam proficiência na língua nacional, evitando desincentivar a matrícula de imigrantes/refugiados.

            ### 2.2. Fórmula do Indicador e Evolução

            O indicador de atendimento mensura a taxa de sucesso da permanência escolar para a rede $r$ no ano letivo $t$:

            $$VAAR\_Atendimento_{r,t} = 1 - \frac{Abandono_{r,t} + 0{,}5 \times SIR_{r,t}}{M_{r,t}}$$

            Para que a rede municipal ou estadual seja elegível aos recursos financeiros deste módulo, deve demonstrar evolução em relação à edição anterior ($t-1$):

            $$\Delta VAAR\_Atendimento_r = VAAR\_Atendimento_{r,t} - VAAR\_Atendimento_{r,t-1} \ge 0$$

            ### 2.3. Margem de Flutuação (Tolerância Estatística)

            Devido à alta volatilidade estatística em redes com baixo número de alunos, o Inep aplica uma **Tabela de Margem de Flutuação**. Uma rede que apresente um $\Delta VAAR\_Atendimento_r$ negativo, mas que esteja contido dentro do limite de tolerância estabelecido para o seu porte populacional (ex: redes com até 500 matrículas possuem maior tolerância percentual do que redes com mais de 10.000 matrículas), será considerada habilitada por empate estatístico.

            ### 2.4. Coeficiente de Distribuição ($C_{atend}^r$) e Repasse em Reais

            Para os entes habilitados, o peso das matrículas é ajustado linearmente no intervalo contínuo $[1, 2]$. O ente com o menor resultado positivo entre os habilitados recebe peso 1, e o de melhor resultado recebe peso 2, garantindo progressividade financeira:

            $$peso_{atend}^r = 1 + \left( \frac{VAAR\_Atendimento_{r,t} - \min(VAAR\_Atendimento_{t})}{\max(VAAR\_Atendimento_{t}) - \min(VAAR\_Atendimento_{t})} \right)$$

            O coeficiente financeiro da rede $r$ e o repasse em reais (R$) são dados por:

            $$C_{atend}^r = \frac{M_r \times peso_{atend}^r}{\sum_{i=1}^{n} (M_i \times peso_{atend}^i)}$$

            $$Repasse_{Atend}^r = C_{atend}^r \times (0{,}50 \times \text{Montante Global VAAR})$$

            ---

            ## 3. Metodologia do Indicador VAAR-Aprendizagem (50% do montante)

            O módulo de aprendizagem avalia de forma combinada o desempenho cognitivo, o fluxo escolar e a equidade do sistema educacional.

            ### 3.1. Fórmula Geral do Indicador

            A métrica síntese da rede $r$ no ano $t$ é produto de três dimensões estruturais:

            $$VAAR\_Aprendizagem_{r,t} = Inad_{r,(t,t-1)} \times IPSaeb_{r,t} \times IndEqui_{r,t}$$

            ### 3.2. Decomposição das Variáveis

            * **Índice de Nível e Avanço de Desempenho ($Inad$):**  
              Recompensa o patamar atual de qualidade e a melhoria contínua, ponderado pelo sucesso no fluxo escolar (Taxa de Aprovação - $TAp$):
              * $IND$: Índice de Nível de Desempenho (peso 0,3);
              * $IAD$: Índice de Avanço de Desempenho (peso 0,7);
              * Ambos consideram a proporção de alunos que atingem o nível de aprendizado adequado no Saeb em Língua Portuguesa e Matemática. A fórmula padronizada passa por um reescalonamento matemático rígido para enquadrar os resultados de uma escala original teórica (ex: $[-7, 10]$) para o intervalo normatizado final $[0, 1]$, utilizando a transformação linear:
                $$Inad\_Norm = \frac{Inad_{Bruto} - (-7)}{10 - (-7)}$$

            * **Indicador de Participação no Saeb ($IPSaeb$):**  
              Mede a taxa de presença no dia do exame, condicionada ao mínimo de 80% (0,80) e limitada ao teto estatístico de 1,0 (100%):
              * Se $IPSaeb_{r,t} < 0{,}80 \rightarrow$ a rede é inabilitada.
              * O valor multiplica a equação central estimulando redes com altas taxas de presença contínua.

            * **Índice de Equidade ($IndEqui$):**  
              Mede a diminuição das lacunas de aprendizado para grupos historicamente vulnerabilizados:
              * **$INE\text{-}S$ (Equidade Socioeconômica):** Proporção de alunos do estrato socioeconômico mais vulnerável (definido por recortes em quantis: quartis, tercis ou mediana, dependendo do porte populacional da rede para garantir validade amostral) que alcançam a proficiência adequada.
              * **$INE\text{-}R$ (Equidade Racial):** Proporção de estudantes autodeclarados Pretos, Pardos ou Indígenas (PPI) que alcançam a proficiência adequada.
              * **Imputação:** Em redes de pequeno porte onde a amostragem destes grupos é insuficiente para gerar significância estatística, aplica-se a média regional/estadual ou modelos de vizinhança para não excluir o município financeiramente.

            ### 3.3. Cálculo da Evolução e Margem de Erro

            Para habilitar-se ao montante, a rede precisa apresentar evolução positiva entre as edições do Saeb:

            $$\Delta VAAR\_Aprendizagem_r = VAAR\_Aprendizagem_{r,t} - VAAR\_Aprendizagem_{r,t-1} \ge 0$$

            Da mesma forma que no Atendimento, aplica-se margem de erro baseada no número de alunos presentes nos exames, evitando que ruídos amostrais penalizem redes de pequeno porte.

            ### 3.4. Coeficiente de Distribuição ($C_{aprend}^r$) e Repasse em Reais

            O peso final ($peso_{aprend}^r$) sofre transformação linear contínua para garantir que o repasse per capita do município com o melhor desempenho da federação seja exatamente o dobro daquele com o menor desempenho habilitado:

            $$peso_{aprend}^r = 1 + \left( \frac{VAAR\_Aprendizagem_{r,t} - \min}{\max - \min} \right)$$

            $$C_{aprend}^r = \frac{M_r \times peso_{aprend}^r}{\sum_{i=1}^n (M_i \times peso_{aprend}^i)}$$

            $$Repasse_{Aprend}^r = C_{aprend}^r \times (0{,}50 \times \text{Montante Global VAAR})$$

            ---

            ## 4. Especificações Técnicas para Desenvolvimento de Sistemas (Painel e Simulador)

            A arquitetura do painel de monitoramento e do simulador financeiro exige o cruzamento determinístico de múltiplas bases públicas, operando em um fluxo condicional estrito.

            ### 4.1. Mapeamento de Bases de Dados Oficiais

            1. **Censo Escolar (Inep):** Fornece as variáveis de matrículas totais ($M$), Taxa de Aprovação ($TAp$), Abandono e os registros de $SIR$. Extração via microdados e Sinopse Estatística anual.
            2. **Microdados do Saeb (Inep):** Fornece proficiência em Matemática e Língua Portuguesa, contagem de presentes/matriculados ($IPSaeb$) e microdados do questionário do aluno para extração de nível socioeconômico (NSE) e raça/cor.
            3. **Simec (MEC):** Integração para extração do status booleano das 5 condicionalidades de gestão do Art. 14 da Lei nº 14.113/2020.
            4. **Siope e Portarias do FNDE:** Extração do montante global (R$) projetado para a Complementação-VAAR do Fundeb no exercício financeiro simulado.

            ### 4.2. Dicionário de Variáveis de Entrada Requeridas (Simulador)

            | Variável | Tipo | Origem | Descrição |
            | :--- | :--- | :--- | :--- |
            | `Cod_Ibge` | Int | IBGE | Código identificador unívoco do município/estado |
            | `Status_Condicionalidades` | Boolean | Simec | `True` se cumpriu os 5 requisitos; `False` caso contrário |
            | `Matriculas_Vaal_R` | Int | FNDE | Número base de matrículas consideradas para o ente ($M_r$) |
            | `Tx_Abandono_T` e `T_1` | Float | Censo | Taxa de abandono escolar na rede (ano atual e anterior) |
            | `Total_SIR` | Int | Censo | Contagem absoluta de alunos sem informação de rendimento |
            | `Proficiencia_LP_MT` | Float | Saeb | Percentual de alunos com aprendizado adequado por etapa |
            | `IPSaeb` | Float | Saeb | Taxa de participação nos exames ($\ge 0{,}80$) |
            | `INE_S` e `INE_R` | Float | Saeb | Indicadores calculados de equidade socioeconômica e racial |
            | `Orcamento_Global_VAAR` | Monetário | FNDE | Valor em R$ correspondente a 2,5% da receita total do Fundeb |

            ### 4.3. Passo a Passo do Algoritmo de Cálculo do Simulador

            1. **Filtro de Elegibilidade Primária:**  
               Verificar a matriz `Status_Condicionalidades`. Redes onde a variável for `False` recebem repasse nulo ($\text{Repasse} = 0{,}00$, equivalente a R\$ 0,00) imediatamente e são removidas da base de rateio financeiro.
            2. **Processamento do VAAR-Atendimento:**  
               - Calcular $VAAR\_Atendimento_{r,t}$ combinando abandono e penalização de $SIR$ (peso 0,5).  
               - Subtrair o ano-base ($t-1$). Se $\Delta < 0$, checar se a diferença está dentro da Tabela de Margem de Flutuação. Redes fora da margem recebem peso zero neste módulo.
            3. **Processamento do VAAR-Aprendizagem:**  
               - Calcular o $Inad$ e normalizar o valor aplicando as ponderações $0{,}3 \times IND$ e $0{,}7 \times IAD$.  
               - Verificar $IPSaeb \ge 0{,}80$.  
               - Calcular equidades socioeconômicas e raciais imputando as médias estaduais onde a amostra for estatisticamente insuficiente, fechando o $IndEqui$.  
               - Multiplicar $Inad \times IPSaeb \times IndEqui$.  
               - Calcular o $\Delta$ em relação ao ano-base, aplicando a margem de erro por porte populacional. Redes não habilitadas são desconsideradas do rateio deste módulo.
            4. **Reescalonamento de Pesos:**  
               - Para as redes habilitadas em *Atendimento*, calcular os valores mínimos e máximos nacionais. Aplicar a transformação linear projetando o `peso_atend` de todos os habilitados para o intervalo contínuo $[1, 2]$.  
               - Repetir o mesmo procedimento exato (Min/Max independentes) para os habilitados em *Aprendizagem*, gerando o `peso_aprend` no intervalo $[1, 2]$.
            5. **Cálculo de Quotas e Repasses Finais:**  
               - Calcular a soma nacional das matrículas ponderadas no eixo Atendimento: $\sum (Matriculas \times peso\_atend)$.  
               - Calcular o coeficiente da rede dividindo sua matrícula ponderada pela soma nacional ($C_{atend}$).  
               - Multiplicar o $C_{atend}$ por `(Orcamento_Global_VAAR * 0.5)`.  
               - Repetir o processo para calcular $C_{aprend}$ e multiplicar por `(Orcamento_Global_VAAR * 0.5)`.
            6. **Agregação:**  
               - O valor final simulado a ser exibido no painel para a rede será a soma monetária de seus ganhos nos dois eixos: $\text{Repasse Total} = Repasse_{Atend} + Repasse_{Aprend}$.
            """
        )

        st.markdown("#### 📥 Download das Bases de Dados Consolidadas")
        st.caption("Acesse os dados brutos e processados para verificação independente e uso em planilhas ou sistemas analíticos:")

        c_dl1, c_dl2, c_dl3 = st.columns(3)
        with c_dl1:
            p_xlsx = Path("outputs/Fundeb_2026_base_consolidada.xlsx")
            if p_xlsx.exists():
                st.download_button(
                    label="📥 Baixar Planilha Consolidada (.xlsx)",
                    data=p_xlsx.read_bytes(),
                    file_name="Fundeb_2026_base_consolidada.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Planilha completa com 42 colunas auditadas cobrindo os 5.596 entes federados.",
                    use_container_width=True,
                )
        with c_dl2:
            csv_data = df.to_csv(sep=";", index=False, decimal=",").encode("utf-8-sig")
            st.download_button(
                label="📥 Baixar Base em CSV (Padrão Excel BR)",
                data=csv_data,
                file_name="fundeb_2026_recursos_condicionalidades.csv",
                mime="text/csv",
                help="Arquivo CSV com separador ponto-e-vírgula (;) pronto para abertura direta no Microsoft Excel.",
                use_container_width=True,
            )
        with c_dl3:
            p_json = Path("data/processed/base_clean.json")
            if p_json.exists():
                st.download_button(
                    label="📥 Baixar Base Processada (.json)",
                    data=p_json.read_bytes(),
                    file_name="base_clean_fundeb_2026.json",
                    mime="application/json",
                    help="Base de dados em formato JSON estruturado com dados de financiamento e condicionalidades.",
                    use_container_width=True,
                )

        st.markdown("---")

        # Assinatura e Ficha Técnica da Produção
        st.markdown(
            """
            #### ✍️ Assinatura e Ficha Técnica da Produção
            <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 16px 20px; line-height: 1.6; font-size: 0.92rem; color: #0F172A;">
                <b>Responsabilidade Técnica e Engenharia de Dados:</b> Carlos Artur Guimarães<br>
                <b>Ambiente Institucional:</b> Núcleo de Inteligência de Dados em Políticas Públicas e Financiamento Educacional<br>
                <b>Data de Homologação Técnica:</b> Outubro de 2026 &middot; Ciclo Orçamentário FUNDEB 2026<br>
                <b>Fontes Governamentais:</b> FNDE &middot; INEP &middot; Ministério da Educação &middot; NIC.br (Censo Escolar, SIMET, SIOPE, Saeb e Ideb)<br>
                <b>Licença e Acesso:</b> Dados Públicos Abertos (Lei nº 12.527/2011 - LAI) &middot; Permitida a livre reprodução para fins de gestão pública, pesquisa e controle social com citação da fonte.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

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
            value=f"{format_int(resumo.habilitados)} redes",
            subtitle=f"{format_percent(resumo.pct_habilitados)} ({format_int(resumo.habilitados)} de {format_int(resumo.total_entes)}) com as 5 condic.",
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
            subtitle=f"VAAF: {format_currency(resumo.total_vaaf_reais)} • VAAT: {format_currency(resumo.total_vaat_reais)}",
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

        map_busca_nomes = {
            ib: f"{nome} ({uf} - IBGE {ib})"
            for ib, nome, uf in zip(df_busca["ibge"], df_busca["nome"], df_busca["uf"])
        }

        ente_selecionado = st.selectbox(
            "Selecione ou digite o nome/IBGE da rede:",
            options=df_busca["ibge"].tolist(),
            format_func=lambda ib: map_busca_nomes.get(ib, str(ib)),
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
                st.markdown(f"- **IND Atendimento:** {format_decimal(row['ind_atend'], 4)}" if pd.notna(row['ind_atend']) else "- **IND Atendimento:** —")
                st.markdown(f"- **Evoluiu Atendimento:** {'Sim' if row['evoluiu_atend'] else 'Não'}")
                st.markdown(f"- **IND Aprendizagem:** {format_decimal(row['ind_aprend'], 4)}" if pd.notna(row['ind_aprend']) else "- **IND Aprendizagem:** —")
                st.markdown(f"- **Evoluiu Aprendizagem:** {'Sim' if row['evoluiu_aprend'] else 'Não'}")
                st.markdown(f"- **Total Reprovações:** {format_int(row['n_reprovacoes'])} de 5")
            with g3:
                st.markdown("**🎓 Desempenho Educacional (Inep)**")
                st.markdown(f"- **Ideb Anos Iniciais:** {format_decimal(row['ideb_ai'], 1)}" if pd.notna(row['ideb_ai']) else "- **Ideb (AI):** —")
                st.markdown(f"- **Ideb Anos Finais:** {format_decimal(row['ideb_af'], 1)}" if pd.notna(row['ideb_af']) else "- **Ideb (AF):** —")
                st.markdown(f"- **Saeb Matemática (AI):** {format_decimal(row['saeb_ai_mt'], 1)}" if pd.notna(row['saeb_ai_mt']) else "- **Saeb MT:** —")
                st.markdown(f"- **Saeb Língua Port. (AI):** {format_decimal(row['saeb_ai_lp'], 1)}" if pd.notna(row['saeb_ai_lp']) else "- **Saeb LP:** —")
                st.markdown(f"- **INSE Municipal:** {format_decimal(row['inse'], 2)}" if pd.notna(row['inse']) else "- **INSE:** —")
            with g4:
                st.markdown("**⚖️ Status das 5 Condicionalidades**")
                st.markdown(f"- **Cond. I (Diretores por Mérito):** {'✅ Aprovada' if row['c1'] else '❌ Reprovada'}")
                st.markdown(f"- **Cond. II (Saeb >= 80%):** {'✅ Aprovada' if row['c2'] else '❌ Reprovada'}")
                st.markdown(f"- **Cond. III (Red. Desigualdades):** {'✅ Aprovada' if row['c3'] else '❌ Reprovada'}")
                st.markdown(f"- **Cond. IV (ICMS Educação):** {'✅ Aprovada' if row['c4'] else '❌ Reprovada'}")
                st.markdown(f"- **Cond. V (Currículo BNCC):** {'✅ Aprovada' if row['c5'] else '❌ Reprovada'}")

    st.markdown("---")

    # ------------------------------------------------------------- EXPLICAÇÃO DOS TÓPICOS COM FRASES LONGAS E NEGRITOS
    with st.expander("📌 Tópicos e Estrutura do Painel: Guia Detalhado de Leitura", expanded=False):
        st.caption("Abaixo apresentamos a fundamentação conceitual, metodológica e institucional de cada um dos eixos estruturantes do painel:")

        col_t1, col_t2 = st.columns(2)

        with col_t1:
            with st.container(border=True):
                st.markdown(
                    """
                    #### ⚖️ 1. Condicionalidades & Ranking de Impacto
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
                    r"""
                    #### 🛡️ 6. Qualidade dos Dados, Transparência & Verificação SHA-256
                    **O compromisso primordial do painel é com a integridade absoluta dos dados: nenhuma variável é inventada, estimada aleatoriamente ou preenchida com valores artificiais.**
                    Todos os registros derivam diretamente das publicações oficiais do **FNDE (Portarias e Resoluções de rateio), INEP (Censo Escolar, Ideb, proficiências Saeb e INSE) e NIC.br/SIMET (Conectividade Escolar)**.
                    A aba de auditoria executa **testes automáticos em tempo real demonstrando que a soma das parcelas fecha perfeitamente com o total da União ($\text{VAAF} + \text{VAAT} + \text{VAAR} = \text{Total}$) em 100% dos 5.596 entes avaliados**, além de listar as **assinaturas criptográficas SHA-256** de todos os arquivos de dados para auditoria pública independente.
                    """
                )
