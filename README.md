# LIMS — Fiscalização Pós-Mercado de Dispositivos Médicos

MVP de um LIMS (Laboratory Information Management System) para vigilância
sanitária pós-mercado de dispositivos médicos. O sistema cobre a entrada da
amostra apreendida, a cadeia de custódia, a execução e assinatura de ensaios,
a abertura automática de CAPA em reprovação e a trilha de auditoria
inviolável.

O projeto foi desenhado para demonstrar controles alinhados a **21 CFR Part
11**, **Anvisa RDC 665/2022** e **ALCOA+**, com assinatura eletrônica em duas
etapas em toda gravação definitiva.

---

## 1. Stack

| Camada | Tecnologia |
| --- | --- |
| API | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (async) |
| Banco | PostgreSQL 16 (`asyncpg`), JSONB, triggers e sequences |
| Segurança | JWT (access + refresh rotativo), Argon2id, HMAC-SHA256, SHA-256 |
| Front-end | React 18, TypeScript, Vite, Tailwind CSS, Radix/shadcn-style |
| Dados no cliente | TanStack Query, React Hook Form + Zod |
| Infra | Docker Compose (PostgreSQL + API + Nginx + seed opcional) |
| Testes | pytest (domínio, integridade e fluxos HTTP ponta a ponta) |

---

## 2. Arquitetura

```
┌──────────────────────────┐        /api/v1 (proxy Nginx / Vite)
│  React SPA (Nginx)       │  ─────────────────────────────────┐
│  Dashboard · Ensaios ·   │                                   │
│  CAPA · Auditoria        │                                   ▼
└──────────────────────────┘                     ┌───────────────────────────┐
                                                 │ FastAPI                   │
                                                 │ routes → services → ORM   │
                                                 │ JWT · RBAC · e-signature  │
                                                 └─────────────┬─────────────┘
                                                               │
                                      ┌────────────────────────▼──────────────────┐
                                      │ PostgreSQL 16                             │
                                      │ users · refresh_tokens · samples          │
                                      │ custody · tests · result versions         │
                                      │ capas · audit_log (append-only)           │
                                      │ signatures · triggers de imutabilidade    │
                                      └───────────────────────────────────────────┘
```

### Back-end (`backend/app`)

```
api/v1/routes/     endpoints HTTP (auth, samples, custody, tests, capas, audit, users)
api/deps.py        autenticação, RBAC e dependência de assinatura eletrônica
services/          regras de negócio e unidades de trabalho atômicas
models/            ORM, enums e tipos SQL
schemas/           contratos Pydantic de entrada/saída
core/              config, security (JWT/Argon2/HMAC), RBAC, erros, serialização
db/                engine async, init_db e SQL de triggers/indexes
seed.py            dados de demonstração
```

Princípios aplicados:

- **Unidade de trabalho atômica**: alteração de negócio + evento de auditoria
  + consumo da assinatura são commitados juntos. Se qualquer etapa falhar,
  nada é gravado.
- **UUID gerado no cliente** para registros novos: a intenção da assinatura é
  vinculada ao `entity_id` antes do `INSERT`.
- **Assinatura em duas etapas**: `POST /auth/sign` reautentica a senha e
  emite um token de uso único, curto e vinculado a
  `(usuário, tipo de entidade, id, ação)`. A rota de negócio consome o token
  via header `X-Signature-Token`.
- **Trilha append-only**: cada evento tem `sequence`, `prev_hash`, `hash`
  SHA-256 do conteúdo canônico e `hmac` com chave mantida fora do banco.
- **Exportação assinada**: a trilha pode ser baixada em CSV/JSON dentro de um
  ZIP com manifesto SHA-256/HMAC, arquivo canônico `events.jsonl` e endpoint
  de verificação que ancora a cabeça exportada no banco atual.
- **Resultados imutáveis**: cada laudo gera uma versão de `LabTestResult`;
  correções exigem `amendment_reason` e criam nova versão.
- **CAPA automática**: resultado `REPROVADO` abre CAPA (`auto_opened=true`)
  na mesma transação e retorna um `TestAlert` ao cliente.
- **Reteste sem rebaixamento silencioso**: amostra `APROVADO` não aceita novo
  ensaio; a reabertura `APROVADO → EM_TESTE` é uma transição assinada
  (`PATCH /samples/{id}/status`), disponível na tela de entrada.

### Front-end (`frontend/src`)

```
pages/Dashboard.tsx    entrada da amostra + timeline/cadeia de custódia
pages/Tests.tsx        lançamento de resultado + "Salvar e assinar laudo"
pages/Capas.tsx        gestão de CAPAs com verificação de eficácia
pages/AuditTrail.tsx   consulta com filtros + verificação da cadeia
hooks/use-auth.tsx     sessão, refresh e timeout de inatividade
hooks/use-esignature.tsx  modal de reautenticação e motivo da assinatura
lib/api.ts             cliente HTTP, refresh automático e tratamento de erros
components/ui/         primitivas acessíveis no estilo shadcn/ui
```

---

## 3. Como executar

### 3.1 Docker Compose (recomendado)

Pré-requisitos: Docker Desktop com Compose v2.

```bash
cp .env.example .env          # opcional: ajuste segredos e portas
docker compose up --build
```

Serviços:

| Serviço | URL |
| --- | --- |
| Aplicação web | http://localhost:8080 |
| Swagger / OpenAPI | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |
| PostgreSQL | `localhost:5432` (lims/lims) |

O serviço `migrate` executa `alembic upgrade head` antes da API. O `api` só
inicia após a migração concluir com sucesso e roda com
`AUTO_CREATE_SCHEMA=false` — o startup não executa DDL. Para aplicar novas
revisões em um ambiente já em execução:

```bash
docker compose run --rm migrate
docker compose restart api
```

Popular dados de demonstração (execução única; o script ignora se já houver
usuários):

```bash
docker compose --profile tools run --rm seed
```

> O `seed` cria amostras, transferências de custódia, laudos assinados, uma
> CAPA automática e uma CAPA manual. A cadeia de auditoria gerada é real; as
> assinaturas do seed são fixtures já consumidas. O fluxo interativo de
> reautenticação é exercitado pela interface.

Validar a stack como no CI (health da API, SPA pelo Nginx, login, amostras e
verificação da trilha):

```bash
bash scripts/docker-smoke.sh
```

### 3.2 Desenvolvimento local

Back-end:

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

# PostgreSQL local com usuário/senha/base "lims"
export DATABASE_URL="postgresql+asyncpg://lims:lims@localhost:5432/lims"
export AUTO_CREATE_SCHEMA=false
python -m alembic upgrade head     # mesmo caminho da produção
python -m app.seed                 # opcional: dados de demonstração
uvicorn app.main:app --reload
```

> Em desenvolvimento sem Alembic, `AUTO_CREATE_SCHEMA=true` (padrão) cria o
> schema com `create_all` + `app/db/sql/*.sql`. Em produção use sempre
> `AUTO_CREATE_SCHEMA=false` e migrações versionadas.

Front-end:

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (proxy /api → localhost:8000)
```

Verificações:

```bash
cd backend
.venv/Scripts/python.exe -m pytest -q       # Windows
# .venv/bin/python -m pytest -q             # Linux/macOS
.venv/Scripts/python.exe -m ruff check app tests
.venv/Scripts/python.exe -m mypy app
.venv/Scripts/python.exe -m compileall -q app

cd ../frontend
npm run typecheck
npm run build      # tsc --noEmit && vite build
```

> Para rodar a API sem PostgreSQL (apenas import/OpenAPI), use
> `DATABASE_URL=sqlite+aiosqlite:///./local.db`. Os triggers de imutabilidade
> são específicos de PostgreSQL e não são instalados nesse modo.

#### Testes de integração contra PostgreSQL

Por padrão a suíte usa SQLite temporário (rápido). Para exercitar triggers,
sequences nativas e advisory lock, aponte `LIMS_TEST_DATABASE_URL` para um
banco de teste — cada teste cria e destrói um schema isolado, com os arquivos
`app/db/sql/*.sql` aplicados:

```bash
export LIMS_TEST_DATABASE_URL="postgresql+asyncpg://lims:lims@localhost:5432/lims_test"
.venv/Scripts/python.exe -m pytest -q
```

Resultado de referência: **47 passando + 4 ignorados** em SQLite e **51
passando** em PostgreSQL 16. Os testes ignorados sem PostgreSQL são os de
trigger/sequence/advisory lock (`tests/test_postgres_guards.py`).

#### Migrações (Alembic)

```bash
cd backend
export DATABASE_URL="postgresql+asyncpg://lims:lims@localhost:5432/lims"

python -m alembic upgrade head        # aplica até a última revisão
python -m alembic current             # revisão aplicada
python -m alembic check               # metadata x schema (deve dizer "No new ...")
python -m alembic downgrade -1        # reverte a última revisão
python -m alembic revision --autogenerate -m "descrição"
```

- `a1cd5ac5805f` — schema inicial (tabelas, enums, constraints e índices).
- `0002_guards` — snapshot imutável de `app/db/sql/*.sql`: sequences nativas,
  triggers append-only e índices de consulta.
- O `env.py` lê `DATABASE_URL`; o `alembic.ini` não guarda credenciais.
- Antes de gerar uma revisão, rode `alembic check` para confirmar paridade.
  O CI executa `upgrade head` e `check` a cada push.

`tests/test_api_flow.py` sobe a aplicação FastAPI com `httpx.ASGITransport` e
um banco temporário por teste, cobrindo: login/perfil/RBAC, exigência de
assinatura, uso único do token, vínculo ao registro, autorização de custódia,
reprovação com CAPA automática, imutabilidade lógica do laudo (emenda),
bloqueio de aprovação manual, rotação/roubo de refresh token, adulteração da
trilha, expiração de assinatura, bloqueio de conta por senha errada na
assinatura e rate limiting (429 + `Retry-After`).

### 3.3 Contas de demonstração

| Usuário | Senha | Perfil |
| --- | --- | --- |
| `fiscal` | `Fiscal@Lims2026` | Fiscal sanitário |
| `tecnico` | `Tecnico@Lims2026` | Técnico de laboratório |
| `auditor` | `Auditor@Lims2026` | Auditor da qualidade |
| `admin` | `Admin@Lims2026` | Administrador |
| `custodiante` | `Custodia@Lims2026` | Custodiante |

As três primeiras aparecem na tela de login apenas como atalho de
desenvolvimento. **Remova esse bloco antes de qualquer implantação real.**

---

## 4. Fluxo de assinatura eletrônica (exemplo `curl`)

Toda rota que grava dados exige **duas coisas**: JWT de acesso e um token de
assinatura de uso único. O token de assinatura é emitido por
`POST /api/v1/auth/sign` depois de o usuário informar novamente a senha, o
significado e o motivo da assinatura.

### 4.1 Autenticar

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=fiscal&password=Fiscal@Lims2026" | jq -r .access_token)
```

### 4.2 Registrar uma amostra

O `id` é gerado pelo cliente para que a assinatura seja vinculada ao registro
antes do `INSERT`.

```bash
SAMPLE_ID=$(python -c "import uuid; print(uuid.uuid4())")

SIG=$(curl -s -X POST http://localhost:8000/api/v1/auth/sign \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"password\": \"Fiscal@Lims2026\",
    \"meaning\": \"AUTORIA\",
    \"reason\": \"Registro de entrada da amostra para fiscalização pós-mercado.\",
    \"entity_type\": \"DeviceSample\",
    \"entity_id\": \"$SAMPLE_ID\",
    \"action\": \"CREATE\"
  }" | jq -r .token)

curl -s -X POST http://localhost:8000/api/v1/samples \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Signature-Token: $SIG" \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"$SAMPLE_ID\",
    \"commercial_name\": \"Monitor de Sinais Vitais VitalOne 5\",
    \"manufacturer\": \"Vital Devices Ltda.\",
    \"serial_number\": \"SN-2026-0041\",
    \"lot_number\": \"L2026-041\",
    \"registration_number\": \"80012345678\",
    \"storage_location\": \"Prateleira B3 — Sala de amostras\",
    \"description\": \"Apreensão por suspeita de desvio de desempenho.\"
  }" | jq
```

A resposta contém `sample`, `audit_log_id`, `signature_id` e `qr_code_url`.

### 4.3 Programar e assinar um ensaio

```bash
TEST_ID=$(python -c "import uuid; print(uuid.uuid4())")

SIG=$(curl -s -X POST http://localhost:8000/api/v1/auth/sign \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{
    \"password\": \"Fiscal@Lims2026\",
    \"meaning\": \"AUTORIA\",
    \"reason\": \"Programação do ensaio de resistência mecânica.\",
    \"entity_type\": \"LabTest\",
    \"entity_id\": \"$TEST_ID\",
    \"action\": \"CREATE\"
  }" | jq -r .token)

curl -s -X POST http://localhost:8000/api/v1/tests \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Signature-Token: $SIG" \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"$TEST_ID\",
    \"device_sample_id\": \"$SAMPLE_ID\",
    \"name\": \"Resistência mecânica\",
    \"method\": \"ABNT NBR IEC 60601-1\",
    \"unit\": \"N\",
    \"lower_limit\": 10,
    \"upper_limit\": 50
  }" | jq
```

Resultado **dentro** da faixa (aprovado):

```bash
SIG=$(curl -s -X POST http://localhost:8000/api/v1/auth/sign \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{
    \"password\": \"Fiscal@Lims2026\",
    \"meaning\": \"RESPONSABILIDADE_TECNICA\",
    \"reason\": \"Lançamento e assinatura do resultado do ensaio.\",
    \"entity_type\": \"LabTest\",
    \"entity_id\": \"$TEST_ID\",
    \"action\": \"UPDATE\"
  }" | jq -r .token)

curl -s -X PATCH http://localhost:8000/api/v1/tests/$TEST_ID/result \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Signature-Token: $SIG" \
  -H "Content-Type: application/json" \
  -d "{ \"result_value\": 32.5, \"version\": 1 }" | jq
```

Se `result_value` estiver fora dos limites, a resposta traz
`alert.code = "RESULTADO_REPROVADO"`, `capa_id` preenchido e a CAPA é criada
automaticamente. Um valor fora da faixa **não pode** ser aprovado
manualmente, um resultado inconclusivo mantém a amostra em `EM_TESTE` e
nenhum desfecho pode ser assinado sem evidência registrada (valor numérico
ou texto descritivo).

### 4.4 Verificar a integridade da trilha

```bash
curl -s -X POST "http://localhost:8000/api/v1/audit/verify" \
  -H "Authorization: Bearer $AUDITOR_TOKEN" | jq
```

A própria verificação é registrada como evento `INTEGRITY_CHECK`.

### 4.5 Exportar e verificar a trilha assinada

O perfil `AUDITOR` (ou `ADMIN`) exporta o recorte atual da tela em um pacote
ZIP. O pacote contém:

| Arquivo | Papel |
| --- | --- |
| `manifest.json` | Escopo, contagem, âncora/cabeça, hashes e HMAC |
| `events.jsonl` | Registros canônicos, um por linha — dado verificável |
| `events.csv` ou `events.json` | Apresentação legível do mesmo recorte |

```bash
# Exporta tudo em CSV (os mesmos filtros da consulta são aceitos)
curl -s -X POST "http://localhost:8000/api/v1/audit/export" \
  -H "Authorization: Bearer $AUDITOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"format":"csv"}' \
  -o trilha-auditoria.zip

# Exporta apenas eventos de login de um usuário em um intervalo
curl -s -X POST "http://localhost:8000/api/v1/audit/export" \
  -H "Authorization: Bearer $AUDITOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "format":"json",
    "action":"LOGIN",
    "search":"auditor",
    "date_from":"2026-11-01T00:00:00Z",
    "date_to":"2026-11-30T23:59:59Z"
  }' \
  -o trilha-logins.zip

# Verifica o arquivo entregue ao inspetor
curl -s -X POST "http://localhost:8000/api/v1/audit/export/verify" \
  -H "Authorization: Bearer $AUDITOR_TOKEN" \
  -F "file=@trilha-auditoria.zip" | jq
```

A verificação recalcula o hash/HMAC do manifesto e de cada arquivo, valida a
cadeia interna dos registros e compara a âncora e a cabeça exportadas com o
banco atual. Exportação e verificação geram, respectivamente, os eventos
`EXPORT` e `EXPORT_VERIFIED`. O recorte é limitado por
`AUDIT_EXPORT_MAX_RECORDS` (50.000) e o upload por `AUDIT_EXPORT_MAX_BYTES`
(25 MiB), configuráveis por variável de ambiente.

---

## 5. Superfície da API

| Método | Rota | Descrição |
| --- | --- | --- |
| POST | `/auth/login` | OAuth2 password grant |
| POST | `/auth/refresh` | Rotação de refresh token |
| POST | `/auth/logout` | Revogação da sessão |
| GET | `/auth/me` | Perfil e permissões |
| POST | `/auth/sign` | Reautenticação + token de assinatura |
| POST | `/auth/change-password` | Troca de senha (invalida sessões) |
| POST | `/samples` | Entrada de amostra (assinada) |
| GET | `/samples` | Lista paginada com busca/status |
| GET | `/samples/{id}` | Detalhe |
| GET | `/samples/{id}/timeline` | Linha do tempo consolidada |
| GET | `/samples/{id}/custody` | Histórico de custódia |
| GET | `/samples/{id}/signatures` | Manifestos de assinatura |
| GET | `/samples/{id}/qrcode` | QR lógico assinado |
| GET | `/samples/{id}/qrcode.png` | Etiqueta PNG |
| GET | `/samples/verify?token=` | Validação do QR |
| PATCH | `/samples/{id}/status` | Mudança de status (assinada) |
| POST | `/custody/transfer` | Transferência de guarda (assinada) |
| GET | `/custody/{id}/history` | Histórico |
| POST | `/tests` | Programar ensaio (assinado) |
| GET | `/tests` | Lista paginada |
| GET | `/tests/{id}` | Detalhe |
| GET | `/tests/{id}/history` | Versões imutáveis do laudo |
| PATCH | `/tests/{id}/result` | Resultado + assinatura + auto-CAPA |
| GET/POST | `/capas` | Lista / abertura manual (assinada) |
| GET/PATCH | `/capas/{id}` | Detalhe / atualização (assinada) |
| GET | `/audit` | Consulta (ADMIN/AUDITOR) |
| GET | `/audit/{id}` | Detalhe com hashes |
| POST | `/audit/verify` | Verificação da cadeia |
| POST | `/audit/export` | Exportação assinada CSV/JSON (ADMIN/AUDITOR) |
| POST | `/audit/export/verify` | Verificação do arquivo exportado |
| GET/POST | `/users` | Lista / criação (ADMIN, assinada) |

Swagger: `http://localhost:8000/docs`. O fluxo de login pode ser usado no
botão **Authorize** (OAuth2 password flow).

---

## 6. Mapa de conformidade

> Este mapa descreve **como o MVP endereça** cada controle. Ele não substitui
> validação formal, qualificação de fornecedores, SOPs, treinamento nem
> auditoria regulatória.

### 21 CFR Part 11

| Requisito | Implementação no MVP |
| --- | --- |
| §11.10(a) — validação e controle de sistemas | Testes de domínio (`pytest`), tipagem Pydantic, migrações versionadas com Alembic e `alembic check` no CI |
| §11.10(b) — cópias legíveis e exatas | Endpoints de consulta, histórico de versões, timeline, detalhe de auditoria com JSON canônico e exportação assinada em CSV/JSON |
| §11.10(c) — retenção e recuperação | Registros persistidos; trilha append-only; triggers impedem `UPDATE`/`DELETE`/`TRUNCATE` |
| §11.10(d) — acesso limitado | JWT de curta duração, RBAC por rota, bloqueio por tentativas, invalidação por `token_version` |
| §11.10(e) — trilha de auditoria independente | `audit_log` com sequência, hash SHA-256 encadeado e HMAC; eventos de login, assinatura, integridade e negócio |
| §11.10(f) — checagens de sequência | Máquina de estados de amostra/ensaio/CAPA; `version` otimista; `sequence` monotônica na auditoria |
| §11.10(g) — checagem de autoridade | RBAC revalidado no servidor em toda rota; assinatura vinculada ao usuário emissor |
| §11.10(h) — checagem de dispositivo | Fora do escopo do MVP (sem integração com instrumentos) |
| §11.50 — manifestação da assinatura | Manifesto com nome, usuário, papel, registro profissional, data/hora UTC, significado e motivo |
| §11.70 — vínculo assinatura/registro | `manifest_hash`, `payload_snapshot` e `payload_hash` gravados uma única vez e protegidos por trigger |
| §11.100 — unicidade | Uma conta por usuário; senha individual com Argon2id; assinatura sempre vinculada ao `user_id` |
| §11.200 — dois componentes | Senha + token de intenção de uso único, curto e vinculado ao registro/ação |
| §11.300 — controles de senha | Política mínima, bloqueio temporário, rotação de refresh, revogação em troca de senha |

### Anvisa RDC 665/2022 (princípios aplicáveis)

- **Rastreabilidade**: accession único, QR assinado, timeline e histórico de
  custódia por amostra.
- **Cadeia de custódia**: eventos append-only com origem, destino, local,
  lacre, motivo e assinatura de quem transfere.
- **Integridade de dados**: resultados versionados e imutáveis; emendas
  justificadas; auditoria encadeada.
- **CAPA**: abertura automática em reprovação e gestão com causa raiz, plano
  de ação, responsável, prazo e verificação de eficácia.
- **Retenção**: registros finais (laudos, custódia, CAPA encerrada) não podem
  ser alterados; exclusão bloqueada no banco.

### ALCOA+

| Princípio | Como é atendido |
| --- | --- |
| **A**tribuível | Todo evento guarda usuário, papel, IP e request ID |
| **L**egível | Respostas tipadas, UI em pt-BR e exportação JSON canônica |
| **C**ontemporâneo | Timestamps UTC gerados no servidor no momento da gravação |
| **O**riginal | Versões imutáveis de resultados; trilha append-only |
| **A**curate | Validação de faixa, desfecho obrigatório e verificação de integridade |
| **+** completo, consistente, durável, disponível | Encadeamento de hash, constraints, retenção e backup do PostgreSQL |

---

## 7. Segurança e limitações conhecidas

Controles implementados:

- Senhas com **Argon2id**; nunca retornadas pela API.
- Access token JWT de 30 min (configurável) e refresh token **de uso único**
  com rotação. Reutilização de refresh revoga a família de sessões e
  incrementa `token_version`.
- Timeout de inatividade no cliente (15 min por padrão), sincronizado com
  `/api/v1/meta`.
- Bloqueio temporário após tentativas de login inválidas, com auditoria
  atômica de sucesso e falha. O **mesmo contador** é usado na reautenticação
  de `/auth/sign`: senha errada na assinatura também bloqueia a conta.
- Rate limiting por janela deslizante em `/auth/login` (por IP) e `/auth/sign`
  (por usuário), com resposta `429` e cabeçalho `Retry-After`.
- Cabeçalhos de segurança na API e no Nginx; CSP restritiva na SPA.
- Segredos de desenvolvimento são recusados quando `ENVIRONMENT=prod`.
- Token de assinatura com TTL de 5 min, uso único e vínculo ao registro,
  ação, usuário e motivo; tentativas inválidas geram `SIGNATURE_REJECTED`.
- Triggers PostgreSQL impedem alteração/exclusão da auditoria e reescrita de
  assinaturas consumidas.

Limitações do MVP (não aptas a produção sem trabalho adicional):

1. **Rate limiting por processo**: a janela deslizante é mantida em memória.
   Com múltiplos workers o limite efetivo é multiplicado pelo número de
   processos; para um teto global exato, use Redis ou o rate limiting do
   proxy/ingress.
2. **Append-only lógico**: um superusuário do PostgreSQL pode desabilitar
   triggers. Recomenda-se WORM/object lock, backup imutável e ancoragem
   externa do `head_hash`.
3. **Sem MFA/SSO**: a assinatura usa senha + token de intenção. MFA/IdP
   corporativo é evolução natural.
4. **Sem anexos**: laudos, fotos e certificados não são armazenados; o modelo
   guarda metadados e resultados.
5. **Sem notificações**: CAPAs não enviam e-mail/push; a gestão é feita na UI.
6. **Contas demo visíveis**: o bloco de atalhos da tela de login deve ser
   removido em produção.
7. **Sem testes E2E de navegador**: a validação de front-end é manual/
   typecheck; não há Playwright/Cypress neste MVP.
8. **Cobertura PostgreSQL no CI**: a suíte roda em SQLite por padrão e em
   PostgreSQL quando `LIMS_TEST_DATABASE_URL` está definido. O workflow
   `.github/workflows/ci.yml` executa as duas modalidades (com serviço
   PostgreSQL 16), o build do front-end e um job Docker que constrói as
   imagens e roda `scripts/docker-smoke.sh` na stack completa.
9. **Sem qualificação formal**: este repositório é uma base técnica, não um
   sistema validado (IQ/OQ/PQ) nem um dossiê regulatório.

---

## 8. Estrutura do repositório

```
LIMS/
├── backend/
│   ├── app/
│   │   ├── api/            rotas e dependências
│   │   ├── core/           config, segurança, RBAC, erros
│   │   ├── db/             engine, init_db, SQL de triggers
│   │   ├── models/         ORM
│   │   ├── schemas/        contratos Pydantic
│   │   ├── services/       regras de negócio
│   │   ├── main.py         aplicação FastAPI
│   │   └── seed.py         dados de demonstração
│   ├── alembic/           migrações versionadas (env.py + versions/)
│   ├── tests/              testes de domínio e integração
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/     layout e primitivas de UI
│   │   ├── hooks/          auth e assinatura eletrônica
│   │   ├── lib/            cliente HTTP, tipos e utilitários
│   │   ├── pages/          telas
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 9. Licença e uso

Projeto de demonstração para uso interno e avaliação técnica. Dados de
demonstração são fictícios. Não utilize em ambiente regulado sem validação
formal, revisão de segurança independente e adequação aos requisitos da
organização.
