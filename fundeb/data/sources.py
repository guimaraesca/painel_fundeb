"""Registro de fontes: o que cada arquivo contém e de onde veio."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fonte:
    arquivo: str
    conteudo: str
    origem: str


FONTES: tuple[Fonte, ...] = (
    Fonte("base_clean.json", "Fundeb 2026 por rede: receita, VAAF, VAAT, VAAR (atendimento/aprendizagem), "
          "condicionalidades, habilitação, pendências e ponderadores",
          "FNDE — Publicações Fundeb 2026 e lista de beneficiários/não beneficiários do VAAR 2026"),
    Fonte("v2025.json", "VAAR recebido em 2025 por rede (R$)",
          "FNDE — Redes beneficiadas, coeficientes e complementação VAAR 2025"),
    Fonte("ideb.json", "Ideb 2025 e proficiências Saeb (anos iniciais, finais, ensino médio)",
          "Inep — Divulgação Ideb 2025 (municípios e UFs)"),
    Fonte("rend.json", "Taxas de aprovação, reprovação e abandono 2025",
          "Inep — Indicadores educacionais: taxas de rendimento 2025"),
    Fonte("inse.json", "Indicador de Nível Socioeconômico (INSE) 2023", "Inep — INSE 2023"),
    Fonte("conect.json", "Conectividade das escolas: % com internet, % adequada à aprendizagem, download",
          "NIC.br — SIMET/Educação Conectada (via Base dos Dados)"),
    Fonte("sim_atend.json", "Matrículas da etapa de referência do IEE 2017–2023 (rede estadual: ensino médio; "
          "rede municipal: educação infantil), matrícula total 2023, IEE e IAE do ciclo 2024",
          "Censo Escolar/Inep, compilado na planilha Produto_Simulador_VAAR_Atendimento.xlsx "
          "(guimaraesca/Simulador-VAAR-PI, aba IEE)"),
    Fonte("geo/uf_simpl.json", "Malha das UFs (simplificada)", "IBGE (via codeforgermany/click_that_hood)"),
    Fonte("geo/mun_simpl.json", "Malha municipal (simplificada)", "IBGE (via tbrugz/geodata-br)"),
)

FONTE_POR_ARQUIVO = {f.arquivo: f for f in FONTES}
