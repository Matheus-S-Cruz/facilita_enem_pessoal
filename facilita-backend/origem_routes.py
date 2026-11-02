"""Módulo origem: quanto a renda da família e a escola pesam na sua posição?

Compara a posição do participante no Brasil todo com a posição dentro de quem
tem a mesma renda, dentro de quem estudou no mesmo tipo de escola, e dentro do
cruzamento dos dois (mesma renda E mesma escola). A ideia é mostrar o quanto a
origem socioeconômica "move" a régua: um mesmo ponto rende percentis diferentes
conforme o grupo de comparação.
"""
from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from dependencias import exigir_tamanho_minimo, obter_gold
from gold import Gold
from rotulos import AREAS, RENDA, TIPO_ESCOLA

origem_router = APIRouter(prefix="/api/modulos", tags=["modulo origem"])

Area = Enum("Area", {area: area for area in [*AREAS, "MEDIA"]}, type=str)
Renda = Enum("Renda", {codigo: codigo for codigo in RENDA}, type=str)
# O código 1 de TP_ESCOLA é "não informou"; não faz sentido comparar por ele.
TipoEscola = Enum("TipoEscola", {c: c for c in TIPO_ESCOLA if c != "1"}, type=str)


@origem_router.get("/origem")
def origem(
    nota: Annotated[float, Query(ge=0, le=1000)],
    renda: Renda,
    tipo_escola: TipoEscola,
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

    grupo_renda = gold.grupo(area.value, "RENDA", renda.value)
    exigir_tamanho_minimo(grupo_renda, f"com renda {RENDA[renda.value]!r}")
    grupo_escola = gold.grupo(area.value, "TIPO_ESCOLA", tipo_escola.value)
    exigir_tamanho_minimo(grupo_escola, f"de escola {TIPO_ESCOLA[tipo_escola.value]!r}")
    grupo_ambos = gold.grupo(area.value, "RENDA_X_TIPO_ESCOLA", f"{renda.value}|{tipo_escola.value}")
    exigir_tamanho_minimo(grupo_ambos, "com essa renda e esse tipo de escola")

    return {
        "anos": gold.anos,
        "area": area.value,
        "nota": nota,
        "renda": {"codigo": renda.value, "nome": RENDA[renda.value]},
        "tipo_escola": {"codigo": tipo_escola.value, "nome": TIPO_ESCOLA[tipo_escola.value]},
        "brasil": posicao(brasil),
        "por_renda": posicao(grupo_renda),
        "por_escola": posicao(grupo_escola),
        "por_renda_e_escola": posicao(grupo_ambos),
    }
