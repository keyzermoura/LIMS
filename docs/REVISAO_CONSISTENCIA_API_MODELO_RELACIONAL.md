# Revisão de Consistência — Contratos de Recebimento e Custódia

**Identificador:** REV-LIMS-API-REL-001  
**Versão:** 0.1  
**Situação:** Análise documental preliminar; não aprovada para implementação  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Data:** 2026-11-09

---

## 1. Objetivo e escopo

Avaliar a consistência entre:

1. `ESPECIFICACAO_CONTRATOS_API_RECEBIMENTO_CUSTODIA.md` — contrato funcional HTTP;
2. `OPENAPI_CONTRATOS_RECEBIMENTO_CUSTODIA.yaml` — representação OpenAPI 3.1;
3. `MODELO_RELACIONAL_PRELIMINAR_LIMS.md` — modelo lógico de dados;
4. `ANALISE_COMPATIBILIDADE_CADEIA_CUSTODIA_DEC04.md` — compatibilidade da cadeia legada;
5. `ESTADOS_E_TRANSICOES_SOLICITACAO_RECEBIMENTO.md` — estados e regras do processo.

A revisão é estática e documental. Não foram executados testes, validação automática do YAML, build, CI, inspeção do banco em execução ou alteração de código/schema/migração/API/frontend.

## 2. Conclusão executiva

A direção arquitetural geral é coerente: recebimento e custódia existem antes da amostra operacional; o objeto de custódia permanece como alvo dos eventos após a criação da amostra; a cadeia legada baseada em `DeviceSample` deve continuar consultável; e o aceite deve criar a amostra de forma atômica, preservando o instante e o recebedor físicos originais.

Entretanto, o OpenAPI 0.1 ainda não deve ser tratado como contrato pronto para implementação. Foram identificadas lacunas de representação e decisões em aberto, principalmente:

- cardinalidade e validação condicional dos itens/quantidades/objetos;
- campos obrigatórios e semântica do evento inicial de custódia;
- conflito de representação entre `If-Match` e `expected_version`;
- divergência entre a rota de transferência legada documentada e a resposta HTTP indicada;
- cobertura incompleta das rotas legadas;
- regras de autoria, timestamps e assinatura ainda não fechadas;
- detalhes de paginação/snapshot e idempotência não definidos.

Não foi identificada contradição que invalide o princípio central DEC04/DEC05. As diferenças abaixo exigem correção documental ou decisão antes de congelar o contrato.

## 3. Matriz de achados

### REV01 — Quantidade e apresentação do item

**Classificação:** Alta — contrato incompleto.

O modelo relacional define `quantity_presented` como condicional: obrigatória quando apresentado e nula/zero conforme regra quando não apresentado. O OpenAPI exige `presented_quantity` numérico e não expressa a condição por estado. Assim, o schema aceita combinações semanticamente inválidas, como item `NOT_PRESENTED` com quantidade positiva ou item `PRESENTED` com quantidade zero.

**Recomendação:**
- definir formalmente a regra de quantidade ausente/zero para `NOT_PRESENTED`;
- exigir quantidade estritamente positiva para `PRESENTED`, se compatível com as unidades e procedimentos;
- aplicar validação condicional no servidor; documentar com `oneOf`/schemas condicionais ou descrição normativa clara;
- validar que a soma das quantidades representadas pelos objetos corresponda à quantidade apresentada, quando a unidade e o agrupamento permitirem essa comparação.

### REV02 — Cardinalidade e completude dos ReceiptItems

**Classificação:** Alta — regra de domínio não expressa integralmente no schema.

O modelo lógico determina um `ReceiptItem` por `SolicitationItem` no recebimento principal, com `solicitation_item_id` único. A especificação funcional determina que todos os itens declarados estejam representados, cada um exatamente uma vez. O OpenAPI recebe uma lista de itens, mas não consegue, sozinho, assegurar que:
- todos os itens da solicitação foram incluídos;
- nenhum item alheio à solicitação foi incluído;
- não há `solicitation_item_id` duplicado;
- cada item não apresentado tenha lista de objetos vazia;
- cada item apresentado tenha ao menos um objeto, conforme regra final de granularidade.

**Recomendação:** manter essas condições como validações de domínio transacionais no servidor e enumerá-las explicitamente no contrato. Adicionar restrição de unicidade por array quando suportada pelo validador escolhido; não depender apenas do schema para integridade.

### REV03 — Evento inicial de custódia

**Classificação:** Alta — payload/semântica incompletos.

O POST de recebimento propõe criar `CustodyObject` e eventos iniciais de custódia na mesma transação. O schema `CustodyObjectCreate` contém quantidade, agrupamento, localização inicial, selo e notas, mas não declara explicitamente o custodiante inicial, o tipo do evento, o instante efetivo nem a autoria do registro.

O modelo lógico exige `Receipt.received_by_id` e o modelo de estados determina que a custódia começa na chegada física. A análise de compatibilidade também identifica `event_type` e `recorded_by_id` como extensões candidatas ainda ausentes no schema legado.

**Recomendação:**
- definir se o custodiante inicial será sempre o recebedor físico do Receipt;
- se sim, declarar isso como regra normativa e retornar a referência no resultado;
- definir se o evento inicial usa `occurred_at = Receipt.arrived_at` e `recorded_at = instante de persistência`;
- definir como `event_type` e `recorded_by_id` serão representados;
- não permitir que o usuário que posteriormente executa o aceite substitua o recebedor físico ou a autoria do evento original.

### REV04 — Controle de concorrência: If-Match versus expected_version

**Classificação:** Alta — ambiguidade explícita.

O OpenAPI apresenta `If-Match` como cabeçalho opcional, mas mantém `expected_version` obrigatório no corpo de transferência e `expected_object_version` obrigatório no aceite. A descrição afirma que os mecanismos são alternativas, mas o schema atualmente permite/exige uma combinação diferente dessa alternativa.

**Recomendação:** escolher um mecanismo único para os novos endpoints:
- preferencialmente `If-Match` com ETag/versão, se o padrão HTTP for adotado; ou
- campo `expected_version`/ `expected_object_version` no corpo, removendo o parâmetro `If-Match`.

Até a decisão API06, o OpenAPI deve marcar claramente a escolha como pendente e evitar sugerir que ambos são simultaneamente obrigatórios.

### REV05 — Resposta e status da rota legada POST /custody/transfer

**Classificação:** Média — compatibilidade precisa de confirmação.

A especificação HTTP funcional lista a rota legada `POST /api/v1/custody/transfer` para preservação, mas o OpenAPI atribui resposta `200` e usa schema genérico. O contrato runtime descrito no inventário deve ser consultado para confirmar método, status, corpo, erros e cabeçalhos reais.

**Recomendação:** não fixar status nem payload legado por suposição. Copiar o contrato efetivo do endpoint existente para a especificação de compatibilidade, preservando-o sem breaking change. O fluxo novo por `CustodyObject` deve continuar separado.

### REV06 — Cobertura das rotas legadas

**Classificação:** Média — cobertura parcial.

A matriz de compatibilidade funcional menciona preservação de `POST /samples`, `GET /samples`, `GET /samples/{id}`, rotas de QR Code e outras consultas. O OpenAPI atual documenta somente parte das rotas legadas: custódia, histórico e timeline.

**Recomendação:** decidir se este arquivo OpenAPI tem escopo restrito ao recebimento/custódia ou se pretende ser um contrato de compatibilidade mais abrangente. Se for restrito, declarar explicitamente que as demais rotas permanecem documentadas em outro contrato. Se for abrangente, incluir as rotas omitidas usando schemas copiados do runtime, não schemas inventados.

### REV07 — Representação de CustodyHistory e enumeração de eventos

**Classificação:** Média — semântica incompleta.

A rota `GET /custody/objects/{id}/history` é coerente com DEC04 e com o modelo relacional, mas o schema inclui `source: NEW_FLOW | LEGACY` sem explicar se um histórico por objeto poderá conter eventos legados associados por vínculo/migração. O modelo prevê que eventos antigos continuem ligados diretamente a `DeviceSample`, enquanto eventos novos se ligam ao objeto.

**Recomendação:** definir se o endpoint por objeto retorna exclusivamente eventos cujo alvo físico é aquele objeto. Se sim, `source` pode ser redundante ou deve representar apenas a origem de migração, não inferida. A resolução de eventos legados para objetos não pode ocorrer sem vínculo confiável. Fechar também ordenação estável, cursor e snapshot (API11).

### REV08 — Cardinalidade e integridade de CustodyObject

**Classificação:** Média — validação condicional necessária.

O modelo lógico define `CustodyObject.quantity` como NOT NULL e `receipt_item_id` obrigatório. O OpenAPI exige `represented_quantity` na criação, mas permite que a resposta `CustodyObjectSummary.represented_quantity` seja nula. Além disso, o contrato não expressa que um item não apresentado não pode gerar objeto de custódia.

**Recomendação:** tornar a quantidade não nula na resposta de objeto persistido e documentar a regra: `NOT_PRESENTED` implica zero objetos; `PRESENTED` implica objetos em quantidade/granularidade aprovada. Ajustar quando API03/DEC05/COMP06 estiverem fechadas.

### REV09 — Dados da DeviceSample no aceite

**Classificação:** Alta — regra ainda provisória.

O OpenAPI exige `lot_number`, `manufacturer`, `commercial_name` e `storage_location`; permite `serial_number` nulo. Isso acompanha a preocupação de não exigir serial universalmente, mas o modelo atual exige serial/lote/fabricante/nome comercial e possui unicidade composta. O modelo relacional recomenda revisar essas regras sem alteração prematura. A especificação funcional também declara que `storage_location` deve ser reconciliado com a custódia e não substituir o histórico.

**Recomendação:**
- manter API08/COMP04 como bloqueadores;
- definir payload por classe de dispositivo;
- decidir se localização de armazenamento é projeção da custódia ou atributo próprio da amostra;
- não declarar o schema atual da amostra compatível com esse payload até resolver a diferença com o modelo runtime;
- não alterar a obrigatoriedade de serial ou constraint de unicidade sem análise de dados legados.

### REV10 — Timestamps e autoria

**Classificação:** Alta — decisão de domínio pendente.

O contrato distingue `occurred_at` e `recorded_at`, enquanto o modelo físico legado possui `transferred_at` e pode possuir `created_at`; a análise indica que `event_type` e `recorded_by_id` não existem explicitamente no modelo atual. O contrato deve evitar apresentar esses campos como já existentes.

**Recomendação:** definir formalmente:
- instante efetivo do evento;
- instante de gravação;
- ator que executou a ação;
- custodiante de origem e destino;
- política de lançamento tardio/retroativo e fuso;
- campos novos ou mapeamento auditável, sem inferência retroativa.

### REV11 — Assinatura eletrônica

**Classificação:** Média — decisão institucional pendente.

O OpenAPI admite `signature_id` nulo nas respostas e não define um mecanismo de assinatura para as operações. Isso é coerente com API05/EST07 ainda pendentes, mas deve ser explicitado como provisório, não como regra final.

**Recomendação:** não inferir que autenticação + AuditLog substituem assinatura eletrônica. Definir por tipo de operação, alvo, conteúdo assinado, momento de pré-assinatura e política de repetição.

### REV12 — Idempotência

**Classificação:** Média — cabeçalho presente, política incompleta.

O OpenAPI exige `Idempotency-Key` em recebimento, transferência e aceite. A especificação funcional ainda deixa escopo, retenção, replay e resposta para objeto já aceito em aberto (API07/API09).

**Recomendação:** manter a chave como requisito candidato, mas definir escopo (usuário/rota/recurso), janela de retenção, hash do payload, resposta de replay, conflito de reutilização e comportamento após timeout/commit. A unicidade de domínio no banco continua necessária; chave idempotente não substitui constraints.

## 4. Pontos de coerência confirmados

1. **DEC04:** a custódia é modelada em torno de `CustodyObject`, não de `DeviceSample`, permitindo eventos pré-amostra.
2. **DEC05:** a amostra operacional é criada posteriormente e vinculada ao objeto; um objeto gera no máximo uma amostra no fluxo ordinário.
3. **Recebimento único:** a rota de criação está vinculada à solicitação e o modelo lógico prevê `solicitation_id UNIQUE`.
4. **Item não apresentado:** o modelo de estados estabelece que não inicia custódia nem gera amostra; o contrato prevê lista de objetos vazia como exemplo.
5. **Preservação temporal:** o aceite deve copiar `arrived_at` e `received_by_id` originais, não a hora/usuário do aceite.
6. **Compatibilidade:** o contrato mantém rotas antigas de custódia separadas dos novos endpoints por objeto.
7. **Imutabilidade:** a análise técnica recomenda preservar append-only e retificações/eventos compensatórios, sem reescrever eventos antigos.

## 5. Sequência recomendada para saneamento documental

Antes de produzir uma versão OpenAPI candidata a congelamento:

1. Resolver API03/COMP06: quantidade, agrupamento e cardinalidade dos objetos.
2. Resolver API04: evento inicial, catálogo de eventos, autoria e timestamps.
3. Resolver API06: mecanismo único de concorrência.
4. Resolver API08/COMP04: payload mínimo da amostra e localização.
5. Resolver API05/EST07: assinatura por operação.
6. Resolver API07/API09: idempotência e resposta para objeto já aceito.
7. Resolver API11/API12: paginação/snapshot, datas retroativas e fuso.
8. Conferir contratos runtime legados e completar ou delimitar formalmente a cobertura do OpenAPI.
9. Atualizar o YAML e os documentos funcionais/relacionais de forma coordenada, mantendo histórico de versões.

## 6. Decisões que não devem ser presumidas

Esta revisão não decide:
- nomes finais de tabelas, colunas ou rotas;
- enumeração definitiva de eventos;
- obrigatoriedade universal de serial;
- assinatura obrigatória em todas as operações;
- status HTTP final para repetição de aceite;
- inclusão automática de eventos legados no histórico de objetos;
- perfis institucionais e segregação de funções;
- autorização para migração ou implementação.

## 7. Controle de execução

- Revisão estática de cinco documentos do repositório.
- Nenhum teste, build, CI ou validação automática de OpenAPI/YAML foi executado.
- Nenhum código, modelo ORM, schema, banco, migração, endpoint, frontend ou configuração foi alterado.
- Este documento é uma análise para revisão, não aprovação institucional nem autorização de implementação.

## 8. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-09 | Primeira revisão cruzada entre contratos HTTP, OpenAPI, modelo relacional, compatibilidade da custódia e estados do processo. |
