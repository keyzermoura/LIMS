# Matriz de Resolução das Decisões da API — Recebimento e Custódia

**Identificador:** MAT-LIMS-API-001  
**Versão:** 0.1  
**Situação:** Instrumento de análise e encaminhamento; propostas técnicas não aprovadas para implementação  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Data:** 2026-11-09

---

## 1. Objetivo e limites

Consolidar as decisões API01–API12 da especificação de contratos de recebimento e custódia, relacionando cada questão aos documentos afetados, aos impactos no domínio, no modelo relacional e nos contratos HTTP, aos riscos de compatibilidade e ao encaminhamento recomendado.

Esta matriz é **documental e preparatória**. Não altera nem aprova automaticamente as decisões registradas em outros documentos. DEC04 e DEC05 permanecem diretrizes de desenho aprovadas pelo usuário, ainda sujeitas à formalização institucional. Nenhuma proposta desta matriz autoriza alterações em código, modelos SQLAlchemy, banco de dados, migrações Alembic, endpoints, frontend, testes ou infraestrutura.

As decisões deverão ser confirmadas pelos responsáveis funcionais, técnicos e institucionais competentes. Quando dependerem de política institucional ou procedimento laboratorial, a decisão técnica isolada não é suficiente.

## 2. Documentos de referência

- `ESPECIFICACAO_CONTRATOS_API_RECEBIMENTO_CUSTODIA.md` — API-LIMS-REC-CUST-001 v0.1.
- `OPENAPI_CONTRATOS_RECEBIMENTO_CUSTODIA.yaml` — contrato OpenAPI 3.1 v0.1.
- `REVISAO_CONSISTENCIA_API_MODELO_RELACIONAL.md` — REV-LIMS-API-REL-001 v0.1.
- `MODELO_RELACIONAL_PRELIMINAR_LIMS.md` — MOD-REL-001 v0.3.
- `MATRIZ_DECISOES_LIMS.md` — DEC-LIMS-001 v1.2.
- `ESTADOS_E_TRANSICOES_SOLICITACAO_RECEBIMENTO.md` — EST01–EST10.
- `ANALISE_COMPATIBILIDADE_CADEIA_CUSTODIA_DEC04.md` — ANL-LIMS-CUST-001 v0.2.
- `CONTRATO_HISTORICO_UNIFICADO_E_ACEITE.md` — CTR-LIMS-CUST-001 v0.1.
- `PROPOSTA_RESOLUCAO_API01_NOMES_RECURSOS_ROTAS.md` — PROP-LIMS-API01-001 v0.1.
- `PROPOSTA_RESOLUCAO_API06_CONTROLE_CONCORRENCIA.md` — PROP-LIMS-API06-001 v0.1.
- `PROPOSTA_RESOLUCAO_API07_IDEMPOTENCIA.md` — PROP-LIMS-API07-001 v0.1.

## 3. Estados utilizados

| Estado | Significado |
|---|---|
| Pendente | Decisão ainda não tomada pelo responsável competente. |
| Proposta técnica | Existe encaminhamento recomendado, sem aprovação. |
| Aprovada no desenho | Diretriz de domínio aprovada pelo usuário, ainda sujeita à formalização institucional quando aplicável. |
| Aprovada formalmente | Decisão aprovada pela autoridade competente e registrada com evidência. |
| Implementável | Requisitos, contratos, modelo e autorização específica de implementação concluídos. |

**Regra de governança:** nenhuma linha será considerada implementável apenas porque há uma recomendação técnica ou porque o contrato OpenAPI já contém um exemplo.

## 4. Matriz consolidada API01–API12

| ID | Decisão a resolver | Documentos afetados | Impacto no domínio | Impacto relacional | Impacto HTTP/OpenAPI | Risco principal | Responsável pela decisão | Estado |
|---|---|---|---|---|---|---|---|---|
| API01 | Nomes finais de recursos e rotas | API-LIMS-REC-CUST-001; OpenAPI; UI-LIMS-001; matriz de compatibilidade; PROP-LIMS-API01-001 | Define a linguagem pública dos recursos e a separação entre solicitação, recebimento, item e objeto de custódia. | Em regra, não altera cardinalidades; nomes lógicos devem permanecer alinhados sem espelhar mecanicamente tabelas. | Padroniza paths, operações, parâmetros, operationId, tags e códigos de erro; preserva contratos legados. | Divergência entre interface, documentação e endpoints; breaking change por renomeação posterior. | Arquitetura/API e responsável funcional. | Validada pelo responsável pelo projeto em revisão (2026-11-10); conferência runtime pendente — implementação bloqueada |
| API02 | Recebimento formal em comando único ou rascunho + confirmação | API-LIMS-REC-CUST-001; OpenAPI; UI-LIMS-001; estados e transições; MOD-REL-001; PROP-LIMS-API02-001 | Define quando a chegada se torna registro oficial e quando começa a custódia; distingue preparação de formalização. | Comando único favorece transação integral. Rascunho persistente exige estado, autoria, versionamento, expiração e distinção entre dados provisórios e eventos efetivos. | Recomenda comando único para formalizar chegada e salvamento progressivo posterior de conferência, evidências, pendências e decisões; nomes finais e contratos dependem de API01 e decisões relacionadas. | Recebimento parcial/inconsistente, custódia iniciada antes da formalização ou perda de informação de chegada. | Responsável funcional do recebimento, responsável técnico/laboratorial e arquitetura. | Alternativa C validada pelo responsável pelo projeto em revisão (2026-11-10); fechamento contratual e aprovação institucional pendentes — implementação bloqueada |
| API03 | Regra de quantidade, agrupamento e cardinalidade de CustodyObjects | API-LIMS-REC-CUST-001; OpenAPI; MOD-REL-001; DEC05; REV-LIMS-API-REL-001; PROP-LIMS-API03-001 | Define quando material homogêneo pode ser agrupado e quando unidades exigem decisões, resultados ou destinações independentes. | Define quantity, unidade, vínculos com ReceiptItem e regra de zero a vários objetos; deve preservar DEC05 (ItemRecebimento → 0..N ObjetosCustodia; objeto → no máximo uma DeviceSample). | Validação condicional de PRESENTED/NOT_PRESENTED, soma de quantidades e conteúdo de cada objeto; quantidade persistida não nula. | Perda de rastreabilidade individual ou criação de amostras em granularidade incompatível com o ensaio. | Responsável técnico/laboratorial, responsável funcional e arquitetura de dados. | Regras gerais validadas pelo responsável pelo projeto em revisão (2026-11-10); detalhes operacionais e aprovação institucional pendentes — implementação bloqueada |
| API04 | Catálogo de eventos, autoria e semântica temporal da custódia | API-LIMS-REC-CUST-001; OpenAPI; MOD-REL-001; ANL-LIMS-CUST-001; CTR-LIMS-CUST-001; REV-LIMS-API-REL-001; PROP-LIMS-API04-001 | Define evento de chegada, transferência, mudança de localização, retificação, devolução e encerramento; distingue ator registrador de custodiante. | Avalia extensão da ChainOfCustody existente para event_type, recorded_by_id e timestamps sem criar tabela paralela; mantém alvo XOR legado/novo conforme proposta. | Define campos obrigatórios e enums para eventos, além da representação de occurred_at, recorded_at, from/to custodian e localizações. | Evento inicial atribuído ao usuário do aceite, cronologia falsa, autoria não auditável ou ruptura de histórico legado. | Responsável técnico/laboratorial, segurança/auditoria e arquitetura. | Catálogo de sete eventos e distinção occurred_at/recorded_at/recorded_by validados pelo responsável pelo projeto em revisão (2026-11-10); detalhes operacionais, compatibilidade técnica e aprovação institucional pendentes — implementação bloqueada |
| API05 | Assinatura eletrônica exigida por operação e alvo assinado | API-LIMS-REC-CUST-001; OpenAPI; DEC09; EST07; MOD-REL-001; CTR-LIMS-CUST-001 | Determina quais atos exigem assinatura e se a assinatura recai sobre recebimento, decisão, transferência, aceite ou outro ato. | Define vínculo de ElectronicSignature, snapshot/conteúdo assinado e momento de geração; não presumir que autenticação ou AuditLog equivalem a assinatura. | Define campos, pré-condições, erros SIGNATURE_REQUIRED e comportamento de tokens/assinaturas no novo fluxo. | Assinatura vinculada a DeviceSample inexistente, assinatura sem conteúdo estável ou ausência de assinatura obrigatória. | Autoridade institucional, responsável funcional e segurança da informação. | Pendente |
| API06 | Mecanismo único de concorrência: expected_version no corpo | API-LIMS-REC-CUST-001; OpenAPI; REV-LIMS-API-REL-001; contratos de interface; PROP-LIMS-API06-001 | Define como impedir atualização baseada em estado desatualizado em recebimento, conferência, transferência e aceite. | Recomenda versão monotônica por agregado mutável; recebimento inicial usa bloqueio transacional + unicidade + idempotência; transferência/aceite protegem CustodyObject. | Padroniza expected_version nos comandos novos, version nas respostas e 409 VERSION_CONFLICT; remove If-Match/412/428 dos contratos novos. | Contrato contraditório, perda de atualização ou versão associada ao agregado errado; idempotência/replay precisa ser coordenada com API07. | Arquitetura/API e backend. | Proposta técnica elaborada; validação pendente — bloqueadora |
| API07 | Política geral de Idempotency-Key | API-LIMS-REC-CUST-001; OpenAPI; REV-LIMS-API-REL-001; MOD-REL-001; PROP-LIMS-API07-001 | Define identidade de uma tentativa lógica e comportamento de repetição após timeout ou falha de comunicação. | Recomenda persistência transacional de chave, hash da requisição e resultado; escopo por principal + operação/rota + recurso-alvo; unicidade persistente; snapshot de replay e marcador de retenção. | Chave obrigatória em recebimento, transferência, aceite e comandos críticos não repetíveis; mesmo hash = replay; hash divergente = 409 IDEMPOTENCY_KEY_REUSED; processamento concorrente = 409 IDEMPOTENCY_REQUEST_IN_PROGRESS; janela preliminar de replay de 7 dias, sujeita à validação institucional. | Duplicidade de recebimentos/eventos/amostras, replay de resposta incompatível, exposição de resposta a usuário não autorizado ou reutilização após expiração. | Arquitetura/API, backend, segurança e responsável funcional. | Proposta técnica elaborada; validação pendente — bloqueadora |
| API08 | Payload mínimo e regras de identidade de DeviceSample por classe de material | API-LIMS-REC-CUST-001; OpenAPI; MOD-REL-001; INV-TEC-001; REV-LIMS-API-REL-001; DEC10 | Define quais identificadores são aplicáveis a agulhas, seringas, equipos, cateteres e outros materiais; serial pode não existir ou não ser aplicável. | Confronta obrigatoriedade atual de serial_number, lot_number, manufacturer e commercial_name e unique composta; exige decisão explícita antes de alterar constraints. | Definir schemas por classe ou payload comum com campos condicionais; resolver storage_location como dado próprio ou projeção de custódia. | Rejeição de materiais legítimos, duplicidade indevida ou alteração incompatível de dados legados. | Responsável técnico/laboratorial, cadastro de materiais e arquitetura de dados. | Pendente — bloqueadora |
| API09 | Resposta HTTP e comportamento semântico quando objeto já foi aceito | API-LIMS-REC-CUST-001; OpenAPI; REV-LIMS-API-REL-001 | Define se repetição do aceite retorna o recurso existente, resposta idempotente ou conflito de estado, sem criar segunda amostra. | Exige unicidade do vínculo CustodyObject–DeviceSample e proteção transacional contra concorrência. | Definir status e corpo para primeira aceitação, replay da mesma operação, chave diferente e objeto já aceito por outra operação. | Cliente interpreta conflito como falha e repete; criação duplicada ou ocultação de amostra já criada. | Responsável funcional e arquitetura/API. | Pendente |
| API10 | Escopos de autorização e segregação de funções | API-LIMS-REC-CUST-001; OpenAPI; EST01–EST03; EST10; DEC09; MOD-REL-001 | Define quem cadastra, recebe, confere, corrige, valida, aceita, transfere e encerra custódia; decide quando ator distinto é obrigatório. | Pode exigir FKs de autoria, validações de ator distinto, registros de aprovação e constraints/serviços transacionais. | Define permissões por operação, 401/403, pré-condições e identidade do ator obtida da sessão, nunca livremente do payload. | Autoaprovação indevida, segregação inconsistente e autorização baseada apenas na interface. | Gestão institucional, responsável funcional, segurança e arquitetura. | Pendente — bloqueadora |
| API11 | Paginação, ordenação estável e snapshot do histórico | API-LIMS-REC-CUST-001; OpenAPI; CTR-LIMS-CUST-001; REV-LIMS-API-REL-001 | Define como o usuário percorre uma cadeia append-only enquanto novos eventos podem ser registrados. | Requer índices compatíveis e chave de ordenação estável; snapshot pode exigir cursor que carregue limite temporal/identificador. | Definir cursor opaco, limite, ordenação determinística, filtros e semântica de snapshot; evitar offset instável em histórico crescente. | Eventos omitidos ou repetidos entre páginas e histórico não reproduzível. | Arquitetura/API e backend. | Pendente |
| API12 | Datas retroativas, lançamento tardio, offset e fuso institucional | API-LIMS-REC-CUST-001; OpenAPI; MOD-REL-001; REV-LIMS-API-REL-001; EST08 | Distingue instante efetivo do fato, instante de registro e justificativa de lançamento tardio; define limites e autoridade para retroagir. | Exige timestamps com timezone, armazenamento consistente e autoria/justificativa quando houver registro tardio; sem backfill inferido. | Definir formato ISO 8601 com offset, normalização UTC, validação de datas futuras/passadas e erros específicos. | Cronologia inconsistente, perda do fuso original ou alteração silenciosa da data de chegada. | Responsável institucional pelo processo, responsável técnico e arquitetura. | Pendente — bloqueadora |

## 5. Dependências e ordem recomendada de resolução

A ordem abaixo minimiza retrabalho e respeita as dependências de domínio:

| Ordem | Decisões | Justificativa | Saída documental esperada |
|---|---|---|---|
| 1 | API03 | A granularidade dos objetos condiciona o recebimento, a custódia e a criação de amostras. | Regra de quantidade, agrupamento, individualização e exemplos por material. |
| 2 | API04 + API12 | O evento inicial e a política temporal devem ser definidos conjuntamente para preservar chegada, autoria e cronologia. | Catálogo de eventos e contrato temporal/autoria. |
| 3 | API02 + API01 | Com a semântica da chegada definida, fechar comando de formalização e nomes públicos. | Fluxo HTTP de recebimento e nomenclatura estável. (PROP-LIMS-API01-001 elaborada; validação pendente.) |
| 4 | API06 + API07 + API09 | Concorrência, idempotência e repetição de aceite formam um conjunto de confiabilidade transacional. | Política de versão (API06) e chave/replay (API07) propostas; resposta para nova chave em objeto já aceito permanece dependente de API09. |
| 5 | API08 | O payload da amostra depende da identidade e granularidade de material definidas. | Schemas e regras condicionais por classe de dispositivo. |
| 6 | API05 + API10 | Assinatura, autorização e segregação devem ser coerentes por ato e perfil. | Matriz operação × perfil × assinatura × validação. |
| 7 | API11 | Fechar paginação depois de estabilizar o catálogo de eventos e sua ordenação. | Contrato de histórico paginado e snapshot. |
| 8 | Consolidação | Reconciliar todos os documentos e só então avaliar prontidão para revisão formal. | API v0.2, OpenAPI coerente e modelo relacional atualizado como propostas. |

A sequência é uma recomendação de trabalho, não uma aprovação das decisões nem uma autorização para implementação.

## 6. Regras de compatibilidade que devem permanecer invariantes

1. Preservar as rotas legadas e seus contratos efetivos até decisão formal de descontinuação; não alterar status ou payload por suposição.
2. Não vincular eventos legados a CustodyObject sem evidência confiável.
3. Manter uma única cadeia cronológica, sem tabela paralela de eventos de custódia.
4. Para eventos novos, o alvo de custódia é CustodyObject, inclusive depois da criação da DeviceSample, conforme DEC04.
5. Preservar DEC05: ItemRecebimento pode originar zero ou vários objetos; objeto origina no máximo uma amostra operacional.
6. Item NOT_PRESENTED não cria CustodyObject, evento inicial ou DeviceSample.
7. A criação da DeviceSample deve preservar o instante efetivo da chegada e o recebedor físico original; o usuário do aceite não os substitui.
8. Aceite, criação da amostra, vínculo e identificador devem ser atômicos e protegidos contra concorrência e repetição.
9. Não inferir serial, lote, fabricante, autoria, timestamp ou associação histórica ausentes.
10. Não remover ou tornar obrigatórios/nullable campos legados sem análise de dados, contratos consumidores e plano de compatibilidade.

## 7. Critérios de fechamento da matriz

Uma decisão poderá mudar de Pendente para Aprovada no desenho somente quando:
- a alternativa escolhida e as alternativas rejeitadas estiverem registradas;
- a justificativa e os exemplos operacionais forem suficientes;
- os impactos no domínio, modelo relacional, API e interface estiverem descritos;
- os riscos de compatibilidade e a estratégia de transição estiverem identificados;
- o responsável pela decisão e a evidência de aprovação estiverem registrados.

A especificação da API e o OpenAPI somente poderão ser atualizados após resolução das decisões que afetam seus contratos. O modelo relacional deverá ser atualizado em coordenação com a API, sem antecipar alterações físicas.

A classificação **Implementável** exige, adicionalmente, revisão técnica, aprovação institucional aplicável e autorização específica do usuário para iniciar a implementação. Essa matriz, isoladamente, não satisfaz esses requisitos.

## 8. Pendências que não podem ser presumidas

- A política institucional de assinatura eletrônica e os atos que a exigem.
- A autoridade que pode autorizar exceções, retificações e lançamentos retroativos.
- A segregação de funções e os perfis concretos do processo.
- Os checklists, critérios impeditivos/saneáveis/informativos e classes de materiais.
- A regra técnica de agrupamento por tipo de dispositivo e método de ensaio.
- A política de retenção de chaves idempotentes e dados de auditoria.
- O comportamento runtime exato das rotas legadas, que deve ser confirmado por inspeção do código/contratos existentes, não por inferência do OpenAPI proposto.

## 9. Controle de execução

**Atividade realizada:** consolidação documental das decisões API01–API12 e de seus impactos e dependências; elaboração das propostas API01 (nomenclatura de recursos/rotas), API06 (controle de concorrência) e API07 (idempotência); registro das validações de API01 e da Alternativa C da API02 pelo responsável pelo projeto em revisão, mantendo as respectivas dependências técnicas.

**Não realizado:** alterações em código, modelos, banco de dados, migrações, endpoints, frontend, OpenAPI existente, testes, build, CI ou infraestrutura.

**Situação após esta atualização:** API01 foi validada como diretriz de nomenclatura, com conferência runtime pendente. A Alternativa C da API02 foi validada, mas seu fechamento contratual depende de API03/API04/API06/API07, dados mínimos e revisão da interface/estados. API03–API12 permanecem nos estados anteriormente registrados. DEC04/DEC05 permanecem diretrizes de domínio aprovadas pelo usuário nos limites registrados em DEC-LIMS-001. Nenhuma aprovação institucional ou autorização de implementação é presumida.

## 10. Histórico de alterações

| Versão | Data | Alteração |
|---|---|---|
| 0.1 | 2026-11-09 | Criação da matriz de resolução API01–API12, com impactos, riscos, responsáveis, estados e sequência recomendada. |
| 0.2 | 2026-11-10 | Inclusão da proposta PROP-LIMS-API01-001 e atualização do estado documental da decisão API01. |
| 0.3 | 2026-11-10 | Inclusão da proposta PROP-LIMS-API06-001 e atualização do estado documental da decisão API06. |
| 0.4 | 2026-11-10 | Inclusão da proposta PROP-LIMS-API07-001 e atualização do estado documental da decisão API07. |
| 0.5 | 2026-11-10 | Registro da validação de API01 pelo responsável pelo projeto em revisão; conferência runtime e implementação permanecem pendentes. |
| 0.6 | 2026-11-10 | Registro da validação da Alternativa C da API02 pelo responsável pelo projeto em revisão; fechamento contratual e aprovação institucional permanecem pendentes. |
