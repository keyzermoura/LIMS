# Parecer Consolidado de Prontidão — Gate G0 do LIMS-SEFI

**Identificador:** PCR-G0-001  
**Versão:** 1.0  
**Data:** 2026-11-22  
**Repositório:** keyzermoura/LIMS — branch main  
**Baseline técnica/documental examinada:** commit `343c3905f50e695048cb527b5e60f765d1d9b98e`  
**Situação:** parecer de auditoria documental, estática e de evidências CI; não constitui homologação nem autorização de implementação.

## 1. Objetivo e conclusão executiva

Consolidar os resultados das auditorias P1–P7, relacionando causas-raiz, impactos, dependências, critérios objetivos de saída e evidências necessárias para decisão do Gate G0. O parecer distingue diretrizes institucionais ratificadas, especificações propostas, implementação observada, testes versionados, execução CI e homologação operacional.

**Conclusão:** o repositório possui fundação técnica reutilizável, mas o fluxo de admissão SEFI não está demonstrado como aderente de ponta a ponta; há falhas reproduzíveis no CI do commit-base, lacunas de segurança contextual, concorrência, ciclo de vida de ensaios/laudos e continuidade operacional, além de evidência insuficiente de validação e homologação.

**GATE G0: NÃO APROVADO.**  
**IMPLEMENTAÇÃO DE FUNCIONALIDADES SEFI: NÃO AUTORIZADA.**

A autorização prévia para atualizar documentação não abrange código, testes, migrações, banco, workflows, scripts, infraestrutura ou deploy.

## 2. Escopo, método e níveis de evidência

Foram confrontados os documentos D01–D20, G0-P01–P30, M0.2/M0.3, EST-REC-001, CA01–CA37, SIM01–SIM12, as matrizes de aderência/prontidão/rastreabilidade/governança, o plano de fechamento, código e testes previamente inspecionados e execuções GitHub Actions.

Níveis usados neste parecer:

- **Confirmado:** evidência direta observada no documento, código, log ou metadado da execução.
- **Parcial:** existe parte da capacidade ou especificação, mas falta condição, integração, cobertura ou prova.
- **Não comprovado:** a evidência acessível não permite afirmar conclusão; não significa necessariamente inexistência.
- **Pendente de decisão:** depende de definição formal da autoridade institucional ou do responsável funcional.
- **Histórico:** resultado de commit/versão anterior, não transferível automaticamente ao HEAD atual.

A leitura estática de teste não equivale à execução. Execução CI não equivale à validade das asserções. Teste aprovado não equivale à homologação operacional. Homologação exige participantes autorizados, ambiente/versionamento, roteiro, evidências, desvios e aceite formal.

## 3. Revalidação do CI no commit-base

**Commit:** `343c3905f50e695048cb527b5e60f765d1d9b98e`  
**Workflow run:** `44974199006` — concluído com falha.

| Job | Resultado | Evidência observada | Interpretação |
|---|---|---|---|
| Segurança (SAST/SCA) | Sucesso | Bandit e pip-audit concluíram com sucesso | Resultado positivo limitado aos scanners e escopo do job |
| Backend | Falha | Ruff e mypy passaram; `alembic upgrade head` falhou com `value too long for type character varying(32)` ao gravar revision `0022_official_reports_attributes_immutable` | `alembic check`, testes SQLite e PostgreSQL foram ignorados; não há evidência desses testes nesta execução |
| Front-end | Falha | `npm ci` reportou ausência no lockfile de `@playwright/test@1.65.1`, `playwright@1.65.1` e `playwright-core@1.65.1` | Typecheck e build não foram alcançados |
| Docker | Falha | Build da imagem web falhou no mesmo `npm ci` por lockfile incompatível | Stack, semeadura e smoke test foram ignorados; não se deve classificar como falha independente do runtime Docker |

O job de segurança bem-sucedido não compensa as falhas dos demais jobs. Os runs anteriores também não substituem o resultado do commit-base. A execução é evidência atual e inequívoca de que o pipeline não está verde nesse commit.

## 4. Consolidação dos bloqueadores P1–P7

| Pacote | Estado | Causa-raiz / constatação principal | Impacto | Dependências | Critério objetivo de saída | Evidência de fechamento |
|---|---|---|---|---|---|---|
| **P1 — CI, build, migrações e reprodutibilidade** | **Confirmado — bloqueador** | Revision Alembic longa excede coluna `alembic_version.version_num` de 32 caracteres no PostgreSQL de CI; `npm ci` falha por manifesto e lockfile divergentes | Pipeline não alcança validações de migração, testes, typecheck/build e smoke Docker | P2–P6 para validação integrada; manutenção/arquitetura para estratégia de migração e dependências | Pipeline integral verde em commit candidato; migrações aplicadas em banco limpo e banco representativo; paridade Alembic; lockfile reproduzível; testes efetivamente executados | Run/commit, logs completos, versão do banco, estado Alembic, resultados SQLite/PostgreSQL, typecheck/build, Docker e E2E |
| **P2 — Admissão, recebimento e custódia** | **Confirmado — divergência funcional** | Objeto de custódia pode ser criado antes da confirmação de apresentação; aceite não valida uniformemente conferência/decisão; transferência muda custodiante sem confirmação do destinatário; APIs/modelos legados e novos coexistem | Risco de custódia, reconciliação de quantidades, aceite ou criação de amostra fora da sequência aprovada | Baseline D01–D20, M0.2 aprovado, M0.3 ainda não aprovado; P1 para retestes | Fluxo implementado respeita chegada → apresentação/conferência → decisão/validação exigível → aceite → amostra; não apresentado não gera objeto; transferência só muda guarda após confirmação; legado tem estratégia de compatibilidade/retirada | Testes de todos os ramos, logs CI, trilha de eventos, reconciliação de quantidades, testes de transferência/recusa/destinação e homologação SIM01–SIM08/SIM12 |
| **P3 — Segurança contextual e identidade** | **Confirmado — controle parcial** | Autorização observada predominantemente por papel; consultas sem escopo contextual por unidade/recurso; modelo de usuário sem vínculo institucional demonstrado; QR não verifica expiração temporal e expõe dados além do mínimo | Risco de acesso transversal indevido, exposição de dados e validação inadequada de identidade | Pendente de política institucional de perfis/unidades, identidade externa e QR; P1 para testes | Política ator × papel × unidade/vínculo × recurso × estado × ação definida; negação por padrão; exceções explícitas; QR opaco, mínimo, expirável e revogável conforme política | Matriz de autorização aprovada, testes positivos/negativos multiunidade e externos, testes QR de validade/revogação, logs e revisão independente |
| **P4 — Integridade transacional, concorrência e idempotência** | **Parcial — riscos técnicos identificados** | Existem controles positivos de lock/versionamento em serviços; lacunas em idempotência de comandos, concorrência de subalíquotas, emenda de laudo/latest, snapshot e atomicidade de emissão em lote | Possibilidade de duplicidade, estado concorrente incoerente, múltiplas versões vigentes ou lote parcialmente persistido | P1; P2 para agregados; P5 para emissão/emenda | Contratos explícitos de idempotência, versão e atomicidade; constraints/locks coerentes; operação concorrente testada no PostgreSQL; uma única versão vigente | Testes concorrentes repetíveis, evidência PostgreSQL, constraints/migrações, logs, reconciliação de resultados e revisão independente |
| **P5 — Qualidade, resultados e laudos** | **Parcial — controles presentes, integração insuficiente** | Há resultado versionado, assinatura, auditoria, CAPA e verificações na emissão; porém conclusão do laudo não valida explicitamente resultado APROVADO para cada ensaio; snapshot, concorrência e atomicidade de lote requerem fechamento | Risco de emitir laudo com conclusão não derivada de regra formal ou com dados não consistentes; emendas/lotes com integridade insuficiente | P4; decisão institucional sobre regra de emissão diante de ensaio reprovado/inconclusivo; P1 | Regra de conclusão aprovada; emissão bloqueia resultados incompatíveis; snapshot consistente; emenda preserva original e uma única versão vigente; lote tem atomicidade ou retomada formalmente definida | Requisitos aprovados, testes de resultados aprovados/reprovados/inconclusivos, concorrência, emenda, lote, PDF/hash e evidência CI |
| **P6 — Continuidade, backup, recuperação e integrações** | **Confirmado — prontidão não demonstrada** | Script mascara falhas com `|| true`; PITR não está implementado pelo script observado; CronJob referencia recursos não encontrados no Kustomize examinado; retenção/off-site/RPO/RTO/restore drill não comprovados; outbox tem janela de duplicidade e runbook divergente; readiness pode responder HTTP 200 degradado | Recuperação de dados/documentos e entrega confiável de eventos não demonstradas; risco de falsa indicação de disponibilidade | Política institucional de retenção/RPO/RTO; P1 e arquitetura/infra; classificação documental e jurídica | Backup fail-closed, verificado e monitorado; restore/PITR demonstrados; política aprovada; recursos implantáveis; outbox idempotente e observável; readiness/liveness separados | Logs de backup/restore, comparação origem-destino, validação de constraints/sequences/auditoria/PDFs, teste PITR, manifests aplicados, alertas, métricas e teste de integração |
| **P7 — Governança da qualidade, validação e homologação** | **Não comprovado — bloqueador de Gate** | CA01–CA37 sem comprovação integral consolidada; SIM01–SIM12 possuem roteiros/testes versionados, mas execução atual válida e homologação não comprovadas; matriz de rastreabilidade ainda registra associações temáticas em pontos; dependências institucionais e pacotes GOV não encerrados | Não há base objetiva suficiente para declarar o produto validado, operacionalmente aceito ou pronto para avançar Gate | P1–P6; responsáveis institucionais, Qualidade, SEFI, TI/Segurança e revisores independentes | Requisitos individualizados e rastreados; desvios tratados; CI verde; revisão independente; validação por perfis; SIM executados; evidência operacional; atas e aceite formal; decisão formal do Gate | Matriz CA com commit/run/log/resultado/reteste/aprovador; protocolos SIM; atas; revisão independente; evidências de ambiente, treinamento, migração, segurança e continuidade; termo de homologação |

### 4.1 Leitura correta da classificação

“Confirmado” identifica uma constatação observada, não uma conclusão automática de não conformidade normativa. “Não comprovado” não deve ser reescrito como “inexistente”. P2/P3 contêm divergências de comportamento observadas; P4/P5 combinam controles positivos com lacunas; P6 apresenta problemas concretos e ausência de evidência operacional; P7 representa a insuficiência do conjunto probatório necessário ao Gate.

## 5. Dependências e ordem recomendada de fechamento

1. **P1 — restabelecer pipeline reprodutível.** Sem migrações, testes e builds executáveis, os demais pacotes não podem produzir evidência integrada confiável.
2. **P2 + P3 — consolidar admissão/custódia e autorização contextual.** Tratar conjuntamente o ciclo de vida e as barreiras de acesso, mantendo M0.3 como proposta até validação.
3. **P4 + P5 — fechar integridade transacional e regras de ensaio/laudo.** Não testar apenas caminhos felizes; incluir concorrência, repetição, falha parcial, reprovação e emenda.
4. **P6 — demonstrar continuidade e operação.** Não considerar configuração declarada como backup/restauração comprovados.
5. **P7 — executar validação e homologação integrada.** Somente após os pacotes técnicos e institucionais fornecerem evidência rastreável.
6. **Submeter o Gate G0 à autoridade competente.** A decisão é formal e distinta da ratificação de D01–D20 e G0-P01–P30.

A ordem não exige que todas as decisões institucionais aguardem o fim da engenharia: decisões podem ser preparadas em paralelo, mas não se deve codificar uma regra ainda ambígua.

## 6. Critérios mínimos de entrada para decisão do Gate G0

O Gate só deverá ser submetido à decisão quando todos os itens abaixo estiverem satisfeitos ou formalmente tratados por autoridade competente, com justificativa e avaliação de risco:

1. Baseline institucional D01–D20 e G0-P01–P30 vinculada a requisitos individualizados e versão controlada.
2. M0.3 e especificações operacionais aplicáveis revisados e aprovados, sem confundir proposta com baseline aprovada.
3. CA01–CA37 individualizados: pré-condição, dados, passos, esperado, commit, ambiente, run, log, obtido, defeito, reteste e aceite.
4. SIM01–SIM12 executados com perfis autorizados; validade das asserções revisada; desvios tratados; ata e aceite.
5. P1: CI verde no commit candidato, incluindo migrações PostgreSQL, testes SQLite/PostgreSQL, frontend, Docker e E2E previstos.
6. P2/P3: fluxo de admissão/custódia e política de autorização contextual aprovados e testados.
7. P4/P5: concorrência, idempotência, emissão, emenda, resultados e atomicidade demonstrados.
8. P6: backup/restauração/PITR, recuperação de documentos, retenção, monitoramento e RPO/RTO demonstrados/aprovados.
9. Revisão independente de arquitetura, segurança e qualidade; achados impeditivos encerrados ou aceitos formalmente pela autoridade competente.
10. Ambiente, migração de dados, perfis, treinamento, suporte, monitoramento e plano de retorno documentados.
11. Pacotes GOV-01–GOV-20 com estado, responsável, aprovador, versão e evidência.
12. Parecer final e decisão formal do Gate registrados, com escopo e limites explícitos da autorização subsequente.

## 7. Decisões institucionais que não devem ser presumidas

As seguintes decisões devem ser organizadas em blocos objetivos, apresentando opções, impacto e recomendação, sem bloquear a auditoria documental:

| Tema | Decisão necessária | Responsável funcional sugerido |
|---|---|---|
| Competências e substituições | Perfis, designações, substitutos, segregação e atos que exigem revisão independente | Coordenação SEFI / autoridade competente |
| Checklists por categoria | Critérios eliminatórios, saneáveis e informativos; versão e aprovação | Especialistas técnicos / Qualidade |
| Prazos e comunicação | Prazos, canais, comprovação, escalonamento, prorrogação e encerramento | SEFI / área administrativa |
| Recusa e destinação | Devolução, guarda, destinação, comprovante e prazos | Coordenação / área responsável pelo patrimônio ou logística |
| Assinatura | Modalidade, atos que exigem assinatura formal e requisitos jurídicos | Autoridade institucional / Jurídico / TI |
| Identidade externa | Prova de identidade, representante, recuperação e habilitação | Governança de acesso / TI / área demandante |
| RPO/RTO e retenção | Frequência, prazo de guarda, cópia externa, recuperação e temporalidade documental | TI/Infraestrutura / Jurídico / autoridade competente |
| Resultados e laudos | Regra de emissão diante de ensaio reprovado, inconclusivo ou parcialmente concluído | Responsável técnico / Qualidade / Coordenação |
| Agrupamento e fracionamento | Granularidade por categoria e critérios de amostragem | Especialistas técnicos / Qualidade |
| Homologação | Participantes, critérios, desvios aceitáveis e autoridade de aceite | SEFI / Qualidade / autoridade competente |

Nenhuma decisão acima é considerada aprovada por este parecer.

## 8. Plano de validação e homologação

### Fase A — preparação controlada
- Congelar commit candidato, versão de documentos, banco, configuração e ambiente.
- Aprovar matriz de requisitos, dados de teste, perfis, responsabilidades e critérios de aceite.
- Preparar dados sintéticos e plano de proteção/expurgo; não usar dados pessoais reais sem autorização e controles.

### Fase B — validação técnica
- Executar pipeline completo e registrar run/commit/logs.
- Validar migrações em banco limpo e em cenário representativo de atualização.
- Executar testes unitários, integração, PostgreSQL concorrente, segurança contextual, frontend, Docker e E2E.
- Demonstrar backup, restore e PITR, integridade da auditoria e recuperação dos PDFs.
- Registrar defeitos, severidade, responsável, correção e reteste.

### Fase C — homologação operacional SEFI
- Executar SIM01–SIM12 com representantes dos perfis previstos.
- Observar recebimento, conferência, aceite/pendência/recusa, custódia, transferência, localização, retificação e criação da amostra.
- Verificar trilha, documentos, assinaturas, permissões, mensagens e tratamento de exceções.
- Registrar evidências, desvios, decisões, participantes/funções, data, ambiente e versão.
- Obter aceite formal da autoridade designada.

### Fase D — decisão do Gate
- Consolidar CA01–CA37, GOV-01–GOV-20, achados P1–P7 e riscos residuais.
- Obter revisão independente e parecer da Qualidade.
- Registrar decisão formal: aprovado, aprovado com escopo/condições expressas ou não aprovado.
- Qualquer autorização de implementação deve ser específica, versionada e posterior à decisão do Gate.

## 9. Papéis e responsabilidades — sem designação nominal

- **Responsável institucional SEFI:** valida fluxo, critérios operacionais, papéis e aceite.
- **Coordenação SEFI:** aprova decisões dentro de sua competência e designa validadores.
- **Qualidade:** governa critérios, evidências, desvios, revisão e homologação.
- **Arquitetura/Desenvolvimento:** propõe e implementa correções somente após autorização; mantém rastreabilidade.
- **QA/Validação:** prepara e executa testes, registra resultados e retestes.
- **Segurança/TI:** revisa identidade, autorização, infraestrutura, continuidade e monitoramento.
- **Infraestrutura/DBA:** executa migrações, backup, restore, PITR e operação de banco.
- **Jurídico/autoridade competente:** decide questões jurídicas, assinatura, retenção e atos institucionais.
- **Revisor independente:** avalia arquitetura, segurança e evidências sem revisar o próprio trabalho.

Os papéis são recomendações de governança; não representam nomeação ou delegação formal.

## 10. Limitações e ressalvas

- Esta rodada revalidou metadados e jobs/logs do run `44974199006` no commit `343c3905f50e695048cb527b5e60f765d1d9b98e`; não executou testes localmente.
- Não foram executados testes operacionais com usuários SEFI, testes de backup/restore/PITR em ambiente, ensaios de carga ou revisão jurídica.
- As constatações P2–P6 decorrem das auditorias estáticas documentadas; não substituem teste dinâmico ou análise completa de todos os caminhos.
- A matriz CA01–CA37 mantém o consolidado de 0 integrais, 17 parciais, 13 não conformes e 7 não comprovados; esta rodada não reexecutou individualmente os 37 critérios.
- SIM01–SIM12 têm roteiros e testes versionados, mas execução válida no commit-base e homologação operacional não estão demonstradas.
- D01–D20 e G0-P01–P30 ratificadas não significam M0.3 aprovado, entregáveis concluídos ou Gate aprovado.

## 11. Referências documentais

- `docs/DECISOES_PREVALIDACAO_SEFI_D01_D20.md`
- `docs/MODELO_CONCEITUAL_DOMINIO_SOLICITACAO_RECEBIMENTO.md`
- `docs/ESTADOS_E_TRANSICOES_SOLICITACAO_RECEBIMENTO.md`
- `docs/VALIDACAO_CENARIOS_OPERACIONAIS_SEFI.md`
- `docs/MATRIZ_ADERENCIA_DOMINIO_SEFI.md`
- `docs/MATRIZ_PRONTIDAO_GATE_G0.md`
- `docs/MATRIZ_GERAL_RASTREABILIDADE_M0_3.md`
- `docs/MATRIZ_EVIDENCIAS_GOVERNANCA_QUALIDADE_G0.md`
- `docs/PLANO_FECHAMENTO_BLOQUEADORES_G0.md`

## 12. Histórico

| Versão | Data | Descrição |
|---|---|---|
| 1.0 | 2026-11-22 | Consolidação P1–P7, revalidação do CI no commit-base, critérios objetivos de fechamento, dependências, plano de validação/homologação e parecer de prontidão. |
