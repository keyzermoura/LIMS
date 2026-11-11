# Especificação Integrada do LIMS-SEFI

**Identificador:** ESP-INT-LIMS-SEFI-001  
**Versão:** 0.3 — baseline de domínio/processos integrada  
**Data:** 2026-11-11  
**Branch de trabalho:** `docs/integracao-especificacao-sefi`  
**Status:** documento integrador em elaboração; não aprovado.

## 1. Finalidade

Este documento será o ponto de entrada integrado para a especificação do LIMS-SEFI. Reunirá requisitos, processos, domínio, regras, arquitetura, controles e critérios de verificação por referência aos documentos-fonte. Não substituirá os registros originais nem criará aprovação por consolidação editorial.

## 2. Documentos de governança e fontes primárias

| Fonte | Papel | Status conhecido |
|---|---|---|
| [Registro D01–D20 e G0-P01–P30](../DECISOES_PREVALIDACAO_SEFI_D01_D20.md) | Baseline de decisões ratificadas/aprovadas | D01–D20 ratificadas; P01–P30 aprovadas, com dependências explicitadas |
| [Matriz de Prontidão G0](../MATRIZ_PRONTIDAO_GATE_G0.md) | Entregáveis, evidências, bloqueadores e situação do Gate | G0 não aprovado |
| [Matriz de Aderência](../MATRIZ_ADERENCIA_DOMINIO_SEFI.md) | Diagnóstico do software existente versus domínio SEFI | Aderência parcial/insuficiente para admissão |
| [Modelo Conceitual M0.2](../MODELO_CONCEITUAL_DOMINIO_SOLICITACAO_RECEBIMENTO.md) | Modelo conceitual aprovado funcionalmente; cardinalidades canônicas | M0.2 v0.7 aprovado funcionalmente; validação operacional pendente |
| [Estados e Transições](../ESTADOS_E_TRANSICOES_SOLICITACAO_RECEBIMENTO.md) | Estados, transições, permissões e critérios CA01–CA37 | Proposta documental consolidada; validação operacional pendente |
| [Modelo Relacional Preliminar](../MODELO_RELACIONAL_PRELIMINAR_LIMS.md) | Tradução relacional preliminar | Proposta técnica; não aprovada para implementação |
| [Contrato de Histórico e Aceite](../CONTRATO_HISTORICO_UNIFICADO_E_ACEITE.md) | Histórico unificado e transação de aceite | Proposta técnica; não aprovada para implementação |
| [Auditoria de Consistência EST01–EST10](../AUDITORIA_CONSISTENCIA_EST01_EST10.md) | Achados AUD01–AUD22 e consistência funcional | Auditoria documental concluída; validação operacional e dependências técnicas pendentes |
| [Revisão Multidisciplinar](../REVISAO_MULTIDISCIPLINAR_MAQUINA_ESTADOS_CA01_CA24.md) | Parecer multidisciplinar e revisão de critérios | Revisão documental concluída; dependências e validação operacional pendentes |
| [Simulação de Mesa SIM01–SIM12](../VALIDACAO_CENARIOS_OPERACIONAIS_SEFI.md) | Cenários operacionais e relação com CA | Simulação documental; não é homologação nem teste de software |
| [Modelo Lógico M0.3](../MODELO_LOGICO_REVISADO_DOMINIO_SEFI_M0_3.md) | Modelo lógico proposto para revisão | Elaborado; aguarda revisão/validação |
| [Baseline Consolidada de Domínio e Processos](../02_DOMINIO/BASELINE_CONSOLIDADA_DOMINIO_PROCESSOS_SEFI.md) | Referência integrada que preserva cardinalidades e separa regras aprovadas de refinamentos pendentes | v0.1; proposta documental não validada |
| [Comparação M0.2 × M0.3](../02_DOMINIO/COMPARACAO_M0_2_M0_3.md) | Preservação de cardinalidades, refinamentos e divergências de nomenclatura | Análise documental inicial; não validada |
| [Requisitos Funcionais RF-001–RF-020](../03_ESPECIFICACAO_FUNCIONAL/REQUISITOS_FUNCIONAIS_SEFI_RF001_RF020.md) | Decomposição de D01–D20 em requisitos funcionais | Versão inicial derivada de decisões ratificadas; detalhamento/testes pendentes |
| [Catálogo Mestre](CATALOGO_MESTRE_DOCUMENTAL.md) | Inventário, versões, fontes e limitações | Inventário ampliado; ainda não exaustivo |
| [Plano de Integração](PLANO_DE_INTEGRACAO_DOCUMENTAL.md) | Escopo, pacotes, governança e critérios de execução | Plano de trabalho documental |

## 3. Regras de interpretação

1. D01–D20 e G0-P01–P30 devem ser interpretadas conforme o registro primário e seus limites.
2. O modelo M0.3 é uma proposta lógica de trabalho. As questões M03-01 a M03-16 não são consideradas resolvidas apenas por constarem do documento.
3. A matriz de aderência é diagnóstico do produto existente, não especificação-alvo.
4. A matriz G0 é instrumento de prontidão; aprovação de diretriz não comprova execução ou evidência.
5. O README e o código descrevem a solução existente e não prevalecem sobre a baseline funcional ratificada.
6. Em caso de conflito, a especificação integrada apontará as fontes e registrará a decisão necessária, sem alterar unilateralmente a baseline.

## 4. Estrutura planejada da especificação

| Seção | Conteúdo previsto | Fontes necessárias | Situação |
|---|---|---|---|
| 1 | Objetivo, escopo, atores e glossário | Decisões, EST-REC-001, documentos institucionais | Em elaboração |
| 2 | Governança, papéis, competências e segregação | D10, D12, D15, G0-P01, P16 | Diretrizes aprovadas; designações pendentes |
| 3 | Processos ponta a ponta | EST-REC-001, SIM-SEFI-REC-001, D01–D20 | Baseline de domínio/processos v0.1 e mapa PROC-01–PROC-17 v0.2 elaborados; validação operacional pendente |
| 4 | Requisitos funcionais | D01–D20, G0-P01–P30, critérios CA | RF-001–RF-020 elaborados; decomposição detalhada e validação pendentes |
| 5 | Modelo de domínio | M0.1/M0.2/M0.3 e fontes relacionadas | Baseline consolidada v0.1 elaborada; M0.3 e refinamentos aguardam validação |
| 6 | Estados, transições e eventos | EST-REC-001, M0.3 | Fontes recuperadas; diferenças de nomenclatura e refinamentos pendentes |
| 7 | Regras de negócio e invariantes | D01–D20, M0.3 | Parcial; M03-01 a M03-16 em aberto |
| 8 | Checklists, critérios e evidências | D11–D13, G0-P02/P09/P17/P24 | Estrutura aprovada; conteúdo específico pendente |
| 9 | Custódia, localização e destinação | D06–D08, G0-P04/P08/P20 | Diretrizes aprovadas; procedimento e parâmetros pendentes |
| 10 | Amostras, ensaios e laudos | D20, M0.3, fluxo técnico existente | Compatibilização pendente |
| 11 | Retificações e impacto | D09, G0-P10/P27 | Metodologia detalhada pendente |
| 12 | Segurança, identidade e acesso | D10, D15, G0-P21/P23/P29 | Requisitos aprovados; arquitetura e políticas finais pendentes |
| 13 | Assinatura eletrônica e auditoria | D14/D16, G0-P05/P19/P25 | Requisitos aprovados; modalidade e parâmetros pendentes |
| 14 | Documentos, anexos e evidências digitais | D13, G0-P09/P24/P30 | Requisitos aprovados; arquitetura e parâmetros pendentes |
| 15 | Dados, integrações e migração | D18, G0-P07/P22/P23 | Especificação e reconciliação pendentes |
| 16 | Continuidade, backup e retenção | D17, G0-P06/P30 | Diretrizes aprovadas; parâmetros e evidências pendentes |
| 17 | Arquitetura-alvo | Diagnóstico, requisitos e decisões técnicas | Não iniciada; requisitos transversais RT-001–RT-017 consolidados como insumo |
| 18 | Critérios de aceitação e testes | CA01–CA37, SIM01–SIM12, G0-P11–P15 | Fontes recuperadas; casos preliminares elaborados; execução não comprovada |
| 19 | Rastreabilidade integral | Todas as fontes anteriores | Em elaboração |
| 19.1 | Matriz D01–D20 × domínio × CA × SIM × evidência | D01–D20, M0.3, EST-REC-001 e registros SIM | Primeira versão documental criada; associação CA em consolidação; SIM pendente |
| 20 | Pendências, decisões e histórico | Catálogo Mestre e registros de validação | Em elaboração |

## 5. Processos e requisitos funcionais

A [Baseline Consolidada de Domínio e Processos](../02_DOMINIO/BASELINE_CONSOLIDADA_DOMINIO_PROCESSOS_SEFI.md) estabelece a referência integrada de entidades, cardinalidades, dimensões de estado, eventos, invariantes, processos e pendências, preservando as fontes aprovadas e identificando refinamentos ainda não validados. O [Mapa de Processos Operacionais PROC-01–PROC-17](../02_DOMINIO/MAPA_PROCESSOS_OPERACIONAIS_SEFI_PROC01_PROC16.md) organiza os fluxos de solicitação, chegada, apresentação, custódia, conferência, pendência, decisão, validação, admissão, movimentação, destinação, retificação, chegada posterior, evidências e consulta; PROC-17 trata continuidade/backup/recuperação como controle transversal. O mapa é documental e ainda depende de validação operacional.

## 5.1 Requisitos funcionais e matriz de rastreabilidade

O [Catálogo de Requisitos Funcionais RF-001–RF-020](../03_ESPECIFICACAO_FUNCIONAL/REQUISITOS_FUNCIONAIS_SEFI_RF001_RF020.md) decompõe D01–D20 sem alterar as decisões-fonte.

## 5.2 Matrizes de rastreabilidade

A [Matriz D01–D20 × domínio × CA × SIM](../05_RASTREABILIDADE/MATRIZ_RASTREABILIDADE_D01_D20.md) relaciona as decisões ratificadas ao modelo lógico e aos critérios/cenários documentados. A [Matriz G0-P01–P30 × RF × RT × artefatos](../05_RASTREABILIDADE/MATRIZ_RASTREABILIDADE_G0_P01_P30.md) relaciona as propostas G0 aprovadas aos requisitos e entregáveis documentais. Ambas são matrizes analíticas iniciais e ainda não validadas.

## 5.3 Matriz inicial de rastreabilidade

A [Matriz Inicial de Rastreabilidade D01–D20](../05_RASTREABILIDADE/MATRIZ_RASTREABILIDADE_D01_D20.md) foi criada na branch documental. Ela relaciona decisões às entidades, estados, eventos e invariantes propostos em M0.3. A associação analítica aos critérios CA01–CA37 foi iniciada a partir de EST-REC-001. Os cenários SIM01–SIM12 foram recuperados e estão relacionados a decisões/CA na própria fonte; permanecem simulação documental, sem validação operacional ou teste de software.

## 6. Requisitos transversais

Os [Requisitos Transversais e de Qualidade RT-001–RT-017](../04_REQUISITOS/REQUISITOS_TRANSVERSAIS_QUALIDADE_SEFI_RT001_RT017.md) consolidam controles de identidade, competência, assinatura, auditoria, evidências, integridade, idempotência, consultas, backup, migração, retenção, proteção contra abuso, testes, identificadores, localização e comunicação.

## 7. Plano preliminar de testes

O [Plano Preliminar de Casos de Teste CA01–CA37](../06_VALIDACAO/PLANO_CASOS_TESTE_CA01_CA37.md) foi elaborado a partir de EST-REC-001 v1.7. Ele especifica pré-condições genéricas, ações, resultados esperados e evidências sugeridas. Todos os casos permanecem não executados; CA25–CA37 continuam identificados como complementos propostos.

## 8. Registro de questões que não podem ser presumidas como resolvidas

- M03-01 a M03-16, conforme M0.3.
- Designações nominais de competências e substitutos.
- Checklists técnicos por categoria e critérios E/S/I concretos.
- Prazos, canais oficiais e regras numéricas.
- Procedimentos e formulários de devolução/destinação.
- Modalidade jurídica e tecnologia de assinatura.
- Padrões de protocolo, accession e QR.
- Identidade e autenticação de solicitantes externos.
- Arquitetura, parâmetros e política de anexos/evidências.
- RPO/RTO, frequência, retenção e evidência de restauração.
- Metodologia de retificação e impacto.
- Plano e reconciliação dos dados legados.
- Contratos de idempotência, concorrência e versionamento.
- Classificação, temporalidade e destinação das informações.
- Validação operacional SIM01–SIM12.
- Especificação, execução e evidências dos CA01–CA37.

## 9. Estado formal

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-11 | Estrutura inicial da especificação integrada. |
| 0.2 | 2026-11-11 | Integra mapa de processos e matrizes de rastreabilidade. |
| 0.3 | 2026-11-11 | Incorpora baseline consolidada de domínio/processos e atualiza o mapa para PROC-01–PROC-17. |


- Especificação integrada: **EM ELABORAÇÃO — baseline de domínio/processos v0.1 incorporada**.
- D01–D20: **RATIFICADAS**, sem alteração.
- G0-P01–P30: **APROVADAS**, preservados os limites e detalhamentos pendentes.
- Baseline consolidada de domínio/processos v0.1: **PROPOSTA DOCUMENTAL — NÃO VALIDADA**.
- M0.3: **AGUARDANDO REVISÃO/VALIDAÇÃO**.
- Gate G0: **NÃO APROVADO**.
- Implementação: **NÃO AUTORIZADA**.
- Escopo desta branch: **DOCUMENTAÇÃO**.
