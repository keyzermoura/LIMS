# Plano de Fechamento Acelerado dos Bloqueadores do Gate G0

**Versão:** 1.0  
**Data:** 2026-11-22  
**Baseline examinada:** branch `main`, commit `e276c8739c4726155f4e228f9b5092cff1f0699a`  
**Natureza:** plano de auditoria e preparação de correções; não autoriza implementação.

## 1. Objetivo e regra de execução

Reduzir o retrabalho e o número de intervenções institucionais agrupando os achados por causa-raiz. A execução será feita em pacotes de trabalho, com auditoria estática, proposta de correção, critérios de aceite e evidências requeridas. A documentação pode ser consolidada; código, banco, migrações, testes, frontend, workflows, configuração e infraestrutura permanecem bloqueados até autorização expressa e aprovação do Gate G0.

## 2. Situação CI confirmada no baseline

Workflow `CI`, run [44972881963](https://github.com/keyzermoura/LIMS/actions/runs/44972881963), associado exatamente ao commit `e276c8739c4726155f4e228f9b5092cff1f0699a`:
- Backend: **failure**.
- Docker: **failure**.
- Segurança (SAST/SCA): **success**.
- Front-end: **failure**.

### 2.1 Causas-raiz objetivamente confirmadas

**CI-01 — Identificador de revisão Alembic excede o limite do banco.**  
A migração `0022_official_reports_attributes_immutable` define revision ID com 38 caracteres. O PostgreSQL cria `alembic_version.version_num` com `varchar(32)` no fluxo de CI e falha ao atualizar a revisão. O `backend/alembic/env.py` já configura `version_num_length=64`, mas a configuração do contexto não altera retroativamente a coluna criada no banco de teste. A falha ocorre durante `alembic upgrade head`; os testes PostgreSQL subsequentes não são alcançados. A proposta de correção deve avaliar a criação explícita de `alembic_version` com largura compatível antes da primeira migração, preservando compatibilidade com bancos já existentes e com o caminho SQLite. Não encurtar identificadores ou alterar migrações sem avaliar histórico e ambientes implantados.

**CI-02 — package.json e package-lock.json estão dessincronizados.**  
`frontend/package.json` declara `@playwright/test ^1.49.0`, enquanto o lockfile não contém os pacotes `@playwright/test`, `playwright` e `playwright-core` requeridos pelo manifesto. `npm ci` falha tanto no job Front-end quanto na etapa de build Docker. O lockfile também mantém versão raiz `0.1.0`, enquanto o manifesto está em `1.1.0`. A correção proposta é regenerar o lockfile a partir do manifesto e verificar a versão resolvida, scripts E2E e reprodutibilidade; não editar o lock manualmente.

### 2.2 Efeito no alcance dos testes

Como as migrações falham antes dos testes PostgreSQL, e a instalação frontend falha antes do typecheck/build, os jobs não demonstram esses resultados. O Docker falha no estágio de instalação do frontend; build das imagens e smoke test integral não são comprovados. O job de segurança passou nessa execução, sem que isso equivalha a homologação do produto.

## 3. Pacotes de trabalho por causa-raiz

| Pacote | Escopo agrupado | Saída necessária | Dependência |
|---|---|---|---|
| P1 — Reprodutibilidade CI | Alembic/PostgreSQL, lock npm, build Docker, ordem dos testes | Proposta técnica única, CI verde em execução completa, logs e artefatos | Autorização técnica |
| P2 — Admissão e custódia | Solicitação, itens apresentados/não apresentados, conferência, aceite, recusa, transferência e encerramento | Fluxo canônico, matriz de transições, invariantes e cenários negativos | Baseline D01–D20/G0-P01–P30; validação institucional quando houver ambiguidade |
| P3 — Segurança contextual | Autorização por ação, vínculo organizacional, escopo de solicitação/amostra/evidência, segregação de funções | Matriz ator × ação × recurso × contexto, testes de negação e trilha | P2 para recursos e estados canônicos |
| P4 — Integridade transacional | Idempotência, concorrência, locks, atomicidade, histórico e eventos | Matriz de comandos críticos, invariantes de banco e testes concorrentes | P2/P3 |
| P5 — Ensaios, revisão e laudos | Execução, resultados, revisão, emissão, imutabilidade, emendas e CAPA | Ciclo de vida verificável, transições e testes | P2/P4 |
| P6 — Continuidade operacional | Backup, restauração, PITR, segredos, readiness e recuperação | Evidências de backup/restore, política RPO/RTO e validação de operação | Decisões de infraestrutura |
| P7 — Qualidade e homologação | CA01–CA37, SIM01–SIM12, pacotes GOV e Gate G0 | Rastreabilidade teste–execução–log–resultado–aceite | P1–P6 e participação SEFI |

## 4. Ordem de execução acelerada

1. Fechar diagnóstico estático P1 e elaborar proposta de correção agrupada.
2. Auditar P2 e P3 em conjunto, pois estados de admissão determinam os contextos de autorização.
3. Auditar P4 sobre os comandos e transições canônicos definidos em P2.
4. Auditar P5 em conjunto com os invariantes de integridade P4.
5. Tratar P6 em paralelo, sem misturar evidência de infraestrutura com evidência funcional.
6. Atualizar matrizes centrais e só então executar a reconciliação final CA/SIM/GOV.
7. Submeter os pontos institucionais pendentes em blocos de até 5–10 decisões, sem solicitar microaprovações técnicas.

## 5. Papéis e responsabilidades

- **Auditoria/arquitetura:** inspeção, rastreabilidade, análise de causa-raiz, proposta técnica e critérios de teste.
- **Desenvolvimento/DevOps:** implementação e execução de correções após autorização.
- **Responsável institucional SEFI:** validação dos fluxos, critérios operacionais e evidências de uso.
- **Coordenação/gestão competente:** decisões de governança, designações, políticas e aceite formal.
- **Infraestrutura/TI:** parâmetros de segurança, backup, retenção, recuperação e operação.

Nenhum nome individual é presumido neste plano.

## 6. Critérios mínimos para encerrar cada pacote

- **P1:** migrações aplicam do zero em PostgreSQL e SQLite quando suportado; `alembic check` sem drift; `npm ci` reproduz dependências; typecheck/build passam; Docker build e smoke test executam; testes relevantes têm logs e resultados identificáveis.
- **P2:** estados, eventos, transições e regras de custódia não apresentam contradições com baseline; casos de exceção e rejeição cobertos; histórico preservado.
- **P3:** toda operação sensível valida ator, papel, vínculo, recurso, estado e contexto; testes positivos e negativos comprovam negação por padrão.
- **P4:** comandos críticos são atômicos e idempotentes; concorrência não duplica protocolo, amostra, transferência ou emissão; trilha não é sobrescrita.
- **P5:** execução, revisão, aprovação, emissão e emenda são separadas e auditáveis; laudo oficial e evidências preservam imutabilidade conforme regra aprovada.
- **P6:** backup é agendado, monitorado e retido; falhas não são mascaradas; restauração independente é demonstrada; RPO/RTO são aprovados.
- **P7:** cada CA tem requisito, teste, execução, resultado e evidência; cada SIM tem protocolo, participantes, registros e aceite; Gate é deliberado formalmente.

## 7. Decisões que podem exigir validação institucional

Somente serão escaladas decisões sem resposta inequívoca nos documentos aprovados, por exemplo: papéis e substituições; exigência de dupla conferência; critérios de aceite/recusa; prazos e canais; política de assinatura; regras de transferência e encerramento físico; destinação de itens recusados; RPO/RTO e retenção; critérios de homologação. A auditoria deverá apresentar opções, impactos e recomendação, evitando perguntas abertas desnecessárias.

## 8. Limites e parecer

Esta versão confirma duas causas-raiz de CI por logs e leitura estática: largura insuficiente do identificador Alembic no banco de teste e lock npm incompatível com o manifesto. Não altera qualquer arquivo técnico. A análise dos pacotes P2–P7 ainda requer auditoria por causa-raiz e evidência atualizada.

**Gate G0: NÃO APROVADO. Implementação SEFI: NÃO AUTORIZADA.**  
Este plano organiza o fechamento; não representa aceite, homologação nem autorização de mudança técnica.
