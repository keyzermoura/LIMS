# Revisão técnica do Pacote 1 — autorização, assinatura e auditoria

**Identificador:** REV-LIMS-GOV-001  
**Versão:** 0.1  
**Data:** 2026-11-10  
**Branch de referência:** `main`  
**Natureza:** inspeção estática de código-fonte; não é teste, validação operacional ou aprovação institucional.  
**Estado:** diagnóstico preliminar; lacunas relevantes identificadas; implementação permanece bloqueada.

## 1. Objetivo e limites

Confrontar GOV01–GOV05 e as diretrizes relacionadas de API04, API05, API06, API07 e API10 com os modelos, serviços e rotas existentes no repositório.

A análise foi feita por leitura dos arquivos atuais em `main`. Não foram executados testes, build, CI, migrações ou consultas ao banco/runtime. Não houve alteração de código, banco, migrações, endpoints, frontend, OpenAPI ou infraestrutura.

A existência de código-fonte não comprova que a configuração de produção, os segredos externos, os privilégios do banco ou os mecanismos de infraestrutura estejam corretamente implantados.

## 2. Arquivos inspecionados e evidências

| Área | Arquivo | SHA do blob consultado |
|---|---|---|
| Usuários e sessões | `backend/app/models/user.py` | `1d49a4188bd453e7b51575c627784a001dcfdd86` |
| Assinatura | `backend/app/models/electronic_signature.py` | `01500f428cb2185dbf1c553c1c137b6948ad56f5` |
| Auditoria | `backend/app/models/audit_log.py` | `f0ab9437fb20077f74e05de2844299b4f6798e68` |
| Autenticação e usuários | `backend/app/services/auth_service.py` | `2102d1d7bb4dfa9399bdfb125257e29e2dd04d2e` |
| Assinatura | `backend/app/services/signature_service.py` | `150fc361d4da1496b8a6ccd89c69fa74fb8ed32f` |
| Auditoria | `backend/app/services/audit_service.py` | `0b535dd27af317420a9f824f35d2426de2f3959d` |
| RBAC | `backend/app/core/rbac.py` | `6a717fe0d1ec907b4f7873057365795e8ff219e5` |
| JWT e criptografia | `backend/app/core/security.py` | `160b26bd540956c2135af94a2e2369741bc5eff3` |
| Dependências API | `backend/app/api/deps.py` | `ce4971d76a4697439acfc954fcf9d25de29b1ef4` |
| Rotas de autenticação | `backend/app/api/v1/routes/auth.py` | `3d9c34757ff1cf376acb6dff7ad2f7a88fa9380b` |
| Rotas de usuários | `backend/app/api/v1/routes/users.py` | `ffce1ddd571f4abd0198c517071171a3aaf92ca1` |
| Rotas de auditoria | `backend/app/api/v1/routes/audit.py` | `c5585b1ac5440079198133056bdd43aa49b69a6c` |
| Rotas de amostras | `backend/app/api/v1/routes/samples.py` | `016b587e61bcf63d5cdc223bd9787453ada2702a` |
| Enums | `backend/app/models/enums.py` | `ea82e633153a96d4c1166b438b1d5c011f6002c7` |
| Canonicalização | `backend/app/core/serialization.py` | `aa92870cce7fa7e8567a1e43f2a05f24d860dd46` |
| Configuração | `backend/app/core/config.py` | `075d96e34fb2dc0c005f7eb24837707e86b8bf9d` |
| Agregador de rotas | `backend/app/api/v1/router.py` | `516de27f62763c78fbfcd31a657c259280711e82` |

## 3. Matriz de conformidade preliminar

Legenda: **Atendido** = há mecanismo explícito no código consultado; **Parcial** = há parte do mecanismo, mas faltam elementos relevantes; **Ausente** = não foi localizado no escopo inspecionado; **Não verificável** = depende de runtime, configuração, migração ou infraestrutura não inspecionados.

| Requisito | Evidência observada | Status | Risco / recomendação |
|---|---|---|---|
| Autenticação JWT e validação de sessão | `get_current_user` valida token, tipo, usuário ativo/bloqueado e `pwdv`; tokens de acesso incluem sujeito, papel e versão da senha. | Atendido no código consultado | Confirmar configuração real de assinatura/rotação de chaves, expiração e política de sessão no ambiente implantado. |
| Autorização server-side | `require_roles` aplica restrição de papel nas rotas em que é usado. | Parcial | O mecanismo é baseado em enumeração de papéis, sem autorização por escopo/recurso/estado observada. Inventariar cada rota e formalizar matriz de permissões. |
| RBAC + ABAC e menor privilégio | `ROLE_PERMISSIONS` lista permissões para a interface; dependência de backend `require_roles` verifica somente `User.role`. | Parcial | Não foi localizado enforcement genérico das permissões granulares nem atributos de escopo. Não tratar lista enviada a `/auth/me` como barreira de segurança. |
| Administração de permissões conforme GOV02/API10 | `User.role` é campo único; criação de usuário é restrita a ADMIN e assinada. Não foram localizados modelos/serviços/rotas próprios de concessão, revogação, escopo, prazo ou autoridade autorizadora. | Ausente no escopo inspecionado | Separar autorização institucional da execução técnica; criar trilha formal de concessões/revogações somente após decisão e autorização institucional. |
| Segregação e acumulação de funções GOV01/GOV03 | Papéis de usuário são mutuamente exclusivos como valor único; não há matriz de incompatibilidade ou verificação de executor versus validador observada nos componentes consultados. | Parcial | A enumeração não representa múltiplas capacidades nem impedimentos por operação. Definir modelo de capacidades e regras de independência, sem presumir que cargos reais equivalem a papéis. |
| Exceções administrativas GOV04 | Não foram localizados mecanismos próprios de autorização, prazo/escopo, ratificação e encerramento de exceções. | Ausente no escopo inspecionado | Exigir autorização identificável, motivo, escopo, validade/condição, executor técnico e auditoria. |
| Emissão de assinatura com reautenticação | `/auth/sign` exige usuário autenticado e senha; serviço valida senha, motivo mínimo, bloqueio, alvo/ação, cria manifesto e token curto. | Atendido em parte | Emissão não mostra, por si só, que o signatário está autorizado para aquele ato; vincular emissão a política de operação/competência. |
| Alvo, ação e token de uso único | Token contém usuário, entidade, identificador, ação, significado e JTI; consumo confere claims, expiração, usuário, JTI e `consumed_at` sob bloqueio de linha. | Atendido no código consultado | Avaliar lista permitida de tipos de entidade/ações e validar o alvo contra o recurso real no momento da emissão e consumo. |
| Snapshot do manifesto e conteúdo assinado | Manifesto inclui identidade/ação/significado/motivo/instante; `bind_record` grava snapshot canônico e SHA-256 do payload. | Parcial | `payload_snapshot` e `payload_hash` são opcionais no modelo; confirmar que todas as operações que exigem assinatura chamam `bind_record` e que o snapshot representa exatamente o ato aprovado. |
| Algoritmo/versão de canonicalização | Canonicalização determinística versionada (`lims-canon-v1`); SHA-256 para manifesto e payload. | Parcial | O modelo de assinatura não persiste explicitamente o identificador do algoritmo/versão de canonicalização junto a cada assinatura; documentar e tornar verificável a evolução. |
| Revogação e ciclo de vida da assinatura | Há expiração e consumo de uso único; não foi localizado campo/fluxo de revogação explícita. | Parcial | Definir cancelamento/revogação antes do consumo, retenção, assinatura órfã e tratamento de operações canceladas. |
| Atomicidade assinatura × operação | `consume` não faz commit; comentário estabelece commit junto à alteração de negócio; serviço faz flush do consumo. | Parcial | O padrão é adequado em princípio, mas requer confirmação por operação e transação real. Não executado teste de rollback/concorrência. |
| Política de assinatura GOV05/API05 | Algumas rotas exigem assinatura; outras não. Criação de amostra e criação de usuário são assinadas; listagens/consultas não. | Parcial | Não há evidência de matriz institucional completa por ato; a cobertura atual não deve ser confundida com política aprovada. |
| Auditoria append-only e hash encadeado | `AuditLog` tem sequência, payload, prev_hash, hash e HMAC; serviço usa advisory lock no PostgreSQL e verifica sequência/hash/HMAC. | Atendido no código consultado | Confirmar trigger de imutabilidade, privilégios de banco, proteção/rotação da chave e monitoramento operacional. |
| Cobertura de eventos de auditoria | Há eventos de login, falhas, refresh, logout, assinatura emitida/recusada, operações de negócio, exportação e verificação. | Parcial | Não foi localizada trilha específica de concessão/revogação de permissões, mudança de papel, escopo e exceção. Confirmar cobertura integral das rotas/serviços. |
| Identidade de autoria e participantes API04 | AuditLog registra ator/username/papel; contexto registra request, IP e user-agent. Não há campos universais separados para recorded_by, performed_by, received_by, decided_by, validated_by e autorizador. | Parcial | Preservar semântica distinta por ato e não preencher participantes diferentes com o ator autenticado automaticamente. |
| Instante efetivo versus instante de registro API04 | AuditLog possui `occurred_at`; não foi observada coluna genérica `recorded_at` no modelo consultado. | Parcial | Formalizar timestamps separados e origem do instante; não inferir que occurred_at também representa registro no sistema. |
| Consulta e exportação de auditoria | Rotas de consulta, detalhe, verificação, exportação e verificação de pacote restritas a ADMIN/AUDITOR. | Atendido em parte | Avaliar exposição do payload completo, dados pessoais, escopo por unidade e auditoria de consultas sensíveis. |
| Administração e auditoria protegidas contra abuso | Há chave HMAC externa por configuração e validação contra segredo padrão em produção. | Não verificável | O código exige segredo diferente em prod, mas não comprova KMS/Vault, rotação, controle de acesso, backup ou segregação operacional. |

## 4. Achados técnicos relevantes

### 4.1 Autorização e administração de acesso

1. `User.role` contém um único papel enum: ADMIN, FISCAL, TECNICO, CUSTODIANTE ou AUDITOR.
2. `ROLE_PERMISSIONS` declara permissões granulares, mas a dependência consultada `require_roles` compara somente o papel. A lista de permissões é exposta em `/auth/me`; não foi localizada dependência genérica que imponha cada permissão da lista.
3. Rotas consultadas de listagem de usuários e detalhe de usuário exigem usuário autenticado, mas não uma permissão administrativa específica. A criação de usuário exige ADMIN e token de assinatura.
4. `/auth/roles` é uma rota pública que enumera papéis disponíveis; não altera permissões, mas deve ser classificada como informação pública intencional.
5. Não foram localizados modelos/rotas de concessão, alteração, suspensão ou revogação de competências, escopos ou exceções.
6. Não foi localizada separação técnica persistida entre pessoa/autoridade que autoriza a concessão e administrador que executa a alteração.

**Conclusão:** o mecanismo atual fornece autenticação e RBAC básico, mas não demonstra atendimento à autorização híbrida por capacidade/escopo, à segregação de funções e à governança de concessões definida em GOV01–GOV04/API10.

### 4.2 Assinatura eletrônica

1. A assinatura é emitida em duas etapas: reautenticação por senha e token de uso único, curto e vinculado a usuário, entidade, identificador e ação.
2. O manifesto registra snapshots de usuário, papel, significado, motivo, método, data/hora, IP e request ID.
3. O consumo confere identidade, alvo, ação, expiração, JTI e uso prévio, com bloqueio da linha.
4. O serviço permite vincular snapshot do registro e hash SHA-256, e a transação de consumo é desenhada para participar da transação da operação de negócio.
5. O modelo não apresenta mecanismo explícito de revogação/cancelamento de assinatura pendente, nem campos de algoritmo/versão do hash. O payload assinado é opcional.
6. A rota de emissão recebe `entity_type`, `entity_id` e `action` informados no payload e exige autenticação, mas não aplica nessa rota uma regra de competência específica para a ação. A autorização do comando de negócio deve ser verificada separadamente.
7. A assinatura é baseada em reautenticação por senha (`PASSWORD`); isso não permite concluir, sem política institucional, qual modalidade ou nível de garantia é juridicamente/administrativamente adequado.

**Conclusão:** há uma base técnica relevante de assinatura eletrônica, mas a matriz de atos, a autorização do signatário, o ciclo de vida, a verificabilidade do snapshot e a política institucional permanecem incompletos.

### 4.3 Auditoria e integridade

1. O serviço monta payload canônico versionado, calcula SHA-256 encadeado e HMAC-SHA256, com serialização transacional via advisory lock no PostgreSQL.
2. A verificação recalcula sequência, hash, elo anterior e HMAC.
3. Há comentário/modelo que declara trigger PostgreSQL para bloquear UPDATE/DELETE/TRUNCATE, porém a migração/trigger e os privilégios efetivos do banco não foram localizados/verificados nesta inspeção.
4. A chave HMAC é configurável e o código impede o uso do segredo padrão em produção; isso não comprova que a chave esteja armazenada fora do banco nem que seu acesso/rotação estejam segregados.
5. O payload auditado identifica ator e ação, mas a estrutura não resolve todos os participantes de negócio e nem a diferença universal entre instante efetivo e instante de registro.
6. A consulta de detalhe expõe o payload canônico integral a ADMIN/AUDITOR; precisa ser confrontada com política de dados pessoais, segredo operacional e minimização.

**Conclusão:** o mecanismo de integridade é tecnicamente mais maduro que a cobertura de governança. A existência da cadeia não comprova que todos os eventos de autorização, exceção e decisão sejam registrados.

## 5. Lacunas prioritárias e recomendações documentais

| Prioridade | Lacuna | Recomendação para fechamento documental |
|---|---|---|
| Crítica | Ausência de modelo de concessão/revogação com autoridade autorizadora e executor técnico separados | Definir ciclo de vida, evidência de autorização, escopo, prazo, revogação e revisão; alinhar GOV02/API10. |
| Crítica | RBAC por papel não demonstra autorização por operação e escopo | Construir matriz de capacidades e escopos por rota/recurso/estado; distinguir permissões declaradas à interface de enforcement backend. |
| Alta | Não há evidência de regras de independência executor/validador | Definir impedimentos e acumulação de funções por operação, conforme GOV01/GOV03 e política institucional. |
| Alta | Assinatura emitida sem regra de competência específica observada na rota de emissão | Definir autorização para assinar cada ato, lista permitida de alvos/ações e verificação no momento de emissão e consumo. |
| Alta | Ciclo de vida da assinatura incompleto | Definir cancelamento/revogação, validade, retenção, algoritmo/versionamento e tratamento de assinaturas não consumidas. |
| Alta | Snapshot assinado opcional e cobertura de bind não demonstrada para todas as operações | Inventariar chamadas a `bind_record` por operação; definir conteúdo canônico obrigatório e teste de consistência em etapa futura autorizada. |
| Alta | Auditoria de permissões e exceções não demonstrada | Definir eventos obrigatórios, autoria, aprovador, executor, usuário afetado, escopo, justificativa e validade. |
| Alta | Trigger de imutabilidade e gestão real da chave HMAC não verificados | Revisar migrações, grants de banco, configuração de produção, KMS/Vault, rotação, backup e recuperação. |
| Média | Timestamps e participantes de negócio não cobrem explicitamente todos os papéis | Compatibilizar API04 com recorded_at/occurred_at e identidades distintas por evento. |
| Média | Consulta de auditoria e detalhes do payload podem expor dados além do necessário | Definir perfis, escopo, mascaramento e auditoria de consultas/exportações. |

## 6. Questões para fechamento integrado

1. A autoridade institucional será responsável por conceder competências e o administrador técnico apenas executará as concessões autorizadas? Como serão registradas as evidências de autorização?
2. A autorização será definida por capacidade + escopo organizacional/recurso/estado, mantendo papéis como agrupadores de permissões?
3. Quais operações exigem independência entre executor, validador, decisor, signatário e custodiante?
4. Quais alvos e ações podem receber assinatura? A emissão deve ser recusada quando o usuário não possuir competência para o ato?
5. Qual política regerá cancelamento/revogação de assinatura ainda não consumida, expiração e retenção?
6. Qual mecanismo institucional/tecnológico será usado para proteger, rotacionar e recuperar a chave HMAC?
7. Quais dados do payload de auditoria podem ser consultados/exportados por ADMIN e AUDITOR, e em qual escopo?

Essas questões devem ser incorporadas ao fechamento consolidado do Pacote 1; não são autorização para implementação.

## 7. Limitações da inspeção

- Inspeção estática de arquivos-fonte em `main`; não houve execução do sistema.
- Não foram consultados banco de dados, migrações efetivamente aplicadas, triggers, grants, dados persistidos, variáveis reais de ambiente, KMS/Vault, logs de produção ou configuração de implantação.
- Não foram executados testes, build, CI ou validação automatizada.
- A cobertura de assinatura e auditoria por todas as operações não foi provada; foram examinadas rotas representativas e os serviços centrais.
- O estado de produção não pode ser inferido do código-fonte.

## 8. Conclusão

O repositório contém mecanismos concretos de autenticação JWT, RBAC básico, assinatura eletrônica de duas etapas e auditoria encadeada com SHA-256/HMAC-SHA256. Entretanto, a governança requerida pelo Pacote 1 ainda não está integralmente representada no modelo e nas rotas: faltam evidências de concessão/revogação de competências, escopos de autorização, segregação por ato, exceções administrativas e matriz completa de assinatura. A auditoria criptográfica também precisa ser confrontada com migrações, privilégios e gestão real de segredos.

**Situação do Pacote 1:** não fechado.  
**Situação da implementação:** bloqueada; esta revisão não autoriza alterações de código ou infraestrutura.

## 9. Histórico

| Versão | Data | Alteração |
|---|---|---|
| 0.1 | 2026-11-10 | Primeira inspeção estática de autorização, assinatura eletrônica e auditoria; matriz de conformidade e lacunas documentadas. |
