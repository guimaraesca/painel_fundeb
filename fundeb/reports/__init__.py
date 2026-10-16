"""Geração de relatórios PDF (geral e específico) do painel FUNDEB."""
from fundeb.reports.geral import relatorio_geral
from fundeb.reports.especifico import relatorio_especifico

__all__ = ["relatorio_geral", "relatorio_especifico"]
