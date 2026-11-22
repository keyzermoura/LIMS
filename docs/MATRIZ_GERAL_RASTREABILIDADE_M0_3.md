# Matriz Geral de Rastreabilidade M0.3 — LIMS-SEFI

**Identificador:** MAT-RAST-M03-001  
**Versão:** 0.4  
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
