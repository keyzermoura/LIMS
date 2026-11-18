# Pacote B — Especificação técnica e matriz de testes do recebimento e aceite

**Identificador:** ESP-B-LIMS-SEFI-001  
**Versão:** 0.1 — proposta técnica para revisão  
**Data:** 2026-11-18  
**Repositório:** `keyzermoura/LIMS`  
**Branch de trabalho:** `docs/plano-correcoes-pacote-a`  
**Baseline de código examinada:** `e5797013cff5b455c3d105a3a8ee2407da5213c5`  
**Branch documental consultada:** `docs/plano-correcoes-pacote-a`  
**Gate G0:** NÃO APROVADO  
**Natureza:** especificação e plano de testes; não altera regras institucionais nem autoriza implementação.

---

## 1. Objetivo e escopo

Detalhar os requisitos P0-01 a P0-04 do plano PLN-COR-LIMS-SEFI-001, com foco em:

1. separar item declarado de material efetivamente apresentado;
2. impedir a criação de custódia para quantidade não apresentada;
3. reconciliar quantidades declaradas, apresentadas, sob custódia, aceitas e recusadas;
4. preservar histórico de apresentações/retificações e permitir chegada complementar vinculada ao mesmo recebimento principal, sem criar segundo recebimento para a solicitação;
5. assegurar que a amostra operacional só seja criada após aceite válido;
6. estabelecer testes unitários, integração, concorrência, migração e regressão.

Fora do escopo desta especificação: backup/restore (P0-05), reagentes, anexos, segurança M2M, interface final e liberação do Gate G0.

## 2. Evidência da baseline examinada

### 2.1 Modelos e serviço confirmados

- `Solicitation` possui relação 1:1 com `Receipt`; `Receipt.solicitation_id` é único.
- `SolicitationItem` registra `declared_quantity` e `unit_of_measure`.
- `ReceiptItem` já separa `presentation_status`, `presented_quantity`, `conference_status` e `decision`, mas não mantém histórico próprio de apresentações.
- `CustodyObject` pertence a `ReceiptItem` e registra `represented_quantity`; aceita múltiplos objetos por item.
- `CustodyEvent` registra eventos append-only associados a cada objeto.
- `DeviceSample.origin_custody_object_id` liga a amostra ao objeto de origem.
- `ReceiptCreate` não recebe a lista de itens apresentados nem quantidades por item.
- `ReceiptItemConference` recebe status, quantidade apresentada, status de conferência, decisão, observação e versão.
- `create_receipt()` atualmente cria um ReceiptItem como PRESENTED com a quantidade declarada e cria CustodyObject/INGRESSO para cada item declarado.
- `conference_item()` atualiza o agregado ReceiptItem, mas o trecho examinado não cria objetos de custódia a partir de quantidades efetivamente conferidas.
- `accept_custody_object()` cria DeviceSample quando a decisão é ACCEPTED e atualiza o objeto, mas o trecho examinado não demonstra todas as pré-condições de checklist, pendências e validação da coordenação.

### 2.2 Limitações da inspeção

Esta especificação foi construída a partir dos arquivos consultados: `receipt_service.py`, `models/receipt.py`, `models/solicitation.py`, `schemas/receipt.py`, `models/enums.py` e `solicitation_service.py`.

Ainda precisam ser inspecionados antes da implementação: rotas efetivamente registradas, migrations existentes e constraints reais do banco, testes atuais de recebimento/custódia/aceite, serviços de checklist e decisão/coordenação, políticas de autorização e componentes frontend que consomem os schemas. Portanto, nomes de novos campos, endpoints e migrações permanecem propostas, não fatos da implementação.

## 3. Regras de domínio que a solução deve preservar

- Uma solicitação mantém um único recebimento principal (`Receipt`).
- Cada item declarado permanece identificável, mesmo se nada dele for apresentado.
- Quantidade declarada nunca é copiada automaticamente para quantidade apresentada.
- Quantidade não apresentada não gera objeto de custódia, evento de ingresso ou amostra.
- Cada quantidade efetivamente recebida deve ter vínculo rastreável com o item declarado e com o registro de apresentação que a originou.
- Apresentações complementares, quando admitidas pelo fluxo aprovado, são registradas como novos fatos históricos dentro do mesmo recebimento, sem sobrescrever ou apagar a apresentação anterior.
- A soma das quantidades sob custódia não pode exceder a soma das quantidades efetivamente apresentadas, considerando a mesma unidade de medida.
- A soma das quantidades aceitas e recusadas não pode exceder a quantidade sob custódia; a quantidade ainda pendente deve permanecer explícita.
- A criação de amostra operacional é consequência do aceite favorável do objeto elegível, nunca do mero registro de chegada ou da conferência ainda pendente.
- Toda mudança crítica deve ser transacional, auditável, versionada e protegida contra repetição/concorrência.
- Não converter unidades automaticamente sem regra de conversão aprovada e registrada.

## 4. Diagnóstico funcional: estados e fatos distintos

O modelo atual mistura um estado agregado de apresentação com uma única quantidade editável. Isso não representa adequadamente múltiplas apresentações ao longo do tempo. A recomendação é separar:

1. **Declaração:** fato original imutável da solicitação (`declared_quantity`, unidade).
2. **Apresentação:** fato histórico datado, por item, com quantidade e responsável pelo registro.
3. **Custódia:** objetos físicos efetivamente constituídos para as quantidades recebidas.
4. **Conferência/decisão:** avaliação do material apresentado, com checklist e decisão.
5. **Aceite:** decisão por objeto/quantidade, que libera a criação da amostra operacional.

O agregado `ReceiptItem` pode continuar sendo a visão corrente/resumo do item, mas não deve ser a única fonte de histórico.

## 5. Modelo lógico proposto

### 5.1 Manter entidades existentes

| Entidade | Papel proposto |
|---|---|
| Solicitation / SolicitationItem | Declaração original e item solicitado. |
| Receipt | Único recebimento principal da solicitação. |
| ReceiptItem | Agregado do item no recebimento; resumo derivado das apresentações, conferências e objetos. |
| CustodyObject | Unidade física sob custódia, individual ou agrupada homogeneamente, com quantidade e estado próprios. |
| CustodyEvent | Histórico de movimentação/ingresso/encerramento de cada objeto. |
| DeviceSample | Amostra operacional criada somente após aceite favorável. |

### 5.2 Nova entidade histórica recomendada

Criar uma entidade filha, nome provisório `ReceiptPresentation` (nome final depende da convenção do projeto), para registrar cada apresentação física:

| Campo proposto | Finalidade / regra |
|---|---|
| id | Identificador UUID. |
| receipt_item_id | FK obrigatória para o item do recebimento. |
| presented_quantity | Decimal positivo; zero não deve ser persistido como apresentação. |
| unit_of_measure | Unidade copiada/snapshot da declaração no momento do evento, ou FK para catálogo se já existir. |
| presentation_status | Apresentação total/parcial, se necessário como classificação explícita; quantidade é a fonte para reconciliação. |
| presented_at | Data/hora efetiva da apresentação. |
| registered_by_id | Usuário que registrou o fato. |
| notes | Observação e justificativa. |
| idempotency_key | Chave opcional/obrigatória conforme padrão existente, para impedir duplicação de submissão. |
| created_at | Data/hora de registro no sistema; não substitui presented_at. |

A entidade deve ser append-only após formalização. Correções devem ocorrer por evento de retificação/cancelamento com justificativa e vínculo ao registro anterior, não por edição destrutiva. Se o projeto já possuir mecanismo genérico de eventos/retificações compatível, reutilizá-lo em vez de duplicar infraestrutura.

### 5.3 Campos agregados em ReceiptItem

A princípio, evitar persistir vários totais redundantes. Calcular por consulta/serviço a partir dos fatos filhos:

- total apresentado = soma de ReceiptPresentation válida;
- total sob custódia = soma de CustodyObject ativo/representado, descontadas saídas ou encerramentos quantitativos quando o domínio já os suportar;
- total aceito = soma dos objetos/parcelas aceitos;
- total recusado = soma dos objetos/parcelas recusados;
- total pendente = total sob custódia menos total aceito e recusado.

Se desempenho exigir cache/materialização, definir atualização transacional, reconciliação periódica e fonte de verdade explícita. Não manter campos duplicados sem mecanismo de consistência.

### 5.4 Granularidade dos objetos de custódia

Um `CustodyObject` pode representar um conjunto homogêneo e rastreável. Para uma apresentação parcial, o objeto deve representar somente a quantidade efetivamente recebida. Quando parte do material tiver destino/decisão diferente, separar em objetos distintos ou em parcelas formalmente modeladas; não aceitar/rejeitar parcialmente um objeto indivisível sem representar essa divisão no domínio.

Antes de definir se uma apresentação gera sempre um objeto ou pode gerar vários, confirmar a regra de agrupamento aprovada em D01–D20/G0-Pxx e os requisitos de rastreabilidade física do SEFI. A especificação não presume que itens de lotes/séries diferentes possam ser agrupados.

## 6. Fluxo transacional proposto

### 6.1 Criar recebimento principal

1. Bloquear/serializar a solicitação para evitar dois recebimentos concorrentes.
2. Validar existência, estado SUBMETIDA e inexistência de Receipt.
3. Criar um Receipt.
4. Criar um ReceiptItem para cada item declarado.
5. Inicializar cada ReceiptItem sem apresentação confirmada, quantidade apresentada igual a zero e conferência pendente.
6. Não criar CustodyObject nem CustodyEvent de ingresso nesta etapa.
7. Atualizar status/version da solicitação e registrar auditoria.
8. Commit único; em qualquer falha, rollback integral.

**Observação:** o enum atual `PresentationStatus` contém apenas PRESENTED e NOT_PRESENTED, sem estado pendente ou parcial. Recomenda-se avaliar migration aditiva para estados PENDING/PARTIALLY_PRESENTED, ou derivar a classificação de totais e manter apenas estados persistidos estritamente necessários. Não alterar enum persistido sem avaliar estratégia compatível com PostgreSQL e versões de aplicação.

### 6.2 Registrar apresentação física

1. Receber item, quantidade, unidade, data/hora, observação e versão esperada.
2. Validar que Receipt está em estado que admite apresentação e que o item pertence ao Receipt.
3. Validar quantidade maior que zero e compatibilidade da unidade.
4. Somar apresentações válidas anteriores; impedir exceder a quantidade declarada, salvo exceção formalmente autorizada e auditada.
5. Criar ReceiptPresentation imutável.
6. Criar um ou mais CustodyObject para a quantidade apresentada, de acordo com a granularidade aprovada.
7. Criar evento INGRESSO para cada objeto, com custodiante/local/horário e referência rastreável à apresentação.
8. Atualizar o resumo ReceiptItem e Receipt, com versionamento otimista.
9. Registrar auditoria com valores anterior/novo e referência do evento.
10. Commit único.

Não criar objeto se a validação falhar. A criação do evento, do objeto e da apresentação deve ocorrer na mesma transação.

### 6.3 Conferir item/objeto

A conferência deve ocorrer sobre a quantidade efetivamente apresentada e/ou sobre cada objeto, não sobre a quantidade declarada abstrata. A API deve impedir que um payload altere retrospectivamente o total apresentado sem produzir fato histórico.

Checklist, decisão e coordenação devem ser consultados pelos serviços de domínio existentes. A implementação deverá definir qual entidade representa a decisão final e como se liga ao objeto ou à parcela. Se checklist é requisito obrigatório, não basta aceitar um campo `conference_status` enviado pelo cliente.

### 6.4 Aceitar ou recusar objeto e criar amostra

A operação de aceite deve:

1. bloquear o objeto (ou usar atualização condicional/versionamento com garantia real no banco);
2. validar que está sob custódia e ainda não foi decidido;
3. validar quantidade positiva e origem em apresentação válida;
4. validar conferência concluída e checklist obrigatório completo;
5. validar ausência de pendência impeditiva;
6. validar aprovação da coordenação quando a regra aplicável exigir;
7. validar autorização do ator e segregação de funções, conforme política;
8. validar inexistência de amostra já vinculada;
9. se decisão ACCEPTED, criar exatamente uma DeviceSample e vincular origem;
10. registrar eventos e auditoria;
11. confirmar tudo em uma transação.

A constraint única atual em `CustodyObject.linked_device_sample_id` impede que uma mesma amostra seja vinculada a mais de um objeto, mas não prova sozinha que um objeto não possa produzir duas amostras em operações concorrentes. A implementação deve verificar a existência de constraint/relacionamento único no sentido objeto → amostra e acrescentar proteção no banco, se ausente.

A decisão REJECTED encerra o fluxo do objeto sem criar DeviceSample. A decisão PENDING não deve encerrar o objeto nem gerar amostra.

## 7. Invariantes obrigatórios

| ID | Invariante | Verificação |
|---|---|---|
| INV-B01 | No máximo um Receipt por Solicitation. | UNIQUE(receipts.solicitation_id) + teste concorrente. |
| INV-B02 | Todo ReceiptItem pertence a um Receipt e a um SolicitationItem da mesma solicitação. | Validação de domínio e, se viável, constraint. |
| INV-B03 | Quantidade declarada é maior que zero e não é alterada pelo recebimento. | Modelo + serviço + teste de regressão. |
| INV-B04 | Apresentação registrada possui quantidade > 0 e unidade compatível. | Schema + serviço + constraint. |
| INV-B05 | Nenhum objeto de custódia existe sem apresentação física válida de origem. | FK/origem + serviço + teste de integridade. |
| INV-B06 | Soma sob custódia não excede quantidade apresentada válida. | Serviço transacional + reconciliação. |
| INV-B07 | Soma aceita + recusada não excede quantidade sob custódia. | Serviço + teste de partição. |
| INV-B08 | Objeto aceito/recusado não pode receber decisão final conflitante sem fluxo formal de retificação. | Máquina de estados + concorrência. |
| INV-B09 | DeviceSample só existe com aceite ACCEPTED válido. | Serviço + FK/constraint + teste negativo. |
| INV-B10 | Um objeto origina no máximo uma DeviceSample. | UNIQUE(origin_custody_object_id), se compatível com modelo e legado. |
| INV-B11 | Eventos formalizados não são apagados nem reescritos. | Política append-only + auditoria. |
| INV-B12 | Repetição da mesma requisição não duplica apresentação, objeto, evento ou amostra. | Idempotência e constraints. |
| INV-B13 | Falha em qualquer passo crítico reverte todos os efeitos da operação. | Teste de rollback em banco. |
| INV-B14 | Concorrência não permite exceder quantidade declarada nem duplicar aceite. | Lock/UPDATE condicional + testes concorrentes. |
| INV-B15 | Toda decisão e retificação identifica ator, instante, motivo e estado anterior/novo. | Auditoria e trilha de eventos. |

## 8. Contratos de API — proposta

Não fixar rotas sem inspecionar o router real. A intenção funcional é:

- Criar recebimento principal: mantém endpoint existente, mas não inventa apresentação nem custódia.
- Registrar apresentação: novo comando por ReceiptItem, com quantidade, unidade, timestamp efetivo, justificativa e idempotency key.
- Consultar reconciliação: retornar declarado, apresentado, sob custódia, aceito, recusado e pendente, todos com unidade.
- Conferir: associar a conferência aos objetos/parcelas realmente apresentados.
- Aceitar/recusar: comando sobre objeto de custódia, com versão e decisão; resposta retorna amostra somente no aceite válido.

Regras de contrato:
- Cliente não escolhe status calculado nem informa total agregado como autoridade.
- Valores monetários não se aplicam; quantidades devem ser Decimal e serializadas sem perda de precisão.
- Respostas incluem versão para concorrência otimista.
- Erros distinguem 404 (recurso ausente), 409 (conflito/versão/idempotência), 422 (regra de domínio) e 403 (autorização).
- Não revelar dados de outra solicitação por IDs conhecidos.

## 9. Estratégia de migração e compatibilidade

1. Inventariar migrations, constraints, enum types PostgreSQL e volume de dados antes de definir migration.
2. Fazer backup validado antes da migração em ambiente de teste.
3. Introduzir entidade histórica de apresentação de forma aditiva.
4. Para registros legados, não inferir que todo item foi fisicamente apresentado apenas porque o código antigo criou ReceiptItem como PRESENTED. Fazer reconciliação por evidência disponível; quando não houver evidência, marcar como legado não reconciliado e preservar o estado original em metadados/auditoria.
5. Não fabricar ReceiptPresentation retroativa sem evidência documental.
6. Preservar Receipt, ReceiptItem, CustodyObject, CustodyEvent e DeviceSample existentes.
7. Se houver necessidade de novo enum, usar migration PostgreSQL compatível com implantação rolling; testar upgrade e downgrade (quando downgrade for seguro) em banco descartável.
8. Executar backfill em lotes, com relatório de linhas afetadas, inconsistências e possibilidade de retomada.
9. Verificar constraints, FKs, índices, unicidade e contagens antes/depois.
10. Só ativar o novo fluxo após backend, frontend e contratos estarem compatíveis; prever feature flag se a arquitetura já possuir padrão aprovado.

## 10. Matriz de testes de aceitação

| ID | Cenário | Preparação/ação | Resultado esperado |
|---|---|---|---|
| TB-01 | Solicitação com item integralmente apresentado | Declarado 10 UN; registrar apresentação 10 UN. | Um fato de apresentação de 10; objetos representam no máximo 10; eventos de ingresso correspondentes; sem excedente. |
| TB-02 | Apresentação parcial | Declarado 10 UN; registrar 6 UN. | Apresentado 6; sob custódia até 6; saldo não apresentado 4; não classificar como total. |
| TB-03 | Item não apresentado | Declarado 10 UN; criar Receipt sem apresentação. | ReceiptItem existe; apresentado 0; nenhum objeto/evento/amostra. |
| TB-04 | Divergência acima do declarado | Declarado 10; tentar registrar 11. | Rejeição 422/409 conforme contrato; nenhuma gravação parcial. |
| TB-05 | Apresentações complementares | Declarado 10; registrar 4 e depois 6 no mesmo ReceiptItem. | Dois fatos históricos; total apresentado 10; sem segundo Receipt; sem sobrescrita do primeiro fato. |
| TB-06 | Excesso em apresentação complementar | Declarado 10; registrar 7 e depois 4. | Segunda operação bloqueada; total permanece 7. |
| TB-07 | Múltiplos objetos por apresentação | Apresentar 10 e dividir em dois objetos conforme regra aprovada. | Soma representada = 10; cada objeto tem origem e evento inicial. |
| TB-08 | Falha entre gravações | Injetar falha após criar apresentação ou objeto, antes do commit. | Rollback integral; nenhum objeto órfão, evento parcial ou soma inconsistente. |
| TB-09 | Conferência pendente | Objeto sem checklist/conferência concluída; tentar aceitar. | Bloqueio; nenhuma DeviceSample. |
| TB-10 | Checklist eliminatório não conforme | Responder critério eliminatório como não conforme; tentar aceite. | Bloqueio/decisão de recusa conforme regra aprovada; sem amostra. |
| TB-11 | Coordenação obrigatória pendente | Regra exige validação e ela está pendente. | Aceite bloqueado; sem amostra. |
| TB-12 | Aceite favorável | Objeto elegível, checklist completo, validação exigida aprovada. | Uma DeviceSample vinculada ao objeto; evento e auditoria na mesma transação. |
| TB-13 | Recusa | Objeto elegível com decisão REJECTED. | Objeto recusado; nenhuma DeviceSample. |
| TB-14 | Repetição idempotente | Reenviar mesma apresentação/aceite com mesma chave. | Resposta idempotente ou conflito controlado; nunca duplica fatos/objetos/amostras. |
| TB-15 | Duas apresentações concorrentes | Duas transações tentam consumir o saldo final. | No máximo uma vence; total não ultrapassa declarado. |
| TB-16 | Dois aceites concorrentes | Duas transações aceitam o mesmo objeto. | Uma única decisão efetiva e uma única DeviceSample. |
| TB-17 | Versão desatualizada | Enviar versão anterior do ReceiptItem/objeto. | 409; nenhum efeito colateral. |
| TB-18 | Unidade incompatível | Tentar somar unidades diferentes sem conversão aprovada. | Bloqueio; nenhuma reconciliação silenciosa. |
| TB-19 | Legado sem evidência de apresentação | Migrar ReceiptItem antigo sem documento de comprovação. | Preservar registro legado; não inventar evento de apresentação nem afirmar rastreabilidade inexistente. |
| TB-20 | Integridade relacional | Criar objeto sem apresentação válida ou amostra sem aceite. | Banco/serviço rejeita; não há registro inconsistente. |
| TB-21 | Autorização | Usuário sem permissão tenta registrar/aceitar ou acessa outro Receipt. | 403/404 conforme política; nenhum dado ou alteração indevida. |
| TB-22 | Auditoria e retificação | Retificar quantidade registrada incorretamente. | Fato original preservado; retificação vinculada, justificada e auditada; totais recalculados corretamente. |

## 11. Testes de regressão obrigatórios

- Criação, submissão, consulta e cancelamento de solicitação.
- Regra de um único Receipt por Solicitation.
- Listagem/detalhe do recebimento e serialização dos novos campos.
- Transferência e histórico de custódia.
- Aceite/recusa e vínculo de DeviceSample.
- Geração de número SEFI/LIMS sem duplicidade.
- Auditoria encadeada e snapshots.
- Controle de versão otimista.
- Permissões de perfis humanos e contas de serviço.
- Compatibilidade do frontend com status pendente/parcial e múltiplas apresentações.
- Migração em banco vazio e banco com dados legados.

## 12. Critérios de saída do Pacote B — especificação

A especificação só estará pronta para implementação quando:

- [ ] rotas, testes, migrations e frontend existentes tiverem sido inventariados;
- [ ] decisão de domínio sobre apresentação complementar e granularidade dos objetos estiver confirmada contra D01–D20/G0-P01–P30;
- [ ] modelo histórico e política de retificação estiverem definidos;
- [ ] estados e enums compatíveis com banco e frontend estiverem definidos;
- [ ] pré-condições exatas de checklist/coordenação/aceite estiverem rastreadas às regras aprovadas;
- [ ] constraints, locks, idempotência e limites de transação estiverem especificados;
- [ ] migração dos dados legados tiver estratégia e relatório de impacto;
- [ ] todos os casos TB-01 a TB-22 tiverem mapeamento para testes automatizados e evidência.

## 13. Decisões pendentes — não presumidas

| ID | Questão | Recomendação técnica provisória | Autoridade |
|---|---|---|---|
| DB-01 | É permitido receber quantidade complementar em data posterior mantendo o mesmo Receipt? | Sim, modelar eventos de apresentação filhos; confirmar aderência ao D19 e ao processo SEFI. | Validação institucional se D19 não resolver inequivocamente. |
| DB-02 | Um item pode gerar vários objetos de custódia? | Sim, quando houver separação física, lote/série, decisão ou destino diferente; confirmar granularidade operacional. | SEFI / coordenação. |
| DB-03 | Pode haver aceite/recusa parcial de um conjunto? | Não sobre objeto indivisível; dividir em objetos/parcelas antes da decisão. | SEFI / coordenação. |
| DB-04 | Apresentação acima da quantidade declarada é permitida? | Bloquear por padrão; eventual exceção requer justificativa e autorização formal. | Autoridade do processo. |
| DB-05 | Quais critérios de checklist bloqueiam aceite e quais são saneáveis? | Reutilizar classificação E/S aprovada; exigir referência explícita à versão aplicada. | Decisões D/G0 e coordenação. |
| DB-06 | Quais casos exigem validação da coordenação? | Aplicar matriz de alçada aprovada; não inferir no código. | Coordenação SEFI. |
| DB-07 | Retificação após aceite pode reabrir objeto/amostra? | Não permitir alteração destrutiva; exigir processo formal de desvio/retificação com histórico e avaliação de impacto. | Qualidade/coordenação. |

## 14. Parecer técnico desta etapa

A arquitetura existente já possui os agregados centrais e relacionamentos necessários para evoluir sem reconstrução. A lacuna principal não é a ausência de Receipt ou CustodyObject: é a falta de representação histórica e transacional suficientemente explícita da apresentação física e da reconciliação de quantidades.

A proposta preferencial é aditiva: introduzir o fato histórico de apresentação, transformar ReceiptItem em agregado/resumo, gerar custódia apenas a partir de material apresentado e fechar a barreira de aceite com pré-condições rastreáveis e proteção no banco.

**Status:** especificação preliminar produzida; ainda não liberada para implementação.  
**Pacote A:** documentalmente concluído, PR #5 permanece separado e não mesclado.  
**Pacote B:** em especificação; nenhuma alteração de backend, frontend, migration ou infraestrutura nesta entrega.  
**Gate G0:** NÃO APROVADO.


---

## 15. Complemento da inspeção — checklist e decisão/coordenação

Após a primeira redação, foram examinados também `models/checklist.py`, `models/decision.py`, `services/checklist_service.py` e `services/decision_service.py`. Esses arquivos refinam os riscos e exigem os seguintes ajustes na especificação de implementação.

### 15.1 Checklist atual

- `ChecklistAnswer` está vinculado a `ReceiptItem`, não diretamente a `CustodyObject` ou a um evento de apresentação.
- `submit_checklist_answers()` limpa a coleção de respostas anteriores antes de gravar as novas (`receipt_item.checklist_answers.clear()`). Isso significa substituição destrutiva do conjunto de respostas, incompatível com a exigência de histórico imutável se já houve formalização.
- O serviço calcula conformidade a partir de classes de critério, mas o trecho inspecionado ainda precisa ser lido integralmente e relacionado aos critérios vigentes, inclusive regra de saneamento, para fechar a matriz de bloqueio.

**Consequência:** antes de implementar P0-04, decidir se o checklist é aplicado por item, apresentação ou objeto. Para auditoria, recomenda-se preservar cada submissão como uma revisão/versionamento identificável, sem apagar respostas previamente formalizadas. A revisão deve apontar o template e a versão exatos usados, o ator, o instante e a justificativa de eventual reaplicação.

### 15.2 Decisão e revisão da coordenação atuais

- `ReceiptDecision` já possui vínculo obrigatório com `ReceiptItem` e vínculo opcional com `CustodyObject`.
- A decisão armazena `decision`, justificativa, decisor e `requires_coordination_review`.
- `record_receipt_decision()` define revisão obrigatória para decisões PENDING e REJECTED; cria `CoordinationReview` pendente e atualiza o campo-resumo `ReceiptItem.decision`.
- `review_coordination_decision()` aplica segregação de funções: o revisor não pode ser o mesmo usuário que formalizou a decisão.
- Quando a coordenação aprova, o serviço limpa `requires_coordination_review`; é necessário verificar no fluxo completo o tratamento de DEVOLVIDO/REJEITADO e se há uma decisão final explícita.
- O trecho de `accept_custody_object()` não consulta `ReceiptDecision`, `CoordinationReview` nem `ChecklistAnswer` antes de criar `DeviceSample`.

**Consequência:** o intertravamento P0-04 é uma lacuna comportamental concreta no trecho examinado. O aceite não pode confiar somente em `CustodyAcceptanceCreate.decision`; deve reconciliar a decisão formal registrada, checklist vigente, coordenação quando exigida e estado atual do objeto.

### 15.3 Requisitos adicionais de aceite

| ID | Requisito adicional | Critério verificável |
|---|---|---|
| TB-23 | Checklist substituído após submissão formal | A versão anterior permanece consultável; nova versão não apaga a anterior. |
| TB-24 | Decisão PENDING com revisão pendente | `accept_custody_object()` bloqueia criação de amostra. |
| TB-25 | Decisão REJECTED com coordenação pendente | Nenhuma amostra é criada enquanto a revisão obrigatória não estiver concluída conforme regra aprovada. |
| TB-26 | Revisor igual ao decisor | Revisão é bloqueada pela segregação de funções. |
| TB-27 | Decisão formal inexistente | Não se aceita objeto apenas com decisão enviada no payload se o processo exigir registro formal. |
| TB-28 | Divergência entre decisão no ReceiptItem e histórico ReceiptDecision | Bloqueio e encaminhamento para reconciliação; não escolher silenciosamente um dos valores. |
| TB-29 | Reaplicação de checklist | Nova revisão versionada preserva template, critérios, respostas e autor da revisão anterior. |

### 15.4 Questões que continuam abertas

1. Confirmar se checklist é por item, por objeto ou por apresentação. O modelo atual aponta para ReceiptItem; não alterar essa semântica sem validação.
2. Confirmar se decisão de recebimento e aceite de custódia são a mesma decisão em fases diferentes ou decisões distintas. O modelo atual sugere decisões do item/objeto e um comando separado de aceite.
3. Confirmar quais estados da revisão de coordenação liberam o avanço: APROVADO é o único resultado positivo explícito no enum; DEVOLVIDO e REJEITADO não devem liberar.
4. Definir se decisão REJECTED, após validação da coordenação, resulta em encerramento/recusa do objeto, devolução ou outra destinação. Não presumir que revisão aprovada signifique aceite do material.
5. Rever o histórico de respostas do checklist para não apagar evidência de uma decisão já formalizada.

**Status do complemento:** achados de inspeção estática; ainda não foram executados testes nem homologação. Mantêm-se todos os limites e ressalvas das seções anteriores.
