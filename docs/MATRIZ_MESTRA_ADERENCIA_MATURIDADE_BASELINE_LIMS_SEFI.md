# Pacote A — Matriz Mestra de Aderência, Maturidade e Baseline LIMS-SEFI

**Identificador:** MAT-MESTRA-LIMS-SEFI-001  
**Versão:** 1.0  
**Data:** 2026-11-18  
**Repositório:** `keyzermoura/LIMS`  
**Branch documental:** `docs/plano-correcoes-pacote-a`  
**Baseline examinada:** `e5797013cff5b455c3d105a3a8ee2407da5213c5`  
**Documentos relacionados:** PLN-COR-LIMS-SEFI-001; MOD-LOG-SEFI-003; MAT-ADER-SEFI-001; MAT-G0-SEFI-001; DEC-SEFI-001.  
**Natureza:** auditoria documental e estática de aderência; não constitui homologação operacional, validação institucional ou aprovação do Gate G0.  
**Situação:** Pacote A — versão inicial consolidada; itens não verificados permanecem explicitamente abertos.

---

## 1. Objetivo

Estabelecer uma visão única e rastreável da aderência entre decisões institucionais D01–D20, propostas G0-P01–P30, domínio lógico SEFI e implementação presente na baseline examinada.

Esta matriz corrige a defasagem das avaliações anteriores: documentos de 10/11/2026 ainda descreviam a ausência de entidades de Solicitação, Recebimento, ItemRecebimento e ObjetoCustodia, enquanto a baseline de 18/11/2026 já contém esses modelos e serviços. A existência desses componentes, porém, não demonstra automaticamente aderência semântica integral.

## 2. Baseline, escopo e limitações

### 2.1 Baseline

- Branch principal examinada: `main`.
- Commit: `e5797013cff5b455c3d105a3a8ee2407da5213c5`.
- Mensagem: `feat(security): fechar P4.1 (attributes imutavel), P1.2 (escopos M2M) e P5.1 (SAST/SCA no CI)`.
- Data informada pelo GitHub: 18/11/2026.
- Branch de trabalho documental: `docs/plano-correcoes-pacote-a`, criada a partir dessa baseline.

### 2.2 Escopo inspecionado

A inspeção estática consultou os documentos M0.3, matriz de aderência, matriz G0, matriz de lacunas, roadmap, decisões D01–D20, modelo M0.2 e estados/transições, além dos serviços de recebimento, custódia/aceite e execução de ensaios.

Arquivos centrais identificados:
- `backend/app/services/receipt_service.py`
- `backend/app/services/execution_service.py`
- `backend/app/services/reagent_service.py`
- modelos e rotas dos domínios `solicitation`, `receipt`, `custody`, `sample`, `lab_test`, `test_execution`, `equipment`, `qualification`, `oos`, `capa` e relatórios oficiais.

### 2.3 Limitações

- Não foi executada nesta atividade a suíte completa de testes.
- Não foi feita homologação de navegador com operadores SEFI.
- Não foi realizado restore de backup em ambiente isolado.
- Não foram inspecionados todos os arquivos, rotas e testes em profundidade suficiente para atribuir PASS a cada CA/SIM.
- A análise estática não comprova o comportamento em produção, segurança operacional, aderência ISO/IEC 17025 ou validação institucional.

### 2.4 Legenda de status

| Status | Significado |
|---|---|
| **Aderente estruturalmente** | Há entidade/serviço compatível; ainda pode haver critérios comportamentais pendentes. |
| **Parcial** | Parte do requisito está representada, mas a implementação inspecionada revela lacuna ou cobertura incompleta. |
| **Não evidenciado** | Não foi localizada evidência suficiente nesta inspeção; não significa prova de inexistência absoluta. |
| **Pendente institucional** | Depende de parâmetro, designação, procedimento ou decisão de autoridade competente. |
| **Não verificado** | Exige inspeção/teste adicional antes de qualquer conclusão. |
| **Bloqueador** | Impede declarar o fluxo ou Gate G0 pronto até que a evidência exigida seja produzida. |

---

## 3. Síntese executiva atualizada

1. A implementação já contém uma cadeia própria de Solicitação → ItemSolicitação → Recebimento → ItemRecebimento → ObjetoCustodia → evento/decisão de custódia → DeviceSample.
2. O serviço de recebimento ainda apresenta uma divergência funcional material: inicializa cada item como apresentado, iguala quantidade apresentada à declarada e cria objeto de custódia para cada item, sem condicionar a apresentação física efetiva.
3. O serviço de aceite de objeto de custódia já cria `DeviceSample` quando a decisão é favorável, em operação transacional e com vínculo ao objeto. A barreira completa D20 precisa, contudo, ser comprovada quanto a checklist, pendências impeditivas, validação independente, quantidades e idempotência/concorrência.
4. O serviço de execução registra leituras e dados brutos em `TestExecution`, verifica qualificação do analista e equipamento na abertura; o trecho de conclusão inspecionado não apresenta intertravamento explícito para consumo obrigatório de reagentes/padrões.
5. Há estruturas relevantes de OOS/CAPA, auditoria, assinatura, relatórios, equipamento, qualificação e integração instrumental; a abrangência e evidência de cada fluxo precisam ser verificadas individualmente.
6. Backup e recuperação continuam como risco crítico até restore reproduzível e verificado.
7. A matriz de aderência v1.1, a matriz G0 v0.3 e o M0.3 não representam corretamente a baseline de 18/11/2026. Este documento passa a ser a referência de auditoria estática do Pacote A, sem apagar o histórico dos documentos anteriores.

**Parecer preliminar:** a base técnica é aproveitável e não justifica reconstrução. O fluxo de recebimento/admissão ainda não deve ser considerado aderente nem o Gate G0 liberado.

---

## 4. Mapeamento do domínio lógico para a implementação

| Conceito lógico SEFI | Implementação identificada | Evidência de código / domínio | Avaliação |
|---|---|---|---|
| Solicitante | Relação/campos de solicitante em Solicitation | `Solicitation`, `SolicitationItem` | Parcial — validar representação de pessoa, organização e cadastro em nome de terceiro. |
| Solicitação | `Solicitation` | `backend/app/models/solicitation.py`; serviço/rotas de solicitação | Aderente estruturalmente. |
| Item declarado | `SolicitationItem` | `backend/app/models/solicitation_item.py` | Aderente estruturalmente. |
| Recebimento principal | `Receipt` | `backend/app/models/receipt.py`; `receipt_service.py` | Aderente estruturalmente; regra de unicidade e concorrência requer teste. |
| Item de recebimento | `ReceiptItem` | `backend/app/models/receipt_item.py`; `receipt_service.py` | Parcial — representação existe, inicialização de apresentação/quantidade está incorreta para item não apresentado. |
| Objeto de custódia | `CustodyObject` | `backend/app/models/custody_object.py`; serviço de custódia | Aderente estruturalmente; geração deve depender de material efetivamente apresentado. |
| Evento de custódia | `CustodyEvent` | `backend/app/models/custody_event.py`; serviço de custódia | Parcial — confirmar semântica distinta de transferência, mudança de localização, confirmação do custodiante e encerramento. |
| Conferência | Operações de conferência sobre ReceiptItem | serviço/rotas de recebimento e checklist | Parcial — verificar checklist versionado, classes E/S/I e preservação da versão aplicada. |
| Pendência de recebimento | Modelo/serviço próprio não confirmado nesta inspeção | verificar modelos e rotas de pendência | Não verificado — CAPA/OOS não devem ser presumidos equivalentes. |
| Decisão de recebimento | Decisão/aceite de CustodyObject | serviço de aceite de custódia | Parcial — comprovar pré-condições completas D20 e validação da coordenação. |
| Amostra operacional | `DeviceSample` | `backend/app/models/device_sample.py`; serviço `accept_custody_object()` | Aderente estruturalmente à origem por objeto; conferir unicidade, idempotência e barreira completa. |
| Ensaio | `LabTest` | `backend/app/models/lab_test.py` | Aderente estruturalmente; mapear plano de ensaios e versões de método. |
| Execução | `TestExecution` | `backend/app/models/test_execution.py`; `execution_service.py` | Parcial — leituras, condições e dados brutos existem; intertravamento de insumos requer evolução. |
| Método/procedimento | `LabTest` e entidades de método | modelos/serviços de métodos | Não verificado — comprovar versão imutável aplicada à execução. |
| Equipamento | `LaboratoryEquipment` | `equipment_service.py`; `execution_service.py` | Parcial — validação de uso na abertura identificada; comprovar histórico e evidência temporal. |
| Competência | Qualificação de analista | `qualification_service.py`; `execution_service.py` | Parcial — verificação na abertura identificada; conferir validade e trilha de designações institucionais. |
| Reagentes/padrões | Serviços e modelos de reagentes/lotes | `reagent_service.py` | Parcial — serviço existe; conclusão de ensaio não evidencia intertravamento obrigatório. |
| OOS/CAPA | Modelos e serviços OOS/CAPA | execução chama abertura automática de OOS em resultado reprovado | Aderente estruturalmente; validar ciclo completo e origem de desvios de recebimento separada. |
| Revisão/laudo | Relatórios oficiais, resultados versionados e assinatura | serviços/modelos de relatório e assinatura | Aderente estruturalmente; validar pacote de evidência, assinatura e retificação. |
| Evidências/anexos | Não confirmado de ponta a ponta | verificar armazenamento, metadados, rotas e testes | Não verificado; requisito D13/G0-P09/P24 permanece bloqueador até comprovação. |
| Auditoria | `AuditLog` e `audit_service` | serviço/modelos/guardas PostgreSQL | Aderente estruturalmente; verificar cobertura dos eventos SEFI e resistência operacional. |
| Assinatura | `ElectronicSignature` | serviço/modelo de assinatura | Aderente estruturalmente; modalidade institucional/jurídica permanece pendente. |
| Identificadores | UUIDs, sequências de recebimento, objeto e amostra | modelos e serviços | Parcial — conferir unicidade, não reutilização e padrão de negócio de cada agregado. |
| Indicadores | Endpoints de analytics | rotas/serviços analytics | Parcial — validar métricas, filtros e reconciliação com operação real. |
| Backup/recuperação | Scripts e configuração de infraestrutura | manifests/scripts de backup | Bloqueador — restore operacional e PITR não comprovados. |

---

## 5. Matriz de aderência por decisão D01–D20

A classificação abaixo distingue estrutura presente de conformidade comportamental. A coluna de evidência aponta o principal ponto de inspeção; não substitui o mapeamento exaustivo de todas as rotas e testes.

| Decisão | Regra aprovada resumida | Evidência atual identificada | Status | Lacuna / ação necessária |
|---|---|---|---|---|
| D01 | Recepção registra chegada; recebimento e conferência são atos distintos; acumulação permitida conforme permissões. | `Solicitation`, `Receipt`, `ReceiptItem`, `received_by_id`, serviço de recebimento. | Parcial | Confirmar autoria/horários distintos e matriz de permissões por operação. |
| D02 | Registrar horários, recebedor, entregador, volumes, embalagem, avarias, documentos e evidências. | `Receipt` e campos de chegada/embalagem/local/observações. | Parcial | Inventariar campos e comprovar timestamp de fato versus registro, entregador/ausência, volumes e evidências. |
| D03 | Quantidades declarada, apresentada, aceita, recusada e não apresentada independentes. | `SolicitationItem`, `ReceiptItem`; `create_receipt()` iguala apresentada à declarada. | **Parcial — bloqueador** | Corrigir inicialização e reconciliação; não inferir apresentação a partir da declaração. |
| D04 | Item recebido pode originar múltiplos objetos com decisão/histórico próprios. | `ReceiptItem` e relação com `CustodyObject`. | Parcial | Preservar granularidade e permitir múltiplos objetos; não gerar objetos antes da apresentação física. |
| D05 | Pendências individualizadas, saneamento, comunicação, prazo, prorrogação e reavaliação. | Não confirmado ciclo de pendência de recebimento nesta inspeção. | Não verificado | Inspecionar entidades/rotas; separar pendência de recebimento de CAPA/OOS; testar prazo vencido sem recusa automática. |
| D06 | Recusa motivada; custódia só termina com destinação efetiva comprovada. | Decisão de recusa no serviço de aceite de objeto e evento de encerramento. | Parcial | Confirmar comunicação, autoridade, validação exigida, devolução/destinação e evidência efetiva. |
| D07 | Transferência exige entregador, recebedor, horários e confirmação do novo custodiante. | `CustodyEvent` e serviço de transferência. | Parcial | Confirmar aceite do novo custodiante como condição para transferir responsabilidade; distinguir horários. |
| D08 | Mudança de localização separada da transferência e sem alterar custodiante. | `current_location` e eventos de custódia. | Não verificado | Confirmar operação autônoma de localização e testes que preservam custodiante. |
| D09 | Retificação justificada, autorizada, assinada e com avaliação de impacto. | Emenda/versionamento de resultado; trilha de auditoria. | Parcial | Criar/confirmar retificação transversal e avaliação de impacto em amostra, ensaio e laudo. |
| D10 | Acumulação permitida; independência bloqueia autoaprovação quando exigida. | RBAC e escopos M2M; verificação de qualificação em execução. | Parcial | Separar permissão, competência, designação e autoridade; testar autoaprovação por ato. |
| D11 | Checklists por categoria com critérios E/S/I, versão e histórico. | Estrutura/rotas de checklist e conferência a revisar em detalhe. | Não verificado | Comprovar versão congelada, critérios e respostas por alvo. |
| D12 | Governança de elaboração, revisão, aprovação e publicação dos checklists. | Não confirmada nesta inspeção estática. | Não verificado | Demonstrar workflow e impedir publicação/alteração técnica sem aprovação. |
| D13 | Anexos vinculados, originais preservados, versionamento, hash, acesso e auditoria. | Evidência ponta a ponta não confirmada. | Não verificado — bloqueador | Comprovar armazenamento, hash, autorização, backup, retenção e recuperação. |
| D14 | Auditoria cronológica, individualizada e protegida. | `AuditLog`, `audit_service`, mecanismos de integridade. | Aderente estruturalmente | Testar cobertura de novos eventos, integridade, lacunas de sequência e acesso privilegiado. |
| D15 | Contas individuais, menor privilégio, concessão/revogação e rastreabilidade. | Autenticação, RBAC, escopos M2M, bloqueio e sessões. | Parcial | Conferir escopos por rota, revisão de acessos, desligamento/mudança de função e testes negativos. |
| D16 | Assinatura ligada ao conteúdo, identidade, intenção, tempo e verificação. | `ElectronicSignature`, manifesto/hash e reautenticação. | Parcial | Modalidade jurídica e tecnologia permanecem pendentes; provar vínculo com atos de recebimento/admissão e retificação. |
| D17 | Backup segregado de banco e documentos, retenção, monitoramento e restore. | Scripts/configuração presentes; restore não comprovado. | **Bloqueador** | Testar restauração real, retenção, cópia segregada, recuperação de evidências e RPO/RTO. |
| D18 | Identificadores únicos, permanentes e não reutilizáveis para cada agregado. | UUIDs e sequências para entidades operacionais. | Parcial | Especificar protocolo de negócio e provar unicidade/não reutilização para solicitação, recebimento, objeto, amostra e ensaio. |
| D19 | Chegada posterior vinculada, novo evento e nova conferência; preservar histórico. | Solicitação/recebimento existem; regra de chegada complementar não comprovada. | Não verificado | Confirmar suporte a complemento/reabertura autorizada e histórico sem sobrescrita. |
| D20 | Barreira formal de admissão antes de criar amostra. | `accept_custody_object()` cria `DeviceSample` quando decisão ACCEPTED, vinculando `origin_custody_object_id`. | Parcial — bloqueador | Comprovar todas as pré-condições, pendências, checklist, validação independente, quantidades, idempotência e concorrência. |

---

## 6. Rastreabilidade de G0-P01–G0-P30

As 30 propostas foram aprovadas como diretrizes de governança. A aprovação das propostas não significa que os respectivos entregáveis, parâmetros ou evidências estejam concluídos.

| Grupo | Propostas | Estado documental | Situação de implementação/evidência |
|---|---|---|---|
| Competências, checklists, prazos, devolução e assinatura | G0-P01 a P05; P16 a P20 | Aprovadas integralmente | Designações, checklists concretos, valores/canais, procedimentos e modalidade de assinatura continuam pendentes conforme DEC-SEFI-001. |
| Backup, identificadores, locais, anexos e retificação | G0-P06 a P10; P24 | Aprovadas integralmente | Backup/restore, catálogo de locais, especificação de anexos e retificação transversal precisam de evidência. |
| Homologação, CA, arquitetura, PostgreSQL, E2E | G0-P11 a P15 | Aprovadas integralmente | Execução com usuários, rastreabilidade CA, revisão independente, cobertura E2E e dossiê de evidências ainda precisam ser demonstrados. |
| Identidade externa, legado, idempotência, trilha, monitoramento | G0-P21 a P25 | Aprovadas integralmente | Isolamento externo, reconciliação de legado, contratos de idempotência e evidência de integridade/monitoramento requerem inspeção e teste. |
| Amostragem, consulta, integração, indicadores e continuidade | G0-P26 a P30 | Aprovadas integralmente | Regras por categoria, consulta/exportação, integração, indicadores e continuidade devem ser especificados e testados segundo o escopo institucional. |

**Regra:** não declarar nenhuma proposta G0-Pxx implementada apenas por sua aprovação. A matriz detalhada de entregáveis G0 permanece necessária e deve apontar artefatos/testes concretos.

---

## 7. Matriz de maturidade técnica

| Capacidade | Nota preliminar (0–5) | Confiança da avaliação | Evidência/observação | Lacuna dominante |
|---|---:|---|---|---|
| Arquitetura e organização do backend | 4 | Média | Domínios, serviços, rotas e modelos separados. | Revisão completa de dependências e contratos. |
| Solicitação e itens declarados | 3 | Média | `Solicitation`, `SolicitationItem`. | Campos, regras e testes de ciclo completo. |
| Recebimento e conferência | 2 | Alta | `Receipt`, `ReceiptItem`; inicialização de apresentação inadequada. | D03 e reconciliação de quantidades. |
| Custódia e movimentação | 3 | Média | `CustodyObject`, `CustodyEvent`. | Confirmação de transferência e localização autônoma. |
| Aceite e amostra | 3 | Média | Serviço transacional liga objeto aceito a `DeviceSample`. | Barreiras completas D20 e concorrência. |
| Execução de ensaios | 3 | Média | `TestExecution`, leituras, condições e dados brutos. | Intertravamento de insumos e evidência completa. |
| Métodos e versões | 3 | Baixa | Entidades de método/ensaio identificadas. | Congelamento da versão aplicada. |
| Equipamentos e qualificação | 3 | Média | Validação na abertura de execução. | Evidência temporal e ciclo completo. |
| Reagentes e padrões | 3 | Alta | Serviço próprio existe; integração na conclusão não evidenciada. | Intertravamento condicional. |
| OOS e CAPA | 4 | Média | OOS pode ser aberto automaticamente em resultado reprovado. | Validar fluxo integral e separar desvios de recebimento. |
| Revisão e laudos oficiais | 4 | Média | Modelos/serviços de relatório e assinatura. | Vínculo de manifesto, resultados, evidências e retificações. |
| Auditoria e integridade | 4 | Média | Serviço e mecanismos de integridade presentes. | Cobertura, verificação e ameaça privilegiada. |
| Anexos e evidências | 2 | Baixa | Não comprovado ponta a ponta. | Armazenamento, hash, controle, retenção e restore. |
| Integração instrumental | 3 | Média | Estrutura de upload/parsing e integração. | Inventário de protocolos e validação de dados. |
| Analytics | 2 | Baixa | Endpoints identificados. | Indicadores de processo e reconciliação. |
| Experiência do usuário | 2 | Baixa | Frontend SPA existente. | Avaliação de tarefas com usuários reais. |
| Segurança da aplicação | 3 | Média | RBAC, M2M scopes e SAST/SCA no CI identificados. | Cobertura de rotas, testes negativos e revisão independente. |
| Backup e recuperação | 1 | Alta | Scripts/configuração com pontos de falha documentados. | Restore comprovado e continuidade. |
| Documentação e validação | 2 | Alta | Documentos aprovados e matrizes existentes, mas defasados. | Baseline única e rastreabilidade requisito-teste-evidência. |

As notas não são uma média estatística de conformidade. São uma ferramenta de priorização de engenharia e devem ser revistas após inspeção aprofundada e execução de testes.

---

## 8. Achados técnicos prioritários e provas necessárias

### 8.1 Recebimento — achado confirmado por inspeção estática

Arquivo: `backend/app/services/receipt_service.py`, função `create_receipt()`.

Comportamento observado:
- itera por todos os itens declarados;
- define `presentation_status=PRESENTED`;
- define `presented_quantity=declared_quantity`;
- cria `CustodyObject` com `represented_quantity=declared_quantity`;
- cria evento inicial `INGRESSO`.

Impacto: material ausente pode ser representado como apresentado e sob custódia. Divergência direta com D03, D04, D19 e a semântica de custódia desde a chegada.

A correção deverá preservar todos os itens declarados no recebimento, mas só criar objeto de custódia para material efetivamente apresentado. A modelagem exata de apresentação e complemento deve respeitar as regras aprovadas de D19 e não deve ser inventada por conveniência técnica.

### 8.2 Aceite e criação de amostra — estrutura identificada, barreira incompletamente comprovada

Arquivo/serviço: operação `accept_custody_object()` no serviço de custódia.

Comportamento observado no trecho:
- exige objeto em `SOB_GUARDA`;
- verifica `version` esperada;
- em decisão favorável, cria `DeviceSample` com `origin_custody_object_id`;
- registra evento de encerramento da custódia pré-amostra;
- atualiza o objeto para `ACEITO` e vincula a amostra;
- registra auditoria.

Ponto de atenção: a presença do serviço não prova, isoladamente, que checklist, quantidades, pendências impeditivas, validação da coordenação, assinatura e todas as condições D20 sejam verificadas antes da criação. Também é necessário comprovar restrição de unicidade no banco e comportamento concorrente.

### 8.3 Reagentes — achado parcial confirmado

Arquivo: `backend/app/services/execution_service.py`, função `complete_execution()`.

O trecho inspecionado conclui a execução e registra resultado; não mostra verificação obrigatória de consumo de reagente/padrão condicionado ao método. O serviço de reagentes existe, mas sua integração transacional deve ser confirmada e evoluída.

### 8.4 Backup — risco crítico a comprovar

A auditoria documental anterior identificou:
- supressão potencial de erro em restauração;
- contagens coletadas sem necessariamente se tornarem condição de falha;
- PITR/WAL não comprovados;
- referências a recursos de execução que precisam ser conferidas;
- ausência de evidência de restore isolado.

O critério de encerramento é execução real e registrada de recuperação, não apenas presença de scripts.

### 8.5 CI e testes

A configuração de CI inclui verificações de backend, frontend, banco PostgreSQL e segurança estática. O estado verde do commit atual deve ser confirmado por consulta direta ao GitHub Actions quando utilizado como evidência. Não foi executada a suíte completa nesta atividade; por isso, nenhum CA/SIM foi declarado aprovado aqui.

---

## 9. Atualização conceitual necessária no M0.3

O M0.3 de 10/11/2026 deve ser revisado porque sua seção de diagnóstico afirma ausência de agregados que já existem na baseline atual.

A revisão deve preservar os princípios lógicos já aprovados e alterar apenas o diagnóstico de implementação:
1. reconhecer `Solicitation`, `SolicitationItem`, `Receipt`, `ReceiptItem`, `CustodyObject` e `CustodyEvent`;
2. descrever o mapeamento lógico para os modelos existentes;
3. registrar a divergência de `create_receipt()` na apresentação e geração inicial de custódia;
4. reconhecer a operação de aceite que cria `DeviceSample` vinculada ao objeto;
5. manter D20 como parcialmente atendida até prova de todas as pré-condições;
6. separar lacunas confirmadas, não verificadas e pendentes de decisão;
7. não declarar entidades lógicas como novas tabelas sem decisão de desenho físico;
8. manter o Gate G0 não aprovado e a implementação sujeita à autorização aplicável.

---

## 10. Plano de atualização dos documentos existentes

| Documento atual | Ação do Pacote A | Regra de preservação |
|---|---|---|
| `MODELO_LOGICO_REVISADO_DOMINIO_SEFI_M0_3.md` | Atualizar diagnóstico, baseline, mapeamento e status de implementação. | Não alterar decisões ratificadas nem transformar proposta lógica em schema aprovado. |
| `MATRIZ_ADERENCIA_DOMINIO_SEFI.md` | Substituir classificação defasada por referência à matriz atual e registrar adendo de baseline. | Preservar histórico v1.1 como fotografia de 10/11/2026. |
| `MATRIZ_PRONTIDAO_GATE_G0.md` | Atualizar evidências de código e separar status técnico de homologação institucional. | Não promover itens a concluídos sem artefato/teste/aceite correspondente. |
| `MATRIZ_LACUNAS_ARQUITETURAIS_LIMS.md` | Reclassificar lacunas já cobertas por componentes novos e manter as lacunas sem prova. | Não apagar histórico do diagnóstico anterior. |
| `ROADMAP_90_180_365_LIMS.md` | Reordenar roadmap conforme P0–P3 deste plano. | Não criar compromisso de prazo sem estimativa e capacidade acordadas. |

---

## 11. Critérios de saída do Pacote A

O Pacote A será considerado documentalmente concluído quando:
- [x] baseline e limitações forem registradas;
- [x] plano de correções e evolução estiver versionado;
- [x] matriz mestra mapear D01–D20 para componentes e lacunas;
- [ ] M0.3 atualizado e coerente com a baseline;
- [ ] matriz de aderência anterior receber adendo ou referência explícita de supersessão;
- [ ] matriz G0 separar evidência de software, evidência operacional e decisão institucional;
- [ ] matriz de lacunas e roadmap apontarem para o plano atual;
- [ ] revisão cruzada dos documentos não introduzir contradição de status.

O fechamento documental do Pacote A não equivale a aprovação de G0.

## 12. Parecer do Pacote A

A arquitetura existente deve ser aproveitada. O principal bloqueio funcional identificado é a representação incorreta da apresentação física e da custódia inicial dos itens. O mecanismo de aceite que cria a amostra a partir do objeto é um avanço estrutural relevante, mas ainda exige prova completa da barreira D20.

As correções P0 devem ser especificadas e testadas antes de serem implementadas. A recuperação de backup e a validação de anexos/evidências precisam de comprovação independente. A execução de ensaios deve incorporar os requisitos de insumos condicionais por método.

**Conclusão:** evoluir a implementação atual, sem reconstrução; manter G0 não aprovado até encerramento dos bloqueadores e homologação operacional.

---

## 13. Histórico

| Versão | Data | Alteração |
|---|---|---|
| 1.0 | 2026-11-18 | Primeira consolidação contra a baseline `e579701`; mapeamento lógico, aderência D01–D20, G0-P01–P30, maturidade, achados e plano documental. |
