"""Utilitários de parsing das fontes oficiais (FNDE em CSV latin-1, INEP em XLSX).

Regras transversais:
- CSV do FNDE: encoding latin-1, delimitador ';', vírgula decimal e ponto de milhar
  (padrão BR), com linhas de cabeçalho institucional antes da linha de colunas.
- Valores ausentes na fonte ('-', '', '**', 'ND') viram None (nunca 0 implícito).
- IBGE: 2 dígitos = rede estadual (UF); 7 dígitos = município.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterator

AUSENTES = {"", "-", "--", "**", "***", "ND", "N/D", "nan", "None", "x", "X"}


def num(v: Any) -> float | None:
    """Converte número no padrão BR ('1.234.567,89', '54%', '-') para float ou None."""
    if v is None:
        return None
    s = str(v).strip().replace("%", "").strip()
    if s in AUSENTES:
        return None
    # remove ponto de milhar e troca vírgula decimal por ponto
    s = s.replace(".", "").replace(",", ".") if ("," in s) else s
    try:
        return float(s)
    except ValueError:
        return None


def num_en(v: Any) -> float | None:
    """Converte número no padrão EN do INEP ('77.2', '0.759273', '-') para float ou None."""
    if v is None:
        return None
    s = str(v).strip()
    if s in AUSENTES:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def sim(v: Any) -> bool:
    return str(v or "").strip().lower().startswith("s")


def texto(v: Any) -> str:
    s = str(v).strip() if v is not None else ""
    return "" if s in AUSENTES else s


def ler_csv(path: Path, marcadores_header: tuple[str, ...]) -> tuple[list[str], list[list[str]]]:
    """Lê um CSV do FNDE (latin-1, ';'), localiza a linha de cabeçalho pelos marcadores
    e retorna (cabecalho, linhas_de_dados)."""
    with open(path, encoding="latin-1", newline="") as f:
        linhas = [[c.strip() for c in r] for r in csv.reader(f, delimiter=";")]
    hi = None
    for i, r in enumerate(linhas):
        if any(c in marcadores_header for c in r):
            hi = i
            break
    if hi is None:
        raise ValueError(f"Cabeçalho não encontrado em {path.name} (marcadores {marcadores_header}).")
    cab = linhas[hi]
    dados = [r for r in linhas[hi + 1:] if any(c for c in r)]
    return cab, dados


def idx_colunas(cabecalho: list[str], nomes: dict[str, str]) -> dict[str, int]:
    """Mapeia rótulos amigáveis -> índice da coluna, casando por prefixo (robusto a \\n)."""
    def _norm(s: str) -> str:
        return " ".join(str(s).split()).lower()
    normcab = [_norm(c) for c in cabecalho]
    out = {}
    for chave, rotulo in nomes.items():
        alvo = _norm(rotulo)
        for j, c in enumerate(normcab):
            if c.startswith(alvo):
                out[chave] = j
                break
    return out


def iter_xlsx(path: Path, sheet: str | None = None) -> Iterator[tuple]:
    """Itera linhas de uma planilha (valores), de forma preguiçosa."""
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb.active
    for row in ws.iter_rows(values_only=True):
        yield row
    wb.close()


def achar_header_xlsx(linhas: list[tuple], marcadores: tuple[str, ...]) -> int:
    for i, r in enumerate(linhas):
        if any((str(c).strip() in marcadores) for c in r if c is not None):
            return i
    raise ValueError(f"Cabeçalho XLSX não encontrado (marcadores {marcadores}).")
