# Proposta de Resolução da API04 — Eventos de Custódia, Autoria e Timestamps

**Identificador:** PROP-LIMS-API04-001  
**Versão:** 0.1  
**Situação:** Proposta técnica para validação funcional, metrológica/operacional e institucional; não aprovada para implementação  
**Decisão relacionada:** API04 / COMP02 / COMP03 / DEC04 / EST07 / EST08 / API12  
**Data:** 2026-11-09  
**Repositório:** keyzermoura/LIMS — branch `main`

---

## 1. Objetivo

Definir uma proposta semântica para os eventos da cadeia de custódia do LIMS, distinguindo:

- o fato ocorrido no mundo físico;
- o instante em que o fato foi registrado no sistema;
- a pessoa que efetivamente recebeu ou passou a custodiar o material;
- a pessoa autenticada que lançou o registro;
- a pessoa que entrega e a que recebe uma transferência;
- a origem e o destino físicos do material.

A proposta deve permitir que a custódia comece na chegada física, antes da criação da `DeviceSample`, e continue vinculada ao `CustodyObject` após o aceite, em conformidade com DEC04.

Não se propõe uma tabela paralela de eventos. A recomendação é evoluir, de forma aditiva e compatível, a tabela `ChainOfCustody` existente, sujeita à confirmação do schema real e à aprovação das decisões pendentes.

## 2. Referências e premissas

1. DEC04 estabelece `CustodyObject` como alvo dos eventos de custódia do novo fluxo, antes e depois da criação da amostra operacional.
2. Eventos legados permanecem associados a `DeviceSample`; não se devem inferir vínculos retroativos com `CustodyObject`.
3. O recebimento físico e a custódia começam na chegada do material, não no aceite posterior.
4. `DeviceSample.received_at` e `received_by_id`, quando criada a amostra após o aceite, devem preservar respectivamente o instante original da chegada e a identidade do recebedor físico.
5. O usuário que realiza conferência, validação ou aceite posterior não substitui o recebedor físico nem o autor do evento original.
6. O modelo legado possui `transferred_at`, `from_custodian_id`, `to_custodian_id`, `location_from`, `location_to`, `reason`, `seal_number`, `signature_id` e `notes`; a análise disponível aponta ausência explícita de `event_type` e `recorded_by_id`.
7. A existência e a semântica de `created_at` precisam ser confirmadas no schema efetivo antes de mapear `recorded_at`.
8. API12 permanece pendente para política completa de datas retroativas, lançamentos tardios e fuso horário.

## 3. Vocabulário temporal e de autoria

| Campo conceitual | Significado | Regra proposta |
|---|---|---|
| `occurred_at` | Instante efetivo em que o fato ocorreu fisicamente ou operacionalmente. | Não deve ser substituído pelo momento em que alguém digitou o registro. |
| `recorded_at` | Instante em que o evento foi persistido no LIMS. | Gerado pelo servidor/banco; não livremente informado pelo cliente. |
| `recorded_by` | Usuário autenticado que registrou o evento no sistema. | Obtido da sessão/autorização; não confiar em ID arbitrário no payload. |
| `from_custodian` | Pessoa que entrega a guarda, quando aplicável. | Representa o custodiante anterior, não necessariamente o autor do lançamento. |
| `to_custodian` | Pessoa que assume a guarda, quando aplicável. | Deve representar o custodiante efetivo após o evento. |
| `location_from` | Local físico de origem, quando aplicável. | Preservar como informação do evento, não como projeção mutável. |
| `location_to` | Local físico de destino, quando aplicável. | Preservar como informação do evento, não como projeção mutável. |
| `reason` | Motivo/justificativa do evento. | Obrigatório para transferências, correções, destinações e eventos excepcionais; texto/catálogo final a aprovar. |

**Distinção essencial:** custodiante é quem detém a guarda do material; `recorded_by` é quem registra o fato no sistema. Uma mesma pessoa pode exercer os dois papéis, mas isso não deve ser presumido em todos os eventos.

## 4. Catálogo de eventos proposto

O catálogo abaixo é um ponto de partida para validação institucional. Os códigos são candidatos e não devem ser tratados como enums já implementados.

| Código candidato | Significado | Campos/semântica principais | Observações |
|---|---|---|---|
| `RECEIPT` | Chegada física e início da custódia. | `occurred_at` = instante da chegada; `to_custodian` = recebedor físico; `location_to` = local de recebimento; `recorded_by` = usuário que formaliza o registro. | Evento inicial do objeto. Não aguardar a criação de DeviceSample. |
| `TRANSFER` | Transferência de guarda entre pessoas. | `from_custodian` e `to_custodian` obrigatórios; origem/destino quando aplicáveis; motivo. | Evento de transferência efetiva, não mera alteração de cadastro. |
| `LOCATION_CHANGE` | Mudança de localização sem mudança de custodiante. | `location_from` e `location_to`; custodiante pode permanecer o mesmo. | Não registrar como TRANSFER se a guarda não mudou. |
| `RETURN` | Devolução do material ao solicitante ou representante autorizado. | Destinatário, local/destino, motivo, data efetiva e evidência quando exigida. | Deve estar associada à decisão/autoridade que autorizou a devolução. |
| `DISPOSITION` | Destinação final, descarte, retenção externa ou outra saída de custódia. | Tipo/destino da destinação, responsável, justificativa e evidência. | Vocabulário final depende da política institucional e dos procedimentos aplicáveis. |
| `CLOSURE` | Encerramento da custódia institucional sem transferência física ordinária. | Motivo, autoridade, data efetiva e destino/condição final. | Não equivale automaticamente a exclusão do objeto ou da amostra. |
| `CORRECTION` | Retificação formal de informação/evento anterior. | Referência ao evento corrigido, motivo, autor, instante de registro e dados corretos. | Não sobrescrever ou apagar evento original; definir se é evento compensatório ou entidade de retificação vinculada. |

### 4.1 Regras de uso do catálogo

- Um evento deve representar um fato identificável e ter um único tipo semântico.
- Não usar `TRANSFER` para representar apenas mudança de localização quando a guarda não mudou.
- Não usar `RECEIPT` para simular aceite técnico ou criação de amostra.
- O aceite técnico é uma decisão do fluxo de recebimento; não é, por si só, uma transferência de custódia.
- A recusa técnica não encerra automaticamente a custódia: o material continua sob guarda até devolução, destinação ou outra saída formal.
- Correções não devem reescrever a cadeia histórica; a estratégia concreta de retificação depende de EST08.
- A lista final e os requisitos de assinatura dependem de validação institucional e de API05/EST07.

## 5. Semântica do evento inicial de chegada

### 5.1 Regra proposta

No momento da chegada física:

1. registrar `Receipt.arrived_at` como instante efetivo da chegada;
2. registrar `Receipt.received_by_id` como a pessoa que recebeu fisicamente o material;
3. iniciar a custódia dos objetos apresentados, mesmo que ainda estejam pendentes de conferência ou decisão técnica;
4. criar um evento `RECEIPT` para cada `CustodyObject` criado no recebimento;
5. usar `occurred_at = Receipt.arrived_at` no evento inicial;
6. registrar `recorded_at` no momento em que o registro é efetivamente persistido;
7. identificar `recorded_by` pelo usuário autenticado que executou a operação de formalização;
8. não permitir que o usuário que realiza aceite posterior substitua o recebedor físico ou o instante original.

### 5.2 Custodiante inicial

**Recomendação:** o custodiante inicial do objeto deve ser o recebedor físico indicado em `Receipt.received_by_id`, desde que o procedimento institucional confirme que o recebimento físico transfere a guarda para essa pessoa ou para a equipe/setor sob sua responsabilidade.

Se a guarda institucional for atribuída a uma unidade organizacional, e não a uma pessoa individual, o domínio deverá representar explicitamente essa unidade ou seu responsável designado. Não se deve preencher um usuário fictício apenas para satisfazer uma FK legada.

A regra exata — pessoa recebedora, equipe ou unidade organizacional — depende de validação do procedimento de recebimento e da estrutura real de custódia. Até essa confirmação, a proposta não autoriza alterar o significado de `to_custodian_id`.

### 5.3 Um evento por objeto

Cada objeto de custódia deve possuir seu próprio evento inicial, pois cada objeto pode ter localização, lacre, condição, responsável ou trajetória diferentes. Não criar evento inicial para item `NOT_PRESENTED`, nem para material que não tenha originado objeto de custódia.

## 6. Mapeamento lógico para o modelo legado

O mapeamento abaixo é conceitual e não constitui autorização para migração.

| Conceito API | Campo legado/candidato | Tratamento proposto |
|---|---|---|
| `occurred_at` | `ChainOfCustody.transferred_at` | Reutilizar como instante efetivo, se a inspeção confirmar que não há consumidores com semântica incompatível. Considerar renome lógico apenas na API, sem renome físico obrigatório. |
| `recorded_at` | `created_at`, se existente e com semântica adequada | Reutilizar somente após confirmação do schema, default, timezone e imutabilidade. Caso contrário, avaliar coluna aditiva. |
| `event_type` | Nova coluna candidata | Adicionar de forma aditiva para eventos novos, após aprovação do catálogo; registros legados permanecem sem classificação inferida. |
| `recorded_by_id` | Nova FK candidata para `User.id` | Registrar explicitamente o usuário autenticado que persistiu o evento; não inferir do custodiante de destino. |
| `from_custodian` | `from_custodian_id` | Preservar semântica atual, inclusive nulos legítimos em evento inicial. |
| `to_custodian` | `to_custodian_id` | Preservar semântica atual; verificar se a entidade de custódia pode ser pessoa ou unidade organizacional. |
| `location_from` | `location_from` | Texto histórico; não é FK de localização no schema conhecido. |
| `location_to` | `location_to` | Texto histórico; não é FK de localização no schema conhecido. |
| `reason` | `reason` | Preservar; avaliar catálogo/estrutura adicional sem eliminar texto descritivo. |
| `signature_id` | `signature_id` | Manter nullable enquanto API05/EST07 estiverem pendentes. |
| `notes` | `notes` | Complemento textual; não substitui evidência estruturada nem condição de recebimento. |

### 6.1 Compatibilidade de alvos

Preservar a proposta de uma única tabela `ChainOfCustody`, com exatamente um alvo:

- evento legado: `device_sample_id` preenchido e `custody_object_id` nulo;
- evento do novo fluxo: `custody_object_id` preenchido e `device_sample_id` nulo.

A regra XOR exige CHECK e FKs explícitas. Eventos do novo fluxo continuam ligados ao objeto mesmo depois da criação de `DeviceSample`. Não copiar eventos para ambos os alvos e não associar amostras legadas a objetos sem evidência.

## 7. Autoria e segregação dos papéis

| Papel | Origem do dado | Pode ser informado livremente pelo cliente? |
|---|---|---|
| Usuário que registra (`recorded_by`) | Identidade autenticada e autorização no backend | Não. |
| Recebedor físico | Informação confirmada no ato da chegada | Não em operação sem validação; deve ser selecionado/confirmado conforme permissão e evidência. |
| Custodiante que entrega | Estado de custódia imediatamente anterior, validado no servidor | Não como valor arbitrário. |
| Custodiante que recebe | Pessoa/unidade que efetivamente assume a guarda, confirmada na operação | Não sem validação de identidade/permissão. |
| Usuário que confere/valida/aceita | Identidade autenticada do ator da respectiva operação | Não. |

A aplicação deve registrar separadamente quem praticou o ato e quem o lançou no sistema quando forem pessoas diferentes. O campo de autor não pode ser derivado automaticamente de `to_custodian_id`.

A política de segregação — por exemplo, quando recebedor, conferente, validador e aprovador precisam ser pessoas distintas — permanece dependente de API10, DEC09 e EST10.

## 8. Integridade temporal e registros tardios

### 8.1 Regra padrão proposta

- `recorded_at` deve ser gerado no servidor/banco no momento da persistência e não pode ser retrodatado pelo cliente.
- Para eventos ordinários realizados no momento da operação, `occurred_at` deve ser gerado pelo servidor ou validado contra a hora operacional autorizada.
- Para o evento inicial `RECEIPT`, `occurred_at` deve corresponder a `Receipt.arrived_at`, preservando o instante da chegada física.
- O instante efetivo e o instante de registro devem permanecer consultáveis e distintos.
- Não sobrescrever `occurred_at` para fazê-lo coincidir com `recorded_at` quando houver lançamento posterior.

### 8.2 Lançamento tardio

Quando um fato for lançado depois de sua ocorrência:

- preservar o instante efetivo declarado e a hora de registro real;
- exigir justificativa e identificação do responsável;
- registrar a evidência que sustenta a data efetiva, quando aplicável;
- sinalizar que se trata de lançamento tardio;
- aplicar a política de autorização e limites que vier a ser aprovada em API12/EST08.

Não definir nesta proposta uma janela máxima de retroatividade nem permitir que o cliente envie livremente datas passadas. Esses parâmetros são decisão institucional pendente.

### 8.3 Fuso horário

A API deverá transportar timestamps ISO 8601 com offset explícito. A persistência deverá representar o instante de forma inequívoca, preferencialmente normalizado em UTC, e a apresentação deverá usar o fuso institucional configurado.

A normalização para UTC não preserva necessariamente o offset original informado. Se a instituição precisar conservar também o offset/fuso de origem, essa exigência deverá ser especificada em API12 antes do desenho físico final.

Não usar timestamps sem timezone em contratos novos.

## 9. Proposta para o contrato HTTP

Os schemas futuros de evento devem expor, conceitualmente:

- `event_id`;
- `event_type`;
- `occurred_at`;
- `recorded_at`;
- `recorded_by`;
- `from_custodian` e `to_custodian`, quando aplicáveis;
- `location_from` e `location_to`, quando aplicáveis;
- `reason`;
- `signature_id`, conforme API05;
- referência a evidência, se aplicável;
- origem do registro (`NEW_FLOW` ou `LEGACY`) apenas quando a distinção for confiável.

Para operações de escrita, o backend deve obter `recorded_by` da sessão. Não aceitar `recorded_at` fornecido pelo cliente. `occurred_at` só pode ser fornecido/ajustado conforme a operação e a política API12; no recebimento, o evento inicial deriva de `Receipt.arrived_at`.

Os nomes finais, obrigatoriedade por tipo de evento, status HTTP e schemas de erro devem ser consolidados depois da validação da proposta e das decisões API05, API06, API10 e API12.

## 10. Impactos e riscos

| Tema | Impacto/riscos | Mitigação proposta |
|---|---|---|
| Campo `transferred_at` | Nome físico sugere transferência, mas o evento inicial também pode ser chegada. | Manter nome físico inicialmente e mapear como `occurred_at` na API, se compatível. |
| `created_at` | Pode não existir ou ter semântica diferente. | Inspecionar modelo/migrações e consumidores antes de mapear. |
| `event_type` | Ausência impede interpretação uniforme do histórico. | Coluna aditiva para eventos novos; não classificar legados por inferência. |
| `recorded_by_id` | Ausência explícita impede distinguir ator registrador de custodiante. | FK explícita ou vínculo auditável formalmente especificado. |
| Custodiante inicial | Pode ser pessoa, equipe ou unidade. | Validar procedimento e modelar identidade real, sem usuário fictício. |
| Lançamento tardio | Pode alterar a cronologia aparente. | Manter occurred_at e recorded_at separados, justificativa e trilha de auditoria. |
| Fuso horário | Offset pode se perder após normalização. | Definir política API12 e persistir dados adicionais se exigido. |
| Histórico legado | Dados antigos podem não ter tipo/autoria equivalentes. | Preservar valores originais e representar ausência como desconhecida/nula. |
| Correções | UPDATE/DELETE silencioso destrói rastreabilidade. | Evento compensatório/retificação append-only, sujeito a EST08. |

## 11. Questões pendentes de validação

| ID | Questão | Recomendação | Responsável |
|---|---|---|---|
| COMP02.1 | Qual é o catálogo institucional definitivo de eventos? | Validar códigos e cenários com recebimento, laboratório e coordenação. | Responsável funcional e técnico/laboratorial. |
| COMP02.2 | Custodiante inicial é o recebedor físico, equipe ou unidade organizacional? | Usar o recebedor físico como referência inicial somente se o procedimento confirmar essa atribuição de guarda. | Responsável pelo recebimento e gestão institucional. |
| COMP02.3 | Mudança de localização sem troca de custodiante é evento autônomo? | Sim, modelar como LOCATION_CHANGE se houver necessidade de rastreio histórico. | Responsável técnico e funcional. |
| COMP02.4 | Devolução, descarte e encerramento são eventos distintos? | Separar semânticas e exigir autoridade/evidência apropriada. | Gestão institucional e responsável técnico. |
| COMP02.5 | Retificação será evento compensatório ou entidade de correção vinculada? | Não editar eventos originais; definir mecanismo em conjunto com EST08. | Auditoria, segurança e arquitetura. |
| COMP03.1 | `created_at` atual pode representar `recorded_at`? | Confirmar modelo, migrações, default e consumidores. | Arquitetura/backend. |
| COMP03.2 | `transferred_at` pode representar `occurred_at` para todos os tipos de evento? | Confirmar semântica e compatibilidade dos consumidores; se não, avaliar coluna nova. | Arquitetura/backend. |
| COMP03.3 | `recorded_by_id` será coluna FK ou relação auditável? | Preferir FK explícita na linha do evento, mantendo AuditLog como trilha complementar. | Arquitetura, segurança e auditoria. |
| COMP03.4 | Como representar custodiante organizacional? | Avaliar entidade de unidade/equipe ou modelo de custodiante polimórfico controlado; não usar texto livre como identidade primária. | Arquitetura e gestão institucional. |
| API12.1 | Qual janela e autoridade permitem lançamento tardio/retroativo? | Definir em política institucional; esta proposta não fixa limite. | Autoridade institucional e responsável funcional. |
| API05.1 | Quais tipos de evento exigem assinatura? | Matriz operação × assinatura, sem presumir assinatura universal. | Autoridade institucional e segurança. |

## 12. Critérios para considerar API04 resolvida

API04 somente poderá ser marcada como aprovada quando:

1. catálogo de eventos e seus significados forem validados pelos responsáveis do processo;
2. regra do custodiante inicial estiver confirmada no procedimento de recebimento;
3. diferença entre autor do registro e custodiante estiver aprovada;
4. mapeamento de `occurred_at` e `recorded_at` estiver confirmado contra modelos, migrações e consumidores reais;
5. campos `event_type` e `recorded_by_id` tiverem solução aprovada, sem backfill inferido;
6. política de lançamento tardio/fuso estiver coordenada com API12;
7. retificação estiver coordenada com EST08 e preservar append-only;
8. assinatura por evento estiver coordenada com API05/EST07;
9. contratos HTTP e modelo relacional forem revisados em conjunto.

## 13. Controle de execução

**Realizado:** elaboração desta proposta documental de catálogo de eventos, autoria e semântica temporal, baseada em DEC04, COMP02/COMP03 e nos achados REV03/REV10.

**Não realizado:** alteração da especificação de API existente, OpenAPI, modelo relacional, matriz DEC, código, modelos ORM, banco, migrações, endpoints, frontend, testes, build ou CI.

**Estado:** o responsável pelo projeto validou em revisão (2026-11-10) o catálogo proposto de sete tipos de eventos (`RECEIPT`, `TRANSFER`, `LOCATION_CHANGE`, `RETURN`, `DISPOSITION`, `CLOSURE` e `CORRECTION`) e a distinção conceitual entre `occurred_at`, `recorded_at` e `recorded_by`. Permanecem pendentes a confirmação do custodiante inicial, a validação dos procedimentos e autoridades para devolução/destinação/encerramento, a solução técnica de compatibilidade dos campos e consumidores, a representação de custodiantes organizacionais, as políticas API12 de lançamento tardio/fuso, API05 de assinatura e EST08 de retificação. A validação registrada é de revisão do projeto, não aprovação institucional, não resolve integralmente API04 e não autoriza implementação.

## 14. Histórico de alterações

| Versão | Data | Alteração |
|---|---|---|
| 0.1 | 2026-11-09 | Criação da proposta de catálogo de eventos, autoria, instante efetivo, instante de registro e compatibilidade com a cadeia legada. |
| 0.2 | 2026-11-10 | Registro da validação do catálogo de sete eventos e da distinção entre ocorrência, registro e autoria pelo responsável pelo projeto em revisão; detalhes operacionais, compatibilidade técnica e aprovação institucional permanecem pendentes. |
