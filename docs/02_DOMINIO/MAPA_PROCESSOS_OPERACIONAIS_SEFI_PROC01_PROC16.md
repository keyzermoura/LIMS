# Mapa de Processos Operacionais do LIMS-SEFI

**Identificador:** PROC-MAP-SEFI-001  
**Versão:** 0.2  
**Data:** 2026-11-11  
**Fontes:** D01–D20 (DEC-SEFI-001 v1.7); M0.2 v0.7; EST-REC-001 v1.7; M0.3 v0.1; SIM-SEFI-REC-001 v1.2; BCDP-LIMS-SEFI-001 v0.1.  
**Natureza:** consolidação documental dos processos; não é procedimento operacional institucional aprovado nem homologação.

## 1. Objetivo

Organizar os processos de negócio do SEFI em sequência e explicitar atores, pré-condições, resultados, entidades, eventos, critérios de aceitação e dependências. O mapa deriva das decisões e documentos existentes; não cria alçadas, prazos, critérios técnicos ou exceções não aprovados.

## 2. Fluxo macro

**Solicitação → chegada física → apresentação dos itens → criação dos objetos sob custódia → conferência → pendências (se houver) → decisão → validação independente (quando exigida) → aceite e criação da AmostraOperacional ou recusa e destinação → continuidade da custódia, ensaios e histórico.**

A chegada física, a conferência, a decisão e a criação da amostra são atos/processos distintos. O recebimento pode ser concluído administrativamente com item não apresentado quando as condições de EST-REC-001 forem atendidas; isso não equivale a aceite universal.

## 3. Catálogo de processos

| ID | Processo | Objetivo e gatilho | Atores/papéis | Pré-condições e controles | Resultado / eventos principais | Decisões / RF | CA / SIM | Pendências |
|---|---|---|---|---|---|---|---|---|
| PROC-01 | Registrar e submeter solicitação | Formalizar a demanda e os itens declarados. | Solicitante; usuário interno que cadastra em nome do solicitante. | Solicitante identificado; pelo menos um ItemDeclarado; campos obrigatórios; usuário autorizado. | Solicitação RASCUNHO → SUBMETIDA; SOLICITACAO_CRIADA/SOLICITACAO_SUBMETIDA. | D02, D18; RF-002/RF-018. | CA25, CA37; SIM01–SIM12 como pré-contexto. | Identidade externa e vínculo do solicitante (G0-P21) pendentes; M0.2 descreve primeira entrega sem conta externa. |
| PROC-02 | Registrar chegada física principal | Registrar fato da apresentação física no SEFI, mesmo com divergência ou documentação incompleta; chegada não equivale a aceite. | RECEPÇÃO; recebedor físico; autor do registro. | Solicitação submetida; recebedor identificado; instante efetivo e registro separados; volumes, condição externa, documentos e observações conforme D02. | Recebimento REGISTRADO; CHEGADA_REGISTRADA. | D01, D02; RF-001/RF-002. | CA01, CA02, CA28; SIM01–SIM03. | Perfil/permissões, dados obrigatórios e horários institucionais precisam de configuração/validação. |
| PROC-03 | Registrar apresentação por item e quantidades | Determinar o que foi efetivamente apresentado, parcialmente apresentado ou não apresentado. | RECEPÇÃO; conferente conforme etapa. | ItemDeclarado vinculado; observação física; quantidade/unidade observadas; tempo do fato e registro. | ItemRecebimento APRESENTADO/NAO_APRESENTADO; ITEM_APRESENTADO/ITEM_NAO_APRESENTADO. | D02, D03, D19; RF-002/RF-003/RF-019. | CA07, CA08, CA23, CA26, CA28, CA36; SIM02, SIM03, SIM12. | M03-01/M03-03: apresentação parcial, múltiplas apresentações e reconciliação; nomenclatura entre EST e M0.3 pendente. |
| PROC-04 | Individualizar material e iniciar custódia | Criar objetos para material apresentado e registrar guarda inicial. | RECEPÇÃO/designado; custodiante inicial. | Material fisicamente apresentado; individualização/agrupamento justificado; quantidade/unidade; custodiante e localização inicial identificados. | ObjetoCustodia sob guarda; OBJETO_CUSTODIA_CRIADO/CUSTODIA_INICIADA. | D03, D04, D07, D08; RF-003/RF-004/RF-007/RF-008. | CA07, CA09, CA18, CA27; SIM01–SIM04, SIM06. | M03-02/M03-03: critérios por categoria e linhagem de agrupamento/fracionamento; M03-15: modelo físico. |
| PROC-05 | Executar conferência técnica/administrativa | Avaliar os critérios aplicáveis ao item/objeto. | CONFERENTE; especialista habilitado. | Material apresentado e sob custódia; checklist publicado e aplicável; versão fixada; conferente autorizado. | Conferência NAO_INICIADA → EM_ANDAMENTO → CONCLUIDA; CONFERENCIA_INICIADA/RESPOSTA_CHECKLIST_REGISTRADA/CONFERENCIA_CONCLUIDA. | D01, D10–D12; RF-001/RF-010/RF-011/RF-012. | CA02–CA06, CA24; SIM01–SIM06. | Checklists concretos, critérios E/S/I e competências nominais pendentes (G0-P01/P02/P16/P17). |
| PROC-06 | Abrir, comunicar e tratar pendência | Solicitar regularização de condição saneável ou providência necessária. | CONFERENTE; responsável pela comunicação; solicitante; coordenação para prorrogação conforme alçada. | Não conformidade classificada; responsável, providência, prazo e canal definidos; comunicação comprovável. | Pendência PENDENTE → EM_REGULARIZACAO → AGUARDANDO_REAVALIACAO → REGULARIZADA; PENDENCIA_ABERTA/COMUNICADA/PRORROGADA/REGULARIZACAO_RECEBIDA/PENDENCIA_REGULARIZADA. | D05, D11; RF-005/RF-011. | CA05, CA12, CA13, CA26; SIM05. | Valores de prazo, canais oficiais, alertas, prorrogação e responsáveis (G0-P03/P18) pendentes. |
| PROC-07 | Formalizar decisão de aceite ou recusa | Registrar desfecho do material no menor nível onde os resultados possam divergir. | CONFERENTE/autoridade técnica; decisor habilitado. | Conferência concluída; checklist; critérios impeditivos tratados; pendências impeditivas resolvidas; evidências; competência. | ACEITA/RECUSADA/PENDENTE; DECISAO_ACEITE_REGISTRADA/DECISAO_RECUSA_REGISTRADA. | D04–D06, D10–D12; RF-004/RF-005/RF-006/RF-010/RF-011. | CA04–CA06, CA14–CA18; SIM01–SIM06. | Harmonizar estado da decisão versus estado do objeto; critérios técnicos por categoria e alçadas pendentes. |
| PROC-08 | Validar decisão pela coordenação | Realizar revisão independente quando exigida. | COORDENAÇÃO ou substituto formalmente designado. | Decisão sujeita à validação; validador diferente do autor/executor quando independência exigida; competência vigente. | ValidacaoCoordenacao APROVADA/DEVOLVIDA/REJEITADA; VALIDACAO_COORDENACAO_REGISTRADA. | D06, D09, D10, D16; RF-006/RF-009/RF-010/RF-016. | CA03, CA14, CA15, CA17, CA19; SIM01, SIM04–SIM06, SIM09. | Designações nominais, substitutos e alçadas (G0-P01/P16) pendentes. |
| PROC-09 | Admitir objeto e criar AmostraOperacional | Converter objeto aceito em amostra do ciclo laboratorial. | Ator autorizado pela matriz de competência; sistema. | Aceite formal válido; checklist concluído; bloqueios e pendências impeditivas resolvidos; validações exigidas; custódia rastreável; objeto sem amostra anterior. | AMOSTRA_OPERACIONAL_CRIADA; AmostraOperacional CRIADA/ATIVA conforme compatibilização. | D20; RF-020. | CA16–CA18, CA31–CA33; SIM01–SIM06, SIM09, SIM10. | M03-16: estados da amostra; contrato de atomicidade/idempotência; compatibilidade de DeviceSample; G0-P23. |
| PROC-10 | Transferir custódia entre responsáveis | Alterar custodiante somente após confirmação do recebedor. | Custodiante de origem; destinatário; sistema. | Objeto sob custódia; origem/destino e recebedor pretendido identificados. | TRANSFERENCIA_SOLICITADA → TRANSFERENCIA_CONFIRMADA; custodiante muda apenas na confirmação. | D07; RF-007. | CA10, CA11, CA30; SIM07. | Procedimento de confirmação, evidência e eventual assinatura conforme política institucional. |
| PROC-11 | Alterar localização física | Registrar movimentação sem troca de custodiante. | Custodiante/responsável autorizado. | Objeto identificado; origem, destino, responsável, tempo e justificativa. | LOCALIZACAO_ALTERADA; custodiante permanece. | D08; RF-008. | CA29, CA34; SIM08. | Inventário de locais, códigos e permissões (G0-P08) pendentes. |
| PROC-12 | Devolver ou destinar material recusado | Concluir guarda somente após entrega/destinação efetiva e comprovada. | Coordenação/autoridade; custodiante; representante autorizado; recebedor/destinatário. | Decisão e destino autorizados; identidade/representação verificada; quantidade/condição e comprovante. | DEVOLUCAO_AUTORIZADA/REALIZADA ou DESTINACAO_AUTORIZADA/REALIZADA; ENCERRADO após comprovação. | D06, D07; RF-006/RF-007. | CA09, CA14, CA15; SIM04, SIM06. | Procedimento, formulários, alçadas e designações (G0-P04/P20) pendentes. |
| PROC-13 | Retificar ato ou dado formalizado | Corrigir excepcionalmente sem apagar o original e avaliar impactos. | Autor da solicitação; coordenação/autoridade competente; executor habilitado. | Motivo, valores original/corrigido, evidência, autorização prévia, impacto e assinatura quando exigida. | RETIFICACAO_REGISTRADA; original preservado e novo ato vinculado. | D09, D14, D16; RF-009/RF-014/RF-016. | CA19, CA20, CA22; SIM09. | Metodologia de impacto sobre amostra/ensaio/laudo (G0-P10/P27) pendente. |
| PROC-14 | Registrar chegada posterior/complementar | Tratar material apresentado depois da chegada ou conclusão original sem retroatividade. | RECEPÇÃO; autoridade que autoriza exceção/reabertura; conferente. | Solicitação/recebimento original consultado; reabertura autorizada ou nova solicitação vinculada quando aplicável. | Novo fato de apresentação/chegada; histórico original preservado. | D19; RF-019. | CA07, CA23, CA28, CA36; SIM12. | M03-01: EventoApresentacao é proposta, não decisão aprovada; definir exceção/reabertura. |
| PROC-15 | Vincular e preservar documentos/evidências | Sustentar chegada, conferência, pendência, decisão, assinatura e retificação. | Usuário autorizado; custodiante documental/sistema. | Evidência identificada; alvo/finalidade autorizados; metadados e integridade disponíveis. | EVIDENCIA_VINCULADA; versões e original preservados. | D02, D05, D06, D09, D13, D14; RF-002/RF-005/RF-006/RF-009/RF-013/RF-014. | CA13, CA19, CA25, CA35; SIM05, SIM09, SIM11. | G0-P09/P24/P30: formatos, armazenamento, retenção e recuperação pendentes. |
| PROC-16 | Consultar histórico e exportar registros | Reconstruir processo, custódia, decisões, auditoria e evidências. | Usuários internos autorizados; solicitante dentro de seu escopo; auditor. | Identidade, permissão e escopo validados; filtros/ordenação/paginação controlados. | Consulta histórica e exportação autorizada e rastreável. | D13–D15, D18; RF-013/RF-014/RF-015/RF-018. | CA22, CA25, CA34–CA37; SIM09–SIM12. | G0-P28/P30: campos, formatos, limites, retenção e políticas pendentes. |
| PROC-17 | Assegurar continuidade, backup e recuperação | Proteger dados, documentos e evidências e comprovar capacidade de restauração. | TI/infraestrutura; responsáveis institucionais formalmente designados; auditoria/Qualidade conforme governança. | Política aprovada; cópias segregadas/protegidas; escopo, retenção, RPO/RTO e responsáveis definidos. | Backup monitorado; restauração testada; evidência e plano de continuidade registrados. | D17; G0-P06; RT-009/RT-014. | Plano de testes complementar; SIM01–SIM12 não cobre integralmente recuperação. | Frequência, retenção, RPO/RTO, segregação, responsáveis e teste de restauração permanecem pendentes. |

## 4. Regras de sequência e exceção

1. A solicitação é distinta do recebimento; o recebimento principal é no máximo um por solicitação, conforme cardinalidade M0.2.
2. Todos os itens declarados devem ter representação no recebimento principal, inclusive os não apresentados.
3. Somente material apresentado pode originar ObjetoCustodia e custódia.
4. Conferência e decisão ocorrem após a chegada e não são presumidas pelo registro físico.
5. A decisão é feita no menor nível em que os desfechos possam divergir.
6. Pendência vencida não gera recusa automática; evidência recebida exige reavaliação.
7. Recusa não encerra custódia; devolução/destinação efetiva e comprovada é necessária.
8. Transferência só muda custodiante após confirmação do destinatário; mudança de localização não muda custodiante.
9. AmostraOperacional só pode ser criada após aceite formal e validações/bloqueios resolvidos.
10. Retificação é novo ato, preservando original e avaliando impacto.
11. Chegada posterior é novo fato; não retroagir o evento anterior.
12. Estado agregado não substitui histórico individual de item/objeto.

## 5. Limites e questões em aberto

- O mapa não define prazos, canais, formulários, critérios técnicos por categoria, competências nominais, modalidade de assinatura ou tecnologia.
- A nomenclatura de estados entre EST-REC-001/SIM e M0.3 ainda requer harmonização, conforme `CMP-DOM-SEFI-M02-M03-001`.
- EventoApresentacao permanece proposta sujeita à validação funcional (M03-01).
- Critérios CA01–CA37 e SIM01–SIM12 ainda não foram executados; SIM são simulações documentais.
- D17 requer cenários adicionais de backup/restauração; os SIM atuais não cobrem integralmente continuidade.
- A referência integrada para interpretação de entidades, cardinalidades, estados e pendências é a [Baseline Consolidada do Domínio e dos Processos](BASELINE_CONSOLIDADA_DOMINIO_PROCESSOS_SEFI.md).
- O mapa não prova que o software atual implemente os processos.

## 6. Situação formal

- Processos PROC-01–PROC-17: **MAPEAMENTO DOCUMENTAL INICIAL**.
- PROC-17 é controle transversal de continuidade/recuperação; não é etapa do recebimento.
- Baseline consolidada de domínio/processos: **v0.1 — proposta para revisão, não validada**.
- Validação operacional: **PENDENTE**.
- Critérios/testes: **NÃO EXECUTADOS**.
- Gate G0: **NÃO APROVADO**.
- Implementação: **NÃO AUTORIZADA**.
