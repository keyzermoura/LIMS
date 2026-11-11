# Especificação Detalhada dos Processos Críticos de Recebimento — LIMS-SEFI

**Identificador:** EDP-REC-SEFI-001  
**Versão:** 0.1 — primeira decomposição documental  
**Data:** 2026-11-11  
**Branch:** `docs/integracao-especificacao-sefi`  
**Fontes normativas/decisórias:** D01–D20 (DEC-SEFI-001 v1.7); M0.2 v0.7; EST-REC-001 v1.7; SIM-SEFI-REC-001 v1.2.  
**Fontes integradoras:** BCDP-LIMS-SEFI-001 v0.1; PROC-MAP-SEFI-001 v0.2; RF-001–RF-020; MAT-HARM-EST-SEFI-001 v0.1; matriz D01–D20; matriz G0-P01–P30; plano CA01–CA37.  
**Natureza:** especificação funcional derivada para revisão; não é procedimento operacional aprovado, desenho físico, homologação ou autorização de implementação.

## 1. Objetivo e limites

Detalhar, em sequência ponta a ponta, os processos críticos desde a solicitação até a criação da AmostraOperacional ou formalização da recusa/destinação. O documento transforma o mapa PROC-01–PROC-09 em fluxos verificáveis, preservando as decisões ratificadas e explicitando lacunas que dependem de validação institucional.

Este documento:
- não altera D01–D20, G0-P01–P30, M0.2, EST-REC-001 ou SIM-SEFI-REC-001;
- não transforma M0.3 ou qualquer proposta integradora em regra aprovada;
- não escolhe prazos, canais, formulários, critérios técnicos por categoria, alçadas nominais, modalidade de assinatura ou unidades de medida ainda não definidos;
- não especifica tabelas, endpoints, telas, tecnologia, infraestrutura ou migrações;
- não declara CA ou SIM executados;
- não autoriza implementação nem altera o Gate G0.

## 2. Regras gerais de leitura

1. **Fato não é estado:** chegada, apresentação, comunicação, decisão e transferência são fatos/eventos; estados são condições resultantes.
2. **Chegada não é aceite:** registrar a chegada física não conclui conferência, decisão nem admissão.
3. **Ausência não é recusa:** item não apresentado permanece representado no recebimento, sem objeto de custódia ou amostra.
4. **Menor granularidade decisória:** decidir no nível mais específico em que os desfechos possam divergir.
5. **Custódia antecede aceite:** o material apresentado fica sob custódia antes da decisão técnica.
6. **Evidência não regulariza sozinha:** a juntada de documento/resposta exige reavaliação.
7. **Vencimento não recusa:** prazo vencido não produz recusa ou encerramento automático.
8. **Validação independente:** quando exigida, o autor/executor não valida a própria decisão.
9. **D20 é barreira:** AmostraOperacional só nasce após aceite formal e todos os bloqueios/validações obrigatórios.
10. **Rastreabilidade temporal:** instante efetivo do fato e instante do registro são preservados separadamente.
11. **Histórico não é sobrescrito:** retificação é novo ato relacionado ao original.
12. **Sem presunção de identidade/autoridade:** papel de sistema, permissão técnica e competência institucional são controles distintos.

## 3. Papéis funcionais

Os nomes abaixo representam papéis de processo, não designações de servidores. A acumulação de papéis é permitida somente conforme D10 e matriz de permissões EST-REC-001; validação independente é obrigatória nos casos aplicáveis.

| Papel funcional | Responsabilidade no fluxo | Limite |
|---|---|---|
| Solicitante | Fornecer dados da demanda e itens declarados; responder a comunicações e regularizar pendências. | Identidade externa, autenticação e vínculo institucional seguem G0-P21. |
| Cadastrador autorizado | Registrar solicitação em nome do solicitante quando o fluxo admitir. | Deve identificar o solicitante real e o autor do registro. |
| Recepção/recebedor físico | Registrar a chegada e a apresentação observada. | Não presume conformidade técnica nem aceite. |
| Conferente | Executar checklist e registrar respostas/evidências. | Deve possuir permissão e competência aplicáveis. |
| Autor/decisor habilitado | Formalizar proposta/decisão no nível permitido. | Não pode ultrapassar critérios E nem alçadas institucionais. |
| Coordenação/validador independente | Validar, devolver ou rejeitar nos casos exigidos. | Não pode validar a própria decisão quando a independência for obrigatória. |
| Custodiante | Responder pela guarda física do objeto sob sua responsabilidade. | Permanece responsável até confirmação de transferência ou destinação efetiva. |
| Sistema | Validar precondições, gerar identificadores, manter vínculos e registrar eventos/auditoria. | Não substitui decisão técnica ou designação institucional. |

## 4. Fluxo ponta a ponta e portas de controle

| Porta | Processo | Condição para avançar | Se não atendida |
|---|---|---|---|
| P0 | PROC-01 Solicitação | Solicitação válida e submetida; solicitante e itens identificados. | Permanecer em rascunho ou rejeitar submissão inválida, preservando motivo. |
| P1 | PROC-02 Chegada | Fato físico registrado com autor, recebedor e horários. | Não iniciar conferência/aceite; permitir completar registro conforme regra sem inventar dados. |
| P2 | PROC-03 Apresentação | Todos os itens declarados representados; quantidades/unidades reconciliáveis. | Registrar não apresentação/divergência; não criar objeto para material ausente. |
| P3 | PROC-04 Custódia | Material apresentado individualizado/agrupado justificadamente, com custodiante e localização. | Não criar objeto/custódia sem material apresentado e responsável/local inicial. |
| P4 | PROC-05 Conferência | Checklist publicado, aplicável e versionado; respostas obrigatórias e evidências. | Não concluir conferência com critério obrigatório sem resposta/evidência. |
| P5 | PROC-06 Pendência | Pendência caracterizada, comunicada e com prazo conforme regra institucional. | Não iniciar prazo sem comunicação formal comprovável. |
| P6 | PROC-07 Decisão | Conferência concluída; critérios impeditivos e pendências impeditivas tratados; decisor habilitado. | Manter pendência/bloqueio; não emitir aceite/recusa sem fundamento e autoridade. |
| P7 | PROC-08 Validação | Validação exigida concluída por pessoa independente e habilitada. | Decisão não alcança estado final necessário à admissão. |
| P8 | PROC-09 Admissão | Aceite formal válido, controles D20 satisfeitos e ausência de amostra anterior para o objeto. | Bloquear criação; manter objeto e histórico sob custódia. |

## 5. Especificação dos processos

### PROC-01 — Registrar e submeter solicitação

**Objetivo:** formalizar a demanda administrativa e identificar cada ItemDeclarado antes da chegada física.

**Gatilho:** necessidade de encaminhar material ao SEFI para avaliação/ensaios.

**Entradas mínimas documentadas:** identificação do solicitante; dados da demanda; descrição de um ou mais itens; quantidades e unidades declaradas; informações obrigatórias definidas no formulário institucional. A lista final de campos e validações deve ser conferida com D02/EST-REC-001 e com o formulário vigente; este documento não inventa campos adicionais.

**Fluxo principal:**
1. O solicitante ou cadastrador autorizado inicia uma solicitação.
2. O autor do registro e o solicitante em nome de quem a demanda é registrada ficam distinguíveis.
3. O sistema valida presença dos campos obrigatórios e a existência de ao menos um ItemDeclarado.
4. Cada item declarado recebe identidade própria dentro da solicitação e preserva descrição, quantidade e unidade originais.
5. A solicitação permanece RASCUNHO enquanto não submetida.
6. Após validação, o ator autorizado submete a solicitação.
7. O sistema registra autor, instante do fato quando aplicável, instante de submissão, estado e evento de auditoria.
8. A solicitação submetida torna-se referência para o recebimento principal.

**Saídas:** Solicitação SUBMETIDA; um ou mais ItemDeclarado; identificador institucional conforme D18; evento SOLICITACAO_CRIADA e SOLICITACAO_SUBMETIDA, sem confundir criação com submissão.

**Bloqueios e exceções:**
- Não submeter solicitação sem solicitante identificável ou sem ItemDeclarado.
- Não inferir identidade externa nem criar conta externa automaticamente; G0-P21 permanece dependência.
- Não alterar quantidade/unidade declaradas para fazê-las coincidir com material recebido.
- Cancelamento, edição após submissão e retificação seguem regras próprias e não são detalhados aqui sem fonte suficiente.

**Evidências/auditoria:** autor, solicitante, dados submetidos, identificador, instante, versão dos dados e eventos de criação/submissão; dados pessoais/documentos seguem controle de acesso e retenção ainda sujeitos a G0-P30.

**Rastreabilidade:** D02, D14, D15, D18; RF-002, RF-014, RF-015, RF-018; PROC-01; CA25, CA37; SIM01–SIM12 apenas como contexto de cenário, não como execução deste processo.

**Questões pendentes:** identidade/autenticação externa (G0-P21); formulário e campos finais; regra de edição/cancelamento; protocolo/QR e padrão de identificador (G0-P07); migração/legado (G0-P22).

### PROC-02 — Registrar chegada física principal

**Objetivo:** registrar o fato da chegada física no SEFI, inclusive quando existirem divergências ou documentação incompleta.

**Gatilho:** apresentação física de volumes/material vinculados a uma solicitação submetida.

**Pré-condições:** solicitação submetida; recebedor/autor do registro identificado; acesso de recepção autorizado. A identificação do entregador pode estar disponível ou ausente, e a ausência deve ser registrada como tal, sem inferência.

**Fluxo principal:**
1. O recebedor localiza a solicitação submetida.
2. Confirma que o material apresentado se refere à solicitação, registrando divergências observáveis sem corrigi-las silenciosamente.
3. Registra o instante efetivo da chegada, distinto do timestamp automático de registro.
4. Identifica o recebedor físico e o autor do registro; registra entregador quando disponível ou sua ausência.
5. Registra volumes, descrição externa, condição da embalagem, observações/avarias e documentos apresentados, conforme campos de D02.
6. Anexa fotografias quando pertinentes e permitidas pelo procedimento.
7. O sistema cria o Recebimento principal, respeitando a cardinalidade Solicitação 1:0..1 Recebimento.
8. O sistema registra CHEGADA_REGISTRADA e a transição correspondente, sem iniciar aceite ou criar AmostraOperacional.
9. O material efetivamente apresentado permanece sob custódia desde a chegada, com individualização no PROC-04.

**Saídas:** Recebimento REGISTRADO; evento CHEGADA_REGISTRADA; metadados da chegada e vínculos à solicitação.

**Bloqueios e exceções:**
- Não criar segundo recebimento principal para a mesma solicitação; chegada complementar é tratada no PROC-14 conforme D19.
- Divergência documental ou de quantidade não impede o registro do fato físico, mas deve ficar explícita.
- Não preencher entregador, horário ou condição por suposição.
- Não converter o registro de chegada em conferência concluída, aceite, recusa ou criação de amostra.
- Se a solicitação não puder ser identificada, o tratamento provisório não está definido nas fontes recuperadas e exige regra institucional; não criar vínculo presumido.

**Evidências/auditoria:** dados de chegada, recebedor, autor, entregador ou ausência, horários efetivo/registro, volumes, condição externa, documentos/fotos, divergências e autoria de cada alteração.

**Rastreabilidade:** D01, D02, D13, D14, D18; RF-001, RF-002, RF-013, RF-014, RF-018; PROC-02; CA01, CA02, CA28; SIM01–SIM03.

**Questões pendentes:** campos obrigatórios finais; regras de horário institucional; permissão RECEPÇÃO e acumulação de funções; anexos e retenção (G0-P09/P24/P30).

### PROC-03 — Registrar apresentação por item e quantidades

**Objetivo:** reconciliar o que foi declarado com o que efetivamente foi apresentado, preservando itens não apresentados e apresentações parciais sem retroatividade.

**Gatilho:** conferência física inicial da chegada, por item declarado.

**Pré-condições:** Recebimento principal registrado; cada ItemDeclarado possui representação ItemRecebimento; observação física disponível.

**Fluxo principal:**
1. O recebedor percorre todos os ItemRecebimento vinculados ao recebimento.
2. Para cada item, registra se houve apresentação, não apresentação ou apresentação em quantidade diferente da declarada.
3. Registra quantidade apresentada e unidade observada sem sobrescrever quantidade/unidade declaradas.
4. Registra instante efetivo da apresentação e instante do registro.
5. Registra justificativa/evidência para divergência quantitativa ou de identificação.
6. Item não apresentado permanece no recebimento com situação NAO_APRESENTADO; não gera ObjetoCustodia, EventoCustodia ou AmostraOperacional.
7. Item apresentado fica apto à individualização no PROC-04.
8. A apresentação posterior é novo fato, nunca edição retroativa do evento original; a estrutura para isso segue D19 e PROC-14.
9. O sistema permite reconciliação entre declarada, apresentada, representada sob custódia, aceita, recusada e não apresentada, sem somar unidades incompatíveis.

**Saídas:** estado de apresentação por ItemRecebimento; quantidades e unidades observadas; divergências justificadas; eventos ITEM_APRESENTADO ou ITEM_NAO_APRESENTADO.

**Bloqueios e exceções:**
- Não criar objeto para item não apresentado.
- Não tratar ausência como recusa.
- Não equiparar quantidade a número de objetos.
- Não converter unidades ou arredondar sem regra aprovada.
- Não persistir APRESENTACAO_PARCIAL como estado canônico até resolver HARM-01/M03-01/M03-03; a condição parcial deve ser demonstrável pelas quantidades e ocorrências registradas.
- Se múltiplas apresentações ocorrerem, registrar cada novo fato; a forma de entidade/evento e a linhagem permanecem pendentes.

**Evidências/auditoria:** quantidades declarada/apresentada, unidade, instante efetivo/registro, autor, justificativa, documentos/fotos, ocorrências e histórico de reconciliação.

**Rastreabilidade:** D02, D03, D13, D14, D18, D19; RF-002, RF-003, RF-013, RF-014, RF-018, RF-019; PROC-03; CA07, CA08, CA23, CA26, CA28, CA36; SIM02, SIM03, SIM12.

**Questões pendentes:** M03-01 a M03-03; HARM-01, HARM-04, HARM-05; unidades e conversões; regra de reabertura/nova solicitação em chegada complementar.

### PROC-04 — Individualizar material e iniciar custódia

**Objetivo:** representar o material efetivamente apresentado por um ou mais ObjetosCustodia e estabelecer a guarda inicial rastreável.

**Gatilho:** ItemRecebimento com material apresentado.

**Pré-condições:** apresentação registrada; quantidade/unidade observadas; possibilidade de identificar o material; custodiante e localização inicial definidos.

**Fluxo principal:**
1. O responsável avalia a granularidade necessária para preservar rastreabilidade, avaliação, decisão e destinação.
2. Individualiza o material em um ou mais ObjetosCustodia.
3. Quando houver agrupamento, registra justificativa de homogeneidade e demonstra que os materiais compartilham guarda, avaliação, decisão, rastreabilidade e destinação.
4. Não agrupa materiais cujos resultados possam divergir.
5. Registra quantidade/unidade representada por cada objeto e vínculo ao ItemRecebimento.
6. Atribui identificador de objeto distinto dos identificadores de solicitação, recebimento, item e amostra.
7. Registra custodiante inicial, localização inicial e instante efetivo de início da custódia.
8. Registra OBJETO_CUSTODIA_CRIADO e CUSTODIA_INICIADA.
9. Mantém o objeto sob custódia mesmo quando sua decisão futura for pendente ou recusada.

**Saídas:** um ou mais ObjetosCustodia vinculados ao ItemRecebimento; custódia SOB_GUARDA; custodiante/localização inicial; eventos de criação e início.

**Bloqueios e exceções:**
- Material não apresentado não gera objeto.
- Não criar objeto vazio para satisfazer cardinalidade.
- Não agrupar sem justificativa; não fracionar sem preservar origem, quantidades e linhagem.
- Não presumir que ObjetoCustodia equivale sempre a unidade física, embalagem, amostra ou produto individual.
- O objeto deve permanecer rastreável ao ItemRecebimento; a origem em uma ocorrência específica de apresentação e a possibilidade de agregar múltiplas ocorrências dependem de M03-01/M03-02/M03-03.
- Não iniciar custódia sem custodiante e localização inicial identificados.

**Evidências/auditoria:** critério de individualização/agrupamento, quantidades/unidades, origem, identificador, custodiante, localização, instante e autor.

**Rastreabilidade:** D03, D04, D07, D08, D13, D14, D18; RF-003, RF-004, RF-007, RF-008, RF-013, RF-014, RF-018; PROC-04; CA07, CA09, CA18, CA27; SIM01–SIM04, SIM06.

**Questões pendentes:** M03-02/M03-03 (agrupamento/fracionamento); M03-15 (modelo físico); G0-P26 (amostragem/agrupamento); catálogo de localizações G0-P08.

### PROC-05 — Executar conferência técnica/administrativa

**Objetivo:** avaliar os critérios aplicáveis ao material apresentado, com checklist publicado, versionado e evidências rastreáveis.

**Gatilho:** ObjetoCustodia sob guarda e ItemRecebimento apresentado, aptos à conferência.

**Pré-condições:** conferente autorizado; checklist publicado e aplicável à categoria; versão vigente identificada; versão aplicada fixada para aquele recebimento; critérios e classes E/S/I aprovados.

**Fluxo principal:**
1. O conferente inicia a conferência para o item/objeto aplicável.
2. O sistema registra conferente, instante e versão do checklist.
3. Para cada critério aplicável, o conferente registra CONFORME, NAO_CONFORME ou NAO_APLICAVEL, conforme regra aprovada.
4. Critérios não aplicáveis recebem justificativa quando exigida pela versão do checklist.
5. Para não conformidades, registra descrição objetiva, critério relacionado e evidência.
6. Critério classificado como E, S ou I conserva a classe da versão publicada; o operador não pode alterar sua classificação durante a execução.
7. Respostas e evidências são vinculadas ao objeto/item correspondente.
8. A conferência somente é concluída quando todos os critérios obrigatórios aplicáveis estiverem respondidos e as evidências exigidas estiverem presentes.
9. O sistema registra CONFERENCIA_CONCLUIDA com autor e instante; a conclusão não decide automaticamente aceite ou recusa.

**Saídas:** conferência concluída ou em andamento; respostas por critério; não conformidades; evidências; evento de auditoria.

**Bloqueios e exceções:**
- Não iniciar conferência sem material apresentado e sob custódia.
- Não aplicar checklist em rascunho, não publicado ou cuja aplicabilidade não esteja definida.
- Não alterar retroativamente a versão do checklist aplicada.
- Não permitir que operador altere classe E/S/I.
- Não concluir com critério obrigatório sem resposta/evidência.
- Não converter automaticamente qualquer não conformidade em recusa; aplicar classificação e regras de pendência/decisão.

**Evidências/auditoria:** versão do checklist, critérios, respostas, justificativas, classe E/S/I, conferente, horários, anexos, retificações e trilha de eventos.

**Rastreabilidade:** D01, D10, D11, D12, D13, D14; RF-001, RF-010, RF-011, RF-012, RF-013, RF-014; PROC-05; CA02–CA06, CA24; SIM01–SIM06.

**Questões pendentes:** conteúdo dos checklists por categoria; critérios E/S/I; aprovação e governança (G0-P02/P17); matriz nominal de competência (G0-P01/P16); critérios de evidência e retenção.

### PROC-06 — Abrir, comunicar e tratar pendência

**Objetivo:** registrar uma condição saneável e conduzir sua regularização por comunicação formal, prazo e reavaliação.

**Gatilho:** resultado de conferência ou outra condição que, conforme regra aprovada, admita regularização em vez de aceite imediato ou recusa.

**Pré-condições:** condição identificada; descrição e vínculo ao ItemRecebimento/ObjetoCustodia; responsável pela comunicação; prazo e canal conforme tabela/procedimento institucional.

**Fluxo principal:**
1. O conferente registra a não conformidade e identifica se é saneável, conforme classificação aprovada.
2. Abre Pendencia no nível apropriado (item ou objeto), descrevendo o requisito, providência esperada e evidências aceitáveis conforme checklist/procedimento.
3. Define responsável, prazo aplicável e canal oficial; não inventa prazo ad hoc.
4. Emite comunicação formal ao solicitante.
5. Registra conteúdo, destinatário, canal, instante de envio e evidência de entrega/ciência conforme política.
6. O prazo começa somente com a comunicação formal comprovável.
7. O solicitante apresenta regularização; o sistema registra recebimento e vincula evidências sem encerrar a pendência.
8. A pendência passa a AGUARDANDO_REAVALIACAO.
9. Conferente/avaliador habilitado reavalia a evidência.
10. Somente resultado favorável registra PENDENCIA_REGULARIZADA.
11. Se o prazo expirar, registrar PRAZO_VENCIDO como condição temporal; não recusar nem encerrar automaticamente.
12. Prorrogação exige justificativa e autorização conforme alçada ainda pendente.

**Saídas:** pendência aberta/comunicada; prazo rastreável; regularização recebida; reavaliação; pendência regularizada ou ainda aberta/vencida.

**Bloqueios e exceções:**
- Não iniciar prazo sem comunicação formal comprovável.
- Não tratar juntada de evidência como regularização automática.
- Não permitir prorrogação sem justificativa/autorização.
- Não transformar prazo vencido em recusa automática.
- Não permitir que a pendência desapareça por alteração de estado agregado.
- Se a condição não for saneável, seguir processo de decisão/recusa com fundamento, sem classificar artificialmente como pendência.

**Evidências/auditoria:** condição, critério, classificação, comunicação, destinatário, canal, datas, prazo, prorrogações, anexos, avaliador e resultado da reavaliação.

**Rastreabilidade:** D05, D11, D13, D14, D16; RF-005, RF-011, RF-013, RF-014, RF-016; PROC-06; CA05, CA12, CA13, CA26; SIM05.

**Questões pendentes:** prazos e canais oficiais (G0-P03/P18); regras de alerta; alçadas de prorrogação; designação de avaliadores; modelos de comunicação.

### PROC-07 — Formalizar decisão de aceite, pendência ou recusa

**Objetivo:** registrar o resultado formal da avaliação no menor nível em que os desfechos possam divergir.

**Gatilho:** conferência concluída, com critérios e pendências analisados.

**Pré-condições:** checklist aplicável concluído; respostas e evidências preservadas; critérios impeditivos tratados; pendências impeditivas resolvidas ou com resultado formal cabível; decisor habilitado; validação subsequente identificada quando exigida.

**Fluxo principal:**
1. O decisor revisa o conjunto de respostas, evidências e pendências.
2. Determina a granularidade da decisão: ObjetoCustodia quando objetos do mesmo ItemRecebimento puderem ter desfechos distintos; ItemRecebimento somente quando o resultado for único e indivisível.
3. Registra resultado ACEITA, RECUSADA ou PENDENTE conforme regras EST-REC-001 e D05/D06.
4. Para aceite, registra fundamento e vínculo aos critérios/evidências favoráveis.
5. Para recusa, registra motivo, critério não atendido quando aplicável, justificativa técnica, evidências e destino/encaminhamento pendente.
6. Para pendência, vincula a Pendencia e não a trata como decisão final de aceite/recusa.
7. Registra autor, competência utilizada, instante, versão do checklist e evento de decisão.
8. Encaminha para validação de coordenação quando exigida.
9. A recusa não encerra custódia; o objeto permanece sob guarda até devolução/destinação efetiva.
10. O aceite não cria automaticamente AmostraOperacional; a admissão ocorre apenas no PROC-09 após controles D20.

**Saídas:** resultado decisório formal no nível aplicável; evento de decisão; encaminhamento para validação independente ou admissão/destinação.

**Bloqueios e exceções:**
- Não decidir antes de concluir conferência e tratar bloqueios aplicáveis.
- Não permitir aceite com critério E não atendido.
- Não permitir que coordenação dispense critério eliminatório.
- Não converter prazo vencido em recusa.
- Não confundir decisão com estado de custódia ou localização.
- Não encerrar custódia por recusa.
- O workflow intermediário ACEITE_PROPOSTO/ACEITE_VALIDADO/RECUSA_PROPOSTA/SUBSTITUIDA de M0.3 não é aqui declarado enum aprovado; ver HARM-02.

**Evidências/auditoria:** resultado, fundamento, critério, checklist/versionamento, autor, competência, data/hora, evidências, pendências relacionadas, assinatura/validação quando exigidas.

**Rastreabilidade:** D04, D05, D06, D09, D10, D11, D12, D13, D14, D16; RF-004, RF-005, RF-006, RF-009, RF-010, RF-011, RF-012, RF-013, RF-014, RF-016; PROC-07; CA04–CA06, CA14–CA18; SIM01–SIM06.

**Questões pendentes:** harmonização de estado e workflow decisório (HARM-02); critérios técnicos por categoria; nível exato de decisão para casos mistos; alçadas/competências nominais; procedimentos de devolução/destinação (G0-P04/P20).

### PROC-08 — Validar decisão pela coordenação

**Objetivo:** realizar revisão independente da decisão nos casos em que D10/EST-REC-001 a exigem.

**Gatilho:** decisão que requer validação de coordenação.

**Pré-condições:** decisão e evidências completas; validador com competência/designação vigente; identidade do autor/executor conhecida; regra de independência aplicável.

**Fluxo principal:**
1. O sistema identifica que a decisão exige validação.
2. Encaminha para coordenação ou substituto formalmente designado.
3. Verifica que o validador é diferente do autor/executor nos casos em que a independência é obrigatória.
4. O validador revisa decisão, critérios, justificativas, evidências e pendências.
5. Registra resultado APROVADA, DEVOLVIDA ou REJEITADA, com justificativa e instante.
6. Se devolvida, encaminha para correção/reanálise sem apagar a decisão anterior; nova decisão/versão deve permanecer rastreável.
7. Se rejeitada, mantém o material no fluxo correspondente, sem presumir automaticamente a destinação final se a regra aplicável não a definir.
8. Se aprovada, libera apenas a próxima etapa permitida; não substitui a decisão técnica nem cria amostra por si só.
9. Registra assinatura/identificação conforme política institucional aplicável.

**Saídas:** ValidacaoCoordenacao com resultado e justificativa; evento VALIDACAO_COORDENACAO_REGISTRADA; liberação, devolução para revisão ou bloqueio.

**Bloqueios e exceções:**
- Não permitir autoaprovação quando independência for obrigatória.
- Não aceitar validador sem competência/designação vigente.
- Perfil administrador não confere competência técnica.
- A ausência de designação/substituto formal impede concluir a validação obrigatória.
- Devolução/rejeição da validação não se converte automaticamente em recusa do material.
- Não dispensar assinatura/identificação exigida pela política ainda pendente.

**Evidências/auditoria:** autor/executor da decisão, validador, designação/competência, independência, conteúdo revisado, resultado, justificativa, timestamps, assinatura e eventos.

**Rastreabilidade:** D06, D09, D10, D14, D16; RF-006, RF-009, RF-010, RF-014, RF-016; PROC-08; CA03, CA14, CA15, CA17, CA19; SIM01, SIM04–SIM06, SIM09.

**Questões pendentes:** matriz de competências e substitutos (G0-P01/P16); definição de casos obrigatórios; modalidade de assinatura (G0-P05/P19); regras para devolução/rejeição.

### PROC-09 — Admitir objeto e criar AmostraOperacional

**Objetivo:** criar o registro laboratorial somente depois de concluído o aceite formal e satisfeitos todos os bloqueios e validações.

**Gatilho:** objeto com decisão de aceite formal e controles de validação concluídos.

**Pré-condições obrigatórias (barreira D20):**
- decisão ACEITA válida no ObjetoCustodia ou nível decisório aplicável;
- conferência concluída e checklist/versionamento preservados;
- critérios impeditivos atendidos;
- pendências impeditivas regularizadas;
- validação independente aprovada quando exigida;
- evidências e assinatura requeridas presentes;
- ObjetoCustodia identificado e sob custódia rastreável;
- inexistência de AmostraOperacional previamente criada para o mesmo objeto;
- identificadores institucionais aplicáveis disponíveis.

**Fluxo principal:**
1. O sistema verifica todas as pré-condições D20 em uma única operação lógica.
2. O ator autorizado solicita admissão do objeto aceito.
3. O sistema verifica competência/permissão e ausência de bloqueios.
4. O sistema gera identificador institucional/laboratorial conforme D18 e regras institucionais.
5. O sistema cria uma única AmostraOperacional vinculada ao ObjetoCustodia, preservando a relação 1:0..1 aprovada em M0.2.
6. A criação e os eventos/auditoria correspondentes devem ser atômicos: ou a amostra e seus vínculos são integralmente registrados, ou nenhum resultado parcial é confirmado.
7. A operação deve ser idempotente: repetição da mesma solicitação não cria amostra duplicada.
8. O objeto mantém sua cadeia de custódia; a criação da amostra não cria nova chegada nem encerra custódia.
9. O sistema registra AMOSTRA_OPERACIONAL_CRIADA, autor, instante, identificadores e vínculos.
10. O objeto segue para o fluxo laboratorial de ensaios, fora do escopo desta especificação de recebimento.

**Saídas:** AmostraOperacional criada e vinculada ao ObjetoCustodia; identificador institucional; evento e trilha de auditoria; custódia preservada.

**Bloqueios e exceções:**
- Bloquear se qualquer pré-condição D20 falhar.
- Bloquear se houver amostra anterior para o mesmo objeto.
- Não criar amostra para item não apresentado, objeto recusado ou pendência impeditiva aberta.
- Não criar amostra somente porque a conferência foi concluída ou porque houve proposta de aceite.
- Não permitir criação parcial em caso de falha.
- Não redefinir nesta especificação os estados posteriores de amostra/ensaio; M03-16 segue pendente.
- Não converter automaticamente DeviceSample atual em AmostraOperacional sem análise de compatibilidade e migração.

**Evidências/auditoria:** decisão, checklist, validação, pendências, competência, assinatura, objeto, identificadores, autor, timestamps, idempotência e resultado transacional.

**Rastreabilidade:** D18, D20; RF-018, RF-020; PROC-09; CA16–CA18, CA31–CA33; SIM01–SIM06, SIM09, SIM10; G0-P11/P12/P14/P15/P23/P26.

**Questões pendentes:** M03-16; G0-P07 (padrão de protocolo/QR); G0-P14/P15 (integridade, concorrência e E2E); G0-P23 (idempotência/concorrência/versionamento); compatibilidade do domínio laboratorial atual e plano de migração (G0-P22).

## 6. Contratos de dados funcionais mínimos

Esta seção define informação necessária ao processo, não esquema físico ou tipo de coluna.

| Grupo | Dados funcionais mínimos | Aplicação |
|---|---|---|
| Identidade/autoria | ator, papel exercido, solicitante em nome de quem age, competência/permissão aplicável | Todos os processos |
| Temporalidade | instante efetivo do fato, instante de registro, fuso/regra temporal institucional | PROC-01–PROC-09 |
| Origem/vínculo | Solicitação, ItemDeclarado, Recebimento, ItemRecebimento, ObjetoCustodia e referências externas aplicáveis | PROC-01–PROC-09 |
| Quantidade | valor, unidade, natureza (declarada/apresentada/representada/aceita/recusada/não apresentada) | PROC-01, 03, 04, 07 |
| Evidência | tipo, finalidade, autoria/origem, instante, vínculo, versão/integridade e acesso | PROC-02–PROC-09 |
| Decisão | resultado, fundamento, critério, autor, competência, evidência e validação | PROC-05–PROC-09 |
| Custódia | objeto, custodiante, localização, instante de início e eventos posteriores | PROC-04 em diante |
| Identificadores | identificador de solicitação/recebimento/item/objeto/amostra e correlação sem reutilização | PROC-01–PROC-09 |

Os valores de domínio, formatos, obrigatoriedade por categoria, regras de retenção e políticas de acesso precisam ser fechados nos artefatos próprios e não são inventados nesta especificação.

## 7. Requisitos não funcionais e controles transversais aplicáveis

- **Auditoria (D14):** eventos de criação, submissão, chegada, apresentação, custódia, conferência, pendência, decisão, validação e admissão devem ser reconstruíveis e protegidos contra alteração indevida.
- **Acesso (D15):** acesso individual, menor privilégio, segregação de funções e escopo por papel; detalhes de autenticação externa permanecem G0-P21.
- **Assinatura (D16):** aplicar nos atos definidos pela política; modalidade e força probatória permanecem G0-P05/P19.
- **Evidências (D13):** manter vínculo com o fato/critério/decisão, autoria, integridade e preservação do original.
- **Integridade/concorrência:** evitar duplicidade de recebimento principal e de amostra por objeto; regras técnicas detalhadas seguem G0-P14/P23.
- **Privacidade/retenção:** classificação, acesso, exportação e destinação seguem G0-P30; não presumir política.
- **Continuidade:** backup/restauração é PROC-17 e não está coberto integralmente pelos processos de recebimento.

## 8. Rastreabilidade consolidada dos processos

| Processo | Decisões | Requisitos | Critérios preliminares | Simulações relacionadas |
|---|---|---|---|---|
| PROC-01 | D02, D14, D15, D18 | RF-002, RF-014, RF-015, RF-018 | CA25, CA37 | SIM01–SIM12 (contexto; associação não prova execução) |
| PROC-02 | D01, D02, D13, D14, D18 | RF-001, RF-002, RF-013, RF-014, RF-018 | CA01, CA02, CA28 | SIM01–SIM03 |
| PROC-03 | D02, D03, D13, D14, D18, D19 | RF-002, RF-003, RF-013, RF-014, RF-018, RF-019 | CA07, CA08, CA23, CA26, CA28, CA36 | SIM02, SIM03, SIM12 |
| PROC-04 | D03, D04, D07, D08, D13, D14, D18 | RF-003, RF-004, RF-007, RF-008, RF-013, RF-014, RF-018 | CA07, CA09, CA18, CA27 | SIM01–SIM04, SIM06 |
| PROC-05 | D01, D10, D11, D12, D13, D14 | RF-001, RF-010, RF-011, RF-012, RF-013, RF-014 | CA02–CA06, CA24 | SIM01–SIM06 |
| PROC-06 | D05, D11, D13, D14, D16 | RF-005, RF-011, RF-013, RF-014, RF-016 | CA05, CA12, CA13, CA26 | SIM05 |
| PROC-07 | D04, D05, D06, D09, D10, D11, D12, D13, D14, D16 | RF-004, RF-005, RF-006, RF-009, RF-010, RF-011, RF-012, RF-013, RF-014, RF-016 | CA04–CA06, CA14–CA18 | SIM01–SIM06 |
| PROC-08 | D06, D09, D10, D14, D16 | RF-006, RF-009, RF-010, RF-014, RF-016 | CA03, CA14, CA15, CA17, CA19 | SIM01, SIM04–SIM06, SIM09 |
| PROC-09 | D18, D20 | RF-018, RF-020 | CA16–CA18, CA31–CA33 | SIM01–SIM06, SIM09, SIM10 |

A associação de um CA/SIM a um processo significa cobertura documental pretendida. Não significa que o caso esteja executado, que a simulação tenha sido homologada ou que a cobertura seja completa.

## 9. Lacunas e decisões que exigem participação institucional

| ID | Tema | Dependência | Por que não será decidido editorialmente |
|---|---|---|---|
| DEC-01 | Identidade e vínculo do solicitante externo | G0-P21 | Define governança de identidade, representação e responsabilidade. |
| DEC-02 | Campos/formulário e identificadores oficiais | D02/D18; G0-P07 | Exige validação do fluxo e dos padrões institucionais. |
| DEC-03 | Unidades, conversões e tolerâncias | D03; M03-03 | Exige conhecimento técnico por categoria e evita reconciliação incorreta. |
| DEC-04 | Agrupamento/fracionamento e linhagem | D04; G0-P26; M03-02/M03-03 | Afeta identidade, custódia, decisão e amostragem. |
| DEC-05 | Checklists e critérios E/S/I | D11/D12; G0-P02/P17 | Exige aprovação técnica dos critérios aplicáveis. |
| DEC-06 | Competências, alçadas e substitutos | D10; G0-P01/P16 | Exige designação formal de pessoas/autoridades. |
| DEC-07 | Prazos, canais e prorrogações | D05; G0-P03/P18 | Exige procedimento administrativo aprovado. |
| DEC-08 | Assinatura eletrônica | D16; G0-P05/P19 | Exige definição institucional de modalidade e atos abrangidos. |
| DEC-09 | D19 e chegada complementar após encerramento | D19; M03-01; HARM-04 | Exige escolher regra operacional de reabertura ou nova solicitação. |
| DEC-10 | Workflow decisório intermediário | HARM-02 | Exige harmonização entre EST e M0.3, sem confundir decisão e custódia. |
| DEC-11 | Devolução/destinação de recusados | D06; G0-P04/P20; HARM-03 | Exige procedimento, recebedor autorizado, comprovantes e alçadas. |
| DEC-12 | Estados de AmostraOperacional e compatibilidade com ensaios | M03-16 | Exige preservar o ciclo laboratorial e avaliar o legado atual. |

## 10. Critérios de revisão desta especificação

A revisão funcional deve verificar, no mínimo:

1. Cada processo começa com gatilho e pré-condições identificáveis.
2. Cada transição indica ator autorizado e evento rastreável.
3. Nenhum estado agregado apaga fatos/decisões por item ou objeto.
4. Nenhum item não apresentado gera objeto ou amostra.
5. Quantidades e unidades permanecem reconciliáveis sem conversão presumida.
6. Custódia começa antes do aceite e só termina com destinação efetiva comprovada.
7. Checklist é publicado/versionado e suas respostas são preservadas.
8. Pendência tem comunicação comprovável, prazo e reavaliação.
9. Vencimento não causa recusa automática.
10. Decisão é registrada no menor nível em que resultados possam divergir.
11. Validação independente é bloqueada quando obrigatória e não há designação válida.
12. Criação de amostra cumpre D20, é atômica/idempotente e preserva custódia.
13. Eventos efetivos e timestamps de registro não são confundidos.
14. Dúvidas não cobertas pelas fontes permanecem pendentes, sem regra inventada.

## 11. Situação formal

- PROC-01–PROC-09: **DECOMPOSIÇÃO FUNCIONAL DOCUMENTAL v0.1 — NÃO VALIDADA**.
- D01–D20: **preservadas; não alteradas**.
- Cardinalidades M0.2: **preservadas**.
- M03-01–M03-16 e HARM-01–HARM-07: **pendências mantidas**.
- CA01–CA37: **referenciados; não executados por este documento**.
- SIM01–SIM12: **simulações documentais; não homologadas por este documento**.
- Validação operacional: **PENDENTE**.
- Gate G0: **NÃO APROVADO**.
- Implementação: **NÃO AUTORIZADA**.
- Código, banco, API, frontend, CI e infraestrutura: **SEM ALTERAÇÕES**.

## 12. Histórico

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-11 | Primeira decomposição funcional de PROC-01–PROC-09, com portas de controle, fluxo, saídas, bloqueios, evidências, rastreabilidade e decisões pendentes. |
