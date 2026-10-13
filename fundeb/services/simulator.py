"""Motor de simulação de cenários do VAAR (Complementação Valor Aluno Ano Resultado).

Diferencia estritamente:
- **Rede Estadual**: Etapa IEE avaliada no Ensino Médio, SAEB (EF/EM) e rendimento EM.
- **Rede Municipal**: Etapa IEE avaliada na Educação Infantil (Creche/Pré-escola), SAEB (EF) e rendimento EF.

Alinhado à metodologia da Nota Técnica Inep nº 23/2022 e Simulador-VAAR-PI.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import math
import numpy as np
import pandas as pd

from fundeb.domain.formulas import (
    CENARIOS_IEE,
    K_PESO,
    iee_cenarios,
    peso_indicador,
    ind_atendimento,
    ind_aprendizagem,
    razao,
)


@dataclass(frozen=True)
class ResultadoSimulacao:
    ibge: str
    nome: str
    uf: str
    esfera: str
    etapa_atendimento: str
    # Valores Originais (FNDE/Inep)
    ind_atend_orig: float
    ind_aprend_orig: float
    peso_atend_orig: float
    peso_aprend_orig: float
    vaar_atend_orig_rs: float
    vaar_aprend_orig_rs: float
    vaar_total_orig_rs: float
    # Valores Simulados
    ind_atend_sim: float
    ind_aprend_sim: float
    peso_atend_sim: float
    peso_aprend_sim: float
    vaar_atend_sim_rs: float
    vaar_aprend_sim_rs: float
    vaar_total_sim_rs: float
    # Deltas
    delta_rs: float
    delta_pct: float
    # Cenários do IEE
    cenarios_iee: list[dict]
    # Memória de cálculo descritiva
    memoria_calculo: list[dict[str, str]]


class SimulatorService:
    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

    def get_ente(self, ibge: str) -> dict[str, Any] | None:
        row = self._df[self._df["ibge"] == ibge]
        if row.empty:
            return None
        return row.iloc[0].to_dict()

    def simular_ente(
        self,
        ibge: str,
        delta_atendimento_pct: float = 0.0,
        delta_aprendizagem_pct: float = 0.0,
        forcar_habilitacao: bool = False,
        cenario_iee_escolhido: str | None = None,
    ) -> ResultadoSimulacao | None:
        """Simula o impacto financeiro de variações no atendimento ou aprendizagem para um ente."""
        ente = self.get_ente(ibge)
        if not ente:
            return None

        esfera = "Estadual" if ente["rede"] == "Estadual" else "Municipal"
        etapa = "Ensino Médio" if esfera == "Estadual" else "Educação Infantil (Creche e Pré-Escola)"

        # Extrair matrículas IEE históricas
        mats_iee = {ano: float(ente.get(f"mat_iee_{ano}", np.nan)) for ano in range(2017, 2024)}
        cenarios = iee_cenarios(mats_iee)

        # Indicadores base
        ind_atend_orig = float(ente.get("ind_atend") or 0.0)
        ind_aprend_orig = float(ente.get("ind_aprend") or 0.0)

        # Peso original da matrícula: w = 2 - exp(-4 * IND)
        peso_atend_orig = peso_indicador(ind_atend_orig) if ind_atend_orig > 0 else 1.0
        peso_aprend_orig = peso_indicador(ind_aprend_orig) if ind_aprend_orig > 0 else 1.0

        vaar_atend_orig = float(ente.get("vaar_atend") or 0.0)
        vaar_aprend_orig = float(ente.get("vaar_aprend") or 0.0)
        vaar_total_orig = float(ente.get("vaar") or 0.0)

        # Se forçar habilitação em ente não habilitado, estimar cota base proporcional
        if vaar_total_orig == 0.0 and (forcar_habilitacao or ente.get("habilitado")):
            # Estimativa de repasse caso seja habilitado: média por matrícula ou receita
            mat_eb = float(ente.get("mat_eb_2023") or 1000.0)
            vaar_atend_orig = mat_eb * 150.0  # valor de referência aproximado
            vaar_aprend_orig = mat_eb * 150.0
            vaar_total_orig = vaar_atend_orig + vaar_aprend_orig

        # Ajuste de atendimento por cenário IEE ou slider customizado
        if cenario_iee_escolhido:
            cen = next((c for c in cenarios if c["cenario"] == cenario_iee_escolhido), None)
            if cen and cen.get("iee"):
                ind_atend_sim = ind_atend_orig * (cen["iee"] / (ente.get("iee_ciclo2024") or 1.0))
            else:
                ind_atend_sim = ind_atend_orig * (1.0 + delta_atendimento_pct / 100.0)
        else:
            ind_atend_sim = max(0.0, ind_atend_orig * (1.0 + delta_atendimento_pct / 100.0))

        ind_aprend_sim = max(0.0, ind_aprend_orig * (1.0 + delta_aprendizagem_pct / 100.0))

        peso_atend_sim = peso_indicador(ind_atend_sim) if ind_atend_sim > 0 else 1.0
        peso_aprend_sim = peso_indicador(ind_aprend_sim) if ind_aprend_sim > 0 else 1.0

        # O repasse financeiro do VAAR varia proporcionalmente ao peso do indicador
        # Ponderação do repasse = vaar_base * (peso_sim / peso_orig)
        razao_peso_atend = (peso_atend_sim / peso_atend_orig) if peso_atend_orig > 0 else 1.0
        razao_peso_aprend = (peso_aprend_sim / peso_aprend_orig) if peso_aprend_orig > 0 else 1.0

        vaar_atend_sim = vaar_atend_orig * razao_peso_atend
        vaar_aprend_sim = vaar_aprend_orig * razao_peso_aprend
        vaar_total_sim = vaar_atend_sim + vaar_aprend_sim

        delta_rs = vaar_total_sim - vaar_total_orig
        delta_pct = (delta_rs / vaar_total_orig * 100.0) if vaar_total_orig > 0 else 0.0

        # Memória de Cálculo passo a passo
        memoria = [
            {
                "passo": "1. Esfera e Etapa Avaliada",
                "formula": "Metodologia diferenciada por esfera (Lei 14.113/2020 e NT Inep 23/2022)",
                "descricao": f"Rede {esfera}: etapa de expansão avaliada = {etapa}.",
            },
            {
                "passo": "2. Peso do Indicador de Atendimento (w_atend)",
                "formula": r"w = 2 - e^{-4 \cdot \text{IND\_Atend}}",
                "descricao": f"IND Atendimento: {ind_atend_orig:.4f} → {ind_atend_sim:.4f} | Peso: {peso_atend_orig:.4f} → {peso_atend_sim:.4f}",
            },
            {
                "passo": "3. Peso do Indicador de Aprendizagem (w_aprend)",
                "formula": r"w = 2 - e^{-4 \cdot \text{IND\_Aprend}}",
                "descricao": f"IND Aprendizagem: {ind_aprend_orig:.4f} → {ind_aprend_sim:.4f} | Peso: {peso_aprend_orig:.4f} → {peso_aprend_sim:.4f}",
            },
            {
                "passo": "4. Divisão Legal dos Recursos (50% / 50%)",
                "formula": r"\text{VAAR} = \text{VAAR}_{\text{atend}} + \text{VAAR}_{\text{aprend}}",
                "descricao": f"Cota Atendimento: R$ {vaar_atend_sim:,.2f} | Cota Aprendizagem: R$ {vaar_aprend_sim:,.2f}",
            },
            {
                "passo": "5. Impacto Financeiro Total",
                "formula": r"\Delta = \text{VAAR}_{\text{simulado}} - \text{VAAR}_{\text{atual}}",
                "descricao": f"Variação projetada: {'+' if delta_rs >= 0 else ''}R$ {delta_rs:,.2f} ({delta_pct:+.2f}%)",
            },
        ]

        return ResultadoSimulacao(
            ibge=ibge,
            nome=ente["nome"],
            uf=ente["uf"],
            esfera=esfera,
            etapa_atendimento=etapa,
            ind_atend_orig=ind_atend_orig,
            ind_aprend_orig=ind_aprend_orig,
            peso_atend_orig=peso_atend_orig,
            peso_aprend_orig=peso_aprend_orig,
            vaar_atend_orig_rs=vaar_atend_orig,
            vaar_aprend_orig_rs=vaar_aprend_orig,
            vaar_total_orig_rs=vaar_total_orig,
            ind_atend_sim=ind_atend_sim,
            ind_aprend_sim=ind_aprend_sim,
            peso_atend_sim=peso_atend_sim,
            peso_aprend_sim=peso_aprend_sim,
            vaar_atend_sim_rs=vaar_atend_sim,
            vaar_aprend_sim_rs=vaar_aprend_sim,
            vaar_total_sim_rs=vaar_total_sim,
            delta_rs=delta_rs,
            delta_pct=delta_pct,
            cenarios_iee=cenarios,
            memoria_calculo=memoria,
        )
