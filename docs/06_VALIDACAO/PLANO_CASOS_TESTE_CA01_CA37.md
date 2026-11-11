# Plano Preliminar de Casos de Teste — CA01 a CA37

**Identificador:** QA-PLAN-SEFI-CA-001  
**Versão:** 0.1  
**Data:** 2026-11-11  
**Fonte de critérios:** `docs/ESTADOS_E_TRANSICOES_SOLICITACAO_RECEBIMENTO.md`, v1.7.  
**Fontes de revisão:** `docs/REVISAO_MULTIDISCIPLINAR_MAQUINA_ESTADOS_CA01_CA24.md`, v1.2; `docs/VALIDACAO_CENARIOS_OPERACIONAIS_SEFI.md`, v1.2.  
**Natureza:** plano preliminar de especificação de testes; não executado, não homologado e não aprovado para implementação.

## 1. Objetivo e limites

Converter os critérios CA01–CA37 em casos de teste rastreáveis, conforme a metodologia aprovada em G0-P12. Esta versão define intenção, pré-condições genéricas, ação, resultado esperado e evidência sugerida.

**Não é evidência de execução.** Não há ambiente de teste definido, dados de teste aprovados, scripts, resultados obtidos, logs ou aceite de QA. Não se atribuem códigos HTTP, parâmetros técnicos, prazos ou comportamentos de infraestrutura que não estejam nas fontes.

### 1.1 Status dos critérios na fonte

- **CA01–CA24:** critérios funcionais consolidados para revisão em EST-REC-001; a revisão multidisciplinar os avaliou individualmente, mas a execução dos testes permanece pendente.
- **CA25–CA37:** complementos propostos pela revisão multidisciplinar e incorporados à documentação de estados; sua adoção/validação institucional e técnica permanece pendente.
- **Todos CA01–CA37:** caso de teste abaixo está **ESPECIFICADO EM RASCUNHO — NÃO EXECUTADO**.

## 2. Casos de teste

| Caso | RF / D relacionados | Pré-condições mínimas | Ação / estímulo | Resultado esperado (fonte CA) | Evidência sugerida | Situação |
|---|---|---|---|---|---|---|
| CA01 | RF-001/RF-015 · D01/D15 | Usuário sem permissão de registrar chegada; solicitação de teste existente. | Tentar registrar a chegada. | Operação bloqueada; tentativa registrada quando tecnicamente disponível. | Identidade/permissões antes do teste, solicitação, registro da tentativa e ausência de mutação. | Não executado |
| CA02 | RF-001/RF-010 · D01/D10 | Usuário com permissões RECEPÇÃO e CONFERENTE; item apto a conferência. | Registrar chegada e executar conferência com o mesmo usuário. | Permitido se ambas as permissões existirem; eventos distintos com ator e data/hora próprios. | Permissões vigentes, eventos de chegada/conferência e trilha de autoria/tempos. | Não executado |
| CA03 | RF-010 · D10 | Decisão sujeita à validação independente; usuário autor da decisão. | Tentar validar a própria decisão. | Bloqueio por independência; decisão permanece pendente. | Autoria da decisão, identidade do validador tentado, resposta e estado preservado. | Não executado |
| CA04 | RF-006/RF-011 · D06/D11 | Checklist publicado com critério E aplicável. | Registrar resultado NAO_CONFORME no critério E e tentar aceite. | Aceite bloqueado; coordenação não pode dispensar o critério. | Versão do checklist, resposta do critério, tentativa de aceite e bloqueio. | Não executado |
| CA05 | RF-005/RF-011 · D05/D11 | Checklist publicado com critério S aplicável. | Registrar NAO_CONFORME no critério S. | Pendência criada; aceite bloqueado até regularização e reavaliação favorável. | Checklist/versão, resposta, pendência, comunicação e reavaliação. | Não executado |
| CA06 | RF-011 · D11 | Checklist publicado com critério I; demais critérios sem bloqueio. | Deixar o critério I sem informação ou marcar NAO_APLICAVEL conforme regra. | Não bloqueia isoladamente, salvo regra obrigatória associada formalizada. | Versão, classe do critério, justificativa quando aplicável e decisão resultante. | Não executado |
| CA07 | RF-003/RF-020 · D03/D20 | Solicitação com item declarado não apresentado na chegada. | Registrar ausência do item. | ItemRecebimento NAO_APRESENTADO; sem ObjetoCustodia, custódia ou amostra. | Item declarado, registro da chegada, estado do item e consulta que demonstre ausência de objeto/amostra. | Não executado |
| CA08 | RF-003/RF-020 · D03/D20 | Recebimento com itens apresentados e não apresentados; demais desfechos válidos. | Concluir administrativamente o recebimento. | Pode ser CONCLUIDO; ausência permanece visível e não representa aceite. | Estado de cada item, decisões, pendências, estado agregado e trilha de conclusão. | Não executado |
| CA09 | RF-006/RF-007 · D06/D07 | Objeto formalmente recusado e ainda não retirado/destinado. | Consultar estado de guarda e tentar encerrar custódia sem entrega/destinação efetiva. | Objeto permanece SOB_GUARDA; custódia não ENCERRADA. | Decisão de recusa, custodiante/local atuais, tentativa e ausência de comprovante de destinação. | Não executado |
| CA10 | RF-007 · D07 | Objeto sob custódia de A; transferência solicitada para B, sem confirmação. | Solicitar transferência e não confirmar recebimento. | TRANSFERENCIA_PENDENTE; responsabilidade permanece com A. | Evento solicitado, ausência de confirmação e projeção de custodiante vigente. | Não executado |
| CA11 | RF-007 · D07 | Transferência pendente; destinatário B apto a confirmar. | B confirma recebimento. | Novo responsável/localização passam a vigorar; evento anterior permanece no histórico. | Confirmação de B, eventos anterior/novo e projeção de custódia. | Não executado |
| CA12 | RF-005 · D05 | Pendência comunicada formalmente, prazo institucional configurado, sem regularização. | Avançar o tempo de teste além do prazo. | PRAZO_VENCIDO e escalonamento; pendência continua aberta, sem recusa automática. | Comunicação/marco inicial, prazo, histórico temporal, alerta e estado aberto. | Não executado |
| CA13 | RF-005/RF-013 · D05/D13 | Pendência aberta; evidência/resposta recebida, sem reavaliação. | Registrar recebimento da evidência e consultar pendência. | Permanece AGUARDANDO_REAVALIACAO; não REGULARIZADA. | Evidência vinculada, evento de recebimento e ausência de avaliação favorável. | Não executado |
| CA14 | RF-006/RF-010/RF-016 · D06/D10/D16 | Recusa proposta por conferente; coordenação distinta e competente; assinatura aplicável definida. | Coordenação aprova a recusa proposta. | Validação independente e assinatura formal registradas; decisão final pode ser formalizada. | Autoria da proposta, identidade/competência do validador, assinatura e decisão final. | Não executado |
| CA15 | RF-006/RF-011 · D06/D11 | Critério E não conforme; coordenação sem fundamento normativo/institucional prévio aplicável. | Tentar dispensar o critério E. | Operação bloqueada, salvo fundamento normativo/institucional válido e previamente formalizado aplicável. | Critério E, versão, regra formal aplicável (se existir), ator, tentativa e resultado. | Não executado |
| CA16 | RF-018/RF-020 · D18/D20 | Objeto elegível para amostra; duas requisições concorrentes de criação. | Enviar requisições concorrentes para o mesmo ObjetoCustodia. | Uma única AmostraOperacional e um único identificador institucional. | Correlação das requisições, registros criados, identificador e consulta de unicidade. | Não executado |
| CA17 | RF-020 · D20 | Objeto aceito, mas validação obrigatória pendente. | Tentar criar AmostraOperacional. | Criação da amostra bloqueada. | Decisão de aceite, estado da validação e tentativa bloqueada; ausência de amostra. | Não executado |
| CA18 | RF-003/RF-004/RF-006/RF-020 · D03/D04/D06/D20 | Item com dois ObjetosCustodia elegíveis a decisões independentes. | Aceitar um objeto e recusar o outro. | Decisões independentes; item não aparece como integralmente aceito; recusado permanece sob custódia. | Objetos/quantidades, decisões, consolidação do item, custódia e amostra do objeto aceito quando elegível. | Não executado |
| CA19 | RF-009/RF-016 · D09/D16 | Decisão formalizada; pedido de retificação sem justificativa, evidência ou autorização. | Tentar retificar. | Operação bloqueada; registro original permanece íntegro. | Decisão original, pedido incompleto, resposta/bloqueio e trilha sem sobrescrita. | Não executado |
| CA20 | RF-009 · D09 | Amostra criada e ensaio iniciado; retificação solicitada. | Iniciar avaliação de retificação. | Avaliação de impacto obrigatória; nenhuma amostra, ensaio ou laudo excluído automaticamente. | Estado da amostra/ensaio, solicitação de retificação, avaliação de impacto e vínculos preservados. | Não executado |
| CA21 | RF-010/RF-015 · D10/D15 | Usuário com perfil administrador sem autoridade para autoelevação. | Tentar elevar a própria permissão. | Bloqueado; evento da tentativa registrado quando tecnicamente disponível. | Perfil/permissões antes/depois, solicitação, bloqueio e evento de segurança. | Não executado |
| CA22 | RF-014 · D14 | Evento de auditoria formalizado; usuário tenta alterá-lo/excluí-lo. | Executar tentativa de alteração/exclusão. | Bloqueado; original preservado. | Evento original, tentativa, resultado e verificação de integridade/trilha. | Não executado |
| CA23 | RF-019/RF-018 · D19/D18 | Recebimento concluído com item NAO_APRESENTADO. | Registrar material que chega posteriormente. | Não há retroação; nova solicitação ou exceção formal com data/hora efetiva. | Registro original, novo fato, autorização de exceção/nova solicitação e tempos. | Não executado |
| CA24 | RF-011/RF-012 · D11/D12 | Conferência iniciada com versão publicada de checklist; nova versão publicada posteriormente. | Consultar/continuar conferência após mudança de versão. | Conferência permanece vinculada à versão original; migração somente por procedimento formal auditável. | Versão inicial e nova, vínculo da conferência e eventual procedimento formal. | Não executado |
| CA25 | RF-013/RF-015 · D13/D15 | Solicitante autenticado sem vínculo autorizado à solicitação de terceiro. | Consultar, listar ou baixar registro/anexo de terceiro. | Acesso negado no servidor, sem revelar conteúdo ou existência indevida; evento de segurança conforme política. | Identidades/vínculos, requisição, resposta sem dados sensíveis e registro de segurança. | Não executado; complemento proposto |
| CA26 | RF-002/RF-003 · D02/D03 | Item declarado com quantidade diferente da apresentada. | Registrar a quantidade observada. | Ambas permanecem preservadas; divergência registrada e encaminhada ao critério/checklist aplicável. | Declaração original, observação, unidade, divergência e encaminhamento. | Não executado; complemento proposto |
| CA27 | RF-003/RF-004 · D03/D04 | ObjetoCustodia representa agrupamento homogêneo. | Criar/consultar objeto agrupado. | Quantidade/unidade representada e justificativa de agrupamento ficam explícitas; não se presume equivalência objeto-unidade física. | Critério de homogeneidade, quantidade/unidade, justificativa e linhagem. | Não executado; complemento proposto |
| CA28 | RF-002/RF-014/RF-019 · D02/D14/D19 | Fato ocorreu antes do registro; fonte temporal e justificativa disponíveis. | Registrar evento tardiamente com tempos distintos. | occurred_at e recorded_at permanecem distintos; registro tardio justificado; recorded_at não retroage. | Horário do fato, horário de gravação, autor, justificativa e fonte temporal. | Não executado; complemento proposto |
| CA29 | RF-008 · D08 | Objeto sob custódia de A em local X. | Registrar mudança para local Y sem transferência. | LOCATION_CHANGE atualiza localização projetada sem simular TRANSFER nem trocar responsável. | Evento de movimentação, locais antes/depois e custodiante inalterado. | Não executado; complemento proposto |
| CA30 | RF-007/RF-008 · D07/D08 | Transferência solicitada sem confirmação do destinatário. | Consultar custodiante/localização vigentes. | Custodiante e localização permanecem conforme último evento confirmado. | Eventos da transferência, falta de confirmação e projeção atual. | Não executado; complemento proposto |
| CA31 | RF-018/RF-020 · D18/D20 | Operação crítica concluída com chave de idempotência e conteúdo registrados. | Reenviar mesma chave e mesmo conteúdo após sucesso. | Resultado original é devolvido sem duplicar recebimento, evento ou amostra. | Chave, hash/conteúdo, resposta original, resposta de replay e contagem de registros. | Não executado; complemento proposto |
| CA32 | Transversal · G0-P23 | Chave de idempotência já associada a conteúdo diferente. | Reutilizar a mesma chave com payload diferente. | Requisição rejeitada como conflito; nenhum efeito adicional ocorre. | Chave anterior, conteúdo/hash novo, conflito e ausência de mutação. | Não executado; complemento proposto |
| CA33 | Transversal · G0-P23 | Duas alterações concorrentes partem da mesma versão esperada. | Executar alterações simultâneas. | Apenas uma efetivada; outra recebe VERSION_CONFLICT e não sobrescreve dados. | Versão inicial, requisições, ordem/resultado, versão final e ausência de perda de atualização. | Não executado; complemento proposto |
| CA34 | RF-014/RF-018 · D14/D18 | Histórico paginado; novas gravações ocorrem durante a consulta. | Percorrer páginas sucessivas enquanto novos eventos são gravados. | Ordenação/paginação estáveis, sem perda ou duplicação lógica dos eventos já existentes. | Filtros, cursores/páginas, sequência/ordenação e conjunto de IDs consultados. | Não executado; complemento proposto |
| CA35 | RF-013/RF-014 · D13/D14 | Evidência vinculada a entidade; operação de envio/consulta/substituição autorizada. | Enviar, consultar e substituir evidência. | Hash, metadados, vínculo, autorização e histórico preservados; alteração não destrói evidência formalizada. | Arquivo/hash original, metadados, permissões, versões, vínculo e trilha. | Não executado; complemento proposto |
| CA36 | RF-018/RF-019 · D18/D19 | Registro legado sem evidência confiável de vínculo ao novo domínio. | Executar reconciliação/migração do registro. | Não é associado por presunção; permanece identificado como legado não reconciliado. | Registro legado, regra de reconciliação, resultado e fila de exceções. | Não executado; complemento proposto |
| CA37 | RF-018 · D18 | Processo, amostra e representação QR disponíveis. | Apresentar protocolo SEFI, accession e QR em telas/documentos. | Cada elemento mantém finalidade e vínculo próprios; QR não substitui identificador persistido. | Identificadores, entidades-alvo, representação QR e consulta de vínculo. | Não executado; complemento proposto |

## 3. Requisitos transversais de execução

Antes de executar os casos, o plano de QA deverá definir e aprovar:
1. ambiente isolado, versão/build e commit sob teste;
2. banco-alvo e estratégia de limpeza/recriação de dados;
3. usuários de teste, perfis, permissões, competências e vínculos;
4. dados sintéticos/anonimizados e massa de teste;
5. política de relógio/fuso e como simular prazos/concorrência;
6. mecanismo de captura de evidências e identificação do executor;
7. critérios de aprovação/reprovação, severidade, defeitos e reteste;
8. vínculo de cada execução ao commit, configuração e resultado;
9. tratamento de dados pessoais e anexos usados no teste;
10. aprovação de QA e, para SIM, validação com representantes do SEFI.

## 4. Cobertura ainda não representada por CA01–CA37

Conforme SIM-SEFI-REC-001 v1.2, devem ser acrescentados cenários próprios para:
- restauração de backup e continuidade (D17/G0-P06);
- integridade de anexos/hash em falha, corrupção ou indisponibilidade;
- autorização e assinatura em todos os atos críticos aplicáveis;
- acesso indevido direto a anexos/URLs;
- conflitos de concorrência adicionais e requisições em processamento;
- falhas de armazenamento e recuperação de evidências;
- cobertura E2E do fluxo completo de solicitação até admissão da amostra.

Não criar números CA adicionais até a governança de critérios definir e aprovar a numeração.

## 5. Situação formal

- CA01–CA24: **CASOS ESPECIFICADOS EM RASCUNHO; NÃO EXECUTADOS**.
- CA25–CA37: **COMPLEMENTOS PROPOSTOS; CASOS ESPECIFICADOS EM RASCUNHO; NÃO EXECUTADOS**.
- SIM01–SIM12: **SIMULAÇÃO DOCUMENTAL; VALIDAÇÃO OPERACIONAL PENDENTE**.
- Evidências de execução: **NENHUMA PRODUZIDA NESTE DOCUMENTO**.
- Gate G0: **NÃO APROVADO**.
- Implementação: **NÃO AUTORIZADA**.
