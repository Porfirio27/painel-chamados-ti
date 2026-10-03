"""Extração: baixa todos os chamados da API, página por página."""
import json
import time
from datetime import datetime

import requests

from src import config


def buscar_chamados(**filtros) -> list[dict]:
    """Percorre todas as páginas e devolve a lista de chamados.

    `filtros` são repassados à API (ex.: data_inicio="2026-09-01", status="fechado").
    """
    if not config.API_KEY:
        raise RuntimeError("API_KEY não definida no .env")

    chamados, pagina = [], 1
    with requests.Session() as sessao:
        while True:
            params = {"api_key": config.API_KEY, "page": pagina,
                      "limit": config.PAGE_LIMIT, **filtros}
            for tentativa in range(3):
                try:
                    resp = sessao.get(config.API_URL, params=params, timeout=60)
                    resp.raise_for_status()
                    break
                except requests.RequestException:
                    if tentativa == 2:
                        raise
                    time.sleep(2 ** tentativa)

            corpo = resp.json()
            chamados.extend(corpo["data"])
            pag = corpo["pagination"]
            print(f"  página {pag['page']}/{pag['total_pages']} — {len(chamados)}/{pag['total']} chamados")
            if not pag["has_more"]:
                return chamados
            pagina += 1


def salvar_raw(chamados: list[dict]) -> None:
    """Guarda o JSON bruto com data/hora, para auditoria e reprocessamento."""
    config.DIR_RAW.mkdir(parents=True, exist_ok=True)
    arquivo = config.DIR_RAW / f"chamados_{datetime.now():%Y%m%d_%H%M%S}.json"
    arquivo.write_text(json.dumps(chamados, ensure_ascii=False), encoding="utf-8")
    print(f"  bruto salvo em {arquivo.relative_to(config.RAIZ)}")
