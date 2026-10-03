"""Visual do painel no padrão do sistema de chamados: tema escuro, barra superior e cartões."""
import html
from itertools import count

import streamlit as st

# Cores dos números nos cartões (mesmo significado do sistema de chamados)
CORES = {
    "branco": "#f3f4f6", "amarelo": "#facc15", "roxo": "#a855f7", "verde": "#22c55e",
    "laranja": "#f97316", "vermelho": "#ef4444", "azul": "#3b82f6", "rosa": "#fb7185",
}

CSS = """
<style>
:root {
  --bg: #111827; --barra: #1f2937; --card: #1f2937; --card-2: #263244; --borda: #2d3a4d;
  --tinta: #f3f4f6; --tinta-2: #d1d5db; --muda: #9ca3af; --azul: #3b82f6;
}
html, body, .stApp, button, input, textarea, [data-testid="stMarkdownContainer"] {
  font-family: "Segoe UI", "Nunito", system-ui, -apple-system, sans-serif !important; }
.stApp { background: var(--bg); color: var(--tinta); }
[data-testid="stHeader"] { display: none; }
[data-testid="stToolbar"], [data-testid="stDecoration"], footer, #MainMenu { display: none !important; }
.block-container { padding-top: 0 !important; padding-bottom: 3rem; max-width: 1560px; }
/* Barra superior */
.topbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap;
  background: var(--barra); margin: 0 calc(50% - 50vw); padding: 14px max(24px, calc(50vw - 760px));
  border-bottom: 1px solid #263244; }
.topbar .marca { font-size: 20px; font-weight: 700; letter-spacing: .02em; color: #fff; }
.topbar .direita { display: flex; align-items: center; gap: 14px; color: var(--muda); font-size: 14px; }
.topbar .sino { width: 38px; height: 38px; border-radius: 10px; display: grid; place-items: center;
  border: 1px solid #a16207; background: rgba(250, 204, 21, .08); color: #facc15; font-size: 18px; }
.titulo-pagina { font-size: 38px; font-weight: 700; color: #fff; margin: 34px 0 22px; letter-spacing: -.01em; }
/* Cartões de conteúdo (st.container com key "card_*") */
[class*="st-key-card_"] { background: var(--card); border: none !important; border-radius: 10px !important; padding: 8px 10px; }
[class*="st-key-filtros"] { background: var(--card); border-radius: 10px !important; padding: 6px 14px 12px; margin-bottom: 22px; }
[class*="st-key-filtros"] label p { font-size: 14px !important; color: var(--muda) !important; }
/* Indicadores */
.kpis { display: grid; gap: 20px; margin: 0 0 20px; }
.kpi { background: var(--card); border-radius: 10px; padding: 26px 30px; min-height: 132px; }
.kpis.c5 .kpi { min-height: 180px; }
.kpi .rotulo { font-size: 17px; color: var(--tinta-2); font-weight: 400; margin-bottom: 4px; }
.kpi .valor { font-size: 38px; font-weight: 700; line-height: 1.15; letter-spacing: -.01em; }
.kpi .valor small { font-size: 18px; font-weight: 600; margin-left: 2px; opacity: .85; }
.kpi .nota { font-size: 14px; color: var(--tinta-2); margin-top: 12px; line-height: 1.45; }
.kpi .delta { display: inline-block; margin-top: 10px; font-size: 13px; font-weight: 600; padding: 2px 10px; border-radius: 999px; }
.delta.bom { color: #4ade80; background: rgba(34,197,94,.12); }
.delta.ruim { color: #f87171; background: rgba(239,68,68,.12); }
.delta.neutro { color: var(--tinta-2); background: rgba(156,163,175,.14); }
.kpi .barra { height: 6px; border-radius: 999px; background: #374151; margin-top: 12px; overflow: hidden; max-width: 220px; }
.kpi .barra > div { height: 100%; border-radius: 999px; }
@media (max-width: 1100px) { .kpis { grid-template-columns: repeat(2, 1fr) !important; } }
@media (max-width: 520px) { .kpis { grid-template-columns: 1fr !important; } .titulo-pagina { font-size: 30px; } }
/* Abas no estilo do menu: texto cinza, ativa em branco sublinhada */
[role="tablist"] { gap: 28px; border-bottom: 1px solid #263244 !important; box-shadow: none !important;
  overflow-x: auto; margin-bottom: 6px; }
[data-testid="stTab"] { padding: 0 2px 10px !important; background: transparent !important; border-bottom: 3px solid transparent; }
[data-testid="stTab"] p { font-size: 17px; font-weight: 600; color: var(--muda); margin: 0; }
[data-testid="stTab"]:hover p { color: var(--tinta-2); }
[data-testid="stTab"][aria-selected="true"] { border-bottom-color: #fff; }
[data-testid="stTab"][aria-selected="true"] p { color: #fff; }
.react-aria-SelectionIndicator { display: none !important; }
[role="tabpanel"] { padding-top: 18px; }
.secao { font-size: 15px; font-weight: 600; color: var(--muda); margin: 14px 2px 10px; }
.nota-pagina { font-size: 14px; color: var(--muda); margin: 2px 2px 12px; }
[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
.stDownloadButton button, .stButton button { border-radius: 8px; font-weight: 600; }
[data-testid="stExpander"] details { background: var(--card); border: none; border-radius: 10px; }
</style>
"""

_cards = count()


def aplicar() -> None:
    global _cards
    _cards = count()
    # st.html (e não st.markdown) para o CSS não passar pelo interpretador de Markdown
    st.html(CSS)


def barra_superior(marca: str, direita: str) -> None:
    st.html(f"""
<div class="topbar">
  <div class="marca">{marca}</div>
  <div class="direita"><span>{direita}</span></div>
</div>""")


def titulo(texto: str) -> None:
    st.html(f'<div class="titulo-pagina">{texto}</div>')


def card():
    """Contêiner escuro com cantos arredondados para um gráfico ou tabela."""
    return st.container(border=True, key=f"card_{next(_cards)}")


def secao(texto: str) -> None:
    st.html(f'<div class="secao">{texto}</div>')


def nota(texto: str) -> None:
    st.html(f'<div class="nota-pagina">{texto}</div>')


def kpi(rotulo: str, valor: str, unidade: str = "", cor: str = "branco", delta: str | None = None,
        tom: str = "neutro", nota: str | None = None, ajuda: str = "", barra: float | None = None) -> str:
    """HTML de um cartão de indicador. cor: chave de CORES; tom do delta: 'bom', 'ruim' ou 'neutro'."""
    c = CORES.get(cor, cor)
    barra_html = (f'<div class="barra"><div style="width:{max(0, min(barra, 100)):.0f}%;background:{c}"></div></div>'
                  if barra is not None else "")
    delta_html = f'<div><span class="delta {tom}">{delta}</span></div>' if delta else ""
    nota_html = f'<div class="nota">{nota}</div>' if nota else ""
    return (f'<div class="kpi" title="{html.escape(ajuda)}"><div class="rotulo">{rotulo}</div>'
            f'<div class="valor" style="color:{c}">{valor}<small>{unidade}</small></div>'
            f"{barra_html}{delta_html}{nota_html}</div>")


def kpis(cartoes: list[str], colunas: int | None = None) -> None:
    n = colunas or len(cartoes)
    st.html(f'<div class="kpis c{n}" style="grid-template-columns:repeat({n},1fr)">{"".join(cartoes)}</div>')


def delta(atual: float, anterior: float, casas: int = 0, sufixo: str = "", menor_melhor: bool = False,
          neutro: bool = False, pct: bool = False) -> tuple[str | None, str]:
    """Texto e tom do delta vs período anterior."""
    if anterior is None or atual is None or anterior != anterior or atual != atual:
        return None, "neutro"
    diff = (atual / anterior - 1) * 100 if pct and anterior else atual - anterior
    if abs(diff) < 10 ** -casas / 2:
        return "= estável vs anterior", "neutro"
    seta = "▲" if diff > 0 else "▼"
    texto = f"{seta} {abs(diff):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".") + \
            ("%" if pct else sufixo) + " vs anterior"
    if neutro:
        return texto, "neutro"
    melhorou = (diff < 0) if menor_melhor else (diff > 0)
    return texto, "bom" if melhorou else "ruim"
