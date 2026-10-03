"""Previsão do volume semanal de chamados.

Com poucas semanas de histórico, modelos simples são mais confiáveis que ARIMA/Prophet.
Testamos alguns candidatos "prevendo o passado" (backtest com origem móvel) e usamos o que
errou menos. A faixa de incerteza vem dos próprios erros do backtest.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src import config

HORIZONTE = 8          # semanas à frente
MIN_TREINO = 8         # semanas mínimas antes de começar a testar
H_TESTE = 4            # horizonte avaliado no backtest
Z_80 = 1.2816          # intervalo de 80%


# ---------------------------------------------------------------- série semanal

def serie_semanal(fato: pd.DataFrame, hoje: pd.Timestamp | None = None) -> pd.Series:
    """Chamados abertos por semana (segunda-feira), só semanas completas."""
    hoje = (hoje or pd.Timestamp.now(tz=config.FUSO)).normalize()
    c = fato["criado_em"]
    semana = (c.dt.normalize() - pd.to_timedelta(c.dt.dayofweek, unit="D")).dt.tz_localize(None)
    s = semana.value_counts().sort_index()
    s = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="W-MON"), fill_value=0)

    # Primeira semana: incompleta se o primeiro chamado não foi na segunda
    if c.min().dayofweek > 0:
        s = s.iloc[1:]
    # Semana atual: só conta quando os 5 dias úteis já passaram
    inicio_atual = (hoje - pd.Timedelta(days=hoje.dayofweek)).tz_localize(None)
    if hoje.dayofweek < 5:
        s = s[s.index < inicio_atual]
    return s.rename("chamados").rename_axis("inicio_semana")


def dias_uteis(inicio_semana: pd.Timestamp) -> int:
    dias = pd.date_range(inicio_semana, periods=5, freq="D").strftime("%Y-%m-%d")
    return int(sum(d not in config.FERIADOS for d in dias))


# ---------------------------------------------------------------- modelos

def _media_movel(y: np.ndarray, janela: int, h: int) -> np.ndarray:
    return np.full(h, y[-janela:].mean())


def _ses(y: np.ndarray, alpha: float, h: int) -> np.ndarray:
    nivel = y[0]
    for v in y[1:]:
        nivel = alpha * v + (1 - alpha) * nivel
    return np.full(h, nivel)


def _holt_amortecido(y: np.ndarray, alpha: float, beta: float, h: int, phi: float = 0.9) -> np.ndarray:
    nivel, tend = y[0], y[1] - y[0]
    for v in y[1:]:
        anterior = nivel
        nivel = alpha * v + (1 - alpha) * (anterior + phi * tend)
        tend = beta * (nivel - anterior) + (1 - beta) * phi * tend
    passos = np.cumsum(phi ** np.arange(1, h + 1))
    return nivel + passos * tend


def candidatos() -> dict:
    modelos = {"Média das últimas 4 semanas": lambda y, h: _media_movel(y, 4, h),
               "Média das últimas 8 semanas": lambda y, h: _media_movel(y, 8, h)}
    for a in (0.1, 0.2, 0.3, 0.5):
        modelos[f"Suavização exponencial (α={a})"] = lambda y, h, a=a: _ses(y, a, h)
    for a in (0.2, 0.4):
        for b in (0.1, 0.2):
            modelos[f"Holt amortecido (α={a}, β={b})"] = lambda y, h, a=a, b=b: _holt_amortecido(y, a, b, h)
    return modelos


# ---------------------------------------------------------------- backtest

def backtest(y: np.ndarray, modelo) -> np.ndarray:
    """Matriz de erros (real - previsto): linhas = origens, colunas = horizonte 1..H_TESTE."""
    erros = []
    for origem in range(MIN_TREINO, len(y) - 1):
        real = y[origem:origem + H_TESTE]
        prev = modelo(y[:origem], len(real))
        linha = np.full(H_TESTE, np.nan)
        linha[:len(real)] = real - prev
        erros.append(linha)
    return np.array(erros)


@dataclass
class Resultado:
    previsao: pd.DataFrame        # semana, previsao, lim_inf, lim_sup
    historico: pd.Series
    modelo: str
    erro_medio: float             # MAE em chamados/semana
    erro_pct: float               # MAE / média semanal
    erro_ingenuo: float           # MAE de "repetir a semana passada", para comparar
    ranking: pd.DataFrame


def prever(fato: pd.DataFrame, horizonte: int = HORIZONTE) -> Resultado | None:
    s = serie_semanal(fato)
    y = s.to_numpy(dtype=float)
    if len(y) < MIN_TREINO + 3:
        return None

    modelos = candidatos()
    erros = {nome: backtest(y, m) for nome, m in modelos.items()}
    mae = {nome: np.nanmean(np.abs(e)) for nome, e in erros.items()}
    ingenuo = np.nanmean(np.abs(backtest(y, lambda t, h: np.full(h, t[-1]))))
    melhor = min(mae, key=mae.get)

    # Incerteza por horizonte a partir dos erros do backtest; cresce com √h além do testado
    desvio = np.nanstd(erros[melhor], axis=0, ddof=1)
    desvio = np.array([desvio[min(h, H_TESTE) - 1] * np.sqrt(max(h / H_TESTE, 1))
                       for h in range(1, horizonte + 1)])

    semanas = pd.date_range(s.index[-1] + pd.Timedelta(weeks=1), periods=horizonte, freq="W-MON")
    # Semana com feriado recebe proporcionalmente menos chamados
    uteis = np.array([dias_uteis(sem) for sem in semanas])
    fator = uteis / 5
    prev = np.maximum(modelos[melhor](y, horizonte), 0) * fator
    desvio = desvio * fator
    tabela = pd.DataFrame({
        "inicio_semana": semanas,
        "dias_uteis": uteis,
        "previsao": prev.round(1),
        "lim_inf": np.maximum(prev - Z_80 * desvio, 0).round(1),
        "lim_sup": (prev + Z_80 * desvio).round(1),
    })
    ranking = (pd.DataFrame({"modelo": list(mae), "erro_medio": list(mae.values())})
               .sort_values("erro_medio").reset_index(drop=True))
    return Resultado(tabela, s, melhor, mae[melhor], mae[melhor] / y.mean() * 100, ingenuo, ranking)


# ---------------------------------------------------------------- desdobramentos

def por_categoria(fato: pd.DataFrame, resultado: Resultado, semanas: int = 4, base_semanas: int = 12) -> pd.DataFrame:
    """Divide a previsão das próximas `semanas` pela participação recente de cada categoria."""
    corte = resultado.historico.index[-1] - pd.Timedelta(weeks=base_semanas - 1)
    recente = fato[fato["criado_em"].dt.tz_localize(None) >= corte]
    share = recente["categoria"].value_counts(normalize=True)
    total = resultado.previsao["previsao"].head(semanas).sum()
    return (pd.DataFrame({"categoria": share.index, "participacao_pct": (share.values * 100).round(1),
                          "previsao": (share.values * total).round(0).astype(int)})
            .reset_index(drop=True))


def por_dia_semana(fato: pd.DataFrame, resultado: Resultado) -> pd.DataFrame:
    """Chamados esperados por dia útil na próxima semana (perfil histórico × previsão)."""
    perfil = fato["dia_semana"].astype(str).value_counts(normalize=True).reindex(config.DIAS_SEMANA, fill_value=0)
    perfil = perfil[perfil > 0.01]
    prox = resultado.previsao.iloc[0]
    return pd.DataFrame({"dia_semana": perfil.index,
                         "previsao": (perfil.values * prox["previsao"]).round(1),
                         "participacao_pct": (perfil.values * 100).round(1)})
