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


# ----------------------------------------------------------------
# Metodologia Canônica das Especificações Técnicas (MEC/Inep/FNDE)
# ----------------------------------------------------------------

def ind_atendimento_sir(abandono: float, sir: float, matriculas: float) -> float:
    """VAAR_Atendimento = 1 − (Abandono + 0,5 × SIR) / M.
    
    Penaliza a omissão de informação de rendimento/movimento (SIR) com fator 0,5.
    """
    if not _valido(matriculas) or matriculas <= 0:
        return float("nan")
    ab = abandono if _valido(abandono) else 0.0
    si = sir if _valido(sir) else 0.0
    return 1.0 - ((ab + 0.5 * si) / float(matriculas))


def delta_evolucao(atual: float | None, anterior: float | None) -> float:
    """Δ = atual − anterior (requer Δ ≥ 0 para habilitação, observada margem de erro)."""
    if not _valido(atual) or not _valido(anterior):
        return float("nan")
    return float(atual) - float(anterior)


def peso_distribuicao_minmax(valor: float | None, min_val: float, max_val: float) -> float:
    """peso = 1 + (valor − Min) / (Max − Min).
    
    Ajusta linearmente o peso das matrículas no intervalo contínuo [1, 2].
    O menor habilitado positivo recebe peso 1 e o melhor recebe peso 2.
    """
    if not _valido(valor):
        return 1.0
    v = float(valor)
    if max_val <= min_val:
        return 1.0
    ratio = (v - min_val) / (max_val - min_val)
    return 1.0 + max(0.0, min(1.0, ratio))


def inad_normalizado(inad_bruto: float, min_escala: float = -7.0, max_escala: float = 10.0) -> float:
    """Inad_Norm = (Inad_Bruto − (-7)) / (10 − (-7)).
    
    Transformação linear que converte a escala teórica [-7, 10] para [0, 1].
    """
    if not _valido(inad_bruto):
        return 0.0
    return (float(inad_bruto) - min_escala) / (max_escala - min_escala)


def inad_ponderado(ind: float, iad: float, tap: float = 1.0) -> float:
    """Inad = (0,3 × IND + 0,7 × IAD) × TAp.
    
    Combina patamar (IND peso 0,3), avanço (IAD peso 0,7) e Taxa de Aprovação (TAp).
    """
    ind_v = float(ind) if _valido(ind) else 0.0
    iad_v = float(iad) if _valido(iad) else 0.0
    tap_v = float(tap) if _valido(tap) else 1.0
    return (0.3 * ind_v + 0.7 * iad_v) * tap_v


def ind_aprendizagem_triade(inad_norm: float, ip_saeb: float, ind_equi: float) -> float:
    """VAAR_Aprendizagem = Inad_Norm × IPSaeb × IndEqui.
    
    Síntese estrutural combinando desempenho normalizado, presença no Saeb (≥ 0,80)
    e índice de equidade socioeconômica e racial (INE-S e INE-R).
    """
    if not _valido(inad_norm) or not _valido(ip_saeb) or not _valido(ind_equi):
        return float("nan")
    return float(inad_norm) * float(ip_saeb) * float(ind_equi)


def coeficiente_distribuicao(matricula: float, peso: float, soma_matriculas_ponderadas: float) -> float:
    """C = (M × peso) / Σ (Mi × pesoi)."""
    if not _valido(soma_matriculas_ponderadas) or soma_matriculas_ponderadas <= 0:
        return 0.0
    m = float(matricula) if _valido(matricula) else 0.0
    p = float(peso) if _valido(peso) else 1.0
    return (m * p) / float(soma_matriculas_ponderadas)


def repasse_reais(coeficiente: float, montante_global_vaar: float, cota: float = 0.5) -> float:
    """Repasse = C × (cota × Montante_Global_VAAR)."""
    if not _valido(coeficiente) or not _valido(montante_global_vaar):
        return 0.0
    return float(coeficiente) * (cota * float(montante_global_vaar))

