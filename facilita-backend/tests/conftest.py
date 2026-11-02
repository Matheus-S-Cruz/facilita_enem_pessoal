"""Gold sintética e pequena, montada em memória, para os testes não dependerem dos microdados."""
import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dependencias import obter_gold  # noqa: E402
from gold import Gold  # noqa: E402
from main import app  # noqa: E402

AREAS = ["LC", "CH", "CN", "MT", "REDACAO", "MEDIA"]


def _grupo(area, recorte, categoria, notas_e_qtd):
    return [{"AREA": area, "RECORTE": recorte, "CATEGORIA": categoria, "NOTA": n, "QTD": q} for n, q in notas_e_qtd]


@pytest.fixture(scope="session")
def gold() -> Gold:
    # Brasil: 100 pessoas, uma em cada nota 400, 405, ..., 895.
    brasil = [(400.0 + 5 * i, 1) for i in range(100)]
    # SC tem notas mais altas que AM; RR é pequena demais para comparar.
    sc = [(600.0 + 2 * i, 1) for i in range(150)]
    am = [(400.0 + 2 * i, 1) for i in range(150)]
    rr = [(500.0, 10)]
    # Módulo origem: renda alta (Q) tira mais que renda baixa (B); escola
    # privada (3) mais que pública (2). O cruzamento B|2 é renda baixa em
    # escola pública. Grupo B|3 é pequeno demais para comparar.
    renda_b = [(400.0 + 2 * i, 1) for i in range(150)]
    renda_q = [(600.0 + 2 * i, 1) for i in range(150)]
    escola_2 = [(420.0 + 2 * i, 1) for i in range(150)]
    escola_3 = [(620.0 + 2 * i, 1) for i in range(150)]
    cruz_b2 = [(410.0 + 2 * i, 1) for i in range(150)]
    cruz_b3 = [(500.0, 10)]
    # Módulo família: mãe com ensino médio (E) tira menos que com pós (G);
    # cor/raça 3 (parda) tem notas mais baixas que 1 (branca). Cor 5 é pequena.
    mae_e = [(400.0 + 2 * i, 1) for i in range(150)]
    mae_g = [(600.0 + 2 * i, 1) for i in range(150)]
    cor_1 = [(620.0 + 2 * i, 1) for i in range(150)]
    cor_3 = [(420.0 + 2 * i, 1) for i in range(150)]
    cor_5 = [(500.0, 10)]
    linhas = []
    for area in AREAS:
        linhas += _grupo(area, "GERAL", "TODOS", brasil)
        linhas += _grupo(area, "UF", "SC", sc)
        linhas += _grupo(area, "UF", "AM", am)
        linhas += _grupo(area, "UF", "RR", rr)
        linhas += _grupo(area, "RENDA", "B", renda_b)
        linhas += _grupo(area, "RENDA", "Q", renda_q)
        linhas += _grupo(area, "TIPO_ESCOLA", "2", escola_2)
        linhas += _grupo(area, "TIPO_ESCOLA", "3", escola_3)
        linhas += _grupo(area, "RENDA_X_TIPO_ESCOLA", "B|2", cruz_b2)
        linhas += _grupo(area, "RENDA_X_TIPO_ESCOLA", "B|3", cruz_b3)
        linhas += _grupo(area, "ESCOLARIDADE_MAE", "E", mae_e)
        linhas += _grupo(area, "ESCOLARIDADE_MAE", "G", mae_g)
        linhas += _grupo(area, "COR_RACA", "1", cor_1)
        linhas += _grupo(area, "COR_RACA", "3", cor_3)
        linhas += _grupo(area, "COR_RACA", "5", cor_5)
    distribuicao = pd.DataFrame(linhas)

    estatisticas = []
    for (area, recorte, categoria), grupo in distribuicao.groupby(["AREA", "RECORTE", "CATEGORIA"]):
        notas = grupo["NOTA"].repeat(grupo["QTD"])
        estatisticas.append({
            "NU_ANO": 2023, "AREA": area, "RECORTE": recorte, "CATEGORIA": categoria,
            "MEDIA": notas.mean(), "DESVIO_PADRAO": notas.std(ddof=0) or 1.0,
        })
    gold = Gold(pd.DataFrame(estatisticas))
    gold.adicionar_ano(2023, pa.Table.from_pandas(distribuicao, preserve_index=False))
    return gold


@pytest.fixture
def cliente(gold):
    app.dependency_overrides[obter_gold] = lambda: gold
    yield TestClient(app)
    app.dependency_overrides.clear()
