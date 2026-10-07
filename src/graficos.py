"""Gráficos Plotly com visual padronizado. Usados pelo app.py e por notebooks."""
import threading

import pandas as pd
import plotly.graph_objects as go

# Paletas por tema. Os tons de azul/laranja são validados para daltonismo — não reordenar.
TEMAS = {
    "claro": {
        "azul": "#2a78d6", "laranja": "#eb6834",
        "area": "rgba(42,120,214,0.10)", "faixa": "rgba(42,120,214,0.12)",
        "sequencial": ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#2a78d6", "#1c5cab", "#104281", "#0d366b"],
        "superficie": "#ffffff", "tinta": "#0f172a", "tinta_2": "#475569", "muda": "#64748b",
        "grade": "#eef0f4", "eixo": "#d5dae3", "hover": "#ffffff",
    },
    "escuro": {
        "azul": "#3987e5", "laranja": "#d95926",
        "area": "rgba(57,135,229,0.14)", "faixa": "rgba(57,135,229,0.20)",
        # no escuro, valor baixo fica perto do fundo e valor alto mais claro
        "sequencial": ["#1a3556", "#184f95", "#1c5cab", "#2a78d6", "#3987e5", "#5598e7", "#86b6ef", "#b7d3f6"],
        "superficie": "#1b2433", "tinta": "#e8edf5", "tinta_2": "#c3cddb", "muda": "#94a3b8",
        "grade": "#2a3546", "eixo": "#3b4a60", "hover": "#0f1623",
    },
}
FONTE = 'Inter, system-ui, -apple-system, "Segoe UI", sans-serif'

# Tema por sessão: cada sessão do Streamlit roda em sua própria thread
_local = threading.local()


def usar_tema(nome: str) -> None:
    _local.cores = TEMAS[nome]


def _c() -> dict:
    return getattr(_local, "cores", TEMAS["claro"])


def _tema(fig: go.Figure, titulo: str, subtitulo: str | None = None, altura: int = 340) -> go.Figure:
    c = _c()
    texto = f"<b>{titulo}</b>" + (f"<br><span style='font-size:12px;color:{c['tinta_2']}'>{subtitulo}</span>"
                                   if subtitulo else "")
    fig.update_layout(
        title=dict(text=texto, x=0.01, xanchor="left", y=0.97, yanchor="top", font=dict(size=15, color=c['tinta'])),
        height=altura,
        margin=dict(l=12, r=28, t=78 if subtitulo else 56, b=12),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",  # transparente: o cartão de vidro aparece
        font=dict(family=FONTE, size=12, color=c['tinta_2']),
        separators=",.",
        hoverlabel=dict(bgcolor=c['hover'], bordercolor=c['eixo'], font=dict(family=FONTE, color=c['tinta'], size=13)),
        legend=dict(orientation="h", y=1.02, yanchor="bottom", x=1, xanchor="right",
                    font=dict(color=c['tinta_2'])),
        barcornerradius=4,
    )
    eixo = dict(gridcolor=c['grade'], gridwidth=1, linecolor=c['eixo'], zeroline=False,
                tickfont=dict(color=c['muda']), title_font=dict(color=c['muda']))
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
    c = _c()
    fig = go.Figure()
    for col, cor, nome in [("abertos", c["azul"], "Abertos"), ("resolvidos", c["laranja"], "Resolvidos")]:
        fig.add_scatter(x=semanal["inicio_semana"], y=semanal[col], name=nome, mode="lines",
                        line=dict(color=cor, width=2, shape="linear"),
                        hovertemplate=f"{nome}: %{{y}}<extra></extra>")
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(tickformat="%d/%m", hoverformat="Semana de %d/%m/%Y")
    fig.update_yaxes(rangemode="tozero")
    return _tema(fig, "Chamados por semana", "Abertos (data de criação) e resolvidos (data de resolução)")


def backlog(diario: pd.DataFrame) -> go.Figure:
    c = _c()
    fig = go.Figure(go.Scatter(
        x=diario["data"], y=diario["backlog"], mode="lines", fill="tozeroy", showlegend=False,
        line=dict(color=c["azul"], width=2), fillcolor=c["area"],
        hovertemplate="%{x|%d/%m/%Y}<br>Em aberto: %{y}<extra></extra>"))
    fim = diario.iloc[-1]
    fig.add_scatter(x=[fim["data"]], y=[fim["backlog"]], mode="markers+text", showlegend=False,
                    marker=dict(size=8, color=c["azul"], line=dict(color=c["superficie"], width=2)),
                    text=[f"{int(fim['backlog'])}"], textposition="middle right",
                    textfont=dict(color=c["tinta"]), hoverinfo="skip", cliponaxis=False)
    fig.update_xaxes(tickformat="%d/%m")
    fig.update_yaxes(rangemode="tozero")
    return _tema(fig, "Backlog diário", "Chamados em aberto ao fim de cada dia")


# ---------------------------------------------------------------- colunas e barras

def colunas(x, y, titulo: str, subtitulo: str | None = None, sufixo: str = "",
            casas: int = 0, linha_meta: float | None = None) -> go.Figure:
    c = _c()
    rotulos = [fmt(v, casas) + sufixo if pd.notna(v) else "" for v in y]
    fig = go.Figure(go.Bar(
        x=x, y=y, marker_color=c["azul"], text=rotulos, textposition="outside", cliponaxis=False,
        textfont=dict(color=c["tinta_2"]), hovertemplate="%{x}<br>%{text}<extra></extra>"))
    if linha_meta is not None:
        fig.add_hline(y=linha_meta, line=dict(color=c["muda"], width=1),
                      annotation_text=f"meta {fmt(linha_meta, 0)}{sufixo}",
                      annotation_font=dict(color=c["muda"], size=11), annotation_position="top left")
    fig.update_layout(bargap=0.55)
    fig.update_xaxes(type="category")
    fig.update_yaxes(rangemode="tozero")
    return _tema(fig, titulo, subtitulo)


def barras_horizontais(rotulos, valores, titulo: str, subtitulo: str | None = None,
                       sufixo: str = "", casas: int = 0, altura: int | None = None) -> go.Figure:
    """Ranking: maior em cima. Recebe já ordenado do maior para o menor."""
    c = _c()
    rotulos, valores = list(rotulos)[::-1], list(valores)[::-1]
    textos = [fmt(v, casas) + sufixo for v in valores]
    fig = go.Figure(go.Bar(
        y=rotulos, x=valores, orientation="h", marker_color=c["azul"], text=textos,
        textposition="outside", cliponaxis=False, textfont=dict(color=c["tinta_2"]),
        hovertemplate="%{y}<br>%{text}<extra></extra>"))
    fig.update_layout(bargap=0.45)
    altura = altura or max(260, 34 * len(rotulos) + 70)
    fig = _tema(fig, titulo, subtitulo, altura)
    fig.update_xaxes(showgrid=False, showline=False, showticklabels=False)
    fig.update_yaxes(showgrid=False, showline=True, ticksuffix="  ", tickfont=dict(color=c["tinta_2"]))
    return fig


# ---------------------------------------------------------------- mapa de calor

def heatmap_dia_hora(fato: pd.DataFrame) -> go.Figure:
    c = _c()
    dias = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
    horas = range(max(fato["hora"].min(), 0), min(fato["hora"].max(), 23) + 1)
    tabela = (fato.groupby([fato["dia_semana"].astype(str), "hora"]).size().unstack(fill_value=0)
              .reindex(index=dias, columns=horas, fill_value=0))
    tabela = tabela.loc[(tabela.sum(axis=1) > 0) | tabela.index.isin(dias[:5])]  # oculta fim de semana vazio
    seq = c["sequencial"]
    escala = [[0, "rgba(0,0,0,0)"], [1e-9, seq[0]]] + \
             [[(i + 1) / (len(seq) - 1), cor] for i, cor in enumerate(seq[1:])]
    fig = go.Figure(go.Heatmap(
        z=tabela.values, x=[f"{h}h" for h in tabela.columns], y=tabela.index,
        colorscale=escala, xgap=2, ygap=2,
        colorbar=dict(thickness=10, outlinewidth=0, tickfont=dict(color=c["muda"]), title=None),
        hovertemplate="%{y}, %{x}<br>%{z} chamados<extra></extra>"))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(showline=False)
    return _tema(fig, "Quando os chamados são abertos", "Quantidade por dia da semana e hora (horário de Brasília)")


# ---------------------------------------------------------------- previsão

def previsao_semanal(historico: pd.Series, previsao: pd.DataFrame) -> go.Figure:
    """Histórico (linha cheia) + previsão (tracejada, por ser projeção) com faixa de 80%."""
    c = _c()
    fig = go.Figure()
    # faixa de incerteza: começa no último ponto real para a linha não "pular"
    ultimo_x, ultimo_y = historico.index[-1], historico.iloc[-1]
    x_faixa = [ultimo_x, *previsao["inicio_semana"]]
    fig.add_scatter(x=x_faixa, y=[ultimo_y, *previsao["lim_sup"]], mode="lines",
                    line=dict(width=0), showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=x_faixa, y=[ultimo_y, *previsao["lim_inf"]], mode="lines", line=dict(width=0),
                    fill="tonexty", fillcolor=c["faixa"], name="Faixa provável (80%)",
                    hoverinfo="skip")
    fig.add_scatter(x=historico.index, y=historico.values, mode="lines", name="Realizado",
                    line=dict(color=c["azul"], width=2),
                    hovertemplate="Semana de %{x|%d/%m}<br>Realizado: %{y}<extra></extra>")
    texto = [f"{fmt(p, 0)} (entre {fmt(i, 0)} e {fmt(s, 0)})"
             for p, i, s in zip(previsao["previsao"], previsao["lim_inf"], previsao["lim_sup"])]
    fig.add_scatter(x=[ultimo_x, *previsao["inicio_semana"]], y=[ultimo_y, *previsao["previsao"]],
                    mode="lines+markers", name="Previsão",
                    line=dict(color=c["azul"], width=2, dash="dash"),
                    marker=dict(size=[0] + [8] * len(previsao), color=c["azul"],
                                line=dict(color=c["superficie"], width=2)),
                    customdata=[""] + texto,
                    hovertemplate="Semana de %{x|%d/%m}<br>Previsão: %{customdata}<extra></extra>")
    fig.update_xaxes(tickformat="%d/%m")
    fig.update_yaxes(rangemode="tozero")
    return _tema(fig, "Previsão de chamados por semana",
                 "Linha tracejada = previsão; área = faixa onde o valor deve cair em 8 de cada 10 semanas",
                 altura=380)
