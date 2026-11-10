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
