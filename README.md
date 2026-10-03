# Painel de chamados de TI

Painel em Streamlit com os chamados da API `chamado.jjsis.online`. O app busca os dados direto
da API e guarda em cache por 1 hora.

## Rodar localmente

```
pip install -r requirements.txt
cp .env.example .env       # e coloque a API_KEY
streamlit run app.py
```

`python main.py` gera as tabelas tratadas em `data/final/` (Parquet e CSV) para análises fora do painel.

## Estrutura

| Arquivo | Função |
|---|---|
| `src/config.py` | Regras de negócio: fuso, expediente, metas de SLA, mapeamento de categorias e setores |
| `src/extract.py` | Busca paginada na API |
| `src/transform.py` | Limpeza, colunas calculadas, agregados e checagens de qualidade |
| `src/graficos.py` | Gráficos Plotly padronizados |
| `app.py` | Painel |
| `main.py` | Pipeline que grava as tabelas em disco |

## Publicação (Streamlit Community Cloud)

A chave da API fica em **Settings → Secrets** do app, nunca no repositório:

```toml
API_KEY = "..."
```
