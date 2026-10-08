# Troubleshooting

Este documento reúne os problemas mais comuns durante a configuração e execução do projeto, junto com a solução recomendada.

Caso encontre um problema novo e que não esteja coberto nesta página, por favor nos informe abrindo uma Issue para que possamos te ajudar.

## 1. `pytest`, `ruff` ou `alembic`: command not found

### Descrição

Ao rodar `make test`, `make lint` ou um comando do `alembic`, aparece uma mensagem como:

```bash
/bin/sh: 1: pytest: not found
```

### Solução

O ambiente virtual do backend não está ativo neste terminal. Ative-o e tente de novo:

```bash
source server/.venv/bin/activate
```

Se a pasta `server/.venv` não existir, crie-a seguindo a seção Python do [SETUP.MD](SETUP.MD).

## 2. `redirect_uri_mismatch` ao entrar com o Google

### Descrição

Ao clicar em **Entrar com Google**, o Google mostra `Error 400: redirect_uri_mismatch`.

### Solução

A URI cadastrada no cliente OAuth precisa ser exatamente `FRONTEND_URL` + `/api/auth/callback/google`, com o mesmo protocolo, host e porta. Em desenvolvimento ela é:

```
http://localhost:5173/api/auth/callback/google
```

Confira também que `FRONTEND_URL` no `.env` é `http://localhost:5173`, sem barra no fim, e que você abriu o site por `localhost`, não por `127.0.0.1`.

## 3. `Error 403: access_denied` ao entrar com o Google

### Descrição

O Google recusa o login com a mensagem `Error 403: access_denied` e algo como "o app está em teste".

### Solução

Enquanto o app estiver em **Testing** no Google Cloud, só as contas cadastradas em **Audience → Test users** conseguem entrar. Adicione o seu e-mail (e o de cada colega) lá e tente de novo.

## 4. `permission denied while trying to connect to the Docker daemon socket`

### Descrição

Qualquer comando `docker` (inclusive `make up`) responde:

```bash
permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock
```

### Solução

O seu usuário ainda não está no grupo `docker` nesta sessão. Depois do `sudo usermod -aG docker "$USER"` da seção Docker do [SETUP.MD](SETUP.MD), saia e entre de novo na sessão (ou rode `newgrp docker` no terminal atual) e tente novamente.

## 5. Porta ocupada

### Descrição

Ao rodar `make up` aparece `bind: address already in use`, o `make dev-server` falha com `address already in use`, ou o Vite sobe em outra porta (`5174`).

### Solução

Já existe algo na porta 5432, 8000 ou 5173. Se o erro aparecer no `make dev-server`, quem ocupa a 8000 é a API do Docker: suba só o banco com `make db` ou pare a API com `docker compose stop api`. Para o banco e a API, mude `POSTGRES_PORT` ou `BACKEND_PORT` no `.env` (e, fora do Docker, a porta em `DATABASE_URL` e `TEST_DATABASE_URL`). Para o site, feche o outro processo na 5173: o Google só devolve o login para `http://localhost:5173`, então o Vite em outra porta quebra o login.

> [!NOTE]
> Se mudar `BACKEND_PORT`, ajuste também o alvo do proxy em `web/vite.config.ts`.

## 6. A migração gerada veio vazia

### Descrição

`make makemigration m="..."` gera um arquivo com `pass` em `upgrade()` e `downgrade()`, mesmo depois de mudar um modelo.

### Solução

Confira que:

1. a entidade nova está importada em `server/src/models/__init__.py` (o autogenerate só enxerga o que está lá);
2. o banco já está com as migrações anteriores aplicadas (`make migrate`);
3. o arquivo foi salvo antes de rodar o comando.

## 7. `TEST_DATABASE_URL is not set`

### Descrição

`make test` falha com uma mensagem começando por `TEST_DATABASE_URL is not set`.

### Solução

Os testes do backend rodam contra um banco separado. Defina no `.env`:

```bash
TEST_DATABASE_URL=postgresql+psycopg://donabe:donabe@localhost:5432/donabe_test
```

e suba o banco com `make up` ou `make db`. O banco `donabe_test` é criado sozinho na primeira execução. O nome precisa terminar em `_test`, porque os testes apagam as tabelas desse banco.

## 8. O site em produção demora um minuto para responder

### Descrição

Depois de um tempo sem uso, a primeira requisição ao site publicado leva até um minuto.

### Solução

A API gratuita do Render dorme depois de 15 minutos sem acesso e demora cerca de um minuto para acordar. Uma chamada a `https://donabe-api.onrender.com/api/health` a acorda. Não é um bug.

## 9. O Swagger não abre pelo site em produção

### Descrição

Em produção, `https://donabe.vercel.app/api/docs` abre uma página em branco ou com erros no console do navegador.

### Solução

A política de segurança do site (`Content-Security-Policy` em `web/vercel.json`) bloqueia os scripts externos do Swagger quando ele passa pelo proxy. Abra a documentação direto na API:

```
https://donabe-api.onrender.com/api/docs
```
