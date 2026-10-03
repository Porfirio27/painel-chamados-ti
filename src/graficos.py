"""Gráficos Plotly com visual padronizado. Usados pelo app.py e por notebooks."""
import pandas as pd
import plotly.graph_objects as go

# Paleta (validada para daltonismo na ordem abaixo — não reordenar)
AZUL = "#2a78d6"
LARANJA = "#eb6834"
SEQUENCIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#2a78d6", "#1c5cab", "#104281", "#0d366b"]

SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
TINTA_MUDA = "#898781"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"
FONTE = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def _tema(fig: go.Figure, titulo: str, subtitulo: str | None = None, altura: int = 340) -> go.Figure:
    texto = f"<b>{titulo}</b>" + (f"<br><span style='font-size:12px;color:{TINTA_2}'>{subtitulo}</span>"
                                   if subtitulo else "")
    fig.update_layout(
        title=dict(text=texto, x=0, xanchor="left", font=dict(size=15, color=TINTA)),
        height=altura,
        margin=dict(l=8, r=24, t=64 if subtitulo else 48, b=8),
        paper_bgcolor=SUPERFICIE, plot_bgcolor=SUPERFICIE,
        font=dict(family=FONTE, size=12, color=TINTA_2),
        separators=",.",
        hoverlabel=dict(bgcolor="white", bordercolor=GRADE, font=dict(family=FONTE, color=TINTA)),
        legend=dict(orientation="h", y=1.02, yanchor="bottom", x=1, xanchor="right",
                    font=dict(color=TINTA_2)),
        barcornerradius=4,
    )
    eixo = dict(gridcolor=GRADE, gridwidth=1, linecolor=EIXO, zeroline=False,
                tickfont=dict(color=TINTA_MUDA), title_font=dict(color=TINTA_MUDA))
    fig.update_xaxes(**eixo, showgrid=False, showline=True)
    fig.update_yaxes(**eixo, showgrid=True, showline=False)
    return fig


MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def rotulo_mes(ano_mes: str) -> str:
    """'2026-05' -> 'mai/26'"""
    ano, mes = ano_mes.split("-")
    return f"{MESES[int(mes) - 1]}/{ano[2:]}"


def fmt(valor: float, casas: int = 1) -> str:
    """Número no padrão brasileiro."""
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------- séries temporais

def abertos_vs_resolvidos(semanal: pd.DataFrame) -> go.Figure:
    """semanal: colunas inicio_semana, abertos, resolvidos."""
    fig = go.Figure()
    for col, cor, nome in [("abertos", AZUL, "Abertos"), ("resolvidos", LARANJA, "Resolvidos")]:
        fig.add_scatter(x=semanal["inicio_semana"], y=semanal[col], name=nome, mode="lines",
                        line=dict(color=cor, width=2, shape="linear"),
                        hovertemplate=f"{nome}: %{{y}}<extra></extra>")
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(tickformat="%d/%m", hoverformat="Semana de %d/%m/%Y")
    fig.update_yaxes(rangemode="tozero")
    return _tema(fig, "Chamados por semana", "Abertos (data de criação) e resolvidos (data de resolução)")


def backlog(diario: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=diario["data"], y=diario["backlog"], mode="lines", fill="tozeroy", showlegend=False,
        line=dict(color=AZUL, width=2), fillcolor="rgba(42,120,214,0.10)",
        hovertemplate="%{x|%d/%m/%Y}<br>Em aberto: %{y}<extra></extra>"))
    fim = diario.iloc[-1]
    fig.add_scatter(x=[fim["data"]], y=[fim["backlog"]], mode="markers+text", showlegend=False,
                    marker=dict(size=8, color=AZUL, line=dict(color=SUPERFICIE, width=2)),
                    text=[f"{int(fim['backlog'])}"], textposition="middle right",
                    textfont=dict(color=TINTA), hoverinfo="skip", cliponaxis=False)
    fig.update_xaxes(tickformat="%d/%m")
    fig.update_yaxes(rangemode="tozero")
    return _tema(fig, "Backlog diário", "Chamados em aberto ao fim de cada dia")


# ---------------------------------------------------------------- colunas e barras

def colunas(x, y, titulo: str, subtitulo: str | None = None, sufixo: str = "",
            casas: int = 0, linha_meta: float | None = None) -> go.Figure:
    rotulos = [fmt(v, casas) + sufixo if pd.notna(v) else "" for v in y]
    fig = go.Figure(go.Bar(
        x=x, y=y, marker_color=AZUL, text=rotulos, textposition="outside", cliponaxis=False,
        textfont=dict(color=TINTA_2), hovertemplate="%{x}<br>%{text}<extra></extra>"))
    if linha_meta is not None:
        fig.add_hline(y=linha_meta, line=dict(color=TINTA_MUDA, width=1),
                      annotation_text=f"meta {fmt(linha_meta, 0)}{sufixo}",
                      annotation_font=dict(color=TINTA_MUDA, size=11), annotation_position="top left")
    fig.update_layout(bargap=0.55)
    fig.update_xaxes(type="category")
    fig.update_yaxes(rangemode="tozero")
    return _tema(fig, titulo, subtitulo)


def barras_horizontais(rotulos, valores, titulo: str, subtitulo: str | None = None,
                       sufixo: str = "", casas: int = 0, altura: int | None = None) -> go.Figure:
    """Ranking: maior em cima. Recebe já ordenado do maior para o menor."""
    rotulos, valores = list(rotulos)[::-1], list(valores)[::-1]
    textos = [fmt(v, casas) + sufixo for v in valores]
    fig = go.Figure(go.Bar(
        y=rotulos, x=valores, orientation="h", marker_color=AZUL, text=textos,
        textposition="outside", cliponaxis=False, textfont=dict(color=TINTA_2),
        hovertemplate="%{y}<br>%{text}<extra></extra>"))
    fig.update_layout(bargap=0.45)
    altura = altura or max(260, 34 * len(rotulos) + 70)
    fig = _tema(fig, titulo, subtitulo, altura)
    fig.update_xaxes(showgrid=False, showline=False, showticklabels=False)
    fig.update_yaxes(showgrid=False, showline=True, ticksuffix="  ", tickfont=dict(color=TINTA_2))
    return fig


# ---------------------------------------------------------------- mapa de calor

def heatmap_dia_hora(fato: pd.DataFrame) -> go.Figure:
    dias = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
    horas = range(max(fato["hora"].min(), 0), min(fato["hora"].max(), 23) + 1)
    tabela = (fato.groupby([fato["dia_semana"].astype(str), "hora"]).size().unstack(fill_value=0)
              .reindex(index=dias, columns=horas, fill_value=0))
    tabela = tabela.loc[(tabela.sum(axis=1) > 0) | tabela.index.isin(dias[:5])]  # oculta fim de semana vazio
    escala = [[0, SUPERFICIE], [1e-9, SEQUENCIAL[0]]] + \
             [[(i + 1) / (len(SEQUENCIAL) - 1), c] for i, c in enumerate(SEQUENCIAL[1:])]
    fig = go.Figure(go.Heatmap(
        z=tabela.values, x=[f"{h}h" for h in tabela.columns], y=tabela.index,
        colorscale=escala, xgap=2, ygap=2,
        colorbar=dict(thickness=10, outlinewidth=0, tickfont=dict(color=TINTA_MUDA), title=None),
        hovertemplate="%{y}, %{x}<br>%{z} chamados<extra></extra>"))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(showline=False)
    return _tema(fig, "Quando os chamados são abertos", "Quantidade por dia da semana e hora (horário de Brasília)")
