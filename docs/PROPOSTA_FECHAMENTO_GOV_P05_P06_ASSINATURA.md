# Proposta consolidada de fechamento GOV-P05 e GOV-P06 — Assinatura eletrônica

**Identificador:** PROP-LIMS-GOV-SIG-001  
**Versão:** 0.2  
**Data:** 2026-11-10  
**Branch:** `main`  
**Estado:** proposta para revisão do responsável pelo projeto; não validada; aprovação institucional pendente; implementação bloqueada.

## 1. Objetivo e limites

Este documento consolida as recomendações para as decisões GOV-P05 (matriz de assinatura por operação) e GOV-P06 (vínculo entre assinatura, competência e conteúdo), articulando a proposta API05, as diretrizes GOV01–GOV05/API10 e a inspeção técnica REV-LIMS-GOV-001.

O objetivo é permitir uma decisão de desenho do projeto sobre **quando exigir assinatura e quais garantias técnicas são invariantes**, sem escolher em nome da instituição a modalidade juridicamente/administrativamente aceita, os signatários vinculados a cargos reais ou os prazos de retenção.

Esta proposta não aprova política institucional nem autoriza implementação.

## 2. Premissas já estabelecidas

1. Autenticação, autoria, auditoria e assinatura são conceitos distintos.
2. Não exigir assinatura em toda gravação, navegação ou salvamento intermediário.
3. O signatário deve possuir competência específica, vigente e compatível com o escopo do ato.
4. O conteúdo assinado deve ser identificável e preservado; hash isolado não substitui o snapshot.
5. O alvo da assinatura deve ser o ato real. Atos anteriores à criação de `DeviceSample` não devem ser vinculados artificialmente à amostra.
6. A identidade de `recorded_by`, `performed_by`, `received_by`, `decided_by`, `validated_by`, `signer` e custodiante deve permanecer semanticamente distinta, mesmo quando uma pessoa acumular papéis permitidos.
7. Aplicam-se GOV01 e GOV03: acumulação é possível quando permitida e sem impedimento; executor não valida a própria regularização quando independência for exigida.
8. A autorização da operação e a autorização para assinar devem ser avaliadas pelo backend; token de assinatura não concede competência.

## 3. Matriz consolidada recomendada

| Ato/operação | Exigência recomendada | Alvo conceitual | Regra de assinatura |
|---|---|---|---|
| Formalização da chegada física | Condicional | Registro/versão da chegada (`Receipt`) | Exigir quando o procedimento atribuir ao registrador ou recebedor uma declaração formal de responsabilidade. Autoria e auditoria sempre registradas. |
| Conferência de itens, quantidades e condições | Condicional | Versão formal da conferência | Exigir quando a conferência for declaração formal atestada; não assinar automaticamente cada salvamento parcial. |
| Inclusão de evidência, observação ou pendência | Não exigir por padrão | Registro específico, com autoria | Autenticação, autorização e auditoria; assinatura apenas se a informação constituir declaração formal autônoma. |
| Regularização executada | Condicional | Registro/versão da regularização e evidências | Registrar executor e evidência. Assinatura do executor somente quando procedimento definir declaração formal. |
| Validação independente da regularização | Obrigatória quando a validação independente constituir ato formal exigido | Ato de validação e versão/evidência validada | Signatário deve ser distinto do executor quando a independência for exigida (GOV03). |
| Aceite do material | Obrigatória | Decisão formal de aceite vinculada ao `CustodyObject`/`ItemRecebimento` | Assinatura do decisor autorizado deve integrar atomicamente a decisão e a criação/vinculação da amostra, quando aplicável. |
| Recusa do material | Obrigatória | Decisão formal de recusa, motivo e fundamento | Assinatura do decisor autorizado; a recusa não encerra por si só a custódia. |
| Validação da coordenação | Obrigatória somente quando o fluxo institucional exigir validação formal | Ato/versão validada | Assinatura identifica o coordenador/validador; não substitui o decisor nem afasta critério impeditivo. |
| Transferência de custódia | Condicional | Evento específico de transferência | Identificar entregante e recebedor. Exigir assinatura de uma ou ambas as partes conforme procedimento formal; não presumir assinatura bilateral universal. |
| Mudança de localização sem troca de custodiante | Não exigir por padrão; condicional por risco/procedimento | Evento de mudança de localização | Autoria, instante efetivo e auditoria; assinatura se houver declaração formal de responsabilidade definida. |
| Devolução, destinação final ou descarte | Obrigatória para a decisão/ato formal | Decisão de devolução/destinação e evento de entrega correspondente | Assinatura do responsável autorizado; assinatura externa depende de mecanismo institucional próprio. |
| Retificação formal de dado ou decisão assinada | Obrigatória | Novo ato de retificação ligado ao original | Preservar original, snapshot e assinatura anteriores; registrar motivo, autor, aprovador quando exigido e novo conteúdo. |
| Autorização de exceção administrativa | Obrigatória | Ato de autorização da exceção | Assinatura/manifestação formal da autoridade competente, com escopo, justificativa e prazo/condição. |
| Aprovação de concessão, suspensão ou revogação de competência | Obrigatória como aprovação formal, conforme política de acesso | Ato de autorização da concessão/revogação | Distinguir autoridade aprovadora do administrador técnico que executa. |
| Salvamento intermediário, consulta, listagem e navegação | Não exigir | Não aplicável | Aplicar autenticação, autorização e auditoria conforme sensibilidade; não criar assinatura artificial. |

### 3.1 Regras de interpretação

- “Obrigatória” nesta matriz é uma recomendação de desenho do projeto para atos decisórios/formais; sua adoção operacional depende de aprovação institucional.
- “Condicional” não significa decisão discricionária do operador. A condição deve ser definida em procedimento institucional, por classe de ato e risco.
- A assinatura deve ser proporcional ao efeito do ato, não à quantidade de cliques ou gravações.
- Uma assinatura não deve ser exigida para evidência simples se não houver declaração formal ou responsabilidade adicional a comprovar.
- Em operações compostas, assinar o ato decisório final e seu snapshot, não cada atualização intermediária.

## 4. Vínculo da assinatura com competência e conteúdo — GOV-P06

Recomenda-se adotar as seguintes invariantes:

1. **Alvo e ação permitidos:** a emissão deve validar que o tipo de entidade, identificador e ação correspondem a uma operação assinável prevista na política.
2. **Competência na emissão:** verificar capacidade, escopo, estado do recurso, validade temporal e impedimentos do signatário antes de emitir o desafio/token.
3. **Conteúdo apresentado:** construir o snapshot canônico a partir dos dados efetivos do servidor, contendo o ato, alvo, versão, decisão/declaração, justificativa e referências às evidências relevantes.
4. **Confirmação explícita:** o usuário deve confirmar o conteúdo específico que está assinando; reautenticação isolada sem vinculação clara ao conteúdo não basta para satisfazer a semântica de assinatura.
5. **Competência no consumo:** revalidar identidade, competência, escopo, estado, segregação, alvo, ação, expiração, uso único e correspondência exata do snapshot no momento de efetivar o ato.
6. **Imutabilidade:** persistir o snapshot ou representação recuperável, hash, algoritmo e versão de canonicalização; não permitir alteração silenciosa do conteúdo assinado.
7. **Atomicidade:** consumo da assinatura e operação de negócio devem integrar a mesma transação quando o ato for síncrono. Se houver provedor externo/fluxo assíncrono, modelar estado pendente explícito e impedir efeitos de negócio antes da confirmação.
8. **Revogação antes do consumo:** se a competência do signatário for suspensa/revogada ou o conteúdo/versão mudar antes do consumo, rejeitar o consumo e exigir novo fluxo de assinatura.
9. **Histórico:** cancelamento, expiração, rejeição e retificação devem preservar evidência e autoria; não reutilizar token consumido nem reinterpretar assinaturas legadas.
10. **Replay idempotente:** replay de operação já concluída deve reproduzir o resultado original sem consumir novamente a assinatura nem repetir efeitos. Antes de revelar o snapshot de resposta, aplicar a autorização atual exigida pela API07.
11. **Identidade não fornecida livremente:** o cliente não escolhe arbitrariamente o signatário. A identidade vem da sessão/reautenticação e do mecanismo de assinatura aprovado.

## 5. Conteúdo mínimo do manifesto/snapshot

Para atos que exigem assinatura, preservar de forma recuperável:

- identificador único do ato e tipo de operação;
- entidade/alvo e identificador;
- versão exata do agregado/ato;
- conteúdo decisório/declaratório apresentado ao signatário;
- justificativa e referências às evidências relevantes;
- identidade do signatário e capacidade/escopo considerados;
- instante de assinatura e instante de registro, com timezone inequívoco;
- método/modalidade de assinatura e evidência de confirmação;
- hash e algoritmo;
- versão do esquema/canonicalização;
- estado do ciclo de vida e referências a cancelamento/retificação, sem sobrescrever o original.

Não se deve presumir que os campos atuais de `ElectronicSignature` já cobrem todos esses elementos.

## 6. Compatibilidade com a implementação existente

A inspeção estática REV-LIMS-GOV-001 identificou:

- emissão de assinatura em duas etapas, com reautenticação por senha e token curto de uso único;
- vínculo do token a usuário, entidade, identificador, ação, significado, JTI e expiração;
- consumo com verificação de alvo/ação/expiração/uso prévio e bloqueio da linha;
- possibilidade de vincular snapshot canônico e SHA-256, mas snapshot/hash opcionais no modelo;
- canonicalização versionada no serviço, sem evidência de persistência explícita da versão/algoritmo junto a cada assinatura;
- ausência localizada de fluxo explícito de cancelamento/revogação antes do consumo;
- ausência de evidência de que todas as operações que exigem assinatura executem `bind_record`;
- emissão não demonstra, por si só, autorização específica do signatário para a ação.

**Conclusão:** existe uma base técnica aproveitável, mas não há evidência suficiente para declarar a política GOV-P05/P06 atendida. É necessária futura inspeção por operação e confirmação de migrações/runtime; esta proposta não autoriza testes ou alterações.

## 7. Decisões validadas em revisão pelo responsável pelo projeto

| ID | Recomendação validada em revisão | Limite da validação |
|---|---|---|
| SIG-P01 | Adotar a matriz da seção 3 como regra de desenho: assinatura obrigatória para decisões formais de aceite/recusa, devolução/destinação, retificação formal, exceção e aprovação formal de concessões/revogações; condicional para chegada, conferência, regularização, coordenação e transferência conforme procedimento; não exigir para salvamentos intermediários e consultas. | Não aprova a política institucional nem define signatários por cargo. |
| SIG-P02 | Exigir competência específica e escopo compatível tanto na emissão quanto no consumo da assinatura. | Não define o catálogo institucional de capacidades ou autoridades. |
| SIG-P03 | Exigir snapshot recuperável e imutável, hash/algoritmo/versionamento, alvo/ação/versão explícitos e confirmação do conteúdo apresentado. | Não escolhe modalidade jurídica/tecnológica de assinatura. |
| SIG-P04 | Rejeitar assinatura se a competência for suspensa/revogada, o alvo/ação não corresponder ou o conteúdo/versão mudar antes do consumo. | Prazos, tratamento de contingência e autoridade de revogação dependem de política institucional. |
| SIG-P05 | Consumir assinatura e efetivar o ato atomicamente quando síncrono; em fluxo assíncrono, impedir efeitos antes da confirmação final. | Arquitetura de integração externa depende de escolha institucional e revisão técnica. |
| SIG-P06 | Preservar replay idempotente sem novo consumo/efeito, com autorização atual antes de revelar o resultado. | Deve ser reconciliado com fechamento técnico API06/API07. |

## 8. Definições que dependem de autoridade institucional

Não podem ser decididas apenas pelo responsável do projeto:

1. modalidade e nível de garantia juridicamente/administrativamente aceitos (senha reautenticada, MFA, certificado ou provedor institucional);
2. signatários autorizados por ato e respectivas delegações;
3. atos que procedimentos institucionais tornam obrigatoriamente assináveis, inclusive eventual assinatura bilateral na transferência;
4. tratamento de assinatura de pessoa externa sem conta LIMS;
5. retenção, temporalidade, acesso, exportação e preservação das evidências;
6. contingência por indisponibilidade, assinatura assíncrona e prazo de regularização;
7. autoridade e rito para cancelamento/revogação, substituição e retificação;
8. critérios de segregação adicionais entre conferente, decisor, coordenador, custodiante, signatário e administrador.

## 9. Critérios de fechamento

As recomendações SIG-P01–SIG-P06 foram validadas em revisão pelo responsável pelo projeto em 2026-11-10, nos limites da seção 7. GOV-P05/P06 ainda não podem ser considerados institucional ou tecnicamente fechados. O fechamento integral depende de:

- autoridades, signatários, modalidade e atos obrigatórios estiverem formalizados institucionalmente;
- matriz de assinatura estiver alinhada com API04, API06, API07 e API10;
- alvos e snapshots estiverem definidos para cada operação;
- inspeção técnica por operação confirmar emissão, vinculação, consumo, rollback, revogação e replay;
- compatibilidade com assinaturas e contratos legados estiver demonstrada;
- segurança, privacidade, retenção e auditoria forem revisadas;
- aprovação institucional aplicável estiver registrada.

## 10. Controle de execução

**Realizado:** análise documental consolidada de GOV-P05/GOV-P06 e da proposta API05, com matriz recomendada, invariantes de competência/assinatura e separação entre decisões do projeto e definições institucionais.

**Não realizado:** alterações de código, modelos, banco, migrações, serviços, rotas, frontend, OpenAPI, testes, build, CI ou infraestrutura. Não houve validação runtime ou consulta ao banco.

**Estado:** SIG-P01–SIG-P06 validadas em revisão pelo responsável pelo projeto em 2026-11-10, nos limites da seção 7. GOV-P05/P06 permanecem pendentes de formalização institucional, fechamento técnico e autorização específica de implementação. GOV-P01 e GOV-P04 permanecem validadas em revisão nos limites anteriormente registrados.

## 11. Histórico

| Versão | Data | Alteração |
|---|---|---|
| 0.1 | 2026-11-10 | Consolidação das recomendações de assinatura eletrônica para validação de GOV-P05/GOV-P06, com matriz por ato, competência, snapshot, atomicidade, replay e pendências institucionais. |
| 0.2 | 2026-11-10 | Registro da validação em revisão de SIG-P01–SIG-P06 pelo responsável pelo projeto; formalização institucional, fechamento técnico e autorização de implementação permanecem pendentes. |
