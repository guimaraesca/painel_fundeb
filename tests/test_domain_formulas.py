"""Testes unitários das fórmulas matemáticas puras do VAAR."""
import math
import pytest
from fundeb.domain.formulas import (
    peso_indicador,
    razao,
    iee_cenarios,
    ind_atendimento,
    ind_aprendizagem,
    ipa,
)


def test_peso_indicador_limites():
    # Para IND = 0, peso = 2 - exp(0) = 1.0
    assert pytest.approx(peso_indicador(0.0), rel=1e-5) == 1.0

    # Para IND alto, peso tende a 2.0
    assert pytest.approx(peso_indicador(5.0), rel=1e-3) == 2.0

    # Para IND intermediário (ex: 0.5): 2 - exp(-2) = 2 - 0.135335 = 1.86466
    assert pytest.approx(peso_indicador(0.5), rel=1e-4) == 1.86466

    # Se None ou NaN, retorna NaN
    assert math.isnan(peso_indicador(None))
    assert math.isnan(peso_indicador(float("nan")))


def test_razao():
    assert pytest.approx(razao(110, 100), rel=1e-5) == 1.10
    assert razao(100, 0) is None
    assert razao(None, 100) is None


def test_iee_cenarios():
    # Simula matrícula crescendo 10% de 2017 a 2020
    mats = {2017: 1000, 2018: 1020, 2019: 1050, 2020: 1100, 2021: 1120, 2022: 1150, 2023: 1200}
    cenarios = iee_cenarios(mats)
    assert len(cenarios) == 5

    # Primeiro cenário (IEE vigente 2017->2020)
    c1 = cenarios[0]
    assert c1["cenario"] == "IEE vigente"
    assert pytest.approx(c1["iee"], rel=1e-4) == 1.10
    assert c1["evolui"] is True


def test_ind_atendimento():
    # IND_Atend = IEE * (1 - IAE)
    assert pytest.approx(ind_atendimento(1.10, 0.05), rel=1e-5) == 1.10 * 0.95


def test_ipa_e_aprendizagem():
    # IPA = 0.3 * aprendizagem + 0.7 * progresso
    val_ipa = ipa(100.0, 100.0)
    assert pytest.approx(val_ipa, rel=1e-5) == 100.0

    # IND_Aprend = IPA * IAPE
    assert pytest.approx(ind_aprendizagem(100.0, 0.90), rel=1e-5) == 90.0
