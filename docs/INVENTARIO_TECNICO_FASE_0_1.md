# Inventário Técnico do LIMS — Fase 0.1

**Identificador:** INV-TEC-001  
**Versão:** 1.0  
**Situação:** Inventário documental preliminar concluído — revisão técnica pendente  
**Repositório:** `keyzermoura/LIMS`  
**Branch inspecionada:** `main`  
**Commit de referência:** `5bbabac4868c0b1152f273abb91e1632a1cfe98f`  
**Data da inspeção:** 2026-11-09

---

## 1. Objetivo e limites

Registrar o inventário técnico inicial do repositório para orientar a Fase 0 do projeto LIMS. Esta atividade é uma inspeção estática dos arquivos versionados na branch e no commit de referência acima.

**Limites importantes:**
- Não houve alteração de código, banco de dados, migrações, API, frontend ou infraestrutura.
- Não foi executada a aplicação.
- Não foram executados testes automatizados, build do frontend, migrações ou testes contra PostgreSQL.
- Não houve inspeção de ambiente implantado, banco real, logs operacionais, dados reais, backups ou configuração de produção.
- Portanto, este documento não declara que os recursos descritos estejam operacionalmente validados ou conformes para uso institucional.

## 2. Método de inspeção

1. Consulta da árvore Git recursiva da branch `main`.
2. Identificação dos diretórios e arquivos versionados.
3. Leitura estática de arquivos centrais de modelos, serviços, rotas, migrações, testes, configuração, frontend e implantação.
4. Registro de evidências observáveis e de questões que exigem inspeção adicional.

A árvore consultada continha 124 arquivos e não estava truncada. O commit de referência corresponde à publicação da política documental e é a referência usada para esta inspeção.

## 3. Estrutura identificada

| Área | Conteúdo observado |
|---|---|
| Raiz | `README.md`, `.env.example`, `docker-compose.yml`, scripts e configuração Git |
| Backend | Aplicação Python/FastAPI em `backend/app` |
| Modelos | SQLAlchemy em `backend/app/models` |
| Serviços | Regras de negócio em `backend/app/services` |
| API | Rotas REST em `backend/app/api/v1/routes` |
| Schemas | Contratos Pydantic em `backend/app/schemas` |
| Banco | Configuração SQLAlchemy e SQL específico em `backend/app/db` |
| Migrações | Alembic em `backend/alembic` |
| Testes | Pytest em `backend/tests` |
| Frontend | React/TypeScript/Vite em `frontend/src` |
| CI | Workflow em `.github/workflows/ci.yml` |
| Documentação | Diagnóstico, desenho funcional, matriz de lacunas, plano diretor e política documental em `docs/` |

## 4. Stack e tecnologias identificadas

### 4.1 Backend
- Python.
- FastAPI.
- SQLAlchemy 2 com sessões assíncronas.
- Pydantic e pydantic-settings.
- PostgreSQL como banco de referência, com suporte a SQLite nos testes.
- Alembic para migrações.
- JWT para autenticação.
- Argon2 para hash de senha (conforme módulo de segurança e testes).
- QR Code assinado por HMAC.
- Hash SHA-256 e HMAC-SHA256 na trilha de auditoria.

### 4.2 Frontend
- React 18.
- TypeScript.
- Vite.
- React Router.
- TanStack Query.
- React Hook Form e Zod.
- Tailwind CSS e componentes Radix UI.

### 4.3 Infraestrutura declarada no repositório
- Docker Compose.
- PostgreSQL 16 Alpine.
- Serviços separados para banco, migração, API, frontend e seed de demonstração.
- Configuração de produção no Compose define `AUTO_CREATE_SCHEMA=false` e executa Alembic antes da API.

A presença dessas tecnologias nos arquivos não comprova que a infraestrutura esteja implantada, protegida ou operando corretamente em ambiente institucional.

## 5. Domínio e modelos existentes

Os modelos observados incluem:

| Modelo | Responsabilidade aparente | Observações |
|---|---|---|
| `DeviceSample` | Registro operacional de amostra de dispositivo médico | Possui `accession_number`, identidade do dispositivo, status, recebimento e custódia atual |
| `LabTest` | Ensaio associado a uma amostra | Guarda método, parâmetros, limites, resultado corrente, responsável e assinatura |
| `LabTestResult` | Versões históricas de resultados | Modelo descrito como imutável e protegido por trigger PostgreSQL |
| `ChainOfCustody` | Eventos de transferência de guarda | Relacionado diretamente a `DeviceSample`; append-only no PostgreSQL |
| `AuditLog` | Trilha de auditoria | Sequência, payload, hash, HMAC, ator, ação e entidade |
| `ElectronicSignature` | Manifesto de assinatura eletrônica | Guarda snapshots, intenção, motivo, hashes e dados de consumo |
| `CapaAction` | Ações CAPA | Existe modelo, rota e serviço |
| `User` | Usuários e perfis | Perfis incluem ADMIN, FISCAL, TECNICO, CUSTODIANTE e AUDITOR |
| `RefreshToken` | Sessões/renovação de autenticação | Identificado na migração inicial e nos serviços de autenticação |

### 5.1 Lacuna de domínio para a Etapa 1

Na estrutura inspecionada não foram encontrados modelos dedicados para:
- solicitação institucional;
- itens declarados dentro da solicitação;
- recebimento físico independente da amostra;
- conferência por item;
- checklist de recebimento;
- evidências anexadas ao recebimento;
- decisão individual de aceite, pendência ou recusa;
- histórico/versionamento de decisões de recebimento.

Isso é uma observação da árvore e dos modelos lidos, não prova definitiva de inexistência de qualquer implementação indireta. A busca completa por referências e dependências deve ser fechada na revisão do inventário.

## 6. Fluxos e serviços existentes

### 6.1 Amostras
O serviço `sample_service.create_sample`:
- verifica ID duplicado;
- verifica duplicidade pela combinação serial + lote + fabricante;
- gera `accession_number` no formato `LIMS-AAAA-######` via sequence;
- define recebimento, recebedor e custódia inicial usando o usuário que registra a amostra;
- cria evento inicial de custódia;
- vincula assinatura ao snapshot;
- registra auditoria e efetua commit.

A rota `POST /api/v1/samples` recebe diretamente dados de amostra e exige token de assinatura eletrônica. Não foi observada uma etapa prévia de solicitação e conferência/aceite físico.

**Ponto de atenção:** o modelo exige serial, lote e fabricante e possui restrição única sobre os três campos. Essa regra pode impedir o registro de unidades distintas com mesma combinação e não contempla adequadamente itens sem número de série. A adequação deve ser avaliada antes de qualquer migração.

### 6.2 Ensaios e resultados
O serviço de ensaios permite programar ensaio para uma amostra, atribuir testador, lançar resultado, avaliar limites, assinar resultado e registrar versões imutáveis. O código também prevê abertura automática de CAPA em caso de reprovação.

O modelo atual concentra no `LabTest` o planejamento básico, dados do ensaio, resultado corrente e assinatura. A modelagem futura deve avaliar separação entre método/catálogo, plano de ensaio, execução, dados brutos, evidências, revisão e aprovação.

### 6.3 Custódia
A custódia é relacionada diretamente a `DeviceSample`. O evento inicial é criado no mesmo fluxo de criação da amostra. Isso não representa ainda o requisito funcional definido para custódia desde a chegada física, antes da criação de uma amostra operacional.

### 6.4 Auditoria e assinatura
Foram identificados:
- trilha com sequência e encadeamento SHA-256;
- HMAC com chave de configuração;
- função de verificação da cadeia;
- assinatura em duas etapas, com reautenticação;
- token de assinatura de uso único, vinculado a entidade/ação;
- snapshot do conteúdo assinado;
- triggers PostgreSQL para proteger registros selecionados.

Esses mecanismos são controles técnicos relevantes, mas sua adequação ao uso pretendido depende de análise de ameaças, gestão de chaves, configuração operacional, segregação de funções, procedimentos, evidências e validação.

## 7. API observada

O agregador da API v1 inclui rotas para:
- autenticação e assinatura;
- amostras;
- custódia;
- ensaios;
- CAPA;
- auditoria;
- usuários.

Rotas principais observadas:
- `/api/v1/auth`
- `/api/v1/samples`
- `/api/v1/custody`
- `/api/v1/tests`
- `/api/v1/capas`
- `/api/v1/audit`
- `/api/v1/users`

Não foram identificadas rotas dedicadas a solicitações, recebimentos ou itens de recebimento na árvore consultada.

## 8. Banco de dados e migrações

Foram identificadas três revisões Alembic:
1. `a1cd5ac5805f_schema_inicial.py` — schema inicial.
2. `0002_guards.py` — sequences, triggers de imutabilidade e índices adicionais.
3. `0003_audit_export.py` — inclusão de ações de exportação no enum de auditoria.

O modelo inicial contém tabelas para usuários, amostras, ensaios, resultados, custódia, auditoria, assinaturas, CAPA e tokens de renovação, entre outras.

A migração `0002_guards` cria sequences e triggers PostgreSQL para impedir alterações em trilhas/resultados/custódia e proteger determinados campos de assinatura. A suíte de testes também instala SQL específico em schemas isolados.

**Pontos que exigem aprofundamento:**
- comparar integralmente metadata SQLAlchemy, migrações Alembic e scripts SQL;
- verificar se o caminho de inicialização automática de schema e o caminho Alembic produzem estruturas equivalentes;
- confirmar compatibilidade e reversibilidade das migrações;
- verificar a cobertura dos triggers e as permissões reais do usuário de banco;
- definir estratégia de migração aditiva e de preservação de dados para os novos conceitos de solicitação e recebimento.

## 9. Frontend observado

Rotas principais identificadas:
- login;
- dashboard;
- ensaios;
- CAPA;
- auditoria.

O dashboard concentra a listagem de amostras, criação direta de amostra, QR Code, timeline e ações relacionadas à custódia/status. A página de ensaios permite selecionar amostra e programar/acompanhar ensaios.

Não foi identificada tela própria de solicitação e recebimento físico conforme o desenho funcional aprovado. A Etapa 1 demandará fluxo e componentes novos, sem pressupor que a interface atual seja reaproveitável sem ajustes.

## 10. Testes e automação

A árvore contém testes para:
- fluxo HTTP de autenticação, assinatura, amostra, custódia, ensaios e CAPA;
- regras de domínio e transições;
- segurança e tokens;
- trilha de auditoria;
- proteções específicas do PostgreSQL;
- rate limiting.

A configuração de testes usa SQLite por padrão e pode usar PostgreSQL quando `LIMS_TEST_DATABASE_URL` estiver definido. Os testes PostgreSQL são explicitamente ignorados quando a variável não está configurada.

O workflow CI está presente em `.github/workflows/ci.yml`, mas sua execução e resultados não foram consultados nesta atividade.

**Não foram executados testes nesta inspeção.** A existência de arquivos de teste não comprova que estejam passando no commit atual, nem que cubram o uso pretendido institucional.

## 11. Configuração e segurança — observações iniciais

O módulo de configuração contém segredos padrão de desenvolvimento e impede seu uso em ambiente declarado como produção. O Compose define serviços de migração, API e frontend e usa variáveis de ambiente.

Pontos que precisam de validação específica:
- gestão e rotação de segredos;
- TLS e terminação HTTPS;
- configuração de CORS e exposição da API;
- política de backup, restauração e teste de recuperação;
- gestão de contas e privilégios do PostgreSQL;
- rate limiting distribuído, pois o código descreve limite por processo;
- MFA, que aparece como campo de usuário, mas precisa ter fluxo efetivo comprovado;
- armazenamento, retenção, acesso e backup de anexos/evidências;
- logs, monitoramento e resposta a incidentes;
- segregação de ambientes e dados de demonstração.

## 12. Principais achados preliminares

| ID | Achado | Impacto para o projeto | Próxima ação |
|---|---|---|---|
| INV-01 | Fluxo atual cria `DeviceSample` diretamente | Não representa solicitação → chegada → conferência → aceite | Projetar domínio da Etapa 1 |
| INV-02 | Não foram encontrados modelos/rotas de solicitação e recebimento na árvore examinada | Lacuna estrutural provável | Busca completa e desenho de dados |
| INV-03 | `DeviceSample` exige serial, lote e fabricante | Pode bloquear casos reais sem serial e unidades repetidas | Avaliar requisitos de identificação |
| INV-04 | Restrição única serial+lote+fabricante | Pode impedir múltiplas unidades legítimas | Definir identidade da unidade e regra de duplicidade |
| INV-05 | Custódia começa na criação de `DeviceSample` | Diverge da custódia desde a chegada física | Modelar custódia pré-amostra |
| INV-06 | `accession_number` é gerado como `LIMS-AAAA-######` | Precisa ser alinhado ao identificador institucional e QR | Decidir DEC sobre identificador |
| INV-07 | Um único modelo `LabTest` concentra planejamento e resultado | Pode limitar rastreabilidade de execução e dados brutos | Modelar ciclo analítico |
| INV-08 | Há testes SQLite e testes PostgreSQL condicionais | Parte das garantias depende do banco real | Definir matriz de execução CI |
| INV-09 | Existem dois caminhos aparentes de schema: criação automática e Alembic | Risco de divergência de estrutura | Comparar e definir caminho único por ambiente |
| INV-10 | Controles criptográficos estão presentes no código | Não comprovam por si sós conformidade ou validação | Avaliar operação, chaves, procedimentos e evidências |
| INV-11 | UI atual é centrada em amostras, ensaios, CAPA e auditoria | Não implementa o fluxo de recebimento aprovado | Especificar telas e transições da Etapa 1 |
| INV-12 | Execução de CI e testes não foi verificada nesta inspeção | Estado de qualidade atual permanece desconhecido | Consultar workflow e executar suíte em ambiente controlado |

## 13. Decisões que o inventário não resolve

O inventário técnico não substitui decisão funcional ou institucional. Permanecem especialmente relevantes:
- DEC-001: cardinalidade de solicitação e itens (há divergência entre documentação anterior e diagnóstico técnico antigo);
- regra de recebimento único por solicitação e tratamento de exceções;
- distinção entre item declarado, unidade física, amostra operacional, amostra de ensaio e corpo de prova;
- identidade de dispositivos sem serial e duplicidade legítima;
- função definitiva de `accession_number` e preservação do QR Code;
- regras de aceite, pendência, recusa, não apresentação e regularização;
- escopo e responsabilidades de coordenação.

Nenhuma dessas decisões deve ser inferida apenas da estrutura atual do código.

## 14. Próximas atividades da Fase 0

1. **Fechar inventário:** inspecionar integralmente modelos, schemas, serviços, rotas, configuração, CI e migrações; mapear dependências e referências cruzadas.
2. **Verificar qualidade atual:** consultar execuções recentes de CI e, em ambiente controlado, executar testes sem modificar dados operacionais.
3. **Glossário:** formalizar os conceitos do domínio e distinguir item, unidade, amostra e corpo de prova.
4. **Matriz de decisões:** registrar DEC-001 em diante, separando propostas de decisões aprovadas.
5. **Modelo de domínio:** produzir diagrama conceitual e cardinalidades antes de desenhar migrações.
6. **Estados e transições:** especificar estados da solicitação, recebimento, item e amostra, com permissões e eventos auditáveis.
7. **Estratégia de migração:** preservar dados, IDs, QR Code, referências legadas e compatibilidade.
8. **Critérios de aceite:** definir verificações técnicas e funcionais para a Fase 1.

## 15. Conclusão

O repositório contém uma base técnica organizada, com API, interface web, modelos de amostra e ensaio, custódia, assinatura eletrônica, auditoria, CAPA, migrações e testes.

A principal lacuna para o escopo institucional definido é a ausência, na estrutura examinada, de um domínio explícito de solicitação e recebimento físico com conferência e decisão individual por item antes da criação da amostra operacional. Há também regras atuais de identificação/duplicidade que precisam ser confrontadas com a realidade do SEFI e com o desenho funcional.

Este inventário é preliminar e estático. Não autoriza implementação, migração ou alteração de infraestrutura. A Fase 0 deve concluir as decisões de domínio, modelo de dados, estados, estratégia de migração e critérios de aceite antes do portão de aprovação para desenvolvimento da Fase 1.

## 16. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 1.0 | 2026-11-09 | Inventário técnico estático inicial da branch `main`, sem execução de testes ou alteração de código. |
