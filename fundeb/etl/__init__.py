"""Pacote de ETL completo do painel FUNDEB (Extract → Transform → Load)."""
from fundeb.etl.consolidate import consolidar, tabela_fato, agregados

__all__ = ["consolidar", "tabela_fato", "agregados"]
