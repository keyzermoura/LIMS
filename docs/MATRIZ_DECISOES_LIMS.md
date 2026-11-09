# Matriz de Decisões do Projeto LIMS

**Identificador:** DEC-LIMS-001  
**Versão:** 1.1  
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
| DEC01 | Cardinalidade e semântica dos itens da solicitação | Recomendação técnica adotada no desenho; aprovação institucional pendente | P0 |
| DEC02 | Persistência de todos os itens no recebimento | Proposta | P0 |
| DEC03 | Entrega posterior de item não apresentado | Definida no desenho; exceção formal pendente | P1 |
| DEC04 | Relação entre item recebido, custódia e amostra operacional | Recomendação técnica proposta; aprovação funcional pendente | P0 |
| DEC05 | Dispositivo, unidade física, amostra e corpo de prova | Recomendação técnica proposta; validação por exemplos pendente | P0 |
| DEC06 | Protocolo local do SEFI | Pendente | P1 |
| DEC07 | Identificador institucional da amostra | Recomenda-se formalizar accession_number após verificação técnica; aprovação institucional pendente | P0 |
| DEC08 | Migração de amostras legadas | Recomendação técnica proposta: preservar sem backfill indiscriminado | P0 |
| DEC09 | Atos que exigem assinatura eletrônica | Pendente | P1 |
| DEC10 | Categorias de materiais e checklists | Pendente | P1 |
| DEC11 | Escopo organizacional e multi laboratório | Diretriz de extensibilidade definida; arquitetura inicial pendente | P1 |
| DEC12 | Retenção, backup e recuperação | Pendente | P1 |

## 4. Registro detalhado das decisões

### DEC01 — Cardinalidade e semântica dos itens da solicitação

- **Questão:** uma solicitação pode conter um ou vários dispositivos/itens?
- **Estado:** Recomendação técnica adotada para o desenho conceitual; aprovação institucional pendente. **Prioridade:** P0.
- **Diretriz adotada:** uma solicitação pode conter vários itens declarados, registrados em linhas independentes. Cada linha representa o objeto/tipo de material declarado e deve preservar sua descrição, identificação e quantidade informada. O recebimento apresenta todas as linhas, mesmo quando algum material não é apresentado.
- **Distinção obrigatória:** item declarado não é sinônimo de unidade física, amostra operacional ou corpo de prova. A quantidade declarada e a quantidade efetivamente apresentada devem ser registradas separadamente. A regra de correspondência entre unidades físicas aceitas e registros de amostra será detalhada em DEC05, sem presumir equivalência antes da validação dos exemplos operacionais.
- **Alternativas rejeitadas para o desenho-base:** limitar toda solicitação a um único dispositivo; ou introduzir configuração variável por tipo de demanda sem requisito institucional que a justifique.
- **Justificativa:** o modelo de múltiplos itens representa solicitações compostas sem obrigar a fragmentação artificial em vários protocolos, permite conferência e decisão independentes e preserva a rastreabilidade de itens apresentados e não apresentados.
- **Impactos:** cardinalidades do modelo, telas, numeração, conferência, custódia, aceite, criação de amostras, relatórios e migração. O diagnóstico legado deverá ser tratado como fluxo atual a compatibilizar, não como limitação obrigatória do modelo futuro.
- **Evidência ainda necessária:** validar exemplos representativos de solicitações reais do SEFI e obter aprovação do responsável funcional/institucional.
- **Responsável:** responsável funcional SEFI, com aprovação institucional quando aplicável.
- **Próximo passo:** utilizar esta diretriz como premissa do modelo conceitual e validar DEC05 com exemplos reais. Não implementar antes da aprovação do portão G0.

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

- **Questão:** como registrar a custódia desde a chegada física e manter vínculo íntegro quando a amostra operacional for criada depois?
- **Estado:** Recomendação técnica proposta para o desenho; aprovação funcional/institucional pendente. **Prioridade:** P0.
- **Recomendação:** introduzir no modelo conceitual um objeto de custódia do material recebido (denominação provisória: **ObjetoCustodia**), subordinado ao ItemRecebimento. Ele representa o material efetivamente apresentado que permanece sob guarda. Pode representar uma unidade individual ou um conjunto homogêneo/agrupado quando a identificação individual não for necessária e a regra técnica permitir.
- **Eventos:** registrar a chegada e a primeira guarda no ObjetoCustodia, com data/hora efetiva, recebedor físico, localização e condição. Transferências posteriores são eventos append-only. A amostra operacional criada após aceite mantém referência rastreável ao ObjetoCustodia de origem; a transferência para a custódia laboratorial é um evento explícito, não a criação retroativa da cadeia.
- **Integridade:** evitar referência polimórfica sem integridade referencial. Recomenda-se que os eventos de custódia apontem para uma entidade persistente de objeto de custódia, e que esta se relacione com ItemRecebimento e, quando aplicável, UnidadeRecebida e AmostraOperacional. A implementação física e cardinalidade final dependem de DEC05.
- **Alternativa não recomendada:** vincular eventos pré-aceite diretamente a DeviceSample, pois a amostra ainda não existe; também não se recomenda uma FK polimórfica livre que aceite IDs sem garantir o tipo e a existência do objeto.
- **Recusa:** material recusado continua sob custódia até devolução/transferência efetivamente registrada. A recusa não encerra automaticamente a custódia.
- **Impactos:** novo relacionamento de custódia, API, relatórios, auditoria e compatibilidade com ChainOfCustody existente.
- **Responsáveis:** responsável técnico/laboratorial, responsável funcional e arquitetura técnica.
- **Próximo passo:** validar com exemplos de material individual e agrupado; depois detalhar modelo físico. Não implementar antes do G0.

### DEC05 — Dispositivo, unidade física, amostra operacional e corpo de prova

- **Questão:** quais níveis materiais devem ser representados e quando cada um gera uma amostra operacional?
- **Estado:** Recomendação técnica proposta; validação com exemplos reais e aprovação funcional pendentes. **Prioridade:** P0.
- **Definições recomendadas:**
  - **ItemDeclarado:** linha de produto/material informada na solicitação, com quantidade declarada.
  - **ItemRecebimento:** registro da apresentação e conferência da linha declarada; registra quantidade efetivamente apresentada.
  - **Unidade física:** objeto individual que pode ser identificado separadamente (por exemplo, uma seringa, agulha ou equipo).
  - **ObjetoCustodia:** unidade física ou agrupamento homogêneo que constitui uma unidade de guarda/rastreabilidade no processo.
  - **AmostraOperacional:** registro LIMS criado após aceite para controlar o trabalho laboratorial e seus resultados; não deve ser tratado automaticamente como sinônimo de cada unidade física.
  - **Corpo de prova:** unidade/porção preparada ou selecionada para um ensaio específico, subordinada à amostra ou ao plano de ensaio conforme método.
- **Regra recomendada para criação de amostra:** criar uma AmostraOperacional por objeto aceito que precise de rastreabilidade, decisão ou resultado independente no LIMS. Se várias unidades físicas forem tecnicamente homogêneas e avaliadas como um único conjunto, permitir um agrupamento explícito com quantidade e identificação preservadas; não criar uma amostra por unidade apenas por conveniência de modelagem. Se cada unidade tiver identidade, resultado ou destino independente, cada uma deve ter registro próprio.
- **Corpos de prova:** uma amostra pode originar vários corpos de prova e vários ensaios. A quantidade de corpos de prova decorre do método/plano de ensaio, não da quantidade de itens declarados.
- **Exemplos de aplicação a validar:**
  1. Dez agulhas do mesmo fabricante, lote e especificação, avaliadas como conjunto: um ObjetoCustodia agrupado e uma amostra operacional do conjunto, se a regra laboratorial permitir; discriminar unidades quando houver necessidade de rastreio individual.
  2. Três seringas com números de série distintos e resultados individuais: três objetos de rastreabilidade e, em princípio, três amostras operacionais.
  3. Um equipo submetido a vários ensaios: uma amostra operacional pode originar vários corpos de prova/execuções, sem multiplicar a amostra por ensaio.
  4. Dez unidades recebidas, mas apenas cinco apresentadas: quantidade declarada 10, apresentada 5; as cinco ausentes permanecem NAO_APRESENTADO e não geram custódia nem amostra.
  5. Embalagem coletiva sem identificação individual das unidades internas: registrar o agrupamento/embalagem como objeto de custódia, detalhando quantidade e lote, até que procedimento técnico determine a individualização.
- **Restrições:** não usar apenas fabricante+lote como chave universal de unidade; não assumir serial obrigatório; não equiparar corpo de prova a amostra operacional; não criar amostra para material não apresentado, pendente ou recusado.
- **Evidência necessária:** validar os exemplos com registros reais anonimizados e representantes de categorias distintas do SEFI.
- **Responsáveis:** responsável técnico/laboratorial e responsável funcional.
- **Próximo passo:** selecionar casos reais representativos e confirmar a regra de agrupamento antes de congelar cardinalidades.

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

- **Questão:** qual campo representa o identificador institucional único da amostra?
- **Estado:** Diretriz funcional definida; recomendação técnica proposta; aprovação institucional e verificação de consumidores pendentes. **Prioridade:** P0.
- **Diretrizes definidas:** cada amostra operacional aceita recebe identificador institucional único no âmbito institucional, sem prefixo SEFI como restrição de escopo. Harpya é referência externa opcional. O identificador LIMS é gerado no backend, com unicidade no banco, idempotência, auditoria e sem reutilização.
- **Recomendação:** adotar `DeviceSample.accession_number` como candidato preferencial a identificador institucional, pois já existe e é gerado pelo sistema. Não criar outro campo equivalente nem renumerar registros antes de mapear todos os usos e comprovar que o campo atual atende ao escopo global institucional.
- **Condições para confirmar:** verificar unicidade histórica, sequence, formato, colisões potenciais entre laboratórios, QR Code, etiquetas, relatórios, exportações e integrações. O formato visual atual `LIMS-AAAA-######` é uma implementação observada, não uma decisão institucional sobre formato futuro.
- **Se o campo atual não atender:** preservar `accession_number` e introduzir eventual identificador novo de forma aditiva, com mapeamento explícito e compatibilidade. Não alterar payload/algoritmo do QR sem análise e autorização.
- **Responsáveis:** gestão institucional, responsável funcional e arquitetura técnica.
- **Próximo passo:** produzir relatório de referências de código e testes de unicidade/escopo antes da decisão final.

### DEC08 — Migração de amostras legadas

- **Questão:** como tratar amostras antigas sem solicitação/recebimento vinculados no novo modelo?
- **Estado:** Recomendação técnica proposta; aprovação institucional pendente. **Prioridade:** P0.
- **Recomendação principal:** manter amostras legadas sem vínculo com Solicitação/Recebimento quando não houver evidência documental inequívoca. Não criar recebimentos fictícios, não preencher relações por aproximação de datas, fabricante, lote ou texto e não reescrever a cadeia histórica.
- **Migração:** aditiva e compatível (expand/contract); novas relações opcionais para legado e exigidas no novo fluxo conforme regras aprovadas. Preservar IDs, accession_number, QR, datas, autoria, status, ensaios, resultados, assinaturas, auditoria e eventos ChainOfCustody.
- **Associação seletiva:** somente para casos documentados e confirmados, com evidência, critério determinístico, responsável, data/hora e relatório de reconciliação. Casos ambíguos permanecem sem vínculo.
- **Backfill:** não executar backfill indiscriminado. A ausência de vínculo deve ser estado legítimo do legado.
- **Rollback:** backup restaurável e ensaio de recuperação em ambiente isolado; não presumir que downgrade Alembic seja suficiente.
- **Responsáveis:** arquitetura técnica, TI responsável pelo banco e responsável funcional/qualidade.
- **Próximo passo:** diagnóstico somente leitura do banco-alvo e inventário dos consumidores, após autorização e disponibilidade de ambiente seguro.

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
2. Validar institucionalmente a diretriz DEC01 (solicitação com múltiplos itens declarados) usando exemplos reais e concluir DEC05 sobre a relação entre item declarado, unidade física e amostra.
3. Fechar DEC04 e DEC05 por meio do modelo conceitual e de um diagrama de sequência.
4. Definir DEC07 após análise de accession_number e QR Code.
5. Elaborar estratégia de migração para DEC08.
6. Identificar responsáveis institucionais para DEC09–DEC12.
7. Após as decisões bloqueadoras, produzir modelo entidade-relacionamento, estados/transições e critérios de aceite.
8. Submeter o pacote ao portão G0. Somente após aprovação explícita e autorização específica poderá começar a implementação da Fase 1.

## 8. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 1.0 | 2026-11-09 | Primeira consolidação das decisões DEC01–DEC12 e regras funcionais previamente acordadas. |\n| 1.1 | 2026-11-09 | Inclusão de recomendações técnicas para DEC04, DEC05, DEC07 e DEC08; aprovação institucional permanece pendente. |
