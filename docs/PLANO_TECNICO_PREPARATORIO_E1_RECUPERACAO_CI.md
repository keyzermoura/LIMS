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


### 9.10 Auditoria estática do bloqueador npm/lockfile (22/11/2026)

**Escopo:** leitura somente dos manifestos, lockfile, Dockerfile e workflow atualmente publicados na branch `main`. Nenhum comando npm foi executado; nenhum arquivo técnico foi alterado.

#### Evidências verificadas

| Elemento | Evidência observada | SHA do arquivo |
|---|---|---|
| `frontend/package.json` | versão `1.1.0`; declara `@playwright/test: ^1.49.0` em `devDependencies`; script `test:e2e: playwright test` | `7dfca517d4ac827d7263b856204597ed309c6748` |
| `frontend/package-lock.json` | versão raiz `0.1.0`; `lockfileVersion: 3`; não declara Playwright nas dependências raiz e não contém entradas `node_modules/*playwright*` | `dc00a2c5a06f61aea2f939562bb57e1384602c45` |
| `frontend/Dockerfile` | copia manifesto e lockfile e executa `npm ci --no-audit --no-fund` | `578fb387f8b33b95f6c3432c7c1f0c4165c2dad1` |
| `.github/workflows/ci.yml` | Node `22`; cache npm vinculado ao lockfile; executa `npm ci`, depois typecheck e build | `72d446f1c326f9f0cb076f2a7d186197013a3beb` |

A inspeção programática do JSON confirmou:
- versão do manifesto: `1.1.0`;
- versão registrada no lockfile: `0.1.0`;
- dependência `@playwright/test` declarada no manifesto, mas ausente do bloco de dependências raiz do lockfile;
- nenhuma entrada de pacote Playwright na árvore do lockfile;
- as demais dependências de desenvolvimento listadas no manifesto aparecem no bloco raiz do lockfile.

A listagem da raiz do repositório não apresenta `package.json` nem `package-lock.json` no nível raiz; os arquivos relevantes para o frontend estão em `frontend/`.

#### Parecer técnico E1.2 — causa estática

Há **duas divergências objetivas e independentes no estado dos arquivos**: (1) versão do projeto divergente entre manifesto e lockfile; (2) dependência Playwright declarada no manifesto, mas ausente do lockfile. Isso explica tecnicamente por que `npm ci`, que exige sincronismo entre manifesto e lockfile, rejeita a instalação. O log do CI já citado na seção 2.3 registra a falha em `npm ci`; a inspeção atual confirma a divergência diretamente nos arquivos.

O Dockerfile repete a mesma condição de instalação, portanto seu build web fica bloqueado pelo mesmo descompasso antes de qualquer validação do runtime. Não há, com esta evidência, base para classificar a falha Docker observada como defeito independente do Dockerfile.

A decisão sobre manter Playwright ainda precisa considerar o uso real dos testes em `frontend/e2e`, a configuração `playwright.config.ts` e a política de execução E2E. Como existe script `test:e2e` e diretório `e2e`, a recomendação preparatória é **preservar a capacidade E2E** até que uma análise de cobertura demonstre que pode ser removida; não retirar a dependência apenas para fazer `npm ci` passar.

#### Plano de correção futura, sem execução

1. confirmar versão oficial Node/npm adotada pelo projeto e pelo CI;
2. verificar se todos os testes em `frontend/e2e` e a configuração Playwright estão ativos e quais browsers/dependências de sistema serão necessários;
3. regenerar o lockfile a partir do manifesto aprovado, preservando Playwright se a capacidade E2E for mantida;
4. alinhar o campo `version` do lockfile à versão do manifesto;
5. validar em ambiente limpo: `npm ci`, presença de `@playwright/test`, typecheck, build e, em etapa própria, E2E com browsers instalados;
6. validar o mesmo fluxo pelo Dockerfile, sem cache como única condição de sucesso;
7. registrar diff, versões de Node/npm, logs e artefatos do commit candidato.

Não usar `npm install` no CI como substituto de lockfile sincronizado, nem `--force`/ `--legacy-peer-deps` para ocultar a divergência.

#### Estado E1.2

| Verificação | Estado |
|---|---|
| Manifesto e lockfile atuais lidos | Confirmado |
| Divergência de versão `1.1.0` vs `0.1.0` | Confirmado |
| Playwright declarado no manifesto e ausente do lockfile | Confirmado |
| Dockerfile reutiliza `npm ci` | Confirmado |
| Uso funcional de todos os testes E2E | Ainda não auditado |
| Execução real de `npm ci` em ambiente limpo | Não executada |
| Correção de manifesto/lockfile | Não iniciada |
| Typecheck/build/E2E após correção | Não executados |

**Parecer E1.2:** o bloqueador npm está confirmado por inspeção estática e sua causa imediata é a falta de sincronismo entre `frontend/package.json` e `frontend/package-lock.json`. O Docker web herda o mesmo bloqueio. A correção está especificada em nível preparatório, mas não executada nem aprovada. Gate G0 permanece não aprovado e as alterações técnicas continuam bloqueadas.


### 9.11 Verificação do uso efetivo de Playwright/E2E

A inspeção complementar de `frontend/playwright.config.ts` e do diretório `frontend/e2e` identificou:

- existe configuração Playwright ativa, com `testDir: ./e2e`;
- existem dois projetos de navegador configurados: Chromium e Firefox;
- existem dois casos E2E no arquivo `lims-e2e-flow.spec.ts`: exibição da tela de login com três verificações de conteúdo e navegação para a rota pública de verificação de laudo;
- o script `test:e2e` está declarado no manifesto;
- o workflow CI atual executa `npm ci`, typecheck e build, mas não contém etapa `npm run test:e2e`;
- o Dockerfile instala dependências e faz build, mas não executa testes E2E.

**Conclusão:** Playwright não é uma dependência meramente órfã: há configuração e testes versionados que o importam diretamente. Remover a dependência quebraria a capacidade de executar esses testes. Entretanto, a existência dos testes não comprova que eles são suficientes, atualizados, executáveis ou que cobrem os fluxos críticos; tampouco existe evidência de execução E2E no CI observado.

**Pendências para o plano de validação:**
1. confirmar se as rotas e textos assertados ainda correspondem ao frontend atual;
2. verificar se o backend/API e os dados necessários são inicializados para o cenário E2E;
3. definir se Chromium e Firefox são ambos requisitos de homologação ou se a matriz de navegadores deve ser reduzida/ampliada por decisão técnica;
4. definir instalação/cache dos browsers e dependências de sistema no runner;
5. decidir quando inserir execução E2E no CI, preferencialmente após ambiente de integração estar disponível e saudável;
6. ampliar os cenários para autenticação, permissões, recebimento/conferência, custódia, resultados e laudos, conforme requisitos aprovados e antes de considerar cobertura institucional.

**Estado:** existência e conteúdo dos dois testes confirmados por leitura; execução, cobertura funcional e validade das asserções não verificadas. Nenhum teste foi executado e nenhuma configuração foi alterada.


### 9.12 Reprodutibilidade Node/npm e alinhamento do E2E com o ambiente Docker

**Escopo:** inspeção estática do workflow, Dockerfile, Compose, configuração E2E, roteamento React e smoke test. Nenhum build, container, teste ou comando npm foi executado.

#### 9.12.1 Toolchain Node/npm

- O workflow usa `actions/setup-node@v4` com `node-version: "22"`; fixa a linha principal Node 22, mas não fixa patch/minor nem versão do npm.
- O Dockerfile usa `node:22-alpine`; também acompanha a linha Node 22 e a tag Alpine móvel, sem digest ou patch imutável.
- O manifesto não declara `engines` nem `packageManager`.
- Não foi localizado `.nvmrc` ou `.npmrc` na raiz ou no diretório frontend inspecionados.
- O workflow usa cache npm vinculado ao lockfile, o que ajuda desempenho, mas não substitui a fixação da toolchain nem a sincronização do lockfile.

**Parecer:** a linha principal Node é coerente entre CI e Docker (22), mas a versão exata do Node/npm não é reprodutível a partir dos arquivos atuais. Recomenda-se decidir uma versão Node 22 patchada e suportada, fixar npm por mecanismo documentado (ou registrar versão obtida e controlar atualização), e alinhar CI/Docker. Fixar imagens por digest pode ser avaliado na política de cadeia de suprimentos, sem transformar tag móvel em alegação de vulnerabilidade.

#### 9.12.2 Topologia E2E e serviço disponível

A configuração Playwright define:
- `baseURL` padrão `http://localhost:8080`;
- `webServer` local apenas quando `CI` não está definido;
- em CI, não inicia o servidor frontend nem verifica a prontidão do serviço;
- projetos Chromium e Firefox;
- não declara `ignoreHTTPSErrors`.

O job `frontend` do workflow apenas instala dependências, executa typecheck e build. Não sobe a stack Compose, não publica um servidor e não executa `npm run test:e2e`. Portanto, se a suíte fosse simplesmente adicionada ao job atual, não haveria serviço garantido em `localhost:8080`.

O job Docker sobe a stack Compose e publica o web em `8080:80` e `8443:443`, mas atualmente executa apenas `scripts/docker-smoke.sh`, não Playwright.

#### 9.12.3 Divergência HTTP/HTTPS entre Nginx, smoke test e Playwright

O Nginx do frontend:
- escuta HTTP na porta 80 e responde com redirecionamento para `https://$host$request_uri`;
- serve a aplicação em HTTPS na porta 443, com certificado autoassinado gerado durante o build;
- o Compose publica HTTPS no host pela porta 8443, não pela porta 443.

Em contraste:
- o smoke test define `WEB_URL=http://localhost:8080`, usa `curl -fsS` sem `-L` e espera receber diretamente o HTML da SPA;
- o Playwright usa por padrão `http://localhost:8080`.

**Risco técnico identificado:** a requisição HTTP do host para 8080 recebe redirecionamento do Nginx para HTTPS sem preservar o mapeamento externo 8443. O destino padrão do navegador/curl passa a ser a porta 443 do host, que não é a porta publicada pelo Compose. Além disso, acessar diretamente a porta 8443 usa certificado autoassinado e a configuração Playwright não declara confiança nesse certificado. A combinação atual é incompatível com o caminho de acesso presumido pelo smoke test e pelo Playwright. Trata-se de divergência de configuração observável; a falha efetiva em runtime ainda precisa ser reproduzida.

**Alternativas para decisão técnica futura:**
1. smoke/E2E via HTTPS: usar URL explícita com porta 8443, configurar confiança controlada no certificado de teste e validar redirecionamentos;
2. smoke/E2E via HTTP interno: testar serviço/porta apropriados sem atravessar redirecionamento público, ou definir endpoint de teste específico e isolado;
3. ajustar Nginx/Compose para que o redirecionamento preserve corretamente a porta publicada e o ambiente de teste tenha certificado confiável;
4. evitar desabilitar verificação TLS globalmente como solução permanente; qualquer exceção deve ficar restrita ao ambiente descartável de teste e ser documentada.

A escolha deve preservar a política de HTTPS do ambiente e não enfraquecer a configuração de produção para acomodar o teste.

#### 9.12.4 Rota pública E2E não corresponde ao roteador atual

O teste `frontend/e2e/lims-e2e-flow.spec.ts` navega para `/public/verify` e espera encontrar o texto “Verificação Pública”. A leitura de `frontend/src/App.tsx` mostra rotas de login e rotas internas protegidas, seguidas por rota curinga que redireciona para `/`; não há rota `/public/verify` declarada no roteador atual. A página `Login.tsx` também não implementa essa tela pública.

**Parecer:** a segunda asserção E2E estática está desalinhada com o roteamento atualmente publicado e tende a falhar ou ser redirecionada. É necessário decidir se a verificação pública é requisito funcional aprovado: se for, especificar e implementar a rota em fase autorizada; se não for, corrigir/remover o teste mediante decisão e rastreabilidade. Não criar rota nem alterar o teste nesta etapa.

O primeiro teste também deve ser revisado: as expressões de conteúdo de assinatura, trilha e rastreabilidade encontram correspondência textual na página de login; contudo, não há execução para confirmar título, visibilidade responsiva ou comportamento real do navegador.

#### 9.12.5 Estado das verificações

| Verificação | Estado |
|---|---|
| Node major 22 no CI e Docker | Confirmado por leitura |
| Versão exata Node/npm fixada | Não |
| `packageManager` / `engines` declarados | Não |
| Execução E2E no workflow | Não |
| Serviço E2E garantido no job frontend | Não |
| Nginx HTTP redireciona para HTTPS | Confirmado por leitura |
| Compose publica HTTPS em 8443 | Confirmado por leitura |
| Smoke test usa HTTP 8080 sem seguir redirecionamento | Confirmado por leitura |
| Playwright usa HTTP 8080 por padrão e não configura exceção TLS | Confirmado por leitura |
| Rota `/public/verify` declarada em `App.tsx` | Não encontrada; roteador inspecionado usa rota curinga |
| Falha de runtime reproduzida | Não |
| Correções executadas | Não |

**Parecer E1.4:** a auditoria identificou pendências além do lockfile: toolchain Node/npm parcialmente flutuante, ausência de orquestração E2E no CI, incompatibilidade aparente entre URLs HTTP e redirecionamento HTTPS/porta publicada, e teste para rota pública não declarada no roteador. Essas constatações devem ser tratadas como itens preparatórios separados, sem presumir que já houve falha em runtime. E1 continua não executado e não aprovado.


---

## 10. Matriz consolidada de correções E1 — preparação para execução controlada

**Identificador:** MAT-E1-001  
**Versão:** 0.1  
**Status:** CONSOLIDAÇÃO DOCUMENTAL — NÃO EXECUTADA / NÃO APROVADA  
**Baseline:** evidências das seções 2 e 9 deste documento; branch `main`.  
**Regra de governança:** esta matriz organiza o trabalho futuro. Não autoriza alterações em código, dependências, lockfiles, migrações, workflows, Docker, infraestrutura, banco de dados ou ambientes. Gate G0 permanece não aprovado.

### 10.1 Convenções de estado

- **Confirmado — estático/log:** divergência ou falha diretamente demonstrada por arquivo ou log.
- **Risco a reproduzir:** incompatibilidade inferida da configuração, ainda sem execução que confirme o comportamento em runtime.
- **Causa aberta:** evidência do sintoma existe, mas a origem técnica ainda não foi isolada.
- **Não executado:** correção ou teste ainda não realizado.
- **Não aprovado:** solução proposta ainda depende das autorizações técnicas/institucionais aplicáveis.

### 10.2 Matriz única de correções

| ID | Bloqueador / causa | Evidência objetiva | Arquivos / componentes afetados | Dependência / ordem | Solução proposta (futura) | Critérios de aceite verificáveis | Testes / evidências exigidos | Risco / rollback | Estado atual |
|---|---|---|---|---|---|---|---|---|---|
| E1-C01 | Comprimento efetivo de `alembic_version.version_num` incompatível com revision 0022; causa-raiz ainda aberta | Run `44974653168`, commit `7940598cde763f15ba08d0b7f011df620f69aeae`; erro PostgreSQL varchar(32) ao gravar `0022_official_reports_attributes_immutable`; `env.py` declara `version_num_length=64` | `backend/alembic/env.py`, `backend/alembic.ini`, contexto Alembic e PostgreSQL CI | Primeira atividade; precede qualquer correção Alembic | Reproduzir em banco descartável e coletar caminho do env.py, configuração efetiva, dialect, schema/search_path, DDL e SQL da criação/UPDATE; distinguir contexto 32, tabela/schema alternativo ou bootstrap externo | Causa discriminada por evidência do processo e catálogo; DDL e tabela que recebe UPDATE identificados; nenhum histórico alterado | Log instrumentado sem segredos; consulta ao catálogo antes do upgrade e antes da revisão 0022; versão Alembic/SQLAlchemy; commit reproduzível | Diagnóstico incorreto pode levar a correção no objeto errado. Não experimentar em banco persistente; preservar histórico e descartar ambiente de teste | Sintoma confirmado; causa aberta; reprodução não autorizada/não executada |
| E1-C02 | Compatibilidade de bancos existentes com coluna de versão de 32 caracteres | Mesmo erro do run; plano identifica necessidade de cobrir bancos preexistentes, além de banco vazio | Bootstrap/mecanismo de migração Alembic; PostgreSQL; eventual estratégia SQLite suportada | Depende de E1-C01 e da escolha técnica documentada | Definir mecanismo seguro para ampliar coluna existente antes de gravar revision longa; garantir também criação correta em banco vazio; não apagar nem carimbar histórico | Upgrade de banco vazio e de banco com histórico até 0021 concluem até head; histórico permanece íntegro; solução idempotente e compatível com versões suportadas | Testes PostgreSQL 16 limpo e preexistente; current/history; upgrade repetido; teste de falha/reentrada; compatibilidade SQLite somente no escopo suportado | Risco de interromper upgrade ou tornar histórico inconsistente. Exigir backup verificável e plano de reversão antes de qualquer ambiente persistente | Solução não escolhida; não executada; não aprovada |
| E1-C03 | Manifesto e lockfile divergentes, impedindo instalação determinística | `frontend/package.json` versão 1.1.0 e Playwright ^1.49.0; lockfile versão 0.1.0 sem entradas Playwright; log CI falha em `npm ci` | `frontend/package.json`, `frontend/package-lock.json` | Correção prioritária após fixar toolchain e confirmar dependências E2E | Alinhar versão raiz e árvore completa; regenerar lockfile com Node/npm aprovados; preservar Playwright, pois há configuração, script e testes versionados | `npm ci` conclui em checkout limpo; manifesto e lockfile coerentes; Playwright resolvido na versão travada; instalação não depende de cache | Log de instalação limpa; versões Node/npm; inspeção da árvore instalada; diff de manifesto/lockfile | Alterar lockfile sem toolchain definida pode gerar drift. Reverter manifesto e lockfile em conjunto | Causa estática confirmada; correção não iniciada |
| E1-C04 | Toolchain Node/npm parcialmente flutuante | CI usa Node major 22; Docker usa `node:22-alpine`; sem `packageManager`, `engines`, .nvmrc/.npmrc identificados; npm não fixado | `.github/workflows/ci.yml`, `frontend/Dockerfile`, `frontend/package.json`, documentação de desenvolvimento | Definir antes de regenerar lockfile em E1-C03 | Escolher versão Node 22 patchada e suportada; definir/registrar npm; alinhar CI, geração do lockfile e Docker; avaliar digest da imagem conforme política de cadeia de suprimentos | Mesma toolchain declarada e verificável em geração local, CI e Docker; atualizações controladas | Logs de `node --version` e `npm --version`; instalação limpa; build CI/Docker no mesmo commit | Fixação excessivamente antiga aumenta risco de obsolescência; atualização futura deve ser deliberada e testada | Risco de reprodutibilidade confirmado por leitura; decisão de versão pendente; não executado |
| E1-C05 | Suíte E2E não é executada no CI e job frontend não garante servidor | Workflow executa install/typecheck/build; não executa `npm run test:e2e`; Playwright só inicia webServer fora de CI; frontend job não sobe serviço | `.github/workflows/ci.yml`, `frontend/playwright.config.ts`, `frontend/e2e/**`, Docker Compose | Depende de E1-C03/C04 e definição de topologia/URL em E1-C06 | Definir job ou etapa E2E com serviço explícito, health/readiness e dados de teste; instalar browsers/dependências; não apenas adicionar comando sem servidor | E2E inicia contra endpoint disponível e saudável; falhas de serviço são claras; execução e relatório ficam no CI | Execução Chromium/Firefox conforme matriz aprovada; logs, traces/screenshots em falha; relatório JUnit/HTML ou equivalente | E2E pode ficar flaky ou testar ambiente errado. Isolar dados e serviço efêmero; não conectar a ambiente institucional | Lacuna CI confirmada por leitura; não executado |
| E1-C06 | Caminho HTTP/HTTPS, redirect e portas não alinhados entre Nginx, Compose, smoke e Playwright | Nginx HTTP 80 redireciona para HTTPS; Compose publica 8080:80 e 8443:443; smoke e Playwright usam HTTP 8080; smoke não segue redirect; TLS autoassinado | `frontend/nginx.conf`, `docker-compose.yml`, `scripts/docker-smoke.sh`, `frontend/playwright.config.ts`, Dockerfile/certificado de teste | Resolver antes de executar smoke/E2E em E1-C05/C08 | Escolher URL/topologia coerente: HTTPS explícito com 8443 e confiança de teste controlada, endpoint interno HTTP isolado ou ajuste de redirect/porta; manter TLS de produção | URL de teste resolve para serviço publicado; redirect termina na porta correta; certificado é validado conforme política; smoke e Playwright usam a mesma topologia | Testes de redirect, status/HTML, handshake TLS, hostname/certificado e acesso via container/host | Risco inferido, não reproduzido. Não enfraquecer TLS globalmente; exceção, se necessária, limitada ao ambiente efêmero | Divergência estática confirmada; falha runtime não reproduzida |
| E1-C07 | Teste E2E usa rota pública não declarada no roteador atual | `lims-e2e-flow.spec.ts` navega para `/public/verify`; `App.tsx` não declara rota e catch-all redireciona para `/` | `frontend/e2e/lims-e2e-flow.spec.ts`, `frontend/src/App.tsx`, eventual página pública e requisito funcional | Decisão funcional antes de alterar teste ou frontend; precede aceite E2E | Verificar se verificação pública é requisito aprovado. Se sim, especificar e implementar em fase autorizada; se não, corrigir teste com rastreabilidade. Não criar rota por inferência | Teste corresponde a requisito aprovado e rota real; comportamento de acesso público e dados expostos definidos | Teste positivo/negativo de verificação pública; autorização, minimização de dados e estados inválidos, conforme requisito aprovado | Implementar rota não aprovada pode expor dados; remover teste pode ocultar requisito. Exigir rastreabilidade e revisão de segurança | Desalinhamento estático confirmado; decisão funcional pendente; não executado |
| E1-C08 | Build Docker e smoke test bloqueados por npm e potencialmente por URL/redirect | Dockerfile executa `npm ci`; job Docker falha em `docker compose build`; smoke usa HTTP 8080 sem seguir redirect; stack não foi alcançada no run | `frontend/Dockerfile`, `docker-compose.yml`, `scripts/docker-smoke.sh`, Nginx e workflow | Depende de E1-C03/C04 e E1-C06; depois E1-C01/C02 para backend | Reexecutar build após npm corrigido; validar Compose, healthchecks, seed e smoke web/API/auditoria; separar causa de build da causa de runtime | Todas as imagens buildam; stack saudável; smoke conclui contra URL correta; logs preservados; nenhum serviço externo real usado | `docker compose config -q`, build sem cache como evidência complementar, up/health, seed efêmero, smoke API/web/auditoria | Falha parcial pode deixar containers/dados residuais; usar projeto Compose isolado e limpeza controlada | Build falhou por dependência npm confirmada; runtime não alcançado; smoke não executado |
| E1-C09 | CI não comprova execução integral dos testes e verificações | Run de referência: migrações falharam; alembic check, SQLite/PostgreSQL tests, typecheck/build e Docker smoke foram skipped; segurança passou | `.github/workflows/ci.yml` e todos os jobs/artefatos | Última etapa; depende de E1-C01 a E1-C08 | Reexecutar pipeline completo no commit candidato; ajustar dependências/ordem/condições para que falhas sejam explícitas e testes aplicáveis não sejam silenciosamente omitidos | CI verde no mesmo commit; todos os testes obrigatórios executados; skipped justificados e cobertos por evidência equivalente; revisão independente | Run URL/ID, SHA do commit, logs por job, artefatos, relatórios de testes, versões e status de cada etapa | Pipeline verde por etapas omitidas cria falsa confiança. Bloquear aceite se qualquer etapa obrigatória não executou | Falha CI confirmada; recuperação não executada |
| E1-C10 | Cobertura e validade dos cenários E2E insuficientemente demonstradas | Existem dois testes E2E: tela de login e rota pública; nenhum foi executado; fluxos críticos ainda não cobertos por evidência | `frontend/e2e/**`, critérios aprovados e documentação de testes | Após E1-C05/C07 e disponibilidade do ambiente | Revisar asserções e ampliar cobertura a partir dos requisitos aprovados: autenticação/autorização, recebimento/conferência, custódia, resultados e laudos; evitar inventar fluxo | Cada cenário mapeia requisito aprovado, pré-condição, ação, resultado esperado e evidência; execução reproduzível | Relatórios E2E e rastreabilidade requisito-caso; testes negativos e de permissões conforme escopo | Cobertura superficial pode gerar falsa homologação. Revisão independente e segregação de dados de teste | Existência de testes confirmada; validade/cobertura não comprovadas; não executado |
| E1-C11 | Escopo SQLite/PostgreSQL e paridade de migrações não explicitados | CI prevê testes SQLite e PostgreSQL após upgrade; cadeia contém DDL PostgreSQL; nenhum desses testes foi alcançado no run | Migrações, fixtures, configuração de testes e workflow | Antes do aceite E1-C09; esclarecer em paralelo ao diagnóstico Alembic | Classificar recursos suportados por dialeto; manter PostgreSQL como prova de migração real; definir o que SQLite valida sem alegar equivalência | Matriz de compatibilidade por dialeto documentada; testes executados no banco apropriado; incompatibilidades intencionais justificadas | Upgrade PostgreSQL; suíte SQLite no escopo suportado; testes de triggers/funções no PostgreSQL | Testes SQLite podem mascarar falhas PostgreSQL; não substituir banco alvo por conveniência | Lacuna de escopo identificada; decisão e execução pendentes |
| E1-C12 | Evidência de correção, revisão e reversibilidade ainda não estruturada como pacote único | Plano atual define critérios dispersos; nenhuma correção E1 foi executada; CI não está verde | Documentação E1, PR/diff futuro, logs CI, artefatos e registro de mudanças | Acompanhar todas as correções; fechar após E1-C09 | Para cada correção registrar causa, decisão, diff, testes, commit, run, revisão independente, riscos e rollback; manter vínculo com Gate e autorizações | Pacote de evidência completo por ID; rastreabilidade até bloqueador; aprovação técnica e institucional quando exigida | PRs/commits, logs, relatórios, checksums/artefatos, parecer de revisão e registro de aprovação | Evidência incompleta impede demonstrar que a correção resolveu a causa. Não declarar concluído com base em relato verbal | Estrutura proposta; não executada/não aprovada |

### 10.3 Ordem consolidada de trabalho

| Fase | IDs | Objetivo | Saída necessária para avançar |
|---|---|---|---|
| A — Diagnóstico Alembic | E1-C01 | Isolar causa do varchar(32) | Evidência discriminante do contexto e DDL efetivos |
| B — Compatibilidade de migração | E1-C02, E1-C11 | Definir e provar estratégia para bancos vazios/existentes e dialetos | Solução técnica revisada e matriz de compatibilidade |
| C — Toolchain e dependências | E1-C04, E1-C03 | Fixar Node/npm e sincronizar lockfile preservando E2E | Instalação limpa reproduzível |
| D — Ambiente E2E | E1-C06, E1-C07, E1-C05, E1-C10 | Resolver URL/servidor/rota e validar cobertura | Suíte E2E executável e rastreável |
| E — Docker e smoke | E1-C08 | Validar build e execução da stack | Build, saúde e smoke aprovados |
| F — CI integrado e evidência | E1-C09, E1-C12 | Executar pipeline integral e consolidar prova | Run verde, testes executados e revisão independente |

A ordem não implica que todos os itens sejam puramente sequenciais: E1-C04 deve preceder a regeneração do lockfile; E1-C07 requer decisão funcional antes de qualquer alteração; E1-C01 deve preceder a escolha da correção Alembic. Não se deve usar o sucesso de uma fase para declarar concluída outra.

### 10.4 Critério de encerramento E1

E1 somente poderá receber parecer **TECNICAMENTE CONCLUÍDO** quando:
1. todos os bloqueadores confirmados estiverem corrigidos e as causas abertas tiverem sido discriminadas;
2. os critérios de aceite de cada ID aplicável estiverem comprovados por execução real;
3. PostgreSQL limpo e preexistente forem cobertos, preservando o histórico de migrações;
4. npm/lockfile e toolchain forem reproduzíveis em ambiente limpo;
5. E2E, Docker e smoke forem executados na topologia aprovada;
6. CI integral estiver verde no commit identificado, sem omissão de etapas obrigatórias;
7. diffs, logs, artefatos, riscos, rollback e revisão independente estiverem registrados;
8. as autorizações institucionais e técnicas aplicáveis tiverem sido obtidas.

**E1 não é Gate G0.** Mesmo um CI tecnicamente verde não aprova automaticamente requisitos, M0.3, segurança operacional, validação institucional ou homologação. O Gate G0 permanece pendente até avaliação formal de todos os seus critérios e evidências.

### 10.5 Parecer consolidado

A matriz separa:
- **causa imediata confirmada:** manifesto/lockfile npm divergentes, com Playwright ausente do lockfile;
- **sintoma confirmado e causa-raiz aberta:** coluna PostgreSQL varchar(32) ao atualizar para revision 0022, apesar de `version_num_length=64` no arquivo inspecionado;
- **risco de configuração a reproduzir:** HTTP/HTTPS/portas/certificado entre Nginx, Compose, smoke e Playwright;
- **desalinhamento estático confirmado:** teste E2E aponta para rota pública não declarada no roteador;
- **lacunas de execução:** E2E não é executado no CI; build/runtime Docker, smoke e testes posteriores às falhas não foram alcançados.

Nenhuma correção técnica foi iniciada ou executada. Esta matriz é instrumento de planejamento e controle de mudanças, não autorização para implementação. Gate G0 continua NÃO APROVADO.


---

## 11. Protocolo de execução controlada — E1.1 e sequência das demais frentes

**Identificador:** RUN-E1-001  
**Versão:** 0.1  
**Status:** PROCEDIMENTO PREPARATÓRIO — NÃO EXECUTADO / NÃO AUTORIZADO  
**Finalidade:** transformar a matriz da Seção 10 em roteiro verificável de trabalho, começando pelo diagnóstico discriminante Alembic/PostgreSQL.

> Este protocolo não é autorização para executar comandos, acessar bancos, iniciar containers, modificar arquivos técnicos ou disparar workflows. A primeira reprodução de migração deve ocorrer exclusivamente em ambiente descartável e somente após autorização específica. Consultas SQL abaixo são modelos de coleta; não foram executadas.

### 11.1 Pré-condições obrigatórias antes de qualquer execução

A equipe técnica deverá registrar e confirmar:

1. autorização explícita para a atividade e identificação do responsável pela execução;
2. repositório, branch, commit e estado limpo do checkout;
3. ambiente descartável isolado, sem credenciais, dados ou conectividade de produção;
4. versão de PostgreSQL, Alembic, SQLAlchemy, Python e dependências;
5. URL de conexão sanitizada, sem usuário, senha, token ou host sensível;
6. estratégia para destruir/recriar o ambiente de teste sem tocar em dados persistentes;
7. diretório seguro para logs, DDL, resultados e hashes dos artefatos;
8. critérios de interrupção e pessoa autorizada a decidir sobre continuidade.

**Interromper** se a conexão não puder ser comprovadamente identificada como descartável, se houver dúvida sobre o alvo, se o log expuser segredo ou se o checkout diferir da baseline aprovada.

### 11.2 E1.1-A — reprodução observacional do contexto Alembic

Objetivo: descobrir o contexto efetivamente carregado e o objeto que recebe a atualização da revisão 0022, sem antecipar a correção.

Coletar no mesmo processo que executaria a migração:

| Dado | Evidência a registrar | Pergunta respondida |
|---|---|---|
| Diretório corrente | Caminho absoluto | O comando parte do diretório esperado? |
| Arquivo de configuração | Caminho absoluto do `alembic.ini` | Qual configuração foi carregada? |
| Script de migração | Caminho absoluto do `env.py` | O arquivo inspecionado é o efetivamente executado? |
| Revisões | Diretório e head(s) identificados | O conjunto de revisões corresponde à baseline? |
| Runtime | Python, Alembic e SQLAlchemy efetivos | A execução usa as versões esperadas? |
| Contexto | Valor de `version_num_length` entregue a `context.configure` | A opção 64 chega ao contexto efetivo? |
| Dialect | Dialect e driver | A conexão é PostgreSQL e usa o driver esperado? |
| Banco/schema | database, current_schema e search_path | A tabela está no schema esperado? |
| SQL emitido | DDL de criação e UPDATE, com parâmetros sensíveis omitidos | Qual tabela/coluna recebe a operação? |

A instrumentação deve ser temporária, revisada e limitada ao ambiente descartável. Não imprimir `DATABASE_URL`, senhas, tokens ou variáveis completas. A instrumentação não deve alterar a lógica da migração nem corrigir a largura durante a coleta.

### 11.3 E1.1-B — coleta read-only do catálogo PostgreSQL

Depois que a conexão descartável estiver identificada, coletar o catálogo antes do upgrade e, se a reprodução alcançar esse ponto, imediatamente antes da tentativa de aplicar a revisão 0022.

Consultas indicativas:

```sql
SELECT current_database(), current_schema(), current_user;
SHOW search_path;

SELECT
    table_schema,
    table_name,
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'alembic_version'
  AND column_name = 'version_num'
ORDER BY table_schema;

SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_name = 'alembic_version'
ORDER BY table_schema;

SELECT version_num FROM alembic_version;
```

A última consulta deverá ser qualificada pelo schema caso haja mais de uma tabela homônima ou search_path ambíguo. Se a tabela ainda não existir, registrar explicitamente essa condição em vez de adaptar silenciosamente a consulta.

Para preservar o valor probatório:
- salvar saída integral e timestamp;
- registrar versão do servidor PostgreSQL;
- registrar schema e conexão usados;
- associar cada coleta ao commit e ao momento da reprodução;
- não executar DDL corretivo durante a coleta;
- não substituir evidência de catálogo por inferência a partir de `env.py`.

### 11.4 E1.1-C — árvore de decisão após a coleta

| Resultado observado | Interpretação permitida | Próxima ação de análise | O que não fazer |
|---|---|---|---|
| Contexto efetivo recebe comprimento 32 | A configuração executada diverge do arquivo esperado ou foi sobrescrita | Rastrear origem do valor, caminho de execução e ordem de configuração | Não ampliar coluna antes de explicar a configuração |
| Contexto recebe 64, mas tabela atual tem varchar(32) | Tabela pode ter sido criada anteriormente, por outro contexto ou em outro schema | Identificar DDL, schema, momento e origem da tabela | Não assumir defeito do Alembic nem renomear revision |
| Há múltiplas tabelas `alembic_version` em schemas diferentes | Possível divergência de search_path/qualificação | Determinar qual tabela recebe o UPDATE e por que | Não alterar todas as tabelas sem identificar a tabela autoritativa |
| Tabela é criada com 64 e posteriormente aparece com 32 | Existe operação posterior ou objeto diferente do inicialmente observado | Localizar DDL/alteração posterior e origem | Não atribuir a revisão sem evidência de autoria |
| Tabela é criada com 32 apesar do contexto efetivo 64 | Divergência entre configuração declarada e mecanismo efetivo de criação | Preparar reprodução mínima e revisar versão/API efetiva do Alembic | Não aplicar workaround de produção |
| Evidência não discrimina os cenários | Diagnóstico inconclusivo | Melhorar instrumentação e repetir somente com autorização | Não escolher correção por tentativa e erro |

O encerramento de E1.1 exige parecer técnico que identifique o cenário sustentado por evidência, as hipóteses descartadas e as incertezas remanescentes. “Aumentar para 64” não é conclusão suficiente sem saber por que a configuração existente não produziu o efeito esperado.

### 11.5 E1.1-D — avaliação de solução, somente depois do diagnóstico

Após a árvore de decisão, elaborar uma nota de decisão técnica comparando pelo menos:

- correção da configuração efetiva de criação da tabela;
- bootstrap seguro para bancos já existentes com coluna curta;
- estratégia idempotente para banco vazio e banco que já aplicou até 0021;
- compatibilidade com PostgreSQL e limites reais de suporte SQLite;
- impacto sobre upgrades, downgrades, restauração e histórico;
- comportamento em falha parcial e reexecução.

A nota deve apresentar diff proposto, ordem de operações, compatibilidade, rollback e testes. Nenhuma alternativa será implementada antes de revisão técnica e autorização específica.

### 11.6 Sequência de trabalho das frentes E1-C03 a E1-C12

A execução futura deverá seguir esta ordem, com paralelismo apenas quando não houver dependência:

| Passo | Frente | Atividade futura | Saída que habilita o próximo passo |
|---|---|---|---|
| 1 | E1-C01 | Diagnóstico discriminante Alembic | Causa-raiz sustentada por DDL/contexto/log |
| 2 | E1-C04 | Decidir e fixar Node/npm | Versões aprovadas e alinhamento CI/Docker |
| 3 | E1-C03 | Sincronizar manifesto/lockfile mantendo Playwright | Instalação limpa comprovada |
| 4 | E1-C07 | Confirmar requisito e comportamento esperado da verificação pública | Decisão funcional rastreável |
| 5 | E1-C06 | Definir topologia HTTP/HTTPS, porta e certificado de teste | Contrato de acesso local/CI validado |
| 6 | E1-C05 | Configurar execução E2E com servidor saudável | E2E executável no ambiente isolado |
| 7 | E1-C10 | Revisar e ampliar cobertura baseada em requisitos aprovados | Matriz requisito-cenário e relatórios |
| 8 | E1-C02 / E1-C11 | Aprovar solução Alembic e matriz de dialetos | Estratégia de migração revisada |
| 9 | E1-C08 | Build Docker, saúde da stack e smoke | Evidência de build e smoke |
| 10 | E1-C09 | Executar CI integral | Run completo no commit candidato |
| 11 | E1-C12 | Consolidar diff, logs, artefatos, rollback e revisão | Pacote de evidência E1 completo |

Os passos 2–7 podem ter análise documental paralela ao diagnóstico Alembic, mas nenhuma mudança técnica deve ser introduzida fora de autorização. E1-C02 depende da causa-raiz de E1-C01. E1-C08 depende da instalação npm e da topologia de acesso. E1-C09 depende das frentes aplicáveis anteriores.

### 11.7 Pacote de evidência obrigatório por execução

Cada atividade executada deverá gerar registro com:

- ID E1-Cxx e atividade RUN-E1-001 correspondente;
- autorização e responsável;
- commit e branch;
- ambiente, versões e configuração sanitizada;
- comandos efetivamente executados;
- início/fim e resultado;
- logs integrais e artefatos;
- testes previstos versus executados, incluindo skipped e justificativas;
- divergências, incidentes e decisões;
- hash dos artefatos relevantes;
- revisão independente e parecer;
- plano de rollback e confirmação de limpeza do ambiente descartável.

Não registrar “aprovado” quando houver apenas inspeção estática. Usar os estados: **inspecionado**, **reproduzido**, **corrigido**, **testado**, **evidenciado**, **revisado** e **aprovado**, cada um com seu suporte documental.

### 11.8 Estado desta etapa

| Atividade | Estado |
|---|---|
| Protocolo de diagnóstico Alembic documentado | Concluído documentalmente |
| Ambiente descartável provisionado | Não |
| Autorização para reprodução | Não concedida |
| Instrumentação executada | Não |
| SQL de catálogo executado | Não |
| Causa-raiz Alembic encerrada | Não |
| Solução técnica aprovada | Não |
| Correções npm/E2E/Docker/CI executadas | Não |
| CI integral reexecutado | Não |

**Parecer:** o roteiro agora define quais evidências devem ser coletadas, como distinguir as hipóteses e qual saída é necessária antes de selecionar uma correção. O próximo avanço técnico não é executar um upgrade por tentativa; é obter autorização específica para reproduzir o cenário em ambiente descartável e capturar contexto/DDL. As análises documentais das demais frentes podem prosseguir sem tocar no código.

**Governança:** Gate G0 permanece NÃO APROVADO. Este protocolo não autoriza implementação, execução de comandos mutáveis, alteração de banco, instalação de dependências, Docker, E2E ou workflow.
