"""Módulo de visualização baseado nos princípios de Stephen Few ('Show Me the Numbers').

Diretrizes implementadas:
1. Maximização do Data-Ink Ratio (Tufte & Few): eliminação de chart junk e grades pesadas.
2. Eixo de barras SEMPRE iniciando em zero (eliminação do Lie Factor).
3. Uso de barras horizontais para categorias com rótulos extensos.
4. Cores suaves e neutras (slate/earth tones) na base; cor de destaque estritamente para ênfase.
5. Gráficos de Desvio (Deviation) com linha de referência zero evidente.
6. Small Multiples para comparação multi-variável em um único relance visual.
"""
from __future__ import annotations

from typing import Any
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Paleta Muted / Natural (Stephen Few - Slide 127)
COLOR_NEUTRAL = "#64748B"       # Slate base para dados normais
COLOR_NEUTRAL_LIGHT = "#94A3B8" # Slate claro para dados secundários
COLOR_EMPHASIS = "#1E40AF"      # Azul nobre para foco/destaque
COLOR_ALERT = "#DC2626"         # Carmesim para alerta/perda crítica
COLOR_POSITIVE = "#16A34A"      # Verde floresta para ganhos/conformidade
COLOR_GRID = "#F1F5F9"          # Grade sutil quase imperceptível
COLOR_AXIS = "#94A3B8"          # Eixos limpos


def apply_few_theme(fig: go.Figure, show_x_grid: bool = True, show_y_grid: bool = False) -> go.Figure:
    """Aplica o padrão Stephen Few de alta proporção tinta-dado (Data-Ink Ratio)."""
    fig.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(
            family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
            size=12,
            color="#1E293B",
        ),
        margin=dict(l=10, r=20, t=30, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title_text="",
            font=dict(size=11),
        ),
    )
    fig.update_xaxes(
        showgrid=show_x_grid,
        gridcolor=COLOR_GRID,
        gridwidth=1,
        linecolor=COLOR_AXIS,
        linewidth=1,
        zeroline=True,
        zerolinecolor=COLOR_AXIS,
        zerolinewidth=1.5,
    )
    fig.update_yaxes(
        showgrid=show_y_grid,
        gridcolor=COLOR_GRID,
        gridwidth=1,
        linecolor=COLOR_AXIS,
        linewidth=1,
        zeroline=True,
        zerolinecolor=COLOR_AXIS,
        zerolinewidth=1.5,
    )
    return fig


def chart_ranking_horizontal(
    df: pd.DataFrame,
    categoria_col: str,
    valor_col: str,
    titulo: str,
    destacar_primeiro: bool = True,
    formato_rotulo: str = "%{x:,.0f}",
    cor_destaque: str = COLOR_EMPHASIS,
) -> go.Figure:
    """Gráfico de Ranking ordenado com barras horizontais (Stephen Few - Slide 101 e 116).
    
    Barras sempre começam em zero e rótulos longos alinham perfeitamente no eixo vertical.
    """
    df_sorted = df.sort_values(by=valor_col, ascending=True).copy()
    n = len(df_sorted)

    # Cores: base neutra com destaque pontual (Slide 126-127)
    cores = [COLOR_NEUTRAL] * n
    if destacar_primeiro and n > 0:
        cores[-1] = cor_destaque  # O maior valor (último no sort ascendente)

    fig = go.Figure(
        go.Bar(
            x=df_sorted[valor_col],
            y=df_sorted[categoria_col],
            orientation="h",
            marker=dict(color=cores),
            text=df_sorted[valor_col],
            texttemplate=formato_rotulo,
            textposition="outside",
            cliponaxis=False,
        )
    )
    fig.update_layout(title=dict(text=titulo, font=dict(size=13, color="#0F172A")), height=max(260, n * 38))
    fig.update_xaxes(rangemode="tozero")  # Regra de ouro de Few: base zero para barras
    return apply_few_theme(fig, show_x_grid=True, show_y_grid=False)


def chart_deviation(
    df: pd.DataFrame,
    categoria_col: str,
    delta_col: str,
    titulo: str,
    formato_rotulo: str = "%{x:+,.2s}",
) -> go.Figure:
    """Gráfico de Desvio com linha de referência em zero (Stephen Few - Slide 105-106).
    
    Barras estendem-se à direita (positivo/verde) ou à esquerda (negativo/vermelho).
    """
    df_sorted = df.sort_values(by=delta_col, ascending=True).copy()
    cores = [COLOR_POSITIVE if v >= 0 else COLOR_ALERT for v in df_sorted[delta_col]]

    fig = go.Figure(
        go.Bar(
            x=df_sorted[delta_col],
            y=df_sorted[categoria_col],
            orientation="h",
            marker=dict(color=cores),
            text=df_sorted[delta_col],
            texttemplate=formato_rotulo,
            textposition="outside",
            cliponaxis=False,
        )
    )
    fig.update_layout(title=dict(text=titulo, font=dict(size=13, color="#0F172A")), height=max(280, len(df_sorted) * 32))
    # Linha zero bem demarcada
    fig.update_xaxes(zeroline=True, zerolinecolor="#475569", zerolinewidth=2)
    return apply_few_theme(fig, show_x_grid=True, show_y_grid=False)


def chart_time_series(
    df: pd.DataFrame,
    x_col: str,
    series: list[tuple[str, str, str]],  # (coluna, nome_legenda, cor)
    titulo: str,
    y_title: str = "",
) -> go.Figure:
    """Gráfico de Séries Temporais (Stephen Few - Slide 88 e 99).
    
    Linhas com marcadores discretos para enfatizar taxa de variação contínua no tempo.
    """
    fig = go.Figure()
    for col, nome, cor in series:
        fig.add_trace(
            go.Scatter(
                x=df[x_col],
                y=df[col],
                mode="lines+markers",
                name=nome,
                line=dict(color=cor, width=2.5),
                marker=dict(size=6, color=cor),
            )
        )
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=13, color="#0F172A")),
        yaxis_title=y_title,
        height=320,
    )
    return apply_few_theme(fig, show_x_grid=False, show_y_grid=True)


def chart_part_to_whole_100(
    rotulo: str,
    parte_a_nome: str,
    parte_a_val: float,
    parte_b_nome: str,
    parte_b_val: float,
    titulo: str,
) -> go.Figure:
    """Gráfico Parte-pelo-Todo (Stephen Few - Slide 103: 'Save the pies for dessert!').
    
    Barra empilhada 100% que permite julgamento visual preciso sem distorção angular.
    """
    total = parte_a_val + parte_b_val
    pct_a = (parte_a_val / total * 100.0) if total else 50.0
    pct_b = (parte_b_val / total * 100.0) if total else 50.0

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name=f"{parte_a_nome} ({pct_a:.1f}%)",
            y=[rotulo],
            x=[pct_a],
            orientation="h",
            marker=dict(color="#2563EB"),
            text=f"{pct_a:.1f}%",
            textposition="inside",
        )
    )
    fig.add_trace(
        go.Bar(
            name=f"{parte_b_nome} ({pct_b:.1f}%)",
            y=[rotulo],
            x=[pct_b],
            orientation="h",
            marker=dict(color="#0D9488"),
            text=f"{pct_b:.1f}%",
            textposition="inside",
        )
    )
    fig.update_layout(
        barmode="stack",
        title=dict(text=titulo, font=dict(size=13, color="#0F172A")),
        height=140,
        xaxis=dict(range=[0, 100], suffix="%"),
    )
    return apply_few_theme(fig, show_x_grid=True, show_y_grid=False)
