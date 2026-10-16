"""Parser das fontes FNDE → base_clean.json e v2025.json.

Faz o *merge* por código IBGE de 8 publicações do FNDE (receita/VAAF/VAAT/VAAR,
indicadores, condicionalidades, estimativas e ponderadores) na base única que
alimenta o painel. Rede estadual = IBGE de 2 dígitos; município = 7 dígitos.
"""
from __future__ import annotations

from pathlib import Path

from src.parse._util import ler_csv, num, texto

HEADER = [
    "UF", "IBGE", "Entidade", "Rede", "Receita_Contrib", "Compl_VAAF", "Compl_VAAT",
    "Compl_VAAR", "Compl_Uniao_Total", "Total_Receitas_Prev", "VAAT_antes", "VAAT_com_compl",
    "VAAT_compl", "IEI_pct", "VAAR_coef", "VAAR_valor_redes", "VAAR_evoluiu_atend",
    "VAAR_ind_atend", "VAAR_evoluiu_aprend", "VAAR_ind_aprend", "Cond_I", "Cond_II", "Cond_III",
    "Cond_IV", "Cond_V", "Habilitado_VAAR", "Benef_VAAR", "Pend_VAAR", "Est_VAAR_atend",
    "Est_VAAR_aprend", "Est_VAAR_total", "Pond_NSE", "Pond_Drec", "Compl_VAAT_EI", "VAAT_hab_status",
]


def _ibge_valido(s: str) -> bool:
    return s.isdigit() and len(s) in (2, 7)


def _indexar(path: Path, col_ibge: int, extrai, marcador=("UF",)) -> dict[str, dict]:
    """Lê um CSV do FNDE e indexa por IBGE aplicando ``extrai(linha) -> dict``."""
    _, dados = ler_csv(path, marcador)
    out: dict[str, dict] = {}
    for r in dados:
        if len(r) <= col_ibge:
            continue
        ib = texto(r[col_ibge])
        if not _ibge_valido(ib):
            continue
        out[ib] = extrai(r)
    return out


def construir_base_clean(raw: Path) -> dict:
    # Espinha: receita total do Fundeb (tem todos os entes + valores financeiros).
    _, linhas_receita = ler_csv(raw / "fnde_receita_vaaf_2026.csv", ("UF",))

    # IEI publicado em % (ex.: "54%"); a base armazena como fração (0,54).
    vaat = _indexar(raw / "fnde_vaat_2026.csv", 2, lambda r: {
        "antes": num(r[3]), "com": num(r[4]), "compl": num(r[5]),
        "iei": (num(r[6]) / 100 if num(r[6]) is not None else None)})
    indic = _indexar(raw / "fnde_vaar_indic_2026.csv", 2, lambda r: {
        "ea": texto(r[3]), "ia": num(r[4]), "ep": texto(r[5]), "ip": num(r[6])})
    # Campos de condicionalidade/status preservam o texto bruto publicado (inclusive '-'),
    # exatamente como a fonte; o painel os interpreta com _sim() (começa com 's' = Sim).
    benef = _indexar(raw / "fnde_lista_benef_vaar_2026.csv", 1, lambda r: {
        "c1": r[3] or None, "c2": r[4] or None, "c3": r[5] or None, "c4": r[6] or None, "c5": r[7] or None,
        "hab": r[8] or None, "ben": r[11] or None, "pend": texto(r[12])})
    estim = _indexar(raw / "fnde_estimativa_vaar_2026.csv", 1, lambda r: {
        "a": num(r[5]), "b": num(r[6]), "c": num(r[7])})
    nse = _indexar(raw / "fnde_pond_nse_2026.csv", 2, lambda r: num(r[3]))
    drec = _indexar(raw / "fnde_pond_drec_2026.csv", 2, lambda r: num(r[3]))
    indei = _indexar(raw / "fnde_ind_ei_2026.csv", 2, lambda r: {"iei": num(r[4]), "ei": num(r[5])})

    recs = []
    for r in linhas_receita:
        if len(r) < 9:
            continue
        ib = texto(r[1])
        if not _ibge_valido(ib):
            continue
        estadual = len(ib) == 2
        vt, idc, bf, es, ie = (d.get(ib, {}) for d in (vaat, indic, benef, estim, indei))

        rec = {
            "UF": texto(r[0]),
            "IBGE": ib,
            "Entidade": "GOVERNO DO ESTADO" if estadual else texto(r[2]),
            "Rede": "Estadual" if estadual else "Municipal",
            "Receita_Contrib": num(r[3]),
            "Compl_VAAF": num(r[4]),
            "Compl_VAAT": num(r[5]),
            "Compl_VAAR": num(r[6]),
            "Compl_Uniao_Total": num(r[7]),
            "Total_Receitas_Prev": num(r[8]),
            "VAAT_antes": vt.get("antes"),
            "VAAT_com_compl": vt.get("com"),
            "VAAT_compl": vt.get("compl"),
            "IEI_pct": vt.get("iei"),
            "VAAR_coef": None,          # publicado em arquivo próprio de redes beneficiárias (não consumido pelo painel)
            "VAAR_valor_redes": None,   # idem
            "VAAR_evoluiu_atend": idc.get("ea") or None,
            "VAAR_ind_atend": idc.get("ia"),
            "VAAR_evoluiu_aprend": idc.get("ep") or None,
            "VAAR_ind_aprend": idc.get("ip"),
            "Cond_I": bf.get("c1") or None,
            "Cond_II": bf.get("c2") or None,
            "Cond_III": bf.get("c3") or None,
            "Cond_IV": bf.get("c4") or None,
            "Cond_V": bf.get("c5") or None,
            "Habilitado_VAAR": bf.get("hab") or None,
            "Benef_VAAR": bf.get("ben") or None,
            "Pend_VAAR": bf.get("pend") or "",
            "Est_VAAR_atend": es.get("a"),
            "Est_VAAR_aprend": es.get("b"),
            "Est_VAAR_total": es.get("c"),
            "Pond_NSE": nse.get(ib),
            "Pond_Drec": drec.get(ib),
            "Compl_VAAT_EI": ie.get("ei"),
            "VAAT_hab_status": "Habilitado para o cálculo do VAAT.",
        }
        recs.append(rec)

    return {"header": HEADER, "recs": recs}


def construir_v2025(raw: Path) -> dict:
    """VAAR recebido em 2025 por rede (R$ inteiro), de redes beneficiadas 2025."""
    _, dados = ler_csv(raw / "fnde_vaar_redes_2025.csv", ("UF",))
    out: dict[str, int] = {}
    for r in dados:
        if len(r) < 5:
            continue
        ib = texto(r[2])
        if not (ib.isdigit() and len(ib) in (2, 7)):
            continue
        v = num(r[4])
        if v:
            out[ib] = int(v + 0.5)  # arredondamento meio-para-cima (R$ inteiro)
    return out
