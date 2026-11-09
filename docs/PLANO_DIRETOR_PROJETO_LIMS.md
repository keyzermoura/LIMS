# Plano Diretor do Projeto LIMS — Fases, Etapas, Prazos e Governança

- **Projeto:** LIMS institucional — início pelo fluxo SEFI/FUNED
- **Repositório:** \`keyzermoura/LIMS\`
- **Branch documental:** \`main\`
- **Versão:** 1.0 — proposta de linha de base
- **Data:** 09/11/2026
- **Responsável pela aprovação institucional:** a definir
- **Gerenciamento:** apoio de planejamento, acompanhamento, análise de riscos e controle documental com ChatGPT; decisões e aprovações permanecem com o responsável institucional.
- **Status geral:** Planejamento proposto — aguardando aprovação.

---

## 1. Objetivo e mandato de gerenciamento

Este documento estabelece a estrutura de gerenciamento do projeto LIMS, com fases, etapas, entregáveis, dependências, estimativas de duração, critérios de conclusão, riscos e rotina de acompanhamento.

O objetivo é conduzir a evolução do sistema desde a organização do domínio de solicitação e recebimento até a execução laboratorial, emissão de laudos, controles da qualidade e expansão institucional.

O gerenciamento deve manter alinhados:
- necessidades institucionais e operacionais;
- requisitos técnicos e funcionais;
- arquitetura e modelo de dados;
- implementação e migrações;
- testes e evidências;
- validação para o uso pretendido;
- documentação e decisões aprovadas.

### 1.1 Papel do apoio de gerenciamento

O ChatGPT poderá atuar como apoio de gerente de projetos nesta conversa, ajudando a:
1. manter o plano, cronograma, marcos, riscos, pendências e decisões;
2. decompor fases em tarefas executáveis;
3. preparar reuniões de acompanhamento e registrar atas/decisões;
4. revisar entregáveis técnicos e funcionais;
5. confrontar o andamento informado com a linha de base;
6. identificar atrasos, dependências, riscos e impactos;
7. preparar atualizações dos documentos do repositório, mediante solicitação;
8. recomendar replanejamento quando houver mudança de escopo, capacidade ou prazo.

O apoio não substitui gerente formal, responsável técnico, autoridade institucional, equipe de desenvolvimento, homologação ou validação. Não consegue observar automaticamente o trabalho realizado fora desta conversa. O status deverá ser atualizado a partir de evidências compartilhadas pelo usuário ou verificáveis no repositório.

### 1.2 Limites de autorização

Este plano não autoriza alterações no código, banco de dados, migrações, API, frontend, infraestrutura ou ambiente de produção. Cada pacote de implementação deverá ter escopo e critérios de aceite aprovados antes de ser executado.

---

## 2. Premissas para estimativa de prazo

Os prazos abaixo são estimativas preliminares de planejamento, não compromissos contratuais.

### 2.1 Cenário de referência

A linha de base considera:
- um desenvolvedor principal com disponibilidade média aproximada de 20 horas por semana;
- participação do responsável funcional/institucional por aproximadamente 4 a 6 horas semanais para esclarecimentos, decisões e homologação;
- uso da base tecnológica e dos componentes existentes no repositório, após revisão;
- desenvolvimento incremental, com testes automatizados e revisão por etapa;
- implantação inicial voltada ao fluxo interno do SEFI, sem portal externo de solicitantes;
- decisões institucionais tomadas em até cinco dias úteis, sempre que possível;
- ausência de contratação adicional ou integração externa complexa no caminho crítico.

### 2.2 Como interpretar os prazos

- **Duração em semanas:** tempo de calendário estimado para a etapa, considerando as premissas acima.
- **Esforço:** faixa aproximada de horas de trabalho técnico e funcional. Não representa apenas codificação; inclui análise, desenho, implementação, testes e documentação.
- **Reserva:** margem para correções, descobertas técnicas, decisões e retrabalho.
- **Dependência:** uma etapa não deve começar em produção de código antes da aprovação das entradas necessárias.

Se houver mais desenvolvedores, a duração não diminui linearmente: integração, revisão, arquitetura e validação continuam exigindo tempo. Se a disponibilidade for inferior à premissa, o cronograma deverá ser recalculado.

---

## 3. Visão geral do cronograma

| Fase | Nome | Duração estimada | Janela acumulada | Marco de saída |
|---|---|---:|---:|---|
| 0 | Descoberta, decisões e arquitetura | 3 semanas | Semanas 1–3 | Modelo de domínio e requisitos bloqueadores aprovados |
| 1 | Solicitação, recebimento e aceite | 6 semanas | Semanas 4–9 | Fluxo de ingresso testado e homologado |
| 2 | Planejamento e execução laboratorial | 7 semanas | Semanas 10–16 | Execuções e resultados rastreáveis |
| 3 | Revisão, aprovação e laudos | 4 semanas | Semanas 17–20 | Laudo controlado e fluxo de liberação homologado |
| 4 | Qualidade, validação e preparação operacional | 6 semanas | Semanas 21–26 | Evidências e prontidão para uso pretendido |
| 5 | Integrações, indicadores e expansão | 4 semanas | Semanas 27–30 | Melhorias priorizadas entregues ou planejadas |
| — | Reserva de cronograma | 6 semanas | Semanas 31–36 | Absorção de riscos e estabilização |

**Estimativa global de referência: 30 semanas de execução planejada + até 6 semanas de reserva, totalizando aproximadamente 36 semanas.**

A Fase 5 contém funcionalidades de evolução e poderá ser reordenada conforme prioridade institucional. A validação e os controles essenciais não devem ser empurrados para depois da entrada em operação.

---

## 4. Estrutura Analítica do Projeto (EAP)

### Fase 0 — Descoberta, decisões e arquitetura

**Duração:** 3 semanas  
**Prioridade:** bloqueadora  
**Objetivo:** consolidar o modelo de domínio, resolver divergências e estabelecer uma arquitetura implementável sem comprometer dados legados.

| Código | Etapa / atividade | Entregável | Estimativa |
|---|---|---|---:|
| 0.1 | Revisar repositório e diagnóstico técnico | Inventário confirmado de modelos, serviços, rotas, telas, migrações e testes | 3 dias |
| 0.2 | Consolidar requisitos e glossário | Glossário institucional e requisitos rastreáveis | 2 dias |
| 0.3 | Resolver cardinalidade da solicitação e semântica dos itens | Decisão DEC01 aprovada | 2 dias |
| 0.4 | Desenhar entidades e relacionamentos | Diagrama ER e dicionário de dados | 3 dias |
| 0.5 | Definir estados e transições | Máquinas de estado e regras de negócio | 2 dias |
| 0.6 | Planejar migração e compatibilidade | Estratégia de migração, rollback e tratamento de legado | 2 dias |
| 0.7 | Definir critérios de aceite e testes | Matriz requisito–risco–teste–evidência | 1 dia |

**Marco M0:** modelo de domínio, decisões bloqueadoras, estados, migração e critérios de aceite aprovados.

**Condição de saída:** não restar ambiguidade sobre solicitação, item solicitado, unidade física, recebimento, amostra operacional, amostra de ensaio e corpo de prova.

### Fase 1 — Solicitação, recebimento e aceite

**Duração:** 6 semanas  
**Objetivo:** implementar o ingresso controlado de materiais, preservando a separação entre solicitação, chegada física e amostra operacional.

| Código | Etapa / atividade | Entregável | Estimativa |
|---|---|---|---:|
| 1.1 | Modelo e migrações aditivas | Entidades e relações aprovadas, com compatibilidade de legado | 1 semana |
| 1.2 | Cadastro de solicitação e itens | API e interface para cadastro assistido interno | 1 semana |
| 1.3 | Registro do recebimento único | Chegada, recebedor, data/hora e bloqueio de duplicidade | 3 dias |
| 1.4 | Persistência dos itens recebidos | Todos os itens declarados, inclusive não apresentados | 3 dias |
| 1.5 | Conferência e checklist por item | Checklist versionado, observações e evidências | 1 semana |
| 1.6 | Pendência, recusa e coordenação | Decisões independentes, justificativas e histórico | 3 dias |
| 1.7 | Aceite e criação da amostra | Operação atômica, idempotente, identificador e custódia | 1 semana |
| 1.8 | Testes integrados e homologação | Evidências de teste e aceite funcional | 1 semana |

**Marco M1:** fluxo de solicitação, recebimento e aceite homologado.

**Critérios mínimos de saída:**
- uma solicitação não pode ter dois recebimentos principais;
- todos os itens declarados permanecem rastreáveis;
- item não apresentado não gera amostra operacional nem custódia de material;
- decisões são independentes por item;
- aceite não gera amostra duplicada em reenvios ou concorrência;
- data/hora e recebedor físico originais são preservados;
- QR e referências legadas continuam funcionando;
- auditoria registra atos críticos.

### Fase 2 — Planejamento e execução laboratorial

**Duração:** 7 semanas  
**Objetivo:** permitir que ensaios sejam planejados e executados de forma independente, com rastreabilidade técnica.

| Código | Etapa / atividade | Entregável | Estimativa |
|---|---|---|---:|
| 2.1 | Catálogo de ensaios e métodos | Definições e versões controladas | 1 semana |
| 2.2 | Plano de ensaios por amostra | Ensaios requeridos, critérios e sequência | 1 semana |
| 2.3 | Distribuição e atribuição | Responsáveis, filas e histórico de atribuição | 3 dias |
| 2.4 | Modelo de execução | Execução, tentativas, interrupções e repetição | 1 semana |
| 2.5 | Dados brutos e evidências | Anexos, arquivos, cálculos e integridade | 1 semana |
| 2.6 | Equipamentos e condições | Equipamento, situação metrológica e condições ambientais | 1 semana |
| 2.7 | Registro estruturado de resultados | Valores, unidades, critérios e avaliação | 1 semana |
| 2.8 | Testes e homologação | Cenários completos de execução | 3 dias |

**Marco M2:** ensaios planejados e executados com método, versão, analista, equipamento, dados e resultados rastreáveis.

**Critérios mínimos de saída:**
- planejamento não se confunde com execução;
- cada execução tem identidade própria;
- repetição não apaga tentativa anterior;
- dados brutos e cálculos podem ser recuperados;
- método e equipamento utilizados são identificáveis;
- equipamento fora de condição válida pode ser bloqueado conforme regra aprovada;
- resultado é associado à execução correta.

### Fase 3 — Revisão, aprovação e laudos

**Duração:** 4 semanas  
**Objetivo:** estabelecer revisão técnica e liberação documental do conjunto de resultados.

| Código | Etapa / atividade | Entregável | Estimativa |
|---|---|---|---:|
| 3.1 | Fluxo de revisão técnica | Revisão, devolução, correção e histórico | 1 semana |
| 3.2 | Segregação de funções | Regras de incompatibilidade e permissões | 3 dias |
| 3.3 | Aprovação consolidada | Liberação do conjunto de resultados | 3 dias |
| 3.4 | Modelo e geração de laudo | Documento final, dados e responsáveis | 1 semana |
| 3.5 | Assinatura, emissão e retificação | Versões imutáveis e documento substitutivo | 3 dias |
| 3.6 | Testes e homologação | Evidências de revisão e emissão | 2 dias |

**Marco M3:** laudo emitido somente após conclusão dos controles e aprovações exigidos.

**Critérios mínimos de saída:**
- revisor e executor respeitam segregação aprovada;
- resultados não liberados não entram no laudo;
- laudo emitido preserva conteúdo, versão, autoria e assinaturas;
- correção posterior gera nova versão, sem apagar a anterior;
- emissão é idempotente e auditável.

### Fase 4 — Qualidade, validação e preparação operacional

**Duração:** 6 semanas  
**Objetivo:** completar controles de qualidade e demonstrar que o sistema atende ao uso pretendido definido pela instituição.

| Código | Etapa / atividade | Entregável | Estimativa |
|---|---|---|---:|
| 4.1 | Controle documental e métodos | Documentos, vigência e versões | 1 semana |
| 4.2 | Competência e autorização | Matriz por pessoa, método e validade | 3 dias |
| 4.3 | Equipamentos e rastreabilidade metrológica | Cadastro, calibração, manutenção e bloqueios | 1 semana |
| 4.4 | Não conformidade e CAPA | Fluxo ampliado e evidências de eficácia | 3 dias |
| 4.5 | Controle de mudanças e riscos | Processo de mudança e avaliação de impacto | 3 dias |
| 4.6 | Plano de validação do sistema | Requisitos, riscos, testes e rastreabilidade | 1 semana |
| 4.7 | Segurança operacional e recuperação | Backup, restauração, monitoramento e procedimentos | 3 dias |
| 4.8 | Execução de testes e homologação | Relatório de evidências e pendências | 1 semana |

**Marco M4:** prontidão avaliada e decisão institucional documentada sobre uso pretendido.

**Atenção:** esta fase não transforma automaticamente o software em “conforme ISO/IEC 17025”. A instituição deverá avaliar o sistema dentro de seu sistema de gestão, processos, riscos, validação e evidências.

### Fase 5 — Integrações, indicadores e expansão

**Duração:** 4 semanas iniciais; escopo sujeito à priorização  
**Objetivo:** ampliar eficiência e alcance após estabilização dos fluxos essenciais.

| Código | Etapa / atividade | Entregável | Estimativa |
|---|---|---|---:|
| 5.1 | Painéis e indicadores | Indicadores operacionais aprovados | 1 semana |
| 5.2 | Notificações e alertas | Eventos, destinatários e histórico de entrega | 3 dias |
| 5.3 | Integração com instrumentos | Prova de conceito ou integração priorizada | 1 semana |
| 5.4 | Integrações institucionais | Contratos e integração priorizada | 3 dias |
| 5.5 | Avaliação multi laboratório | Modelo organizacional e permissões | 3 dias |
| 5.6 | Portal externo — estudo de viabilidade | Análise de risco e proposta, sem liberação automática | 2 dias |

**Marco M5:** pacote de evolução priorizado entregue ou backlog institucional aprovado.

---

## 5. Marcos de aprovação e governança por portão

Nenhuma fase deve avançar para implementação dependente sem passar pelo respectivo portão de aprovação.

| Portão | Momento | O que precisa ser aprovado |
|---|---|---|
| G0 | Antes da Fase 1 | Modelo de domínio, cardinalidades, estados, identificadores e migração |
| G1 | Antes de liberar o fluxo de recebimento | Testes, integridade, auditoria, permissões, QR e homologação funcional |
| G2 | Antes da Fase 3 | Modelo de execução, dados brutos, métodos e equipamentos |
| G3 | Antes de emitir laudos em operação | Revisão, aprovação, assinaturas, versionamento e modelos de laudo |
| G4 | Antes do uso institucional pretendido | Validação, treinamento, procedimentos, backup, recuperação e aprovação institucional |
| G5 | Antes de expansão | Avaliação de segurança, privacidade, capacidade e integração |

A aprovação de desenho não significa aprovação de implementação. A aprovação de implementação não significa validação para uso institucional.

---

## 6. Caminho crítico e dependências

O caminho crítico preliminar é:

**Decisões de domínio → modelo de dados → migração segura → solicitação/recebimento → criação de amostra → planejamento de ensaio → execução e dados → revisão → aprovação → laudo → validação e liberação institucional.**

Dependências que podem provocar retrabalho:
- cardinalidade da solicitação indefinida;
- semântica indefinida de item, unidade recebida e amostra;
- identificadores sem estratégia de compatibilidade;
- criação da amostra antes de fechar custódia e aceite;
- resultados sem entidade de execução;
- laudo sem congelamento de versão;
- permissões sem segregação de funções;
- migrações sem inventário do legado.

Esses pontos devem ser tratados antes de iniciar as tarefas que dependem deles.

---

## 7. Papéis e responsabilidades

| Papel | Responsabilidade principal |
|---|---|
| Patrocinador / gestor institucional | Prioridades, recursos, decisões institucionais e aprovação dos marcos |
| Responsável funcional SEFI | Requisitos operacionais, regras de negócio e homologação |
| Responsável técnico/laboratorial | Métodos, critérios técnicos, equipamentos, revisão e uso pretendido |
| Desenvolvedor / equipe técnica | Arquitetura, código, banco, testes, segurança e implantação |
| Qualidade / gestão da qualidade | Procedimentos, riscos, validação, evidências e controles |
| Usuários-chave | Avaliação de usabilidade, cenários reais e testes de aceitação |
| Apoio de gerenciamento (ChatGPT) | Plano, cronograma, riscos, pendências, documentação, revisão e relatórios de status |

Uma pessoa poderá acumular mais de um papel, mas a segregação de funções exigida no processo laboratorial deverá ser preservada.

---

## 8. Rotina de gerenciamento

### 8.1 Atualização semanal

A cada ciclo de acompanhamento, registrar:
1. atividades concluídas desde a última atualização;
2. evidências: commits, PRs, testes, documentos ou aprovações;
3. atividades em andamento e percentual estimado;
4. atividades não iniciadas e dependências;
5. impedimentos e decisões necessárias;
6. riscos novos ou alterados;
7. impacto no cronograma;
8. plano da próxima semana.

### 8.2 Relatório de status

Usar o seguinte padrão:

| Campo | Conteúdo |
|---|---|
| Status geral | Verde / Amarelo / Vermelho |
| Fase atual | Fase e etapa |
| Período | Semana de referência |
| Concluído | Entregas verificáveis |
| Em andamento | Atividades e responsáveis |
| Próximos passos | Atividades da próxima janela |
| Impedimentos | Problemas que exigem ação |
| Decisões pendentes | ID, responsável e prazo necessário |
| Riscos | ID, probabilidade, impacto e mitigação |
| Cronograma | No prazo / atenção / atrasado |
| Evidências | Links para commits, PRs, documentos e testes |

### 8.3 Regras de status

- **Verde:** sem impedimento relevante e dentro da tolerância acordada.
- **Amarelo:** risco de atraso, decisão pendente ou dependência ameaçando o marco.
- **Vermelho:** marco comprometido, falha crítica, risco de integridade/segurança ou requisito bloqueador sem solução.
- **Concluído:** somente quando houver evidência verificável e critérios de aceite atendidos.
- **Validado para uso:** somente após evidências e aprovação institucional correspondentes.

### 8.4 Controle de mudanças

Toda alteração relevante de escopo, prazo ou prioridade deve registrar:
- solicitação e justificativa;
- impacto técnico e funcional;
- impacto em prazo e esforço;
- riscos introduzidos;
- decisão e responsável;
- atualização da linha de base, se aprovada.

---

## 9. Registro inicial de riscos

| ID | Risco | Probabilidade inicial | Impacto | Resposta / mitigação |
|---|---|---|---|---|
| R01 | Divergência de cardinalidade entre diagnóstico e desenho | Alta | Alto | Resolver na Fase 0 antes de migração |
| R02 | Modelo legado de amostras incompatível com novo fluxo | Alta | Alto | Inventário, migração aditiva e testes de regressão |
| R03 | Identificadores novos quebrarem QR ou integrações existentes | Média | Alto | Mapear consumidores e manter compatibilidade |
| R04 | Escopo crescer sem controle | Alta | Alto | Backlog priorizado, portões e controle de mudanças |
| R05 | Disponibilidade insuficiente de desenvolvimento | Média | Alto | Confirmar capacidade real e recalcular cronograma |
| R06 | Decisões institucionais demorarem | Média | Alto | Registrar decisor, prazo e impacto no caminho crítico |
| R07 | Testes automatizados não cobrirem cenários reais | Média | Alto | Testes de integração, E2E e homologação com usuários |
| R08 | Auditoria e assinatura não cobrirem novos atos | Média | Alto | Requisitos transversais e testes de integridade |
| R09 | Uso institucional antes de validação adequada | Média | Muito alto | Portão G4 obrigatório e aprovação formal |
| R10 | Falha de backup ou recuperação | Média | Muito alto | Testes de restauração e plano de continuidade |

---

## 10. Backlog inicial de decisões

| ID | Decisão | Prioridade | Estado inicial |
|---|---|---|---|
| DEC01 | Uma solicitação pode conter um ou vários dispositivos/itens? | Bloqueadora | Aguardando decisão |
| DEC02 | Entidade persistente para todos os itens do recebimento | Bloqueadora | Proposta: ReceiptItem/ReceiptLine |
| DEC03 | Tratamento de entrega posterior de item não apresentado | Alta | Aguardando decisão institucional |
| DEC04 | Relação ReceiptItem, conferência, decisão, custódia e DeviceSample | Bloqueadora | Aguardando desenho |
| DEC05 | Distinção entre dispositivo, unidade recebida, amostra de ensaio e corpo de prova | Bloqueadora | Aguardando glossário |
| DEC06 | Regra do protocolo SEFI | Alta | Aguardando decisão |
| DEC07 | Escopo global do identificador institucional | Alta | Diretriz geral definida; detalhamento pendente |
| DEC08 | Migração das amostras legadas | Bloqueadora | Aguardando análise |
| DEC09 | Atos que exigem assinatura eletrônica | Alta | Aguardando matriz |
| DEC10 | Catálogo de materiais e checklists aplicáveis | Alta | Aguardando definição |
| DEC11 | Modelo de laboratório e unidade organizacional | Alta | Aguardando decisão |
| DEC12 | Retenção, backup, RPO e RTO | Alta | Aguardando decisão |

---

## 11. Critérios de conclusão do projeto

O projeto não será considerado concluído apenas porque o código foi desenvolvido ou os testes automatizados passaram.

A conclusão deverá considerar:
1. requisitos aprovados e rastreados a implementações;
2. fluxos críticos testados e homologados;
3. migrações verificadas e dados legados preservados;
4. permissões, segregação de funções e auditoria testadas;
5. assinatura e versionamento verificados;
6. documentação técnica e operacional atualizada;
7. treinamento e procedimentos preparados;
8. backup e restauração demonstrados;
9. validação do sistema para o uso pretendido documentada;
10. aprovação formal da instituição para entrada em operação.

---

## 12. Linha de base e replanejamento

A estimativa de 36 semanas é uma referência inicial, sujeita a revisão após:
- confirmação da equipe e disponibilidade semanal;
- revisão técnica completa do repositório;
- decisão de cardinalidade e modelo de domínio;
- avaliação das dependências institucionais;
- definição do escopo obrigatório da primeira entrada em operação.

O cronograma deverá ser recalculado quando houver mudança material de escopo, capacidade, risco ou dependência. Não se deve reduzir prazo eliminando testes, auditoria, segurança ou validação obrigatória.

---

## 13. Registro de acompanhamento

| Data | Fase / etapa | Status | Evidência / decisão | Impacto no prazo | Próxima ação |
|---|---|---|---|---|---|
| 09/11/2026 | Planejamento inicial | Proposto | Plano Diretor v1.0 criado; linha de base ainda não aprovada | Ainda não iniciado | Confirmar capacidade, papéis e prioridades |
| 09/11/2026 | Fase 0 | Não iniciada | Matriz de lacunas arquiteturais disponível | Sem impacto apurado | Iniciar revisão do modelo de domínio |

---

## 14. Próxima reunião / primeira atividade

A primeira sessão de gerenciamento deve validar a linha de base e iniciar a Fase 0.

Agenda proposta:
1. confirmar objetivo e escopo da primeira versão;
2. identificar quem aprova requisitos e decisões institucionais;
3. confirmar disponibilidade real de desenvolvimento e homologação;
4. resolver DEC01: cardinalidade da solicitação;
5. iniciar glossário e diagrama de domínio;
6. confirmar o mecanismo de atualização semanal do projeto.

**Saída esperada:** plano aprovado ou ajustado, responsáveis identificados, cronograma recalibrado e primeira lista de tarefas priorizada.

---

## 15. Histórico de revisão

| Versão | Data | Alteração |
|---|---|---|
| 1.0 | 09/11/2026 | Criação da proposta de gerenciamento, EAP, cronograma, marcos, riscos e rotina de acompanhamento. |
