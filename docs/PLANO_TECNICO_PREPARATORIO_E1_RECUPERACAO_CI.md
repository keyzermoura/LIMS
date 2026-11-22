# Plano técnico preparatório E1 — Recuperação do CI

**Identificador:** PT-E1-001  
**Versão:** 0.1  
**Status:** PLANO PREPARATÓRIO — NÃO EXECUTADO / NÃO APROVADO  
**Escopo:** diagnóstico e critérios para recuperar o pipeline CI do LIMS  
**Baseline inspecionada:** branch `main`, commit `7940598cde763f15ba08d0b7f011df620f69aeae`  
**Execução CI analisada:** run `44974653168`, execução 439, concluída em 22/11/2026 com falha.

> Este documento não autoriza alterações em código, dependências, lockfiles, migrações, Docker, workflows ou infraestrutura. Gate G0 permanece não aprovado e a implementação continua bloqueada. As ações abaixo são plano para execução futura após as autorizações institucionais e técnicas aplicáveis.

---

## 1. Objetivo e resultado esperado

Restabelecer uma execução reproduzível do CI, de modo que:
1. as migrações sejam aplicadas integralmente em PostgreSQL limpo;
2. a verificação de paridade entre metadata e migrações seja alcançada;
3. testes SQLite e PostgreSQL sejam efetivamente executados;
4. o frontend instale dependências de forma determinística, passe typecheck e build;
5. as imagens Docker sejam construídas, a stack suba e os smoke tests sejam executados;
6. a evidência preserve commit, run, jobs, etapas, logs e resultados.

A etapa de segurança já concluiu com sucesso no run analisado, mas isso não compensa as etapas técnicas que falharam ou foram ignoradas.

## 2. Evidência atual do CI

### 2.1 Execução de referência

- Run: `44974653168`
- Commit: `7940598cde763f15ba08d0b7f011df620f69aeae`
- Workflow: `.github/workflows/ci.yml`
- Resultado global: `failure`

| Job | Resultado | Última etapa alcançada | Consequência |
|---|---|---|---|
| Backend | Falha | `alembic upgrade head` | `alembic check`, testes SQLite e PostgreSQL foram skipped |
| Frontend | Falha | `npm ci` | typecheck e build foram skipped |
| Segurança | Sucesso | SAST e SCA concluídos | Evidência positiva limitada ao escopo dos scanners |
| Docker | Falha | `docker compose build` | stack, seed e smoke test foram skipped |

### 2.2 Bloqueador B-E1-01 — Alembic/PostgreSQL

O log do job Backend mostra:

```text
asyncpg.exceptions.StringDataRightTruncationError:
value too long for type character varying(32)

UPDATE alembic_version
SET version_num='0022_official_reports_attributes_immutable'
WHERE alembic_version.version_num = '0021_fase8_mfa_secret_text'
```

Constatações:
- A revisão `0022_official_reports_attributes_immutable` possui identificador maior que 32 caracteres.
- `backend/alembic/env.py` contém `version_num_length=64` na configuração do contexto.
- Apesar dessa configuração no arquivo inspecionado, o banco de CI apresentou `alembic_version.version_num` com limite 32 e falhou ao atualizar para a revisão 0022.
- O pipeline usa PostgreSQL 16 efêmero e falha antes de `alembic check` e dos testes.

**Diagnóstico ainda necessário:** determinar em que ponto e com qual configuração efetiva a tabela `alembic_version` é criada, se há criação manual/legada em alguma revisão, se o contexto de migração executado corresponde exatamente ao `env.py` inspecionado e se há divergência entre banco recém-criado e bancos preexistentes. A presença de `version_num_length=64` no arquivo, isoladamente, não prova que a tabela efetiva tenha sido criada com esse comprimento.

**Diretriz preparatória:** não renomear nem reescrever a revisão 0022 como primeira reação. Preservar o histórico de migrações. A solução deve cobrir tanto banco vazio quanto banco existente cuja tabela de versão já tenha sido criada com largura 32.

Alternativas a avaliar em ambiente descartável:
1. garantir que a tabela de versão seja criada com largura suficiente antes da primeira gravação de revisão, identificando por que a configuração atual não produziu esse resultado;
2. para bancos preexistentes, avaliar uma ampliação explícita e segura da coluna `alembic_version.version_num`, com verificação de dialect e estratégia compatível com PostgreSQL e SQLite;
3. avaliar se a ampliação deve ocorrer em bootstrap controlado do ambiente de migração ou em migração dedicada. Não adotar migração que dependa de conseguir gravar a própria revisão longa antes de ampliar a coluna;
4. validar downgrade/upgrade e instalações existentes sem apagar, carimbar ou recriar histórico de produção.

**Não aceitável:** apagar `alembic_version`, executar `stamp head` para mascarar falha, editar retrospectivamente revisões já publicadas sem plano de compatibilidade, ou validar somente em banco novo.

### 2.3 Bloqueador B-E1-02 — npm / lockfile

O log do job Frontend registra que `npm ci` recusou instalar porque `package.json` e `package-lock.json` não estão sincronizados. Pacotes ausentes do lockfile:

- `@playwright/test@1.65.1`
- `playwright@1.65.1`
- `playwright-core@1.65.1`

A leitura dos arquivos confirma:
- `frontend/package.json` declara `@playwright/test: ^1.49.0`;
- `frontend/package-lock.json` não contém a árvore correspondente do Playwright;
- o campo `version` do manifesto é `1.1.0`, enquanto o lockfile registra `0.1.0`;
- o lockfile usa `lockfileVersion: 3`.

**Diretriz preparatória:**
1. decidir se Playwright é dependência realmente necessária ao projeto (o script `test:e2e` está declarado); se sim, manter a dependência e regenerar o lockfile com versão de Node/npm compatível com CI; se não, retirar declaração/script somente mediante análise de uso e aprovação;
2. sincronizar nome, versão, dependências e devDependencies entre manifesto e lockfile;
3. fixar e documentar a versão de Node/npm utilizada para gerar o lockfile e a versão utilizada no CI;
4. confirmar que uma instalação limpa com `npm ci` funciona sem depender de cache local;
5. não resolver com `npm install` no CI, `--force`, `--legacy-peer-deps` ou remoção indiscriminada do Playwright.

### 2.4 Bloqueador B-E1-03 — Docker como falha dependente

O Dockerfile do frontend copia `package.json` e `package-lock.json` e executa `npm ci --no-audit --no-fund`. O build da imagem web falha pelo mesmo descompasso de Playwright. Portanto, a falha Docker observada é consequência direta do bloqueador B-E1-02; não há evidência, neste run, de falha independente do Dockerfile ou do runtime.

A stack, seed e smoke test não foram executados. Após corrigir e validar a instalação npm, o build Docker deve ser reexecutado; somente então será possível identificar eventuais falhas subsequentes de runtime.

## 3. Sequência de execução proposta (quando autorizada)

| Ordem | Atividade | Dependência | Evidência obrigatória |
|---|---|---|---|
| E1.1 | Reproduzir falha Alembic em PostgreSQL limpo e inspecionar criação da tabela de versão | Ambiente descartável | DDL real de `alembic_version`, logs e revisão que a cria |
| E1.2 | Reproduzir cenário de banco preexistente com coluna de 32 caracteres | E1.1 | Teste de upgrade sem perda do histórico |
| E1.3 | Implementar solução aprovada de largura da versão | E1.1–E1.2 | Diff revisado e teste de compatibilidade |
| E1.4 | Sincronizar manifesto/lockfile e definir versão Node/npm | Decisão sobre Playwright | `npm ci` limpo e árvore instalada |
| E1.5 | Validar frontend | E1.4 | Typecheck e build concluídos |
| E1.6 | Validar Docker | E1.5 e backend migrável | Build de imagens, stack saudável e smoke test |
| E1.7 | Executar CI completo e consolidar evidências | E1.3–E1.6 | Run verde no commit candidato, todos os jobs/etapas aplicáveis executados |

## 4. Matriz mínima de testes e critérios de aceite

### 4.1 Migrações

- PostgreSQL 16 vazio: `alembic upgrade head` alcança a revisão head.
- PostgreSQL 16 com histórico preexistente até 0021 e coluna de versão 32: upgrade alcança head sem truncamento e sem perda de histórico.
- PostgreSQL 16 já atualizado: `alembic current` e `alembic history` coerentes.
- `alembic check` executado e aprovado após upgrade.
- SQLite: validar apenas as migrações/estruturas suportadas pelo projeto; não presumir que DDL PostgreSQL (triggers/funções PL/pgSQL) seja portável. Registrar explicitamente o escopo suportado.
- Se uma migração depende de recurso exclusivo do PostgreSQL, o CI deve testar essa migração no PostgreSQL e documentar a estratégia SQLite correspondente, sem mascarar incompatibilidade.

### 4.2 Frontend

- `npm ci` em diretório limpo com Node/npm fixados.
- Confirmar presença de `@playwright/test`, `playwright` e `playwright-core` se Playwright permanecer no manifesto.
- `npm run typecheck` concluído.
- `npm run build` concluído.
- Registrar versão Node, npm e resultado sem cache como única condição de sucesso.

### 4.3 Docker

- `docker compose config -q` concluído.
- `docker compose build` para todas as imagens concluído.
- `docker compose up -d` com serviços saudáveis.
- Seed executado somente no ambiente efêmero de CI.
- `scripts/docker-smoke.sh` executado e aprovado, com verificação de API, SPA e trilha conforme seu conteúdo atual.
- Logs e status dos serviços preservados como artefato/evidência.

### 4.4 Aceite E1

E1 só pode ser considerado tecnicamente concluído quando:
1. o CI do commit candidato estiver verde;
2. backend, frontend, segurança e Docker estiverem concluídos;
3. `alembic check`, testes SQLite, testes PostgreSQL, typecheck, build e smoke test não estiverem skipped;
4. eventuais etapas intencionalmente condicionais estiverem justificadas e cobertas por evidência equivalente;
5. logs, versões, commit e run estiverem registrados;
6. revisão independente confirmar que nenhuma correção apagou histórico ou reduziu cobertura.

Um único job verde ou uma execução parcial não satisfaz o aceite.

## 5. Rollback e proteção de dados

- Executar as primeiras tentativas apenas em bancos descartáveis e branches/commits de trabalho autorizados.
- Não usar dados reais nem banco institucional para experimentação.
- Antes de qualquer alteração em ambiente persistente, exigir backup verificável, plano de reversão e janela autorizada.
- Para ampliação de coluna, validar comportamento em bancos vazios e existentes; não reverter por truncamento de identificadores.
- Para lockfile, manter o manifesto e lockfile do commit anterior disponíveis para reversão conjunta.
- Para Docker, preservar imagens/artefatos identificados por commit, sem substituir imagens de produção durante o diagnóstico.

## 6. Riscos e decisões técnicas a confirmar

| ID | Questão | Risco se não resolvida |
|---|---|---|
| DEC-E1-01 | Por que `version_num_length=64` não resultou em coluna efetiva de 64? | Correção incompleta ou falha repetida em banco novo |
| DEC-E1-02 | Como ampliar com segurança a tabela de versão em bancos existentes? | Upgrade interrompido ou histórico inconsistente |
| DEC-E1-03 | Playwright é dependência efetivamente requerida? | Remoção indevida de capacidade E2E ou dependência sem uso |
| DEC-E1-04 | Qual versão Node/npm será padrão para gerar lockfile e executar CI? | Builds não reproduzíveis |
| DEC-E1-05 | Qual o escopo real de suporte das migrações SQLite versus PostgreSQL? | Falsa equivalência entre bancos e cobertura enganosa |

## 7. Limites deste plano

- Este documento não altera nem aprova requisitos institucionais D01–D20 ou G0-P01–P30.
- Não aprova M0.3 nem Gate G0.
- Não comprova que os testes de aplicação passaram: no run de referência eles foram ignorados após a falha de migração.
- Não autoriza execução de correções técnicas.
- A execução deve ocorrer em etapa posterior, com autorização explícita e controle de mudanças.

## 8. Fontes de evidência consultadas

- CI run 439: `44974653168`, commit `7940598cde763f15ba08d0b7f011df620f69aeae`.
- Workflow: `.github/workflows/ci.yml`.
- Migração: `backend/alembic/versions/0022_official_reports_attributes_immutable.py`.
- Configuração: `backend/alembic/env.py`.
- Dependências: `frontend/package.json` e `frontend/package-lock.json`.
- Build web: `frontend/Dockerfile`.

**Conclusão:** E1 está diagnosticado em nível suficiente para preparar uma correção controlada, mas ainda não está corrigido nem validado. Os dois bloqueadores primários são Alembic/PostgreSQL e sincronização npm/lockfile; o build Docker é atualmente bloqueado pelo segundo. A recuperação deve preservar o histórico de migrações e a reprodutibilidade do ambiente.
