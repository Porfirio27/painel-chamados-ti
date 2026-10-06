"""Transformação: limpa os dados da API e gera as tabelas para visualização."""
import unicodedata
from datetime import timedelta

import numpy as np
import pandas as pd

from src import config

COLUNAS_DATA = ["criado_em", "atualizado_em", "primeira_resposta_em", "resolvido_em",
                "fechado_em", "primeira_resposta_prazo_em", "resolucao_prazo_em"]


# ---------------------------------------------------------------- auxiliares

def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def normalizar_texto(serie: pd.Series) -> pd.Series:
    """Remove espaços extras e acentos e põe em maiúsculas — junta variações de digitação."""
    return (serie.fillna("").str.strip().str.replace(r"\s+", " ", regex=True)
            .map(_sem_acento).str.upper().replace("", pd.NA))


def grupo_setor(setor: str) -> str:
    for trecho, grupo in config.GRUPOS_SETOR:
        if trecho in setor.upper():
            return grupo
    return "Outros setores"


def minutos_uteis(inicio: pd.Timestamp, fim: pd.Timestamp) -> float:
    """Minutos entre inicio e fim contando só o expediente de dias úteis."""
    if pd.isna(inicio) or pd.isna(fim) or fim <= inicio:
        return np.nan if pd.isna(inicio) or pd.isna(fim) else 0.0
    h_ini, h_fim = config.EXPEDIENTE
    feriados = set(config.FERIADOS)
    total, dia = 0.0, inicio.normalize()
    while dia <= fim:
        if dia.dayofweek < 5 and dia.strftime("%Y-%m-%d") not in feriados:
            abre = dia + timedelta(hours=h_ini)
            fecha = dia + timedelta(hours=h_fim)
            sobreposto = (min(fim, fecha) - max(inicio, abre)).total_seconds()
            total += max(sobreposto, 0)
        dia += timedelta(days=1)
    return total / 60


def faixa_resolucao(horas: float) -> str | None:
    if pd.isna(horas):
        return None
    for ini, fim, rotulo in config.FAIXAS_RESOLUCAO:
        if ini <= horas < fim:
            return rotulo
    return None


def turno(hora: int) -> str:
    if 6 <= hora < 12:
        return "manhã"
    if 12 <= hora < 18:
        return "tarde"
    return "noite/madrugada"


# ---------------------------------------------------------------- tabela fato

def montar_fato(chamados: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(chamados).drop_duplicates("codigo", keep="last")
    agora = pd.Timestamp.now(tz=config.FUSO)

    for col in COLUNAS_DATA:
        df[col] = pd.to_datetime(df[col], utc=True, format="ISO8601").dt.tz_convert(config.FUSO)

    fato = pd.DataFrame({
        "codigo": df["codigo"],
        "numero": df["codigo"].str.extract(r"(\d+)$", expand=False).astype(int),
        "status": df["status"],
        "aberto": ~df["status"].isin(["fechado", "resolvido", "cancelado"]),
        "prioridade": pd.Categorical(df["prioridade"], config.ORDEM_PRIORIDADE, ordered=True),
        "impacto": df["impacto"],
        "urgencia": df["urgencia"],
        "tipo": df["tipo"],
        "categoria_original": df["categoria"],
        "categoria": df["categoria"].replace(config.MAPA_CATEGORIA),
        "subcategoria": df["subcategoria"].fillna("Não informada"),
        "setor": df["setor"],
        "setor_grupo": df["setor"].map(grupo_setor),
        "unidade_informada": df["unidade"],              # texto livre digitado pelo usuário
        "unidade_normalizada": normalizar_texto(df["unidade"]),
        "canal": df["canal"],
        "criado_em": df["criado_em"],
        "primeira_resposta_em": df["primeira_resposta_em"],
        "resolvido_em": df["resolvido_em"],
        "fechado_em": df["fechado_em"],                  # atenção: houve fechamento em lote
    })
    # Toner era categoria própria; vira subcategoria de Impressora.
    toner = df["categoria"].isin(["Solicitar Tonner", "Solicitar Toner"]) & fato["subcategoria"].eq("Não informada")
    fato.loc[toner, "subcategoria"] = "Toner"

    # Dimensões de tempo (sempre no fuso local; o campo "dia" da API é em UTC)
    c = fato["criado_em"]
    fato["data"] = c.dt.date
    fato["ano"] = c.dt.year
    fato["mes"] = c.dt.month
    fato["ano_mes"] = c.dt.strftime("%Y-%m")
    fato["semana_iso"] = c.dt.isocalendar().week.astype(int)
    fato["inicio_semana"] = (c.dt.normalize() - pd.to_timedelta(c.dt.dayofweek, unit="D")).dt.date
    fato["dia_semana_num"] = c.dt.dayofweek
    fato["dia_semana"] = pd.Categorical(c.dt.dayofweek.map(dict(enumerate(config.DIAS_SEMANA))),
                                        config.DIAS_SEMANA, ordered=True)
    fato["hora"] = c.dt.hour
    fato["turno"] = c.dt.hour.map(turno)
    h_ini, h_fim = config.EXPEDIENTE
    fato["fora_expediente"] = (c.dt.dayofweek >= 5) | (c.dt.hour < h_ini) | (c.dt.hour >= h_fim)

    # Tempos
    fato["tempo_resolucao_h"] = (fato["resolvido_em"] - c).dt.total_seconds() / 3600
    fato["tempo_resolucao_util_h"] = [minutos_uteis(i, f) / 60 for i, f in zip(c, fato["resolvido_em"])]
    fato["faixa_resolucao"] = pd.Categorical(fato["tempo_resolucao_h"].map(faixa_resolucao),
                                             [f[2] for f in config.FAIXAS_RESOLUCAO], ordered=True)
    fato["tempo_primeira_resposta_h"] = (fato["primeira_resposta_em"] - c).dt.total_seconds() / 3600
    fato["tem_primeira_resposta"] = fato["primeira_resposta_em"].notna()
    fato["idade_dias"] = np.where(fato["aberto"], (agora - c).dt.total_seconds() / 86400, np.nan)

    # SLA recalculado (o da API não é confiável)
    meta_res = df["prioridade"].map(config.SLA_RESOLUCAO_HORAS)
    meta_resp = df["prioridade"].map(config.SLA_PRIMEIRA_RESPOSTA_HORAS)
    fato["sla_meta_resolucao_h"] = meta_res
    resolvido = fato["tempo_resolucao_h"].notna()
    fato["sla_resolucao_cumprido"] = (fato["tempo_resolucao_h"] <= meta_res).where(resolvido).astype("boolean")
    # Aberto e já passou da meta = estourado, mesmo sem resolução
    estourado_aberto = fato["aberto"] & ((agora - c).dt.total_seconds() / 3600 > meta_res)
    fato.loc[estourado_aberto, "sla_resolucao_cumprido"] = False
    fato["sla_resposta_cumprido"] = (fato["tempo_primeira_resposta_h"] <= meta_resp) \
        .where(fato["tem_primeira_resposta"]).astype("boolean")
    fato["sla_status_api"] = df["sla_status_armazenado"]

    fato["avaliacao_satisfacao"] = df["avaliacao_satisfacao"]
    return fato.sort_values("criado_em").reset_index(drop=True)


# ---------------------------------------------------------------- qualidade

def checar_qualidade(fato: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por problema encontrado — para investigar, não para apagar."""
    regras = {
        "resolvido_antes_de_criado": fato["resolvido_em"] < fato["criado_em"],
        "fechado_sem_resolucao": fato["status"].eq("fechado") & fato["resolvido_em"].isna(),
        "sem_primeira_resposta": ~fato["tem_primeira_resposta"] & ~fato["aberto"],
        "categoria_nao_classificada": fato["categoria"].eq("Não classificado"),
        "resolucao_acima_7_dias": fato["tempo_resolucao_h"] > 168,
        "fechamento_em_lote": fato.groupby("fechado_em")["codigo"].transform("size").gt(5)
                              & fato["fechado_em"].notna(),
    }
    linhas = [pd.DataFrame({"codigo": fato.loc[m, "codigo"], "problema": nome})
              for nome, m in regras.items() if m.any()]
    return pd.concat(linhas, ignore_index=True) if linhas else pd.DataFrame(columns=["codigo", "problema"])


# ---------------------------------------------------------------- agregados

def _resumo(g) -> pd.Series:
    resolvidos = g["tempo_resolucao_h"].dropna()
    sla = g["sla_resolucao_cumprido"].dropna()
    return pd.Series({
        "chamados": len(g),
        "resolvidos": len(resolvidos),
        "abertos": int(g["aberto"].sum()),
        "resolucao_mediana_h": resolvidos.median(),
        "resolucao_p90_h": resolvidos.quantile(0.9) if len(resolvidos) else np.nan,
        "resolucao_util_mediana_h": g["tempo_resolucao_util_h"].median(),
        "pct_sla_resolucao": sla.mean() * 100 if len(sla) else np.nan,
        "pct_com_primeira_resposta": g["tem_primeira_resposta"].mean() * 100,
    })


def agregar(fato: pd.DataFrame) -> dict[str, pd.DataFrame]:
    tabelas = {}

    # Série diária: abertos, resolvidos e backlog acumulado (com dias sem movimento)
    dias = pd.date_range(fato["criado_em"].min().normalize(), pd.Timestamp.now(tz=config.FUSO).normalize(),
                         freq="D")
    abertos = fato.groupby(fato["criado_em"].dt.normalize()).size()
    # Fechados sem data de resolução saem do backlog na data de fechamento
    saida = fato["resolvido_em"].fillna(fato["fechado_em"])
    resolvidos = fato.groupby(saida.dt.normalize()).size()
    diario = pd.DataFrame({"abertos": abertos, "resolvidos": resolvidos}).reindex(dias, fill_value=0)
    diario = diario.fillna(0).astype(int)
    diario["backlog"] = (diario["abertos"] - diario["resolvidos"]).cumsum()
    diario["abertos_media_7d"] = diario["abertos"].rolling(7, min_periods=1).mean().round(2)
    diario.index = diario.index.date
    tabelas["agg_diario"] = diario.rename_axis("data").reset_index()

    tabelas["agg_mensal"] = fato.groupby("ano_mes").apply(_resumo, include_groups=False).reset_index()
    tabelas["agg_semanal"] = fato.groupby("inicio_semana").apply(_resumo, include_groups=False).reset_index()
    tabelas["agg_setor"] = (fato.groupby(["setor_grupo", "setor"]).apply(_resumo, include_groups=False)
                            .reset_index().sort_values("chamados", ascending=False))
    tabelas["agg_categoria"] = (fato.groupby("categoria").apply(_resumo, include_groups=False)
                                .reset_index().sort_values("chamados", ascending=False))
    tabelas["agg_prioridade"] = fato.groupby("prioridade", observed=True).apply(_resumo, include_groups=False).reset_index()
    tabelas["agg_categoria_mes"] = (fato.groupby(["ano_mes", "categoria"]).size()
                                    .rename("chamados").reset_index())
    grade = pd.MultiIndex.from_product([config.DIAS_SEMANA, range(24)], names=["dia_semana", "hora"])
    tabelas["agg_heatmap_dia_hora"] = (fato.groupby([fato["dia_semana"].astype(str), "hora"]).size()
                                       .reindex(grade, fill_value=0).rename("chamados").reset_index())

    for df in tabelas.values():
        for col in ("chamados", "resolvidos", "abertos"):
            if col in df:
                df[col] = df[col].astype(int)
    return tabelas


def dimensoes(fato: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "dim_setor": fato[["setor", "setor_grupo"]].drop_duplicates().sort_values(["setor_grupo", "setor"]),
        "dim_categoria": fato[["categoria", "categoria_original", "subcategoria"]].drop_duplicates()
                         .sort_values(["categoria", "categoria_original"]),
        "dim_unidade": (fato.groupby(["unidade_normalizada", "setor"]).size().rename("chamados")
                        .reset_index().sort_values("chamados", ascending=False)),
    }
