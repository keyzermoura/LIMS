# Proposta consolidada de fechamento do Pacote 1 — Governança, autorização e responsabilidade

**Identificador:** PROP-LIMS-GOV-002  
**Versão:** 0.6  
**Data:** 2026-11-10  
**Branch:** main  
**Estado:** proposta para revisão do responsável pelo projeto; não validada integralmente; aprovação institucional pendente; implementação bloqueada.

## 1. Objetivo e escopo

Consolidar em uma única proposta as lacunas identificadas na inspeção técnica REV-LIMS-GOV-001 e as diretrizes GOV01–GOV05/API10, abrangendo:

1. autorização por operação, recurso, estado e escopo;
2. concessão, revisão, suspensão e revogação de competências;
3. acumulação e segregação de funções;
4. assinatura eletrônica por natureza do ato;
5. autoria, participantes e timestamps;
6. auditoria de acessos, decisões, concessões e exceções;
7. exceções administrativas e acesso emergencial;
8. proteção operacional da trilha de auditoria.

Esta proposta não substitui a política institucional de segurança, gestão de pessoas, assinatura eletrônica, qualidade ou proteção de dados. Não atribui competências a cargos reais nem presume que ADMIN, FISCAL, TÉCNICO, CUSTODIANTE e AUDITOR correspondam automaticamente a autoridades institucionais.

## 2. Base documental e técnica

A proposta considera:
- PAC-LIMS-GOV-001 v0.1 — diretrizes GOV01–GOV05;
- PROP-LIMS-API10-001 v0.8 — operações 1 a 7 validadas em revisão;
- PROP-LIMS-API05-001 v0.1 — assinatura por operação;
- PROP-LIMS-API04-001 v0.2 — autoria, participantes e timestamps;
- PROP-LIMS-API06-001 v0.2 — controle de concorrência;
- PROP-LIMS-API07-001 v0.2 — idempotência;
- REV-LIMS-GOV-001 v0.1 — inspeção estática de autorização, assinatura e auditoria.

A inspeção identificou autenticação JWT, RBAC básico por papel, emissão/consumo de assinatura de uso único e auditoria encadeada SHA-256/HMAC-SHA256. Não identificou, no escopo consultado, mecanismo completo de concessão/revogação de competências, autorização genérica por escopo, exceções formais ou cobertura integral de eventos de governança.

## 3. Modelo de autorização recomendado

### 3.1 Princípio

Adotar autorização backend baseada em **capacidade + escopo + contexto da operação**, mantendo papéis como agrupadores administrativos e não como prova suficiente de competência.

Toda operação protegida deve ser negada por padrão e autorizada após avaliar:
- identidade autenticada e conta ativa;
- capacidade funcional expressamente concedida;
- escopo organizacional e/ou laboratorial aplicável;
- recurso e estado atual;
- condições e impedimentos da operação;
- validade temporal da concessão;
- segregação de funções e eventuais exceções autorizadas.

A interface pode ocultar ações indisponíveis para facilitar o uso, mas nunca constitui o controle de autorização. A decisão final é sempre do backend.

### 3.2 Componentes conceituais

| Componente | Finalidade |
|---|---|
| Usuário/identidade | Pessoa autenticada responsável pela sessão. |
| Papel administrativo | Agrupador de capacidades para administração e apresentação; não substitui a autorização efetiva. |
| Capacidade | Ação funcional específica, por exemplo formalizar chegada, conferir, regularizar, decidir aceite, transferir custódia, auditar. |
| Escopo | Limite da competência: unidade, serviço, laboratório, classe de material, recurso ou conjunto de processos, conforme política institucional. |
| Concessão | Ato autorizado que associa usuário, capacidade, escopo, validade e condições. |
| Autorização | Avaliação backend de uma operação concreta no contexto e estado atual. |
| Impedimento | Regra de incompatibilidade ou independência aplicável ao ato. |
| Exceção | Autorização excepcional, delimitada e temporária, aprovada pela autoridade competente. |

Não se recomenda criar antecipadamente uma hierarquia complexa de papéis ou uma matriz de cargos. A instituição deverá fornecer o catálogo real de autoridades, unidades, serviços e delegações.

### 3.3 Resultado de autorização

Para cada comando mutável, o backend deverá produzir uma decisão inequívoca:
- permitido;
- negado por ausência/expiração de competência;
- negado por escopo incompatível;
- negado por estado inválido;
- negado por impedimento de segregação;
- permitido por exceção formal vigente, com referência auditável.

A decisão deverá ser reavaliada no momento da execução, inclusive em replay idempotente antes de revelar qualquer snapshot de resposta. Uma chave idempotente, token JWT ou token de assinatura não constitui concessão de competência.

## 4. Concessão e administração de competências

### 4.1 Fluxo recomendado

1. **Solicitação:** registrar usuário, capacidade solicitada, escopo, justificativa e período pretendido.
2. **Análise:** verificar atribuições institucionais, treinamento/habilitação quando aplicável, conflitos e segregação.
3. **Autorização:** autoridade institucional formalmente designada aprova ou rejeita, registrando identidade, instante, fundamento e evidência.
4. **Execução técnica:** administrador técnico aplica exatamente a concessão autorizada, sem ampliar capacidade, escopo ou prazo.
5. **Confirmação:** sistema registra o resultado da execução e vincula-o à autorização original.
6. **Revisão:** realizar revisão periódica e também por mudança de função, afastamento, desligamento, alteração organizacional ou ocorrência relevante.
7. **Revogação/suspensão:** autoridade competente determina; administrador técnico executa; a sessão e permissões efetivas devem refletir a alteração conforme prazo institucional definido.

### 4.2 Separação de responsabilidades

| Ator conceitual | Pode | Não pode por esse papel isoladamente |
|---|---|---|
| Autoridade concedente | Aprovar, limitar, suspender ou revogar competência conforme delegação formal. | Executar tecnicamente concessão fora do fluxo ou ampliar escopo sem nova autorização. |
| Administrador técnico | Criar/alterar configuração conforme autorização válida; registrar execução. | Conceder competência por iniciativa própria, autoatribuir capacidade ou alterar o conteúdo da autorização. |
| Titular da competência | Exercer somente capacidades vigentes e dentro do escopo. | Delegar, ampliar ou compartilhar credenciais. |
| Auditor | Consultar evidências conforme escopo e política de acesso. | Alterar concessões ou registros auditados. |

A mesma pessoa só poderá acumular autoridade concedente e administrador técnico se houver previsão institucional explícita, justificativa, controles compensatórios e registro auditável. A proposta preferencial é manter a separação.

### 4.3 Dados mínimos da concessão

- identificador da concessão;
- usuário beneficiário;
- capacidade(s) concedida(s);
- escopo;
- autoridade que aprovou;
- referência à delegação/ato institucional que sustenta a autoridade;
- justificativa e evidência;
- início e fim de validade, ou condição de encerramento;
- administrador técnico executor;
- data/hora da execução;
- estado (solicitada, aprovada, ativa, suspensa, revogada, expirada, rejeitada);
- motivo e data/hora de suspensão/revogação;
- histórico de alterações, sem sobrescrever silenciosamente o estado anterior.

Os nomes são conceituais; não definem esquema físico.

## 5. Matriz funcional preliminar de autorização e segregação

Esta matriz consolida as Operações 1–7 da API10 sem substituí-las. Os termos representam capacidades, não cargos institucionais.

| Operação | Capacidade necessária | Participantes distintos | Regras de segregação |
|---|---|---|---|
| Formalizar chegada física | FORMALIZAR_CHEGADA | recorded_by; received_by, quando identificável | Registrador pode ser diferente do recebedor físico. Não atribuir automaticamente custódia ao registrador. |
| Conferir materiais | CONFERIR_RECEBIMENTO | conferente; recorded_by | Conferência não concede competência de aceite/recusa. |
| Registrar regularização | REGISTRAR_REGULARIZACAO | executor; recorded_by | Se validação independente for exigida, executor não pode validar a própria regularização (GOV03). |
| Validar regularização | VALIDAR_REGULARIZACAO | validador; executor da regularização | Exigir identidade diferente do executor quando a regra de validação independente se aplicar. |
| Decidir aceite/recusa | DECIDIR_RECEBIMENTO | decisor; conferente e executores anteriores como participantes do processo | Competência específica; não inferir a partir de conferência ou coordenação; não dispensar critério impeditivo. |
| Validar pela coordenação | VALIDAR_COORDENACAO | coordenador/validador; decisor, quando aplicável | Somente em situações definidas institucionalmente; não substitui o decisor nem dispensa critérios impeditivos. |
| Transferir custódia | TRANSFERIR_CUSTODIA | from_custodian; to_custodian; recorded_by | Identificar quem entrega e quem recebe. Regras para auto transferência, equipes/unidades e substitutos devem ser definidas no procedimento. |
| Administrar concessões | ADMINISTRAR_ACESSOS | autoridade concedente; administrador executor; usuário beneficiário | Separação preferencial entre aprovação e execução; proibir autoatribuição sem autorização independente. |
| Consultar/exportar auditoria | CONSULTAR_AUDITORIA / EXPORTAR_AUDITORIA | solicitante | Acesso mínimo necessário, escopo e finalidade registrados conforme política. |
| Administrar exceção | AUTORIZAR_EXCECAO / EXECUTAR_EXCECAO | autoridade; executor; revisor, quando exigido | Exceção não elimina critérios impeditivos legais/técnicos nem apaga histórico. |

### 5.1 Acumulação de funções

Aplicar GOV01: uma pessoa pode acumular capacidades quando a política institucional permitir e não houver conflito/impedimento. Não adotar proibição universal de acumulação sem avaliar o processo.

Impedimentos mínimos propostos:
- executor não valida a própria regularização quando validação independente for obrigatória;
- administrador técnico não se autoatribui competência funcional;
- exceção não pode ser aprovada pelo próprio beneficiário quando a política exigir autoridade independente;
- usuário não pode usar capacidade fora do escopo/validade concedidos.

A instituição deverá decidir se há impedimentos adicionais entre conferente, decisor, coordenador, signatário e custodiante, considerando risco e procedimento.

## 6. Política de assinatura eletrônica por natureza do ato

### 6.1 Princípios

- Não exigir assinatura indiscriminadamente em toda gravação ou consulta.
- Distinguir autenticação, autoria de registro, assinatura eletrônica e evento de auditoria.
- Assinatura deve expressar significado e responsabilidade pelo ato, não apenas presença de sessão.
- Signatário deve possuir competência vigente para o ato e escopo correspondente.
- O conteúdo assinado deve ser identificável e imutável após a assinatura.
- Consumo da assinatura e alteração de negócio devem ser atômicos.
- A emissão do token de assinatura não pode antecipar ou dispensar a autorização da operação.

### 6.2 Matriz recomendada para revisão

| Ato | Política preliminar recomendada | Justificativa/condição |
|---|---|---|
| Formalização da chegada física | Condicional | Assinatura se o procedimento institucional atribuir responsabilidade formal ao registrador; autenticação e auditoria sempre obrigatórias. |
| Conferência de materiais | Condicional | Assinatura quando a conferência constituir declaração formal de responsabilidade; caso contrário, autoria autenticada + auditoria. |
| Registro de pendência/regularização | Condicional | Autoria do executor e evidência obrigatórias; assinatura conforme relevância e procedimento. |
| Validação de regularização | Obrigatória quando a validação independente for ato formal | Identifica validador e conteúdo validado. |
| Aceite/recusa | Obrigatória | Decisão com impacto sobre a entrada institucional e a cadeia de custódia; signatário deve ter competência de decisão. |
| Validação da coordenação | Obrigatória quando exigida pelo fluxo institucional | Registra a revisão/validação, sem substituir a decisão técnica/administrativa. |
| Transferência de custódia | Condicional, preferencialmente bilateral quando procedimento exigir confirmação do recebedor | A assinatura deve refletir a entrega/recebimento; não confundir signatário com custodiante automaticamente. |
| Retificação formal de evento/decisão | Obrigatória | Preserva o original, registra motivo, autor, instante e conteúdo retificado. |
| Exceção administrativa | Obrigatória para autorização da exceção | Assinatura/registro da autoridade competente e vínculo ao escopo, prazo e justificativa. |
| Concessão/revogação de competência | Obrigatória como aprovação formal, segundo política institucional | Distingue autoridade que aprovou e administrador que executou. |
| Consulta, listagem e leitura ordinária | Não exigir | Registrar auditoria somente quando a política de segurança/privacidade definir necessidade. |

Esta matriz é recomendação para validação, não política institucional aprovada. A modalidade e o nível de garantia (senha reautenticada, MFA, certificado ou outro mecanismo) dependem de análise jurídica, administrativa, de segurança e do contexto de risco.

### 6.3 Manifesto e snapshot

Para cada assinatura, recomenda-se persistir e permitir verificar:
- signatário e identificadores de identidade;
- papel/capacidade/escopo vigente no momento do ato;
- significado da assinatura;
- entidade e identificador alvo;
- ação específica;
- versão do recurso/ato;
- snapshot canônico do conteúdo aprovado;
- hash do snapshot e algoritmo;
- versão do algoritmo de canonicalização;
- instante da assinatura e instante de registro;
- motivo, quando aplicável;
- referência à autorização/competência e à evidência de exceção, se houver;
- estado do ciclo de vida (emitida, consumida, expirada, cancelada/revogada), com histórico.

A assinatura deve ser consumida apenas para o alvo/ação exatos. Alteração do conteúdo após a emissão deve invalidar a correspondência ou exigir nova assinatura. O snapshot não deve ser opcional em atos que formalmente exigem assinatura.

### 6.4 Ciclo de vida

Definir formalmente:
- validade do token;
- cancelamento/revogação antes do consumo;
- tratamento de assinatura emitida e não utilizada;
- bloqueio por alteração do recurso/versão;
- retenção do manifesto e snapshot;
- recuperação e verificação de assinatura histórica;
- efeito de suspensão/revogação da competência entre emissão e consumo.

Recomendação: revalidar competência e autorização no consumo. Se a competência tiver sido suspensa/revogada antes do consumo, não aceitar a assinatura para efetivar o ato.

## 7. Autoria, participantes e timestamps

Adotar a semântica da API04 em todos os eventos relevantes, sem preencher papéis diferentes com o mesmo usuário por conveniência.

| Campo conceitual | Significado |
|---|---|
| recorded_by | Usuário que registrou o evento no sistema. |
| performed_by | Pessoa que executou materialmente a ação. |
| received_by | Pessoa que recebeu fisicamente o material. |
| decided_by | Pessoa competente que tomou a decisão. |
| validated_by | Pessoa que realizou validação independente ou de coordenação. |
| signer | Pessoa que assinou eletronicamente o ato. |
| from_custodian | Responsável que entrega a custódia. |
| to_custodian | Responsável que recebe a custódia. |
| authorized_by | Autoridade que aprovou uma concessão ou exceção. |
| executed_by | Administrador/técnico que aplicou a autorização no sistema. |

Timestamps:
- `occurred_at`: instante efetivo em que o evento aconteceu;
- `recorded_at`: instante em que o sistema registrou o evento;
- `signed_at`: instante em que a assinatura foi realizada;
- timestamps devem conter timezone/offset inequívoco;
- não aceitar `recorded_at` fornecido pelo cliente;
- lançamento tardio deve manter ambos os instantes, motivo e auditoria;
- correções devem gerar evento compensatório/retificação, não reescrever silenciosamente o histórico.

## 8. Auditoria, integridade e monitoramento

### 8.1 Eventos mínimos a auditar

- autenticação bem-sucedida/falha, bloqueio, logout, refresh e mudança de credenciais;
- emissão, consumo, cancelamento, expiração e rejeição de assinatura;
- concessão, alteração, suspensão, revogação e expiração de competência;
- tentativa negada por autorização, escopo ou impedimento, com minimização de dados;
- autorização, execução, revisão e encerramento de exceção;
- formalização, conferência, regularização, validação, decisão e retificação;
- transferência de custódia e alteração de localização;
- consultas/exportações sensíveis de auditoria e verificação de integridade;
- mudanças em parâmetros de segurança e administração técnica.

Cada evento deve identificar ator autenticado, participante material do ato quando diferente, alvo, ação, resultado, instante efetivo/registro, justificativa e request/correlation ID, conforme aplicabilidade.

### 8.2 Integridade e proteção operacional

Manter a cadeia existente como mecanismo central, sem criar trilha paralela concorrente. Para considerá-la operacionalmente confiável, é necessário verificar e formalizar:
- trigger/controles de banco contra UPDATE/DELETE/TRUNCATE;
- privilégios que impeçam aplicação e administradores comuns de alterar a trilha;
- armazenamento segregado da chave HMAC;
- acesso restrito à chave, rotação, versionamento, backup e recuperação;
- monitoramento de falhas de append/verificação;
- verificação periódica e independente da cadeia;
- retenção, cópia de segurança e preservação de evidências;
- registro das próprias consultas/exportações/verificações conforme política.

Não considerar hash/HMAC como substituto de controle de acesso, segregação, backup ou gestão de chaves. Não armazenar segredo HMAC em log ou junto ao payload auditado.

### 8.3 Acesso a dados de auditoria

Separar capacidade de consultar metadados, visualizar payload completo, exportar, verificar integridade e administrar parâmetros. Definir escopo organizacional, finalidade, mascaramento e retenção. ADMIN não deve automaticamente receber acesso irrestrito a todo conteúdo sensível apenas por ser administrador técnico; a instituição deverá definir exceções justificadas e auditadas.

## 9. Exceções administrativas e acesso emergencial

Toda exceção deve conter:
- identificador e categoria;
- situação concreta e justificativa;
- autoridade que autorizou e evidência da autoridade;
- beneficiário e executor;
- capacidade e escopo estritamente necessários;
- início, expiração ou condição objetiva de encerramento;
- recursos/operações abrangidos;
- controles compensatórios;
- revisão posterior, quando aplicável;
- resultado, encerramento e trilha de auditoria.

Regras:
1. Exceção não pode dispensar requisito legal, normativo ou critério técnico impeditivo.
2. Exceção não altera retroativamente o fato histórico.
3. Exceção emergencial deve ser limitada no tempo e escopo, com revisão posterior em prazo institucional definido.
4. Se o fluxo emergencial admitir a mesma pessoa em papéis normalmente separados, registrar a justificativa e exigir revisão independente posterior, quando aplicável.
5. Não manter acesso privilegiado permanente sob justificativa de emergência.

## 10. Decisões propostas para validação consolidada

| ID | Decisão proposta | Recomendação | O que depende de manifestação/autoridade institucional |
|---|---|---|---|
| GOV-P01 | Modelo de autorização | Capacidade + escopo + contexto/estado; papéis como agrupadores | **Validada em revisão pelo responsável pelo projeto (2026-11-10).** A instituição ainda deve formalizar catálogo, escopos e autoridades reais. |
| GOV-P02 | Concessão de competência | Autoridade formal aprova; administrador técnico executa; beneficiário não se autoatribui | Identificar autoridade, delegações e procedimento oficial. |
| GOV-P03 | Revisão/revogação | Validade explícita e revisão por mudança funcional/afastamento/desligamento; revogação executada tecnicamente após autorização | Definir prazos, responsáveis e integração com gestão de pessoas. |
| GOV-P04 | Segregação | Aplicar independência obrigatória executor/validador quando exigida; manter demais acumulações conforme política | **Validada em revisão pelo responsável pelo projeto (2026-11-10)** quanto ao princípio geral, em coerência com GOV01 e GOV03. Incompatibilidades adicionais entre conferente, decisor, coordenação, signatário, custodiante e administrador dependem de definição institucional. |
| GOV-P05 | Matriz de assinatura | Aceite/recusa, validação independente formal, retificação formal, exceção e concessão/revogação com aprovação exigem assinatura formal; outros atos condicionais conforme procedimento | Aprovar matriz por operação e modalidade/nível de garantia. |
| GOV-P06 | Assinatura e competência | Competência verificada na emissão e novamente no consumo; snapshot obrigatório para atos assinados | Confirmar política, validade, revogação e retenção. |
| GOV-P07 | Autoria e tempo | Separar participantes e `occurred_at`/`recorded_at`/`signed_at` | **Recomendações AUD-P07-01 a AUD-P07-06 validadas em revisão (2026-11-10)**; política institucional de fuso, lançamento tardio, retificação e participantes permanece pendente. |
| GOV-P08 | Auditoria | Registrar eventos de acesso, governança, exceção e atos críticos na cadeia existente | **Recomendações AUD-P08-01 a AUD-P08-07 validadas em revisão (2026-11-10)**; cobertura por operação, acesso, retenção, monitoramento e comprovação técnica permanecem pendentes. |
| GOV-P09 | Chaves e imutabilidade | Segregar chave HMAC, restringir privilégios e verificar trigger/backup/rotação | Definir responsável institucional e controles de infraestrutura. |
| GOV-P10 | Exceções | Autorização formal, escopo mínimo, prazo/condição, controles compensatórios e revisão posterior | Definir autoridades, hipóteses admissíveis e prazos. |
| GOV-P11 | Administração de auditoria | Separar consulta, exportação, verificação e administração técnica; acesso mínimo e auditado | Definir perfis, unidades, finalidade e mascaramento. |

## 11. Dependências e sequência de fechamento

1. GOV-P01 (modelo de autorização) e GOV-P04 (princípio geral de segregação) foram validadas pelo responsável pelo projeto em revisão em 2026-11-10. GOV-P07/GOV-P08 foram validadas em revisão. Permanecem para validação GOV-P05/GOV-P06 quanto à formalização institucional e fechamento técnico, GOV-P09, GOV-P10 e GOV-P11.
2. Obter da instituição as definições de autoridade, delegação, cargos/funções, modalidade de assinatura, prazos, retenção, exceções e escopos.
3. Consolidar catálogo de capacidades e matriz de acesso por operação, rota, recurso, estado e escopo.
4. Confrontar a matriz com runtime de todas as rotas e serviços, incluindo as operações API10 1–7 e contratos legados.
5. Realizar revisão de segurança/privacidade e arquitetura; confirmar migrações, trigger, grants, configuração e gestão de segredos, sem inferir estado de produção.
6. Atualizar documentos API04/API05/API10 e matriz geral somente após decisões; depois revisar contratos/API/OpenAPI e modelo relacional em pacote coordenado.
7. Submeter pacote à aprovação institucional aplicável.
8. Somente após revisão técnica, aprovação institucional e autorização específica, avaliar implementação.

## 12. Critérios de fechamento do Pacote 1

O Pacote 1 só poderá ser marcado como fechado quando:
- catálogo de capacidades, escopos e regras de autorização estiver definido;
- autoridade e procedimento de concessão/revogação estiverem formalizados;
- matriz de segregação e acumulação estiver aprovada;
- matriz de assinatura e modalidade aplicável estiver formalizada;
- autoria, participantes e timestamps estiverem harmonizados com API04;
- eventos de auditoria e controles de integridade estiverem especificados e verificados;
- fluxo de exceções estiver formalizado;
- compatibilidade com API06/API07/API10 e contratos existentes estiver demonstrada;
- pendências técnicas e institucionais estiverem resolvidas ou formalmente aceitas;
- aprovação institucional e evidência documental estiverem registradas.

## 13. Controle e limitações

Esta proposta é exclusivamente documental. Não altera código, banco, migrações, endpoints, frontend, OpenAPI, testes, build, CI ou infraestrutura. Não foi executada validação de runtime, banco ou produção. As recomendações GOV-P01 e GOV-P04 foram validadas pelo responsável pelo projeto em revisão em 2026-11-10, nos limites descritos na seção 10. As recomendações GOV-P05 e GOV-P06 (SIG-P01–SIG-P06) tiveram suas recomendações validadas em revisão, nos limites do documento complementar PROP-LIMS-GOV-SIG-001, mas dependem de formalização institucional e fechamento técnico. GOV-P02, GOV-P03, GOV-P09, GOV-P10 e GOV-P11 permanecem sem validação pelo responsável do projeto. GOV-P07 e GOV-P08 tiveram as recomendações AUD-P07/AUD-P08 validadas em revisão, nos limites da proposta complementar PROP-LIMS-GOV-AUD-001 v0.2. Nenhuma dessas validações equivale a aprovação institucional.

**Situação:** Pacote 1 aberto. **Implementação bloqueada.**


## 15. Proposta específica para assinatura eletrônica — GOV-P05/GOV-P06

Em 2026-11-10, foi elaborada a proposta complementar PROP-LIMS-GOV-SIG-001 (docs/PROPOSTA_FECHAMENTO_GOV_P05_P06_ASSINATURA.md), que detalha a matriz de assinatura por natureza do ato e as invariantes de competência na emissão/consumo, snapshot, integridade, atomicidade, revogação e replay idempotente.

As recomendações SIG-P01–SIG-P06 da proposta específica foram validadas em revisão pelo responsável pelo projeto em 2026-11-10, nos limites registrados em PROP-LIMS-GOV-SIG-001 v0.2. GOV-P05/GOV-P06 permanecem pendentes de formalização institucional e fechamento técnico.

## 16. Proposta específica para autoria, timestamps e auditoria — GOV-P07/GOV-P08

A proposta complementar PROP-LIMS-GOV-AUD-001 v0.2 (docs/PROPOSTA_FECHAMENTO_GOV_P07_P08_AUTORIA_AUDITORIA.md) teve as recomendações AUD-P07-01 a AUD-P07-06 e AUD-P08-01 a AUD-P08-07 validadas em revisão pelo responsável pelo projeto em 2026-11-10. A validação preserva os limites do documento: não define fuso institucional, política de lançamento tardio/retificação, retenção, acesso, infraestrutura ou prova de implantação dos controles. GOV-P07/GOV-P08 permanecem pendentes de formalização institucional e fechamento técnico; não há autorização de implementação. A modalidade de assinatura, signatários por ato, retenção e demais definições institucionais não foram presumidas.

## 17. Proposta específica para integridade operacional e acesso à auditoria — GOV-P09/GOV-P11\n\nFoi elaborada a proposta complementar PROP-LIMS-GOV-SEC-001 v0.1 (docs/PROPOSTA_FECHAMENTO_GOV_P09_P11_INTEGRIDADE_ACESSO_AUDITORIA.md), com recomendações AUD-P09-01 a AUD-P09-09 e AUD-P11-01 a AUD-P11-09 para revisão. Essas recomendações ainda não foram validadas. A proposta não comprova configuração operacional de banco, chaves, backups ou controles de acesso e não autoriza implementação.\n\n## 14. Histórico

| Versão | Data | Alteração |
|---|---|---|
| 0.1 | 2026-11-10 | Proposta consolidada de fechamento com modelo de autorização, concessões, segregação, assinatura, autoria, auditoria e exceções, derivada da inspeção REV-LIMS-GOV-001. |
| 0.2 | 2026-11-10 | Registro da validação em revisão de GOV-P01 (modelo de autorização) e GOV-P04 (princípio geral de segregação); definições institucionais específicas e demais decisões permanecem pendentes. |
| 0.3 | 2026-11-10 | Referência à proposta complementar PROP-LIMS-GOV-SIG-001 para GOV-P05/GOV-P06; decisões de assinatura permanecem pendentes de validação e aprovação institucional. |
| 0.4 | 2026-11-10 | Registro da validação em revisão de SIG-P01–SIG-P06; GOV-P05/GOV-P06 seguem pendentes de formalização institucional, fechamento técnico e autorização de implementação. |
