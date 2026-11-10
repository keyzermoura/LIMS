# M0.3 — Modelo Lógico Revisado do Domínio SEFI

**Identificador:** MOD-LOG-SEFI-003  
**Versão:** 0.1  
**Data:** 2026-11-10  
**Repositório:** `keyzermoura/LIMS`  
**Branch de referência:** `main`  
**Base examinada:** HEAD `4cbcabc91da82f0239a1b3d5a87b9765e8b0ad3f`  
**Natureza:** modelo lógico conceitual revisado; não é modelo físico, contrato definitivo de API ou autorização de implementação.  
**Situação:** proposta documental para revisão; Gate G0 NÃO APROVADO; implementação NÃO AUTORIZADA.

---

## 1. Objetivo

Definir uma representação lógica, coerente e rastreável do domínio de solicitação, chegada física, recebimento, conferência, pendências, decisão, custódia, aceite e criação da AmostraOperacional no SEFI. O modelo responde às divergências registradas na Matriz de Aderência v1.1 e na Matriz de Prontidão G0 v0.3, sem modificar código, banco, migrações, API, frontend, CI ou infraestrutura.

O M0.3 detalha:
- entidades e responsabilidades, distinguindo conceitos que não podem ser tratados como sinônimos;
- cardinalidades e regras de granularidade;
- estados independentes por entidade e transições conceituais;
- eventos de negócio e fatos de auditoria;
- invariantes que devem ser verdadeiros em qualquer estado válido;
- relações entre chegada, custódia pré-amostra e continuidade após o aceite;
- tratamento de chegadas complementares, retificações, evidências e legado;
- questões ainda dependentes de validação operacional, institucional ou arquitetural.

## 2. Fontes, precedência e limites

### 2.1 Fontes utilizadas

1. `docs/DECISOES_PREVALIDACAO_SEFI_D01_D20.md`, versão 1.7 — decisões D01–D20 ratificadas integralmente pelo responsável pela Validação Institucional em 2026-11-10.
2. `docs/MODELO_CONCEITUAL_DOMINIO_SOLICITACAO_RECEBIMENTO.md`, versão 0.7 — modelo M0.2 e consolidação de entidades/cardinalidades.
3. `docs/ESTADOS_E_TRANSICOES_SOLICITACAO_RECEBIMENTO.md`, versão 1.7 — estados, transições, regras de autorização, auditoria e critérios CA01–CA37 propostos.
4. `docs/MODELO_RELACIONAL_PRELIMINAR_LIMS.md`, versão 0.3 — proposta relacional preliminar, usada apenas como referência de compatibilidade, não como esquema aprovado.
5. `docs/CONTRATO_HISTORICO_UNIFICADO_E_ACEITE.md`, versão 0.1 — contrato conceitual de histórico e transação de aceite, ainda sujeito a revisão.
6. `docs/MATRIZ_ADERENCIA_DOMINIO_SEFI.md`, versão 1.1, e `docs/MATRIZ_PRONTIDAO_GATE_G0.md`, versão 0.3 — diagnóstico da implementação existente e parecer da auditoria cruzada.

### 2.2 Hierarquia de interpretação

- As decisões D01–D20 e as cardinalidades explicitamente aprovadas no M0.2 prevalecem sobre alternativas preliminares.
- O M0.3 não revoga nem reinterpreta silenciosamente decisões ratificadas.
- Quando este documento propõe entidade ou refinamento novo para materializar uma decisão já ratificada, a proposta é identificada como refinamento lógico e deve passar por revisão funcional antes de ser considerada baseline definitiva.
- Recomendações técnicas do modelo relacional e do contrato de API não são automaticamente regras de domínio.
- Em caso de conflito não resolvido, registrar a questão como pendência; não escolher uma solução física por conveniência.

### 2.3 O que este documento não faz

- Não define nomes finais de tabelas, colunas, enums SQL, índices, constraints ou migrations.
- Não define endpoints, payloads, telas, componentes ou arquitetura de armazenamento.
- Não aprova valores de prazos, critérios técnicos por categoria, protocolo SEFI, política de retenção ou modalidade jurídica de assinatura.
- Não presume que o schema atual represente o domínio SEFI.
- Não autoriza desenvolvimento, migração de dados ou alteração do sistema existente.

## 3. Diagnóstico que orienta a revisão

A auditoria cruzada confirmou uma fundação técnica relevante no sistema existente, mas identificou divergência semântica entre o fluxo implementado e o domínio SEFI aprovado. O sistema atual está centrado em `DeviceSample`, `ChainOfCustody`, ensaios e CAPA. O domínio SEFI exige uma cadeia anterior e independente à amostra operacional.

A lacuna central é a ausência de uma representação própria e completa da cadeia:

**Solicitação → ItemDeclarado → Recebimento → ItemRecebimento → ObjetoCustodia → Conferência/Decisão → Aceite → AmostraOperacional.**

Consequências que o M0.3 precisa evitar:
1. `DeviceSample` não pode ser usado como sinônimo de `ObjetoCustodia`.
2. `DeviceSample` não pode ser criado apenas para representar material que chegou fisicamente, mas ainda não foi aceito.
3. `ChainOfCustody` não substitui a entidade que representa o material sob custódia; ela registra eventos sobre esse material.
4. CAPA de ensaio não substitui Pendência de recebimento.
5. estado de ensaio não substitui decisão de aceite/recusa.
6. transferência de custódia não é sinônimo de mudança de localização.
7. perfil RBAC não é, isoladamente, designação de competência ou autoridade técnica.

## 4. Princípios estruturantes do M0.3

1. **Separação de ciclos:** solicitação, recebimento, conferência, decisão, custódia e amostra possuem ciclos próprios.
2. **Custódia desde a chegada:** a guarda começa quando o material é fisicamente recebido, antes do aceite e da amostra.
3. **Decisão na menor granularidade necessária:** quando objetos do mesmo item puderem ter destinos ou resultados diferentes, a decisão é por ObjetoCustodia.
4. **Quantidades não se confundem:** declarada, apresentada, representada sob custódia, aceita, recusada e não apresentada são dimensões distintas.
5. **Ausência não é recusa:** NAO_APRESENTADO não gera objeto, custódia, decisão técnica de recusa ou amostra.
6. **Histórico não se reescreve:** correção é novo ato relacionado ao original; não se apaga fato formalizado.
7. **Tempo do fato e tempo do registro:** instante efetivo e instante de gravação são atributos distintos.
8. **Aceite é uma barreira formal:** somente objeto elegível e aceito pode originar AmostraOperacional.
9. **Amostra não encerra custódia:** a cadeia continua vinculada ao ObjetoCustodia após o aceite.
10. **Estado agregado é derivado:** o estado do recebimento/solicitação resume os estados filhos, sem ocultá-los.
11. **Sem inferência de legado:** associação histórica só ocorre quando houver evidência confiável.
12. **Autorização é contextual:** usuário, perfil, competência, designação, independência e assinatura são controles distintos.

## 5. Modelo lógico — entidades e responsabilidades

### 5.1 Núcleo da solicitação

| Entidade | Responsabilidade | Conteúdo lógico mínimo | Observações |
|---|---|---|---|
| **Solicitante** | Identificar pessoa, órgão ou instituição em nome de quem a demanda é registrada. | Identidade cadastral, organização/unidade, contatos e situação cadastral. | Não implica conta externa na primeira entrega. |
| **Solicitação** | Representar a demanda administrativa e seu contexto. | Identificador próprio, solicitante, origem, finalidade, tipo, prioridade, autor do cadastro/submissão, datas e estado. | Pode conter vários itens declarados. |
| **ItemDeclarado** | Representar cada linha de material/produto solicitada. | Identificador, descrição declarada, fabricante/modelo quando informado, lote/série quando aplicável, quantidade e unidade declaradas, categoria e observações. | Não é ainda material recebido nem amostra. |

### 5.2 Núcleo da chegada e recebimento

| Entidade | Responsabilidade | Conteúdo lógico mínimo | Observações |
|---|---|---|---|
| **Recebimento** | Registrar a chegada física principal vinculada à solicitação. | Identificador próprio, solicitação, instante efetivo da chegada, recebedor físico, autor do registro, local inicial, volumes, condição externa, documentos apresentados e observações. | No máximo um recebimento principal por solicitação, conforme M0.2. |
| **ItemRecebimento** | Representar a situação de apresentação e conferência de cada ItemDeclarado. | Item declarado de origem, situação de apresentação, quantidades observadas, unidade, estado de conferência e situação agregada de decisão. | Deve existir para todo ItemDeclarado do recebimento, inclusive não apresentado. |
| **EventoApresentacao** *(refinamento proposto)* | Registrar uma ocorrência de apresentação física de quantidade de um item em uma chegada principal ou complementar. | ItemRecebimento, tipo de chegada, instante efetivo, quantidade apresentada, unidade, autor do registro, recebedor físico, observações e evidências. | Proposto para preservar D19 e distinguir múltiplas apresentações sem criar um segundo recebimento principal. Requer validação funcional. |

### 5.3 Núcleo de custódia

| Entidade | Responsabilidade | Conteúdo lógico mínimo | Observações |
|---|---|---|---|
| **ObjetoCustodia** | Representar material efetivamente apresentado e mantido sob custódia, individualmente ou em agrupamento homogêneo justificado. | Identificador próprio, ItemRecebimento de origem, apresentação de origem, descrição/identificação observada, quantidade/unidade representada, justificativa de agrupamento, condição inicial e situação decisória. | Entidade canônica do material sob custódia. Pode haver vários por ItemRecebimento. |
| **EventoCustodia** | Registrar fatos de início, transferência, mudança de localização, devolução, destinação, encerramento e correção relacionados ao objeto. | ObjetoCustodia, tipo, instante efetivo, instante de registro, atores, origem/destino, localizações, motivo, justificativa e evidências. | Nome lógico do evento; não implica tabela física adicional à cadeia existente. |
| **Localizacao** *(catálogo conceitual)* | Identificar locais controlados de guarda e movimentação. | Código, descrição, unidade/setor, tipo e situação. | Inventário e códigos dependem de definição institucional. |

### 5.4 Núcleo de conferência e decisão

| Entidade | Responsabilidade | Conteúdo lógico mínimo | Observações |
|---|---|---|---|
| **ChecklistModelo** | Identificar o checklist aplicável a categoria/tipo de material. | Código, categoria, finalidade, situação e governança. | Pode possuir versões sucessivas. |
| **VersaoChecklist** | Congelar o conjunto de critérios vigente aplicado a uma conferência. | Número/identificador de versão, vigência, estado de publicação, aprovadores e data. | Conferência formalizada mantém a versão utilizada. |
| **CriterioChecklist** | Definir requisito de conferência e sua classe. | Texto, classe E/S/I, obrigatoriedade, aplicabilidade, evidência esperada e justificativa requerida. | Critérios técnicos específicos ainda dependem de aprovação por categoria. |
| **RespostaChecklist** | Registrar resultado de um critério aplicado a um item/objeto. | Critério/versão, alvo, resultado, avaliador, instante, justificativa e evidências. | Resposta formalizada não é sobrescrita; correção é nova avaliação/retificação. |
| **Pendencia** | Controlar condição saneável ou providência requerida. | Alvo, origem, classificação, descrição, responsável, comunicação, prazo, prorrogações, evidências, reavaliação e estado. | Pode ser vinculada ao ItemRecebimento ou ObjetoCustodia conforme alcance. |
| **DecisaoRecebimento** | Registrar ato formal de aceite, pendência decisória ou recusa. | Alvo decisório, resultado, fundamento, autor, instante, evidências, checklist considerado e referência a decisão anterior quando houver. | Preferencialmente por ObjetoCustodia se os desfechos puderem divergir. |
| **ValidacaoCoordenacao** | Registrar revisão independente quando exigida. | Decisão submetida, validador, resultado, justificativa, instante e assinatura quando exigida. | Autor da decisão não pode validar a própria decisão nos casos obrigatórios. |

### 5.5 Núcleo de amostra e ensaio

| Entidade | Responsabilidade | Conteúdo lógico mínimo | Observações |
|---|---|---|---|
| **AmostraOperacional** | Representar o material formalmente admitido no ciclo laboratorial. | Identificador próprio, ObjetoCustodia de origem, dados laboratoriais necessários, instante/autor da criação e vínculo com recebimento original. | Cada ObjetoCustodia pode originar no máximo uma amostra. |
| **Ensaio** | Representar atividade analítica vinculada à amostra. | Identificador, amostra, tipo/método, estado e resultados associados. | Reutiliza o conceito existente de LabTest, sujeito à compatibilização técnica. |

### 5.6 Evidências, retificação e referências

| Entidade | Responsabilidade | Conteúdo lógico mínimo | Observações |
|---|---|---|---|
| **Evidencia** | Identificar documento, imagem ou arquivo que sustenta um fato, avaliação ou decisão. | Tipo, nome original, autor, instante, descrição, hash, versão, localização lógica, classificação e retenção. | O binário pode residir fora do banco relacional; original formalizado deve ser preservado. |
| **VinculoEvidencia** *(associação lógica)* | Relacionar uma evidência a uma ou mais entidades/ocorrências autorizadas. | Evidência, alvo, finalidade, autor e instante do vínculo. | Não pressupõe associação polimórfica irrestrita no banco. A estratégia física depende da arquitetura. |
| **Retificacao** | Registrar correção excepcional de dado/decisão formalizada. | Alvo, valor/estado original, valor corrigido, motivo, evidência, autor, autorização, impacto e instante. | Novo ato; não altera nem apaga o original. |
| **ReferenciaExterna** | Relacionar protocolo ou identificador de outro sistema. | Sistema de origem, tipo, valor, alvo, data de associação e evidência. | Não substitui identificadores internos. |

### 5.7 Identidade, competência, assinatura e auditoria — conceitos transversais

- **UsuarioInterno:** ator individual autenticado; pode acumular funções se autorizado.
- **Perfil/Permissao:** define operações permitidas; não concede automaticamente competência técnica ou autoridade institucional.
- **DesignacaoCompetencia:** referência a ato/matriz institucional que habilita usuário para atividade, categoria, período e alçada. A entidade/cadastro lógico é proposto como referência de governança; designações nominais permanecem pendentes.
- **AssinaturaEletronica:** evidência de autoria, intenção e vínculo ao conteúdo/ato quando a política exigir. Não substitui validação independente.
- **EventoAuditoria:** registra operação, ator, instante, alvo, ação, antes/depois, justificativa e correlação. A trilha é transversal e não substitui eventos de domínio.

## 6. Cardinalidades e regras de relacionamento

| Origem | Cardinalidade | Destino | Regra lógica |
|---|---:|---|---|
| Solicitante | 1:N | Solicitação | Um solicitante pode originar várias solicitações. |
| Solicitação | 1:N | ItemDeclarado | Uma solicitação submetida contém um ou mais itens declarados. |
| Solicitação | 1:0..1 | Recebimento principal | No máximo um recebimento principal por solicitação. |
| Recebimento | 1:N | ItemRecebimento | Deve representar todas as linhas declaradas, inclusive as não apresentadas. |
| ItemDeclarado | 1:1 | ItemRecebimento | Cada item declarado possui exatamente uma representação no recebimento principal quando este é criado. |
| ItemRecebimento | 1:0..N | EventoApresentacao | Pode haver uma ou mais apresentações ao longo do tratamento, conforme D19 e autorização de complemento. |
| EventoApresentacao | 1:0..N | ObjetoCustodia | Uma apresentação pode gerar vários objetos se a granularidade/decisão exigir; pode não gerar nenhum se não houver material sob custódia. |
| ItemRecebimento | 1:0..N | ObjetoCustodia | Cardinalidade M0.2 preservada; somente material apresentado e efetivamente sob guarda gera objeto. |
| ObjetoCustodia | 1:N | EventoCustodia | Todo objeto sob custódia possui evento inicial; eventos subsequentes preservam a cadeia. |
| Localizacao | 1:N | EventoCustodia | Um local pode participar de muitos eventos como origem ou destino. |
| ItemRecebimento/ObjetoCustodia | 1:0..N | RespostaChecklist | Respostas vinculam-se ao menor nível de avaliação tecnicamente adequado. |
| ChecklistModelo | 1:N | VersaoChecklist | Um modelo possui versões controladas. |
| VersaoChecklist | 1:N | CriterioChecklist | Uma versão publicada congela seus critérios. |
| CriterioChecklist | 1:N | RespostaChecklist | Um critério versionado pode ser aplicado em diversas conferências. |
| ItemRecebimento/ObjetoCustodia | 1:0..N | Pendencia | Pendências podem existir em qualquer nível onde a providência seja independente. |
| ItemRecebimento/ObjetoCustodia | 1:0..N | DecisaoRecebimento | A decisão ocorre no menor nível em que os desfechos podem divergir. |
| DecisaoRecebimento | 1:0..N | ValidacaoCoordenacao | Zero quando não exigida; uma ou mais avaliações históricas quando exigidas/repetidas. |
| ObjetoCustodia | 1:0..1 | AmostraOperacional | No máximo uma amostra por objeto; somente após aceite e validações obrigatórias. |
| AmostraOperacional | 1:N | Ensaio | Uma amostra pode originar vários ensaios. |
| Entidade/ocorrência elegível | 1:0..N | VinculoEvidencia | Evidência pode sustentar vários alvos autorizados, sem duplicar o arquivo original. |
| Entidade formalizada | 1:0..N | Retificacao | Retificações sucessivas preservam a cadeia original e as correções. |
| Entidade de negócio | 1:0..N | ReferenciaExterna | Identificadores externos são auxiliares e tipados. |

**Regra de cardinalidade importante:** a relação ObjetoCustodia 1:0..1 AmostraOperacional é obrigatória no modelo lógico. A direção não deve ser invertida para permitir que uma amostra exista sem objeto de origem no novo fluxo. Dados legados podem permanecer sem vínculo quando não houver evidência suficiente.

## 7. Quantidades e granularidade

### 7.1 Dimensões distintas

| Quantidade | Entidade de referência | Significado |
|---|---|---|
| Declarada | ItemDeclarado | Quantidade informada na solicitação. |
| Apresentada | EventoApresentacao / ItemRecebimento | Quantidade efetivamente apresentada em cada chegada; o agregado do item é derivado das apresentações válidas. |
| Sob custódia | ObjetoCustodia | Quantidade representada por cada objeto individual ou agrupado. |
| Aceita | DecisaoRecebimento | Quantidade/escopo efetivamente aceito, derivada dos objetos aceitos ou decisão única no item. |
| Recusada | DecisaoRecebimento | Quantidade/escopo efetivamente recusado; não equivale a não apresentado. |
| Não apresentada | ItemRecebimento | Quantidade declarada ainda não apresentada na ocasião registrada, conforme conciliação. |

Não calcular ou sobrescrever uma dimensão usando outra sem regra de unidade e conversão aprovada. Toda divergência deve ser explicável por reconciliação entre quantidade declarada, apresentações, objetos e desfechos.

### 7.2 ObjetoCustodia individual ou agrupado

ObjetoCustodia pode representar:
- uma unidade individual, quando serialização/rastreabilidade individual for necessária;
- um agrupamento homogêneo, quando os itens forem equivalentes para guarda, avaliação, decisão e destinação.

Um agrupamento deve manter descrição do critério de homogeneidade, quantidade/unidade representada e justificativa. Não agrupar materiais cujos resultados, decisão, rastreabilidade ou destino possam divergir. Se a divergência surgir depois, o processo deverá registrar fracionamento controlado, preservando o vínculo com o objeto de origem e a reconciliação de quantidades; a regra detalhada de fracionamento por categoria ainda exige validação técnica.

Não criar entidade UnidadeFisica independente na primeira versão do domínio. A granularidade individual é representada por ObjetoCustodia quando necessária, conforme consolidação M0.2.

### 7.3 Reconciliação

Para cada ItemRecebimento, o sistema deve permitir demonstrar:
- quantidade declarada;
- total apresentado acumulado, sem duplicar reenvios idempotentes;
- total representado pelos ObjetosCustodia ativos e históricos;
- total aceito;
- total recusado;
- total não apresentado;
- diferenças, perdas, sobras ou divergências justificadas.

As regras de equivalência de unidade, precisão decimal, arredondamento e categorias fracionáveis dependem de procedimento técnico/institucional. Não se presumem neste modelo.

## 8. Chegada principal e chegada complementar

### 8.1 Recebimento principal

A Solicitação pode possuir no máximo um Recebimento principal. No ato da chegada, a Recepção registra o fato físico mesmo que existam divergências ou documentos incompletos. A conferência e a decisão são eventos posteriores e distintos.

O recebimento principal cria a representação ItemRecebimento para todas as linhas declaradas. Cada item é marcado como APRESENTADO ou NAO_APRESENTADO no contexto daquela chegada, sem transformar ausência em recusa.

### 8.2 Complementação de chegada — proposta de materialização de D19

Para não violar a cardinalidade aprovada de um único recebimento principal, o M0.3 propõe representar a entrega posterior como **EventoApresentacao complementar**, vinculado ao ItemRecebimento e ao Recebimento original, e não como um segundo Recebimento principal.

Regras:
1. A apresentação complementar é um novo fato, com instante efetivo, instante de registro, recebedor, autor, quantidade e evidências próprios.
2. Ela não altera retroativamente a data/hora ou o conteúdo do evento de chegada anterior.
3. Deve haver reavaliação/conferência do material que chegou posteriormente.
4. Só material efetivamente apresentado pode gerar ObjetoCustodia e evento inicial de custódia.
5. Se a Solicitação/Recebimento estiver concluído, a chegada posterior exige reabertura autorizada ou nova Solicitação vinculada, conforme regra institucional D19; o modelo não escolhe automaticamente entre essas alternativas.
6. A criação de EventoApresentacao complementar e sua elegibilidade dependem da validação funcional da proposta, especialmente para cenários SIM e CA correspondentes.

## 9. Estados por entidade

Os estados abaixo são dimensões independentes. Não se deve armazenar um único status global que tente representar todo o processo. Estados agregados de Recebimento e Solicitação são projeções derivadas dos estados filhos.

### 9.1 Solicitação

| Estado | Significado |
|---|---|
| RASCUNHO | Cadastro iniciado e ainda não submetido. |
| SUBMETIDA | Demanda formalizada, apta a aguardar chegada. |
| RECEBIMENTO_REGISTRADO | Recebimento principal registrado. |
| EM_TRATAMENTO | Existem itens/objetos em conferência, pendência ou validação. |
| CONCLUIDA | Recebimento concluído administrativamente, com todos os itens em desfecho válido. |
| CANCELADA | Cancelamento autorizado, justificado e auditável. |

Cancelamento não apaga chegada nem encerra custódia automaticamente.

### 9.2 Recebimento

| Estado | Significado |
|---|---|
| REGISTRADO | Chegada principal registrada. |
| EM_CONFERENCIA | Um ou mais itens/objetos em conferência. |
| AGUARDANDO_REGULARIZACAO | Existe pendência aberta que impede decisão/conclusão. |
| AGUARDANDO_COORDENACAO | Existe ato que requer validação independente. |
| PARCIALMENTE_DECIDIDO | Parte dos itens/objetos possui desfecho e parte permanece em tratamento. |
| CONCLUIDO | Todos os itens possuem desfecho administrativo válido, sem providência obrigatória aberta e sem objeto sem destino. |
| CANCELADO | Cancelamento excepcional autorizado; histórico e custódia permanecem. |

### 9.3 ItemRecebimento e apresentação

| Dimensão | Valores | Regra |
|---|---|---|
| Apresentação | AGUARDANDO_CHEGADA, APRESENTADO, NAO_APRESENTADO, APRESENTACAO_PARCIAL | Estado resumido das apresentações vinculadas; ausência não é recusa. |
| Conferência | NAO_INICIADA, EM_ANDAMENTO, CONCLUIDA | Conferência só inicia para material apresentado e sob custódia. |
| Consolidação do item | NAO_DECIDIDO, PARCIALMENTE_DECIDIDO, ACEITO, PENDENTE, RECUSADO, MISTO | Derivado das decisões dos objetos e do que foi apresentado. |

APRESENTACAO_PARCIAL só é usada quando a quantidade apresentada é menor que a declarada e a diferença permanece identificada. A semântica de apresentação parcial e não apresentada deve ser validada nos cenários operacionais; não deve apagar o histórico de apresentações.

### 9.4 EventoApresentacao

| Estado/condição | Significado |
|---|---|
| REGISTRADO | Fato de apresentação registrado e auditável. |
| RETIFICADO | Registro corrigido por novo ato, preservando a ocorrência original. |

EventoApresentacao é histórico de fatos; não deve ser tratado como workflow editável. Uma correção é Retificacao relacionada ao evento.

### 9.5 ObjetoCustodia

| Estado | Significado |
|---|---|
| SOB_CUSTODIA | Material fisicamente recebido e sob responsabilidade identificada. |
| EM_CONFERENCIA | Objeto em avaliação técnica/administrativa. |
| PENDENTE | Existe providência aberta que impede decisão final ou aceite. |
| AGUARDANDO_VALIDACAO | Decisão depende de validação de coordenação. |
| ACEITO | Decisão formal favorável concluída. |
| RECUSADO | Decisão formal desfavorável concluída; material permanece sob custódia até destino efetivo. |
| EM_DEVOLUCAO | Devolução autorizada e em preparação/execução. |
| EM_DESTINACAO | Destinação alternativa autorizada em execução. |
| ENCERRADO | Custódia encerrada após entrega/devolução/destinação efetiva comprovada. |

ACEITO não significa custódia encerrada. RECUSADO não significa devolvido. Estados de custódia e de decisão devem ser separados se a implementação precisar representar simultaneamente, por exemplo, decisão RECUSADO e custódia SOB_CUSTODIA.

### 9.6 Conferência e RespostaChecklist

| Dimensão | Valores |
|---|---|
| Conferência | NAO_INICIADA, EM_ANDAMENTO, CONCLUIDA |
| Resultado de critério | CONFORME, NAO_CONFORME, NAO_APLICAVEL |
| Classe do critério | E (eliminatório), S (saneável), I (informativo) |

A classificação E/S/I pertence à versão publicada do checklist, não pode ser escolhida livremente pelo operador durante a resposta. NAO_APLICAVEL exige justificativa quando assim definido no critério.

### 9.7 Pendência

| Estado | Significado |
|---|---|
| PENDENTE | Providência formalmente requerida e comunicável. |
| EM_REGULARIZACAO | Providência em atendimento. |
| AGUARDANDO_REAVALIACAO | Evidência/resposta recebida; aguarda avaliação. |
| REGULARIZADA | Reavaliação favorável registrada por responsável habilitado. |
| PRAZO_VENCIDO | Condição temporal de atraso; não encerra a pendência. |
| NAO_REGULARIZAVEL | Decisão formal de que a condição não pode ser sanada no fluxo; não equivale automaticamente a recusa. |
| CANCELADA | Cancelamento justificado por erro/perda do objeto, autorizado e auditado. |

PRAZO_VENCIDO é indicador/condição temporal, não estado terminal. A contagem começa após comunicação formal comprovável. A pendência só é regularizada após reavaliação favorável.

### 9.8 DecisaoRecebimento

| Estado/resultado | Significado |
|---|---|
| ACEITE_PROPOSTO | Resultado favorável registrado, aguardando validações obrigatórias quando houver. |
| ACEITE_VALIDADO | Aceite formal concluído após controles exigidos. |
| PENDENCIA | Decisão de encaminhar para regularização, quando o procedimento assim definir. |
| RECUSA_PROPOSTA | Resultado desfavorável submetido à validação quando exigida. |
| RECUSADA | Recusa formal concluída. |
| SUBSTITUIDA | Decisão superada por nova decisão autorizada; histórico original permanece. |

Decisão e estado de custódia são dimensões diferentes. Uma decisão recusada não encerra guarda física.

### 9.9 ValidacaoCoordenacao

| Estado/resultado | Significado |
|---|---|
| NAO_EXIGIDA | Regra aplicável não exige revisão. |
| AGUARDANDO | Encaminhada para revisão independente. |
| APROVADA | Validação favorável registrada. |
| DEVOLVIDA | Devolvida para complementação/correção. |
| REJEITADA | Validação desfavorável, com fundamento. |

Validador deve ser diferente do autor/executor nos casos em que independência for obrigatória. Administrador não recebe autoridade técnica por ser administrador.

### 9.10 AmostraOperacional e Ensaio

| Entidade | Estados conceituais |
|---|---|
| AmostraOperacional | CRIADA, ATIVA, EM_ENSAIO, ENCERRADA, CANCELADA_COM_HISTORICO |
| Ensaio | Estados e ciclo existentes do domínio de ensaios, a compatibilizar sem redefinir neste documento. |

Os estados de AmostraOperacional são uma proposta lógica; devem ser harmonizados com o workflow atual de `DeviceSample` antes de qualquer detalhamento físico.

### 9.11 Custódia

A custódia corrente deve ser projetada a partir dos eventos válidos e confirmados, distinguindo:
- situação de guarda: SOB_CUSTODIA ou ENCERRADA;
- custodiante atual;
- localização atual;
- transferência pendente de confirmação;
- destino final e evidência de encerramento.

Não fundir localização e custodiante em um único atributo ou estado.

## 10. Transições essenciais e pré-condições

| Entidade | Transição | Pré-condições / controles |
|---|---|---|
| Solicitação | RASCUNHO → SUBMETIDA | Solicitante identificado; pelo menos um ItemDeclarado válido; campos obrigatórios; autor autorizado. |
| Solicitação | SUBMETIDA → RECEBIMENTO_REGISTRADO | Criação transacional do recebimento principal e representação de todos os itens declarados. |
| Recebimento | REGISTRADO → EM_CONFERENCIA | Ao menos um item apresentado; checklist aplicável e versão vigente fixada. |
| ItemRecebimento | AGUARDANDO_CHEGADA → APRESENTADO | Chegada física observada; quantidade/unidade registradas; recebedor e instante do fato preservados. |
| ItemRecebimento | AGUARDANDO_CHEGADA → NAO_APRESENTADO | Ausência constatada; quantidade apresentada zero para aquela ocorrência; não criar objeto. |
| ObjetoCustodia | inexistente → SOB_CUSTODIA | Material apresentado e individualização/agrupamento justificado; custodiante e localização inicial definidos; evento inicial de custódia registrado. |
| Conferência | NAO_INICIADA → EM_ANDAMENTO | Objeto sob custódia; checklist vigente; conferente autorizado. |
| Conferência | EM_ANDAMENTO → CONCLUIDA | Critérios obrigatórios respondidos; evidências/justificativas exigidas presentes. |
| Pendência | inexistente → PENDENTE | Critério/ocorrência identificada; descrição, responsável, comunicação e prazo conforme regra institucional. |
| Pendência | AGUARDANDO_REAVALIACAO → REGULARIZADA | Reavaliação favorável por ator habilitado; evidência vinculada. |
| Decisão | ACEITE_PROPOSTO → ACEITE_VALIDADO | Sem bloqueio E; pendências impeditivas resolvidas; validação independente quando exigida; assinatura se exigida. |
| ObjetoCustodia | estado elegível → ACEITO | Decisão formal final favorável; registro histórico. |
| ObjetoCustodia | estado elegível → RECUSADO | Motivo, critério/evidência, autoridade e validação quando exigida; material continua sob custódia. |
| ObjetoCustodia | RECUSADO → EM_DEVOLUCAO/EM_DESTINACAO | Destino autorizado, representante/responsável e procedimento definido. |
| ObjetoCustodia | EM_DEVOLUCAO/EM_DESTINACAO → ENCERRADO | Entrega/destinação efetiva, quantidade/condição, recebedor/representante, data/hora e comprovante. |
| Custódia | transferência proposta → transferência confirmada | Entregador e recebedor identificados; confirmação do destinatário; responsabilidade só muda na confirmação. |
| Custódia | mudança de localização | Evento próprio com origem, destino, responsável, instante e justificativa; custodiante não muda. |
| ObjetoCustodia | ACEITO → AmostraOperacional criada | Transação atômica/idempotente; objeto sem amostra anterior; aceite e validações válidos; vínculo único. |
| Retificação | dado/ato formalizado → retificado | Motivo, valor original/novo, evidência, autorização, impacto e assinatura quando exigida; novo evento sem apagar o original. |

Transições não listadas não são presumidas permitidas. Reabertura, reconsideração de recusa, exceções e correções devem ter autorização e regras explícitas.

## 11. Eventos de domínio

Os eventos abaixo descrevem fatos relevantes do processo. Cada evento deve manter identificador, tipo, alvo, instante efetivo (`occurred_at`), instante de registro (`recorded_at`), autor do registro, ator físico/decisor quando diferente, motivo, evidências e correlação/idempotência conforme aplicável.

| Evento | Alvo principal | Quando ocorre | Efeito lógico |
|---|---|---|---|
| SOLICITACAO_CRIADA | Solicitação | Cadastro inicial. | Cria a demanda em RASCUNHO. |
| SOLICITACAO_SUBMETIDA | Solicitação | Formalização. | Torna a demanda apta a receber. |
| SOLICITACAO_CANCELADA | Solicitação | Cancelamento autorizado. | Marca cancelamento sem apagar fatos anteriores. |
| CHEGADA_REGISTRADA | Recebimento | Chegada física principal. | Inicia o recebimento e a custódia do material apresentado. |
| ITEM_APRESENTADO | ItemRecebimento / EventoApresentacao | Material fisicamente apresentado. | Registra quantidade/unidade observadas. |
| ITEM_NAO_APRESENTADO | ItemRecebimento | Ausência constatada na chegada. | Mantém a linha declarada sem gerar custódia ou amostra. |
| APRESENTACAO_COMPLEMENTAR_REGISTRADA | ItemRecebimento / EventoApresentacao | Entrega posterior autorizada. | Registra novo fato sem retroagir a chegada original. |
| OBJETO_CUSTODIA_CRIADO | ObjetoCustodia | Material passa à guarda. | Cria unidade individual/agrupada sob custódia. |
| CUSTODIA_INICIADA | ObjetoCustodia | Entrada física sob responsabilidade. | Define custodiante/local inicial e início histórico. |
| CONFERENCIA_INICIADA | Item/Objeto | Início da avaliação. | Fixa checklist e avaliador. |
| RESPOSTA_CHECKLIST_REGISTRADA | RespostaChecklist | Avaliação de critério. | Registra resultado imutável da avaliação. |
| CONFERENCIA_CONCLUIDA | Item/Objeto | Todos os critérios obrigatórios respondidos. | Habilita decisão, se não houver bloqueios. |
| PENDENCIA_ABERTA | Pendência | Condição a sanar identificada. | Inicia ciclo e prazo após comunicação formal. |
| PENDENCIA_COMUNICADA | Pendência | Comunicação comprovável. | Inicia contagem do prazo aplicável. |
| PENDENCIA_PRORROGADA | Pendência | Prorrogação autorizada. | Atualiza prazo sem apagar o anterior. |
| REGULARIZACAO_RECEBIDA | Pendência | Resposta/evidência recebida. | Encaminha para reavaliação; não encerra automaticamente. |
| PENDENCIA_REGULARIZADA | Pendência | Reavaliação favorável. | Remove bloqueio correspondente, preservando histórico. |
| PENDENCIA_NAO_REGULARIZAVEL | Pendência | Decisão formal competente. | Encaminha para decisão de aceite/recusa; não equivale a recusa. |
| DECISAO_ACEITE_REGISTRADA | Objeto/Item | Decisão favorável proposta/formalizada. | Registra resultado e fundamento. |
| DECISAO_RECUSA_REGISTRADA | Objeto/Item | Decisão desfavorável. | Mantém custódia até destinação efetiva. |
| VALIDACAO_COORDENACAO_REGISTRADA | Decisão | Revisão exigida. | Aprova, devolve ou rejeita conforme competência. |
| TRANSFERENCIA_SOLICITADA | ObjetoCustodia | Início da transferência. | Mantém responsabilidade no custodiante atual até confirmação. |
| TRANSFERENCIA_CONFIRMADA | ObjetoCustodia | Recebedor confirma. | Atualiza custodiante corrente. |
| LOCALIZACAO_ALTERADA | ObjetoCustodia | Mudança física sem troca de responsável. | Atualiza local corrente; custodiante permanece. |
| DEVOLUCAO_AUTORIZADA | ObjetoCustodia | Autorização de devolução. | Inicia processo de entrega. |
| DEVOLUCAO_REALIZADA | ObjetoCustodia | Entrega efetiva comprovada. | Registra destinatário, quantidade/condição e encerra custódia quando aplicável. |
| DESTINACAO_AUTORIZADA | ObjetoCustodia | Destino alternativo autorizado. | Inicia processo de destinação. |
| DESTINACAO_REALIZADA | ObjetoCustodia | Destinação efetiva comprovada. | Registra evidência e encerra custódia quando aplicável. |
| AMOSTRA_OPERACIONAL_CRIADA | AmostraOperacional | Aceite concluído. | Cria amostra vinculada ao objeto; não reinicia a custódia. |
| RETIFICACAO_REGISTRADA | Entidade/ato | Correção excepcional autorizada. | Preserva original e registra nova versão/efeito. |
| EVIDENCIA_VINCULADA | Evidencia/Vínculo | Anexo associado a fato/decisão. | Preserva metadados, integridade e autorização. |
| RECEBIMENTO_CONCLUIDO | Recebimento | Todos os itens com desfecho administrativo válido. | Fecha etapa administrativa, não necessariamente custódia de objetos recusados. |

Eventos de negócio e eventos técnicos de auditoria podem coexistir, mas não devem duplicar a mesma semântica. Evento de domínio expressa o fato; auditoria registra quem executou a operação e quais dados foram alterados.

## 12. Invariantes do domínio

Os invariantes são condições permanentes de validade do modelo. A implementação futura deverá protegê-los em regras de domínio, transações e, quando apropriado, constraints de persistência. Esta seção não especifica a técnica de enforcement.

| ID | Invariante | Consequência se violado |
|---|---|---|
| INV-01 | Solicitação submetida possui ao menos um ItemDeclarado. | Não submeter demanda vazia. |
| INV-02 | Uma Solicitação possui no máximo um Recebimento principal. | Impedir duplicidade por repetição/concorrência. |
| INV-03 | Todo ItemDeclarado possui exatamente um ItemRecebimento no recebimento principal criado. | Não omitir linhas declaradas, mesmo não apresentadas. |
| INV-04 | Item NAO_APRESENTADO não gera ObjetoCustodia, EventoCustodia ou AmostraOperacional. | Ausência não se converte em custódia/recusa/amostra. |
| INV-05 | Somente material efetivamente apresentado pode originar ObjetoCustodia. | Não criar objeto vazio ou presumido. |
| INV-06 | Todo ObjetoCustodia tem origem rastreável em ItemRecebimento e apresentação correspondente. | Impedir objeto órfão. |
| INV-07 | Quantidades declarada, apresentada, sob custódia, aceita, recusada e não apresentada permanecem distinguíveis e reconciliáveis. | Não perder divergências nem somar unidades incompatíveis. |
| INV-08 | Um ObjetoCustodia representa material homogêneo para guarda/decisão/destino, salvo fracionamento formal. | Não ocultar desfechos divergentes em agrupamento. |
| INV-09 | Todo objeto sob custódia possui evento inicial e custodiante/local inicial identificáveis. | Não existir material sem responsabilidade rastreável. |
| INV-10 | EventoCustodia aponta para exatamente um ObjetoCustodia no novo fluxo; evento legado continua vinculado à amostra legada conforme compatibilidade. | Evitar evento sem alvo ou com alvos conflitantes. |
| INV-11 | Transferência só muda custodiante após confirmação do recebedor. | Responsabilidade não migra por solicitação unilateral. |
| INV-12 | Mudança de localização não altera custodiante. | Separar local físico de responsabilidade. |
| INV-13 | Custódia só se encerra após devolução/entrega/destinação efetiva e comprovada. | Recusa ou autorização isolada não encerram guarda. |
| INV-14 | Checklist aplicado é versionado e preservado; resposta concluída não é sobrescrita. | Manter critério efetivamente utilizado na decisão. |
| INV-15 | Critério E não pode ser dispensado por decisão discricionária; critério S exige saneamento e reavaliação; I não cria bloqueio técnico por si só. | Respeitar classes E/S/I ratificadas. |
| INV-16 | Pendência vencida permanece aberta até regularização, decisão formal não regularizável ou cancelamento autorizado. | PRAZO_VENCIDO não gera recusa automática. |
| INV-17 | Evidência recebida não regulariza pendência sem reavaliação favorável. | Evitar liberação automática por mera juntada. |
| INV-18 | Decisão ocorre na menor granularidade em que os desfechos podem divergir. | Evitar decisão agregada que oculte objeto recusado/aceito. |
| INV-19 | Validação independente, quando exigida, é realizada por ator diferente do autor/executor. | Bloquear autoaprovação. |
| INV-20 | Administrador não possui autoridade técnica implícita nem pode alterar critérios técnicos publicados sem governança. | Separar administração de decisão técnica. |
| INV-21 | AmostraOperacional só existe no novo fluxo para ObjetoCustodia com aceite formal válido e todos os bloqueios impeditivos resolvidos. | Preservar D20. |
| INV-22 | Cada ObjetoCustodia origina no máximo uma AmostraOperacional. | Impedir duplicação por reenvio ou concorrência. |
| INV-23 | Criação da amostra e registro do aceite definido como indivisível são atômicos e idempotentes. | Evitar aceite sem amostra ou amostra sem aceite. |
| INV-24 | Criação da amostra não reinicia nem duplica evento de chegada/custódia. | Preservar linha histórica contínua. |
| INV-25 | Instante efetivo do fato e instante de registro são preservados separadamente. | Não simular retroatividade. |
| INV-26 | Retificação preserva valor/evento original, motivo, autor, autorização, evidência e impacto. | Não apagar trilha nem reescrever passado. |
| INV-27 | Identificadores de Solicitação, Recebimento, ObjetoCustodia e AmostraOperacional são distintos, únicos e não reutilizados. | Não confundir identidades de processos e materiais. |
| INV-28 | Protocolo SEFI, accession laboratorial e QR Code têm semânticas distintas até decisão formal sobre o padrão. | Não criar identificadores equivalentes concorrentes. |
| INV-29 | Referências legadas só são vinculadas quando houver evidência confiável. | Não inventar relacionamento histórico. |
| INV-30 | Cada operação crítica é autorizada no servidor conforme usuário, permissão, competência, escopo e independência aplicáveis. | Não confiar apenas na interface ou no perfil genérico. |
| INV-31 | Toda transição formal e evento crítico possui ator, timestamp, alvo e justificativa/evidência conforme sua natureza. | Reconstruir quem fez o quê e por quê. |
| INV-32 | Recebimento concluído não significa que todos os objetos foram aceitos nem que toda custódia foi encerrada. | Separar fechamento administrativo, decisão técnica e destinação física. |
| INV-33 | Uma chegada complementar é um novo fato vinculado ao processo original ou à nova solicitação autorizada; não altera retroativamente a chegada anterior. | Cumprir D19. |
| INV-34 | Agrupamento/fracionamento conserva reconciliação de quantidades e linhagem dos objetos. | Evitar perda de rastreabilidade. |

## 13. Regras transversais de autorização, assinatura e auditoria

### 13.1 Autorização e competência

- As operações são autorizadas por usuário individual e permissões explícitas.
- A competência técnica deve ser verificada conforme atividade, categoria, vigência e designação aplicáveis; RBAC sozinho não prova competência.
- Perfis funcionais podem ser acumulados conforme D10, mas atos que exigem independência devem ser praticados por outro servidor habilitado.
- Recepção pode também conferir quando possuir ambas as permissões, mas registro da chegada e conferência permanecem eventos distintos, com autoria/horários próprios.
- Administrador técnico não adquire autoridade para aceitar, recusar ou aprovar critério técnico por sua função administrativa.
- Ausência de validador independente não autoriza autoaprovação; o processo aguarda substituto formalmente designado ou decisão da autoridade competente.

### 13.2 Assinatura eletrônica

A assinatura eletrônica formal é exigida somente para atos definidos pela política institucional. Quando exigida, deve identificar signatário, intenção, ato/alvo e conteúdo exato assinado, com data/hora e evidência de verificação. Assinatura não substitui autorização ou validação independente. A modalidade tecnológica/jurídica permanece pendente.

### 13.3 Auditoria

A auditoria deve permitir reconstruir solicitação, chegada, apresentação, custódia, conferência, pendência, decisão, validação, amostra, transferência, localização, devolução/destinação e retificação. Deve preservar ator, papel/competência aplicável, tempo do fato, tempo do registro, antes/depois, justificativa, evidência e correlação de operação. Eventos formalizados não são apagados.

## 14. Compatibilidade com o domínio atual e legado

### 14.1 Componentes potencialmente reutilizáveis

| Componente atual | Papel lógico futuro | Limite |
|---|---|---|
| User / RefreshToken / RBAC | Identidade e autenticação de usuários internos. | Não substitui competência/designação institucional nem isolamento de solicitante externo. |
| ElectronicSignature | Evidência técnica de assinatura de atos. | Política e alvos de assinatura precisam ser aprovados. |
| AuditLog | Trilha técnica transversal. | Taxonomia e cobertura dos eventos SEFI precisam ser especificadas. |
| ChainOfCustody | Possível suporte ao histórico de EventoCustodia. | Compatibilização deve preservar eventos legados e evitar duplicação; não substitui ObjetoCustodia. |
| DeviceSample | Implementação atual que pode ser compatibilizada como AmostraOperacional. | Não deve ser criada na chegada; criação somente após D20. |
| LabTest / LabTestResult | Implementação atual do domínio de ensaios. | Mantém-se subordinada à AmostraOperacional, sem substituir recebimento/decisão. |
| CapaAction | Ação corretiva/preventiva do domínio da qualidade. | Não substitui Pendencia de recebimento. |

### 14.2 Registros legados

- Amostras e eventos legados permanecem consultáveis conforme seu vínculo original.
- Não preencher Solicitação, Recebimento, ItemRecebimento ou ObjetoCustodia retroativamente sem documento/evidência suficiente.
- A reconciliação deve produzir relatório de associados, não associados, ambiguidades e exceções aprovadas.
- Compatibilidade do `accession_number`, QR e campos atuais de recebimento exige decisão própria; não criar identificador institucional duplicado.
- A continuidade histórica do novo fluxo deve apontar eventos a ObjetoCustodia mesmo após a criação da AmostraOperacional, conforme contrato a revisar.

### 14.3 Lacunas que o M0.3 resolve conceitualmente

1. Explicita o agregado ObjetoCustodia separado da AmostraOperacional.
2. Define chegada e custódia antes da amostra.
3. Distingue EventoCustodia de ObjetoCustodia.
4. Separa transferência de mudança de localização.
5. Define decisão por objeto quando os resultados podem divergir.
6. Distingue pendência de CAPA e recusa de não apresentação.
7. Estabelece a barreira de D20 para a AmostraOperacional.
8. Propõe um mecanismo lógico para D19 sem criar segundo recebimento principal.
9. Define estados e invariantes transversais para orientar rastreabilidade e validação.

Estas definições são propostas documentais e não significam que o código atual já as implemente.

## 15. Questões pendentes e classificações

| ID | Questão | Natureza | Tratamento no M0.3 | Condição para encerramento |
|---|---|---|---|---|
| M03-01 | EventoApresentacao para chegadas complementares e apresentações parciais. | Refinamento funcional de D19. | Proposto. | Revisão e aceite em cenários SIM correspondentes; definir reabertura versus nova solicitação quando encerrada. |
| M03-02 | Critérios de agrupamento/fracionamento por categoria e linhagem. | Funcional/técnica. | Princípios definidos; parâmetros não. | Procedimentos técnicos e exemplos reais validados; compatibilizar com G0-P26. |
| M03-03 | Unidades, precisão, conversão e reconciliação de quantidades. | Funcional/técnica. | Dimensões separadas; regras numéricas pendentes. | Catálogo de unidades e critérios por categoria aprovados. |
| M03-04 | Taxonomia e estados terminais de devolução/destinação. | Institucional/operacional. | Eventos e princípios descritos. | Procedimento G0-P04/G0-P20, alçadas e comprovantes aprovados. |
| M03-05 | Checklist concreto, classes E/S/I e critérios por categoria. | Técnica/institucional. | Estrutura e governança modeladas. | Checklists versionados aprovados por especialistas, Qualidade e autoridade. |
| M03-06 | Matriz nominal de competências, substitutos e independência. | Institucional. | Referência lógica prevista. | Designações formais G0-P01/G0-P16. |
| M03-07 | Prazos, canais, prorrogação e comunicação formal. | Institucional. | Ciclo da pendência definido sem valores numéricos. | Tabela/procedimento G0-P03/G0-P18. |
| M03-08 | Modalidade, nível jurídico e atos que exigem assinatura. | Institucional/jurídica/técnica. | Conceito separado de validação independente. | Deliberação G0-P05/G0-P19 e revisão jurídica/TI. |
| M03-09 | Protocolo SEFI, accession e QR. | Institucional/técnica. | Semânticas separadas. | DEC07 e padrão institucional aprovados. |
| M03-10 | Política de identidade/contas externas e isolamento de solicitante. | Segurança/institucional. | Solicitante não pressupõe conta externa. | G0-P21 e revisão de arquitetura/segurança. |
| M03-11 | Anexos, armazenamento, integridade, retenção e recuperação. | Arquitetural/institucional. | Evidência e vínculo lógico previstos. | G0-P09/G0-P24/G0-P30 e arquitetura aprovados. |
| M03-12 | Backup, restauração, RPO/RTO e continuidade. | Infraestrutura/institucional. | Fora do modelo de entidades de negócio; obrigação transversal. | G0-P06 e evidência de teste de restauração. |
| M03-13 | Retificação e impacto sobre amostras, ensaios e laudos. | Funcional/técnica/institucional. | Entidade Retificacao e vínculo de impacto propostos. | Matriz G0-P10/G0-P27 aprovada e casos CA executados. |
| M03-14 | Migração/reconciliação e convivência com legado. | Dados/arquitetura. | Regras de não inferência definidas. | G0-P22, inventário e relatório de reconciliação aprovados. |
| M03-15 | Modelo físico da cadeia única de custódia e projeções de estado/local. | Arquitetural. | EventoCustodia é conceito lógico; não define tabela. | Revisão COMP01–COMP07, contrato histórico e schema. |
| M03-16 | Estados da AmostraOperacional e compatibilidade com workflow atual. | Domínio/arquitetura. | Estados propostos como candidatos. | Mapeamento validado com fluxo de ensaios e testes de regressão. |

## 16. Rastreabilidade D01–D20

| Decisão | Materialização lógica no M0.3 |
|---|---|
| D01 | Separação de ator de recepção, autoria do registro e conferência; eventos distintos. |
| D02 | Metadados de chegada, volumes, condição, observações, documentos e timestamp. |
| D03 | Dimensões de quantidade declarada, apresentada, sob custódia, aceita, recusada e não apresentada. |
| D04 | ItemRecebimento 1:0..N ObjetoCustodia; decisões independentes por objeto. |
| D05 | Pendência com responsável, comunicação, prazo, prorrogação, evidência e reavaliação. |
| D06 | Decisão de recusa separada da custódia e do encerramento físico. |
| D07 | Evento de transferência com confirmação do novo custodiante. |
| D08 | Evento de mudança de localização independente da transferência. |
| D09 | Retificacao com valores original/corrigido, autorização, assinatura quando exigida e impacto. |
| D10 | Acúmulo de funções permitido; validação independente obrigatória quando aplicável. |
| D11 | Checklist por categoria, critérios E/S/I e versão aplicada preservada. |
| D12 | Governança de modelo, versão, aprovação e publicação de checklist. |
| D13 | Evidencia e VinculoEvidencia com metadados, hash, versão, controle e retenção. |
| D14 | EventoAuditoria transversal, append-only e correções como novos atos. |
| D15 | Usuários individuais, menor privilégio, escopo e competência. |
| D16 | Assinatura eletrônica vinculada ao ato/conteúdo, separada da validação. |
| D17 | Continuidade/backup/restauração como requisito transversal, não entidade de negócio. |
| D18 | Identificadores independentes para Solicitação, Recebimento, ObjetoCustodia, Amostra e Ensaio. |
| D19 | EventoApresentacao complementar, novo fato e reavaliação, sem retroatividade. |
| D20 | AmostraOperacional somente após aceite, checklist, bloqueios, validações e custódia válidos. |

## 17. Critérios de validação do M0.3

O M0.3 somente poderá ser considerado funcionalmente consolidado após:
1. revisão do responsável pela Validação Institucional e Qualidade;
2. confirmação explícita de que as cardinalidades M0.2 foram preservadas;
3. validação da proposta EventoApresentacao para D19 e de sua compatibilidade com recebimento principal único;
4. validação de cenários de item parcial, múltiplas apresentações, vários objetos, agrupamento, fracionamento e decisões divergentes;
5. confirmação da distinção entre decisão do objeto, estado de custódia e estado agregado do recebimento;
6. validação da sequência de aceite e criação da AmostraOperacional conforme D20;
7. rastreabilidade de cada invariante a um ou mais CA01–CA37 e cenários SIM01–SIM12, com identificação de lacunas;
8. revisão de coerência com EST-REC-001, MOD-DOM-001, MOD-REL-001 e CTR-LIMS-CUST-001;
9. registro das divergências, decisões e responsáveis, sem converter pendência em aprovação tácita.

## 18. Próxima sequência documental recomendada

1. Revisar M0.3 com foco nas decisões M03-01 a M03-16; priorizar M03-01 a M03-03 por afetarem cardinalidades e reconciliação.
2. Atualizar a matriz de rastreabilidade `D01–D20 × entidade × estado × evento × invariante × CA × SIM`.
3. Confrontar M0.3 com EST-REC-001 e MOD-REL-001, registrando divergências sem editar silenciosamente os documentos anteriores.
4. Produzir uma versão consolidada do DER conceitual, depois da resolução das questões que alteram relações.
5. Só então revisar o modelo relacional e contratos técnicos; qualquer implementação dependerá de autorização específica posterior e da deliberação formal do Gate G0.

## 19. Parecer e situação formal

O M0.3 organiza em um único modelo lógico as entidades, relações, estados, eventos e invariantes necessários para representar o fluxo SEFI e explicita as lacunas que a auditoria cruzada identificou. Ele preserva as cardinalidades M0.2 já aprovadas e sinaliza como proposta o refinamento de apresentação complementar para cumprir D19 sem criar um segundo recebimento principal.

Este documento é uma proposta para revisão, não uma aprovação institucional do novo refinamento nem um atestado de que o software existente já atende ao domínio.

**M0.3: DOCUMENTO ELABORADO — AGUARDANDO REVISÃO/VALIDAÇÃO.**  
**Gate G0: NÃO APROVADO.**  
**Implementação: NÃO AUTORIZADA.**  
**Alterações de código, banco, API, frontend, CI e infraestrutura: NENHUMA.**

## 20. Histórico de versões

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-10 | Primeira versão do modelo lógico revisado: entidades, cardinalidades, estados, transições, eventos, invariantes, D01–D20, compatibilidade com legado e pendências. |
