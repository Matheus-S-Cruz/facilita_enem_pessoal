# Guia de instalação — Radar ENEM

Passo a passo para rodar o projeto do zero, pensado para quem nunca configurou
Python, Java ou Spark. Se algo der errado, pule direto para
[Problemas comuns](#problemas-comuns) no fim — os erros que mais aparecem já
estão resolvidos lá.

> **O atalho que quase todo mundo quer:** para ver o site funcionando você só
> precisa do **back-end** e do **front-end**. A camada de dados (Gold) já vem
> pronta no repositório — **não é preciso baixar os microdados nem rodar o
> pipeline**. Comece em [1. Clonar](#1-clonar-o-projeto), pule a seção do
> pipeline e vá para [3. Back-end](#3-back-end-api) e [4. Front-end](#4-front-end-site).

## Qual versão de Python usar?

O projeto tem duas partes em Python com exigências diferentes. Isso é a causa
mais comum de confusão, então vale deixar claro de início:

| Parte            | Python            | Precisa de Java? | Quando você usa                         |
|------------------|-------------------|------------------|-----------------------------------------|
| **Back-end (API)** | **3.12 ou mais novo** | Não              | Sempre que quiser rodar o site          |
| **Front-end**      | — (usa Node.js)   | Não              | Sempre que quiser rodar o site          |
| **Pipeline (ETL)** | **3.11**          | Sim (Java 8/11/17) | Só para regenerar a Gold (raro)         |

Dá para ter as duas versões de Python instaladas lado a lado sem conflito — cada
parte cria sua própria venv apontando para a versão certa (os comandos abaixo
mostram como). No Windows, o comando `py -3.12` / `py -3.11` escolhe a versão.

Pré-requisitos gerais:
- **Git** — <https://git-scm.com/downloads>
- **Node.js 18+** (para o front-end) — <https://nodejs.org>
- **Python** — <https://www.python.org/downloads> (instale 3.12+ para o back-end;
  adicione o 3.11 só se for regenerar a Gold)

No Windows, ao instalar o Python marque **"Add python.exe to PATH"** e deixe o
**py launcher** habilitado.

---

## 1. Clonar o projeto

```bash
git clone https://github.com/Matheus-S-Cruz/facilita_enem_pessoal.git
cd facilita_enem_pessoal
```

---

## 2. (Opcional) Regenerar a Gold

**Pule esta seção se você só quer ver o site** — a Gold já está versionada em
`data/gold/`. Faça isto apenas para recriar os dados do zero (por exemplo, ao
incluir uma nova edição do ENEM). Exige **Python 3.11** e **Java** (8, 11 ou 17).

### 2.1. Confirme o Java

O Spark precisa de Java e da variável `JAVA_HOME` apontando para a pasta de
instalação (não para o `java.exe`).

```powershell
# Windows — veja se tem Java e descubra a pasta real:
java -version
dir "C:\Program Files\Java"      # procure uma pasta como jre-1.8, jdk-17, etc.

# Defina o JAVA_HOME para a pasta que existe (ajuste o nome ao que apareceu):
$env:JAVA_HOME = "C:\Program Files\Java\jre-1.8"
Test-Path "$env:JAVA_HOME\bin\java.exe"   # precisa dar True
```

```bash
# Linux/Mac:
java -version
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
```

Não tem Java? Instale o Temurin 17 (recomendado):
`winget install EclipseAdoptium.Temurin.17.JDK` (Windows) — ele já define o
`JAVA_HOME`. Feche e reabra o terminal depois.

### 2.2. Windows: instale o winutils (uma vez só)

No Windows, o Spark precisa de dois arquivos nativos do Hadoop para **escrever**
arquivos (`winutils.exe` e `hadoop.dll`). Sem eles o pipeline sobe o Spark e
falha ao gravar o Parquet. Baixe os do Hadoop 3.3.5 (compatível com o PySpark 3.5.3):

```powershell
New-Item -ItemType Directory -Force -Path "C:\hadoop\bin"
curl.exe -L -o "C:\hadoop\bin\winutils.exe" "https://github.com/cdarlint/winutils/raw/master/hadoop-3.3.5/bin/winutils.exe"
curl.exe -L -o "C:\hadoop\bin\hadoop.dll"  "https://github.com/cdarlint/winutils/raw/master/hadoop-3.3.5/bin/hadoop.dll"

# Aponte o HADOOP_HOME e deixe o hadoop.dll no PATH:
$env:HADOOP_HOME = "C:\hadoop"
$env:PATH = "$env:HADOOP_HOME\bin;$env:PATH"
```

> Em Linux/Mac isso não é necessário.

### 2.3. Rode o pipeline

```powershell
# Windows (na mesma janela onde definiu JAVA_HOME e HADOOP_HOME):
# Se ainda não tem python 3.11 baixa primeiro:
winget install Python.Python.3.11
# Se tem pode pular para:
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r etl/requirements.txt
py etl/run_pipeline.py            # baixa os microdados (se faltarem), verifica e processa
```

```bash
# Linux/Mac:
python3.11 -m venv .venv
. .venv/bin/activate
pip install -r etl/requirements.txt
python etl/run_pipeline.py
```

O pipeline baixa os microdados automaticamente a partir de `etl/fontes.json`. Se
os CSVs já estiverem extraídos em `public/`, acrescente `--sem-download` para ir
direto ao processamento. A execução leva alguns minutos e cria `data/gold/`.

---

## 3. Back-end (API)

Carrega a Gold e calcula percentil e Z-Score. **Use Python 3.12 ou mais novo**
(o numpy/pandas fixados exigem isso). Não precisa de Java.

```powershell
# Windows:
cd facilita-backend
py -3.12 -m venv venv              # ou a versão 3.12+ que você tiver (3.13, 3.14…)
.\venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py -m uvicorn main:app --reload --port 8001
```

```bash
# Linux/Mac:
cd facilita-backend
python3.12 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8001
```

Deu certo quando o terminal mostra `Uvicorn running on http://127.0.0.1:8001`.
Abra <http://localhost:8001/docs> — se a documentação da API aparecer, o back-end
está lendo a Gold corretamente. **Deixe este terminal aberto** e abra outro para
o front-end.

Para rodar os testes (usam uma Gold sintética, não precisam dos microdados):

```bash
py -m pytest tests          # Windows
python -m pytest tests      # Linux/Mac
```

---

## 4. Front-end (site)

React + Chakra UI. Em um **segundo terminal**:

```bash
cd facilita-frontend
npm install
npm run dev
```

Abra o endereço que aparecer (normalmente <http://localhost:5173>). Em
desenvolvimento, as chamadas a `/api` vão para o back-end na porta 8001; para
usar outra porta: `API_URL=http://localhost:8000 npm run dev`.

### Como saber que está tudo certo

1. O site abre e mostra o formulário "Descubra onde você está…".
2. Preencha as cinco notas (Linguagens, Humanas, Natureza, Matemática, Redação)
   e clique em **Ver meu radar**.
3. Devem aparecer percentil, Z-Score, média e o histograma — esses números vêm
   da Gold, via API.
4. Marque a pergunta **"Seu estado e o Brasil"**, escolha uma UF e veja o
   comparativo regional.

Se os números aparecem, a cadeia **Gold → API → site** está funcionando.

---

## Problemas comuns

**`uvicorn` não é reconhecido / `No matching distribution found for numpy==...`**
A venv do back-end está num Python antigo demais. O numpy/pandas fixados exigem
**Python 3.12+**. Apague a venv e recrie com uma versão nova:
`Remove-Item -Recurse -Force venv` e refaça o passo 3 com `py -3.12`. Rode o
servidor como `py -m uvicorn ...` (em vez de só `uvicorn`), que sempre usa a venv
ativa.

**O pipeline "trava" / processos finalizados sem erro claro**
O Python é incompatível com o PySpark (ex.: 3.14). Use **Python 3.11** no
pipeline. Confira com `py etl/verificar_ambiente.py`.

**`O sistema não pode encontrar o caminho especificado` ao rodar o pipeline**
O `JAVA_HOME` aponta para uma pasta que não existe. Rode `dir "C:\Program Files\Java"`
para achar a pasta real e redefina o `JAVA_HOME` para ela; confirme com
`Test-Path "$env:JAVA_HOME\bin\java.exe"` (precisa dar `True`).

**`HADOOP_HOME and hadoop.home.dir are unset` / `winutils.exe` não encontrado**
Faltam os binários do Hadoop no Windows. Siga o passo [2.2](#22-windows-instale-o-winutils-uma-vez-só).
Baixe **os dois** arquivos (`winutils.exe` e `hadoop.dll`) e garanta que
`hadoop.dll` esteja no `PATH`.

**Download dos microdados falha com conexão recusada/resetada**
O servidor do INEP às vezes recusa a conexão. O script tenta de novo e cai para o
`curl`. Se ainda falhar, baixe o ZIP pelo navegador no
[portal do INEP](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem),
salve em `public/microdados_enem_AAAA.zip` e rode o pipeline de novo — ele
reaproveita o ZIP.

**As variáveis `JAVA_HOME`/`HADOOP_HOME` somem quando fecho o terminal**
No PowerShell, `$env:VAR = "..."` vale só para aquela janela. Para não redefinir
toda vez, configure-as como variáveis de ambiente do usuário em
*Editar as variáveis de ambiente do sistema* no Windows.
