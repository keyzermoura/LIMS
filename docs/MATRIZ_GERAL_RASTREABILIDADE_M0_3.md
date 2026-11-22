# Matriz Geral de Rastreabilidade M0.3 — LIMS-SEFI

**Identificador:** MAT-RAST-M03-001  
**Versão:** 0.8  
**Data:** 2026-11-21  
**Situação:** Consolidação técnica preliminar para revisão; M0.3 não aprovado; Gate G0 não aprovado; implementação não autorizada.  
**Repositório:** keyzermoura/LIMS — branch main

## 1. Objetivo e limites

Consolidar rastreabilidade entre decisões D01–D20, entidades, estados, eventos, invariantes INV-01–INV-34, critérios CA01–CA37, cenários SIM01–SIM12 e evidências técnicas. A matriz orienta fechamento de lacunas e preparação de validação, mas não altera decisões institucionais nem transforma proposta M0.3 em modelo aprovado.

Esta versão é uma matriz de correspondência semântica inicial. Vínculos CA/SIM indicados como associação temática não substituem a validação formal requisito-a-requisito. Quando não há vínculo unívoco ou evidência suficiente, a lacuna é explicitada em vez de inferir conformidade.

## 2. Baseline e fontes

| Artefato | Referência examinada | Papel |
|---|---|---|
| D01–D20 e G0-P01–P30 | `docs/DECISOES_PREVALIDACAO_SEFI_D01_D20.md` (1.7) | Registro de decisões ratificadas e diretrizes aprovadas; não aprova entregáveis/Gate. |
| M0.3 | `docs/MODELO_LOGICO_REVISADO_DOMINIO_SEFI_M0_3.md` (0.1) | Entidades, cardinalidades, estados, eventos, 34 invariantes e rastreabilidade D01–D20. |
| Estados e transições | `docs/ESTADOS_E_TRANSICOES_SOLICITACAO_RECEBIMENTO.md` (1.7) | Proposta EST-REC-001 e CA01–CA37; validação operacional pendente. |
| Auditoria de aderência | `docs/MATRIZ_ADERENCIA_DOMINIO_SEFI.md` (1.2) | ACH-01–ACH-41 e confronto indicativo com invariantes. |
| Prontidão G0 | `docs/MATRIZ_PRONTIDAO_GATE_G0.md` (0.4) | Situação de entregáveis e Gate; G0 não aprovado. |
| Cenários | `docs/VALIDACAO_CENARIOS_OPERACIONAIS_SEFI.md` (2.1) | SIM01–SIM12 e distinção entre teste escrito, executado, aprovado e homologado. |
| Testes | `backend/tests/test_phase1_simulations.py` | Arquivo de testes versionado; leitura estática, sem execução nesta rodada. |

**Baseline Git de referência para esta consolidação:** os documentos foram relidos em `main` após as publicações documentais anteriores. O HEAD de código e o estado de CI não foram revalidados nesta etapa; não usar esta matriz como declaração de execução ou de commit de código.

## 3. Matriz D01–D20 × domínio × evidência

| Decisão | Requisito/resultado | Entidades | Estados | Eventos | Invariantes | CA (associação preliminar) | SIM | Evidência / implementação examinada | Lacuna | Parecer |
|---|---|---|---|---|---|---|---|---|---|---|
| D01 | Registro de chegada, recebedor, autor e conferência separados | Recebimento; UsuarioInterno; EventoAuditoria | REGISTRADO; EM_CONFERENCIA | CHEGADA_REGISTRADA; CONFERENCIA_INICIADA/CONCLUIDA | INV-09, INV-25, INV-30, INV-31 | CA01–CA03 (associação temática) | SIM01 | EST-REC-001 separa registro e conferência; código cria Receipt/CustodyObject; auditoria deve validar ator, escopo e timestamps em todos caminhos. | Parcial; separar eventos e comprovar competência/ator/horário. |
| D02 | Metadados da chegada física e condição dos volumes | Recebimento; Evidencia; Localizacao | REGISTRADO | CHEGADA_REGISTRADA | INV-09, INV-25, INV-31 | CA28 (registro tardio) | SIM01, SIM12 | M0.3 define instante efetivo/registro, local, volumes, condição, documentos e observações. | Parcial; justificativa de registro tardio e completude de metadados não comprovadas. |
| D03 | Quantidades declarada, apresentada, sob custódia, aceita, recusada e ausente | ItemDeclarado; ItemRecebimento; EventoApresentacao; ObjetoCustodia | APRESENTADO; NAO_APRESENTADO | APRESENTACAO_REGISTRADA; QUANTIDADE_RECONCILIADA | INV-03, INV-07, INV-25, INV-34 | CA26–CA28 | SIM02, SIM03 | Campos declarados/apresentados existem em entidades distintas; reconciliação integral não demonstrada. | Parcial; falta reconciliação formal e unidade/conversão por categoria. |
| D04 | Objeto de custódia por material apresentado, decisão independente e agrupamento/fracionamento | ItemRecebimento; EventoApresentacao; ObjetoCustodia | SOB_GUARDA; decisão por objeto | OBJETO_CRIADO; FRACIONAMENTO/AGRUPAMENTO | INV-04, INV-05, INV-06, INV-08, INV-10, INV-34 | CA07, CA18, CA24, CA27 | SIM02, SIM04 | M0.3 preserva ItemRecebimento 1:0..N ObjetoCustodia; implementação cria objetos no recebimento antes da confirmação de apresentação. | Não conforme em cenário de não apresentado; granularidade/linhagem parcial. |
| D05 | Pendência com responsável, prazo, comunicação, evidência e reavaliação | Pendencia; RespostaChecklist; Evidencia | PENDENTE; EM_REGULARIZACAO; REAVALIACAO | PENDENCIA_ABERTA; EVIDENCIA_JUNTADA; REAVALIACAO_REGISTRADA | INV-15, INV-16, INV-17, INV-31 | CA05, CA12, CA13, CA19 | SIM05 | Há conceitos/serviços de checklist e pendência; não comprovada reavaliação favorável como pré-condição uniforme de aceite. | Parcial/não comprovado; fechar ciclo de reavaliação. |
| D06 | Recusa fundamentada não encerra custódia; destinação física posterior comprovada | DecisaoRecebimento; ObjetoCustodia; EventoCustodia; Evidencia | RECUSADO + SOB_GUARDA; depois DESTINADO/DEVOLVIDO | DECISAO_RECUSA; DEVOLUCAO/DESTINACAO_CONFIRMADA | INV-13, INV-18, INV-31, INV-32 | CA09, CA14 | SIM06 | Serviço registra estado RECUSADO e evento ENCERRAMENTO sem evidência de destinação física. | Não conforme; separar decisão de recusa do encerramento material. |
| D07 | Transferência só muda custodiante após confirmação do recebedor | ObjetoCustodia; EventoCustodia; UsuarioInterno | TRANSFERENCIA_PENDENTE; SOB_GUARDA | TRANSFERENCIA_SOLICITADA; TRANSFERENCIA_CONFIRMADA | INV-09, INV-11, INV-19, INV-31 | CA10, CA11, CA30 | SIM07 | transfer_custody atualiza custodiante/local imediatamente; fluxo de confirmação independente não identificado. | Não conforme; requer estado pendente e confirmação do destinatário. |
| D08 | Mudança de localização sem alterar custodiante | ObjetoCustodia; Localizacao; EventoCustodia | SOB_GUARDA | LOCALIZACAO_ALTERADA | INV-12, INV-31 | CA29 | SIM08 | Taxonomia examinada usa evento de transferência; evento independente de mudança de localização não identificado. | Não conforme no fluxo examinado. |
| D09 | Retificação excepcional com original, motivo, autorização, evidência, assinatura e impacto | Retificacao; Evidencia; AssinaturaEletronica; EventoAuditoria | RETIFICACAO_PENDENTE; RETIFICADO | RETIFICACAO_SOLICITADA; AUTORIZACAO; IMPACTO_AVALIADO | INV-25, INV-26, INV-31 | CA19, CA20 | SIM09 | Retificação de resultado/laudo existe em parte; retificação transversal de solicitação/recebimento/objeto e avaliação de impacto não comprovadas. | Parcial/não comprovado; distinguir retificação de domínio e retificação de laudo. |
| D10 | Acúmulo permitido, mas autoaprovação bloqueada quando independência exigida; ADMIN sem autoridade técnica implícita | UsuarioInterno; DesignacaoCompetencia; ValidacaoCoordenacao | AGUARDANDO_COORDENACAO; VALIDADO/REJEITADO | VALIDACAO_SOLICITADA; VALIDACAO_DECIDIDA | INV-19, INV-20, INV-30 | CA02, CA03, CA14, CA21 | SIM12 | Serviço bloqueia parte de autoaprovação; exceção ADMIN e matriz institucional de competência precisam revisão. | Parcial; testar combinações de papéis e autoridade. |
| D11 | Checklist por categoria, critérios E/S/I e versão aplicada preservada | ChecklistModelo; VersaoChecklist; CriterioChecklist; RespostaChecklist | EM_CONFERENCIA; CONCLUIDA | CHECKLIST_APLICADO; RESPOSTA_FORMALIZADA | INV-14, INV-15, INV-17 | CA04–CA06, CA15, CA24 | SIM01, SIM05 | Há checklist/respostas; serviço substitui respostas via clear e aceite não consulta integralmente os bloqueios. | Não conforme; preservar snapshot e fazer E/S funcionarem como barreira. |
| D12 | Governança de checklist: elaboração, revisão, aprovação e publicação | ChecklistModelo; VersaoChecklist; UsuarioInterno; DesignacaoCompetencia | RASCUNHO; EM_REVISAO; APROVADO; PUBLICADO | VERSAO_APROVADA; CHECKLIST_PUBLICADO | INV-14, INV-20, INV-30, INV-31 | CA15, CA21, CA24 | SIM01 | Modelo M0.3 prevê ciclo e aprovadores; workflow institucional completo e trilha de publicação não comprovados. | Não comprovado; definir matriz de competência e ciclo de vida. |
| D13 | Evidências vinculadas, originais preservados, hash, versões, acesso e retenção | Evidencia; VinculoEvidencia; EventoAuditoria | VINCULADA; SUBSTITUIDA_POR_NOVA_VERSAO | EVIDENCIA_RECEBIDA; EVIDENCIA_VINCULADA | INV-26, INV-30, INV-31 | CA25, CA35, CA36 | SIM11 | Hash SHA-256/metadados existem; autorização contextual, versionamento, retenção e vínculo legado incompletos. | Parcial; hash não substitui controle de acesso e retenção. |
| D14 | Trilha cronológica individualizada e protegida; correções como novos eventos | EventoAuditoria; EventoCustodia; Retificacao | REGISTRADO; CORRIGIDO_POR_NOVO_EVENTO | OPERACAO_AUDITADA; RETIFICACAO_REGISTRADA | INV-10, INV-25, INV-26, INV-31 | CA22, CA28, CA33, CA34 | SIM09, SIM10 | Auditoria hash/HMAC e eventos existem; imutabilidade forte, paginação estável e cobertura transversal não comprovadas. | Parcial; comprovar append-only, histórico e ordenação/paginação. |
| D15 | Contas individuais, menor privilégio, competência, escopo e revogação | UsuarioInterno; Perfil/Permissao; DesignacaoCompetencia | ATIVO; BLOQUEADO; REVOGADO | ACESSO_AUTORIZADO/NEGADO; PERMISSAO_ALTERADA | INV-19, INV-20, INV-30, INV-31 | CA01, CA21, CA25 | SIM11, SIM12 | RBAC/autenticação existem; isolamento organizacional/contextual não demonstrado em consultas e anexos. | Parcial/insuficiente; auditoria transversal de autorização é bloqueadora. |
| D16 | Assinatura ligada ao ato/conteúdo, identidade, intenção e instante; não substitui autorização/independência | AssinaturaEletronica; UsuarioInterno; ValidacaoCoordenacao; EventoAuditoria | ASSINATURA_PENDENTE; ASSINADO | ATO_ASSINADO; ASSINATURA_VERIFICADA | INV-19, INV-20, INV-30, INV-31 | CA03, CA14, CA19, CA20 | SIM05, SIM09, SIM12 | Assinatura de laudo existe; token em revisão técnica opcional em trechos examinados; política institucional permanece pendente. | Parcial; exigir assinatura somente nos atos definidos e testar conteúdo/ator. |
| D17 | Backup, recuperação, retenção, segregação, monitoramento e testes de restauração | Infraestrutura/serviço transversal; registros de backup e restauração | BACKUP_VALIDADO; RESTAURACAO_TESTADA | BACKUP_EXECUTADO; RESTAURACAO_VALIDADA | INV-30, INV-31 | CA35 (relação indireta) | Não há SIM específico inequívoco | G0-P17 e G0-P30 aprovam diretrizes; evidência técnica de backup/restauração e política final não foi verificada nesta matriz. | Não comprovado; exige evidência de infraestrutura, não só modelo de domínio. |
| D18 | Identificadores próprios, únicos, permanentes e não reutilizáveis | Solicitacao; Recebimento; ObjetoCustodia; AmostraOperacional; Ensaio; ReferenciaExterna | IDENTIFICADO; LEGADO_NAO_RECONCILIADO | IDENTIFICADOR_ATRIBUIDO; REFERENCIA_ASSOCIADA | INV-02, INV-22, INV-27, INV-28, INV-29 | CA31, CA32, CA36, CA37 | SIM10 | Accession e QR aparecem acoplados; reconciliação legado não comprovada; unicidade de objetos/amostras parcial. | Parcial; separar protocolo, accession e QR; definir legado com evidência. |
| D19 | Chegada posterior como novo fato, sem retroagir recebimento anterior | EventoApresentacao; ItemRecebimento; Recebimento; Evidencia | APRESENTACAO_COMPLEMENTAR; EM_TRATAMENTO | APRESENTACAO_COMPLEMENTAR_REGISTRADA; NOVA_CONFERENCIA | INV-02, INV-25, INV-33 | CA23, CA28, CA36 | SIM12 | M0.3 propõe EventoApresentacao complementar; código/documentação operacional não comprovam evento próprio. | Não comprovado; depende de validação funcional M0.3 e implementação futura. |
| D20 | Amostra só após apresentação, conferência, quantidades, checklist, pendências, decisão/validação e custódia válidos | DecisaoRecebimento; ValidacaoCoordenacao; ObjetoCustodia; AmostraOperacional | ACEITO; VALIDADO; AMOSTRA_CRIADA | DECISAO_ACEITE; VALIDACAO_COORDENACAO; AMOSTRA_CRIADA | INV-04, INV-05, INV-15, INV-17, INV-19, INV-21, INV-22, INV-23, INV-24 | CA04, CA05, CA15–CA18, CA21–CA24 | SIM01, SIM04, SIM05 | accept_custody_object cria DeviceSample após checagem de estado/versão, sem integrar todos os bloqueios formais; risco concorrência/idempotência. | Não conforme/parcial; bloqueador crítico até unificar barreira formal de aceite. |

## 4. Cobertura dos invariantes INV-01–INV-34

| Grupo | Invariantes | Cobertura de decisões | Lacuna principal |
|---|---|---|---|
| Solicitação/recebimento | INV-01–INV-03 | D01–D03, D18 | Evidência de submissão com item e unicidade/concorrência do recebimento principal. |
| Apresentação/custódia | INV-04–INV-13 | D03–D08, D19 | Não apresentado não pode gerar objeto; confirmação transferência; localização independente; destinação efetiva. |
| Checklist/decisão/independência | INV-14–INV-20 | D05, D06, D10–D12, D15, D16 | Snapshot de versão, bloqueios E/S, reavaliação e competência/independência. |
| Amostra/atomicidade | INV-21–INV-24 | D20, D18 | Barreira formal, unicidade, atomicidade e idempotência de aceite/amostra. |
| Tempo/retificação | INV-25–INV-26 | D02, D09, D14 | Preservar efetivo/registro e impacto/autorizações em retificação. |
| Identificadores/legado | INV-27–INV-29 | D18 | Semântica independente e reconciliação sem presunção. |
| Segurança/auditoria | INV-30–INV-31 | D10, D13–D16 | Autorização contextual por escopo/competência, assinatura e trilha. |
| Agregação/chegada/linhagem | INV-32–INV-34 | D03, D04, D06, D19 | Estado agregado sem ocultar desfechos, chegada complementar e fracionamento. |

## 5. Cobertura dos cenários SIM01–SIM12

| Cenário | Tema | Decisões/invariantes relacionados | Resultado da auditoria estática |
|---|---|---|---|
| SIM01 | Recebimento integral e aceite | D01–D04, D11, D20; INV-04–06, 14–24 | Caminho feliz documentado; barreira de aceite completa não demonstrada. |
| SIM02 | Item não apresentado | D03–D04; INV-03–06 | Divergência: objetos são criados antes de confirmar apresentação. |
| SIM03 | Quantidade divergente | D03; INV-07, 34 | Campos separados; reconciliação integral parcial. |
| SIM04 | Dois objetos, decisões divergentes | D04, D06, D20; INV-08, 18, 21 | Granularidade parcial; decisões independentes devem ser provadas. |
| SIM05 | Pendência saneável e reavaliação | D05, D10, D11, D20; INV-15–19, 21 | Ciclo de reavaliação e bloqueio de aceite não demonstrados integralmente. |
| SIM06 | Recusa e devolução posterior | D06; INV-13, 32 | Recusa confundida com encerramento; destinação física não comprovada. |
| SIM07 | Transferência | D07; INV-11 | Transferência efetivada sem confirmação do destinatário. |
| SIM08 | Mudança de localização | D08; INV-12 | Evento independente de localização não identificado. |
| SIM09 | Retificação após amostra/ensaio | D09, D13, D14, D16; INV-25, 26, 31 | Retificação de resultado/laudo não prova retificação transversal e avaliação de impacto. |
| SIM10 | Reenvio concorrente/versão obsoleta | D14, D18, D20; INV-02, 22, 23, 27 | Idempotência/concorrência em comandos de recebimento, custódia e aceite não comprovadas. |
| SIM11 | Acesso a terceiro | D13, D15; INV-30, 31 | Autenticação existe; autorização contextual por solicitante/unidade/recurso não demonstrada. |
| SIM12 | Chegada posterior | D19; INV-25, 33 | EventoApresentacao é proposta M0.3; materialização no fluxo não comprovada. |

## 6. Achados técnicos ACH-01–ACH-41 e relação com D/INV

Os 41 achados estão detalhados em `MATRIZ_ADERENCIA_DOMINIO_SEFI.md`, seção 10. A associação por tema não deve ser interpretada como 41 violações independentes: há grupos correlatos (por exemplo, transferência ACH-10/18/35; barreira de aceite ACH-08/15/20/21/23; evidências ACH-13/31/39). O fechamento deve agrupar causa-raiz e preservar rastreabilidade individual.

## 7. G0-P01–P30 — diretrizes aprovadas versus entregáveis

G0-P01–P30 estão registrados como aprovados integralmente no documento de decisões. A aprovação refere-se às diretrizes/processos de elaboração, não à conclusão automática dos entregáveis correspondentes. A matriz G0 continua sendo o instrumento de prontidão. Os grupos de dependência identificados são:

- Governança, competências, critérios e aceite: P01–P07, P12–P16.
- Custódia, eventos, evidências e rastreabilidade: P08–P15, P24–P25.
- Continuidade, migração e reconciliação: P17–P20.
- Agrupamento, fracionamento, consulta histórica e exportação: P21–P28.
- Autenticação reforçada e retenção: P29–P30.

Os agrupamentos acima são navegação temática preliminar, não substituem a leitura individual de cada proposta nem demonstram conclusão dos entregáveis G0-01–G0-26.

## 8. Lacunas prioritárias para fechamento

| Prioridade | Pacote de correção/validação | Dependências principais | Critério de encerramento |
|---|---|---|---|
| P0 | Unificar barreira de aceite e criação de amostra | D11, D20; INV-14–23; CA04/05/15–18/21–24; SIM01/04/05 | Uma única operação transacional exige checklist versionado, ausência de E impeditivo, saneamento/reavaliação S, decisão, revisão e custódia válidas; idempotência/concorrrência demonstradas. |
| P0 | Corrigir nascimento e ciclo de custódia | D04, D06–D08; INV-04–13; CA07/09–11/29/30; SIM02/06–08 | Não apresentado não gera objeto/evento; transferência só após aceite do destinatário; localização separada; recusa não encerra custódia. |
| P0 | Autorização contextual e independência | D10, D15, D16; INV-19/20/30/31; CA01–03/21/25; SIM11/12 | Testes negativos por papel, competência, unidade, vínculo e alvo; sem acesso cruzado ou autoaprovação indevida. |
| P0 | Concorrência/idempotência dos comandos críticos | D14, D18, D20; INV-02/22/23/27; CA31–33; SIM10 | Reenvio idêntico não duplica; payload divergente conflita; concorrência gera um único aceite/amostra. |
| P1 | Checklist e retificação com histórico | D09, D11–D14; INV-14/17/26/31; CA19/20/24/35; SIM05/09 | Versão aplicada imutável; respostas não sobrescritas; retificação preserva original, autorização, evidência e impacto. |
| P1 | Quantidades, agrupamento, fracionamento e chegada complementar | D03, D04, D19; INV-07/08/33/34; CA23/26–28/32/36; SIM03/04/12 | Reconciliação auditável de quantidades e linhagem; apresentação complementar como novo fato sem retroatividade. |
| P1 | Evidências, histórico, retenção e continuidade | D13, D14, D17; INV-26/30/31; CA22/34/35/36 | Acesso contextual, versionamento, paginação, política de retenção e teste de restauração evidenciados. |

## 9. Pendências de validação institucional M0.3

Antes de declarar M0.3 consolidado, ainda são necessárias as condições da seção 17 do próprio M0.3: revisão por Validação Institucional/Qualidade; confirmação de cardinalidades M0.2; validação de EventoApresentacao/D19; cenários de apresentação parcial/múltipla, objetos, agrupamento/fracionamento e decisões divergentes; separação entre decisão, custódia e recebimento agregado; sequência de aceite/amostra D20; rastreabilidade individual de cada INV para CA/SIM; coerência com EST-REC-001 e demais contratos; registro de divergências e responsáveis.

## 10. Parecer

A rastreabilidade está estruturada em nível de decisão e grupos de invariantes/cenários, mas ainda não está fechada requisito a requisito com execução de teste e evidência verificável para cada linha. A matriz é suficiente para orientar a próxima rodada de auditoria e planejamento, não para aprovar M0.3, CA/SIM, entregáveis G0 ou operação.

**M0.3: AGUARDANDO REVISÃO/VALIDAÇÃO.**  
**GATE G0: NÃO APROVADO.**  
**IMPLEMENTAÇÃO SEFI: NÃO AUTORIZADA.**  
**Nesta entrega: somente documento novo; sem alteração de código, banco, API, frontend, CI ou infraestrutura.**

## 11. Histórico

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-21 | Primeira consolidação D01–D20 × entidades/estados/eventos × INV × CA × SIM, com evidência, lacunas, parecer e plano de fechamento. |
| 0.2 | 2026-11-21 | Segunda camada de rastreabilidade estática: serviços, rotas/API, testes existentes, linhas de código e lacunas entre teste escrito e requisito. |
| 0.3 | 2026-11-21 | Auditoria estática de autorização contextual, isolamento organizacional, acesso a anexos, usuários e exposição pública de laudos. |
| 0.4 | 2026-11-21 | Auditoria estática de concorrência, atomicidade, idempotência e consistência transacional dos fluxos de recebimento, decisão, aceite e custódia. |
## 12. Rastreabilidade técnica — requisito → serviço → API → teste

**Método:** leitura estática dos arquivos atuais da branch main. As referências identificam código e testes versionados; não representam execução da suíte. A coluna teste descreve o que o teste efetivamente afirma, não o que o nome promete.

| Fluxo/requisito | Serviço e trecho | Rota/API | Teste versionado | Constatação estática e lacuna |
|---|---|---|---|---|
| Criar recebimento e objetos iniciais | receipt_service.py:45-160 — create_receipt | POST de recebimento por solicitação | test_phase1_simulations.py:39-167 SIM01; :168-218 SIM02 | Cria ReceiptItem e CustodyObject para cada item declarado, com status PRESENTED e evento INGRESSO, antes da conferência física. SIM02 apenas muda depois o item para NOT_PRESENTED; não testa ausência de objeto/evento inicial. Divergência direta com INV-04/05. |
| Conferir item apresentado/não apresentado | receipt_service.py:196-260 — conference_item | POST /api/v1/receipts/{receipt_id}/items/{item_id}/conference; routes/receipts.py:43-69 | SIM02, test_phase1_simulations.py:168-218 | Atualiza status/quantidade/conferência, mas não desfaz ou impede CustodyObject criado anteriormente. SIM02 verifica status e quantidade, não ausência de objeto/custódia. |
| Decisão técnica por item | decision_service.py:28-82 — record_receipt_decision | POST /api/v1/receipts/{receipt_id}/items/{item_id}/decisions; routes/decisions.py:27-52 | test_phase1_checklist_decisions.py:191 em diante; SIM06 e SIM12 | Registra ReceiptDecision e abre CoordinationReview para PENDING/REJECTED. No trecho examinado não valida se custody_object_id pertence ao ReceiptItem nem bloqueia decisão antes da conferência física. |
| Revisão independente da coordenação | decision_service.py — review_coordination_decision | POST /api/v1/coordination/reviews/{review_id}/action; routes/decisions.py:75-100 | test_phase1_checklist_decisions.py:191 em diante; SIM12 test_phase1_simulations.py:669 em diante | Serviço compara autor da decisão com revisor; teste cobre auto-revisão e revisão por outro usuário. Não demonstra matriz completa de competência/unidade nem autoridade ADMIN. |
| Checklist e classes E/S/I | checklist_service.py:132-220 — submit_checklist_answers | POST /api/v1/receipts/{receipt_id}/items/{item_id}/checklist; routes/checklists.py | test_phase1_checklist_decisions.py:66-189 | Teste demonstra E não conforme → NAO_CONFORME; S não conforme → COM_RESSALVA; conforme → CONFORME. Serviço limpa respostas anteriores com checklist_answers.clear(); teste inclusive reenvia respostas e verifica apenas o conjunto final. Não preserva snapshot/histórico da versão aplicada e não testa barreira de aceite. |
| Transferência de custódia | receipt_service.py:299-360 — transfer_custody | POST /api/v1/custody/objects/{id}/transfers; routes/receipts.py:95-125 | SIM07, test_phase1_simulations.py:461-520 | Serviço cria evento TRANSFERENCIA e atualiza custodiante/local imediatamente. SIM07 exige esse resultado e não contém etapa de confirmação do destinatário. Divergência direta com INV-11. |
| Aceite e geração de amostra | receipt_service.py:362 em diante — accept_custody_object | POST /api/v1/custody/objects/{id}/acceptance; routes/receipts.py:127-160 | SIM01, test_phase1_simulations.py:39-167 | Serviço valida status SOB_GUARDA e versão, depois cria DeviceSample; no trecho examinado não consulta checklist, ReceiptDecision, CoordinationReview, pendências ou confirmação de apresentação. Amostra e evento são criados na mesma sessão/transação, mas não há prova suficiente de barreira formal completa, idempotência sob concorrência ou lock do objeto. |
| Recusa e permanência física | receipt_service.py — ramo REJECTED de accept_custody_object | Mesmo endpoint de acceptance | SIM06, test_phase1_simulations.py:412-460 | Ramo de recusa marca RECUSADO e cria evento ENCERRAMENTO com destinatário/local nulos. SIM06 apenas verifica ausência de amostra e consulta do objeto; não demonstra permanência sob custódia nem destinação física posterior. |
| Evidências anexadas a ensaio | attachment_service.py:20-100 | routes/attachments.py: POST upload; GET list/download | Não localizado SIM dedicado; testes específicos de anexos ainda precisam ser inventariados | Upload valida tamanho, calcula SHA-256, grava arquivo/autor e auditoria. GET/list/download recebem CurrentUser, mas serviço consulta por ID/test_id sem autorização contextual demonstrada. Hash prova integridade do conteúdo recebido, não autorização nem imutabilidade do ciclo de vida. |
| Resultado assinado versus execução | execution_service.py:220 em diante — complete_execution; test_service.py:148 em diante — record_result | POST /api/v1/executions/{id}/complete; PATCH /api/v1/tests/{id}/result em routes/tests.py:119 em diante | test_phase2_executions.py:272 em diante; test_phase3_reviews.py | Existe fluxo formal TestExecution e endpoint separado para assinar resultado. record_result bloqueia por amostra/versão e exige assinatura, mas não exige vínculo com TestExecution concluída. Testes de execução não provam que todo resultado assinado depende de execução válida. |

### 12.1 Testes escritos que não demonstram o requisito integral

| Teste | O que efetivamente verifica | O que não verifica |
|---|---|---|
| SIM02 | Item atualizado para NOT_PRESENTED e quantidade 0 | Ausência de CustodyObject, evento INGRESSO ou custódia para esse item. |
| SIM06 | Decisão REJECTED abre revisão; objeto consultável e sem amostra | Objeto continua SOB_GUARDA, ENCERRAMENTO não ocorre ou devolução/destinação é comprovada. |
| SIM07 | Transferência muda imediatamente custodiante/local e cria evento | Confirmação expressa do destinatário antes da mudança. |
| SIM08 | Localização muda sem alterar custodiante | Evento de domínio independente LOCATION_CHANGE e trilha distinta de transferência. |
| SIM09 | Atualização de solicitação em rascunho gera sequência de auditoria crescente | Retificação formal após submissão/recebimento/ensaio, autorização, evidência e avaliação de impacto. |
| SIM10 | Versão obsoleta conflita e segundo recebimento para mesma solicitação retorna 409 | Idempotência por chave/conteúdo e concorrência real de aceite/amostra/transferência. |
| SIM11 | Perfil auditor não cria solicitação (403) | Isolamento entre unidades, escopo de solicitação, anexos e objetos. |
| SIM12 | Autor da decisão não pode aprovar sua própria revisão | Todas as combinações de papel/competência e exceção administrativa. |

### 12.2 Evidência de código versus evidência de execução

- **Código/serviço:** os arquivos listados existem na branch consultada e seus trechos foram lidos.
- **API:** rotas e dependências foram inspecionadas estaticamente; isso não prova comportamento runtime.
- **Teste escrito:** os testes SIM e de fases existem e contêm as asserções resumidas.
- **Teste executado:** não executado nesta rodada; nenhum resultado de pytest ou relatório CI foi obtido.
- **Homologação institucional:** não demonstrada por estes artefatos.
- **Conformidade:** parecer estático e limitado aos trechos citados; não equivale a decisão formal de Qualidade/Validação Institucional.

### 12.3 Prioridades de auditoria subsequente

1. **P0 — Aceite:** rastrear rota de criação de recebimento, serviço, decisão, checklist e aceite em uma sequência; definir e testar pré-condições e atomicidade.
2. **P0 — Custódia:** corrigir o contrato funcional de transferência, recusa, localização e não apresentação; desenhar testes negativos que afirmem os invariantes, não apenas os estados atuais do código.
3. **P0 — Segurança contextual:** percorrer todas as rotas de leitura/download e serviços, relacionando usuário, competência, unidade e vínculo com o recurso.
4. **P0 — Execução/resultado:** tornar explícito o vínculo LabTestResult → TestExecution → versão de método, com exceções formalmente governadas.
5. **P1 — Histórico:** preservar versões de checklist/respostas e retificações sem sobrescrever o registro anterior.
6. **P1 — Testes:** revisar SIM01–SIM12 para que cada um tenha asserções positivas e negativas alinhadas aos INV e CA correspondentes; depois executar suíte em ambiente controlado e registrar artefatos.

**Conclusão da v0.2:** foi possível ligar os principais fluxos de recebimento, conferência, decisão, checklist, custódia, aceite e execução a serviços, rotas e testes versionados. A auditoria confirma que parte dos testes valida o comportamento atualmente implementado, mas não os invariantes institucionais pretendidos. Não houve execução de testes nem alteração de código.

## 13. Auditoria de segurança — autorização contextual e isolamento

**Escopo:** leitura estática da branch main, limitada aos arquivos e trechos listados. A constatação de ausência de filtro nos trechos examinados não prova, por si só, exploração em produção; indica que o controle contextual não está demonstrado na camada examinada e precisa ser verificado transversalmente.

### 13.1 Controles positivos identificados

| Controle | Evidência de código | Parecer |
|---|---|---|
| Autenticação de usuário | backend/app/api/deps.py: get_current_user; CurrentUser | Rotas protegidas exigem usuário autenticado. |
| RBAC central | backend/app/core/rbac.py | Matriz de papéis/permissões centralizada; ADMIN possui wildcard; API usa require_roles em operações de escrita selecionadas. |
| Escopos M2M | backend/app/api/deps.py: require_scope | Há dependência para verificar escopos de contas SERVICE quando aplicada à rota. A existência da dependência não prova aplicação uniforme. |
| MFA | backend/app/models/user.py e backend/tests/test_phase6_mfa_totp.py | Modelo contém MFA e teste de ciclo setup/enable/disable e assinatura reforçada. Não prova MFA obrigatório para todos os perfis/operações. |
| Sessões | backend/app/models/user.py e auth_service.py | Refresh tokens rotativos, revogação e token_version; controles positivos de autenticação. |
| Auditoria de upload | backend/app/services/attachment_service.py:20-76 | Upload registra usuário, SHA-256 e evento de auditoria. |

### 13.2 Achados de autorização contextual

| ID | Superfície | Evidência observada | Lacuna/risco | Prioridade preliminar |
|---|---|---|---|---|
| SEC-01 | Listagem de solicitações | routes/solicitations.py:50-72 exige CurrentUser; solicitation_service.py:103-137 filtra somente status e texto, sem usuário/unidade/escopo | Usuário autenticado pode receber conjunto amplo de solicitações se não houver filtro em outra camada. Isolamento por laboratório/unidade não demonstrado. | P0 |
| SEC-02 | Detalhe de solicitação e recebimento | routes/solicitations.py:76-90 e :189-200; serviço get_solicitation busca pelo ID e get_receipt_by_solicitation pelo ID da solicitação | Controle é autenticação + conhecimento do identificador; não há verificação contextual de vínculo, unidade ou competência no trecho. | P0 |
| SEC-03 | Lista/detalhe de amostras | routes/samples.py:90-119 e :148-152; user autenticado é recebido, mas não encaminhado ao sample_service.list_samples/get_sample | Serviço não recebe ator nem contexto de autorização; escopo organizacional/contextual não demonstrado. | P0 |
| SEC-04 | Listagem e download de anexos | routes/attachments.py:54-75 exige CurrentUser; attachment_service.py:79-110 busca/lista por ID do anexo ou ensaio | Nenhum ator, unidade, vínculo de solicitação/ensaio ou permissão contextual é passado ao serviço. Anexo contém file_data e pode expor evidência bruta. | P0 |
| SEC-05 | Listagem de usuários | routes/users.py:18-31 exige CurrentUser; auth_service.py:378-389 lista todos os usuários ativos, com filtro opcional de papel | Usuário autenticado comum pode consultar diretório institucional amplo; avaliar minimização de dados, competência e necessidade operacional. | P1 |
| SEC-06 | Detalhe de usuário | routes/auth.py:286-290 exige CurrentUser, depois busca qualquer user_id | Não foi identificado no trecho controle para restringir consulta ao próprio perfil ou a ADMIN/gestor autorizado. Verificar campos efetivamente expostos pelo schema. | P1 |
| SEC-07 | Admin wildcard | core/rbac.py: ROLE_PERMISSIONS[ADMIN] = ["*"]; require_roles também admite ADMIN em várias rotas | Privilégio amplo é explícito. Não há evidência, nestes trechos, de separação entre administração técnica, gestão de contas e autoridade técnica/decisória de laboratório. | P1/P0 conforme atos governados |
| SEC-08 | Solicitante externo | models/solicitation.py:41-46 armazena nome/email/documento/organização e created_by_id obrigatório; criação usa WRITE_ROLES | Solicitante declarado não é identidade autenticada. Não foi encontrado portal/identidade externa neste fluxo. Não concluir que exista acesso externo indevido; requisito de acesso externo permanece não comprovado. | P1 |
| SEC-09 | Verificação/download público de laudos | routes/public_reports.py:20-55 não exige autenticação; busca por token ou hash e disponibiliza PDF | Exposição pública é intencional no desenho, mas requer decisão institucional sobre quais laudos podem ser publicados, escopo do PDF, revogação, expiração/entropia do token e proteção contra enumeração. | P0 para governança de publicação |
| SEC-10 | QR/consulta de amostra | routes/samples.py:107-145 valida token e retorna dados de amostra; exige CurrentUser | Autenticação existe, mas autorização contextual por laboratório/unidade/atribuição não aparece no trecho. Verificar também política de dados retornados. | P1 |

### 13.3 Modelo de identidade e escopo

O modelo User examinado contém username, email, nome, registro profissional, role, senha, estado ativo, MFA e dados de sessão. Não foi identificado no modelo examinado vínculo direto com unidade organizacional, laboratório, lotação, competência vigente ou escopo de dados.

O modelo Solicitation registra solicitante declarado e created_by_id (usuário interno que cadastrou). Essa separação é positiva e deve ser preservada. Não se deve converter requester_email ou requester_document em credencial ou autorização implícita.

A dependência require_scope existe para contas SERVICE; porém, a listagem de solicitações, amostras e anexos examinados usa CurrentUser sem encaminhar escopo ao serviço. O controle de escopo M2M não substitui autorização contextual de usuários humanos.

### 13.4 Testes existentes e lacunas de teste

| Arquivo de teste | Evidência que oferece | Lacuna em relação ao domínio |
|---|---|---|
| backend/tests/test_security.py | Hash de senha, política de senha, tokens, assinatura, QR assinado e serialização | Não testa isolamento por unidade, autorização por recurso, IDOR em solicitação/anexo/amostra ou privilégio mínimo. |
| backend/tests/test_phase6_mfa_totp.py | Setup/ativação/desativação MFA e MFA em assinatura quando habilitado | Não prova MFA obrigatório por perfil/ato, nem autorização contextual. |
| backend/tests/test_phase1_api.py | Fluxos HTTP de solicitação/recebimento/custódia | Não foi identificada, nos trechos examinados, matriz de dois usuários/unidades com tentativas cruzadas de leitura. |
| backend/tests/test_api_flow.py | Fluxos HTTP amplos com middleware, dependências e RBAC | A existência do arquivo não substitui casos negativos específicos de isolamento por unidade, recurso e vínculo. |
| backend/tests/test_phase8_service_clients_and_idempotency.py | Integrações de clientes de serviço e idempotência | Escopos de M2M não demonstram escopo de dados por laboratório nem isolamento entre usuários humanos. |

**Não houve execução dos testes nesta rodada.** A tabela descreve cobertura localizada por inspeção; não é relatório de execução.

### 13.5 Recomendações de validação/correção para etapa posterior

1. Definir formalmente o modelo de escopo: usuário, unidade/laboratório, competência, vínculo com solicitação/ensaio e exceções de acesso.
2. Centralizar autorização contextual no serviço/repositório ou política de domínio, sem depender apenas de filtros do frontend ou da rota.
3. Aplicar o mesmo predicado de autorização a listagem, detalhe, download, histórico, busca por código de barras, exportações e endpoints auxiliares.
4. Criar testes de isolamento com dois usuários e duas unidades: listar, consultar por UUID conhecido, baixar anexo, consultar amostra e histórico; todas as tentativas cruzadas devem ser negadas sem revelar existência de recurso.
5. Restringir diretório e detalhe de usuários conforme necessidade operacional e minimização de dados.
6. Formalizar matriz de privilégios ADMIN e separar administração técnica de decisão técnica, validação e assinatura.
7. Definir política de publicação pública de laudos: consentimento/base legal institucional aplicável, classificação, conteúdo publicável, token forte, revogação, retenção e trilha de consulta.
8. Definir se solicitantes externos terão portal próprio; até essa decisão, manter solicitante declarado separado do usuário autenticado.

### 13.6 Parecer de segurança

A implementação possui controles positivos de autenticação, RBAC, MFA, sessão e auditoria de upload. Entretanto, a leitura das rotas e serviços identificou ausência de demonstração de autorização contextual para solicitações, amostras e anexos, além de exposição pública deliberada de laudos que exige governança de publicação. O modelo User examinado não contém vínculo explícito de unidade/laboratório.

**Conclusão:** autorização por papel existe; isolamento contextual por recurso/unidade não está comprovado nos fluxos examinados. SEC-01 a SEC-04 são bloqueadores preliminares de segurança para uso institucional com dados reais até que o requisito seja esclarecido, implementado e testado. SEC-09 exige decisão institucional antes de considerar o endpoint público adequado.

**Limite:** parecer estático; não foi realizado teste de intrusão, execução automatizada, revisão completa de todos os endpoints ou avaliação de ambiente implantado. Não afirmar vulnerabilidade explorável em produção sem essas verificações.

## 14. Auditoria de integridade transacional, concorrência e idempotência

**Escopo:** inspeção estática dos serviços, modelos, rotas e testes na branch main. Nenhum teste foi executado nesta rodada. As conclusões distinguem restrições de banco, verificações de versão no serviço e testes que apenas simulam conflito sequencial.

### 14.1 Achados

| ID | Operação | Evidência estática | Parecer | Prioridade preliminar |
|---|---|---|---|---|
| TX-01 | Criação concorrente de recebimento | receipt_service.py:45-155 consulta Receipt existente e status da Solicitation, mas não bloqueia a solicitação com SELECT FOR UPDATE. Receipt.solicitation_id é UNIQUE (models/receipt.py:54-59). | A constraint impede dois recebimentos persistidos para a mesma solicitação; a corrida pode terminar em IntegrityError não convertido em conflito de domínio. Não há evidência de tratamento/retry idempotente para reenvio concorrente. | P0 |
| TX-02 | Aceite concorrente e geração de amostra | receipt_service.py:362-501 carrega CustodyObject sem FOR UPDATE; compara version em memória e cria DeviceSample. | A verificação version não é compare-and-swap SQL. Duas transações podem ler a mesma versão antes de gravar. CustodyObject.linked_device_sample_id é UNIQUE, mas DeviceSample.origin_custody_object_id não é UNIQUE; a restrição existente não demonstra exclusividade da origem no lado da amostra. Risco de amostras duplicadas por objeto. | P0 |
| TX-03 | Transferência concorrente de objeto de custódia novo | receipt_service.py:299-357 busca objeto sem FOR UPDATE, valida version em memória, altera custodiante/local e grava evento. | Não há bloqueio pessimista nem atualização condicional pela versão no trecho. Duas transferências concorrentes podem produzir eventos e estado final divergentes do fluxo pretendido. | P0 |
| TX-04 | Transferência de amostra no fluxo legado | custody_service.py:30-138 usa SELECT FOR UPDATE e valida version após adquirir o lock; grava evento, estado, assinatura e auditoria na mesma sessão/transação. | Controle significativamente mais robusto para concorrência do registro principal. Ainda requer teste concorrente real e avaliação de comportamento em falha/timeout de assinatura. | Parcial/positivo |
| TX-05 | Decisão técnica e revisão da coordenação | decision_service.py:28-84 cria decisão e altera ReceiptItem sem lock/validação de versão; :122-190 altera CoordinationReview sem FOR UPDATE e sem comparar versão. | Requisições concorrentes podem registrar decisões/revisões duplicadas ou sobrescrever estado. Não foi localizada constraint de unicidade que limite uma decisão vigente por objeto/etapa. | P0 |
| TX-06 | Idempotência de operações SEFI | idempotency_service.py:38-112 implementa chave e hash; instrument_data.py aplica replay em upload de dados de instrumento. | A idempotência está aplicada a integração/upload de instrumento, não aos comandos de recebimento, conferência, decisão, aceite ou transferência SEFI. | P0 |
| TX-07 | Corrida no registro da chave idempotente | idempotency_service.py:38-112 faz leitura antes de processar e grava a chave depois do efeito de negócio; não há reserva atômica/in-progress nem tratamento de conflito concorrente. | Duas requisições simultâneas com mesma chave podem ambas observar ausência e executar o efeito antes de tentar persistir a chave. A PK composta evita duas linhas, mas não garante que o efeito de negócio não tenha sido duplicado. | P0 |
| TX-08 | Atomicidade negócio + chave idempotente | instrument_data.py:93-116 chama serviço de ingestão, que persiste o dado, e depois record_idempotency(), que executa commit próprio. | Efeito de negócio e resposta idempotente não estão demonstrados na mesma transação atômica. Falha entre commits pode persistir importação sem cache da resposta; retry pode repetir operação. | P1 |
| TX-09 | Atomicidade de recebimento/aceite e auditoria | receipt_service.py e decision_service.py fazem flush, audit_service.append e commit ao final; audit_service.append usa advisory transaction lock no PostgreSQL. | Dentro da mesma AsyncSession, operação de negócio e evento de auditoria são agrupados na transação; é um controle positivo. Deve-se verificar comportamento de exceções e rollback integral nos testes de integração. | Parcial/positivo |
| TX-10 | Cadeia global de auditoria concorrente | audit_service.py:115-180 adquire pg_advisory_xact_lock antes de ler último hash/sequence; test_postgres_guards.py:141-150 contém teste concorrente com 8 eventos. | Controle explícito contra corrida na cadeia de auditoria; o teste está escrito, mas execução atual não foi comprovada nesta auditoria. O lock da cadeia não substitui lock/controle de versão das entidades de negócio. | Positivo, execução não comprovada |
| TX-11 | Numeração de identificadores | db/dialect.py:39-69 usa sequences nativas no PostgreSQL e UPSERT em contador SQLite; test_postgres_guards.py:129-138 testa monotonicidade. | Estratégia de geração centralizada. Sequences PostgreSQL podem apresentar lacunas em rollback; isso é comportamento esperado e não deve ser confundido com duplicidade. Não prova atomicidade do processo de negócio. | Positivo |
| TX-12 | Teste de concorrência SIM10 | test_phase1_simulations.py:603-635 testa versão obsoleta e duplicação sequencial de recebimento. | Testa conflito de versão e segundo POST após conclusão, mas não executa requisições simultâneas nem valida concorrência real no aceite, decisão ou transferência. | Lacuna |
| TX-13 | Teste de carga idempotente M2M | load_test_concurrency.py:165-190 dispara 30 GETs para integration-exports com uma chave compartilhada. | Não é teste de mutação idempotente nem comprova ausência de duplicidade; aceita respostas 200/403/404 como sucesso. | Lacuna |
| TX-14 | Teste de replay de upload instrumento | test_phase8_service_clients_and_idempotency.py:257-320 cobre reenvio sequencial igual e payload divergente. | Evidencia replay sequencial, não duas requisições concorrentes com a mesma chave, nem crash entre persistência do efeito e persistência da chave. | Parcial |

### 14.2 Pontos técnicos relevantes

**A. Restrições existentes que ajudam**
- Receipt.solicitation_id possui UNIQUE: impede dois registros de recebimento principal persistidos para a mesma solicitação.
- CustodyObject.linked_device_sample_id possui UNIQUE: limita repetição do mesmo ID de amostra nesse campo.
- DeviceSample.accession_number é UNIQUE.
- DeviceSample possui UNIQUE composto para serial, lote e fabricante.
- CoordinationReview.decision_id é UNIQUE.
- A cadeia de auditoria usa advisory lock transacional no PostgreSQL.
- Transferência legada de amostra usa SELECT FOR UPDATE.

Essas restrições são úteis, mas não substituem proteção de corrida nas operações de domínio.

**B. Controle otimista atual**
O OptimisticLockMixin apenas declara coluna version; a proteção depende de cada serviço comparar e atualizar corretamente. Nos fluxos de receipt_service.py e decision_service.py examinados, a comparação ocorre em memória após leitura sem bloqueio e a atualização não inclui a versão anterior no predicado SQL. Portanto, não há garantia de compare-and-swap uniforme.

**C. Sequência transacional crítica**
Para aceite SEFI, o efeito esperado deve permanecer indivisível: validar bloqueios e decisão → reservar/alterar objeto sob controle concorrente → criar uma única amostra vinculada à origem → registrar evento de custódia → registrar auditoria → persistir tudo. O serviço atual agrupa alterações e auditoria em uma sessão, mas a ausência de serialização/controle atômico por objeto deixa a corrida de aceite sem proteção suficiente.

**D. Idempotência de domínio**
Uma implementação robusta precisa reservar a chave por escopo e operação, associar hash canônico do comando, estado (em processamento/concluído/falhou recuperável), resultado persistido e prazo de retenção. A reserva, o efeito de domínio e o resultado devem ser coordenados transacionalmente; reuso com payload diferente deve resultar em conflito; concorrentes com mesma chave devem aguardar/reproduzir um único resultado. O contrato precisa diferenciar chave repetida, comando duplicado por regra de negócio e conflito de versão.

### 14.3 Recomendações para etapa de correção futura

1. Não corrigir isoladamente cada endpoint: criar padrão transacional de comando para recebimento, decisão, aceite e transferência.
2. Adquirir lock de linha (SELECT FOR UPDATE) ou aplicar compare-and-swap explícito (UPDATE WHERE id = :id AND version = :expected_version) para entidade agregada antes de validar e alterar estado.
3. Para aceite, garantir unicidade da origem no lado de DeviceSample.origin_custody_object_id e/ou constraint equivalente de domínio, além da serialização por objeto.
4. Tratar IntegrityError de constraints esperadas como conflito de domínio 409, com rollback e leitura do estado persistido; não mascarar falhas inesperadas.
5. Implementar idempotência para comandos SEFI críticos, com escopo por ator/cliente + operação + chave, hash canônico e persistência atômica do resultado.
6. Eliminar commits internos que separem efeito de negócio e chave idempotente; coordenar transação no limite do comando.
7. Adicionar testes concorrentes reais no PostgreSQL com sessões independentes e asyncio.gather: recebimento, aceite, transferência, decisão, revisão e reenvio de chave.
8. Validar invariantes pós-concorrência: um recebimento principal; no máximo uma amostra por objeto; um evento por transferência confirmada; um resultado por chave idempotente; sequência íntegra de auditoria.
9. Adicionar testes de falha induzida entre etapas e garantir rollback integral, incluindo auditoria e idempotência.
10. Manter SQLite para testes rápidos, mas exigir PostgreSQL para aprovação dos cenários de concorrência que dependem de locks, sequences e advisory locks.

### 14.4 Parecer

Há bons fundamentos implementados: constraints de unicidade, versionamento, sequences nativas, transações com auditoria e advisory lock para a cadeia de auditoria. O fluxo legado de transferência de amostra também utiliza lock pessimista.

Entretanto, os fluxos centrais novos de recebimento, aceite e transferência de objeto, bem como decisão/revisão, não demonstram proteção concorrente uniforme. A idempotência existente está concentrada na ingestão de instrumentos e não protege os comandos críticos do domínio SEFI. Os testes localizados são predominantemente sequenciais; o teste de carga compartilhando chave executa GET, não mutação.

**Conclusão:** integridade transacional parcial; concorrência de domínio não comprovada e com lacunas concretas nos serviços examinados. TX-01, TX-02, TX-03, TX-05, TX-06 e TX-07 são bloqueadores preliminares para operação institucional concorrente. TX-08 requer correção para garantir replay após falhas. O Gate G0 permanece NÃO APROVADO.

**Limite:** auditoria estática; não foram executados pytest, carga, testes concorrentes PostgreSQL, nem testes de falha induzida nesta rodada. A severidade é triagem técnica preliminar, não classificação institucional aprovada.


## 15. Auditoria de integridade do ciclo de vida e rastreabilidade ponta a ponta

**Escopo:** inspeção estática dos modelos, serviços, rotas e testes existentes na branch `main`, do vínculo Solicitação → Recebimento → Objeto de Custódia → Amostra → Ensaio → Execução → Resultado → Revisão → Laudo → Emenda. Foram examinados relacionamentos ORM, chaves estrangeiras e regras `ondelete` dos modelos selecionados. Nenhum código foi alterado e nenhum teste foi executado.

### 15.1 Mapa do ciclo efetivamente materializado

| Etapa | Vínculo encontrado | Evidência examinada | Limite |
|---|---|---|---|
| Solicitação → itens | `SolicitationItem.solicitation_id` FK; relacionamento `items` | `models/solicitation.py` | Itens podem ser excluídos em cascata enquanto não houver bloqueio referencial posterior; política de retenção deve ser explícita. |
| Solicitação → recebimento principal | `Receipt.solicitation_id` FK UNIQUE, NOT NULL, ON DELETE RESTRICT | `models/receipt.py` | Unicidade relacional positiva; não materializa por si só apresentações complementares D19. |
| Recebimento → item → objeto | `ReceiptItem.receipt_id`; `CustodyObject.receipt_item_id` | `models/receipt.py`, `receipt_service.py` | Vínculo estrutural existe; permanecem as lacunas já registradas sobre objeto criado antes da confirmação de apresentação e reconciliação de quantidades. |
| Objeto → amostra | `DeviceSample.origin_custody_object_id` e `CustodyObject.linked_device_sample_id` | `models/device_sample.py`, `models/receipt.py`, `receipt_service.py` | Há referências em ambos os sentidos, mas a FK de origem na amostra não é UNIQUE; risco concorrente já descrito em TX-02. |
| Amostra → ensaio | `LabTest.device_sample_id` FK NOT NULL, ON DELETE RESTRICT | `models/lab_test.py` | Vínculo direto e obrigatório. |
| Ensaio → execuções | `TestExecution.lab_test_id` FK ON DELETE CASCADE; relação ORM `executions` com `all, delete-orphan` | `models/test_execution.py`, `models/lab_test.py` | Tentativas são separadas e numeradas, mas o resultado assinado não aponta para uma execução específica. |
| Ensaio → resultados assinados | `LabTestResult.lab_test_id` FK ON DELETE RESTRICT; unicidade `(lab_test_id, version)` | `models/lab_test.py`, `test_service.py` | Histórico de versões do resultado existe; não há FK para `TestExecution`. |
| Ensaio → revisões | `TestReview.lab_test_id` FK ON DELETE CASCADE; unicidade `(lab_test_id, review_number)` | `models/test_review.py`, `models/lab_test.py` | Revisão não fixa a versão do resultado que foi analisada. |
| Ensaio → anexos | `TestAttachment.lab_test_id` FK ON DELETE CASCADE; `execution_id` opcional ON DELETE SET NULL | `models/test_attachment.py`, `attachment_service.py` | Serviço de upload examinado recebe apenas `test_id` e não preenche `execution_id`; anexo não fica associado a uma tentativa específica. |
| Amostra/ensaios → laudo | `OfficialReport.device_sample_id` FK NOT NULL; `solicitation_id` opcional | `models/official_report.py`, `report_service.py` | Laudo aponta para amostra e manifesto, mas a emissão inicial não preenche `solicitation_id`, embora a amostra tenha esse vínculo. |
| Laudo → emendas | `root_report_id` e `supersedes_id` autorreferenciais; versão, hash, assinatura e PDF próprios | `models/official_report.py`, `report_service.py` | Cadeia de versões é materializada; a emenda reaproveita o manifesto anterior, sem reconstruir a base técnica atual. |
| Atos → auditoria | `AuditLog.entity_type/entity_id` polimórficos, sem FK para a entidade auditada | `models/audit_log.py`, `audit_service.py` | A trilha é encadeada e protegida por hash/HMAC/guards PostgreSQL; integridade referencial direta com cada entidade não existe por desenho polimórfico. |

### 15.2 Achados de ciclo de vida

| ID | Achado | Evidência estática | Impacto na rastreabilidade | Parecer / prioridade preliminar |
|---|---|---|---|---|
| ACH-42 | Resultado assinado pode ser criado sem execução de bancada vinculada | `test_service.record_result()` cria `LabTestResult` usando somente `lab_test_id`; `TestExecution` não é consultada. O helper de `test_phase3_reviews.py` conclui o ensaio via `PATCH /tests/{id}/result` sem criar execução. | Não é possível demonstrar, a partir do resultado assinado, qual tentativa, leituras brutas, condições ambientais e equipamento o sustentam. | Lacuna concreta; P0 preliminar para rastreabilidade do resultado. |
| ACH-43 | Conclusão de execução e resultado assinado são dois fluxos sem associação transacional/relacional | `execution_service.complete_execution()` conclui `TestExecution`, registra auditoria e evento outbox `test.completed`; não cria nem vincula `LabTestResult`. O caminho de resultado é separado em `test_service.record_result()`. | O evento de execução concluída não é prova de que o resultado foi revisado/assinado; o resultado assinado também não prova qual execução foi usada. | Lacuna estrutural; P0 preliminar. |
| ACH-44 | Revisão técnica não identifica a versão exata do resultado revisado | `TestReview` contém `lab_test_id`, status, revisor, data, justificativa e assinatura opcional, mas não `result_version_id`/versão. `record_test_review()` consulta o estado corrente do `LabTest`; o token de assinatura é opcional no serviço e na rota. | Após retificação do resultado, a trilha não demonstra de forma inequívoca qual versão foi objeto de cada parecer anterior. | Lacuna concreta; P0/P1 preliminar conforme política institucional de assinatura. |
| ACH-45 | Manifesto do laudo não fixa execução, versão assinada, revisão, método e condição metrológica histórica | `generate_official_report()` monta o manifesto a partir dos campos correntes de `LabTest` (resultado, limites, analista e data) e do orçamento de incerteza mais recente. Não inclui ID/versão de `TestExecution`, ID/versão de `LabTestResult`, ID da revisão, versão do método ou snapshot histórico da situação metrológica do equipamento. | Hash comprova integridade do PDF gerado, mas não supre a ausência de referências técnicas versionadas que permitam reconstruir a origem do resultado. | Lacuna de snapshot/rastreabilidade; P0 preliminar para fechamento documental do laudo. |
| ACH-46 | Laudo emitido não recebe o vínculo da solicitação de origem na emissão inicial | `OfficialReport.solicitation_id` é nullable; o construtor em `generate_official_report()` preenche `device_sample_id`, mas não atribui `solicitation_id`, embora `DeviceSample.solicitation_id` exista. A rotina de emenda apenas replica `prev_report.solicitation_id`. | A consulta do laudo pode não percorrer diretamente a cadeia Laudo → Solicitação; depende de navegar pela amostra e o vínculo direto permanece nulo. | Lacuna de vínculo; P1 preliminar. |
| ACH-47 | Emenda de laudo preserva manifesto anterior, mas não avalia impacto de alterações posteriores no resultado | `amend_official_report()` lê `prev_report.attributes['manifest']`, copia os ensaios desse manifesto e altera campos documentais (razão, conclusão/resumo/título); não reconsulta versões atuais de `LabTestResult`, execuções ou revisões, nem registra avaliação de impacto sobre resultados posteriores. | Uma emenda pode manter a fotografia técnica anterior mesmo quando o resultado do ensaio foi retificado depois da emissão original; não há demonstração de reconciliação ou justificativa de não impacto. | Lacuna concreta; P0 preliminar quando houver retificação técnica posterior. |
| ACH-48 | Anexos não são associados a uma tentativa de execução pelo fluxo de upload examinado | `TestAttachment.execution_id` é opcional; `upload_attachment()` recebe `test_id` e grava `lab_test_id`, deixando `execution_id` nulo. | Curvas, fotos e arquivos brutos podem ficar associados apenas ao ensaio geral, sem identificar a tentativa a que pertencem, especialmente quando há repetição/interrupção. | Lacuna concreta; P1 preliminar. |
| ACH-49 | Exclusão em cascata pode remover registros históricos subordinados antes de haver resultado assinado que bloqueie a exclusão | `Solicitation.items`, `Receipt.items`, `ReceiptItem.custody_objects`, `CustodyObject.custody_events` e `LabTest.executions/reviews/attachments` possuem cascades ORM/delete-orphan; várias FKs usam ON DELETE CASCADE. `LabTestResult.lab_test_id` usa RESTRICT e protege ensaios que já tenham resultado assinado. | A proteção é desigual por etapa: execuções, revisões e anexos podem estar sujeitos à exclusão pelo pai em cenários sem resultado assinado. A leitura estática não demonstra se rotas de exclusão estão expostas ou se há bloqueios adicionais. | Risco de retenção a validar; P1 preliminar, não declarar exclusão explorável sem auditar todos os comandos/rotas. |

### 15.3 Cobertura de testes localizada — sem execução

| Arquivo/caso | O que demonstra por inspeção | O que não demonstra |
|---|---|---|
| `backend/tests/test_phase2_executions.py` | Início, bloqueio de segunda tentativa em andamento, leituras, interrupção e repetição de execução. | Associação obrigatória entre execução concluída e resultado assinado; concorrência real; vínculo de anexos à tentativa. |
| `backend/tests/test_phase3_reviews.py` | Revisão por pares, bloqueio de auto-revisão em cenário coberto, histórico de revisões, emissão de laudo e anexo; helper de conclusão usa endpoint direto de resultado. | Fixação da versão do resultado revisado; assinatura obrigatória em todas as decisões; execução formal como pré-requisito do resultado/laudo. |
| `backend/tests/test_phase6_report_amendments.py` | PDF binário, hash, versionamento V1/V2, supersedes/root e justificativa de emenda. | Impacto de resultado retificado após laudo; manifesto técnico versionado; vínculo direto com solicitação e execução. |
| `backend/tests/test_phase1_api.py` e `test_phase1_simulations.py` | Fluxos de recebimento/aceite e cenários de custódia já descritos nas seções anteriores. | Reconciliação ponta a ponta de IDs, retenção e não órfãos após exclusões/retificações. |

**Não houve execução de pytest, testes de integração, testes de exclusão, testes de concorrência ou testes de falha nesta etapa.** A cobertura acima é leitura estática dos casos existentes.

### 15.4 Relação com decisões e invariantes M0.3

| Decisão/invariante | Relação com os achados | Situação |
|---|---|---|
| D09 / INV-26 | ACH-44 e ACH-47: preservar versão original, motivo, autorização, evidência e impacto em retificações; o histórico de resultado e de laudo existe, mas a ligação entre versões e avaliação de impacto não está completa. | Parcial; validação institucional e evidência adicional necessárias. |
| D13 / INV-31 | ACH-48 e ACH-49: evidência deve ter vínculo contextual e histórico preservado; cascades e anexos sem tentativa específica precisam ser avaliados. | Parcial/não comprovado. |
| D14 / INV-31 | ACH-42 a ACH-49: eventos de execução, resultado, revisão, emissão e emenda devem permitir reconstrução cronológica com ator, alvo e evidência. | Parcial; trilha genérica existe, mas os vínculos entre objetos de domínio são incompletos. |
| D16 / INV-19 e INV-31 | ACH-44: parecer e assinatura precisam apontar para o conteúdo/versão efetivamente revisados; assinatura opcional no fluxo examinado não prova política uniforme. | Parcial; decisão de política de assinatura pendente. |
| D18 / INV-27 e INV-28 | ACH-46: manter identificadores distintos e percorrer a origem Solicitação → Amostra → Ensaio → Laudo sem depender de associação presumida. | Parcial; vínculo via amostra existe, vínculo direto do laudo não é preenchido. |
| D20 / INV-21 a INV-24 | ACH-42 e ACH-43: resultado e laudo devem derivar de amostra operacional validamente aceita, com linhagem técnica das execuções. | Parcial; cadeia de recebimento/amostra existe, mas linhagem execução→resultado não. |

A relação com CA01–CA37 e SIM01–SIM12 permanece a já consolidada nas seções 3 e 5. **Não foi criada equivalência automática entre estes novos achados e critérios/cenários**: a validação requisito-a-requisito depende da leitura integral dos textos normativos e da confirmação institucional, especialmente para os cenários de retificação (SIM09), execução/resultado e emissão do laudo.

### 15.5 Parecer de integridade ponta a ponta

A arquitetura possui vínculos úteis e componentes de preservação: solicitação e itens declarados, recebimento principal único, objetos de custódia, amostra com referência ao objeto de origem, ensaios vinculados à amostra, tentativas numeradas, resultados assinados versionados, revisões históricas, PDFs com hash e emendas encadeadas, além de trilha de auditoria com hash/HMAC e guards PostgreSQL.

Entretanto, a cadeia não é plenamente reconstruível em nível de evidência técnica: resultado assinado não referencia execução; execução concluída não gera/vincula resultado; revisão não fixa a versão revisada; anexo não aponta para tentativa; manifesto do laudo não captura as referências históricas necessárias; a emissão inicial não preenche o vínculo direto da solicitação; e a emenda não reavalia alterações técnicas posteriores.

**Conclusão:** rastreabilidade ponta a ponta parcial. ACH-42, ACH-43, ACH-44, ACH-45 e ACH-47 são bloqueadores técnicos preliminares para afirmar reconstrução completa do ciclo resultado–revisão–laudo. ACH-46 e ACH-48 são lacunas de vínculo relevantes. ACH-49 exige auditoria específica de rotas de exclusão e política de retenção antes de classificar risco efetivo. O Gate G0 permanece NÃO APROVADO e a implementação permanece NÃO AUTORIZADA.

**Limites desta etapa:** inspeção estática dos arquivos e trechos indicados; não foi feita execução de testes, teste de intrusão, inspeção de banco implantado, validação de retenção institucional nem confirmação de todos os endpoints de exclusão. Prioridades P0/P1 são triagem técnica preliminar, não severidade institucional aprovada.


## 16. Auditoria de integridade do banco de dados e migrações

**Escopo:** inspeção estática da cadeia Alembic, dos scripts SQL executados pelo modo de inicialização automática, dos modelos SQLAlchemy e dos testes PostgreSQL. HEAD consultado: `fe209a713bed6cd267c15e5390ff41b0d3c9084e` (`main`). Não houve conexão a banco implantado, execução de migrações, `alembic check`, inspeção de schema real ou execução de testes nesta etapa.

### 16.1 Arquitetura de persistência e fontes de DDL

| Componente | Evidência | Constatação |
|---|---|---|
| Metadados ORM | `backend/app/models/base.py`; `backend/alembic/env.py` | Alembic usa `Base.metadata`, compara tipos e defaults de servidor (`compare_type=True`, `compare_server_default=True`). |
| Caminho de produção | `backend/app/db/database.py:init_db()` | Com `AUTO_CREATE_SCHEMA=false`, startup não cria schema nem aplica SQL; comentário operacional indica `alembic upgrade head` antes da API. |
| Caminho automático de desenvolvimento/teste | `database.py:init_db()`, `app/db/sql/001_immutability.sql`, `002_indexes.sql`, `003_integridade_fase5.sql` | Executa `Base.metadata.create_all` e scripts SQL específicos de PostgreSQL; SQLite não recebe triggers/sequences PL/pgSQL. |
| Histórico versionado | `backend/alembic/versions/a1cd5ac5805f_schema_inicial.py` e revisões `0002` a `0022` | Há cadeia incremental, com snapshots de guardas e revisões posteriores que atualizam funções/triggers. |
| Paridade do schema | `backend/tests/test_migrations_postgres.py::test_upgrade_head_creates_schema_without_drift` | O teste prevê `alembic check` após upgrade em PostgreSQL descartável; o código do teste não prova que foi executado no ambiente atual. |

A coexistência de dois caminhos de DDL (Alembic em produção e `create_all` + SQL no modo automático) é intencional segundo os comentários do projeto, mas cria duas superfícies que precisam permanecer sincronizadas. A inspeção identificou funções de guarda replicadas em snapshots Alembic e scripts SQL; a paridade nominal de triggers é parcialmente testada, mas não substitui comparação semântica dos corpos das funções.

### 16.2 Proteções e integridade identificadas

| Área | Proteção encontrada | Limite da comprovação |
|---|---|---|
| Chaves e cardinalidades | PKs UUID, FKs, UNIQUEs e índices nos modelos e migrações; exemplo: um recebimento principal por solicitação (`receipts.solicitation_id UNIQUE`). | Não houve introspecção de banco implantado nem verificação real de constraints em produção. |
| Registros de auditoria | Trigger append-only para UPDATE/DELETE e bloqueio de TRUNCATE; teste dedicado tenta as três operações e verifica a cadeia. | Teste escrito, não executado nesta auditoria. |
| Resultados assinados | Trigger append-only em `lab_test_results`; assinatura eletrônica com guarda de manifesto e consumo write-once. | Cobertura comportamental localizada não prova todas as combinações de UPDATE/DELETE nem permissões do papel de banco. |
| Execuções e revisões | Trigger de congelamento após estados terminais; delete é bloqueado pela função. | Há divergência concreta no conjunto de estados terminais da revisão, detalhada em ACH-50. |
| Laudos oficiais | Trigger no-delete/write-once; migração 0013 acrescenta proteção de versionamento e migração 0022 acrescenta `attributes`. | O downgrade 0022 não restaura integralmente a proteção da revisão 0013 (ACH-51). |
| Registros de recebimento/custódia | Triggers no-delete em solicitações, itens, recebimentos, objetos, decisões e revisões de coordenação; eventos de custódia append-only. | Teste de paridade verifica nomes dos triggers, mas não testa semanticamente cada um. |
| Numeração e auditoria concorrente | Sequences PostgreSQL e advisory lock na cadeia de auditoria; testes específicos existem. | Testes não executados nesta etapa; sequences não substituem idempotência/concorrência dos comandos de domínio (ver TX-01 a TX-14). |
| Dados legados | Migrações aditivas; teste cria amostra pré-Fase 1 e verifica preservação após upgrade/downgrade. | Cenário cobre amostra legada simples; não demonstra reconciliação de toda a cadeia histórica ou dos anexos/laudos associados. |

### 16.3 Achados novos de banco/migração

| ID | Achado | Evidência | Impacto | Parecer / prioridade preliminar |
|---|---|---|---|---|
| ACH-50 | Estado `DEVOLVIDO` não está incluído na lista de congelamento de revisões técnicas | `CoordinationReviewStatus` em `models/enums.py` define `PENDENTE`, `APROVADO`, `DEVOLVIDO`, `REJEITADO`. A migração `0011_fase5_guards_integridade.py` cria `trg_test_reviews_freeze` com argumentos `{APROVADO,REJEITADO,RESSALVAS}`; o script `003_integridade_fase5.sql` replica a mesma lista. | Uma revisão cujo status anterior seja `DEVOLVIDO` não satisfaz a condição de congelamento por estado terminal. UPDATE direto pode alterar registro devolvido, embora DELETE continue bloqueado pela função. | Divergência código/DDL confirmada; P1 preliminar. Confirmar a semântica institucional de terminalidade de DEVOLVIDO antes de definir correção. |
| ACH-51 | Downgrade da migração 0022 enfraquece a guarda de laudos introduzida em 0013 | `0022_official_reports_attributes_immutable.py::downgrade()` recria `lims_official_reports_guard()` sem as comparações de `version`, `root_report_id`, `supersedes_id` e `amendment_reason`, que estavam protegidas desde `0013_fase6_laudos_emendas.py`. | Um rollback somente de 0022 para 0021 mantém 0013 aplicada, mas substitui sua função por uma versão que deixa esses campos fora da proteção; pode permitir mutação direta desses metadados no banco. | Defeito de reversão DDL demonstrável por leitura; P1 preliminar. O teste de downgrade integral até PRE_PHASE1 não cobre o rollback isolado 0022→0021. |
| ACH-52 | Guarda de laudos permite desativar o indicador `is_latest` sem exigir sucessor na mesma operação | A função criada em `0013` impede reativar `is_latest=false` para `true`, mas permite a transição `true→false`; a aplicação usa essa transição ao emitir emenda, porém o trigger não exige que exista versão sucessora vinculada. | Uma atualização direta pode deixar uma família de laudos sem versão vigente, se não houver controle transacional de serviço/rotina que a acompanhe. | Lacuna de integridade referencial/estado no nível DDL; P1 preliminar. Não foi demonstrado que uma rota pública permita essa mutação isolada. |

### 16.4 Cobertura dos testes de migração e guardas — leitura estática

| Teste | Cobertura declarada no código | Limitação |
|---|---|---|
| `test_upgrade_head_creates_schema_without_drift` | Upgrade completo em banco PostgreSQL descartável; presença de tabelas/enums; trigger de auditoria; `alembic current`; `alembic check`. | Não foi executado nesta auditoria; verificação nominal de um trigger não garante comportamento de todas as guardas. |
| `test_downgrade_is_reversible` | Downgrade de head para `0003_audit_export`, preservação de tabelas legadas e reaplicação de head. | Não cobre downgrade individual de cada revisão, em especial `0022→0021`. |
| `test_additive_migration_preserves_legacy_rows` | Preserva uma amostra legada com série/lote durante upgrade e downgrade. | Não cobre todos os tipos de registros, relações e evidências legadas. |
| `test_downgrade_refuses_when_it_would_lose_data` | Impede downgrade que descartaria amostra legada sem série/lote e verifica falha sem reversão parcial. | Cenário de perda coberto é específico; não constitui prova de ausência de perda para todos os dados e revisões. |
| `test_trigger_parity_phase5` | Compara nomes esperados de 23 triggers no schema de teste. | Não compara corpo das funções, argumentos de triggers ou comportamento de cada regra. |
| Demais testes de `test_postgres_guards.py` | Exercitam append-only da auditoria, imutabilidade de assinatura, sequences, advisory lock e isolamento da busca de triggers por schema. | Não há, nos trechos examinados, teste comportamental específico para a lista de estados de `trg_test_reviews_freeze`, rollback isolado da revisão 0022 ou consistência de `is_latest` com sucessor. |

**Condição de execução:** `test_migrations_postgres.py` e `test_postgres_guards.py` usam `pytest.mark.skipif` quando `LIMS_TEST_DATABASE_URL` não está definido; exigem PostgreSQL real e, para migrações, usuário capaz de criar bancos. Não foi consultado o resultado de uma execução CI nesta etapa. Portanto, a existência desses testes não será apresentada como aprovação operacional.

### 16.5 Parecer e implicações para o Gate G0

A estrutura de banco apresenta uma base relevante de integridade: migrações versionadas, constraints relacionais, guardas PostgreSQL, append-only seletivo, no-delete de registros regulados, sequences, testes de upgrade/downgrade e verificação prevista de drift entre metadata e migrações.

Ainda assim, a auditoria identificou três pontos que impedem considerar a camada DDL integralmente fechada: divergência do estado terminal `DEVOLVIDO` na guarda de revisões; downgrade isolado de 0022 que remove proteções de campos introduzidas em 0013; e ausência de garantia DDL de que um laudo marcado como superado tenha sucessor correspondente.

**Conclusão:** integridade do banco/migrações parcialmente demonstrada por desenho e testes escritos; execução atual, paridade de ambiente implantado e cobertura semântica completa das guardas não comprovadas. ACH-50 a ACH-52 devem ser incorporados ao plano de saneamento técnico e à rastreabilidade G0, após confirmação das regras institucionais aplicáveis.

**Gate G0 permanece NÃO APROVADO. Implementação permanece NÃO AUTORIZADA.** Nenhuma migração, script SQL, modelo, trigger ou teste foi alterado nesta atividade.


## 17. Auditoria de implantação, configuração, CI e recuperação operacional

**Escopo:** inspeção estática dos arquivos de configuração e implantação e consulta dos resultados reais mais recentes do GitHub Actions. Branch `main`, commit auditado `bf6ec23c2ed14795d25b5b081296f6c4a7bbbb60`. Foram consultados workflow `CI`, jobs e logs da execução associada ao commit. Não houve deploy, acesso a ambiente institucional, rotação de segredos, execução manual de backup/restauração ou alteração de infraestrutura.

### 17.1 Configuração e inicialização

| Área | Evidência | Constatação | Limite |
|---|---|---|---|
| Segredos de exemplo | `.env.example`, `backend/.env.example` | Os arquivos de exemplo contêm credenciais PostgreSQL e chaves JWT/HMAC/QR/MFA com valores explícitos de desenvolvimento. | São exemplos, não prova de segredo real implantado. |
| Defaults no Compose | `docker-compose.yml` | Variáveis críticas usam fallback para valores `dev-insecure-...`; PostgreSQL também usa usuário/senha padrão `lims`. | Em `ENVIRONMENT=prod`, o validator rejeita três chaves padrão (JWT, auditoria e QR), mas não se deve depender de falha tardia para governar configuração. |
| Validação de produção | `backend/app/core/config.py` | Bloqueia segredos padrão JWT/AUDIT/QR e DEBUG em produção; força docs/OpenAPI desligadas via propriedade `docs_enabled`. | TOTP_ENCRYPTION_KEY não participa dessa validação; política de obrigatoriedade e armazenamento de todos os segredos não comprovada. |
| Migração antes da API | `docker-compose.yml` | Serviço `migrate` executa `alembic upgrade head`; API depende de `service_completed_successfully`; `AUTO_CREATE_SCHEMA=false`. | Bom desenho fail-before-start; depende de migrações concluírem sem erro, o que falha atualmente no CI. |
| Falha de banco no startup | `backend/app/main.py::lifespan` | Exceção em `init_db()` é capturada e logada; processo da API segue para `yield`, enquanto `/health` retorna `degraded` se banco estiver indisponível. | Em Compose, a dependência migrate reduz o risco; fora dele, API pode iniciar sem banco. Não há prova de política operacional de readiness/retentativa. |
| Portas e rede | `docker-compose.yml` | DB e API publicam portas no host por padrão, além do frontend; não há redes internas segregadas explicitamente no arquivo. | Exposição efetiva depende do host/firewall; não se conclui exposição pública sem ambiente real. |

### 17.2 Evidência real de GitHub Actions

A execução mais recente consultada para o commit `bf6ec23c2ed14795d25b5b081296f6c4a7bbbb60` foi concluída com **failure**. O workflow é disparado em push para qualquer branch e pull request, incluindo alterações somente em documentação.

| Job | Resultado observado | Evidência no log |
|---|---|---|
| Backend (lint, tipos e testes) | **Falha** em `alembic upgrade head`; lint e mypy passaram; paridade e testes foram pulados. | PostgreSQL rejeitou atualização de `alembic_version.version_num`: valor `0022_official_reports_attributes_immutable` excede `varchar(32)`. |
| Front-end (typecheck e build) | **Falha** na instalação; typecheck/build pulados. | `npm ci` informa `package.json` e `package-lock.json` fora de sincronia; faltam `@playwright/test@1.65.1`, `playwright@1.65.1` e `playwright-core@1.65.1` no lockfile. |
| Docker (imagens e smoke test) | **Falha** no build da imagem web; stack e smoke test pulados. | Mesmo erro de sincronização package/lockfile no `npm ci` do Dockerfile frontend. |
| Segurança (SAST/SCA) | **Sucesso**. | Bandit e pip-audit concluíram sem erro no job consultado. |

Execução: `https://github.com/keyzermoura/LIMS/actions/runs/44972207054`.

**ACH-53 — Identificador de revisão Alembic excede a coluna padrão de versão.** A tabela `alembic_version.version_num` foi criada com largura 32 (padrão Alembic), mas a revisão `0022_official_reports_attributes_immutable` tem identificador maior. O upgrade falha ao atualizar a versão corrente; impede migração limpa e bloqueia a sequência CI antes de `alembic check` e testes. Evidência: log do job Backend acima. Prioridade preliminar P0 — bloqueador operacional demonstrado.

**ACH-54 — package-lock.json não acompanha dependências declaradas.** `npm ci` falha porque três pacotes Playwright declarados no package.json não estão no lockfile. O mesmo defeito bloqueia o job frontend e o build Docker; smoke test não é alcançado. Evidência: logs dos jobs Front-end e Docker acima. Prioridade preliminar P0 — bloqueador de build/deploy demonstrado.

### 17.3 Backup, WAL e restauração

Inspecionado `scripts/backup_restore_pitr.sh`.

**ACH-55 — Script de backup não comprova PITR nem restauração íntegra e pode reportar sucesso falso.**

- Executa `pg_dump -Fc` e gera SHA-256 do arquivo: evidência positiva de backup lógico e checksum.
- Cria diretório `wal_archive`, mas não configura nem verifica `archive_mode`, `archive_command`, retenção de WAL, continuidade de segmentos ou base backup; a criação do diretório não implementa arquivamento WAL/PITR.
- A verificação de `pg_waldump` limita-se a testar existência do utilitário.
- `createdb ... || true`, `pg_restore ... || true` e `dropdb ... || true` suprimem falhas.
- Após `pg_restore` falhar, o script continua, consulta contagens e imprime “restauração validada 100% com sucesso” sem comparar com origem, validar constraints, migrações, hashes de laudos, cadeia de auditoria ou amostras de controle.
- Não foi encontrada, nos arquivos operacionais examinados, agenda/scheduler que execute backup em periodicidade definida, nem evidência de cópia externa/imutável e teste de restauração independente.

Parecer: há um esqueleto de backup lógico, mas PITR, restauração confiável, monitoramento e política de retenção não estão demonstrados. P0/P1 preliminar conforme RPO/RTO institucional; requer decisão e validação de infraestrutura.

### 17.4 Achados adicionais de configuração

**ACH-56 — Segredos de desenvolvimento são usados como fallback pelo Compose.** Os defaults estão identificados como inseguros e o validator de produção bloqueia JWT/AUDIT/QR padrão, o que é controle positivo. Ainda assim, Compose aceita implicitamente credenciais de banco e chaves padrão se variáveis forem omitidas; a inicialização pode falhar (fail-closed para três chaves), mas a configuração não impede erro operacional de implantação nem garante TOTP key forte. Recomenda-se exigir arquivo de ambiente/secrets manager e validar todas as chaves obrigatórias no perfil de produção. P1 preliminar.

**ACH-57 — Inicialização da API absorve falha de conexão/DDL e continua processo.** `lifespan` captura exceção de `init_db()` e prossegue. Health reporta `degraded`, o que permite detecção, mas o processo aceita inicialização. Em deploys fora do Compose ou com orquestrador que não respeite readiness, pode haver instância sem persistência pronta. P1 preliminar; avaliar estratégia fail-fast/readiness conforme plataforma.

### 17.5 Parecer de prontidão operacional

O projeto tem pipeline CI abrangente em intenção: lint, tipagem, migrações, drift, testes SQLite/PostgreSQL, SAST/SCA, build Docker e smoke test. A execução consultada, entretanto, prova que a pipeline **não está verde**: migração PostgreSQL e instalação frontend falham, e testes de banco/smoke não chegam a executar. O job de segurança concluiu com sucesso nessa execução.

A existência de workflow e scripts não comprova deploy institucional, agendamento de backup, retenção, PITR ou recuperação testada. O script atual de backup contém supressão explícita de erros, de modo que sua mensagem final não deve ser tratada como evidência de restauração bem-sucedida.

**Conclusão:** ambiente operacional NÃO demonstrado como pronto. ACH-53 e ACH-54 são bloqueadores objetivos de CI/build; ACH-55 bloqueia a aceitação da alegação de PITR/restauração; ACH-56 e ACH-57 exigem endurecimento e validação de operação. Gate G0 permanece NÃO APROVADO e implementação SEFI permanece NÃO AUTORIZADA.

**Limites:** a consulta do Actions cobre a execução vinculada ao commit auditado e seus jobs/logs; não substitui inventário de todos os ambientes, configuração real de secrets, branch protection, firewall, storage, scheduler, RPO/RTO ou evidência de backup institucional. Nenhuma correção foi aplicada.


## 18. Governança, qualidade e evidências do Gate G0 — 2026-11-22

Foi criada a matriz complementar `docs/MATRIZ_EVIDENCIAS_GOVERNANCA_QUALIDADE_G0.md` v1.0, que organiza a hierarquia E0–E6 e a rastreabilidade D01–D20, G0-P01–P30, CA01–CA37, SIM01–SIM12, evidências CI e pacotes GOV-01–GOV-20.

### 18.1 Resultado consolidado

- D01–D20: ratificadas integralmente em 2026-11-10; não equivalem a homologação ou autorização.
- G0-P01–P30: 30 diretrizes aprovadas em seis blocos; entregáveis, parâmetros e evidências permanecem condicionados conforme os registros.
- CA01–CA37: distribuição auditada registrada na Matriz de Prontidão v0.4: 0 integralmente comprovados, 17 parciais, 13 não conformes e 7 não comprovados.
- SIM01–SIM12: testes versionados parcialmente; execução atual e homologação operacional não comprovadas.
- CI no commit `47133479685a9f1bbfbd12aa508cc46eaa3e913f`, run `44972383967`: Backend falhou na migração, Frontend falhou na instalação, Docker falhou no build; SAST/SCA passou. Smoke test e testes posteriores não foram alcançados.
- GOV-01: rótulos GREEN históricos da tabela SIM foram ajustados em VALIDACAO_CENARIOS_OPERACIONAIS_SEFI.md v2.2 para evitar interpretação como resultado vigente.

### 18.2 Novo achado documental

**GOV-01 — Rótulos históricos GREEN mantidos na tabela SIM após suspensão da conclusão.** A tabela histórica da seção 5 do documento SIM v2.1 mantinha “APROVADO (GREEN)” em SIM02–SIM12, embora a seção 7.3 suspendesse a conclusão e declarasse a execução atual não revalidada. A coexistência poderia induzir leitura seletiva. Ação documental realizada: atualização para v2.2, preservando a declaração histórica da v2.0 e identificando-a como não revalidada no commit atual. Este achado não é defeito de código nem evidência de falha dos testes; é risco de governança documental.

### 18.3 Parecer

A baseline institucional está ratificada, mas a comprovação dos entregáveis, a execução válida de CA/SIM e a homologação operacional continuam incompletas. O novo documento de governança complementa, mas não substitui, a Matriz de Prontidão G0 e as evidências técnicas individuais.

**GATE G0: NÃO APROVADO. IMPLEMENTAÇÃO SEFI: NÃO AUTORIZADA.**


| 0.8 | 2026-11-22 | Integração da auditoria de governança, qualidade e evidências G0; referência à matriz complementar e correção documental dos rótulos históricos SIM. |
