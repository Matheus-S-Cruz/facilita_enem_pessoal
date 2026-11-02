"""Módulo família: posição por escolaridade da mãe e por cor/raça."""
PARAMS = {"nota": 600, "escolaridade_mae": "E", "cor_raca": "3", "area": "MT"}


def test_compara_brasil_escolaridade_e_cor(cliente):
    corpo = cliente.get("/api/modulos/familia", params=PARAMS).json()
    # Brasil (400..895 de 5 em 5): 40 de 100 abaixo de 600.
    assert corpo["brasil"]["percentil"] == 40.0
    # Escolaridade E (400..698 de 2 em 2): 100 de 150 abaixo de 600.
    assert corpo["por_escolaridade_mae"]["percentil"] == 66.7
    # Cor/raça 3 (420..718 de 2 em 2): 90 de 150 abaixo de 600.
    assert corpo["por_cor_raca"]["percentil"] == 60.0


def test_nomes_legiveis_na_resposta(cliente):
    corpo = cliente.get("/api/modulos/familia", params=PARAMS).json()
    assert corpo["escolaridade_mae"] == {"codigo": "E", "nome": "Ensino médio completo"}
    assert corpo["cor_raca"] == {"codigo": "3", "nome": "Parda"}


def test_area_padrao_e_a_media(cliente):
    corpo = cliente.get("/api/modulos/familia", params={k: v for k, v in PARAMS.items() if k != "area"}).json()
    assert corpo["area"] == "MEDIA"


def test_escolaridade_inexistente_e_recusada(cliente):
    assert cliente.get("/api/modulos/familia", params={**PARAMS, "escolaridade_mae": "Z"}).status_code == 422


def test_cor_raca_nao_declarada_e_recusada(cliente):
    # O código 0 ("não declarada") não é opção válida de comparação.
    assert cliente.get("/api/modulos/familia", params={**PARAMS, "cor_raca": "0"}).status_code == 422


def test_grupo_pequeno_e_recusado(cliente):
    # Cor/raça 5 tem só 10 participantes na Gold sintética (abaixo do mínimo).
    resposta = cliente.get("/api/modulos/familia", params={**PARAMS, "cor_raca": "5"})
    assert resposta.status_code == 422
    assert "mínimo" in resposta.json()["detail"]


def test_cor_raca_invalida_lista_as_opcoes(cliente):
    campos = cliente.get("/api/modulos/familia", params={**PARAMS, "cor_raca": "9"}).json()["campos"]
    assert campos["cor_raca"].startswith("não é válido; use um destes:")
    assert "'3'" in campos["cor_raca"]
