# Proposta de Resolução da API05 — Assinatura Eletrônica por Operação e Alvo

**Identificador:** PROP-LIMS-API05-001  
**Versão:** 0.1  
**Situação:** Proposta técnica para validação funcional, segurança e governança institucional; não aprovada para implementação  
**Decisão relacionada:** API05 / DEC09 / EST07 / EST10 / API04 / API06 / API07  
**Data:** 2026-11-10  
**Repositório:** keyzermoura/LIMS — branch `main`

---

## 1. Objetivo

Propor uma política coerente para determinar:

- quais operações exigem assinatura eletrônica;
- quem deve assinar cada ato;
- qual entidade/decisão/evento constitui o alvo assinado;
- qual conteúdo imutável deve ser vinculado à assinatura;
- em que momento a assinatura é produzida e validada;
- como tratar assinatura ausente, inválida, revogada ou incompatível com a versão do conteúdo.

A proposta parte da diretriz validada pelo responsável pelo projeto em revisão: não exigir assinatura indiscriminadamente em toda ação; definir uma matriz de operações, atores, alvos e exigências. Essa validação de diretriz não equivale a aprovação institucional da política de assinatura.

## 2. Princípios

1. **Autenticação não é assinatura:** estar autenticado ou possuir sessão válida não comprova, por si só, que o usuário assinou um ato.
2. **Auditoria não é assinatura:** um registro em `AuditLog` demonstra atividade registrada, mas não substitui automaticamente uma assinatura eletrônica.
3. **Assinatura tem alvo explícito:** deve apontar para o ato/decisão/conteúdo efetivamente assinado, não para uma entidade aproximada apenas por conveniência.
4. **Conteúdo assinado é estável:** deve existir snapshot canônico ou representação equivalente, com integridade verificável.
5. **Identidade e papel são distintos:** signatário, autor do registro, recebedor físico, custodiante, conferente, validador e usuário que executa a operação podem ser pessoas diferentes.
6. **Obrigatoriedade decorre de política aprovada:** a aplicação deve bloquear a operação quando a assinatura for obrigatória e não estiver válida; não deve inventar requisitos institucionais.
7. **Assinatura não corrige autorização:** além de assinar, o usuário precisa estar autorizado a praticar o ato.
8. **Histórico preservado:** retificação não apaga assinatura ou conteúdo anterior; gera novo ato relacionado, conforme EST08.
9. **Compatibilidade legada:** não reinterpretar assinaturas antigas nem atribuir alvos ou conteúdos que não estejam comprovados.
10. **Sem tabela paralela de custódia:** a assinatura pode referenciar evento/decisão/recebimento, mas não cria uma segunda cadeia de eventos.

## 3. Matriz inicial de operações e assinatura

A matriz abaixo é uma recomendação para revisão. A classificação “obrigatória proposta” precisa ser confirmada pelos responsáveis institucionais e pelos procedimentos aplicáveis. “Condicional” significa que a assinatura depende da natureza do ato, risco, procedimento ou decisão formal.

| Operação/ato | Exigência proposta | Signatário esperado | Alvo conceitual da assinatura | Observações |
|---|---|---|---|---|
| Formalização da chegada física | Condicional | Recebedor físico ou responsável formal designado | Registro de chegada/Receipt e dados essenciais da entrega | A autoria do lançamento deve ser registrada separadamente; assinatura pode ser exigida pelo procedimento de recebimento. |
| Conferência de itens e quantidades | Condicional | Conferente responsável | Resultado/versionamento da conferência do recebimento | Se houver declaração formal de conferência, assinar a versão efetivamente conferida. |
| Registro de pendência ou evidência | Em regra, autoria e auditoria; assinatura condicional | Usuário que registra ou responsável pela declaração | Pendência/evidência específica, quando constituir declaração formal | Não exigir assinatura para cada anotação operacional sem justificativa. |
| Regularização de pendência | Condicional | Responsável que executa e/ou valida a regularização, conforme procedimento | Registro/versionamento da regularização e evidências | Distinguir quem apresentou evidência de quem validou sua suficiência. |
| Aceite do material | Obrigatória proposta | Agente autorizado a decidir o aceite | Decisão formal de aceite vinculada ao CustodyObject/ReceiptItem | Assinatura deve ocorrer antes ou atomicamente com a confirmação da decisão e criação da amostra, quando aplicável. |
| Recusa do material | Obrigatória proposta | Agente autorizado a decidir a recusa | Decisão formal de recusa, com motivo e fundamento | Recusa não encerra automaticamente a custódia. |
| Validação de coordenação | Obrigatória quando exigida pelo fluxo | Coordenador/validador autorizado | Ato de validação e versão do objeto/recebimento validada | Não deve ser confundida com o aceite nem dispensar critérios impeditivos. |
| Transferência de custódia | Condicional; assinatura dos envolvidos quando exigida pelo procedimento | Responsável que entrega e responsável que recebe | Evento de transferência específico | Definir se uma ou ambas as partes assinam; não presumir que o autor do lançamento é o custodiante. |
| Mudança de localização sem troca de custodiante | Condicional | Responsável autorizado pelo movimento | Evento LOCATION_CHANGE | Pode bastar autoria auditável conforme risco e procedimento. |
| Devolução | Obrigatória proposta | Responsável autorizado pela devolução e, quando aplicável, recebedor externo | Decisão/autorização de devolução e evento de entrega | Definir como comprovar assinatura de pessoa externa sem conta no LIMS. |
| Destinação final/descarte/encerramento | Obrigatória proposta | Responsável autorizado e eventual testemunha exigida | Decisão de destinação e evento correspondente | Requisitos dependem de política institucional e classe de material. |
| Correção/retificação | Obrigatória proposta quando altera dado formal ou decisão assinada | Autor da retificação e aprovador, se exigido | Ato de retificação, com referência ao conteúdo/evento original | Preservar original e assinatura anterior; não sobrescrever snapshot. |

### 3.1 Diretriz de proporcionalidade

Não se recomenda exigir assinatura eletrônica para toda interação, navegação, salvamento intermediário, inclusão de observação ou registro de evidência sem efeito decisório. Esses atos devem ter autenticação, autorização e auditoria adequadas. A assinatura fica reservada aos atos formalmente declaratórios, decisórios, de transferência ou encerramento, conforme matriz institucional aprovada.

## 4. Identidade, papéis e segregação

Cada operação deve identificar separadamente, quando aplicável:

- `recorded_by`: usuário autenticado que persistiu o registro;
- `signer`: pessoa que efetivamente assinou o conteúdo;
- `received_by`: recebedor físico;
- `from_custodian` e `to_custodian`: responsáveis pela entrega e recebimento da guarda;
- `performed_by`: pessoa que praticou o ato operacional;
- `validated_by`: pessoa que validou ou aprovou, quando exigido.

Uma pessoa pode acumular mais de um papel somente quando a política de segregação permitir. A regra de impedimento de autoaprovação, dupla assinatura e independência entre recebedor, conferente, decisor e validador depende de API10/EST10 e não é resolvida por esta proposta.

O sistema deve derivar a identidade autenticada do contexto de segurança. Não aceitar identificador de signatário arbitrário no payload como prova suficiente de autoria. Quando a assinatura for realizada por terceiro externo, o mecanismo de identificação e evidência deverá ser aprovado institucionalmente.

## 5. Alvo e conteúdo assinado

### 5.1 Alvo conceitual

A assinatura deve estar vinculada a um alvo de domínio específico, por exemplo:

- `Receipt`/formalização de chegada;
- versão de conferência;
- decisão de aceite ou recusa;
- validação de coordenação;
- evento `ChainOfCustody` de transferência, localização, devolução ou destinação;
- ato de retificação.

Não vincular assinatura a `DeviceSample` quando o ato ocorreu antes de a amostra existir. Para o novo fluxo, o alvo deverá refletir o agregado/ato real, inclusive `CustodyObject` quando apropriado, preservando a semântica legada.

### 5.2 Snapshot canônico

No momento da assinatura, produzir uma representação estável contendo, conforme o tipo de ato:

- identificador do ato e tipo de operação;
- identificador do objeto/recebimento/item relacionado;
- versão do agregado assinada;
- decisão, resultado ou declaração;
- dados essenciais apresentados ao signatário;
- justificativa e referências às evidências relevantes;
- identidade e papel do signatário;
- data/hora da assinatura;
- versão do formato/canonicalização do conteúdo.

O snapshot deve ser imutável. Uma alteração posterior não pode modificar silenciosamente o conteúdo assinado. Se o conteúdo precisar mudar, deve ser criado novo ato/versão e, quando aplicável, nova assinatura.

### 5.3 Integridade

Recomenda-se armazenar hash criptográfico do snapshot canônico, algoritmo identificado e referência ao conteúdo preservado. O hash, isoladamente, não substitui o snapshot: deve ser possível recuperar o conteúdo exato que foi apresentado e assinado.

A forma de canonicalização, algoritmo, armazenamento, retenção, verificação e proteção contra substituição deve ser especificada pela arquitetura e segurança antes de qualquer implementação. Não presumir que o hash atual de `AuditLog` ou os campos atuais de `ElectronicSignature` já satisfazem todos esses requisitos.

## 6. Momento e atomicidade da assinatura

Para atos cuja assinatura é obrigatória:

1. validar identidade, autorização e segregação;
2. construir o conteúdo exato do ato e sua versão;
3. apresentar ao signatário o conteúdo que será assinado;
4. obter a confirmação/assinatura pelo mecanismo aprovado;
5. validar a assinatura e vincular o resultado ao alvo e snapshot;
6. persistir assinatura, decisão/evento e mudanças de estado de forma atômica, quando pertencentes à mesma operação;
7. somente então confirmar a operação e liberar efeitos subsequentes.

Se o mecanismo de assinatura for externo ou assíncrono, não manter transação de banco aberta durante interação humana ou chamada remota longa. Nesse caso, desenhar estado intermediário explícito, expiração, retomada idempotente e prevenção de efeitos antes da confirmação final. Essa alternativa depende da tecnologia institucional escolhida e não está definida nesta proposta.

Quando a assinatura obrigatória estiver ausente, inválida, expirada ou vinculada a conteúdo/versão diferente, a operação deve ser bloqueada sem produzir aceite, transferência ou encerramento parcial. O código HTTP e os detalhes de erro devem ser fechados no contrato API, coordenados com API06/API07.

## 7. Relação com o modelo existente

O inventário disponível identifica entidade/modelo `ElectronicSignature` com vínculo genérico por `entity_type`, `entity_id` e `action`, além de `AuditLog`. A existência desses elementos não demonstra, por si só, que o sistema atual armazene snapshot canônico, hash, versão assinada, método de autenticação, validação ou evidência suficientes.

Antes de propor alteração física, inspecionar modelo ORM, migrações, serviços, rotas e consumidores para confirmar:

- campos efetivos de `ElectronicSignature`;
- se o vínculo genérico possui integridade referencial ou validação de domínio;
- como são produzidos e verificados tokens/assinaturas;
- qual conteúdo é assinado e se é preservado;
- se há hash, algoritmo e versão do conteúdo;
- como são registrados signatário, instante e método;
- se existe expiração, revogação, revalidação ou consulta posterior;
- como o modelo legado se relaciona com novos alvos pré-`DeviceSample`.

Não inferir dados históricos nem alterar a semântica das assinaturas legadas. Uma solução aditiva deve preservar leitura e validação do legado.

## 8. Contrato HTTP — requisitos conceituais

Os contratos deverão:

- indicar no tipo de operação se assinatura é requerida;
- identificar o alvo e a versão exata a assinar;
- não aceitar `recorded_by` ou identidade do signatário como prova fornecida livremente pelo cliente;
- retornar estado da assinatura e referência do ato assinado, sem expor segredo/token reutilizável;
- distinguir ausência de assinatura, assinatura inválida, conteúdo divergente, signatário não autorizado e conflito de versão;
- permitir consulta de evidência de assinatura conforme permissão;
- preservar idempotência em operações que geram decisão/evento assinado.

A forma de assinatura — senha reautenticada, confirmação eletrônica institucional, certificado digital ou outro mecanismo — não é escolhida nesta proposta. A instituição deve definir nível de garantia, identidade, validade jurídica/administrativa, evidência, retenção e eventuais requisitos normativos aplicáveis. Não presumir que uma modalidade específica atende à política institucional.

## 9. Segurança, privacidade e retenção

- Proteger snapshots, evidências e dados de signatários contra acesso indevido.
- Aplicar controle de acesso por papel e finalidade, inclusive na consulta posterior.
- Registrar tentativas de assinatura, falhas e revogações relevantes sem expor credenciais.
- Não armazenar senhas, tokens de autenticação ou segredos de assinatura em texto claro.
- Definir retenção e descarte conforme tabela institucional de temporalidade e obrigações aplicáveis.
- Garantir que cópias exportadas/reproduzidas permitam verificar a integridade do conteúdo e a relação com a assinatura.
- Tratar assinatura externa e dados pessoais segundo política de privacidade e segurança institucional.

## 10. Questões pendentes de validação

| ID | Questão | Recomendação | Responsável |
|---|---|---|---|
| API05.1 | Quais atos exigem assinatura obrigatória? | Validar a matriz da seção 3 por procedimento e risco. | Autoridade institucional e responsável funcional. |
| API05.2 | Qual modalidade de assinatura é aceita? | Definir nível de garantia, identidade, validade e evidência. | Autoridade institucional, jurídico/compliance e segurança. |
| API05.3 | Quem assina cada operação? | Definir signatários e papéis por ato, inclusive agentes externos. | Responsável funcional e gestão institucional. |
| API05.4 | A transferência exige assinatura de uma ou das duas partes? | Definir regra de entrega/recebimento e exceções operacionais. | Responsável pela custódia e gestão institucional. |
| API05.5 | Qual é o alvo de assinatura em cada operação? | Adotar entidade/ato real e evitar vínculo a DeviceSample inexistente. | Arquitetura e responsável funcional. |
| API05.6 | Qual conteúdo e snapshot devem ser preservados? | Definir campos, canonicalização, versão, evidências e hash. | Arquitetura, segurança e auditoria. |
| API05.7 | Como tratar assinatura externa, indisponibilidade e fluxo assíncrono? | Definir mecanismo e estado intermediário sem efeitos prematuros. | Segurança, arquitetura e responsável funcional. |
| API05.8 | Como tratar revogação, expiração, substituição e retificação? | Preservar evidência original e registrar novo ato relacionado. | Autoridade institucional, auditoria e segurança. |
| API05.9 | Quais regras de segregação impedem autoassinatura/autoaprovação? | Resolver conjuntamente com API10/EST10. | Gestão institucional e segurança. |
| API05.10 | Qual retenção e acesso às evidências? | Alinhar temporalidade, privacidade e auditoria. | Gestão documental, segurança e autoridade institucional. |

## 11. Critérios para considerar API05 resolvida

API05 só poderá ser considerada resolvida quando:

1. a matriz de operações e obrigatoriedade estiver aprovada pelos responsáveis competentes;
2. modalidade e nível de garantia da assinatura estiverem definidos institucionalmente;
3. signatários e regras de segregação estiverem alinhados com API10/EST10;
4. alvo e conteúdo/snapshot de cada assinatura estiverem definidos;
5. o modelo `ElectronicSignature` e os serviços existentes tiverem sido inspecionados;
6. estratégia de integridade, validação, revogação, retenção e consulta estiver aprovada;
7. assinatura externa e falhas/indisponibilidade tiverem tratamento definido;
8. contratos HTTP, OpenAPI, modelo relacional e interface estiverem reconciliados;
9. compatibilidade com assinaturas e rotas legadas estiver demonstrada;
10. aprovação institucional e evidência documental estiverem registradas.

## 12. Controle de execução

**Realizado:** elaboração desta proposta documental de matriz de assinatura por operação, identidade/papéis, alvo, snapshot, integridade, atomicidade e questões de governança.

**Não realizado:** inspeção adicional de código/modelos/migrações nesta atividade; alteração da especificação HTTP, OpenAPI, modelo relacional, código, banco, migrações, endpoints, frontend, testes, build ou CI.

**Estado:** proposta técnica pendente de validação funcional, segurança e aprovação institucional. A diretriz geral de não exigir assinatura indiscriminadamente foi validada pelo responsável pelo projeto em revisão (2026-11-10); a matriz detalhada e a política institucional ainda não foram aprovadas. Não há autorização para implementação.

## 13. Histórico de alterações

| Versão | Data | Alteração |
|---|---|---|
| 0.1 | 2026-11-10 | Criação da proposta de matriz de assinatura por operação, alvo assinado, identidade, snapshot, integridade e governança. |
