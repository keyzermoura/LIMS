# Matriz de Harmonização de Estados, Transições e Eventos do LIMS-SEFI

**Identificador:** MAT-HARM-EST-SEFI-001  
**Versão:** 0.1 — análise de harmonização  
**Data:** 2026-11-11  
**Fontes:** EST-REC-001 v1.7 (seções 25–30); M0.2 v0.7; M0.3 v0.1; D01–D20; SIM01–SIM12; BCDP-LIMS-SEFI-001 v0.1.  
**Status:** matriz analítica; não validada; não altera documentos-fonte.

## 1. Objetivo

Explicitar a correspondência entre as máquinas de estado da EST-REC-001 e os estados propostos em M0.3, separando estados de entidades, resultados decisórios, condições temporais, eventos e projeções. A matriz subsidia a revisão da baseline consolidada e evita a criação de um único status global.

## 2. Regras de harmonização

1. EST-REC-001, especialmente decisões EST01–EST10 e seções 25–30, é a referência funcional consolidada para os processos de recebimento.
2. M0.2 prevalece nas sete cardinalidades canônicas.
3. M0.3 detalha o domínio, mas estados/refinamentos que não constam das decisões aprovadas permanecem propostas.
4. Um evento representa fato; um estado representa condição atual; uma projeção agrega fatos/estados filhos. Não usar os termos como sinônimos.
5. Custódia, decisão, conferência, validação, pendência e localização são dimensões distintas.
6. Os estados agregados de Solicitação, Recebimento e ItemRecebimento são derivados, sem apagar estados e eventos dos objetos filhos.
7. Mapeamento semântico não autoriza alteração de enum, banco, API ou workflow.

## 3. Matriz de harmonização por entidade/dimensão

| Entidade/dimensão | EST-REC-001 v1.7 | M0.3 v0.1 | Referência consolidada nesta análise | Situação |
|---|---|---|---|---|
| Solicitação | RASCUNHO, SUBMETIDA, RECEBIMENTO_REGISTRADO, EM_TRATAMENTO, CONCLUIDA, CANCELADA | Mesmos estados | Preservar os seis estados; conclusão é administrativa e derivada do recebimento. | Equivalência documental |
| Recebimento | REGISTRADO, EM_CONFERENCIA, AGUARDANDO_REGULARIZACAO, AGUARDANDO_COORDENACAO, PARCIALMENTE_DECIDIDO, CONCLUIDO, CANCELADO | Mesmos estados | Preservar os sete estados; estado agregado derivado de itens/objetos, pendências e validações. | Equivalência documental |
| Apresentação do ItemRecebimento | AGUARDANDO_CHEGADA, APRESENTADO, NAO_APRESENTADO | AGUARDANDO_CHEGADA, APRESENTADO, NAO_APRESENTADO, APRESENTACAO_PARCIAL | Preservar os três estados funcionais por ocorrência. APRESENTACAO_PARCIAL fica como condição/projeção proposta baseada na reconciliação de quantidades, até validação. | Parcial; M03-01/M03-03 |
| Conferência | NAO_INICIADA, EM_ANDAMENTO, CONCLUIDA | NAO_INICIADA, EM_ANDAMENTO, CONCLUIDA | Preservar os três estados; inicia somente para material apresentado e sob custódia, com versão de checklist fixada. | Equivalência documental |
| RespostaChecklist | CONFORME, NAO_CONFORME, NAO_APLICAVEL; classes E/S/I na versão | Mesmos valores/classes | Separar resultado da resposta e classificação imutável do critério publicado. | Equivalência documental |
| Pendência | PENDENTE, EM_REGULARIZACAO, AGUARDANDO_REAVALIACAO, REGULARIZADA, PRAZO_VENCIDO, NAO_REGULARIZAVEL, CANCELADA | Mesmos estados | Preservar ciclo. PRAZO_VENCIDO é condição temporal/indicador coexistente com pendência aberta, não estado terminal. | Equivalência com semântica consolidada |
| Decisão | NAO_DECIDIDA; resultados ACEITA, PENDENTE, RECUSADA; retificação como novo ato | ACEITE_PROPOSTO, ACEITE_VALIDADO, PENDENCIA, RECUSA_PROPOSTA, RECUSADA, SUBSTITUIDA | Separar resultado final (ACEITA/RECUSADA/PENDENTE) do workflow de proposta/validação. Os estados de workflow M0.3 são candidatos e não se tornam enum canônico sem harmonização funcional. | Pendente de harmonização |
| Validação da coordenação | NAO_EXIGIDA, AGUARDANDO, APROVADA, DEVOLVIDA, REJEITADA | Mesmos estados | Preservar os cinco estados; validador independente nos casos exigidos; devolução/rejeição não se converte automaticamente em recusa do material. | Equivalência documental |
| Custódia física | SOB_GUARDA, TRANSFERENCIA_PENDENTE, SOB_NOVA_RESPONSABILIDADE, ENCERRADA | SOB_CUSTODIA, EM_CONFERENCIA, PENDENTE, AGUARDANDO_VALIDACAO, ACEITO, RECUSADO, EM_DEVOLUCAO, EM_DESTINACAO, ENCERRADO | Usar a dimensão de custódia da EST: SOB_GUARDA, TRANSFERENCIA_PENDENTE, SOB_NOVA_RESPONSABILIDADE, ENCERRADA. Os estados M0.3 EM_CONFERENCIA/PENDENTE/AGUARDANDO_VALIDACAO/ACEITO/RECUSADO são outras dimensões; EM_DEVOLUCAO/EM_DESTINACAO são etapas de destinação a detalhar. | Mapeamento proposto; revisar com M03-04/M03-15 |
| Custodiante atual | Identidade do responsável atual derivada de eventos confirmados | Separado da situação/localização | Atributo/projeção independente; muda somente após confirmação do recebedor. | Regra aprovada D07 |
| Localização atual | Localização anterior/nova nos eventos | Separada do custodiante | Projeção independente; mudança de local não altera custodiante. | Regra aprovada D08 |
| AmostraOperacional | NÃO_CRIADA, APTA_PARA_CRIACAO (calculada), CRIADA, BLOQUEADA (calculada) | CRIADA, ATIVA, EM_ENSAIO, ENCERRADA, CANCELADA_COM_HISTORICO | No recebimento, limitar-se à condição de aptidão/criação conforme EST. Ciclo posterior de amostra/ensaio permanece no domínio laboratorial e depende de M03-16. | M03-16 pendente |
| Ensaio | Ciclo posterior fora da máquina de recebimento | Estados existentes a compatibilizar | Não redefinir o workflow de ensaios nesta consolidação. | Fora do escopo do recebimento |

## 4. Mapeamento de eventos e estados derivados

| Fato/evento | Estado/projeção afetada | Regra de interpretação |
|---|---|---|
| SOLICITACAO_CRIADA | Solicitação RASCUNHO | Criação não significa submissão. |
| SOLICITACAO_SUBMETIDA | Solicitação SUBMETIDA | Exige campos válidos e ao menos um item declarado. |
| CHEGADA_REGISTRADA | Recebimento REGISTRADO; Solicitação RECEBIMENTO_REGISTRADO | Registra o fato físico; não significa aceite. |
| ITEM_APRESENTADO | ItemRecebimento APRESENTADO | Quantidade/unidade observadas e instante efetivo. |
| ITEM_NAO_APRESENTADO | ItemRecebimento NAO_APRESENTADO | Não gera objeto, custódia, decisão técnica de recusa ou amostra. |
| Apresentação posterior (novo fato) | Histórico do ItemRecebimento/solicitação; eventualmente estado agregado recalculado | D19; nunca altera retroativamente o fato original. A entidade EventoApresentacao é proposta, não imposta. |
| OBJETO_CUSTODIA_CRIADO / CUSTODIA_INICIADA | Objeto sob SOB_GUARDA | Exige material apresentado, responsável e localização inicial. |
| CONFERENCIA_INICIADA | Conferência EM_ANDAMENTO | Fixar versão do checklist e avaliador. |
| CONFERENCIA_CONCLUIDA | Conferência CONCLUIDA | Todos os critérios obrigatórios respondidos e evidências exigidas presentes. |
| PENDENCIA_COMUNICADA | Prazo da pendência começa | Somente com comunicação formal comprovável. |
| PENDENCIA_PRORROGADA | Prazo projetado atualizado | Preservar prazo anterior, justificativa e autorização. |
| REGULARIZACAO_RECEBIDA | Pendência AGUARDANDO_REAVALIACAO | Juntada de evidência não regulariza automaticamente. |
| PENDENCIA_REGULARIZADA | Pendência REGULARIZADA | Exige reavaliação favorável por ator habilitado. |
| DECISAO_ACEITE_REGISTRADA | Resultado ACEITA após controles aplicáveis | Aceite formal e validação exigida concluídos; assinatura conforme regra. |
| DECISAO_RECUSA_REGISTRADA | Resultado RECUSADA | Custódia permanece até destinação efetiva. |
| VALIDACAO_COORDENACAO_REGISTRADA | Validação APROVADA/DEVOLVIDA/REJEITADA | Autor/executor não pode ser validador quando independência obrigatória. |
| TRANSFERENCIA_SOLICITADA | Custódia TRANSFERENCIA_PENDENTE | Custodiante anterior continua responsável. |
| TRANSFERENCIA_CONFIRMADA | Custódia SOB_NOVA_RESPONSABILIDADE | Confirmação do destinatário efetiva a mudança de custodiante. |
| LOCALIZACAO_ALTERADA | Projeção de localização atual | Não altera custodiante. |
| DEVOLUCAO_REALIZADA / DESTINACAO_REALIZADA | Custódia apta a ENCERRADA | Exige execução efetiva, evidência e confirmação aplicáveis. |
| AMOSTRA_OPERACIONAL_CRIADA | Amostra CRIADA; ObjetoCustodia permanece com histórico de custódia | Não reinicia chegada nem cria nova custódia inicial. |
| RETIFICACAO_REGISTRADA | Novo ato relacionado ao original | Preservar evento/decisão original, motivo, evidência, autorização e impacto. |
| RECEBIMENTO_CONCLUIDO | Recebimento CONCLUIDO; Solicitação CONCLUIDA quando aplicável | Fechamento administrativo; não implica aceite universal nem custódia encerrada para objetos sem destinação. |

## 5. Regras de agregação

1. Solicitação e Recebimento são estados agregados derivados; não sobrescrevem estado de item/objeto.
2. ItemRecebimento com vários objetos pode apresentar situação PARCIALMENTE_DECIDIDO ou MISTA, sem ocultar resultados individuais.
3. Recebimento só conclui quando todos os itens possuem desfecho administrativo válido, sem pendências/validações obrigatórias abertas e sem objeto sob custódia sem destino.
4. Item NAO_APRESENTADO pode coexistir com Recebimento CONCLUIDO quando as condições EST05 forem satisfeitas; isso não equivale a aceite.
5. PRAZO_VENCIDO não conclui Pendência nem Recebimento.
6. Objeto RECUSADO pode continuar SOB_GUARDA; decisão e custódia não são o mesmo estado.
7. Custódia ENCERRADA exige destinação efetiva comprovada; autorização isolada não basta.

## 6. Questões que exigem validação antes da baseline definitiva

| ID | Questão | Evidência necessária |
|---|---|---|
| HARM-01 | APRESENTACAO_PARCIAL será estado persistido ou projeção calculada? | Validar SIM02/SIM03/SIM12, reconciliação de quantidade e regra de unidade. |
| HARM-02 | Quais estados de workflow decisório devem existir além do resultado final? | Harmonizar EST-REC-001 26.6 com M0.3 9.8, sem misturar ACEITE_PROPOSTO/ACEITE_VALIDADO com estado de custódia. |
| HARM-03 | Como representar EM_DEVOLUCAO/EM_DESTINACAO sem fundir custódia e decisão? | Procedimento G0-P04/P20 e modelo de eventos/estado físico. |
| HARM-04 | EventoApresentacao será entidade lógica ou apenas evento de domínio? | D19, EST08, SIM12 e M03-01; definir reabertura/nova solicitação e linhagem. |
| HARM-05 | Um ObjetoCustodia pode agregar material de apresentações distintas? | M03-02/M03-03; evitar dupla contagem e perda de origem. |
| HARM-06 | Como compatibilizar estados posteriores da AmostraOperacional com o workflow de ensaios? | M03-16 e testes de regressão do domínio laboratorial. |
| HARM-07 | Qual a projeção exata do estado do Recebimento quando há objeto aceito e outro recusado? | SIM04, regra de menor granularidade e conclusão administrativa EST05. |

## 7. Situação formal

- Correspondência EST-REC-001 × M0.3: **ANÁLISE DOCUMENTAL INICIAL**.
- Regras funcionais EST01–EST10: **APROVADAS**, conforme fonte.
- Cardinalidades M0.2: **PRESERVADAS**.
- Mapeamentos semânticos desta matriz: **PROPOSTOS; NÃO VALIDADOS**.
- Questões HARM-01–HARM-07: **PENDENTES**.
- Gate G0: **NÃO APROVADO**.
- Implementação: **NÃO AUTORIZADA**.

## 8. Histórico

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-11 | Primeira matriz de correspondência entre estados, eventos e projeções de EST-REC-001 e M0.3. |
