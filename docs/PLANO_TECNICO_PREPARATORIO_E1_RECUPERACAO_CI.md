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


---

## 9. Aprofundamento E1.1 — evidências adicionais sobre Alembic (22/11/2026)

**Status desta investigação:** leitura de código e logs concluída; causa-raiz ainda não fechada; nenhuma execução experimental ou alteração técnica realizada.

### 9.1 Evidências adicionais confirmadas

1. O workflow cria um serviço PostgreSQL 16.16 em container e o log registra que o serviço ficou saudável antes da execução do Alembic.
2. O job instala Alembic **1.20.1**. Portanto, a falha não pode ser atribuída, com a evidência disponível, à ausência da versão mínima que suporta a opção `version_num_length`.
3. O job executa `alembic upgrade head` a partir do diretório `backend`, e o workflow aponta para `backend/alembic.ini`.
4. `backend/alembic/env.py` chama `context.configure` com `version_num_length=64` tanto no caminho online quanto no offline, por meio de `_configure`.
5. A cadeia atual possui uma revisão inicial `a1cd5ac5805f_schema_inicial.py`, seguida pelas revisões 0002 até 0022. O ID inicial é curto; a revisão 0021 também é menor que 32 caracteres; a revisão 0022 é `0022_official_reports_attributes_immutable` e ultrapassa 32 caracteres.
6. O erro ocorre especificamente ao atualizar a linha de versão de 0021 para 0022:
   `UPDATE alembic_version SET version_num='0022_official_reports_attributes_immutable' WHERE alembic_version.version_num = '0021_fase8_mfa_secret_text'`.
7. O log mostra que a instalação de dependências, Ruff e mypy foram concluídos antes da falha. Os passos seguintes — `alembic check`, testes SQLite e PostgreSQL — foram skipped.

### 9.2 Reavaliação da hipótese inicial

A hipótese genérica de que o CI estaria usando uma instalação antiga do Alembic fica **afastada**: o log identifica Alembic 1.20.1.

Também não há evidência de banco persistente herdado de uma execução anterior: o workflow inicia um serviço PostgreSQL novo para o job, e o log registra a inicialização do banco. Isso reduz a probabilidade de uma tabela antiga ter sido reutilizada, mas não substitui a inspeção do catálogo PostgreSQL no momento da falha.

Há uma inconsistência objetiva a explicar: o ambiente de migração declara comprimento 64, mas a coluna efetivamente usada pelo PostgreSQL comporta somente 32 caracteres. A causa pode estar no caminho efetivo de criação/uso da tabela de versão ou em uma diferença entre o contexto configurado e a tabela que recebe o UPDATE. **Não é tecnicamente correto escolher uma dessas causas sem observar o DDL efetivo.**

### 9.3 Diagnóstico discriminante obrigatório

Em ambiente descartável, antes de qualquer correção, coletar:

- versão efetiva do Alembic no mesmo processo que executa a migração;
- configuração efetiva do contexto de migração, sem expor credenciais;
- schema, tipo e comprimento real da coluna `alembic_version.version_num` no PostgreSQL;
- localização da tabela no catálogo (`table_schema`) e `search_path` da conexão;
- momento em que `alembic_version` é criada e DDL emitido para sua criação;
- comprimento do identificador da revisão que está sendo aplicado;
- resultado da mesma inspeção imediatamente após a criação da tabela de versão e antes da migração 0022.

Consultas de diagnóstico indicativas (somente leitura):

```sql
SELECT table_schema, table_name, column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name = 'alembic_version'
  AND column_name = 'version_num';

SHOW search_path;

SELECT version_num FROM alembic_version;
```

Também registrar a sequência de revisões aplicada até 0021. A coleta precisa demonstrar se a tabela é criada com largura 32 desde o início ou se sofre alteração posterior.

### 9.4 Decisão técnica provisória

A correção ainda não deve ser escolhida. Primeiro, a reprodução precisa identificar a origem exata da largura 32. Depois, comparar no mínimo:

- garantir que a tabela de versão seja criada com largura 64 no contexto efetivamente executado;
- ampliar a coluna de forma controlada para bancos preexistentes que já tenham largura 32, sem apagar nem carimbar o histórico;
- assegurar que o processo de upgrade consiga corrigir a coluna antes de tentar gravar um identificador maior que 32.

A solução final deve cobrir banco limpo e banco existente, com PostgreSQL como banco de migração real do CI. SQLite não substitui esse teste, pois a falha observada é específica do PostgreSQL e o conjunto de revisões contém DDL PostgreSQL.

### 9.5 Estado atualizado E1.1

| Verificação | Estado |
|---|---|
| Run e commit de referência identificados | Confirmado |
| PostgreSQL do CI identificado como serviço recém-inicializado | Confirmado |
| Versão real Alembic identificada (1.20.1) | Confirmado |
| Configuração `version_num_length=64` identificada nos caminhos online/offline | Confirmado por leitura |
| ID de revisão 0022 excede 32 caracteres | Confirmado |
| DDL efetivo da tabela no instante da falha | Não coletado |
| Causa-raiz final | Em aberto |
| Correção técnica | Não iniciada |
| Testes de correção | Não executados |

**Parecer E1.1:** a falha está isolada ao comprimento efetivo da coluna de controle de versão durante a atualização para a revisão 0022. A evidência exclui explicações simplistas como “Alembic antigo” e torna obrigatória a inspeção do DDL real. A investigação está suficientemente delimitada para preparar uma reprodução controlada, mas não autoriza ainda uma alteração de migração ou de infraestrutura.


### 9.6 Revisão estática da cadeia de revisões

Foi feita leitura dos metadados de todas as 23 revisões presentes em `backend/alembic/versions/` na branch `main`:

- revisão inicial: `a1cd5ac5805f`;
- sequência numerada: `0002_guards` até `0022_official_reports_attributes_immutable`;
- cada revisão numerada referencia como `down_revision` a revisão imediatamente anterior;
- a revisão 0022 referencia `0021_fase8_mfa_secret_text`;
- não foram identificados, nos metadados de revisão inspecionados, múltiplos heads, ramificações ou revisões concorrentes.

O workflow inspecionado executa o comando a partir de `backend`, com `backend/alembic.ini`; esse arquivo define `script_location = %(here)s/alembic`. O `env.py` desse diretório contém a configuração de comprimento 64 já registrada acima.

**Limite da conclusão:** esta verificação confirma a linearidade da cadeia declarada nos metadados e a correspondência dos caminhos de configuração visíveis. Ela não demonstra qual DDL foi efetivamente emitido pelo Alembic nem o estado real da tabela no PostgreSQL. Também não equivale à execução de `alembic history`, `alembic heads` ou à reprodução do pipeline. A causa-raiz permanece aberta.

### 9.7 Próxima investigação read-only

Antes de encerrar E1.1, a análise estática deve ser complementada, quando disponível, por:

1. inspeção integral das revisões iniciais e de eventuais utilitários/bootstrap para localizar qualquer criação, alteração ou referência explícita a `alembic_version`;
2. inspeção do log bruto desde o início do job, para confirmar o comando efetivo, diretório, variáveis não sigilosas e ordem das etapas;
3. identificação do ponto em que a tabela é criada pelo contexto Alembic e do DDL gerado, por reprodução em banco descartável somente após autorização específica;
4. coleta de `information_schema.columns`, `SHOW search_path` e identificação do schema da tabela no instante imediatamente anterior à gravação da revisão 0022.

Não há evidência suficiente para atribuir a largura 32 a uma revisão específica, a um schema alternativo, a uma tabela preexistente ou a um defeito do Alembic. Essas hipóteses permanecem abertas até a coleta discriminante.



### 9.8 Inspeção das revisões iniciais, bootstrap e workflow

A inspeção integral da revisão inicial `a1cd5ac5805f_schema_inicial.py` e da revisão seguinte `0002_guards.py`, além da busca no repositório por referências explícitas a `alembic_version`, `version_num_length`, `version_table` e `Base.metadata.create_all`, não identificou comando de aplicação que crie ou altere manualmente a tabela de controle de versão do Alembic.

A revisão inicial cria as tabelas de domínio da aplicação (usuários, amostras, assinaturas, auditoria, custódia, ensaios, CAPA e resultados). Não cria `alembic_version`. A revisão 0002 também não contém referência explícita à tabela de versão. A busca textual no repositório não retornou outras ocorrências explícitas desses identificadores.

O workflow confirma a seguinte sequência relevante:
1. checkout do repositório;
2. instalação das dependências de desenvolvimento;
3. lint e mypy;
4. execução de `alembic upgrade head` com `DATABASE_URL=postgresql+asyncpg://lims:lims@localhost:5432/lims_test`;
5. somente após sucesso, execução de `alembic check` e dos testes.

O `alembic.ini` define `script_location = %(here)s/alembic`; o workflow usa `working-directory: backend`. O `env.py` inspecionado lê a URL de `DATABASE_URL`, importa `Base.metadata` e chama `context.configure` por meio de `_configure`, incluindo explicitamente `version_num_length=64`.

**Conclusão adicional:** não há evidência no código de migração inspecionado de que uma revisão do projeto crie a tabela Alembic com largura 32. Em condições normais, a tabela de versão é gerenciada pelo próprio Alembic a partir das opções efetivas do contexto. Assim, o foco discriminante passa a ser demonstrar qual valor de `version_num_length` chega ao contexto em execução e qual objeto/tabela recebe o UPDATE. A hipótese de criação manual por uma revisão do projeto perde sustentação, mas não é possível excluir bootstrap externo ou configuração/runtime divergente sem log/DDL.

**Ponto ainda não resolvido:** o workflow cria um serviço PostgreSQL novo, mas não captura no log o DDL da tabela de versão nem consulta o catálogo antes da falha. A URL aponta para o banco `lims_test`; a conexão e o `search_path` efetivos ainda precisam ser comprovados no instante da migração. Não foi realizada reprodução local nem execução SQL.

### 9.9 Diagnóstico de maior poder discriminante

Na próxima execução diagnóstica autorizada, instrumentar somente um ambiente descartável para registrar, sem segredos:

- caminho absoluto do `env.py` efetivamente carregado;
- versão do Alembic e SQLAlchemy no mesmo interpretador/processo;
- valor efetivo de `version_num_length` entregue ao `context.configure`;
- dialect, database, current_schema e search_path da conexão;
- existência, schema e DDL da tabela `alembic_version` antes do primeiro upgrade e imediatamente antes da revisão 0022;
- SQL de criação da tabela e SQL de atualização da revisão, com parâmetros sensíveis omitidos.

A instrumentação deve permitir distinguir três cenários: (a) contexto efetivo configurado com 32; (b) contexto com 64, mas atualização direcionada a outra tabela/schema com 32; (c) tabela criada antes do contexto esperado por bootstrap externo. Não se deve aplicar alteração corretiva antes de separar esses cenários.

A coleta de diagnóstico, instrumentação, reprodução ou execução de comandos contra PostgreSQL continua condicionada à autorização específica e ao ambiente descartável. Esta atualização é exclusivamente documental.
