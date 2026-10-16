#!/usr/bin/env python3
"""Extract — download das fontes oficiais para ``data/raw`` (+ extração de ZIPs).

Fontes:
- FNDE (gov.br): CSV latin-1 — Fundeb 2026 por ente + VAAR 2025.
- INEP (download.inep.gov.br): ZIP/XLSX — Ideb, taxas de rendimento, INSE.
  Observação: a cadeia de certificados do host do INEP falha em alguns ambientes;
  por isso o download do INEP usa um contexto SSL sem verificação de cadeia
  (os arquivos são públicos e sua integridade é checada depois no pipeline).
- IBGE (via GitHub): malhas geográficas.

Uso:
    python src/sources.py             # lista as fontes
    python src/sources.py --download  # baixa tudo em data/raw/ e extrai os ZIPs
"""
from __future__ import annotations

import ssl
import sys
import urllib.request
import zipfile
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
EXT = RAW / "ext"

# chave -> (url, extensão, precisa_ssl_relaxado)
SOURCES: dict[str, tuple[str, str, bool]] = {
    # FNDE — Fundeb 2026 (por ente) → base_clean.json
    "fnde_lista_benef_vaar_2026": ("https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2026-1/ListaentesbeneficiariosenaobeneficiariosacomplementacaoVAARdoFundeb2026.csv/@@download/file", ".csv", False),
    "fnde_receita_vaaf_2026": ("https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2026-1/publicacoes-2026/3-publicacoes/1-receita-total-do-fundeb-por-ente-federado-p-11.csv/@@download/file", ".csv", False),
    "fnde_vaat_2026": ("https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2026-1/publicacoes-2026/3-vaat-vaat-min-e-complementacao-vaat-por-ente-federado-iii.csv/@@download/file", ".csv", False),
    "fnde_vaar_indic_2026": ("https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2026-1/indicadores-atendimento-aprendizagem-vaar-2026-iii.csv/@@download/file", ".csv", False),
    "fnde_estimativa_vaar_2026": ("https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2026-estima/estimativadacomplementacaovaarparacadaentefederadoporindicadorii.csv/@@download/file", ".csv", False),
    "fnde_pond_nse_2026": ("https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2026-1/ponderador-de-nivel-socioeconomico.csv/@@download/file", ".csv", False),
    "fnde_pond_drec_2026": ("https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2026-1/ponderador-de-disponibilidade-de-recursos.csv/@@download/file", ".csv", False),
    "fnde_ind_ei_2026": ("https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2026-1/publicacoes-2026/3-publicacoes/4-indicador-para-educacao-infantil-portaria-11.csv/@@download/file", ".csv", False),
    # FNDE — VAAR 2025 → v2025.json
    "fnde_vaar_redes_2025": ("https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2025-1/6-publicacao-2013-portaria-mec-mf-n-5-de-29-de-abril-de-2026/6.RedesbeneficiadascoeficientesdedistribuioecomplementaoVAAR.csv/@@download/file", ".csv", False),
    # INEP — Ideb 2025 → ideb.json
    "ideb_ai_mun_2025": ("https://download.inep.gov.br/ideb/resultados/divulgacao_anos_iniciais_municipios_2025.zip", ".zip", True),
    "ideb_af_mun_2025": ("https://download.inep.gov.br/ideb/resultados/divulgacao_anos_finais_municipios_2025.zip", ".zip", True),
    "ideb_em_mun_2025": ("https://download.inep.gov.br/ideb/resultados/divulgacao_ensino_medio_municipios_2025.zip", ".zip", True),
    "ideb_regioes_ufs_2025": ("https://download.inep.gov.br/ideb/resultados/divulgacao_regioes_ufs_ideb_2025.zip", ".zip", True),
    # INEP — Taxas de rendimento 2025 → rend.json
    "rend_mun_2025": ("https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2025/tx_rend_municipios_2025.zip", ".zip", True),
    "rend_ufs_2025": ("https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2025/tx_rend_brasil_regioes_ufs_2025.zip", ".zip", True),
    # INEP — INSE 2023 → inse.json
    "inse_mun_2023": ("https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2023/nivel_socioeconomico/INSE_2023_municipios.xlsx", ".xlsx", True),
    # IBGE (via GitHub) → geo/*.json
    "geo_estados": ("https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/brazil-states.geojson", ".geojson", False),
    "geo_municipios": ("https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json", ".json", False),
}

# Inputs já preparados (não há URL simples de 1 arquivo):
#   conect.json  — NIC.br/SIMET Educação Conectada (export do Base dos Dados / BigQuery)
#   sim_atend.json — matrículas da etapa do IEE 2017–2023 (repo Simulador-VAAR-PI)
#   geo/*_simpl.json — malhas IBGE simplificadas (ver src/parse/geo.py)


def _opener(relaxar_ssl: bool) -> urllib.request.OpenerDirector:
    ctx = ssl.create_default_context()
    if relaxar_ssl:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))


def baixar() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    EXT.mkdir(parents=True, exist_ok=True)
    for key, (url, ext, relaxar) in SOURCES.items():
        dest = RAW / (key + ext)
        try:
            op = _opener(relaxar)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (fundeb-etl)"})
            with op.open(req, timeout=180) as resp, open(dest, "wb") as f:
                f.write(resp.read())
            print(f"  ✓ {key}{ext} ({dest.stat().st_size:,} bytes)".replace(",", "."))
            if ext == ".zip":
                destino = EXT / key
                with zipfile.ZipFile(dest) as z:
                    z.extractall(destino)
                print(f"      → extraído em {destino.relative_to(RAW.parent.parent)}")
        except Exception as e:
            print(f"  ✗ {key}: {e}")


def main() -> None:
    if "--download" in sys.argv:
        print("Baixando fontes oficiais (FNDE, INEP, IBGE)...")
        baixar()
    else:
        for key, (url, _ext, relaxar) in SOURCES.items():
            print(f"- {key}{' [SSL relaxado]' if relaxar else ''}: {url}")


if __name__ == "__main__":
    main()
