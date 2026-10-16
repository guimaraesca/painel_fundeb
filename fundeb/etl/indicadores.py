"""Catálogo multidimensional de indicadores.

Espinha dorsal compartilhada pelo ETL (consolidação e tabela-fato) e pelos
relatórios. Cada indicador declara sua dimensão, rótulo, unidade, fonte e o
sentido em que "melhor" aponta — permitindo que o painel deixe de ser apenas
financeiro (VAAR) e passe a tratar fluxo, aprendizagem e contexto como cidadãos
de primeira classe.

Nada aqui inventa dado: apenas descreve colunas que já existem na base auditada
(ver ``fundeb.data.repository.JsonDataRepository.entes``).
"""
from __future__ import annotations

from dataclasses import dataclass

# Dimensões analíticas
FINANCEIRO = "Financeiro"
FLUXO = "Fluxo escolar"
APRENDIZAGEM = "Aprendizagem"
CONTEXTO = "Contexto"
VAAR = "VAAR & Condicionalidades"

DIMENSOES: tuple[str, ...] = (FINANCEIRO, FLUXO, APRENDIZAGEM, CONTEXTO, VAAR)

# Sentido do "melhor"
MAIOR = "maior"   # quanto maior, melhor
MENOR = "menor"   # quanto menor, melhor
NEUTRO = "neutro"  # contextual / sem juízo de valor


@dataclass(frozen=True)
class Indicador:
    coluna: str       # coluna na base consolidada
    dimensao: str
    rotulo: str
    unidade: str      # "R$", "%", "índice", "Mbps", "bool"
    fonte: str
    melhor: str = NEUTRO
    tipo: str = "float"  # float | bool | moeda | pct


CATALOGO: tuple[Indicador, ...] = (
    # ----------------------------------------------------------- Financeiro
    Indicador("receita_contrib", FINANCEIRO, "Receita de contribuição ao Fundeb", "R$", "FNDE 2026", NEUTRO, "moeda"),
    Indicador("vaaf", FINANCEIRO, "Complementação VAAF", "R$", "FNDE 2026", NEUTRO, "moeda"),
    Indicador("vaat", FINANCEIRO, "Complementação VAAT", "R$", "FNDE 2026", NEUTRO, "moeda"),
    Indicador("vaar", FINANCEIRO, "Complementação VAAR 2026", "R$", "FNDE 2026", MAIOR, "moeda"),
    Indicador("vaar_2025", FINANCEIRO, "VAAR recebido em 2025", "R$", "FNDE 2025", NEUTRO, "moeda"),
    Indicador("uniao_total", FINANCEIRO, "Total da Complementação da União", "R$", "FNDE 2026", NEUTRO, "moeda"),
    # ----------------------------------------------------------- Fluxo escolar
    Indicador("aprov_fund", FLUXO, "Aprovação — Ensino Fundamental", "%", "Inep — Taxas de rendimento 2025", MAIOR, "pct"),
    Indicador("reprov_fund", FLUXO, "Reprovação — Ensino Fundamental", "%", "Inep — Taxas de rendimento 2025", MENOR, "pct"),
    Indicador("aband_fund", FLUXO, "Abandono — Ensino Fundamental", "%", "Inep — Taxas de rendimento 2025", MENOR, "pct"),
    Indicador("aprov_med", FLUXO, "Aprovação — Ensino Médio", "%", "Inep — Taxas de rendimento 2025", MAIOR, "pct"),
    Indicador("aband_med", FLUXO, "Abandono — Ensino Médio", "%", "Inep — Taxas de rendimento 2025", MENOR, "pct"),
    # ----------------------------------------------------------- Aprendizagem
    Indicador("ideb_ai", APRENDIZAGEM, "Ideb — Anos Iniciais", "índice", "Inep — Ideb 2025", MAIOR),
    Indicador("ideb_af", APRENDIZAGEM, "Ideb — Anos Finais", "índice", "Inep — Ideb 2025", MAIOR),
    Indicador("ideb_em", APRENDIZAGEM, "Ideb — Ensino Médio", "índice", "Inep — Ideb 2025", MAIOR),
    Indicador("saeb_ai_mt", APRENDIZAGEM, "Saeb Matemática — Anos Iniciais", "proficiência", "Inep — Saeb 2025", MAIOR),
    Indicador("saeb_ai_lp", APRENDIZAGEM, "Saeb Língua Portuguesa — Anos Iniciais", "proficiência", "Inep — Saeb 2025", MAIOR),
    Indicador("saeb_af_mt", APRENDIZAGEM, "Saeb Matemática — Anos Finais", "proficiência", "Inep — Saeb 2025", MAIOR),
    Indicador("saeb_af_lp", APRENDIZAGEM, "Saeb Língua Portuguesa — Anos Finais", "proficiência", "Inep — Saeb 2025", MAIOR),
    Indicador("saeb_em_mt", APRENDIZAGEM, "Saeb Matemática — Ensino Médio", "proficiência", "Inep — Saeb 2025", MAIOR),
    Indicador("saeb_em_lp", APRENDIZAGEM, "Saeb Língua Portuguesa — Ensino Médio", "proficiência", "Inep — Saeb 2025", MAIOR),
    # ----------------------------------------------------------- Contexto
    Indicador("inse", CONTEXTO, "Nível socioeconômico (INSE)", "índice", "Inep — INSE 2023", NEUTRO),
    Indicador("net_pct", CONTEXTO, "Escolas com internet", "%", "NIC.br/SIMET — Educação Conectada", MAIOR, "pct"),
    Indicador("net_aprend_pct", CONTEXTO, "Internet adequada à aprendizagem", "%", "NIC.br/SIMET — Educação Conectada", MAIOR, "pct"),
    Indicador("download_mbps", CONTEXTO, "Velocidade média de download", "Mbps", "NIC.br/SIMET — Educação Conectada", MAIOR),
    # ----------------------------------------------------------- VAAR & condicionalidades
    Indicador("ind_atend", VAAR, "Indicador de Atendimento (VAAR)", "índice", "FNDE 2026", MAIOR),
    Indicador("ind_aprend", VAAR, "Indicador de Aprendizagem (VAAR)", "índice", "FNDE 2026", MAIOR),
    Indicador("n_reprovacoes", VAAR, "Condicionalidades reprovadas (0–5)", "contagem", "FNDE 2026 — art. 14", MENOR),
    Indicador("habilitado", VAAR, "Habilitada ao VAAR", "bool", "FNDE 2026", MAIOR, "bool"),
    Indicador("beneficiario", VAAR, "Beneficiária do VAAR", "bool", "FNDE 2026", MAIOR, "bool"),
)

CATALOGO_POR_COLUNA = {ind.coluna: ind for ind in CATALOGO}


def indicadores_da_dimensao(dimensao: str) -> list[Indicador]:
    return [ind for ind in CATALOGO if ind.dimensao == dimensao]
