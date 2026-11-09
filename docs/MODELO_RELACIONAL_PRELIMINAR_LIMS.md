# Modelo Relacional Preliminar do LIMS

**Identificador:** MOD-REL-001  
**Versão:** 0.3  
**Situação:** Proposta técnica preliminar atualizada conforme diretrizes DEC04/DEC05 e análise de compatibilidade da cadeia de custódia; revisão arquitetural/institucional e autorização de implementação pendentes  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Data:** 2026-11-09

---

## 1. Objetivo e limites

Traduzir o modelo conceitual de solicitação, recebimento, conferência, custódia e criação de amostra operacional em uma proposta relacional preliminar. O documento identifica entidades/tabelas candidatas, chaves, relações, cardinalidades, restrições e pontos de compatibilização com o banco existente.

Este documento é **proposta documental**. Não autoriza nem executa alterações em código, modelos SQLAlchemy, banco de dados, migrações Alembic, API, frontend ou infraestrutura. Os nomes físicos sugeridos são lógicos e poderão ser ajustados à convenção já adotada no projeto.

As diretrizes de domínio e as cardinalidades DEC04/DEC05 foram aprovadas pelo usuário para orientar o desenho. O modelo relacional permanece preliminar porque DEC07, DEC08, EST01–EST10, a inspeção do schema legado e a revisão arquitetural/institucional ainda precisam ser concluídas. Esta aprovação não autoriza implementação.

## 2. Fontes e premissas

A proposta foi elaborada a partir da revisão dos documentos versionados na branch \`main\`:

- \`INVENTARIO_TECNICO_FASE_0_1.md\`, versão 1.1;
- \`MODELO_CONCEITUAL_DOMINIO_SOLICITACAO_RECEBIMENTO.md\`, versão 0.2;
- \`MATRIZ_DECISOES_LIMS.md\`, versão 1.2;
- \`ESTRATEGIA_MIGRACAO_DADOS_LEGADOS.md\`, versão 0.2;
- \`ESPECIFICACAO_INTERFACE_ETAPA_1_RECEBIMENTO.md\`, versão 0.1;
- \`ESTADOS_E_TRANSICOES_SOLICITACAO_RECEBIMENTO.md\`, versão 0.2.

Premissas de domínio consideradas:

1. Uma solicitação pode conter vários itens declarados.
2. Cada solicitação possui no máximo um recebimento principal.
3. O recebimento representa todos os itens declarados, inclusive os não apresentados.
4. A conferência, as pendências e as decisões são registradas individualmente por item de recebimento.
5. A custódia começa na chegada física do material apresentado, antes da criação da amostra operacional.
6. A custódia deve estar vinculada a um ObjetoCustodia, que pode representar uma unidade física ou um agrupamento homogêneo autorizado.
7. A amostra operacional só é criada após aceite final e validações obrigatórias.
8. Referências externas, como Harpya, são opcionais e não substituem a chave primária nem o identificador institucional.
9. Registros legados sem evidência confiável não receberão associações retroativas inferidas.
10. O recebimento principal único não deve ser contornado por registro retroativo de entrega posterior.

## 3. Modelo legado identificado e compatibilização

O inventário técnico identificou, entre outros, os modelos existentes:

| Modelo existente | Papel observado | Tratamento nesta proposta |
|---|---|---|
| \`DeviceSample\` | Amostra operacional; possui \`accession_number\`, dados de identificação do dispositivo, status, dados de recebimento e custódia atual. | Preservar como entidade operacional existente. Avaliar vínculos novos opcionais com objetos de custódia e itens de recebimento. |
| \`LabTest\` | Ensaio associado à amostra, com método/parâmetros, limites, resultado corrente, responsável e assinatura. | Manter relação existente com \`DeviceSample\`; fora do escopo de remodelagem analítica desta proposta. |
| \`LabTestResult\` | Versões históricas de resultados. | Preservar histórico e integridade existentes. |
| \`ChainOfCustody\` | Eventos de transferência de guarda atualmente relacionados diretamente a \`DeviceSample\`. | Avaliar extensão para custódia pré-amostra, sem duplicar eventos nem romper consultas/relatórios existentes. |
| \`AuditLog\` | Trilha de auditoria com sequência, payload, hash/HMAC, ator, ação e entidade. | Reutilizar para eventos de domínio conforme arquitetura atual, complementando com tabelas de histórico transacional quando necessário. |
| \`ElectronicSignature\` | Manifestos e dados de assinatura eletrônica. | Reutilizar conforme política de assinatura aprovada; não presumir que toda gravação exige assinatura. |
| \`User\` | Usuários e perfis existentes. | Referenciar usuários por FK nas novas tabelas, após mapear permissões reais. |

O inventário observou que o serviço atual de criação de amostra gera \`accession_number\` no formato \`LIMS-AAAA-######\`, cria evento inicial de custódia e registra auditoria no fluxo de criação. Também observou que a rota de criação direta de amostra não possui a etapa prévia de solicitação e aceite.

**Limite de evidência:** este documento não reproduz colunas completas, tipos SQL, constraints ou nomes físicos das tabelas legadas, pois isso exige inspeção integral e comparativa dos modelos SQLAlchemy, migrações e banco-alvo. Nenhuma coluna legada deve ser renomeada ou removida com base apenas nesta proposta.

## 4. Convenções propostas

- PK: UUID ou tipo já padronizado no projeto; a escolha deve seguir a convenção real do schema existente.
- FK: chave estrangeira com integridade referencial no banco.
- Datas: armazenar instantes com timezone (preferencialmente UTC no banco), apresentando-os no fuso institucional.
- Quantidades: tipo numérico apropriado à unidade de medida; não usar texto livre para valores quantitativos.
- Estados: enums ou tabelas de domínio versionadas, conforme padrão já adotado; não duplicar enums com significados divergentes.
- Registros formais: preservar autoria, data/hora, justificativa e referência à versão da regra/checklist aplicável.
- Exclusão: registros formalizados de recebimento, custódia, decisão e evidência não devem ser apagados fisicamente no fluxo ordinário.
- Nomes apresentados são nomes lógicos. A implementação deverá respeitar convenções SQLAlchemy/Alembic existentes.

## 5. Tabelas propostas

### 5.1 Solicitante

**Finalidade:** identificar pessoa, órgão ou instituição que origina a demanda.

| Campo lógico | Chave/regra | Observação |
|---|---|---|
| id | PK | Identificador interno. |
| tipo | obrigatório | Pessoa física, órgão, instituição ou categoria aprovada. |
| nome_razao_social | obrigatório | Nome de referência. |
| identificacao | opcional | Documento/código institucional, com proteção de acesso conforme natureza. |
| contatos | conforme política | Evitar armazenar dados pessoais excessivos. |
| ativo | obrigatório | Controle cadastral. |
| created_at / updated_at | obrigatório | Auditoria técnica do cadastro. |

Relação: um Solicitante pode originar várias Solicitações (1:N).

### 5.2 Solicitation

**Finalidade:** registrar a demanda institucional antes da chegada física.

| Campo lógico | Chave/regra | Observação |
|---|---|---|
| id | PK | Chave interna. |
| solicitation_number | UNIQUE, NOT NULL | Protocolo próprio da solicitação; formato ainda a definir. |
| requester_id | FK → Solicitante.id | Solicitante de origem. |
| status | NOT NULL | Estado da solicitação, conforme máquina de estados aprovada. |
| purpose / origin | conforme regra | Finalidade e origem da demanda. |
| created_by_id | FK → User.id | Usuário interno que cadastrou. |
| submitted_at | NULL até submissão | Instante de formalização. |
| created_at / updated_at | NOT NULL | Datas técnicas. |
| cancelled_at / cancelled_by_id | NULL | Apenas se cancelada, com justificativa/histórico associado. |

Regra: a primeira entrega prevê cadastro assistido por usuário interno; não pressupõe contas externas para solicitantes.

### 5.3 SolicitationItem

**Finalidade:** representar cada linha de material declarada na solicitação.

| Campo lógico | Chave/regra | Observação |
|---|---|---|
| id | PK | Chave interna. |
| solicitation_id | FK → Solicitation.id, NOT NULL | Solicitação proprietária. |
| item_number | NOT NULL | Ordem/identificador dentro da solicitação. |
| description | NOT NULL | Descrição declarada. |
| manufacturer_declared | NULL | Fabricante declarado, quando conhecido. |
| model_reference / catalog_reference | NULL | Referências declaradas. |
| lot_declared / serial_declared | NULL | Identificação declarada, sem pressupor serial universal. |
| quantity_declared | NOT NULL | Quantidade solicitada/declarada. |
| unit_of_measure | NOT NULL | Unidade de medida controlada. |
| created_at / updated_at | NOT NULL | Datas técnicas. |

Constraints candidatas:
- UNIQUE (solicitation_id, item_number);
- CHECK (quantity_declared > 0), conforme unidades fracionárias permitidas;
- FK restritiva para impedir exclusão da solicitação com itens formalizados.

**Importante:** quantidade declarada não equivale à quantidade apresentada, quantidade de unidades físicas, objetos de custódia ou amostras operacionais.

### 5.4 Receipt

**Finalidade:** registrar a única chegada física principal vinculada à solicitação.

| Campo lógico | Chave/regra | Observação |
|---|---|---|
| id | PK | Chave interna. |
| receipt_number | UNIQUE, NOT NULL | Protocolo interno do recebimento, formato a definir. |
| solicitation_id | FK → Solicitation.id, NOT NULL, UNIQUE | Garante no máximo um recebimento principal por solicitação. |
| arrived_at | NOT NULL | Instante real da chegada física; não deve ser substituído pela data de criação. |
| received_by_id | FK → User.id, NOT NULL | Usuário que efetivamente recebeu o material. |
| location_id / location_text | conforme arquitetura | Local inicial de recebimento/guarda. |
| general_condition | NULL | Condições gerais da entrega. |
| status | NOT NULL | Estado agregado do recebimento, preferencialmente derivado das situações dos itens. |
| created_at / created_by_id | NOT NULL | Momento e autoria do registro no sistema. |
| version / updated_at | conforme concorrência | Controle otimista de alterações. |

Constraint essencial:
- UNIQUE (solicitation_id).

A restrição deve existir no banco, não apenas na interface ou no serviço. Uma segunda tentativa deve recuperar/exibir o recebimento existente, sem criar outro. Correções excepcionais devem ser versionadas, justificadas e auditadas.

A regra de recebimento único não autoriza registrar entrega posterior como se tivesse ocorrido na chegada original. Exceções institucionais devem ter mecanismo formal próprio, sem adulterar o fato histórico.

### 5.5 ReceiptItem

**Finalidade:** representar, no recebimento, cada item declarado, mesmo quando não apresentado.

| Campo lógico | Chave/regra | Observação |
|---|---|---|
| id | PK | Chave interna. |
| receipt_id | FK → Receipt.id, NOT NULL | Recebimento principal. |
| solicitation_item_id | FK → SolicitationItem.id, NOT NULL, UNIQUE | Correspondência com a linha declarada. |
| presentation_status | NOT NULL | AGUARDANDO_CHEGADA, APRESENTADO ou NAO_APRESENTADO. |
| quantity_presented | NULL/NOT NULL condicional | Quantidade física efetivamente apresentada; obrigatória quando apresentado, nula/zero conforme regra quando ausente. |
| unit_of_measure | NOT NULL | Deve ser compatível com a unidade declarada ou registrar conversão explícita. |
| identification_observed | NULL | Identificação efetivamente observada. |
| conference_status | NOT NULL | Estado independente da conferência. |
| created_at / updated_at | NOT NULL | Datas técnicas. |

Constraints/regras candidatas:
- UNIQUE (receipt_id, solicitation_item_id);
- CHECK/validação transacional garantindo que SolicitationItem.solicitation_id corresponda a Receipt.solicitation_id;
- se presentation_status = NAO_APRESENTADO, não permitir objetos de custódia nem amostras;
- se APRESENTADO, exigir quantidade apresentada válida;
- preservar a linha mesmo se não apresentada.

A cardinalidade conceitual preferida é um ReceiptItem por SolicitationItem. Caso a operação precise dividir uma linha declarada em várias parcelas recebidas ou tratar subconjuntos separadamente, a regra atual precisará ser revista antes da implementação.

### 5.6 CustodyObject (ObjetoCustodia)

**Finalidade:** representar o material efetivamente sob guarda institucional antes e depois da criação da amostra.

| Campo lógico | Chave/regra | Observação |
|---|---|---|
| id | PK | Chave interna. |
| receipt_item_id | FK → ReceiptItem.id, NOT NULL | Item de recebimento de origem. |
| object_code | UNIQUE, opcional | Código interno de rastreabilidade, se necessário. |
| object_type | NOT NULL | INDIVIDUAL ou AGRUPADO, conforme vocabulário aprovado. |
| quantity | NOT NULL | Quantidade representada pelo objeto. |
| unit_of_measure | NOT NULL | Unidade correspondente. |
| grouping_basis | NULL | Justificativa e regra técnica para agrupamento. |
| identification_snapshot | NULL | Identificação observada do material no momento da chegada. |
| custody_status | NOT NULL | Estado atual, derivado dos eventos. |
| created_at / created_by_id | NOT NULL | Autoria e criação. |

Regras:
- somente ReceiptItem apresentado pode originar CustodyObject;
- um ReceiptItem pode originar zero ou vários CustodyObjects;
- um CustodyObject pode representar uma unidade física ou um agrupamento homogêneo autorizado;
- quantidade e critério de agrupamento devem ser explícitos;
- não presumir que cada unidade física exige cadastro individual;
- se houver decisão, resultado ou destino independente, o material deve ser discriminado no nível apropriado.

**DEC04/DEC05:** a entidade e as cardinalidades abaixo foram aprovadas pelo usuário como diretriz de desenho do projeto em 2026-11-09. A formalização institucional e a validação dos procedimentos técnicos aplicáveis permanecem pendentes. O fracionamento deve ser uma operação explícita, auditável e quantitativamente reconciliada.

### 5.7 CustodyEvent — mapeamento lógico para ChainOfCustody

**Finalidade:** registrar início, transferência, localização, responsável e encerramento da custódia de cada CustodyObject.

**Decisão de mapeamento recomendada com base na inspeção estática:** CustodyEvent é o nome lógico do conceito; não deve originar uma segunda tabela física. O conceito será representado pela tabela existente chain_of_custody, estendida de forma aditiva.

| Campo lógico | Mapeamento físico atual/proposto | Chave/regra | Observação |
|---|---|---|---|
| id | chain_of_custody.id | PK | Preservar UUID e eventos legados. |
| device_sample_id | chain_of_custody.device_sample_id | FK nullable → DeviceSample.id | Alvo exclusivo dos eventos legados. Tornar nullable em migração aditiva. |
| custody_object_id | nova coluna chain_of_custody.custody_object_id | FK nullable → CustodyObject.id | Alvo exclusivo dos eventos do novo fluxo, antes e depois da criação da amostra. |
| target exclusivity | CHECK novo | exatamente um alvo preenchido | (device_sample_id IS NOT NULL AND custody_object_id IS NULL) OR (device_sample_id IS NULL AND custody_object_id IS NOT NULL). |
| event_type | nova coluna candidata | obrigatório para eventos novos | Entrada, transferência, mudança de localização, devolução, destinação, encerramento ou outra taxonomia aprovada. Não inferir retroativamente para registros antigos. |
| occurred_at | transferred_at | NOT NULL | Instante efetivo do evento. |
| from_user_id / to_user_id | from_custodian_id / to_custodian_id | FKs atuais | Preservar semântica de quem entrega e quem recebe. |
| from_location_id / to_location_id | location_from / location_to | textos atuais | Não são FKs de localização no schema atual. |
| recorded_by_id | nova coluna candidata ou vínculo auditável explícito | FK → User.id | O modelo atual não registra autor do lançamento diretamente na linha de custódia; assinatura/AuditLog não devem ser presumidos como substitutos sem decisão. |
| recorded_at | created_at | NOT NULL | Instante de gravação no banco. |
| reason | reason | NOT NULL | Justificativa existente. |
| condition_note / evidence_reference | notes e/ou vínculo de Evidence | a definir | notes é texto livre e não substitui automaticamente condição estruturada ou evidência vinculada. |
| seal_number / signature_id | colunas atuais | nullable | Preservar compatibilidade. |

A constraint de alvo exclusivo deve ser expressa por CHECK e acompanhada por FKs explícitas. Não usar FK polimórfica. Eventos legados continuam com device_sample_id preenchido e custody_object_id nulo; eventos do novo fluxo usam o inverso. Eventos novos permanecem vinculados ao CustodyObject mesmo depois da criação de DeviceSample, permitindo uma cadeia única sem duplicar o evento inicial.

Os eventos devem ser append-only no fluxo ordinário. A proteção atual contra UPDATE/DELETE deve permanecer ativa. Correções devem gerar evento compensatório ou mecanismo de retificação auditável, sem reescrever silenciosamente a cadeia.

### 5.8 ChecklistTemplate e ChecklistVersion

**Finalidade:** manter checklists por categoria de material com conteúdo versionado e imutável após uso.

**ChecklistTemplate**

| Campo lógico | Chave/regra | Observação |
|---|---|---|
| id | PK | Identificador do tipo de checklist. |
| code | UNIQUE, NOT NULL | Código estável. |
| name | NOT NULL | Nome legível. |
| material_category | NOT NULL | Categoria aplicável. |
| active | NOT NULL | Disponibilidade para novos recebimentos. |

**ChecklistVersion**

| Campo lógico | Chave/regra | Observação |
|---|---|---|
| id | PK | Versão específica. |
| checklist_template_id | FK → ChecklistTemplate.id, NOT NULL | Template de origem. |
| version_number | NOT NULL | Número sequencial. |
| status | NOT NULL | Rascunho, vigente ou obsoleto. |
| effective_from / effective_to | NULL | Vigência. |
| approved_by_id | FK → User.id, conforme governança | Aprovação do conteúdo. |
| approved_at | NULL | Momento da aprovação. |
| content_hash | NOT NULL após publicação | Integridade da versão publicada. |

Constraint candidata: UNIQUE (checklist_template_id, version_number).

### 5.9 ChecklistCriterion

**Finalidade:** definir critérios e regras de resposta dentro de uma versão de checklist.

| Campo lógico | Chave/regra | Observação |
|---|---|---|
| id | PK | Identificador do critério. |
| checklist_version_id | FK → ChecklistVersion.id, NOT NULL | Versão proprietária. |
| criterion_code | NOT NULL | Código dentro da versão. |
| description | NOT NULL | Texto do critério. |
| required | NOT NULL | Se a resposta é obrigatória. |
| criticality | NOT NULL | IMPEDITIVO, SANEAVEL ou INFORMATIVO, após decisão EST06. |
| allowed_responses | conforme implementação | Vocabulário controlado. |
| order_index | NOT NULL | Ordem de exibição. |

Constraint candidata: UNIQUE (checklist_version_id, criterion_code).

### 5.10 ChecklistResponse

**Finalidade:** registrar resposta de critério por item e preservar reavaliações.

| Campo lógico | Chave/regra | Observação |
|---|---|---|
| id | PK | Identificador da resposta/versão. |
| receipt_item_id | FK → ReceiptItem.id, NOT NULL | Item conferido. |
| checklist_criterion_id | FK → ChecklistCriterion.id, NOT NULL | Critério específico de versão. |
| response | NOT NULL | Conforme, não conforme ou não aplicável. |
| observation / justification | condicional | Justificativa exigida conforme regra. |
| evaluated_by_id | FK → User.id, NOT NULL | Responsável. |
| evaluated_at | NOT NULL | Instante da avaliação. |
| supersedes_response_id | FK → ChecklistResponse.id, NULL | Resposta anterior substituída, sem apagá-la. |
| conference_revision | NOT NULL | Identifica a revisão/conferência. |

A conferência deve registrar qual ChecklistVersion foi efetivamente usada. Não alterar conteúdo de versão publicada que já tenha sido aplicada a recebimentos.

### 5.11 Evidence

**Finalidade:** registrar metadados e integridade de arquivos ou documentos que sustentam conferência, pendência, decisão ou custódia.

| Campo lógico | Chave/regra | Observação |
|---|---|---|
| id | PK | Identificador. |
| storage_key | UNIQUE, NOT NULL | Chave opaca do armazenamento; não expor caminho físico. |
| original_filename | NOT NULL | Nome original sanitizado. |
| media_type / size_bytes | NOT NULL | Metadados e limites. |
| sha256 | NOT NULL | Hash de integridade. |
| uploaded_by_id | FK → User.id, NOT NULL | Autor do envio. |
| uploaded_at | NOT NULL | Data/hora. |
| classification / retention | conforme política | Acesso, retenção e descarte. |

Para evitar FKs polimórficas sem integridade, recomenda-se associar Evidence por tabelas de vínculo específicas, por exemplo:
- ChecklistResponseEvidence (checklist_response_id FK, evidence_id FK);
- PendingIssueEvidence (pending_issue_id FK, evidence_id FK);
- ReceiptDecisionEvidence (receipt_decision_id FK, evidence_id FK);
- CustodyEventEvidence (custody_event_id FK, evidence_id FK).

Cada tabela de vínculo deve ter PK própria ou UNIQUE sobre o par de FKs, além de restrições de exclusão apropriadas. A política de armazenamento, antivírus, retenção, backup e controle de acesso ainda precisa ser especificada.

### 5.12 PendingIssue

**Finalidade:** registrar pendências individualizadas e seu ciclo de regularização.

| Campo lógico | Chave/regra | Observação |
|---|---|---|
| id | PK | Identificador. |
| receipt_item_id | FK → ReceiptItem.id, NOT NULL | Item afetado. |
| source_checklist_response_id | FK → ChecklistResponse.id, NULL | Critério que originou a pendência. |
| status | NOT NULL | Pendente, em regularização, regularizada ou não regularizável. |
| description | NOT NULL | Condição a sanar. |
| required_action | NOT NULL | Providência esperada. |
| opened_by_id / opened_at | FK/NOT NULL | Autoria e instante. |
| due_at | NULL | Prazo, se aprovado. |
| closed_by_id / closed_at | NULL | Fechamento e autoria. |

A regularização deve preservar a pendência e a avaliação original. Reabertura ou correção deve gerar histórico/evento próprio.

### 5.13 ReceiptDecision

**Finalidade:** preservar decisões formais individuais por item de recebimento.

| Campo lógico | Chave/regra | Observação |
|---|---|---|
| id | PK | Identificador da decisão. |
| receipt_item_id | FK → ReceiptItem.id, NOT NULL | Item decidido. |
| decision | NOT NULL | ACEITA, PENDENTE ou RECUSADA. |
| rationale | NOT NULL conforme decisão | Fundamentação. |
| checklist_version_id | FK → ChecklistVersion.id, NULL | Versão que fundamenta a decisão, quando aplicável. |
| decided_by_id | FK → User.id, NOT NULL | Autor da decisão. |
| decided_at | NOT NULL | Instante da decisão. |
| supersedes_decision_id | FK → ReceiptDecision.id, NULL | Decisão anterior substituída. |
| status | NOT NULL | Rascunho/formalizada/retificada, conforme governança. |

Não sobrescrever decisão formal. A decisão vigente pode ser obtida pela cadeia de substituição ou por projeção controlada, mas o histórico deve permanecer íntegro.

### 5.14 CoordinationValidation

**Finalidade:** registrar revisão da coordenação quando exigida.

| Campo lógico | Chave/regra | Observação |
|---|---|---|
| id | PK | Identificador. |
| receipt_decision_id | FK → ReceiptDecision.id, NOT NULL | Decisão submetida. |
| status | NOT NULL | Aguardando, aprovada, devolvida ou rejeitada. |
| reviewer_id | FK → User.id, NULL enquanto aguardando | Coordenador/revisor. |
| rationale | condicional | Justificativa da decisão. |
| reviewed_at | NULL enquanto aguardando | Instante da revisão. |
| supersedes_validation_id | FK → CoordinationValidation.id, NULL | Revisão posterior. |

A coordenação não pode dispensar critério impeditivo não conforme. A obrigatoriedade, escopo e segregação de funções dependem de EST01–EST03 e EST10.

### 5.15 ExternalReference

**Finalidade:** armazenar identificadores externos, como número Harpya, sem confundi-los com a chave primária ou o identificador institucional do LIMS.

| Campo lógico | Chave/regra | Observação |
|---|---|---|
| id | PK | Identificador interno. |
| reference_type | NOT NULL | HARPYА ou outro tipo cadastrado (grafia/código a padronizar). |
| reference_value | NOT NULL | Valor externo. |
| solicitation_id | FK → Solicitation.id, NULL | Quando a referência se aplica à solicitação inteira. |
| solicitation_item_id | FK → SolicitationItem.id, NULL | Quando se aplica a um item declarado. |
| device_sample_id | FK → DeviceSample.id, NULL | Quando se aplica à amostra operacional. |
| issuer / issued_at | NULL | Emissor e data, quando conhecidos. |
| created_at / created_by_id | NOT NULL | Auditoria do vínculo. |

Regra: deve existir exatamente um alvo de associação entre solicitação, item ou amostra, conforme CHECK ou modelagem por tabelas de vínculo específicas. A unicidade do par (reference_type, reference_value) deve ser decidida considerando se o emissor reutiliza números em contextos diferentes. Harpya é opcional.

### 5.16 Relação com DeviceSample

**Finalidade:** preservar o modelo operacional existente e vinculá-lo ao fluxo de recebimento somente após aceite final, sem permitir que uma amostra nova reúna vários objetos de custódia.

**Regra aprovada para o desenho-base — relação 1:0..1:**
- cada `CustodyObject` pode estar associado a zero ou uma `DeviceSample`;
- cada `DeviceSample` pode estar associada a zero ou um `CustodyObject` no schema de compatibilidade, pois amostras legadas permanecem sem vínculo;
- para novas amostras criadas pelo fluxo de aceite, o vínculo com exatamente um `CustodyObject` de origem é obrigatório;
- a unicidade de `DeviceSample.custody_object_id` impede que o mesmo objeto origine duas amostras;
- associação N:M e tabela associativa `DeviceSampleCustodyObject` não fazem parte do desenho-base.

**Mapeamento lógico preferencial:** adicionar em `DeviceSample` uma FK nullable `custody_object_id → CustodyObject.id`, com constraint UNIQUE para valores não nulos. A nulabilidade preserva registros legados; a obrigatoriedade para novas amostras deve ser imposta pelo serviço/transação de criação e, se tecnicamente viável, por regra de integridade que distinga o fluxo novo do legado. O nome físico e a localização final da FK dependem da inspeção do schema SQLAlchemy/Alembic.

Compatibilização:
- manter `DeviceSample` e sua PK atual;
- manter `accession_number` até decisão DEC07;
- avaliar se `accession_number` já cumpre a função de identificador institucional, incluindo sequence, unicidade, QR Code, etiquetas, relatórios e integrações;
- não criar campo equivalente sem justificativa;
- não alterar o significado do QR Code sem análise de compatibilidade;
- preservar referências legadas nullable, sem associação retroativa inventada;
- para novas amostras, estabelecer o vínculo com o `CustodyObject` no mesmo fluxo transacional do aceite final.

### 5.17 Identificador institucional

A amostra aceita deve receber identificador institucional único, gerado no backend e protegido por constraint de unicidade. O formato visual e a formalização de \`accession_number\` permanecem sujeitos a DEC07.

A criação deve ser transacional e idempotente. Reenvio da mesma operação, repetição após timeout ou concorrência não pode produzir duas amostras ou dois identificadores para o mesmo objeto/unidade de origem. A chave de idempotência deve estar vinculada à operação de aceite e ao objeto/escopo aprovado, com constraint de banco como última barreira.

## 6. Diagrama relacional preliminar

O diagrama apresenta relações centrais e reflete a cardinalidade aprovada para DEC04/DEC05. Não reproduz todas as tabelas de vínculo de evidências nem fixa nomes físicos definitivos.

\`\`\`mermaid
erDiagram
  REQUESTER ||--o{ SOLICITATION : originates
  USER ||--o{ SOLICITATION : creates
  SOLICITATION ||--|{ SOLICITATION_ITEM : declares
  SOLICITATION ||--o| RECEIPT : has
  RECEIPT ||--|{ RECEIPT_ITEM : records
  SOLICITATION_ITEM ||--o| RECEIPT_ITEM : represented_by
  USER ||--o{ RECEIPT : receives
  RECEIPT_ITEM ||--o{ CUSTODY_OBJECT : materializes
  CUSTODY_OBJECT ||--o{ CHAIN_OF_CUSTODY : has_new_flow_events
  DEVICE_SAMPLE ||--o{ CHAIN_OF_CUSTODY : has_legacy_events
  RECEIPT_ITEM ||--o{ CHECKLIST_RESPONSE : evaluated_by
  CHECKLIST_TEMPLATE ||--|{ CHECKLIST_VERSION : versions
  CHECKLIST_VERSION ||--|{ CHECKLIST_CRITERION : defines
  CHECKLIST_CRITERION ||--o{ CHECKLIST_RESPONSE : answered_by
  RECEIPT_ITEM ||--o{ PENDING_ISSUE : may_have
  RECEIPT_ITEM ||--o{ RECEIPT_DECISION : decided_by
  RECEIPT_DECISION ||--o{ COORDINATION_VALIDATION : reviewed_by
  CUSTODY_OBJECT o|--o| DEVICE_SAMPLE : originates
  DEVICE_SAMPLE ||--o{ LAB_TEST : tested_in
  SOLICITATION ||--o{ EXTERNAL_REFERENCE : references
  SOLICITATION_ITEM ||--o{ EXTERNAL_REFERENCE : references
  DEVICE_SAMPLE ||--o{ EXTERNAL_REFERENCE : references
\`\`\`

**Observações do diagrama:**
- A relação SolicitationItem–ReceiptItem foi desenhada como opcional no lado do recebimento porque o recebimento ainda não existe enquanto a solicitação está em preparação. Quando Receipt existir, deve haver exatamente um ReceiptItem para cada SolicitationItem, inclusive para os não apresentados.
- A relação CUSTODY_OBJECT–DEVICE_SAMPLE é 1:0..1 no desenho-base. A opcionalidade preserva amostras legadas sem vínculo e objetos ainda não aceitos; novas amostras do fluxo de aceite devem ter exatamente um objeto de origem.
- CHAIN_OF_CUSTODY representa um único histórico físico. Cada evento aponta para exatamente um alvo: DeviceSample (eventos legados) ou CustodyObject (eventos do novo fluxo), nunca ambos.
- A relação legada DeviceSample–LabTest é ilustrativa da associação existente identificada no inventário; os nomes físicos e a cardinalidade exata devem ser confirmados no schema.
- As referências externas devem ter exatamente um alvo por registro, apesar de o diagrama mostrar os três possíveis alvos.

## 7. Matriz resumida de cardinalidades e restrições

| Relação | Cardinalidade proposta | Restrição/observação |
|---|---|---|
| Solicitante → Solicitation | 1:N | FK obrigatória na solicitação. |
| Solicitation → SolicitationItem | 1:N | Solicitação formalizada deve possuir ao menos um item. |
| Solicitation → Receipt | 1:0..1 | UNIQUE em Receipt.solicitation_id. |
| Receipt → ReceiptItem | 1:N | Um registro para cada item declarado. |
| SolicitationItem → ReceiptItem | 1:0..1 antes do recebimento; 1:1 após criado | UNIQUE em ReceiptItem.solicitation_item_id. |
| ReceiptItem → CustodyObject | 1:0..N | Apenas quando apresentado; quantidade total deve reconciliar com a apresentada. |
| CustodyObject → CustodyEvent | 1:N | Evento inicial obrigatório na entrada sob custódia. |
| ReceiptItem → ChecklistResponse | 1:N | Respostas versionadas; critérios associados a uma ChecklistVersion. |
| ReceiptItem → PendingIssue | 1:N | Histórico de pendências e regularizações. |
| ReceiptItem → ReceiptDecision | 1:N | Histórico de decisões, sem sobrescrita. |
| ReceiptDecision → CoordinationValidation | 1:0..N | Apenas quando exigida; histórico preservado. |
| CustodyObject → DeviceSample | 1:0..1 | FK nullable e UNIQUE em DeviceSample.custody_object_id; obrigatória para novas amostras do fluxo de aceite. |
| CustodyObject → ChainOfCustody | 1:N | Eventos do novo fluxo vinculados ao objeto, inclusive após a criação da amostra. |
| DeviceSample → ChainOfCustody (legado) | 1:N | Preservar eventos existentes; novos eventos do fluxo integrado apontam para CustodyObject. |
| ChainOfCustody → alvo | exatamente 1 | CHECK XOR entre device_sample_id e custody_object_id. |
| DeviceSample → LabTest | 1:N (a confirmar) | Preservar relação existente. |
| ExternalReference → alvo | exatamente 1 | Solicitação OU item OU amostra, nunca múltiplos simultâneos. |

## 8. Regras de integridade e transações

### 8.1 Restrições que devem ser garantidas no banco

1. PK em todas as entidades persistentes.
2. FKs para relações internas e usuários/autores.
3. UNIQUE em \`Receipt.solicitation_id\`.
4. UNIQUE em \`ReceiptItem.solicitation_item_id\`, além da consistência com o recebimento correspondente.
5. UNIQUE em \`SolicitationItem(solicitation_id, item_number)\`.
6. UNIQUE em \`ChecklistVersion(checklist_template_id, version_number)\`.
7. UNIQUE em \`ChecklistCriterion(checklist_version_id, criterion_code)\`.
8. UNIQUE em \`DeviceSample.custody_object_id\` para valores não nulos; não criar tabela associativa N:M.
9. CHECK de alvo exclusivo em \`chain_of_custody\`: exatamente um entre \`device_sample_id\` e \`custody_object_id\` preenchido.
10. FKs de \`chain_of_custody.device_sample_id\` e \`chain_of_custody.custody_object_id\` com ON DELETE RESTRICT.
11. Índice de consulta \`(custody_object_id, transferred_at)\`, mantendo o índice legado por amostra.
12. Não permitir eventos do novo fluxo sem tipo de evento e autoria explícita, após a decisão sobre as colunas aditivas correspondentes.
13. UNIQUE no identificador institucional efetivamente adotado.
14. CHECKs para quantidades positivas, respostas/estados válidos e alvo único de ExternalReference.
15. Integridade que impeça CustodyObject e DeviceSample para item não apresentado.
16. Proteção contra exclusão de registros referenciados por eventos formais.

Algumas regras cruzam várias tabelas e podem exigir constraints compostas, triggers cuidadosamente justificados ou transações de serviço. Não confiar exclusivamente em validação frontend.

### 8.2 Fluxo transacional de chegada

A operação de registrar a chegada deve, em uma única transação:
1. validar que a solicitação está em estado que permite recebimento;
2. inserir Receipt com arrived_at e received_by_id reais;
3. criar um ReceiptItem para cada SolicitationItem;
4. marcar apresentação de cada item e registrar quantidade apresentada;
5. para cada material apresentado, criar CustodyObject(s) de acordo com a granularidade aprovada;
6. criar evento inicial de custódia com o instante real da chegada e responsável físico;
7. registrar auditoria e commit.

A constraint UNIQUE de Receipt.solicitation_id protege contra concorrência. Se duas requisições simultâneas tentarem registrar a chegada, apenas uma deve confirmar; a outra deve recuperar o recebimento existente ou retornar conflito controlado, sem duplicar itens ou eventos.

### 8.3 Fluxo transacional de aceite e criação da amostra

A operação de aceite final deve, em uma única transação:
1. bloquear/serializar a decisão do ReceiptItem e o(s) CustodyObject(s) de origem;
2. verificar apresentação, conferência concluída, ausência de bloqueios impeditivos, pendências resolvidas e validação de coordenação quando exigida;
3. verificar se a amostra correspondente já foi criada;
4. criar DeviceSample com os dados aprovados;
5. atribuir identificador institucional único no backend;
6. preservar o instante de chegada original e o usuário que recebeu fisicamente o material, sem confundir received_at/received_by com created_at/created_by;
7. criar DeviceSample já com a FK única para o CustodyObject de origem;
8. registrar a continuidade/transferência de custódia como evento apropriado, sem duplicar o evento de chegada;
9. registrar auditoria e, quando exigido, assinatura;
10. commit.

A idempotência deve ser apoiada por chave de operação persistida ou constraint de unicidade do vínculo de origem, além de tratamento de concorrência. Uma verificação apenas em código antes do INSERT não é suficiente.

### 8.4 Estados e dados derivados

O status agregado de Receipt e Solicitation deve ser calculado a partir dos estados dos itens e das validações abertas, ou atualizado por serviço transacional com testes que comprovem consistência. Evitar que o status agregado contradiga os registros individuais.

CustodyObject.custody_status também deve ser derivado dos eventos ou atualizado sob uma única regra transacional. Não permitir divergência entre estado corrente e histórico de eventos.

## 9. Índices e desempenho — candidatos

Índices devem ser confirmados com consultas reais e plano de execução, mas são candidatos:

- Solicitation.solicitation_number UNIQUE;
- Solicitation (requester_id, created_at);
- SolicitationItem (solicitation_id, item_number) UNIQUE;
- Receipt.solicitation_id UNIQUE;
- Receipt (arrived_at, status);
- ReceiptItem (receipt_id, presentation_status, decision/status quando materializado);
- CustodyObject (receipt_item_id);
- CustodyEvent (custody_object_id, occurred_at);
- ChecklistVersion (checklist_template_id, version_number) UNIQUE;
- ChecklistResponse (receipt_item_id, conference_revision);
- PendingIssue (receipt_item_id, status, due_at);
- ReceiptDecision (receipt_item_id, decided_at);
- CoordinationValidation (status, reviewed_at);
- ExternalReference (reference_type, reference_value);
- DeviceSample (custody_object_id) UNIQUE, quando não nulo.

Evitar índices redundantes e indexação indiscriminada de campos de texto/evidência. Validar seletividade e impacto de escrita antes da criação.

## 10. Estratégia de migração e convivência com legado

A estratégia deve ser **aditiva e retrocompatível**, preferencialmente em fases expand-contract:

### Fase A — Expandir
- criar novas tabelas sem remover/renomear estruturas existentes;
- criar FKs nullable de integração quando necessário;
- manter DeviceSample, accession_number, QR Code, ChainOfCustody, ensaios, resultados, assinaturas e auditoria;
- não criar recebimentos fictícios para amostras antigas;
- não preencher solicitation_id/receipt_item_id/custody_object_id por inferência.

### Fase B — Compatibilidade
- atualizar serviços para suportar o fluxo novo e preservar rotas/consultas legadas durante transição;
- decidir como ChainOfCustody receberá eventos pré-amostra;
- garantir que consultas de timeline e QR continuem funcionando;
- testar leitura e escrita de dados antigos e novos.

### Fase C — Transição controlada
- ativar o novo fluxo por configuração/permissão após testes;
- impedir criação direta de amostras fora do fluxo quando a política institucional assim determinar, sem desativar prematuramente integrações existentes;
- monitorar integridade, duplicidade, eventos e reconciliação.

### Fase D — Contract, somente após evidência
- remover estruturas ou caminhos antigos apenas após análise de dependências, plano de rollback, migração validada, aceite e autorização formal.
- Não está proposta nenhuma remoção nesta versão.

Toda migração futura exige backup testado, plano de reversão, testes com cópia representativa, verificação de contagens e integridade referencial, execução controlada e aprovação específica. Nenhuma migração foi criada ou executada nesta atividade.

## 11. Decisões pendentes e impacto no modelo

| Referência | Tema | Impacto relacional | Situação |
|---|---|---|---|
| DEC04 | Nível da custódia e continuidade até a amostra | FK de CustodyEvent/ChainOfCustody e relação com CustodyObject | Diretriz aprovada para o desenho; compatibilização física de ChainOfCustody pendente. |
| DEC05 | Granularidade item/unidade/agrupamento/amostra/corpo de prova | Cardinalidade ReceiptItem–CustodyObject–DeviceSample | Diretriz aprovada para o desenho; validação dos procedimentos técnicos e formalização institucional pendentes. |
| DEC07 | Papel de accession_number e identificador institucional | Reutilizar campo atual ou criar novo; unicidade e compatibilidade QR | Pendente de análise dos usos e aprovação. |
| DEC08 | Migração e referências legadas | FKs nullable, compatibilidade, ausência de backfill inferido | Diretriz aditiva proposta; detalhes de implantação pendentes. |
| EST01 | Perfis que cadastram, recebem e conferem | FKs de autoria e autorização por ação | Pendente. |
| EST02 | Recebedor pode também conferir? | Regras de segregação/constraints de serviço | Pendente. |
| EST03 | Casos que exigem coordenação | Obrigatoriedade de CoordinationValidation | Pendente. |
| EST04 | Destino de material recusado | Eventos de custódia e encerramento | Pendente. |
| EST05 | Fechamento com itens não apresentados | Regra de estado agregado de Receipt/Solicitation | Pendente. |
| EST06 | Classes impeditivo/saneável/informativo | ChecklistCriterion.criticality e bloqueio de aceite | Pendente. |
| EST07 | Ações que exigem assinatura eletrônica | Associação com ElectronicSignature e transações formais | Pendente. |
| EST08 | Correções excepcionais | Versionamento, supersedes e trilha de auditoria | Pendente. |
| EST09 | Prazos de pendência | PendingIssue.due_at e alertas | Pendente. |
| EST10 | Segregação de funções/autoaprovação | Autorização, validação e possíveis constraints de ator distinto | Pendente. |

## 12. Riscos e pontos que exigem inspeção antes do desenho físico

1. **Nomes e tipos reais do schema:** confirmar nomes físicos, PKs, tipos, enums, FKs, índices, triggers e constraints diretamente nos modelos e migrações.
2. **ChainOfCustody:** determinar se é tecnicamente seguro estender a tabela existente ou se é necessária estratégia de compatibilidade alternativa; evitar histórico duplicado.
3. **DeviceSample:** verificar todas as dependências de accession_number, QR, relatórios, testes, integrações e consultas.
4. **Identidade/duplicidade:** a restrição atual observada sobre serial + lote + fabricante pode não representar adequadamente dispositivos sem serial ou unidades repetidas; não reutilizar essa combinação como chave de identidade.
5. **Unidade e agrupamento:** validar reconciliação de quantidade declarada, apresentada e representada por CustodyObjects.
6. **Evidências:** definir armazenamento, antivírus, tamanho, tipos permitidos, retenção, backup, controle de acesso e trilha de download.
7. **Auditoria e assinatura:** definir quais eventos usam AuditLog, quais exigem ElectronicSignature e como evitar commits parciais entre entidades e histórico.
8. **Estados agregados:** decidir se serão persistidos ou derivados, com regra única e testes de consistência.
9. **Perfis:** mapear os perfis existentes para funções reais sem presumir equivalência.
10. **Retenção e proteção de dados:** definir minimização, acesso e descarte de dados pessoais/documentos dos solicitantes.

## 13. Critérios para aprovação do modelo relacional

O modelo estará pronto para detalhamento físico quando:

- DEC04 e DEC05 estiverem decididas, com cardinalidades e exemplos operacionais aprovados;
- DEC07 estiver resolvida após análise de accession_number e QR Code;
- DEC08 possuir plano de compatibilidade legado validado;
- EST01–EST10 estiverem respondidas nos pontos que alteram persistência, transições ou autorização;
- nomes, tipos e constraints do schema atual tiverem sido verificados;
- a estratégia de ChainOfCustody evitar duplicidade e preservar histórico;
- as transações de chegada e aceite estiverem especificadas com idempotência e concorrência;
- os cenários de teste de integridade e migração estiverem definidos;
- responsável funcional, responsável técnico e qualidade revisarem o documento;
- o portão de aprovação aplicável e a autorização específica para implementação forem formalizados.

## 14. Próxima etapa recomendada

Realizar uma **revisão arquitetural do modelo atualizado**, com foco em compatibilização com o schema existente e validação técnica dos cenários operacionais. Em seguida:

1. revisar a análise \`ANALISE_COMPATIBILIDADE_CADEIA_CUSTODIA_DEC04.md\` e confirmar a estratégia de tabela única com alvo exclusivo;
2. decidir COMP02–COMP07, especialmente tipo de evento, autoria explícita, assinatura e projeção de custodiante/localização;
3. reavaliar obrigatoriedade de serial e unicidade serial/lote/fabricante à luz da DEC05;
4. fechar DEC07 e DEC08 e resolver EST01–EST10 nos pontos que afetam persistência e autorização;
5. preparar o mapeamento físico SQLAlchemy e o plano de migração aditiva, sem executá-los;
6. submeter o pacote ao portão de aprovação institucional e obter autorização específica antes de qualquer implementação.

As diretrizes DEC04/DEC05 aprovadas para o desenho não autorizam alterações em código, banco, API, frontend, migrações ou infraestrutura.

## 15. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-09 | Primeira proposta relacional, com entidades, PK/FK, cardinalidades, integridade, convivência com legado e estratégia de migração aditiva. |
| 0.2 | 2026-11-09 | Atualização conforme aprovação do usuário para DEC04/DEC05: CustodyObject–DeviceSample 1:0..1, remoção da associação N:M, atualização do DER, constraints e transação de aceite. Revisão arquitetural/institucional e autorização de implementação permanecem pendentes. |
| 0.3 | 2026-11-09 | Análise de compatibilidade com o schema existente: CustodyEvent passa a ser explicitamente o mapeamento lógico da tabela ChainOfCustody; proposta de duas FKs explícitas com CHECK de alvo exclusivo, preservação de eventos legados e identificação de campos aditivos necessários. Nenhum código ou schema foi alterado. |
