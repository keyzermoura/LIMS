# Procedimento Operacional Padrão (Runbook): Monitoramento e Reprocessamento do Transactional Outbox

**Documento:** `RUNBOOK_OUTBOX_MESSAGING.md`  
**Objetivo:** Estabelecer o procedimento operacional para diagnóstico, alerta e resolução de backlog e dead-letter no Transactional Outbox e Webhooks do LIMS.  
**Normas de Referência:** ISO/IEC 17025:2017 §7.11 (Controle de Dados e Gestão da Informação), 21 CFR Part 11 §11.10.

---

## 1. Visão Geral da Arquitetura do Outbox

O LIMS utiliza o padrão **Transactional Outbox** para garantir que eventos de negócio (emissão de laudos periciais, descarte de amostras, alterações de custódia e desvios OOS) sejam persistidos de forma atômica no banco de dados relacional e despachados assincronamente para sistemas integrados (SEFI, Anvisa, barramentos de mensageria).

- **Tabela:** `outbox_events`
- **Worker em Runtime:** `outbox_worker.py` (executado no lifespan da API FastAPI com polling contínuo via `SELECT ... FOR UPDATE SKIP LOCKED`).
- **Estados dos Eventos:** `PENDENTE`, `PROCESSANDO`, `PUBLICADO`, `FALHOU` (Dead-letter).

---

## 2. Indicadores e Limiares de Alerta

| Métrica | Limiar de Alerta | Severidade | Ação Imediata |
|---|---|---|---|
| **Eventos Pendentes Atrasados** | Evento `PENDENTE` há mais de 15 minutos | **Média** | Verificar conectividade do worker e disponibilidade dos webhooks de destino. |
| **Volume de Backlog** | Total de eventos `PENDENTE` > 100 registros | **Alta** | Investigar sobrecarga na fila ou contenção de locks no banco. |
| **Dead-letter / Falha Definitiva** | Evento com `retry_count >= 12` em estado `FALHOU` | **Alta** | Diagnosticar erro de payload/endpoint e aplicar reprocessamento manual auditado. |

---

## 3. Diagnóstico de Falhas e Backlog

### 3.1 Consulta de Status do Outbox via SQL
Em caso de alerta de eventos pendentes ou atrasados:

```sql
-- Verificar total de eventos por status
SELECT status, count(*) 
FROM outbox_events 
GROUP BY status;

-- Identificar eventos em atraso (pendentes há mais de 15 minutos)
SELECT id, event_type, aggregate_type, aggregate_id, retry_count, created_at, last_error
FROM outbox_events
WHERE status = 'PENDENTE' AND created_at < NOW() - INTERVAL '15 minutes'
ORDER BY created_at ASC;

-- Identificar mensagens em dead-letter (FALHOU)
SELECT id, event_type, destination_url, retry_count, last_error, updated_at
FROM outbox_events
WHERE status = 'FALHOU'
ORDER BY updated_at DESC;
```

---

## 4. Procedimento Operacional de Reprocessamento Manual

Quando um evento atinge o estado `FALHOU` após as 12 tentativas com backoff exponencial:

1. **Investigação do Erro:** Analisar a coluna `last_error` para determinar se a causa é timeout, erro 5xx no endpoint de destino ou incompatibilidade de schema.
2. **Correção do Destino:** Garantir que o serviço consumidor (SEFI / Anvisa) está saudável e apto a receber payloads.
3. **Reprocessamento Auditado:**
   Executar o reset controlado do status via rota administrativa autenticada ou comando SQL restrito pelo DBA:
   ```sql
   UPDATE outbox_events
   SET status = 'PENDENTE', retry_count = 0, last_error = NULL, updated_at = NOW()
   WHERE id = '<ID_DO_EVENTO>' AND status = 'FALHOU';
   ```
4. **Registro de Auditoria:** Toda ação de reprocessamento manual é automaticamente capturada na trilha de auditoria (`audit_logs`) com identificação do operador e justificativa técnica.
