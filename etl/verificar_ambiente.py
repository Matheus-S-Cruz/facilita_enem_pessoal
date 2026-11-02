"""Verifica, antes de subir o Spark, se o Python é compatível com o PySpark.

O PySpark 3.5.x roda a JVM via py4j e exige uma versão de Python suportada
(3.8 a 3.11). Em versões novas demais — como a 3.14 — a sessão sobe e morre
sem explicação clara, deixando o pipeline "travado". Checar a versão aqui
transforma esse erro confuso num aviso objetivo logo no início.
"""
import sys

# Faixa oficialmente suportada pelo PySpark 3.5.x.
MIN_SUPORTADO = (3, 8)
MAX_SUPORTADO = (3, 11)


def _versao_atual() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def verificar_python(interromper: bool = True) -> bool:
    """Confere a versão do Python. Devolve True se é totalmente suportada.

    - Abaixo do mínimo ou acima do máximo suportado: erro (encerra se interromper).
    - Exatamente uma minor acima do máximo (ex.: 3.12): só avisa, não interrompe.
    """
    atual = sys.version_info[:2]
    if MIN_SUPORTADO <= atual <= MAX_SUPORTADO:
        return True

    faixa = f"{MIN_SUPORTADO[0]}.{MIN_SUPORTADO[1]} a {MAX_SUPORTADO[0]}.{MAX_SUPORTADO[1]}"
    # 3.12 funciona na prática, mas fora do suporte oficial: avisa e segue.
    if atual == (MAX_SUPORTADO[0], MAX_SUPORTADO[1] + 1):
        print(
            f"AVISO: Python {_versao_atual()} está fora da faixa oficialmente suportada "
            f"pelo PySpark 3.5.3 ({faixa}). Pode funcionar, mas se houver falhas estranhas, "
            f"use Python {faixa}.",
            file=sys.stderr,
        )
        return False

    mensagem = (
        f"Python {_versao_atual()} não é compatível com o PySpark 3.5.3 "
        f"(suportado: {faixa}).\n"
        "O Spark sobe a JVM e falha sem mensagem clara nessa versão — foi o que "
        "causou o pipeline 'travado'.\n"
        "Crie a venv com uma versão suportada, por exemplo:\n"
        "  py -3.11 -m venv .venv\n"
        "  .\\.venv\\Scripts\\Activate.ps1   (Windows)   |   source .venv/bin/activate   (Linux/Mac)\n"
        "  py -m pip install -r etl/requirements.txt"
    )
    if interromper:
        sys.exit(f"\nERRO DE AMBIENTE\n{mensagem}")
    print(f"AVISO: {mensagem}", file=sys.stderr)
    return False


if __name__ == "__main__":
    if verificar_python(interromper=False):
        print(f"Python {_versao_atual()} OK para o PySpark 3.5.3.")
