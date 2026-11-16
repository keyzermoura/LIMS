# Especificação — Camada de Integração e Autenticação Máquina-a-Máquina

**Data:** 16/11/2026
**Contexto:** hoje o LIMS só expõe API autenticada por JWT de **usuário humano** e só recebe dados de instrumento por **upload de arquivo**. Não existe caminho seguro para um sistema externo (ERP, QMS, BI, agente de instrumento) conversar com o LIMS.
**Objetivo:** definir a camada que permite integração **sem acesso ao banco** e **sem credencial de pessoa física**.

---

## 1. Princípios não negociáveis

1. **Nenhuma integração acessa o PostgreSQL diretamente.** ETL no banco contorna auditoria, assinatura e triggers — é proibido pela própria lógica de validação do sistema.
2. **Todo chamador é identificado.** Não existe chamada anônima nem credencial compartilhada entre sistemas.
3. **Toda escrita é idempotente.** Reenvio não duplica dado.
4. **Todo evento é auditável.** A trilha registra *ator* (pessoa ou serviço), *correlação* e *payload mínimo*.
5. **Contrato versionado.** Mudança incompatível exige nova versão de mídia.

---

## 2. Contas de serviço

### 2.1 Modelo

Em vez de criar um sexto "tipo de identidade" paralelo, reutilizar a entidade `users` com um papel não interativo:

```python
class UserRole(str, Enum):
    ...
    SERVICE = "SERVICE"   # conta de máquina; login interativo bloqueado
```

Vantagens: `audit_logs.actor_id` continua com FK válida, as permissões reaproveitam `ROLE_PERMISSIONS` e o frontend já sabe esconder o papel.

Bloqueio obrigatório em `auth_service`: se `user.role == UserRole.SERVICE`, o endpoint `/auth/login` rejeita — senha de serviço não autentica pessoa.

### 2.2 Tabela `service_clients`

| Coluna | Tipo | Nota |
|---|---|---|
| `id` | UUID | PK |
| `client_id` | String(64) unique | identificador público |
| `name` | String(160) | ex.: "Agente HPLC Lab 2" |
| `secret_hash` | String(128) | Argon2/bcrypt — **nunca** segredo em claro |
| `scopes` | JSON | lista de permissões concedidas |
| `service_user_id` | UUID FK `users` | ator da trilha |
| `is_active` | Boolean | revogação imediata |
| `expires_at` | DateTime | rotação obrigatória |
| `last_used_at` | DateTime | detecção de credencial ociosa |
| `created_by_id` | UUID FK `users` | responsável pela concessão |

### 2.3 Fluxo de token (OAuth2 client credentials)

```
POST /api/v1/auth/service-token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=...&client_secret=...
```

Resposta:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 900,
  "scope": "instrument:write samples:read"
}
```

Claims do JWT de serviço: `sub = "client:<uuid>"`, `typ = "service"`, `scp = [...]`, `jti`, `exp` curto (15 min).

Regras:
- `scopes` do token são a **interseção** entre o concedido ao cliente e o permitido ao papel `SERVICE`.
- Revogação: `is_active=false` invalida no próximo `refresh`/validação (checar em `get_current_user`).
- Rotação de segredo a cada 90 dias, com janela de sobreposição de 7 dias (dois segredos válidos).
- Rate limit por `client_id` (não por IP).

---

## 3. Idempotência

Toda escrita vinda de integração aceita `Idempotency-Key`.

```http
POST /api/v1/instrument-data/upload
Idempotency-Key: 3f1c...-sha256-do-arquivo
```

Tabela `idempotency_keys`:

| Coluna | Nota |
|---|---|
| `key` + `client_id` | PK composta |
| `request_hash` | SHA-256 do payload — detecta reuso da chave com corpo diferente (409) |
| `response_status` / `response_body` | replay da resposta original |
| `created_at` / `expires_at` | TTL 24 h para escrita, 7 dias para instrumento |

Sem chave informada, o endpoint gera uma a partir de `(equipment_id, sha256(raw_content))`.

**Correção adicional necessária:** `instrument_data_imports.raw_file_hash_sha256` é indexado, mas **não único**. Adicionar índice único parcial:

```sql
CREATE UNIQUE INDEX uq_instrument_import_dedup
    ON instrument_data_imports (equipment_id, raw_file_hash_sha256);
```

Isso transforma "reenvio acidental" em erro de conflito explícito, em vez de duplicata silenciosa.

---

## 4. Outbox transacional (eventos de saída)

Integração de saída **nunca** publica direto da transação de negócio: se o broker cair, o dado se perde; se o broker responder e o commit falhar, o evento mente.

### 4.1 Tabela `integration_outbox`

| Coluna | Nota |
|---|---|
| `id` | UUID |
| `event_type` | ex.: `report.issued`, `test.completed`, `capa.opened` |
| `aggregate_type` / `aggregate_id` | entidade de origem |
| `payload` | JSON canônico |
| `created_at` | ordem de publicação |
| `published_at` | NULL enquanto pendente |
| `attempts` / `next_attempt_at` | backoff exponencial (1s → 5min, teto 1h) |
| `last_error` | diagnóstico |
| `dead_lettered_at` | após 12 tentativas |

### 4.2 Worker

```sql
SELECT * FROM integration_outbox
 WHERE published_at IS NULL
   AND dead_lettered_at IS NULL
   AND next_attempt_at <= now()
 ORDER BY created_at
   FOR UPDATE SKIP LOCKED
 LIMIT 50;
```

`SKIP LOCKED` permite múltiplos workers sem coordenação externa — reaproveita a mesma filosofia já usada nas sequences.

### 4.3 Webhooks de saída

`webhook_endpoints` (url, secret cifrado, lista de eventos, ativo) e `webhook_deliveries` (outbox_id, endpoint_id, status, response_code).

Assinatura obrigatória:

```http
X-LIMS-Event: report.issued
X-LIMS-Delivery: <uuid>
X-LIMS-Timestamp: 1763300000
X-LIMS-Signature: v1=<hmac_sha256(secret, timestamp + "." + body)>
```

Receptor deve rejeitar `timestamp` com desvio > 5 min (anti-replay) e responder 2xx em < 5 s. Entrega é **at-least-once**; o receptor deduplica por `X-LIMS-Delivery`.

---

## 5. Gateway de instrumentos

O ponto fraco atual: `instrument_parser_service` recebe um arquivo já exportado. Para HPLC/GC-MS, o export manual é justamente onde nasce o erro de transcrição.

### 5.1 Arquitetura

```
[Instrumento] --serial/TCP/file--> [Agente local] --HTTPS--> /instrument-data/upload
                                          |
                                   buffer local (SQLite/spool)
```

O agente roda na estação de bancada, é **stateless em relação ao LIMS** e funciona offline:

1. Captura via porta serial (RS-232), TCP ou *file watch*.
2. Normaliza para o contrato JSON do LIMS.
3. Enfileira localmente (spool durável).
4. Envia com `Idempotency-Key` e credencial de serviço.
5. Reenvia com backoff até confirmação.

### 5.2 Adaptadores por protocolo

| Protocolo | Uso | Observação |
|---|---|---|
| **ASTM E1381/E1394** | analisadores hematológicos, bioquímicos | framing com ENQ/ACK/NAK; mapear para `parsed_data` |
| **SCPI/VISA** | balanças, espectrofotômetros | comandos de leitura; requer driver por fabricante |
| **Arquivo** (CSV/ASCII/JSON) | HPLC/GC, UV-Vis | *file watch* com estabilização de tamanho |
| **OPC UA** | futuro (automação) | só se houver requisito real |

### 5.3 Perfis de parser versionados

Substituir heurística solta por perfil declarativo:

```json
{
  "profile": "agilent-chemstation-csv",
  "version": 3,
  "match": { "manufacturer": "Agilent", "model_regex": "^1260" },
  "delimiter": ",",
  "decimal_separator": ".",
  "columns": { "retention_time": "RT", "area": "Area", "height": "Height" },
  "units": { "area": "mAU*s" },
  "validation": { "min_rows": 1, "required": ["RT", "Area"] }
}
```

Cada perfil tem **arquivo de teste real** versionado em `backend/tests/fixtures/instruments/<profile>/`. Mudança de firmware que quebre o parser passa a ser detectada pelo CI, não pelo analista.

---

## 6. BI e leitura analítica

- **Réplica read-only** do PostgreSQL para consultas pesadas; nunca BI no primário.
- **Views materializadas** versionadas por migração: `v_tat_operational`, `v_qc_points`, `v_backlog_stratified`.
- **Endpoints de exportação** com paginação por cursor e `updated_since`:

```http
GET /api/v1/integration/exports/tests?updated_since=2026-11-01T00:00:00Z&cursor=...
```

- Contrato versionado por mídia: `Accept: application/vnd.lims.v1+json`.
- Sem ODBC direto no banco primário. Se a ferramenta de BI exigir, apontar para a réplica e criar usuário somente-leitura com `statement_timeout`.

---

## 7. Segurança da camada

| Controle | Implementação |
|---|---|
| Autenticação | OAuth2 client credentials + JWT curto (15 min) |
| Autorização | escopos ∩ permissões do papel `SERVICE` |
| Transporte | TLS obrigatório; mTLS opcional para agente de instrumento |
| Rede | allowlist de IP por `client_id` (quando aplicável) |
| Segredo | hash Argon2 no banco; rotação 90 dias; nunca logado |
| Replay | `Idempotency-Key` + timestamp assinado nos webhooks |
| Abuso | rate limit por `client_id` (Redis em multi-réplica) |
| Auditoria | `audit_logs` com `actor_id` = usuário de serviço, `request_id` e `client_id` em metadata |
| Dados | payload mínimo; sem PII além do necessário; sem credencial em URL |

---

## 8. Observabilidade

- Log estruturado com `request_id`, `client_id`, `idempotency_key`, `outbox_id`.
- Métricas: requisições por cliente, taxa de 4xx/5xx, latência p95, tamanho da fila de outbox, entregas em dead-letter.
- Alerta obrigatório: outbox com item > 15 min pendente ou dead-letter > 0.
- Painel de saúde por integração (último evento, última falha, idade do backlog).

---

## 9. Faseamento e esforço

| Fase | Entrega | SP | Pré-requisito |
|---|---|---|---|
| F1 | Papel `SERVICE`, `service_clients`, endpoint de token, rate limit por cliente | 4 | G-B aprovado |
| F2 | `idempotency_keys` + índice único de deduplicação de instrumento | 2 | F1 |
| F3 | Outbox + worker + webhooks assinados | 4 | F1 |
| F4 | Gateway de instrumento com 1 adaptador (ASTM ou arquivo) | 8 | F3 |
| F5 | Conector corporativo (ERP **ou** QMS) | 6 | F3 |
| F6 | Views de BI + endpoints de exportação | 3 | Réplica |
| **Total** | | **27** | |

---

## 10. Critérios de aceite

- [ ] Nenhuma integração possui credencial de usuário humano.
- [ ] Requisição sem `Idempotency-Key` em escrita é rejeitada com 400 (ou deriva chave determinística documentada).
- [ ] Reenvio do mesmo payload retorna a **mesma resposta**, sem criar segundo registro.
- [ ] Revogar `service_client` bloqueia acesso em ≤ 1 requisição.
- [ ] Webhook sem assinatura válida é rejeitado pelo receptor de teste.
- [ ] Outbox sobrevive a reinício da API sem perder evento.
- [ ] Agente de instrumento opera 24 h offline e sincroniza sem duplicar.
- [ ] Toda chamada de serviço aparece na trilha de auditoria com ator identificável.
- [ ] Nenhum processo lê o banco primário diretamente.

---

## 11. Riscos específicos

| Risco | Mitigação |
|---|---|
| Credencial de serviço vazar em log ou repositório | Scan de segredo no CI; rotação; hash no banco |
| Agente local sem atualização vira ponto cego | Versão mínima exigida no handshake; telemetria de versão |
| Webhook do cliente indisponível gera backlog infinito | Dead-letter + alerta + política de descarte auditada |
| Formato de instrumento mudar após update de firmware | Perfis versionados + fixtures reais no CI |
| Timeout de BI afetar operação | Réplica isolada + `statement_timeout` |
