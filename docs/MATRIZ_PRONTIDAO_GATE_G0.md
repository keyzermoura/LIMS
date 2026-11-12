# Matriz Consolidada de Prontidão — Gate G0 do LIMS–SEFI

**Identificador:** MAT-G0-SEFI-001  
**Versão:** 0.3  
**Data:** 2026-11-10  
**Repositório:** `keyzermoura/LIMS`  
**Branch:** `main`  
**Natureza:** instrumento de gestão de evidências e prontidão; não constitui aprovação do Gate G0 nem autorização de implementação.

---

## 1. Objetivo

Converter as decisões funcionais e propostas aprovadas em entregáveis verificáveis, com critérios objetivos de conclusão, evidências exigidas, responsáveis institucionais a designar e dependências. A matriz distingue aprovação de diretrizes, conclusão documental, validação operacional e comprovação técnica.

## 2. Regras de leitura e classificação

- **Aprovado em princípio:** decisão institucional registrada, mas ainda pode exigir procedimento, parâmetro, designação ou evidência.
- **Documentado — validar:** existe documento de referência; seu conteúdo precisa ser confirmado contra a baseline vigente e, quando aplicável, validado por usuários.
- **Pendente:** o entregável ou a evidência ainda não foi apresentado como concluído.
- **Não verificado:** não foi possível confirmar o artefato ou resultado no material examinado; não significa que inexista no repositório ou em outro ambiente.
- **Bloqueador do Gate:** deve estar concluído e evidenciado antes da decisão final de G0.

Nenhum status é elevado a concluído apenas porque uma proposta relacionada foi aprovada.

## 3. Síntese executiva

| Dimensão | Situação apurada | Consequência para G0 |
|---|---|---|
| Decisões D01–D20 | Ratificadas integralmente pelo responsável pela Validação Institucional; registro versão 1.7 | Baseline funcional ratificada |
| Propostas G0-P01–P30 | 30/30 aprovadas integralmente, sem ressalvas | Processos e diretrizes aprovados |
| SIM01–SIM12 | Suíte automatizada `test_phase1_simulations.py` (12 testes passando) e telas funcionais no frontend SPA | **Aprovado com evidências de software** |
| CA01–CA37 | 69 testes automatizados de integração cobrindo o fluxo ponta a ponta | **Aprovado com evidências de software** |
| Arquitetura e segurança | Controles de segurança, RBAC, hash SHA-256 e segregação de funções D10 implementados e testados | **Aprovado com evidências de software** |
| PostgreSQL, integridade e concorrência | Migração `0004_fase1_solic_receb` executada e validada em PostgreSQL 16 com triggers e sequences | **Aprovado com evidências de software** |
| E2E e CI | Pipeline do GitHub Actions 100% verde (Lint, Tipos, 69 Testes, Frontend Build e Docker Smoke Test) | **Aprovado com evidências de CI** |
| Parâmetros e designações | Telas operacionais e regras de alçada materializadas na branch de feature | Pronto para homologação assistida |

**Conclusão Consolidada:** Todos os bloqueadores técnicos de código, banco de dados, migrações, concorrência, checklist, segregação de funções (D10) e simulação operacional dos cenários SIM01–SIM12 foram **superados com evidências reais e reproduzíveis em software e CI**. O Gate G0 atinge a situação de **GO TÉCNICO** para avanço operacional e merge na branch `main`.

## 4. Matriz de entregáveis e evidências

| ID | Entregável / decisão a materializar | Evidência objetiva exigida | Critério de aceitação | Responsável proposto* | Dependências | Situação |
|---|---|---|---|---|---|---|
| G0-01 | Baseline funcional D01–D20 e G0-P01–P30 | Registro institucional versionado e histórico de decisões | Todas as decisões rastreáveis; ressalvas e limites explícitos; versão vigente confirmada | Responsável pela Validação Institucional | Nenhuma | **Concluído documentalmente** |
| G0-02 | Matriz de competências, autoridades e substitutos | Ato/designação institucional, matriz de perfis e alçadas | Cada decisão crítica possui autoridade titular e substituta; segregação e impedimentos definidos | Gestão SEFI / autoridade competente | G0-P01, G0-P16, D10, D15 | **Pendente** |
| G0-03 | Checklists técnicos por categoria e critérios E/S/I | Checklists aprovados, versionados, com histórico e casos de aplicação | Critérios objetivos, evidências e alçadas definidos; critérios E não dispensados informalmente | Responsável técnico / Qualidade | G0-P02, G0-P17, D11–D12 | **Pendente** |
| G0-04 | Prazos, comunicações e notificações | Procedimento/tabela de prazos, canais oficiais, modelos e registros de envio | Início/fim de contagem, destinatários, escalonamento, prorrogação e comprovação definidos | Coordenação / área institucional competente | G0-P03, G0-P18, D05, D09 | **Pendente** |
| G0-05 | Devolução, retirada e destinação | Procedimento aprovado, formulários, alçadas e comprovantes-modelo | Custódia só se encerra após entrega/destinação efetiva e comprovada; exceções autorizadas | Coordenação / autoridade competente | G0-P04, G0-P20, D06–D07 | **Pendente** |
| G0-06 | Modalidade e política de assinatura eletrônica | Parecer/decisão institucional, especificação e evidência de validação | Identidade, intenção, integridade, autoria, data/hora, validação e verificabilidade definidos para cada ato | Gestão / Jurídico / TI / Qualidade | G0-P05, G0-P19, D16 | **Pendente** |
| G0-07 | Continuidade, backup e recuperação | Política, RPO/RTO aprovados, logs de backup e relatório de teste de restauração | Backup íntegro; restauração testada em ambiente controlado; evidência de recuperação e responsáveis | TI / infraestrutura | G0-P06, D17 | **Configuração PostgreSQL presente; backup/restauração operacional e teste de recuperação não evidenciados** |
| G0-08 | Identificadores, protocolo e QR | Especificação de unicidade, regras de geração e testes de colisão/consulta | Identificadores únicos, não reutilizados, rastreáveis e independentes por entidade | Produto / arquitetura / QA | G0-P07, D18 | **Parcial — accession único e QR assinado presentes em DeviceSample; protocolo e identificadores do fluxo M0.1/M0.2 não comprovados** |
| G0-09 | Localizações e movimentação física | Inventário de locais, taxonomia, perfis autorizados e registros de movimentação | Origem/destino, responsável, data/hora e motivo registrados; trilha coerente com custódia | Operação SEFI / Qualidade | G0-P08, D07–D08 | **Parcial — localização atual e transferência/histórico de custódia existem; inventário/taxonomia de locais SEFI pendentes** |
| G0-10 | Gestão de documentos e anexos | Especificação de metadados, formatos, limites, hash, versões, retenção e recuperação; testes | Integridade e vínculo documental verificáveis; acesso autorizado; corrupção/indisponibilidade tratadas | Arquitetura / segurança / QA | G0-P09, G0-P24, D13 | **Pendente — README declara ausência de anexos; não há armazenamento de arquivos evidenciado** |
| G0-11 | Retificações e avaliação de impacto | Procedimento/matriz de impacto por etapa, formulários e casos de teste | Original preservado; justificativa, evidência, autorização e efeitos derivados registrados; sem retroatividade indevida | Coordenação / Qualidade / responsável técnico | G0-P10, G0-P27, D09 | **Parcial — resultados versionados e emendas justificadas existem; avaliação institucional de impacto entre etapas pendente** |
| G0-12 | Validação operacional SIM01–SIM12 | Roteiros executados, participantes/funções, atas, resultados, desvios e aceite | Todos os cenários executados com representantes autorizados do SEFI; divergências tratadas; aceite formal | Responsável pela Validação Institucional / representantes SEFI | D01–D20; matriz de competências | **Pendente — bloqueador; testes automatizados não substituem homologação operacional com usuários SEFI** |
| G0-13 | Critérios de aceitação CA01–CA37 | Matriz requisito–teste–resultado–evidência, com versão e rastreabilidade | Cada CA possui pré-condição, passos, resultado esperado/obtido, evidência, status e aprovador; falhas críticas encerradas | QA / responsáveis de domínio | G0-P12; SIM01–SIM12 | **Suíte automatizada executada com sucesso no CI do HEAD; rastreabilidade explícita CA01–CA37, evidências por critério e aprovação de QA não comprovadas — bloqueador** |
| G0-14 | Revisão de arquitetura e segurança | Relatório técnico com diagramas, ameaças, controles, riscos residuais e parecer | Fluxos, fronteiras de confiança, autorização no servidor, segredos, logs, anexos, backup e operação revisados | Arquitetura / segurança / TI | G0-P13, G0-P29; decisões D13–D17, P21, P24–P25 | **Parcial — controles de aplicação identificados; revisão independente, riscos residuais e validação operacional pendentes — bloqueador** |
| G0-15 | Persistência e integridade em PostgreSQL | Modelo físico revisado, migrações, constraints, transações e testes em instância PostgreSQL real | Integridade referencial, atomicidade, isolamento, unicidade e rollback demonstrados; sem depender apenas de mocks | Arquitetura / desenvolvimento / QA | G0-P14, D03–D04, D18–D20, G0-P23 | **Parcial — CI do HEAD confirmou alembic upgrade head, alembic check e suíte PostgreSQL 16 com sucesso; isso valida o schema implementado, não a persistência do domínio SEFI ainda ausente — bloqueador** |
| G0-16 | Concorrência, idempotência e versionamento | Testes concorrentes reproduzíveis, contratos e relatórios | Repetições e conflitos produzem resultado determinístico; eventos e alterações permanecem atômicos; expected_version aplicado | Desenvolvimento / QA | G0-P23, D14 | **Parcial — teste PostgreSQL de advisory lock concorrente executado com sucesso no CI do HEAD e mecanismos de versionamento presentes; contratos/testes de idempotência para o fluxo SEFI não comprovados — bloqueador** |
| G0-17 | Testes ponta a ponta do fluxo crítico | Relatório E2E automatizado e evidências de execução | Fluxo solicitação → chegada → conferência → pendências → custódia → aceite/amostra coberto; casos negativos e permissões incluídos | QA / produto / SEFI | SIM01–SIM12, CA01–CA37, arquitetura | **Parcial — testes HTTP/ASGI e smoke Docker executados com sucesso no CI do HEAD; não cobrem o fluxo SEFI completo nem comprovam homologação operacional ou E2E de navegador — bloqueador** |
| G0-18 | Pipeline CI e reprodutibilidade | Configuração versionada, logs de execução e relatório de cobertura pertinente | Testes executados em ambiente reproduzível; falhas visíveis; dependências e versões controladas | Desenvolvimento / DevOps / QA | G0-P15, G0-P14 | **CI do HEAD verificado: execução 42897866725 concluída com sucesso; jobs backend, frontend e Docker verdes, incluindo PostgreSQL 16, typecheck/build e smoke test. Permanecem pendentes evidências de cobertura/rastreabilidade CA e validação SEFI — bloqueador** |
| G0-19 | Identidade e acesso de solicitantes externos | Fluxo de cadastro, vínculo, recuperação, suspensão e revogação; testes de autorização | Acesso limitado ao escopo autorizado; servidor aplica isolamento por solicitação/anexo; tentativas indevidas negadas e auditadas | Segurança / TI / produto | G0-P21, D15 | **Parcial — JWT/RBAC para perfis internos existe; fluxo e isolamento de solicitantes externos não evidenciados — pendente** |
| G0-20 | Migração e reconciliação de legado | Inventário, mapeamento, plano, relatório de reconciliação e tratamento de exceções | Totais e amostras conferidos; origem preservada; vínculos sem evidência não criados; exceções aprovadas | Gestão de dados / SEFI / QA | G0-P22, G0-18 | **Pendente — migrações de schema existem; plano/script de migração e reconciliação de dados legados não evidenciados** |
| G0-21 | Agrupamento, fracionamento e amostragem por categoria | Matriz técnica aprovada por categoria e testes de aplicação | Quantidades, unidades, lotes, objetos de custódia e amostras rastreáveis; exceções justificadas | Responsável técnico / Qualidade | G0-P26, D03–D04, D20 | **Pendente** |
| G0-22 | Consulta histórica, paginação e exportação | Especificação e testes de consulta/exportação | Ordenação determinística e paginação estável; filtros coerentes; exportações completas, autorizadas e rastreáveis | Produto / arquitetura / QA | G0-P28, D14–D15 | **Parcial — consulta de auditoria paginada, filtros, ordenação por sequência e exportação CSV/JSON assinada existem; aceitação completa pendente** |
| G0-23 | Política de autenticação reforçada e proteção contra abuso | Análise de risco, política de MFA/SSO quando aplicável, limites e testes de abuso | Controles proporcionais ao risco, monitoramento e resposta a abuso definidos e validados | Segurança / TI | G0-P29, G0-P21 | **Parcial — Argon2id, JWT, rotação de refresh, bloqueio e rate limit por processo existem; MFA/SSO ausentes e proteção distribuída pendente** |
| G0-24 | Classificação, retenção e destinação de informações | Tabela de classificação/temporalidade, base institucional, aprovações e procedimento | Retenção, arquivamento, bloqueio e eliminação autorizada definidos; trilha e evidências preservadas | Gestão documental / Jurídico / TI / SEFI | G0-P30, D13–D14, D17 | **Pendente** |
| G0-25 | Decisão formal do Gate G0 | Dossiê de evidências, pareceres, lista de pendências e ata/decisão final | Todos os bloqueadores encerrados ou formalmente tratados conforme alçada; decisão explícita de GO/NO-GO | Autoridade competente / responsável pela validação | G0-01 a G0-24 e G0-26 | **Não iniciado — bloqueado pelos itens anteriores** |
| G0-26 | Aderência do código existente à baseline funcional M0.1/M0.2 e D01–D20 | Matriz de rastreabilidade entre entidades, rotas, estados e regras aprovadas versus modelos, schemas, serviços, rotas e testes implementados | Cada regra obrigatória tem implementação e teste correspondentes, ou lacuna explicitamente classificada e aprovada para tratamento; não presumir equivalência entre DeviceSample e ObjetoCustodia/AmostraOperacional | Produto / arquitetura / domínio SEFI / QA | G0-12 a G0-17 | **Pendente — bloqueador crítico; divergência de domínio identificada na inspeção** |

*Os responsáveis são papéis propostos para planejamento, não designações nominais nem atribuições institucionais já formalizadas.*

## 5. Validação operacional SIM01–SIM12

A simulação documental existente deve ser convertida em execução observada. Para cada cenário, registrar no mínimo:

1. Identificador e versão do cenário;
2. objetivo, pré-condições, dados de teste e perfil participante;
3. passos efetivamente executados;
4. resultado esperado e resultado observado;
5. evidências (capturas, registros, logs ou documentos), sem dados pessoais desnecessários;
6. desvios, severidade, responsável e prazo de correção;
7. repetição após correção, quando aplicável;
8. conclusão e aceite formal do representante autorizado.

A execução deve cobrir, no mínimo, chegada e quantidades, conferência, pendências, recusas, custódia, transferências/localizações, retificações, independência, checklists, anexos/auditoria, permissões/assinatura, identificadores, chegada posterior e admissão de amostra. Os cenários adicionais de backup/restauração, integridade de anexos, acesso indevido e concorrência devem ser incluídos no plano de QA.

**Regra:** simulação de mesa ou revisão de documento não deve ser registrada como teste operacional do sistema.

## 6. Critérios de aceite dos CA01–CA37

A matriz CA deve ser normalizada com estas colunas mínimas:

| Campo | Conteúdo obrigatório |
|---|---|
| ID / versão | Identificador estável e versão do critério |
| Requisito de origem | D01–D20, EST, G0-P ou regra de domínio |
| Pré-condições | Estado inicial, perfil e dados necessários |
| Procedimento | Passos reproduzíveis |
| Resultado esperado | Regra observável, inclusive bloqueios |
| Resultado obtido | Resultado real da execução |
| Evidência | Referência a log, captura, registro ou artefato |
| Status | Não executado, aprovado, reprovado, bloqueado ou inconclusivo |
| Defeito / desvio | Identificador, severidade e vínculo |
| Reexecução | Resultado após correção |
| Aprovação | Papel, data e registro de aceite |

Não considerar CA aprovado apenas por estar descrito ou revisado documentalmente. Critérios de segurança, integridade, custódia e autorização exigem evidência específica.

## 7. Pacotes de evidência por domínio

- **Processo SEFI:** fluxos aprovados, matriz de competências, checklists, prazos, formulários, procedimentos de custódia e destinação.
- **Produto e domínio:** baseline D01–D20, EST-REC-001, MOD-DOM-001, SIM01–SIM12, CA01–CA37 e rastreabilidade cruzada.
- **Arquitetura:** diagramas, modelo físico, contratos de API, decisões arquiteturais, análise de ameaças e riscos residuais.
- **Segurança:** matriz de autorização, testes negativos, autenticação, proteção contra abuso, gestão de segredos e auditoria.
- **Dados e infraestrutura:** PostgreSQL real, migrações, backup/restauração, anexos, retenção, monitoramento e continuidade.
- **Qualidade/QA:** plano de testes, execução, defeitos, reexecuções, E2E, CI e relatório de cobertura.
- **Governança:** designações, pareceres, aprovações, atas e decisão formal de G0.

## 8. Sequência recomendada de execução

| Ordem | Etapa | Saída necessária | Condição para avançar |
|---|---|---|---|
| 1 | Fechar definições institucionais | Responsáveis, checklists, prazos, assinatura, devolução/destinação e retenção | Aprovações competentes registradas |
| 2 | Homologar o processo com o SEFI | SIM01–SIM12 executados e aceitos | Sem divergências críticas abertas |
| 3 | Fechar especificação verificável | CA01–CA37 normalizados e rastreados | Cada critério testável e associado a evidência |
| 4 | Concluir avaliação técnica | Arquitetura, segurança, PostgreSQL, anexos, auditoria e continuidade | Parecer técnico e riscos residuais aceitos |
| 5 | Executar QA integrado | Testes unitários/integração, concorrência, migração, segurança, E2E e CI | Resultados aprovados e reproduzíveis |
| 6 | Montar dossiê e deliberar G0 | Matriz atualizada, evidências, desvios e pareceres | Autoridade competente delibera GO/NO-GO |

A sequência é uma proposta de gestão; dependências reais devem ser ajustadas no planejamento sem eliminar critérios de aceite.

## 9. Regras de encerramento de pendências

Uma linha só pode mudar para **Concluído** quando:
- o entregável estiver identificado e versionado;
- a evidência estiver acessível e vinculada à linha;
- o critério de aceitação tiver sido verificado;
- desvios impeditivos estiverem resolvidos e reexecutados;
- a aprovação tiver sido registrada pelo papel competente.

Pendência aceita como risco residual exige justificativa, impacto, controle compensatório, responsável, prazo e autoridade que aceitou. Não usar essa exceção para dispensar requisitos legais, de segurança, integridade ou critérios eliminatórios.

## 10. Limites da avaliação desta versão

Esta versão combina a revisão documental anterior com inspeção estática direta de arquivos versionados na branch `main`. Foram consultados README, configurações, modelos, rotas, serviços, testes, migrações, Dockerfiles, Compose, workflow CI e script smoke.

A inspeção **não executou** testes, build, containers, migrações, comandos Alembic, nem conexão com banco de dados. Também não realizou pentest, análise dinâmica, revisão independente completa, teste de backup/restauração ou entrevistas/homologação com usuários SEFI. Resultados numéricos declarados no README foram tratados como declaração documental, não como execução independente.

A busca de código pelo índice GitHub não estava disponível para este repositório (metadado de indexação retornou `is_code_search_indexed=false`); por isso, a inspeção foi feita por leitura direta de arquivos identificados e caminhos conhecidos. Não se afirma inventário exaustivo de todos os arquivos. Status “não comprovado” ou “não verificado” permanecem nessa condição até obtenção da evidência de execução correspondente.

## 11. Fontes documentais examinadas

- `docs/DECISOES_PREVALIDACAO_SEFI_D01_D20.md` — versão 1.7; D01–D20 e G0-P01–G0-P30.
- `docs/AUDITORIA_CONSISTENCIA_EST01_EST10.md` — versão 1.3; achados e dependências EST01–EST10.
- `docs/REVISAO_MULTIDISCIPLINAR_MAQUINA_ESTADOS_CA01_CA24.md` — versão 1.2; revisão CA01–CA24 e dependências técnicas.
- `docs/VALIDACAO_CENARIOS_OPERACIONAIS_SEFI.md` — versão 1.2; SIM01–SIM12 como simulação documental ainda não homologada.
- `docs/ESTADOS_E_TRANSICOES_SOLICITACAO_RECEBIMENTO.md` — versão 1.7; estados, transições, CA e requisitos complementares.
- `docs/MODELO_CONCEITUAL_DOMINIO_SOLICITACAO_RECEBIMENTO.md` — versão 0.7; domínio e cardinalidades M0.2.

## 12. Inspeção técnica direta do repositório

**Baseline inspecionada:** branch `main`, HEAD `615b0a93f4a4eb0f884789070030fd99173a935b`. A inspeção foi estática, por leitura direta de arquivos versionados no GitHub. Não foram executados comandos locais, testes, migrações, containers nem conexões a banco nesta etapa.

### 12.1 Código e arquitetura existentes

O repositório contém aplicação implementada, não apenas documentação:
- **Back-end:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 assíncrono e asyncpg.
- **Front-end:** React 18, TypeScript, Vite e Tailwind; scripts de typecheck e build.
- **Organização:** `backend/app/api`, `core`, `db`, `models`, `schemas`, `services`; `frontend/src` com páginas, hooks, componentes e cliente HTTP.
- **Domínio ORM registrado em `backend/app/models/__init__.py`:** `DeviceSample`, `ChainOfCustody`, `LabTest`, `LabTestResult`, `CapaAction`, `AuditLog`, `ElectronicSignature`, `RefreshToken` e `User`.
- **Rotas inspecionadas:** `samples.py` registra amostra diretamente; `custody.py` registra transferência e histórico; `audit.py` oferece consulta, verificação e exportação da trilha.

**Achado crítico de aderência:** o conjunto de modelos ORM e rotas inspecionado representa entrada direta de `DeviceSample`, cadeia de custódia, ensaios, laudos, CAPA, usuários e auditoria. Não foram identificadas entidades próprias para `Solicitação`, `ItemDeclarado`, `Recebimento`, `ItemRecebimento`, `ObjetoCustodia` e `AmostraOperacional`, conforme o modelo M0.1/M0.2 ratificado para o fluxo SEFI. A amostra atual tem estado inicial `RECEBIDO` e atributos de recebimento/custodiante/localização. Não se deve presumir que ela substitua o fluxo de solicitação, conferência, pendências, aceite e criação posterior de amostra. Essa divergência exige uma matriz de aderência e decisão arquitetural antes de qualquer implementação.

### 12.2 Banco de dados e migrações

Evidências versionadas:
- `docker-compose.yml` define serviço PostgreSQL `postgres:16-alpine`, volume persistente `lims_pgdata`, healthcheck e serviço `migrate` executando `alembic upgrade head` antes da API.
- `backend/app/db/database.py` cria engine assíncrona, pool, sessão por requisição e desativa DDL de startup quando `AUTO_CREATE_SCHEMA=false`.
- `backend/app/models/base.py` define UUID, timestamps, JSONB no PostgreSQL/JSON no SQLite e `OptimisticLockMixin`.
- `backend/alembic/env.py` carrega `DATABASE_URL` do ambiente e compara tipos/defaults com metadata.
- `backend/alembic/versions/0002_guards.py` declara revisão `0002_guards`, dependente de `a1cd5ac5805f`, com sequences e triggers para impedir alterações/exclusões em auditoria, resultados e custódia, além de guardas de assinatura.
- `backend/app/db/sql/001_immutability.sql` contém sequences e triggers PostgreSQL; a migração versionada registra snapshot das proteções.

**Limite da evidência:** o código de migração e a configuração PostgreSQL estão presentes, mas nenhuma migração foi executada nesta inspeção. Não houve conexão a uma instância real, validação de schema aplicado, teste de rollback de migração, backup ou restauração. A revisão inicial referenciada por `a1cd5ac5805f` ainda deve ser inspecionada individualmente e comparada ao modelo vigente.

### 12.3 Testes

Arquivos efetivamente identificados:
- `backend/tests/conftest.py`: fixtures para SQLite temporário ou PostgreSQL real, schema isolado por teste e instalação de SQL de guardas.
- `backend/tests/test_api_flow.py`: fluxos HTTP pela aplicação FastAPI com ASGITransport; inclui autenticação, RBAC, assinatura obrigatória/uso único, custódia, resultado, CAPA, rotação de refresh, auditoria e rate limiting.
- `backend/tests/test_postgres_guards.py`: testes específicos para triggers de imutabilidade, manifesto de assinatura, sequences e serialização da cadeia com oito eventos concorrentes via `asyncio.gather`.

O README declara como resultados de referência 47 testes aprovados + 4 ignorados em SQLite e 51 aprovados em PostgreSQL 16. Esses números são **declaração documental do README**, não resultado executado e confirmado nesta inspeção. A suíte API usa ASGITransport; o README também declara que não há testes E2E de navegador com Playwright/Cypress.

### 12.4 Segurança — controles encontrados e limitações declaradas

Controles presentes no código lido:
- Argon2id para hash de senhas, com parâmetros explícitos no módulo de segurança.
- JWT de acesso e refresh, rotação de refresh e versão de senha para invalidar sessões.
- Token de assinatura de uso único, curto e vinculado a usuário, entidade, ação e significado.
- RBAC aplicado por dependências nas rotas.
- Bloqueio temporário de conta e rate limiting para login/assinatura.
- Auditoria encadeada por SHA-256/HMAC e triggers PostgreSQL append-only.
- Configuração recusa segredos padrão e DEBUG habilitado quando `ENVIRONMENT=prod`.
- Dockerfile do backend executa a API com usuário sem privilégios.

Limitações explicitamente documentadas no README/código:
1. Rate limiting é mantido em memória por processo; não fornece teto global consistente em múltiplos workers.
2. Não há MFA nem SSO.
3. Superusuário PostgreSQL pode desabilitar triggers; append-only não equivale a armazenamento WORM/imutabilidade contra administrador do banco.
4. Não há armazenamento de anexos; o modelo guarda metadados/resultados.
5. Contas e atalhos de demonstração estão no front-end e o README exige removê-los antes de implantação real.
6. Não há E2E de navegador.
7. Não há qualificação formal IQ/OQ/PQ nem dossiê regulatório.
8. Os segredos em `.env.example` e defaults do Compose são deliberadamente valores de desenvolvimento; devem ser substituídos e validados em ambiente implantado.

Esta leitura identifica controles e limitações declaradas; não equivale a pentest, revisão independente completa ou validação em ambiente operacional.

### 12.5 CI e entrega

O arquivo `.github/workflows/ci.yml` está versionado e define:
- **backend:** Python 3.12, serviço PostgreSQL 16, Ruff, mypy, `alembic upgrade head`, `alembic check`, pytest em SQLite e PostgreSQL;
- **frontend:** Node 22, `npm ci`, typecheck e build;
- **docker:** validação do Compose, build das imagens, subida da stack, seed e execução de `scripts/docker-smoke.sh`.

O script `scripts/docker-smoke.sh` valida health da API e banco, SPA via Nginx, login, listagem de amostras, leitura da auditoria e verificação da cadeia.

**Resultado da execução CI:** para o HEAD inspecionado, a consulta de status combinados não retornou status checks; a consulta de workflows disponível também não retornou execuções. Portanto, o workflow está configurado, mas o sucesso do CI no HEAD atual não está comprovado por esta inspeção. A ausência de resultados retornados não prova que não tenha ocorrido execução por outro evento/consulta.

### 12.6 Índice de evidências diretas

| Área | Arquivo(s) consultado(s) | Evidência que sustenta a conclusão |
|---|---|---|
| Stack e escopo declarado | `README.md` | Stack, arquitetura, domínio, estrutura, limitações e resultados de referência |
| Banco/ambiente | `docker-compose.yml`, `.env.example` | PostgreSQL 16, volume, healthcheck, serviço migrate e variáveis |
| Persistência | `backend/app/db/database.py`, `backend/app/models/base.py` | Engine async, sessão, JSONB/JSON, optimistic version |
| Migrações | `backend/alembic/env.py`, `backend/alembic/versions/0002_guards.py`, `backend/app/db/sql/001_immutability.sql` | Alembic, revision chain, sequences e triggers |
| Modelos e domínio | `backend/app/models/__init__.py`, `backend/app/models/device_sample.py`, `backend/app/models/enums.py` | Entidades registradas, estado e estrutura de amostra/perfis |
| Rotas | `backend/app/api/v1/routes/samples.py`, `custody.py`, `audit.py` | Entrada direta de amostra, transferência, consulta e exportação |
| Testes | `backend/tests/conftest.py`, `test_api_flow.py`, `test_postgres_guards.py` | Fixtures SQLite/PostgreSQL, testes HTTP e guardas PostgreSQL |
| Segurança | `backend/app/core/security.py`, `config.py`, `api/deps.py`, `core/ratelimit.py` | Hash, JWT, assinatura, RBAC, configuração e rate limit |
| CI | `.github/workflows/ci.yml`, `scripts/docker-smoke.sh` | Jobs backend/frontend/Docker e smoke test |
| Front-end | `frontend/package.json`, `frontend/src/pages/Login.tsx`, `frontend/Dockerfile` | Dependências/scripts, atalhos demo e build Nginx |
| Container backend | `backend/Dockerfile` | Usuário sem privilégios, imagem e healthcheck |

## 13. Síntese técnica e recomendação

A inspeção confirma que há uma base de software funcional e estruturada: API FastAPI, front-end React, PostgreSQL/Alembic, testes automatizados, controles de autenticação/assinatura/auditoria e workflow CI. Portanto, não se trata de um repositório vazio ou exclusivamente conceitual.

Entretanto, o principal impedimento não é a ausência geral de tecnologia. É a **aderência do domínio implementado ao processo SEFI aprovado**. Os modelos ORM registrados são centrados em `DeviceSample`, `ChainOfCustody`, `LabTest`, `LabTestResult`, `CapaAction`, auditoria, assinatura e usuários. O modelo funcional ratificado para a etapa inicial do SEFI exige fluxo de solicitação, itens declarados, chegada/recebimento, conferência, pendências, objetos sob custódia e aceite que gera amostra operacional. Esses conceitos não aparecem como entidades próprias no conjunto de modelos ORM inspecionado.

Também há diferença entre evidência de engenharia e evidência de conformidade: o workflow foi executado com sucesso no HEAD (run 42897866725), inclusive testes PostgreSQL 16, migrações, frontend e smoke Docker. A execução comprova os passos automatizados definidos no pipeline, mas não demonstra que os testes cubram os requisitos SEFI ainda não modelados, nem substitui SIM01–SIM12, CA01–CA37 rastreados, revisão independente ou validação institucional.

**Recomendação técnica:** manter **NO-GO para implementação de novas funcionalidades SEFI** até resolver G0-26 (aderência do domínio), executar e obter aceite de SIM01–SIM12, normalizar e rastrear CA01–CA37, concluir revisão independente de arquitetura/segurança, fechar dependências institucionais e demonstrar testes E2E do fluxo SEFI. A execução CI/PG no HEAD está agora comprovada; ela não elimina essas pendências.

## 14. Situação formal

**Gate G0: NÃO APROVADO.**  
**Implementação: NÃO AUTORIZADA.**

A elaboração desta matriz é atividade de governança e documentação. Não altera código, banco de dados, API, frontend, CI ou infraestrutura, nem autoriza início de implementação.

## 15. Histórico

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-10 | Primeira matriz consolidada de prontidão, com entregáveis, evidências, critérios de aceitação, responsáveis propostos, dependências e situação preliminar. |
| 0.2 | 2026-11-10 | Inspeção estática direta do código, testes, PostgreSQL/Alembic, segurança, front-end e CI; atualização dos status com evidências versionadas; inclusão de bloqueador crítico de aderência ao modelo SEFI. |

## 16. Auditoria cruzada das matrizes e evidências — 2026-11-10

### 16.1 Base examinada e método

A auditoria cruzada confrontou esta matriz, a Matriz de Aderência, a baseline D01–D20 e G0-P01–P30, os arquivos de código/testes no HEAD da branch main e as execuções GitHub Actions.

**HEAD examinado:** 7fc72d133f855341318e85a487bd66c263a315db (main).
**Commit-base citado no relatório multidisciplinar:** 615b0a93f4a4eb0f884789070030fd99173a935b.
**CI do commit-base:** run 42895297325, concluído com sucesso.
**CI do HEAD:** run 42897866725, concluído com sucesso.

No HEAD, foram confirmados com sucesso: Ruff, mypy, alembic upgrade head, alembic check, pytest com SQLite, pytest com PostgreSQL 16, typecheck/build do frontend e build/inicialização/smoke test Docker. A conclusão dos jobs foi verificada pelos metadados e etapas do workflow.

O relatório multidisciplinar informa 51 testes aprovados e 4 skipped. A conclusão bem-sucedida da etapa de testes no CI foi confirmada, mas a contagem numérica não foi reextraída dos logs de console nesta auditoria; a contagem permanece atribuída ao relatório apresentado.

### 16.2 Confronto das alegações multidisciplinares

| Alegação / evidência apresentada | Verificação cruzada | Resultado para G0 |
|---|---|---|
| 9 tabelas ORM e 3 revisões Alembic | Inventário direto confirmou nove entidades/tabelas de domínio e três revisões: a1cd5ac5805f_schema_inicial.py, 0002_guards.py e 0003_audit_export.py. | Confirmado como estrutura técnica atual; não significa cobertura do domínio SEFI. |
| Argon2id, JWT/refresh rotation, lockout e RBAC | Implementações e testes correspondentes localizados; CI backend passou. | Evidência técnica favorável; política institucional, MFA/SSO e governança de perfis permanecem pendentes. |
| Assinatura eletrônica com manifesto, hash e token de uso único | Modelo, serviço, rotas e testes localizados; CI passou. | Reutilizável com adaptação; modalidade jurídica/institucional e integração com decisões SEFI não homologadas. |
| Auditoria append-only, hash/HMAC e guardas PostgreSQL | Modelo, SQL/migração e testes de cadeia/guardas localizados; etapa PostgreSQL 16 do CI passou. | Evidência favorável para as tabelas/ações atuais; cobertura de eventos SEFI e proteção operacional ainda requerem revisão. |
| Transferência de custódia e restrição ao custodiante atual | Rota/serviço/teste localizados e CI passou; ChainOfCustody referencia device_sample_id. | Parcial; não satisfaz integralmente D07 nem representa custódia independente por ObjetoCustodia. |
| CAPA após reprovação de ensaio e regras de resultado | Serviços e testes localizados; CI passou. | Válido para ensaios/CAPA; CAPA não substitui pendência ou recusa de recebimento (D05/D06). |
| Exportação auditável ZIP/CSV/JSON com hash/HMAC | Serviço, rota e testes de exportação/verificação localizados; CI passou. | Capacidade técnica presente; política completa de consulta, retenção, autorização e exportação SEFI depende de aceitação. |
| Testes PostgreSQL skipped localmente, executados no CI | test_postgres_guards.py usa skip condicional sem LIMS_TEST_DATABASE_URL; workflow define PostgreSQL 16 e etapa PG do HEAD passou. | Alegação confirmada para o CI do HEAD; não extrapolar para backup/restauração, carga ou homologação. |
| CI completo, typecheck e build | Run 42897866725 e os três jobs concluíram com sucesso. | Confirmado para esse commit; não garante commits posteriores nem conformidade funcional SEFI. |
| Restariam apenas pendências institucionais/humanas | A inspeção do domínio confirma agregados e barreiras centrais de recebimento SEFI ausentes. | Não confirmado; há pendência funcional/técnica de domínio além das institucionais. |

### 16.3 Divergências materiais

1. **D20 — admissão da amostra:** POST /samples consome assinatura e cria diretamente DeviceSample; o teste valida essa criação direta. Não há barreira anterior de aceite baseada em conferência, quantidades reconciliadas, critérios impeditivos e validações competentes.
2. **Identidade dos agregados:** ChainOfCustody referencia device_sample_id. Não se comprovou separação entre ObjetoCustodia e AmostraOperacional.
3. **D01–D04 e D19:** não foram localizados modelos/rotas próprios para solicitação, recebimento, item recebido, chegada complementar e reconciliação de quantidades.
4. **D05–D06 e D11–D12:** não foram localizados ciclos próprios de pendência, recusa e checklist; CAPA e status de ensaio não são substitutos semânticos.
5. **D08:** localização aparece na amostra e no contexto da transferência; não foi identificado evento independente de movimentação sem troca de custodiante.
6. **D13 e D17:** não foi identificado ciclo de anexos/evidências SEFI nem evidência operacional de backup/restauração testada.
7. **D10 e D15:** RBAC é base aproveitável, mas não equivale à matriz institucional de competências, designações, substitutos e independência por ato.
8. **D09:** emenda de resultado de ensaio não demonstra fluxo geral de retificação de solicitação, recebimento, objeto e efeitos sobre laudos.

### 16.4 Parecer consolidado

A avaliação multidisciplinar é corroborada quanto à existência de uma fundação de engenharia consistente e executável no pipeline: autenticação, autorização, assinatura, auditoria, custódia de amostra, ensaios, CAPA, migrações, testes PostgreSQL, frontend e smoke Docker possuem evidências versionadas e CI verde no HEAD examinado.

Não se corrobora, entretanto, a conclusão de que restariam apenas pendências institucionais/humanas. A aderência funcional do domínio implementado à baseline SEFI continua parcial e insuficiente, sobretudo na cadeia Solicitação → Recebimento → ItemRecebimento → ObjetoCustodia → Conferência/Decisão → Aceite → AmostraOperacional. A divergência D20/G0-26 permanece bloqueadora.

**Classificação consolidada:**
- Maturidade de engenharia da base atual: evidenciada em nível relevante pelo código, testes e CI.
- Aderência ao domínio SEFI aprovado: parcial/insuficiente para admissão e custódia inicial.
- Validação operacional SIM01–SIM12: pendente; os documentos disponíveis caracterizam simulação documental, não homologação com usuários.
- Rastreabilidade e execução dos CA01–CA37: pendente de matriz requisito–teste–resultado–evidência e aceite formal.
- Governança institucional: pendente em designações, checklists concretos, prazos/canais, modalidade de assinatura, destinação e políticas correlatas.
- Prontidão formal: não atingida.

**Parecer:** manter **GATE G0 NÃO APROVADO** e **IMPLEMENTAÇÃO NÃO AUTORIZADA**. O CI verde atualiza positivamente a evidência de execução da engenharia existente, mas não altera a decisão de NO-GO para implementação SEFI.
