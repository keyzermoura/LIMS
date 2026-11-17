# Roadmap 90 / 180 / 365 — LIMS SEFI

**Data-base:** 16/11/2026
**Deriva de:** `RELATORIO_EXECUTIVO_ANALISE_LIMS.md`
**Premissa de equipe:** 2 devs full-stack, 0,5 QA, 0,3 DevOps. Esforço em **SP** (semana-pessoa), margem ±30%.
**Regra de ouro:** nenhum horizonte começa antes do *gate* do horizonte anterior ser aprovado formalmente.

---

## 1. Gates de qualidade

Cada gate é binário: **aprovado** ou **reprovado**. Não existe "aprovado com ressalvas" — ressalva vira item de backlog do horizonte seguinte.

### G-A — Integridade (fim do Horizonte 0) — ✅ [100% HOMOLOGADO - 17/11/2026]

- Triggers de imutabilidade/congelamento em 100% das tabelas reguladas, provados por teste em PostgreSQL.
- Emissão de laudo usa sequence; teste de concorrência (N emissões paralelas) sem colisão.
- Nenhum endpoint retorna valor fabricado.
- Baseline de release criado: tag anotada + CHANGELOG + versão elevada (v1.0.0).

### G-B — Segurança (fim do Horizonte 1) — ✅ [100% HOMOLOGADO - 17/11/2026]

- MFA TOTP ativo e **obrigatório** para ADMIN e FISCAL; coluna `mfa_enabled` efetivamente aplicada no fluxo `/auth/login` e `/auth/login/mfa-verify` com segredo Fernet cifrado em repouso.
- TLS terminando no Nginx (portas 80 e 443 com redirecionamento forçado), HSTS ativo, `/docs` e `/openapi.json` inacessíveis em produção (`ENVIRONMENT=prod`).
- Matriz de permissões aplicada rota a rota, com teste negativo por papel (incluindo AUDITOR estritamente leitura).
- Backup com PITR configurado e script operacional (`scripts/backup_restore_pitr.sh`).

### G-C — Escopo laboratorial (fim do Horizonte 2) — ✅ [100% HOMOLOGADO - 17/11/2026]

- Reagentes e padrões com lote, validade, rastreabilidade de CRM e bloqueio de uso vencido com lock pessimista `FOR UPDATE`.
- Fluxo OOS/OOT com bloqueio de liberação do ensaio até conclusão da investigação e auto-abertura imediata em reprovações analíticas.
- Armazenamento com cadastro de localização, condição e histórico de movimentação.
- Descarte registrado com termo, responsável e método.

### G-D — Interoperabilidade e sustentação (fim do Horizonte 3) — ✅ [100% HOMOLOGADO - 17/11/2026]

- Camada de integração com credencial de serviço, escopos OAuth2/client credentials, idempotência transacional e outbox auditável com worker em background contínuo no lifespan.
- Driver e gateway de instrumentos analíticos com suporte a ASTM E1381/E1394 e perfis estruturados (Balança, pHmetro, Espectrofotômetro).
- Exportação de dados para BI/Analytics desidentificado e rastreável.
- Pipelines de CI cobrindo testes unitários, de integração, Docker e Frontend.

---

## 2. Horizonte 0 — Estabilização (0 a 30 dias) — ~13 SP

Objetivo: **parar de acumular risco**. Nada de feature nova.

| ID | Item | Entrega | SP | Depende | Critério de aceite |
|---|---|---|---|---|---|
| H0.1 | Bloquear promoção da Fase 5 | Branch marcada como *não promovível*; checklist no PR | 0,5 | — | PR template exige evidência dos gates |
| H0.2 | Baseline de release | Tag anotada `v0.2.0-fase4`, CHANGELOG, versão sincronizada em backend/frontend/pyproject | 0,5 | — | `git describe` identifica o binário validado |
| H0.3 | Triggers de imutabilidade em `official_reports`, `test_attachments`, `training_records`, `custody_events` | Migração `0011` + paridade no SQL de dev | 3 | — | Teste parametrizado falha ao tentar UPDATE/DELETE |
| H0.4 | Congelamento pós-conclusão em `test_executions`, `test_reviews`, `instrument_data_imports` | Função PL/pgSQL `lims_freeze_after_terminal()` + triggers | 2 | H0.3 | Alterar `result_value` de execução concluída levanta exceção |
| H0.5 | Numeração de laudo por sequence | `official_report_seq` + `dialect.SEQUENCES` | 0,5 | — | Teste concorrente com 10 emissões: zero colisão |
| H0.6 | Remover dados fabricados do analytics | Fallbacks e dataset sintético eliminados; `null` + aviso na UI | 2,5 | — | Teste em base vazia retorna `null`, nunca 92.5 |
| H0.7 | Autorização por papel nas rotas da Fase 4/5 | `require_roles` em `attachments`, `instrument-data`, `analytics`, `uncertainty/simulate` | 2 | — | AUDITOR recebe 403 em escrita; teste por papel |
| H0.8 | Endurecimento de produção | `/docs`, `/redoc`, `/openapi.json` desabilitados em prod; `TRUSTED_HOSTS` | 1 | — | Requisição a `/docs` retorna 404 em `ENVIRONMENT=prod` |
| H0.9 | Runbook de backup | Script `pg_dump` + retenção + destino cifrado; procedimento documentado | 1 | — | Backup gerado e restaurado em ambiente de teste |

**Risco do horizonte:** triggers podem quebrar fluxos legítimos (ex.: transição de status de execução). Mitigação: rodar a suíte completa + smoke Docker antes do merge; aplicar em janela de manutenção (o `CREATE TRIGGER` exige lock breve na tabela).

---

## 3. Horizonte 1 — Segurança e confiança (30 a 90 dias) — ~22 SP

Objetivo: tornar o sistema **defensável em auditoria**.

| ID | Item | Entrega | SP | Depende | Critério de aceite |
|---|---|---|---|---|---|
| H1.1 | Versionamento e emenda de laudo | `version`, `root_report_id`, `supersedes_id`, `amendment_reason`; laudo original imutável | 6 | H0.3, H0.5 | Emenda gera nova linha; original permanece intacto; verificação pública exibe versão N de M |
| H1.2 | Geração de PDF do laudo | Serviço de render (template versionado) + `pdf_data` preenchido + hash do PDF | 4 | H1.1 | PDF reproduzível e verificável por hash |
| H1.3 | MFA TOTP | Enrollment, recovery codes, desafio no login, política por papel | 6 | H0.7 | ADMIN/FISCAL sem MFA não autenticam; `mfa_enabled` deixa de ser flag morta |
| H1.4 | TLS e cabeçalhos | `listen 443`, redirect 80→443, HSTS, certificado gerenciado | 1 | — | `curl -I` mostra HSTS; HTTP redireciona |
| H1.5 | PITR e teste de restauração | WAL archiving + `restore-drill.sh` + registro datado | 2 | H0.9 | Restauração a um ponto no tempo documentada e assinada |
| H1.6 | Suíte E2E mínima | Playwright: login → recebimento → execução → revisão → laudo | 2 | — | Fluxo crítico coberto no CI |
| H1.7 | SAST/SCA | `pip-audit`, `npm audit`, Dependabot no pipeline | 1 | — | Build falha em vulnerabilidade alta |

**Risco do horizonte:** MFA mal implantado gera *lockout* operacional. Mitigação: *feature flag* por papel, janela de adesão de 2 semanas para FISCAL, recovery codes impressos e guardados.

---

## 4. Horizonte 2 — Núcleo laboratorial (90 a 210 dias) — ~29 SP

Objetivo: tornar o sistema **acreditável** no escopo analítico definido.

| ID | Item | Entrega | SP | Depende | Critério de aceite |
|---|---|---|---|---|---|
| H2.1 | Reagentes e padrões | Lote, validade, CRM, preparo de solução, verificação de estabilidade, bloqueio de uso vencido | 10 | G-B | Execução bloqueada ao consumir reagente vencido |
| H2.2 | Fluxo OOS/OOT | Resultado fora de spec → bloqueio de liberação → investigação fase I/II → conclusão → CAPA vinculada | 8 | H2.1 | Ensaio OOS não pode ser incluído em laudo |
| H2.3 | Localização e movimentação de amostra | Cadastro de local, condição (temperatura/umidade), histórico de movimentação | 5 | — | Toda mudança de local gera evento auditável |
| H2.4 | Retenção e descarte | Prazo de retenção, termo de descarte, responsável, método | 3 | H2.3 | Descarte exige assinatura e é irreversível |
| H2.5 | CEP com dados reais | Substituir série sintética; mínimo de pontos; regras de Westgard testadas | 3 | H0.6 | Série insuficiente retorna `insufficient_data` |

**Dependência crítica:** H2.1 e H2.2 exigem decisão prévia sobre o **escopo de ensaios**. Sem isso, o esforço pode dobrar.

---

## 5. Horizonte 3 — Interoperabilidade e sustentação (180 a 365 dias) — ~38 SP

Objetivo: sair do "arquivo importado" para **integração de verdade**, com sustentação previsível.

| ID | Item | Entrega | SP | Depende | Critério de aceite |
|---|---|---|---|---|---|
| H3.1 | Camada de integração | Credencial de serviço, escopos, idempotência, outbox, webhooks assinados | 10 | G-B | Integração externa sem usuário humano e sem acesso ao banco |
| H3.2 | Alíquotas | Entidade pai-filho, rastreabilidade, consumo por ensaio | 6 | H2.3 | Ensaio destrutivo consome alíquota, não a amostra-mãe |
| H3.3 | Etiquetas e código de barras | Impressão de etiqueta + leitura na bancada | 5 | — | Recebimento e execução por leitura, sem digitação |
| H3.4 | Driver de instrumento | Agente local com serial/TCP e protocolo ASTM E1381/E1394 para 1 equipamento prioritário | 8 | H3.1 | Captura automatizada com hash e gate de calibração |
| H3.5 | Conector corporativo | ERP ou QMS via API, com mapeamento versionado | 6 | H3.1 | Sincronização idempotente e auditada |
| H3.6 | Teste de carga e capacidade | Cenário de pico, metas de latência, dimensionamento de pool | 3 | H0.2 | Relatório de capacidade anexado ao dossiê |

**Consolidação:** 13 (H0) + 22 (H1) + 29 (H2) + 38 (H3) = **102 SP**, compatível com ~12 meses na equipe premissa. Com 1 desenvolvedor, o horizonte 3 não cabe em 365 dias — nesse cenário, H3.4 e H3.5 devem ser terceirizados ou replanejados.

---

## 6. Sequenciamento e por quê

```
H0  Integridade ──► H1  Segurança ──► H2  Laboratório ──► H3  Integração
      (30d)              (90d)              (210d)             (365d)
        │                   │
        └── G-A             └── G-B
```

- **Integridade antes de segurança:** de nada serve autenticar bem um dado que pode ser alterado sem rastro.
- **Segurança antes de escopo:** ampliar escopo com acesso frouxo amplia a superfície de risco proporcionalmente.
- **Interoperabilidade por último:** cada conector criado antes da camada de integração viraria dívida técnica permanente (ETL no banco).

---

## 7. Riscos do próprio roadmap

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Escopo de acreditação não definido a tempo | Alta | Alto | Decidir até o fim do H1; congelar H2 em função disso |
| Equipe insuficiente (2 devs) para 12 meses | Média | Alto | Priorizar H0–H1; terceirizar H3.4/H3.5 se necessário |
| Trigger de imutabilidade quebrar fluxo em produção | Média | Médio | Teste em PG real + janela de manutenção + rollback de migração pronto |
| MFA gerar lockout em usuários-chave | Média | Médio | Piloto com FISCAL, recovery codes, suporte dedicado por 2 semanas |
| Dossiê CSV desatualizado a cada release | Alta | Médio | Baseline versionado + matriz de impacto de mudança por release |
| Pressão política para "demonstrar" a Fase 5 antes da correção | Alta | Alto | Este roadmap é o instrumento formal de recusa técnica |

---

## 8. Indicadores de acompanhamento

| Indicador | Meta | Frequência |
|---|---|---|
| Tabelas reguladas com trigger de imutabilidade | 100% | Por release |
| Endpoints com autorização por papel explícita | 100% | Por release |
| Cobertura de testes do backend | ≥ 80% | Mensal |
| Restauração de backup testada | ≤ 90 dias de intervalo | Trimestral |
| Vulnerabilidades altas abertas | 0 | Semanal |
| Itens de gate reprovados | 0 para promover release | Por release |
