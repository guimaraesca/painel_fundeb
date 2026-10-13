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
        # Índice hash O(1) para acesso instantâneo de entes por código IBGE (elimina varreduras lineares)
        self._lookup: dict[str, dict[str, Any]] = {
            str(row["ibge"]): row for row in df.to_dict("records")
        }

    def get_ente(self, ibge: str) -> dict[str, Any] | None:
        return self._lookup.get(str(ibge))

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

        # Memória de Cálculo estruturada no Algoritmo de 6 Etapas
        hab_status = "Elegível (5 condicionalidades cumpridas)" if (ente.get("habilitado") or forcar_habilitacao) else "Inabilitado (Repasse Zerado)"
        memoria = [
            {
                "passo": "1. Filtro de Elegibilidade Primária (Simec / MEC)",
                "formula": r"\text{Status\_Condicionalidades} \in \{\text{True}, \text{False}\}",
                "descricao": f"Status da rede: {hab_status}. Avaliação na esfera {esfera} (Etapa de expansão de atendimento: {etapa}).",
            },
            {
                "passo": "2. Processamento do VAAR-Atendimento (Censo Escolar)",
                "formula": r"VAAR\_Atendimento_{r,t} = 1 - \frac{Abandono_{r,t} + 0{,}5 \times SIR_{r,t}}{M_{r,t}}",
                "descricao": f"IND Atendimento: {ind_atend_orig:.4f} → {ind_atend_sim:.4f} | Aplica penalização de SIR (fator 0,5) e margem de flutuação.",
            },
            {
                "passo": "3. Processamento do VAAR-Aprendizagem (Saeb / Inep)",
                "formula": r"VAAR\_Aprendizagem_{r,t} = Inad_{r,(t,t-1)} \times IPSaeb_{r,t} \times IndEqui_{r,t}",
                "descricao": f"IND Aprendizagem: {ind_aprend_orig:.4f} → {ind_aprend_sim:.4f} | Presença Saeb ≥ 80%, equidade socioeconômica (INE-S) e racial (INE-R).",
            },
            {
                "passo": "4. Reescalonamento de Pesos das Matrículas",
                "formula": r"peso^r = 1 + \left( \frac{IND - Min}{Max - Min} \right) \iff w = 2 - e^{-4 \cdot IND}",
                "descricao": f"Peso Atendimento: {peso_atend_orig:.4f} → {peso_atend_sim:.4f} | Peso Aprendizagem: {peso_aprend_orig:.4f} → {peso_aprend_sim:.4f} (Intervalo contínuo [1, 2]).",
            },
            {
                "passo": "5. Coeficientes e Quotas Legais (50% / 50%)",
                "formula": r"C^r = \frac{M_r \times peso^r}{\sum (M_i \times peso^i)} \quad \text{e} \quad Repasse = C^r \times (50\% \text{ VAAR})",
                "descricao": f"Cota Atendimento: R$ {vaar_atend_sim:,.2f} | Cota Aprendizagem: R$ {vaar_aprend_sim:,.2f}",
            },
            {
                "passo": "6. Agregação Final e Variação Líquida",
                "formula": r"\text{VAAR}_{\text{simulado}} = Repasse_{Atend} + Repasse_{Aprend} \quad \implies \quad \Delta = \text{VAAR}_{\text{sim}} - \text{VAAR}_{\text{orig}}",
                "descricao": f"Repasse total simulado: R$ {vaar_total_sim:,.2f} | Variação projetada: {'+' if delta_rs >= 0 else ''}R$ {delta_rs:,.2f} ({delta_pct:+.2f}%)",
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

    def simular_trilha_hipoteses(self, ibge: str) -> list[dict[str, Any]]:
        """Gera a trilha de 6 hipóteses incrementais para o ente, do atual até a melhor hipótese teórica."""
        ente = self.get_ente(ibge)
        if not ente:
            return []

        # 1. Atual FNDE (Baseline)
        r0 = self.simular_ente(ibge, 0.0, 0.0, forcar_habilitacao=False)
        v0 = r0.vaar_total_sim_rs if r0 else 0.0

        # 2. Habilitação Plena (regularização das 5 condicionalidades mantendo desempenho atual)
        r1 = self.simular_ente(ibge, 0.0, 0.0, forcar_habilitacao=True)
        v1 = r1.vaar_total_sim_rs if r1 else v0

        # 3. Conservadora (+5% Atendimento / +5% Aprendizagem)
        r2 = self.simular_ente(ibge, 5.0, 5.0, forcar_habilitacao=True)
        v2 = r2.vaar_total_sim_rs if r2 else v1

        # 4. Moderada (+15% Atendimento / +15% Aprendizagem)
        r3 = self.simular_ente(ibge, 15.0, 15.0, forcar_habilitacao=True)
        v3 = r3.vaar_total_sim_rs if r3 else v2

        # 5. Otimista (+30% Atendimento / +30% Aprendizagem)
        r4 = self.simular_ente(ibge, 30.0, 30.0, forcar_habilitacao=True)
        v4 = r4.vaar_total_sim_rs if r4 else v3

        # 6. Melhor Hipótese Teórica (Teto: Peso 2.0 nos dois eixos)
        peso_atend_orig = r1.peso_atend_orig if r1 else 1.0
        peso_aprend_orig = r1.peso_aprend_orig if r1 else 1.0
        vaar_atend_base = r1.vaar_atend_orig_rs if r1 else 0.0
        vaar_aprend_base = r1.vaar_aprend_orig_rs if r1 else 0.0
        v5 = (vaar_atend_base * (2.0 / max(1.0, peso_atend_orig))) + (vaar_aprend_base * (2.0 / max(1.0, peso_aprend_orig)))
        v5 = max(v5, v4 * 1.08)

        return [
            {"cenario": "1. Atual (FNDE)", "valor_rs": v0, "delta_rs": 0.0, "destaque": False},
            {"cenario": "2. Habilitação Plena (5 Condic.)", "valor_rs": v1, "delta_rs": v1 - v0, "destaque": False},
            {"cenario": "3. Hipótese Conservadora (+5%)", "valor_rs": v2, "delta_rs": v2 - v0, "destaque": False},
            {"cenario": "4. Hipótese Moderada (+15%)", "valor_rs": v3, "delta_rs": v3 - v0, "destaque": False},
            {"cenario": "5. Hipótese Otimista (+30%)", "valor_rs": v4, "delta_rs": v4 - v0, "destaque": False},
            {"cenario": "6. Melhor Hipótese (Teto Máximo)", "valor_rs": v5, "delta_rs": v5 - v0, "destaque": True},
        ]

    def comparativo_entes_potencial(
        self,
        esfera: str = "Estadual",
        uf: str | None = None,
    ) -> pd.DataFrame:
        """Gera dataset comparando o valor atual recebido com a melhor hipótese simulada para entes."""
        if esfera == "Estadual":
            df_subset = self._df[self._df["rede"] == "Estadual"].copy()
        else:
            df_subset = self._df[(self._df["rede"] == "Municipal") & (self._df["uf"] == (uf or "PI"))].copy()

        registros = []
        for _, row in df_subset.iterrows():
            ib = row["ibge"]
            v_atu = float(row.get("vaar") or 0.0)
            trilha = self.simular_trilha_hipoteses(ib)
            v_melhor = trilha[-1]["valor_rs"] if trilha else v_atu
            registros.append({
                "ibge": ib,
                "nome": row["nome"],
                "uf": row["uf"],
                "habilitado": row["habilitado"],
                "vaar_atual": v_atu,
                "vaar_melhor_hipotese": v_melhor,
                "delta_salto": v_melhor - v_atu,
            })
        return pd.DataFrame(registros)
