# Matriz Geral de Rastreabilidade M0.3 — LIMS-SEFI

**Identificador:** MAT-RAST-M03-001  
**Versão:** 0.1  
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