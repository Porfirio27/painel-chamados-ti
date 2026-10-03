"""Visual do painel: CSS, cabeçalho, cartões de indicador e cartões de conteúdo."""
import html
from itertools import count

import streamlit as st

CSS = """
<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Material+Symbols+Rounded:opsz,wght,FILL@24,500,1&display=swap");
:root {
  --bg: #f4f6fa; --card: #ffffff; --borda: #e6e9f0; --tinta: #0f172a; --tinta-2: #475569;
  --muda: #64748b; --azul: #2a78d6; --azul-escuro: #1c5cab; --verde: #0f8a3c; --vermelho: #c53030;
}
html, body, [class*="css"], .stApp, button, input, textarea { font-family: "Inter", system-ui, sans-serif !important; }
.stApp { background: var(--bg); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"], [data-testid="stDecoration"], footer, #MainMenu { display: none !important; }
.block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1440px; }

/* Cabeçalho */
.hero { display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap;
  background: linear-gradient(120deg, #0d366b 0%, #1c5cab 55%, #2a78d6 100%);
  border-radius: 20px; padding: 26px 30px; margin-bottom: 18px; color: #fff;
  box-shadow: 0 10px 30px -12px rgba(13, 54, 107, .45); }
.hero .eyebrow { font-size: 12px; letter-spacing: .08em; text-transform: uppercase; opacity: .75; font-weight: 600; }
.hero h1 { font-size: 30px; font-weight: 700; margin: 4px 0 2px; color: #fff; padding: 0; letter-spacing: -.02em; }
.hero p { margin: 0; opacity: .85; font-size: 14px; }
.hero .chip { display: inline-flex; align-items: center; gap: 8px; background: rgba(255,255,255,.14);
  border: 1px solid rgba(255,255,255,.22); padding: 8px 14px; border-radius: 999px; font-size: 13px; font-weight: 500;
  backdrop-filter: blur(6px); }
.hero .ponto { width: 8px; height: 8px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 0 3px rgba(74,222,128,.25); }

/* Cartões de conteúdo (st.container com key "card_*") */
[class*="st-key-card_"] { background: var(--card); border: 1px solid var(--borda) !important; border-radius: 16px !important;
  box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 4px 14px -6px rgba(15,23,42,.08); padding: 6px 8px; }
[class*="st-key-filtros"] { background: var(--card); border: 1px solid var(--borda) !important; border-radius: 16px !important;
  padding: 4px 10px 8px; margin-bottom: 4px; box-shadow: 0 1px 2px rgba(15,23,42,.04); }
[class*="st-key-filtros"] label p { font-size: 12px !important; font-weight: 600; color: var(--muda); text-transform: uppercase; letter-spacing: .04em; }

/* Indicadores */
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(165px, 1fr)); gap: 14px; margin: 14px 0 18px; }
.kpi { background: var(--card); border: 1px solid var(--borda); border-radius: 16px; padding: 16px 18px;
  box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 4px 14px -6px rgba(15,23,42,.08); transition: transform .15s, box-shadow .15s; }
.kpi:hover { transform: translateY(-2px); box-shadow: 0 10px 24px -10px rgba(15,23,42,.18); }
.kpi .topo { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.kpi .icone { width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center; background: #e8f1fc; color: var(--azul); }
.kpi .icone span { font-family: "Material Symbols Rounded"; font-size: 20px; line-height: 1; font-variation-settings: "FILL" 1; }
.kpi .rotulo { font-size: 13px; color: var(--muda); font-weight: 500; line-height: 1.25; }
.kpi .valor { font-size: 28px; font-weight: 700; color: var(--tinta); letter-spacing: -.02em; line-height: 1.1; }
.kpi .valor small { font-size: 15px; font-weight: 600; color: var(--tinta-2); margin-left: 2px; }
.kpi .rodape { margin-top: 8px; font-size: 12px; color: var(--muda); display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.delta { font-weight: 600; padding: 2px 8px; border-radius: 999px; font-size: 12px; }
.delta.bom { color: var(--verde); background: #e7f6ec; }
.delta.ruim { color: var(--vermelho); background: #fdecec; }
.delta.neutro { color: var(--tinta-2); background: #eef1f5; }
.barra { height: 6px; border-radius: 999px; background: #e8f1fc; margin-top: 10px; overflow: hidden; }
.barra > div { height: 100%; border-radius: 999px; background: var(--azul); }

/* Abas em pílula */
[role="tablist"] { gap: 6px; background: #e9edf3; padding: 5px; border-radius: 12px; width: fit-content;
  max-width: 100%; overflow-x: auto; border: none !important; box-shadow: none !important; }
[data-testid="stTab"] { height: 36px; padding: 0 16px !important; border-radius: 9px; background: transparent;
  display: flex; align-items: center; transition: background .15s; }
[data-testid="stTab"]:hover { background: rgba(255,255,255,.6); }
[data-testid="stTab"] p { font-weight: 600; font-size: 14px; color: var(--tinta-2); margin: 0; }
[data-testid="stTab"][aria-selected="true"] { background: var(--card); box-shadow: 0 1px 3px rgba(15,23,42,.14); }
[data-testid="stTab"][aria-selected="true"] p { color: var(--azul-escuro); }
.react-aria-SelectionIndicator { display: none !important; }
[role="tabpanel"] { padding-top: 14px; }
.secao { font-size: 13px; font-weight: 700; color: var(--muda); text-transform: uppercase; letter-spacing: .06em; margin: 10px 2px 8px; }
.nota { font-size: 13px; color: var(--muda); margin: 2px 4px 10px; }
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
.stDownloadButton button, .stButton button { border-radius: 10px; font-weight: 600; }
</style>
"""

_cards = count()


def aplicar() -> None:
    global _cards
    _cards = count()
    # st.html (e não st.markdown) para o CSS não passar pelo interpretador de Markdown
    st.html(CSS)


def cabecalho(titulo: str, subtitulo: str, atualizado: str) -> None:
    st.html(f"""
<div class="hero">
  <div><div class="eyebrow">Central de chamados · TI</div><h1>{titulo}</h1><p>{subtitulo}</p></div>
  <div class="chip"><span class="ponto"></span>{atualizado}</div>
</div>""")


def card():
    """Contêiner branco com borda arredondada para um gráfico ou tabela."""
    return st.container(border=True, key=f"card_{next(_cards)}")


def secao(texto: str) -> None:
    st.markdown(f'<div class="secao">{texto}</div>', unsafe_allow_html=True)


def kpi(icone: str, rotulo: str, valor: str, unidade: str = "", delta: str | None = None,
        tom: str = "neutro", nota: str | None = None, ajuda: str = "", barra: float | None = None) -> str:
    """HTML de um cartão de indicador. tom: 'bom', 'ruim' ou 'neutro' (cor do delta)."""
    rodape = ""
    if delta or nota:
        rodape = '<div class="rodape">' + (f'<span class="delta {tom}">{delta}</span>' if delta else "") + \
                 (f"<span>{nota}</span>" if nota else "") + "</div>"
    barra_html = f'<div class="barra"><div style="width:{max(0, min(barra, 100)):.0f}%"></div></div>' \
        if barra is not None else ""
    return f"""<div class="kpi" title="{html.escape(ajuda)}">
  <div class="topo"><div class="icone"><span>{icone}</span></div><div class="rotulo">{rotulo}</div></div>
  <div class="valor">{valor}<small>{unidade}</small></div>{barra_html}{rodape}
</div>"""


def kpis(cartoes: list[str]) -> None:
    st.html(f'<div class="kpis">{"".join(cartoes)}</div>')


def delta(atual: float, anterior: float, casas: int = 0, sufixo: str = "", menor_melhor: bool = False,
          neutro: bool = False, pct: bool = False) -> tuple[str | None, str]:
    """Texto e tom do delta vs período anterior."""
    if anterior is None or atual is None or anterior != anterior or atual != atual:
        return None, "neutro"
    diff = (atual / anterior - 1) * 100 if pct and anterior else atual - anterior
    if abs(diff) < 10 ** -casas / 2:
        return "= estável", "neutro"
    seta = "▲" if diff > 0 else "▼"
    texto = f"{seta} {abs(diff):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".") + \
            ("%" if pct else sufixo)
    if neutro:
        return texto, "neutro"
    melhorou = (diff < 0) if menor_melhor else (diff > 0)
    return texto, "bom" if melhorou else "ruim"
