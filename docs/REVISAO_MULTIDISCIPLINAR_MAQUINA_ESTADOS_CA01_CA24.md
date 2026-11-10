# Revisão Multidisciplinar — Máquina de Estados e Critérios de Aceitação do LIMS

**Identificador:** REV-MD-LIMS-002  
**Versão:** 1.1
**Data:** 2026-11-10  
**Repositório:** keyzermoura/LIMS  
**Base documental:** EST-REC-001 v1.5; MOD-DOM-001 v0.5; AUD-LIMS-001 v1.1; avaliação multidisciplinar compartilhada em 2026-11-09/10.  
**Situação:** revisão documental concluída nesta rodada; complementos propostos registrados; Gate G0 não aprovado; implementação não autorizada.

---

## 1. Objetivo e limites

Avaliar a coerência da máquina de estados das seções 26–27, revisar individualmente os critérios CA01–CA24 e incorporar recomendações da avaliação multidisciplinar anterior. A revisão considera processos SEFI, domínio, arquitetura, segurança, qualidade, QA e gestão de produto/projeto.

A avaliação é documental. Não equivale a inspeção independente do código, execução de testes, validação jurídica, aprovação institucional de competências ou autorização para implementar.

## 2. Parecer executivo

**Conclusão:** a base funcional EST01–EST10 e as cardinalidades M0.2 permanecem coerentes e não precisam ser reabertas. Entretanto, EST-REC-001 v1.4 e CA01–CA24 não cobriam integralmente isolamento do solicitante, semântica de quantidades, temporalidade dos eventos, taxonomia de custódia, identificadores institucionais, contrato de idempotência/concorrência, paginação histórica, evidências binárias e reconciliação de legado.

Foram propostos complementos nas seções 28–30 de EST-REC-001 v1.5 e seção 16 de MOD-DOM-001 v0.5, além dos achados AUD13–AUD22. Os novos critérios CA25–CA37 ampliam a cobertura, mas precisam ser validados com usuários SEFI e convertidos em testes.

## 3. Avaliação por especialidade

### 3.1 Processos e operação SEFI

- Manter o fluxo simples na ponta: registrar chegada, identificar itens, conferir, registrar divergência, pendência e evidência.
- Não expor ao operador detalhes técnicos como chaves de idempotência, versões ou hashes; esses controles devem ser transparentes.
- Preservar a diferença entre o declarado e o observado.
- Permitir conclusão administrativa com itens ausentes, sem aceite presumido.
- Testar a cadeia física da custódia até a devolução/destinação efetiva.
- Validar checklists e justificativas com operadores antes de congelar requisitos em código.

### 3.2 Domínio e modelagem

- Manter Solicitação, Recebimento, ItemRecebimento, ObjetoCustodia e AmostraOperacional separados.
- Não alterar cardinalidades M0.2.
- Não equiparar automaticamente ObjetoCustodia a unidade física.
- Diferenciar quantidade declarada, apresentada e representada.
- Separar protocolo SEFI, accession e QR.
- Tratar custódia como histórico de eventos, com estado atual derivado.
- Não vincular registros legados sem evidência confiável.

### 3.3 Arquitetura e engenharia

- Definir persistência/expiração e escopo das chaves de idempotência.
- Definir controle de versão otimista e resposta a conflito.
- Fazer alteração de negócio, evento de auditoria e consumo de assinatura na mesma transação, quando aplicável.
- Planejar migração aditiva Alembic e compatibilidade com dados legados.
- Definir armazenamento de anexos com hash e metadados.
- Planejar paginação determinística de históricos.
- Não criar endpoints nem migrações nesta fase.

### 3.4 Segurança e conformidade

- Isolar dados do solicitante no servidor, incluindo anexos e listagens.
- Revisar MFA/SSO e ciclo de vida da reautenticação para assinatura.
- Avaliar limites de rate limiting em múltiplos workers.
- Reconhecer que triggers append-only não protegem, isoladamente, contra administrador privilegiado do banco.
- Avaliar ancoragem externa/WORM do hash de auditoria como controle de produção, com análise de custo, operação e recuperação.
- Definir classificação, acesso, retenção e backup de evidências.

### 3.5 QA e qualidade

- Converter CA01–CA37 em testes rastreáveis.
- Executar testes de integridade e concorrência em PostgreSQL real.
- Manter SQLite para testes rápidos quando apropriado, sem tratá-lo como substituto de PostgreSQL.
- Adicionar testes E2E para o fluxo crítico de autenticação, recebimento, assinatura e auditoria.
- Testar cenários negativos, reenvio, concorrência, conflito de versão, permissões e dados legados.

### 3.6 Gestão de produto e projeto

- Evitar análise sem marco de decisão: consolidar bloqueadores e preparar Gate Review M0/G0.
- Priorizar o incremento de recebimento e conferência assistida, mantendo o MVP delimitado.
- Obter feedback direto dos operadores.
- Replanejar prazo e disponibilidade institucional antes de assumir datas; a reserva de seis semanas mencionada na avaliação externa deve ser revalidada, não presumida.
- Fatiar futura Fase 1 em incrementos curtos e verificáveis somente após aprovação e autorização.

## 4. Revisão dos critérios CA01–CA24

| Critério | Parecer | Complemento recomendado |
|---|---|---|
| CA01 | Parcialmente suficiente | Incluir escopo do registro, não apenas permissão da ação; ver CA25. |
| CA02 | Adequado | Testar permissões independentes, autoria e eventos separados. |
| CA03 | Adequado | Cobrir acúmulo de perfis e substituição competente sem autoaprovação. |
| CA04 | Adequado | Testar também combinações de vários critérios impeditivos. |
| CA05 | Adequado | Verificar comunicação, prazo e reavaliação da pendência. |
| CA06 | Adequado com ressalva | Testar NAO_APLICAVEL justificado e regra obrigatória associada. |
| CA07 | Adequado | Acrescentar ausência de custódia/amostra e preservar quantidades declaradas. |
| CA08 | Adequado | Cobrir recebimento parcial, divergência de quantidade e todos os bloqueios de fechamento. |
| CA09 | Adequado | Distinguir custódia ativa, devolução, destinação e encerramento. |
| CA10 | Adequado | Manter custodiante de origem; testar cancelamento antes da entrega. |
| CA11 | Adequado | Confirmar recebedor, localização e tempos do fato/registro. |
| CA12 | Adequado | Testar alertas, escalonamento e prorrogação autorizada. |
| CA13 | Adequado | Evidência recebida não equivale a reavaliação favorável. |
| CA14 | Adequado | Garantir validação independente e assinatura vinculada ao conteúdo. |
| CA15 | Adequado | Bloquear dispensa ad hoc; exigir regra formal prévia se houver exceção normativa. |
| CA16 | Insuficiente isoladamente | Acrescentar repetição após sucesso, chave com payload distinto e requisição em andamento; ver CA31–CA32. |
| CA17 | Adequado | Testar atomicidade entre aceite, validação e criação. |
| CA18 | Adequado | Acrescentar agrupamento/quantidades e destino individual dos objetos. |
| CA19 | Adequado | Testar vínculo entre evento original, autorização, nova decisão e assinatura. |
| CA20 | Adequado | Avaliação de impacto antes de ação operacional; preservar ensaios/laudos. |
| CA21 | Adequado | Testar escalonamento de privilégios e separação entre administrador técnico e autoridade funcional. |
| CA22 | Parcialmente suficiente | Controle de aplicação não basta contra superusuário; complementar com arquitetura/WORM. |
| CA23 | Adequado | Preservar tempos real e de registro; proibir retroatividade fictícia. |
| CA24 | Adequado | Testar reprodutibilidade da versão do checklist e migração formal. |

## 5. Novos critérios propostos

CA25–CA37 foram adicionados à seção 30 de EST-REC-001 v1.5 e cobrem:

- CA25: isolamento do solicitante;
- CA26–CA27: quantidades declaradas/apresentadas/representadas e agrupamento;
- CA28: occurred_at versus recorded_at;
- CA29–CA30: mudança de localização e transferência de custódia;
- CA31–CA33: idempotência, chave reutilizada e conflito de versão;
- CA34: paginação estável de histórico;
- CA35: integridade e metadados de anexos;
- CA36: não associação presumida de legado;
- CA37: distinção entre protocolo SEFI, accession e QR.

## 6. Cenários de aceitação operacional

A validação com o SEFI deverá executar pelo menos os seguintes cenários:

1. Recebimento integral, conferência e aceite.
2. Recebimento parcial com item não apresentado.
3. Divergência de quantidade declarada/apresentada.
4. Item com objetos aceitos e recusados.
5. Pendência saneável, comunicação, vencimento, prorrogação e reavaliação.
6. Recusa e permanência sob custódia até devolução/destinação.
7. Transferência entre responsáveis e mudança de localização sem transferência.
8. Retificação antes/depois da criação de amostra.
9. Reenvio concorrente de recebimento/amostra e conflito de versão.
10. Tentativa de solicitante acessar solicitação ou evidência de terceiro.
11. Consulta paginada do histórico durante novas movimentações.
12. Chegada posterior de material após conclusão como não apresentado.

## 7. Decisões ainda pendentes

### 7.1 Institucionais

- Matriz de competências, cargos, substitutos e autoridade de concessão/revogação.
- Checklists concretos por categoria, classificação E/S/I e versionamento.
- Prazos e canais oficiais de comunicação.
- Regra de numeração do protocolo SEFI e accession.
- Procedimentos de agrupamento, fracionamento e destinação.
- Nível jurídico e tecnologia de assinatura eletrônica.
- Política de acesso externo e vínculo de solicitantes.

### 7.2 Arquiteturais e técnicas

- Modelo de idempotência, retenção e recuperação.
- Controle de versão e contratos de conflito.
- Estratégia de migração aditiva e reconciliação de legado.
- Object storage, hash, metadados, retenção e backup.
- Paginação, ordenação e exportação de históricos.
- Rate limiting distribuído.
- MFA/SSO e desacoplamento da assinatura.
- Proteção externa/WORM da trilha de auditoria.
- CI com PostgreSQL e suíte E2E.

## 8. Plano de continuidade recomendado

1. Validar documentalmente EST-REC-001 v1.5, MOD-DOM-001 v0.5 e os achados AUD13–AUD22.
2. Validar com operadores/representantes do SEFI os 12 cenários simulados em `docs/VALIDACAO_CENARIOS_OPERACIONAIS_SEFI.md`, registrando evidências e ajustes.
3. Elaborar contratos técnicos de idempotência, concorrência, anexos, legado e autorização.
4. Realizar revisão arquitetural e de segurança com evidências do repositório e ambiente.
5. Consolidar matriz institucional de pendências e responsáveis.
6. Preparar Gate G0 com critérios objetivos e parecer de prontidão.
7. Somente após aprovação formal e autorização específica, iniciar modelagem relacional/migrações e sprints da Fase 1.

## 9. Parecer final

A revisão multidisciplinar encontrou complementos importantes, mas não identificou motivo para reabrir as decisões EST01–EST10 ou as cardinalidades M0.2. A máquina de estados v1.4 e CA01–CA24 são uma base coerente, mas insuficiente isoladamente para declarar prontidão funcional completa. Com os complementos registrados em v1.5, CA25–CA37 e os cenários operacionais, o conjunto fica mais completo para a próxima validação.

**Situação do Gate G0: NÃO APROVADO.**  
**Situação da implementação: NÃO AUTORIZADA.**  
**Alterações de código, banco, API, frontend, CI e infraestrutura nesta revisão: NENHUMA.**

A avaliação multidisciplinar externa descreve pontos fortes e riscos do código, mas esta rodada não executou auditoria direta do código ou dos testes. A confirmação desses pontos fica para a etapa própria de arquitetura, segurança e QA.

## 10. Referências internas

- `docs/ESTADOS_E_TRANSICOES_SOLICITACAO_RECEBIMENTO.md` — versão 1.5.
- `docs/MODELO_CONCEITUAL_DOMINIO_SOLICITACAO_RECEBIMENTO.md` — versão 0.5.
- `docs/AUDITORIA_CONSISTENCIA_EST01_EST10.md` — versão 1.1.
- `docs/VALIDACAO_CENARIOS_OPERACIONAIS_SEFI.md` — simulação documental SIM01–SIM12.
- Avaliação multidisciplinar anterior: `Markdown colado(2).md`.



## 11. Atualização — pré-validação das decisões D01–D20

Em 2026-11-10, o usuário pré-validou sequencialmente as vinte decisões consolidadas em `docs/DECISOES_PREVALIDACAO_SEFI_D01_D20.md`. O conjunto cobre recebimento, quantidades, objetos de custódia, pendências, recusa, movimentações, retificação, independência, checklists, evidências, auditoria, controle de acesso, assinatura, backup, identificadores, chegada posterior e admissão de amostras.

**Parecer atualizado:** o conjunto documental pode avançar para validação institucional estruturada com o SEFI. A rodada não substitui a reunião/ratificação institucional nem resolve as dependências técnicas e institucionais listadas no registro D01–D20.

**Gate G0: NÃO APROVADO. Implementação: NÃO AUTORIZADA.** Nenhum código, banco, API, frontend, CI ou infraestrutura foi alterado nesta consolidação.

### Histórico de versões

| 1.1 | 2026-11-10 | Registro da pré-validação das decisões D01–D20 e atualização do encaminhamento ao Gate G0. |
