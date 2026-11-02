"""Executa o pipeline completo, na ordem, medindo o tempo de cada camada.

Antes das camadas, garante que os microdados estão no lugar: se faltar o CSV de
algum ano, baixa e extrai automaticamente a partir de etl/fontes.json (pule com
--sem-download, útil quando os microdados já estão extraídos).

Uso:
    python etl/run_pipeline.py                 # baixa o que faltar e processa
    python etl/run_pipeline.py --sem-download  # assume os microdados já extraídos
"""
import argparse
import time

import baixar_microdados
import bronze
import gold
import silver
import volumetria
from config import criar_spark
from verificar_ambiente import verificar_python


def garantir_microdados() -> None:
    """Baixa e extrai os anos de fontes.json cujo CSV ainda não existe."""
    fontes = baixar_microdados.carregar_fontes()
    atualizou = False
    for ano, fonte in fontes["anos"].items():
        atualizou |= baixar_microdados.processar_ano(ano, fonte, so_verificar=False, manter_zip=False)
    if atualizou:
        baixar_microdados.salvar_fontes(fontes)


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa o pipeline ETL completo do Radar ENEM.")
    parser.add_argument("--sem-download", action="store_true", help="não baixa microdados; assume que já estão extraídos")
    args = parser.parse_args()

    # Barra cedo um Python incompatível, antes de baixar GBs ou subir o Spark.
    verificar_python()

    if not args.sem_download:
        garantir_microdados()

    spark = criar_spark("enem-pipeline")
    spark.sparkContext.setLogLevel("ERROR")
    tempos = {}
    for nome, etapa in (("bronze", bronze), ("silver", silver), ("gold", gold)):
        inicio = time.perf_counter()
        etapa.executar(spark)
        tempos[nome] = round(time.perf_counter() - inicio, 1)
        print(f"[{nome}] concluída em {tempos[nome]} s")
    volumetria.imprimir(volumetria.medir(spark, tempos))
    spark.stop()


if __name__ == "__main__":
    main()
