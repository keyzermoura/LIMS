# Relatório de Reavaliação do LIMS — 17/11/2026

**Objeto:** LIMS de fiscalização pós-mercado de dispositivos médicos (SEFI)
**Baseline avaliado:** `HEAD` = `d6bbc52` (`feature/horizonte-3-integracao-ecossistema`); `main` = `e9b7675`
**Método:** leitura de código, migrações, testes e execução da suíte em worktree limpo
**Natureza:** parecer técnico sênior — não é auditoria formal de validação
**Documento anterior:** `RELATORIO_EXECUTIVO_ANALISE_LIMS.md` (16/11/2026)

---

## 1. Sumário executivo

Em 24 horas o repositório avançou três gates. A avaliação anterior descrevia um LIMS de fiscalização com bons controles de custódia e lacunas no núcleo laboratorial. O sistema atual **já possui núcleo laboratorial**: reagentes e padrões com rastreabilidade de CRM, fluxo OOS/OOT com fases de investigação, armazenamento/contraprova/descarte com dupla assinatura, e controle estatístico de processo com regras de Westgard que **bloqueiam a emissão de laudo**.

A natureza da dívida mudou. Antes era *falta de função*; agora é *falta de fechamento*. Três conclusões sustentam o parecer:

1. **O baseline commitado está saudável** — 140 testes passam, 9 são ignorados localmente por exigirem PostgreSQL real.
2. **O working tree está quebrado** — há WIP não commitado que impede o `app.main` de importar, o que derruba coleta de testes e build de container.
3. **O Gate G-B foi declarado, não completado** — MFA, TLS e backup eram o núcleo dele; dois não existem no repositório e o terceiro foi implementado como fator de assinatura, não de sessão.

**Recomendação:** não promover o Horizonte 3 enquanto os riscos 1–3 da seção 6 estiverem abertos.

---

## 2. Escopo e método

### 2.1 O que foi avaliado

| Item | Valor |
|---|---|
| Branch de trabalho | `feature/horizonte-3-integracao-ecossistema` |
| Commit avaliado (limpo) | `d6bbc52` — gateway de instrumentos, perfis declarativos, parser ASTM E1394 |
| `main` | `e9b7675` — homologação do Horizonte 2 (Gate G-C) |
| Migrações | 20 revisões (`a1cd5ac5805f` → `0020_fase8_outbox_webhooks`) |
| Modelos / serviços / rotas | 33 modelos, 35 serviços, 30 arquivos de rota |
| Frontend | 18 páginas |

### 2.2 Como foi avaliado

- O `HEAD` foi materializado em **worktree isolado**, para não contaminar nem depender de alterações locais não commitadas.
- Suíte executada nesse worktree com Python 3.12: **149 testes coletados — 140 passaram, 9 ignorados, 0 falhas** (4 min 48 s, SQLite). Os 9 ignorados são os que exigem PostgreSQL real e rodam no job `postgres` do CI.
- O working tree original foi inspecionado separadamente e **não** entra nas conclusões sobre o baseline.

### 2.3 Limitações

- Não houve execução da suíte contra PostgreSQL real nesta avaliação; a evidência de triggers vem do código das migrações e do teste de paridade `test_trigger_parity_phase5`.
- Não houve teste de carga, nem inspeção de infraestrutura implantada (apenas o que está versionado no repositório).
- O parecer não substitui IQ/OQ/PQ.

---

## 3. O que mudou desde a avaliação anterior

| Gate | Conteúdo incorporado | Migrações | Commit de homologação |
|---|---|---|---|
| **G-A — Integridade** | Fase 5 (BI, notificações, aquisição de instrumentos), guardas de imutabilidade, webhooks | `0011`, `0012` | `c4e51d3` |
| **G-B — Segurança e laudos** | Emendas ISO 17025 §7.8.8, geração real de PDF com hash, MFA TOTP | `0013`, `0014` | `6e9b447` |
| **G-C — Núcleo laboratorial** | Reagentes e padrões CRM, OOS/OOT com fases I/II, armazenamento/contraprova/descarte, Westgard | `0015`–`0018` | `e9b7675` |
| **G-D — Integração (em curso)** | Contas de serviço M2M, idempotência, outbox e webhooks, gateway ASTM | `0019`, `0020` | **não mergeado** (4 commits à frente de `main`) |

Os quatro documentos produzidos na avaliação anterior foram commitados na `main` e serviram de base direta para os horizontes. O roadmap foi seguido item a item — inclusive na numeração das tarefas (H0.x, H1.x, H2.x).

---

## 4. Veredito por pilar

| Pilar | Avaliação anterior | Avaliação atual | Tendência |
|---|---|---|---|
| Arquitetura e infraestrutura | Parcial | **Parcial** — sem TLS, sem backup/PITR, sem worker de outbox | estável |
| Segurança da informação | Insuficiente | **Parcial** — MFA existe, mas não protege a sessão; segredo TOTP em claro | melhora |
| Integridade de dados / ALCOA+ | Parcial | **Bom** — 20 tabelas com guarda, teste de paridade no CI | melhora forte |
| Fluxo laboratorial | Incompleto | **Bom** — reagentes, OOS/OOT, contraprova, descarte, Westgard | melhora forte |
| Laudos e resultados | Frágil | **Bom** — sequence, emenda versionada, PDF com hash, verificação pública | melhora forte |
| Interoperabilidade | Embrionária | **Parcial-Alta** — M2M, idempotência, outbox, ASTM (em branch) | melhora |
| Usabilidade e configurabilidade | Parcial | **Parcial** — 6 telas novas; sem UI para contas de serviço e outbox | leve melhora |
| Validação CSV | Parcial | **Fraco** — dossiê não cobre H1/H2 e aponta para código que mudou | **regressão** |
| Disciplina de release | Insuficiente | **Insuficiente** — zero tags, versão `0.1.0` | estável |

---

## 5. Fechamento das constatações anteriores

| # | Constatação (16/11) | Status | Evidência |
|---|---|---|---|
| 1 | Indicadores fabricados no analytics | **Resolvido** | Sem `48.5 / 92.5 / 85.7`; `data_quality` e `sample_size` por indicador (`analytics_service.py:113,165,194,452`) |
| 2 | Imutabilidade parcial (7 tabelas descobertas) | **Resolvido** | `0011_fase5_guards_integridade.py` + `003_integridade_fase5.sql` (15 triggers); `test_trigger_parity_phase5` valida o conjunto |
| 3 | `report_number = count + 1` | **Resolvido** | `next_sequence(db, "official_report_seq")` (`report_service.py:112`) |
| 4 | Laudo mutável, sem emenda | **Resolvido** | `root_report_id`, `supersedes_id`, `amendment_reason`, numeração `-V{n}` |
| 5 | `pdf_data` nunca preenchido | **Resolvido** | `pdf_report_service.py` (ReportLab), hash do PDF |
| 6 | Rotas da Fase 4/5 sem autorização por papel | **Resolvido** | `require_roles` aplicado em 18 arquivos de rota, incluindo AUDITOR como somente-leitura |
| 7 | Sem reagentes/padrões (lote, validade, CRM) | **Resolvido** | `reagent_service`, `ReagentBatch`, intertravamento de vencido/quarentena/saldo |
| 8 | Sem fluxo OOS/OOT | **Resolvido** | `oos_service` com Fase I/II, CAPA automática e **bloqueio de laudo** (`report_service.py:86-97`) |
| 9 | Sem armazenamento/descarte | **Resolvido** | `storage_disposal_service`, termo de descarte com dupla assinatura e segregação de funções |
| 10 | CEP sem dados reais | **Resolvido** | `qc_spc_service` com 5 regras de Westgard; bloqueio de laudo em violação ativa |
| 11 | MFA inexistente (flag morta) | **Parcial** | Implementado como segundo fator **de assinatura**, não de login; cadastro opcional |
| 12 | TLS, backup, `/docs` expostos | **Não feito** | `nginx.conf:2` (`listen 80`); `main.py:85-87`; nenhum script de backup no repositório |
| 13 | Baseline de release inexistente | **Não feito** | `git tag` vazio; `VERSION = "0.1.0"` em backend, frontend e `pyproject.toml` |
| 14 | Sem alíquotas / código de barras | **Não feito** | 0 ocorrências de `aliquot`; `barcode` aparece apenas em comentário do parser ASTM |

---

## 6. Riscos atuais

### 6.1 Top 5

| # | Risco | Sev. | Evidência no código | Mitigação |
|---|---|---|---|---|
| 1 | **Working tree não compila**: WIP de exportação de BI referencia `deps.get_current_active_user` (função inexistente) e `UserRole.ANALYST` (papel inexistente). Como `router.py` inclui o módulo, `app.main` falha no import — nenhum teste roda e o container não sobe | **Alta** | `routes/integration_exports.py:52`; `router.py:17,68`; falha reproduzida na coleta do pytest | Corrigir para `deps.get_current_user` e `UserRole.TECNICO`, ou remover o WIP do tree antes de qualquer build ou demonstração |
| 2 | **Gate G-B não fechado**: sem TLS no repositório; `/docs` e `/openapi.json` expostos; sem backup/PITR; MFA não aplicado no login e opt-in; segredo TOTP em claro no banco | **Alta** | `nginx.conf:2`; `main.py:85-87`; `auth_service.login` não chama `verify_user_mfa`; `mfa_service.py:153-154` grava o segredo sem cifra | TLS + redirect 80→443; `docs_url=None` em produção; pgBackRest/WAL com restauração testada; desafio MFA no login para ADMIN/FISCAL; cifrar segredo com chave de aplicação |
| 3 | **Rastreabilidade de validação quebrada**: o dossiê CSV aponta o CEP para `analytics_service.py`, mas o motor migrou para `qc_spc_service.py`; não há dossiê nem RTM para MFA, emendas, reagentes, OOS e descarte | **Alta** | `DOSSIE_VALIDACAO_SISTEMA_COMPUTADORIZADO_CSV_FASE_5.md:47`; ausência de documentos de H1/H2 | Reemitir dossiê e RTM por release, com baseline versionado e assinado |
| 4 | **Outbox sem worker**: eventos são enfileirados, mas a entrega só acontece via `POST /outbox/dispatch` (ADMIN). Sem cron externo, webhooks nunca disparam; não há runbook nem alerta de backlog | **Média-Alta** | `routes/outbox.py:79`; nenhum `create_task`, `BackgroundTasks` ou serviço de scheduler no compose | Worker com advisory lock no lifespan **ou** cron documentado e monitorado; alerta para evento pendente > 15 min |
| 5 | **Intertravamentos consultivos**: consumo de reagente é rota manual e a conclusão da execução não exige registro de consumo; OOS só nasce por ação humana; baixa de estoque sem `FOR UPDATE` permite saldo negativo sob concorrência | **Média** | `execution_service.py:29` não importa `reagent_service`; único chamador de `create_investigation` é a rota; `reagent_service` sem `with_for_update` (o restante do código usa) | Exigir consumo registrado quando o método declara insumos; abrir OOS automaticamente em resultado fora de spec; `SELECT ... FOR UPDATE` no lote |

### 6.2 Achados secundários

| Achado | Impacto | Observação |
|---|---|---|
| Escopos M2M não aplicados por rota | Médio | `_service_scopes` só é lido pelo WIP de exportação; no baseline, apenas o papel `SERVICE` é verificado |
| `official_reports.attributes` mutável no trigger | Médio | Adulteração do manifesto é *detectável* pelo hash imutável, mas não *prevenida* |
| Sem SAST/SCA/E2E no CI | Médio | Pipeline segue com ruff, mypy, Alembic, pytest (SQLite + PG16), typecheck, build e smoke Docker |
| Sem UI para contas de serviço e outbox | Baixo | Funcionalidade existe só por API; aceitável no curto prazo para operação administrativa |
| `.env.example` sem variáveis novas | Baixo | Dificulta provisionamento correto de MFA e integração |
| Avisos de deprecação do Starlette (`422_UNPROCESSABLE_ENTITY`) | Baixo | Ruído no log; correção trivial na próxima passagem |
| Roadmap commitado sem atualização de status | Baixo | Documento descreve o plano, não o executado — risco de leitura equivocada |

---

## 7. Sequência recomendada

| Ordem | Ação | Esforço | Critério de conclusão |
|---|---|---|---|
| 0 | Corrigir ou descartar o WIP quebrado | 30 min | `pytest` coleta e `docker compose build` conclui |
| 1 | Fechar G-B: TLS, docs off, backup/PITR com restore testado, MFA no login (ou exceção formal), cifrar segredo TOTP | 2–3 semanas | Evidência de configuração + registro de restauração assinado |
| 2 | Worker/agendador do outbox, runbook e alerta de backlog | 2–3 dias | Evento entregue sem intervenção humana |
| 3 | Reemitir dossiê CSV e RTM para H1/H2, corrigindo a referência ao CEP | 3–5 dias | RTM aponta para o módulo correto e cobre 100% dos requisitos |
| 4 | Endurecer intertravamentos (reagente, OOS automático, `FOR UPDATE`) | ~1 semana | Teste negativo: execução sem consumo registrado é rejeitada |
| 5 | Tag anotada + CHANGELOG + SAST/SCA/E2E | 3–5 dias | `git describe` identifica o binário validado |

---

## 8. Conclusão

O LIMS deixou de ser um sistema de fiscalização com lacunas laboratoriais e passou a ser um LIMS laboratorial com lacunas operacionais. Essa é uma mudança qualitativa relevante, e ela é verificável: as guardas de integridade têm teste de paridade, o laudo é bloqueado por OOS pendente e por violação de Westgard, e a emissão usa sequence em vez de contagem.

O que impede o próximo passo não é arquitetura. É disciplina de fechamento: um working tree quebrado, um gate de segurança declarado sem infraestrutura correspondente, e um dossiê de validação que aponta para código que já mudou. Os três são corrigíveis em semanas, não em meses — e nenhum deles exige redesenho.

**Recomendação formal:** manter o Horizonte 3 bloqueado até o fechamento dos riscos 1–3; tratar o item 0 como condição de entrada para qualquer demonstração.

---

## Anexo A — Evidências de execução

```
Ambiente: Python 3.12 (worktree limpo em d6bbc52)
Comando:  python -m pytest -q --tb=line
Resultado: 140 passed, 9 skipped, 17 warnings in 288.15s
```

Os 9 testes ignorados localmente são os que exigem PostgreSQL real (`test_postgres_guards.py`, `test_migrations_postgres.py`) e executam no job `postgres` do CI, com `postgres:16-alpine`.

## Anexo B — Inventário de migrações

| Revisão | Conteúdo |
|---|---|
| `a1cd5ac5805f` | Schema inicial |
| `0002_guards` | Sequences e triggers originais |
| `0003_audit_export` | Exportação de auditoria |
| `0004`–`0006` | Fases 1–3 (recebimento, execução, laudos) |
| `0007`–`0008` | Fase 4 (competências, CAPA) |
| `0009`–`0010` | Fase 5 (notificações, instrumentos) |
| `0011`–`0012` | Gate G-A (guardas de integridade, webhooks) |
| `0013`–`0014` | Gate G-B (emendas de laudo, MFA TOTP) |
| `0015`–`0018` | Gate G-C (reagentes, OOS, armazenamento/descarte, Westgard) |
| `0019`–`0020` | Gate G-D (contas de serviço/idempotência, outbox/webhooks) — em branch |

## Anexo C — Documentos relacionados

| Documento | Papel |
|---|---|
| `RELATORIO_EXECUTIVO_ANALISE_LIMS.md` | Avaliação de 16/11 — base do plano |
| `ROADMAP_90_180_365_LIMS.md` | Roadmap executado nos horizontes 0–3 |
| `PLANO_CORRECAO_RISCOS_1_3_LIMS.md` | Plano técnico que originou `0011`–`0014` |
| `ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md` | Especificação que originou `0019`–`0020` |
| `DOSSIE_VALIDACAO_SISTEMA_COMPUTADORIZADO_CSV_FASE_5.md` | Dossiê CSV — requer atualização |
