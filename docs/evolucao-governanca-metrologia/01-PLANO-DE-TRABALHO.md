# 01 — Plano de Trabalho

## 1. Contexto

O LIMS já possui uma base técnica e regulatória relevante: API FastAPI, PostgreSQL, SQLAlchemy assíncrono, React/TypeScript, assinatura eletrônica, resultados versionados, trilha de auditoria, gestão de equipamentos, qualificações de analistas, revisão técnica e laudo oficial.

A iniciativa não deve reconstruir esses recursos. O trabalho será identificar lacunas reais, completar os controles e integrar os domínios com consistência.

## 2. Objetivo geral

Evoluir o sistema para suportar controles institucionais e laboratoriais com:

- autorização administrativa configurável e hierárquica;
- autorização técnica vigente por analista e método;
- controle metrológico do equipamento efetivamente utilizado;
- evidências históricas imutáveis relacionadas ao ensaio;
- fluxo formal de execução, conferência e emissão;
- revisões documentais independentes das versões de resultados;
- auditoria completa e observabilidade técnica;
- backup, retenção e restauração demonstráveis.

## 3. Objetivos específicos

1. Mapear o comportamento real da autorização atual e propor migração segura do RBAC fixo.
2. Garantir que a qualificação técnica seja verificada na operação de execução e gravação do resultado.
3. Garantir que o equipamento usado esteja adequado ao uso e com situação metrológica válida na data/hora pertinente.
4. Registrar no ensaio um snapshot dos dados/certificado que fundamentaram o uso.
5. Formalizar estados, transições, responsabilidades e segregação de funções nas etapas de revisão e emissão.
6. Preservar documentos emitidos e permitir emendas controladas, justificadas e rastreáveis.
7. Completar cobertura da auditoria e a correlação de logs técnicos.
8. Definir e validar rotinas de backup e testes de restauração.

## 4. Escopo

### Incluído

- Organizações/entidades em árvore e vínculo de usuários a escopos.
- Perfis customizáveis e permissões granulares por recurso/ação.
- Regras de herança, precedência, negação e segregação de funções.
- Qualificações por método, escopo, vigência, evidências e autorização.
- Cadastro e histórico de equipamentos/calibrações/certificados.
- Bloqueios de domínio no backend para registros definitivos.
- Snapshot metrológico associado ao ensaio/execução.
- Fluxo de conferência e emissão, com estados e trilha de transições.
- Revisões documentais R00, R01... e relação com revisões de resultados.
- PDF oficial com conteúdo, dados de decisão e elementos de verificação.
- Auditoria de alterações, reimpressões, operações sensíveis e erros técnicos.
- Procedimentos de backup, retenção, cópia externa e restauração.

### Fora do escopo inicial

- Reescrita integral do LIMS.
- Troca de stack, framework ou banco sem ADR e aprovação.
- Integrações reais com SGA, rede corporativa ou serviços da TI sem contrato e autorização.
- Implantação em produção, alteração de dados reais ou operação com equipamentos físicos.
- Declaração de conformidade/acreditação apenas pela existência de funcionalidades.
- Refatorações não relacionadas que aumentem o risco ou dificultem a revisão.

## 5. Frentes de trabalho

### F1 — Governança organizacional e autorização

Construir modelo de entidades hierárquicas, membership, perfis, permissões e escopo de acesso. Avaliar compatibilidade com UserRole e ROLE_PERMISSIONS. Prever administração e auditoria das próprias permissões.

### F2 — Competência e habilitação técnica

Aproveitar AnalystQualification e TrainingRecord. Garantir vínculo inequívoco método/versão do método/analista, vigência, escopo, evidências e autorizador. Impedir execução e assinatura quando a habilitação exigida estiver ausente, suspensa ou vencida.

### F3 — Equipamentos e metrologia

Aproveitar LaboratoryEquipment e serviços existentes. Completar patrimônio, identificação, documentos, histórico de calibrações, situação, rastreabilidade e adequação ao uso. Impedir gravação definitiva quando o instrumento não puder ser usado e persistir snapshot histórico verificável.

### F4 — Conferência, revisão e emissão

Aproveitar TestReview, estados de revisão e OfficialReport. Formalizar workflow, segregação, transições, revisão documental, relação com emendas e preservação dos PDFs emitidos. Definir o modelo visual institucional após especificação aprovada.

### F5 — Auditoria, observabilidade e continuidade

Completar auditoria de negócio com antes/depois em todos os domínios críticos, eventos de reimpressão e correlação por request ID. Definir backups de banco e documentos, destino, retenção, monitoramento, alertas e teste de restauração.

## 6. Estratégia de execução

### Etapa 0 — Diagnóstico e definição

- Confirmar o HEAD e a estrutura da branch.
- Inspecionar modelos, schemas, rotas, serviços, dependências, frontend, migrações e testes.
- Mapear o que já existe, o que está parcialmente ligado e o que não existe.
- Registrar diagramas, dependências, riscos e decisões pendentes.
- Refinar backlog e aprovar os critérios com o responsável pelo produto.

### Etapa 1 — Fundamentos transversais

- Definir autorização e modelo de escopo organizacional.
- Definir conceitos comuns: método, versão, execução, habilitação, equipamento, certificado, revisão e emissão.
- Definir regras de auditoria, assinaturas e imutabilidade.
- Definir contratos e migração retrocompatível.

### Etapa 2 — Controles de execução

- Completar habilitação técnica.
- Completar controle metrológico e snapshot.
- Aplicar validações no ponto de gravação definitiva do backend.
- Criar testes negativos para qualquer tentativa de contornar os bloqueios.

### Etapa 3 — Workflow documental

- Definir estados e transições.
- Aplicar segregação de funções.
- Integrar conferência, emissão e revisões documentais.
- Gerar e preservar o artefato final verificável.

### Etapa 4 — Auditoria e operação

- Fechar lacunas de auditoria.
- Correlacionar eventos e erros.
- Documentar backup e restauração.
- Executar testes de recuperação em ambiente isolado.

### Etapa 5 — Validação e liberação

- Executar testes unitários, integração e PostgreSQL real.
- Revisar segurança e migrações.
- Fazer revisão independente do diff.
- Gerar evidências e relatório.
- Abrir PR em estado draft para revisão, sem merge automático.

## 7. Priorização

| Prioridade | Definição |
|---|---|
| P0 | Risco de integridade, autorização indevida, perda de rastreabilidade ou emissão sem controle |
| P1 | Controle essencial para o fluxo operacional e evidência técnica |
| P2 | Administração, experiência operacional, automação e observabilidade ampliada |
| P3 | Melhorias incrementais sem impacto no controle essencial |

Prioridade é proposta inicial e deve ser confirmada após diagnóstico de código e avaliação do risco operacional.

## 8. Governança da iniciativa

- Responsável de produto/laboratório: define uso pretendido, regras e aprova critérios.
- Gerente do projeto: mantém escopo, backlog, dependências, riscos, decisões e status.
- Desenvolvimento: implementa tarefas refinadas e registra evidências.
- QA/revisor: valida critérios, testes, regressões e diff.
- Responsável técnico/qualidade: valida requisitos regulatórios e regras de processo.

Uma mesma pessoa pode exercer mais de um papel no projeto, mas o sistema deve preservar segregação de funções exigida para cada processo.

## 9. Fluxo de trabalho de cada tarefa

1. Issue ou tarefa com objetivo e problema.
2. Evidências do estado atual (arquivos, símbolos, testes e comportamento).
3. Regras funcionais e não funcionais.
4. Proposta técnica e impactos.
5. Critérios de aceite testáveis.
6. Implementação limitada ao escopo.
7. Testes e resultados reais.
8. Revisão de código e segurança.
9. Atualização documental e histórico.
10. Aprovação do responsável e integração.

## 10. Definition of Ready

Uma tarefa só está pronta para implementação quando:

- objetivo e problema estão claros;
- regra de negócio possui responsável;
- estado atual foi verificado;
- dependências e contratos são conhecidos;
- migração/retrocompatibilidade foi avaliada;
- critérios de aceite e casos negativos estão definidos;
- impacto em assinaturas, auditoria e imutabilidade foi avaliado;
- riscos e permissões da mudança estão claros.

## 11. Definition of Done

Uma tarefa só é concluída quando:

- critérios de aceite foram atendidos;
- testes pertinentes foram executados e documentados;
- falhas e limitações estão registradas;
- migrações são versionadas e testadas;
- nenhuma regra crítica depende exclusivamente do frontend;
- auditoria e assinatura foram preservadas quando aplicáveis;
- revisão do diff não aponta bloqueadores;
- documentação e histórico foram atualizados.

## 12. Riscos principais

| Risco | Consequência | Mitigação |
|---|---|---|
| Duplicar modelos já existentes | Inconsistência e retrabalho | Diagnóstico antes de propor novos modelos |
| Migrar RBAC sem compatibilidade | Bloqueio de usuários e acessos indevidos | Matriz de equivalência, migração gradual e testes |
| Validar apenas no frontend | Contorno por API direta | Regras obrigatórias no backend e testes HTTP |
| Sobrescrever calibração | Perda de evidência histórica | Histórico imutável e snapshot no ensaio |
| Misturar revisão de resultado e laudo | Ambiguidade documental | Identificadores e ciclos de vida independentes |
| Permitir autoaprovação | Falha de segregação | Regras de conflito de interesse no backend |
| Backup sem teste | Falsa sensação de recuperação | Testes periódicos de restauração documentados |
| Fazer alterações amplas em uma entrega | Revisão difícil e regressão | Issues pequenas, PRs graduais e CI |

## 13. Fontes e referências do projeto

- Repositório LIMS: https://github.com/keyzermoura/LIMS
- Central Global de Skills: https://github.com/Edson-Morais/central-global-skills
- Arquitetura da Central: https://github.com/Edson-Morais/central-global-skills/blob/main/docs/ARCHITECTURE.md
- Metodologia da Central: https://github.com/Edson-Morais/central-global-skills/blob/main/docs/METHODOLOGY.md
- Governança da Central: https://github.com/Edson-Morais/central-global-skills/blob/main/docs/GOVERNANCE.md

## 14. Observação regulatória

As referências à ISO/IEC 17025 são orientadoras para o desenho dos controles. A interpretação de requisitos, aplicabilidade, regras de decisão, evidências requeridas e adequação ao escopo acreditado deve ser confirmada pelo responsável da qualidade/técnico. O software não declara conformidade por si só.
