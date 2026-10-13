"""Fórmulas do VAAR — funções puras e testáveis.

Origem: planilhas ``Produto_Simulador_VAAR_Atendimento.xlsx`` e
``Produto_Simulador_VAAR_Aprendizagem.xlsx`` do repositório *guimaraesca/Simulador-VAAR-PI*,
que implementam a Nota Técnica Inep nº 23/2022 (ciclo de cálculo 2024).

Importante: o método oficial pode mudar a cada ciclo. Estas fórmulas descrevem o
ciclo documentado e servem para leitura e sensibilidade; os valores em R$ exibidos
no painel vêm sempre das publicações do FNDE.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

K_PESO = 4.0  # constante do peso exponencial (planilha: 2-EXP((-4)*IND))


def _valido(x: float | None) -> bool:
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def peso_indicador(ind: float | None, k: float = K_PESO) -> float:
    """Peso da matrícula na distribuição do VAAR: ``2 − e^(−k·IND)``.

    Varia de 1 (IND = 0) até o limite 2 (IND → ∞).
    """
    if not _valido(ind):
        return float("nan")
    return 2.0 - math.exp(-k * float(ind))


def razao(fim: float | None, inicio: float | None) -> float | None:
    """Razão simples ``fim / inicio`` (None se o denominador for inválido)."""
    if not _valido(fim) or not _valido(inicio) or not inicio:
        return None
    return float(fim) / float(inicio)


#: Cenários de IEE da planilha de Atendimento (o produto das variações anuais
#: simplifica para a razão entre matrículas do ano final e do inicial).
CENARIOS_IEE: tuple[tuple[str, int, int, str], ...] = (
    ("IEE vigente", 2017, 2020, "var18/17 × var19/18 × var20/19"),
    ("Cenário (a) — com 2021", 2018, 2021, "var19/18 × var20/19 × var21/20"),
    ("Cenário (b) — sem 2021", 2018, 2022, "var19/18 × var20/19 × var22/20"),
    ("Cenário (c) — 2 anos com 2021", 2019, 2022, "var20/19 × var21/20 × var22/21"),
    ("Cenário (d) — 2 anos sem 2021", 2019, 2023, "var20/19 × var22/20 × var23/22"),
)


def iee_cenarios(matriculas: Mapping[int, float]) -> list[dict]:
    """Índice de Expansão Escolar em cada cenário da planilha (IEE ≥ 1 ⇒ evolução)."""
    out = []
    for nome, ini, fim, formula in CENARIOS_IEE:
        v = razao(matriculas.get(fim), matriculas.get(ini))
        out.append({"cenario": nome, "periodo": f"{ini}→{fim}", "formula": formula, "iee": v,
                    "evolui": (v is not None and v >= 1.0)})
    return out


def media_ponderada_taxas(taxas_e_pesos: Sequence[tuple[float, float]]) -> float | None:
    """Σ(taxa% × matrículas) / (100 × Σ matrículas). Usada no IAE (abandono) e no IAPE (aprovação)."""
    pares = [(t, m) for t, m in taxas_e_pesos if _valido(t) and _valido(m) and m > 0]
    den = sum(m for _, m in pares)
    if not den:
        return None
    return sum(t * m for t, m in pares) / (100.0 * den)


def ind_atendimento(iee: float, iae: float) -> float:
    """IND_Atend = IEE × (1 − IAE)."""
    return iee * (1.0 - iae)


def aprendizagem(media_proficiencia: float, ine: float, ide_raca: float, ide_social: float) -> float:
    """Aprendizagem = Média de proficiência × INE × (IDE_raça + IDE_social) / 2."""
    return media_proficiencia * ine * (ide_raca + ide_social) / 2.0


def progresso(atual: Mapping[str, float], anterior: Mapping[str, float]) -> float:
    """Progresso = Σ razões (atual/anterior) de proficiência, INE, IDE_raça e IDE_social."""
    chaves = ("proficiencia", "ine", "ide_raca", "ide_social")
    return sum(atual[k] / anterior[k] for k in chaves)


def ipa(aprendizagem_atual: float, progresso_: float) -> float:
    """IPA = 0,3 × Aprendizagem + 0,7 × Progresso."""
    return 0.3 * aprendizagem_atual + 0.7 * progresso_


def ind_aprendizagem(ipa_: float, iape: float) -> float:
    """IND_Aprend = IPA × IAPE."""
    return ipa_ * iape
