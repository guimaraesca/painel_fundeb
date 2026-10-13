"""Testes de integração dos serviços e integridade de dados."""
import pytest
from fundeb.data.repository import JsonDataRepository
from fundeb.services.analytics import AnalyticsService
from fundeb.services.simulator import SimulatorService
from fundeb.data.validation import validar_tudo


@pytest.fixture(scope="session")
def repo():
    return JsonDataRepository()


@pytest.fixture(scope="session")
def df(repo):
    return repo.entes()


def test_repositorio_entes(df):
    assert len(df) == 5596
    assert "ibge" in df.columns
    assert "habilitado" in df.columns
    assert "beneficiario" in df.columns


def test_analytics_resumo_nacional(df):
    analytics = AnalyticsService(df)
    res = analytics.resumo_nacional()

    assert res.total_entes == 5596
    assert res.total_estados == 27
    assert res.total_municipios == 5569
    assert res.habilitados == 3076
    assert res.nao_habilitados == 2520
    assert res.total_vaar_reais > 0


def test_analytics_gargalos_condicionalidade(df):
    analytics = AnalyticsService(df)
    gargalos = analytics.gargalos_condicionalidade()

    # Verifica os gargalos exatos citados nos requisitos do usuário
    d_gargalos = {g.codigo: g.reprovacoes_nao_habilitadas for g in gargalos}
    assert d_gargalos["Cond. III"] == 1930
    assert d_gargalos["Cond. I"] == 575
    assert d_gargalos["Cond. II"] == 417
    assert d_gargalos["Cond. IV"] == 93


def test_simulador_estadual_vs_municipal(df):
    sim = SimulatorService(df)

    # Rede Municipal (Teresina ou SP Capital)
    sp_mun = sim.simular_ente("3550308", delta_atendimento_pct=10.0)
    assert sp_mun is not None
    assert sp_mun.esfera == "Municipal"
    assert "Educação Infantil" in sp_mun.etapa_atendimento

    # Rede Estadual (SP Estado ou PI Estado)
    pi_est = sim.simular_ente("22", delta_atendimento_pct=10.0)
    assert pi_est is not None
    assert pi_est.esfera == "Estadual"
    assert "Ensino Médio" in pi_est.etapa_atendimento


def test_auditoria_qualidade_dados(repo, df):
    from fundeb.data.validation import verificar, cobertura, proveniencia, OK
    verifs = verificar(df)
    assert len(verifs) > 0
    # Verifica que o fechamento contábil e unicidade IBGE estão OK
    unicidade = next(v for v in verifs if "Código IBGE único" in v.nome)
    assert unicidade.status == OK

    fechamento = next(v for v in verifs if "VAAF + VAAT + VAAR" in v.nome)
    assert fechamento.status == OK

    split = next(v for v in verifs if "50% / 50%" in v.nome)
    assert split.status == OK

    df_prov = proveniencia(repo)
    assert len(df_prov) > 0
    assert "SHA-256" in df_prov.columns

    df_cob = cobertura(df)
    assert len(df_cob) > 0
