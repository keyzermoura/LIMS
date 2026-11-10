# Estados e Transições — Solicitação e Recebimento

**Identificador:** EST-REC-001  
**Versão:** 1.2  
**Situação:** Proposta para revisão funcional alinhada ao modelo M0.2 aprovado; EST02 a EST10 aprovadas; EST01 pendente; não aprovada para implementação  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Data:** 2026-11-09

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

### 3.5 Regularização

| Estado | Significado |
|---|---|
| NAO_HA_PENDENCIA | Não há pendência aberta. |
| PENDENTE | Há providência necessária antes da decisão final. |
| EM_REGULARIZACAO | Providência está sendo tratada. |
| REGULARIZADA | Evidência/providência foi recebida e reavaliada. |
| NAO_REGULARIZAVEL | A condição não pode ser sanada no fluxo; encaminhar para decisão de recusa ou outra destinação autorizada. |

A regularização não apaga a pendência original. Deve criar novo evento, registrar evidência e preservar quem reavaliou.

### 3.6 Decisão do item

| Estado | Significado |
|---|---|
| NAO_DECIDIDA | Ainda não há decisão formal. |
| ACEITA | Requisitos de admissão atendidos e validações obrigatórias concluídas. |
| PENDENTE | Não é possível concluir enquanto houver condição a regularizar ou revisar. |
| RECUSADA | Item não admitido, com fundamento e evidência quando aplicável. |

Decisão PENDENTE não equivale a encerramento. Uma decisão anterior deve permanecer no histórico quando substituída por nova decisão autorizada.

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
| NAO_INICIADA | Material não foi apresentado; não existe custódia física registrada. |
| SOB_GUARDA | Material apresentado sob responsabilidade institucional. |
| TRANSFERENCIA_PENDENTE | Transferência iniciada, mas ainda não confirmada pelo recebedor de destino. |
| SOB_NOVA_RESPONSABILIDADE | Transferência concluída e aceita pelo novo responsável. |
| ENCERRADA | Custódia encerrada por destinação formalmente registrada. |

Custódia inicia na chegada física do material apresentado, independentemente do aceite. Material recusado também exige registro de sua guarda e da destinação/devolução até a entrega efetiva ao responsável externo.

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

| Origem | Destino | Quem pode executar | Pré-condições |
|---|---|---|---|
| inexistente | REGISTRADO | Recebedor autorizado | Solicitação submetida; registrar chegada efetiva, recebedor físico e dados gerais; unicidade de solicitação garantida no banco. |
| REGISTRADO | EM_CONFERENCIA | Conferente autorizado | Itens apresentados identificados; checklist aplicável disponível. |
| EM_CONFERENCIA | AGUARDANDO_REGULARIZACAO | Sistema/conferente | Uma ou mais pendências abertas. |
| EM_CONFERENCIA | AGUARDANDO_COORDENACAO | Sistema/conferente | Regra versionada exige revisão da coordenação. |
| EM_CONFERENCIA | PARCIALMENTE_DECIDIDO | Sistema | Ao menos um item decidido e outros ainda em tratamento. |
| EM_CONFERENCIA | CONCLUIDO | Sistema | Todos os itens encerrados; sem ação obrigatória pendente. |
| AGUARDANDO_REGULARIZACAO | EM_CONFERENCIA | Sistema/conferente | Pendência regularizada e reavaliada, ou encaminhada a outro desfecho permitido. |
| AGUARDANDO_COORDENACAO | EM_CONFERENCIA | Sistema | Coordenação aprovou/devolveu/rejeitou e a ação subsequente foi registrada. |
| PARCIALMENTE_DECIDIDO | CONCLUIDO | Sistema | Todos os itens encerrados e todas as condições de fechamento atendidas. |

Os estados agregados são informativos e devem ser calculados a partir dos estados dos itens. O sistema deve impedir fechamento se houver item apresentado sem decisão ou material sob custódia sem destinação definida.

### 4.3 Item de recebimento

| Origem | Destino | Quem pode executar | Pré-condições |
|---|---|---|---|
| AGUARDANDO_CHEGADA | APRESENTADO | Recebedor autorizado | Material fisicamente presente; quantidade/identificação efetiva registradas. |
| AGUARDANDO_CHEGADA | NAO_APRESENTADO | Recebedor autorizado | Ausência confirmada e registrada na chegada. |
| APRESENTADO | conferência EM_ANDAMENTO | Conferente autorizado | Material sob custódia e checklist carregado. |
| EM_ANDAMENTO | conferência CONCLUIDA | Conferente autorizado | Todos os critérios obrigatórios respondidos; justificativas e evidências requeridas presentes. |

Depois de registrado como NAO_APRESENTADO, o item não pode ser alterado para APRESENTADO como se tivesse chegado na data original. Entrega posterior exige nova solicitação ou exceção institucional formal, com evento e data/hora reais.

### 4.4 Decisão e validação

| Evento | Resultado | Regra |
|---|---|---|
| Formalizar aceite | ACEITA | Checklist concluído; nenhum impeditivo não conforme; pendências resolvidas; validação da coordenação concluída quando exigida. |
| Formalizar pendência | PENDENTE | Há requisito saneável ou informação faltante que impede conclusão. Deve indicar providência e responsável/prazo quando aplicável. |
| Formalizar recusa | RECUSADA | Fundamento documentado; critérios e evidências aplicáveis registrados; destinação do material sob custódia definida. |
| Encaminhar coordenação | AGUARDANDO | Exceção/regra exige validação; pacote de evidências e decisão do conferente completos. |
| Coordenador aprova | APROVADA | Dentro da competência e sem dispensar bloqueios impeditivos. |
| Coordenador devolve | DEVOLVIDA | Justificativa e complementação requerida registradas. |
| Coordenador rejeita | REJEITADA | Justificativa formal; item retorna ao fluxo definido ou segue para recusa, conforme regra aprovada. |

## 5. Matriz de permissões — proposta inicial

| Ação | Operador/Recebedor | Conferente/Técnico | Coordenador | Administrador |
|---|---:|---:|---:|---:|
| Cadastrar solicitação | Sim, se autorizado | Sim, se autorizado | Sim, se autorizado | Configurável |
| Registrar chegada física | Sim | Sim, se designado | Sim, se designado | Não por privilégio automático |
| Marcar item apresentado/não apresentado | Sim, no ato da chegada | Sim, se designado | Não por padrão | Não por privilégio automático |
| Preencher checklist | Não por padrão | Sim | Apenas quando formalmente designado | Não por privilégio automático |
| Registrar pendência | Não por padrão | Sim | Sim, na revisão | Não por privilégio automático |
| Formalizar decisão do conferente | Não por padrão | Sim, se autorizado | Conforme segregação aprovada | Não por privilégio automático |
| Validar decisão encaminhada | Não | Não | Sim, se designado | Não por privilégio automático |
| Corrigir registro concluído | Não | Apenas com permissão específica, justificativa e histórico | Conforme permissão específica | Não deve editar conteúdo técnico por padrão |
| Configurar checklists e regras | Não | Não | Conforme governança | Administrador técnico com aprovação de conteúdo pelo responsável competente |

Esta matriz não mapeia automaticamente os perfis existentes do software. O inventário identificou perfis como ADMIN, FISCAL, TECNICO, CUSTODIANTE e AUDITOR, mas sua equivalência com funções operacionais precisa ser avaliada. A segregação de funções e a possibilidade de autoaprovação devem ser decididas institucionalmente.

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
| EST01 | Quais perfis institucionais podem cadastrar solicitação, receber material e conferir? | P0 |
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

Concluir a decisão funcional remanescente EST01 e, em seguida, consolidar a máquina de estados e produzir os critérios de aceite verificáveis para a Etapa 1. As decisões EST02–EST10 estão registradas. A implementação permanece bloqueada até conclusão da Fase 0, aprovação do portão G0 e autorização específica.

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

A EST01 permanece aberta. As decisões EST02 e EST10 já definem, respectivamente, a possibilidade de acumular recebimento e conferência e os controles gerais de segregação e autoaprovação. A próxima revisão deverá definir os perfis institucionais autorizados a cadastrar solicitações, registrar chegadas e realizar conferências;
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

EST02 fica **resolvida funcionalmente**. A matriz de permissões deverá permitir a acumulação dos papéis de recebedor e conferente, condicionada à atribuição explícita das permissões correspondentes. A definição dos perfis institucionais autorizados permanece pendente em EST01. A segregação e a autoaprovação são tratadas na EST10.

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

EST10 fica **resolvida funcionalmente** quanto ao acúmulo de atividades operacionais, à proibição de autoaprovação nas decisões sujeitas à validação independente e ao tratamento da indisponibilidade de validador. A definição nominal dos perfis institucionais, dos cargos e das substituições autorizadas permanece vinculada à EST01 e à matriz de competências institucional, a serem formalizadas antes da utilização operacional.

Esta decisão não autoriza implementação. A implementação permanece condicionada à conclusão da Fase 0, aprovação do portão G0 e autorização específica.

### Histórico

| Versão | Data | Descrição |
|---|---|---|
| 1.2 | 2026-11-10 | Registro da decisão EST10: acúmulo de atividades operacionais permitido conforme permissões; autoaprovação vedada quando houver validação independente; indisponibilidade não dispensa validação. |
