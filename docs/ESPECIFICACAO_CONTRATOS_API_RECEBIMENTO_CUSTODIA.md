# Especificação Proposta dos Contratos da API — Recebimento e Custódia

**Identificador:** API-LIMS-REC-CUST-001  
**Versão:** 0.1  
**Situação:** Proposta de contrato para revisão técnica e funcional. Não aprovada para implementação.  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Data:** 2026-11-09

---

## 1. Objetivo e escopo

Este documento detalha contratos HTTP propostos para a primeira versão do fluxo de recebimento e custódia:

1. registrar a chegada física de uma solicitação e a apresentação individual dos itens;
2. consultar o recebimento e seus itens;
3. consultar o histórico de custódia antes e depois da criação de uma amostra operacional;
4. transferir a custódia de um objeto ainda sem amostra ou já vinculado a uma amostra;
5. formalizar o aceite e criar a DeviceSample de forma atômica;
6. preservar os contratos legados de amostras e custódia durante a transição.

A proposta utiliza os conceitos Solicitation, SolicitationItem, Receipt, ReceiptItem, CustodyObject, ChainOfCustody e DeviceSample. Os nomes de rotas e campos são candidatos para discussão; não constituem API implementada ou aprovada.

**Limite desta atividade:** análise e documentação. Não foram alterados código, modelos, banco, migrações, API, frontend ou testes. Nenhum teste, build ou chamada operacional foi executado.

## 2. Premissas e compatibilidade com a API existente

A inspeção estática da branch main identificou:

- POST /api/v1/samples cria diretamente DeviceSample e exige token de assinatura vinculado a DeviceSample;
- POST /api/v1/custody/transfer transfere a guarda por device_sample_id;
- GET /api/v1/custody/{sample_id}/history consulta eventos legados por amostra;
- GET /api/v1/samples/{sample_id}/custody retorna histórico por amostra;
- GET /api/v1/samples/{sample_id}/timeline retorna a timeline da amostra;
- CustodyOut exige device_sample_id;
- SampleCreate exige serial_number, lot_number, manufacturer, commercial_name e storage_location;
- as rotas atuais são registradas no agregador da API v1.

A API nova deverá coexistir com esses contratos durante a transição. Não se propõe remover, renomear ou alterar de forma incompatível as rotas existentes nesta etapa.

### 2.1 Princípios

- O usuário autenticado é a fonte de identidade do ator; não aceitar user_id de autoria enviado livremente no corpo.
- O instante de chegada é informado/confirmado no registro do recebimento, com validação de fuso e política de lançamento tardio. A autoria do recebimento vem da sessão autenticada.
- Cada ItemDeclarado possui exatamente um ReceiptItem no recebimento principal.
- Item não apresentado não cria CustodyObject nem evento de custódia.
- Um ItemRecebimento pode originar zero ou vários CustodyObjects, conforme a granularidade aprovada.
- Cada evento de custódia novo aponta para exatamente um CustodyObject.
- Cada CustodyObject pode originar no máximo uma DeviceSample.
- O aceite não duplica o evento de chegada e não transfere automaticamente a custódia, salvo regra funcional expressa.
- Chaves de idempotência e constraints persistentes protegem operações críticas.
- Erros de validação e conflito não podem deixar gravações parciais.

## 3. Convenções gerais

### 3.1 Prefixo e formato

Prefixo proposto: /api/v1.

Identificadores internos: UUID em formato canônico. Datas: ISO 8601 com offset explícito na entrada e saída; a política de persistência UTC deve ser confirmada no desenho físico.

Corpos JSON usam snake_case. Campos desconhecidos devem ser rejeitados ou tratados conforme política Pydantic comum da API; recomenda-se rejeição explícita para evitar que o cliente suponha que um campo foi aplicado quando foi ignorado.

### 3.2 Cabeçalhos

| Cabeçalho | Uso |
|---|---|
| Authorization: Bearer | Autenticação existente. |
| Idempotency-Key | Obrigatório nas operações de criação de recebimento e aceite; recomendado para transferência. Valor opaco, único no escopo documentado. |
| If-Match ou version | Controle de concorrência otimista, quando a entidade possuir versão exposta. A escolha final entre cabeçalho e campo de corpo fica pendente. |
| X-Request-ID | Correlação de requisições, se adotado pelo middleware existente. |

O servidor deverá devolver identificador de correlação em respostas de erro quando disponível. Não incluir tokens de assinatura, segredos ou dados pessoais desnecessários em logs de aplicação.

### 3.3 Envelope de erro

Formato candidato:

~~~json
{
  "error": {
    "code": "RECEIPT_ALREADY_EXISTS",
    "message": "Já existe recebimento principal para esta solicitação.",
    "details": {
      "receipt_id": "uuid"
    },
    "request_id": "correlation-id"
  }
}
~~~

Os códigos são estáveis e destinados ao tratamento pelo frontend. A mensagem é destinada à leitura humana. Não retornar stack trace, SQL, dados sigilosos ou detalhes internos.

Códigos HTTP recomendados:

| HTTP | Significado |
|---|---|
| 400 | Corpo ou parâmetro malformado. |
| 401 | Ausência ou invalidade da autenticação. |
| 403 | Usuário autenticado sem autorização para a ação. |
| 404 | Recurso inexistente ou não visível ao usuário, conforme política de segurança. |
| 409 | Conflito de estado, duplicidade, concorrência ou chave de idempotência incompatível. |
| 422 | Dados sintaticamente válidos, mas inconsistentes com regras de domínio. |
| 428 | Pré-condição de versão/concorrência obrigatória não informada, se adotado If-Match. |
| 500 | Falha inesperada; sem detalhes internos na resposta. |

## 4. Registro da chegada e do recebimento

### 4.1 Endpoint proposto

**POST /api/v1/solicitations/{solicitation_id}/receipt**

Responsabilidade: registrar uma única chegada física para a solicitação, criar o Receipt e todos os ReceiptItems correspondentes, registrar a apresentação de cada item, criar os CustodyObjects aplicáveis e registrar os eventos iniciais de custódia na mesma transação.

A escolha de um único comando transacional evita que o recebimento fique parcialmente criado. A interface poderá organizar o preenchimento em telas e modal, mas o comando formal de confirmação deve validar o conjunto completo.

### 4.2 Cabeçalhos

- Authorization: Bearer obrigatório.
- Idempotency-Key obrigatório.
- Content-Type: application/json.

### 4.3 Corpo candidato

~~~json
{
  "arrived_at": "2026-11-09T08:45:00-03:00",
  "arrival_location": "Setor de recebimento",
  "external_protocol": "HARPYA-123456",
  "notes": "Entrega acompanhada de documentação.",
  "items": [
    {
      "solicitation_item_id": "uuid-item-1",
      "presentation_status": "PRESENTED",
      "presented_quantity": 10,
      "custody_objects": [
        {
          "grouping_description": "Dez unidades agrupadas para avaliação conjunta",
          "represented_quantity": 10,
          "initial_location": "Área de recebimento",
          "seal_number": null,
          "notes": null
        }
      ]
    },
    {
      "solicitation_item_id": "uuid-item-2",
      "presentation_status": "NOT_PRESENTED",
      "presented_quantity": 0,
      "custody_objects": []
    }
  ]
}
~~~

Este exemplo é ilustrativo. A definição de represented_quantity, grouping_description e a reconciliação entre quantidade apresentada e objetos de custódia dependem da regra operacional de agrupamento/fracionamento (DEC05/COMP06). Não se deve exigir que cada unidade física tenha objeto individual se o procedimento admitir guarda agrupada.

### 4.4 Regras de validação

1. A solicitação deve existir e estar em estado que permita recebimento.
2. Não pode existir outro Receipt principal para a solicitação.
3. O conjunto de solicitation_item_id deve corresponder exatamente aos itens declarados da solicitação: nenhum item omitido, repetido ou estranho.
4. Para PRESENTED, presented_quantity deve ser positiva e os CustodyObjects devem representar o material recebido conforme regra aprovada.
5. Para NOT_PRESENTED, presented_quantity deve ser zero e custody_objects deve ser vazio.
6. NOT_PRESENTED não é decisão de recusa e não cria custódia.
7. Não aceitar quantidade negativa, inconsistência de soma ou objetos sem item de origem.
8. arrived_at deve ter offset explícito; lançamento tardio ou data anterior ao instante atual deve obedecer à política a aprovar.
9. received_by_id deve ser obtido do usuário autenticado que efetivamente registra a chegada, ou de fluxo autorizado que identifique o recebedor físico real. Não confiar em autoria arbitrária enviada pelo cliente.
10. O instante efetivo da chegada deve ser preservado, mesmo se conferência e aceite ocorrerem posteriormente.

### 4.5 Resposta de sucesso

**201 Created** na primeira execução.

~~~json
{
  "receipt": {
    "id": "uuid-receipt",
    "solicitation_id": "uuid-solicitation",
    "arrived_at": "2026-11-09T08:45:00-03:00",
    "received_by": {
      "id": "uuid-user",
      "display_name": "Servidor responsável"
    },
    "arrival_location": "Setor de recebimento",
    "status": "IN_CONFERENCE",
    "created_at": "2026-11-09T08:46:12-03:00"
  },
  "items": [
    {
      "id": "uuid-receipt-item-1",
      "solicitation_item_id": "uuid-item-1",
      "presentation_status": "PRESENTED",
      "presented_quantity": 10,
      "custody_objects": [
        {
          "id": "uuid-object-1",
          "status": "IN_CUSTODY",
          "represented_quantity": 10
        }
      ]
    },
    {
      "id": "uuid-receipt-item-2",
      "solicitation_item_id": "uuid-item-2",
      "presentation_status": "NOT_PRESENTED",
      "presented_quantity": 0,
      "custody_objects": []
    }
  ],
  "audit_log_id": 12345
}
~~~

### 4.6 Idempotência e conflitos

- Repetição com mesma Idempotency-Key e mesmo conteúdo lógico: retornar o mesmo resultado confirmado, sem criar outro Receipt, ReceiptItem, CustodyObject ou evento.
- Mesma chave com conteúdo diferente: 409 IDEMPOTENCY_KEY_REUSED.
- Chave diferente para solicitação que já possui Receipt: 409 RECEIPT_ALREADY_EXISTS, informando o identificador existente quando autorizado.
- Duas requisições concorrentes: apenas uma confirma. A outra recupera o resultado idempotente ou recebe conflito controlado.
- Falha em qualquer criação de item/objeto/evento: rollback integral.

### 4.7 Consulta do recebimento

**GET /api/v1/receipts/{receipt_id}**

Retorna dados gerais, todos os ReceiptItems, apresentação, conferência, pendências, decisões, objetos de custódia e estado de validação, respeitando paginação/limites se o volume exigir.

**GET /api/v1/solicitations/{solicitation_id}/receipt**

Retorna o recebimento principal existente. Se não houver, 404 RECEIPT_NOT_FOUND; não criar registro por efeito colateral de GET.

O payload de leitura deverá distinguir explicitamente:
- declarado na solicitação;
- apresentado na chegada;
- quantidade apresentada;
- objetos de custódia criados;
- item não apresentado;
- estado de conferência e decisão.

## 5. Histórico unificado

### 5.1 Endpoint por objeto

**GET /api/v1/custody/objects/{custody_object_id}/history**

Consulta o histórico completo do CustodyObject, antes e depois da criação de DeviceSample.

Parâmetros candidatos:
- from: instante inicial ISO 8601;
- to: instante final ISO 8601;
- event_type: filtro repetível;
- limit: 1 a 100, padrão 50;
- cursor: cursor opaco para paginação estável;
- order: asc ou desc, padrão asc.

Resposta candidata:

~~~json
{
  "target": {
    "type": "CUSTODY_OBJECT",
    "id": "uuid-object"
  },
  "linked_sample": {
    "id": "uuid-sample",
    "accession_number": "LIMS-2026-000321"
  },
  "items": [
    {
      "event_id": "uuid-event",
      "event_type": "RECEIPT",
      "occurred_at": "2026-11-09T08:45:00-03:00",
      "recorded_at": "2026-11-09T08:46:12-03:00",
      "from_custodian": null,
      "to_custodian": {
        "id": "uuid-user",
        "display_name": "Servidor responsável"
      },
      "location_from": null,
      "location_to": "Setor de recebimento",
      "reason": "Chegada física do material",
      "recorded_by": {
        "id": "uuid-user",
        "display_name": "Servidor responsável"
      },
      "signature_id": null,
      "notes": null,
      "source": "NEW_FLOW"
    }
  ],
  "page": {
    "next_cursor": null,
    "has_more": false
  }
}
~~~

O campo linked_sample será null enquanto o objeto não tiver amostra. O exemplo não define definitivamente o enum event_type nem a exigência de assinatura.

### 5.2 Endpoint por amostra

**GET /api/v1/samples/{sample_id}/custody**

A rota existente deverá manter o comportamento e o formato legados para amostras antigas. Para amostra nova vinculada a CustodyObject, a implementação futura deverá resolver o objeto e devolver os eventos do objeto, adaptados ao contrato de resposta acordado.

A transição não deve duplicar eventos: uma amostra nova consulta a cadeia do objeto; uma amostra legada sem vínculo consulta device_sample_id.

### 5.3 Timeline

**GET /api/v1/samples/{sample_id}/timeline**

Manter o endpoint atual. Para amostra nova, a timeline deverá incorporar os eventos de custódia do objeto associado e manter eventos de ensaios, assinaturas, CAPA e alterações de status. O evento sintético de chegada não pode usar a localização corrente como se fosse a localização original.

A timeline de um objeto ainda sem amostra poderá ser disponibilizada separadamente:

**GET /api/v1/custody/objects/{custody_object_id}/timeline**

Esse endpoint é opcional; o histórico de custódia é o contrato mínimo obrigatório. A composição de uma timeline completa de recebimento depende dos demais eventos funcionais e pode ser definida em etapa posterior.

## 6. Transferência de custódia

### 6.1 Endpoint proposto para novo fluxo

**POST /api/v1/custody/objects/{custody_object_id}/transfers**

Responsabilidade: registrar transferência de guarda do objeto, com ou sem DeviceSample já criada.

Corpo candidato:

~~~json
{
  "to_custodian_id": "uuid-user-destino",
  "occurred_at": "2026-11-09T10:30:00-03:00",
  "reason": "Encaminhamento para área de ensaios",
  "location_from": "Área de recebimento",
  "location_to": "Laboratório de ensaios",
  "seal_number": null,
  "notes": "Material conferido e acondicionado.",
  "expected_version": 3
}
~~~

O custodiante de origem deverá ser derivado do estado corrente confiável do objeto, não informado livremente pelo cliente. O ator que registra a operação é obtido da autenticação. O instante de registro é gerado pelo servidor; occurred_at representa o instante efetivo da transferência e deve seguir política de lançamento retroativo.

### 6.2 Assinatura

A rota atual consome token de assinatura vinculado a DeviceSample e action TRANSFER. Para o novo fluxo, o alvo de assinatura deverá ser o CustodyObject/evento, conforme decisão EST07. Não se deve consumir assinatura vinculada a DeviceSample inexistente.

A assinatura obrigatória ou opcional nesta operação permanece pendente de decisão institucional. O contrato final deverá indicar o mecanismo de pré-assinatura sem permitir assinatura cega ou reutilização indevida.

### 6.3 Resposta

**201 Created**

~~~json
{
  "event": {
    "id": "uuid-event",
    "target": {
      "type": "CUSTODY_OBJECT",
      "id": "uuid-object"
    },
    "event_type": "TRANSFER",
    "occurred_at": "2026-11-09T10:30:00-03:00",
    "recorded_at": "2026-11-09T10:31:10-03:00",
    "from_custodian_id": "uuid-user-origem",
    "to_custodian_id": "uuid-user-destino",
    "location_from": "Área de recebimento",
    "location_to": "Laboratório de ensaios",
    "reason": "Encaminhamento para área de ensaios",
    "signature_id": null
  },
  "object_version": 4,
  "audit_log_id": 12346
}
~~~

### 6.4 Concorrência e erros de domínio

- Exigir expected_version ou If-Match para impedir transferência sobre estado desatualizado.
- Bloquear/serializar atualização do objeto e criação do evento.
- 409 CUSTODY_VERSION_CONFLICT quando a versão estiver desatualizada.
- 409 CUSTODY_STATE_CONFLICT quando o objeto estiver encerrado ou em estado que não permita transferência.
- 403 CUSTODY_TRANSFER_FORBIDDEN quando o ator não tiver permissão.
- Não atualizar projeções de custodiante/localização sem criar o evento correspondente na mesma transação.
- Repetição com mesma Idempotency-Key não cria evento duplicado.

### 6.5 Compatibilidade da rota antiga

**POST /api/v1/custody/transfer** permanece disponível para DeviceSample legada durante a transição. Não deve ser usada para eventos do novo fluxo vinculados a CustodyObject. Eventual migração de clientes deverá ocorrer depois de período de compatibilidade e aprovação.

## 7. Aceite e criação de DeviceSample

### 7.1 Endpoint proposto

**POST /api/v1/custody/objects/{custody_object_id}/acceptance**

Responsabilidade: formalizar o aceite final e criar uma única DeviceSample, atomicamente.

Cabeçalhos:
- Authorization obrigatório;
- Idempotency-Key obrigatório;
- mecanismo de assinatura conforme EST07, quando aplicável;
- controle de versão/estado obrigatório.

Corpo candidato:

~~~json
{
  "decision": "ACCEPTED",
  "reason": "Documentação e conferência atendem aos critérios aplicáveis.",
  "expected_object_version": 4,
  "sample_data": {
    "serial_number": null,
    "lot_number": "LOTE-2026-01",
    "manufacturer": "Fabricante",
    "commercial_name": "Dispositivo médico",
    "model": null,
    "registration_number": null,
    "description": "Descrição técnica",
    "storage_location": "Laboratório de ensaios",
    "attributes": {}
  },
  "coordination_validation_id": null
}
~~~

O exemplo usa serial_number nulo para evidenciar que o contrato não deve impor número de série universalmente. A possibilidade técnica depende de revisão do schema e da regra de identidade (COMP04). O campo storage_location também deverá ser reconciliado com o modelo de custódia; não deve substituir o histórico de localização.

A decisão pode não precisar ser enviada novamente se já estiver registrada em endpoint próprio. Nesse caso, o comando de aceite deverá referenciar a decisão persistida, sem duplicá-la. Essa escolha de desenho permanece aberta.

### 7.2 Pré-condições

O servidor deve validar novamente, dentro da transação:

- objeto e ReceiptItem existentes;
- apresentação confirmada;
- conferência concluída;
- nenhum impedimento aberto;
- regularizações e evidências necessárias concluídas;
- decisão de aceite válida;
- validação de coordenação quando exigida;
- objeto elegível e não encerrado/recusado definitivamente;
- ausência de DeviceSample vinculada;
- dados mínimos da amostra conforme tipo de dispositivo e regra aprovada;
- ator autorizado e segregação de funções conforme EST01–EST10.

### 7.3 Resposta

**201 Created** na primeira confirmação.

~~~json
{
  "acceptance": {
    "id": "uuid-acceptance",
    "custody_object_id": "uuid-object",
    "decision": "ACCEPTED",
    "decided_at": "2026-11-09T11:15:00-03:00",
    "decided_by": {
      "id": "uuid-user",
      "display_name": "Responsável pelo aceite"
    }
  },
  "sample": {
    "id": "uuid-sample",
    "accession_number": "LIMS-2026-000321",
    "custody_object_id": "uuid-object",
    "received_at": "2026-11-09T08:45:00-03:00",
    "received_by_id": "uuid-recebedor",
    "created_at": "2026-11-09T11:15:00-03:00"
  },
  "audit_log_id": 12347,
  "signature_id": null
}
~~~

O número accession_number é ilustrativo. A DEC07 deverá confirmar se o campo existente será mantido como identificador institucional. O QR Code atual deverá continuar apontando para a mesma identidade de DeviceSample.

### 7.4 Atomicidade e idempotência

A transação deverá bloquear o objeto, validar as pré-condições, criar a amostra vinculada, gerar o identificador, preservar received_at e received_by_id originais, registrar auditoria/assinatura aplicáveis e armazenar o resultado idempotente. Qualquer falha obrigatória deve reverter o conjunto.

Comportamento:
- mesma chave e mesmo conteúdo lógico: devolver o mesmo acceptance e sample;
- mesma chave e conteúdo divergente: 409 IDEMPOTENCY_KEY_REUSED;
- chave diferente, objeto já aceito: devolver conflito ou resultado existente conforme política de repetição aprovada;
- concorrência: no máximo uma DeviceSample por objeto;
- timeout após commit: repetição recupera a resposta confirmada.

### 7.5 Erros de aceite

| Código sugerido | HTTP | Condição |
|---|---:|---|
| CUSTODY_OBJECT_NOT_FOUND | 404 | Objeto inexistente. |
| ACCEPTANCE_BLOCKED | 422 | Critério impeditivo ou pendência aberta. |
| COORDINATION_VALIDATION_REQUIRED | 422 | Validação obrigatória ausente. |
| CUSTODY_OBJECT_NOT_ELIGIBLE | 409 | Estado incompatível com aceite. |
| SAMPLE_ALREADY_CREATED | 409 | Objeto já possui DeviceSample, sem repetição idempotente reconhecida. |
| CUSTODY_VERSION_CONFLICT | 409 | Estado alterado desde a leitura. |
| IDEMPOTENCY_KEY_REUSED | 409 | Mesma chave com payload divergente. |
| SIGNATURE_REQUIRED | 422 | Assinatura obrigatória ausente, após aprovação de EST07. |

## 8. Decisões de API que permanecem pendentes

| ID | Decisão | Motivo |
|---|---|---|
| API01 | Escolher nomes finais de rotas e recursos | Consistência REST e padrão já adotado no projeto. |
| API02 | Definir criação do recebimento como comando único ou fluxo em rascunho + confirmação | Interface pode salvar parcialmente, mas a chegada formal deve ser atômica. |
| API03 | Definir contrato de agrupamento/quantidade de CustodyObjects | DEC05/COMP06 e procedimentos técnicos. |
| API04 | Definir event_type, autoria explícita e timestamps físicos | COMP02 e análise do schema atual. |
| API05 | Definir assinatura por operação e alvo | EST07. |
| API06 | Definir If-Match versus expected_version no corpo | Padronização de concorrência. |
| API07 | Definir política de chave idempotente, retenção e replay | Segurança e confiabilidade de operações críticas. |
| API08 | Definir payload mínimo de DeviceSample por classe de dispositivo | COMP04; não exigir serial universalmente sem base. |
| API09 | Definir status HTTP e política de retorno quando objeto já aceito | Idempotência semântica e experiência do cliente. |
| API10 | Definir escopos de autorização e segregação de funções | EST01–EST03 e EST10. |
| API11 | Definir paginação e snapshot de consulta do histórico | Eventos novos durante navegação. |
| API12 | Definir política de data retroativa, lançamento tardio e fuso | Integridade cronológica e auditoria. |

## 9. Matriz de compatibilidade

| Contrato atual | Tratamento proposto |
|---|---|
| POST /samples | Preservar durante transição; fluxo novo cria amostra pelo aceite. Desativação futura depende de decisão e plano de migração. |
| GET /samples | Preservar; avaliar filtros por objeto/recebimento em etapa própria. |
| GET /samples/{id} | Preservar; incluir vínculo com CustodyObject somente após versionamento/compatibilidade do schema. |
| GET /samples/{id}/timeline | Preservar; timeline da amostra nova incorpora histórico do objeto sem duplicação. |
| GET /samples/{id}/custody | Preservar; resolver objeto para amostra nova e FK legada para amostra antiga. |
| POST /custody/transfer | Preservar para fluxo legado por DeviceSample. |
| GET /custody/{sample_id}/history | Preservar para legado; novo endpoint por objeto atende pré-amostra. |
| GET /samples/{id}/qrcode e PNG | Preservar accession_number, payload assinado e resolução do QR Code. |
| POST /solicitations/{id}/receipt | Novo contrato proposto. |
| GET /receipts/{id} | Novo contrato proposto. |
| GET /custody/objects/{id}/history | Novo contrato proposto. |
| POST /custody/objects/{id}/transfers | Novo contrato proposto. |
| POST /custody/objects/{id}/acceptance | Novo contrato proposto. |

## 10. Segurança, auditoria e observabilidade

- Todas as rotas exigem autenticação, salvo exceção explicitamente aprovada.
- Autorização deve ser verificada no backend por ação e recurso; ocultar botão no frontend não é controle de acesso.
- O servidor determina o ator autenticado e o instante de registro.
- O cliente informa somente os dados de negócio permitidos e o instante efetivo quando a política admitir.
- Toda operação formal registra audit log com entidade, ação, ator, instante, resultado e correlação.
- Eventos de custódia permanecem append-only; correções serão retificações formais, conforme EST08.
- Assinatura eletrônica deve estar vinculada ao alvo/ato correto, após decisão EST07.
- Não registrar conteúdo integral de documentos ou dados sensíveis em logs técnicos.
- Respostas não devem expor dados de solicitantes ou usuários além do necessário à rastreabilidade.
- Métricas recomendadas: conflitos de recebimento duplicado, replay idempotente, conflitos de versão, falhas de aceite, latência do histórico e inconsistências de projeção.

## 11. Critérios para aprovação da especificação

A especificação estará pronta para virar contrato OpenAPI detalhado quando:

1. nomes de recursos e rotas forem revisados;
2. o fluxo de rascunho e confirmação do recebimento for definido;
3. DEC05/COMP06 definirem a representação de agrupamento e quantidade;
4. COMP02/COMP03 definirem campos e semântica do evento;
5. EST07 definir assinatura;
6. COMP04 definir dados de identidade de amostra;
7. DEC07/DEC08 definirem identificador e compatibilidade legada;
8. perfis e segregação de funções forem aprovados;
9. política de idempotência, concorrência, fuso e lançamento tardio for definida;
10. responsáveis funcionais, técnicos e de qualidade revisarem o documento.

## 12. Próxima etapa recomendada

Submeter os contratos propostos para revisão e fechar as decisões API01–API12. Em seguida, produzir uma versão OpenAPI/JSON Schema independente de implementação, incluindo exemplos e catálogo de erros. Somente após aprovação e autorização específica será possível planejar alterações de backend, banco, frontend e testes.

**Este documento não autoriza implementação. Nenhum código, schema, banco, migração, API, frontend ou teste foi alterado.**

## 13. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-09 | Primeira proposta dos contratos HTTP para recebimento, histórico unificado, transferência de custódia, aceite e compatibilidade legada. |
