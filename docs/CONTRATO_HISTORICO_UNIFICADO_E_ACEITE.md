# Contrato do Histórico Unificado e da Transação de Aceite

**Identificador:** CTR-LIMS-CUST-001  
**Versão:** 0.1  
**Situação:** Proposta técnica para revisão funcional e arquitetural. Não aprovada para implementação.  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Data:** 2026-11-09

---

## 1. Objetivo e limites

Este documento propõe o contrato funcional e técnico para:

1. consultar uma única linha histórica de custódia que inclua eventos anteriores e posteriores à criação de \`DeviceSample\`;
2. manter consultáveis os eventos legados vinculados diretamente a \`DeviceSample\`;
3. registrar e consultar eventos novos vinculados a \`CustodyObject\`, inclusive antes do aceite;
4. realizar o aceite de um objeto e a criação da amostra operacional de forma atômica, idempotente e auditável;
5. preservar o histórico de materiais pendentes, recusados e aceitos, sem criar amostra operacional antes da elegibilidade.

O contrato é independente de implementação e não define ainda nomes finais de rotas, schemas Pydantic, tabelas ou telas. Os nomes de campos e exemplos são ilustrativos, salvo quando identificam estruturas existentes.

**Não foram alterados código, schema, banco, migrações, API, frontend ou testes. Nenhum teste ou build foi executado nesta atividade.**

## 2. Conceitos e fontes de verdade

| Conceito | Papel no contrato |
|---|---|
| \`ReceiptItem\` | Registro de conferência de cada item declarado no recebimento principal. |
| \`CustodyObject\` | Unidade individual ou agrupada sob guarda e rastreabilidade. Existe a partir da entrada física sob custódia. |
| \`ChainOfCustody\` | Tabela física existente que deverá representar o histórico unificado de eventos. |
| \`CustodyEvent\` | Nome lógico do evento de custódia; não significa criar uma segunda tabela de histórico. |
| \`DeviceSample\` | Amostra operacional criada somente após aceite final e validações obrigatórias. |

### 2.1 Alvo de cada evento

Cada evento deverá apontar para exatamente um alvo:

- **Evento legado:** \`device_sample_id\` preenchido e \`custody_object_id\` nulo.
- **Evento do novo fluxo:** \`custody_object_id\` preenchido e \`device_sample_id\` nulo.

A proposta mantém a tabela \`chain_of_custody\`, com a FK legada nullable e uma nova FK para \`CustodyObject\`, ambas com integridade referencial e exclusão restrita. Um CHECK deverá impedir evento sem alvo ou com os dois alvos preenchidos.

Eventos do novo fluxo continuarão apontando para \`CustodyObject\` mesmo depois de existir \`DeviceSample\`. Não se deve copiar ou duplicar eventos para a FK da amostra no momento do aceite.

Essa estratégia é coerente com a análise de compatibilidade, mas a adoção de tabela única e do CHECK XOR ainda depende de revisão arquitetural (COMP01).

### 2.2 Fonte de verdade por atributo

- O evento persistido é a fonte de verdade para a ocorrência histórica de uma movimentação ou ato de custódia.
- \`transferred_at\`, existente, representa o instante efetivo do evento.
- \`created_at\`, se confirmado no schema e mantido, representa o instante de gravação no sistema, não substitui o instante efetivo.
- A autoria de quem registrou o evento deve ser explícita no contrato. O schema atual não possui \`recorded_by_id\`; a forma de persistência é pendente.
- O custodiante de destino e a localização de destino representam o resultado do evento; o estado corrente pode ser uma projeção, mas não substitui o histórico.
- O registro de chegada/recebimento deve preservar o recebedor físico real e o instante original, sem confundi-los com quem posteriormente conferiu, decidiu ou aceitou o material.

## 3. Contrato de consulta do histórico unificado

### 3.1 Consultas lógicas

O sistema deverá oferecer as seguintes consultas, independentemente dos nomes finais das rotas:

| Consulta | Fonte | Uso |
|---|---|---|
| Histórico de um \`CustodyObject\` | Eventos com \`custody_object_id\` igual ao objeto | Antes e depois do aceite; materiais pendentes, recusados ou aceitos. |
| Histórico de uma \`DeviceSample\` nova vinculada a objeto | Eventos do \`CustodyObject\` associado | Exibir a cadeia contínua iniciada antes da amostra. |
| Histórico de uma \`DeviceSample\` legada sem objeto | Eventos com \`device_sample_id\` igual à amostra | Preservar integralmente o comportamento legado. |
| Histórico de uma amostra, sem vínculo conhecido | Não inferir vínculo; consultar somente fonte legada | Evitar associação retroativa não comprovada. |

A consulta da amostra nova deverá resolver primeiro se há \`custody_object_id\`. Se houver, consulta o histórico do objeto. Se não houver, mantém a consulta legada por \`device_sample_id\`. Não se deve combinar as duas fontes para uma mesma amostra nova, pois isso poderia duplicar eventos.

### 3.2 Resposta lógica de evento

A resposta deverá identificar o alvo e os instantes sem ambiguidade. Exemplo conceitual:

\`\`\`json
{
  "event_id": "uuid",
  "target": {
    "type": "CUSTODY_OBJECT",
    "id": "uuid"
  },
  "event_type": "TRANSFER",
  "occurred_at": "2026-11-09T14:20:00-03:00",
  "recorded_at": "2026-11-09T14:22:13-03:00",
  "from_custodian_id": "uuid-or-null",
  "to_custodian_id": "uuid",
  "location_from": "Recebimento",
  "location_to": "Área de guarda",
  "reason": "Transferência de responsabilidade",
  "seal_number": null,
  "recorded_by_id": "uuid",
  "signature_id": null,
  "notes": null,
  "source": "NEW_FLOW"
}
\`\`\`

O exemplo não aprova o vocabulário \`event_type\`, nem determina quais eventos exigem assinatura. O schema atual não possui \`event_type\` ou \`recorded_by_id\`; sua inclusão ou mapeamento formal permanece pendente (COMP02/COMP03 e EST07).

Para eventos legados, o contrato de leitura deverá preservar os dados originais. Quando não houver informação equivalente, retornar nulo ou indicar a origem legada; nunca fabricar tipo, autoria, localização ou assinatura por inferência.

### 3.3 Ordenação, fuso e empates

A ordenação padrão deverá ser cronológica crescente pelo instante efetivo do evento (\`occurred_at\`, mapeado inicialmente para \`transferred_at\`). A API poderá oferecer ordenação decrescente para apresentação, sem alterar a semântica.

Regras propostas:

1. Persistir instantes como timestamps com fuso/instante inequívoco; preferir armazenamento UTC e conversão para o fuso de apresentação institucional.
2. Não interpretar timestamp sem offset como horário local sem regra explícita de migração/compatibilidade.
3. Para eventos com o mesmo instante efetivo, usar \`recorded_at\` como segundo critério e identificador estável do evento como desempate final.
4. A ordem de apresentação não deve ser confundida com causalidade. Se a sequência operacional for relevante, poderá ser necessário um número de sequência por objeto, decisão ainda não tomada.
5. Exibir, quando útil, tanto o instante efetivo quanto o instante de registro, especialmente em lançamentos tardios e retificações.
6. Não reordenar ou reescrever eventos históricos para simular uma sequência que não foi registrada.

A precisão e o tipo físico dos timestamps devem ser confirmados no schema antes da implementação.

### 3.4 Paginação e filtros

A consulta deverá suportar paginação estável, preferencialmente por cursor composto pelos campos de ordenação e identificador do evento. Filtros por período, tipo, custodiante e localização poderão ser disponibilizados conforme necessidade operacional.

A paginação não poderá omitir eventos quando novos registros forem inseridos durante a navegação. A estratégia de cursor e o comportamento sob inserção concorrente deverão ser especificados no desenho da API.

### 3.5 Compatibilidade com contratos existentes

As rotas legadas e seus formatos atuais deverão continuar funcionando durante a transição. O novo contrato deverá acrescentar consultas por objeto e permitir que a consulta de uma amostra nova recupere a cadeia do objeto.

O schema de resposta legado que exige \`device_sample_id\` não deve ser alterado de forma incompatível sem estratégia de versionamento. Para respostas unificadas, o alvo explícito substitui a suposição de que todo evento pertence a uma amostra.

Os caminhos e nomes exatos de endpoints ficam para a especificação de API. Não se propõe remover \`POST /samples\`, \`POST /custody/transfer\` ou consultas existentes nesta etapa.

## 4. Estados do material e continuidade da custódia

### 4.1 Material pendente

Um objeto pendente:

- permanece sob custódia e possui histórico consultável;
- pode ter pendência aberta, evidências, observações e tentativas de regularização registradas;
- não gera \`DeviceSample\` enquanto houver bloqueio impeditivo ou validação obrigatória pendente;
- mantém o histórico anterior, sem sobrescrever eventos ou respostas de checklist;
- pode receber novos eventos de custódia, respeitando autorização e rastreabilidade.

A regularização deve ser registrada como novo fato/versionamento da pendência ou da conferência, preservando o que foi observado anteriormente. A mudança de estado para elegível não apaga o estado pendente anterior.

### 4.2 Material recusado

Um objeto recusado:

- permanece rastreável e consultável;
- não gera \`DeviceSample\` pelo fluxo ordinário;
- continua sob custódia até que haja transferência, devolução, destinação ou encerramento formal;
- deve ter decisão, motivo, responsável, instante e eventual validação registrados;
- não pode ser tratado como material devolvido apenas porque foi recusado.

A custódia só se encerra ou muda de responsável mediante evento apropriado e autorizado. A taxonomia dos eventos de devolução/destinação e os perfis autorizados permanecem pendentes (COMP06, EST04 e EST10).

Uma reversão de recusa não deverá apagar a decisão anterior. Se a política permitir reconsideração, deverá existir nova decisão formal, vinculada à anterior e com justificativa. A permissão para reconsiderar e as condições de reabertura ainda precisam de aprovação funcional.

### 4.3 Material aceito

Um objeto aceito:

- deve ter conferência concluída e critérios impeditivos atendidos;
- deve ter pendências impeditivas resolvidas;
- deve possuir validação de coordenação quando exigida;
- pode originar no máximo uma \`DeviceSample\`;
- mantém a mesma cadeia de custódia, que continua vinculada ao objeto;
- deve preservar o instante e o responsável da chegada física original.

Aceite não significa encerramento da custódia. A custódia continua após a criação da amostra, e eventos posteriores seguem apontando para \`CustodyObject\`.

### 4.4 Itens não apresentados

Item declarado e não apresentado deve permanecer no recebimento como “não apresentado”, sem \`CustodyObject\`, sem evento de custódia e sem \`DeviceSample\`. Não se deve criar um objeto vazio para satisfazer cardinalidade.

Material entregue em data posterior não pode ser incorporado retroativamente ao recebimento original. Deve seguir nova solicitação ou exceção institucional formalmente aprovada, conforme regra já definida para o projeto.

## 5. Contrato transacional do aceite

### 5.1 Pré-condições

Antes de iniciar a transação, o serviço deve identificar o objeto e o item de recebimento de origem. Dentro da transação, deve revalidar:

1. o objeto existe e está vinculado a item efetivamente apresentado;
2. a conferência exigida está concluída;
3. não há pendência impeditiva aberta;
4. as pendências saneáveis foram tratadas conforme regra aprovada;
5. a decisão de aceite é válida e foi registrada por ator autorizado;
6. a validação de coordenação foi concluída quando exigida;
7. o objeto ainda não possui \`DeviceSample\`;
8. o objeto não está em estado incompatível com aceite, como recusa definitiva ou destinação encerrada;
9. os dados mínimos para criação da amostra estão disponíveis e validados, sem impor número de série a materiais para os quais ele não se aplica.

Os critérios impeditivos/saneáveis/informativos e a exigência de assinatura dependem das decisões EST06 e EST07.

### 5.2 Unidade atômica

A operação deverá ocorrer em uma única transação de banco, com isolamento/bloqueio suficiente para serializar aceites concorrentes do mesmo objeto. Sequência lógica proposta:

1. iniciar transação;
2. bloquear o \`CustodyObject\` e os registros de decisão/validação relevantes;
3. verificar chave de idempotência e estado atual;
4. validar todas as pré-condições;
5. confirmar que não existe amostra vinculada ao objeto;
6. criar \`DeviceSample\` com FK para o objeto;
7. gerar o identificador institucional, preservando o comportamento vigente de \`accession_number\` até conclusão da DEC07;
8. copiar \`received_at\` do instante original da chegada e \`received_by_id\` do recebedor físico real;
9. definir \`created_at\` e autoria de criação com o instante/ator efetivo da operação de aceite, sem confundir com chegada;
10. manter os eventos já existentes vinculados ao objeto, sem criar evento de recebimento duplicado;
11. atualizar projeções de estado/custodiante/localização somente conforme regra aprovada e de modo consistente com a cadeia;
12. registrar auditoria e assinatura, se exigida, no escopo correto;
13. persistir o resultado idempotente da operação;
14. confirmar a transação.

Se qualquer etapa obrigatória falhar, toda a transação deve ser revertida. Não pode haver amostra sem vínculo, identificador consumido sem política definida, evento parcial ou aceite registrado sem a criação correspondente quando a operação tiver sido definida como indivisível.

A política de consumo de sequências de identificadores em rollback pode permitir lacunas; não se deve exigir sequência sem lacunas sem decisão institucional específica.

### 5.3 Idempotência

A operação deverá receber uma chave de idempotência estável por tentativa lógica de aceite. O escopo recomendado é o objeto de custódia e a operação de aceite, não o usuário ou a sessão.

Comportamento:

- primeira chamada válida: executa a operação e retorna a amostra criada;
- repetição com a mesma chave e mesmo conteúdo lógico: retorna o mesmo resultado, sem criar outra amostra, evento ou identificador;
- repetição com a mesma chave e conteúdo divergente: retorna conflito controlado;
- chamada concorrente com chave diferente para o mesmo objeto: apenas uma pode criar a amostra; a outra recupera o resultado já confirmado ou retorna conflito com referência à amostra existente;
- falha antes do commit: não deixa resultado parcial; uma nova tentativa poderá executar conforme a política de idempotência;
- timeout após commit: repetição recupera o resultado confirmado.

A idempotência deve ser protegida por constraints no banco, em especial UNIQUE de \`DeviceSample.custody_object_id\` e, se adotado, armazenamento persistente da chave de idempotência. Verificação apenas no frontend ou em código antes da gravação não é suficiente.

A retenção da chave e o prazo de replay ainda precisam ser definidos na especificação de API.

### 5.4 Identificador e QR Code

A criação deve preservar o contrato atual de \`accession_number\` e QR Code até que a DEC07 determine formalmente se o campo já cumpre a função de identificador institucional.

Não criar um segundo identificador equivalente por conveniência. A amostra criada pelo aceite deve ter exatamente um identificador institucional único conforme a regra aprovada. O QR Code deve continuar resolvendo para a mesma identidade de amostra e não deve mudar de significado durante a transição.

O formato visual, prefixo, ano e sequência não estão aprovados neste documento.

### 5.5 Dados de chegada versus dados de aceite

Os campos devem manter semânticas distintas:

| Dado | Origem |
|---|---|
| \`received_at\` | Instante original da chegada física registrado no Receipt. |
| \`received_by_id\` | Usuário que recebeu fisicamente o material. |
| \`created_at\` | Instante em que a DeviceSample foi efetivamente criada no aceite. |
| Autor do aceite | Usuário que executou/confirmou a decisão, conforme trilha de auditoria. |
| Conferente | Usuário que realizou a conferência, se distinto do recebedor. |
| Validador | Usuário que realizou validação de coordenação, quando exigida. |

Não substituir recebedor físico pelo usuário que aceitou, conferiu ou cadastrou a amostra posteriormente.

## 6. Auditoria, assinatura e retificação

### 6.1 Auditoria

A auditoria deverá permitir reconstruir:

- quem registrou a chegada e quando;
- quem conferiu cada item e quando;
- quem abriu/regularizou pendências;
- quem decidiu pelo aceite ou recusa;
- quem validou pela coordenação, quando aplicável;
- quem executou a operação de criação da amostra;
- qual objeto originou a amostra;
- qual chave/operação idempotente foi concluída;
- quais dados foram assinados, se houver assinatura.

O \`AuditLog\` genérico existente pode ser tecnicamente reutilizável, mas os tipos de entidade, ações, snapshots, filtros e relatórios precisam ser definidos. A flexibilidade do modelo atual não substitui uma taxonomia auditável.

### 6.2 Assinatura eletrônica

Este documento não determina que toda chegada, transferência, conferência, decisão ou aceite exija assinatura eletrônica. A obrigatoriedade, o ator, o alvo da assinatura e o snapshot assinado dependem da decisão EST07 e da governança aplicável.

Quando exigida, a assinatura deverá estar vinculada ao ato e à entidade corretos no momento em que o ato ocorre. Uma assinatura vinculada a \`DeviceSample\` não deve ser usada retroativamente para representar uma chegada anterior à existência da amostra.

### 6.3 Correções e retificações

O histórico de custódia deve permanecer append-only. Não editar nem excluir eventos formalizados para corrigir erro.

A correção deverá ser registrada por retificação ou evento compensatório que:
- referencie o evento corrigido;
- informe o motivo;
- preserve o valor original;
- identifique autor e instante de registro;
- mantenha o instante efetivo original e o instante da retificação separados;
- receba assinatura quando a regra aprovada exigir.

A semântica exata de retificação, permissões e campos de supersessão depende de EST08. Não se deve criar um evento compensatório genérico sem definir como ele afeta o estado corrente.

## 7. Projeções de estado e localização

A cadeia de eventos é a fonte histórica. Campos como \`current_custodian_id\`, \`current_location\` e status corrente podem ser mantidos como projeções para consulta eficiente, desde que:

1. sejam atualizados na mesma transação que o evento correspondente;
2. sejam reconstruíveis a partir dos eventos e decisões formais;
3. não sejam apresentados como evidência histórica independente;
4. tenham regra de reconciliação e detecção de divergência;
5. a transição de legado seja explicitamente tratada.

A decisão sobre manter esses campos em \`DeviceSample\` como projeções sincronizadas ou descontinuá-los em favor do objeto continua pendente (COMP03). Até essa decisão, o contrato não autoriza remover nem alterar sua semântica.

## 8. Cenários de aceitação propostos (não executados)

Os cenários abaixo são critérios candidatos para futura suíte automatizada e validação funcional. Não representam testes executados.

| ID | Cenário | Resultado esperado |
|---|---|---|
| HST-01 | Consultar histórico de objeto antes de existir DeviceSample | Retornar eventos vinculados ao objeto, em ordem cronológica. |
| HST-02 | Consultar amostra nova vinculada a objeto | Retornar cadeia do objeto, incluindo chegada anterior ao aceite, sem duplicidade. |
| HST-03 | Consultar amostra legada sem objeto | Retornar eventos legados por device_sample_id, sem associação inferida. |
| HST-04 | Evento com ambos os alvos nulos | Rejeitar pela integridade do banco. |
| HST-05 | Evento com ambos os alvos preenchidos | Rejeitar pela integridade do banco. |
| HST-06 | Dois eventos com mesmo occurred_at | Aplicar desempate estável por recorded_at e identificador. |
| HST-07 | Evento registrado depois do instante efetivo | Exibir ambos os instantes sem reescrever a cronologia. |
| HST-08 | Objeto pendente com custódia transferida | Manter histórico e custódia; não criar DeviceSample. |
| HST-09 | Objeto recusado | Manter histórico; não criar DeviceSample; exigir evento próprio para devolução/destinação. |
| HST-10 | Item declarado não apresentado | Não criar CustodyObject, evento de custódia ou DeviceSample. |
| HST-11 | Aceite sem pendência impeditiva e com validações concluídas | Criar uma única DeviceSample vinculada ao objeto. |
| HST-12 | Aceite com pendência impeditiva aberta | Bloquear sem criação parcial. |
| HST-13 | Aceite que exige coordenação sem validação | Bloquear sem criação parcial. |
| HST-14 | Repetir aceite com mesma chave | Retornar a mesma amostra sem duplicar eventos ou identificador. |
| HST-15 | Dois aceites concorrentes para o mesmo objeto | No máximo uma amostra; resultado determinístico para a segunda chamada. |
| HST-16 | Falha antes do commit | Reverter toda a operação, sem amostra ou aceite parcial. |
| HST-17 | Aceite posterior à chegada | Preservar received_at e received_by_id originais; created_at posterior. |
| HST-18 | Aceite de material sem número de série aplicável | Não impor serial fictício; aplicar regra de identidade aprovada. |
| HST-19 | Retificação de evento | Preservar evento original e registrar retificação auditável. |
| HST-20 | Consulta de timeline após várias transferências | Localização histórica da chegada não deve ser substituída pela localização atual. |
| HST-21 | Evento novo após criação de DeviceSample | Continuar vinculado ao CustodyObject e aparecer no histórico da amostra. |
| HST-22 | Tentativa de criar segunda DeviceSample para o objeto | Rejeitar pela constraint e retornar resultado idempotente/conflito controlado. |
| HST-23 | Evento legado sem autoria equivalente explícita | Preservar dado original sem inventar recorded_by_id. |
| HST-24 | Página seguinte do histórico durante novas inserções | Paginação estável, sem perda ou duplicação indevida de eventos. |

## 9. Decisões em aberto e dependências

| Referência | Questão | Impacto neste contrato |
|---|---|---|
| COMP01 | Adoção da tabela única \`chain_of_custody\` com dois alvos e CHECK XOR | Base física do histórico unificado. |
| COMP02 | Conteúdo e semântica do evento inicial; campos aditivos \`event_type\` e autoria | Classificação e rastreabilidade dos eventos. |
| COMP03 | \`current_custodian_id\`/\`current_location\` como projeções sincronizadas ou campos legados | Estado corrente e consistência. |
| COMP04 | Obrigatoriedade de serial e unicidade serial/lote/fabricante | Dados mínimos para criação da amostra e prevenção de duplicidade. |
| COMP05 | Contrato final de API, payload e compatibilidade das rotas | Integração backend/frontend. |
| COMP06 | Fracionamento, agrupamento, devolução e destinação | Cardinalidade e ciclo de vida do objeto. |
| COMP07 | Estratégia de testes de integridade, concorrência, idempotência e continuidade | Evidência técnica antes de ativação. |
| DEC07 | Reutilização de \`accession_number\` como identificador institucional | Geração, QR Code e compatibilidade. |
| DEC08 | Tratamento de registros legados sem associação presumida | Consulta e migração retrocompatíveis. |
| EST04 | Destino de materiais recusados | Encerramento ou transferência da custódia. |
| EST06 | Classificação de critérios impeditivos/saneáveis/informativos | Elegibilidade do aceite. |
| EST07 | Atos que exigem assinatura eletrônica | Alvo, snapshot e bloqueio transacional. |
| EST08 | Correções excepcionais e retificações | Semântica append-only e autorização. |
| EST10 | Segregação de funções e autoaprovação | Permissões para decisão e validação. |

Nenhum ponto acima é considerado resolvido por este documento. Onde a decisão estiver pendente, o contrato descreve comportamento-alvo condicionado à aprovação, não uma regra institucional já vigente.

## 10. Critérios de revisão deste contrato

Antes de detalhar a implementação, revisar e aprovar:

1. se a cadeia unificada atende à governança e aos requisitos de rastreabilidade;
2. se a ordenação e a distinção entre instante efetivo e instante de registro atendem aos registros reais;
3. se a consulta por objeto e por amostra preserva compatibilidade e evita duplicidade;
4. quais estados de pendência e recusa bloqueiam ou permitem reconsideração;
5. quais dados são obrigatórios para cada tipo de dispositivo, sem exigir serial universalmente;
6. qual política de assinatura e auditoria se aplica a cada ato;
7. como são tratadas devolução, destinação, agrupamento e fracionamento;
8. qual regra institucional identifica a amostra e mantém o QR Code;
9. como são protegidos concorrência, idempotência e integridade;
10. quais cenários de teste serão obrigatórios e quais evidências serão exigidas.

## 11. Próximas atividades recomendadas

1. Submeter este contrato e a análise de compatibilidade a revisão arquitetural e funcional.
2. Resolver COMP02–COMP07 e as decisões EST04, EST06–EST08 e EST10 que afetam o contrato.
3. Confirmar DEC07/DEC08 e os usos atuais de \`accession_number\` e QR Code.
4. Após aprovação, detalhar schemas/rotas da API e regras de autorização, sem alterar ainda o banco.
5. Somente com autorização específica, preparar migração aditiva, implementação e suíte de testes.
6. Executar testes e validação em ambiente controlado em etapa própria, com registro de evidências e aprovação correspondente.

**Este documento não autoriza implementação. Não houve alteração de código, schema, banco, migrações, API, frontend ou testes.**

## 12. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-09 | Primeira proposta de contrato para histórico unificado, estados pendente/recusado/aceito, transação de aceite, idempotência, auditoria, assinatura, retificação e cenários de teste candidatos. |
