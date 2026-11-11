# Matriz Inicial de Rastreabilidade — D01 a D20

**Identificador:** MAT-TRC-SEFI-D01-D20-001  
**Versão:** 0.3  
**Data:** 2026-11-11  
**Branch:** `docs/integracao-especificacao-sefi`  
**Fontes principais:** DEC-SEFI-001 v1.7; MOD-DOM-001 (M0.2) v0.7; EST-REC-001 v1.7; MOD-LOG-SEFI-003 (M0.3) v0.1; MAT-G0-SEFI-001 v0.3.  
**Natureza:** rastreabilidade documental inicial; não é validação funcional, homologação ou aprovação de implementação.

## 1. Objetivo e limites

Relacionar cada decisão ratificada D01–D20 aos elementos lógicos propostos em M0.3, para orientar a especificação integrada. A matriz distingue:
- **decisão ratificada:** conteúdo da baseline D01–D20;
- **materialização lógica:** entidade, estado, evento ou invariante proposto no M0.3;
- **rastreabilidade de teste:** associação a CA01–CA37 e SIM01–SIM12, que ainda não foi estabelecida nesta versão porque as fontes detalhadas desses artefatos não foram recuperadas;
- **evidência de execução:** resultado operacional ou técnico, que não é presumido pela existência de requisito/documento.

As referências a entidades, estados, eventos e invariantes abaixo são transcrições/associações de trabalho com o M0.3. Como M0.3 aguarda revisão/validação, essas associações também permanecem sujeitas à validação.

## 2. Matriz D01–D20

| Decisão | Requisito ratificado (síntese) | Entidades / conceitos M0.3 | Estados / condições relevantes | Eventos de domínio M0.3 | Invariantes candidatos | G0 relacionado | CA / SIM | Situação da evidência |
|---|---|---|---|---|---|---|---|---|
| D01 | Recepção registra chegada; conferência é evento distinto; acumulação de funções só com permissões. | UsuarioInterno, Perfil/Permissao, Recebimento, ItemRecebimento, RespostaChecklist, EventoAuditoria. | Recebimento REGISTRADO; conferência NAO_INICIADA → EM_ANDAMENTO → CONCLUIDA. | CHEGADA_REGISTRADA; CONFERENCIA_INICIADA; CONFERENCIA_CONCLUIDA. | INV-25, INV-30, INV-31. | P01, P11, P13, P16. | CA: ver 2.1; SIM: ver 2.2. | Regra ratificada; fluxo no sistema atual diagnosticado como insuficiente; validação operacional pendente. |
| D02 | Registrar dados da chegada, atores, volumes, condição, documentos, observações e tempos efetivo/registro. | Solicitação, Recebimento, ItemRecebimento, Evidencia, VinculoEvidencia. | Recebimento REGISTRADO; apresentação por item. | CHEGADA_REGISTRADA; ITEM_APRESENTADO; ITEM_NAO_APRESENTADO; EVIDENCIA_VINCULADA. | INV-25, INV-31. | P07, P09, P11, P24. | Não mapeados nesta versão. | Regra ratificada; diagnóstico aponta lacunas no domínio atual; execução operacional não comprovada. |
| D03 | Distinguir quantidades declarada, apresentada, aceita, recusada e não apresentada; permitir parcialidade e justificar divergências. | ItemDeclarado, ItemRecebimento, EventoApresentacao, ObjetoCustodia, DecisaoRecebimento. | APRESENTADO, NAO_APRESENTADO, APRESENTACAO_PARCIAL; decisão por escopo/objeto. | ITEM_APRESENTADO; ITEM_NAO_APRESENTADO; APRESENTACAO_COMPLEMENTAR_REGISTRADA; DECISAO_ACEITE_REGISTRADA; DECISAO_RECUSA_REGISTRADA. | INV-04, INV-05, INV-07, INV-34. | P07, P26. | Não mapeados nesta versão. | Regras conceituais presentes; unidades, precisão e reconciliação numérica continuam pendentes (M03-02/M03-03). |
| D04 | Um item recebido pode originar vários objetos de custódia com decisões e históricos próprios. | ItemRecebimento, EventoApresentacao, ObjetoCustodia, EventoCustodia. | Objeto SOB_CUSTODIA, EM_CONFERENCIA, PENDENTE, ACEITO ou RECUSADO. | OBJETO_CUSTODIA_CRIADO; CUSTODIA_INICIADA; DECISAO_ACEITE_REGISTRADA; DECISAO_RECUSA_REGISTRADA. | INV-05, INV-06, INV-08, INV-18, INV-34. | P26. | Não mapeados nesta versão. | Cardinalidade lógica proposta em M0.3; regras por categoria e exemplos de agrupamento/fracionamento pendentes. |
| D05 | Pendência individualizada, comunicação formal, prazo, prorrogação, evidência e reavaliação; vencimento não recusa automaticamente. | Pendencia, Evidencia, VinculoEvidencia, UsuarioInterno, DesignacaoCompetencia. | PENDENTE, EM_REGULARIZACAO, AGUARDANDO_REAVALIACAO, REGULARIZADA, PRAZO_VENCIDO, NAO_REGULARIZAVEL, CANCELADA. | PENDENCIA_ABERTA; PENDENCIA_COMUNICADA; PENDENCIA_PRORROGADA; REGULARIZACAO_RECEBIDA; PENDENCIA_REGULARIZADA; PENDENCIA_NAO_REGULARIZAVEL. | INV-16, INV-17, INV-30, INV-31. | P03, P09, P18. | Não mapeados nesta versão. | Ciclo lógico descrito; prazos numéricos, canais e regras institucionais permanecem pendentes. |
| D06 | Recusa fundamentada, evidenciada, validada quando exigido; custódia só encerra com destinação efetiva. | DecisaoRecebimento, ValidacaoCoordenacao, ObjetoCustodia, EventoCustodia, Evidencia. | RECUSA_PROPOSTA, RECUSADA; objeto RECUSADO, EM_DEVOLUCAO, EM_DESTINACAO, ENCERRADO. | DECISAO_RECUSA_REGISTRADA; VALIDACAO_COORDENACAO_REGISTRADA; DEVOLUCAO_AUTORIZADA/REALIZADA; DESTINACAO_AUTORIZADA/REALIZADA. | INV-13, INV-18, INV-19, INV-31, INV-32. | P01, P04, P11, P20. | Não mapeados nesta versão. | Diretriz ratificada/aprovada; procedimento, formulários, alçadas e comprovantes concretos pendentes. |
| D07 | Transferência só muda custodiante após confirmação do recebedor. | ObjetoCustodia, EventoCustodia, UsuarioInterno, Localizacao. | Transferência proposta/pendente de confirmação; custodiante anterior permanece até confirmação. | TRANSFERENCIA_SOLICITADA; TRANSFERENCIA_CONFIRMADA. | INV-09, INV-10, INV-11, INV-31. | P08, P13, P14, P23. | Não mapeados nesta versão. | Regra lógica descrita; contrato físico e testes de concorrência/confirmacão não comprovados para fluxo SEFI. |
| D08 | Mudança de localização é independente da transferência e não altera custodiante. | ObjetoCustodia, EventoCustodia, Localizacao, UsuarioInterno. | Custodiante permanece; localização corrente é atualizada pelo evento válido. | LOCALIZACAO_ALTERADA. | INV-12, INV-31. | P08, P13, P14. | Não mapeados nesta versão. | Diretriz aprovada; catálogo físico de locais, códigos e permissões pendentes. |
| D09 | Retificação excepcional preserva original/corrigido, motivo, evidência, autorização, assinatura e impacto em ensaios/laudos. | Retificacao, Evidencia, VinculoEvidencia, AmostraOperacional, Ensaio, AssinaturaEletronica, EventoAuditoria. | Ato original preservado; correção como novo ato/versionamento. | RETIFICACAO_REGISTRADA; EVIDENCIA_VINCULADA. | INV-25, INV-26, INV-30, INV-31. | P05, P10, P27. | Não mapeados nesta versão. | Requisito ratificado e modelo proposto; metodologia de impacto e alçadas detalhadas pendentes. |
| D10 | Acumular funções conforme permissão; impedir autoaprovação quando independência é exigida; administrador sem autoridade técnica implícita. | UsuarioInterno, Perfil/Permissao, DesignacaoCompetencia, ValidacaoCoordenacao. | ValidaçãoCoordenacao NAO_EXIGIDA, AGUARDANDO, APROVADA, DEVOLVIDA ou REJEITADA. | VALIDACAO_COORDENACAO_REGISTRADA. | INV-19, INV-20, INV-30, INV-31. | P01, P13, P16. | Não mapeados nesta versão. | Princípio ratificado; designações nominais e matriz institucional de competências pendentes. |
| D11 | Checklists por categoria, critérios E/S/I, aprovação, versionamento e preservação da versão aplicada. | ChecklistModelo, VersaoChecklist, CriterioChecklist, RespostaChecklist. | Conferência NAO_INICIADA, EM_ANDAMENTO, CONCLUIDA; critérios E/S/I definidos na versão publicada. | CONFERENCIA_INICIADA; RESPOSTA_CHECKLIST_REGISTRADA; CONFERENCIA_CONCLUIDA. | INV-14, INV-15, INV-17. | P02, P11, P17. | Não mapeados nesta versão. | Estrutura/governança aprovadas; checklists e critérios concretos por categoria pendentes. |
| D12 | Governança de checklist com elaboração técnica, revisão da Qualidade, aprovação competente e publicação administrativa. | ChecklistModelo, VersaoChecklist, CriterioChecklist, UsuarioInterno, DesignacaoCompetencia. | Estados de publicação/vigência da versão; estados detalhados a validar no modelo de processos. | Eventos de proposta, revisão, aprovação e publicação não estão discriminados na tabela de eventos de M0.3. | INV-14, INV-15, INV-20, INV-30, INV-31. | P01, P02, P13, P17. | Não mapeados nesta versão. | Processo aprovado em princípio; fluxo de governança e eventos específicos precisam de especificação. |
| D13 | Evidências vinculadas, originais preservados, versionamento, hash, acesso, retenção e auditoria. | Evidencia, VinculoEvidencia, Retificacao, EventoAuditoria. | Versões de evidência; vínculo formalizado preservado. | EVIDENCIA_VINCULADA; RETIFICACAO_REGISTRADA. | INV-17, INV-26, INV-31. | P09, P24, P25, P30. | Não mapeados nesta versão. | Requisitos aprovados; formatos, limites, armazenamento, retenção e tecnologia pendentes. |
| D14 | Trilha cronológica individualizada, protegida, com ator, data/hora, operação, antes/depois e justificativa. | EventoAuditoria, UsuarioInterno, entidades/ocorrências de negócio. | Registro append-only; correções por novos eventos. | Todos os eventos críticos do domínio correlacionados a eventos técnicos de auditoria. | INV-25, INV-26, INV-30, INV-31. | P13, P25. | Não mapeados nesta versão. | Base técnica atual é reutilizável com adaptação segundo diagnóstico; cobertura completa do fluxo SEFI ainda precisa ser especificada e testada. |
| D15 | Contas individuais, menor privilégio, concessão/revogação autorizadas, bloqueio e rastreabilidade. | UsuarioInterno, Perfil/Permissao, DesignacaoCompetencia, EventoAuditoria. | Situação de conta, vigência de permissão/competência e bloqueio de acesso. | Eventos de concessão, alteração, revogação e bloqueio não detalhados como eventos de negócio M0.3. | INV-20, INV-30, INV-31. | P13, P21, P29. | Não mapeados nesta versão. | Base de autenticação/RBAC existe; workflow formal, escopo externo e revisão periódica não comprovados. |
| D16 | Assinatura vinculada ao conteúdo/decisão, identidade, intenção, data/hora, autenticação reforçada e verificação. | AssinaturaEletronica, UsuarioInterno, DecisaoRecebimento, Retificacao, EventoAuditoria. | Assinatura requerida conforme política do ato; assinatura não substitui validação independente. | Assinatura associada ao ato; evento específico de assinatura deve ser definido na taxonomia técnica. | INV-19, INV-26, INV-30, INV-31. | P05, P19, P23, P29. | Não mapeados nesta versão. | Requisitos funcionais aprovados; modalidade jurídica, tecnologia e atos sujeitos a assinatura pendentes. |
| D17 | Backup e recuperação abrangendo banco, documentos e evidências, cópias segregadas, retenção, testes e continuidade. | Controle transversal de infraestrutura/continuidade; não é entidade de negócio M0.3. | Não aplicável como estado de entidade de negócio; definir estados de execução/recuperação no plano técnico. | Eventos operacionais de backup/restauração não constam na taxonomia de domínio M0.3. | Não há invariante de negócio específico; requisitos de continuidade são transversais. | P06, P13, P24, P30. | Não mapeados nesta versão. | Diretriz aprovada; parâmetros, arquitetura e evidências de restauração pendentes. |
| D18 | Identificadores distintos, únicos, permanentes e não reutilizáveis para cada agregado e seus vínculos. | Solicitação, Recebimento, ObjetoCustodia, AmostraOperacional, Ensaio, ReferenciaExterna. | Identidade estável durante todo o ciclo de vida; não reutilização. | Criação de cada agregado e associação de referência externa. | INV-27, INV-28, INV-29. | P07, P22, P23, P28. | Não mapeados nesta versão. | Princípios aprovados; formato, máscaras, accession/QR e política de migração pendentes. |
| D19 | Chegada posterior vinculada à solicitação original, novo evento, nova conferência e sem retroatividade. | Solicitação, Recebimento, ItemRecebimento, EventoApresentacao, ObjetoCustodia. | Apresentação complementar registrada; reabertura autorizada ou nova solicitação vinculada se processo encerrado. | APRESENTACAO_COMPLEMENTAR_REGISTRADA; ITEM_APRESENTADO; OBJETO_CUSTODIA_CRIADO. | INV-02, INV-05, INV-06, INV-25, INV-33. | P11, P18, P22, P23, P26. | Não mapeados nesta versão. | D19 ratificada; EventoApresentacao é refinamento proposto em M0.3 e requer validação funcional; M03-01 pendente. |
| D20 | Amostra operacional somente após aceite formal, critérios impeditivos atendidos, pendências resolvidas, validações e custódia válidas. | ObjetoCustodia, DecisaoRecebimento, ValidacaoCoordenacao, AmostraOperacional, Ensaio. | Objeto ACEITO; decisão ACEITE_VALIDADO; AmostraOperacional CRIADA/ATIVA conforme fluxo compatibilizado. | DECISAO_ACEITE_REGISTRADA; VALIDACAO_COORDENACAO_REGISTRADA; AMOSTRA_OPERACIONAL_CRIADA. | INV-21, INV-22, INV-23, INV-24. | P11, P12, P14, P15, P17, P23, P26. | Não mapeados nesta versão. | Barreira D20 ratificada; divergência com fluxo atual de POST /samples registrada; implementação futura depende de validação e G0. |


## 2.1 Correspondência analítica com CA01–CA37

A tabela abaixo é uma **associação analítica inicial** entre o texto dos critérios CA em EST-REC-001 v1.7 e as decisões D01–D20. O documento EST-REC-001 apresenta os critérios, mas não fornece uma matriz formal CA × D01–D20. Portanto, esta correspondência é rastreabilidade proposta para revisão, não uma decisão adicional nem uma aprovação dos critérios.

| Critério | Decisão(ões) relacionadas por análise textual | Conteúdo central do critério | Status na fonte EST-REC-001 |
|---|---|---|---|
| CA01 | D01, D15 | Usuário sem permissão tenta registrar chegada; bloqueio e registro da tentativa. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA02 | D01, D10 | Usuário com RECEPÇÃO + CONFERENTE pode registrar e conferir com eventos/autorias distintos. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA03 | D10 | Impedir validação da própria decisão quando independência é exigida. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA04 | D06, D11 | Critério E não conforme bloqueia aceite. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA05 | D05, D11 | Critério S não conforme gera pendência e bloqueia aceite até reavaliação favorável. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA06 | D11 | Critério I sem informação não bloqueia isoladamente. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA07 | D03 | Item não apresentado não gera ObjetoCustodia, custódia ou amostra. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA08 | D03 | Recebimento com itens apresentados e não apresentados pode ser concluído sem converter ausência em aceite. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA09 | D06, D07 | Material recusado e não retirado permanece sob guarda. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA10 | D07 | Transferência sem confirmação mantém responsabilidade com origem. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA11 | D07 | Confirmação do destinatário efetiva a mudança de responsável. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA12 | D05 | Vencimento não encerra pendência nem gera recusa automática. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA13 | D05, D13 | Evidência recebida sem reavaliação mantém pendência aguardando reavaliação. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA14 | D06, D10, D16 | Validação independente e assinatura formal na aprovação de recusa proposta. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA15 | D06, D11 | Coordenação não dispensa critério E, salvo fundamento previamente formalizado aplicável. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA16 | D18, D20 | Reenvio concorrente de criação de amostra não duplica amostra/identificador. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA17 | D20 | Aceite sem validação obrigatória concluída não permite criar amostra. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA18 | D03, D04, D06, D20 | Objetos de um item podem ter decisões distintas; objeto recusado permanece sob custódia. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA19 | D09, D16 | Retificação sem justificativa, evidência ou autorização é bloqueada. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA20 | D09 | Retificação após início de ensaios exige avaliação de impacto; não exclui dados automaticamente. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA21 | D10, D15 | Administrador não pode elevar a própria permissão. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA22 | D14 | Impedir alteração/exclusão de evento de auditoria formalizado. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA23 | D18, D19 | Chegada após conclusão como não apresentada não retroage; exige nova solicitação ou exceção formal. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA24 | D11, D12 | Conferência mantém versão do checklist originalmente aplicada. | Critério CA01–CA24 consolidado para revisão; teste não comprovado |
| CA25 | D13, D15 | Solicitante não acessa solicitação/evidência de terceiro sem vínculo autorizado. | Complemento CA25–CA37 proposto; adoção/validação pendente |
| CA26 | D02, D03 | Quantidade declarada e apresentada permanecem distintas; divergência é registrada. | Complemento CA25–CA37 proposto; adoção/validação pendente |
| CA27 | D03, D04 | Agrupamento de ObjetoCustodia explicita quantidade, unidade e justificativa. | Complemento CA25–CA37 proposto; adoção/validação pendente |
| CA28 | D02, D14, D19 | Instante efetivo e instante de registro permanecem distintos. | Complemento CA25–CA37 proposto; adoção/validação pendente |
| CA29 | D08 | Mudança de localização não simula transferência nem troca custodiante. | Complemento CA25–CA37 proposto; adoção/validação pendente |
| CA30 | D07, D08 | Transferência não confirmada mantém custodiante e localização vigentes. | Complemento CA25–CA37 proposto; adoção/validação pendente |
| CA31 | D18, D20 | Reenvio idempotente com mesma chave/conteúdo devolve resultado original sem duplicar efeitos. | Complemento CA25–CA37 proposto; adoção/validação pendente |
| CA32 | Transversal — G0-P23 | Reutilização de chave de idempotência com conteúdo diferente é rejeitada como conflito. | Complemento CA25–CA37 proposto; adoção/validação pendente |
| CA33 | Transversal — G0-P23 | Alterações concorrentes com mesma versão esperada produzem conflito, sem sobrescrita. | Complemento CA25–CA37 proposto; adoção/validação pendente |
| CA34 | D14, D18 | Paginação/ordenação histórica estável durante novas gravações. | Complemento CA25–CA37 proposto; adoção/validação pendente |
| CA35 | D13, D14 | Upload/consulta/substituição de anexo preserva hash, metadados, vínculo, autorização e histórico. | Complemento CA25–CA37 proposto; adoção/validação pendente |
| CA36 | D18, D19 | Registro legado sem evidência suficiente não recebe vínculo presumido. | Complemento CA25–CA37 proposto; adoção/validação pendente |
| CA37 | D18 | Protocolo SEFI, accession e QR mantêm finalidades distintas. | Complemento CA25–CA37 proposto; adoção/validação pendente |

**Observação de cobertura:** D17 (backup/recuperação) não possui CA específico entre CA01–CA37 conforme o conteúdo recuperado de EST-REC-001. Deve ser coberto por requisitos/critério técnico próprio associado a G0-P06, não por associação artificial a um CA existente. D12 possui cobertura apenas parcial por CA24 (congelamento de versão aplicada); o fluxo de elaboração, revisão, aprovação e publicação de checklist exige critérios adicionais.

## 2.2 Correspondência com SIM01–SIM12

A fonte `docs/VALIDACAO_CENARIOS_OPERACIONAIS_SEFI.md` (SIM-SEFI-REC-001 v1.2) foi recuperada. A relação D→SIM abaixo consta expressamente do adendo da fonte; os critérios CA relacionados a cada cenário também estão listados no documento.

| Cenário | Escopo | Decisões relacionadas conforme adendo da fonte | Critérios CA relacionados conforme cenário | Situação |
|---|---|---|---|---|
| SIM01 | Recebimento integral com aceite | D01–D04, D09–D12, D18, D20 | CA01–CA05, CA14, CA16–CA18, CA24, CA31–CA33, CA37 | Simulação documental; validação operacional pendente |
| SIM02 | Recebimento parcial com item não apresentado | D01–D04, D11–D12 | CA07, CA08, CA23, CA28, CA36 | Simulação documental; validação operacional pendente |
| SIM03 | Divergência entre quantidade declarada e apresentada | D02–D04 | CA04–CA08, CA26–CA27 | Simulação documental; depende de checklist/categoria |
| SIM04 | Um item com dois objetos, um aceito e outro recusado | D01–D04, D09–D12, D20 | CA09, CA14, CA18, CA20, CA27, CA37 | Simulação documental; depende de regra por categoria |
| SIM05 | Pendência saneável, comunicação, vencimento, prorrogação e reavaliação | D05–D06, D11–D12, D20 | CA05, CA12, CA13, CA14, CA26 | Simulação documental; prazos/canais/alçadas pendentes |
| SIM06 | Recusa com permanência em custódia e posterior devolução | D05–D06, D09–D12, D20 | CA04, CA09, CA14, CA15 | Simulação documental; procedimento de devolução pendente |
| SIM07 | Transferência entre responsáveis | D07 | CA10, CA11, CA29, CA30 | Simulação documental; confirmação e política de assinatura pendentes |
| SIM08 | Mudança de localização sem troca de custodiante | D08 | CA29, CA34 | Simulação documental; catálogo de locais pendente |
| SIM09 | Retificação após criação de amostra e início de ensaio | D09–D10, D13–D16, D20 | CA19, CA20, CA22 | Simulação documental; procedimento de impacto pendente |
| SIM10 | Reenvio concorrente e alteração com versão obsoleta | D18, D20; controles transversais G0-P23 | CA16, CA17, CA31, CA32, CA33 | Simulação documental; contrato técnico e testes reais pendentes |
| SIM11 | Solicitante tenta acessar solicitação/evidência de terceiro | D13–D16 | CA01, CA25, CA35 | Simulação documental; identidade externa e isolamento ainda pendentes |
| SIM12 | Material chega após conclusão como não apresentado | D18–D19 | CA07, CA23, CA28, CA36 | Simulação documental; regra de exceção/reabertura pendente |

**Rastreabilidade D→SIM expressa no adendo SIM-SEFI-REC-001 v1.2:**
- D01–D04: SIM01–SIM04.
- D05–D06: SIM05–SIM06.
- D07–D08: SIM07–SIM08.
- D09–D10: SIM09 e SIM01/SIM04/SIM06.
- D11–D12: SIM01–SIM06.
- D13–D16: SIM09–SIM11.
- D17: cenários de falha/recuperação ainda precisam ser acrescentados.
- D18: SIM01/SIM10/SIM12.
- D19: SIM12.
- D20: SIM01–SIM06 e SIM09.

A matriz não declara os cenários executados com operadores. A fonte afirma expressamente que SIM01–SIM12 permanecem simulação documental, não teste automatizado nem homologação. Também recomenda acrescentar cenários de restauração de backup, integridade de anexos/hash, autorização/assinatura, acesso indevido a anexos e conflitos de concorrência na etapa de QA.

## 3. Lacunas de rastreabilidade identificadas

1. **CA01–CA37:** o conteúdo individual foi recuperado em EST-REC-001 v1.7 e a correspondência analítica inicial está na seção 2.1. Ela não substitui uma matriz formal da fonte nem a validação dos vínculos.
2. **SIM01–SIM12:** conteúdo dos doze cenários e sua rastreabilidade D/CA foram recuperados. A execução de validação de mesa com representantes do SEFI, os registros de concordância/divergência e evidências de execução continuam pendentes.
3. **M03-01 a M03-16:** permanecem pendências explícitas no M0.3. Em especial, M03-01 (EventoApresentacao/D19), M03-02 (agrupamento/fracionamento) e M03-03 (unidades/reconciliação) afetam o detalhamento do domínio.
4. **M0.1/M0.2:** M0.2 v0.7 e EST-REC-001 v1.7 foram recuperados. A comparação detalhada das cardinalidades e regras entre M0.2 e M0.3 ainda precisa ser concluída.
5. **Evidências operacionais:** a presença de uma regra ou evento no modelo não comprova execução por usuários do SEFI.
6. **Evidências técnicas:** a matriz de aderência e a matriz G0 registram limites específicos de CI/testes; não converter resultado de CI em homologação do fluxo SEFI.

## 4. Fontes para completar a matriz

Fontes citadas no M0.3 que precisam ser localizadas/recuperadas:
- `docs/MODELO_CONCEITUAL_DOMINIO_SOLICITACAO_RECEBIMENTO.md` (M0.2 v0.7);
- `docs/ESTADOS_E_TRANSICOES_SOLICITACAO_RECEBIMENTO.md` (v1.7; CA01–CA37);
- `docs/MODELO_RELACIONAL_PRELIMINAR_LIMS.md` (v0.3);
- `docs/CONTRATO_HISTORICO_UNIFICADO_E_ACEITE.md` (v0.1);
- evidências de execução/validação operacional dos cenários SIM01–SIM12;
- evidências de execução dos testes CA01–CA37.

Os caminhos acima são citados literalmente por M0.3; sua recuperação ainda não foi concluída nesta etapa.

## 5. Próximos passos documentais

1. Localizar e recuperar M0.2, estados/transições, modelo relacional, contrato de histórico/aceite, CA01–CA37 e SIM01–SIM12.
2. Comparar M0.3 com M0.2 e com a baseline D01–D20, registrando qualquer divergência.
3. Substituir “não mapeados” por referências CA/SIM somente após leitura das fontes originais.
4. Vincular cada CA a requisito, entidade, estado, evento, invariante, pré-condição, resultado esperado e evidência.
5. Manter a execução dos SIM como validação operacional pendente até haver registros reais e participantes designados.

## 6. Situação formal

- Matriz D01–D20: **PRIMEIRA VERSÃO DOCUMENTAL — NÃO VALIDADA**.
- M0.3: **AGUARDANDO REVISÃO/VALIDAÇÃO**.
- CA01–CA37: **MAPEAMENTO DETALHADO PENDENTE**.
- SIM01–SIM12: **VALIDAÇÃO OPERACIONAL NÃO COMPROVADA**.
- Gate G0: **NÃO APROVADO**.
- Implementação: **NÃO AUTORIZADA**.
- Escopo: **DOCUMENTAÇÃO EXCLUSIVAMENTE**.
