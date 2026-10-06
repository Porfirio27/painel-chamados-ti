"""Configurações do pipeline. Ajuste aqui as regras de negócio."""
import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

API_URL = os.getenv("API_URL", "https://chamado.jjsis.online/api/bi/v1/chamados")
API_KEY = os.getenv("API_KEY")
PAGE_LIMIT = 1000

DIR_RAW = RAIZ / "data" / "raw"
DIR_FINAL = RAIZ / "data" / "final"

# A API devolve tudo em UTC; as análises usam o horário local.
FUSO = "America/Sao_Paulo"

# Expediente (hora inicial, hora final) em dias úteis — usado no tempo útil.
EXPEDIENTE = (7, 17)
# Feriados nacionais (dias úteis a menos). Acrescente os municipais de Paracambi.
FERIADOS: list[str] = ["2026-06-04", "2026-09-07", "2026-10-12", "2026-11-02",
                       "2026-11-20", "2026-12-25", "2027-01-01"]

# Metas de SLA em horas corridas, por prioridade.
# Inferidas dos prazos que a API registrava no início (4h resposta / 24h resolução).
# CONFIRME com a equipe — o sla_status da API está sempre "ok" e não serve.
SLA_RESOLUCAO_HORAS = {"alta": 24, "media": 24, "baixa": 120}
SLA_PRIMEIRA_RESPOSTA_HORAS = {"alta": 4, "media": 4, "baixa": 96}

# Categoria original -> categoria padronizada.
MAPA_CATEGORIA = {
    "Acesso": "Acesso e Permissões",
    "Solicitar Tonner": "Impressora e Periféricos",
    "Solicitar Toner": "Impressora e Periféricos",   # grafia nova da API (out/2026)
    # "Solicitação" e "Incidente" são tipos, não categorias.
    "Solicitação": "Não classificado",
    "Incidente": "Não classificado",
    "Outros": "Não classificado",
}

# Agrupamento de setores (primeira regra que casar vence; ordem importa).
GRUPOS_SETOR = [
    ("VIGILÂNCIA", "Vigilância em Saúde"),
    ("EPIDEMIOLOGIA", "Vigilância em Saúde"),
    ("ZOONOSES", "Vigilância em Saúde"),
    ("CONTROLE DE VETORES", "Vigilância em Saúde"),
    ("CAPS", "Saúde Mental"),
    ("SAÚDE MENTAL", "Saúde Mental"),
    ("RESIDÊNCIA TERAPÊUTICA", "Saúde Mental"),
    ("POSTO DE SAÚDE", "Postos de Saúde"),
    ("POLICLÍNICA", "Policlínica"),
    ("GABINETE SEMUS", "Gabinete SEMUS"),
    ("REGULAÇÃO", "Regulação"),
    ("FARMÁCIA", "Farmácia / Almoxarifado"),
    ("ALMOXARIFADO", "Farmácia / Almoxarifado"),
    ("PRÉDIO GUARAJUBÃO", "Prédio Guarajubão"),
    ("LABORATÓRIO", "Laboratório"),
    ("COORDENAÇÃO", "Coordenações"),
]

ORDEM_PRIORIDADE = ["baixa", "media", "alta"]
FAIXAS_RESOLUCAO = [(0, 4, "até 4h"), (4, 24, "4h a 24h"), (24, 72, "1 a 3 dias"),
                    (72, 168, "3 a 7 dias"), (168, float("inf"), "mais de 7 dias")]
DIAS_SEMANA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
