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

from fundeb.ui.components import (
    format_currency,
    format_currency_full,
    format_percent,
    format_int,
    format_decimal,
)

# Paleta Muted / Natural (Stephen Few - Slide 127)
COLOR_NEUTRAL = "#64748B"       # Slate base para dados normais
COLOR_NEUTRAL_LIGHT = "#94A3B8" # Slate claro para dados secundários
COLOR_EMPHASIS = "#1E40AF"      # Azul nobre para foco/destaque
COLOR_ALERT = "#DC2626"         # Carmesim para alerta/perda crítica
COLOR_POSITIVE = "#16A34A"      # Verde floresta para ganhos/conformidade
COLOR_GRID = "#F1F5F9"          # Grade sutil quase imperceptível
COLOR_AXIS = "#94A3B8"          # Eixos limpos


# Paleta Regional para Gráficos e Rankings
CORES_REGIAO = {
    "Norte": "#0284C7",        # Azul Céu
    "Nordeste": "#D97706",     # Âmbar
    "Centro-Oeste": "#16A34A", # Verde Esmeralda
    "Sudeste": "#2563EB",      # Azul Cobalto
    "Sul": "#7C3AED",          # Violeta
}


def apply_few_theme(fig: go.Figure, show_x_grid: bool = True, show_y_grid: bool = False) -> go.Figure:
    """Aplica o padrão Stephen Few de alta proporção tinta-dado (Data-Ink Ratio), padrão ABNT e sem sobreposição."""
    # Detecta se há título definido para ajustar margem superior proporcional
    has_title = bool(fig.layout.title and fig.layout.title.text)
    top_margin = 58 if has_title else 26
    bottom_margin = 35

    fig.update_layout(
        separators=",.",  # ABNT: vírgula decimal (,), ponto de milhar (.)
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(
            family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
            size=12,
            color="#1E293B",
        ),
        margin=dict(l=25, r=35, t=top_margin, b=bottom_margin),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            title_text="",
            font=dict(size=11, color="#334155"),
            bgcolor="rgba(255, 255, 255, 0)",
        ),
    )
    if has_title:
        fig.update_layout(
            title=dict(
                y=0.98,
                x=0.01,
                xanchor="left",
                yanchor="top",
                font=dict(size=13, color="#0F172A"),
            )
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
        automargin=True,
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
        automargin=True,
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
    cor_col: str | None = None,
    escala_cores: dict[str, str] | None = None,
) -> go.Figure:
    """Gráfico de Ranking ordenado com barras horizontais (Stephen Few - Slide 101 e 116).
    
    Barras sempre começam em zero e rótulos longos alinham perfeitamente no eixo vertical.
    """
    df_sorted = df.sort_values(by=valor_col, ascending=True).copy()
    n = len(df_sorted)

    if cor_col and cor_col in df_sorted.columns:
        mapa_cor = escala_cores or CORES_REGIAO
        cores = [mapa_cor.get(v, COLOR_NEUTRAL) for v in df_sorted[cor_col]]
    else:
        # Cores: base neutra com destaque pontual (Slide 126-127)
        cores = [COLOR_NEUTRAL] * n
        if destacar_primeiro and n > 0:
            cores[-1] = cor_destaque  # O maior valor (último no sort ascendente)

    max_v = float(df_sorted[valor_col].max()) if not df_sorted.empty else 0.0

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
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=13, color="#0F172A")),
        height=max(280, n * 44),
        margin=dict(r=55),
    )
    if max_v > 0:
        fig.update_xaxes(range=[0, max_v * 1.25], rangemode="tozero")
    else:
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
            name=f"{parte_a_nome} ({format_percent(pct_a)})",
            y=[rotulo],
            x=[pct_a],
            orientation="h",
            marker=dict(color="#2563EB"),
            text=format_percent(pct_a),
            textposition="inside",
        )
    )
    fig.add_trace(
        go.Bar(
            name=f"{parte_b_nome} ({format_percent(pct_b)})",
            y=[rotulo],
            x=[pct_b],
            orientation="h",
            marker=dict(color="#0D9488"),
            text=format_percent(pct_b),
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
    
    # Rótulo amigável no padrão ABNT
    def _rotulo_rs(v: float) -> str:
        if v >= 1e9:
            s = f"{v / 1e9:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"R$ {s} bi"
        elif v >= 1e6:
            s = f"{v / 1e6:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"R$ {s} mi"
        elif v >= 1e3:
            s = f"{v / 1e3:,.0f}".replace(",", ".")
            return f"R$ {s} mil"
        elif v == 0:
            return "R$ 0,00"
        return format_currency_full(v)

    rotulos = [_rotulo_rs(h["valor_rs"]) for h in hipoteses]
    hover_texts = [
        f"<b>{h['cenario']}</b><br>Valor Projetado: {format_currency_full(h['valor_rs'])}<br>Salto vs Atual: {'+' if h['delta_rs'] >= 0 else ''}{format_currency_full(h['delta_rs'])}"
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
            hovertext=[f"<b>{cat}</b><br>VAAR Atual: {format_currency_full(v)}" for cat, v in zip(df_sorted[categoria_col], df_sorted[val_atual_col])],
        )
    )

    # 3. Ponto Potencial: Melhor Hipótese
    def _delta_label(atu: float, pot: float) -> str:
        d = pot - atu
        if d >= 1e9:
            s = f"{d / 1e9:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"+R$ {s} bi"
        elif d >= 1e6:
            s = f"{d / 1e6:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"+R$ {s} mi"
        elif d >= 1e3:
            s = f"{d / 1e3:,.0f}".replace(",", ".")
            return f"+R$ {s} mil"
        elif d > 0:
            return f"+{format_currency_full(d)}"
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
                f"<b>{cat}</b><br>Potencial Máximo: {format_currency_full(pot)}<br>Salto: +{format_currency_full(pot - atu)}"
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


def chart_progressao_uniao(
    df_prog: pd.DataFrame,
    titulo: str,
    y_title: str = "Recursos (R$)",
) -> go.Figure:
    """Gráfico de barras empilhadas para a progressão da Complementação da União (2021–2026).
    
    Apresenta a composição em VAAF (fixo 10 p.p.), VAAT (progressivo) e VAAR (resultado) segundo Stephen Few.
    """
    fig = go.Figure()

    # VAAF (Base azul)
    fig.add_trace(
        go.Bar(
            x=df_prog["ano"],
            y=df_prog["vaaf"],
            name="VAAF (Fixo 10 p.p.)",
            marker=dict(color="#2563EB"),
            hoverinfo="text",
            hovertext=[f"<b>{ano}</b><br>VAAF: {format_currency_full(v)}" for ano, v in zip(df_prog["ano"], df_prog["vaaf"])],
        )
    )
    # VAAT (Verde petróleo intermediário)
    fig.add_trace(
        go.Bar(
            x=df_prog["ano"],
            y=df_prog["vaat"],
            name="VAAT (Progressivo até 10,5 p.p.)",
            marker=dict(color="#0D9488"),
            hoverinfo="text",
            hovertext=[f"<b>{ano}</b><br>VAAT: {format_currency_full(v)}" for ano, v in zip(df_prog["ano"], df_prog["vaat"])],
        )
    )
    # VAAR (Carmesim desempenho)
    fig.add_trace(
        go.Bar(
            x=df_prog["ano"],
            y=df_prog["vaar"],
            name="VAAR (Desempenho até 2,5 p.p.)",
            marker=dict(color="#E11D48"),
            hoverinfo="text",
            hovertext=[f"<b>{ano}</b><br>VAAR: {format_currency_full(v)}" for ano, v in zip(df_prog["ano"], df_prog["vaar"])],
        )
    )

    # Rótulo sobre o topo com o total formatado em ABNT
    totais_rotulos = [format_currency(tot) for tot in df_prog["total"]]
    fig.add_trace(
        go.Scatter(
            x=df_prog["ano"],
            y=df_prog["total"],
            mode="text",
            text=totais_rotulos,
            textposition="top center",
            showlegend=False,
            hoverinfo="skip",
        )
    )

    max_val = df_prog["total"].max() if not df_prog.empty else 1.0
    fig.update_layout(
        barmode="stack",
        title=dict(text=titulo, font=dict(size=13, color="#0F172A")),
        yaxis=dict(title=y_title, range=[0, max_val * 1.18]),
        height=380,
    )
    return apply_few_theme(fig, show_x_grid=False, show_y_grid=True)


# Cores por esforço (nº de condicionalidades a cumprir)
CORES_ESFORCO = {
    0: "#16A34A",   # já habilitada / sem esforço
    1: "#22C55E",   # 1 condicionalidade — quick win
    2: "#D97706",   # 2 — esforço médio
    3: "#DC2626",   # 3+ — esforço alto
}


def _cor_esforco(n: int) -> str:
    return CORES_ESFORCO.get(int(n), CORES_ESFORCO[3] if n >= 3 else CORES_ESFORCO[0])


def chart_pareto_vaar(
    df: pd.DataFrame,
    nome_col: str,
    valor_col: str,
    esforco_col: str,
    titulo: str,
    max_barras: int = 25,
) -> tuple[go.Figure, int, int]:
    """Gráfico de Pareto do retorno potencial de VAAR por município (Few/Juran).

    Barras (eixo esquerdo) = ganho potencial de VAAR por ente, ordenado do maior
    para o menor e colorido pelo ESFORÇO (nº de condicionalidades a cumprir).
    Linha (eixo direito) = % acumulado. Retorna (figura, n_vital_few, n_total),
    onde n_vital_few é quantos entes concentram 80% do ganho potencial total.
    """
    d = df[df[valor_col] > 0].sort_values(valor_col, ascending=False).reset_index(drop=True).copy()
    n_total = len(d)
    total = float(d[valor_col].sum()) or 1.0
    d["cum_pct"] = d[valor_col].cumsum() / total * 100.0
    # Minoria vital: menor nº de entes cujo acumulado atinge 80% do ganho total.
    n_vital = min(int((d["cum_pct"] < 80.0).sum()) + 1, n_total) if n_total else 0

    vis = d.head(max_barras)
    cores = [_cor_esforco(n) for n in vis[esforco_col]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=vis[nome_col], y=vis[valor_col],
        marker=dict(color=cores),
        name="Ganho potencial de VAAR",
        hovertext=[f"<b>{n}</b><br>Ganho potencial: {format_currency_full(v)}<br>Condicionalidades a cumprir: {int(e)}"
                   for n, v, e in zip(vis[nome_col], vis[valor_col], vis[esforco_col])],
        hoverinfo="text",
        yaxis="y",
    ))
    fig.add_trace(go.Scatter(
        x=vis[nome_col], y=vis["cum_pct"],
        mode="lines+markers",
        line=dict(color="#1E293B", width=2),
        marker=dict(size=5, color="#1E293B"),
        name="% acumulado",
        yaxis="y2",
        hovertemplate="Acumulado: %{y:.1f}%<extra></extra>",
    ))
    # Linha de referência 80%
    fig.add_hline(y=80, line=dict(color="#94A3B8", width=1, dash="dot"), yref="y2")

    fig.update_layout(
        title=dict(text=titulo, font=dict(size=13, color="#0F172A")),
        height=max(360, 30 + len(vis) * 14),
        bargap=0.25,
        yaxis=dict(title="Ganho potencial (R$)", side="left"),
        yaxis2=dict(title="% acumulado", overlaying="y", side="right",
                    range=[0, 105], ticksuffix="%", showgrid=False),
        xaxis=dict(tickangle=-45),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
    )
    fig = apply_few_theme(fig, show_x_grid=False, show_y_grid=True)
    fig.update_layout(yaxis2=dict(title="% acumulado", overlaying="y", side="right",
                                  range=[0, 105], ticksuffix="%", showgrid=False))
    return fig, n_vital, n_total


