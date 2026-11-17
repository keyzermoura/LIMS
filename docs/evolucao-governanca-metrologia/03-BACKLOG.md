# 03 — Backlog Inicial

Este backlog é uma proposta de decomposição. Os itens ainda precisam ser refinados com evidências, contrato de domínio, critérios de aceite completos e definição de prioridade final antes da implementação.

## Convenções

- IDs estáveis: `EGLM-NNN`.
- Status inicial: `PROPOSTA`.
- Prioridade proposta: P0–P3 conforme plano.
- Não iniciar tarefa sem Definition of Ready.
- Uma tarefa pode gerar uma ou mais Issues GitHub após refinamento.
- Dependências são explícitas; ciclos devem ser resolvidos no planejamento.

## Épico A — Diagnóstico e arquitetura

### EGLM-001 — Inventariar fluxo de execução e gravação definitiva
**Prioridade:** P0 | **Dependências:** nenhuma | **Estado:** PROPOSTA

- Mapear todas as rotas, schemas e serviços que criam/alteram execução e resultado.
- Identificar consumo de assinatura, commits/transações e eventos de auditoria.
- Mapear como equipment_id, method_id e analyst_id chegam ao registro definitivo.

**Aceite:** matriz rota → serviço → validações → entidades → commit → auditoria/assinatura; todos os caminhos de escrita identificados; gaps e riscos documentados.

### EGLM-002 — Mapear estados, transições e responsabilidades do workflow
**Prioridade:** P0 | **Dependências:** EGLM-001

- Levantar status de solicitação, amostra, execução, revisão e laudo.
- Identificar atores que iniciam, executam, conferem, aprovam e emitem.
- Documentar exceções, devoluções, cancelamentos e emendas.

**Aceite:** diagrama de estados validado; matriz papel × ação × transição; estados sem saída, transições não autorizadas e ambiguidades registradas.

### EGLM-003 — Inventariar autorização e endpoints protegidos
**Prioridade:** P0 | **Dependências:** nenhuma

- Catalogar UserRole, ROLE_PERMISSIONS, require_roles, verificações no serviço e guardas frontend.
- Identificar rotas sem autorização granular ou com autorização somente na UI.
- Verificar endpoints administrativos e de assinatura.

**Aceite:** matriz endpoint × permissão × papel × entidade/escopo; todos os pontos de enforcement identificados; riscos priorizados.

### EGLM-004 — Inventariar armazenamento de documentos e anexos
**Prioridade:** P1 | **Dependências:** EGLM-001

- Mapear PDF, certificado, anexos de ensaio, arquivos de instrumentos e demais binários.
- Identificar armazenamento em banco, filesystem, volume ou serviço externo.
- Identificar hash, retenção, backup e política de acesso.

**Aceite:** mapa de artefatos com localização, proprietário, ciclo de vida, tamanho/limites, integridade, permissões e estratégia de backup.

### EGLM-005 — Baseline de testes e CI
**Prioridade:** P0 | **Dependências:** nenhuma

- Identificar jobs/workflows e ambientes.
- Executar lint, typecheck, testes e build de acordo com o README.
- Executar suíte com PostgreSQL real para triggers/sequences/locks.
- Registrar falhas preexistentes sem as atribuir às futuras mudanças.

**Aceite:** relatório reproduzível com comandos, versões, resultados, logs essenciais e baseline de falhas conhecidas.

## Épico B — Governança organizacional e autorização

### EGLM-010 — Especificar árvore de entidades e escopo organizacional
**Prioridade:** P0 | **Dependências:** EGLM-003

- Definir entidade organizacional, tipo, código, pai, estado e vigência.
- Definir se usuário pode pertencer a múltiplas unidades.
- Definir herança de escopo e limites de visibilidade.
- Considerar mudança de lotação sem reescrever a história de registros antigos.

**Aceite:** modelo conceitual e regras de acesso aprovados; exemplos FUNED > DIVISA > SEFI; casos de múltiplas unidades e transferência documentados.

### EGLM-011 — Especificar perfis e permissões granulares
**Prioridade:** P0 | **Dependências:** EGLM-003, EGLM-010

- Definir recursos, ações e permissões atômicas.
- Definir perfis customizáveis e vínculo perfil-entidade.
- Definir precedência, negação explícita, herança e privilégios administrativos.
- Definir segregação de funções e administração delegada.

**Aceite:** catálogo de permissões e matriz papel/perfil × ação × escopo; regras de herança/negação sem ambiguidades; cenários de escalonamento negados.

### EGLM-012 — Projetar migração segura do RBAC atual
**Prioridade:** P0 | **Dependências:** EGLM-010, EGLM-011

- Mapear cada UserRole atual para perfil equivalente.
- Definir migração sem perda de acesso necessário nem ampliação indevida.
- Planejar período de compatibilidade e fallback controlado.
- Definir rollback e trilha de auditoria.

**Aceite:** plano de migração versionado, tabela de equivalência, cenários de rollback e testes para impedir regressão de autorização.

### EGLM-013 — Implementar núcleo de autorização por permissão e escopo
**Prioridade:** P0 | **Dependências:** EGLM-010, EGLM-011, EGLM-012

- Persistir entidades, membership, perfis e permissões após ADR aprovado.
- Integrar deps/policies do backend sem confiar na UI.
- Expor ao frontend apenas permissões efetivas necessárias.
- Auditar concessões, revogações e alterações de perfil.

**Aceite:** testes de allow/deny por recurso, ação, entidade e hierarquia; usuários sem permissão não conseguem operar por API direta; migração validada no PostgreSQL.

### EGLM-014 — Administração e auditoria de permissões
**Prioridade:** P1 | **Dependências:** EGLM-013

- Criar operações administrativas para entidades, memberships, perfis e permissões.
- Impedir remoção do último administrador efetivo.
- Registrar ator, alvo, valores antes/depois, escopo e motivo.
- Prever concessões temporárias com expiração.

**Aceite:** trilha completa e imutável; testes de privilégio mínimo, expiração e proteção contra lockout administrativo.

## Épico C — Competência e habilitação técnica

### EGLM-020 — Especificar ciclo de vida da habilitação por método
**Prioridade:** P0 | **Dependências:** EGLM-001

- Definir método e revisão/versão.
- Definir treinamento, supervisão, avaliação de eficácia, escopo e evidência.
- Definir concessão, suspensão, expiração, revogação e requalificação.
- Definir quem pode autorizar e quais conflitos são proibidos.

**Aceite:** máquina de estados e matriz competência × método × versão × atividade aprovadas.

### EGLM-021 — Garantir enforcement no fluxo de execução
**Prioridade:** P0 | **Dependências:** EGLM-020

- Verificar habilitação no backend na criação/início e na gravação definitiva quando exigido.
- Definir comportamento para habilitação vencida durante execução.
- Revalidar antes da assinatura/conclusão.
- Registrar versão e snapshot da evidência de habilitação utilizada.

**Aceite:** casos positivos e negativos cobrem API direta, alteração concorrente, expiração e revogação; operação não autorizada é bloqueada no backend com motivo auditável.

### EGLM-022 — Evoluir evidências de treinamento e avaliação
**Prioridade:** P1 | **Dependências:** EGLM-020

- Avaliar anexos, certificados, avaliação prática, supervisão e eficácia.
- Relacionar registros a método/versão e qualificação.
- Definir retenção e assinatura do autorizador.

**Aceite:** evidências consultáveis e rastreáveis; mudanças preservam histórico e não permitem qualificação sem requisitos configurados.

## Épico D — Equipamentos e metrologia

### EGLM-030 — Especificar modelo de ativo, certificado e calibração histórica
**Prioridade:** P0 | **Dependências:** EGLM-001, EGLM-004

- Definir tag patrimonial e identidade única.
- Separar equipamento, evento de calibração e documento/certificado.
- Definir status: em serviço, bloqueado, manutenção, fora de uso e não aplicável.
- Definir validade, escopo/faixa, resultado, laboratório calibrador e rastreabilidade.
- Definir política para calibração vencida, não aplicável, uso fora de faixa e exceções.

**Aceite:** modelo conceitual e regras de elegibilidade de uso aprovados; histórico não depende da edição do registro corrente.

### EGLM-031 — Projetar snapshot metrológico por execução
**Prioridade:** P0 | **Dependências:** EGLM-030, EGLM-001

- Definir momento de captura: seleção, início, medição e fechamento.
- Persistir identidade, condição, validade, certificado e hash do documento aplicável.
- Definir se múltiplos equipamentos podem ser associados a uma execução.
- Definir forma de preservar documentos mesmo após substituição/arquivamento.

**Aceite:** contrato de snapshot aprovado; snapshot demonstra exatamente os dados usados e é imutável após fechamento.

### EGLM-032 — Aplicar bloqueio metrológico no backend
**Prioridade:** P0 | **Dependências:** EGLM-030, EGLM-031

- Enforçar validação em todo caminho definitivo de escrita.
- Resolver corrida entre validação e alteração do estado do equipamento.
- Definir bloqueio transacional/concorrência e política de contingência.
- Registrar falha e motivo.

**Aceite:** nenhum endpoint de escrita permite registrar resultado com instrumento inelegível; testes negativos, concorrência e PostgreSQL real aprovados.

### EGLM-033 — Completar gestão documental de certificados
**Prioridade:** P1 | **Dependências:** EGLM-030, EGLM-004

- Armazenar certificados, metadados, hashes, emissor, escopo e vigência.
- Definir limites de arquivo, formatos permitidos e controle de acesso.
- Definir alertas de vencimento e histórico de substituição.

**Aceite:** documento é recuperável, hash verificável, acesso auditado e substituição não altera snapshots anteriores.

## Épico E — Conferência, revisões e laudo oficial

### EGLM-040 — Especificar workflow e matriz de segregação
**Prioridade:** P0 | **Dependências:** EGLM-002, EGLM-011

- Definir recebimento/SGA, planejamento, execução, conferência técnica e emissão.
- Definir transições válidas e quem pode executá-las.
- Definir regras de devolução, correção, rejeição, ausência, impedimento e substituição.
- Definir segregação executor/conferente/emissor e exceções formalizadas.

**Aceite:** diagrama e matriz de segregação aprovados; toda transição tem pré-condições, ator, assinatura e evento de auditoria quando exigido.

### EGLM-041 — Separar revisão de resultado e revisão de documento
**Prioridade:** P0 | **Dependências:** EGLM-040

- Definir versionamento de dados de ensaio e revisão documental R00/R01...
- Relacionar cada revisão a um conjunto fechado de resultados, métodos, equipamentos e evidências.
- Definir emissão inicial e emenda/retificação.
- Definir numeração e documento vigente sem apagar anteriores.

**Aceite:** modelo evita ambiguidade entre versões técnicas e revisões documentais; cadeia de versões é navegável e verificável.

### EGLM-042 — Especificar conteúdo e identidade do PDF oficial
**Prioridade:** P1 | **Dependências:** EGLM-041

- Especificar layout institucional FUNED.
- Definir dados obrigatórios, regra de decisão e declaração aplicável.
- Definir representação de assinaturas, identidades, significados, datas e hashes.
- Definir QR/código de verificação e conteúdo verificável.
- Definir requisitos de acessibilidade, impressão e legibilidade.

**Aceite:** modelo de laudo aprovado pelo responsável institucional; checklist de conteúdo e exemplos de casos normais, emenda e múltiplos ensaios.

### EGLM-043 — Integrar emissão, armazenamento e reimpressão
**Prioridade:** P1 | **Dependências:** EGLM-041, EGLM-042

- Preservar PDF emitido e seu hash.
- Registrar emissão, download e reimpressão conforme política definida.
- Garantir que reimpressão não regenere silenciosamente conteúdo histórico.
- Auditar qualquer nova emissão/retificação.

**Aceite:** PDF recuperado é byte a byte idêntico ao artefato emitido, salvo fluxo formal de nova revisão; reimpressão é rastreada.

## Épico F — Auditoria, observabilidade e backup

### EGLM-050 — Auditar cobertura de antes/depois
**Prioridade:** P1 | **Dependências:** EGLM-003

- Inventariar serviços de escrita para cadastros e entidades reguladas.
- Verificar consistência dos snapshots.
- Adicionar cobertura onde faltar, sem duplicar eventos.
- Definir política de dados sensíveis no payload.

**Aceite:** matriz entidade/operação × evento antes/depois; testes garantem conteúdo, autoria, motivo, assinatura e atomicidade quando aplicável.

### EGLM-051 — Auditar visualização, impressão e reimpressão
**Prioridade:** P1 | **Dependências:** EGLM-043

- Definir quais eventos devem ser registrados: consulta, download, impressão, reimpressão, exportação.
- Definir ator, documento/revisão, finalidade/motivo e contexto.
- Diferenciar acesso técnico do evento de negócio.

**Aceite:** eventos definidos e registrados sem alterar documento emitido; auditoria de operações sensíveis verificável.

### EGLM-052 — Padronizar logs e correlação de exceções
**Prioridade:** P1 | **Dependências:** nenhuma

- Verificar propagação de request_id em middleware, logs, exceções e tarefas em background.
- Definir logs estruturados e campos mínimos.
- Definir mascaramento de dados pessoais e credenciais.
- Definir alertas, retenção e rotação.

**Aceite:** requisição rastreável do HTTP ao erro e evento de auditoria quando aplicável; nenhum segredo ou dado restrito exposto nos logs.

### EGLM-053 — Projetar política e rotina de backup
**Prioridade:** P0 | **Dependências:** EGLM-004

- Definir escopo: PostgreSQL, PDFs, anexos, certificados, configuração não secreta e chaves sob política própria.
- Definir RPO/RTO, periodicidade, retenção, criptografia, destino e responsáveis.
- Definir cópia para rede TI somente após especificação do compartilhamento e credenciais seguras.
- Definir monitoramento e política de falha.

**Aceite:** procedimento executável e aprovado; artefatos identificados, protegidos e monitorados; segredos excluídos do repositório.

### EGLM-054 — Implementar e testar restauração
**Prioridade:** P0 | **Dependências:** EGLM-053

- Restaurar banco e documentos em ambiente isolado.
- Validar integridade relacional e hashes de arquivos.
- Medir RPO/RTO e registrar passos.
- Documentar recuperação e responsáveis.

**Aceite:** restauração demonstrada em ambiente isolado com relatório, evidências e tempos medidos; nenhum dado de produção é sobrescrito.

## Relações de dependência

```text
EGLM-001 ─┬─> EGLM-020 ─> EGLM-021 ─> EGLM-022
          ├─> EGLM-030 ─> EGLM-031 ─> EGLM-032
          │                         └─> EGLM-033
          ├─> EGLM-002 ─> EGLM-040 ─> EGLM-041 ─> EGLM-042 ─> EGLM-043
          └─> EGLM-004 ─> EGLM-053 ─> EGLM-054

EGLM-003 ─> EGLM-010 ─> EGLM-011 ─> EGLM-012 ─> EGLM-013 ─> EGLM-014
    └────────────────────────────────────────────> EGLM-040

EGLM-052 pode avançar em paralelo após análise de contexto.
EGLM-050 depende do inventário de serviços de escrita.
EGLM-051 depende do fluxo de documentos definido em EGLM-043.
EGLM-005 estabelece baseline antes de alterações estruturais.
```

## Sequência recomendada de início

1. EGLM-001, EGLM-003 e EGLM-005 em paralelo.
2. EGLM-002 e EGLM-004.
3. Refinar F1/F2/F3 em conjunto para definir contratos e pontos de enforcement.
4. Tratar workflow documental após os conceitos de autorização e evidência.
5. Planejar backup antes de qualquer mudança de armazenamento e testar restauração antes do release.

## Regra de gestão

O backlog não constitui autorização automática para implementar. A tarefa passa a `PRONTA` somente após revisão dos critérios, riscos, contratos e responsáveis.
