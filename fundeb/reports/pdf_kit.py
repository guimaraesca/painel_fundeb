"""Kit de componentes para relatórios PDF (ReportLab, sem dependência de sistema).

Mantém o relatório desacoplado do Streamlit: formatadores BR/ABNT próprios,
paleta sóbria (slate + azul de ênfase), e flowables reutilizáveis — capa, títulos
de seção, faixa de KPIs, tabelas e gráfico de barras horizontais.
"""
from __future__ import annotations

from datetime import datetime
from typing import Sequence

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Drawing, Line
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.platypus import Flowable, Paragraph, Spacer, Table, TableStyle

# ------------------------------------------------------------------ paleta
AZUL = colors.HexColor("#1E3A8A")
AZUL_CLARO = colors.HexColor("#2563EB")
SLATE = colors.HexColor("#475569")
SLATE_CLARO = colors.HexColor("#94A3B8")
TINTA = colors.HexColor("#0F172A")
BORDA = colors.HexColor("#E2E8F0")
FUNDO_SUAVE = colors.HexColor("#F8FAFC")
VERDE = colors.HexColor("#16A34A")
VERMELHO = colors.HexColor("#DC2626")
AMBAR = colors.HexColor("#D97706")

PAGINA = A4
MARGEM = 16 * mm
LARGURA_UTIL = PAGINA[0] - 2 * MARGEM


# ------------------------------------------------------------------ formatação BR/ABNT
def _br(num: float, dec: int) -> str:
    return f"{num:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def moeda(v: float | None, compacto: bool = True) -> str:
    if v is None or v != v:
        return "—"
    s = "-" if v < 0 else ""
    a = abs(v)
    if compacto and a >= 1e9:
        return f"{s}R$ {_br(a / 1e9, 2)} bi"
    if compacto and a >= 1e6:
        return f"{s}R$ {_br(a / 1e6, 2)} mi"
    return f"{s}R$ {_br(a, 2)}"


def pct(v: float | None, dec: int = 1) -> str:
    return "—" if v is None or v != v else f"{_br(v, dec)}%"


def numero(v: float | None, dec: int = 0) -> str:
    return "—" if v is None or v != v else _br(v, dec)


def valor_indicador(v: float | None, unidade: str) -> str:
    if v is None or v != v:
        return "—"
    if unidade == "R$":
        return moeda(v)
    if unidade == "%":
        return pct(v)
    if unidade in ("índice", "proficiência"):
        return _br(v, 1 if unidade == "índice" else 0)
    if unidade == "Mbps":
        return f"{_br(v, 1)} Mbps"
    if unidade == "contagem":
        return numero(v)
    if unidade == "bool":
        return "Sim" if v else "Não"
    return _br(v, 2)


# ------------------------------------------------------------------ estilos
def estilos() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    fam = "Helvetica"
    return {
        "capa_titulo": ParagraphStyle("capa_titulo", parent=base["Title"], fontName=fam + "-Bold",
                                      fontSize=24, leading=28, textColor=colors.white, alignment=TA_LEFT),
        "capa_sub": ParagraphStyle("capa_sub", fontName=fam, fontSize=12, leading=16,
                                   textColor=colors.HexColor("#CBD5E1"), alignment=TA_LEFT),
        "h1": ParagraphStyle("h1", fontName=fam + "-Bold", fontSize=14, leading=18,
                             textColor=TINTA, spaceBefore=10, spaceAfter=4),
        "h2": ParagraphStyle("h2", fontName=fam + "-Bold", fontSize=11, leading=15,
                             textColor=AZUL, spaceBefore=8, spaceAfter=2),
        "corpo": ParagraphStyle("corpo", fontName=fam, fontSize=9.5, leading=14, textColor=TINTA),
        "corpo_cinza": ParagraphStyle("corpo_cinza", fontName=fam, fontSize=9, leading=13, textColor=SLATE),
        "bluf": ParagraphStyle("bluf", fontName=fam, fontSize=10.5, leading=15, textColor=TINTA,
                               backColor=FUNDO_SUAVE, borderColor=AZUL, borderWidth=0,
                               leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=8,
                               borderPadding=(8, 8, 8, 8)),
        "rodape": ParagraphStyle("rodape", fontName=fam, fontSize=7.5, leading=10, textColor=SLATE_CLARO),
        "kpi_valor": ParagraphStyle("kpi_valor", fontName=fam + "-Bold", fontSize=15, leading=17,
                                    textColor=TINTA, alignment=TA_LEFT),
        "kpi_rotulo": ParagraphStyle("kpi_rotulo", fontName=fam + "-Bold", fontSize=7, leading=9,
                                     textColor=SLATE, alignment=TA_LEFT),
        "kpi_sub": ParagraphStyle("kpi_sub", fontName=fam, fontSize=7.5, leading=9.5, textColor=SLATE),
        "cel": ParagraphStyle("cel", fontName=fam, fontSize=8.5, leading=11, textColor=TINTA),
        "cel_dir": ParagraphStyle("cel_dir", fontName=fam, fontSize=8.5, leading=11, textColor=TINTA, alignment=TA_RIGHT),
        "cab": ParagraphStyle("cab", fontName=fam + "-Bold", fontSize=8.5, leading=11, textColor=colors.white),
        "cab_dir": ParagraphStyle("cab_dir", fontName=fam + "-Bold", fontSize=8.5, leading=11,
                                  textColor=colors.white, alignment=TA_RIGHT),
    }


ST = estilos()


# ------------------------------------------------------------------ capa (faixa colorida)
class FaixaCapa(Flowable):
    def __init__(self, titulo: str, subtitulo: str, tag: str, altura: float = 62 * mm):
        super().__init__()
        self.titulo, self.subtitulo, self.tag, self.altura = titulo, subtitulo, tag, altura
        self.width = LARGURA_UTIL

    def wrap(self, *_):
        return self.width, self.altura

    def draw(self):
        c = self.canv
        c.setFillColor(AZUL)
        c.roundRect(0, 0, self.width, self.altura, 8, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 23)
        c.drawString(14 * mm, self.altura - 22 * mm, self.titulo)
        c.setFillColor(colors.HexColor("#CBD5E1"))
        c.setFont("Helvetica", 11.5)
        # subtítulo com quebra simples
        y = self.altura - 31 * mm
        for linha in _quebrar(self.subtitulo, 82):
            c.drawString(14 * mm, y, linha)
            y -= 6 * mm
        # tag
        c.setFillColor(colors.HexColor("#1E40AF"))
        c.roundRect(14 * mm, 9 * mm, 92 * mm, 7 * mm, 3.5, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(17 * mm, 11.2 * mm, self.tag.upper())


def _quebrar(texto: str, largura: int) -> list[str]:
    palavras, linhas, atual = texto.split(), [], ""
    for p in palavras:
        if len(atual) + len(p) + 1 <= largura:
            atual = f"{atual} {p}".strip()
        else:
            linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


def bluf(texto_html: str) -> Table:
    """Caixa de leitura executiva (conclusão antes da evidência)."""
    p = Paragraph(texto_html, ST["bluf"])
    t = Table([[p]], colWidths=[LARGURA_UTIL])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), FUNDO_SUAVE),
        ("LINEBEFORE", (0, 0), (0, -1), 3, AZUL),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDA),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def faixa_kpis(itens: Sequence[tuple[str, str, str]]) -> Table:
    """Linha de KPIs: cada item é (rótulo, valor, subtítulo)."""
    celulas = []
    for rotulo, valor, sub in itens:
        bloco = [
            Paragraph(rotulo.upper(), ST["kpi_rotulo"]),
            Spacer(1, 2),
            Paragraph(valor, ST["kpi_valor"]),
            Spacer(1, 1),
            Paragraph(sub, ST["kpi_sub"]),
        ]
        celulas.append(bloco)
    larg = LARGURA_UTIL / len(celulas)
    t = Table([celulas], colWidths=[larg] * len(celulas))
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, BORDA),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
    ]))
    return t


def tabela(cabecalho: Sequence[str], linhas: Sequence[Sequence[str]],
           larguras: Sequence[float] | None = None, alinhar_dir: Sequence[int] = ()) -> Table:
    dados = [[Paragraph(h, ST["cab_dir"] if i in alinhar_dir else ST["cab"]) for i, h in enumerate(cabecalho)]]
    for ln in linhas:
        dados.append([Paragraph(str(c), ST["cel_dir"] if i in alinhar_dir else ST["cel"])
                      for i, c in enumerate(ln)])
    if larguras is None:
        larguras = [LARGURA_UTIL / len(cabecalho)] * len(cabecalho)
    t = Table(dados, colWidths=larguras, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, FUNDO_SUAVE]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDA),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    t.setStyle(TableStyle(estilo))
    return t


def _rotulo_barra_int(v: float) -> str:
    return _br(v, 0)


def grafico_barras(categorias: Sequence[str], valores: Sequence[float], titulo: str = "",
                   cor=AZUL_CLARO, altura: float = None, fmt=None) -> Drawing:
    """Gráfico de barras horizontais (base zero), rótulos à direita de cada barra.

    ``fmt`` é um callable valor→str (ReportLab aceita função em ``barLabelFormat``);
    o padrão formata inteiros no padrão BR (ponto de milhar).
    """
    fmt = fmt or _rotulo_barra_int
    n = len(categorias)
    alt = altura or max(60, n * 20 + 28)
    d = Drawing(LARGURA_UTIL, alt)
    bc = HorizontalBarChart()
    bc.x = 86
    bc.y = 14
    bc.width = LARGURA_UTIL - 150
    bc.height = alt - 26
    bc.data = [list(valores)]
    bc.strokeColor = None
    bc.bars[0].fillColor = cor
    bc.valueAxis.valueMin = 0
    vmax = max(valores) if valores else 1
    bc.valueAxis.valueMax = vmax * 1.18 if vmax > 0 else 1
    bc.valueAxis.visible = False
    bc.valueAxis.visibleGrid = False
    bc.categoryAxis.categoryNames = list(categorias)
    bc.categoryAxis.labels.fontName = "Helvetica"
    bc.categoryAxis.labels.fontSize = 8
    bc.categoryAxis.labels.dx = -4
    bc.categoryAxis.strokeColor = BORDA
    bc.barLabelFormat = fmt
    bc.barLabels.fontName = "Helvetica-Bold"
    bc.barLabels.fontSize = 7.5
    bc.barLabels.dx = 6
    bc.barLabels.boxAnchor = "w"
    bc.barLabels.fillColor = SLATE
    d.add(bc)
    if titulo:
        from reportlab.graphics.shapes import String
        d.add(String(0, alt - 10, titulo, fontName="Helvetica-Bold", fontSize=9, fillColor=TINTA))
    return d


def regua() -> Drawing:
    d = Drawing(LARGURA_UTIL, 6)
    d.add(Line(0, 3, LARGURA_UTIL, 3, strokeColor=BORDA, strokeWidth=0.6))
    return d


def rodape_callback(texto: str):
    """Retorna função onPage que carimba número de página e proveniência."""
    def _desenhar(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(SLATE_CLARO)
        canvas.drawString(MARGEM, 10 * mm, texto)
        canvas.drawRightString(PAGINA[0] - MARGEM, 10 * mm, f"Página {doc.page}")
        canvas.setStrokeColor(BORDA)
        canvas.line(MARGEM, 13 * mm, PAGINA[0] - MARGEM, 13 * mm)
        canvas.restoreState()
    return _desenhar


def carimbo_data() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")
