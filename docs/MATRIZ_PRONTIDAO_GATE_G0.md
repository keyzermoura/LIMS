# Matriz Consolidada de Prontidão — Gate G0 do LIMS–SEFI

**Identificador:** MAT-G0-SEFI-001  
**Versão:** 0.1  
**Data:** 2026-11-10  
**Repositório:** `keyzermoura/LIMS`  
**Branch:** `main`  
**Natureza:** instrumento de gestão de evidências e prontidão; não constitui aprovação do Gate G0 nem autorização de implementação.

---

## 1. Objetivo

Converter as decisões funcionais e propostas aprovadas em entregáveis verificáveis, com critérios objetivos de conclusão, evidências exigidas, responsáveis institucionais a designar e dependências. A matriz distingue aprovação de diretrizes, conclusão documental, validação operacional e comprovação técnica.

## 2. Regras de leitura e classificação

- **Aprovado em princípio:** decisão institucional registrada, mas ainda pode exigir procedimento, parâmetro, designação ou evidência.
- **Documentado — validar:** existe documento de referência; seu conteúdo precisa ser confirmado contra a baseline vigente e, quando aplicável, validado por usuários.
- **Pendente:** o entregável ou a evidência ainda não foi apresentado como concluído.
- **Não verificado:** não foi possível confirmar o artefato ou resultado no material examinado; não significa que inexista no repositório ou em outro ambiente.
- **Bloqueador do Gate:** deve estar concluído e evidenciado antes da decisão final de G0.

Nenhum status é elevado a concluído apenas porque uma proposta relacionada foi aprovada.

## 3. Síntese executiva

| Dimensão | Situação apurada | Consequência para G0 |
|---|---|---|
| Decisões D01–D20 | Ratificadas integralmente pelo responsável pela Validação Institucional; registro versão 1.7 | Baseline funcional ratificada; não substitui homologação |
| Propostas G0-P01–P30 | 30/30 aprovadas integralmente, sem ressalvas | Processos e diretrizes aprovados; detalhamentos e evidências continuam necessários |
| SIM01–SIM12 | Simulação documental existente; validação operacional com usuários/representantes do SEFI não comprovada | Bloqueador |
| CA01–CA37 | Critérios documentados/referenciados; execução, resultados, evidências e aprovação de QA não comprovados | Bloqueador |
| Arquitetura e segurança | Diretrizes e riscos identificados; revisão técnica baseada em implementação/ambiente não comprovada | Bloqueador |
| PostgreSQL, integridade e concorrência | Requisitos conceituais aprovados; execução em banco real e evidências de concorrência não comprovadas | Bloqueador |
| E2E e CI | Necessidade reconhecida; execução integral e resultados reproduzíveis não comprovados | Bloqueador |
| Parâmetros e designações institucionais | Diversas definições permanecem dependentes de autoridades, procedimentos e áreas competentes | Bloqueador conforme aplicabilidade |

**Conclusão preliminar:** o projeto possui baseline funcional e diretrizes institucionais amplamente ratificadas, mas a documentação examinada não sustenta a aprovação do Gate G0. A recomendação atual é **NO-GO para implementação** até que os bloqueadores e suas evidências sejam encerrados e avaliados.

## 4. Matriz de entregáveis e evidências

| ID | Entregável / decisão a materializar | Evidência objetiva exigida | Critério de aceitação | Responsável proposto* | Dependências | Situação |
|---|---|---|---|---|---|---|
| G0-01 | Baseline funcional D01–D20 e G0-P01–P30 | Registro institucional versionado e histórico de decisões | Todas as decisões rastreáveis; ressalvas e limites explícitos; versão vigente confirmada | Responsável pela Validação Institucional | Nenhuma | **Concluído documentalmente** |
| G0-02 | Matriz de competências, autoridades e substitutos | Ato/designação institucional, matriz de perfis e alçadas | Cada decisão crítica possui autoridade titular e substituta; segregação e impedimentos definidos | Gestão SEFI / autoridade competente | G0-P01, G0-P16, D10, D15 | **Pendente** |
| G0-03 | Checklists técnicos por categoria e critérios E/S/I | Checklists aprovados, versionados, com histórico e casos de aplicação | Critérios objetivos, evidências e alçadas definidos; critérios E não dispensados informalmente | Responsável técnico / Qualidade | G0-P02, G0-P17, D11–D12 | **Pendente** |
| G0-04 | Prazos, comunicações e notificações | Procedimento/tabela de prazos, canais oficiais, modelos e registros de envio | Início/fim de contagem, destinatários, escalonamento, prorrogação e comprovação definidos | Coordenação / área institucional competente | G0-P03, G0-P18, D05, D09 | **Pendente** |
| G0-05 | Devolução, retirada e destinação | Procedimento aprovado, formulários, alçadas e comprovantes-modelo | Custódia só se encerra após entrega/destinação efetiva e comprovada; exceções autorizadas | Coordenação / autoridade competente | G0-P04, G0-P20, D06–D07 | **Pendente** |
| G0-06 | Modalidade e política de assinatura eletrônica | Parecer/decisão institucional, especificação e evidência de validação | Identidade, intenção, integridade, autoria, data/hora, validação e verificabilidade definidos para cada ato | Gestão / Jurídico / TI / Qualidade | G0-P05, G0-P19, D16 | **Pendente** |
| G0-07 | Continuidade, backup e recuperação | Política, RPO/RTO aprovados, logs de backup e relatório de teste de restauração | Backup íntegro; restauração testada em ambiente controlado; evidência de recuperação e responsáveis | TI / infraestrutura | G0-P06, D17 | **Pendente** |
| G0-08 | Identificadores, protocolo e QR | Especificação de unicidade, regras de geração e testes de colisão/consulta | Identificadores únicos, não reutilizados, rastreáveis e independentes por entidade | Produto / arquitetura / QA | G0-P07, D18 | **Documentado — validar** |
| G0-09 | Localizações e movimentação física | Inventário de locais, taxonomia, perfis autorizados e registros de movimentação | Origem/destino, responsável, data/hora e motivo registrados; trilha coerente com custódia | Operação SEFI / Qualidade | G0-P08, D07–D08 | **Pendente** |
| G0-10 | Gestão de documentos e anexos | Especificação de metadados, formatos, limites, hash, versões, retenção e recuperação; testes | Integridade e vínculo documental verificáveis; acesso autorizado; corrupção/indisponibilidade tratadas | Arquitetura / segurança / QA | G0-P09, G0-P24, D13 | **Pendente** |
| G0-11 | Retificações e avaliação de impacto | Procedimento/matriz de impacto por etapa, formulários e casos de teste | Original preservado; justificativa, evidência, autorização e efeitos derivados registrados; sem retroatividade indevida | Coordenação / Qualidade / responsável técnico | G0-P10, G0-P27, D09 | **Pendente** |
| G0-12 | Validação operacional SIM01–SIM12 | Roteiros executados, participantes/funções, atas, resultados, desvios e aceite | Todos os cenários executados com representantes autorizados do SEFI; divergências tratadas; aceite formal | Responsável pela Validação Institucional / representantes SEFI | D01–D20; matriz de competências | **Pendente — bloqueador** |
| G0-13 | Critérios de aceitação CA01–CA37 | Matriz requisito–teste–resultado–evidência, com versão e rastreabilidade | Cada CA possui pré-condição, passos, resultado esperado/obtido, evidência, status e aprovador; falhas críticas encerradas | QA / responsáveis de domínio | G0-P12; SIM01–SIM12 | **Documentado — execução não comprovada; bloqueador** |
| G0-14 | Revisão de arquitetura e segurança | Relatório técnico com diagramas, ameaças, controles, riscos residuais e parecer | Fluxos, fronteiras de confiança, autorização no servidor, segredos, logs, anexos, backup e operação revisados | Arquitetura / segurança / TI | G0-P13, G0-P29; decisões D13–D17, P21, P24–P25 | **Pendente — bloqueador** |
| G0-15 | Persistência e integridade em PostgreSQL | Modelo físico revisado, migrações, constraints, transações e testes em instância PostgreSQL real | Integridade referencial, atomicidade, isolamento, unicidade e rollback demonstrados; sem depender apenas de mocks | Arquitetura / desenvolvimento / QA | G0-P14, D03–D04, D18–D20, G0-P23 | **Pendente — bloqueador** |
| G0-16 | Concorrência, idempotência e versionamento | Testes concorrentes reproduzíveis, contratos e relatórios | Repetições e conflitos produzem resultado determinístico; eventos e alterações permanecem atômicos; expected_version aplicado | Desenvolvimento / QA | G0-P23, D14 | **Pendente — bloqueador** |
| G0-17 | Testes ponta a ponta do fluxo crítico | Relatório E2E automatizado e evidências de execução | Fluxo solicitação → chegada → conferência → pendências → custódia → aceite/amostra coberto; casos negativos e permissões incluídos | QA / produto / SEFI | SIM01–SIM12, CA01–CA37, arquitetura | **Pendente — bloqueador** |
| G0-18 | Pipeline CI e reprodutibilidade | Configuração versionada, logs de execução e relatório de cobertura pertinente | Testes executados em ambiente reproduzível; falhas visíveis; dependências e versões controladas | Desenvolvimento / DevOps / QA | G0-P15, G0-P14 | **Não verificado** |
| G0-19 | Identidade e acesso de solicitantes externos | Fluxo de cadastro, vínculo, recuperação, suspensão e revogação; testes de autorização | Acesso limitado ao escopo autorizado; servidor aplica isolamento por solicitação/anexo; tentativas indevidas negadas e auditadas | Segurança / TI / produto | G0-P21, D15 | **Pendente** |
| G0-20 | Migração e reconciliação de legado | Inventário, mapeamento, plano, relatório de reconciliação e tratamento de exceções | Totais e amostras conferidos; origem preservada; vínculos sem evidência não criados; exceções aprovadas | Gestão de dados / SEFI / QA | G0-P22, G0-18 | **Pendente** |
| G0-21 | Agrupamento, fracionamento e amostragem por categoria | Matriz técnica aprovada por categoria e testes de aplicação | Quantidades, unidades, lotes, objetos de custódia e amostras rastreáveis; exceções justificadas | Responsável técnico / Qualidade | G0-P26, D03–D04, D20 | **Pendente** |
| G0-22 | Consulta histórica, paginação e exportação | Especificação e testes de consulta/exportação | Ordenação determinística e paginação estável; filtros coerentes; exportações completas, autorizadas e rastreáveis | Produto / arquitetura / QA | G0-P28, D14–D15 | **Pendente** |
| G0-23 | Política de autenticação reforçada e proteção contra abuso | Análise de risco, política de MFA/SSO quando aplicável, limites e testes de abuso | Controles proporcionais ao risco, monitoramento e resposta a abuso definidos e validados | Segurança / TI | G0-P29, G0-P21 | **Pendente** |
| G0-24 | Classificação, retenção e destinação de informações | Tabela de classificação/temporalidade, base institucional, aprovações e procedimento | Retenção, arquivamento, bloqueio e eliminação autorizada definidos; trilha e evidências preservadas | Gestão documental / Jurídico / TI / SEFI | G0-P30, D13–D14, D17 | **Pendente** |
| G0-25 | Decisão formal do Gate G0 | Dossiê de evidências, pareceres, lista de pendências e ata/decisão final | Todos os bloqueadores encerrados ou formalmente tratados conforme alçada; decisão explícita de GO/NO-GO | Autoridade competente / responsável pela validação | G0-01 a G0-24 | **Não iniciado — bloqueado pelos itens anteriores** |

*Os responsáveis são papéis propostos para planejamento, não designações nominais nem atribuições institucionais já formalizadas.*

## 5. Validação operacional SIM01–SIM12

A simulação documental existente deve ser convertida em execução observada. Para cada cenário, registrar no mínimo:

1. Identificador e versão do cenário;
2. objetivo, pré-condições, dados de teste e perfil participante;
3. passos efetivamente executados;
4. resultado esperado e resultado observado;
5. evidências (capturas, registros, logs ou documentos), sem dados pessoais desnecessários;
6. desvios, severidade, responsável e prazo de correção;
7. repetição após correção, quando aplicável;
8. conclusão e aceite formal do representante autorizado.

A execução deve cobrir, no mínimo, chegada e quantidades, conferência, pendências, recusas, custódia, transferências/localizações, retificações, independência, checklists, anexos/auditoria, permissões/assinatura, identificadores, chegada posterior e admissão de amostra. Os cenários adicionais de backup/restauração, integridade de anexos, acesso indevido e concorrência devem ser incluídos no plano de QA.

**Regra:** simulação de mesa ou revisão de documento não deve ser registrada como teste operacional do sistema.

## 6. Critérios de aceite dos CA01–CA37

A matriz CA deve ser normalizada com estas colunas mínimas:

| Campo | Conteúdo obrigatório |
|---|---|
| ID / versão | Identificador estável e versão do critério |
| Requisito de origem | D01–D20, EST, G0-P ou regra de domínio |
| Pré-condições | Estado inicial, perfil e dados necessários |
| Procedimento | Passos reproduzíveis |
| Resultado esperado | Regra observável, inclusive bloqueios |
| Resultado obtido | Resultado real da execução |
| Evidência | Referência a log, captura, registro ou artefato |
| Status | Não executado, aprovado, reprovado, bloqueado ou inconclusivo |
| Defeito / desvio | Identificador, severidade e vínculo |
| Reexecução | Resultado após correção |
| Aprovação | Papel, data e registro de aceite |

Não considerar CA aprovado apenas por estar descrito ou revisado documentalmente. Critérios de segurança, integridade, custódia e autorização exigem evidência específica.

## 7. Pacotes de evidência por domínio

- **Processo SEFI:** fluxos aprovados, matriz de competências, checklists, prazos, formulários, procedimentos de custódia e destinação.
- **Produto e domínio:** baseline D01–D20, EST-REC-001, MOD-DOM-001, SIM01–SIM12, CA01–CA37 e rastreabilidade cruzada.
- **Arquitetura:** diagramas, modelo físico, contratos de API, decisões arquiteturais, análise de ameaças e riscos residuais.
- **Segurança:** matriz de autorização, testes negativos, autenticação, proteção contra abuso, gestão de segredos e auditoria.
- **Dados e infraestrutura:** PostgreSQL real, migrações, backup/restauração, anexos, retenção, monitoramento e continuidade.
- **Qualidade/QA:** plano de testes, execução, defeitos, reexecuções, E2E, CI e relatório de cobertura.
- **Governança:** designações, pareceres, aprovações, atas e decisão formal de G0.

## 8. Sequência recomendada de execução

| Ordem | Etapa | Saída necessária | Condição para avançar |
|---|---|---|---|
| 1 | Fechar definições institucionais | Responsáveis, checklists, prazos, assinatura, devolução/destinação e retenção | Aprovações competentes registradas |
| 2 | Homologar o processo com o SEFI | SIM01–SIM12 executados e aceitos | Sem divergências críticas abertas |
| 3 | Fechar especificação verificável | CA01–CA37 normalizados e rastreados | Cada critério testável e associado a evidência |
| 4 | Concluir avaliação técnica | Arquitetura, segurança, PostgreSQL, anexos, auditoria e continuidade | Parecer técnico e riscos residuais aceitos |
| 5 | Executar QA integrado | Testes unitários/integração, concorrência, migração, segurança, E2E e CI | Resultados aprovados e reproduzíveis |
| 6 | Montar dossiê e deliberar G0 | Matriz atualizada, evidências, desvios e pareceres | Autoridade competente delibera GO/NO-GO |

A sequência é uma proposta de gestão; dependências reais devem ser ajustadas no planejamento sem eliminar critérios de aceite.

## 9. Regras de encerramento de pendências

Uma linha só pode mudar para **Concluído** quando:
- o entregável estiver identificado e versionado;
- a evidência estiver acessível e vinculada à linha;
- o critério de aceitação tiver sido verificado;
- desvios impeditivos estiverem resolvidos e reexecutados;
- a aprovação tiver sido registrada pelo papel competente.

Pendência aceita como risco residual exige justificativa, impacto, controle compensatório, responsável, prazo e autoridade que aceitou. Não usar essa exceção para dispensar requisitos legais, de segurança, integridade ou critérios eliminatórios.

## 10. Limites da avaliação desta versão

Esta versão foi elaborada a partir dos documentos de decisão, auditoria, revisão multidisciplinar, cenários operacionais, máquina de estados e modelo conceitual identificados abaixo. A avaliação confirma o conteúdo documental disponível, mas não constitui auditoria independente do código-fonte, execução de testes, inspeção do ambiente PostgreSQL, infraestrutura, CI ou entrevistas com usuários do SEFI.

A pesquisa de arquivos de código pelo conector GitHub nesta etapa não retornou resultados utilizáveis. Portanto, **não se conclui que código, testes ou pipelines inexistam**; sua presença, estado, cobertura e execução deverão ser inventariados diretamente na próxima revisão técnica. Status marcados como “Não verificado” ou “não comprovado” devem permanecer assim até inspeção direta.

## 11. Fontes documentais examinadas

- `docs/DECISOES_PREVALIDACAO_SEFI_D01_D20.md` — versão 1.7; D01–D20 e G0-P01–G0-P30.
- `docs/AUDITORIA_CONSISTENCIA_EST01_EST10.md` — versão 1.3; achados e dependências EST01–EST10.
- `docs/REVISAO_MULTIDISCIPLINAR_MAQUINA_ESTADOS_CA01_CA24.md` — versão 1.2; revisão CA01–CA24 e dependências técnicas.
- `docs/VALIDACAO_CENARIOS_OPERACIONAIS_SEFI.md` — versão 1.2; SIM01–SIM12 como simulação documental ainda não homologada.
- `docs/ESTADOS_E_TRANSICOES_SOLICITACAO_RECEBIMENTO.md` — versão 1.7; estados, transições, CA e requisitos complementares.
- `docs/MODELO_CONCEITUAL_DOMINIO_SOLICITACAO_RECEBIMENTO.md` — versão 0.7; domínio e cardinalidades M0.2.

## 12. Situação formal

**Gate G0: NÃO APROVADO.**  
**Implementação: NÃO AUTORIZADA.**

A elaboração desta matriz é atividade de governança e documentação. Não altera código, banco de dados, API, frontend, CI ou infraestrutura, nem autoriza início de implementação.

## 13. Histórico

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-10 | Primeira matriz consolidada de prontidão, com entregáveis, evidências, critérios de aceitação, responsáveis propostos, dependências e situação preliminar. |
