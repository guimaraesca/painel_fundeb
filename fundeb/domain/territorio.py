"""Tabelas territoriais do IBGE (códigos de UF e grandes regiões)."""

UF_CODIGO: dict[str, str] = {
    "RO": "11", "AC": "12", "AM": "13", "RR": "14", "PA": "15", "AP": "16", "TO": "17",
    "MA": "21", "PI": "22", "CE": "23", "RN": "24", "PB": "25", "PE": "26", "AL": "27",
    "SE": "28", "BA": "29", "MG": "31", "ES": "32", "RJ": "33", "SP": "35", "PR": "41",
    "SC": "42", "RS": "43", "MS": "50", "MT": "51", "GO": "52", "DF": "53",
}
CODIGO_UF: dict[str, str] = {v: k for k, v in UF_CODIGO.items()}

REGIOES: tuple[str, ...] = ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul")

REGIAO_POR_UF: dict[str, str] = {
    **dict.fromkeys(("AC", "AM", "AP", "PA", "RO", "RR", "TO"), "Norte"),
    **dict.fromkeys(("AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"), "Nordeste"),
    **dict.fromkeys(("DF", "GO", "MT", "MS"), "Centro-Oeste"),
    **dict.fromkeys(("ES", "MG", "RJ", "SP"), "Sudeste"),
    **dict.fromkeys(("PR", "RS", "SC"), "Sul"),
}
