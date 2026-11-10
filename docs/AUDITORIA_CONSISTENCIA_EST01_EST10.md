# Auditoria de Consistência das Decisões EST01–EST10

**Identificador:** AUD-LIMS-001  
**Versão:** 1.0  
**Data:** 2026-11-10  
**Repositório:** keyzermoura/LIMS  
**Escopo:** consistência entre EST01–EST10, máquina de estados EST-REC-001 e modelo de domínio MOD-DOM-001.  
**Resultado:** achados documentais e funcionais tratados na consolidação EST-REC-001 v1.4 e MOD-DOM-001 v0.4.  
**Situação de implementação:** não autorizada; Gate G0 permanece obrigatório.

---

## 1. Objetivo e método

Verificar contradições, lacunas, duplicidades e regras preliminares que permaneceram nos documentos após a aprovação funcional EST01–EST10 e do modelo M0.2. A auditoria é documental e funcional; não representa validação jurídica, teste de software, aprovação institucional de cargos nem autorização de implementação.

Foram examinadas as relações:
- EST01 × EST10 — perfis, permissões e segregação;
- EST02 × EST03 — recebimento, conferência e validação independente;
- EST03 × EST06 — autoridade da coordenação e critérios impeditivos;
- EST04 × EST05 — custódia, recusas e itens não apresentados;
- EST07 × EST08 — assinatura e retificação;
- EST09 × EST04 — prazo de pendência e manutenção da custódia;
- EST01–EST10 × M0.2 — granularidade e cardinalidades.

## 2. Sumário executivo

As decisões EST01–EST10 são funcionalmente compatíveis entre si e com as cardinalidades aprovadas no M0.2. Os principais problemas identificados estavam em descrições preliminares que não haviam sido atualizadas após decisões posteriores: matriz de perfis antiga, decisão apenas no nível do item, estados incompletos de pendência, falta de separação explícita entre assinatura e validação independente e descrição insuficiente do estado atual versus histórico de custódia.

As correções foram feitas por consolidação documental, sem reabrir nem alterar o conteúdo das decisões aprovadas.

## 3. Registro dos achados

| ID | Prioridade | Achado | Tratamento realizado | Evidência |
|---|---|---|---|---|
| AUD01 | Alta | Matriz antiga usava perfis Operador/Recebedor, Conferente/Técnico, Coordenador e Administrador, incompatíveis com EST01. | Substituída por matriz dos cinco perfis aprovados e permissões por operação. | EST-REC-001 v1.4, seção 5; EST01 seção 24. |
| AUD02 | Alta | Acumulação de perfis não distinguia permissão operacional, competência, validação independente e assinatura. | Criada matriz e regras separando os quatro controles; autoaprovação bloqueada quando independência for obrigatória. | EST-REC-001 v1.4, seções 5.1 e 25.2. |
| AUD03 | Crítica | Decisão no nível do ItemRecebimento poderia ocultar resultados divergentes entre objetos. | ObjetoCustodia adotado como nível decisório quando houver possibilidade de desfechos independentes; item passa a consolidar. | EST-REC-001 v1.4, seções 3.6 e 25.1; MOD-DOM-001 v0.4, seção 15.3. |
| AUD04 | Alta | Estados de pendência preliminares estavam incompletos e divergiam da EST09. | Estados consolidados: PENDENTE, EM_REGULARIZACAO, AGUARDANDO_REAVALIACAO, REGULARIZADA, PRAZO_VENCIDO, NAO_REGULARIZAVEL e CANCELADA. | EST-REC-001 v1.4, seção 3.5 e 25.3. |
| AUD05 | Alta | NAO_REGULARIZAVEL poderia ser interpretado como recusa automática. | Explicitado que é desfecho da pendência, não decisão automática de recusa; decisão de material permanece separada. | EST-REC-001 v1.4, seções 3.5 e 25.3. |
| AUD06 | Alta | Regra de conclusão com itens não apresentados não estava uniformemente refletida nas transições. | Critérios EST05 incorporados à transição agregada do recebimento e aos bloqueios. | EST-REC-001 v1.4, seções 4.2 e 25.7. |
| AUD07 | Alta | Estado atual de custódia não estava claramente separado do histórico de transferências. | Estado atual definido como projeção do último evento confirmado; eventos e responsáveis anteriores preservados. | EST-REC-001 v1.4, seções 3.8 e 25.4; MOD-DOM-001 v0.4, seção 15.4. |
| AUD08 | Alta | Assinatura eletrônica poderia ser confundida com validação independente. | Definidos como controles distintos; assinatura não substitui validação e nem toda assinatura exige segundo signatário. | EST-REC-001 v1.4, seções 4.4 e 25.2; MOD-DOM-001 v0.4, seção 15.6. |
| AUD09 | Média | Transições não explicitavam consistentemente granularidade, responsável, pré-condições e bloqueios. | Máquina de estados detalhada por entidade, com origem/destino, responsável, pré-condições, bloqueios e controles de auditoria; critérios funcionais CA01–CA24 acrescentados. | EST-REC-001 v1.4, seções 26–27. |
| AUD10 | Alta | Consolidação por ItemRecebimento poderia perder decisões individuais de ObjetosCustodia. | Definida regra de consolidação, PARCIALMENTE_DECIDIDO e independência dos destinos/decisões. | EST-REC-001 v1.4, seção 25.1; MOD-DOM-001 v0.4, seção 15.3. |
| AUD11 | Alta | Vínculo entre aceite, criação de amostra e continuidade de custódia precisava de condições explícitas. | Reforçados aceite final, pendências/validações resolvidas, atomicidade, idempotência, vínculo 1:0..1 e evento de continuidade da custódia. | EST-REC-001 v1.4, seção 25.5; MOD-DOM-001 v0.4, seção 15.5. |
| AUD12 | Alta | Retificação não estava completamente conectada à avaliação de impacto após criação de amostra/ensaios/laudos. | Consolidado novo ato vinculado ao original, sem sobrescrita, com avaliação de impacto e sem exclusão automática. | EST-REC-001 v1.4, seção 25.6; EST08 seção 21; MOD-DOM-001 v0.4, seção 15.7. |

## 4. Verificação cruzada das decisões

| Relação | Resultado da verificação |
|---|---|
| EST01 × EST10 | Compatíveis: perfis acumuláveis conforme autorização, sem autoaprovação em atos sujeitos a revisão independente. |
| EST02 × EST03 | Compatíveis: mesmo servidor pode receber e conferir, mas não pode validar a própria decisão quando a coordenação for obrigatória. |
| EST03 × EST06 | Compatíveis: coordenação revisa exceções e recusas, mas não dispensa critério impeditivo nem altera classificação pontualmente. |
| EST04 × EST05 | Compatíveis: item ausente não gera custódia; item recusado permanece sob custódia até destinação efetiva. |
| EST07 × EST08 | Compatíveis: retificação exige novo ato, preservação do original e assinatura formal; validação independente permanece distinta. |
| EST09 × EST04 | Compatíveis: vencimento ou encerramento da pendência não encerra custódia. |
| EST01–EST10 × M0.2 | Compatíveis: ObjetoCustodia preserva granularidade pré-amostra; amostra só surge após aceite e validações obrigatórias. |

## 5. Pontos institucionais ainda pendentes

A auditoria não inventa nem substitui decisões institucionais ainda necessárias:

1. Correspondência entre perfis, cargos, unidades, servidores e substitutos autorizados.
2. Autoridade competente para conceder, revisar e revogar permissões.
3. Prazos concretos por tipo de pendência, antecedência de alertas e canais oficiais de comunicação.
4. Checklists por categoria de dispositivo, com critérios E/S/I, versão e aprovação técnica.
5. Definição jurídica e tecnológica do mecanismo de assinatura eletrônica.
6. Procedimento de guarda, prazos de permanência e destinações autorizadas.
7. Regras de agrupamento de materiais e amostragem por categoria, fundamentadas nos procedimentos técnicos.
8. Critérios e responsáveis para avaliação de impacto em amostras, ensaios e laudos após retificação.

## 6. Limites e riscos residuais

- A matriz de permissões é funcional; não equivale à matriz institucional formal de competências.
- As regras descrevem comportamento esperado, ainda não demonstrado por testes de software.
- A segurança e imutabilidade da auditoria dependem de arquitetura, controles técnicos e operação a serem avaliados em etapa própria.
- Atomicidade e idempotência da criação de amostra são requisitos; ainda não foram implementados nem testados.
- O mecanismo de assinatura não foi escolhido nem validado juridicamente.
- Não foi realizada migração ou associação de dados legados; vínculos sem evidência confiável continuam proibidos.
- Os critérios CA01–CA24 ainda precisam ser convertidos em testes automatizados e executados; a máquina de estados funcional por entidade está documentada na seção 26.

## 7. Conclusão

Os 12 achados foram tratados no nível documental definido para esta etapa. Não foi identificada necessidade de reabrir as decisões funcionais EST01–EST10 nem de alterar as cardinalidades aprovadas no M0.2.

A auditoria documental pode ser considerada concluída para fins de preparação da próxima etapa, condicionada à revisão do responsável funcional. A próxima etapa recomendada é revisar os critérios CA01–CA24 com casos reais anonimizados e, depois, realizar a avaliação multidisciplinar de arquitetura, segurança e prontidão para o Gate G0.

**Esta conclusão não representa aprovação do Gate G0 e não autoriza implementação.**

## 8. Histórico

| Versão | Data | Descrição |
|---|---|---|
| 1.0 | 2026-11-10 | Primeira auditoria cruzada EST01–EST10 × M0.2; registro e tratamento documental dos achados AUD01–AUD12. |


## 9. Segunda rodada — revisão multidisciplinar da máquina de estados e CA01–CA24

**Data:** 2026-11-10  
**Fontes adicionais:** avaliação multidisciplinar compartilhada em 2026-11-09/10 e revisão das seções 26–27 do EST-REC-001 v1.4.  
**Resultado:** identificadas lacunas que não invalidam as decisões EST01–EST10 nem as cardinalidades M0.2, mas exigem complementação antes da aprovação do Gate G0.

### 9.1 Novos achados

| ID | Prioridade | Achado | Recomendação/Tratamento documental |
|---|---|---|---|
| AUD13 | Crítica | Escopo do SOLICITANTE não possuía critério explícito de isolamento em listagem, detalhe e evidências. | Definir autorização por vínculo do registro no servidor e acrescentar CA25. |
| AUD14 | Alta | Quantidade declarada, quantidade apresentada e quantidade representada pelo ObjetoCustodia não estavam separadas. | Preservar dimensões distintas e acrescentar CA26–CA27. |
| AUD15 | Alta | Tempo do fato e tempo do registro não estavam separados em todos os eventos. | Definir occurred_at, recorded_at e recorded_by; acrescentar CA28. |
| AUD16 | Alta | Taxonomia de eventos de custódia não distinguia localização, transferência, devolução, destinação e encerramento. | Adotar taxonomia conceitual RECEIPT/TRANSFER/LOCATION_CHANGE/RETURN/DISPOSITION/CLOSURE/CORRECTION; acrescentar CA29–CA30. |
| AUD17 | Alta | Protocolo institucional, accession e QR não tinham semântica e ciclo de vida explicitados. | Separar finalidade, entidade, unicidade e momento de atribuição; acrescentar CA37. |
| AUD18 | Crítica | Atomicidade/idempotência e concorrência estavam descritas como princípios, sem contrato de conflito e cenários suficientes. | Especificar chave persistida, hash, replay, conflito em andamento e expected_version; acrescentar CA31–CA33. |
| AUD19 | Alta | Consulta histórica/paginação não possuía requisito de ordenação estável e continuidade. | Definir paginação determinística e acrescentar CA34. |
| AUD20 | Alta | Evidências binárias não tinham requisito de integridade, metadados, armazenamento e retenção suficientemente descrito. | Definir metadados/hash/acesso/retenção e acrescentar CA35; tecnologia permanece pendente. |
| AUD21 | Alta | Transição dos registros legados para o novo domínio poderia gerar vínculos presumidos ou quebra de compatibilidade. | Exigir migração aditiva, reconciliação auditável e não associação sem evidência; acrescentar CA36. |
| AUD22 | Alta | Recomendações técnicas da avaliação externa não estavam separadas por horizonte e criticidade. | Classificar rate limiting distribuído, WORM/ancoragem externa, MFA/SSO, object storage, E2E e paridade PostgreSQL como itens de arquitetura/segurança e plano de testes, não como autorização imediata de implementação. |

### 9.2 Revisão individual dos CA01–CA24

A revisão constatou que os 24 critérios são coerentes como base funcional, mas não formam cobertura suficiente para o Gate G0 sem os complementos CA25–CA37. Os principais pontos são:

- CA01–CA03: adequados em princípio; CA01 deve cobrir autorização por escopo do registro e CA03 deve ser testado também para acumulação de perfis.
- CA04–CA06: coerentes com EST06; falta validar combinação de critérios E/S/I, justificativa NAO_APLICAVEL e checklist versionado em cenários compostos.
- CA07–CA08: coerentes; explicitar que ausência não gera ObjetoCustodia e que quantidades divergentes não são sobrescritas.
- CA09–CA11: coerentes; faltava distinguir LOCATION_CHANGE de TRANSFER e eventos de RETURN/DISPOSITION/CLOSURE.
- CA12–CA13: coerentes; vencimento permanece indicador de controle e evidência recebida exige reavaliação.
- CA14–CA15: coerentes; a validação deve ser independente, assinada e limitada à competência, sem dispensar critério impeditivo.
- CA16–CA17: insuficientes para demonstrar idempotência robusta; acrescentar replay, mesma chave com payload distinto, requisição em andamento e concorrência.
- CA18: adequado; complementar com quantidades e agrupamento de objetos.
- CA19–CA20: coerentes; exigir trilha completa da retificação e avaliação de impacto antes de qualquer efeito operacional.
- CA21–CA22: adequados como controles de aplicação; a proteção contra administrador privilegiado de banco exige defesa arquitetural adicional, não apenas teste de permissão.
- CA23: coerente; deve preservar occurred_at e recorded_at e impedir retroatividade fictícia.
- CA24: coerente; complementar com versão de regra/checklist e prova de reprodutibilidade.

### 9.3 Recomendações técnicas separadas por horizonte

**Necessárias para especificação do Gate G0:**
- estratégia de migração aditiva e reconciliação de legado;
- contratos de idempotência e concorrência otimista;
- escopo de autorização do solicitante;
- evidências binárias com integridade e política de retenção;
- paginação/consulta histórica;
- testes automatizados dos critérios, incluindo concorrência.

**Necessárias para arquitetura de produção, com decisão institucional:**
- rate limiting distribuído (Redis ou camada de ingress/reverse proxy), pois o limitador em memória não coordena múltiplos workers;
- proteção da trilha de auditoria contra administrador privilegiado, avaliando ancoragem periódica externa/WORM;
- MFA e futura integração SSO/IdP (OIDC/SAML), desacoplando assinatura da verificação direta de senha;
- armazenamento de anexos em object storage compatível, como MinIO/S3, sem fixar fornecedor antes da avaliação;
- testes E2E do fluxo de autenticação, recebimento, assinatura e auditoria;
- testes de integridade/concorrência executados em PostgreSQL real no CI, não apenas SQLite.

### 9.4 Cenários operacionais mínimos para validação com o SEFI

1. Recebimento integral com conferência e aceite de todos os objetos.
2. Recebimento parcial com um item não apresentado e conclusão administrativa válida.
3. Divergência entre quantidade declarada e apresentada.
4. Um item com dois objetos, sendo um aceito e outro recusado.
5. Pendência saneável, comunicação formal, vencimento, prorrogação e reavaliação.
6. Recusa com permanência em custódia e posterior devolução/destinação.
7. Transferência entre responsáveis e mudança de localização sem transferência.
8. Retificação de ausência ou decisão após criação de amostra, com avaliação de impacto.
9. Reenvio concorrente de criação de recebimento/amostra e alteração com versão obsoleta.
10. Tentativa de solicitante acessar solicitação/evidência de terceiro.
11. Consulta paginada do histórico durante novas movimentações.
12. Recebimento de material após conclusão anterior como não apresentado, sem retroatividade.

### 9.5 Conclusão da segunda rodada

A máquina de estados v1.4 e CA01–CA24 são uma base consistente, porém **a revisão multidisciplinar não recomenda declarar prontidão funcional completa para o Gate G0 antes de incorporar e validar CA25–CA37, os cenários operacionais e os contratos técnicos pendentes**. As decisões EST01–EST10 e cardinalidades M0.2 não foram reabertas nem alteradas.

A avaliação anterior descreve pontos fortes do código existente e riscos arquiteturais, mas não foi executada nesta rodada uma auditoria direta do código, dos testes ou da infraestrutura. Portanto, tais pontos permanecem como hipóteses/itens a verificar na etapa de arquitetura e segurança; não são declarados como defeitos confirmados por inspeção independente.

**Não houve alteração de código, schema, API, frontend, pipeline ou infraestrutura. Gate G0 permanece não aprovado e implementação não autorizada.**

## 10. Histórico

| Versão | Data | Descrição |
|---|---|---|
| 1.1 | 2026-11-10 | Segunda rodada multidisciplinar; achados AUD13–AUD22; revisão CA01–CA24; cenários operacionais e complementos CA25–CA37. |
