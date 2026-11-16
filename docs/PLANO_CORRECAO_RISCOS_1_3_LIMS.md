# Plano de Correção — Riscos 1 a 3 (Integridade, Analytics e Segurança)

**Data:** 16/11/2026
**Escopo:** fechamento dos riscos **Alta** identificados no relatório executivo.
**Pré-requisito de leitura:** `RELATORIO_EXECUTIVO_ANALISE_LIMS.md` e `ROADMAP_90_180_365_LIMS.md`.
**Regra:** cada item só é considerado concluído com teste automatizado que **falhe** na ausência da correção.

---

## 0. Diagnóstico da causa-raiz

O gap de imutabilidade não é acidental: ele decorre de um detalhe de arquitetura de banco.

```python
# backend/app/db/database.py:62-80
async def init_db() -> None:
    if not settings.AUTO_CREATE_SCHEMA:
        return                      # <-- em produção, nada é aplicado aqui
    ...
    await apply_sql_file(SQL_DIR / "001_immutability.sql")
    await apply_sql_file(SQL_DIR / "002_indexes.sql")
```

Em produção `AUTO_CREATE_SCHEMA=false` (ver `docker-compose.yml`), então os triggers vêm **apenas** da migração `0002_guards.py`. Como `0002` foi escrita antes das Fases 1–5, **todas as tabelas criadas depois ficaram sem guarda** — e como o arquivo SQL de desenvolvimento continua sendo aplicado, o ambiente de dev "parece" protegido enquanto produção não está.

**Consequência direta:** qualquer correção precisa entrar em **dois lugares** (migração para produção, SQL para dev), com teste de paridade. Sem isso, o problema volta na próxima fase.

---

## 1. Risco 1 — Integridade de dados e laudo

### 1.1 Nova migração de guardas

Criar `backend/alembic/versions/0011_guards_integridade.py` (`down_revision = "0010_fase5_instrument_data"`; em `main`, encadear a partir de `0008_fase4_capa`).

Três funções PL/pgSQL, reaproveitando o padrão já existente:

```sql
-- (a) já existe: lims_reject_mutation()  -> UPDATE e DELETE proibidos
-- (b) já existe: lims_reject_delete()    -> apenas DELETE proibido

-- (c) NOVA: congela colunas após o registro atingir estado terminal
CREATE OR REPLACE FUNCTION lims_freeze_after_terminal() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Exclusao bloqueada em % (ALCOA+)', TG_TABLE_NAME
            USING ERRCODE = 'insufficient_privilege';
    END IF;

    -- Só congela quando o estado anterior já era terminal
    IF OLD.status = ANY (TG_ARGV[0]::text[]) THEN
        RAISE EXCEPTION 'Registro terminal em % nao pode ser alterado (21 CFR Part 11)',
            TG_TABLE_NAME USING ERRCODE = 'insufficient_privilege';
    END IF;

    RETURN NEW;
END;
$$;
```

**Mapa de guardas por tabela** — a escolha do tipo de guarda é o ponto crítico; um `append-only` ingênuo em `test_executions` quebraria o fluxo normal de transição de status.

| Tabela | Guarda | Justificativa |
|---|---|---|
| `official_reports` | **append-only** com transição única de `pdf_data` (NULL → valor) | Laudo emitido não muda; PDF pode ser materializado uma vez |
| `test_executions` | **freeze-after-terminal** (`CONCLUIDA`, `INTERROMPIDA`, `CANCELADA`) + no-delete | Status precisa transitar; resultado, condições ambientais e equipamento não podem mudar depois |
| `test_reviews` | **freeze-after-terminal** (qualquer status ≠ `PENDENTE`) | Parecer emitido é definitivo |
| `test_attachments` | **append-only** | Evidência bruta nunca é reescrita |
| `instrument_data_imports` | no-delete + **imutabilidade de colunas de origem** (`raw_content`, `raw_file_hash_sha256`, `file_name`, `file_format`, `equipment_id`, `imported_by_id`) | Status e vínculo podem evoluir; o dado bruto não |
| `training_records` | **append-only** | Registro de treinamento é evidência de competência |
| `custody_events` | **append-only** | Evento de custódia é fato consumado |
| `solicitations`, `solicitation_items`, `receipts`, `receipt_items`, `custody_objects`, `receipt_decisions`, `coordination_reviews`, `analyst_qualifications` | **no-delete** | Preservação regulatória; ciclo de vida por estado |

> **Atenção:** `chain_of_custody` já é append-only (`001_immutability.sql:59`). A tabela nova é `custody_events` — nomes diferentes, coberturas diferentes.

### 1.2 Paridade dev/produção

Criar `backend/app/db/sql/003_integridade_fase5.sql` com **exatamente** o mesmo DDL e registrá-lo em `init_db()`:

```python
await apply_sql_file(SQL_DIR / "003_integridade_fase5.sql")
```

Adicionar teste de paridade que compara o conjunto de triggers do banco com uma lista canônica:

```python
EXPECTED_TRIGGERS = {
    "audit_logs", "lab_test_results", "chain_of_custody", "electronic_signatures",
    "device_samples", "lab_tests", "capa_actions",
    "official_reports", "test_executions", "test_reviews", "test_attachments",
    "instrument_data_imports", "training_records", "custody_events",
    "solicitations", "receipts", "custody_objects", "receipt_decisions",
    "coordination_reviews", "analyst_qualifications",
}
```

Esse teste é o que impede a regressão na Fase 6.

### 1.3 Numeração de laudo sem corrida

Hoje (`report_service.py:79-81`):

```python
total_reports = (await db.scalar(select(func.count()).select_from(OfficialReport))) or 0
report_number = f"LDO-{now.year}-{total_reports + 1:04d}"
```

Como `report_number` é `unique=True`, a corrida **não gera duplicata silenciosa**: a segunda transação falha com `IntegrityError` e o usuário recebe erro 500 em plena emissão de laudo. Ainda é um defeito, apenas com sintoma diferente do esperado.

Correção — usar o mecanismo que já existe para amostras e CAPA:

```python
# backend/app/db/dialect.py: SEQUENCES
SEQUENCES = frozenset({..., "official_report_seq"})
```

```python
seq = await next_sequence(db, "official_report_seq")
report_number = f"LDO-{now.year}-{seq:04d}"
```

Sequence é monotônica e tolera lacunas (transação abortada consome número). Isso é **aceitável e auditável** — e muito melhor que colisão. Se a regra de negócio exigir numeração reiniciando por ano, usar tabela de contador por ano com `INSERT ... ON CONFLICT ... RETURNING` (o `dialect.next_sequence` já implementa esse padrão para SQLite e serve de referência).

### 1.4 Versionamento e emenda de laudo

Requisito ISO/IEC 17025 §7.8.8. O desenho precisa respeitar a imutabilidade: **não use `is_current` booleano**, porque atualizá-lo exigiria `UPDATE` — exatamente o que o trigger proíbe.

Modelo recomendado (append-only puro):

```python
# official_report.py — novas colunas
version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
root_report_id: Mapped[UUID | None] = mapped_column(
    ForeignKey("official_reports.id", ondelete="RESTRICT"), nullable=True, index=True
)
supersedes_id: Mapped[UUID | None] = mapped_column(
    ForeignKey("official_reports.id", ondelete="RESTRICT"), nullable=True, index=True
)
amendment_reason: Mapped[str | None] = mapped_column(Text)
```

Regras:

- Emissão original: `version=1`, `root_report_id=NULL`, `supersedes_id=NULL`.
- Emenda: `version = max(version do root) + 1`, `root_report_id = id do original`, `supersedes_id = id da versão imediatamente anterior`, `amendment_reason` obrigatório.
- **Versão vigente** é derivada, nunca armazenada: `max(version)` por `root_report_id`.
- `auth_token` é único por versão; a verificação pública resolve o root e informa `is_current` por comparação.
- O `manifest` do hash passa a incluir `version`, `supersedes_id` e `amendment_reason`, de modo que a emenda tem hash próprio e a original permanece verificável.
- `pdf_data`: permitir **uma única** transição `NULL → bytes`. O trigger de `official_reports` valida:

```sql
IF OLD.pdf_data IS NOT NULL AND NEW.pdf_data IS DISTINCT FROM OLD.pdf_data THEN
    RAISE EXCEPTION 'PDF do laudo e write-once';
END IF;
```

Isso evita o beco sem saída de "laudo imutável, mas PDF gerado depois".

### 1.5 Testes obrigatórios

| Teste | Tipo | Critério |
|---|---|---|
| `test_official_report_is_append_only` | integração PG | `UPDATE`/`DELETE` levantam exceção |
| `test_pdf_is_write_once` | integração PG | segunda escrita de PDF falha |
| `test_execution_frozen_after_completion` | integração PG | alterar `result_value` pós-conclusão falha |
| `test_report_number_concurrent` | integração PG | 10 emissões paralelas, 10 números distintos |
| `test_trigger_parity` | integração PG | conjunto de triggers == lista canônica |
| `test_amendment_creates_new_version` | integração | original intacto; `max(version)` correto |

---

## 2. Risco 2 — Indicadores fabricados

### 2.1 Inventário exato a remover

`backend/app/services/analytics_service.py`:

| Linha | Conteúdo | Ação |
|---|---|---|
| 95 | `else 48.5` | remover |
| 100 | `else 18.2` | remover |
| 105 | `else 14.4` | remover |
| 113 | `else 15.9` | remover |
| 156 | `else 92.5` | remover |
| 183 | `else 85.7` | remover |
| ~420 | tupla de 16 pontos sintéticos de CEP | remover integralmente |

### 2.2 Contrato de saída

Trocar "número inventado" por "ausência explícita + qualidade do dado":

```python
class MetricValue(BaseModel):
    value: float | None
    sample_size: int
    data_quality: Literal["complete", "partial", "insufficient"]
```

Regra: `data_quality="insufficient"` quando `sample_size < N` (N definido por indicador; sugerido 5 para TAT, 20 para CEP). A UI **nunca** exibe número quando `value is None` — exibe "Dados insuficientes".

### 2.3 CEP

- Mínimo de 20 pontos reais para emitir carta.
- Regras de Westgard com testes unitários sobre séries conhecidas (1-3s, 2-2s, R-4s, 4-1s, 10x).
- Cada ponto carrega `source_execution_id` e `measured_at` — rastreabilidade do dado.
- Nunca interpolar, nunca "completar" série.

### 2.4 Teste que trava a regressão

```python
async def test_empty_database_returns_no_fabricated_metrics(db):
    result = await analytics_service.get_operational_analytics(db)
    assert result.tat.reception_to_execution.value is None
    assert result.conformity_rate.value is None
    assert result.capa_effectiveness.value is None
```

Esse teste é a garantia de que o dossiê de validação não volta a citar indicador sem lastro.

---

## 3. Risco 3 — Segurança e infraestrutura

### 3.1 Matriz de autorização das rotas da Fase 4/5

Situação atual: `attachments`, `instrument-data`, `analytics`, `uncertainty/simulate` e `notifications` usam apenas `CurrentUser`. Proposta:

| Rota | ADMIN | FISCAL | TECNICO | CUSTODIANTE | AUDITOR |
|---|---|---|---|---|---|
| `POST /attachments/tests/{id}` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `GET /analytics/*` | ✅ | ✅ | ✅ | ❌ | ✅ |
| `POST /instrument-data/upload` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `POST /instrument-data/{id}/map` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `POST /uncertainty/simulate` | ✅ | ✅ | ✅ | ❌ | ✅ (não persiste) |
| `POST /uncertainty/budgets` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `GET /notifications` | ✅ | ✅ | ✅ | ✅ | ✅ (apenas próprias) |

Implementação: `Depends(require_roles(...))` já existente em `deps.py`. Adicionar teste negativo parametrizado por papel — hoje o AUDITOR consegue escrever, o que é o achado mais objetivo da matriz.

### 3.2 MFA real

A coluna `mfa_enabled` existe em `user.py:49` e **não é lida em lugar algum**. Duas opções: implementar ou remover. Recomendo implementar, porque o requisito é real.

Desenho:

- Novas colunas: `mfa_secret_encrypted` (cifrado com chave de aplicação), `mfa_recovery_codes_hashed`, `mfa_enrolled_at`, `mfa_last_used_at`.
- `POST /auth/mfa/enroll` → gera segredo TOTP, retorna URI `otpauth://` e 8 recovery codes (exibidos uma única vez).
- `POST /auth/mfa/verify` → confirma primeiro código e ativa.
- Login passa a responder, quando aplicável, `401` com `{"mfa_required": true, "challenge_token": "..."}` (TTL 5 min) em vez de emitir o par de tokens.
- `POST /auth/mfa/challenge` → valida TOTP ou recovery code e só então emite o par.
- Política: **obrigatório** para ADMIN e FISCAL; opcional para os demais; `mfa_enabled` passa a ser efetivamente consultado.
- Anti-replay: rejeitar reutilização do mesmo código TOTP dentro da janela.

### 3.3 TLS e endurecimento

```nginx
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    http2 on;
    ssl_certificate     /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    ...
}
```

E remover de produção: `location /docs`, `location /redoc`, `location = /openapi.json`. No backend:

```python
_is_prod = settings.ENVIRONMENT == "production"
app = FastAPI(
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
    openapi_url=None if _is_prod else "/openapi.json",
)
```

Adicionar `TrustedHostMiddleware` com `ALLOWED_HOSTS` explícito.

### 3.4 Backup, PITR e DRP

| Item | Meta |
|---|---|
| RPO | 15 minutos |
| RTO | 4 horas |
| Retenção | 30 dias diário, 12 meses mensal |
| Cifra | `age` ou GPG com chave custodiada fora do servidor |
| Offsite | bucket com Object Lock (WORM) |
| Teste de restauração | trimestral, com registro assinado |

Implementação mínima (H0): `pg_dump -Fc` agendado no host + cópia cifrada offsite + `scripts/restore-drill.sh`.
Implementação alvo (H1): `pgBackRest` ou WAL-G com archiving contínuo, permitindo PITR.

### 3.5 Rate limit distribuído (H1)

`account_lockout.py` mantém estado em memória. Com duas réplicas, o limite efetivo dobra. Migrar contadores para Redis com `INCR` + `EXPIRE`, mantendo a interface atual — mudança localizada, sem alterar rotas.

---

## 4. Ordem de execução recomendada

1. **H0.3 + H0.4** (triggers e congelamento) — maior redução de risco por esforço.
2. **H0.5** (sequence de laudo) — correção de 30 minutos que elimina falha em produção.
3. **H0.6** (remover fabricação) — protege o dossiê de validação.
4. **H0.7 + H0.8** (autorização e endurecimento) — barreiras de baixo custo.
5. **H0.9** (backup) — sem isso, todo o resto é reversível por um incidente.
6. **H1.1/H1.2** (emenda e PDF) — dependem dos triggers prontos.
7. **H1.3** (MFA) — maior esforço do bloco; exige janela de adesão.

---

## 5. Impacto na validação (CSV)

| Mudança | Impacto | Evidência exigida |
|---|---|---|
| Triggers de imutabilidade | Não altera função; altera comportamento em falha | IQ (instalação dos objetos) + teste negativo |
| Sequence de numeração | Altera formato/continuidade | OQ de emissão concorrente |
| Emenda de laudo | **Nova função** | OQ + UAT + atualização do RTM |
| Remoção de fallback analítico | Altera saída da API | OQ com base vazia |
| Autorização por papel | Altera controle de acesso | OQ negativo por papel + matriz assinada |
| MFA | **Nova função** | OQ + UAT + plano de contingência de acesso |
| TLS/HSTS | Infraestrutura | IQ + evidência de configuração |
| Backup/PITR | Processo | IQ + registro de restauração testada |

---

## 6. Rollback

- **Migração `0011`**: `downgrade()` remove triggers e a sequence; não há perda de dado (nenhuma coluna é removida no H0).
- **Colunas de emenda (H1.1)**: `downgrade()` remove as colunas; laudos originais permanecem íntegros.
- **MFA (H1.3)**: feature flag `MFA_ENFORCEMENT=off` restaura o login atual sem migração.
- **TLS (H1.4)**: manter o `server` bloco 80 ativo durante a janela; rollback = reverter arquivo e recarregar Nginx.

Todo rollback deve ser exercitado em ambiente de teste **antes** da janela de produção. É o item que mais falta hoje: o CI roda `alembic upgrade head` mas **não testa downgrade**.
