# Proposta de fechamento GOV-P09 e GOV-P11 — Integridade operacional e acesso à auditoria

**Identificador:** PROP-LIMS-GOV-SEC-001  
**Versão:** 0.3  
**Data:** 2026-11-10  
**Branch:** `main`  
**Estado:** as 18 recomendações (AUD-P09-01 a AUD-P09-09 e AUD-P11-01 a AUD-P11-09) foram integralmente validadas em revisão pelo responsável pelo projeto em 2026-11-10; não há recomendação desse conjunto aguardando validação do responsável pelo projeto. Aprovação institucional, fechamento técnico e comprovação operacional permanecem pendentes; implementação bloqueada.

## 1. Objetivo e limites

Esta proposta dá sequência ao Pacote 1 após a validação em revisão de GOV-P07/GOV-P08. O foco é:

- **GOV-P09:** proteção operacional da cadeia de auditoria, gestão da chave HMAC, imutabilidade, privilégios, monitoramento, backup e verificação independente;
- **GOV-P11:** segregação de capacidades de consulta, visualização detalhada, exportação, verificação de integridade e administração técnica da auditoria.

A proposta considera REV-LIMS-GOV-001 v0.1, PROP-LIMS-GOV-002 v0.5 e PROP-LIMS-GOV-AUD-001 v0.2. Não declara controles implantados, não escolhe fornecedor de KMS/Vault, não define prazo legal de retenção, não atribui autoridade a cargos reais e não autoriza alterações em código, banco, infraestrutura ou configuração.

## 2. Diagnóstico técnico disponível e limites da evidência

A inspeção estática anterior identificou:

1. A cadeia AuditLog utiliza sequência, hash anterior, SHA-256, HMAC-SHA256 e advisory lock no PostgreSQL.
2. Há referência no código/modelo a controle de imutabilidade, mas isso não comprova que trigger/migração estejam aplicados no banco efetivo.
3. Não foram comprovados os privilégios reais de banco que impedem UPDATE/DELETE/TRUNCATE por contas da aplicação ou perfis administrativos.
4. A chave HMAC é configurável e há rejeição de segredo padrão em produção; não foram comprovados KMS/Vault, segregação operacional, rotação, backup, recuperação ou processo de emergência.
5. Há rotina de verificação de integridade, mas não foi comprovada execução periódica independente, monitoramento ou evidência operacional.
6. O detalhe de auditoria pode expor payload integral a perfis ADMIN/AUDITOR; a separação de permissões e o escopo efetivo de acesso precisam de revisão.
7. A inspeção foi estática. Não houve consulta ao banco, ambiente de produção, secrets manager, logs operacionais, backup, restore ou execução de verificação.

Portanto, os itens abaixo são controles a especificar e comprovar, não afirmações sobre o estado atual.

## 3. GOV-P09 — integridade operacional, imutabilidade e gestão de chaves

### 3.1 Princípios recomendados

- Manter AuditLog como cadeia central, sem criar uma cadeia paralela.
- Separar identidade da aplicação, administração do banco, administração da infraestrutura/chaves e auditoria independente.
- A aplicação deve ter apenas os privilégios necessários para inserir eventos e executar operações estritamente previstas; não deve possuir privilégio ordinário para alterar ou apagar registros históricos.
- A integridade deve depender de controles em camadas: restrições de banco, controle de privilégios, HMAC, gestão protegida de chave, monitoramento, backup e verificação independente.
- A chave HMAC não deve ser armazenada no banco de auditoria, no repositório, em logs ou em configuração acessível a usuários da aplicação.
- Rotação de chave deve preservar verificabilidade histórica por identificador/versão da chave, sem reescrever hashes anteriores.
- Falha de append ou de integridade em operação crítica deve produzir bloqueio/contingência formal, nunca sucesso silencioso.

### 3.2 Recomendações validadas em revisão

| ID | Recomendação | Limite / decisão institucional pendente |
|---|---|---|
| AUD-P09-01 | Segregar contas e privilégios da aplicação, DBA, administração de infraestrutura/chaves e auditoria; aplicar menor privilégio. | Identidades técnicas, responsáveis e modelo operacional devem ser definidos pela instituição. |
| AUD-P09-02 | Proibir alteração/exclusão ordinária da trilha por controles efetivos no banco, incluindo avaliação de UPDATE/DELETE/TRUNCATE, ownership, superuser e caminhos administrativos. | A solução física e as exceções de manutenção dependem da arquitetura e da administração institucional. |
| AUD-P09-03 | Proteger a chave HMAC em cofre/serviço de gestão de segredos, com acesso restrito, autenticação forte e segregação de funções. | Escolha entre KMS, Vault ou mecanismo equivalente, fornecedor e responsáveis não são definidos nesta proposta. |
| AUD-P09-04 | Versionar/identificar chaves e definir rotação sem invalidar a verificação histórica; registrar transições e manter material histórico protegido pelo período aprovado. | Frequência, janela de sobreposição, retenção e custódia das chaves dependem de política de segurança. |
| AUD-P09-05 | Definir backup e recuperação da trilha e do material criptográfico necessário à verificação, com testes documentados de restauração. | RPO/RTO, localidade, criptografia, retenção e responsáveis dependem da instituição. |
| AUD-P09-06 | Monitorar append, sequência, hash/HMAC, disponibilidade da verificação e falhas; gerar alerta e incidente auditável. | Ferramenta, limiares, plantão e tratamento de incidentes dependem da operação institucional. |
| AUD-P09-07 | Executar verificação periódica e independente da cadeia, preservando relatório, escopo, instante, resultado e responsável. | Periodicidade, independência e autoridade revisora devem ser formalizadas. |
| AUD-P09-08 | Definir contingência para indisponibilidade de auditoria/chave: bloquear operações críticas ou usar procedimento excepcional formal, limitado e posteriormente conciliado. | Hipóteses, autoridade, prazo e reconciliação dependem de procedimento institucional; não se presume operação offline. |
| AUD-P09-09 | Documentar e comprovar a configuração efetiva de triggers, grants, ownership, roles, backup, chave e monitoramento antes de declarar integridade operacional. | Evidência deve vir do ambiente autorizado; inspeção estática não é suficiente. |

### 3.3 Critério de integridade verificável

A cadeia somente poderá ser declarada operacionalmente protegida quando houver evidência de que:

1. a aplicação não consegue alterar ou apagar registros históricos por seus privilégios ordinários;
2. contas administrativas e de infraestrutura estão segregadas e monitoradas;
3. a chave HMAC está protegida e seu ciclo de vida é controlado;
4. rotação permite verificar registros anteriores e posteriores;
5. falhas são detectadas, alertadas e tratadas;
6. backup/restauração preservam a cadeia e a capacidade de verificação;
7. verificação independente é executada e registrada;
8. contingência está formalizada e não permite perda silenciosa de eventos.

## 4. GOV-P11 — acesso, consulta e administração da auditoria

### 4.1 Separação de capacidades

Não tratar “acesso à auditoria” como uma permissão única. Recomenda-se separar, no mínimo:

- **AUDIT_METADATA_READ:** consultar metadados e resultados resumidos de auditoria;
- **AUDIT_DETAIL_READ:** visualizar payload e detalhes potencialmente sensíveis;
- **AUDIT_EXPORT:** exportar registros ou relatórios;
- **AUDIT_INTEGRITY_VERIFY:** executar ou consultar verificações de integridade;
- **AUDIT_POLICY_ADMIN:** administrar parâmetros, escopos e políticas de auditoria;
- **AUDIT_KEY_ADMIN:** administrar referências e ciclo de vida da chave, sem acesso automático ao conteúdo de negócio;
- **AUDIT_RETENTION_ADMIN:** executar operações autorizadas de retenção/preservação, conforme política formal.

Esses identificadores são nomes conceituais para discussão; não são permissões já implementadas nem nomes finais de código.

### 4.2 Recomendações validadas em revisão

| ID | Recomendação | Limite / decisão institucional pendente |
|---|---|---|
| AUD-P11-01 | Separar consulta de metadados, visualização detalhada, exportação, verificação de integridade e administração de política. | Catálogo final de capacidades e perfis depende da matriz institucional. |
| AUD-P11-02 | Conceder acesso por capacidade + escopo + finalidade, com menor privilégio; não conceder acesso irrestrito apenas pelo papel ADMIN. | Escopos organizacionais e finalidades autorizadas devem ser definidos formalmente. |
| AUD-P11-03 | Restringir payload detalhado a usuários com necessidade funcional demonstrável; aplicar mascaramento/minimização por categoria de dado. | Categorias sensíveis, regras de mascaramento e exceções dependem de segurança/privacidade e proteção de dados. |
| AUD-P11-04 | Exigir justificativa e registrar ator, finalidade, filtros/escopo, instante, resultado e volume para consultas detalhadas e exportações relevantes. | Definir quais consultas exigem justificativa e limiares de volume conforme risco e operação. |
| AUD-P11-05 | Registrar a própria consulta, exportação, verificação e alteração de política em trilha auditável, evitando recursão infinita. | O mecanismo de auditoria de auditoria deve ter regra técnica explícita e não gerar cadeia paralela. |
| AUD-P11-06 | Separar administração de política de auditoria da administração de banco e da gestão de chaves; impedir autoelevação sem autorização independente. | Autoridades, delegações e fluxo de aprovação dependem de GOV-P02/GOV-P03 e política institucional. |
| AUD-P11-07 | Definir retenção, preservação legal, descarte autorizado e tratamento de solicitações de acesso/correção sem apagar evidência histórica indevidamente. | Prazos, base legal, autoridade e procedimento devem ser aprovados pela instituição. |
| AUD-P11-08 | Definir acesso emergencial com escopo mínimo, prazo/condição de encerramento, justificativa, alerta e revisão posterior independente. | Integrar com GOV-P10, sem criar exceção permanente ou dispensa de requisito legal. |
| AUD-P11-09 | Proteger exportações com controle de destino, formato, minimização, rastreabilidade e proteção contra divulgação não autorizada. | Canais, classificação, criptografia e responsáveis dependem da política institucional. |

### 4.3 Regra para perfis administrativos

ADMIN técnico não recebe automaticamente acesso irrestrito ao conteúdo de auditoria, não administra sozinho a própria competência funcional e não deve administrar a chave HMAC apenas por possuir privilégios administrativos da aplicação. A instituição deve separar as funções e registrar qualquer acumulação excepcional autorizada, com escopo e revisão.

## 5. Dependências e compatibilidade

- **GOV-P01/P04:** aplicar modelo capacidade + escopo + contexto e independência obrigatória quando exigida.
- **GOV-P02/P03:** autoridade de concessão, revisão, suspensão e revogação ainda depende de definição institucional.
- **GOV-P05/P06:** assinatura e competência continuam regidas pela matriz por operação; administração de chave HMAC não equivale a assinatura eletrônica.
- **GOV-P07/P08:** preservar autoria, timestamps e catálogo de auditoria já validados em revisão; esta proposta detalha controles operacionais e acesso sem reabrir essas validações.
- **GOV-P10:** contingência e acesso emergencial devem respeitar o processo formal de exceção.
- **API10:** manter segregação entre administração técnica e concessão de competências funcionais.
- **Privacidade e documentação:** retenção, minimização, acesso e descarte exigem alinhamento com políticas institucionais aplicáveis.

## 6. Decisões para manifestação do responsável pelo projeto

Em 2026-11-10, o responsável pelo projeto validou integralmente em revisão as 18 recomendações: AUD-P09-01 a AUD-P09-09 e AUD-P11-01 a AUD-P11-09, consideradas as ressalvas e os limites expressamente registrados em cada item. Não há recomendação desse conjunto aguardando validação do responsável pelo projeto. A validação confirma integralmente as diretrizes propostas para orientar o desenho, mas não escolhe fornecedores, não define políticas institucionais nem comprova controles implantados.

A validação em revisão do projeto não substitui aprovação institucional, não comprova implantação dos controles e não autoriza implementação.

## 7. Critérios para fechamento de GOV-P09/GOV-P11

GOV-P09/GOV-P11 somente poderão ser considerados fechados quando:

1. recomendações desta proposta tiverem decisão documentada;
2. responsáveis, segregação de funções e autoridade institucional estiverem formalizados;
3. controles de banco, privilégios, triggers/ownership e proteção da chave estiverem comprovados no ambiente autorizado;
4. ciclo de vida/rotação e verificabilidade histórica da chave estiverem documentados e testados sob autorização;
5. monitoramento, backup, restauração, contingência e verificação independente estiverem demonstrados;
6. catálogo de capacidades, escopos, finalidades e mascaramento estiver aprovado;
7. retenção, preservação, exportação e descarte estiverem formalizados;
8. aprovação institucional aplicável e revisão técnica estiverem registradas.

## 8. Controle de execução

**Realizado:** elaboração documental da proposta GOV-P09/GOV-P11 com base nos achados estáticos existentes e nas diretrizes GOV-P07/GOV-P08 validadas em revisão.

**Não realizado:** alteração de código, modelos, banco, migrações, serviços, rotas, frontend, OpenAPI, secrets, triggers, grants, infraestrutura, testes, build, CI ou configuração de produção. Não houve acesso a banco, cofre de segredos, backups ou ambiente operacional.

**Estado:** as 18 recomendações AUD-P09-01 a AUD-P09-09 e AUD-P11-01 a AUD-P11-09 foram integralmente validadas em revisão pelo responsável pelo projeto em 2026-11-10. GOV-P09/GOV-P11 permanecem abertas até formalização institucional, fechamento técnico e comprovação operacional; autorização específica de implementação continua pendente.

## 9. Histórico

| Versão | Data | Alteração |
|---|---|---|
| 0.1 | 2026-11-10 | Criação da proposta para revisão de integridade operacional, gestão de chaves e segregação de acesso à auditoria. |
| 0.2 | 2026-11-10 | Registro da validação em revisão de AUD-P09-01 a AUD-P09-09 e AUD-P11-01 a AUD-P11-09; políticas institucionais, comprovação operacional, fechamento técnico e autorização de implementação permanecem pendentes. |
| 0.3 | 2026-11-10 | Esclarecimento expresso de que as 18 recomendações AUD-P09/AUD-P11 foram integralmente validadas em revisão pelo responsável pelo projeto; não restam recomendações desse conjunto aguardando validação, sem prejuízo das pendências institucionais, técnicas e operacionais. |
