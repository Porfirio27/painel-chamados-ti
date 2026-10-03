"""Painel de chamados de TI.

Uso:
    streamlit run app.py

Os dados vêm direto da API (chave em API_KEY no .env ou nos secrets do Streamlit Cloud)
e ficam em cache por 1 hora.
"""
import pandas as pd
import streamlit as st

from src import config, extract, graficos as g, previsao, transform

st.set_page_config(page_title="Chamados de TI", page_icon="📊", layout="wide")


@st.cache_data(ttl=3600, show_spinner="Buscando chamados na API...")
def carregar() -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    fato = transform.montar_fato(extract.buscar_chamados())
    return fato, transform.checar_qualidade(fato), pd.Timestamp.now(tz=config.FUSO)


try:
    fato, qualidade, atualizado = carregar()
except Exception as erro:
    st.error(f"Não foi possível buscar os dados da API: {erro}")
    st.stop()

# ---------------------------------------------------------------- cabeçalho e filtros
topo = st.columns([3, 1])
topo[0].title("Chamados de TI")
topo[1].caption(f"Dados de {atualizado:%d/%m/%Y %H:%M} · atualiza a cada hora")
if topo[1].button("Atualizar agora", type="tertiary"):
    carregar.clear()
    st.rerun()

f1, f2, f3, f4 = st.columns([2, 2, 2, 1.4])
dmin, dmax = fato["data"].min(), fato["data"].max()
periodo = f1.date_input("Período (abertura)", (dmin, dmax), min_value=dmin, max_value=dmax, format="DD/MM/YYYY")
grupos = f2.multiselect("Grupo de setor", sorted(fato["setor_grupo"].unique()), placeholder="Todos")
categorias = f3.multiselect("Categoria", sorted(fato["categoria"].unique()), placeholder="Todas")
prioridades = f4.multiselect("Prioridade", config.ORDEM_PRIORIDADE, placeholder="Todas")

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

# ---------------------------------------------------------------- indicadores
resolvidos = df.dropna(subset=["tempo_resolucao_h"])
sla = df["sla_resolucao_cumprido"].dropna()
def horas(serie: pd.Series) -> str:
    return f"{g.fmt(serie.median())} h" if serie.notna().any() else "–"


k = st.columns(5)
k[0].metric("Chamados abertos no período", f"{len(df):,}".replace(",", "."))
k[1].metric("Resolução mediana", horas(resolvidos["tempo_resolucao_h"]),
            help="Tempo corrido entre abertura e resolução. Metade dos chamados é resolvida em menos tempo que isso.")
k[2].metric("Resolução mediana (horário útil)", horas(resolvidos["tempo_resolucao_util_h"]),
            help=f"Conta só dias úteis das {config.EXPEDIENTE[0]}h às {config.EXPEDIENTE[1]}h.")
k[3].metric("SLA de resolução cumprido", f"{g.fmt(sla.mean() * 100, 0)}%" if len(sla) else "–",
            help=f"Meta (horas corridas): {config.SLA_RESOLUCAO_HORAS}. Recalculado — o status da API não é confiável.")
k[4].metric("Em aberto agora", int(base["aberto"].sum()),
            help="Chamados ainda não fechados (respeita os filtros de setor, categoria e prioridade).")

# ---------------------------------------------------------------- abas
aba_visao, aba_setores, aba_previsao, aba_dados, aba_qualidade = st.tabs(
    ["Visão geral", "Setores e categorias", "Previsões", "Dados", "Qualidade dos dados"])

cfg = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]}

with aba_visao:
    agg = transform.agregar(base)
    r = df["resolvido_em"].dropna()
    semana_resolucao = (r.dt.normalize() - pd.to_timedelta(r.dt.dayofweek, unit="D")).dt.date
    semanal = (pd.DataFrame({
        "abertos": df.groupby("inicio_semana").size(),
        "resolvidos": semana_resolucao.value_counts(),
    }).fillna(0).astype(int).sort_index().rename_axis("inicio_semana").reset_index())
    semanal = semanal[(semanal["inicio_semana"] >= ini - pd.Timedelta(days=6)) & (semanal["inicio_semana"] <= fim)]

    c1, c2 = st.columns([3, 2])
    c1.plotly_chart(g.abertos_vs_resolvidos(semanal), width="stretch", config=cfg)
    diario = agg["agg_diario"]
    diario = diario[(diario["data"] >= ini) & (diario["data"] <= fim)]
    c2.plotly_chart(g.backlog(diario), width="stretch", config=cfg)

    mensal = df.groupby("ano_mes").agg(
        mediana=("tempo_resolucao_h", "median"),
        sla=("sla_resolucao_cumprido", lambda s: s.dropna().mean() * 100),
        chamados=("codigo", "size")).reset_index()
    mensal["ano_mes"] = mensal["ano_mes"].map(g.rotulo_mes)
    c1, c2, c3 = st.columns(3)
    c1.plotly_chart(g.colunas(mensal["ano_mes"], mensal["chamados"], "Chamados por mês"),
                    width="stretch", config=cfg)
    c2.plotly_chart(g.colunas(mensal["ano_mes"], mensal["mediana"], "Resolução mediana por mês",
                              "Horas corridas", sufixo="h", casas=1), width="stretch", config=cfg)
    c3.plotly_chart(g.colunas(mensal["ano_mes"], mensal["sla"], "SLA de resolução cumprido",
                              "% dos chamados resolvidos dentro da meta", sufixo="%"),
                    width="stretch", config=cfg)

    c1, c2 = st.columns([3, 2])
    c1.plotly_chart(g.heatmap_dia_hora(df), width="stretch", config=cfg)
    faixas = df["faixa_resolucao"].value_counts().reindex([f[2] for f in config.FAIXAS_RESOLUCAO], fill_value=0)
    c2.plotly_chart(g.colunas(faixas.index, faixas.values, "Tempo até a resolução",
                              "Quantidade de chamados por faixa (horas corridas)"),
                    width="stretch", config=cfg)

with aba_setores:
    c1, c2 = st.columns(2)
    cat = df["categoria"].value_counts()
    c1.plotly_chart(g.barras_horizontais(cat.index, cat.values, "Chamados por categoria"),
                    width="stretch", config=cfg)
    grp = df["setor_grupo"].value_counts()
    c2.plotly_chart(g.barras_horizontais(grp.index, grp.values, "Chamados por grupo de setor"),
                    width="stretch", config=cfg)

    st.subheader("Setores")
    setores = (df.groupby(["setor_grupo", "setor"])
               .agg(chamados=("codigo", "size"),
                    resolucao_mediana_h=("tempo_resolucao_h", "median"),
                    sla_pct=("sla_resolucao_cumprido", lambda s: s.dropna().mean() * 100),
                    categoria_principal=("categoria", lambda s: s.mode().iat[0]))
               .reset_index().sort_values("chamados", ascending=False))
    st.dataframe(setores, hide_index=True, width="stretch", column_config={
        "setor_grupo": "Grupo", "setor": "Setor",
        "chamados": st.column_config.ProgressColumn("Chamados", format="%d",
                                                    max_value=int(setores["chamados"].max())),
        "resolucao_mediana_h": st.column_config.NumberColumn("Resolução mediana (h)", format="%.1f"),
        "sla_pct": st.column_config.NumberColumn("SLA cumprido (%)", format="%.0f%%"),
        "categoria_principal": "Categoria mais frequente",
    })

with aba_previsao:
    # Usa só os filtros de setor/categoria/prioridade: o modelo precisa do histórico completo
    res = previsao.prever(base)
    if res is None:
        st.info("Histórico insuficiente para prever com esses filtros (mínimo de 11 semanas com dados).")
    else:
        prox = res.previsao.iloc[0]
        mes = res.previsao.head(4)
        k = st.columns(4)
        k[0].metric(f"Próxima semana ({prox['inicio_semana']:%d/%m})", f"{g.fmt(prox['previsao'], 0)} chamados",
                    help=f"Faixa provável: {g.fmt(prox['lim_inf'], 0)} a {g.fmt(prox['lim_sup'], 0)}")
        k[1].metric("Próximas 4 semanas", f"{g.fmt(mes['previsao'].sum(), 0)} chamados")
        k[2].metric("Erro médio do modelo", f"± {g.fmt(res.erro_medio)} por semana",
                    help=f"Medido prevendo semanas passadas. Equivale a {g.fmt(res.erro_pct, 0)}% da média semanal.")
        melhora = (1 - res.erro_medio / res.erro_ingenuo) * 100
        k[3].metric("Ganho sobre repetir a semana anterior", f"{g.fmt(melhora, 0)}%",
                    help=f"Repetir a semana passada erraria ± {g.fmt(res.erro_ingenuo)} por semana.")

        st.plotly_chart(g.previsao_semanal(res.historico, res.previsao), width="stretch", config=cfg)

        c1, c2 = st.columns(2)
        cat = previsao.por_categoria(base, res)
        c1.plotly_chart(g.barras_horizontais(cat["categoria"], cat["previsao"], "Próximas 4 semanas por categoria",
                                             "Chamados esperados, pela participação das últimas 12 semanas"),
                        width="stretch", config=cfg)
        dias = previsao.por_dia_semana(base, res)
        c2.plotly_chart(g.colunas(dias["dia_semana"], dias["previsao"], "Próxima semana por dia",
                                  "Chamados esperados em cada dia útil", casas=1),
                        width="stretch", config=cfg)

        tabela = res.previsao.assign(inicio_semana=res.previsao["inicio_semana"].dt.strftime("%d/%m/%Y"))
        st.dataframe(tabela, hide_index=True, width="stretch", column_config={
            "inicio_semana": "Semana de", "dias_uteis": "Dias úteis",
            "previsao": st.column_config.NumberColumn("Previsão", format="%.0f"),
            "lim_inf": st.column_config.NumberColumn("Mínimo provável", format="%.0f"),
            "lim_sup": st.column_config.NumberColumn("Máximo provável", format="%.0f"),
        })
        with st.expander("Como a previsão é feita"):
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

with aba_dados:
    colunas = ["codigo", "criado_em", "resolvido_em", "status", "prioridade", "tipo", "categoria",
               "subcategoria", "setor_grupo", "setor", "unidade_informada", "tempo_resolucao_h",
               "tempo_resolucao_util_h", "sla_resolucao_cumprido"]
    tabela = df[colunas].sort_values("criado_em", ascending=False)
    st.dataframe(tabela, hide_index=True, width="stretch", column_config={
        "criado_em": st.column_config.DatetimeColumn("Criado em", format="DD/MM/YYYY HH:mm"),
        "resolvido_em": st.column_config.DatetimeColumn("Resolvido em", format="DD/MM/YYYY HH:mm"),
        "tempo_resolucao_h": st.column_config.NumberColumn("Resolução (h)", format="%.1f"),
        "tempo_resolucao_util_h": st.column_config.NumberColumn("Resolução útil (h)", format="%.1f"),
        "sla_resolucao_cumprido": st.column_config.CheckboxColumn("SLA ok"),
    })
    csv = tabela.assign(criado_em=tabela["criado_em"].dt.tz_localize(None),
                        resolvido_em=tabela["resolvido_em"].dt.tz_localize(None)) \
        .to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig")
    st.download_button("Baixar CSV filtrado", csv.encode("utf-8-sig"), "chamados_filtrados.csv", "text/csv")

with aba_qualidade:
    st.caption("Problemas encontrados nos dados da API. Nada foi apagado — servem para corrigir na origem.")
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
    st.dataframe(pd.DataFrame({"Problema": resumo.index.map(lambda p: descricoes.get(p, p)),
                               "Chamados": resumo.values,
                               "% do período": (resumo.values / len(df) * 100).round(0)}),
                 hide_index=True, width="stretch")
    st.dataframe(q.merge(df[["codigo", "criado_em", "setor", "categoria"]], on="codigo"),
                 hide_index=True, width="stretch")
