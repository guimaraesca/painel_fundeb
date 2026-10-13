"""Caminhos e constantes de infraestrutura (sem regra de negócio)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"
GEO_DIR = DATA_DIR / "geo"

#: Rede usada como seleção inicial (Rede estadual do Piauí — contexto do Simulador-VAAR-PI).
ENTE_PADRAO = "22"
