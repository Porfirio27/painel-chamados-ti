"""Visual do painel: CSS (tema claro e escuro), cabeçalho, cartões de indicador e de conteúdo."""
import html
from itertools import count

import streamlit as st

# Cores de cada tema, usadas como variáveis CSS
TOKENS = {
    "claro": {
        "bg": "#f4f6fa", "card": "#ffffff", "borda": "#e6e9f0", "tinta": "#0f172a", "tinta-2": "#475569",
        "muda": "#64748b", "azul": "#2a78d6", "azul-texto": "#1c5cab", "azul-fundo": "#e8f1fc",
        "verde": "#0f8a3c", "verde-fundo": "#e7f6ec", "vermelho": "#c53030", "vermelho-fundo": "#fdecec",
        "neutro-fundo": "#eef1f5", "abas": "#e9edf3", "aba-hover": "rgba(255,255,255,.6)",
        "campo": "#eef2f8", "sombra": "rgba(15,23,42,.08)",
        "hero": "linear-gradient(120deg, #0d366b 0%, #1c5cab 40%, #2a78d6 70%, #1c5cab 100%)",
        "vidro": "rgba(255,255,255,.72)", "vidro-borda": "rgba(255,255,255,.9)",
        "mancha-1": "rgba(42,120,214,.38)", "mancha-2": "rgba(34,184,230,.30)", "mancha-3": "rgba(124,92,246,.24)",
        "grade": "rgba(15,23,42,.045)",
        "botao": "linear-gradient(135deg, #2a78d6 0%, #3b82f6 50%, #22b8e6 100%)", "botao-sombra": "rgba(42,120,214,.45)",
    },
    "escuro": {
        "bg": "#0f1623", "card": "#1b2433", "borda": "#2a3546", "tinta": "#e8edf5", "tinta-2": "#c3cddb",
        "muda": "#94a3b8", "azul": "#3987e5", "azul-texto": "#8fbcf5", "azul-fundo": "rgba(57,135,229,.16)",
        "verde": "#4ade80", "verde-fundo": "rgba(74,222,128,.12)", "vermelho": "#f87171",
        "vermelho-fundo": "rgba(248,113,113,.12)", "neutro-fundo": "rgba(148,163,184,.14)",
        "abas": "#222d3e", "aba-hover": "rgba(255,255,255,.06)", "campo": "#232e40", "sombra": "rgba(0,0,0,.35)",
        "hero": "linear-gradient(120deg, #0a2346 0%, #164b8f 40%, #2366bb 70%, #164b8f 100%)",
        "vidro": "rgba(22,30,45,.68)", "vidro-borda": "rgba(255,255,255,.07)",
        "mancha-1": "rgba(57,135,229,.50)", "mancha-2": "rgba(34,211,238,.24)", "mancha-3": "rgba(139,92,246,.38)",
        "grade": "rgba(255,255,255,.035)",
        "botao": "linear-gradient(135deg, #2a78d6 0%, #3b82f6 50%, #22b8e6 100%)", "botao-sombra": "rgba(59,130,246,.45)",
    },
}

CSS = """
<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Material+Symbols+Rounded:opsz,wght,FILL@24,500,1&display=swap");
html, body, [class*="css"], .stApp, button, input, textarea { font-family: "Inter", system-ui, sans-serif !important; }
.stApp { background: var(--bg); color: var(--tinta); }
/* Fundo animado: manchas de cor desfocadas que se movem devagar + grade sutil */
.stApp::before { content: ""; position: fixed; inset: -25%; z-index: 0; pointer-events: none; will-change: transform;
  background: radial-gradient(36% 42% at 18% 22%, var(--mancha-1), transparent 70%),
              radial-gradient(30% 36% at 82% 18%, var(--mancha-2), transparent 70%),
              radial-gradient(40% 44% at 70% 82%, var(--mancha-3), transparent 70%),
              radial-gradient(28% 30% at 22% 80%, var(--mancha-2), transparent 70%);
  filter: blur(40px); animation: flutuar 26s ease-in-out infinite alternate; }
.stApp::after { content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background-image: linear-gradient(var(--grade) 1px, transparent 1px), linear-gradient(90deg, var(--grade) 1px, transparent 1px);
  background-size: 44px 44px; mask-image: radial-gradient(ellipse at 50% 30%, #000 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse at 50% 30%, #000 30%, transparent 80%); }
@keyframes flutuar {
  0%   { transform: translate3d(-4%, -3%, 0) rotate(0deg) scale(1); }
  50%  { transform: translate3d(3%, 2%, 0) rotate(6deg) scale(1.08); }
  100% { transform: translate3d(5%, -2%, 0) rotate(-4deg) scale(1.03); } }
@keyframes brilho { 0% { background-position: 0% 50%; } 100% { background-position: 100% 50%; } }
[data-testid="stAppViewContainer"], [data-testid="stMain"] { background: transparent !important; position: relative; z-index: 1; }
@media (prefers-reduced-motion: reduce) { .stApp::before, .hero { animation: none !important; } }
/* Barra do topo transparente e "vazada" (não bloqueia cliques), mas o botão de reabrir o menu continua */
[data-testid="stHeader"] { background: transparent; pointer-events: none; }
[data-testid="stHeader"] * { pointer-events: none; }
[data-testid="stExpandSidebarButton"], [data-testid="stExpandSidebarButton"] * { pointer-events: auto !important; }
/* Menu lateral */
[data-testid="stSidebar"] { background: var(--vidro); border-right: 1px solid var(--vidro-borda);
  backdrop-filter: blur(18px) saturate(150%); -webkit-backdrop-filter: blur(18px) saturate(150%); }
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top: 8px; }
.marca { display: flex; align-items: center; gap: 12px; padding: 0 6px 18px; border-bottom: 1px solid var(--borda); }
.marca .logo { width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center; background: var(--hero);
  color: #fff; font-family: "Material Symbols Rounded"; font-size: 22px; font-variation-settings: "FILL" 1; }
.marca b { display: block; font-size: 15px; color: var(--tinta); }
.marca small { display: block; font-size: 12px; color: var(--muda); }
.menu-titulo { font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muda);
  margin: 16px 8px 4px; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] { gap: 4px; width: 100%; }
[data-testid="stSidebar"] [data-testid="stElementContainer"], [data-testid="stSidebar"] [data-testid="stRadio"],
[data-testid="stSidebar"] [data-testid="stRadioGroup"] { width: 100% !important; }
[data-testid="stExpandSidebarButton"] { background: var(--card); border: 1px solid var(--borda); border-radius: 10px; color: var(--tinta) !important; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div { display: block !important; width: 100% !important; }
[data-testid="stRadioOption"] { display: flex !important; width: 100% !important; box-sizing: border-box; padding: 10px 12px; border-radius: 10px; cursor: pointer; transition: background .15s; }
[data-testid="stRadioOption"] > div > div:first-child { display: none; }  /* esconde a bolinha do rádio */
[data-testid="stRadioOption"] p { font-size: 14px; font-weight: 600; color: var(--tinta-2) !important; }
[data-testid="stRadioOption"] p span[role="img"] { margin-right: 6px; color: var(--muda); }
[data-testid="stRadioOption"] { transition: background .2s, transform .2s; }
[data-testid="stRadioOption"]:hover { background: var(--neutro-fundo); transform: translateX(2px); }
[data-testid="stRadioOption"][data-selected="true"] { background: var(--botao); box-shadow: 0 8px 20px -10px var(--botao-sombra); }
[data-testid="stRadioOption"][data-selected="true"] p, [data-testid="stRadioOption"][data-selected="true"] p span[role="img"] {
  color: #fff !important; }
/* Seletor de tema: só ícones, em pílula */
[class*="st-key-tema_seletor"] [data-testid="stButtonGroup"] { padding: 0 6px; }
[class*="st-key-tema_seletor"] [role="radiogroup"] { display: inline-flex; gap: 4px; padding: 4px; border-radius: 999px;
  background: var(--neutro-fundo); border: 1px solid var(--borda); }
[class*="st-key-tema_seletor"] button { width: 44px; height: 36px; min-height: 36px; border-radius: 999px !important; border: none !important;
  background: transparent !important; color: var(--muda) !important; transition: background .2s, color .2s, box-shadow .2s; }
[class*="st-key-tema_seletor"] button:hover { color: var(--tinta) !important; }
[class*="st-key-tema_seletor"] button [data-testid="stIconMaterial"] { font-size: 20px; }
[class*="st-key-tema_seletor"] button[aria-checked="true"] { background: var(--botao) !important; color: #fff !important;
  box-shadow: 0 6px 16px -6px var(--botao-sombra); }
@media (max-width: 640px) { .block-container { padding-top: 3.4rem; } }  /* espaço para o botão do menu */
/* O script dos ícones (iframe de altura 0) não ocupa espaço no layout */
[data-testid="stElementContainer"]:has(> iframe[data-testid="stIFrame"][height="0"]) {
  position: absolute; width: 0; height: 0; overflow: hidden; }
.titulo-pagina { font-size: 22px; font-weight: 700; color: var(--tinta); letter-spacing: -.01em; margin: 4px 2px 6px; }
/* Esconde menu e deploy do Streamlit, mas mantém a barra (ela guarda o botão de reabrir o menu lateral) */
[data-testid="stMainMenu"], [data-testid="stAppDeployButton"], [data-testid="stToolbarActions"],
[data-testid="stDecoration"], footer, #MainMenu { display: none !important; }
.block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1440px; }
/* Cabeçalho */
.hero { display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap;
  background: var(--hero); background-size: 220% 100%; animation: brilho 14s ease-in-out infinite alternate;
  border-radius: 22px; padding: 26px 30px; margin-bottom: 18px; color: #fff;
  box-shadow: 0 18px 40px -18px rgba(13, 54, 107, .6), inset 0 1px 0 rgba(255,255,255,.18); }
.hero .eyebrow { font-size: 12px; letter-spacing: .08em; text-transform: uppercase; opacity: .75; font-weight: 600; }
.hero h1 { font-size: 30px; font-weight: 700; margin: 4px 0 2px; color: #fff; padding: 0; letter-spacing: -.02em; }
.hero p { margin: 0; opacity: .85; font-size: 14px; }
.hero .chip { display: inline-flex; align-items: center; gap: 8px; background: rgba(255,255,255,.14);
  border: 1px solid rgba(255,255,255,.22); padding: 8px 14px; border-radius: 999px; font-size: 13px; font-weight: 500;
  backdrop-filter: blur(6px); }
.hero .ponto { width: 8px; height: 8px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 0 3px rgba(74,222,128,.25); }
/* Cartões de vidro (st.container com key "card_*"), filtros e indicadores */
[class*="st-key-card_"], [class*="st-key-filtros"], .kpi {
  background: var(--vidro) !important; border: 1px solid var(--vidro-borda) !important;
  backdrop-filter: blur(16px) saturate(150%); -webkit-backdrop-filter: blur(16px) saturate(150%);
  box-shadow: 0 1px 2px var(--sombra), 0 12px 32px -16px var(--sombra) !important; }
[class*="st-key-card_"] { border-radius: 18px !important; padding: 6px 8px; }
[class*="st-key-filtros"] { border-radius: 18px !important; padding: 4px 10px 8px; margin-bottom: 4px; }
[class*="st-key-filtros"] label p { font-size: 12px !important; font-weight: 600; color: var(--muda); text-transform: uppercase; letter-spacing: .04em; }
/* Indicadores */
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(165px, 1fr)); gap: 14px; margin: 14px 0 18px; }
.kpi { border-radius: 18px; padding: 16px 18px; transition: transform .2s, box-shadow .2s; }
.kpi:hover { transform: translateY(-3px); box-shadow: 0 18px 36px -18px var(--botao-sombra) !important; }
.kpi .topo { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.kpi .icone { width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center; background: var(--azul-fundo); color: var(--azul); }
.kpi .icone span { font-family: "Material Symbols Rounded"; font-size: 20px; line-height: 1; font-variation-settings: "FILL" 1; }
.kpi .rotulo { font-size: 13px; color: var(--muda); font-weight: 500; line-height: 1.25; }
.kpi .valor { font-size: 28px; font-weight: 700; color: var(--tinta); letter-spacing: -.02em; line-height: 1.1; }
.kpi .valor small { font-size: 15px; font-weight: 600; color: var(--tinta-2); margin-left: 2px; }
.kpi .rodape { margin-top: 8px; font-size: 12px; color: var(--muda); display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.delta { font-weight: 600; padding: 2px 8px; border-radius: 999px; font-size: 12px; }
.delta.bom { color: var(--verde); background: var(--verde-fundo); }
.delta.ruim { color: var(--vermelho); background: var(--vermelho-fundo); }
.delta.neutro { color: var(--tinta-2); background: var(--neutro-fundo); }
.barra { height: 6px; border-radius: 999px; background: var(--azul-fundo); margin-top: 10px; overflow: hidden; }
.barra > div { height: 100%; border-radius: 999px; background: var(--azul); }
/* Abas em pílula */
[role="tablist"] { gap: 6px; background: var(--abas); padding: 5px; border-radius: 12px; width: fit-content;
  max-width: 100%; overflow-x: auto; border: none !important; box-shadow: none !important; }
[data-testid="stTab"] { height: 36px; padding: 0 16px !important; border-radius: 9px; background: transparent;
  display: flex; align-items: center; transition: background .15s; }
[data-testid="stTab"]:hover { background: var(--aba-hover); }
[data-testid="stTab"] p { font-weight: 600; font-size: 14px; color: var(--tinta-2); margin: 0; }
[data-testid="stTab"][aria-selected="true"] { background: var(--card); box-shadow: 0 1px 3px var(--sombra); }
[data-testid="stTab"][aria-selected="true"] p { color: var(--azul-texto); }
.react-aria-SelectionIndicator { display: none !important; }
[role="tabpanel"] { padding-top: 14px; }
.secao { font-size: 13px; font-weight: 700; color: var(--muda); text-transform: uppercase; letter-spacing: .06em; margin: 10px 2px 8px; }
.nota { font-size: 13px; color: var(--muda); margin: 2px 4px 10px; }
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
/* Botões: degradê, sombra colorida e elevação ao passar o mouse */
.stButton button, .stDownloadButton button {
  background: var(--botao) !important; background-size: 160% 100% !important; color: #fff !important; border: none !important;
  border-radius: 12px !important; font-weight: 600 !important; letter-spacing: .01em;
  box-shadow: 0 8px 20px -10px var(--botao-sombra), inset 0 1px 0 rgba(255,255,255,.25) !important;
  transition: transform .18s, box-shadow .18s, background-position .4s !important; }
.stButton button p, .stDownloadButton button p, .stButton button span, .stDownloadButton button span { color: #fff !important; }
.stButton button:hover, .stDownloadButton button:hover { transform: translateY(-2px); background-position: 100% 0 !important;
  box-shadow: 0 14px 28px -12px var(--botao-sombra), inset 0 1px 0 rgba(255,255,255,.25) !important; }
.stButton button:active, .stDownloadButton button:active { transform: translateY(0) scale(.98); }
[data-testid="stExpander"] details { border-radius: 14px !important; background: var(--vidro); border-color: var(--vidro-borda) !important; }
</style>
"""

# No escuro, os componentes do Streamlit (que seguem o tema claro do config.toml) recebem cores próprias
CSS_ESCURO = """
<style>
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
[data-testid="stCaptionContainer"], [data-testid="stWidgetLabel"] p, [data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p, [data-testid="stHeading"] * { color: var(--tinta) !important; }
[data-testid="stMultiSelect"] > div[data-rac], [data-testid="stMultiSelect"] > div[data-rac] > div,
[data-testid="stDateInputField"], [data-testid="stTextInput"] input {
  background: var(--campo) !important; color: var(--tinta) !important; border-color: var(--borda) !important; }
[data-testid="stMultiSelect"] input, [data-testid="stDateInputField"] [role="spinbutton"],
[data-testid="stDateInputField"] span { color: var(--tinta) !important; }
[data-testid="stMultiSelect"] input::placeholder { color: var(--muda) !important; }
[data-testid="stMultiSelect"] svg, [data-testid="stDateInput"] svg { color: var(--muda) !important; }
[data-testid="stMultiSelectTagsContainer"] > div:not(:has(input)) { background: var(--azul-fundo) !important; color: var(--azul-texto) !important; }
[role="listbox"], [role="dialog"], [role="dialog"] [role="grid"] {
  background: var(--card) !important; color: var(--tinta) !important; border-color: var(--borda) !important; }
[data-testid="stDateInputCalendar"] { background: var(--card) !important; border: 1px solid var(--borda) !important; }
[data-testid="stDateInputCalendar"] *, [data-testid="stDateInputCalendar"] button { color: var(--tinta) !important; }
[data-testid="stDateInputCalendar"] [aria-disabled="true"], [data-testid="stDateInputCalendar"] [data-outside-month] { opacity: .35; }
[role="option"], [role="option"] *, [role="dialog"] *, [role="gridcell"] * { color: var(--tinta) !important; }
[role="option"]:hover, [role="option"][data-focused], [role="option"][aria-selected="true"] { background: var(--campo) !important; }
[role="gridcell"] [data-selected], [role="gridcell"] [aria-selected="true"] { background: var(--azul) !important; color: #fff !important; }
[data-testid="stAlert"] { background: var(--campo) !important; color: var(--tinta) !important; }
/* As tabelas do Streamlit são desenhadas em canvas: inverter as cores é o jeito de deixá-las escuras */
[data-testid="stDataFrame"] { filter: invert(.88) hue-rotate(180deg); }
</style>
"""

_cards = count()


def aplicar(tema: str = "claro") -> None:
    global _cards
    _cards = count()
    variaveis = ";".join(f"--{k}:{v}" for k, v in TOKENS[tema].items())
    # st.html (e não st.markdown) para o CSS não passar pelo interpretador de Markdown
    st.html(f"<style>:root{{{variaveis}}}</style>" + CSS + (CSS_ESCURO if tema == "escuro" else ""))


def cabecalho(titulo: str, subtitulo: str, atualizado: str) -> None:
    st.html(f"""
<div class="hero">
  <div><div class="eyebrow">Central de chamados · TI</div><h1>{titulo}</h1><p>{subtitulo}</p></div>
  <div class="chip"><span class="ponto"></span>{atualizado}</div>
</div>""")


def titulo_pagina(texto: str) -> None:
    st.html(f'<div class="titulo-pagina">{texto}</div>')


def card():
    """Contêiner com borda arredondada para um gráfico ou tabela."""
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
