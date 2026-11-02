"""Baixa, verifica e extrai os microdados do ENEM a partir de etl/fontes.json.

Resolve o download manual e pesado do portal do INEP:
- Só baixa o ZIP de um ano se ele ainda não existir (ou se o tamanho não bater).
- Só extrai se o CSV de destino ainda não estiver no lugar que o pipeline espera.
- Registra tamanho e SHA-256 em fontes.json na primeira vez, e nas próximas
  execuções confere o download contra esse valor (a "verificação das planilhas").

Uso:
    python etl/baixar_microdados.py            # todos os anos de fontes.json
    python etl/baixar_microdados.py 2023       # só um ano
    python etl/baixar_microdados.py --verificar # só confere o que já existe, sem baixar

Os ZIPs ficam em public/ e são apagados após a extração por padrão (são pesados
e não são versionados). Use --manter-zip para conservá-los.
"""
import argparse
import hashlib
import json
import shutil
import ssl
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTES = Path(__file__).resolve().parent / "fontes.json"
PUBLIC = RAIZ / "public"

PEDACO = 1024 * 1024  # 1 MiB por leitura, para barra de progresso e baixo uso de memória


def carregar_fontes() -> dict:
    return json.loads(FONTES.read_text(encoding="utf-8"))


def salvar_fontes(dados: dict) -> None:
    FONTES.write_text(json.dumps(dados, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def csv_destino(ano: str) -> Path:
    """Onde o config.py do pipeline espera encontrar o CSV daquele ano."""
    return PUBLIC / f"microdados_enem_{ano}" / "DADOS" / f"MICRODADOS_ENEM_{ano}.csv"


def sha256_de(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(PEDACO), b""):
            h.update(bloco)
    return h.hexdigest()


def _abrir(url: str, contexto: ssl.SSLContext | None):
    requisicao = urllib.request.Request(url, headers={"User-Agent": "facilita-enem/1.0"})
    return urllib.request.urlopen(requisicao, context=contexto)  # noqa: S310 (URL fixa do INEP)


def baixar(url: str, destino: Path) -> None:
    """Download em streaming com progresso simples; grava em .parcial e renomeia no fim.

    O servidor do INEP (download.inep.gov.br) costuma apresentar uma cadeia de
    certificado SSL incompleta. Tentamos a verificação normal primeiro e, só se
    ela falhar por causa do certificado, repetimos sem verificar — avisando.
    """
    parcial = destino.with_suffix(destino.suffix + ".parcial")
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        resposta = _abrir(url, contexto=None)
    except urllib.error.URLError as erro:
        if not isinstance(erro.reason, ssl.SSLCertVerificationError):
            raise
        print("  aviso: certificado SSL do INEP não pôde ser verificado; baixando mesmo assim.")
        sem_verificacao = ssl.create_default_context()
        sem_verificacao.check_hostname = False
        sem_verificacao.verify_mode = ssl.CERT_NONE
        resposta = _abrir(url, contexto=sem_verificacao)

    with resposta:
        total = int(resposta.headers.get("Content-Length", 0))
        baixado = 0
        with parcial.open("wb") as saida:
            while bloco := resposta.read(PEDACO):
                saida.write(bloco)
                baixado += len(bloco)
                if total:
                    pct = 100 * baixado / total
                    print(f"\r  baixando {destino.name}: {baixado / 1e6:,.0f} / {total / 1e6:,.0f} MB ({pct:.0f}%)", end="")
                else:
                    print(f"\r  baixando {destino.name}: {baixado / 1e6:,.0f} MB", end="")
    print()
    # A integridade real é conferida depois pelo SHA-256 em fontes.json.
    parcial.replace(destino)


def extrair_csv(zip_path: Path, ano: str) -> Path:
    """Extrai apenas a árvore DADOS/ do ZIP e deixa o CSV no caminho que o pipeline espera.

    O ZIP do INEP traz uma pasta raiz (microdados_enem_AAAA/ ou _novo/); achamos o
    MICRODADOS_ENEM_AAAA.csv onde quer que ele esteja e o movemos para o lugar certo.
    """
    destino = csv_destino(ano)
    destino.parent.mkdir(parents=True, exist_ok=True)
    alvo = f"MICRODADOS_ENEM_{ano}.csv".lower()
    with zipfile.ZipFile(zip_path) as z:
        nome_no_zip = next((n for n in z.namelist() if n.lower().endswith(alvo)), None)
        if nome_no_zip is None:
            raise FileNotFoundError(f"{zip_path.name} não contém MICRODADOS_ENEM_{ano}.csv")
        print(f"  extraindo {nome_no_zip} -> {destino.relative_to(RAIZ)}")
        with z.open(nome_no_zip) as origem, destino.open("wb") as saida:
            shutil.copyfileobj(origem, saida, length=PEDACO)
    return destino


def processar_ano(ano: str, fonte: dict, so_verificar: bool, manter_zip: bool) -> bool:
    """Garante o CSV do ano no lugar. Devolve True se fontes.json foi atualizado."""
    destino = csv_destino(ano)
    esperado_sha = fonte.get("sha256")
    esperado_bytes = fonte.get("bytes")
    zip_path = PUBLIC / f"microdados_enem_{ano}.zip"
    atualizou_fontes = False

    if destino.exists():
        print(f"[{ano}] CSV já presente ({destino.stat().st_size / 1e6:,.0f} MB) em {destino.relative_to(RAIZ)}")
        return False

    if so_verificar:
        print(f"[{ano}] CSV ausente — rode sem --verificar para baixar")
        return False

    # Reaproveita um ZIP já baixado se o tamanho bater; senão (re)baixa.
    precisa_baixar = True
    if zip_path.exists():
        tamanho = zip_path.stat().st_size
        if esperado_bytes in (None, tamanho):
            print(f"[{ano}] ZIP já baixado ({tamanho / 1e6:,.0f} MB), reaproveitando")
            precisa_baixar = False
        else:
            print(f"[{ano}] ZIP existente tem tamanho inesperado ({tamanho} != {esperado_bytes}); rebaixando")

    if precisa_baixar:
        print(f"[{ano}] baixando de {fonte['url']}")
        baixar(fonte["url"], zip_path)

    tamanho = zip_path.stat().st_size
    print(f"[{ano}] verificando integridade do ZIP…")
    sha = sha256_de(zip_path)
    if esperado_sha and sha != esperado_sha:
        raise ValueError(
            f"[{ano}] SHA-256 não confere!\n  esperado: {esperado_sha}\n  obtido:   {sha}\n"
            "O arquivo pode estar corrompido ou o INEP republicou os microdados."
        )
    if esperado_sha is None or esperado_bytes is None:
        fonte["sha256"], fonte["bytes"] = sha, tamanho
        atualizou_fontes = True
        print(f"[{ano}] registrado em fontes.json: {tamanho / 1e6:,.0f} MB, sha256 {sha[:16]}…")
    else:
        print(f"[{ano}] integridade confirmada (sha256 {sha[:16]}…)")

    extrair_csv(zip_path, ano)
    if not manter_zip:
        zip_path.unlink()
        print(f"[{ano}] ZIP removido (use --manter-zip para conservar)")
    print(f"[{ano}] pronto.")
    return atualizou_fontes


def main() -> None:
    parser = argparse.ArgumentParser(description="Baixa e verifica os microdados do ENEM (INEP).")
    parser.add_argument("anos", nargs="*", help="anos a processar (padrão: todos os de fontes.json)")
    parser.add_argument("--verificar", action="store_true", help="não baixa; só confere o que já existe")
    parser.add_argument("--manter-zip", action="store_true", help="não apaga o ZIP após extrair")
    args = parser.parse_args()

    fontes = carregar_fontes()
    anos = args.anos or list(fontes["anos"])
    atualizou = False
    for ano in anos:
        if ano not in fontes["anos"]:
            print(f"[{ano}] não está em fontes.json — anos disponíveis: {', '.join(fontes['anos'])}", file=sys.stderr)
            continue
        atualizou |= processar_ano(ano, fontes["anos"][ano], args.verificar, args.manter_zip)
    if atualizou:
        salvar_fontes(fontes)


if __name__ == "__main__":
    main()
