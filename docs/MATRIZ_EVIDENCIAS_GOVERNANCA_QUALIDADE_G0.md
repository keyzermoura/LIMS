# Matriz de Evidências, Governança e Qualidade — Gate G0 LIMS-SEFI

**Versão:** 1.0  
**Data:** 2026-11-22  
**Branch de referência:** main  
**Commit documental desta auditoria:** 47133479685a9f1bbfbd12aa508cc46eaa3e913f  
**Natureza:** auditoria documental e de evidências; somente leitura para código, testes, banco e infraestrutura.  
**Parecer:** Gate G0 NÃO APROVADO; implementação SEFI NÃO AUTORIZADA.

## 1. Objetivo

Consolidar a relação entre decisões institucionais ratificadas, entregáveis do Gate G0, requisitos/critério de aceitação, cenários de validação, artefatos documentais e evidência técnica disponível. A matriz evita que aprovação de diretriz seja confundida com entrega concluída, que código de teste seja confundido com teste executado e que execução automatizada seja confundida com homologação operacional.

## 2. Hierarquia de evidências adotada

| Nível | Evidência | O que demonstra | O que não demonstra |
|---|---|---|---|
| E0 | Decisão/registro institucional aprovado | Baseline e diretriz ratificada | Implementação, execução ou homologação |
| E1 | Especificação/documento versionado | Requisito, processo ou critério descrito | Comportamento real do sistema |
| E2 | Código/serviço/API versionado | Componente implementado no commit examinado | Correção, cobertura ou execução |
| E3 | Teste automatizado versionado | Existe uma verificação automatizada | Que o teste executou ou que suas asserções são suficientes |
| E4 | Run CI identificada, commit e logs | Resultado de execução automatizada naquele commit | Homologação pelos operadores ou cobertura integral de requisitos |
| E5 | Evidência operacional observada e registrada | Execução do processo no ambiente/condições definidos | Aprovação institucional, salvo aceite formal registrado |
| E6 | Ata/termo de homologação e aceite competente | Validação operacional/institucional dentro do escopo aprovado | Autorização automática para ampliar escopo ou iniciar implementação adicional |

A classificação é aplicada por requisito, não por projeto inteiro. Evidência de nível superior não corrige automaticamente lacunas de rastreabilidade ou asserções inadequadas.

## 3. Baseline institucional aprovada

| Artefato/decisão | Estado documentado | Limite explícito |
|---|---|---|
| D01–D20 — DECISOES_PREVALIDACAO_SEFI_D01_D20.md v1.7 | Ratificadas integralmente em 2026-11-10 | Não equivale a homologação operacional, aprovação G0 ou autorização de implementação |
| G0-P01–P30 — mesmo registro, blocos 1 a 6 | 30 propostas aprovadas integralmente, sem ressalvas | A aprovação ratifica diretrizes/processos; designações, parâmetros, entregáveis, evidências e validações permanecem pendentes conforme cada decisão |
| M0.1 | Aprovado | Não substitui G0 |
| M0.2 — MODELO_CONCEITUAL_DOMINIO_SOLICITACAO_RECEBIMENTO.md | Aprovado funcionalmente | Complementos e validação operacional pendentes |
| M0.3 — MODELO_LOGICO_REVISADO_DOMINIO_SEFI_M0_3.md | Proposta lógica documentada | Revisão/aceite institucional e operacional pendentes |
| EST-REC-001 — ESTADOS_E_TRANSICOES_SOLICITACAO_RECEBIMENTO.md v1.7 | Especificação funcional consolidada para revisão | Não autoriza implementação |
| CA01–CA37 | Critérios definidos na especificação e matrizes | Execução e evidência por critério não concluídas |
| SIM01–SIM12 | Cenários descritos e parcialmente automatizados | Homologação operacional com representantes do SEFI não comprovada |

## 4. Rastreabilidade das decisões D01–D20

| Decisão | Resultado/entregável esperado | Artefato de referência | Evidência atual | Lacuna para encerramento |
|---|---|---|---|---|
| D01–D02 | Chegada identificada, autoria, metadados e tempos do fato/registro | D01–D20; EST-REC-001; M0.3 | E0/E1; serviços de recebimento auditados | Fluxo aderente, registros reais de teste e aceite operacional |
| D03–D04 | Quantidades reconciliáveis; objetos por material apresentado e decisões independentes | D01–D20; M0.3; matriz geral | E0/E1; divergências ACH-16, ACH-32 e ACH-34 | Corrigir criação prematura, provar reconciliação e linhagem |
| D05–D06 | Pendências saneáveis, reavaliação, recusa separada de destinação | D01–D20; EST-REC-001; contrato de aceite | E0/E1; lacunas ACH-15/17/19/23 | Fluxo completo e prova de custódia/destinação |
| D07–D08 | Transferência confirmada; localização independente | D01–D20; M0.3 | E0/E1; ACH-18/34/35 | Confirmação pelo destinatário e evento autônomo de localização |
| D09 | Retificação com original, motivo, autorização, evidência, assinatura e impacto | D01–D20; M0.3; contrato histórico | E0/E1; ACH-25/26/47 | Procedimento transversal, impacto e execução dos casos |
| D10 | Acúmulo de funções com independência quando exigida | D01–D20; matriz de competências | E0/E1; parte do RBAC e testes localizados | Designações nominais, matriz completa de competência e testes negativos |
| D11–D12 | Checklist por categoria, E/S/I, versão imutável e governança | D01–D20; EST-REC-001 | E0/E1; implementação parcial; ACH-30 | Checklists concretos aprovados, snapshot e bloqueio efetivo |
| D13–D14 | Evidências preservadas, versionadas, acessíveis por escopo e auditoria protegida | D01–D20; contrato histórico; M0.3 | E0/E1/E2 parcial; ACH-13/28/31/39 | Política de retenção, acesso contextual e comprovação operacional |
| D15–D16 | Contas individuais, menor privilégio, assinatura vinculada ao ato | D01–D20; M0.3 | E0/E1/E2 parcial; achados SEC-01–10 | Competência, escopo, política jurídica/tecnológica e testes completos |
| D17 | Backup, recuperação, segregação, monitoramento, retenção e restauração | D01–D20; G0-P06/P30; auditoria operacional v0.7 | E0/E1; script inspecionado | Política concreta, WAL/PITR, cópias protegidas e restauração comprovada |
| D18 | Identificadores distintos, únicos, permanentes e não reutilizados | D01–D20; M0.3 | E0/E1/E2 parcial; ACH-41 | DEC07, máscara/padrão e reconciliação de legado |
| D19 | Chegada complementar como novo fato sem retroatividade | D01–D20; M0.3 | E0/E1; EventoApresentacao proposto | Validação dos cenários e materialização futura autorizada |
| D20 | Amostra somente após apresentação, checklist, pendências, decisão, validação e custódia | D01–D20; contrato de aceite; M0.3 | E0/E1/E2 parcial; ACH-08/15/21/23 | Barreira transacional completa e testes negativos/concorrentes |

## 5. G0-P01–P30 — aprovação da diretriz versus entrega

| Grupo | Propostas | Diretriz aprovada | Entrega/evidência ainda necessária |
|---|---|---|---|
| Competência e processo | P01, P16 | Matriz de competências, titulares/substitutos, limites e independência | Designações nominais, vigência e formalização |
| Checklists | P02, P17 | Governança, critérios E/S/I, versão e aprovação | Inventário por categoria, critérios concretos, revisão da Qualidade e publicação formal |
| Prazos e comunicação | P03, P18 | Modelo de prazos, marcos, prorrogação e comunicação | Valores, dias/canais específicos e responsáveis |
| Devolução/destinação | P04, P20 | Processo rastreável de entrega e confirmação | Procedimento, formulários, alçadas e designações |
| Assinatura | P05, P19 | Requisitos funcionais e processo de avaliação | Parecer jurídico, atos sujeitos a assinatura e tecnologia/modalidade escolhida |
| Continuidade | P06 | Política de backup/restauração/continuidade | Frequência, retenção, RPO/RTO, infraestrutura, monitoramento e restore test |
| Identificadores/localização | P07, P08 | Semântica de identificadores e movimentações | Padrões, catálogo, inventário físico e permissões |
| Evidências/auditoria | P09, P24, P25 | Preservação, hash, acesso, retenção e proteção da trilha | Arquitetura, armazenamento, controles, WORM/ancoragem e testes |
| Retificação | P10, P27 | Avaliação de impacto e preservação do original | Metodologia, alçadas, critérios e casos executados |
| Validação e qualidade | P11–P15 | Metodologia SIM, CA, arquitetura/segurança, PostgreSQL e E2E | Execução real, logs, análise de cobertura, revisão independente e aceite |
| Identidade externa | P21 | Processo de identidade, autenticação e vínculo | Política, prova de identidade, representante, recuperação e habilitação |
| Legado | P22 | Inventário, migração e reconciliação controlada | Inventário, mapeamento, relatório quantitativo/qualitativo e exceções |
| Idempotência/concorrência | P23 | Contratos de repetição, versão e atomicidade | Parâmetros, implementação autorizada e testes concorrentes no PostgreSQL |
| Amostragem | P26 | Matriz técnica por categoria | Quantidades, agrupamento/fracionamento e critérios aprovados |
| Consulta/exportação | P28 | Filtros, ordenação, paginação e rastreabilidade | Campos, limites, parâmetros e testes |
| Segurança reforçada | P29 | Avaliação MFA/SSO, abuso, alertas e bloqueios | Política, ferramentas, parâmetros e testes |
| Retenção | P30 | Classificação, guarda e destinação | Tabela de temporalidade, parecer jurídico e aprovação competente |

## 6. Critérios de aceitação CA01–CA37

A matriz de prontidão G0 v0.4 registra a distribuição consolidada da auditoria:

| Parecer | Quantidade | Tratamento requerido |
|---|---:|---|
| Integralmente comprovado | 0 | Nenhum critério pode ser encerrado com o conjunto de evidências então auditado |
| Parcial | 17 | Completar integração, condição, evidência ou validação |
| Não conforme | 13 | Corrigir comportamento incompatível e demonstrar reteste |
| Não comprovado | 7 | Obter evidência objetiva ou registrar justificativa/decisão formal |
| **Total** | **37** | **CA01–CA37** |

A matriz geral v0.7 contém a rastreabilidade ampliada e achados ACH-01–ACH-57. Para cada CA, o pacote de encerramento deverá conter, no mínimo: ID e versão do requisito; pré-condições; dados de teste; passos; resultado esperado; commit/ambiente; ID da execução; resultado obtido; log/evidência; revisão da asserção; defeito associado; reteste; aprovador técnico e aceite institucional quando aplicável.

**Não se declara nesta matriz que os 37 critérios tenham sido individualmente reexecutados nesta rodada.** A distribuição é a síntese da auditoria registrada em MATRIZ_PRONTIDAO_GATE_G0.md v0.4.

## 7. SIM01–SIM12 — estado da evidência

O documento VALIDACAO_CENARIOS_OPERACIONAIS_SEFI.md v2.1 distingue corretamente teste versionado, executado, aprovado e homologado. A seção 7.3 prevalece sobre a tabela histórica da seção 5, cuja marcação GREEN não foi integralmente atualizada.

| Cenário | Evidência disponível | Situação para Gate |
|---|---|---|
| SIM01 | Teste versionado; divergências na barreira de aceite | Execução atual não revalidada; homologação não comprovada |
| SIM02 | Teste versionado; objeto pode existir antes da confirmação de apresentação | Execução atual não revalidada; asserção insuficiente para INV-04 |
| SIM03 | Teste versionado; campos de quantidade existem | Execução atual não revalidada; reconciliação não demonstrada |
| SIM04 | Teste versionado; múltiplos objetos/decisões | Execução atual não revalidada; linhagem e independência parcial |
| SIM05 | Teste versionado; checklist/pendência/revisão | Execução atual não revalidada; reavaliação/barreira incompleta |
| SIM06 | Teste versionado; ramo de recusa | Execução atual não revalidada; custódia/destinação não comprovadas |
| SIM07 | Teste versionado; transferência imediata | Execução atual não revalidada; confirmação destinatário ausente |
| SIM08 | Teste versionado; localização tratada em evento existente | Execução atual não revalidada; evento independente não comprovado |
| SIM09 | Teste versionado; retificação de partes do ciclo | Execução atual não revalidada; impacto transversal incompleto |
| SIM10 | Teste versionado; versão obsoleta e replay sequencial | Execução atual não revalidada; concorrência real/idempotência atômica não provadas |
| SIM11 | Teste versionado; RBAC | Execução atual não revalidada; isolamento por unidade/recurso/anexo não comprovado |
| SIM12 | Teste versionado; cenário complementar descrito | Execução atual não revalidada; EventoApresentacao ainda proposto |

A simulação documental não substitui sessão operacional com representantes dos perfis envolvidos. O pacote de homologação deve conter participantes/funções, ambiente e versão, roteiro, evidências observáveis, desvios, decisões, responsável, data e aceite formal.

## 8. Evidência atual do CI e baseline de commits

Foi consultada a execução do workflow CI associada ao commit documental `47133479685a9f1bbfbd12aa508cc46eaa3e913f`, run `44972383967`.

| Job | Resultado | Significado |
|---|---|---|
| Segurança (SAST/SCA) | Sucesso | Bandit e pip-audit passaram no job; não equivale a auditoria integral de segurança |
| Backend | Falha em Alembic upgrade head | Testes posteriores não foram alcançados |
| Frontend | Falha em npm ci | Typecheck/build não foram alcançados |
| Docker | Falha no build | Smoke test não foi alcançado |

A execução confirma falhas de pipeline no commit acima. Os motivos específicos estão registrados como ACH-53 e ACH-54 na Matriz Geral v0.7. Run: https://github.com/keyzermoura/LIMS/actions/runs/44972383967.

**Regra de evidência:** toda matriz de resultado deve fixar um commit único por rodada. Resultados de HEAD histórico (inclusive runs verdes anteriores) não podem ser apresentados como resultado do HEAD atual. Para fechar um CA, anexar a execução que contém o teste correspondente e o commit exato.

## 9. Achado documental de consistência

**GOV-01 — Rótulos históricos GREEN permanecem na tabela SIM01–SIM12 apesar da reclassificação posterior.**

Na seção 5 de VALIDACAO_CENARIOS_OPERACIONAIS_SEFI.md v2.1, SIM02–SIM12 ainda aparecem como “APROVADO (GREEN)” e o histórico da v2.0 menciona 100% GREEN. A seção 7, posterior e datada de 2026-11-21, suspende expressamente essa conclusão e determina que execução atual e homologação não estão comprovadas. A precedência está explicada no texto, mas a coexistência dos rótulos antigos cria risco de leitura seletiva e uso indevido como evidência de Gate.

**Ação documental recomendada:** em atualização futura, substituir os rótulos históricos na tabela por “resultado histórico — não revalidado no commit atual” e identificar a seção 7 como status vigente. Não alterar o registro histórico da versão 2.0; preservar a informação de que aquela declaração foi feita e depois reavaliada.

## 10. Matriz de fechamento por pacote de evidência

| Pacote | Conteúdo mínimo | Dependências | Estado atual |
|---|---|---|---|
| GOV-01 | Correção de rótulos históricos SIM | Atualização documental autorizada | Aberto |
| GOV-02 | Matriz nominal de competências e substitutos | P01/P16; autoridade institucional | Pendente |
| GOV-03 | Checklists por categoria aprovados | P02/P17; especialistas/Qualidade/Coordenação | Pendente |
| GOV-04 | Prazos, canais, devolução e destinação | P03/P04/P18/P20 | Pendente |
| GOV-05 | Política/modalidade de assinatura | P05/P19; Jurídico/TI | Pendente |
| GOV-06 | Backup, retenção, RPO/RTO e restore test | P06/P30; Infraestrutura/Jurídico | Pendente |
| GOV-07 | Identificadores, localização e catálogo físico | P07/P08; gestão laboratorial | Pendente |
| GOV-08 | Anexos, integridade e trilha de auditoria | P09/P24/P25; Segurança/Infraestrutura | Pendente |
| GOV-09 | Identidade e vínculo de solicitantes externos | P21; governança de acesso | Pendente |
| GOV-10 | Inventário e reconciliação de legado | P22; donos dos dados | Pendente |
| GOV-11 | Contratos de concorrência/idempotência | P23; arquitetura/QA | Pendente |
| GOV-12 | Matriz de amostragem por categoria | P26; especialistas técnicos | Pendente |
| GOV-13 | Metodologia de impacto de retificações | P27; Qualidade/Coordenação | Pendente |
| GOV-14 | Consulta histórica/exportação | P28; negócio/segurança | Pendente |
| GOV-15 | Política de segurança reforçada | P29; Segurança/TI | Pendente |
| GOV-16 | Homologação SIM01–SIM12 | P11; representantes SEFI | Não comprovada |
| GOV-17 | Execução e evidência CA01–CA37 | P12; QA/arquitetura | Não concluída |
| GOV-18 | Revisão independente de arquitetura/segurança | P13; revisor independente | Parcial; achados técnicos registrados |
| GOV-19 | PostgreSQL concorrência/integridade | P14; ambiente de teste | Não comprovada na execução CI atual |
| GOV-20 | E2E fluxo crítico | P15; ambiente e perfis | Não comprovada |

## 11. Critérios para recomendar encerramento do Gate G0

O Gate somente poderá ser submetido a decisão formal quando houver:

1. Todos os entregáveis G0-01–G0-26 identificados e com responsável, aprovador, versão e evidência.
2. CA01–CA37 individualizados, rastreados a requisitos/decisões, testes e resultados; desvios classificados e tratados.
3. SIM01–SIM12 executados com operadores/representantes autorizados e atas/evidências.
4. Revisão de arquitetura e segurança independente, com achados impeditivos encerrados ou formalmente aceitos por autoridade competente.
5. CI verde no commit candidato, incluindo migrações, PostgreSQL, frontend, Docker e E2E exigidos; testes skip justificados e aceitos.
6. Backup/restauração testados e política de continuidade aprovada.
7. Dependências institucionais — competência, checklists, prazos, assinatura, devolução, retenção, identidade externa e critérios por categoria — formalizadas.
8. Matriz final de rastreabilidade e parecer consolidado submetidos à autoridade competente.
9. Decisão formal explícita do Gate G0, separada da aprovação das diretrizes D01–D20 e G0-P01–P30.

## 12. Limites desta auditoria

- Auditoria documental e consulta de evidências versionadas/CI; não houve execução local de testes, alteração de código, schema, API, frontend, CI ou infraestrutura.
- Não houve homologação com operadores, inspeção de ambiente institucional, revisão jurídica, designação nominal de responsáveis ou aprovação de política de retenção.
- Os estados “pendente” e “não comprovado” não significam necessariamente que a atividade inexista; significam que a evidência acessível examinada não permite declará-la concluída.
- ACH-01–ACH-57 permanecem na Matriz Geral de Rastreabilidade; esta matriz acrescenta o achado documental GOV-01 sem reclassificar os achados técnicos.

## 13. Parecer

A governança institucional estabeleceu uma baseline robusta: D01–D20 e G0-P01–P30 foram ratificadas. Entretanto, aprovação de diretrizes não é aprovação dos entregáveis. A evidência de qualidade permanece incompleta: nenhum CA01–CA37 foi classificado como integralmente comprovado na auditoria consolidada; SIM01–SIM12 não têm homologação operacional comprovada; dependências institucionais concretas continuam pendentes; e a execução CI mais recente consultada falhou em migrações, frontend e Docker.

**GATE G0: NÃO APROVADO.**  
**IMPLEMENTAÇÃO SEFI: NÃO AUTORIZADA.**  
**Recomendação:** manter o bloqueio de implementação e conduzir o fechamento dos pacotes GOV-01–GOV-20, priorizando primeiro os bloqueadores de CI/ambiente e as evidências de validação operacional.

## 14. Histórico

| Versão | Data | Descrição |
|---|---|---|
| 1.0 | 2026-11-22 | Primeira matriz consolidada de governança, qualidade, baseline D01–D20/G0-P01–P30, CA01–CA37, SIM01–SIM12, evidência CI, dependências e critérios de encerramento G0. |
