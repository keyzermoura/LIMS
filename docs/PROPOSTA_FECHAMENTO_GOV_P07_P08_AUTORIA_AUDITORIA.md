# Proposta de fechamento GOV-P07 e GOV-P08 — Autoria, timestamps e auditoria

**Identificador:** PROP-LIMS-GOV-AUD-001  
**Versão:** 0.1  
**Data:** 2026-11-10  
**Branch:** `main`  
**Estado:** proposta para revisão do responsável pelo projeto; não validada; aprovação institucional e fechamento técnico pendentes; implementação bloqueada.

## 1. Objetivo e limites

Consolidar recomendações para GOV-P07 (autoria, participantes e semântica temporal) e GOV-P08 (cobertura e registro de auditoria), considerando:

- PROP-LIMS-API04-001 v0.2, cujo catálogo de sete eventos e distinção entre `occurred_at`, `recorded_at` e `recorded_by` já foram validados em revisão;
- PROP-LIMS-GOV-002 v0.4;
- REV-LIMS-GOV-001 v0.1, inspeção estática de autorização, assinatura e auditoria;
- diretrizes GOV01–GOV05 e operações API10 1–7 já validadas em revisão, sem reabri-las.

Esta proposta não altera o catálogo API04 já validado, não define cargos ou autoridades institucionais, não estabelece prazo legal de retenção e não comprova a configuração efetiva de banco/produção. É uma proposta de desenho, não autorização para implementação.

## 2. Diagnóstico consolidado

A inspeção estática encontrou:

1. `AuditLog` registra ator/usuário, papel, ação e contexto técnico, mas não representa universalmente todos os participantes materiais de cada ato.
2. `occurred_at` existe no registro de auditoria; não foi identificada uma semântica universal e explícita de `recorded_at` para todos os eventos de negócio.
3. A cadeia usa sequência, hash anterior, SHA-256, HMAC-SHA256 e advisory lock no PostgreSQL.
4. A existência de declaração/modelo de trigger de imutabilidade não comprova que a migração/trigger esteja aplicada nem que os privilégios reais do banco impeçam alteração.
5. A chave HMAC é configurável e o código rejeita segredo padrão em produção, mas KMS/Vault, segregação de acesso, rotação, backup e recuperação não foram verificados.
6. A cobertura identificada inclui eventos de autenticação, assinatura, negócio, exportação e verificação, mas não demonstrou cobertura completa de concessões, revogações, mudanças de escopo e exceções.
7. O detalhe de auditoria pode expor o payload integral a perfis ADMIN/AUDITOR; escopo, finalidade e minimização precisam de política própria.

A análise foi estática. Não houve consulta ao banco, migrações aplicadas, triggers, grants, ambiente de produção, testes, build ou CI.

## 3. GOV-P07 — autoria, participantes e timestamps

### 3.1 Princípios propostos

1. **Identidades semanticamente distintas:** não preencher automaticamente participantes diferentes com o usuário autenticado.
2. **Ator registrador:** `recorded_by` identifica quem praticou o lançamento no sistema, derivado da sessão autenticada e não livremente informado pelo cliente.
3. **Executor material:** `performed_by` identifica quem realizou a ação física/técnica, quando diferente do registrador e quando aplicável.
4. **Participantes específicos:** `received_by`, `decided_by`, `validated_by`, `signer`, `from_custodian`, `to_custodian`, `authorized_by` e `executed_by` são preservados conforme a natureza do evento.
5. **Ausência explícita:** participante desconhecido, não aplicável ou não identificado deve ser representado segundo estado semântico explícito; não preencher com o usuário da sessão para evitar nulos.
6. **Pessoas e identidades organizacionais:** não inventar usuário individual para representar equipe/unidade. A representação de custodiante organizacional permanece dependente de decisão de domínio e política institucional.

### 3.2 Semântica temporal proposta

| Campo | Semântica | Regra recomendada |
|---|---|---|
| `occurred_at` | Instante efetivo em que o fato/ato aconteceu | Preservar o instante informado/confirmado conforme procedimento; não confundir com o momento do lançamento. |
| `recorded_at` | Instante em que o sistema persistiu o registro | Gerado pelo servidor/banco sob controle do sistema; não aceitar valor arbitrário do cliente. |
| `signed_at` | Instante em que a assinatura foi concluída | Proveniente do mecanismo de assinatura e distinto dos demais instantes. |

Regras adicionais:

- Transportar timestamps em formato inequívoco com offset (por exemplo, ISO 8601); normalizar instantes para UTC no armazenamento quando essa for a política técnica, sem perder informação de offset original quando ela tiver significado documental.
- Não presumir que o fuso institucional seja o fuso do servidor, do navegador ou de Belo Horizonte; a instituição deve declarar a referência temporal oficial.
- Lançamento tardio deve preservar `occurred_at` e `recorded_at`, registrar justificativa, autor do lançamento e evidência/autoridade quando o procedimento exigir.
- Não permitir retrodatação silenciosa. Eventual lançamento tardio ou data efetiva retroativa deve seguir regra institucional, com trilha explícita e sem alterar `recorded_at`.
- Correção de fato já registrado deve produzir retificação/evento compensatório vinculado ao original; não sobrescrever o evento original.
- A API não deve aceitar `recorded_at` nem `signed_at` como timestamps de autoria livremente definidos pelo cliente.

### 3.3 Decisões propostas para GOV-P07

| ID | Recomendação a validar | Limite |
|---|---|---|
| AUD-P07-01 | Preservar separadamente registrador, executor material, recebedor físico, decisor, validador, signatário, entregante/recebedor da custódia, autoridade e executor técnico, conforme aplicabilidade. | Não define nomes/cargos institucionais nem obriga todos os campos em todos os eventos. |
| AUD-P07-02 | Derivar `recorded_by` da identidade autenticada; não aceitar que o cliente escolha o autor do registro. | Contas técnicas/integrações e contingência dependem de política própria. |
| AUD-P07-03 | Separar `occurred_at`, `recorded_at` e `signed_at`; `recorded_at` deve ser gerado sob controle do sistema. | Não fixa o fuso institucional nem a tecnologia física de sincronização de relógio. |
| AUD-P07-04 | Preservar offset recebido quando relevante e adotar representação temporal inequívoca; normalização UTC não deve apagar informação documental necessária. | Política oficial de fuso e sincronização depende da instituição/infraestrutura. |
| AUD-P07-05 | Lançamento tardio/retroativo exige justificativa, autoria, instante efetivo e instante de registro separados e autorização quando o procedimento exigir; nunca alterar silenciosamente a cronologia registrada. | Autoridades, limites temporais e hipóteses admissíveis dependem de decisão institucional/API12. |
| AUD-P07-06 | Retificação deve ser append-only, vinculada ao registro original, preservando conteúdo, autoria e timestamps anteriores. | A forma final de representação deve permanecer alinhada com API04/EST08 e modelo relacional. |

### 3.4 Compatibilidade com API04

O catálogo de sete eventos já validado em revisão permanece inalterado:

- `RECEIPT`
- `TRANSFER`
- `LOCATION_CHANGE`
- `RETURN`
- `DISPOSITION`
- `CLOSURE`
- `CORRECTION`

A proposta atual complementa a semântica de autoria e tempo; não reabre a decisão sobre esses códigos. Permanecem pendentes a confirmação do custodiante inicial, procedimentos e autoridades de devolução/destinação/encerramento, compatibilidade de campos e consumidores, fuso e lançamento tardio (API12), assinatura (API05) e retificação (EST08).

## 4. GOV-P08 — cobertura e registro de auditoria

### 4.1 Princípios

1. Manter `AuditLog` como cadeia central de auditoria técnica e de segurança; não criar uma segunda cadeia paralela concorrente.
2. Distinguir evento de negócio/histórico de custódia e evento de auditoria: podem estar correlacionados, mas não são intercambiáveis.
3. Registrar eventos críticos de negócio, segurança e governança com envelope consistente e identificador de correlação.
4. Minimizar dados pessoais, segredos, credenciais e conteúdo sensível; a trilha deve provar o que ocorreu sem copiar indiscriminadamente todo o conteúdo de negócio.
5. Para mutações críticas, persistir o evento de auditoria na mesma transação da alteração de negócio, de modo que não exista alteração confirmada sem sua evidência correspondente.
6. Para tentativas negadas/falhas que precisam sobreviver ao rollback da operação, usar registro de segurança durável e independente da transação revertida, sem transformar falha de auditoria em autorização implícita.
7. Falha ao registrar auditoria obrigatória deve impedir a confirmação de operação crítica; não aceitar sucesso silencioso sem trilha exigida.
8. Integridade criptográfica não substitui autorização, segregação, proteção de infraestrutura, backup ou revisão independente.

### 4.2 Catálogo mínimo de cobertura recomendado

| Categoria | Eventos mínimos |
|---|---|
| Identidade e sessão | Login bem-sucedido/falha, bloqueio, logout, refresh relevante, alteração/reset de credenciais e mudança de estado da conta. |
| Autorização | Acesso negado por capacidade, escopo, estado ou impedimento; mudança relevante de papel/capacidade/escopo; concessão, suspensão, revogação e expiração. |
| Assinatura | Emissão, consumo, cancelamento, expiração, rejeição, falha de validação e retificação vinculada. |
| Recebimento e domínio | Formalização da chegada, conferência, inclusão/regularização de pendência, validação, aceite/recusa, retificação e encerramento. |
| Custódia | Transferência, mudança de localização, devolução, destinação e encerramento, preservando vínculo com evento de negócio correspondente. |
| Exceções | Solicitação, autorização, execução, revisão/ratificação, expiração e encerramento. |
| Administração e segurança | Alterações de parâmetros sensíveis, administração técnica, falha de integridade, rotação/alteração de referência de chave e operações privilegiadas. |
| Auditoria | Consulta detalhada, exportação, verificação de integridade, falha de verificação e alteração de política/escopo de auditoria. |

A cobertura efetiva deve ser mapeada por rota/serviço/operação, sem presumir que a existência de um evento genérico cubra automaticamente cada ato ou participante.

### 4.3 Envelope mínimo recomendado

Cada evento de auditoria deve conter, conforme aplicabilidade:

- identificador único do evento;
- categoria/tipo e versão do esquema;
- ator autenticado e identificador da sessão/cliente técnico, quando aplicável;
- participantes materiais distintos do ator;
- ação, alvo/recurso e escopo relevante;
- resultado (sucesso, negação, falha, cancelamento);
- instante efetivo e instante de registro, quando ambos existirem;
- justificativa/fundamento quando exigidos;
- request/correlation ID e referência à operação de negócio;
- metadados de integridade (sequência, hash anterior, hash, HMAC e versão/identificador da chave, conforme desenho aprovado).

Não registrar senha, token de acesso/refresh/assinatura, segredo HMAC, material criptográfico ou dados pessoais desnecessários. O snapshot integral de negócio não deve ser copiado para o log por padrão; usar referência estável e/ou resumo/hash quando suficiente, preservando o documento original no repositório de domínio apropriado.

### 4.4 Integridade e operação

Para declarar a cadeia confiável, uma futura revisão deverá comprovar, e não apenas localizar comentários no código:

- trigger e/ou controles efetivos contra UPDATE/DELETE/TRUNCATE;
- privilégios mínimos e separação entre conta da aplicação, administração de banco e auditoria;
- proteção, segregação, rotação, versionamento, backup e recuperação da chave HMAC;
- comportamento transacional do append e da verificação;
- monitoramento e alerta para falha de append, quebra de sequência, hash/HMAC inválido e indisponibilidade;
- verificação periódica independente e evidência de execução;
- backup/restauração e retenção compatíveis com a política documental;
- registro de consulta/exportação/verificação sensível, com minimização.

Não se afirma que esses controles estejam implantados. KMS/Vault, responsável pela chave, rotação, retenção e periodicidade de verificação dependem de arquitetura e autoridade institucional (relacionados a GOV-P09/GOV-P11).

### 4.5 Decisões propostas para GOV-P08

| ID | Recomendação a validar | Limite |
|---|---|---|
| AUD-P08-01 | Manter a cadeia `AuditLog` existente como mecanismo central, sem tabela/cadeia paralela de auditoria; distinguir auditoria de histórico de negócio/custódia. | Não define migração ou alteração física do modelo. |
| AUD-P08-02 | Adotar o catálogo mínimo de cobertura da seção 4.2 e mapear cada evento às operações/rotas/serviços efetivos. | A cobertura real só pode ser declarada após inspeção técnica por operação. |
| AUD-P08-03 | Adotar envelope mínimo consistente da seção 4.3, com ator, participantes, alvo, ação, resultado, timestamps e correlação conforme aplicabilidade. | Não exige campos sem significado para determinado evento. |
| AUD-P08-04 | Mutações críticas devem confirmar negócio e auditoria na mesma transação; falhas/negações que precisem ser preservadas devem ter registro durável independente do rollback. | Estratégia concreta depende de arquitetura/transações e revisão técnica. |
| AUD-P08-05 | Falha na auditoria obrigatória deve impedir a confirmação de operações críticas; não permitir sucesso silencioso sem evidência exigida. | Classificação de operações críticas e contingência devem ser formalizadas. |
| AUD-P08-06 | Minimizar dados na trilha: não registrar credenciais/segredos; preferir referência/hash ao conteúdo integral quando suficiente; restringir payload detalhado. | Perfis, escopo, retenção, mascaramento e finalidade são GOV-P11 e dependem de política institucional. |
| AUD-P08-07 | Exigir verificação técnica/operacional de imutabilidade, privilégios, chave HMAC, monitoramento, backup e verificação independente antes de declarar integridade operacional. | Não afirma que trigger, grants, KMS/Vault ou rotinas estejam implantados; integra GOV-P09. |

## 5. Relação com outras decisões

- **API04:** mantém o catálogo de eventos já validado e complementa autoria/tempo; fechamento técnico e institucional pendentes.
- **API05 / GOV-P05/P06:** assinatura permanece distinta de autoria e auditoria; `signed_at` e manifesto não substituem `recorded_at` nem o evento auditável.
- **API06/API07:** controle de concorrência e replay devem preservar auditoria sem duplicar efeitos; replay não deve gerar nova ocorrência de negócio, mas tentativas relevantes podem ser auditadas conforme política.
- **API10 / GOV-P01–P04:** concessão, executor, validador, decisor e administrador mantêm identidades e competências distintas.
- **GOV-P09:** chave HMAC, imutabilidade e controles de infraestrutura permanecem dependência específica.
- **GOV-P11:** acesso, exportação, escopo, finalidade e minimização de dados de auditoria permanecem dependência específica.
- **API12/EST08:** lançamento tardio, fuso e retificação precisam de harmonização.

## 6. Decisões para manifestação do responsável pelo projeto

Solicita-se avaliar em conjunto as recomendações AUD-P07-01 a AUD-P07-06 e AUD-P08-01 a AUD-P08-07, nos limites indicados nas tabelas das seções 3.3 e 4.5.

Uma validação em revisão do projeto não substitui aprovação institucional de política temporal, retenção, acesso, segurança, responsabilidades ou infraestrutura. Não autoriza implementação.

## 7. Critérios para fechamento de GOV-P07/GOV-P08

GOV-P07/P08 somente poderão ser considerados fechados quando:

1. recomendações AUD-P07/AUD-P08 tiverem decisão documentada;
2. política institucional de fuso, lançamento tardio, retificação e participantes estiver formalizada;
3. catálogo de eventos e autoria estiverem reconciliados com API04, API05, API10 e EST08;
4. cobertura de auditoria estiver mapeada por operação, rota e serviço;
5. atomicidade e persistência de eventos críticos estiverem tecnicamente verificadas;
6. controles de banco, chave, privilégios, backup, monitoramento e verificação independente estiverem comprovados;
7. acesso, retenção, minimização e exportação estiverem aprovados institucionalmente (GOV-P11);
8. aprovação institucional aplicável estiver registrada.

## 8. Controle de execução

**Realizado:** elaboração documental de proposta consolidada para GOV-P07/GOV-P08, baseada nos documentos existentes e na inspeção estática REV-LIMS-GOV-001.

**Não realizado:** alteração de código, modelos, banco, migrações, serviços, rotas, frontend, OpenAPI, testes, build, CI, infraestrutura, chaves, triggers ou grants. Não houve consulta a banco/runtime/produção nem validação operacional.

**Estado:** proposta para revisão; AUD-P07-01 a AUD-P07-06 e AUD-P08-01 a AUD-P08-07 não validadas. GOV-P01/P04 e SIG-P01–SIG-P06 permanecem validadas em revisão nos limites registrados. Aprovação institucional, fechamento técnico e autorização específica de implementação permanecem pendentes.

## 9. Histórico

| Versão | Data | Alteração |
|---|---|---|
| 0.1 | 2026-11-10 | Consolidação das recomendações de autoria, timestamps, cobertura, envelope e integridade da auditoria para revisão de GOV-P07/GOV-P08. |
