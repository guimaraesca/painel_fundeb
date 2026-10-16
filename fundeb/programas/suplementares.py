"""Programas suplementares financiados por matrícula: PNAE e PNATE.

Ambos os repasses da União são proporcionais à matrícula do **Censo Escolar
(Educacenso)** — por isso subcontagem de alunos reduz os recursos (exatamente o
caso do RN: ~4,48 mil alunos não cadastrados → perda de repasses em 2024–2026).

Este módulo encapsula os **valores per capita oficiais** (constantes citáveis) e
o cálculo do **impacto financeiro da subcontagem**. Nada aqui é estimado sem
fonte; onde há variação por município (PNATE), trabalha-se com faixa declarada.

Fontes:
- PNAE: Resolução CD/FNDE nº 1/2026 (per capita por aluno/dia; reajuste de
  14,35% sobre a Resolução nº 2/2023, que alterou a nº 6/2020).
- PNATE: Resolução CD/FNDE nº 14/2026 (reajuste de 14,35% sobre a nº 8/2023);
  per capita por aluno rural/ano varia por município (Fator de Necessidade de
  Recursos do Município — FNRM).
"""
from __future__ import annotations

from dataclasses import dataclass

# --------------------------------------------------------------- PNAE
#: Per capita PNAE por aluno/dia, por etapa/modalidade (R$) — Res. CD/FNDE nº 1/2026.
PNAE_PER_CAPITA_DIA: dict[str, float] = {
    "creche": 1.57,
    "pre": 0.82,
    "fundamental": 0.57,
    "medio": 0.57,
    "eja": 0.57,
    "indigena_quilombola": 0.98,
    "integral": 2.93,  # Ensino Médio em Tempo Integral (valor total complementado)
}

#: Rótulos legíveis das etapas.
PNAE_ETAPA_ROTULO: dict[str, str] = {
    "creche": "Creche",
    "pre": "Pré-escola",
    "fundamental": "Ensino Fundamental",
    "medio": "Ensino Médio",
    "eja": "EJA",
    "indigena_quilombola": "Escolas indígenas/quilombolas",
    "integral": "Ensino Médio em Tempo Integral",
}

#: Dias de atendimento usados no cálculo do PNAE para o ensino regular.
#: (FNDE: valor = per capita × dias de atendimento × matrícula.)
PNAE_DIAS_ATENDIMENTO: int = 200

# --------------------------------------------------------------- PNATE
#: Faixa do per capita PNATE por aluno rural transportado/ano (R$), após o
#: reajuste de 14,35% da Res. CD/FNDE nº 14/2026. Varia por município (FNRM).
PNATE_PER_CAPITA_ANO_MIN: float = 138.06
PNATE_PER_CAPITA_ANO_MAX: float = 196.95


# --------------------------------------------------------------- cálculos
def pnae_custo_aluno_ano(etapa: str) -> float:
    """Custo anual do PNAE por aluno de uma etapa (R$) = per capita/dia × dias."""
    return PNAE_PER_CAPITA_DIA[etapa] * PNAE_DIAS_ATENDIMENTO


def pnae_faixa_aluno_ano() -> tuple[float, float]:
    """Faixa do custo anual do PNAE por aluno (menor etapa regular → creche)."""
    regulares = [pnae_custo_aluno_ano(e) for e in ("fundamental", "medio", "eja", "pre", "creche")]
    return min(regulares), max(regulares)


def pnate_faixa_aluno_ano() -> tuple[float, float]:
    return PNATE_PER_CAPITA_ANO_MIN, PNATE_PER_CAPITA_ANO_MAX


@dataclass(frozen=True)
class ImpactoSubcontagem:
    alunos: int
    pnae_min: float
    pnae_max: float
    pnate_min: float
    pnate_max: float
    pct_rural: float

    @property
    def total_min(self) -> float:
        return self.pnae_min + self.pnate_min

    @property
    def total_max(self) -> float:
        return self.pnae_max + self.pnate_max


def impacto_subcontagem(
    alunos: int,
    etapa: str | None = None,
    pct_rural: float = 0.0,
) -> ImpactoSubcontagem:
    """Perda anual de PNAE e PNATE por ``alunos`` não cadastrados no Educacenso.

    - PNAE: se ``etapa`` for dada, valor exato dessa etapa; senão, faixa entre a
      menor etapa regular e a creche.
    - PNATE: aplica-se apenas à fração rural transportada (``pct_rural`` em %),
      com a faixa de per capita por município.
    """
    if etapa:
        c = pnae_custo_aluno_ano(etapa)
        pnae_min = pnae_max = alunos * c
    else:
        lo, hi = pnae_faixa_aluno_ano()
        pnae_min, pnae_max = alunos * lo, alunos * hi

    rurais = alunos * max(0.0, min(pct_rural, 100.0)) / 100.0
    pnate_min = rurais * PNATE_PER_CAPITA_ANO_MIN
    pnate_max = rurais * PNATE_PER_CAPITA_ANO_MAX

    return ImpactoSubcontagem(
        alunos=alunos, pnae_min=pnae_min, pnae_max=pnae_max,
        pnate_min=pnate_min, pnate_max=pnate_max, pct_rural=pct_rural,
    )
