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
| DEC04 | Relação entre item recebido, custódia e amostra operacional | Aprovada como diretriz de desenho do projeto; formalização institucional pendente | P0 |
| DEC05 | Dispositivo, unidade física, amostra e corpo de prova | Aprovada como diretriz de desenho do projeto; formalização institucional pendente | P0 |
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
- **Estado:** **Aprovada pelo usuário como diretriz de desenho do projeto em 2026-11-09**; formalização institucional pela autoridade competente permanece pendente. **Prioridade:** P0.
- **Decisão adotada:** introduzir a entidade **ObjetoCustodia**, subordinada ao ItemRecebimento, para representar o material efetivamente apresentado que permanece sob guarda. O objeto pode representar uma unidade individual ou um agrupamento homogêneo autorizado pelo procedimento técnico.
- **Início da custódia:** a custódia começa na chegada física, antes do aceite e da criação de DeviceSample. O evento inicial deve preservar data/hora efetiva, recebedor físico, localização e condição do material.
- **Eventos:** transferências, mudanças de localização, devolução e encerramento devem ser eventos auditáveis e cronológicos. Correções não apagam eventos anteriores; geram retificação vinculada.
- **Relação com a amostra:** cada ObjetoCustodia pode estar associado a **no máximo uma DeviceSample**. No fluxo ordinário de material aceito que será ensaiado, a criação da DeviceSample deve ocorrer com vínculo obrigatório ao objeto de origem, na mesma transação. Amostras legadas podem permanecer sem vínculo. Uma DeviceSample do novo fluxo não deve reunir vários ObjetosCustodia.
- **Recusa e pendência:** material pendente ou recusado permanece sob custódia até devolução ou outra destinação efetivamente registrada. A decisão de recusa não encerra automaticamente a custódia.
- **Compatibilidade com ChainOfCustody:** não criar histórico paralelo nem duplicar o evento de chegada. A extensão física da estrutura existente depende de inspeção de FKs, consultas, triggers, relatórios e testes; a solução deve oferecer uma única visão cronológica para eventos legados e novos.
- **Alternativas rejeitadas para o desenho-base:** vincular eventos pré-aceite diretamente a DeviceSample, que ainda não existe; usar FK polimórfica sem integridade referencial; manter associação N:M entre ObjetoCustodia e DeviceSample.
- **Impactos:** modelo relacional, custódia, API, relatórios, auditoria, transação de aceite e compatibilidade com dados legados.
- **Responsáveis:** responsável técnico/laboratorial, responsável funcional e arquitetura técnica.
- **Próximo passo:** refletir a cardinalidade 1:0..1 no modelo relacional preliminar e, após revisão técnica do schema legado, preparar proposta de mapeamento físico. Esta aprovação de desenho não autoriza migração nem implementação.

### DEC05 — Dispositivo, unidade física, amostra operacional e corpo de prova

- **Questão:** quais níveis materiais devem ser representados e quando cada um gera uma amostra operacional?
- **Estado:** **Aprovada pelo usuário como diretriz de desenho do projeto em 2026-11-09**; formalização institucional e validação dos procedimentos técnicos aplicáveis permanecem pendentes. **Prioridade:** P0.
- **Definições adotadas:**
  - **ItemDeclarado:** linha de material informada na solicitação, com descrição e quantidade declarada.
  - **ItemRecebimento:** registro da apresentação e conferência daquela linha, incluindo quantidade efetivamente apresentada.
  - **Unidade física:** peça individual existente no mundo físico; só exige cadastro individual quando a rastreabilidade ou o procedimento exigir.
  - **ObjetoCustodia:** unidade lógica de guarda/rastreabilidade, representando uma peça individual ou um agrupamento homogêneo autorizado.
  - **AmostraOperacional:** registro LIMS criado após aceite para controlar o trabalho laboratorial e seus resultados.
  - **Corpo de prova:** unidade/porção selecionada ou preparada para ensaio específico, conforme método/plano de ensaio.
- **Cardinalidades adotadas:**
  1. Um ItemDeclarado corresponde a exatamente um ItemRecebimento no recebimento principal.
  2. Um ItemRecebimento pode originar zero ou vários ObjetosCustodia; zero quando o item não foi apresentado.
  3. Um ObjetoCustodia pode originar no máximo uma AmostraOperacional.
  4. No fluxo ordinário de material aceito que será ensaiado, cada ObjetoCustodia aceito origina exatamente uma AmostraOperacional.
  5. Uma AmostraOperacional pode possuir vários ensaios e vários corpos de prova.
  6. Não haverá associação N:M entre ObjetoCustodia e DeviceSample no desenho-base.
- **Regra de agrupamento:** unidades homogêneas podem constituir um único ObjetoCustodia quando forem avaliadas como conjunto e a decisão/resultado laboratorial for coletiva. O agrupamento deve preservar quantidade, unidade de medida, lote, identificadores disponíveis, critério técnico e autoria.
- **Regra de individualização:** quando houver resultado, decisão, identidade ou destinação independente por unidade, as unidades devem ser representadas por ObjetosCustodia distintos antes da criação das amostras. A existência de número de série deve ser preservada, mas não implica automaticamente relatório individual se o procedimento aprovar avaliação coletiva.
- **UnidadeFisica:** não será criada como tabela obrigatória na primeira versão. Poderá ser introduzida de forma aditiva se surgir requisito recorrente e demonstrado de rastreabilidade individual de unidades internas de agrupamentos.
- **Fracionamento:** se um objeto precisar ser dividido após a chegada, a operação deverá ser formal, auditável e quantitativamente reconciliada, preservando o objeto de origem e registrando objetos-filhos. Não se admite alteração silenciosa de quantidade ou identidade.
- **Exemplos orientadores:**
  1. Dez agulhas do mesmo lote avaliadas como conjunto: um ObjetoCustodia agrupado e uma amostra operacional, se o procedimento permitir.
  2. Dez agulhas com resultados/decisões individuais: dez ObjetosCustodia e, após aceite, dez amostras.
  3. Três seringas serializadas com decisões independentes: três ObjetosCustodia e três amostras; se a avaliação for coletiva, preservar as identidades dentro de um agrupamento autorizado.
  4. Um equipo submetido a vários ensaios: uma amostra, com vários ensaios e corpos de prova.
  5. Cateter avaliado por segmentos: uma amostra para o dispositivo; segmentos são corpos de prova, salvo se houver decisão/destino independente.
  6. Dez unidades declaradas e cinco apresentadas: registrar quantidade declarada 10, apresentada 5; somente o material apresentado pode gerar objetos de custódia e amostras.
  7. Embalagem coletiva: um objeto agrupado enquanto a embalagem constituir unidade de guarda, com individualização posterior auditável se necessária.
- **Restrições:** não usar fabricante+lote como chave universal de unidade; não exigir número de série para todos os materiais; não equiparar corpo de prova a amostra operacional; não criar amostra para material não apresentado, pendente ou recusado.
- **Responsáveis:** responsável técnico/laboratorial e responsável funcional.
- **Próximo passo:** aplicar estas regras ao desenho relacional e validar sua compatibilidade com procedimentos de ensaio e emissão de laudos. A aprovação desta diretriz não autoriza migrações ou implementação.

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
| DEC04–DEC05 | Usuário responsável pelo direcionamento do projeto (aprovação da diretriz de desenho) | Aprovação registrada nesta conversa; recomendações REC-LIMS-DEC-001 | 2026-11-09 | Aprovadas para orientar o desenho; formalização institucional pendente |\n| DEC01–DEC03, DEC06–DEC12 | A definir conforme governança institucional | A registrar | — | Pendente de aprovação formal |

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
| 1.0 | 2026-11-09 | Primeira consolidação das decisões DEC01–DEC12 e regras funcionais previamente acordadas. |
| 1.1 | 2026-11-09 | Inclusão de recomendações técnicas para DEC04, DEC05, DEC07 e DEC08; aprovação institucional permanece pendente. |\n| 1.2 | 2026-11-09 | Registro da aprovação do usuário para orientar o desenho em DEC04/DEC05; definição de CustodyObject–DeviceSample como 1:0..1; remoção de seções duplicadas; formalização institucional e autorização de implementação permanecem pendentes. |
