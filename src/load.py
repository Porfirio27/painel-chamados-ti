"""Carga: grava as tabelas finais em Parquet (Python) e CSV (Excel / Power BI)."""
import pandas as pd

from src import config


def salvar(tabelas: dict[str, pd.DataFrame]) -> None:
    config.DIR_FINAL.mkdir(parents=True, exist_ok=True)
    for nome, df in tabelas.items():
        df.to_parquet(config.DIR_FINAL / f"{nome}.parquet", index=False)

        # CSV no padrão brasileiro: ";" como separador, "," decimal, datas sem fuso
        csv = df.copy()
        for col in csv.select_dtypes(include=["datetimetz"]).columns:
            csv[col] = csv[col].dt.tz_localize(None)
        csv.to_csv(config.DIR_FINAL / f"{nome}.csv", index=False, sep=";", decimal=",",
                   encoding="utf-8-sig", float_format="%.2f", date_format="%Y-%m-%d %H:%M:%S")
        print(f"  {nome}: {len(df)} linhas")
