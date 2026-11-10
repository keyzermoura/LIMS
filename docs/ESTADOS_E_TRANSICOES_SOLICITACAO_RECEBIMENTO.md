# Estados e Transições — Solicitação e Recebimento

**Identificador:** EST-REC-001  
**Versão:** 1.4  
**Situação:** Proposta consolidada após auditoria de consistência EST01–EST10 e alinhamento ao M0.2; não aprovada para implementação  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Data:** 2026-11-10

---

## 1. Objetivo e limites

Definir uma proposta de estados, transições, pré-condições, perfis e eventos de auditoria para o fluxo de solicitação e recebimento físico do LIMS. O documento detalha o modelo conceitual MOD-DOM-001 e deverá ser revisado com o responsável funcional e a qualidade.

Não constitui especificação física definitiva nem autorização para alterar código, banco, API, frontend ou infraestrutura. Os nomes de estados são conceituais e poderão ser ajustados após validação.

## 2. Princípios de modelagem

1. Não concentrar o ciclo inteiro em um único campo de status.
2. Manter estados separados para Solicitação, Recebimento, apresentação do item, conferência, decisão, validação e custódia.
3. Uma transição formal deve registrar ator, papel, data/hora, estado anterior, estado novo, justificativa e evidências aplicáveis.
4. Não permitir que uma mudança de estado apague ou sobrescreva uma decisão anterior.
5. Bloqueios impeditivos não podem ser dispensados pela coordenação.
6. Reenvios e concorrência não podem gerar recebimentos, amostras ou identificadores duplicados.
7. O estado agregado do recebimento deve ser derivado das situações de seus itens, sem substituir o histórico individual.

## 3. Dimensões de estado

### 3.1 Solicitação

| Estado | Significado |
|---|---|
| RASCUNHO | Cadastro iniciado, ainda não submetido. |
| SUBMETIDA | Solicitação formalizada e disponível para recebimento. |
| RECEBIMENTO_REGISTRADO | Chegada física principal registrada. |
| EM_TRATAMENTO | Existem itens em conferência, pendência ou validação. |
| CONCLUIDA | Todos os itens foram encerrados conforme as regras do processo. |
| CANCELADA | Solicitação cancelada por usuário autorizado, com motivo e sem apagar histórico. |

### 3.2 Recebimento

| Estado | Significado |
|---|---|
| REGISTRADO | Chegada principal registrada; itens ainda não necessariamente conferidos. |
| EM_CONFERENCIA | Conferência de um ou mais itens iniciada. |
| AGUARDANDO_REGULARIZACAO | Existe ao menos uma pendência que impede a decisão final de item. |
| AGUARDANDO_COORDENACAO | Existe decisão ou exceção que exige revisão da coordenação. |
| PARCIALMENTE_DECIDIDO | Há itens encerrados e outros ainda em tratamento. |
| CONCLUIDO | Todos os itens possuem desfecho permitido e não há ação obrigatória pendente. |
| CANCELADO | Registro cancelado por exceção formal autorizada; chegada e custódia histórica permanecem preservadas. |

### 3.3 Apresentação do item

| Estado | Significado |
|---|---|
| AGUARDANDO_CHEGADA | Item declarado ainda não avaliado na chegada. |
| APRESENTADO | Material correspondente foi fisicamente apresentado. |
| NAO_APRESENTADO | Material não chegou na ocasião registrada. |

NAO_APRESENTADO é estado de apresentação, não resultado de conferência ou decisão de recusa. Não inicia custódia e não permite criação de amostra operacional.

### 3.4 Conferência do item

| Estado | Significado |
|---|---|
| NAO_INICIADA | Conferência ainda não iniciada. |
| EM_ANDAMENTO | Critérios aplicáveis estão sendo avaliados. |
| CONCLUIDA | Critérios obrigatórios foram respondidos e a avaliação foi formalizada. |

Cada resposta de checklist terá resultado próprio: CONFORME, NAO_CONFORME ou NAO_APLICAVEL, com justificativa obrigatória quando aplicável. A classificação do critério (impeditivo, saneável ou informativo) deve vir de checklist versionado.

### 3.5 Regularização / Pendências

Cada Pendência possui ciclo próprio, vinculado ao ItemRecebimento e, quando a irregularidade atingir material discriminado, ao ObjetoCustodia correspondente. A situação da pendência não deve ser confundida com a decisão técnica do item/objeto nem com o estado agregado do recebimento.

| Estado/condição | Significado | Natureza |
|---|---|---|
| PENDENTE | Providência requerida; aguardando início ou atendimento. | Aberto |
| EM_REGULARIZACAO | Providência em andamento. | Aberto |
| AGUARDANDO_REAVALIACAO | Evidência ou resposta recebida; aguarda avaliação técnica. | Aberto |
| REGULARIZADA | Providência avaliada e considerada satisfatória por responsável autorizado. | Encerrado por regularização |
| PRAZO_VENCIDO | Prazo expirou sem regularização validada. | Indicador de controle; permanece aberto |
| NAO_REGULARIZAVEL | Há decisão formal fundamentada de que a condição não pode ser sanada no fluxo. | Desfecho da pendência; não equivale automaticamente à recusa do material |
| CANCELADA | Pendência cancelada por erro ou perda justificada do objeto, com autorização e histórico. | Encerrado por cancelamento justificado |

Regras obrigatórias:

1. A contagem do prazo começa somente após comunicação formal comprovável ao responsável pela regularização.
2. Prazos, antecedências de alertas e canais são parametrizáveis e dependem de aprovação institucional.
3. PRAZO_VENCIDO não encerra a pendência, não produz recusa automática e não encerra custódia.
4. A recepção de evidência não encerra a pendência; é necessária reavaliação favorável, registrada por responsável autorizado.
5. NAO_REGULARIZAVEL exige decisão formal fundamentada e autoridade competente; quando afetar aceite/recusa, aplica-se EST03, EST06 e EST10. Não é sinônimo de RECUSADA e não substitui a decisão final do objeto/item.
6. REGULARIZADA exige evidência, reavaliação, ator, data/hora e resultado.
7. A pendência original e todas as comunicações, prorrogações e avaliações permanecem no histórico.
8. O encerramento da pendência não encerra automaticamente a custódia nem concede aceite técnico.

### 3.6 Decisão do item ou ObjetoCustodia

A decisão será registrada no menor nível em que aceite, recusa, rastreabilidade ou destinação possam divergir:

- **ObjetoCustodia:** nível decisório preferencial quando o ItemRecebimento originar um ou mais objetos com avaliação, resultado ou destino potencialmente independente.
- **ItemRecebimento:** poderá receber decisão diretamente quando não houver discriminação adicional necessária e a decisão for efetivamente única para todo o material apresentado.
- **ItemRecebimento com múltiplos objetos:** sua situação será consolidada a partir das decisões dos objetos; não poderá ocultar decisões divergentes.

| Estado | Significado |
|---|---|
| NAO_DECIDIDA | Ainda não há decisão formal no nível aplicável. |
| ACEITA | Requisitos atendidos, pendências impeditivas resolvidas e validações obrigatórias concluídas. |
| PENDENTE | Decisão final bloqueada por regularização, evidência, avaliação ou validação ainda pendente. |
| RECUSADA | Material não admitido, com fundamento e evidências aplicáveis, submetido à validação da coordenação quando exigida. |
| PARCIALMENTE_DECIDIDO | Estado agregado do ItemRecebimento quando houver objetos com decisões diferentes ou ainda incompletas. |

Regras:

1. A decisão de um ObjetoCustodia não altera automaticamente a decisão dos demais objetos do mesmo item.
2. O item só pode ser consolidado como integralmente ACEITO quando todos os objetos apresentados estiverem aceitos e todas as validações obrigatórias concluídas.
3. Um objeto recusado permanece sob custódia até destinação efetiva; a recusa não encerra a custódia.
4. A decisão original nunca é sobrescrita; retificação gera novo ato vinculado ao anterior, conforme EST08.
5. Item NAO_APRESENTADO não recebe decisão de aceite/recusa nem gera objeto ou amostra.

### 3.7 Validação da coordenação

| Estado | Significado |
|---|---|
| NAO_EXIGIDA | Regras do fluxo não exigem validação. |
| AGUARDANDO | Encaminhamento formal aguardando coordenação. |
| APROVADA | Coordenação validou a decisão dentro de sua competência. |
| DEVOLVIDA | Coordenação devolveu para complementação ou correção. |
| REJEITADA | Coordenação não validou a decisão, com justificativa. |

A coordenação não pode converter critério impeditivo não conforme em conforme nem dispensar requisito obrigatório. A devolução/rejeição deve indicar o motivo e a ação necessária.

### 3.8 Custódia

| Estado | Significado |
|---|---|
| NAO_INICIADA | Não há material apresentado nem custódia iniciada. |
| SOB_GUARDA | Objeto sob responsabilidade institucional confirmada. |
| TRANSFERENCIA_PENDENTE | Transferência solicitada, mas ainda não confirmada pelo destinatário. |
| SOB_NOVA_RESPONSABILIDADE | Transferência confirmada; novo responsável e localização passam a ser vigentes. |
| ENCERRADA | Entrega/devolução ou destinação autorizada efetivamente concluída e formalizada. |

A custódia é controlada por ObjetoCustodia. O estado atual e o responsável/localização atuais são uma visão derivada do último evento confirmado; o histórico de eventos de guarda e transferência é imutável e não deve ser substituído pelo estado atual.

Durante TRANSFERENCIA_PENDENTE, a responsabilidade permanece com o custodiante de origem até a confirmação do recebedor de destino. Solicitação de transferência, por si só, não transfere a responsabilidade.

A custódia começa na chegada física, independentemente de aceite. Recusa, vencimento/cancelamento de pendência ou conclusão administrativa do recebimento não encerram custódia. O encerramento exige destinação efetiva, destinatário/unidade, responsável pela entrega, data/hora reais e evidência/comprovante quando aplicável, conforme EST04 e EST07.

## 4. Transições permitidas — proposta

### 4.1 Solicitação

| Origem | Destino | Quem pode executar | Pré-condições | Evento/auditoria |
|---|---|---|---|---|
| RASCUNHO | SUBMETIDA | Usuário interno autorizado | Solicitante e ao menos um item declarados; campos obrigatórios válidos. | SOLICITACAO_SUBMETIDA |
| SUBMETIDA | RECEBIMENTO_REGISTRADO | Sistema, após criação transacional do recebimento | Solicitação válida; ainda não existe recebimento principal. | RECEBIMENTO_VINCULADO |
| RECEBIMENTO_REGISTRADO | EM_TRATAMENTO | Sistema | Conferência iniciada ou pendência/validação criada. | SOLICITACAO_EM_TRATAMENTO |
| EM_TRATAMENTO | CONCLUIDA | Sistema | Todos os itens possuem desfecho permitido; nenhuma pendência ou validação obrigatória aberta. | SOLICITACAO_CONCLUIDA |
| RASCUNHO ou SUBMETIDA | CANCELADA | Perfil autorizado a definir | Justificativa e verificação de que não há material sob custódia sem destinação. | SOLICITACAO_CANCELADA |

Após registro de chegada física, cancelamento não pode apagar o recebimento nem encerrar custódia automaticamente. Exige tratamento formal dos materiais.

### 4.2 Recebimento

O estado do Recebimento é agregado e derivado dos estados dos ItemRecebimento, das Pendências, das validações obrigatórias e dos ObjetosCustodia. Não deve ser usado para substituir os estados individuais.

| Origem | Destino | Responsável | Pré-condições e bloqueios |
|---|---|---|---|
| inexistente | REGISTRADO | Recepção autorizada | Solicitação submetida; registrar chegada efetiva e responsável; garantir unicidade do recebimento principal. |
| REGISTRADO | EM_CONFERENCIA | Sistema/conferente autorizado | Ao menos um item apresentado apto a iniciar conferência; checklist aplicável e versionado disponível. |
| EM_CONFERENCIA | AGUARDANDO_REGULARIZACAO | Sistema | Existe Pendência aberta que impede decisão final. |
| EM_CONFERENCIA | AGUARDANDO_COORDENACAO | Sistema | Existe decisão/exceção submetida à validação obrigatória. |
| EM_CONFERENCIA | PARCIALMENTE_DECIDIDO | Sistema | Há desfechos formalizados para parte dos objetos/itens e outros ainda em tratamento. |
| AGUARDANDO_REGULARIZACAO | EM_CONFERENCIA | Sistema/conferente | Pendência regularizada e reavaliada, ou outro encaminhamento formal válido registrado. |
| AGUARDANDO_COORDENACAO | EM_CONFERENCIA | Sistema | Coordenação aprovou, devolveu ou rejeitou; ação subsequente registrada. |
| PARCIALMENTE_DECIDIDO | CONCLUIDO | Sistema | Todos os itens apresentados possuem desfecho formal permitido; itens ausentes estão formalmente registrados; nenhuma pendência/validação obrigatória aberta; nenhum objeto sob custódia sem destino. |
| EM_CONFERENCIA | CONCLUIDO | Sistema | Mesmas condições de fechamento acima, inclusive quando houver itens NAO_APRESENTADO. |

Regras de fechamento (EST05):

1. A conclusão administrativa pode ocorrer com itens NAO_APRESENTADO, desde que a ausência tenha sido registrada na chegada com ator e data/hora reais e permaneça visível.
2. Item não apresentado não gera ObjetoCustodia, decisão técnica, AmostraOperacional ou aceite presumido.
3. Todos os itens apresentados devem ter desfecho formal compatível; nenhum objeto pode permanecer sem decisão quando a decisão for exigida.
4. Não pode haver pendência obrigatória aberta, validação de coordenação pendente ou objeto sob custódia sem destinação definida.
5. O estado CONCLUIDO é administrativo e não significa que todos os materiais foram aceitos.
6. Entrega posterior não altera retroativamente o recebimento original; exige nova solicitação ou exceção institucional formal, com data/hora efetiva.

Os estados agregados devem ser calculados de modo determinístico. A existência de objetos com decisões divergentes deve ser refletida como PARCIALMENTE_DECIDIDO no item/recebimento, sem perda da decisão individual.

### 4.3 Item de recebimento

| Origem | Destino | Responsável | Pré-condições e bloqueios |
|---|---|---|---|
| AGUARDANDO_CHEGADA | APRESENTADO | Recepção autorizada | Material fisicamente presente; quantidade, identificação, data/hora e recebedor efetivos registrados. |
| AGUARDANDO_CHEGADA | NAO_APRESENTADO | Recepção autorizada | Ausência confirmada e registrada no momento da chegada, com ator e data/hora reais. |
| APRESENTADO | conferência EM_ANDAMENTO | Conferente autorizado | ObjetoCustodia criado e sob guarda; checklist vigente carregado; permissão de conferência verificada. |
| EM_ANDAMENTO | conferência CONCLUIDA | Conferente autorizado | Critérios obrigatórios respondidos; justificativas/evidências exigidas presentes; versão do checklist preservada. |

O ItemRecebimento existe para cada ItemDeclarado, inclusive quando não apresentado. A apresentação não é decisão técnica. A custódia começa para o material apresentado e é representada por um ou mais ObjetosCustodia, conforme granularidade aprovada no M0.2.

Após NAO_APRESENTADO, não se permite alterar o estado como se o material tivesse chegado na data original. Erro comprovado exige retificação formal conforme EST08; entrega posterior exige nova solicitação ou exceção institucional formal, sem retroatividade.

### 4.4 Decisão e validação

A decisão deve ser registrada por ObjetoCustodia quando existir possibilidade de avaliação, resultado, aceite, recusa ou destino independente. A decisão diretamente no ItemRecebimento somente se aplica quando o desfecho for único e não houver objetos que precisem de desfechos separados.

| Ato/transição | Resultado | Condições |
|---|---|---|
| Formalizar aceite | ACEITA | Checklist concluído; nenhum critério E não conforme; pendências impeditivas regularizadas; validações obrigatórias concluídas; assinatura formal conforme EST07. |
| Registrar pendência | PENDENTE | Requisito saneável ou informação necessária impede decisão final; providência, responsável e prazo configurável registrados. |
| Formalizar recusa | RECUSADA | Fundamento e evidências registrados; validação prévia da coordenação obrigatória conforme EST03; assinatura formal conforme EST07. |
| Encaminhar à coordenação | AGUARDANDO | Exceção, recusa, retificação ou caso especial sujeito à revisão; decisão e pacote de evidências identificados. |
| Coordenador aprova | APROVADA | Validador competente e independente do autor/executor da decisão; fundamento e limites EST03 respeitados; assinatura formal. |
| Coordenador devolve | DEVOLVIDA | Complementação/correção requerida e justificativa registradas; decisão final permanece bloqueada. |
| Coordenador rejeita | REJEITADA | Justificativa formal; decisão retorna ao fluxo competente, sem conversão automática em recusa. |

A validação independente é um controle distinto da assinatura eletrônica. Assinatura formal comprova autoria e vinculação ao ato/conteúdo; não substitui a revisão independente quando esta for obrigatória. O mesmo usuário não pode validar a própria decisão quando EST03/EST10 exigirem independência. A indisponibilidade de validador não dispensa o controle.

A coordenação não pode dispensar critério impeditivo nem transformar resultado não conforme em conforme sem fundamento normativo/institucional válido e previamente formalizado. A validação deve referenciar o objeto/item e a decisão específica.

## 5. Matriz de permissões — consolidada conforme EST01 e EST10

Os perfis são funcionais e não equivalem automaticamente a cargos, unidades ou pessoas. As permissões são atribuídas explicitamente por usuário e verificadas no momento de cada operação. O perfil ADMINISTRADOR não concede autoridade técnica implícita.

| Ação | SOLICITANTE | RECEPÇÃO | CONFERENTE | COORDENAÇÃO | ADMINISTRADOR |
|---|---|---|---|---|---|
| Cadastrar/acompanhar solicitação própria | Sim, conforme canal/autorização | Não por padrão | Não por padrão | Conforme designação | Não por privilégio automático |
| Complementar informação de solicitação própria | Sim, quando solicitado | Não por padrão | Não por padrão | Conforme designação | Não por privilégio automático |
| Registrar chegada física | Não | Sim | Sim, se também autorizado (EST02) | Sim, se designado | Não por privilégio automático |
| Marcar item apresentado/não apresentado | Não | Sim | Sim, se também autorizado | Conforme designação formal | Não por privilégio automático |
| Criar/registrar ObjetoCustodia e início da guarda | Não | Sim, no ato de recebimento e conforme permissão | Sim, se designado | Conforme competência | Não por privilégio automático |
| Registrar movimentação/transferência de custódia | Não | Sim, se custodiante/designado | Sim, se custodiante/designado | Conforme competência | Não por privilégio automático |
| Conferir e preencher checklist | Não | Sim, se também autorizado | Sim | Somente se formalmente designado e competente | Não por privilégio automático |
| Registrar pendência/evidência | Complementar documento próprio, quando solicitado | Registro operacional se autorizado | Sim | Sim, na revisão e dentro da competência | Não por privilégio automático |
| Avaliar regularização | Não | Não por padrão | Sim, se competente e autorizado | Conforme competência; independente quando exigido | Não por privilégio automático |
| Propor decisão técnica | Não | Não por padrão | Sim, dentro da competência | Conforme competência formal | Não |
| Validar decisão/exceção/recusa | Não | Não | Não para decisão própria quando revisão independente exigida | Sim, se competente e independente | Não |
| Autorizar retificação excepcional | Não | Não | Pode solicitar/instruir, não autorizar a própria retificação | Sim, com independência e fundamento | Não |
| Assinar aceite final | Não | Não por padrão | Sim, se formalmente competente | Conforme competência formal | Não |
| Assinar encerramento de custódia | Não | Sim, se formalmente competente e após entrega efetiva | Sim, se formalmente competente e após entrega efetiva | Conforme competência formal | Não |
| Gerenciar usuários/perfis/permissões | Não | Não | Não | Conforme governança, sem autoelevação | Sim, dentro da autorização administrativa |
| Configurar parâmetros técnicos | Não | Não | Não | Aprova conteúdo/regras quando competente | Executa configuração autorizada; não aprova conteúdo técnico por privilégio |
| Alterar/apagar eventos de auditoria ou registros técnicos formalizados | Não | Não | Não | Não por rotina; retificação formal não apaga original | Não |

### 5.1 Regras de interpretação

1. A tabela define limites funcionais; a concessão efetiva depende da matriz institucional de competências e de permissões específicas.
2. A acumulação RECEPÇÃO + CONFERENTE é permitida conforme EST02, mas não concede autoaprovação em atos sujeitos à validação independente.
3. A COORDENAÇÃO não valida decisão de que seja autora/executora quando a independência for obrigatória.
4. A assinatura eletrônica formal da EST07 e a validação independente da EST10 são controles diferentes. Nem toda assinatura exige segundo signatário; toda validação independente exige validador distinto do autor/executor.
5. ADMINISTRADOR gerencia acessos e parâmetros técnicos autorizados, mas não pode conceder/elevar permissões para si próprio, aprovar conteúdo técnico por privilégio ou apagar trilha de auditoria.
6. SOLICITANTE identifica o papel de negócio. A forma de autenticação/acesso externo não é presumida nesta proposta; a primeira entrega pode manter cadastro por usuário interno em nome do solicitante, preservando o ator interno real.
7. A correspondência entre perfis, cargos, unidades, servidores e substitutos deve ser formalizada institucionalmente antes da operação.

## 6. Eventos mínimos de auditoria

Cada evento deve preservar, no mínimo:

- identificador do agregado e do item afetado;
- tipo do evento e dimensão de estado alterada;
- estado anterior e estado novo;
- ator, papel/permissão efetiva e origem da ação;
- data/hora com fuso e referência temporal inequívoca;
- justificativa, motivo e observações aplicáveis;
- versão do checklist/regra utilizada;
- referências e hashes de evidências quando houver;
- identificador de correlação da operação;
- referência ao evento anterior quando houver correção, devolução ou regularização.

Eventos sugeridos:

1. SOLICITACAO_CRIADA / SOLICITACAO_SUBMETIDA / SOLICITACAO_CANCELADA.
2. CHEGADA_FISICA_REGISTRADA / RECEBIMENTO_REGISTRADO.
3. ITEM_APRESENTADO / ITEM_NAO_APRESENTADO.
4. CUSTODIA_INICIADA / CUSTODIA_TRANSFERENCIA_SOLICITADA / CUSTODIA_TRANSFERIDA / CUSTODIA_ENCERRADA.
5. CHECKLIST_INICIADO / CRITERIO_AVALIADO / CHECKLIST_CONCLUIDO.
6. PENDENCIA_ABERTA / PENDENCIA_REGULARIZADA / PENDENCIA_NAO_REGULARIZAVEL.
7. DECISAO_ACEITE / DECISAO_PENDENCIA / DECISAO_RECUSA.
8. VALIDACAO_COORDENACAO_SOLICITADA / APROVADA / DEVOLVIDA / REJEITADA.
9. AMOSTRA_OPERACIONAL_CRIADA / IDENTIFICADOR_INSTITUCIONAL_ATRIBUIDO.
10. REGISTRO_CORRIGIDO / EXCECAO_AUTORIZADA.

## 7. Regras bloqueadoras

1. Não criar segundo recebimento principal para a mesma solicitação.
2. Não registrar chegada com data/hora retroativa para acomodar entrega posterior.
3. Não criar custódia de item não apresentado.
4. Não criar amostra operacional para item não apresentado, pendente ou recusado.
5. Não aceitar item com critério impeditivo não conforme.
6. Não concluir recebimento com item apresentado sem decisão formal.
7. Não encerrar custódia sem destino/transferência documentados.
8. Não permitir ao coordenador dispensar requisito impeditivo.
9. Não permitir que usuário sem permissão altere decisão formal.
10. Não sobrescrever decisão, checklist ou evento de custódia concluído.
11. Não criar amostra ou identificador duplicado em reenvio, concorrência ou repetição da operação.
12. Não associar registro legado por inferência sem evidência confiável.

## 8. Questões que exigem decisão antes da implementação

| ID | Questão | Prioridade |
|---|---|---|
| EST01 | Quais perfis institucionais podem cadastrar solicitação, receber material e conferir? | P0 — resolvida funcionalmente |
| EST02 | Conferente pode ser o mesmo usuário que registrou a chegada? | P0 |
| EST03 | Coordenação é obrigatória para quais tipos de exceção e decisões? | P0 — resolvida funcionalmente |
| EST04 | Qual destino e fluxo de custódia se aplicam a item recusado? | P0 — resolvida funcionalmente |
| EST05 | Quando um recebimento é considerado concluído se alguns itens não foram apresentados? | P0 — resolvida funcionalmente |
| EST06 | Quais critérios são impeditivos, saneáveis ou informativos por categoria? | P0 — resolvida funcionalmente |
| EST07 | Quais ações exigem assinatura eletrônica, além de autenticação e trilha de auditoria? | P1 — resolvida funcionalmente |
| EST08 | Como tratar correção excepcional de item marcado como não apresentado ou de decisão já formalizada? | P1 — resolvida funcionalmente |
| EST09 | Qual regra de prazo e encerramento de pendências? | P1 — resolvida funcionalmente |
| EST10 | Qual a política de segregação de funções e autoaprovação? | P0 — resolvida funcionalmente |

## 9. Critérios de aceite do desenho

O desenho de estados e transições estará pronto para detalhamento técnico quando:

- cada estado tiver significado, responsável e evento de entrada/saída;
- transições proibidas e pré-condições estiverem explicitadas;
- a matriz de permissões estiver aprovada pelo responsável institucional;
- as regras de coordenação, assinatura e segregação de funções estiverem definidas;
- a custódia de material recusado e o fechamento de itens não apresentados estiverem resolvidos;
- os critérios impeditivos/saneáveis estiverem vinculados a checklists versionados;
- os cenários forem validados com exemplos reais do SEFI;
- os eventos de auditoria e correção estiverem aprovados.

## 10. Próximo passo

A auditoria de consistência EST01–EST10 foi consolidada na versão 1.4 e seus achados estão rastreados em `docs/AUDITORIA_CONSISTENCIA_EST01_EST10.md`. A próxima atividade é detalhar a máquina de estados completa e os critérios de aceite verificáveis, mantendo pendentes a formalização institucional de cargos, responsáveis, substituições, checklists e parâmetros operacionais. A implementação permanece bloqueada até conclusão da Fase 0, aprovação do portão G0 e autorização específica.

## 12. Recomendações adicionais para custódia e granularidade

Esta seção complementa os estados sem alterar sua natureza de proposta.

### 12.1 Custódia antes da amostra

Recomenda-se que o estado de custódia seja aplicado a um **ObjetoCustodia** vinculado ao ItemRecebimento. O objeto pode representar unidade individual ou agrupamento homogêneo autorizado. A custódia começa no instante real da chegada física e não depende de aceite.

A criação posterior da AmostraOperacional não reinicia a custódia nem altera o timestamp original. Deve gerar vínculo auditável com o ObjetoCustodia e evento explícito de transferência/continuidade para a guarda laboratorial.

### 12.2 Material recusado

A decisão RECUSADA não equivale a custódia ENCERRADA. O material permanece SOB_GUARDA até que devolução ou outra destinação autorizada seja efetivamente concluída e registrada, com responsável, data/hora, destino e comprovante quando aplicável.

### 12.3 Material agrupado

Quando várias unidades forem recebidas e tratadas como conjunto homogêneo, a custódia poderá ser registrada em um ObjetoCustodia agrupado, desde que quantidade, lote, identificação e critério de agrupamento sejam explícitos. Se houver necessidade de decisão, resultado ou destino individual, as unidades devem ser discriminadas.

A regra não autoriza agrupar materiais apenas para reduzir cadastros. O responsável técnico deve confirmar que o agrupamento é compatível com o procedimento de amostragem e ensaio.

### 12.4 Encerramento agregado do recebimento

Recomenda-se permitir conclusão administrativa do recebimento quando todos os itens tiverem desfecho de apresentação e decisão compatível com a regra institucional, mesmo que um item esteja NAO_APRESENTADO, desde que:
- sua ausência esteja formalmente registrada;
- não exista material correspondente sob custódia;
- não haja pendência obrigatória aberta;
- a solicitação/recebimento preserve o registro do item ausente;
- o encerramento não seja interpretado como aceite técnico daquele item.

Esta regra precisa ser confirmada com a gestão funcional. A conclusão do recebimento não deve apagar a condição NAO_APRESENTADO nem permitir inclusão retroativa na chegada original.

## 13. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-09 | Primeira proposta de estados, transições, permissões e eventos de auditoria. |
| 0.2 | 2026-11-09 | Inclusão de recomendações para custódia pré-amostra, material recusado, agrupamento e encerramento com itens não apresentados. |


## 14. Alinhamento obrigatório ao modelo de domínio M0.2 aprovado

Em 2026-11-10, o modelo MOD-DOM-001 foi aprovado funcionalmente na versão 0.3. Esta revisão do documento de estados passa a adotar suas entidades e cardinalidades. A presente especificação continua **em proposta**, sem autorização para implementação.

### 14.1 Escopo de aplicação dos estados

| Dimensão | Agregado/entidade | Regra de aplicação |
|---|---|---|
| Solicitação | Solicitação | Estado global do ciclo administrativo da demanda. |
| Recebimento | Recebimento | Estado agregado, derivado dos itens e ações pendentes. |
| Apresentação | ItemRecebimento | Cada item declarado deve ser apresentado ou marcado como não apresentado no recebimento. |
| Conferência | ItemRecebimento | Acompanha o checklist do item, com critérios versionados. |
| Regularização | Pendência vinculada ao item ou objeto | Cada pendência possui ciclo próprio e histórico. |
| Decisão | ObjetoCustodia, quando houver objetos; ItemRecebimento quando não houver discriminação adicional | A decisão deve existir no menor nível em que aceite, recusa, rastreabilidade ou destino possam divergir. |
| Validação da coordenação | Decisão submetida à revisão | A validação referencia a decisão específica, não apenas o recebimento global. |
| Custódia | ObjetoCustodia | Custódia começa na chegada física e existe antes da AmostraOperacional. |
| Amostra | AmostraOperacional | Só é criada após aceite final e validações obrigatórias. |

### 14.2 Regras de consolidação quando houver vários objetos

1. Um ItemRecebimento pode originar zero, um ou vários ObjetosCustodia.
2. Cada ObjetoCustodia apresentado deve possuir estado de custódia e desfecho próprios.
3. Se todos os objetos tiverem a mesma decisão, o ItemRecebimento pode exibir essa decisão como situação consolidada.
4. Se houver decisões divergentes, o item deve exibir situação agregada **PARCIALMENTE_DECIDIDO** ou equivalente, sem ocultar as decisões por objeto.
5. O item só pode ser considerado integralmente aceito quando todos os objetos que compõem o material apresentado tiverem aceite final e validações concluídas.
6. A recusa de um objeto não implica automaticamente a recusa dos demais objetos do mesmo item declarado.
7. Não pode haver conclusão do recebimento enquanto existir objeto sob custódia sem destino definido, pendência obrigatória aberta ou objeto apresentado sem decisão.

### 14.3 Máquina de estados da custódia por ObjetoCustodia

| Estado | Evento de entrada | Próximo estado permitido | Condição |
|---|---|---|---|
| NAO_INICIADA | Chegada física confirmada | SOB_GUARDA | Identificação/descrição, quantidade, local e responsável inicial registrados. |
| SOB_GUARDA | Solicitação de transferência | TRANSFERENCIA_PENDENTE | Origem, destino e responsável destinatário identificados. |
| TRANSFERENCIA_PENDENTE | Recebedor de destino confirma recebimento | SOB_NOVA_RESPONSABILIDADE | Confirmação com ator e data/hora reais. |
| TRANSFERENCIA_PENDENTE | Transferência cancelada antes da entrega | SOB_GUARDA | Motivo e responsável que manteve a guarda registrados. |
| SOB_NOVA_RESPONSABILIDADE | Nova transferência | TRANSFERENCIA_PENDENTE | Nova origem/destino e responsáveis registrados. |
| SOB_GUARDA ou SOB_NOVA_RESPONSABILIDADE | Devolução/destinação efetivada | ENCERRADA | Destinatário, data/hora, responsável e comprovante quando aplicável. |

A decisão RECUSADA não é evento de encerramento da custódia. A custódia só termina quando a entrega externa ou destinação formal for efetivamente concluída.

### 14.4 Criação e vínculo da AmostraOperacional

1. A criação exige decisão ACEITA no objeto correspondente, checklist concluído, ausência de pendências impeditivas e validações obrigatórias concluídas.
2. A operação deve ser atômica e idempotente: repetição da requisição não pode criar outra amostra nem novo identificador.
3. A amostra deve manter referência ao ObjetoCustodia de origem e ao recebimento original.
4. A criação da amostra não altera a data/hora de chegada nem reinicia a custódia.
5. A passagem para guarda laboratorial deve ser registrada como transferência/evento de custódia, sem apagar os eventos anteriores.
6. Objeto recusado, pendente ou não apresentado não pode gerar AmostraOperacional.

### 14.5 Cenários de aceitação para validar as transições

| Cenário | Resultado obrigatório |
|---|---|
| Item declarado não chegou | ItemRecebimento = NAO_APRESENTADO; nenhum ObjetoCustodia ou amostra. |
| Item chegou e aguarda conferência | ObjetoCustodia = SOB_GUARDA; conferência ainda não concluída. |
| Item chegou, mas tem pendência saneável | Pendência aberta; decisão não final; custódia permanece ativa. |
| Um objeto é aceito e outro do mesmo item é recusado | Decisões independentes; apenas o objeto aceito pode gerar amostra; recusado permanece sob custódia até destinação. |
| Item recusado integralmente | Nenhuma amostra; custódia permanece até devolução/destinação efetiva. |
| Item aceito com coordenação obrigatória | Amostra bloqueada até validação aprovada. |
| Recebimento tem itens apresentados e não apresentados | Ausentes permanecem registrados; conclusão administrativa só após todos os desfechos e ausência de pendências/custódias sem destino. |
| Transferência de custódia não confirmada | Estado TRANSFERENCIA_PENDENTE; responsabilidade não é considerada transferida. |
| Reenvio concorrente da criação de amostra | Uma única amostra e um único identificador institucional. |

### 14.6 Pontos que permanecem para decisão funcional

A EST01 foi resolvida funcionalmente na seção 24, com definição dos perfis SOLICITANTE, RECEPÇÃO, CONFERENTE, COORDENAÇÃO e ADMINISTRADOR. A associação desses perfis aos cargos, unidades e servidores da instituição deverá ser formalizada na matriz institucional de competências;
- **EST03 — coordenação:** regra aprovada e registrada na seção 16; eventuais detalhamentos operacionais devem respeitar seus limites;
- **EST04 — recusados:** destinos e controles aprovados e registrados na seção 17; eventuais procedimentos operacionais devem respeitar essa regra;
- **EST05 — ausentes:** regra de conclusão administrativa aprovada e registrada na seção 18; itens não apresentados permanecem sem aceite técnico;
- **EST06 — critérios:** classificação e controle de versão aprovados e registrados na seção 19; a definição concreta dos critérios por categoria deverá ser formalizada nos checklists institucionais;
- **EST07 — assinatura:** regra aprovada e registrada na seção 20; assinatura formal restrita aos atos decisórios e de encerramento definidos;
- **EST08 — correções:** regra aprovada e registrada na seção 21; retificação excepcional sem sobrescrita, com validação da coordenação e avaliação de impacto quando houver amostra;
- **EST09 — prazos:** regra aprovada e registrada na seção 22; prazos configuráveis, alertas, escalonamento e encerramento formal sem recusa automática por vencimento.

### 14.7 Histórico

| Versão | Data | Descrição |
|---|---|---|
| 0.3 | 2026-11-10 | Alinhamento das regras de estados e transições ao modelo de domínio M0.2 aprovado; detalhamento da custódia por ObjetoCustodia, consolidação por item e vínculo com AmostraOperacional. |


## 15. Registro de decisão funcional — EST02

**Decisão:** APROVADA — permitir que o mesmo servidor registre a chegada física e realize a conferência técnica do material.  
**Data:** 2026-11-10  
**Escopo:** segregação entre as atividades de recebimento físico e conferência técnica.

### Regra aprovada

1. O mesmo servidor poderá executar o registro da chegada física e a conferência do mesmo material.
2. O sistema deverá registrar cada atividade como evento distinto, com ator, papel/permissão efetiva e data/hora próprios.
3. A permissão para receber não concede automaticamente permissão para conferir; o usuário deverá possuir as duas permissões funcionais.
4. A possibilidade de acumular as duas funções não elimina validações independentes da coordenação quando exigidas por regra institucional.
5. A autoaprovação de decisões sujeitas à validação independente é vedada, conforme detalhamento aprovado na EST10.
6. A regra deverá ser aplicada de forma uniforme aos objetos e itens abrangidos pelo recebimento, preservando o histórico individual.

### Efeito sobre EST02

EST02 fica **resolvida funcionalmente**. A matriz de permissões deverá permitir a acumulação dos papéis de recebedor e conferente, condicionada à atribuição explícita das permissões correspondentes. A definição dos perfis funcionais foi aprovada na EST01, registrada na seção 24. A associação dos perfis aos cargos e servidores institucionais deverá observar a matriz de competências. A segregação e a autoaprovação são tratadas na EST10.

### Histórico

| Versão | Data | Descrição |
|---|---|---|
| 0.4 | 2026-11-10 | Registro da decisão EST02: mesmo servidor pode registrar a chegada e realizar a conferência, com eventos e permissões distintos. |


## 16. Registro de decisão funcional — EST03

**Decisão:** APROVADA — validação obrigatória da coordenação para exceções e decisões institucionais específicas, sem poder de dispensar critérios impeditivos.  
**Data:** 2026-11-10  
**Escopo:** definição dos casos que exigem revisão da coordenação no fluxo de conferência e recebimento.

### Regra aprovada

A validação da coordenação será obrigatória nas seguintes situações:

1. **Exceções fora do checklist ou que exijam interpretação institucional:** qualquer situação não prevista expressamente no checklist ou cuja solução dependa de interpretação de regra institucional deverá ser encaminhada à coordenação antes da decisão final.
2. **Tentativa de regularização de critério impeditivo não conforme:** se houver tentativa de tratar como regularizável um critério classificado como impeditivo e registrado como não conforme, o caso deverá ser encaminhado à coordenação para revisão. Essa revisão não autoriza a dispensa do requisito nem a conversão do resultado não conforme em conforme.
3. **Decisões de recusa:** toda decisão de recusa deverá ser submetida à validação da coordenação antes de sua formalização final.
4. **Casos especiais previstos em regra institucional:** situações para as quais norma, procedimento ou regra institucional determine revisão da coordenação deverão seguir essa exigência.

### Limites da atuação da coordenação

1. A coordenação poderá aprovar, devolver para complementação ou rejeitar a proposta de encaminhamento, sempre com justificativa registrada.
2. A coordenação não poderá dispensar critérios impeditivos, afastar requisito obrigatório nem transformar resultado não conforme em conforme sem fundamento normativo/institucional válido e previamente formalizado.
3. A validação deverá referenciar o item ou ObjetoCustodia e a decisão específica submetida à revisão.
4. O encaminhamento, a manifestação e o resultado da coordenação deverão gerar eventos de auditoria próprios, com ator, papel/permissão, data/hora, justificativa e evidências aplicáveis.
5. Enquanto a validação obrigatória estiver pendente, a decisão final e a criação de AmostraOperacional permanecerão bloqueadas, quando aplicável.

### Efeito sobre EST03

EST03 fica **resolvida funcionalmente**. As transições e a matriz de permissões deverão exigir a validação da coordenação nos quatro casos acima. A classificação dos critérios como impeditivos, saneáveis ou informativos continua sujeita à decisão própria de EST06; esta decisão não define nem altera essa classificação.

### Histórico

| Versão | Data | Descrição |
|---|---|---|
| 0.5 | 2026-11-10 | Registro da decisão EST03: validação obrigatória para exceções fora do checklist, tentativa de regularização de impeditivo não conforme, recusas e casos especiais previstos institucionalmente. |


## 17. Registro de decisão funcional — EST04

**Decisão:** APROVADA — estabelecer destinos permitidos para materiais recusados e condicionar o encerramento da custódia à destinação efetiva e comprovada.  
**Data:** 2026-11-10  
**Escopo:** tratamento e destinação de materiais recusados após a decisão técnica.

### Destinos permitidos

Conforme o caso e as regras institucionais aplicáveis, o material recusado poderá ter um dos seguintes destinos:

1. **Devolução ao solicitante:** entrega ao próprio solicitante ou à pessoa formalmente indicada por ele, quando permitido.
2. **Retirada por representante autorizado:** entrega a representante cuja autorização e identidade tenham sido verificadas e registradas.
3. **Outra destinação institucional formalmente autorizada:** somente quando houver fundamento normativo ou procedimento institucional aplicável, com autorização e evidências correspondentes.

### Regras obrigatórias de custódia e encerramento

1. A decisão RECUSADA não encerra automaticamente a custódia. O material permanece SOB_GUARDA até a entrega ou destinação efetiva.
2. O encerramento exige registro do destino adotado, identificação do responsável pela entrega, identificação do destinatário ou responsável pela destinação, data/hora efetivas e comprovante quando aplicável.
3. Quando houver representante, devem ser registrados os dados necessários para demonstrar a autorização e a identificação da pessoa que recebeu o material.
4. A transferência de responsabilidade somente será considerada concluída após confirmação do recebimento pelo destinatário, conforme o fluxo de custódia.
5. Se a retirada ou destinação não ocorrer, o objeto permanece sob custódia institucional, com situação pendente e responsável atual identificados.
6. A opção por outra destinação institucional não pode ser usada como autorização genérica para descarte; deve haver fundamento e autorização específicos.
7. Cada objeto recusado deve ter destino e encerramento próprios, preservando a possibilidade de destinos diferentes para objetos originados do mesmo ItemRecebimento.

### Evidência e auditoria

O evento de encerramento da custódia deverá preservar, no mínimo:
- ObjetoCustodia e decisão de recusa relacionados;
- modalidade de destino escolhida;
- identificação do destinatário/representante ou unidade responsável;
- identificação do servidor que realizou a entrega ou destinação;
- data/hora efetivas;
- fundamento/autorização institucional, quando aplicável;
- comprovante ou referência da evidência, quando aplicável;
- ator, papel/permissão e evento de auditoria correspondente.

### Efeito sobre EST04

EST04 fica **resolvida funcionalmente**. O estado ENCERRADA somente poderá ser atribuído após a entrega ou destinação efetiva e o registro dos elementos obrigatórios. A decisão não define prazos de permanência, guarda ou descarte; esses aspectos deverão observar normas e procedimentos institucionais aplicáveis e não ficam autorizados por esta decisão.

### Histórico

| Versão | Data | Descrição |
|---|---|---|
| 0.6 | 2026-11-10 | Registro da decisão EST04: destinos permitidos para materiais recusados e encerramento da custódia somente após destinação efetiva e documentada. |


## 18. Registro de decisão funcional — EST05

**Decisão:** APROVADA — permitir a conclusão administrativa do recebimento mesmo quando houver itens não apresentados, desde que atendidas as condições de encerramento.  
**Data:** 2026-11-10  
**Escopo:** regra de fechamento do recebimento com preservação da situação dos itens ausentes.

### Condições obrigatórias para conclusão

O recebimento poderá ser concluído administrativamente com um ou mais itens em estado NAO_APRESENTADO, desde que todas as condições abaixo sejam atendidas:

1. A ausência de cada item esteja formalmente registrada no momento da chegada, com ator e data/hora reais.
2. Não exista ObjetoCustodia nem material correspondente sob guarda institucional para o item marcado como não apresentado.
3. Todos os itens apresentados tenham decisão formal compatível com as regras do processo.
4. Não existam pendências obrigatórias abertas nem validações de coordenação aguardando manifestação.
5. Não exista ObjetoCustodia sob custódia sem destino definido.
6. O histórico da solicitação e do recebimento preserve explicitamente quais itens não foram apresentados.

### Limites e efeitos da conclusão

1. A conclusão administrativa do recebimento não representa aceite técnico dos itens não apresentados.
2. Item NAO_APRESENTADO não gera ObjetoCustodia nem AmostraOperacional.
3. A conclusão não permite alterar retroativamente a apresentação para APRESENTADO na data original.
4. Uma entrega posterior deverá ser tratada por nova solicitação ou por exceção institucional formalmente autorizada, com registro da data/hora efetivas e sem apagar o histórico anterior.
5. O estado agregado do recebimento poderá ser CONCLUIDO mesmo com itens NAO_APRESENTADO, desde que todas as condições acima sejam satisfeitas.
6. A situação individual NAO_APRESENTADO deverá permanecer visível e consultável após o encerramento.

### Verificações de bloqueio

O sistema deverá impedir a conclusão quando:
- houver item apresentado sem decisão formal;
- existir pendência obrigatória aberta;
- houver validação obrigatória da coordenação pendente;
- existir material sob custódia sem destino definido;
- houver inconsistência entre a ausência registrada e a existência de material ou objeto de custódia vinculado ao item.

### Efeito sobre EST05

EST05 fica **resolvida funcionalmente**. A regra de conclusão administrativa com itens não apresentados passa a integrar os critérios de fechamento do recebimento, sem alterar o significado de aceite técnico e sem criar custódia ou amostra para material ausente.

### Histórico

| Versão | Data | Descrição |
|---|---|---|
| 0.7 | 2026-11-10 | Registro da decisão EST05: conclusão administrativa do recebimento permitida com itens não apresentados, sob condições explícitas e sem aceite técnico desses itens. |


## 19. Registro de decisão funcional — EST06

**Decisão:** APROVADA — adotar as classificações Impeditivo (E), Saneável (S) e Informativo (I), vinculadas a checklists versionados e aprovados pelo responsável técnico competente.  
**Data:** 2026-11-10  
**Escopo:** classificação dos critérios de conferência e seus efeitos sobre o fluxo de aceite e regularização.

### Classificações aprovadas

| Classificação | Significado | Efeito no fluxo |
|---|---|---|
| **Impeditivo (E)** | Requisito obrigatório cuja não conformidade impede o aceite do item ou objeto avaliado. | Não permite aceite enquanto não conforme. Não pode ser dispensado pela coordenação. |
| **Saneável (S)** | Requisito cuja não conformidade pode ser corrigida ou complementada, conforme procedimento aplicável. | Gera pendência; exige providência, evidência de regularização e nova avaliação antes da decisão final. |
| **Informativo (I)** | Informação relevante para registro e rastreabilidade, sem efeito impeditivo autônomo sobre o aceite. | Deve ser registrado quando aplicável, mas sua ausência ou resultado não conforme não bloqueia o aceite por si só, salvo se outra regra institucional estabelecer requisito obrigatório associado. |

### Governança e versionamento dos checklists

1. Cada critério deverá estar vinculado a um checklist identificado e versionado.
2. A classificação E, S ou I deverá ser definida antes do uso do checklist e aprovada pelo responsável técnico competente, conforme a governança institucional.
3. A versão efetivamente utilizada deverá ser preservada em cada conferência, permitindo reconstruir quais critérios e classificações estavam vigentes no momento da avaliação.
4. Alterações de descrição, aplicabilidade, classificação, método de verificação ou efeito no fluxo deverão gerar nova versão, justificativa, responsável pela aprovação e data de vigência.
5. A alteração de checklist não poderá modificar retroativamente conferências ou decisões já formalizadas.
6. Uma conferência iniciada deverá permanecer vinculada à versão de checklist com que foi iniciada. Eventual migração para nova versão exigirá procedimento formal, justificativa e registro de auditoria; não poderá ocorrer silenciosamente.
7. A coordenação não poderá reclassificar pontualmente um critério impeditivo para permitir aceite de um caso individual.
8. A classificação concreta dos critérios por tipo/categoria de dispositivo deverá ser definida nos respectivos checklists institucionais, com participação técnica competente. Esta decisão não presume nem cria classificações específicas para critérios ainda não avaliados.

### Regras de aplicação

- Critério E com resultado NAO_CONFORME bloqueia o aceite do objeto ou item a que se aplica.
- Critério S com resultado NAO_CONFORME exige pendência e regularização documentada; não autoriza aceite enquanto a condição impeditiva ao aceite permanecer aberta.
- Critério I deve ter sua avaliação ou justificativa registrada, mas não bloqueia o aceite isoladamente.
- A resposta NAO_APLICAVEL exige justificativa e deve respeitar as condições de aplicabilidade definidas no checklist.
- A classificação do critério e o resultado observado são informações distintas: a primeira pertence à versão do checklist; o segundo pertence à conferência realizada.

### Efeito sobre EST06

EST06 fica **resolvida funcionalmente** quanto às categorias de classificação e à governança de versionamento. Permanece necessária a elaboração e aprovação dos checklists concretos por categoria de dispositivo, antes de sua utilização operacional.

### Histórico

| Versão | Data | Descrição |
|---|---|---|
| 0.8 | 2026-11-10 | Registro da decisão EST06: classificações E/S/I, efeitos no fluxo e governança de checklists versionados. |


## 20. Registro de decisão funcional — EST07

**Decisão:** APROVADA — exigir assinatura eletrônica formal para atos decisórios e de encerramento com efeitos institucionais relevantes, mantendo autenticação individual e trilha de auditoria para operações rotineiras.  
**Data:** 2026-11-10  
**Escopo:** definição das ações que exigem assinatura eletrônica formal no fluxo de solicitação, recebimento, conferência, decisão e custódia.

### Ações que exigem assinatura eletrônica formal

A assinatura eletrônica formal será obrigatória para:

1. **Decisão final de aceite:** formalização da aprovação do item ou ObjetoCustodia para ingresso no fluxo laboratorial, observadas as condições e validações obrigatórias.
2. **Validação da coordenação:** manifestação formal da coordenação quando sua validação for exigida pelas regras EST03 ou por regra institucional aplicável.
3. **Encerramento da custódia:** confirmação formal da devolução, entrega a representante autorizado ou outra destinação institucional autorizada, após sua efetiva realização.
4. **Retificação excepcional:** correção de registro ou decisão já formalizada, quando autorizada pelo procedimento aplicável, com justificativa, referência ao registro original e preservação integral do histórico.

### Operações cobertas por autenticação e trilha de auditoria

Não será exigida assinatura eletrônica formal individual para cada operação rotineira, desde que executada por usuário autenticado e autorizado e registrada em trilha de auditoria íntegra. Incluem-se, entre outras:

- cadastro e edição de solicitação ainda não formalizada;
- registro da chegada física;
- identificação de itens apresentados ou não apresentados;
- preenchimento de checklist e registro de resultados;
- abertura, acompanhamento e atualização de pendências;
- inclusão de fotografias, documentos e outras evidências;
- registros operacionais de movimentação e acompanhamento da custódia que não representem seu encerramento formal.

A dispensa de assinatura formal nessas operações não dispensa autenticação individual, controle de permissões, registro de ator e data/hora, nem a preservação do histórico de alterações.

### Requisitos gerais da assinatura

1. A assinatura deverá estar vinculada de forma inequívoca ao usuário signatário, ao ato praticado e ao conteúdo/versão exata que foi formalizado.
2. O sistema deverá registrar identidade do signatário, data/hora, ação assinada, objeto/item relacionado e referência ao conteúdo formalizado.
3. Qualquer alteração posterior no conteúdo formalizado deverá invalidar a possibilidade de tratar a assinatura anterior como aprovação do novo conteúdo; deverá ser realizado novo ato formal, com preservação do anterior.
4. A assinatura não substitui as regras de autorização, competência, segregação de funções ou validação da coordenação.
5. O mecanismo tecnológico e o nível jurídico de assinatura aplicável deverão ser definidos na especificação técnica e validados conforme as políticas institucionais e os requisitos legais pertinentes. Esta decisão funcional não presume, por si só, exigência de certificado ICP-Brasil nem escolhe fornecedor ou tecnologia.
6. Os registros de assinatura deverão ser preservados e consultáveis para auditoria, com vínculo ao histórico do processo.

### Efeito sobre EST07

EST07 fica **resolvida funcionalmente** quanto à distinção entre atos que exigem assinatura eletrônica formal e operações rotineiras cobertas por autenticação e trilha de auditoria. A definição do mecanismo tecnológico, do nível jurídico de assinatura e de sua integração permanece para etapa própria de especificação, sem autorização de implementação.

### Histórico

| Versão | Data | Descrição |
|---|---|---|
| 0.9 | 2026-11-10 | Registro da decisão EST07: assinatura eletrônica formal para decisão final de aceite, validação obrigatória da coordenação, encerramento da custódia e retificações excepcionais; operações rotineiras com autenticação e trilha de auditoria. |


## 21. Registro de decisão funcional — EST08

**Decisão:** APROVADA — permitir retificações excepcionais de registros de apresentação e de decisões formalizadas, sem apagar ou sobrescrever o histórico original e mediante justificativa, evidência e validação da coordenação.  
**Data:** 2026-11-10  
**Escopo:** correção de item registrado como NAO_APRESENTADO e retificação de decisão formalizada no fluxo de recebimento.

### 21.1 Correção de item registrado como NAO_APRESENTADO

A correção será admitida somente quando houver evidência de que o material estava fisicamente presente na ocasião original e que o registro NAO_APRESENTADO decorreu de erro.

Condições obrigatórias:

1. Justificativa formal e específica para a retificação.
2. Evidência que sustente a presença física do material na ocasião original.
3. Validação prévia da coordenação, conforme sua competência e a regra EST03.
4. Preservação integral do registro original NAO_APRESENTADO.
5. Criação de evento de retificação vinculado ao registro original, com valor anterior, valor corrigido, ator, papel/permissão, data/hora reais e evidências.
6. Registro da chegada e início da custódia com base nos fatos comprovados, sem inventar, presumir ou retroagir timestamps não demonstráveis.
7. Aplicação dos controles de assinatura eletrônica formal definidos na EST07 para a retificação.

A retificação não poderá ser usada para registrar como presente, na data original, material que efetivamente chegou em momento posterior.

### 21.2 Material entregue posteriormente

Quando o material não estava presente na ocasião original e foi entregue depois, não haverá correção retroativa do estado NAO_APRESENTADO.

Deverá ser adotada nova solicitação ou exceção institucional formalmente autorizada, conforme a regra aprovada na EST05, com registro da chegada efetiva, data/hora reais e vínculo documental apropriado. O histórico anterior deverá permanecer preservado.

### 21.3 Retificação de decisão já formalizada

Decisões formalizadas — incluindo ACEITA, RECUSADA e PENDENTE — poderão ser retificadas excepcionalmente, desde que:

1. Exista justificativa formal, específica e fundamentada.
2. Haja evidência que sustente a necessidade e o conteúdo da correção.
3. A coordenação autorize a retificação antes de sua efetivação.
4. A decisão original permaneça íntegra e consultável.
5. Seja criado novo registro decisório, vinculado à decisão anterior, identificando claramente a retificação e seu motivo.
6. Sejam registrados o responsável, papel/permissão, data/hora reais, evidências e manifestação da coordenação.
7. A nova decisão seja formalizada com assinatura eletrônica, conforme EST07.

A retificação não poderá ser realizada por edição direta do registro original nem por alteração silenciosa de seu estado ou conteúdo. A nova decisão deverá constituir evento próprio no histórico.

### 21.4 Retificação quando já existe AmostraOperacional

Quando a decisão original já tiver resultado na criação de uma AmostraOperacional, a retificação exigirá avaliação de impacto antes da execução de qualquer alteração operacional decorrente.

A avaliação deverá considerar, no mínimo:

- situação atual da amostra e sua localização/responsabilidade;
- ensaios iniciados, em andamento ou concluídos;
- laudos emitidos ou ainda não emitidos;
- registros e evidências já vinculados;
- necessidade de bloqueio cautelar, revisão técnica ou outra providência institucional.

A retificação não excluirá automaticamente a AmostraOperacional, não apagará ensaios ou laudos e não desfará vínculos históricos. As providências sobre amostra, ensaios e laudos deverão seguir procedimento institucional aplicável, com registros e autorizações próprios.

### 21.5 Eventos e controles de auditoria

Toda retificação deverá gerar evento específico e preservar, no mínimo:

- identificador do registro e do item/ObjetoCustodia afetado;
- tipo e motivo da retificação;
- valor/conteúdo anterior e valor/conteúdo novo;
- referência ao evento ou decisão original;
- justificativa e evidências;
- solicitante da retificação e coordenador que a autorizou;
- atores, papéis/permissões e datas/horas reais;
- assinatura eletrônica exigida pela EST07;
- avaliação de impacto e providências subsequentes, quando houver AmostraOperacional.

O sistema deverá impedir a exclusão ou sobrescrita dos eventos originais e deverá manter a sequência cronológica e os vínculos entre registro original, solicitação de retificação, autorização e novo registro.

### Efeito sobre EST08

EST08 fica **resolvida funcionalmente**. Retificações excepcionais são permitidas sob controles formais, sem sobrescrita do histórico, com justificativa, evidência e validação da coordenação. A entrega posterior de material não caracteriza erro retroativo. Quando já houver AmostraOperacional, será obrigatória avaliação de impacto, sem exclusão automática de amostras, ensaios ou laudos.

A decisão não autoriza implementação nem define, por si só, todos os procedimentos técnicos de bloqueio, revisão ou retificação de ensaios e laudos; esses deverão ser detalhados na etapa própria e conforme a governança institucional.

### Histórico

| Versão | Data | Descrição |
|---|---|---|
| 1.0 | 2026-11-10 | Registro da decisão EST08: retificação excepcional de item NAO_APRESENTADO e de decisões formalizadas, com preservação do original, validação da coordenação, assinatura eletrônica e avaliação de impacto quando houver amostra. |


## 22. Registro de decisão funcional — EST09

**Decisão:** APROVADA — estabelecer prazos configuráveis para regularização de pendências, com comunicação formal, alertas, escalonamento, prorrogação autorizada e encerramento mediante regularização validada ou decisão formal fundamentada.  
**Data:** 2026-11-10  
**Escopo:** gestão de prazos, acompanhamento e encerramento das pendências identificadas durante a conferência e o recebimento.

### 22.1 Definição e início da contagem do prazo

1. Cada pendência deverá possuir prazo definido conforme seu tipo, criticidade e procedimento institucional aplicável.
2. Os prazos deverão ser configuráveis e aprovados pela autoridade institucional competente; esta decisão funcional não fixa uma quantidade universal de dias.
3. O registro da pendência deverá conter, no mínimo: descrição da irregularidade, providência requerida, responsável pela regularização, data/hora de abertura, prazo concedido, data/hora da comunicação formal e situação atual.
4. A contagem do prazo terá início a partir da comunicação formal da pendência ao responsável pela regularização, com registro da data/hora, destinatário e meio de comunicação.
5. Se a comunicação não puder ser comprovada, o sistema não deverá presumir que o prazo começou a correr.

### 22.2 Alertas e escalonamento

O sistema deverá permitir configurar alertas relacionados ao prazo da pendência, incluindo:

- comunicação inicial da pendência e do prazo;
- aviso de proximidade do vencimento;
- notificação de vencimento ao responsável e encaminhamento para avaliação da coordenação.

A antecedência e os canais de notificação deverão ser parametrizáveis conforme procedimento institucional. O sistema deverá registrar os avisos enviados, seus destinatários, datas/horas e resultados técnicos disponíveis, sem tratar a simples tentativa de envio como comprovação de ciência.

### 22.3 Tratamento do prazo vencido

1. O vencimento sem regularização deverá gerar situação ou indicador PRAZO_VENCIDO e evento de auditoria próprio.
2. O vencimento deverá notificar o responsável e encaminhar o caso à coordenação para avaliação.
3. O vencimento, por si só, não produzirá aceite, recusa, encerramento automático da pendência ou encerramento da custódia.
4. A coordenação deverá avaliar e registrar a providência adotada, que poderá incluir concessão de prorrogação, solicitação de complementação ou encaminhamento para decisão formal de não regularizável, conforme regra institucional.
5. Enquanto não houver decisão válida, a pendência permanecerá aberta e deverá continuar visível nos controles do recebimento.

### 22.4 Prorrogação

A prorrogação será permitida mediante justificativa e autorização da coordenação ou autoridade competente, conforme governança institucional. Cada prorrogação deverá registrar:

- justificativa;
- prazo original e novo prazo;
- solicitante, autorizador e respectivas permissões;
- data/hora da solicitação e da autorização;
- comunicação ao responsável pela regularização.

O prazo original e todas as prorrogações deverão permanecer preservados no histórico. Não será permitida alteração silenciosa ou retroativa do prazo originalmente concedido.

### 22.5 Estados e encerramento da pendência

A gestão deverá contemplar, no mínimo, os seguintes estados ou condições:

| Estado | Significado |
|---|---|
| PENDENTE | Providência requerida, aguardando início ou atendimento. |
| EM_REGULARIZACAO | Providência em andamento. |
| AGUARDANDO_REAVALIACAO | Evidência ou resposta recebida, aguardando avaliação técnica. |
| REGULARIZADA | Evidência avaliada e providência considerada satisfatória por responsável autorizado. |
| PRAZO_VENCIDO | Prazo expirado sem regularização validada; a pendência permanece aberta até decisão subsequente. |
| NAO_REGULARIZAVEL | Pendência encerrada por decisão formal, fundamentada e autorizada. |
| CANCELADA | Pendência cancelada por erro ou perda justificada de objeto, com motivo e histórico preservados. |

O recebimento de documentos ou evidências não encerra, por si só, a pendência. A transição para REGULARIZADA exige reavaliação favorável, com identificação do avaliador, data/hora, resultado e evidências relacionadas.

A transição para NAO_REGULARIZAVEL exige decisão formal fundamentada e autorização conforme a matriz de competências e as regras institucionais. Quando a decisão afetar o aceite, deverá respeitar os critérios E/S/I definidos na EST06 e a validação da coordenação prevista na EST03.

A situação PRAZO_VENCIDO é uma condição de controle e escalonamento, não um desfecho final. A pendência não deverá ser considerada encerrada enquanto não houver regularização validada, decisão formal de não regularizável ou cancelamento devidamente justificado e autorizado.

### 22.6 Relação com a custódia e o aceite

1. O vencimento ou encerramento de uma pendência não encerra automaticamente a custódia do material.
2. Material sob responsabilidade institucional permanecerá sob guarda até que sua devolução ou outra destinação autorizada seja efetivamente realizada e registrada, conforme EST04.
3. O encerramento administrativo da pendência não equivale a aceite técnico do item ou ObjetoCustodia.
4. A decisão de aceite ou recusa deverá observar os critérios de conferência, as validações obrigatórias e as assinaturas previstas nas EST03, EST06 e EST07.

### 22.7 Eventos e auditoria

O sistema deverá registrar eventos próprios para abertura, comunicação, início da contagem, alertas, vencimento, prorrogação, recebimento de evidência, reavaliação, regularização, decisão de não regularizável e cancelamento.

Cada evento deverá preservar, conforme aplicável: identificador da pendência e do item/ObjetoCustodia, estado anterior e novo, ator e permissões, data/hora, prazo vigente e histórico de prorrogações, destinatários e registros de comunicação, justificativas, evidências e referência à decisão autorizadora.

### Efeito sobre EST09

EST09 fica **resolvida funcionalmente** quanto à configuração de prazos, comunicação formal, alertas, escalonamento, prorrogação e encerramento controlado das pendências. Os valores concretos dos prazos, as antecedências dos alertas, os canais de comunicação e as autoridades institucionais responsáveis deverão ser definidos em procedimentos e configurações aprovados, antes da utilização operacional.

Esta decisão não autoriza implementação e não estabelece recusa automática pelo decurso do prazo.

### Histórico

| Versão | Data | Descrição |
|---|---|---|
| 1.1 | 2026-11-10 | Registro da decisão EST09: prazos configuráveis a partir da comunicação formal, alertas, escalonamento, prorrogação autorizada e encerramento controlado sem recusa automática por vencimento. |


## 23. Registro de decisão funcional — EST10

**Decisão:** APROVADA — permitir o acúmulo de atividades operacionais compatíveis, mas impedir a autoaprovação de decisões críticas sempre que houver exigência de validação independente. A indisponibilidade de outro servidor não constitui autorização automática para dispensar essa validação.  
**Data:** 2026-11-10  
**Escopo:** segregação de funções, prevenção de conflitos de interesse e controles de autorização nas atividades de solicitação, recebimento, conferência, aceite, validação, retificação e encerramento da custódia.

### 23.1 Acúmulo de funções operacionais

1. O sistema poderá permitir que um mesmo servidor acumule atividades operacionais, desde que possua as permissões correspondentes e que não exista regra institucional específica de segregação aplicável.
2. Poderão ser acumuladas, conforme atribuições e permissões, atividades como cadastro de solicitação, registro de chegada física, conferência técnica, registro de pendências e inclusão de evidências.
3. A permissão para executar uma atividade não concederá automaticamente permissão para executar outra. Cada permissão deverá ser atribuída explicitamente.
4. O acúmulo operacional não elimina validações independentes obrigatórias nem autoriza que o usuário aprove formalmente a própria decisão quando a independência for exigida.

### 23.2 Decisões sujeitas à validação independente

A validação independente deverá ser observada, no mínimo, nas situações em que as decisões funcionais anteriores exigem atuação da coordenação ou assinatura/autoridade distinta, incluindo:

- validação da coordenação sobre decisão submetida à sua apreciação, conforme EST03;
- decisões de recusa e exceções institucionais sujeitas à coordenação, conforme EST03;
- autorização de retificação excepcional, conforme EST08;
- decisões de aceite final e encerramento da custódia, respeitadas as competências, assinaturas e controles formais definidos na EST07 e nas demais regras aplicáveis.

O autor ou executor da decisão submetida à validação independente não poderá atuar como seu próprio validador. A matriz de competências deverá identificar claramente o responsável pela elaboração/execução e o responsável pela validação.

### 23.3 Indisponibilidade de validador independente

1. A ausência ou indisponibilidade de outro servidor não dispensará automaticamente a validação independente.
2. Enquanto a validação obrigatória não for realizada, a decisão permanecerá pendente e o sistema deverá impedir a conclusão da etapa que dela dependa.
3. O caso poderá ser encaminhado a outra autoridade institucional formalmente competente e independente, desde que essa substituição esteja prevista ou autorizada pelas regras institucionais.
4. Não será admitida exceção informal, autoaprovação ou alteração retroativa de autoria para contornar a exigência de independência.

### 23.4 Controles sistêmicos e auditoria

O sistema deverá:

1. Identificar o usuário, os papéis e as permissões associados a cada operação.
2. Verificar as permissões no momento da execução da operação, sem presumir autorização a partir de atividades anteriores.
3. Comparar a identidade do autor/executor com a do validador nas etapas que exigem independência e bloquear a autoaprovação.
4. Registrar tentativas de operações não autorizadas ou bloqueadas, quando tecnicamente disponíveis.
5. Preservar os atores, papéis, permissões, datas/horas, decisões, justificativas e referências aos eventos anteriores.
6. Permitir consulta e auditoria da sequência de elaboração, execução, validação e formalização de cada decisão.

### 23.5 Matriz funcional resumida

| Atividade | Acúmulo operacional | Regra de independência |
|---|---|---|
| Cadastro da solicitação | Permitido conforme permissões | Sem exigência geral de validação independente nesta decisão |
| Registro da chegada | Permitido conforme permissões | Não implica autorização para conferir ou aprovar |
| Conferência técnica | Permitido conforme permissões, inclusive pelo mesmo servidor que registrou a chegada, conforme EST02 | Validações obrigatórias continuam aplicáveis |
| Registro de pendência e inclusão de evidências | Permitido conforme permissões | A avaliação/validação segue as regras de competência aplicáveis |
| Avaliação de regularização | Permitido conforme atribuições | Reavaliação deverá ser feita por responsável autorizado; independência quando exigida pela regra aplicável |
| Validação da coordenação | Não pode ser acumulada com a autoria/executação da decisão submetida à validação | Obrigatoriamente independente |
| Autorização de retificação excepcional | Pode instruir/solicitar, mas não autorizar a própria retificação quando exigida autorização da coordenação | Autorização independente conforme EST08 |
| Aceite final | Conforme matriz de competências | Independência quando a validação for obrigatória; assinatura formal conforme EST07 |
| Encerramento da custódia | Conforme matriz de competências | Assinatura formal e controles de destinação conforme EST04 e EST07 |

### 23.6 Efeito da indisponibilidade operacional

A falta de validador independente deverá ser tratada como impedimento temporário à conclusão da decisão que exige validação. O sistema deverá manter o caso identificável e pendente, sem converter a indisponibilidade em aprovação tácita ou recusa automática. A gestão deverá encaminhar o caso à autoridade substituta competente, quando houver previsão institucional.

### Efeito sobre EST10

EST10 fica **resolvida funcionalmente** quanto ao acúmulo de atividades operacionais, à proibição de autoaprovação nas decisões sujeitas à validação independente e ao tratamento da indisponibilidade de validador. A associação dos perfis funcionais aos cargos, unidades, servidores e substituições autorizadas deverá ser formalizada na matriz institucional de competências antes da utilização operacional.

Esta decisão não autoriza implementação. A implementação permanece condicionada à conclusão da Fase 0, aprovação do portão G0 e autorização específica.

### Histórico

| Versão | Data | Descrição |
|---|---|---|
| 1.2 | 2026-11-10 | Registro da decisão EST10: acúmulo de atividades operacionais permitido conforme permissões; autoaprovação vedada quando houver validação independente; indisponibilidade não dispensa validação. |


## 24. Registro de decisão funcional — EST01

**Decisão:** APROVADA — adotar cinco perfis funcionais, com permissões específicas, atribuição explícita e possibilidade de acumulação autorizada, respeitadas as regras de segregação e prevenção de autoaprovação da EST10.  
**Data:** 2026-11-10  
**Escopo:** identificação dos perfis funcionais e governança das permissões de acesso às atividades de solicitação, recebimento, conferência, coordenação e administração do sistema.

### 24.1 Perfis funcionais

| Perfil | Responsabilidades | Permissões principais |
|---|---|---|
| SOLICITANTE | Registrar e acompanhar solicitações de ensaio. | Cadastrar solicitações próprias, consultar seu andamento e complementar informações quando solicitado; não altera decisões técnicas nem acessa solicitações de terceiros sem autorização. |
| RECEPÇÃO | Registrar a chegada física dos materiais. | Registrar chegada, data/hora, responsável e informações do recebimento físico; o registro de chegada não representa aceite técnico. |
| CONFERENTE | Realizar a conferência técnica. | Conferir itens, quantidades e documentos; registrar conformidades, não conformidades, pendências e evidências; propor decisões dentro de suas atribuições, sem dispensar critérios impeditivos. |
| COORDENAÇÃO | Supervisionar e validar decisões específicas. | Validar exceções, recusas, retificações e demais decisões previstas nas regras funcionais e na matriz institucional de competências. |
| ADMINISTRADOR | Administrar usuários, perfis, permissões e parâmetros técnicos do sistema. | Gerenciar acessos e configurações autorizadas; não recebe, por esse perfil isoladamente, autoridade técnica para aceitar materiais ou validar decisões da coordenação. |

Os nomes acima são perfis funcionais do sistema e não representam, por si só, cargos ou unidades administrativas da instituição.

### 24.2 Atribuição e acumulação de perfis

1. Um usuário poderá receber um ou mais perfis, desde que a acumulação seja compatível com suas atribuições institucionais e autorizada pela autoridade competente.
2. A atribuição de um perfil não concederá automaticamente permissões pertencentes a outro perfil. As permissões deverão ser explícitas e verificadas individualmente.
3. A acumulação RECEPÇÃO + CONFERENTE é permitida, em coerência com a EST02, desde que o usuário possua ambas as permissões.
4. A acumulação envolvendo COORDENAÇÃO deverá respeitar a independência exigida pela EST10: o usuário não poderá validar a própria decisão quando a validação independente for obrigatória.
5. O perfil ADMINISTRADOR não concede privilégios técnicos implícitos, nem permite alterar ou apagar registros técnicos formalizados ou eventos de auditoria fora de procedimento autorizado.
6. A acumulação de perfis não poderá ser utilizada para contornar restrições de segregação, competência, assinatura ou validação.

### 24.3 Regras de acesso por perfil

**SOLICITANTE**
- Consulta as solicitações às quais está vinculado.
- Pode complementar informações quando solicitado e conforme permissões.
- Não altera registros de conferência, decisões técnicas, validações ou registros de custódia.

**RECEPÇÃO**
- Registra a chegada física e os dados correspondentes.
- Não realiza aceite técnico apenas em razão do registro de chegada.
- Não altera decisões de conferência formalizadas.

**CONFERENTE**
- Registra a avaliação técnica, conformidades, não conformidades, pendências e evidências.
- Não dispensa critérios impeditivos.
- Não realiza validação independente de decisão própria quando essa validação for obrigatória.

**COORDENAÇÃO**
- Atua nos casos previstos nas decisões funcionais e na matriz institucional de competências.
- Não dispensa critérios impeditivos sem fundamento normativo ou institucional válido.
- Não valida decisão própria quando houver exigência de independência.

**ADMINISTRADOR**
- Gerencia usuários, perfis e permissões dentro de sua competência.
- Não altera silenciosamente registros técnicos formalizados.
- Não apaga eventos de auditoria.
- Não recebe autorização automática para aceite, recusa, retificação ou encerramento de custódia.

### 24.4 Governança das permissões

1. Cada usuário deverá possuir identificação individual e não compartilhada.
2. As permissões deverão ser concedidas por usuário autorizado, conforme matriz institucional de competências.
3. Nenhum usuário poderá conceder ou elevar permissões para si próprio.
4. Toda concessão, alteração, suspensão ou revogação de acesso deverá gerar evento de auditoria com ator, autorização, data/hora, usuário afetado e permissões envolvidas.
5. O sistema deverá verificar as permissões no momento de cada operação.
6. A instituição deverá estabelecer procedimento para revisão periódica dos acessos e para tratamento de afastamento, mudança de função ou desligamento de usuários.
7. O sistema deverá permitir consulta e auditoria do histórico de perfis e permissões.

### 24.5 Matriz funcional resumida

| Atividade | Perfil funcional principal | Observações |
|---|---|---|
| Cadastrar solicitação | SOLICITANTE | Acesso às próprias solicitações, conforme autorização. |
| Registrar chegada física | RECEPÇÃO | Não equivale a aceite técnico. |
| Realizar conferência | CONFERENTE | Pode acumular com RECEPÇÃO conforme EST02. |
| Registrar e avaliar pendências | CONFERENTE | Avaliação conforme competência e regras EST03/EST06/EST09. |
| Validar exceções e decisões críticas | COORDENAÇÃO | Independência obrigatória quando aplicável, conforme EST03 e EST10. |
| Autorizar retificação excepcional | COORDENAÇÃO | Autorização independente conforme EST08 e EST10. |
| Gerenciar usuários e permissões | ADMINISTRADOR | Sem autoridade técnica implícita. |
| Aceite final e encerramento de custódia | Responsável formalmente competente | Observa assinaturas, competências e validações das EST03, EST07 e EST10. |

### 24.6 Formalização institucional pendente

A aprovação desta decisão define os perfis funcionais do sistema, mas não nomeia servidores nem estabelece, por si só, a correspondência definitiva com cargos, setores ou unidades administrativas.

Antes da utilização operacional, a instituição deverá aprovar uma matriz de competências que identifique:
- cargos ou funções institucionais autorizados a exercer cada perfil;
- autoridade responsável por conceder, revisar e revogar permissões;
- substitutos formalmente autorizados para cada função;
- regras de acumulação compatíveis com a EST10;
- procedimento de revisão periódica dos acessos.

### Efeito sobre EST01

EST01 fica **resolvida funcionalmente** quanto aos cinco perfis, suas responsabilidades gerais, regras de acumulação e governança de permissões. A correspondência entre os perfis e os cargos, unidades e servidores da instituição permanece como formalização institucional necessária antes da operação.

Esta decisão não autoriza implementação. A implementação permanece condicionada à conclusão da Fase 0, aprovação do portão G0 e autorização específica.

### Histórico

| Versão | Data | Descrição |
|---|---|---|
| 1.3 | 2026-11-10 | Registro da decisão EST01: cinco perfis funcionais, permissões explícitas, acumulação autorizada e governança de acessos, com formalização institucional da matriz de competências. |


## 25. Consolidação normativa após auditoria de consistência EST01–EST10

**Data:** 2026-11-10  
**Versão:** 1.4  
**Escopo:** consolidação das regras já aprovadas; não cria nova decisão funcional e não autoriza implementação.

Esta seção consolida a interpretação normativa do documento. Em caso de divergência entre descrições preliminares das seções 1–14 e decisões funcionais posteriores das seções 15–24, prevalecem as decisões EST01–EST10 e as regras consolidadas nas seções 3–8 e nesta seção 25. O histórico de decisões anteriores é preservado.

### 25.1 Hierarquia de granularidade e decisão

1. Solicitação contém ItemDeclarado; cada ItemDeclarado possui um ItemRecebimento correspondente.
2. ItemRecebimento pode originar zero, um ou vários ObjetosCustodia, conforme o material apresentado e a granularidade tecnicamente justificada.
3. Item não apresentado não gera ObjetoCustodia, custódia, decisão técnica de aceite/recusa ou AmostraOperacional.
4. Quando houver ObjetosCustodia, a decisão será registrada no objeto sempre que aceite, recusa, resultado, rastreabilidade ou destinação puderem divergir.
5. Decisão diretamente no ItemRecebimento somente é admitida quando o desfecho for único para todo o material e não houver discriminação decisória necessária.
6. A situação agregada do ItemRecebimento não substitui nem oculta decisões por ObjetoCustodia. Decisões divergentes devem produzir situação agregada PARCIALMENTE_DECIDIDO ou equivalente.
7. Um objeto recusado não determina automaticamente a recusa dos demais objetos do item.
8. O item só é integralmente ACEITO quando todos os objetos apresentados tiverem aceite final e validações obrigatórias concluídas.

### 25.2 Matriz de independência, autorização e assinatura

| Controle | Finalidade | Regra |
|---|---|---|
| Autenticação individual | Identificar quem executa a operação | Obrigatória em todas as operações autenticadas; contas compartilhadas vedadas. |
| Permissão funcional | Autorizar uma operação específica | Verificada no momento da operação; um perfil não concede automaticamente permissões de outro. |
| Competência institucional | Demonstrar que a pessoa/cargo pode exercer a função | Deve ser formalizada na matriz institucional de competências. |
| Validação independente | Revisar ato/decisão de outro responsável | Obrigatória nos casos EST03/EST08 e demais casos formalmente previstos; autor/executor não pode validar a própria decisão. |
| Assinatura eletrônica formal | Vincular signatário, ato e conteúdo exato | Obrigatória para aceite final, validação da coordenação, encerramento da custódia e retificações excepcionais. |
| Trilha de auditoria | Reconstruir eventos e alterações | Deve preservar ator, papel/permissão, data/hora, conteúdo, justificativa e vínculo com eventos anteriores. |

Assinatura não substitui competência, permissão ou validação independente. Validação independente não é automaticamente exigida para toda operação assinada; aplica-se quando EST03, EST08, EST10 ou regra institucional assim determinar. O nível jurídico e a tecnologia da assinatura permanecem para especificação própria.

### 25.3 Consolidação de Pendências (EST09)

A máquina de estados da Pendência é independente dos estados do item, recebimento e custódia. PRAZO_VENCIDO é indicador de controle/escalonamento e mantém a pendência aberta. NAO_REGULARIZAVEL é desfecho formal da pendência, não recusa automática do material. A decisão de aceite/recusa permanece no nível decisório adequado e observa EST03, EST06 e EST10. A custódia permanece ativa até destinação efetiva.

### 25.4 Custódia: estado atual versus histórico

1. O estado atual de custódia é uma projeção do último evento válido/confirmado.
2. Cada evento de custódia preserva origem, destino, responsável anterior, responsável novo, localização anterior/nova, ator, data/hora real, justificativa e evidência aplicável.
3. Transferência solicitada sem confirmação mantém a responsabilidade com o custodiante de origem.
4. A confirmação pelo destinatário efetiva a transferência e atualiza a projeção do responsável/localização atuais.
5. ENCERRADA exige entrega/devolução ou destinação autorizada efetivamente realizada; não é consequência automática de recusa, pendência vencida ou conclusão administrativa do recebimento.

### 25.5 Criação e continuidade da AmostraOperacional

1. AmostraOperacional só pode ser criada para ObjetoCustodia com decisão ACEITA, checklist concluído e pendências/validações obrigatórias resolvidas.
2. A relação ObjetoCustodia → AmostraOperacional é 1:0..1, conforme M0.2.
3. A criação e atribuição do identificador institucional devem ser atômicas e idempotentes, com proteção contra reenvio e concorrência.
4. A amostra mantém vínculo inequívoco com ObjetoCustodia e recebimento de origem.
5. A criação da amostra não reinicia nem apaga a custódia. A passagem à guarda laboratorial é novo evento de transferência/continuidade.
6. A amostra não equivale a corpo de prova; um ensaio pode demandar corpos de prova/execuções conforme método, sem alterar a cardinalidade aprovada.

### 25.6 Retificação excepcional (EST08)

Retificação é novo ato vinculado ao registro original, nunca edição destrutiva. Deve preservar valor anterior e novo, justificativa, evidências, solicitante, autorizador independente, ator, permissões, data/hora reais e assinatura formal. Quando já existir AmostraOperacional, a avaliação de impacto antecede providências operacionais e considera amostra, localização, ensaios e laudos. Nenhum desses registros é excluído automaticamente.

### 25.7 Regras de conclusão administrativa do Recebimento (EST05)

O recebimento pode ser CONCLUIDO com itens NAO_APRESENTADO somente quando a ausência estiver registrada na chegada com data/hora reais, não houver objeto/material sob custódia relativo ao item ausente, todos os itens apresentados tiverem desfecho formal, não houver pendência obrigatória nem validação pendente e nenhum objeto permanecer sob custódia sem destino. CONCLUIDO não significa aceite universal.

### 25.8 Identificação dos achados da auditoria

Os achados AUD01–AUD12, suas ações corretivas e evidências de fechamento estão documentados em `docs/AUDITORIA_CONSISTENCIA_EST01_EST10.md`. A conclusão documental da auditoria não substitui aprovação institucional nem o Gate G0.

### 25.9 Histórico da consolidação

| Versão | Data | Descrição |
|---|---|---|
| 1.4 | 2026-11-10 | Consolidação documental após auditoria EST01–EST10: atualização da matriz de permissões, granularidade decisória, estados de pendência, regras de custódia, independência/assinatura, transições e critérios de bloqueio. |


## 26. Máquina de estados consolidada por entidade

**Escopo:** detalhamento funcional das transições, responsáveis, pré-condições e bloqueios. Os estados agregados são derivados; os eventos históricos são preservados. Esta seção não define estrutura física de banco nem autoriza implementação.

### 26.1 Solicitação

| Origem | Destino | Responsável | Pré-condições | Bloqueios/controles |
|---|---|---|---|---|
| inexistente | RASCUNHO | Usuário interno autorizado | Identificação do solicitante e dados iniciais disponíveis. | Identidade individual; identificador único. |
| RASCUNHO | SUBMETIDA | Usuário autorizado a submeter | Campos obrigatórios válidos e ao menos um ItemDeclarado. | Validar integridade dos itens; registrar ator/data-hora. |
| SUBMETIDA | RECEBIMENTO_REGISTRADO | Sistema, após criação do Recebimento | Chegada física efetivamente registrada; não existe recebimento principal. | Restrição de unicidade por Solicitação; operação transacional/idempotente. |
| RECEBIMENTO_REGISTRADO | EM_TRATAMENTO | Sistema | Conferência, pendência ou validação iniciada para algum item/objeto. | Não alterar timestamp real da chegada. |
| EM_TRATAMENTO | CONCLUIDA | Sistema | Recebimento CONCLUIDO e critérios EST05 atendidos; todos os itens têm desfecho administrativo válido. | Não concluir com pendência/validação obrigatória aberta ou objeto sob custódia sem destino. |
| RASCUNHO ou SUBMETIDA | CANCELADA | Usuário com permissão específica | Justificativa registrada e cancelamento permitido pelo procedimento. | Se houver chegada/custódia, não apagar recebimento nem encerrar custódia automaticamente. |

A conclusão da Solicitação é administrativa e decorre da conclusão do Recebimento; não significa aceite técnico universal dos itens.

### 26.2 Recebimento

| Origem | Destino | Responsável | Pré-condições | Bloqueios/controles |
|---|---|---|---|---|
| inexistente | REGISTRADO | RECEPÇÃO | Solicitação SUBMETIDA; chegada efetiva e recebedor identificados. | Um recebimento principal por solicitação. |
| REGISTRADO | EM_CONFERENCIA | CONFERENTE | Ao menos um ItemRecebimento APRESENTADO; checklist aplicável disponível. | Conferente deve ter permissão explícita; checklist versionado. |
| EM_CONFERENCIA | AGUARDANDO_REGULARIZACAO | Sistema | Pendência aberta que impede decisão final. | PRAZO_VENCIDO não encerra o recebimento nem a pendência. |
| EM_CONFERENCIA | AGUARDANDO_COORDENACAO | Sistema | Decisão/exceção sujeita a validação encaminhada. | Autor da decisão não pode validar a própria decisão. |
| EM_CONFERENCIA | PARCIALMENTE_DECIDIDO | Sistema | Pelo menos um item/objeto possui desfecho e outros permanecem em tratamento. | Preservar desfechos individuais. |
| AGUARDANDO_REGULARIZACAO | EM_CONFERENCIA | Sistema/conferente | Pendência regularizada e reavaliada ou novo encaminhamento formal registrado. | Evidência recebida sem reavaliação não libera a transição. |
| AGUARDANDO_COORDENACAO | EM_CONFERENCIA | Sistema | Validação aprovada, devolvida ou rejeitada e ação subsequente registrada. | Validação pendente mantém bloqueio. |
| PARCIALMENTE_DECIDIDO ou EM_CONFERENCIA | CONCLUIDO | Sistema | Todos os itens apresentados com desfecho formal; itens não apresentados registrados; sem pendências/validações obrigatórias abertas; sem ObjetoCustodia sem destino. | CONCLUIDO não implica aceite de itens ausentes ou de todos os objetos. |

### 26.3 ItemRecebimento e apresentação

| Origem | Destino | Responsável | Pré-condições | Bloqueios/controles |
|---|---|---|---|---|
| criação do recebimento | AGUARDANDO_CHEGADA | Sistema | Um ItemRecebimento por ItemDeclarado. | Não duplicar representação do item declarado. |
| AGUARDANDO_CHEGADA | APRESENTADO | RECEPÇÃO | Material fisicamente presente; quantidade/identificação observadas registradas. | Data/hora efetivas; não inferir quantidade apresentada. |
| AGUARDANDO_CHEGADA | NAO_APRESENTADO | RECEPÇÃO | Ausência constatada no ato da chegada. | Ator e data/hora reais; sem criação de objeto/amostra. |
| APRESENTADO | EM_CONFERENCIA | CONFERENTE | ObjetoCustodia criado e sob guarda; checklist vigente disponível. | Permissão explícita; custódia iniciada. |
| EM_CONFERENCIA | CONFERENCIA_CONCLUIDA | CONFERENTE | Critérios obrigatórios respondidos; justificativas e evidências presentes. | Preservar versão do checklist e respostas originais. |

NAO_APRESENTADO não é decisão RECUSADA. Correção de erro comprovado segue EST08; entrega posterior segue nova solicitação ou exceção institucional, sem retroatividade.

### 26.4 Conferência e respostas do checklist

| Origem | Destino | Responsável | Pré-condições | Bloqueios/controles |
|---|---|---|---|---|
| NAO_INICIADA | EM_ANDAMENTO | CONFERENTE | Item apresentado; ObjetoCustodia sob guarda; checklist aplicável e vigente. | Fixar versão do checklist no início. |
| EM_ANDAMENTO | CONCLUIDA | CONFERENTE | Todos os critérios obrigatórios respondidos; NAO_APLICAVEL justificado quando exigido. | Não concluir com critério obrigatório sem resposta ou evidência requerida ausente. |
| EM_ANDAMENTO | EM_ANDAMENTO | CONFERENTE | Resposta/avaliação adicional ou correção ainda não formalizada. | Preservar alterações e autoria; não apagar respostas formalizadas. |

Cada resposta registra critério, versão, resultado (CONFORME, NAO_CONFORME ou NAO_APLICAVEL), classificação E/S/I, avaliador, data/hora, justificativa e evidência aplicável. Alteração posterior de checklist não modifica a versão vinculada à conferência em curso.

### 26.5 Pendência

| Origem | Destino/condição | Responsável | Pré-condições | Bloqueios/controles |
|---|---|---|---|---|
| inexistente | PENDENTE | CONFERENTE autorizado | Não conformidade saneável ou informação necessária identificada. | Descrição, providência, responsável, prazo e comunicação formal. |
| PENDENTE | EM_REGULARIZACAO | Responsável pela regularização/sistema | Providência iniciada ou resposta formal recebida. | Preservar comunicação e início da contagem. |
| PENDENTE ou EM_REGULARIZACAO | PRAZO_VENCIDO | Sistema | Prazo expirado sem regularização validada. | Indicador/escalonamento; permanece aberta. |
| PRAZO_VENCIDO | EM_REGULARIZACAO | Responsável/sistema | Prorrogação autorizada ou providência retomada dentro da regra aplicável. | Preservar prazo original e histórico de prorrogação. |
| PENDENTE ou EM_REGULARIZACAO ou PRAZO_VENCIDO | AGUARDANDO_REAVALIACAO | Sistema/conferente | Evidência/resposta recebida e encaminhada à avaliação. | Recebimento da evidência não encerra a pendência. |
| AGUARDANDO_REAVALIACAO | REGULARIZADA | CONFERENTE competente | Reavaliação favorável documentada. | Registrar avaliador, resultado, data/hora e evidência. |
| PENDENTE ou EM_REGULARIZACAO ou PRAZO_VENCIDO ou AGUARDANDO_REAVALIACAO | NAO_REGULARIZAVEL | Autoridade competente | Decisão formal fundamentada e autorizada. | Não gera recusa automática; decisão de material permanece separada. |
| qualquer estado aberto | CANCELADA | Autoridade competente | Erro ou perda justificada do objeto, com autorização. | Motivo, ator, data/hora e histórico preservados. |

PRAZO_VENCIDO é uma condição de controle que pode coexistir com a pendência aberta. Não se deve perder o estado operacional subjacente (por exemplo, EM_REGULARIZACAO) ao registrar o vencimento. A modelagem técnica deverá preservar ambos, seja por estado combinado, indicador ou evento, sem alterar o significado aprovado na EST09.

### 26.6 Decisão de aceite, pendência ou recusa

| Origem | Destino | Responsável | Pré-condições | Bloqueios/controles |
|---|---|---|---|---|
| NAO_DECIDIDA | PENDENTE | CONFERENTE | Há requisito saneável ou revisão necessária. | Criar Pendência quando houver providência; não tratar como desfecho final. |
| NAO_DECIDIDA ou PENDENTE | ACEITA | Responsável tecnicamente competente | Checklist concluído; critérios E conformes; pendências impeditivas regularizadas; validações obrigatórias concluídas. | Assinatura formal EST07; independência quando exigida EST03/EST10. |
| NAO_DECIDIDA ou PENDENTE | RECUSADA | Responsável competente | Fundamento e evidências; validação prévia da coordenação conforme EST03. | Assinatura formal; custódia continua até destinação efetiva. |
| ACEITA, PENDENTE ou RECUSADA | novo ato retificador | Autoridade competente | Procedimento excepcional EST08, justificativa, evidência e validação prévia da coordenação quando aplicável. | Nunca sobrescrever; preservar decisão original e avaliar impacto se houver amostra. |

A decisão é persistida no ObjetoCustodia quando houver desfecho independente. A situação do ItemRecebimento é consolidada e não substitui o histórico decisório dos objetos.

### 26.7 Validação da coordenação

| Origem | Destino | Responsável | Pré-condições | Bloqueios/controles |
|---|---|---|---|---|
| NAO_EXIGIDA | AGUARDANDO | Sistema/conferente | Exceção, recusa, tentativa de regularização de impeditivo ou caso especial exige validação. | Referenciar decisão, objeto/item e evidências. |
| AGUARDANDO | APROVADA | COORDENAÇÃO independente | Competência e revisão concluídas. | Validador diferente do autor/executor; assinatura formal EST07. |
| AGUARDANDO | DEVOLVIDA | COORDENAÇÃO independente | Complementação/correção necessária. | Motivo e ação requerida; decisão final bloqueada. |
| AGUARDANDO | REJEITADA | COORDENAÇÃO independente | Proposta não validada. | Motivo formal; não converter automaticamente em recusa. |
| DEVOLVIDA | AGUARDANDO | CONFERENTE/sistema | Complementação concluída e novo encaminhamento registrado. | Nova manifestação vinculada ao ciclo anterior. |

A coordenação não pode dispensar critério impeditivo nem validar decisão própria quando a independência for obrigatória.

### 26.8 ObjetoCustodia e transferência

| Origem | Destino | Responsável | Pré-condições | Bloqueios/controles |
|---|---|---|---|---|
| inexistente | SOB_GUARDA | RECEPÇÃO/designado | Material apresentado; identificação/descrição, quantidade, local e responsável inicial registrados. | Não criar para item não apresentado. |
| SOB_GUARDA | TRANSFERENCIA_PENDENTE | Custodiante atual | Origem, destino e recebedor pretendido identificados. | Responsabilidade permanece na origem. |
| TRANSFERENCIA_PENDENTE | SOB_NOVA_RESPONSABILIDADE | Recebedor de destino | Recebimento físico confirmado. | Registrar atores, data/hora reais e localização nova. |
| TRANSFERENCIA_PENDENTE | SOB_GUARDA | Custodiante de origem/sistema | Transferência cancelada antes da entrega. | Justificativa e permanência da guarda confirmadas. |
| SOB_NOVA_RESPONSABILIDADE | TRANSFERENCIA_PENDENTE | Custodiante atual | Nova transferência formal solicitada. | Repetir controles de origem/destino. |
| SOB_GUARDA ou SOB_NOVA_RESPONSABILIDADE | ENCERRADA | Responsável autorizado pela entrega/destinação | Devolução/entrega/destinação efetiva e documentada. | Assinatura formal EST07; destinatário, responsável, data/hora e comprovante quando aplicável. |

O estado atual é derivado do último evento confirmado. Evento de solicitação de transferência não altera o custodiante vigente. Não há transição automática de RECUSADA para ENCERRADA.

### 26.9 AmostraOperacional — somente criação no escopo desta fase

| Situação | Resultado | Condições |
|---|---|---|
| NÃO_CRIADA | Estado inicial | Objeto ainda não aceito ou ainda não apto. |
| APTA_PARA_CRIACAO | Condição calculada, não necessariamente persistida | Decisão ACEITA; checklist concluído; pendências impeditivas resolvidas; validações obrigatórias concluídas. |
| CRIADA | Amostra persistida | Criação atômica/idempotente; identificador único; vínculo ao ObjetoCustodia e recebimento de origem. |
| BLOQUEADA | Condição calculada | Qualquer pré-condição ausente, decisão não final, recusa ou validação pendente. |

A cardinalidade ObjetoCustodia → AmostraOperacional é 1:0..1. Reenvio concorrente não pode criar amostra/identificador duplicado. A criação não reinicia custódia; transferência para guarda laboratorial gera evento próprio. O ciclo posterior de ensaios e laudos permanece fora do escopo desta máquina de estados de recebimento.

### 26.10 Regras transversais de auditoria e concorrência

Toda transição formal deve registrar, conforme aplicável: identificador do agregado e da entidade afetada; evento; estado anterior e novo; ator; perfil/permissão efetiva; data/hora com fuso; justificativa; versão do checklist/regra; evidências e seus hashes/referências; correlação da operação; evento anterior relacionado.

Operações críticas devem ser atômicas e idempotentes. Tentativas bloqueadas por permissão, autoaprovação, duplicidade, critério impeditivo ou pré-condição ausente devem ser registradas quando tecnicamente disponíveis. Nenhum estado atual deve substituir o histórico de eventos.

## 27. Critérios funcionais de aceitação derivados da máquina de estados

Os cenários abaixo deverão ser convertidos em testes automatizados e testes de aceitação durante a etapa técnica. Nesta fase são critérios funcionais normativos, não evidência de que o software já os implementa.

| ID | Cenário | Resultado esperado |
|---|---|---|
| CA01 | Usuário sem permissão tenta registrar chegada. | Operação bloqueada; tentativa registrada quando tecnicamente disponível. |
| CA02 | Usuário RECEPÇÃO + CONFERENTE registra chegada e realiza conferência. | Permitido se ambas as permissões estiverem atribuídas; eventos distintos com ator e data/hora. |
| CA03 | Conferente tenta validar a própria decisão sujeita à coordenação. | Bloqueio por independência; decisão permanece pendente. |
| CA04 | Critério E marcado NAO_CONFORME. | Aceite bloqueado; coordenação não pode dispensar o critério. |
| CA05 | Critério S marcado NAO_CONFORME. | Pendência criada; aceite bloqueado até regularização e reavaliação favorável. |
| CA06 | Critério I sem informação. | Não bloqueia isoladamente, salvo regra obrigatória associada formalizada. |
| CA07 | Item declarado não foi apresentado. | ItemRecebimento NAO_APRESENTADO; sem ObjetoCustodia, custódia ou amostra. |
| CA08 | Recebimento contém item apresentado e item não apresentado, todos os desfechos válidos. | Pode ser CONCLUIDO administrativamente; ausência permanece visível e não representa aceite. |
| CA09 | Material recusado ainda não foi retirado. | ObjetoCustodia permanece SOB_GUARDA; não ENCERRADA. |
| CA10 | Transferência solicitada sem confirmação do destinatário. | TRANSFERENCIA_PENDENTE; responsabilidade permanece com origem. |
| CA11 | Destinatário confirma transferência. | Novo responsável/localização passam a vigorar; evento anterior permanece. |
| CA12 | Pendência vence sem regularização. | PRAZO_VENCIDO e escalonamento; pendência continua aberta, sem recusa automática. |
| CA13 | Evidência de regularização é recebida, mas não reavaliada. | Pendência permanece AGUARDANDO_REAVALIACAO; não REGULARIZADA. |
| CA14 | Coordenação aprova recusa proposta por conferente. | Validação independente e assinatura formal registradas; decisão final pode ser formalizada. |
| CA15 | Coordenação tenta dispensar critério E não conforme. | Operação bloqueada, salvo fundamento normativo/institucional válido e previamente formalizado aplicável. |
| CA16 | Reenvio concorrente da criação de amostra para o mesmo ObjetoCustodia. | Uma única AmostraOperacional e um único identificador institucional. |
| CA17 | Objeto é aceito, mas validação obrigatória está pendente. | Criação da amostra bloqueada. |
| CA18 | Item possui dois ObjetosCustodia, um aceito e outro recusado. | Decisões independentes; item não aparece como integralmente aceito; recusado permanece sob custódia. |
| CA19 | Retificação de decisão formalizada sem justificativa/evidência/autorização. | Bloqueada; registro original permanece íntegro. |
| CA20 | Retificação após criação de amostra e início de ensaios. | Avaliação de impacto obrigatória; nenhuma amostra, ensaio ou laudo excluído automaticamente. |
| CA21 | Administrador tenta elevar a própria permissão. | Bloqueado; evento de tentativa registrado quando tecnicamente disponível. |
| CA22 | Usuário tenta alterar/excluir evento de auditoria formalizado. | Bloqueado; original preservado. |
| CA23 | Material chega após o recebimento ter sido concluído como NAO_APRESENTADO. | Não há retroação; nova solicitação ou exceção formal com data/hora efetiva. |
| CA24 | Checklist muda após início de uma conferência. | Conferência permanece vinculada à versão original; migração somente por procedimento formal auditável. |

### 27.1 Condição de encerramento desta especificação funcional

A máquina de estados e os critérios acima estão consolidados funcionalmente para revisão. Antes do Gate G0, ainda será necessário:
- validar os cenários com casos reais anonimizados do SEFI;
- aprovar institucionalmente a matriz de competências e substituições;
- aprovar checklists concretos por categoria;
- definir parâmetros de prazo e comunicação;
- definir nível jurídico e tecnologia da assinatura;
- revisar arquitetura, segurança, auditoria, backup e recuperação;
- converter os critérios CA01–CA24 em testes rastreáveis.

A conclusão desta especificação não autoriza implementação.


## 28. Complementos da revisão multidisciplinar — identidade, quantidades e tempo dos eventos

**Data:** 2026-11-10  
**Situação:** requisitos funcionais complementares identificados em revisão multidisciplinar; sujeitos à validação institucional e técnica. Não alteram cardinalidades M0.2 nem autorizam implementação.

### 28.1 Quantidades declaradas, apresentadas e representadas

O fluxo deverá distinguir, sem sobrescrita ou inferência:

- **Quantidade declarada:** quantidade informada na solicitação.
- **Quantidade apresentada:** quantidade efetivamente observada na chegada física.
- **Quantidade representada por ObjetoCustodia:** quantidade/unidade que aquele objeto ou agrupamento representa para fins de guarda, rastreabilidade e decisão.

As unidades de medida e a forma de apresentação deverão ser registradas de modo explícito. A quantidade representada por um ObjetoCustodia não implica, por si só, que ele corresponda a uma única unidade física. Divergências entre declarado e apresentado deverão ser registradas como fato observado e encaminhadas conforme checklist/regra aplicável; não se deve corrigir silenciosamente a declaração original. Fracionamento, agrupamento e individualização dependerão de justificativa de rastreabilidade, risco e independência de decisão/ensaio.

### 28.2 Tempo do fato versus tempo do registro

Todo evento relevante deverá distinguir conceitualmente:

- `occurred_at`: quando o fato ocorreu, conforme observado ou comprovado;
- `recorded_at`: quando o evento foi registrado no sistema;
- `recorded_by`: identidade de quem registrou.

Os campos não são intercambiáveis. O horário efetivo da chegada física deverá ser capturado no evento de recebimento; o horário de gravação deverá ser gerado pelo sistema. Registro tardio exige justificativa e preserva ambos os tempos. Não se admite retroagir `recorded_at` nem inventar `occurred_at`. Datas/horas devem possuir fuso/offset inequívoco e fonte temporal controlada. Correções são novos eventos CORRECTION vinculados ao evento original.

### 28.3 Taxonomia mínima dos eventos de custódia

A trilha de custódia deverá distinguir, no mínimo, os seguintes fatos:

| Tipo | Significado |
|---|---|
| RECEIPT | Entrada física inicial do material sob responsabilidade institucional. |
| TRANSFER | Mudança confirmada de responsável/custodiante. |
| LOCATION_CHANGE | Mudança de localização sem necessariamente mudar o custodiante. |
| RETURN | Devolução física ao solicitante ou representante autorizado. |
| DISPOSITION | Outra destinação institucional formalmente autorizada e efetivamente executada. |
| CLOSURE | Encerramento formal da custódia após comprovação da entrega/devolução/destinação. |
| CORRECTION | Retificação de evento anterior, sem apagar ou substituir o original. |

Solicitação de transferência não é TRANSFER confirmado. RETURN/DISPOSITION descrevem o fato de destinação; CLOSURE registra o encerramento formal após verificação das condições. A taxonomia deverá permitir reconstruir custodiante e localização em qualquer instante relevante.

### 28.4 Protocolo institucional, accession e QR

O sistema deverá separar os conceitos:

1. **Protocolo SEFI:** identificador institucional do processo/solicitação ou recebimento, conforme regra de numeração a aprovar.
2. **Accession:** identificador laboratorial atribuído à amostra operacional após o aceite e criação da amostra, conforme regra laboratorial a aprovar.
3. **QR Code:** representação legível por máquina de um identificador ou endereço/URI controlado; não é, por si só, a identidade primária nem substitui os identificadores persistidos.

Cada identificador deverá possuir escopo, entidade referenciada, regra de unicidade, momento de atribuição, origem e histórico. Não atribuir accession a item não apresentado, objeto recusado ou objeto ainda não aceito. A regra definitiva de numeração, conteúdo do QR e interoperabilidade permanece decisão institucional/técnica pendente.

## 29. Complementos da revisão multidisciplinar — acesso, integridade e concorrência

### 29.1 Isolamento do solicitante

O perfil SOLICITANTE deverá ter escopo de dados restrito às solicitações às quais esteja legitimamente vinculado. A autorização deverá ser verificada no servidor em todas as operações de leitura, listagem, consulta de detalhe, download de evidência e alteração; ocultar registros apenas na interface não é controle suficiente. Tentativas de acesso a identificadores de terceiros deverão ser negadas sem revelar existência ou conteúdo não autorizado. A eventual habilitação de contas externas e sua governança permanecem decisão de escopo e segurança; o requisito de isolamento deve ser preservado independentemente do canal de acesso.

### 29.2 Concorrência otimista e versão esperada

Operações de alteração sobre agregados sujeitos a concorrência deverão admitir controle de versão, conceitualmente por `expected_version`. Se a versão apresentada pelo cliente não corresponder à versão vigente, a operação deverá ser rejeitada como conflito, sem sobrescrever a alteração concorrente; contrato proposto: HTTP 409 com código estável `VERSION_CONFLICT`. A interface deverá atualizar os dados e solicitar nova decisão explícita, sem repetir automaticamente uma decisão de negócio.

### 29.3 Idempotência e reenvio

Operações críticas sujeitas a repetição de rede ou concorrência deverão usar chave de idempotência persistida e associada ao escopo da operação, identidade/autorização, hash do conteúdo relevante e resultado. Regras mínimas:

1. Mesma chave e mesmo conteúdo após conclusão: devolver resultado previamente registrado, sem repetir efeitos.
2. Mesma chave com conteúdo diferente: rejeitar como conflito de chave/conteúdo.
3. Mesma chave enquanto a primeira execução estiver em andamento: responder conflito transitório estável (proposta: HTTP 409, `IDEMPOTENCY_REQUEST_IN_PROGRESS`).
4. Falha antes do commit: não deixar efeito parcial nem marcar falsamente como concluída.
5. Política de retenção/expiração deve cobrir a janela real de reenvio e auditoria; a expiração não pode permitir duplicação de identificadores de negócio.

A política de persistência, expiração, escopo e recuperação de chaves deverá ser especificada antes da implementação.

### 29.4 Histórico, consulta e paginação

Listagens de eventos, auditoria, recebimentos e custódia deverão ter ordenação determinística, paginação estável e filtros por entidade/período/tipo, preservando a sequência cronológica e evitando omissões ou duplicações entre páginas. A consulta paginada não poderá alterar a trilha nem expor dados fora do escopo de autorização. Exportações deverão preservar identificadores, tempos do fato/registro e vínculos entre eventos.

### 29.5 Evidências binárias

Fotos, PDFs, termos e outros anexos deverão possuir metadados de autoria, vínculo ao processo/item/objeto, data/hora, tipo, tamanho, hash de integridade, classificação de acesso e política de retenção. O armazenamento binário deverá ser separado do banco relacional por serviço/objeto de armazenamento apropriado, com controle de acesso, versionamento ou imutabilidade conforme risco e cópias de segurança. A tecnologia (por exemplo, MinIO ou serviço S3 compatível) não está escolhida nesta especificação.

### 29.6 Dados legados

A transição do modelo existente para Solicitação, Recebimento, ItemRecebimento e ObjetoCustodia deverá ser aditiva e retrocompatível. Não criar vínculos presumidos quando os dados legados não demonstrarem origem, quantidade, identidade ou custódia. Cada associação migrada deverá ter regra, evidência, origem e possibilidade de auditoria; registros não associáveis permanecem legados sem vínculo forçado. Plano de migração, reconciliação, reversão e validação será requisito de arquitetura/Gate G0.

## 30. Critérios funcionais complementares da revisão

Além de CA01–CA24, ficam propostos os seguintes critérios para fechar lacunas identificadas. Devem ser incorporados à suíte de aceitação após revisão técnica:

| ID | Cenário | Resultado esperado |
|---|---|---|
| CA25 | SOLICITANTE consulta, lista ou baixa evidência de solicitação de terceiro sem vínculo autorizado. | Acesso negado no servidor, sem revelar conteúdo ou existência indevida; evento de segurança registrado conforme política. |
| CA26 | Quantidade declarada difere da quantidade apresentada. | Ambas permanecem preservadas; divergência é registrada e encaminhada ao critério/checklist aplicável. |
| CA27 | Um ObjetoCustodia representa agrupamento de unidades. | Quantidade/unidade representada e justificativa de agrupamento ficam explícitas; não se presume equivalência objeto-unidade física. |
| CA28 | Evento de chegada é registrado depois do fato. | occurred_at e recorded_at permanecem distintos; registro tardio exige justificativa e não altera o tempo de gravação. |
| CA29 | Há mudança de localização sem mudança de custodiante. | LOCATION_CHANGE atualiza localização projetada sem simular TRANSFER nem trocar responsável. |
| CA30 | Solicitação de transferência não é confirmada pelo destinatário. | Custodiante e localização vigentes permanecem conforme último evento confirmado. |
| CA31 | Mesmo pedido crítico é reenviado com a mesma chave e conteúdo após sucesso. | Resultado original é devolvido sem duplicar recebimento, evento ou amostra. |
| CA32 | Chave de idempotência é reutilizada com conteúdo diferente. | Requisição é rejeitada como conflito; nenhum efeito adicional ocorre. |
| CA33 | Duas alterações concorrentes usam a mesma versão esperada. | Apenas uma é efetivada; a outra recebe VERSION_CONFLICT e não sobrescreve dados. |
| CA34 | Eventos são consultados em páginas sucessivas durante novas gravações. | Ordenação/paginação estáveis, sem perda ou duplicação lógica dos eventos já existentes. |
| CA35 | Anexo é enviado, consultado ou substituído. | Hash, metadados, vínculo, autorização e histórico são preservados; alteração não destrói evidência formalizada. |
| CA36 | Registro legado não possui evidência suficiente para vínculo com novo domínio. | Não é associado por presunção; permanece identificado como legado não reconciliado. |
| CA37 | Protocolo SEFI, accession e QR são apresentados em telas/documentos. | Cada elemento mantém finalidade e vínculo próprios; QR não substitui identificador persistido. |

### 30.1 Limite desta complementação

CA25–CA37 são propostas de complementação funcional derivadas da revisão multidisciplinar. A adoção definitiva dos contratos HTTP, tecnologias de armazenamento, políticas de retenção, SSO/MFA e mecanismos de ancoragem externa depende da arquitetura e da governança institucional. Nenhum item desta seção autoriza migração, endpoint, alteração de interface ou infraestrutura.

### 30.2 Histórico

| Versão | Data | Descrição |
|---|---|---|
| 1.5 | 2026-11-10 | Complementos multidisciplinares sobre quantidades, timestamps, taxonomia de custódia, protocolo/accession/QR, isolamento de solicitante, concorrência, idempotência, histórico, evidências e dados legados; critérios propostos CA25–CA37. |
