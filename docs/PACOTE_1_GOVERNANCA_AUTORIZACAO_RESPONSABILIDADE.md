# Pacote 1 — Governança, autorização e responsabilidade

**Identificador:** PAC-LIMS-GOV-001  
**Versão:** 0.1  
**Data:** 2026-11-10  
**Branch:** main  
**Situação:** Diretrizes gerais validadas pelo responsável pelo projeto em revisão; consolidação funcional/técnica e aprovação institucional pendentes — implementação bloqueada.

## 1. Objetivo e limites

Consolidar autorização, segregação de funções, autoria, assinatura eletrônica, auditoria, administração de acessos e exceções administrativas. Este documento complementa, sem substituir, PROP-LIMS-API05-001 e PROP-LIMS-API10-001.

A concordância do responsável pelo projeto valida diretrizes de desenho. Não constitui aprovação institucional de competências, cargos, política de assinatura ou exceções, nem autorização para implementação.

Não foram autorizadas nem realizadas alterações em código, banco, migrações, endpoints, frontend, OpenAPI, testes, build, CI ou infraestrutura.

## 2. Diretrizes GOV01–GOV05 validadas em revisão

Em 2026-11-10, o responsável pelo projeto concordou com as cinco diretrizes abaixo para orientar a consolidação do Pacote 1:

| ID | Diretriz validada | Regra consolidada | Limite/pendência |
|---|---|---|---|
| GOV01 | Acumulação de funções | Uma pessoa pode acumular diferentes capacidades quando a política de segregação permitir e não houver conflito de interesse ou impedimento específico. | Instituição deve definir incompatibilidades por operação, classe de risco e procedimento. |
| GOV02 | Concessão de permissões funcionais | A concessão depende de autoridade institucional formalmente designada. Administrador técnico executa alterações autorizadas, mas não cria para si competências funcionais. | Definir autoridade, fluxo de solicitação/aprovação, delegação, revisão e revogação. |
| GOV03 | Autoaprovação | Quando uma validação independente for exigida, o executor não pode validar a própria regularização. | Definir outros impedimentos por operação, inclusive conferência, decisão, assinatura e custódia. |
| GOV04 | Exceções | Exceções exigem autorização formal, justificativa, escopo delimitado, prazo ou condição de encerramento e auditoria. | Definir autoridade, situações admissíveis, limites, fluxo emergencial e revisão posterior. |
| GOV05 | Assinatura eletrônica | Assinatura é definida por operação e natureza do ato; não é exigida indiscriminadamente. | Política institucional deve definir atos obrigatórios, modalidade, nível de garantia, signatários e evidências. |

Essas diretrizes são decisões de desenho do projeto em revisão. Não presumem autoridade institucional nem dispensam validação jurídica, administrativa, de segurança ou técnica.

## 3. Princípios de autorização

1. Negação por padrão e menor privilégio.
2. Autorização efetiva no backend em toda operação; a interface não é controle de segurança.
3. Autenticação/JWT identifica o principal/sessão, mas não concede competência por si só.
4. A identidade do ator que registra deriva do contexto autenticado; o cliente não escolhe livremente `recorded_by`.
5. Permissões são capacidades específicas e limitadas por escopo organizacional, atribuição, recurso e estado do processo.
6. Reavaliar autorização atual em operações repetidas/idempotentes antes de revelar snapshots ou dados protegidos.
7. Nenhum papel pode contornar critério técnico impeditivo ou evidência obrigatória.
8. Papéis conceituais não equivalem automaticamente a cargos, funções ou competências institucionais existentes.

Recomenda-se manter a abordagem híbrida RBAC + atributos/escopo (ABAC), sujeita à validação da arquitetura e da segurança.

## 4. Identidades e responsabilidades que não devem ser confundidas

| Campo conceitual | Significado | Origem/controle |
|---|---|---|
| `recorded_by` | Usuário autenticado que persistiu o registro | Derivado da sessão/contexto de segurança |
| `received_by` | Pessoa que recebeu fisicamente o material | Identificada conforme evidência/procedimento; não presumida pelo usuário que lançou |
| `performed_by` | Pessoa que efetivamente executou a atividade | Registrada conforme a natureza da atividade |
| `signer` | Pessoa que assinou o conteúdo/ato | Identidade comprovada pelo mecanismo de assinatura aprovado |
| `from_custodian` | Responsável que entregou a custódia | Identificação expressa no evento |
| `to_custodian` | Responsável que recebeu a custódia | Identificação expressa no evento |
| `decided_by` | Pessoa que praticou a decisão de aceite/recusa ou outra decisão formal | Usuário autorizado para a competência e escopo |
| `validated_by` | Pessoa que realizou validação independente, quando exigida | Usuário autorizado; distinto do executor quando a independência for obrigatória |
| Autorizador da permissão | Autoridade que aprovou a concessão/alteração/revogação | Autoridade institucional designada |
| Executor técnico da permissão | Administrador que efetivou a mudança no sistema | Conta administrativa técnica; não se confunde com autorizador |

Não se deve preencher automaticamente os diferentes papéis com o usuário autenticado. Uma mesma pessoa pode ocupar mais de um papel apenas quando permitido pela regra aplicável e sem impedimento.

## 5. Matriz integrada preliminar — operação × ator × assinatura × auditoria

Legenda: P = capacidade principal proposta; C = condicional ao procedimento/escopo; — = não concedida por padrão. A matriz não atribui competências a cargos reais.

| Operação | Capacidade principal | Separação/validação | Assinatura proposta | Auditoria mínima |
|---|---|---|---|---|
| Criar solicitação assistida | Registrador | Escopo de unidade/processo | Não obrigatória por padrão | Autor, instante, alterações relevantes |
| Formalizar chegada | Registrador autorizado | recorded_by distinto de received_by quando diferentes | Condicional | Autor do lançamento, recebedor físico, instante efetivo e de registro |
| Conferir materiais | Conferente | Não concede decisão de aceite/recusa | Condicional | Conferente, versão, itens, quantidades, condições e evidências |
| Registrar pendência/evidência | Servidor autorizado | Preservar histórico; não apagar achados anteriores | Em regra não; condicional se declaração formal | Autor, instante, alvo, conteúdo e vínculo com pendência |
| Regularizar pendência | Executor autorizado | Validador distinto quando exigido | Condicional | Executor, providência, evidências, instante e referência à pendência |
| Validar regularização | Validador autorizado | Independência do executor quando exigida | Condicional | Validador, decisão, fundamento e versão avaliada |
| Aceitar/recusar | Decisor autorizado | Competência própria; critérios impeditivos não podem ser dispensados | Obrigatória proposta | Decisor, instante, decisão, justificativa e evidências |
| Validar coordenação | Coordenador/validador | Somente quando exigido; não substitui decisor | Obrigatória quando exigida, conforme política | Autor, fundamento da exigência, escopo e resultado |
| Transferir custódia | Custodiante autorizado | Identificar quem entrega e quem recebe | Condicional; definir se uma ou ambas as partes | Autor do registro, entregante, recebedor, instante efetivo e locais |
| Alterar localização | Responsável autorizado | Escopo e vínculo com objeto sob custódia | Condicional | Autor, objeto, origem/destino, instante e motivo quando aplicável |
| Devolver material | Responsável autorizado | Recebedor externo e comprovação conforme procedimento | Obrigatória proposta | Autor, decisor, destinatário, entrega e evidência |
| Destinar/encerrar | Responsável autorizado | Competência e eventual testemunha conforme procedimento | Obrigatória proposta | Autor, fundamento, destino, instante e evidência |
| Retificar registro formal | Autor autorizado | Aprovação independente conforme natureza/risco | Obrigatória proposta | Autor, autorizador/validador, justificativa, original e nova versão |
| Administrar conta tecnicamente | Administrador técnico | Sem competência funcional automática | Não se aplica por padrão | Executor técnico, usuário afetado, alteração e instante |
| Conceder/revogar permissão | Autoridade institucional autoriza; administrador executa | Separação entre autorização e execução; sem autoatribuição | Conforme política institucional | Autorizador, executor, usuário, permissão, escopo, prazo, justificativa |
| Aplicar exceção | Autoridade formalmente designada | Escopo restrito, prazo/condição, revisão | Conforme natureza do ato | Autorizador, executor, fundamento, limites, início/fim e revisão |
| Consultar auditoria | Auditor/consulta autorizado | Preferencialmente somente leitura e escopo mínimo | Não | Registrar consultas sensíveis quando política exigir |

A classificação de assinatura é proposta funcional preliminar. Não define modalidade criptográfica, validade jurídica ou competência institucional.

## 6. Política de assinatura — invariantes

1. Autenticação não equivale a assinatura.
2. Registro em AuditLog não equivale a assinatura.
3. Assinatura deve estar vinculada a alvo explícito e ato real; não apontar para DeviceSample ainda inexistente.
4. Deve preservar snapshot canônico imutável, versão do conteúdo, hash e algoritmo identificados, identidade do signatário e instante.
5. O hash sem conteúdo recuperável não é suficiente para demonstrar o que foi assinado.
6. Alteração posterior não modifica o snapshot; retificação cria novo ato relacionado e preserva o original.
7. Usuário deve estar autorizado para praticar o ato além de possuir capacidade de assinar.
8. Assinatura obrigatória deve ser validada antes da confirmação do efeito de negócio; assinatura e decisão/evento devem manter consistência transacional ou fluxo assíncrono explícito, sem efeito prematuro.
9. Modalidade, nível de garantia, identidade de agentes externos, expiração, revogação, retenção e política de evidência dependem de decisão institucional.

A proposta de matriz detalhada de API05 permanece em revisão. As categorias obrigatória proposta, condicional e não obrigatória por padrão não devem ser tratadas como política institucional aprovada.

## 7. Auditoria e rastreabilidade

Para cada evento auditável, especificar conforme sua natureza:

- ator autenticado e executor real, quando distintos;
- ação, recurso/alvo e escopo;
- instante efetivo do fato (`occurred_at`) e instante de registro (`recorded_at`), conforme API04;
- versão anterior/nova e resultado;
- justificativa, evidências e referências;
- autorização concedida/avaliada e eventual exceção;
- vínculo com assinatura, sem confundir os mecanismos;
- identificador de correlação/idempotência, sem expor segredo reutilizável.

A auditoria deve preservar histórico e permitir reconstrução dos atos relevantes. Encadeamento hash/HMAC existente é uma capacidade técnica identificada, mas sua efetiva cobertura, verificação e proteção contra alteração precisam ser confirmadas nos serviços/runtime. Não presumir que a existência do modelo AuditLog comprova cobertura integral.

Eventos de administração de acesso devem registrar, no mínimo, autorizador, executor técnico, usuário afetado, permissão/capacidade, escopo, data/hora, justificativa/referência à autorização e prazo/condição, quando aplicável.

## 8. Administração de permissões e exceções

### 8.1 Concessão, alteração e revogação

- A autoridade institucional designada autoriza a competência funcional.
- O administrador técnico executa a alteração autorizada e não pode conceder competência funcional a si próprio sem autorização independente.
- Aplicar menor privilégio, escopo e duração necessários.
- Registrar concessão, alteração, suspensão e revogação; manter histórico, sem sobrescrever a decisão anterior.
- Definir revisão periódica, expiração, substituição, afastamento e revogação emergencial.

### 8.2 Exceções

Toda exceção deve conter autoridade autorizadora, usuário beneficiado, capacidade e escopo, motivo, referência normativa/procedimental quando houver, início, término ou condição de encerramento, executor técnico e evidência de auditoria. Exceção não pode dispensar critério técnico impeditivo nem transformar privilégio temporário em competência permanente.

O fluxo emergencial, a ratificação posterior e os limites de exceções dependem de política institucional.

## 9. Integração com decisões relacionadas

- **API04:** separar instante efetivo, instante de registro e identidade de quem registrou; preservar autoria dos eventos.
- **API05:** assinatura por operação e alvo explícito; matriz e modalidade continuam pendentes.
- **API06:** controle de versão e conflito não substituem autorização nem segregação.
- **API07:** replay idempotente não pode revelar resultado sem revalidar autorização atual; a assinatura deve permanecer ligada ao conteúdo original.
- **API10:** preservar integralmente as regras gerais já validadas para as Operações 1 a 7; GOV01–GOV05 complementam o enquadramento geral.
- **API12:** lançamento tardio/retroativo exige autoridade, justificativa e preservação de occurred_at/recorded_at, ainda pendente.

## 10. Pendências consolidadas para fechamento

| ID | Pendência | Dependência/validação necessária |
|---|---|---|
| GOV-P01 | Identificar autoridade institucional que concede/revoga competências | Gestão institucional e procedimento formal |
| GOV-P02 | Definir perfis reais, escopos, substituições e revisão periódica | Gestão institucional e responsável funcional |
| GOV-P03 | Definir incompatibilidades adicionais por operação e risco | API10/EST10 e procedimento institucional |
| GOV-P04 | Definir atos com assinatura obrigatória e modalidade aceita | API05, autoridade institucional, jurídico/compliance e segurança |
| GOV-P05 | Definir signatários, assinatura de entrega/recebimento e agentes externos | API05/API10 e procedimento de custódia |
| GOV-P06 | Confirmar alvo, snapshot, canonicalização, hash, verificação, revogação e retenção | Arquitetura, segurança e auditoria |
| GOV-P07 | Confirmar cobertura real de AuditLog e trilha de permissões/exceções | Inspeção de serviços, rotas, migrações e runtime |
| GOV-P08 | Definir fluxo de exceção emergencial, prazo, ratificação e encerramento | Autoridade institucional e segurança |
| GOV-P09 | Confirmar revalidação de autorização em replay e proteção dos snapshots | Inspeção técnica integrada API06/API07 |
| GOV-P10 | Definir regras de consulta de auditoria e evidências pessoais | Segurança, privacidade e gestão documental |

## 11. Critérios de fechamento do Pacote 1

O pacote somente poderá ser considerado fechado após:
1. resolução funcional das pendências que dependem de decisão;
2. definição institucional de autoridades, competências e política de assinatura;
3. inspeção técnica dos serviços, modelos, migrações, rotas e runtime;
4. reconciliação com API04, API05, API06, API07, API10 e API12;
5. definição dos impactos documentais nos contratos, modelo relacional e interface;
6. revisão de segurança, privacidade, auditoria e gestão documental;
7. aprovação institucional aplicável e registro de evidência.

A validação GOV01–GOV05 não fecha o pacote nem autoriza implementação.

## 12. Controle de execução

**Realizado:** consolidação documental do Pacote 1 e registro das diretrizes GOV01–GOV05 validadas pelo responsável pelo projeto em revisão em 2026-11-10. As regras das Operações 1–7 da API10 foram preservadas.

**Não realizado:** alteração de código, banco, migrações, endpoints, frontend, OpenAPI, testes, build, CI ou infraestrutura. Não foi executada revisão runtime nesta etapa.

**Estado:** diretrizes gerais validadas em revisão; fechamento funcional/técnico e aprovação institucional pendentes — implementação bloqueada.

## 13. Histórico de alterações

| Versão | Data | Alteração |
|---|---|---|
| 0.1 | 2026-11-10 | Criação da consolidação do Pacote 1 e registro das diretrizes GOV01–GOV05 validadas em revisão. |
