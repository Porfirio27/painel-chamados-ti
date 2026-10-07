"""Relatório resumido em PDF, gerado com os mesmos filtros do painel.

Usa matplotlib + fpdf2 (Python puro), para funcionar também no Streamlit Cloud.
"""
import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from fpdf import FPDF  # noqa: E402
from fpdf.fonts import FontFace  # noqa: E402

from src import config, previsao  # noqa: E402
from src.estilo import delta  # noqa: E402
from src.graficos import fmt, rotulo_mes  # noqa: E402

AZUL, LARANJA = "#2a78d6", "#eb6834"
TINTA, TINTA_2, MUDA, GRADE = "#0f172a", "#475569", "#64748b", "#e5e7eb"
AZUL_RGB, AZUL_ESCURO_RGB = (42, 120, 214), (13, 54, 107)
FONTES = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
DIAS = {"seg": "segunda", "ter": "terça", "qua": "quarta", "qui": "quinta", "sex": "sexta", "sáb": "sábado", "dom": "domingo"}
DESCRICOES = {
    "sem_primeira_resposta": "Resolvido sem registro de primeira resposta",
    "fechamento_em_lote": "Fechado em lote (data de fechamento não confiável)",
    "categoria_nao_classificada": "Categoria não classificada",
    "fechado_sem_resolucao": "Fechado sem data de resolução",
    "resolvido_antes_de_criado": "Resolução anterior à abertura",
    "resolucao_acima_7_dias": "Mais de 7 dias para resolver",
}


# ---------------------------------------------------------------- gráficos (matplotlib)

def _png(fig) -> io.BytesIO:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf


def _eixos(ax, titulo: str) -> None:
    ax.set_title(titulo, loc="left", fontsize=10, fontweight="bold", color=TINTA, pad=10)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color("#cbd5e1")
    ax.grid(axis="y", color=GRADE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUDA, labelsize=8, length=0)


def _semanal(df: pd.DataFrame, ini, fim) -> pd.DataFrame:
    r = df["resolvido_em"].dropna()
    semana_res = (r.dt.normalize() - pd.to_timedelta(r.dt.dayofweek, unit="D")).dt.date
    semanal = (pd.DataFrame({"abertos": df.groupby("inicio_semana").size(), "resolvidos": semana_res.value_counts()})
               .fillna(0).astype(int).sort_index())
    hoje = pd.Timestamp.now(tz=config.FUSO).date()
    inicio_atual = hoje - pd.Timedelta(days=hoje.weekday())
    idx = pd.Index(semanal.index)
    return semanal[(idx >= ini - pd.Timedelta(days=6)) & (idx <= fim) & (idx < inicio_atual)]


def _grafico_semanal(semanal: pd.DataFrame) -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(9, 2.9))
    x = pd.to_datetime(semanal.index)
    ax.plot(x, semanal["abertos"], color=AZUL, linewidth=2, label="Abertos")
    ax.plot(x, semanal["resolvidos"], color=LARANJA, linewidth=2, label="Resolvidos")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    _eixos(ax, "Chamados por semana (abertos x resolvidos)")
    return _png(fig)


def _grafico_sla(df: pd.DataFrame) -> io.BytesIO:
    mensal = df.groupby("ano_mes")["sla_resolucao_cumprido"].agg(lambda s: s.dropna().mean() * 100)
    fig, ax = plt.subplots(figsize=(9, 2.6))
    rotulos = [rotulo_mes(m) for m in mensal.index]
    barras = ax.bar(rotulos, mensal.values, color=AZUL, width=0.45)
    for b, v in zip(barras, mensal.values):
        if pd.notna(v):
            ax.text(b.get_x() + b.get_width() / 2, v + 2, f"{v:.0f}%", ha="center", fontsize=8, color=TINTA_2)
    ax.set_ylim(0, 110)
    ax.set_yticks([0, 25, 50, 75, 100])
    _eixos(ax, "SLA de resolução cumprido por mês (%)")
    return _png(fig)


def _grafico_previsao(res) -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(9, 2.7))
    hist, prev = res.historico, res.previsao
    ultimo_x, ultimo_y = hist.index[-1], hist.iloc[-1]
    xs = [ultimo_x, *prev["inicio_semana"]]
    ax.fill_between(xs, [ultimo_y, *prev["lim_inf"]], [ultimo_y, *prev["lim_sup"]], color=AZUL, alpha=0.13,
                    linewidth=0, label="Faixa provável (80%)")
    ax.plot(hist.index, hist.values, color=AZUL, linewidth=2, label="Realizado")
    ax.plot(xs, [ultimo_y, *prev["previsao"]], color=AZUL, linewidth=2, linestyle="--", marker="o", markersize=3,
            label="Previsão")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3)
    _eixos(ax, "Chamados por semana: realizado e previsão das próximas 8 semanas")
    return _png(fig)


# ---------------------------------------------------------------- textos

MINUSCULAS = {"de", "da", "do", "das", "dos", "e", "em", "a", "o"}


def _nome(texto: str) -> str:
    """'CENTRAL DE REGULAÇÃO (ADM)' -> 'Central de Regulação (Adm)'"""
    def maiuscula(p: str) -> str:  # primeira letra, mesmo depois de "(" ou "–"
        for i, ch in enumerate(p):
            if ch.isalpha():
                return p[:i] + ch.upper() + p[i + 1:]
        return p
    palavras = str(texto).lower().split()
    return " ".join(p if i and p.strip("()") in MINUSCULAS else maiuscula(p) for i, p in enumerate(palavras))

def _destaques(df: pd.DataFrame, ant: pd.DataFrame) -> list[str]:
    itens = []
    cat = df["categoria"].value_counts()
    itens.append(f"{cat.index[0]} lidera a demanda, com {cat.iloc[0]} chamados ({cat.iloc[0] / len(df):.0%} do total).")
    setor = df["setor"].value_counts()
    itens.append(f"O setor com mais chamados é {_nome(setor.index[0])} ({setor.iloc[0]}).")
    dias = df["dia_semana"].astype(str).value_counts()
    hora = int(df["hora"].value_counts().idxmax())
    dois = dias.head(2)
    itens.append(f"{DIAS.get(dois.index[0], dois.index[0]).capitalize()} e {DIAS.get(dois.index[-1], dois.index[-1])} "
                 f"concentram {dois.sum() / len(df):.0%} dos chamados; o horário de pico é das {hora}h às {hora + 1}h.")
    mensal = df.groupby("ano_mes").agg(n=("codigo", "size"), sla=("sla_resolucao_cumprido", lambda s: s.dropna().mean()))
    mensal = mensal[mensal["n"] >= 10].dropna()
    if len(mensal) >= 2:
        melhor, pior = mensal["sla"].idxmax(), mensal["sla"].idxmin()
        itens.append(f"Melhor mês de SLA: {rotulo_mes(melhor)} ({mensal.loc[melhor, 'sla']:.0%}); "
                     f"pior: {rotulo_mes(pior)} ({mensal.loc[pior, 'sla']:.0%}).")
    if len(ant):
        var = len(df) / len(ant) - 1
        sentido = "a mais" if var > 0 else "a menos"
        itens.append(f"Foram {abs(var):.0%} chamados {sentido} que no período anterior de mesma duração ({len(ant)}).")
    itens.append(f"A primeira resposta está registrada em só {df['tem_primeira_resposta'].mean():.0%} dos chamados.")
    return itens


def _ranking(df: pd.DataFrame, coluna: str, n: int = 5) -> list[list[str]]:
    g = (df.groupby(coluna).agg(chamados=("codigo", "size"), mediana=("tempo_resolucao_h", "median"),
                                sla=("sla_resolucao_cumprido", lambda s: s.dropna().mean() * 100))
         .sort_values("chamados", ascending=False).head(n))
    total = len(df)
    return [[_nome(nome) if coluna == "setor" else str(nome), str(int(r.chamados)), f"{r.chamados / total:.0%}",
             f"{fmt(r.mediana)} h" if pd.notna(r.mediana) else "–", f"{r.sla:.0f}%" if pd.notna(r.sla) else "–"]
            for nome, r in g.iterrows()]


# ---------------------------------------------------------------- PDF

class _PDF(FPDF):
    def __init__(self, rodape: str):
        super().__init__(format="A4")
        self.rodape = rodape
        self.add_font("DejaVu", "", str(FONTES / "DejaVuSans.ttf"))
        self.add_font("DejaVu", "B", str(FONTES / "DejaVuSans-Bold.ttf"))
        self.set_auto_page_break(auto=True, margin=16)
        self.set_margins(15, 15, 15)

    def footer(self):
        self.set_y(-11)
        self.set_font("DejaVu", "", 7)
        self.set_text_color(100, 116, 139)
        self.cell(0, 5, self.rodape, align="L")
        self.cell(0, 5, f"Página {self.page_no()} de {{nb}}", align="R")

    def titulo_secao(self, texto: str):
        self.ln(3)
        self.set_font("DejaVu", "B", 11)
        self.set_text_color(15, 23, 42)
        self.cell(0, 7, texto, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*AZUL_RGB)
        self.set_line_width(0.6)
        self.line(self.l_margin, self.get_y(), self.l_margin + 18, self.get_y())
        self.ln(2.5)

    def tabela(self, cabecalho: list[str], linhas: list[list[str]], larguras: tuple):
        self.set_font("DejaVu", "", 8.5)
        self.set_text_color(15, 23, 42)
        alinhar = ("LEFT",) + ("RIGHT",) * (len(cabecalho) - 1)
        with self.table(col_widths=larguras, text_align=alinhar, line_height=6, borders_layout="HORIZONTAL_LINES",
                        headings_style=FontFace(emphasis="BOLD", color=(255, 255, 255), fill_color=AZUL_ESCURO_RGB),
                        cell_fill_color=(244, 247, 251), cell_fill_mode="ROWS") as t:
            for linha in [cabecalho, *linhas]:
                row = t.row()
                for valor in linha:
                    row.cell(valor)


def gerar(df: pd.DataFrame, base: pd.DataFrame, ant: pd.DataFrame, qualidade: pd.DataFrame,
          ini, fim, filtros: dict[str, list], atualizado: pd.Timestamp) -> bytes:
    """Monta o PDF (2 páginas) e devolve os bytes."""
    agora = pd.Timestamp.now(tz=config.FUSO)
    pdf = _PDF(f"Painel de Chamados de TI · dados de {atualizado:%d/%m/%Y %H:%M} · "
               f"SLA recalculado (meta {config.SLA_RESOLUCAO_HORAS['alta']}h para alta e média)")
    pdf.add_page()

    # Cabeçalho
    pdf.set_fill_color(*AZUL_ESCURO_RGB)
    pdf.rect(0, 0, 210, 34, style="F")
    pdf.set_fill_color(*AZUL_RGB)
    pdf.rect(0, 34, 210, 1.5, style="F")
    pdf.set_xy(15, 9)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", "B", 18)
    pdf.cell(0, 9, "Relatório de Chamados de TI", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 9.5)
    pdf.cell(0, 6, f"Período: {ini:%d/%m/%Y} a {fim:%d/%m/%Y}   ·   Gerado em {agora:%d/%m/%Y às %H:%M}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(40)

    # Filtros
    def nomes(chave, vazio):
        return ", ".join(filtros.get(chave) or []) or vazio
    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(0, 4.5, f"Filtros — Grupo de setor: {nomes('grupos', 'Todos')} · Categoria: {nomes('categorias', 'Todas')}"
                           f" · Prioridade: {nomes('prioridades', 'Todas')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Indicadores
    def med(d, c):
        return d[c].median() if len(d) else None
    sla_at = df["sla_resolucao_cumprido"].dropna().mean() * 100
    sla_ant = ant["sla_resolucao_cumprido"].dropna().mean() * 100 if len(ant) else None
    cartoes = [
        ("Chamados no período", f"{len(df)}", delta(len(df), len(ant) if len(ant) else None, pct=True, neutro=True)),
        ("Resolução mediana", f"{fmt(med(df, 'tempo_resolucao_h'))} h",
         delta(med(df, "tempo_resolucao_h"), med(ant, "tempo_resolucao_h"), 1, "h", menor_melhor=True)),
        ("Horário útil (mediana)", f"{fmt(med(df, 'tempo_resolucao_util_h'))} h",
         delta(med(df, "tempo_resolucao_util_h"), med(ant, "tempo_resolucao_util_h"), 1, "h", menor_melhor=True)),
        ("SLA cumprido", f"{sla_at:.0f}%", delta(sla_at, sla_ant, 0, " p.p.")),
        ("Em aberto agora", f"{int(base['aberto'].sum())}", (None, "neutro")),
    ]
    cores = {"bom": (15, 138, 60), "ruim": (197, 48, 48), "neutro": (100, 116, 139)}
    largura, gap, y0 = (180 - 4 * 3) / 5, 3, pdf.get_y()
    for i, (rotulo, valor, (txt_delta, tom)) in enumerate(cartoes):
        x = 15 + i * (largura + gap)
        pdf.set_fill_color(244, 247, 251)
        pdf.set_draw_color(226, 232, 240)
        pdf.rect(x, y0, largura, 23, style="DF", round_corners=True, corner_radius=2)
        pdf.set_xy(x + 3, y0 + 3)
        pdf.set_font("DejaVu", "", 7)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(largura - 6, 4, rotulo)
        pdf.set_xy(x + 3, y0 + 8)
        pdf.set_font("DejaVu", "B", 14)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(largura - 6, 7, valor)
        if txt_delta:
            pdf.set_xy(x + 3, y0 + 16)
            pdf.set_font("DejaVu", "", 6.5)
            pdf.set_text_color(*cores[tom])
            pdf.cell(largura - 6, 4, f"{txt_delta} vs anterior")
    pdf.set_y(y0 + 27)

    # Destaques
    pdf.titulo_secao("Destaques")
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(30, 41, 59)
    for item in _destaques(df, ant):
        pdf.set_x(17)
        pdf.multi_cell(176, 5, f"•  {item}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    # Gráficos da página 1
    pdf.titulo_secao("Tendência")
    semanal = _semanal(df, ini, fim)
    if len(semanal) >= 2:
        pdf.image(_grafico_semanal(semanal), x=15, w=180)
    pdf.image(_grafico_sla(df), x=15, w=180)

    # Página 2
    pdf.add_page()
    pdf.titulo_secao("Categorias com mais chamados")
    pdf.tabela(["Categoria", "Chamados", "% do total", "Resolução mediana", "SLA"],
               _ranking(df, "categoria"), (70, 22, 24, 36, 28))
    pdf.titulo_secao("Setores com mais chamados")
    pdf.tabela(["Setor", "Chamados", "% do total", "Resolução mediana", "SLA"],
               _ranking(df, "setor"), (82, 20, 22, 32, 24))

    pdf.titulo_secao("Previsão de demanda")
    res = previsao.prever(base)
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(30, 41, 59)
    if res is None:
        pdf.multi_cell(0, 5, "Histórico insuficiente para prever com esses filtros (mínimo de 11 semanas).",
                       new_x="LMARGIN", new_y="NEXT")
    else:
        prox, mes = res.previsao.iloc[0], res.previsao.head(4)
        total4 = mes["previsao"].sum()
        margem4 = (((mes["lim_sup"] - mes["previsao"]) ** 2).sum()) ** 0.5
        pdf.multi_cell(0, 5, f"Próxima semana ({prox['inicio_semana']:%d/%m}): {prox['previsao']:.0f} chamados "
                             f"(entre {prox['lim_inf']:.0f} e {prox['lim_sup']:.0f}). Próximas 4 semanas: {total4:.0f} "
                             f"chamados (entre {max(total4 - margem4, 0):.0f} e {total4 + margem4:.0f}). "
                             f"Erro médio do modelo: ±{fmt(res.erro_medio)} chamados por semana.",
                       new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        pdf.image(_grafico_previsao(res), x=15, w=180)

    pdf.titulo_secao("Qualidade dos dados")
    q = qualidade[qualidade["codigo"].isin(df["codigo"])]["problema"].value_counts()
    if len(q):
        pdf.tabela(["Problema encontrado", "Chamados", "% do período"],
                   [[DESCRICOES.get(p, p), str(n), f"{n / len(df):.0%}"] for p, n in q.items()], (120, 30, 30))
    else:
        pdf.multi_cell(0, 5, "Nenhum problema encontrado nos chamados filtrados.", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
