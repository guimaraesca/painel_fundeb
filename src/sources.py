#!/usr/bin/env python3
"""
Fontes oficiais de dados do painel (URLs) e utilitário de download.

Rode em SUA máquina (os servidores gov.br/INEP exigem rede sem o proxy
restritivo do ambiente do agente):

    python src/sources.py            # lista as fontes
    python src/sources.py --download # baixa tudo em data/raw/

Depois, os parsers em src/parse/ transformam data/raw/ -> data/processed/.
(Os .json já processados acompanham o projeto, então o build roda sem baixar nada.)
"""
import sys, pathlib, urllib.request

RAW = pathlib.Path(__file__).resolve().parents[1] / "data" / "raw"

SOURCES = {
 # FNDE — Fundeb 2026 (por ente). Consolidado em base_clean.json.
 "fnde_lista_benef_vaar_2026": "https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2026-1/ListaentesbeneficiariosenaobeneficiariosacomplementacaoVAARdoFundeb2026.csv/@@download/file",
 "fnde_receita_vaaf_2026":    "https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2026-1/publicacoes-2026/3-publicacoes/1-receita-total-do-fundeb-por-ente-federado-p-11.csv/@@download/file",
 "fnde_vaat_2026":            "https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2026-1/publicacoes-2026/3-vaat-vaat-min-e-complementacao-vaat-por-ente-federado-iii.csv/@@download/file",
 "fnde_vaar_indic_2026":      "https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2026-1/indicadores-atendimento-aprendizagem-vaar-2026-iii.csv/@@download/file",
 "fnde_estimativa_vaar_2026": "https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2026-estima/estimativadacomplementacaovaarparacadaentefederadoporindicadorii.csv/@@download/file",
 "fnde_pond_nse_2026":        "https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2026-1/ponderador-de-nivel-socioeconomico.csv/@@download/file",
 "fnde_pond_drec_2026":       "https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2026-1/ponderador-de-disponibilidade-de-recursos.csv/@@download/file",
 "fnde_ind_ei_2026":          "https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2026-1/publicacoes-2026/3-publicacoes/4-indicador-para-educacao-infantil-portaria-11.csv/@@download/file",
 # FNDE — VAAR 2025 (redes beneficiadas) -> v2025.json
 "fnde_vaar_redes_2025":      "https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2025-1/6-publicacao-2013-portaria-mec-mf-n-5-de-29-de-abril-de-2026/6.RedesbeneficiadascoeficientesdedistribuioecomplementaoVAAR.csv/@@download/file",
 # INEP — Ideb 2025 (município e UF) -> ideb.json
 "ideb_ai_mun_2025": "https://download.inep.gov.br/ideb/resultados/divulgacao_anos_iniciais_municipios_2025.zip",
 "ideb_af_mun_2025": "https://download.inep.gov.br/ideb/resultados/divulgacao_anos_finais_municipios_2025.zip",
 "ideb_em_mun_2025": "https://download.inep.gov.br/ideb/resultados/divulgacao_ensino_medio_municipios_2025.zip",
 "ideb_regioes_ufs_2025": "https://download.inep.gov.br/ideb/resultados/divulgacao_regioes_ufs_ideb_2025.zip",
 # INEP — Taxas de rendimento 2025 -> rend.json
 "rend_mun_2025": "https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2025/tx_rend_municipios_2025.zip",
 "rend_ufs_2025": "https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2025/tx_rend_brasil_regioes_ufs_2025.zip",
 # INEP — INSE 2023 -> inse.json
 "inse_mun_2023": "https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2023/nivel_socioeconomico/INSE_2023_municipios.xlsx",
 # NIC.br / Base dos Dados — SIMET Educação Conectada (escola) -> conect.json
 "simet_conectividade_escola": "br_simet_educacao_conectada_escola.csv.gz  (exporte no Base dos Dados: dataset br_simet_educacao_conectada, tabela escola)",
 # Malhas IBGE (via tbrugz/geodata-br) -> geo/*.json (simplificadas)
 "geo_municipios": "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json",
 "geo_estados":    "https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/brazil-states.geojson",
}

def main():
    download = "--download" in sys.argv
    RAW.mkdir(parents=True, exist_ok=True)
    for key, url in SOURCES.items():
        print(f"- {key}: {url}")
        if download and url.startswith("http"):
            ext = ".zip" if url.endswith(".zip") else (".xlsx" if url.endswith(".xlsx") else ".csv")
            dest = RAW / (key + ext)
            try:
                urllib.request.urlretrieve(url, dest)
                print(f"    -> {dest} ({dest.stat().st_size} bytes)")
            except Exception as e:
                print(f"    !! falha: {e}")

if __name__ == "__main__":
    main()
