"""Serviço gerador do Boletim Executivo Estratégico (Relatório de 2 Páginas).

Incorpora rigorosamente os 8 Princípios Fundamentais de Stephen Few:
1. Simplifique: Redução de ruído gráfico, foco na essência da informação de decisão.
2. Comparar: Benchmarks lado a lado (Ente vs UF vs Brasil) e comparativo de cenários.
3. Atenção: Destaques pré-atentivos em gargalos críticos, semáforos e custo da inação.
4. Explorar: Seletores rápidos em O(1) e alternância imediata de perspectivas.
5. Visão Diversificada: Análise integrada jurídica, contábil, pedagógica e infraestrutural.
6. Pergunte por quê: Diagnóstico causal explícito de causas-raiz de perdas e inabilitações.
7. Seja cético: Simulação contrafactual com 6 hipóteses de sensibilidade auditadas.
8. Responder e Compartilhar: Exportação para impressão em PDF de 2 páginas (Retrato e Paisagem).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any
import pandas as pd

from fundeb.domain.legal import CONDICIONALIDADES, CONDICIONALIDADE_POR_CODIGO
from fundeb.services.simulator import SimulatorService
from fundeb.ui.components import (
    format_currency,
    format_currency_full,
    format_percent,
    format_int,
    format_decimal,
)


@dataclass(frozen=True)
class ItemAcaoEstrategica:
    eixo: str
    prazo: str
    titulo: str
    diagnostico: str
    acao_prescritiva: str
    responsaveis: str
    impacto_estimado: str
    prioridade: str  # "Alta", "Média", "Preventiva"


@dataclass(frozen=True)
class ItemBenchmark:
    metrica: str
    ente_val: float | None
    uf_val: float | None
    br_val: float | None
    unidade: str
    melhor_se: str  # "maior" ou "menor"
    status_relativo: str
    simbolo: str  # "🟢", "🟡", "🔴"


@dataclass(frozen=True)
class DiagnosticoCausal:
    pergunta: str
    resposta: str
    evidencia: str
    impacto_financeiro: str


@dataclass(frozen=True)
class AlertaPreattentive:
    tipo: str  # "perigo", "alerta", "sucesso"
    titulo: str
    descricao: str
    valor_destaque: str
    acao_imediata: str


@dataclass(frozen=True)
class DadosBoletim:
    ibge: str
    nome: str
    uf: str
    regiao: str
    esfera: str
    habilitado: bool
    beneficiario: bool
    transicao: str
    pendencia: str
    n_reprovacoes: int

    # Financiamento Oficial
    receita_contrib_rs: float
    vaaf_rs: float
    vaat_rs: float
    vaar_2025_rs: float
    vaar_2026_rs: float
    uniao_total_rs: float
    delta_vaar_historico_rs: float

    # Condicionalidades de Gestão (Status)
    condicionalidades_status: list[dict[str, Any]]

    # Benchmarks Comparativos Lado a Lado (Stephen Few: Princípio Comparar)
    benchmarks: list[ItemBenchmark]

    # Diagnóstico Causal de Causa-Raiz (Stephen Few: Princípio Pergunte Por Quê)
    diagnosticos_causais: list[DiagnosticoCausal]

    # Alerta Pré-atentivo (Stephen Few: Princípio Atenção)
    alerta_preattentive: AlertaPreattentive

    # Indicadores Pedagógicos e de Fluxo
    saeb_lp: float | None
    saeb_mt: float | None
    ideb_ai: float | None
    ideb_af: float | None
    ideb_em: float | None
    aprovacao_pct: float | None
    abandono_pct: float | None
    inse_score: float | None
    conectividade_aprendizagem_pct: float | None
    ind_atendimento: float | None
    evoluiu_atendimento: bool
    ind_aprendizagem: float | None
    evoluiu_aprendizagem: bool

    # Potencial Financeiro e Simulação
    trilha_cenarios: list[dict[str, Any]]
    custo_inacao_rs: float
    melhor_potencial_rs: float

    # Plano Propositivo de Ações
    acoes_prescritivas: list[ItemAcaoEstrategica]

    # Metadados de Autenticidade
    hash_autenticacao: str
    data_emissao: str


class BoletimService:
    def __init__(self, df: pd.DataFrame, simulator: SimulatorService) -> None:
        self._df = df
        self._simulator = simulator
        self._lookup: dict[str, dict[str, Any]] = {
            str(r["ibge"]): r for r in df.to_dict("records")
        }

    def get_ente(self, ibge: str) -> dict[str, Any] | None:
        return self._lookup.get(str(ibge))

    def gerar_dados_boletim(self, ibge: str) -> DadosBoletim | None:
        ente = self.get_ente(ibge)
        if not ente:
            return None

        esfera = "Estadual" if str(ente.get("rede", "")).lower() == "estadual" else "Municipal"
        uf = str(ente.get("uf", ""))

        # 1. Financiamento
        rec_contrib = float(ente.get("receita_contrib") or 0.0)
        vaaf = float(ente.get("vaaf") or 0.0)
        vaat = float(ente.get("vaat") or 0.0)
        vaar_25 = float(ente.get("vaar_2025") or 0.0)
        vaar_26 = float(ente.get("vaar") or 0.0)
        uniao_tot = float(ente.get("uniao_total") or 0.0)
        delta_vaar = vaar_26 - vaar_25

        # 2. Status das 5 Condicionalidades
        cond_status = []
        mapping_cond = [
            ("c1", "I", "Gestor Escolar por Mérito/Desempenho", "MEC / SEB"),
            ("c2", "II", "Participação Mínima de 80% no Saeb", "Inep / MEC"),
            ("c3", "III", "Redução de Desigualdades Educacionais", "Inep / MEC"),
            ("c4", "IV", "Regime de Colaboração / ICMS Educacional", "Secretaria de Estado / SEB"),
            ("c5", "V", "Referenciais Curriculares BNCC Homologados", "Conselho de Educação / Simec"),
        ]
        for col, inc, rotulo, orgao in mapping_cond:
            atende = bool(ente.get(col, False))
            cond_obj = CONDICIONALIDADE_POR_CODIGO[col]
            cond_status.append({
                "codigo": col,
                "inciso": inc,
                "titulo": rotulo,
                "orgao": orgao,
                "atende": atende,
                "texto_legal": cond_obj.texto_legal,
                "como_cumprir": cond_obj.como_cumprir,
            })

        # 3. Indicadores Pedagógicos do Ente
        if esfera == "Estadual":
            saeb_lp = ente.get("saeb_em_lp") or ente.get("saeb_af_lp")
            saeb_mt = ente.get("saeb_em_mt") or ente.get("saeb_af_mt")
            aprov = ente.get("aprov_med") or ente.get("aprov_fund")
            aband = ente.get("aband_med") or ente.get("aband_fund")
            ideb = ente.get("ideb_em") or ente.get("ideb_af")
        else:
            saeb_lp = ente.get("saeb_af_lp") or ente.get("saeb_ai_lp")
            saeb_mt = ente.get("saeb_af_mt") or ente.get("saeb_ai_mt")
            aprov = ente.get("aprov_fund")
            aband = ente.get("aband_fund")
            ideb = ente.get("ideb_af") or ente.get("ideb_ai")

        inse = ente.get("inse")
        net = ente.get("net_aprend_pct")

        # 4. Cálculo dos Benchmarks Lado a Lado (Princípio Stephen Few: Comparar)
        benchmarks = self._calcular_benchmarks(esfera, uf, saeb_lp, saeb_mt, aprov, aband, ideb, inse, net)

        # 5. Simulação de Cenários e Potencial (Princípio Stephen Few: Seja Cético)
        trilha = self._simulator.simular_trilha_hipoteses(ibge)
        melhor_potencial = trilha[-1]["valor_rs"] if trilha else vaar_26
        custo_inacao = max(0.0, melhor_potencial - vaar_26)

        # 6. Alerta Pré-atentivo e Diagnóstico Causal (Princípios: Atenção e Pergunte Por Quê)
        alerta, diagnosticos = self._analisar_causas_e_alerta(
            ente, esfera, cond_status, custo_inacao, aband, saeb_lp, saeb_mt
        )

        # 7. Motor Prescritivo de Ações (Como Agir)
        acoes = self._prescrever_acoes(ente, esfera, cond_status, aband, saeb_lp, saeb_mt)

        # 8. Hash de Rastreabilidade e Auditoria
        raw_hash = f"{ibge}-{ente.get('nome')}-{vaar_26}-{len(acoes)}"
        hash_cod = hashlib.sha256(raw_hash.encode("utf-8")).hexdigest()[:16].upper()

        return DadosBoletim(
            ibge=str(ibge),
            nome=str(ente.get("nome", "")),
            uf=uf,
            regiao=str(ente.get("regiao", "")),
            esfera=esfera,
            habilitado=bool(ente.get("habilitado", False)),
            beneficiario=bool(ente.get("beneficiario", False)),
            transicao=str(ente.get("transicao", "Fora")),
            pendencia=str(ente.get("pendencia", "")),
            n_reprovacoes=int(ente.get("n_reprovacoes", 0)),
            receita_contrib_rs=rec_contrib,
            vaaf_rs=vaaf,
            vaat_rs=vaat,
            vaar_2025_rs=vaar_25,
            vaar_2026_rs=vaar_26,
            uniao_total_rs=uniao_tot,
            delta_vaar_historico_rs=delta_vaar,
            condicionalidades_status=cond_status,
            benchmarks=benchmarks,
            diagnosticos_causais=diagnosticos,
            alerta_preattentive=alerta,
            saeb_lp=float(saeb_lp) if saeb_lp is not None and saeb_lp == saeb_lp else None,
            saeb_mt=float(saeb_mt) if saeb_mt is not None and saeb_mt == saeb_mt else None,
            ideb_ai=float(ente.get("ideb_ai")) if ente.get("ideb_ai") == ente.get("ideb_ai") else None,
            ideb_af=float(ente.get("ideb_af")) if ente.get("ideb_af") == ente.get("ideb_af") else None,
            ideb_em=float(ente.get("ideb_em")) if ente.get("ideb_em") == ente.get("ideb_em") else None,
            aprovacao_pct=float(aprov) if aprov is not None and aprov == aprov else None,
            abandono_pct=float(aband) if aband is not None and aband == aband else None,
            inse_score=float(inse) if inse == inse else None,
            conectividade_aprendizagem_pct=float(net) if net == net else None,
            ind_atendimento=float(ente.get("ind_atend")) if ente.get("ind_atend") == ente.get("ind_atend") else None,
            evoluiu_atendimento=bool(ente.get("evoluiu_atend", False)),
            ind_aprendizagem=float(ente.get("ind_aprend")) if ente.get("ind_aprend") == ente.get("ind_aprend") else None,
            evoluiu_aprendizagem=bool(ente.get("evoluiu_aprend", False)),
            trilha_cenarios=trilha,
            custo_inacao_rs=custo_inacao,
            melhor_potencial_rs=melhor_potencial,
            acoes_prescritivas=acoes,
            hash_autenticacao=hash_cod,
            data_emissao="Ciclo Oficial 2026",
        )

    def _calcular_benchmarks(
        self,
        esfera: str,
        uf: str,
        saeb_lp: float | None,
        saeb_mt: float | None,
        aprov: float | None,
        aband: float | None,
        ideb: float | None,
        inse: float | None,
        net: float | None,
    ) -> list[ItemBenchmark]:
        """Calcula a comparação do ente com a média estadual da UF e com a média nacional."""
        df_esf = self._df[self._df["rede"] == esfera]
        df_uf = df_esf[df_esf["uf"] == uf]
        if df_uf.empty:
            df_uf = df_esf

        # Colunas correspondentes
        col_lp = "saeb_em_lp" if esfera == "Estadual" else "saeb_af_lp"
        col_mt = "saeb_em_mt" if esfera == "Estadual" else "saeb_af_mt"
        col_ap = "aprov_med" if esfera == "Estadual" else "aprov_fund"
        col_ab = "aband_med" if esfera == "Estadual" else "aband_fund"
        col_id = "ideb_em" if esfera == "Estadual" else "ideb_af"

        itens_def = [
            ("Saeb Língua Portuguesa", saeb_lp, col_lp, "pts", "maior"),
            ("Saeb Matemática", saeb_mt, col_mt, "pts", "maior"),
            ("Taxa de Aprovação", aprov, col_ap, "%", "maior"),
            ("Taxa de Abandono", aband, col_ab, "%", "menor"),
            ("IDEB Geral", ideb, col_id, "escala", "maior"),
            ("Internet para Aprendizagem", net, "net_aprend_pct", "%", "maior"),
            ("Nível Socioeconômico (INSE)", inse, "inse", "escala", "maior"),
        ]

        benchmarks: list[ItemBenchmark] = []
        for rotulo, val_ente, col_df, un, sentido in itens_def:
            m_uf = float(df_uf[col_df].dropna().mean()) if col_df in df_uf.columns and not df_uf[col_df].dropna().empty else None
            m_br = float(df_esf[col_df].dropna().mean()) if col_df in df_esf.columns and not df_esf[col_df].dropna().empty else None

            v_e = float(val_ente) if val_ente is not None and val_ente == val_ente else None

            if v_e is None or m_uf is None or m_br is None:
                status, simb = "Disponível apenas no Ente", "ℹ️"
            elif sentido == "maior":
                if v_e >= max(m_uf, m_br):
                    status, simb = "Acima das Médias", "🟢"
                elif v_e >= min(m_uf, m_br):
                    status, simb = "Alinhado à Média", "🟡"
                else:
                    status, simb = "Abaixo das Médias", "🔴"
            else:  # menor é melhor
                if v_e <= min(m_uf, m_br):
                    status, simb = "Favorável (Menor)", "🟢"
                elif v_e <= max(m_uf, m_br):
                    status, simb = "Alinhado à Média", "🟡"
                else:
                    status, simb = "Alerta (Maior)", "🔴"

            benchmarks.append(
                ItemBenchmark(
                    metrica=rotulo,
                    ente_val=v_e,
                    uf_val=m_uf,
                    br_val=m_br,
                    unidade=un,
                    melhor_se=sentido,
                    status_relativo=status,
                    simbolo=simb,
                )
            )

        return benchmarks

    def _analisar_causas_e_alerta(
        self,
        ente: dict[str, Any],
        esfera: str,
        cond_status: list[dict[str, Any]],
        custo_inacao: float,
        aband: float | None,
        saeb_lp: float | None,
        saeb_mt: float | None,
    ) -> tuple[AlertaPreattentive, list[DiagnosticoCausal]]:
        """Gera o alerta de foco pré-atentivo e as respostas causais para 'Por que isso aconteceu?'."""
        cond_falhas = [c for c in cond_status if not c["atende"]]
        diagnosticos: list[DiagnosticoCausal] = []

        # 1. Alerta Pré-atentivo
        if cond_falhas:
            primeira_falha = cond_falhas[0]
            alerta = AlertaPreattentive(
                tipo="perigo",
                titulo="🚨 ALERTA CRÍTICO: INABILITAÇÃO LEGAL NO VAAR",
                descricao=f"A rede está inabilitada por descumprir o Inciso {primeira_falha['inciso']} ({primeira_falha['titulo']}).",
                valor_destaque=f"Perda estimada de {format_currency_full(custo_inacao)} anuais",
                acao_imediata=f"Regularizar {primeira_falha['titulo']} e homologar certidão no Simec.",
            )
        elif custo_inacao > 50000:
            alerta = AlertaPreattentive(
                tipo="alerta",
                titulo="⚠️ PONTO DE ATENÇÃO: POTENCIAL FINANCEIRO NÃO CAPTADO",
                descricao="Rede habilitada, porém retida em estratos medianos de atendimento ou aprendizagem.",
                valor_destaque=f"Oportunidade de expansão: +{format_currency_full(custo_inacao)}/ano",
                acao_imediata="Reduzir abandono escolar e focar reforço em Língua Portuguesa e Matemática.",
            )
        else:
            alerta = AlertaPreattentive(
                tipo="sucesso",
                titulo="🏆 EXCELÊNCIA: HABILITAÇÃO PLENA E ALTA CAPTAÇÃO",
                descricao="Rede cumpre integralmente os requisitos do art. 14 e opera próxima do teto de coeficientes.",
                valor_destaque="Desempenho Otimizado",
                acao_imediata="Manter monitoramento anual de certidões e assiduidade escolar no Saeb.",
            )

        # 2. Diagnóstico Causal das Raízes (Pergunte por quê)
        if cond_falhas:
            lista_falhas_str = ", ".join([f"Inciso {c['inciso']} ({c['titulo']})" for c in cond_falhas])
            diagnosticos.append(
                DiagnosticoCausal(
                    pergunta="Por que a rede não recebe recursos da Complementação VAAR?",
                    resposta=f"O ente federado foi inabilitado administrativamente pelo não cumprimento de {len(cond_falhas)} condicionalidade(s) legal(is): {lista_falhas_str}. A Lei nº 14.113/2020 estabelece que a inabilitação em qualquer condicionalidade bloqueia o repasse, independentemente do desempenho pedagógico.",
                    evidencia=f"{len(cond_falhas)} pendência(s) registrada(s) na apuração oficial FNDE/Inep.",
                    impacto_financeiro=f"Bloqueio total de até {format_currency_full(custo_inacao)} no ciclo.",
                )
            )

        if aband is not None and aband > 1.5:
            diagnosticos.append(
                DiagnosticoCausal(
                    pergunta="Por que o Indicador de Atendimento está abaixo do potencial máximo?",
                    resposta=f"A taxa de abandono escolar registrada em {aband:.1f}% reduz drasticamente o indicador I_atend, além de gerar fator redutor sobre alunos sem movimentação final no Censo Escolar (SIR).",
                    evidencia=f"Abandono escolar ({aband:.1f}%) acima do limite de conforto estatístico.",
                    impacto_financeiro="Reduz o peso financeiro de atendimento (escala de 1 a 2).",
                )
            )

        if saeb_lp is not None and saeb_lp < 240:
            diagnosticos.append(
                DiagnosticoCausal(
                    pergunta="Por que o avanço de proficiência cognitiva impacta o repasse financeiro?",
                    resposta="A cota de 50% de aprendizagem premia o avanço contínuo (peso 0,7 no IAD) e o nível absoluto (peso 0,3 no IND). Desempenhos abaixo de 240 pontos mantêm o multiplicador nos percentis inferiores da distribuição nacional.",
                    evidencia=f"Proficiência Saeb registrada em {saeb_lp:.1f} pts (Língua Portuguesa).",
                    impacto_financeiro="Restringe a participação na quota global de 50% de aprendizagem.",
                )
            )

        if not diagnosticos:
            diagnosticos.append(
                DiagnosticoCausal(
                    pergunta="Como a rede pode manter a trajetória ascendente e alcançar o teto do VAAR?",
                    resposta="Assegurando que 100% dos estudantes permaneçam na escola (abandono zero) e alcançando patamares superiores de adequação nos níveis de aprendizado do Saeb.",
                    evidencia="Conformidade em 100% dos parâmetros normativos do ciclo.",
                    impacto_financeiro="Estabilidade e manutenção do coeficiente máximo de distribuição.",
                )
            )

        return alerta, diagnosticos

    def _prescrever_acoes(
        self,
        ente: dict[str, Any],
        esfera: str,
        cond_status: list[dict[str, Any]],
        aband: float | None,
        saeb_lp: float | None,
        saeb_mt: float | None,
    ) -> list[ItemAcaoEstrategica]:
        acoes: list[ItemAcaoEstrategica] = []
        cond_map = {c["codigo"]: c["atende"] for c in cond_status}

        # Condicionalidade I (Gestão de Diretores)
        if not cond_map.get("c1", True):
            acoes.append(ItemAcaoEstrategica(
                eixo="Eixo 1 · Governança e Simec",
                prazo="Até 60 dias (Janela Simec)",
                titulo="Adequação da Lei de Gestores Escolares por Mérito",
                diagnostico="Ente reprovado no inciso I do art. 14 da Lei 14.113/2020 por ausência de critérios técnicos ou escolha com participação comunitária.",
                acao_prescritiva="Editar ou atualizar ato normativo municipal/estadual prevendo seleção prévia de gestores escolares por mérito e desempenho ou consulta à comunidade escolar. Protocolar e homologar certidão no módulo VAAR do Simec.",
                responsaveis="Gabinete do Executivo, Secretaria de Educação e Procuradoria Jurídica.",
                impacto_estimado="Desbloqueia a elegibilidade primária ao VAAR e elimina cláusula de barreira inicial.",
                prioridade="Alta",
            ))
        else:
            acoes.append(ItemAcaoEstrategica(
                eixo="Eixo 1 · Governança e Simec",
                prazo="Monitoramento Anual",
                titulo="Manutenção da Conformidade em Gestão Escolar",
                diagnostico="Condicionalidade I cumprida com sucesso.",
                acao_prescritiva="Acompanhar vigência dos mandatos de diretores e garantir que futuros provimentos continuem obedecendo ao rito técnico aprovado, inserindo relatórios anuais no Simec.",
                responsaveis="Secretaria de Educação.",
                impacto_estimado="Preserva a habilitação contínua da rede nos ciclos subsequentes.",
                prioridade="Preventiva",
            ))

        # Condicionalidade II (Participação no Saeb >= 80%)
        if not cond_map.get("c2", True):
            acoes.append(ItemAcaoEstrategica(
                eixo="Eixo 1 · Governança e Simec",
                prazo="Ciclo de Aplicação Saeb",
                titulo="Operação Presença Saeb (Cláusula de Barreira 80%)",
                diagnostico="Participação de estudantes nas turmas avaliadas pelo Inep ficou abaixo de 80%, inabilitando o ente de pleno direito.",
                acao_prescritiva="Instituir Comitê Escolar de Engajamento para o Saeb com busca ativa personalizada no dia da prova, transporte escolar garantido e conscientização de famílias para assegurar presença mínima de 85%.",
                responsaveis="Secretaria de Educação, Gestores Escolares e Conselho Tutelar.",
                impacto_estimado="Supera a barreira eliminatória do Inep, tornando a rede apta ao cômputo dos indicadores cognitivos.",
                prioridade="Alta",
            ))

        # Condicionalidade III (Redução de Desigualdades)
        if not cond_map.get("c3", True):
            acoes.append(ItemAcaoEstrategica(
                eixo="Eixo 1 · Governança e Simec",
                prazo="Contínuo no Ano Letivo",
                titulo="Programa Focado em Equidade Racial e Socioeconômica",
                diagnostico="A rede não demonstrou redução estatística das disparidades socioeconômicas e raciais na aprendizagem aferida pelo Inep.",
                acao_prescritiva="Implementar tutoria pedagógica direcionada aos estudantes de menor nível socioeconômico (NSE) e pretos, pardos e indígenas, monitorando o hiato de proficiência por meio de avaliações diagnósticas bimestrais.",
                responsaveis="Coordenação Pedagógica e Equipe de Avaliação da Rede.",
                impacto_estimado="Garante o cumprimento do inciso III e eleva o multiplicador de equidade (IndEqui).",
                prioridade="Alta",
            ))

        # Condicionalidade IV (ICMS Educação / Colaboração)
        if not cond_map.get("c4", True):
            msg_acao = (
                "Aprovar lei estadual disciplinando a partilha de no mínimo 10% da cota municipal do ICMS por critérios pedagógicos (art. 158 CF)."
                if esfera == "Estadual"
                else "Articular com a Secretaria Estadual de Educação e UNDIME para envio dos dados de desempenho e cumprimento do regime de colaboração."
            )
            acoes.append(ItemAcaoEstrategica(
                eixo="Eixo 1 · Governança e Simec",
                prazo="Imediato",
                titulo="Pactuação do Regime de Colaboração (ICMS Educacional)",
                diagnostico="Ente não validado na regra de colaboração ou regulamentação do ICMS Educacional (EC nº 108/2020).",
                acao_prescritiva=msg_acao,
                responsaveis="Secretaria de Fazenda e Secretaria de Educação.",
                impacto_estimado="Habilita a rede e fortalece a arrecadação vinculada à qualidade de ensino.",
                prioridade="Alta",
            ))

        # Condicionalidade V (Currículo BNCC Homologado)
        if not cond_map.get("c5", True):
            acoes.append(ItemAcaoEstrategica(
                eixo="Eixo 1 · Governança e Simec",
                prazo="Imediato",
                titulo="Homologação Plena dos Referenciais Curriculares BNCC",
                diagnostico="Currículo da rede com pendência de validação ou ausência dos anexos obrigatórios homologados pelo Conselho de Educação.",
                acao_prescritiva="Aprovar formalmente no Conselho de Educação (CME/CEE) o currículo alinhado à BNCC contemplando os anexos obrigatórios (Educação Especial Inclusiva, ERER Leis 10.639/11.645 e Educação Digital) e publicar ato em Diário Oficial com inserção no Simec.",
                responsaveis="Conselho de Educação e Secretaria de Educação.",
                impacto_estimado="Elimina a pendência da Condicionalidade V com impacto direto na habilitação definitiva.",
                prioridade="Alta",
            ))

        # EIXO 2: FLUXO E PERMANÊNCIA (COTA 50% ATENDIMENTO)
        if aband is not None and aband > 1.5:
            acoes.append(ItemAcaoEstrategica(
                eixo="Eixo 2 · Fluxo e Permanência",
                prazo="Bimestral",
                titulo="Combate ao Abandono Escolar e Redução de Omissões SIR",
                diagnostico=f"Taxa de abandono escolar registrada em {aband:.1f}%, gerando penalidade severa no cômputo do Indicador de Atendimento.",
                acao_prescritiva="Implantar protocolo de Alerta Precoce de Infrequência (API) integrado ao sistema de transporte e merenda, com busca ativa domiciliar antes de atingir 5 faltas consecutivas. Assegurar preenchimento de 100% dos dados de rendimento no Censo para evitar o fator redutor de 0,5x por registros sem informação (SIR).",
                responsaveis="Equipe do Censo Escolar, Diretores e Articulação Intersetorial (CRAS/Saúde).",
                impacto_estimado="Pode dobrar o peso do atendimento (peso_atend de 1,0 para até 2,0), gerando ganhos de até 100% na cota de atendimento.",
                prioridade="Média",
            ))
        else:
            acoes.append(ItemAcaoEstrategica(
                eixo="Eixo 2 · Fluxo e Permanência",
                prazo="Anual",
                titulo="Consolidação do Fluxo Escolar Regular",
                diagnostico="Taxa de abandono em patamar controlado ou dentro da margem de flutuação tolerada pelo Inep.",
                acao_prescritiva="Manter acompanhamento sistemático da transição de etapas, reduzindo reprovações acumuladas e garantindo registro rigoroso de transferências.",
                responsaveis="Supervisão Pedagógica e Secretarias Escolares.",
                impacto_estimado=r"Mantém evolução positiva contínua ($\Delta VAAR_{Atend} \ge 0$).",
                prioridade="Preventiva",
            ))

        # EIXO 3: QUALIDADE PEDAGÓGICA (COTA 50% APRENDIZAGEM)
        score_lp = saeb_lp or 0.0
        score_mt = saeb_mt or 0.0
        if score_lp < 240 or score_mt < 240:
            acoes.append(ItemAcaoEstrategica(
                eixo="Eixo 3 · Recomposição e Aprendizagem",
                prazo="Plano Semestral",
                titulo="Recomposição de Habilidades Críticas em LP e MT",
                diagnostico=f"Média Saeb na rede ({score_lp:.1f} LP / {score_mt:.1f} MT) com margem expressiva para evolução nas escalas adequadas do Inep.",
                acao_prescritiva="Formação continuada de professores com foco nas matrizes de referência do Saeb, fornecimento de material estruturado de reforço e simulados diagnósticos com feedback pedagógico item a item para as escolas.",
                responsaveis="Equipe de Formação Pedagógica e Professores.",
                impacto_estimado="Eleva o Índice de Avanço de Desempenho (IAD, peso 0,7) e maximiza a parcela de 50% de aprendizagem.",
                prioridade="Média",
            ))
        else:
            acoes.append(ItemAcaoEstrategica(
                eixo="Eixo 3 · Recomposição e Aprendizagem",
                prazo="Plano Bianual",
                titulo="Inovação Pedagógica e Conectividade para Aprendizagem",
                diagnostico="Desempenho cognitivo em patamar satisfatório em relação à média regional.",
                acao_prescritiva="Expandir conectividade de banda larga para 100% das salas de aula e integrar plataformas digitais interativas às práticas docentes, sustentando a trajetória ascendente no Saeb e IDEB.",
                responsaveis="Núcleo de Tecnologia Educacional e Secretaria de Educação.",
                impacto_estimado="Posiciona a rede nos estratos superiores de coeficiente de distribuição.",
                prioridade="Preventiva",
            ))

        return acoes

    def gerar_html_boletim(self, dados: DadosBoletim, orientacao: str = "portrait") -> str:
        """Gera documento HTML autocontido com suporte aos 8 princípios de Stephen Few e exportação A4."""
        is_landscape = orientacao.lower() == "landscape"
        page_size = "A4 landscape" if is_landscape else "A4 portrait"

        # Formatações ABNT
        rec_contrib_fmt = format_currency_full(dados.receita_contrib_rs)
        vaaf_fmt = format_currency_full(dados.vaaf_rs)
        vaat_fmt = format_currency_full(dados.vaat_rs)
        vaar_25_fmt = format_currency_full(dados.vaar_2025_rs)
        vaar_26_fmt = format_currency_full(dados.vaar_2026_rs)
        uniao_tot_fmt = format_currency_full(dados.uniao_total_rs)
        custo_inacao_fmt = format_currency_full(dados.custo_inacao_rs)
        melhor_pot_fmt = format_currency_full(dados.melhor_potencial_rs)

        # Badges
        badge_hab = (
            '<span class="badge badge-success">HABILITADO</span>'
            if dados.habilitado
            else '<span class="badge badge-danger">NÃO HABILITADO</span>'
        )
        badge_benef = (
            '<span class="badge badge-info">BENEFICIÁRIO VAAR</span>'
            if dados.beneficiario
            else '<span class="badge badge-muted">NÃO BENEFICIÁRIO</span>'
        )
        badge_trans = f'<span class="badge badge-warning">Transição: {dados.transicao.upper()}</span>'

        # Banner de Atenção Pré-atentiva (Few: Atenção)
        al = dados.alerta_preattentive
        cor_alerta_borda = {"perigo": "#dc2626", "alerta": "#d97706", "sucesso": "#16a34a"}.get(al.tipo, "#2563eb")
        cor_alerta_fundo = {"perigo": "#fef2f2", "alerta": "#fffbeb", "sucesso": "#f0fdf4"}.get(al.tipo, "#eff6ff")
        alerta_preattentive_html = f"""
        <div class="alerta-preattentive" style="background:{cor_alerta_fundo}; border-left:4px solid {cor_alerta_borda};">
            <div>
                <strong style="color:{cor_alerta_borda}; font-size:12.5px; text-transform:uppercase; letter-spacing:0.02em;">{al.titulo}</strong><br>
                <span style="font-size:11px; color:#1e293b; line-height:1.4;">{al.descricao} <em>Meta imediata: {al.acao_imediata}</em></span>
            </div>
            <div style="text-align:right; font-weight:800; font-size:14px; color:{cor_alerta_borda}; white-space:nowrap; margin-left:14px;">
                {al.valor_destaque}
            </div>
        </div>
        """

        # Linhas das Condicionalidades
        linhas_cond = ""
        for c in dados.condicionalidades_status:
            icone = '<span class="status-icon success">✓ CUMPRIDA</span>' if c["atende"] else '<span class="status-icon danger">✕ PENDENTE</span>'
            status_cls = "row-ok" if c["atende"] else "row-fail"
            linhas_cond += f"""
            <tr class="{status_cls}">
                <td style="font-weight:800; text-align:center; font-size:11px;">{c['inciso']}</td>
                <td style="font-size:10.5px;"><strong>{c['titulo']}</strong><br><span style="color:#64748b; font-size:9.5px;">Validador: {c['orgao']}</span></td>
                <td style="text-align:center; font-size:10px;">{icone}</td>
                <td style="font-size:10px; color:#334155; line-height:1.35;">{c['como_cumprir']}</td>
            </tr>
            """

        # Linhas dos Benchmarks Lado a Lado (Few: Comparar)
        linhas_bench = ""
        for b in dados.benchmarks:
            v_e = format_decimal(b.ente_val, 1) if b.ente_val is not None else "—"
            v_u = format_decimal(b.uf_val, 1) if b.uf_val is not None else "—"
            v_b = format_decimal(b.br_val, 1) if b.br_val is not None else "—"
            un_suf = f" {b.unidade}" if b.unidade in ("%", "pts") else ""
            linhas_bench += f"""
            <tr>
                <td style="font-size:10.5px;"><strong>{b.metrica}</strong></td>
                <td style="text-align:right; font-weight:700; font-size:11px;">{v_e}{un_suf}</td>
                <td style="text-align:right; color:#475569; font-size:11px;">{v_u}{un_suf}</td>
                <td style="text-align:right; color:#475569; font-size:11px;">{v_b}{un_suf}</td>
                <td style="text-align:center; font-size:10px; font-weight:600;">{b.simbolo} {b.status_relativo}</td>
            </tr>
            """

        # Linhas dos Cenários Contrafactuais (Few: Seja Cético)
        linhas_cenarios = ""
        for i, c in enumerate(dados.trilha_cenarios):
            v_fmt = format_currency_full(c["valor_rs"])
            d_fmt = format_currency_full(c["delta_rs"])
            sinal = "+" if c["delta_rs"] > 0 else ""
            delta_str = f"{sinal}{d_fmt}" if i > 0 else "Baseline"
            destaque_cls = "row-destaque" if c.get("destaque") else ""
            linhas_cenarios += f"""
            <tr class="{destaque_cls}">
                <td style="font-size:10.5px;"><strong>{c['cenario']}</strong></td>
                <td style="text-align:right; font-weight:700; font-size:11px;">{v_fmt}</td>
                <td style="text-align:right; color:{'#16a34a' if c['delta_rs'] > 0 else '#64748b'}; font-weight:700; font-size:10.5px;">{delta_str}</td>
            </tr>
            """

        # Linhas de Diagnóstico Causal (Few: Pergunte Por Quê)
        blocos_causais = ""
        for d in dados.diagnosticos_causais:
            blocos_causais += f"""
            <div style="background:#f8fafc; border:1px solid #cbd5e1; border-left:3.5px solid #2563eb; border-radius:6px; padding:7px 11px; margin-bottom:7px;">
                <div style="font-weight:700; color:#1e3a8a; font-size:11px;">❓ {d.pergunta}</div>
                <div style="font-size:10px; color:#1e293b; margin:3px 0; line-height:1.35;">{d.resposta}</div>
                <div style="font-size:9.5px; color:#475569; border-top:1px dashed #cbd5e1; padding-top:3px; margin-top:3px;">
                    <strong>Evidência:</strong> {d.evidencia} &bull; <span style="color:#b91c1c;"><strong>Impacto:</strong> {d.impacto_financeiro}</span>
                </div>
            </div>
            """

        # Linhas das Ações Propositivas
        blocos_acoes = ""
        for item in dados.acoes_prescritivas:
            cor_prioridade = {"Alta": "#dc2626", "Média": "#d97706", "Preventiva": "#2563eb"}.get(item.prioridade, "#64748b")
            blocos_acoes += f"""
            <div class="acao-card">
                <div class="acao-header">
                    <div>
                        <span class="acao-tag" style="background-color:{cor_prioridade}20; color:{cor_prioridade}; border:1px solid {cor_prioridade}50;">
                            {item.prioridade.upper()}
                        </span>
                        <span class="acao-eixo">{item.eixo} &bull; Prazo: <strong>{item.prazo}</strong></span>
                    </div>
                </div>
                <div class="acao-titulo">{item.titulo}</div>
                <div class="acao-diagnostico"><strong>Diagnóstico:</strong> {item.diagnostico}</div>
                <div class="acao-corpo"><strong>Ação Prescritiva:</strong> {item.acao_prescritiva}</div>
                <div class="acao-footer">
                    <span><strong>Responsáveis:</strong> {item.responsaveis}</span>
                    <span style="float:right; color:#166534; font-weight:600;"><strong>Impacto:</strong> {item.impacto_estimado}</span>
                </div>
            </div>
            """

        # Seleção de Template: Vertical (Portrait) vs Horizontal (Landscape)
        if not is_landscape:
            # -------------------------------------------------------------
            # TEMPLATE VERTICAL (RETRATO A4 - 210mm x 297mm)
            # -------------------------------------------------------------
            corpo_html = f"""
            <!-- PÁGINA 1 VERTICAL -->
            <div class="boletim-page">
                <div class="page-content">
                    <div class="header-bar">
                        <div class="header-title">
                            <h1>Boletim Executivo &bull; FUNDEB & VAAR</h1>
                            <p>Síntese Estratégica, Benchmarks e Auditoria Legal &bull; Princípios de Stephen Few</p>
                        </div>
                        <div class="header-badges">{badge_hab} {badge_benef} {badge_trans}</div>
                    </div>

                    {alerta_preattentive_html}

                    <div class="ente-banner">
                        <div class="ente-field"><div class="label">Ente Federado</div><div class="val">{dados.nome}</div></div>
                        <div class="ente-field"><div class="label">Esfera / UF / Região</div><div class="val">{dados.esfera} &bull; {dados.uf} ({dados.regiao})</div></div>
                        <div class="ente-field"><div class="label">Código IBGE</div><div class="val">{dados.ibge}</div></div>
                        <div class="ente-field"><div class="label">Situação Legal</div><div class="val" style="color:{'#16a34a' if dados.habilitado else '#dc2626'};">{'Habilitado' if dados.habilitado else f'{dados.n_reprovacoes} Cond. Reprovadas'}</div></div>
                    </div>

                    <div class="section-title">1. Financiamento Oficial da Rede (FNDE)</div>
                    <div class="grid-fin">
                        <div class="card-fin"><div class="tit">Receita Contribuição</div><div class="num">{rec_contrib_fmt}</div></div>
                        <div class="card-fin"><div class="tit">Compl. VAAF</div><div class="num">{vaaf_fmt}</div></div>
                        <div class="card-fin"><div class="tit">Compl. VAAT</div><div class="num">{vaat_fmt}</div></div>
                        <div class="card-fin destaque"><div class="tit">Compl. VAAR (2026)</div><div class="num">{vaar_26_fmt}</div><small style="font-size:8.5px; color:#1e40af; display:block; margin-top:2px;">2025: {vaar_25_fmt}</small></div>
                        <div class="card-fin"><div class="tit">Total União</div><div class="num">{uniao_tot_fmt}</div></div>
                    </div>

                    <div class="section-title">2. Auditoria das 5 Condicionalidades de Gestão (Art. 14 da Lei 14.113/2020)</div>
                    <table>
                        <thead>
                            <tr><th style="width:6%; text-align:center;">Inc.</th><th style="width:32%;">Condicionalidade</th><th style="width:16%; text-align:center;">Status</th><th style="width:46%;">Requisito Legal e Como Cumprir</th></tr>
                        </thead>
                        <tbody>{linhas_cond}</tbody>
                    </table>

                    <div class="section-title">3. Comparativo Lado a Lado de Indicadores (Ente vs UF vs Brasil)</div>
                    <table>
                        <thead>
                            <tr><th style="width:35%;">Indicador Pedagógico / Fluxo</th><th style="width:15%; text-align:right;">{dados.nome}</th><th style="width:15%; text-align:right;">Média {dados.uf}</th><th style="width:15%; text-align:right;">Média Brasil</th><th style="width:20%; text-align:center;">Posição Relativa</th></tr>
                        </thead>
                        <tbody>{linhas_bench}</tbody>
                    </table>
                </div>

                <div class="page-footer">
                    <span>Boletim Oficial de Auditoria FUNDEB/VAAR &bull; Página 1 de 2</span>
                    <span>Autenticação: <strong>{dados.hash_autenticacao}</strong> &bull; Emitido: {dados.data_emissao}</span>
                </div>
            </div>

            <!-- PÁGINA 2 VERTICAL -->
            <div class="boletim-page">
                <div class="page-content">
                    <div class="header-bar">
                        <div class="header-title">
                            <h1>Plano Propositivo de Ação &bull; Simulação VAAR</h1>
                            <p>Simulação Contrafactual e Diagnóstico Causal de Causa-Raiz &bull; {dados.nome} ({dados.uf})</p>
                        </div>
                        <div class="header-badges"><span class="badge badge-info">PÁGINA 2 DE 2</span></div>
                    </div>

                    <div class="section-title">1. Simulação Contrafactual de Potencial & Custo da Inação</div>
                    <div class="alerta-inacao">
                        <div class="txt"><strong>CUSTO ANUAL DA INAÇÃO / POTENCIAL NÃO CAPTADO:</strong><br>Recursos anuais adicionais que a rede deixa de captar em caso de inabilitação ou não avanço das metas.</div>
                        <div class="val">{custo_inacao_fmt}</div>
                    </div>

                    <table>
                        <thead>
                            <tr><th style="width:50%;">Cenário Contrafactual de Simulação</th><th style="width:25%; text-align:right;">Repasse Estimado (R$)</th><th style="width:25%; text-align:right;">Variação Líquida (Δ)</th></tr>
                        </thead>
                        <tbody>{linhas_cenarios}</tbody>
                    </table>

                    <div class="section-title">2. Diagnóstico Causal de Causa-Raiz (Pergunte "Por Quê?")</div>
                    {blocos_causais}

                    <div class="section-title">3. Matriz Propositiva de Ações Estratégicas (Como Agir)</div>
                    <div class="blocos-acoes-container">{blocos_acoes}</div>

                    <div class="section-title">4. Compromisso de Gestão & Retorno Educacional</div>
                    <div style="background:#f8fafc; border:1px solid #cbd5e1; border-left:3.5px solid #16a34a; border-radius:6px; padding:7px 11px; font-size:10px; color:#334155; line-height:1.4;">
                        <strong>Metas Prioritárias do Ciclo:</strong> Regularizar certidões pendentes no Simec, garantir presença &ge; 85% no Saeb e combater o abandono escolar. O atingimento destas metas projeta elevar a captação anual para até <strong style="color:#166534;">{melhor_pot_fmt}</strong>.
                    </div>
                </div>

                <div class="page-footer">
                    <span>Fontes: FNDE, Inep, Censo Escolar, Simec &bull; Art. 14 da Lei nº 14.113/2020 &bull; Página 2 de 2</span>
                    <span>Chave de Verificação: <strong>{dados.hash_autenticacao}</strong> &bull; Válido para o Ciclo 2026</span>
                </div>
            </div>
            """
        else:
            # -------------------------------------------------------------
            # TEMPLATE HORIZONTAL (PAISAGEM A4 / SLIDES - 297mm x 210mm)
            # Layout em duas colunas amplas (Side-by-side comparison)
            # -------------------------------------------------------------
            corpo_html = f"""
            <!-- SLIDE 1 PAISAGEM (PÁGINA 1) -->
            <div class="boletim-page">
                <div class="page-content">
                    <div class="header-bar">
                        <div class="header-title">
                            <h1>Boletim Executivo &bull; FUNDEB & VAAR &bull; Slide 1: Diagnóstico e Benchmarks</h1>
                            <p>{dados.nome} &bull; {dados.uf} ({dados.esfera}) &bull; IBGE: {dados.ibge} &bull; Princípios de Stephen Few</p>
                        </div>
                        <div class="header-badges">{badge_hab} {badge_benef} {badge_trans}</div>
                    </div>

                    <div class="grid-two-col">
                        <!-- Coluna Esquerda: Financiamento + Condicionalidades -->
                        <div class="col-side">
                            <div class="section-title">1. Financiamento Oficial da Rede (FNDE)</div>
                            <div class="grid-fin">
                                <div class="card-fin"><div class="tit">Receita Contribuição</div><div class="num">{rec_contrib_fmt}</div></div>
                                <div class="card-fin"><div class="tit">VAAF</div><div class="num">{vaaf_fmt}</div></div>
                                <div class="card-fin"><div class="tit">VAAT</div><div class="num">{vaat_fmt}</div></div>
                                <div class="card-fin destaque"><div class="tit">VAAR 2026</div><div class="num">{vaar_26_fmt}</div></div>
                                <div class="card-fin"><div class="tit">Total União</div><div class="num">{uniao_tot_fmt}</div></div>
                            </div>

                            <div class="section-title">2. Auditoria das 5 Condicionalidades (Lei 14.113/2020)</div>
                            <table>
                                <thead>
                                    <tr><th style="width:8%; text-align:center;">Inc.</th><th style="width:42%;">Condicionalidade</th><th style="width:20%; text-align:center;">Status</th><th style="width:30%;">Órgão Validador</th></tr>
                                </thead>
                                <tbody>{linhas_cond}</tbody>
                            </table>
                        </div>

                        <!-- Coluna Direita: Alerta + Benchmarks Lado a Lado + Diagnóstico Causal -->
                        <div class="col-side">
                            {alerta_preattentive_html}

                            <div class="section-title">3. Comparativo Lado a Lado (Ente vs UF vs Brasil)</div>
                            <table>
                                <thead>
                                    <tr><th>Indicador</th><th style="text-align:right;">{dados.nome}</th><th style="text-align:right;">Média {dados.uf}</th><th style="text-align:right;">Média BR</th><th style="text-align:center;">Posição</th></tr>
                                </thead>
                                <tbody>{linhas_bench}</tbody>
                            </table>

                            <div class="section-title">4. Diagnóstico de Causa-Raiz (Por Que Aconteceu?)</div>
                            {blocos_causais}
                        </div>
                    </div>
                </div>

                <div class="page-footer">
                    <span>Boletim Oficial de Auditoria FUNDEB/VAAR &bull; Slide Executivo 1 de 2</span>
                    <span>Autenticação: <strong>{dados.hash_autenticacao}</strong> &bull; Emitido: {dados.data_emissao}</span>
                </div>
            </div>

            <!-- SLIDE 2 PAISAGEM (PÁGINA 2) -->
            <div class="boletim-page">
                <div class="page-content">
                    <div class="header-bar">
                        <div class="header-title">
                            <h1>Plano Propositivo de Ação &bull; Slide 2: Simulação e Prescrições</h1>
                            <p>{dados.nome} &bull; {dados.uf} &bull; Simulação Contrafactual de Cenários e Roteiro de Políticas Públicas</p>
                        </div>
                        <div class="header-badges"><span class="badge badge-info">SLIDE 2 DE 2</span></div>
                    </div>

                    <div class="grid-two-col">
                        <!-- Coluna Esquerda: Cenários de Potencial + Custo da Inação -->
                        <div class="col-side">
                            <div class="section-title">1. Simulação Contrafactual de Potencial</div>
                            <div class="alerta-inacao">
                                <div class="txt"><strong>CUSTO ANUAL DA INAÇÃO:</strong><br>Perda anual estimada por inabilitação ou não cumprimento de metas.</div>
                                <div class="val">{custo_inacao_fmt}</div>
                            </div>

                            <table>
                                <thead>
                                    <tr><th>Cenário Contrafactual</th><th style="text-align:right;">Repasse (R$)</th><th style="text-align:right;">Ganho Líquido (Δ)</th></tr>
                                </thead>
                                <tbody>{linhas_cenarios}</tbody>
                            </table>

                            <div class="section-title">2. Compromisso e Metas de Retorno Educacional</div>
                            <div style="background:#f8fafc; border:1px solid #cbd5e1; border-left:3.5px solid #16a34a; border-radius:6px; padding:8px 12px; font-size:10px; color:#334155; line-height:1.4;">
                                <strong>Metas Chave:</strong> (1) Regularizar certidões no Simec; (2) Presença &ge; 85% no Saeb; (3) Reduzir abandono escolar abaixo de 1%.<br>
                                A concretização destas metas eleva a captação anual para até <strong style="color:#166534;">{melhor_pot_fmt}</strong>.
                            </div>
                        </div>

                        <!-- Coluna Direita: Ações Prescritivas Estratégicas -->
                        <div class="col-side">
                            <div class="section-title">3. Matriz Prescritiva de Ações Estratégicas (Como Agir)</div>
                            <div class="blocos-acoes-container">{blocos_acoes}</div>
                        </div>
                    </div>
                </div>

                <div class="page-footer">
                    <span>Fontes: FNDE, Inep, Censo Escolar, Simec &bull; Art. 14 da Lei nº 14.113/2020 &bull; Slide 2 de 2</span>
                    <span>Chave de Verificação: <strong>{dados.hash_autenticacao}</strong> &bull; Válido para o Ciclo 2026</span>
                </div>
            </div>
            """

        # Documento HTML Completo
        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Boletim Executivo VAAR - {dados.nome} ({dados.uf})</title>
<style>
    @page {{
        size: {page_size};
        margin: 8mm 10mm;
    }}
    * {{
        box-sizing: border-box;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
    }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #0f172a;
        background-color: #f1f5f9;
        margin: 0;
        padding: 0;
        font-size: 11px;
        line-height: 1.35;
    }}
    .boletim-container {{
        width: 100%;
        max-width: {'1160px' if is_landscape else '840px'};
        margin: 0 auto;
        padding: 12px;
    }}
    .boletim-page {{
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 18px 22px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px -2px rgba(0,0,0,0.07);
        page-break-after: always;
        break-after: page;
        min-height: {'740px' if is_landscape else '1080px'};
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: relative;
    }}
    .page-content {{
        flex: 1 1 auto;
    }}
    .grid-two-col {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px;
    }}
    .col-side {{
        width: 100%;
    }}
    @media print {{
        body {{
            background: #ffffff !important;
            font-size: 10.5px !important;
        }}
        .boletim-container {{
            max-width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
        }}
        .boletim-page {{
            border: none !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
            page-break-after: always !important;
            break-after: page !important;
            min-height: 98vh !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
            overflow: hidden !important;
        }}
        .boletim-page:last-child {{
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}
        .no-print {{
            display: none !important;
        }}
    }}
    /* Top Bar */
    .header-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2.5px solid #1e3a8a;
        padding-bottom: 8px;
        margin-bottom: 10px;
    }}
    .header-title h1 {{
        margin: 0;
        font-size: 16.5px;
        font-weight: 800;
        color: #1e3a8a;
        letter-spacing: -0.02em;
        text-transform: uppercase;
    }}
    .header-title p {{
        margin: 2px 0 0 0;
        font-size: 10px;
        color: #475569;
        font-weight: 500;
    }}
    .header-badges {{
        display: flex;
        gap: 5px;
        align-items: center;
        flex-wrap: wrap;
    }}
    .badge {{
        display: inline-block;
        padding: 3px 8px;
        font-size: 9.5px;
        font-weight: 700;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }}
    .badge-success {{ background: #dcfce7; color: #166534; border: 1px solid #86efac; }}
    .badge-danger  {{ background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }}
    .badge-info    {{ background: #dbeafe; color: #1e40af; border: 1px solid #93c5fd; }}
    .badge-warning {{ background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }}
    .badge-muted   {{ background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }}

    /* Ente Banner */
    .ente-banner {{
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 8px 12px;
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        margin-bottom: 10px;
    }}
    .ente-field .label {{
        font-size: 9px;
        color: #64748b;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.03em;
        margin-bottom: 2px;
    }}
    .ente-field .val {{
        font-size: 12.5px;
        color: #0f172a;
        font-weight: 700;
    }}

    /* Seções */
    .section-title {{
        font-size: 12px;
        font-weight: 700;
        color: #1e3a8a;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        border-left: 3.5px solid #2563eb;
        padding-left: 6px;
        margin: 10px 0 5px 0;
    }}

    /* Grids Financeiros */
    .grid-fin {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 6px;
        margin-bottom: 10px;
    }}
    .card-fin {{
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 6px 8px;
        text-align: center;
    }}
    .card-fin.destaque {{
        background: #eff6ff;
        border-color: #60a5fa;
        border-width: 1.5px;
    }}
    .card-fin .tit {{
        font-size: 9px;
        font-weight: 600;
        color: #475569;
        text-transform: uppercase;
        margin-bottom: 2px;
        letter-spacing: 0.01em;
    }}
    .card-fin .num {{
        font-size: 13px;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.01em;
    }}
    .card-fin.destaque .num {{
        color: #1e40af;
    }}

    /* Tabelas */
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 10px;
        font-size: 10.5px;
    }}
    th {{
        background: #f1f5f9;
        color: #1e293b;
        font-weight: 700;
        text-align: left;
        padding: 5px 7px;
        border-bottom: 1.5px solid #cbd5e1;
        font-size: 9.5px;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }}
    td {{
        padding: 4.5px 7px;
        border-bottom: 1px solid #f1f5f9;
        vertical-align: middle;
    }}
    tr.row-fail td {{ background: #fff5f5; }}
    tr.row-destaque td {{ background: #f0fdf4; color: #166534; font-weight: 700; }}
    .status-icon.success {{ color: #16a34a; font-weight: 800; }}
    .status-icon.danger  {{ color: #dc2626; font-weight: 800; }}

    /* Alerta Inação */
    .alerta-inacao {{
        background: #fef2f2;
        border-left: 4px solid #ef4444;
        border-radius: 6px;
        padding: 9px 12px;
        margin: 5px 0 10px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .alerta-inacao .txt {{
        font-size: 10px;
        color: #7f1d1d;
        line-height: 1.35;
    }}
    .alerta-inacao .val {{
        font-size: 15px;
        font-weight: 800;
        color: #b91c1c;
        white-space: nowrap;
        margin-left: 12px;
    }}

    /* Alerta Pré-atentivo */
    .alerta-preattentive {{
        border-radius: 6px;
        padding: 9px 12px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    /* Ações Cards */
    .acao-card {{
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-left: 3.5px solid #2563eb;
        border-radius: 5px;
        padding: 6px 9px;
        margin-bottom: 6px;
        font-size: 10px;
    }}
    .acao-header {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 2px;
    }}
    .acao-tag {{
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 8.5px;
        font-weight: 700;
        letter-spacing: 0.02em;
    }}
    .acao-eixo {{
        font-size: 9px;
        color: #64748b;
        margin-left: 5px;
    }}
    .acao-titulo {{
        font-size: 11px;
        font-weight: 700;
        color: #0f172a;
        margin: 2px 0;
    }}
    .acao-diagnostico {{ color: #64748b; font-size: 9.5px; margin-bottom: 2px; line-height: 1.35; }}
    .acao-corpo {{ color: #1e293b; font-size: 10px; margin-bottom: 3px; line-height: 1.35; }}
    .acao-footer {{
        border-top: 1px dashed #e2e8f0;
        padding-top: 3px;
        font-size: 8.5px;
        color: #475569;
    }}

    /* Rodapé da Página */
    .page-footer {{
        border-top: 1px solid #cbd5e1;
        padding-top: 6px;
        margin-top: auto;
        display: flex;
        justify-content: space-between;
        font-size: 8.5px;
        color: #64748b;
    }}
</style>
</head>
<body>
<div class="boletim-toolbar no-print" style="position:sticky;top:0;z-index:999;display:flex;justify-content:flex-end;gap:8px;padding:8px 10px;background:rgba(248,250,252,0.96);border-bottom:1px solid #e2e8f0;">
    <button onclick="window.print()" style="cursor:pointer;background:#2563EB;color:#fff;border:none;border-radius:8px;padding:8px 16px;font-weight:600;font-size:13px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;">🖨️ Imprimir / Salvar em PDF</button>
</div>
<div class="boletim-container">
    {corpo_html}
</div>
<style>@media print {{ .no-print {{ display:none !important; }} }}</style>
</body>
</html>
"""
