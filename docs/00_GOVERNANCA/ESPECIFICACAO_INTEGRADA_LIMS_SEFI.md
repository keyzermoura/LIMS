# Especificação Integrada do LIMS-SEFI

**Identificador:** ESP-INT-LIMS-SEFI-001  
**Versão:** 0.1 — estrutura inicial  
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
| [Modelo Lógico M0.3](../MODELO_LOGICO_REVISADO_DOMINIO_SEFI_M0_3.md) | Modelo lógico proposto para revisão | Elaborado; aguarda revisão/validação |
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
| 3 | Processos ponta a ponta | EST-REC-001, SIM-SEFI-REC-001, D01–D20 | Aguardando recuperação/integração das fontes |
| 4 | Requisitos funcionais | D01–D20, G0-P01–P30, critérios CA | Parcial; rastreabilidade detalhada pendente |
| 5 | Modelo de domínio | M0.1/M0.2/M0.3 e fontes relacionadas | M0.3 aguarda validação |
| 6 | Estados, transições e eventos | EST-REC-001, M0.3 | Parcial; propostas pendentes |
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
| 17 | Arquitetura-alvo | Diagnóstico, requisitos e decisões técnicas | Não iniciada |
| 18 | Critérios de aceitação e testes | CA01–CA37, SIM01–SIM12, G0-P11–P15 | Fontes detalhadas a recuperar; execução não comprovada |
| 19 | Rastreabilidade integral | Todas as fontes anteriores | Em elaboração |
| 19.1 | Matriz D01–D20 × domínio × CA × SIM × evidência | D01–D20, M0.3, EST-REC-001 e registros SIM | Primeira versão documental criada; associação CA em consolidação; SIM pendente |
| 20 | Pendências, decisões e histórico | Catálogo Mestre e registros de validação | Em elaboração |

## 5. Matriz inicial de rastreabilidade

A [Matriz Inicial de Rastreabilidade D01–D20](../05_RASTREABILIDADE/MATRIZ_RASTREABILIDADE_D01_D20.md) foi criada na branch documental. Ela relaciona decisões às entidades, estados, eventos e invariantes propostos em M0.3. A associação detalhada aos critérios CA01–CA37 está em consolidação a partir de EST-REC-001; os cenários SIM01–SIM12 e suas evidências ainda precisam ser localizados.

## 6. Registro de questões que não podem ser presumidas como resolvidas

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

## 7. Estado formal

- Especificação integrada: **ESTRUTURA INICIAL — EM ELABORAÇÃO**.
- D01–D20: **RATIFICADAS**, sem alteração.
- G0-P01–P30: **APROVADAS**, preservados os limites e detalhamentos pendentes.
- M0.3: **AGUARDANDO REVISÃO/VALIDAÇÃO**.
- Gate G0: **NÃO APROVADO**.
- Implementação: **NÃO AUTORIZADA**.
- Escopo desta branch: **DOCUMENTAÇÃO**.
