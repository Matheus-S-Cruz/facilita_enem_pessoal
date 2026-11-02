"""Módulo família: quanto a escolaridade da mãe e a cor/raça mudam sua posição?

Compara a posição do participante no Brasil todo com a posição dentro de quem
tem a mesma escolaridade da mãe e dentro de quem declarou a mesma cor/raça. A
ideia é mostrar o quanto esses marcadores familiares e sociais deslocam a régua:
um mesmo ponto rende percentis diferentes conforme o grupo de comparação.

Observação: a Gold tem esses dois recortes separadamente, mas não o cruzamento
dos dois (ao contrário de renda x tipo de escola). Por isso comparamos cada
recorte em relação ao Brasil, sem combiná-los.
"""
from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from dependencias import exigir_tamanho_minimo, obter_gold
from gold import Gold
from rotulos import AREAS, COR_RACA, ESCOLARIDADE_MAE

familia_router = APIRouter(prefix="/api/modulos", tags=["modulo familia"])

Area = Enum("Area", {area: area for area in [*AREAS, "MEDIA"]}, type=str)
EscolaridadeMae = Enum("EscolaridadeMae", {codigo: codigo for codigo in ESCOLARIDADE_MAE}, type=str)
# O código 0 de cor/raça é "não declarada"; não faz sentido comparar por ele.
CorRaca = Enum("CorRaca", {c: c for c in COR_RACA if c != "0"}, type=str)


@familia_router.get("/familia")
def familia(
    nota: Annotated[float, Query(ge=0, le=1000)],
    escolaridade_mae: EscolaridadeMae,
    cor_raca: CorRaca,
    area: Area = Area.MEDIA,
    gold: Gold = Depends(obter_gold),
):
    brasil = gold.grupo(area.value)

    def posicao(grupo) -> dict:
        return {
            "percentil": grupo.percentil(nota),
            "zscore": grupo.zscore(nota),
            "media": round(grupo.media, 1),
            "participantes": grupo.n,
        }

    grupo_mae = gold.grupo(area.value, "ESCOLARIDADE_MAE", escolaridade_mae.value)
    exigir_tamanho_minimo(grupo_mae, f"com escolaridade da mãe {ESCOLARIDADE_MAE[escolaridade_mae.value]!r}")
    grupo_cor = gold.grupo(area.value, "COR_RACA", cor_raca.value)
    exigir_tamanho_minimo(grupo_cor, f"de cor/raça {COR_RACA[cor_raca.value]!r}")

    return {
        "anos": gold.anos,
        "area": area.value,
        "nota": nota,
        "escolaridade_mae": {"codigo": escolaridade_mae.value, "nome": ESCOLARIDADE_MAE[escolaridade_mae.value]},
        "cor_raca": {"codigo": cor_raca.value, "nome": COR_RACA[cor_raca.value]},
        "brasil": posicao(brasil),
        "por_escolaridade_mae": posicao(grupo_mae),
        "por_cor_raca": posicao(grupo_cor),
    }
