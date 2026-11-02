# Radar ENEM (Facilita ENEM)

Projeto Aplicado III — Ciência de Dados e IA, UniSENAI 2026/2.

O Radar ENEM mostra ao participante onde a nota dele fica em relação à população
do ENEM e a recortes socioeconômicos (renda, tipo de escola, cor/raça, sexo, UF e
escolaridade da mãe), usando percentil e Z-Score calculados a partir dos
microdados oficiais do INEP (2022 e 2023).

Equipe: Matheus Silva da Cruz (líder), Nicolas André Krause de Mello e João Paulo
Araujo Cappeletti.

> **Primeira vez aqui?** O **[SETUP.md](SETUP.md)** tem o passo a passo completo de
> instalação (Windows, Linux e Mac), com os erros comuns já resolvidos. Para só
> ver o site rodar, você precisa apenas do back-end e do front-end — a camada de
> dados já vem pronta no repositório.

## Estrutura

```
etl/                 pipeline PySpark em arquitetura medalhão
  config.py          caminhos, anos, colunas e sessão Spark
  fontes.json        URLs, tamanho e checksum dos microdados (manifesto de origem)
  baixar_microdados.py  baixa, verifica (SHA-256) e extrai os microdados do INEP
  verificar_ambiente.py checa, antes do Spark, se a versão do Python é compatível
  bronze.py          CSV do INEP -> Parquet, sem alterar o conteúdo
  silver.py          seleção de colunas, tipagem e validação com motivo de rejeição
  gold.py            distribuição de notas e estatísticas por recorte (o que a API lê)
  volumetria.py      tamanho e linhas de cada camada -> volumetria.json
  run_pipeline.py    baixa o que faltar e executa as três camadas, medindo o tempo
data/gold/           camada Gold versionada (~11 MB): a API lê daqui, sem reprocessar
facilita-backend/    API em FastAPI (percentil, Z-Score e módulos comparativos)
facilita-frontend/   interface em React + Chakra UI
public/docs/         plano de projeto
```

## Dados: só reprocesse se precisar

Os microdados do INEP são pesados (ZIPs de ~2 GB por ano, ~3,3 GB de CSV depois
de extrair) e demoram muito para baixar. Para evitar esse custo no dia a dia, **a
camada Gold já vem versionada no repositório** (`data/gold/`, ~11 MB). Ela é tudo
o que o back-end lê — então, para rodar a API, **você não precisa baixar nem
reprocessar nada**. Baixe os microdados apenas quando quiser regenerar a Gold (por
exemplo, ao incluir uma nova edição do ENEM).

### Regenerar a Gold (opcional)

Precisa de Java 17 para o Spark. O pipeline baixa e extrai os microdados sozinho,
a partir de `etl/fontes.json` (que guarda as URLs do INEP, o tamanho e o SHA-256
de cada ano):

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r etl/requirements.txt
python etl/run_pipeline.py          # baixa o que faltar, verifica e processa
```

Comandos úteis:

```bash
# Só baixar/verificar os microdados, sem rodar o Spark:
python etl/baixar_microdados.py            # todos os anos de fontes.json
python etl/baixar_microdados.py 2023       # só um ano
python etl/baixar_microdados.py --verificar  # confere o que já está extraído

# Pipeline assumindo que os CSVs já estão extraídos em public/:
python etl/run_pipeline.py --sem-download
```

- **Use Python 3.8 a 3.11** para o Spark: o PySpark 3.5.3 não suporta versões
  mais novas (como 3.14), que fazem o pipeline falhar sem mensagem clara. O
  `run_pipeline.py` verifica isso no início e para com uma orientação objetiva se
  a versão não servir (o 3.12 passa com um aviso). Confira com
  `python etl/verificar_ambiente.py`. O **back-end** não usa Spark e roda em
  qualquer Python recente — essa restrição vale só para regenerar a Gold.
- Os ZIPs ficam em `public/` e são apagados após a extração (use `--manter-zip`
  para conservá-los). Bronze, Silver e os ZIPs **não** são versionados; só a Gold.
- **Se o download falhar** (o INEP às vezes recusa a conexão), o script tenta de
  novo e, por fim, cai para o `curl`. Se ainda assim não baixar, baixe o ZIP pelo
  navegador a partir do [portal do INEP](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem),
  salve em `public/microdados_enem_AAAA.zip` e rode o pipeline de novo — ele
  reaproveita o ZIP que já está lá, sem baixar outra vez.
- Na primeira execução, o tamanho e o SHA-256 de cada ZIP são gravados em
  `etl/fontes.json`. Nas próximas, o download é conferido contra esse checksum —
  é assim que o projeto detecta um arquivo corrompido ou uma republicação do INEP.
- Depois de regenerar, **comite `data/gold/` e `etl/fontes.json`** para que o
  próximo a clonar o repositório já tenha os dados prontos. O resumo da execução
  fica em `etl/volumetria.json`.

## Back-end

API em FastAPI que carrega a Gold em memória e calcula percentil e Z-Score.
**Requer Python 3.12+** (não usa Spark nem Java). Passo a passo detalhado e
solução de problemas no [SETUP.md](SETUP.md#3-back-end-api).

```bash
cd facilita-backend
python3.12 -m venv venv
. venv/bin/activate                     # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8001   # docs em http://localhost:8001/docs
python -m pytest tests                  # testes com uma Gold sintética, sem precisar dos microdados
```

## Front-end

React + Chakra UI (ícones do Material UI). Precisa de Node.js 18+. Em
desenvolvimento, as chamadas a `/api` vão para o back-end na porta 8001 (outra
porta: `API_URL=http://localhost:8000 npm run dev`). Veja o
[SETUP.md](SETUP.md#4-front-end-site) para o checklist de verificação.

```bash
cd facilita-frontend
npm install
npm run dev                      # http://localhost:5173
```
