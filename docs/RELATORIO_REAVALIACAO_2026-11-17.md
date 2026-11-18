# Relatório de Reavaliação do LIMS — 17/11/2026

**Objeto:** LIMS de fiscalização pós-mercado de dispositivos médicos (SEFI)
**Baseline avaliado:** `HEAD` = `d6bbc52` (`feature/horizonte-3-integracao-ecossistema`); `main` = `e9b7675`
**Método:** leitura de código, migrações, testes e execução da suíte em worktree limpo
**Natureza:** parecer técnico sênior — não é auditoria formal de validação
**Documento anterior:** `RELATORIO_EXECUTIVO_ANALISE_LIMS.md` (16/11/2026)
**Adendo:** §9 (18/11/2026) revalida este parecer contra o baseline `6e7354d`. Leia o adendo antes de agir sobre as seções 1–8.

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
| `0002_guards` | Sequences e triggers originais |
| `0003_audit_export` | Exportação de auditoria |
| `0004`–`0006` | Fases 1–3 (recebimento, execução, laudos) |
| `0007`–`0008` | Fase 4 (competências, CAPA) |
| `0009`–`0010` | Fase 5 (notificações, instrumentos) |
| `0011`–`0012` | Gate G-A (guardas de integridade, webhooks) |
| `0013`–`0014` | Gate G-B (emendas de laudo, MFA TOTP) |
| `0015`–`0018` | Gate G-C (reagentes, OOS, armazenamento/descarte, Westgard) |
| `0019`–`0020` | Gate G-D (contas de serviço/idempotência, outbox/webhooks) |
| `0021` | Alteração de tipo: `users.mfa_secret` de `String(64)` para `Text` (comporta o ciphertext Fernet) |
| `a1cd5ac5805f` | Schema inicial |

Total no baseline `6e7354d`: **21 revisões** (20 migrações nomeadas + schema inicial).

> `0021` é migração de *tipo*, não de guarda. O segredo TOTP passou a ser cifrado;
> o campo precisa comportar o ciphertext, que excede os 64 caracteres anteriores.

## Anexo C — Documentos relacionados

| Documento | Papel |
|---|---|
| `RELATORIO_EXECUTIVO_ANALISE_LIMS.md` | Avaliação de 16/11 — base do plano |
| `ROADMAP_90_180_365_LIMS.md` | Roadmap executado nos horizontes 0–3 |
| `PLANO_CORRECAO_RISCOS_1_3_LIMS.md` | Plano técnico que originou `0011`–`0014` |
| `ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md` | Especificação que originou `0019`–`0020` |
| `DOSSIE_VALIDACAO_SISTEMA_COMPUTADORIZADO_CSV_FASE_5.md` | Dossiê CSV — requer atualização |

---

## 9. Adendo de 18/11/2026 — revalidação no baseline `6e7354d`

Este adendo **não reescreve** o parecer de 17/11. Ele registra o que mudou no
repositório em 24 horas e o que continua aberto. Onde este adendo contraria as
seções 1–8, **vale o adendo**.

### 9.1 Baseline

| Item | 17/11 (`d6bbc52`) | 18/11 (`6e7354d`) |
|---|---|---|
| `HEAD` | `d6bbc52` em `feature/horizonte-3…` | `6e7354d` em `main`, sincronizado com `origin/main` |
| Tag mais recente | nenhuma | `v1.0.0` em `cb27468` |
| Commits desde a tag | — | 72 (`git describe`: `v1.0.0-72-g6e7354d`) |
| Migrações | 20 | 21 (+`0021_fase8_mfa_secret_text`) |
| Working tree | quebrado (WIP de BI) | limpo |
| Suíte local | não coletava | **149 passed, 9 skipped** |

### 9.2 Riscos 1–5 da seção 6.1

| # | Risco original | Situação em 18/11 |
|---|---|---|
| 1 | Working tree não compila (WIP de BI) | **Fechado.** O WIP foi concluído em `b9d0f64` e o tree está limpo; a suíte coleta e passa. |
| 2 | Gate G-B não fechado | **Quase fechado.** MFA deixou de ser fator de assinatura e passou a ser **desafio de login** (`mfa_pending` + `verify_login_mfa`); o segredo TOTP é cifrado com Fernet; `/docs` e `/openapi.json` são desligados quando `ENVIRONMENT=prod`; backup/PITR com restauração testada existe. **Resta** o redirect 80→443 no caminho docker-compose (P0.1) e o agendamento do backup (P0.2b). |
| 3 | Rastreabilidade de validação quebrada | **Fechado.** O dossiê `V1_0_0` foi reemitido (18,4 KB) cobrindo MFA, emendas, reagentes, OOS, Westgard e descarte, e a referência do CEP aponta para `qc_spc_service.py`. |
| 4 | Outbox sem worker | **Fechado no núcleo.** Worker no lifespan (`main.py:84-88`), `SKIP LOCKED` na seleção e dead-letter com backoff. **Resta** runbook e alerta de backlog (P1.1b). |
| 5 | Intertravamentos consultivos | **Parcial.** OOS automático em resultado reprovado e `FOR UPDATE` na baixa de reagente foram entregues; **a conclusão da execução ainda não exige consumo registrado** (P3.1 aberto). |

### 9.3 Itens fechados desde o parecer

| Item | Evidência |
|---|---|
| P0.2 Backup/PITR com restore | `scripts/backup_restore_pitr.sh`: `pg_dump -Fc` + SHA-256, WAL, `pg_restore --clean` em banco temporário e validação de contagens |
| P0.3 MFA de sessão + TOTP cifrado | `auth_service.py:84-98,118-171`; `mfa_service.py:19,32-61,190` |
| P1.1 Worker do outbox | `main.py:84-88`; `outbox_worker.py:24-63`; `outbox_service.py:109,198-208` |
| P1.3 `.env.example` | Documenta `TOTP_ENCRYPTION_KEY`, `MFA_REQUIRED_ROLES`, `DOCS_ENABLED`, `OUTBOX_*` |
| P2.1 Referência do CEP | `DOSSIE_…_FASE_5.md:47` aponta `qc_spc_service.py` |
| P2.2 Dossiê/RTM H1–H2 | `DOSSIE_VALIDACAO_SISTEMA_COMPUTADORIZADO_CSV_V1_0_0.md` |
| P3.2 Auto-abertura de OOS | `execution_service.py:281-310` (`user_agent="system/auto-oos"`) |
| P3.3 `FOR UPDATE` na baixa | `reagent_service.py:220` |
| P4.2a Código de barras | `routes/samples.py:107-116`; `sample_service.py:132` |
| P5.3 Deprecação Starlette | Zero ocorrências de `HTTP_422_UNPROCESSABLE_ENTITY` |
| P6.1 UI de integrações | `Integrations.tsx` cobre clientes, outbox, gateway e BI |
| P6.2 Roadmap com status | Marcadores de status por item no roadmap |

### 9.4 O que continua aberto

| Item | Sev. | Pendência |
|---|---|---|
| P0.1 | Média | `nginx.conf` escuta 80 e 443 no mesmo `server`, sem `return 301`; o compose publica `${WEB_PORT:-8080}:80` |
| P0.4 | Média | Sem `CHANGELOG.md`; commit diz `v1.1.0`, arquivos de versão seguem em `1.0.0` |
| P0.5 | Média-Alta | `Login.tsx:21-25` define `DEMO_ACCOUNTS` com senhas literais e renderiza em `:272-296` sem guarda de `import.meta.env` |
| P1.2 | Média | `_service_scopes` só é lido em `integration_exports.py`; `instrument_data` aceita `SERVICE` sem escopo |
| P3.1 | Média | `complete_execution` não exige consumo de insumo registrado |
| P4.1 | Média | `attributes` continua fora da lista imutável em `0011_fase5_guards_integridade.py:92-105` |
| P4.2b | Média | Sem alíquota: zero ocorrências de `aliquot` no backend |
| P5.1 | Média | CI sem SAST/SCA (`bandit`, `pip-audit`, `semgrep`, `trivy`) |
| P5.2 | Média | Sem E2E de navegador; `docker-smoke.sh` valida a stack por HTTP |
| P0.2b | Baixa | Script de backup sem CronJob/timer/cron versionado |
| P1.1b | Baixa | Sem runbook dedicado nem alerta de outbox pendente |
| P6.4 | Baixa | `.opencode/` está no `.gitignore`; a skill de pendências existe só localmente |

### 9.5 Achados novos

1. **Credenciais de demonstração na UI (P0.5).** O parecer de 17/11 não viu isso
   porque o arquivo mudou depois. O painel preenche usuário e senha com um clique;
   o aviso textual ("nunca em produção") **não é controle**. Em build de produção
   isso é entrega de credencial válida junto com o binário.
2. **Deriva de versão (P0.4).** O commit `6e7354d` se anuncia como `v1.1.0`, mas
   `backend/pyproject.toml` e `frontend/package.json` continuam em `1.0.0` e não
   existe `CHANGELOG.md`. O binário validado não é identificável por versão.
3. **Backup existe, rotina não (P0.2b).** Há script e há restauração testada, mas
   nada garante que ele rode. Um backup não agendado não é controle operacional.
4. **Skill de pendências fora do versionamento (P6.4).** `.opencode/` está no
   `.gitignore`. O backlog e a auditoria só existem na máquina local — outro
   desenvolvedor não os recebe.
5. **TLS do k8s já correto.** `deploy/k8s/ingress.yaml:10` tem
   `ssl-redirect: "true"`. A lacuna de P0.1 é só o caminho docker-compose.

### 9.6 Evidência de execução

```
Ambiente: Python 3.12 (worktree limpo em 6e7354d)
Comando:  python -m pytest -q --tb=line
Resultado: 149 passed, 9 skipped, 14 warnings in 283.04s (0:04:43)
```

Os 9 ignorados continuam sendo os que exigem PostgreSQL real e rodam no job
`postgres` do CI.

Auditoria automatizada do backlog (24 checks): **12 PASS · 12 FAIL · 0 UNKNOWN**.
Os FAIL correspondem exatamente aos 12 itens abertos de 9.4.

### 9.7 Conclusão do adendo

O parecer de 17/11 está **estruturalmente correto e factualmente desatualizado**.
O sistema fechou os riscos 1, 3 e 4 e quase fechou o 2; o risco 5 encolheu para um
item (consumo de insumo). O que sobrou é de outra natureza: **disciplina de
release** (versão, changelog, redirect), **exposição de demo** e **pipelines de
segurança**. Nenhum exige redesenho.

**Recomendação revisada:** o Horizonte 3 pode avançar assim que P0.5 e P0.1
fecharem; P0.4 deve entrar no mesmo pacote de release. Os demais itens são
endurecimento incremental.

