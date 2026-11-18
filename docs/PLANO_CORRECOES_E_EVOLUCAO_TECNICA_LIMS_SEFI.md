# Plano de Correções e Evolução Técnica — LIMS-SEFI

**Identificador:** PLN-COR-LIMS-SEFI-001  
**Versão:** 1.0  
**Data:** 2026-11-18  
**Repositório:** `keyzermoura/LIMS`  
**Baseline de referência:** `e5797013cff5b455c3d105a3a8ee2407da5213c5`  
**Branch documental:** `docs/plano-correcoes-pacote-a`  
**Natureza:** plano técnico e arquitetural; não constitui aprovação institucional, autorização automática para implementar mudanças de domínio, nem liberação do Gate G0.  
**Situação do Gate G0:** NÃO APROVADO.

---

## 1. Objetivo

Estabelecer um plano único, rastreável e priorizado para corrigir divergências da implementação atual, fortalecer os controles técnicos e evoluir o LIMS-SEFI em direção a uma solução institucional especializada em recebimento, custódia, ensaios físicos de dispositivos médicos, qualidade e emissão de laudos.

O plano parte da arquitetura e dos componentes já existentes. A orientação é **evoluir e consolidar, não reconstruir**. Antes de cada alteração, a implementação deverá ser confrontada com as decisões D01–D20, propostas G0-P01–G0-P30, M0.1/M0.2, SIM, CA e evidências de teste vigentes.

## 2. Princípios de execução

1. Preservar as decisões institucionais já ratificadas; não reabrir decisões sem divergência material ou necessidade explícita.
2. Separar requisito de domínio, desenho lógico, implementação, teste automatizado, homologação operacional e validação institucional.
3. Não tratar documentação, existência de código ou CI verde como prova isolada de validação do processo.
4. Não criar entidades paralelas quando um modelo existente puder ser compatibilizado sem perda semântica.
5. Preservar fatos históricos: retificações devem acrescentar evidência e não apagar registros formalizados.
6. Aplicar transações atômicas, idempotência, controle de versão e trilha de auditoria nas operações críticas.
7. Não implementar mudanças que dependam de decisão institucional ainda pendente.
8. Não fazer merge na branch principal nem declarar G0 aprovado por conclusão deste plano.

## 3. Baseline e limites da auditoria

A baseline documental é o commit informado acima. A inspeção estática identificou, entre outros, os modelos/serviços de Solicitation, SolicitationItem, Receipt, ReceiptItem, CustodyObject, CustodyEvent, DeviceSample, LabTest, TestExecution, reagentes, equipamentos, qualificações, OOS/CAPA, relatórios oficiais, auditoria e integração instrumental.

Os achados deste plano são classificados como:
- **Confirmado por inspeção estática:** comportamento visível no código examinado.
- **Indício / requer confirmação:** risco identificado em documentação ou trecho parcial, que precisa de inspeção adicional.
- **Não verificado:** não há evidência suficiente para afirmar presença ou ausência.

Não foi executada nesta atividade a suíte completa de testes, restauração operacional de backup, teste de navegador ou homologação com usuários SEFI.

## 4. Priorização

- **P0 — integridade do fluxo / continuidade:** corrigir antes de considerar o fluxo de recebimento/admissão pronto ou avançar o Gate G0.
- **P1 — controle laboratorial e segurança:** fechar antes da operação institucional ampliada.
- **P2 — eficiência e gestão:** evoluções importantes após estabilizar os controles essenciais.
- **P3 — expansão de produto:** funcionalidades estratégicas posteriores, condicionadas a necessidade e capacidade institucional.

## 5. Backlog de correções e melhorias

### 5.1 P0 — Correções bloqueadoras

| ID | Tema | Diagnóstico / risco | Proposta de implementação | Critérios de aceite / testes |
|---|---|---|---|---|
| P0-01 | Apresentação física dos itens | `create_receipt()` inicializa todos os itens como `PRESENTED`, usando quantidade declarada como apresentada. | Criar o `ReceiptItem` para cada item declarado, mas iniciar a situação de apresentação como não conciliada/pendente. Registrar quantidade apresentada separadamente, sem assumir equivalência com a declarada. A situação final deve ser informada na conferência física. | Item não apresentado permanece representado; não é classificado como apresentado; quantidades declarada e apresentada não são sobrescritas; testes para total, parcial e zero apresentado. |
| P0-02 | Criação de objetos de custódia | O serviço cria `CustodyObject` para cada item declarado, mesmo quando a apresentação física ainda não foi confirmada. | Criar objeto de custódia somente para material efetivamente apresentado e colocado sob guarda. Definir granularidade/agrupamento com vínculo inequívoco ao item e à apresentação. | Item com quantidade apresentada zero não gera objeto nem evento de ingresso; item parcial gera objeto apenas para quantidade recebida; todo objeto possui origem e evento inicial. |
| P0-03 | Reconciliação de quantidades | Quantidade declarada, apresentada e representada sob custódia são tratadas como se fossem equivalentes. | Formalizar dimensões independentes: declarada, apresentada, sob custódia, aceita, recusada e não apresentada. Definir unidade e regra de reconciliação; impedir saldo negativo e divergência silenciosa. | Testes de igualdade, diferença, apresentação parcial, múltiplas unidades/agrupamentos e arredondamento/conversão quando aplicável. |
| P0-04 | Barreira de aceite e criação de amostra | O serviço `accept_custody_object()` já cria `DeviceSample` no aceite favorável; é necessário comprovar todas as condições de elegibilidade e evitar duplicidade/concorrência. | Manter a criação transacional vinculada ao objeto; validar decisão vigente, conferência obrigatória, pendências impeditivas, validação da coordenação quando exigida, versão esperada e ausência de amostra anterior. Garantir unicidade no banco para o vínculo objeto-amostra. | Sem aceite não existe amostra; decisão desfavorável não cria amostra; repetição/concor­rência não duplica; falha intermediária reverte toda a operação; auditoria registra a cadeia. |
| P0-05 | Backup e recuperação | Scripts e configuração de backup/restauração possuem riscos documentados: falhas potencialmente mascaradas, verificações de contagem sem condição de erro, referências operacionais a validar e PITR não comprovado. | Revisar manifestos, agendamento, permissões, volumes, imagem e dependências; remover supressão de erros; validar códigos de saída; comparar contagens/checksums; documentar retenção, criptografia, RPO/RTO e PITR; automatizar restauração isolada. | Teste real de backup e restore com falha induzida; restauração interrompe em erro; reconciliação passa; evidência de WAL/PITR se reivindicado; relatório com RPO/RTO medidos. |
| P0-06 | Baseline documental | M0.3 e matrizes apontam commits anteriores e descrevem capacidades já existentes como não implementadas. | Criar matriz de aderência por baseline com entidade lógica, modelo ORM, rota, serviço, estado/evento, invariante, CA/SIM e teste. Marcar documentos históricos como supersedidos por versão datada, sem apagar decisões. | Todos os requisitos de domínio com status e evidência; lacunas e itens não verificados explícitos; SHA da baseline registrado. |

### 5.2 P1 — Segurança, qualidade e ciclo laboratorial

| ID | Tema | Diagnóstico / risco | Proposta de implementação | Critérios de aceite / testes |
|---|---|---|---|---|
| P1-01 | Consumo obrigatório de reagentes/padrões | `complete_execution()` não mostra intertravamento explícito para consumo exigido pelo método. | Modelar requisito de insumo por método/versão; antes de concluir, verificar lote, validade, status, quantidade e vínculo do consumo. Registrar consumo na mesma transação da conclusão. Não exigir insumo quando método não o requer. | Método sem requisito conclui sem consumo; método com requisito bloqueia sem consumo válido; lote vencido/insuficiente bloqueia; repetição não duplica baixa; rollback preserva estoque e execução. |
| P1-02 | Escopos e autorização de serviços | Escopos M2M foram adicionados, mas a cobertura de rotas sensíveis precisa ser revisada integralmente. | Inventariar rotas por ator (humano/serviço), operação e recurso; aplicar autorização no servidor; evitar confiar apenas em frontend/RBAC genérico; testar isolamento por solicitação, amostra, laudo e anexos. | Matriz rota × escopo × perfil; testes negativos 401/403; serviço sem escopo não acessa; usuário de uma solicitação não consulta outra. |
| P1-03 | Dados brutos e anexos | A maturidade de evidências/anexos foi avaliada como parcial; é preciso confirmar o caminho completo de armazenamento e recuperação. | Definir metadados, hash, versionamento, tamanho/formato permitido, armazenamento, criptografia, autorização, retenção, antivírus quando aplicável e vínculo ao ensaio/recebimento/decisão. Preservar original. | Upload/download autorizado; hash confere; alteração indevida detectada; versão original preservada; arquivo corrompido/ausente tratado; trilha de acesso. |
| P1-04 | Método e versão aplicada | Existem métodos e vínculo de ensaio; deve-se comprovar congelamento da versão realmente usada. | Vincular execução a versão imutável de método/procedimento, parâmetros, critérios de aceitação e formulário de dados; mudanças futuras não alteram execução histórica. | Execução mantém versão e parâmetros; método revisado não altera histórico; bloqueio de método obsoleto conforme regra aprovada. |
| P1-05 | Equipamento e competência | Serviços de equipamento e qualificação existem; falta consolidar evidência ponta a ponta. | Na abertura e conclusão, registrar equipamento, status metrológico, calibração, manutenção e qualificação do executor válidos no instante do ensaio. | Equipamento vencido/inapto bloqueia; qualificação vencida bloqueia; evidência temporal preservada após renovação. |
| P1-06 | Revisão técnica e liberação | Há estrutura de resultados e relatórios; a cadeia completa de revisão independente precisa ser demonstrada. | Separar execução, revisão, aprovação e emissão; congelar pacote de resultados e evidências que sustenta o laudo; aplicar segregação de funções quando exigida. | Autor da execução não aprova quando independência é exigida; laudo referencia resultados e versões; retificação mantém versão anterior. |
| P1-07 | Relatório em lote | Foram identificados riscos de rastreabilidade entre assinatura em lote, manifesto final e hashes dos PDFs. | Formalizar manifesto imutável do lote, hash agregado, assinatura vinculada ao manifesto e relação individual de cada relatório. Avaliar uso de assinatura individual versus assinatura de manifesto. | Alterar PDF ou composição invalida manifesto; assinatura valida o conjunto exato; razão do lote persistida; teste de integridade. |
| P1-08 | Testes E2E e rastreabilidade CA/SIM | Smoke de container e testes HTTP não equivalem a E2E de navegador nem homologação SEFI. | Criar plano automatizado de jornada crítica e matriz requisito → teste → execução → evidência. Complementar com homologação observada por representantes autorizados. | E2E de navegador executado; casos negativos e perfis incluídos; CA/SIM rastreáveis; aceite operacional registrado separadamente. |

### 5.3 P2 — Melhorias de operação e gestão

| ID | Tema | Proposta de implementação | Critério de aceite |
|---|---|---|---|
| P2-01 | Filas de trabalho por papel | Painéis separados para recebimento, conferência, coordenação, execução, revisão e qualidade. | Cada papel vê pendências autorizadas, idade, prioridade e próxima ação. |
| P2-02 | SLA e tempo de ciclo | Registrar marcos de tempo e motivos de suspensão; calcular prazo por etapa. | Indicadores reproduzíveis, com regras de contagem e exclusões aprovadas. |
| P2-03 | Indicadores operacionais | Painéis de volume, pendências, recusas, retrabalho, prazo, capacidade e situação de ensaios. | Métricas conciliadas com registros transacionais e filtros auditáveis. |
| P2-04 | Busca e histórico | Busca por protocolo, número SEFI, amostra, fabricante, série, lote e laudo. | Paginação estável, autorização e exportação auditável. |
| P2-05 | Notificações e escalonamento | Notificações para pendências, prazo, revisão, validade de insumos e manutenção. | Entrega registrada, reprocessamento idempotente e falhas monitoradas. |
| P2-06 | Experiência de uso | Testes de tarefa com servidores SEFI; reduzir telas e campos duplicados; orientar ações pelo estado do processo. | Usuários concluem tarefas críticas com baixa taxa de erro; evidência de teste de usabilidade. |

### 5.4 P3 — Evolução estratégica

| ID | Tema | Proposta | Condição para priorizar |
|---|---|---|---|
| P3-01 | Portal externo | Submissão, acompanhamento e comunicação com solicitantes externos. | Modelo de identidade, isolamento, proteção de dados e política institucional aprovados. |
| P3-02 | Workflow configurável | Regras e etapas configuráveis com versionamento e governança. | Fluxos SEFI estabilizados e necessidade de variação comprovada. |
| P3-03 | Integração instrumental ampliada | Conectores, importação de arquivos e aquisição automatizada. | Inventário de equipamentos/protocolos e análise custo-benefício. |
| P3-04 | BI avançado | Camada analítica e painéis gerenciais históricos. | Dados transacionais confiáveis, catálogo de indicadores e governança de acesso. |
| P3-05 | Aplicação móvel | Captura de evidências e movimentações em campo/laboratório. | Casos de uso, segurança offline e sincronização definidos. |

## 6. Ordem de execução e dependências

1. **Pacote A — Baseline e arquitetura:** atualizar M0.3, matriz de aderência, matriz de maturidade e rastreabilidade contra a baseline atual. Nenhuma mudança de código.
2. **Pacote B1 — Recebimento e custódia:** P0-01 a P0-04. Fazer desenho detalhado, testes de regressão e migração compatível antes de implementar.
3. **Pacote B2 — Continuidade:** P0-05. Executar teste de recuperação isolado e documentar RPO/RTO.
4. **Pacote B3 — Segurança e evidências:** P1-02 e P1-03, com revisão de ameaças e testes negativos.
5. **Pacote C — Ciclo laboratorial:** P1-01, P1-04, P1-05, P1-06 e P1-07.
6. **Pacote D — Validação e operação:** P1-08, testes de usuário, tratamento de desvios e decisão formal de prontidão.
7. **Evolução:** P2/P3 após estabilização dos controles essenciais e priorização institucional.

A ordem poderá ser refinada quando a Matriz Mestra do Pacote A demonstrar dependências adicionais.

## 7. Governança, autorização e critérios de saída

- Este plano autoriza apenas o trabalho documental nele descrito.
- Correções de código exigem especificação técnica, análise de impacto, testes e autorização de implementação conforme governança do projeto.
- Alterações de regra institucional, critérios de checklist, competência, prazos, assinatura, retenção e destinação exigem decisão/validação da autoridade competente.
- Não considerar G0 aprovado por concluir tarefas técnicas isoladas.
- A decisão de G0 depende do dossiê completo de evidências e da homologação operacional exigida.

## 8. Entregáveis do Pacote A

| Entregável | Resultado esperado |
|---|---|
| M0.3 revisado | Modelo lógico confrontado com entidades e serviços existentes, com divergências e questões pendentes explícitas. |
| Matriz Mestra de Aderência | Rastreabilidade decisão/requisito → domínio → código → teste/evidência. |
| Matriz de Maturidade | Avaliação por capacidade, evidência, confiança, lacuna, impacto e prioridade. |
| Registro de baseline | SHA, branch, data, escopo e limitações da inspeção. |
| Parecer de arquitetura | Recomendação de evolução sem reconstrução e separação entre G0 e roadmap posterior. |

## 9. Registro de execução

| Data | Atividade | Resultado |
|---|---|---|
| 2026-11-18 | Inspeção estática inicial da baseline | Identificados componentes de solicitação/recebimento/custódia, divergência de apresentação e custódia inicial, necessidade de comprovar barreira de aceite, consumo de reagentes e recuperação. |
| 2026-11-18 | Criação deste plano | Documento de planejamento registrado em branch documental. |
| 2026-11-18 | Pacote A | Em execução; ver matriz e parecer de baseline associados. |

