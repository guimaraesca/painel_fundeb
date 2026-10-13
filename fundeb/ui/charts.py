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
        xaxis=dict(range=[0, 100], ticksuffix="%"),
    )
    return apply_few_theme(fig, show_x_grid=True, show_y_grid=False)


def chart_lollipop_hipoteses(
    hipoteses: list[dict[str, Any]],
    titulo: str,
) -> go.Figure:
    """Gráfico Lollipop (Pirulito) para a trilha de hipóteses de uma rede (do atual até a melhor teórica).
    
    Cada hipótese possui uma haste horizontal e uma esfera destacada com o valor financeiro em R$ e o salto (Δ).
    """
    fig = go.Figure()
    n = len(hipoteses)

    # 1. Hastes do pirulito
    for h in hipoteses:
        cor_haste = "#10B981" if h.get("destaque") else "#94A3B8"
        largura = 3.5 if h.get("destaque") else 2.0
        fig.add_trace(
            go.Scatter(
                x=[0, h["valor_rs"]],
                y=[h["cenario"], h["cenario"]],
                mode="lines",
                line=dict(color=cor_haste, width=largura),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # 2. Cabeças do pirulito (marcadores circulares e rótulos de texto)
    cores_pts = [
        "#10B981" if h.get("destaque")
        else "#1E40AF" if h.get("delta_rs", 0) > 0
        else "#64748B"
        for h in hipoteses
    ]
    tamanhos = [16 if h.get("destaque") else 12 for h in hipoteses]
    
    # Rótulo amigável: se for milhão mostra R$ X,X Mi, se menor mostra R$ X mil
    def _rotulo_rs(v: float) -> str:
        if v >= 1e6:
            return f"R$ {v / 1e6:.2f} Mi"
        elif v >= 1e3:
            return f"R$ {v / 1e3:.0f} mil"
        elif v == 0:
            return "R$ 0,00"
        return f"R$ {v:,.2f}"

    rotulos = [_rotulo_rs(h["valor_rs"]) for h in hipoteses]
    hover_texts = [
        f"<b>{h['cenario']}</b><br>Valor Projetado: R$ {h['valor_rs']:,.2f}<br>Salto vs Atual: {'+' if h['delta_rs'] >= 0 else ''}R$ {h['delta_rs']:,.2f}"
        for h in hipoteses
    ]

    fig.add_trace(
        go.Scatter(
            x=[h["valor_rs"] for h in hipoteses],
            y=[h["cenario"] for h in hipoteses],
            mode="markers+text",
            marker=dict(
                size=tamanhos,
                color=cores_pts,
                line=dict(color="#0F172A", width=1.5),
            ),
            text=rotulos,
            textposition="middle right",
            hovertext=hover_texts,
            hoverinfo="text",
            showlegend=False,
        )
    )

    max_val = max([h["valor_rs"] for h in hipoteses] + [1.0])
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=13, color="#0F172A")),
        height=max(280, n * 50),
        xaxis=dict(range=[0, max_val * 1.3], tickprefix="R$ "),
    )
    return apply_few_theme(fig, show_x_grid=True, show_y_grid=False)


def chart_dumbbell_comparativo(
    df: pd.DataFrame,
    categoria_col: str,
    val_atual_col: str,
    val_potencial_col: str,
    titulo: str,
    max_linhas: int = 25,
) -> go.Figure:
    """Gráfico Dumbbell / Lollipop Comparativo entre Entes (Estados ou Municípios).
    
    Compara para cada ente o 'VAAR Recebido Atual' (ponto cinza) com a 'Melhor Hipótese' (ponto verde esmeralda).
    """
    df_sorted = df.sort_values(by=val_potencial_col, ascending=True).tail(max_linhas).copy()
    n = len(df_sorted)

    fig = go.Figure()

    # 1. Hastes de conexão
    for _, row in df_sorted.iterrows():
        cat = row[categoria_col]
        v_atu = row[val_atual_col]
        v_pot = row[val_potencial_col]
        fig.add_trace(
            go.Scatter(
                x=[v_atu, v_pot],
                y=[cat, cat],
                mode="lines",
                line=dict(color="#CBD5E1", width=2.5),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # 2. Ponto Baseline: VAAR Atual Recebido
    fig.add_trace(
        go.Scatter(
            x=df_sorted[val_atual_col],
            y=df_sorted[categoria_col],
            mode="markers",
            name="VAAR Atual Recebido",
            marker=dict(size=9, color="#64748B", line=dict(color="#334155", width=1)),
            hoverinfo="text",
            hovertext=[f"<b>{cat}</b><br>VAAR Atual: R$ {v:,.2f}" for cat, v in zip(df_sorted[categoria_col], df_sorted[val_atual_col])],
        )
    )

    # 3. Ponto Potencial: Melhor Hipótese
    def _delta_label(atu: float, pot: float) -> str:
        d = pot - atu
        if d >= 1e6:
            return f"+R$ {d / 1e6:.2f} Mi"
        elif d >= 1e3:
            return f"+R$ {d / 1e3:.0f} mil"
        elif d > 0:
            return f"+R$ {d:,.0f}"
        return "Sem alteração"

    textos_pot = [_delta_label(atu, pot) for atu, pot in zip(df_sorted[val_atual_col], df_sorted[val_potencial_col])]

    fig.add_trace(
        go.Scatter(
            x=df_sorted[val_potencial_col],
            y=df_sorted[categoria_col],
            mode="markers+text",
            name="Melhor Hipótese (Potencial)",
            marker=dict(size=12, color="#10B981", line=dict(color="#065F46", width=1.5)),
            text=textos_pot,
            textposition="middle right",
            hoverinfo="text",
            hovertext=[
                f"<b>{cat}</b><br>Potencial Máximo: R$ {pot:,.2f}<br>Salto: +R$ {pot - atu:,.2f}"
                for cat, atu, pot in zip(df_sorted[categoria_col], df_sorted[val_atual_col], df_sorted[val_potencial_col])
            ],
        )
    )

    max_x = df_sorted[val_potencial_col].max() if n > 0 else 1.0
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=13, color="#0F172A")),
        height=max(320, n * 30),
        xaxis=dict(range=[0, max_x * 1.3], tickprefix="R$ "),
    )
    return apply_few_theme(fig, show_x_grid=True, show_y_grid=False)

