"""Serviço de análise de dados, métricas nacionais, estaduais e condicionalidades.

Calcula de forma pura sobre o DataFrame do DataRepository:
- Estatísticas agregadas nacionais e regionais
- Gargalos por condicionalidade (art. 14, § 1º)
- Ranking de Unidades da Federação com microindicadores
- Recomendações e plano de ação ("Como Agir")
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import numpy as np
import pandas as pd

from fundeb.domain.legal import CONDICIONALIDADES, CONDICIONALIDADE_POR_CODIGO
from fundeb.domain.territorio import REGIOES


@dataclass(frozen=True)
class GargaloCondicionalidade:
    codigo: str
    nome_curto: str
    artigo: str
    reprovacoes_nao_habilitadas: int
    total_reprovacoes: int
    pct_sobre_nao_habilitadas: float
    descricao_tecnica: str
    como_agir: str


@dataclass(frozen=True)
class ResumoNacional:
    total_entes: int
    total_municipios: int
    total_estados: int
    habilitados: int
    pct_habilitados: float
    nao_habilitados: int
    pct_nao_habilitados: float
    beneficiarios: int
    pct_beneficiarios: float
    total_vaar_reais: float
    total_vaaf_reais: float
    total_vaat_reais: float
    total_uniao_reais: float
    transicao_manteve: int
    transicao_perdeu: int
    transicao_entrou: int
    transicao_fora: int


class AnalyticsService:
    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

    @property
    def df(self) -> pd.DataFrame:
        return self._df

    def resumo_nacional(self) -> ResumoNacional:
        total = len(self._df)
        mun = int((self._df["rede"] == "Municipal").sum())
        est = int((self._df["rede"] == "Estadual").sum())
        hab = int(self._df["habilitado"].sum())
        benef = int(self._df["beneficiario"].sum())
        nao_hab = total - hab

        tr = self._df["transicao"].value_counts().to_dict()

        return ResumoNacional(
            total_entes=total,
            total_municipios=mun,
            total_estados=est,
            habilitados=hab,
            pct_habilitados=(hab / total * 100) if total else 0.0,
            nao_habilitados=nao_hab,
            pct_nao_habilitados=(nao_hab / total * 100) if total else 0.0,
            beneficiarios=benef,
            pct_beneficiarios=(benef / total * 100) if total else 0.0,
            total_vaar_reais=float(self._df["vaar"].sum()),
            total_vaaf_reais=float(self._df["vaaf"].sum()),
            total_vaat_reais=float(self._df["vaat"].sum()),
            total_uniao_reais=float(self._df["uniao_total"].sum()),
            transicao_manteve=int(tr.get("Manteve", 0)),
            transicao_perdeu=int(tr.get("Perdeu", 0)),
            transicao_entrou=int(tr.get("Entrou", 0)),
            transicao_fora=int(tr.get("Fora", 0)),
        )

    def gargalos_condicionalidade(self) -> list[GargaloCondicionalidade]:
        """Calcula o funil de reprovação exato sobre as redes NÃO HABILITADAS ao VAAR 2026."""
        nao_hab = self._df[~self._df["habilitado"]]
        total_nh = len(nao_hab)
        gargalos = []

        mapping = {
            "c1": ("Cond. I", "Inciso I — Gestão Democrática", "c1"),
            "c2": ("Cond. II", "Inciso II — Participação SAEB >= 80%", "c2"),
            "c3": ("Cond. III", "Inciso III — Redução Desigualdades / ICMS", "c3"),
            "c4": ("Cond. IV", "Inciso IV — Referenciais Curriculares BNCC", "c4"),
            "c5": ("Cond. V", "Inciso V — SIOPE / Informações Fiscais", "c5"),
        }

        como_agir_map = {
            "c1": "Adequar legislação local sobre provimento de cargo de diretor escolar por critérios de mérito e desempenho, ou eleição qualificada.",
            "c2": "Intensificar mobilização escolar, busca ativa nos dias de aplicação e assegurar quorum mínimo de 80% de alunos presentes no SAEB.",
            "c3": "Para redes municipais: articulação com governo estadual para aprovação e vigência de lei de ICMS Educação redistributivo.",
            "c4": "Homologar documentos curriculares alinhados à BNCC e comprovar implementação junto aos sistemas do MEC/INEP.",
            "c5": "Transmitir balanços e dados contábeis no SIOPE com antecedência para evitar inconsistências e encerramento fora do prazo legal.",
        }

        for col, (num, titulo, key) in mapping.items():
            reprov_nh = int((~nao_hab[col]).sum())
            reprov_tot = int((~self._df[col]).sum())
            pct = (reprov_nh / total_nh * 100) if total_nh > 0 else 0.0

            gargalos.append(
                GargaloCondicionalidade(
                    codigo=num,
                    nome_curto=titulo,
                    artigo=f"Art. 14, § 1º, {num.split('.')[1].strip()}",
                    reprovacoes_nao_habilitadas=reprov_nh,
                    total_reprovacoes=reprov_tot,
                    pct_sobre_nao_habilitadas=pct,
                    descricao_tecnica=CONDICIONALIDADE_POR_CODIGO[col].texto_legal,
                    como_agir=como_agir_map[col],
                )
            )

        # Ordenar por maior número de reprovações nas não habilitadas (ex: Cond. 3 primeiro, Cond. 1, etc.)
        gargalos.sort(key=lambda g: g.reprovacoes_nao_habilitadas, reverse=True)
        return gargalos

    def ranking_por_uf(self) -> pd.DataFrame:
        """Gera a tabela estruturada de UFs com indicadores e valores agregados."""
        linhas = []
        for uf, grp in self._df.groupby("uf"):
            tot = len(grp)
            hab = int(grp["habilitado"].sum())
            benef = int(grp["beneficiario"].sum())
            v_vaar = float(grp["vaar"].sum())
            v_25 = float(grp["vaar_2025"].sum())
            v_total = float(grp["uniao_total"].sum())
            reg = grp["regiao"].iloc[0] if not grp.empty else "Outra"

            linhas.append({
                "uf": uf,
                "regiao": reg,
                "total_redes": tot,
                "habilitadas": hab,
                "pct_habilitadas": (hab / tot * 100) if tot else 0.0,
                "beneficiarias": benef,
                "pct_beneficiarias": (benef / tot * 100) if tot else 0.0,
                "vaar_2026": v_vaar,
                "vaar_2025": v_25,
                "delta_vaar": v_vaar - v_25,
                "uniao_total": v_total,
                "reprov_c1": int((~grp["c1"]).sum()),
                "reprov_c2": int((~grp["c2"]).sum()),
                "reprov_c3": int((~grp["c3"]).sum()),
                "reprov_c4": int((~grp["c4"]).sum()),
                "reprov_c5": int((~grp["c5"]).sum()),
            })

        res = pd.DataFrame(linhas)
        return res.sort_values(by="vaar_2026", ascending=False).reset_index(drop=True)

    def resumo_por_regiao(self) -> pd.DataFrame:
        """Gera agregados por Grande Região brasileira."""
        linhas = []
        for regiao, grp in self._df.groupby("regiao"):
            tot = len(grp)
            hab = int(grp["habilitado"].sum())
            benef = int(grp["beneficiario"].sum())
            linhas.append({
                "regiao": regiao,
                "total_redes": tot,
                "habilitadas": hab,
                "pct_habilitadas": (hab / tot * 100) if tot else 0.0,
                "beneficiarias": benef,
                "pct_beneficiarias": (benef / tot * 100) if tot else 0.0,
                "total_vaar": float(grp["vaar"].sum()),
                "total_uniao": float(grp["uniao_total"].sum()),
            })
        return pd.DataFrame(linhas).sort_values(by="total_vaar", ascending=False).reset_index(drop=True)

    def plano_de_acao_ente(self, ibge: str) -> dict[str, Any]:
        """Elabora diagnóstico e plano de ação individual para uma rede específica."""
        match = self._df[self._df["ibge"] == ibge]
        if match.empty:
            return {}
        ente = match.iloc[0].to_dict()

        acoes = []
        for c, rotulo in [("c1", "Cond. I (Gestão Democrática)"),
                          ("c2", "Cond. II (Participação no SAEB)"),
                          ("c3", "Cond. III (ICMS / Redução de Desigualdades)"),
                          ("c4", "Cond. IV (BNCC / Currículo)"),
                          ("c5", "Cond. V (SIOPE / Prazos Fiscais)")]:
            cumpriu = bool(ente.get(c, False))
            acoes.append({
                "condicionalidade": rotulo,
                "status": "Cumprida" if cumpriu else "Reprovada / Pendente",
                "impacto": "Garante elegibilidade ao VAAR" if not cumpriu else "Regular",
                "gravidade": "Crítica" if not cumpriu else "OK",
            })

        return {
            "ibge": ibge,
            "nome": ente["nome"],
            "uf": ente["uf"],
            "rede": ente["rede"],
            "habilitado": ente["habilitado"],
            "beneficiario": ente["beneficiario"],
            "transicao": ente["transicao"],
            "reprovacoes": ente["n_reprovacoes"],
            "acoes": acoes,
            "ind_atend": ente["ind_atend"],
            "ind_aprend": ente["ind_aprend"],
            "evoluiu_atend": ente["evoluiu_atend"],
            "evoluiu_aprend": ente["evoluiu_aprend"],
            "vaar_2026": ente["vaar"],
            "vaar_2025": ente["vaar_2025"],
        }
