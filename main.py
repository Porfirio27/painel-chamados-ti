"""Pipeline completo: API -> tratamento -> data/final.

Uso:
    python main.py              # baixa da API
    python main.py --offline    # reprocessa o último JSON bruto salvo
"""
import json
import sys

from src import config, extract, load, previsao, transform


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    if "--offline" in sys.argv:
        ultimo = sorted(config.DIR_RAW.glob("chamados_*.json"))[-1]
        print(f"1/3 Lendo {ultimo.name}")
        chamados = json.loads(ultimo.read_text(encoding="utf-8"))
    else:
        print("1/3 Extraindo da API")
        chamados = extract.buscar_chamados()
        extract.salvar_raw(chamados)

    print("2/3 Transformando")
    fato = transform.montar_fato(chamados)
    tabelas = {"fato_chamados": fato,
               **transform.dimensoes(fato),
               **transform.agregar(fato),
               "qualidade": transform.checar_qualidade(fato)}
    res = previsao.prever(fato)
    if res is not None:
        tabelas["previsao_semanal"] = res.previsao
        tabelas["previsao_categoria"] = previsao.por_categoria(fato, res)

    print("3/3 Salvando em data/final")
    load.salvar(tabelas)

    resolvidos = fato.dropna(subset=["tempo_resolucao_h"])
    print("\nResumo")
    print(f"  chamados: {len(fato)} | abertos: {fato['aberto'].sum()}")
    print(f"  período: {fato['criado_em'].min():%d/%m/%Y} a {fato['criado_em'].max():%d/%m/%Y}")
    print(f"  resolução mediana: {resolvidos['tempo_resolucao_h'].median():.1f}h corridas "
          f"/ {resolvidos['tempo_resolucao_util_h'].median():.1f}h úteis")
    print(f"  SLA de resolução cumprido (recalculado): {fato['sla_resolucao_cumprido'].dropna().mean():.0%}")
    print(f"  problemas de qualidade:\n{tabelas['qualidade']['problema'].value_counts().to_string()}")


if __name__ == "__main__":
    main()
