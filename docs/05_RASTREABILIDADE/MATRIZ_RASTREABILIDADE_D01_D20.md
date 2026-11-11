# Matriz Inicial de Rastreabilidade — D01 a D20

**Identificador:** MAT-TRC-SEFI-D01-D20-001  
**Versão:** 0.1  
**Data:** 2026-11-11  
**Branch:** `docs/integracao-especificacao-sefi`  
**Fontes principais:** DEC-SEFI-001 v1.7; MOD-LOG-SEFI-003 (M0.3) v0.1; MAT-G0-SEFI-001 v0.3.  
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
| D01 | Recepção registra chegada; conferência é evento distinto; acumulação de funções só com permissões. | UsuarioInterno, Perfil/Permissao, Recebimento, ItemRecebimento, RespostaChecklist, EventoAuditoria. | Recebimento REGISTRADO; conferência NAO_INICIADA → EM_ANDAMENTO → CONCLUIDA. | CHEGADA_REGISTRADA; CONFERENCIA_INICIADA; CONFERENCIA_CONCLUIDA. | INV-25, INV-30, INV-31. | P01, P11, P13, P16. | Não mapeados nesta versão. | Regra ratificada; fluxo no sistema atual diagnosticado como insuficiente; validação operacional pendente. |
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

## 3. Lacunas de rastreabilidade identificadas

1. **CA01–CA37:** a matriz de prontidão informa a existência/referência dos critérios, mas esta versão não recuperou o conteúdo individual dos critérios. Não atribuir números CA a decisões por inferência.
2. **SIM01–SIM12:** os cenários são citados como conjunto, mas seus passos, participantes, resultados e evidências precisam ser recuperados.
3. **M03-01 a M03-16:** permanecem pendências explícitas no M0.3. Em especial, M03-01 (EventoApresentacao/D19), M03-02 (agrupamento/fracionamento) e M03-03 (unidades/reconciliação) afetam o detalhamento do domínio.
4. **M0.1/M0.2:** M0.3 declara preservar cardinalidades M0.2, mas as fontes originais M0.2 e de estados ainda precisam ser recuperadas e comparadas diretamente.
5. **Evidências operacionais:** a presença de uma regra ou evento no modelo não comprova execução por usuários do SEFI.
6. **Evidências técnicas:** a matriz de aderência e a matriz G0 registram limites específicos de CI/testes; não converter resultado de CI em homologação do fluxo SEFI.

## 4. Fontes para completar a matriz

Fontes citadas no M0.3 que precisam ser localizadas/recuperadas:
- `docs/MODELO_CONCEITUAL_DOMINIO_SOLICITACAO_RECEBIMENTO.md` (M0.2 v0.7);
- `docs/ESTADOS_E_TRANSICOES_SOLICITACAO_RECEBIMENTO.md` (v1.7; CA01–CA37);
- `docs/MODELO_RELACIONAL_PRELIMINAR_LIMS.md` (v0.3);
- `docs/CONTRATO_HISTORICO_UNIFICADO_E_ACEITE.md` (v0.1);
- documentos de cenários SIM01–SIM12;
- documentos de critérios de aceitação e evidências de execução.

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
