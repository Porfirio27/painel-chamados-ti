"""Painel de chamados de TI.

Uso:
    streamlit run app.py

Os dados vêm direto da API (chave em API_KEY no .env ou nos secrets do Streamlit Cloud)
e ficam em cache por 1 hora.
"""
import pandas as pd
import streamlit as st

from src import config, estilo, extract, graficos as g, previsao, transform

# "auto": menu aberto no computador e recolhido no celular
st.set_page_config(page_title="Chamados de TI", page_icon="📊", layout="wide", initial_sidebar_state="auto")

# Tema claro/escuro: escolha guardada na URL (?tema=escuro) para valer ao recarregar ou compartilhar
TEMAS = {"claro": ":material/light_mode: Claro", "escuro": ":material/dark_mode: Escuro"}
if "tema" not in st.session_state:
    st.session_state.tema = st.query_params.get("tema", "claro") if st.query_params.get("tema") in TEMAS else "claro"
# Menu lateral: página escolhida também fica na URL (?pagina=previsoes)
PAGINAS = {
    "visao": ":material/dashboard: Visão geral",
    "setores": ":material/apartment: Setores e categorias",
    "previsoes": ":material/trending_up: Previsões",
    "dados": ":material/table_rows: Dados",
    "qualidade": ":material/fact_check: Qualidade",
}
if "pagina" not in st.session_state:
    st.session_state.pagina = st.query_params.get("pagina") if st.query_params.get("pagina") in PAGINAS else "visao"

with st.sidebar:
    st.html('<div class="marca"><span class="logo">insights</span>'
            '<div><b>Chamados de TI</b><small>Painel de análise</small></div></div>')
    st.html('<div class="menu-titulo">Menu</div>')
    pagina = st.radio("Página", list(PAGINAS), format_func=PAGINAS.get, key="pagina",
                      label_visibility="collapsed")
    st.html('<div class="menu-titulo">Aparência</div>')
    with st.container(key="tema_seletor"):
        tema = st.segmented_control("Tema", list(TEMAS), format_func=TEMAS.get, key="tema",
                                    label_visibility="collapsed") or "claro"
st.query_params["tema"] = tema
st.query_params["pagina"] = pagina
estilo.aplicar(tema)
g.usar_tema(tema)


@st.cache_data(ttl=3600, show_spinner="Buscando chamados na API...")
def carregar() -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    fato = transform.montar_fato(extract.buscar_chamados())
    return fato, transform.checar_qualidade(fato), pd.Timestamp.now(tz=config.FUSO)


try:
    fato, qualidade, atualizado = carregar()
except Exception as erro:
    st.error(f"Não foi possível buscar os dados da API: {erro}")
    st.stop()

cfg = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]}


def grafico(fig) -> None:
    with estilo.card():
        st.plotly_chart(fig, width="stretch", config=cfg)


# ---------------------------------------------------------------- cabeçalho e filtros
estilo.cabecalho("Chamados de TI", "Volume, tempo de atendimento, SLA e previsão de demanda",
                 f"Atualizado em {atualizado:%d/%m/%Y às %H:%M}")

dmin, dmax = fato["data"].min(), fato["data"].max()
with st.container(key="filtros"):
    f1, f2, f3, f4, f5 = st.columns([2, 2, 2, 1.4, 0.9], vertical_alignment="bottom")
    periodo = f1.date_input("Período", (dmin, dmax), min_value=dmin, max_value=dmax, format="DD/MM/YYYY")
    grupos = f2.multiselect("Grupo de setor", sorted(fato["setor_grupo"].unique()), placeholder="Todos")
    categorias = f3.multiselect("Categoria", sorted(fato["categoria"].unique()), placeholder="Todas")
    prioridades = f4.multiselect("Prioridade", config.ORDEM_PRIORIDADE, placeholder="Todas")
    if f5.button("Atualizar", icon=":material/refresh:", width="stretch", help="Busca os dados mais recentes na API"):
        carregar.clear()
        st.rerun()

# Filtros de dimensão primeiro; o de data depois, para o backlog considerar chamados anteriores
base = fato
if grupos:
    base = base[base["setor_grupo"].isin(grupos)]
if categorias:
    base = base[base["categoria"].isin(categorias)]
if prioridades:
    base = base[base["prioridade"].isin(prioridades)]

ini, fim = (periodo if isinstance(periodo, tuple) and len(periodo) == 2 else (dmin, dmax))
df = base[(base["data"] >= ini) & (base["data"] <= fim)]

if df.empty:
    st.warning("Nenhum chamado com esses filtros.")
    st.stop()

# Período anterior de mesma duração, para comparação
duracao = fim - ini + pd.Timedelta(days=1)
ant = base[(base["data"] >= ini - duracao) & (base["data"] < ini)]


# ---------------------------------------------------------------- indicadores
def medidas(d: pd.DataFrame) -> dict:
    sla = d["sla_resolucao_cumprido"].dropna()
    return {"n": len(d),
            "med": d["tempo_resolucao_h"].median(),
            "util": d["tempo_resolucao_util_h"].median(),
            "sla": sla.mean() * 100 if len(sla) else None}


atual, anterior = medidas(df), (medidas(ant) if len(ant) else {"n": None, "med": None, "util": None, "sla": None})
vs = "vs período anterior" if len(ant) else None


def horas(v) -> str:
    return g.fmt(v) if v == v and v is not None else "–"


d_n, t_n = estilo.delta(atual["n"], anterior["n"], pct=True, neutro=True)
d_med, t_med = estilo.delta(atual["med"], anterior["med"], 1, "h", menor_melhor=True)
d_util, t_util = estilo.delta(atual["util"], anterior["util"], 1, "h", menor_melhor=True)
d_sla, t_sla = estilo.delta(atual["sla"], anterior["sla"], 0, " p.p.")
abertos_agora = int(base["aberto"].sum())

estilo.kpis([
    estilo.kpi("confirmation_number", "Chamados no período", f"{atual['n']:,}".replace(",", "."),
               delta=d_n, tom=t_n, nota=vs, ajuda="Chamados abertos no período selecionado"),
    estilo.kpi("schedule", "Resolução mediana", horas(atual["med"]), "h", d_med, t_med, vs,
               ajuda="Tempo corrido entre abertura e resolução. Metade dos chamados é resolvida em menos tempo."),
    estilo.kpi("work_history", "Resolução em horário útil", horas(atual["util"]), "h", d_util, t_util, vs,
               ajuda=f"Conta só dias úteis das {config.EXPEDIENTE[0]}h às {config.EXPEDIENTE[1]}h."),
    estilo.kpi("verified", "SLA cumprido", g.fmt(atual["sla"], 0) if atual["sla"] is not None else "–", "%",
               d_sla, t_sla, vs, barra=atual["sla"],
               ajuda=f"Meta em horas corridas: {config.SLA_RESOLUCAO_HORAS}. Recalculado — o status da API não é confiável."),
    estilo.kpi("inbox", "Em aberto agora", str(abertos_agora), nota="aguardando resolução",
               ajuda="Chamados ainda não fechados (respeita os filtros de setor, categoria e prioridade)."),
])

# ---------------------------------------------------------------- abas
# ---------------------------------------------------------------- página escolhida no menu
estilo.titulo_pagina(PAGINAS[pagina].split(": ", 1)[1])

if pagina == "visao":
    agg = transform.agregar(base)
    r = df["resolvido_em"].dropna()
    semana_resolucao = (r.dt.normalize() - pd.to_timedelta(r.dt.dayofweek, unit="D")).dt.date
    semanal = (pd.DataFrame({
        "abertos": df.groupby("inicio_semana").size(),
        "resolvidos": semana_resolucao.value_counts(),
    }).fillna(0).astype(int).sort_index().rename_axis("inicio_semana").reset_index())
    semanal = semanal[(semanal["inicio_semana"] >= ini - pd.Timedelta(days=6)) & (semanal["inicio_semana"] <= fim)]
    # Semana em andamento fica de fora: parcial, pareceria uma queda de demanda
    hoje = pd.Timestamp.now(tz=config.FUSO).date()
    semanal = semanal[semanal["inicio_semana"] < hoje - pd.Timedelta(days=hoje.weekday())]
    diario = agg["agg_diario"]
    diario = diario[(diario["data"] >= ini) & (diario["data"] <= fim)]

    estilo.secao("Tendência")
    c1, c2 = st.columns([3, 2])
    with c1:
        grafico(g.abertos_vs_resolvidos(semanal))
    with c2:
        grafico(g.backlog(diario))

    mensal = df.groupby("ano_mes").agg(
        mediana=("tempo_resolucao_h", "median"),
        sla=("sla_resolucao_cumprido", lambda s: s.dropna().mean() * 100),
        chamados=("codigo", "size")).reset_index()
    mensal["ano_mes"] = mensal["ano_mes"].map(g.rotulo_mes)

    estilo.secao("Mês a mês")
    c1, c2, c3 = st.columns(3)
    with c1:
        grafico(g.colunas(mensal["ano_mes"], mensal["chamados"], "Chamados por mês", "Abertos em cada mês"))
    with c2:
        grafico(g.colunas(mensal["ano_mes"], mensal["mediana"], "Resolução mediana", "Horas corridas",
                          sufixo="h", casas=1))
    with c3:
        grafico(g.colunas(mensal["ano_mes"], mensal["sla"], "SLA de resolução cumprido",
                          "% resolvidos dentro da meta", sufixo="%"))

    estilo.secao("Padrões de demanda")
    c1, c2 = st.columns([3, 2])
    with c1:
        grafico(g.heatmap_dia_hora(df))
    faixas = df["faixa_resolucao"].value_counts().reindex([f[2] for f in config.FAIXAS_RESOLUCAO], fill_value=0)
    with c2:
        grafico(g.colunas(faixas.index, faixas.values, "Tempo até a resolução",
                          "Chamados por faixa (horas corridas)"))

if pagina == "setores":
    c1, c2 = st.columns(2)
    cat = df["categoria"].value_counts()
    with c1:
        grafico(g.barras_horizontais(cat.index, cat.values, "Chamados por categoria"))
    grp = df["setor_grupo"].value_counts()
    with c2:
        grafico(g.barras_horizontais(grp.index, grp.values, "Chamados por grupo de setor"))

    estilo.secao("Detalhe por setor")
    setores = (df.groupby(["setor_grupo", "setor"])
               .agg(chamados=("codigo", "size"),
                    resolucao_mediana_h=("tempo_resolucao_h", "median"),
                    sla_pct=("sla_resolucao_cumprido", lambda s: s.dropna().mean() * 100),
                    categoria_principal=("categoria", lambda s: s.mode().iat[0]))
               .reset_index().sort_values("chamados", ascending=False))
    with estilo.card():
        st.dataframe(setores, hide_index=True, width="stretch", height=420, column_config={
            "setor_grupo": "Grupo", "setor": "Setor",
            "chamados": st.column_config.ProgressColumn("Chamados", format="%d",
                                                        max_value=int(setores["chamados"].max())),
            "resolucao_mediana_h": st.column_config.NumberColumn("Resolução mediana (h)", format="%.1f"),
            "sla_pct": st.column_config.ProgressColumn("SLA cumprido", format="%.0f%%", min_value=0, max_value=100),
            "categoria_principal": "Categoria mais frequente",
        })

if pagina == "previsoes":
    # Usa só os filtros de setor/categoria/prioridade: o modelo precisa do histórico completo
    res = previsao.prever(base)
    if res is None:
        st.info("Histórico insuficiente para prever com esses filtros (mínimo de 11 semanas com dados).")
    else:
        prox = res.previsao.iloc[0]
        mes = res.previsao.head(4)
        melhora = (1 - res.erro_medio / res.erro_ingenuo) * 100
        # Somar os limites semanais exageraria a faixa; soma das variâncias é o correto
        total4 = mes["previsao"].sum()
        margem4 = (((mes["lim_sup"] - mes["previsao"]) ** 2).sum()) ** 0.5
        estilo.kpis([
            estilo.kpi("event_upcoming", f"Próxima semana · {prox['inicio_semana']:%d/%m}",
                       g.fmt(prox["previsao"], 0), " chamados",
                       nota=f"entre {g.fmt(prox['lim_inf'], 0)} e {g.fmt(prox['lim_sup'], 0)}"),
            estilo.kpi("date_range", "Próximas 4 semanas", g.fmt(mes["previsao"].sum(), 0), " chamados",
                       nota=f"entre {g.fmt(max(total4 - margem4, 0), 0)} e {g.fmt(total4 + margem4, 0)}"),
            estilo.kpi("target", "Erro médio do modelo", f"±{g.fmt(res.erro_medio)}", " /semana",
                       nota=f"{g.fmt(res.erro_pct, 0)}% da média semanal",
                       ajuda="Medido prevendo semanas que já aconteceram."),
            estilo.kpi("insights", "Ganho sobre o método simples", g.fmt(melhora, 0), "%",
                       nota=f"repetir a semana anterior erraria ±{g.fmt(res.erro_ingenuo)}"),
        ])

        grafico(g.previsao_semanal(res.historico, res.previsao))

        c1, c2 = st.columns(2)
        cat = previsao.por_categoria(base, res)
        with c1:
            grafico(g.barras_horizontais(cat["categoria"], cat["previsao"], "Próximas 4 semanas por categoria",
                                         "Chamados esperados, pela participação das últimas 12 semanas"))
        dias = previsao.por_dia_semana(base, res)
        with c2:
            grafico(g.colunas(dias["dia_semana"], dias["previsao"], "Próxima semana por dia",
                              "Chamados esperados em cada dia útil", casas=1))

        tabela = res.previsao.assign(inicio_semana=res.previsao["inicio_semana"].dt.strftime("%d/%m/%Y"))
        with estilo.card():
            st.dataframe(tabela, hide_index=True, width="stretch", column_config={
                "inicio_semana": "Semana de", "dias_uteis": "Dias úteis",
                "previsao": st.column_config.NumberColumn("Previsão", format="%.0f"),
                "lim_inf": st.column_config.NumberColumn("Mínimo provável", format="%.0f"),
                "lim_sup": st.column_config.NumberColumn("Máximo provável", format="%.0f"),
            })
        with st.expander("Como a previsão é feita", icon=":material/help:"):
            st.markdown(f"""
- Base: chamados abertos por semana, só semanas completas ({len(res.historico)} semanas).
- Testamos {len(res.ranking)} modelos simples prevendo semanas que já aconteceram e escolhemos o que errou menos:
  **{res.modelo}**.
- Semanas com feriado recebem previsão proporcional aos dias úteis (feriados em `src/config.py`).
- A faixa provável (80%) vem dos erros reais do modelo nesse teste e se alarga para semanas mais distantes.
- Com poucos meses de histórico ainda não dá para captar sazonalidade anual (ex.: dezembro). A previsão
  melhora à medida que os dados acumulam.
""")
            st.dataframe(res.ranking.assign(erro_medio=res.ranking["erro_medio"].round(2)), hide_index=True,
                         column_config={"modelo": "Modelo", "erro_medio": "Erro médio (chamados/semana)"})

if pagina == "dados":
    colunas = ["codigo", "criado_em", "resolvido_em", "status", "prioridade", "tipo", "categoria",
               "subcategoria", "setor_grupo", "setor", "unidade_informada", "tempo_resolucao_h",
               "tempo_resolucao_util_h", "sla_resolucao_cumprido"]
    tabela = df[colunas].sort_values("criado_em", ascending=False)
    csv = tabela.assign(criado_em=tabela["criado_em"].dt.tz_localize(None),
                        resolvido_em=tabela["resolvido_em"].dt.tz_localize(None)) \
        .to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig")
    c1, c2 = st.columns([4, 1], vertical_alignment="center")
    c1.markdown(f'<div class="nota">{len(tabela)} chamados com os filtros atuais</div>', unsafe_allow_html=True)
    c2.download_button("Baixar CSV", csv.encode("utf-8-sig"), "chamados_filtrados.csv", "text/csv",
                       icon=":material/download:", width="stretch")
    with estilo.card():
        st.dataframe(tabela, hide_index=True, width="stretch", height=560, column_config={
            "codigo": "Código", "status": "Status", "prioridade": "Prioridade", "tipo": "Tipo",
            "categoria": "Categoria", "subcategoria": "Subcategoria", "setor_grupo": "Grupo",
            "setor": "Setor", "unidade_informada": "Unidade (informada)",
            "criado_em": st.column_config.DatetimeColumn("Criado em", format="DD/MM/YYYY HH:mm"),
            "resolvido_em": st.column_config.DatetimeColumn("Resolvido em", format="DD/MM/YYYY HH:mm"),
            "tempo_resolucao_h": st.column_config.NumberColumn("Resolução (h)", format="%.1f"),
            "tempo_resolucao_util_h": st.column_config.NumberColumn("Resolução útil (h)", format="%.1f"),
            "sla_resolucao_cumprido": st.column_config.CheckboxColumn("SLA ok"),
        })

if pagina == "qualidade":
    st.markdown('<div class="nota">Problemas encontrados nos dados da API. Nada foi apagado — '
                'servem para corrigir na origem.</div>', unsafe_allow_html=True)
    q = qualidade[qualidade["codigo"].isin(df["codigo"])]
    resumo = q["problema"].value_counts()
    descricoes = {
        "sem_primeira_resposta": "Chamado resolvido sem registro de primeira resposta",
        "fechamento_em_lote": "Fechado junto com muitos outros no mesmo instante (data de fechamento não confiável)",
        "categoria_nao_classificada": "Categoria era um tipo ('Solicitação', 'Incidente') ou 'Outros'",
        "fechado_sem_resolucao": "Status fechado, mas sem data de resolução",
        "resolvido_antes_de_criado": "Data de resolução anterior à abertura",
        "resolucao_acima_7_dias": "Levou mais de 7 dias para resolver",
    }
    with estilo.card():
        st.dataframe(pd.DataFrame({"Problema": resumo.index.map(lambda p: descricoes.get(p, p)),
                                   "Chamados": resumo.values,
                                   "% do período": resumo.values / len(df) * 100}),
                     hide_index=True, width="stretch", column_config={
                         "% do período": st.column_config.ProgressColumn("% do período", format="%.0f%%",
                                                                         min_value=0, max_value=100)})
    estilo.secao("Chamados afetados")
    with estilo.card():
        st.dataframe(q.merge(df[["codigo", "criado_em", "setor", "categoria"]], on="codigo"),
                     hide_index=True, width="stretch", column_config={
                         "codigo": "Código", "problema": "Problema", "setor": "Setor", "categoria": "Categoria",
                         "criado_em": st.column_config.DatetimeColumn("Criado em", format="DD/MM/YYYY HH:mm")})
