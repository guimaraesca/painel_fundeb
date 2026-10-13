"""Serviço gerador do Boletim Executivo Estratégico (Relatório de 2 Páginas).

Produz uma síntese executiva diagnóstica e propositiva para qualquer ente federado
(Estado ou Município), contendo:
- Página 1: Radiografia Oficial, Status Legal das 5 Condicionalidades e Indicadores Pedagógicos.
- Página 2: Simulação de Potencial Financeiro, Custo da Inação e Plano de Ação Automatizado.
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

        # 3. Indicadores Pedagógicos (priorizando etapa correspondente à esfera)
        if esfera == "Estadual":
            saeb_lp = ente.get("saeb_em_lp") or ente.get("saeb_af_lp")
            saeb_mt = ente.get("saeb_em_mt") or ente.get("saeb_af_mt")
            aprov = ente.get("aprov_med") or ente.get("aprov_fund")
            aband = ente.get("aband_med") or ente.get("aband_fund")
        else:
            saeb_lp = ente.get("saeb_af_lp") or ente.get("saeb_ai_lp")
            saeb_mt = ente.get("saeb_af_mt") or ente.get("saeb_ai_mt")
            aprov = ente.get("aprov_fund")
            aband = ente.get("aband_fund")

        # 4. Simulação de Cenários e Potencial
        trilha = self._simulator.simular_trilha_hipoteses(ibge)
        melhor_potencial = trilha[-1]["valor_rs"] if trilha else vaar_26
        custo_inacao = max(0.0, melhor_potencial - vaar_26)

        # 5. Motor Prescritivo de Ações (Algoritmo de Inteligência de Políticas Públicas)
        acoes = self._prescrever_acoes(ente, esfera, cond_status, aband, saeb_lp, saeb_mt)

        # 6. Autenticação e Hash de Rastreabilidade
        raw_hash = f"{ibge}-{ente.get('nome')}-{vaar_26}-{len(acoes)}"
        hash_cod = hashlib.sha256(raw_hash.encode("utf-8")).hexdigest()[:16].upper()

        return DadosBoletim(
            ibge=str(ibge),
            nome=str(ente.get("nome", "")),
            uf=str(ente.get("uf", "")),
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
            saeb_lp=float(saeb_lp) if saeb_lp is not None and saeb_lp == saeb_lp else None,
            saeb_mt=float(saeb_mt) if saeb_mt is not None and saeb_mt == saeb_mt else None,
            ideb_ai=float(ente.get("ideb_ai")) if ente.get("ideb_ai") == ente.get("ideb_ai") else None,
            ideb_af=float(ente.get("ideb_af")) if ente.get("ideb_af") == ente.get("ideb_af") else None,
            ideb_em=float(ente.get("ideb_em")) if ente.get("ideb_em") == ente.get("ideb_em") else None,
            aprovacao_pct=float(aprov) if aprov is not None and aprov == aprov else None,
            abandono_pct=float(aband) if aband is not None and aband == aband else None,
            inse_score=float(ente.get("inse")) if ente.get("inse") == ente.get("inse") else None,
            conectividade_aprendizagem_pct=float(ente.get("net_aprend_pct")) if ente.get("net_aprend_pct") == ente.get("net_aprend_pct") else None,
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

        # ------------------------------------------------------------------
        # EIXO 1: CONFORMIDADE LEGAL E HABILITAÇÃO SIMEC (CURTO PRAZO)
        # ------------------------------------------------------------------
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

        # ------------------------------------------------------------------
        # EIXO 2: FLUXO ESCOLAR & PERMANÊNCIA (MÉDIO PRAZO - COTA 50% ATENDIMENTO)
        # ------------------------------------------------------------------
        if aband is not None and aband > 1.5:
            acoes.append(ItemAcaoEstrategica(
                eixo="Eixo 2 · Fluxo e Permanência",
                prazo="Bimestral",
                titulo="Combate ao Abandono Escolar e Redução de Omissões SIR",
                diagnostico=f"Taxa de abandono escolar registrada em {aband:.1f}%, gerando penalidade severa no cômputo do Indicador de Atendimento.",
                acao_prescritiva="Implantar protocolo de Alerta Precoce de Infrequência (API) integrado ao sistema de transporte e merenda, com busca ativa domiciliar antes de atingir 5 faltas consecutivas. Assegurar preenchimento de 100% dos dados de rendimento no Censo para evitar o fator redutor de 0,5x por registros sem informação (SIR).",
                responsaveis="Equipe do Censo Escolar, Diretores e Articulação Intersetorial (CRAS/Saúde).",
                impacto_estimado="Pode dobrar o peso do atendimento ($peso_{atend}$ de 1,0 para até 2,0), gerando ganhos de até 100% na cota de atendimento.",
                prioridade="Média",
            ))
        else:
            acoes.append(ItemAcaoEstrategica(
                eixo="Eixo 2 · Fluxo e Permanência",
                prazo="Anual",
                titulo="Consolidação do Fluxo Escolar Regular",
                diagnostico="Taxa de abandono em patamar controlado ou dentro da margem de flutuação tolerada pelo Inep.",
                acao_prescritiva="Manter acompanhamento sistemático da transição de etapas (ex.: 5º para 6º ano e 9º para 1ª série EM), reduzindo reprovações acumuladas e garantindo registro rigoroso de transferências.",
                responsaveis="Supervisão Pedagógica e Secretarias Escolares.",
                impacto_estimado=r"Mantém evolução positiva contínua ($\Delta VAAR_{Atend} \ge 0$).",
                prioridade="Preventiva",
            ))

        # ------------------------------------------------------------------
        # EIXO 3: QUALIDADE PEDAGÓGICA & INFRAESTRUTURA (COTA 50% APRENDIZAGEM)
        # ------------------------------------------------------------------
        score_lp = saeb_lp or 0.0
        score_mt = saeb_mt or 0.0
        if score_lp < 240 or score_mt < 240:
            acoes.append(ItemAcaoEstrategica(
                eixo="Eixo 3 · Recomposição e Aprendizagem",
                prazo="Plano Semestral",
                titulo="Recomposição de Habilidades Críticas em Língua Portuguesa e Matemática",
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
                impacto_estimado="Posiciona a rede nos estratos superiores de coeficiente de distribuição ($C_{aprend}$).",
                prioridade="Preventiva",
            ))

        return acoes

    def gerar_html_boletim(self, dados: DadosBoletim, orientacao: str = "portrait") -> str:
        """Gera documento HTML autocontido com CSS responsivo e regras @media print para 2 páginas A4."""
        is_landscape = orientacao.lower() == "landscape"
        page_size = "A4 landscape" if is_landscape else "A4 portrait"
        aspect_ratio = "297mm / 210mm" if is_landscape else "210mm / 297mm"

        # Formatações ABNT
        rec_contrib_fmt = format_currency_full(dados.receita_contrib_rs)
        vaaf_fmt = format_currency_full(dados.vaaf_rs)
        vaat_fmt = format_currency_full(dados.vaat_rs)
        vaar_25_fmt = format_currency_full(dados.vaar_2025_rs)
        vaar_26_fmt = format_currency_full(dados.vaar_2026_rs)
        uniao_tot_fmt = format_currency_full(dados.uniao_total_rs)
        custo_inacao_fmt = format_currency_full(dados.custo_inacao_rs)
        melhor_pot_fmt = format_currency_full(dados.melhor_potencial_rs)

        # Status Badges
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

        # Linhas das Condicionalidades
        linhas_cond = ""
        for c in dados.condicionalidades_status:
            icone = '<span class="status-icon success">✓ ATENDE</span>' if c["atende"] else '<span class="status-icon danger">✕ PENDENTE</span>'
            status_cls = "row-ok" if c["atende"] else "row-fail"
            linhas_cond += f"""
            <tr class="{status_cls}">
                <td style="font-weight:700; text-align:center;">{c['inciso']}</td>
                <td><strong>{c['titulo']}</strong><br><small style="color:#64748b;">{c['orgao']}</small></td>
                <td style="text-align:center;">{icone}</td>
                <td style="font-size:0.82rem; color:#334155;">{c['como_cumprir']}</td>
            </tr>
            """

        # Linhas dos Cenários
        linhas_cenarios = ""
        for i, c in enumerate(dados.trilha_cenarios):
            v_fmt = format_currency_full(c["valor_rs"])
            d_fmt = format_currency_full(c["delta_rs"])
            sinal = "+" if c["delta_rs"] > 0 else ""
            delta_str = f"{sinal}{d_fmt}" if i > 0 else "Baseline"
            destaque_cls = "row-destaque" if c.get("destaque") else ""
            linhas_cenarios += f"""
            <tr class="{destaque_cls}">
                <td><strong>{c['cenario']}</strong></td>
                <td style="text-align:right; font-weight:700;">{v_fmt}</td>
                <td style="text-align:right; color:{'#16a34a' if c['delta_rs'] > 0 else '#64748b'}; font-weight:600;">{delta_str}</td>
            </tr>
            """

        # Linhas das Ações Propositivas
        blocos_acoes = ""
        for item in dados.acoes_prescritivas:
            cor_prioridade = {
                "Alta": "#dc2626",
                "Média": "#d97706",
                "Preventiva": "#2563eb",
            }.get(item.prioridade, "#64748b")

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

        # Renderização do Documento HTML
        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Boletim Executivo VAAR - {dados.nome} ({dados.uf})</title>
<style>
    @page {{
        size: {page_size};
        margin: 8mm;
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
        max-width: {'1120px' if is_landscape else '820px'};
        margin: 0 auto;
        padding: 10px;
    }}
    .boletim-page {{
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 16px 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        page-break-after: always;
        break-after: page;
        min-height: {'740px' if is_landscape else '1060px'};
        position: relative;
    }}
    @media print {{
        body {{
            background: #ffffff !important;
        }}
        .boletim-container {{
            max-width: 100% !important;
            padding: 0 !important;
        }}
        .boletim-page {{
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 0 20px 0 !important;
            page-break-after: always !important;
            break-after: page !important;
            min-height: auto !important;
        }}
        .no-print {{
            display: none !important;
        }}
    }}
    /* Top Bar Institucional */
    .header-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid #1e3a8a;
        padding-bottom: 10px;
        margin-bottom: 12px;
    }}
    .header-title h1 {{
        margin: 0;
        font-size: 18px;
        font-weight: 800;
        color: #1e3a8a;
        letter-spacing: -0.02em;
        text-transform: uppercase;
    }}
    .header-title p {{
        margin: 2px 0 0 0;
        font-size: 10px;
        color: #64748b;
        font-weight: 500;
    }}
    .header-badges {{
        display: flex;
        gap: 6px;
        align-items: center;
    }}
    .badge {{
        display: inline-block;
        padding: 3px 8px;
        font-size: 9px;
        font-weight: 700;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}
    .badge-success {{ background: #dcfce7; color: #166534; border: 1px solid #86efac; }}
    .badge-danger  {{ background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }}
    .badge-info    {{ background: #dbeafe; color: #1e40af; border: 1px solid #93c5fd; }}
    .badge-warning {{ background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }}
    .badge-muted   {{ background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }}
    
    /* Bloco Ente */
    .ente-banner {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px 12px;
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        margin-bottom: 12px;
    }}
    .ente-field .label {{
        font-size: 9px;
        color: #64748b;
        text-transform: uppercase;
        font-weight: 600;
    }}
    .ente-field .val {{
        font-size: 12px;
        color: #0f172a;
        font-weight: 700;
    }}
    
    /* Seções */
    .section-title {{
        font-size: 12px;
        font-weight: 700;
        color: #1e3a8a;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        border-left: 3px solid #2563eb;
        padding-left: 6px;
        margin: 10px 0 6px 0;
    }}
    
    /* Grid Financeiro */
    .grid-fin {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 6px;
        margin-bottom: 10px;
    }}
    .card-fin {{
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 5px;
        padding: 6px 8px;
        text-align: center;
    }}
    .card-fin.destaque {{
        background: #eff6ff;
        border-color: #93c5fd;
    }}
    .card-fin .tit {{
        font-size: 8.5px;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        margin-bottom: 2px;
    }}
    .card-fin .num {{
        font-size: 13px;
        font-weight: 800;
        color: #0f172a;
    }}
    .card-fin.destaque .num {{
        color: #1e40af;
    }}
    
    /* Tabelas */
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 8px;
        font-size: 9.5px;
    }}
    th {{
        background: #f1f5f9;
        color: #334155;
        font-weight: 700;
        text-align: left;
        padding: 5px 6px;
        border-bottom: 1px solid #cbd5e1;
        font-size: 9px;
        text-transform: uppercase;
    }}
    td {{
        padding: 4px 6px;
        border-bottom: 1px solid #f1f5f9;
        vertical-align: middle;
    }}
    tr.row-fail td {{
        background: #fff5f5;
    }}
    tr.row-destaque td {{
        background: #f0fdf4;
        color: #166534;
        font-weight: 700;
    }}
    .status-icon.success {{ color: #16a34a; font-weight: 800; font-size: 10px; }}
    .status-icon.danger  {{ color: #dc2626; font-weight: 800; font-size: 10px; }}
    
    /* Indicadores Grid */
    .grid-ind {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 6px;
        margin-bottom: 10px;
    }}
    .card-ind {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 5px 8px;
    }}
    .card-ind .itit {{
        font-size: 8.5px;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
    }}
    .card-ind .ival {{
        font-size: 12px;
        font-weight: 700;
        color: #0f172a;
    }}
    
    /* Alerta Custo Inação */
    .alerta-inacao {{
        background: #fef2f2;
        border-left: 4px solid #ef4444;
        border-radius: 4px;
        padding: 8px 12px;
        margin: 8px 0 12px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .alerta-inacao .txt {{
        font-size: 10px;
        color: #7f1d1d;
    }}
    .alerta-inacao .val {{
        font-size: 16px;
        font-weight: 800;
        color: #b91c1c;
    }}
    
    /* Ações Cards */
    .acao-card {{
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 3px solid #2563eb;
        border-radius: 4px;
        padding: 6px 10px;
        margin-bottom: 6px;
        font-size: 9.5px;
    }}
    .acao-header {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 2px;
    }}
    .acao-tag {{
        padding: 1px 5px;
        border-radius: 3px;
        font-size: 8px;
        font-weight: 700;
    }}
    .acao-eixo {{
        font-size: 8.5px;
        color: #64748b;
        margin-left: 4px;
    }}
    .acao-titulo {{
        font-size: 11px;
        font-weight: 700;
        color: #0f172a;
        margin: 1px 0;
    }}
    .acao-diagnostico {{
        color: #64748b;
        margin-bottom: 2px;
    }}
    .acao-corpo {{
        color: #1e293b;
        margin-bottom: 3px;
    }}
    .acao-footer {{
        border-top: 1px dashed #e2e8f0;
        padding-top: 3px;
        font-size: 8.5px;
        color: #475569;
    }}
    
    /* Rodapé da Página */
    .page-footer {{
        position: absolute;
        bottom: 12px;
        left: 20px;
        right: 20px;
        border-top: 1px solid #e2e8f0;
        padding-top: 5px;
        display: flex;
        justify-content: space-between;
        font-size: 8px;
        color: #94a3b8;
    }}
</style>
</head>
<body>
<div class="boletim-container">

    <!-- ========================================== -->
    <!-- PÁGINA 1: RADIOGRAFIA & DIAGNÓSTICO LEGAL  -->
    <!-- ========================================== -->
    <div class="boletim-page">
        <!-- Top Bar -->
        <div class="header-bar">
            <div class="header-title">
                <h1>Boletim Executivo &bull; FUNDEB & VAAR</h1>
                <p>Diagnóstico de Gestão, Conformidade Legal e Radiografia Pedagógica &bull; Lei nº 14.113/2020</p>
            </div>
            <div class="header-badges">
                {badge_hab}
                {badge_benef}
                {badge_trans}
            </div>
        </div>

        <!-- Banner do Ente -->
        <div class="ente-banner">
            <div class="ente-field">
                <div class="label">Ente Federado</div>
                <div class="val">{dados.nome}</div>
            </div>
            <div class="ente-field">
                <div class="label">Esfera / UF / Região</div>
                <div class="val">{dados.esfera} &bull; {dados.uf} ({dados.regiao})</div>
            </div>
            <div class="ente-field">
                <div class="label">Código IBGE</div>
                <div class="val">{dados.ibge}</div>
            </div>
            <div class="ente-field">
                <div class="label">Situação VAAR 2026</div>
                <div class="val" style="color:{'#16a34a' if dados.habilitado else '#dc2626'};">
                    {'Elegível / Habilitado' if dados.habilitado else f'{dados.n_reprovacoes} Condic. Reprovadas'}
                </div>
            </div>
        </div>

        <!-- Financiamento Oficial -->
        <div class="section-title">1. Financiamento Oficial da Rede (Ciclo FNDE)</div>
        <div class="grid-fin">
            <div class="card-fin">
                <div class="tit">Receita Contribuição</div>
                <div class="num">{rec_contrib_fmt}</div>
            </div>
            <div class="card-fin">
                <div class="tit">Compl. VAAF</div>
                <div class="num">{vaaf_fmt}</div>
            </div>
            <div class="card-fin">
                <div class="tit">Compl. VAAT</div>
                <div class="num">{vaat_fmt}</div>
            </div>
            <div class="card-fin destaque">
                <div class="tit">Compl. VAAR (2026)</div>
                <div class="num">{vaar_26_fmt}</div>
                <small style="font-size:7.5px; color:#1e40af;">2025: {vaar_25_fmt}</small>
            </div>
            <div class="card-fin">
                <div class="tit">Total Repasses União</div>
                <div class="num">{uniao_tot_fmt}</div>
            </div>
        </div>

        <!-- Auditoria das 5 Condicionalidades -->
        <div class="section-title">2. Auditoria das 5 Condicionalidades de Gestão (Art. 14 da Lei 14.113/2020)</div>
        <table>
            <thead>
                <tr>
                    <th style="width:5%; text-align:center;">Inc.</th>
                    <th style="width:30%;">Condicionalidade & Órgão Validador</th>
                    <th style="width:15%; text-align:center;">Status Oficial</th>
                    <th style="width:50%;">Requisito Operacional e Como Cumprir</th>
                </tr>
            </thead>
            <tbody>
                {linhas_cond}
            </tbody>
        </table>

        <!-- Indicadores Pedagógicos e de Fluxo -->
        <div class="section-title">3. Indicadores Pedagógicos, de Fluxo e Equidade (Inep / Censo Escolar)</div>
        <div class="grid-ind">
            <div class="card-ind">
                <div class="itit">Saeb Língua Portuguesa</div>
                <div class="ival">{format_decimal(dados.saeb_lp, 1) if dados.saeb_lp else '—'}</div>
                <small style="font-size:7.5px; color:#64748b;">Proficiência Média</small>
            </div>
            <div class="card-ind">
                <div class="itit">Saeb Matemática</div>
                <div class="ival">{format_decimal(dados.saeb_mt, 1) if dados.saeb_mt else '—'}</div>
                <small style="font-size:7.5px; color:#64748b;">Proficiência Média</small>
            </div>
            <div class="card-ind">
                <div class="itit">Taxa de Aprovação</div>
                <div class="ival">{format_percent(dados.aprovacao_pct)}</div>
                <small style="font-size:7.5px; color:#64748b;">Rendimento Escolar</small>
            </div>
            <div class="card-ind">
                <div class="itit">Taxa de Abandono</div>
                <div class="ival" style="color:{'#dc2626' if (dados.abandono_pct or 0) > 1.5 else '#0f172a'};">{format_percent(dados.abandono_pct)}</div>
                <small style="font-size:7.5px; color:#64748b;">Penalidade no VAAR</small>
            </div>
            <div class="card-ind">
                <div class="itit">Nível Socioeconômico (INSE)</div>
                <div class="ival">{format_decimal(dados.inse_score, 2) if dados.inse_score else '—'}</div>
                <small style="font-size:7.5px; color:#64748b;">Escala Inep</small>
            </div>
            <div class="card-ind">
                <div class="itit">Internet Pedagógica</div>
                <div class="ival">{format_percent(dados.conectividade_aprendizagem_pct)}</div>
                <small style="font-size:7.5px; color:#64748b;">Banda Larga nas Escolas</small>
            </div>
            <div class="card-ind">
                <div class="itit">Indicador Atendimento</div>
                <div class="ival">{format_decimal(dados.ind_atendimento, 4) if dados.ind_atendimento else '—'}</div>
                <small style="font-size:7.5px; color:#16a34a if dados.evoluiu_atendimento else #dc2626;">{'Evoluiu (+)' if dados.evoluiu_atendimento else 'Não Evoluiu (-)'}</small>
            </div>
            <div class="card-ind">
                <div class="itit">Indicador Aprendizagem</div>
                <div class="ival">{format_decimal(dados.ind_aprendizagem, 4) if dados.ind_aprendizagem else '—'}</div>
                <small style="font-size:7.5px; color:#16a34a if dados.evoluiu_aprendizagem else #dc2626;">{'Evoluiu (+)' if dados.evoluiu_aprendizagem else 'Não Evoluiu (-)'}</small>
            </div>
        </div>

        <div class="page-footer">
            <span>Boletim Oficial de Auditoria FUNDEB/VAAR &bull; Página 1 de 2</span>
            <span>Autenticação: <strong>{dados.hash_autenticacao}</strong> &bull; Emitido: {dados.data_emissao}</span>
        </div>
    </div>

    <!-- ========================================== -->
    <!-- PÁGINA 2: SIMULAÇÃO & PLANO PROPOSITIVO    -->
    <!-- ========================================== -->
    <div class="boletim-page">
        <!-- Top Bar -->
        <div class="header-bar">
            <div class="header-title">
                <h1>Plano de Ação Propositivo &bull; Otimização VAAR</h1>
                <p>Simulação de Potencial Financeiro e Roteiro Estratégico de Execução &bull; {dados.nome} ({dados.uf})</p>
            </div>
            <div class="header-badges">
                <span class="badge badge-info">PÁGINA 2 DE 2</span>
            </div>
        </div>

        <!-- Simulação Contrafactual & Custo da Inação -->
        <div class="section-title">1. Simulação de Potencial Financeiro & Custo da Inação</div>
        
        <div class="alerta-inacao">
            <div class="txt">
                <strong>CUSTO ANUAL DA INAÇÃO / POTENCIAL FINANCEIRO NÃO CAPTADO:</strong><br>
                Recursos adicionais anuais que a rede deixa de captar em caso de inabilitação ou não evolução das metas pedagógicas.
            </div>
            <div class="val">
                {custo_inacao_fmt}
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th style="width:50%;">Cenário Contrafactual de Simulação</th>
                    <th style="width:25%; text-align:right;">Repasse Estimado (R$)</th>
                    <th style="width:25%; text-align:right;">Variação Líquida (Δ)</th>
                </tr>
            </thead>
            <tbody>
                {linhas_cenarios}
            </tbody>
        </table>

        <!-- Matriz Prescritiva de Ações -->
        <div class="section-title">2. Matriz Propositiva de Ações Estratégicas (Como Agir)</div>
        <div class="blocos-acoes-container">
            {blocos_acoes}
        </div>

        <!-- Quadro de Metas e Retorno do Investimento -->
        <div class="section-title" style="margin-top:8px;">3. Compromisso de Gestão & Retorno Educacional</div>
        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px; padding:6px 10px; font-size:9px; color:#334155;">
            <strong>Síntese de Metas para o Próximo Ciclo:</strong>
            (1) Subir certidões de provimento e BNCC no Simec dentro dos prazos legais; 
            (2) Garantir participação &ge; 85% no Saeb com busca ativa escolar; 
            (3) Reduzir o abandono escolar abaixo de 1% para maximizar o peso de atendimento ($peso_{{atend}} = 2,0$).
            O atingimento destas metas projeta elevar a receita líquida do ente para até <strong>{melhor_pot_fmt}</strong> anuais.
        </div>

        <div class="page-footer">
            <span>Fontes: FNDE, Inep, Censo Escolar, Simec &bull; Art. 14 da Lei nº 14.113/2020 &bull; Página 2 de 2</span>
            <span>Chave de Verificação: <strong>{dados.hash_autenticacao}</strong> &bull; Válido para o Ciclo 2026</span>
        </div>
    </div>

</div>
</body>
</html>
"""
