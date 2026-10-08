# Configuração do Ambiente de Desenvolvimento

Este projeto usa **Docker Compose** para subir o banco de dados (PostgreSQL com PostGIS, a extensão de dados geográficos que permite buscar instituições por proximidade) e a API num ambiente isolado, sem instalar nada disso direto na sua máquina.

O guia de configuração a partir daqui irá assumir que você está usando um Sistema Operacional Linux. No Windows, use o WSL com o Docker Desktop.

## Dependências

- Docker com o plugin Compose - (sobe o banco e a API)
- Node.js 22 - (roda o site e os testes do frontend)
- Python 3.12 - (roda os testes, o lint e o Alembic fora do Docker)
- make - (atalhos para os comandos do projeto)
- Git

No Ubuntu, o `make` e o Git se instalam com `sudo apt install make git`. As dependências Python do backend são instaladas num ambiente virtual em `server/.venv`, e as do site pelo `npm`.

# Instalação de Dependências

Os passos a seguir rodam dentro do repositório. Clone-o e entre na pasta:

```bash
git clone https://github.com/Dona-Be/DonaBe.git && cd DonaBe
```

Caso tenha qualquer problema na instalação de qualquer componente, refira-se à página de [troubleshooting](TROUBLESHOOTING.MD) para os problemas mais comuns.

Se ainda assim não encontrar ou não conseguir resolver o problema, não hesite em contactar algum dos membros da equipe de desenvolvimento.

## 1. Docker

O Docker roda o PostgreSQL com PostGIS e a API em containers.

### 1. Instalação

1. Instale o [Docker Engine](https://docs.docker.com/engine/install/) (ou o Docker Desktop, no WSL) seguindo o guia do seu sistema. O plugin Compose vem junto.

2. Confira a instalação com o comando:

```bash
docker compose version
```

### 2. Configuração

1. Para usar o Docker sem `sudo`, adicione o seu usuário ao grupo `docker` e entre de novo na sessão:

```bash
sudo usermod -aG docker "$USER"
```

2. Copie o .env.example para o .env através do comando:

~~~bash
cp .env.example .env
~~~

3. Preencha as variáveis obrigatórias no `.env`

Variáveis mínimas para o ambiente de desenvolvimento:

```bash
ENVIRONMENT=development

# Banco local, criado pelo Docker Compose na primeira subida
POSTGRES_USER=donabe
POSTGRES_PASSWORD=donabe
POSTGRES_DB=donabe
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg://donabe:donabe@localhost:5432/donabe
# Banco separado para os testes (criado sozinho pelos testes)
TEST_DATABASE_URL=postgresql+psycopg://donabe:donabe@localhost:5432/donabe_test

BACKEND_PORT=8000
FRONTEND_URL=http://localhost:5173

# Preencha com as credenciais do seu cliente OAuth do Google (passo 4)
GOOGLE_CLIENT_ID=""
GOOGLE_CLIENT_SECRET=""

# Gere um valor diferente para cada um (passo 5); a API não sobe com menos de 32 caracteres
SESSION_SECRET_KEY=""
JWT_SECRET_KEY=""
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

4. Crie as credenciais OAuth do Google:

   1. No [Google Cloud Console](https://console.cloud.google.com/), crie (ou escolha) um projeto e abra **Google Auth Platform**.
   2. Em **Branding**, preencha o nome do app e o e-mail de suporte. Em **Audience**, escolha **External**.
   3. Ainda em **Audience → Test users**, adicione o seu e-mail e o de cada colega: enquanto o app estiver em **Testing**, só essas contas conseguem entrar.
   4. Em **Clients → Create client**, escolha **Web application**.
   5. Em **Authorized JavaScript origins**, cadastre `http://localhost:5173`.
   6. Em **Authorized redirect URIs**, cadastre `http://localhost:5173/api/auth/callback/google`.
   7. Copie o ID e o segredo do cliente para `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET`.

5. Gere os dois segredos, um valor **diferente** para cada um:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. **NUNCA** sob hipótese alguma faça commit do `.env`

## 2. Node.js

O Node.js roda o site (Vite + React) e os seus testes.

### 1. Instalação

1. Instale o Node.js 22 pelo [nvm](https://github.com/nvm-sh/nvm) ou pelo [instalador oficial](https://nodejs.org/).

2. Confira a versão com o comando:

```bash
node --version
```

A saída precisa começar com `v22`.

## 3. Python

O Python roda os testes do backend, o lint e o Alembic (migrações) fora do Docker.

### 1. Instalação

1. Instale o Python 3.12 pelo gerenciador de pacotes do seu sistema, por exemplo:

```bash
sudo apt install python3.12 python3.12-venv
```

> [!NOTE]
> Se o comando `python3.12` não existir com esse nome na sua distribuição, confira com `python3 --version` se o `python3` já é a versão 3.12 e use-o no lugar.

### 2. Configuração

1. Crie o ambiente virtual em `server/.venv` e instale as dependências de desenvolvimento:

```bash
cd server
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cd ..
```

Esse ambiente é obrigatório para `make test`, `make lint` e para os comandos do `alembic`.

> [!IMPORTANT]
> Ative o ambiente virtual com `source server/.venv/bin/activate` em **todo** terminal novo antes de rodar os comandos do projeto. O prompt fica parecido com `(.venv) <seu usuário>@<máquina>`.

## Setup do Projeto

### 1. Subir o banco e a API

Dentro da pasta raiz do projeto, execute

```bash
make up
```

O comando constrói a imagem da API e sobe o PostGIS e a API em segundo plano. A API aplica as migrações do banco sozinha ao iniciar e fica em `http://localhost:8000` (documentação interativa em `http://localhost:8000/api/docs`).

### 2. Instalar as dependências do site

```bash
cd web && npm ci && cd ..
```

### 3. Rodar o site

```bash
make dev-web
```

Acesse `http://localhost:5173`. O Vite repassa as chamadas a `/api` para a API, então o login com o Google funciona pela mesma origem do site. No primeiro acesso, cada conta escolhe entre doador e gestor de instituição, e a escolha não muda depois.

### 4. Migrações do banco

Depois de editar um modelo em `server/src/models/` (entidade nova precisa ser importada em `server/src/models/__init__.py`), gere a migração com o banco no ar e o ambiente virtual ativado. O comando compara os modelos com o banco (autogenerate):

```bash
make makemigration m="descricao da mudanca"
```

Revise o arquivo gerado em `server/alembic/versions/` e depois aplique a migração no banco de desenvolvimento:

```bash
make format
make migrate
```

Se a API estiver rodando no Docker, rode `make up` em seguida para ela usar o código novo.

### 5. Comandos

Subir e derrubar o ambiente:

```bash
make up    # constrói a API e sobe banco + API em segundo plano
make db    # sobe só o banco, para rodar a API fora do Docker
make down  # derruba banco e API
make logs  # acompanha os logs dos containers
```

Banco de dados:

```bash
make migrate                                 # aplica as migrações no banco de desenvolvimento
make makemigration m="descricao da mudanca"  # gera a migração comparando os modelos com o banco (autogenerate)
```

Lint e testes:

```bash
make lint    # ruff no backend; eslint, prettier e tipos no site
make format  # formata o backend e o site
make test    # pytest no backend (contra o banco de testes) e vitest no site
```

Desenvolvimento com reload automático:

```bash
make dev-server  # API fora do Docker, depois de make db e make migrate
make dev-web     # site em http://localhost:5173
```

### 6. Fluxo recomendado para desenvolvimento

Depois do setup, com o ambiente virtual ativado, use os comandos abaixo:

```bash
# Banco + API no Docker e site com reload automático
make up
make dev-web

# Ou só o banco no Docker e a API com reload automático, cada servidor em um terminal
make db
make migrate
make dev-server
make dev-web

# Antes de abrir um pull request
make format
make lint
make test
```

Os testes do backend usam o banco `TEST_DATABASE_URL`, criado sozinho na primeira execução, e aplicam as migrações nele; eles não tocam no banco de desenvolvimento.