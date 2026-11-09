# Matriz de Decisões do Projeto LIMS

**Identificador:** DEC-LIMS-001  
**Versão:** 1.0  
**Situação:** Proposta consolidada — aprovação funcional/institucional pendente  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Data:** 2026-11-09

---

## 1. Objetivo

Consolidar decisões funcionais, institucionais e arquiteturais necessárias ao desenvolvimento do LIMS, registrando o que já foi expressamente definido, o que permanece pendente e quais impactos precisam ser avaliados antes de qualquer implementação.

Esta matriz é instrumento de governança e rastreabilidade. A classificação de uma decisão como “definida no desenho” registra uma orientação expressa do projeto, mas não substitui aprovação formal da autoridade institucional competente quando esta for necessária.

## 2. Estados e critérios

| Estado | Significado |
|---|---|
| **Definida no desenho** | Orientação expressamente acordada no trabalho funcional; ainda pode exigir formalização institucional. |
| **Proposta** | Alternativa recomendada para avaliação; não deve ser implementada como decisão aprovada. |
| **Pendente** | Não há decisão suficiente; exige resposta do responsável funcional/institucional. |
| **Aprovada formalmente** | Decisão aprovada pela autoridade competente e registrada com evidência. |
| **Substituída** | Decisão revogada ou substituída por outra, mantendo histórico. |

Prioridade: **P0** bloqueadora; **P1** alta; **P2** média.

## 3. Resumo executivo

| ID | Tema | Estado atual | Prioridade |
|---|---|---|---|
| DEC01 | Cardinalidade e semântica dos itens da solicitação | Pendente | P0 |
| DEC02 | Persistência de todos os itens no recebimento | Proposta | P0 |
| DEC03 | Entrega posterior de item não apresentado | Definida no desenho; exceção formal pendente | P1 |
| DEC04 | Relação entre item recebido, custódia e amostra operacional | Pendente | P0 |
| DEC05 | Dispositivo, unidade física, amostra e corpo de prova | Parcialmente definido; exemplos pendentes | P0 |
| DEC06 | Protocolo local do SEFI | Pendente | P1 |
| DEC07 | Identificador institucional da amostra | Diretriz definida; compatibilidade técnica pendente | P0 |
| DEC08 | Migração de amostras legadas | Pendente | P0 |
| DEC09 | Atos que exigem assinatura eletrônica | Pendente | P1 |
| DEC10 | Categorias de materiais e checklists | Pendente | P1 |
| DEC11 | Escopo organizacional e multi laboratório | Diretriz de extensibilidade definida; arquitetura inicial pendente | P1 |
| DEC12 | Retenção, backup e recuperação | Pendente | P1 |

## 4. Registro detalhado das decisões

### DEC01 — Cardinalidade e semântica dos itens da solicitação

- **Questão:** uma solicitação pode conter um ou vários dispositivos/itens?
- **Estado:** Pendente. **Prioridade:** P0.
- **Contexto:** o diagnóstico anterior descreve uma relação de solicitação com um dispositivo na rotina analisada; o desenho funcional posterior contempla vários itens declarados na mesma solicitação, com decisões independentes. O glossário distingue item declarado de unidade física, amostra operacional e corpo de prova, mas a semântica precisa ser confirmada com exemplos reais.
- **Alternativas:** (1) uma solicitação corresponde obrigatoriamente a um dispositivo; (2) uma solicitação pode conter várias linhas/itens declarados, cada qual com uma ou mais unidades físicas; (3) modelo configurável por tipo de demanda.
- **Recomendação para discussão:** alternativa 2, se compatível com o processo institucional. Manter explícitos os níveis item declarado, unidade física e amostra operacional.
- **Impactos:** cardinalidades do modelo, telas, numeração, conferência, custódia, aceite, criação de amostras, relatórios e migração.
- **Evidência necessária:** exemplos representativos de solicitações reais do SEFI e confirmação do responsável funcional.
- **Responsável:** responsável funcional SEFI, com aprovação institucional quando aplicável.
- **Próximo passo:** confirmar a semântica de “item” e “unidade” e registrar exemplos. Não implementar antes da decisão.

### DEC02 — Entidade persistente para todos os itens do recebimento

- **Questão:** como persistir todos os itens declarados, inclusive os não apresentados?
- **Estado:** Proposta. **Prioridade:** P0.
- **Contexto:** a tela de recebimento deve apresentar a relação completa dos itens da solicitação; cada item tem situação de apresentação e conferência próprias.
- **Alternativas:** manter itens apenas em campos agregados; criar entidade persistente por item do recebimento; criar entidade de linha vinculada ao item declarado.
- **Recomendação:** entidade persistente por item declarado no contexto do recebimento (nome conceitual ReceiptItem ou ReceiptLine), com relação explícita à solicitação/item de origem.
- **Requisitos mínimos:** registrar apresentado/não apresentado; permitir conferência, pendências, evidências e decisão individual; preservar histórico; não criar amostra para item não apresentado.
- **Impactos:** modelo relacional, integridade referencial, auditoria, API e interface.
- **Responsável:** responsável funcional e arquitetura técnica.
- **Próximo passo:** decidir após DEC01 e desenho de domínio.

### DEC03 — Entrega posterior de item não apresentado

- **Questão:** como tratar material entregue depois da chegada registrada?
- **Estado:** Definida no desenho; exceção formal pendente. **Prioridade:** P1.
- **Regra definida:** material não apresentado na única chegada não pode ser incluído posteriormente como se estivesse presente na data original.
- **Alternativa ordinária definida:** abrir nova solicitação para a entrega posterior.
- **Alternativa excepcional a formalizar:** evento complementar autorizado, sem criar segundo recebimento principal e sem alterar a chegada original.
- **Impactos:** custódia, histórico de chegada, vínculo documental e auditoria.
- **Responsável:** gestão institucional/responsável funcional.
- **Próximo passo:** decidir se haverá exceção e definir autoridade, justificativa, limites e trilha de aprovação.

### DEC04 — Relação entre item recebido, conferência, custódia e amostra operacional

- **Questão:** como se relacionam o item declarado, o registro de recebimento, os eventos de custódia e a amostra operacional?
- **Estado:** Pendente. **Prioridade:** P0.
- **Contexto:** no sistema atual, custódia e eventos iniciais estão ligados diretamente à amostra operacional; no fluxo pretendido, a custódia começa na chegada física, antes da criação da amostra.
- **Princípios definidos:** um recebimento principal por solicitação; conferência e decisão independentes por item; custódia começa na chegada; amostra operacional e identificador são criados somente após aceite final e validações obrigatórias.
- **Alternativas a avaliar:** eventos de custódia ligados a uma entidade de material recebido; custódia por unidade física; associação posterior e auditável à amostra operacional; ou modelo híbrido com evento de recebimento e transferência para custódia da amostra.
- **Recomendação:** não reutilizar sem análise a relação atual de custódia para representar período anterior à amostra. Projetar vínculo rastreável entre custódia pré-aceite e amostra criada.
- **Impactos:** modelo de domínio, histórico, integridade, concorrência, relatórios e compatibilidade.
- **Responsável:** arquitetura técnica e responsável funcional.
- **Próximo passo:** produzir diagrama de sequência e cardinalidades antes de aprovar a solução.

### DEC05 — Dispositivo, unidade física, amostra operacional e corpo de prova

- **Questão:** quais são os níveis materiais distintos e como se relacionam?
- **Estado:** Parcialmente definido; exemplos operacionais pendentes. **Prioridade:** P0.
- **Definições de trabalho:** item declarado é o objeto informado na solicitação; unidade física é o material efetivamente apresentado; amostra operacional é o registro LIMS criado após aceite; corpo de prova é a porção/unidade utilizada em ensaio específico.
- **Risco:** tratar todos esses conceitos como sinônimos pode gerar contagem incorreta, duplicidade, perda de rastreabilidade e associação inadequada dos resultados.
- **Próximo passo:** validar exemplos por categoria de dispositivo e por tipo de ensaio; definir quando uma amostra gera vários corpos de prova ou quando várias unidades físicas geram amostras distintas.
- **Responsável:** responsável técnico/laboratorial e responsável funcional.

### DEC06 — Protocolo local do SEFI

- **Questão:** qual a regra de numeração do protocolo local do laboratório?
- **Estado:** Pendente. **Prioridade:** P1.
- **Contexto:** o identificador institucional do LIMS e o protocolo local possuem finalidades distintas. O protocolo local é complementar.
- **Decisões necessárias:** se haverá protocolo SEFI; escopo e momento de geração; formato; sequência; reinício anual ou não; unicidade; não reutilização; impressão e apresentação em documentos.
- **Restrição:** não usar o protocolo local como chave primária nem como substituto do identificador institucional.
- **Responsável:** gestão/responsável funcional SEFI.
- **Próximo passo:** confirmar necessidade operacional e regra institucional.

### DEC07 — Identificador institucional da amostra

- **Questão:** qual o escopo e a implementação do identificador único da amostra?
- **Estado:** Diretriz definida; compatibilidade técnica pendente. **Prioridade:** P0.
- **Diretrizes definidas:** cada amostra operacional aceita recebe identificador institucional único; o identificador é global no âmbito institucional, não restrito ao SEFI; número Harpya é referência externa opcional, informada pela vigilância quando aplicável; demandas sem Harpya recebem identificador do LIMS; referências externas e protocolos locais são complementares; o identificador é gerado pelo backend na mesma transação de criação da amostra, com unicidade no banco, idempotência, auditoria e sem reutilização.
- **Questão técnica:** verificar se o campo accession_number da amostra já cumpre a função e pode ser formalizado, preservando QR Code e compatibilidade. Se não cumprir, avaliar campo novo e migração aditiva.
- **Pendente:** formato visual, entidade geradora, sequência e escopo entre laboratórios.
- **Responsável:** gestão institucional e arquitetura técnica.
- **Próximo passo:** mapear usos atuais de accession_number e consumidores do QR antes de propor migração.

### DEC08 — Migração de amostras legadas

- **Questão:** como tratar amostras antigas sem solicitação/recebimento vinculados no novo modelo?
- **Estado:** Pendente. **Prioridade:** P0.
- **Princípios:** preservar registros, identificadores, QR, datas, autoria e custódia existentes; não inventar solicitações, itens ou relações sem evidência; manter referências legadas opcionais quando não houver correspondência confiável.
- **Alternativas:** manter legado sem entidade de solicitação; criar registro de migração técnica claramente identificado; vincular apenas quando houver evidência documental confiável.
- **Recomendação:** migração aditiva, sem associação fictícia e sem reescrever a história da amostra.
- **Impactos:** restrições, consultas, relatórios, integridade e compatibilidade.
- **Responsável:** arquitetura técnica e responsável funcional.
- **Próximo passo:** inventariar campos, dados e consumidores; elaborar plano de migração e reconciliação.

### DEC09 — Atos que exigem assinatura eletrônica

- **Questão:** quais ações exigem assinatura eletrônica e qual o significado de cada assinatura?
- **Estado:** Pendente. **Prioridade:** P1.
- **Atos a avaliar:** conferência, aceite, recusa, validação da coordenação, transferência de custódia, execução, revisão técnica, aprovação consolidada e emissão/retificação de laudo.
- **Não presumir:** que toda alteração de campo exige assinatura; auditoria e assinatura são controles distintos.
- **Entregável necessário:** matriz ato × papel autorizado × significado × reautenticação × conteúdo assinado × evidência × possibilidade de delegação.
- **Responsável:** qualidade, gestão institucional e responsável funcional.
- **Próximo passo:** mapear atos críticos e requisitos institucionais/normativos aplicáveis.

### DEC10 — Categorias de materiais e checklists

- **Questão:** quais categorias de materiais, documentos e critérios de conferência se aplicam?
- **Estado:** Pendente. **Prioridade:** P1.
- **Contexto:** o SEFI avalia diferentes dispositivos médicos; a conferência deve ser adequada ao tipo de material e à demanda.
- **Decisões necessárias:** catálogo de categorias; documentos exigidos; critérios impeditivos; critérios saneáveis; evidências; versão e vigência; responsáveis pela aprovação do checklist.
- **Recomendação:** checklists versionados por categoria e contexto, sem codificar regras normativas diretamente na interface.
- **Responsável:** responsável técnico/laboratorial e qualidade.
- **Próximo passo:** levantar categorias e formulários/checklists atualmente utilizados.

### DEC11 — Modelo organizacional e multi laboratório

- **Questão:** a primeira entrega será exclusiva do SEFI ou multi laboratório desde a base?
- **Estado:** Diretriz de extensibilidade definida; arquitetura inicial pendente. **Prioridade:** P1.
- **Diretriz definida:** o identificador institucional não deve conter prefixo SEFI como chave global; o LIMS poderá atender outros laboratórios institucionais.
- **Pendente:** definir se a primeira versão terá escopo operacional SEFI-only com arquitetura extensível ou se exigirá múltiplos laboratórios/unidades desde a primeira migração.
- **Impactos:** modelo de organização, permissões, filas, numeração local, configuração, relatórios e isolamento de dados.
- **Recomendação:** evitar complexidade multi laboratório sem requisito aprovado, mas não codificar o SEFI como pressuposto irreversível.
- **Responsável:** patrocinador/gestão institucional e arquitetura técnica.
- **Próximo passo:** confirmar unidades previstas no horizonte da primeira entrega e requisitos de segregação.

### DEC12 — Retenção, backup e recuperação

- **Questão:** quais políticas de retenção, backup, restauração e continuidade se aplicam?
- **Estado:** Pendente. **Prioridade:** P1.
- **Decisões necessárias:** classes documentais e prazos de retenção; cópias e periodicidade; armazenamento externo; criptografia; RPO; RTO; testes de restauração; responsáveis; descarte autorizado; retenção legal.
- **Restrição:** não definir valores de RPO/RTO ou prazos por suposição técnica sem aprovação institucional.
- **Responsável:** TI institucional, gestão documental/qualidade e gestão do laboratório.
- **Próximo passo:** obter políticas institucionais existentes e propor requisitos de serviço.

## 5. Regras funcionais já definidas no desenho

As regras abaixo foram expressamente acordadas no desenho funcional e devem ser consideradas baseline de análise. A formalização institucional poderá ser necessária antes da implementação.

1. Uma solicitação terá no máximo um registro principal de recebimento; a segunda tentativa deve localizar e exibir o recebimento existente.
2. Correções do recebimento existente exigem permissão, justificativa, versionamento e auditoria.
3. Todos os itens declarados devem permanecer visíveis no recebimento, inclusive os não apresentados.
4. Itens não apresentados não são recusas técnicas, não geram custódia de material ausente e não geram amostra operacional.
5. Conferência e decisão são independentes por item.
6. Pendências podem ser regularizadas no mesmo recebimento quando permitido, mantendo histórico das avaliações anteriores.
7. A coordenação valida quando exigido e não pode dispensar critérios impeditivos.
8. Amostra operacional e identificador institucional somente são criados após aceite final e validações obrigatórias.
9. A custódia começa na chegada física, antes da criação da amostra.
10. Data/hora original da chegada e identidade do recebedor físico devem ser preservadas na transição para a amostra.
11. Material não apresentado não pode ser adicionado retroativamente à chegada original; entrega posterior exige nova solicitação ou exceção institucional formalmente aprovada.
12. A criação da amostra e do identificador deve ser transacional, idempotente, única no banco e auditável.
13. A primeira entrega é de uso interno assistido; não inclui portal ou contas externas para solicitantes.
14. O QR Code atual e as referências legadas devem continuar funcionando durante a evolução.

## 6. Registro de aprovação

| ID | Aprovador competente | Evidência/ata/processo | Data | Estado formal |
|---|---|---|---|---|
| DEC01–DEC12 | A definir conforme governança institucional | A registrar | — | Pendente de aprovação formal |

A ausência de registro de aprovação formal não invalida a documentação de uma orientação funcional, mas impede tratá-la como aprovação institucional definitiva.

## 7. Próximos passos para fechamento da Fase 0

1. Revisar este registro e confirmar se as decisões já definidas refletem corretamente o processo.
2. Resolver DEC01 com exemplos reais de solicitações.
3. Fechar DEC04 e DEC05 por meio do modelo conceitual e de um diagrama de sequência.
4. Definir DEC07 após análise de accession_number e QR Code.
5. Elaborar estratégia de migração para DEC08.
6. Identificar responsáveis institucionais para DEC09–DEC12.
7. Após as decisões bloqueadoras, produzir modelo entidade-relacionamento, estados/transições e critérios de aceite.
8. Submeter o pacote ao portão G0. Somente após aprovação explícita e autorização específica poderá começar a implementação da Fase 1.

## 8. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 1.0 | 2026-11-09 | Primeira consolidação das decisões DEC01–DEC12 e regras funcionais previamente acordadas. |
