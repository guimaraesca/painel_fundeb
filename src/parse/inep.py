"""Parsers das fontes INEP → ideb.json, rend.json, inse.json.

- ideb.json: Ideb 2025 + proficiências Saeb (MT/LP) + indicador de rendimento, por
  etapa (AI/AF/EM). Município usa a linha da rede Municipal; rede estadual (IBGE de
  2 dígitos) usa o arquivo de UFs, rede Estadual.
- rend.json: taxas de aprovação/reprovação/abandono (EF e EM), rede Municipal
  (município) ou Estadual (UF).
- inse.json: INSE 2023 agregado por município (total e rede municipal).
"""
from __future__ import annotations

from pathlib import Path

from src.parse._util import num_en, texto

NOME_UF_SIGLA = {
    "Rondônia": "RO", "Acre": "AC", "Amazonas": "AM", "Roraima": "RR", "Pará": "PA",
    "Amapá": "AP", "Tocantins": "TO", "Maranhão": "MA", "Piauí": "PI", "Ceará": "CE",
    "Rio Grande do Norte": "RN", "Paraíba": "PB", "Pernambuco": "PE", "Alagoas": "AL",
    "Sergipe": "SE", "Bahia": "BA", "Minas Gerais": "MG", "Espírito Santo": "ES",
    "Rio de Janeiro": "RJ", "São Paulo": "SP", "Paraná": "PR", "Santa Catarina": "SC",
    "Rio Grande do Sul": "RS", "Mato Grosso do Sul": "MS", "Mato Grosso": "MT",
    "Goiás": "GO", "Distrito Federal": "DF",
}
SIGLA_COD = {
    "RO": "11", "AC": "12", "AM": "13", "RR": "14", "PA": "15", "AP": "16", "TO": "17",
    "MA": "21", "PI": "22", "CE": "23", "RN": "24", "PB": "25", "PE": "26", "AL": "27",
    "SE": "28", "BA": "29", "MG": "31", "ES": "32", "RJ": "33", "SP": "35", "PR": "41",
    "SC": "42", "RS": "43", "MS": "50", "MT": "51", "GO": "52", "DF": "53",
}


def _carregar(path: Path, sheet: str | None, marcador: tuple[str, ...]):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb.active
    linhas = list(ws.iter_rows(values_only=True))
    wb.close()
    hi = None
    for i, r in enumerate(linhas[:40]):
        if any((str(c).strip() in marcador) for c in r if c is not None):
            hi = i
            break
    if hi is None:
        raise ValueError(f"Cabeçalho não encontrado em {path.name}")
    cab = [str(c).strip() if c is not None else "" for c in linhas[hi]]
    return cab, linhas[hi + 1:]


def _col(cab: list[str], nome: str) -> int:
    for j, c in enumerate(cab):
        if c == nome:
            return j
    raise KeyError(f"coluna {nome} ausente")


# ----------------------------------------------------------------------- Ideb
def _ideb_etapa(path: Path, sheet: str | None, prefixo: str, col_ente: int, col_rede: int,
                rede_alvo: str, chave) -> dict[str, dict]:
    cab, dados = _carregar(path, sheet, ("VL_OBSERVADO_2025",))
    # Indicador de rendimento: nome varia entre o arquivo de municípios e o de UFs.
    ci_rend = next((j for j, c in enumerate(cab) if "INDICADOR_REND_2025" in c), None)
    ci_mt = _col(cab, "VL_NOTA_MATEMATICA_2025")
    ci_lp = _col(cab, "VL_NOTA_PORTUGUES_2025")
    ci_obs = _col(cab, "VL_OBSERVADO_2025")
    out: dict[str, dict] = {}
    for r in dados:
        if not r or len(r) <= max(col_ente, col_rede, ci_obs):
            continue
        if texto(r[col_rede]) != rede_alvo:
            continue
        k = chave(r)
        if not k:
            continue
        out[k] = {
            f"{prefixo}_ideb": num_en(r[ci_obs]),
            f"{prefixo}_mat": num_en(r[ci_mt]),
            f"{prefixo}_lp": num_en(r[ci_lp]),
            f"{prefixo}_rend": num_en(r[ci_rend]) if ci_rend is not None else None,
        }
    return out


def construir_ideb(raw: Path) -> dict:
    ext = raw / "ext"
    base = {
        "ai": "ideb_ai_mun_2025/divulgacao_anos_iniciais_municipios_2025/divulgacao_anos_iniciais_municipios_2025.xlsx",
        "af": "ideb_af_mun_2025/divulgacao_anos_finais_municipios_2025/divulgacao_anos_finais_municipios_2025.xlsx",
        "em": "ideb_em_mun_2025/divulgacao_ensino_medio_municipios_2025/divulgacao_ensino_medio_municipios_2025.xlsx",
    }
    uf_file = ext / "ideb_regioes_ufs_2025/divulgacao_regioes_ufs_ideb_2025/divulgacao_regioes_ufs_ideb_2025.xlsx"
    uf_sheets = {"ai": "UF e Regiões (AI)", "af": "UF e Regiões (AF)", "em": "UF e Regiões (EM)"}

    out: dict[str, dict] = {}
    # Municípios (rede Municipal), código IBGE de 7 dígitos
    for etapa, rel in base.items():
        parcial = _ideb_etapa(ext / rel, None, etapa, col_ente=1, col_rede=3,
                              rede_alvo="Municipal", chave=lambda r: texto(r[1]))
        for ib, vals in parcial.items():
            out.setdefault(ib, {}).update(vals)
    # UFs (rede Estadual), código de 2 dígitos
    for etapa, sheet in uf_sheets.items():
        parcial = _ideb_etapa(uf_file, sheet, etapa, col_ente=0, col_rede=1,
                              rede_alvo="Estadual",
                              chave=lambda r: SIGLA_COD.get(NOME_UF_SIGLA.get(texto(r[0]), ""), ""))
        for cod, vals in parcial.items():
            if cod:
                out.setdefault(cod, {}).update(vals)
    return out


# ---------------------------------------------------------------- Rendimento
def _rend_linha(cab: list[str]) -> dict[str, int]:
    return {
        "ap_fun": _col(cab, "1_CAT_FUN"), "ap_med": _col(cab, "1_CAT_MED"),
        "rp_fun": _col(cab, "2_CAT_FUN"), "rp_med": _col(cab, "2_CAT_MED"),
        "ab_fun": _col(cab, "3_CAT_FUN"), "ab_med": _col(cab, "3_CAT_MED"),
    }


def construir_rend(raw: Path) -> dict:
    ext = raw / "ext"
    out: dict[str, dict] = {}

    # Municípios: Localização=Total, Dependência=Municipal
    mp = ext / "rend_mun_2025/tx_rend_municipios_2025/tx_rend_municipios_2025.xlsx"
    cab, dados = _carregar(mp, None, ("1_CAT_FUN",))
    ci = _rend_linha(cab)
    c_ib, c_cat, c_dep = _col(cab, "CO_MUNICIPIO"), _col(cab, "NO_CATEGORIA"), _col(cab, "NO_DEPENDENCIA")
    for r in dados:
        if not r or len(r) <= max(ci.values()):
            continue
        if texto(r[c_cat]) != "Total" or texto(r[c_dep]) != "Municipal":
            continue
        ib = texto(r[c_ib])
        if ib.isdigit() and len(ib) == 7:
            out[ib] = {k: num_en(r[j]) for k, j in ci.items()}

    # UFs (rede Estadual): UNIDGEO = nome da unidade geográfica (Brasil/região/UF).
    up = ext / "rend_ufs_2025/tx_rend_brasil_regioes_ufs_2025/tx_rend_brasil_regioes_ufs_2025.xlsx"
    cab2, dados2 = _carregar(up, None, ("1_CAT_FUN",))
    ci2 = _rend_linha(cab2)
    c_geo = _col(cab2, "UNIDGEO")
    c_cat2 = _col(cab2, "NO_CATEGORIA")
    c_dep2 = _col(cab2, "NO_DEPENDENCIA")
    for r in dados2:
        if not r or len(r) <= max(ci2.values()):
            continue
        if texto(r[c_cat2]) != "Total" or texto(r[c_dep2]) != "Estadual":
            continue
        cod = SIGLA_COD.get(NOME_UF_SIGLA.get(texto(r[c_geo]), ""), "")
        if cod:
            out[cod] = {k: num_en(r[j]) for k, j in ci2.items()}
    return out


# ----------------------------------------------------------------------- INSE
def construir_inse(raw: Path) -> dict:
    """INSE 2023 agregado por município: inse_tot (todas as redes) e inse_mun
    (rede municipal), ponderado por QTD_ALUNOS_INSE."""
    # Cada linha já é a MÉDIA PONDERADA de um estrato (rede × localização). Usamos:
    #   inse_tot = TP_TIPO_REDE=6 (Total Federal+Estadual+Municipal), TP_LOCALIZACAO=0 (Total)
    #   inse_mun = TP_TIPO_REDE=3 (Municipal), TP_LOCALIZACAO=0 (Total)
    cab, dados = _carregar(raw / "inse_mun_2023.xlsx", "INSE_MUN_2023", ("CO_MUNICIPIO",))
    c_ib = _col(cab, "CO_MUNICIPIO")
    c_rede = _col(cab, "TP_TIPO_REDE")
    c_loc = _col(cab, "TP_LOCALIZACAO")
    c_media = _col(cab, "MEDIA_INSE")

    out: dict[str, dict] = {}
    for r in dados:
        if not r or len(r) <= max(c_ib, c_rede, c_loc, c_media):
            continue
        ib = texto(r[c_ib])
        if not (ib.isdigit() and len(ib) == 7) or texto(r[c_loc]) != "0":
            continue
        rede, m = texto(r[c_rede]), num_en(r[c_media])
        if m is None:
            continue
        reg = out.setdefault(ib, {"inse_mun": None, "inse_tot": None, "_t5": None})
        if rede == "6":
            reg["inse_tot"] = round(m, 3)
        elif rede == "5":
            reg["_t5"] = round(m, 3)  # fallback quando não há rede=6 (município sem rede federal)
        elif rede == "3":
            reg["inse_mun"] = round(m, 3)
    for reg in out.values():
        if reg["inse_tot"] is None:
            reg["inse_tot"] = reg["_t5"]
        del reg["_t5"]
    return out
