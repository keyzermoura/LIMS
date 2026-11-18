# EGLM-006 — Relatório de Correção do Isolamento e Confiabilidade dos Testes PostgreSQL

**Iniciativa:** Evolução de Governança e Metrologia (`EGLM-006`)  
**Repositório:** https://github.com/keyzermoura/LIMS  
**Issue de referência:** https://github.com/keyzermoura/LIMS/issues/4 (`[EGLM-006] Corrigir isolamento e confiabilidade dos testes PostgreSQL`)  
**Data:** 18/11/2026  

---

## 1. Identificação de Branch, Commits e Arquivos Alterados

| Item | Valor Observado |
|---|---|
| **Branch de origem (`main`)** | `main` |
| **Commit de origem (`main` HEAD)** | `6e7354d4c1d696d140ccd2d08125dac50c32f577` |
| **Branch de trabalho** | `fix/eglm-006-postgres-test-isolation` |
| **Commit da correção técnica** | [`5f90764595c1b2f4e851251a4512fad95eeec1df`](https://github.com/keyzermoura/LIMS/commit/5f90764595c1b2f4e851251a4512fad95eeec1df) |
| **Mensagem do commit técnico** | `fix(tests): isolate PostgreSQL test schema and install phase 5 SQL guards (EGLM-006)` |
| **Nota sobre a branch de documentação** | Na data de execução (`18/11/2026`), a branch `feature/evolucao-governanca-metrologia` já havia sido incorporada/removida do remoto, estando a documentação da iniciativa (`docs/evolucao-governanca-metrologia/01` a `06` e `README.md`) na `main` e o relatório `EGLM-005-RELATORIO.md` disponível localmente no workspace |

### Arquivos Alterados na Correção

| Arquivo | Alteração | Resumo |
|---|---|---|
| `backend/tests/conftest.py` | Modificado (`+9 / -2`) | Passa a instalar os três scripts SQL (`001_immutability.sql`, `002_indexes.sql`, `003_integridade_fase5.sql`) via `SQL_FILES` no schema isolado de cada teste |
| `backend/tests/test_postgres_guards.py` | Modificado (`+73 / -7`) | Filtra `pg_trigger` exclusivamente pelo schema corrente (`current_schema()`) e `NOT t.tgisinternal`, amplia `expected_triggers` para todas as 23 triggers esperadas e adiciona o teste de isolamento negativo `test_trigger_lookup_ignores_other_schemas_and_detects_missing_trigger` |
| `backend/tests/test_migrations_postgres.py` | Modificado (`+7 / -2`) | Filtra a verificação de `trg_audit_logs_append_only` em `pg_trigger` por `n.nspname = current_schema()` e `NOT t.tgisinternal` |
| `docs/evolucao-governanca-metrologia/EGLM-006-RELATORIO.md` | Adicionado | Este relatório técnico com evidências reproduzíveis |

Nenhuma funcionalidade da aplicação foi alterada; nenhum dado real ou banco de produção foi acessado; nenhum merge na `main` foi realizado e a Issue #4 permanece aberta para revisão.

---

## 2. Problema Identificado e Causa Raiz

### 2.1 Diagnóstico Técnico Confirmado

A inspeção de `backend/tests/conftest.py`, `backend/app/db/database.py`, `backend/app/db/sql/*.sql`, `backend/tests/test_postgres_guards.py` e `backend/tests/test_migrations_postgres.py` confirmou duas falhas combinadas de isolamento:

1. **Omissão de `003_integridade_fase5.sql` na preparação do schema isolado (`backend/tests/conftest.py:62-68`):**
   - Enquanto `backend/app/db/database.py` (`init_db`, linhas `1236-1238` no commit `6e7354d`) instala em ordem `001_immutability.sql`, `002_indexes.sql` e `003_integridade_fase5.sql`, a função `_install_sql_files` de `backend/tests/conftest.py` instalava apenas `("001_immutability.sql", "002_indexes.sql")`.
   - Com isso, cada schema isolado `lims_test_<uuid>` criado para os testes de integração PostgreSQL ficava **sem** a sequence `official_report_seq`, **sem** o índice único `uq_instrument_import_dedup` e **sem** as **15 triggers** de integridade da Fase 5 (`trg_official_reports_guard`, `trg_test_executions_freeze`, `trg_test_reviews_freeze`, `trg_test_attachments_append_only`, `trg_instrument_data_guard`, `trg_training_records_append_only`, `trg_custody_events_append_only`, `trg_solicitations_no_delete`, `trg_solicitation_items_no_delete`, `trg_receipts_no_delete`, `trg_receipt_items_no_delete`, `trg_custody_objects_no_delete`, `trg_receipt_decisions_no_delete`, `trg_coordination_reviews_no_delete`, `trg_analyst_qualifications_no_delete`).

2. **Consulta global a `pg_trigger` sem filtro de schema (`backend/tests/test_postgres_guards.py:183` e `backend/tests/test_migrations_postgres.py:271`):**
   - `test_trigger_parity_phase5` consultava `SELECT tgname FROM pg_trigger WHERE tgname LIKE 'trg_%'`, retornando triggers de **todos os schemas** do banco PostgreSQL.
   - No pipeline do CI (`.github/workflows/ci.yml`), o passo `alembic upgrade head` é executado previamente contra o schema `public` do mesmo banco `lims_test`. Assim, quando `test_trigger_parity_phase5` rodava posteriormente em seu schema isolado `lims_test_<uuid>`, a consulta enxergava as triggers residuais do schema `public`, gerando um **falso-positivo**.
   - Da mesma forma, `test_upgrade_head_creates_schema_without_drift` em `backend/tests/test_migrations_postgres.py` consultava `SELECT tgname FROM pg_trigger WHERE tgname = 'trg_audit_logs_append_only'` sem restringir ao schema corrente.

### 2.2 Reprodução da Falha Antes da Correção

Executando o código original (`6e7354d4c1d696d140ccd2d08125dac50c32f577`) contra um PostgreSQL 16.8 limpo (schema `public` sem migrações prévias):

```text
tests/test_postgres_guards.py::test_audit_log_blocks_update_delete_and_truncate PASSED [ 20%]
tests/test_postgres_guards.py::test_electronic_signature_manifest_is_immutable PASSED [ 40%]
tests/test_postgres_guards.py::test_native_sequences_are_monotonic PASSED [ 60%]
tests/test_postgres_guards.py::test_advisory_lock_serializes_the_hash_chain PASSED [ 80%]
tests/test_postgres_guards.py::test_trigger_parity_phase5 FAILED         [100%]
...
======================== 1 failed, 4 passed in 13.01s =========================
```

### 2.3 Revisão de Outras Consultas a Catálogos PostgreSQL nos Testes

Foram inspecionados todos os arquivos em `backend/tests/*.py` e `backend/app/**/*.py` para referências a `pg_*`, `information_schema`, `current_schema`, `search_path`, `public.` e `nextval`:
- `test_migrations_postgres.py`:
  - `_tables()` filtra por `WHERE schemaname = 'public'` (correto, pois testa um banco dedicado onde o Alembic cria as tabelas no schema `public`).
  - `_enum_counts()` filtra por `n.nspname = 'public'` (correto no banco descartável do Alembic).
  - `test_downgrade_is_reversible()` filtra `information_schema.columns` por `table_schema = 'public'` (correto).
  - `test_upgrade_head_creates_schema_without_drift()` consultava `pg_trigger` sem filtro de schema — **corrigido neste PR**.
- `backend/app/db/dialect.py`:
  - `next_sequence()` usa `CREATE SEQUENCE IF NOT EXISTS {name}` e `nextval('{name}')`, que resolvem via `search_path` da conexão (no `_postgres_factory()`, `search_path` está restrito exclusivamente ao schema `lims_test_<uuid>`).
- `backend/app/services/audit_service.py`:
  - `pg_advisory_xact_lock(:key)` opera em nível de banco para serializar a cadeia de auditoria (comportamento esperado).

---

## 3. Descrição das Correções Implementadas

1. **`backend/tests/conftest.py`:**
   - Definida a constante `SQL_FILES`:
     ```python
     SQL_FILES: tuple[str, ...] = (
         "001_immutability.sql",
         "002_indexes.sql",
         "003_integridade_fase5.sql",
     )
     ```
   - `_install_sql_files(engine)` agora executa sequencialmente os três scripts no schema isolado `lims_test_<uuid>`, respeitando a dependência de ordem (`003_integridade_fase5.sql` utiliza funções definidas em `001_immutability.sql`, como `lims_reject_mutation()` e `lims_reject_delete()`).

2. **`backend/tests/test_postgres_guards.py`:**
   - Adicionado helper `_fetch_schema_triggers(db)`:
     ```sql
     SELECT t.tgname
     FROM pg_trigger t
     JOIN pg_class c ON c.oid = t.tgrelid
     JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = current_schema()
     AND NOT t.tgisinternal
     AND t.tgname LIKE 'trg_%'
     ```
   - Atualizado `test_trigger_parity_phase5` para:
     - Validar que `current_schema()` inicia com `"lims_test_"`.
     - Verificar todas as **23 triggers** definidas em `001_immutability.sql` (8 triggers, incluindo `trg_audit_logs_no_truncate`) e `003_integridade_fase5.sql` (15 triggers, incluindo `trg_solicitation_items_no_delete` e `trg_receipt_items_no_delete`).
     - Falhar informando explicitamente o nome do schema isolado e a lista ordenada de triggers ausentes (`assert not missing`).
   - Adicionado o teste `test_trigger_lookup_ignores_other_schemas_and_detects_missing_trigger`:
     - Cria um schema auxiliar temporário (`lims_other_<uuid>`) com uma tabela e trigger homônima (`trg_official_reports_guard`),
     - Remove `trg_official_reports_guard` da tabela `official_reports` no schema de teste corrente,
     - Comprova que a trigger existe no schema auxiliar, mas que `_fetch_schema_triggers(db)` **não** a retorna e detecta a ausência no schema corrente do teste,
     - Remove o schema auxiliar no bloco `finally`.

3. **`backend/tests/test_migrations_postgres.py`:**
   - Atualizada a query em `test_upgrade_head_creates_schema_without_drift` para juntar `pg_trigger`, `pg_class` e `pg_namespace` com `WHERE n.nspname = current_schema() AND NOT t.tgisinternal AND t.tgname = 'trg_audit_logs_append_only'`.

---

## 4. Ambiente e Configuração do PostgreSQL

### Ambiente Local Isolado (Windows 10 Pro)

| Item | Configuração |
|---|---|
| **SGBD** | `PostgreSQL 16.8, compiled by Visual C++ build 1942, 64-bit` |
| **Instância** | Cluster portátil isolado em diretório temporário (`scratch/e006/pgdata`), porta `55432` |
| **Encoding / Locale** | `UTF8` / `C` (`initdb -U lims -A trust --encoding=UTF8 --locale=C`) |
| **Banco de teste** | `lims_test`, limpo (`public_tables = 0`, `public_triggers = 0`) |
| **URL de teste** | `LIMS_TEST_DATABASE_URL="postgresql+asyncpg://lims:lims@localhost:55432/lims_test"` |
| **Python / Ferramentas** | Python `3.11.14`, `pytest 9.2.0`, `pytest-asyncio 1.5.0`, `asyncpg 0.32.0`, `SQLAlchemy 2.0.58`, `ruff 0.17.5`, `mypy 2.4.1` |

### Ambiente de CI (GitHub Actions)

- **Runner:** `ubuntu-latest`, Python `3.12`
- **Serviço:** `postgres:16-alpine` (`POSTGRES_USER: lims`, `POSTGRES_PASSWORD: lims`, `POSTGRES_DB: lims_test`, porta `5432`)

---

## 5. Comandos Executados e Resultados

### 5.1 Verificação Estática (`ruff` e `mypy`)

```powershell
.\.venv\Scripts\python.exe -m ruff check app tests
# Saída: All checks passed! (exit code 0)

.\.venv\Scripts\python.exe -m mypy app
# Saída: Success: no issues found in 155 source files (exit code 0)
```

### 5.2 Evidência do Teste Negativo (Ausência de Trigger Detectada Mesmo com Objeto em `public`)

Para comprovar que uma trigger presente em `public` não mascara mais uma falha no schema isolado:

1. Criou-se no schema `public` do banco `lims_test` uma tabela `public.dummy_reports` com uma trigger chamada `trg_official_reports_guard`:
   ```sql
   CREATE TABLE public.dummy_reports (id integer);
   CREATE OR REPLACE FUNCTION public.dummy_guard() RETURNS trigger LANGUAGE plpgsql AS $body$
   BEGIN
       RETURN NEW;
   END;
   $body$;
   CREATE TRIGGER trg_official_reports_guard
   BEFORE UPDATE ON public.dummy_reports
   FOR EACH ROW EXECUTE FUNCTION public.dummy_guard();
   ```
   Confirmação via `psql`:
   ```text
    nspname |           tgname           
   ---------+----------------------------
    public  | trg_official_reports_guard
   (1 linha)
   ```
2. Simulou-se a remoção de `"003_integridade_fase5.sql"` da tupla `SQL_FILES` em `backend/tests/conftest.py` e executou-se:
   ```powershell
   $env:LIMS_TEST_DATABASE_URL = "postgresql+asyncpg://lims:lims@localhost:55432/lims_test"
   .\.venv\Scripts\python.exe -m pytest tests/test_postgres_guards.py -k test_trigger_parity_phase5 -v
   ```
3. **Resultado observado (`NEGATIVE_TEST_EXIT=1` — FALHOU conforme esperado):**
   ```text
   tests/test_postgres_guards.py::test_trigger_parity_phase5 FAILED [100%]
   ...
   E AssertionError: Triggers ausentes no schema lims_test_fcee8890261c4438: ['trg_analyst_qualifications_no_delete', 'trg_coordination_reviews_no_delete', 'trg_custody_events_append_only', 'trg_custody_objects_no_delete', 'trg_instrument_data_guard', 'trg_official_reports_guard', 'trg_receipt_decisions_no_delete', 'trg_receipt_items_no_delete', 'trg_receipts_no_delete', 'trg_solicitation_items_no_delete', 'trg_solicitations_no_delete', 'trg_test_attachments_append_only', 'trg_test_executions_freeze', 'trg_test_reviews_freeze', 'trg_training_records_append_only']
   ======================= 1 failed, 5 deselected in 3.64s =======================
   ```
4. **Restauração:** O arquivo `backend/tests/conftest.py` foi restaurado ao estado corrigido e o schema `public` foi limpo com `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`, validando `public_tables = 0` e `public_triggers = 0`.

### 5.3 Execução Direcionada (`test_postgres_guards.py` e `test_migrations_postgres.py`) em PostgreSQL 16.8 Limpo

```powershell
$env:LIMS_TEST_DATABASE_URL = "postgresql+asyncpg://lims:lims@localhost:55432/lims_test"
.\.venv\Scripts\python.exe -m pytest tests/test_postgres_guards.py tests/test_migrations_postgres.py -v -ra
```

- **Resultado (`TARGETED_PG_EXIT=0`):** **10 passed in 49.81s**
  - `tests/test_postgres_guards.py` (`6 passed`): inclui `test_audit_log_blocks_update_delete_and_truncate`, `test_electronic_signature_manifest_is_immutable`, `test_native_sequences_are_monotonic`, `test_advisory_lock_serializes_the_hash_chain`, `test_trigger_parity_phase5` e `test_trigger_lookup_ignores_other_schemas_and_detects_missing_trigger`.
  - `tests/test_migrations_postgres.py` (`4 passed`): `test_upgrade_head_creates_schema_without_drift`, `test_downgrade_is_reversible`, `test_additive_migration_preserves_legacy_rows`, `test_downgrade_refuses_when_it_would_lose_data`.

### 5.4 Execução da Suíte Completa contra PostgreSQL 16.8 Limpo

Com `public_tables = 0` e `public_triggers = 0` confirmados antes da execução:

```powershell
$env:LIMS_TEST_DATABASE_URL = "postgresql+asyncpg://lims:lims@localhost:55432/lims_test"
.\.venv\Scripts\python.exe -m pytest -v -ra
```

- **Resultado (`FULL_PG_PYTEST_EXIT=0`):** **`159 passed, 14 warnings in 405.94s (0:06:45)`** (0 falhos, 0 ignorados).
- Todos os testes de integridade, imutabilidade (`test_api_flow.py`, `test_phase1_simulations.py`, `test_phase3_reviews.py`, `test_phase6_report_amendments.py`, `test_postgres_guards.py`), migrações (`test_migrations_postgres.py`), concorrência/outbox e v1.1.0 passaram no schema isolado com todas as 23 triggers instaladas.

### 5.5 Execução Adicional em Modo SQLite (Regressão sem PostgreSQL)

```powershell
$env:LIMS_TEST_DATABASE_URL = ""
.\.venv\Scripts\python.exe -m pytest -q
```

- **Resultado (`SQLITE_EXIT=0`):** **`149 passed, 10 skipped, 14 warnings in 259.99s (0:04:19)`** (os 10 ignorados correspondem aos 6 testes de `test_postgres_guards.py` e aos 4 testes de `test_migrations_postgres.py`).

---

## 6. Resultado do CI (GitHub Actions)

O commit [`5f90764595c1b2f4e851251a4512fad95eeec1df`](https://github.com/keyzermoura/LIMS/commit/5f90764595c1b2f4e851251a4512fad95eeec1df) na branch `fix/eglm-006-postgres-test-isolation` disparou o workflow `CI`:

- **Workflow Run:** [#44291439869](https://github.com/keyzermoura/LIMS/actions/runs/44291439869)
- **Status / Conclusão:** `completed` / **`success`** (`2026-11-18T11:05:21Z` – `2026-11-18T11:11:56Z`)
- **Jobs executados:**
  1. `Front-end (typecheck e build)` (`#134757510831`): **`success`** (`11:05:39Z` – `11:06:08Z`)
  2. `Docker (imagens e smoke test)` (`#134757511230`): **`success`** (`11:05:39Z` – `11:06:41Z`)
  3. `Backend (lint, tipos e testes)` (`#134757511308`): **`success`** (`11:05:40Z` – `11:11:56Z`)
     - `Lint (ruff)`: `success`
     - `Tipagem (mypy)`: `success`
     - `Migrações (alembic upgrade head)`: `success`
     - `Paridade metadata x migrações (alembic check)`: `success`
     - `Testes (SQLite)`: `success` (`11:06:18Z` – `11:07:39Z`)
     - `Testes (PostgreSQL 16)`: `success` (`11:07:39Z` – `11:11:53Z`)

---

## 7. Limitações e Riscos Remanescentes

1. **Ordem obrigatória dos scripts SQL:** `003_integridade_fase5.sql` reutiliza funções (`lims_reject_mutation()` e `lims_reject_delete()`) definidas em `001_immutability.sql`. A tupla `SQL_FILES` em `conftest.py` impõe explicitamente a sequência `001` → `002` → `003`, mas futuros scripts em `app/db/sql/` devem ser adicionados manualmente a `SQL_FILES` (ou migrados para um mecanismo único compartilhado com `app/db/database.py`) caso novos arquivos `.sql` sejam criados.
2. **Paridade entre `init_db` e migrações Alembic:** Os testes de integração com `db_factory` continuam construindo tabelas via `Base.metadata.create_all` + `SQL_FILES`, enquanto a suíte de migrações (`test_migrations_postgres.py`) testa as revisões Alembic. Se alguma trigger for adicionada apenas em revisão Alembic sem ser espelhada em `app/db/sql/*.sql` (ou vice-versa), somente uma das frentes detectará a ausência.
3. **Cobertura de `test_downgrade_is_reversible` (fora do escopo da EGLM-006):** Conforme apontado em `EGLM-005`, `test_downgrade_is_reversible` em `backend/tests/test_migrations_postgres.py` ainda não inclui `PHASE7_TABLES`, `PHASE7_ENUMS` e `PHASE8_TABLES` nas asserções de limpeza pós-downgrade (embora `alembic downgrade` e re-`upgrade` estejam passando).
4. **Warnings preexistentes no Pytest:** Permanecem os 14 `PytestCollectionWarning` relativos às classes `TestExecution`, `TestMethod`, `TestStatus` e `TestOutcome`, sem impacto na execução dos testes.
