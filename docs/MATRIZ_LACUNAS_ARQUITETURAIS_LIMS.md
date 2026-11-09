# Matriz de Lacunas Arquiteturais do LIMS

- **Projeto:** LIMS — Serviço de Ensaios Físicos (SEFI/FUNED)
- **Repositório:** `keyzermoura/LIMS`
- **Branch documental:** `main`
- **Data de elaboração:** 09/11/2026
- **Natureza:** análise arquitetural e planejamento; não constitui autorização de implementação.
- **Documentos de referência:**
  - `docs/ENTREGA_1_DIAGNOSTICO_TECNICO_FUNCIONAL.md`
  - `docs/ETAPA_1_DESENHO_TECNICO_SOLICITACAO_RECEBIMENTO.md`
  - `README.md`

---

## 1. Objetivo

Consolidar em um único instrumento de acompanhamento as lacunas entre:

1. a base técnica e funcional já existente no repositório;
2. as regras e decisões já documentadas para o fluxo de solicitação, recebimento e operação laboratorial;
3. as capacidades necessárias para que o projeto evolua de um MVP de gestão de amostras e ensaios para um LIMS institucional, rastreável e adequado às atividades laboratoriais.

A matriz deve orientar decisões, priorização, desenho técnico, implementação, testes e validação. Seu propósito é evitar que lacunas identificadas sejam esquecidas ou que funcionalidades sejam implementadas isoladamente, sem considerar seus impactos sobre o ciclo de vida da amostra e dos resultados.

## 2. Como interpretar esta matriz

### 2.1 Situação da capacidade

| Situação | Significado |
|---|---|
| Existente — reutilizar | O diagnóstico do repositório identificou estrutura funcional aproveitável. A implementação deve ser revalidada antes de alterações. |
| Parcial — evoluir | Existe parte da capacidade, mas ela não cobre integralmente a regra ou o fluxo requerido. |
| Documentada — não implementada | Há decisão, regra ou desenho nos documentos, mas não há implementação correspondente identificada. |
| Não identificada — projetar | O diagnóstico não identificou estrutura suficiente. É necessário detalhar o requisito e o desenho. |
| Decisão pendente | Depende de definição institucional ou de decisão arquitetural antes da implementação. |
| Validar tecnicamente | A documentação indica uma capacidade, mas sua abrangência, integridade ou comportamento precisa ser comprovado por inspeção e testes. |

### 2.2 Prioridade

- **P0 — bloqueadora:** deve ser resolvida antes de implementar ou liberar o fluxo dependente.
- **P1 — alta:** necessária para a primeira entrega funcional ou para preservar integridade, rastreabilidade e segurança.
- **P2 — média:** necessária para completar o ciclo laboratorial ou ampliar a operação.
- **P3 — evolução:** melhoria, integração ou capacidade que pode ser planejada para etapa posterior, sem comprometer os controles essenciais.

### 2.3 Limite das evidências

O diagnóstico técnico-funcional registra inspeção de código, modelos, serviços, rotas, frontend, migrações e testes, tendo como referência o commit nele identificado. O README descreve capacidades e resultados de testes do projeto, mas é documentação produzida pelo próprio projeto. Portanto:

- uma funcionalidade descrita no README não deve ser considerada validada apenas por estar documentada;
- uma estrutura existente no código não significa que atenda à regra operacional do SEFI;
- a aprovação do CI comprova somente os testes e verificações executados naquele commit;
- antes de cada implementação, deve-se reexaminar a branch, os arquivos, as migrações e os testes atuais.

Esta matriz não substitui uma revisão de código por arquivo nem uma validação formal do sistema.

---

## 3. Síntese executiva

O repositório já dispõe de uma base técnica relevante: cadastro operacional de amostras, ensaios e resultados versionados, custódia, autenticação, controle de acesso, assinatura eletrônica, trilha de auditoria com mecanismos de integridade e estrutura de CAPA.

O principal desafio não é reconstruir todo o LIMS. É **adaptar e ampliar a base existente para representar corretamente o processo institucional**, sobretudo a separação entre solicitação, chegada física, conferência, aceite e criação da amostra operacional.

O diagnóstico também aponta lacunas no ciclo laboratorial: execução independente do ensaio, gestão de métodos e suas versões, dados brutos/evidências, revisão técnica, aprovação do conjunto de resultados e laudo consolidado da solicitação.

### 3.1 Cinco pontos que merecem atenção prioritária

1. **Modelo de solicitação e recebimento:** a amostra operacional existente representa material recebido. Não deve ser criada no momento do cadastro prévio da solicitação.
2. **Itens do recebimento:** o desenho precisa persistir todos os itens declarados, inclusive os não apresentados, e preservar a situação individual de cada um.
3. **Transição para a amostra operacional:** o aceite final deve criar a amostra e seus identificadores de forma atômica, idempotente e auditável, preservando a custódia iniciada na chegada.
4. **Ciclo de ensaio:** ensaio planejado, execução, resultado, revisão e aprovação são eventos/entidades distintos e não devem ser condensados em um único registro.
5. **Laudo consolidado:** o histórico de resultados por ensaio não substitui o documento final da solicitação, suas versões e assinaturas.

---

## 4. Matriz A — Solicitação, recebimento e identificação

| ID | Capacidade / requisito | Situação identificada | Lacuna ou risco | Prioridade | Direcionamento / evidência de aceite |
|---|---|---|---|---|---|
| A01 | Cadastro independente da solicitação | Parcial — evoluir | O cadastro atual é centrado em `DeviceSample`; não representa integralmente a demanda anterior à chegada. | P0 | Criar entidade de solicitação, com solicitante, origem, dados declarados, datas e estado próprios. Testar cadastro sem criação de amostra operacional. |
| A02 | Itens declarados na solicitação | Documentada — não implementada | O desenho prevê múltiplos itens por solicitação; o diagnóstico anterior descreveu relação 1:1 entre solicitação e dispositivo para a rotina do SEFI. Há uma diferença de escopo que precisa ser resolvida. | P0 | Confirmar se o modelo institucional será 1 solicitação : 1 dispositivo ou se comportará vários itens. Não implementar cardinalidade antes dessa decisão. |
| A03 | Recebimento físico separado | Documentada — não implementada | A chegada precisa existir antes de `DeviceSample`, com data/hora, recebedor e condições próprias. | P0 | Criar registro de recebimento independente e demonstrar que uma solicitação pode existir sem recebimento e sem amostra operacional. |
| A04 | Um recebimento principal por solicitação | Decisão definida / implementar | A regra aprovada limita a um recebimento físico principal. É necessário impedir duplicidade inclusive sob concorrência. | P0 | Restrição de unicidade no banco, operação transacional e teste concorrente. Segunda tentativa deve carregar o recebimento existente. |
| A05 | Todos os itens declarados representados no recebimento | Parcial — evoluir | A tela lista todos os itens, mas o modelo descrito não garante persistência individual dos itens não apresentados. | P0 | Projetar `ReceiptItem`/`ReceiptLine` para todos os itens declarados, com situação de apresentação e histórico. |
| A06 | Item não apresentado | Documentada — não implementada | Ausência física não pode ser confundida com recusa técnica nem gerar amostra ou custódia individual. | P0 | Persistir a situação “não apresentado”; testar que não cria `DeviceSample`, `ReceiptSample` nem evento de custódia do material ausente. |
| A07 | Conferência individual por item | Documentada — não implementada | Checklist, evidências, observações e decisão precisam estar ligados ao item e à versão avaliada. | P0 | Modelar respostas por critério, versão do checklist, autor, data/hora e evidências. |
| A08 | Decisão de recebimento por item | Documentada — não implementada | Aceite, pendência, recusa e não apresentação têm semânticas diferentes. | P0 | Separar estado de apresentação, situação da conferência e decisão. Testar combinações de resultados entre itens. |
| A09 | Coordenação e exceções | Documentada — não implementada | Exceções exigem encaminhamento e decisão formal; critérios impeditivos não podem ser dispensados. | P0 | Criar registro próprio de análise da coordenação, com decisão, justificativa, autor, data/hora e vínculo à ocorrência. |
| A10 | Regularização e reavaliação | Documentada — não implementada | A correção de pendência não pode apagar a resposta ou decisão anterior. | P1 | Registrar novas versões/eventos de regularização e reavaliação; demonstrar histórico íntegro. |
| A11 | Dados declarados versus conferidos | Decisão definida / implementar | Sobrescrever os dados informados na solicitação com os dados conferidos eliminaria a evidência da divergência. | P0 | Preservar os dois conjuntos e registrar a resolução de divergências. |
| A12 | Identificadores distintos | Parcial — evoluir | Número da solicitação, protocolo SEFI e `accession_number` possuem momentos e finalidades distintos. | P0 | Manter os três conceitos separados, com unicidade e rótulos claros; preservar compatibilidade do QR atual. |
| A13 | Criação da amostra após aceite | Documentada — não implementada | `DeviceSample` já representa material recebido e inicia custódia; criá-lo antes do aceite conflita com seu significado atual. | P0 | Criar a amostra operacional somente após aceite final e validações. Testar transação atômica e idempotência. |
| A14 | Preservação da chegada e do recebedor | Decisão definida / implementar | A criação posterior da amostra não pode alterar a data/hora real da chegada nem atribuir a recepção a quem apenas concluiu o cadastro. | P0 | Copiar `Receipt.arrived_at` e o recebedor físico real para os campos operacionais correspondentes, preservando autoria da criação. |
| A15 | Entrega posterior de item ausente | Decisão definida / decisão complementar pendente | Não se pode incluir material entregue posteriormente como se estivesse presente na chegada original. A regra de exceção precisa ser formalizada. | P1 | Exigir nova solicitação ou evento complementar formalmente autorizado, sem criar segundo recebimento principal nem alterar a chegada original. |
| A16 | Protocolo legado, QR e referências antigas | Parcial — validar tecnicamente | Mudança de significado do `accession_number` pode quebrar consultas, etiquetas, QR e registros antigos. | P0 | Mapear consumidores do identificador e testar leitura dos QR existentes antes de qualquer migração. |

### 4.1 Decisão estrutural ainda necessária: cardinalidade da solicitação

Há uma divergência entre documentos que não deve ser resolvida implicitamente:

- o diagnóstico técnico-funcional descreve a rotina SEFI como uma solicitação vinculada a um único dispositivo;
- o desenho de solicitação/recebimento mais recente contempla vários itens declarados em uma solicitação, com decisões independentes.

É necessário decidir se “item” significa um dispositivo individual, uma unidade de material, um conjunto de produtos ou uma linha de demanda. A decisão afeta as relações entre solicitação, itens, recebimento e amostras operacionais.

**Recomendação:** adotar uma entidade de item da solicitação e explicitar a semântica de cada nível. Se a rotina institucional realmente for sempre um dispositivo por solicitação, a relação poderá ser restringida por regra; não se deve, porém, confundir item de solicitação, unidade física recebida, amostra operacional e corpo de prova.

---

## 5. Matriz B — Ciclo de vida laboratorial

| ID | Capacidade / requisito | Situação identificada | Lacuna ou risco | Prioridade | Direcionamento / evidência de aceite |
|---|---|---|---|---|---|
| B01 | Catálogo de ensaios | Parcial — evoluir | `LabTest` existe, mas deve ser avaliado se representa catálogo, planejamento ou instância de ensaio. | P1 | Separar definição/catalogação do ensaio e ensaio planejado para uma amostra. |
| B02 | Método e versão aplicável | Não identificada — projetar | O método efetivamente utilizado precisa ser preservado, inclusive quando o procedimento mudar depois. | P1 | Criar catálogo e versões de método; vincular cada execução à versão vigente utilizada. |
| B03 | Planejamento dos ensaios | Parcial — evoluir | Planejamento e execução estão concentrados no modelo atual. | P1 | Manter plano de ensaios separado das execuções efetivas. |
| B04 | Distribuição aos analistas | Parcial — evoluir | Há associação de responsável, mas faltam regras completas de fila, disponibilidade, prazos e reatribuição. | P2 | Registrar atribuição e reatribuição, responsável, justificativa e histórico. |
| B05 | Execução independente | Não identificada — projetar | Um ensaio planejado pode ter múltiplas tentativas; versão de resultado não substitui nova execução. | P0 | Criar `TestExecution`, com início/fim, executor, estado, ocorrência e vínculo ao ensaio planejado. |
| B06 | Repetição, interrupção e invalidação | Parcial — evoluir | Emendas de resultado não representam repetição experimental ou interrupção. | P1 | Registrar nova execução, motivo, vínculo à tentativa anterior e destino dos resultados anteriores. |
| B07 | Resultados estruturados | Parcial — evoluir | Resultado atual existe, mas precisa suportar múltiplos parâmetros, unidades, critérios, cálculos e resultados por execução. | P1 | Definir modelo de resultados tipados, unidades, limites, regra de cálculo e vínculo à execução. |
| B08 | Dados brutos e memória de cálculo | Não identificada — projetar | O README/diagnóstico apontam limitação de anexos e evidências. Um valor final isolado pode não sustentar a rastreabilidade metrológica. | P0 | Armazenar ou referenciar dados brutos, arquivos originais, cálculos, versão do algoritmo e hash. |
| B09 | Evidências e anexos | Não identificada — projetar | Faltam armazenamento controlado, metadados, integridade, autorização e retenção. | P1 | Definir repositório de arquivos, hash, tamanho, tipo, autor, data/hora, controle de acesso e política de retenção. |
| B10 | Equipamento por execução | Não identificada — projetar | Não há estrutura suficiente para associar a execução à situação metrológica do equipamento. | P0 | Cadastrar equipamentos e vincular equipamento/sensor/acessório e situação válida à execução. |
| B11 | Calibração e verificação | Não identificada — projetar | A execução deve demonstrar que o equipamento estava apto na data do ensaio. | P0 | Registrar certificados, faixa, validade, situação, verificações intermediárias e bloqueios. |
| B12 | Condições ambientais | Não identificada — projetar | Temperatura, umidade e outras condições podem ser relevantes ao método. | P1 | Registrar parâmetros aplicáveis por execução, com unidade, data/hora, fonte e limites. |
| B13 | Revisão técnica | Não identificada — projetar | Assinatura não substitui fluxo de revisão com devolução, correção e decisão. | P0 | Criar revisão técnica independente, com revisor, checklist, decisão e histórico. |
| B14 | Segregação de funções | Parcial — validar tecnicamente | RBAC existe, mas a matriz real de responsabilidades deve impedir conflitos de autoria, revisão e aprovação. | P0 | Definir matriz de incompatibilidades e testar permissões em API e interface. |
| B15 | Aprovação do conjunto de resultados | Não identificada — projetar | A aprovação de um resultado por ensaio não equivale à liberação do conjunto da solicitação. | P1 | Criar etapa de aprovação consolidada, com pendências, responsável e decisão. |
| B16 | Laudo consolidado | Não identificada — projetar | Versões de resultados por ensaio não substituem laudo final da solicitação. | P0 | Criar documento final, com resultados liberados, conclusão, responsáveis e versão. |
| B17 | Emissão e retificação de laudo | Parcial — evoluir | Há versionamento de resultados; é necessário definir versão do documento emitido, substituição e retificação. | P1 | Congelar conteúdo emitido; correção gera nova versão/documento substitutivo e preserva o anterior. |
| B18 | Histórico de estado do processo | Parcial — evoluir | Estados de solicitação, recebimento, amostra, ensaio, execução, revisão e laudo não podem ser confundidos. | P0 | Definir máquinas de estado independentes e transições válidas, com testes negativos. |

---

## 6. Matriz C — Qualidade e conformidade laboratorial

| ID | Capacidade / requisito | Situação identificada | Lacuna ou risco | Prioridade | Direcionamento / evidência de aceite |
|---|---|---|---|---|---|
| C01 | Controle de documentos e procedimentos | Não identificada — projetar | Métodos, POPs, formulários e modelos precisam de versão, aprovação e vigência. | P1 | Criar controle documental ou integração controlada, com histórico e vínculo às execuções. |
| C02 | Competência e autorização de pessoal | Parcial — evoluir | Perfis de acesso não demonstram competência técnica para executar ou revisar cada método. | P1 | Manter matriz de competência/autorização por pessoa, método e período de validade. |
| C03 | Equipamentos e rastreabilidade metrológica | Não identificada — projetar | Falta gestão de cadastro, calibração, manutenção, verificação e situação de uso. | P0 | Criar módulo de equipamentos e regras de bloqueio por situação metrológica. |
| C04 | Não conformidades | Parcial — evoluir | CAPA existe, mas não necessariamente cobre desvios de recebimento, execução, revisão, equipamento ou sistema. | P1 | Mapear origens de não conformidade e relacionar registro, contenção, avaliação e disposição. |
| C05 | CAPA e eficácia | Existente — reutilizar/evoluir | A abertura automática por reprovação é útil, mas não equivale a um processo completo de ação corretiva/preventiva para todas as origens. | P2 | Preservar o mecanismo e ampliar origens, responsáveis, prazos, evidências e verificação de eficácia. |
| C06 | Controle de mudanças | Não identificada — projetar | Alterações de métodos, regras, formulários, software e parâmetros podem afetar resultados históricos. | P1 | Registrar solicitação, avaliação de impacto, aprovação, implantação e verificação. |
| C07 | Validação do sistema informatizado | Não identificada — projetar | Testes de software e CI não comprovam validação para uso pretendido. | P0 antes de uso institucional | Planejar requisitos, análise de risco, testes de aceitação, rastreabilidade, evidências e aprovação institucional. |
| C08 | Retenção e arquivamento | Não identificada — projetar | Não há política completa identificada para guarda, preservação, recuperação e descarte. | P1 | Definir prazos por classe documental, bloqueio legal, recuperação e descarte autorizado. |
| C09 | Integridade e auditabilidade | Existente — validar/evoluir | Hash, HMAC e append-only são uma boa base, mas devem cobrir novas entidades, anexos e transições. | P0 | Testar alteração, exclusão, concorrência, exportação, verificação e continuidade da cadeia. |
| C10 | Assinaturas eletrônicas | Existente — validar/evoluir | Mecanismo de assinatura existe; novos atos exigem matriz de significado, autorização e vínculo inequívoco. | P0 | Mapear cada ato que exige assinatura, validar autorização na emissão e consumo e testar não repúdio técnico. |
| C11 | LGPD e dados pessoais | Validar tecnicamente / decisão institucional | Snapshots de auditoria e exportações podem conter dados pessoais além do necessário. | P1 | Definir finalidade, minimização, perfis, retenção, mascaramento e tratamento de solicitações de titulares. |
| C12 | Continuidade, backup e recuperação | Validar tecnicamente | A arquitetura de produção precisa comprovar backup, restauração e recuperação de desastre. | P0 antes de produção | Documentar RPO/RTO, rotina, cópias segregadas e testes periódicos de restauração. |

---

## 7. Matriz D — Plataforma, segurança e integração

| ID | Capacidade / requisito | Situação identificada | Lacuna ou risco | Prioridade | Direcionamento / evidência de aceite |
|---|---|---|---|---|---|
| D01 | Autenticação e sessões | Existente — reutilizar/validar | JWT, refresh rotativo e reautenticação são descritos no README. | P1 | Revalidar expiração, revogação, bloqueio, armazenamento seguro e recuperação de conta. |
| D02 | Autorização por função | Existente — evoluir | RBAC existe, mas precisa refletir papéis e segregação de funções reais do SEFI. | P0 | Aprovar matriz de permissões por recurso, ação e estado; testar API e UI. |
| D03 | Isolamento de dados por solicitante externo | Bloqueador conhecido | O diagnóstico identificou ausência de isolamento abrangente por titularidade. | P0 | Manter cadastro assistido interno na primeira entrega; não habilitar portal externo antes de testes de isolamento em todas as rotas. |
| D04 | Auditoria append-only | Existente — reutilizar/validar | Trilha encadeada com hash/HMAC e verificação/exportação é descrita no README. | P0 | Estender a novas entidades e verificar que eventos críticos não podem ser alterados ou omitidos. |
| D05 | Integridade transacional | Parcial — evoluir | Há unidades de trabalho atômicas, mas novas operações exigem transações que incluam negócio, auditoria, assinatura e custódia. | P0 | Testar rollback completo em falha de cada etapa e concorrência. |
| D06 | Idempotência | Parcial — evoluir | O diagnóstico aponta ausência de garantia geral para criações e reenvios. | P0 | Definir chaves e respostas idempotentes para aceite, criação de amostra, identificadores e emissão de laudo. |
| D07 | Controle de concorrência | Parcial — validar/evoluir | Há versionamento e bloqueios em serviços, mas não se deve presumir proteção universal. | P0 | Exigir versão esperada em operações críticas e testar atualizações simultâneas e reenvio. |
| D08 | Migrações e compatibilidade de legado | Parcial — evoluir | Existem amostras e relações operacionais. Mudanças obrigatórias podem quebrar dados existentes. | P0 | Preferir migrações aditivas, fase transitória, mapeamento confiável e plano de rollback/recuperação. |
| D09 | Triggers e mecanismos de imutabilidade | Existente — validar/evoluir | SQL de triggers e snapshot de migração precisam acompanhar novas tabelas. | P0 | Atualizar SQL de desenvolvimento e migração implantável em conjunto; testar PostgreSQL real. |
| D10 | Sequências e identificadores | Parcial — evoluir | Novas sequências precisam ser compatíveis com dialetos, allowlist e testes. | P1 | Definir estratégia de numeração e validar unicidade sob concorrência e falhas. |
| D11 | Armazenamento de arquivos | Não identificada — projetar | Ausência de solução completa de anexos, documentos e dados instrumentais. | P1 | Definir armazenamento, metadados, hash, antivírus quando aplicável, autorização e retenção. |
| D12 | Integração com instrumentos | Não identificada — projetar | Não há integração identificada para importação controlada de dados instrumentais. | P2 | Planejar formatos, validação, identificação do equipamento, integridade e revisão da importação. |
| D13 | Integrações institucionais | Não identificada — projetar | Não há fluxo institucional integrado identificado para sistemas externos. | P3 | Inventariar sistemas, dados, responsabilidades, autenticação, contratos e logs antes de integrar. |
| D14 | Notificações e alertas | Não identificada — projetar | O README aponta ausência de notificações. | P2 | Definir eventos, destinatários, canais, prazos, reenvio e registro de entrega. |
| D15 | Observabilidade e operação | Validar tecnicamente | Health check e infraestrutura existem; faltam evidências sobre monitoramento, logs operacionais, alertas e gestão de incidentes. | P1 | Definir métricas, logs, alertas, rastreamento de falhas e procedimento operacional. |
| D16 | Testes de navegador e acessibilidade | Parcial — evoluir | Há testes de API e build; o diagnóstico aponta ausência de E2E de navegador. | P1 | Criar testes E2E para fluxos críticos e verificar acessibilidade/usabilidade das telas. |

---

## 8. Matriz E — Gestão, consulta e experiência de uso

| ID | Capacidade / requisito | Situação identificada | Lacuna ou risco | Prioridade | Direcionamento / evidência de aceite |
|---|---|---|---|---|---|
| E01 | Telas de solicitação e recebimento | Documentada — não implementada | Duas telas principais e modal foram definidos documentalmente. | P0 | Implementar somente após aprovação do modelo de dados e dos critérios de aceite. |
| E02 | Retomada de trabalho | Documentada — não implementada | Rascunhos, salvamento e retomada exigem persistência e controle de versão. | P1 | Testar saída/retorno, conflito de edição e aviso de alterações não salvas. |
| E03 | Consulta e filtros | Existente — evoluir | Há listagens de amostras, ensaios e auditoria; novas entidades exigirão consultas próprias. | P1 | Definir filtros por solicitação, estado, item, período, responsável e laboratório. |
| E04 | Painel gerencial | Parcial — evoluir | Dashboard atual não necessariamente apresenta o fluxo completo e os indicadores institucionais. | P2 | Definir indicadores operacionais, filas, prazos, pendências e produtividade com regras claras. |
| E05 | Relatórios operacionais | Parcial — evoluir | Exportação de auditoria não substitui relatórios de recebimento, andamento, ensaios e laudos. | P2 | Definir relatórios, filtros, permissões, conteúdo e rastreabilidade da exportação. |
| E06 | Código de barras/QR | Existente — reutilizar/evoluir | QR atual está ligado ao identificador da amostra operacional; solicitação e protocolo são conceitos distintos. | P1 | Preservar QR atual e avaliar etiquetas para solicitação, recebimento e amostra sem confundir identificadores. |
| E07 | Portal do solicitante | Não implementar na primeira entrega | O acesso externo exige isolamento por propriedade, autorização e proteção de dados. | P3 | Manter fora do MVP inicial; reavaliar após implementação e teste abrangente de autorização por titularidade. |
| E08 | Multi laboratório institucional | Decisão arquitetural a confirmar | O identificador institucional não deve ser específico do SEFI; o LIMS pode atender outros laboratórios. | P1 | Definir entidade laboratório, lotação/roteamento, permissões e identificador global antes de expansão multiunidade. |
| E09 | Usabilidade e acessibilidade | Documentada parcialmente | Wireframes definem fluxo, mas não comprovam comportamento, responsividade ou acessibilidade. | P2 | Testar com usuários, teclado, leitores de tela, resoluções e volume real de dados. |
| E10 | Arquivamento e consulta histórica | Não identificada — projetar | O encerramento deve preservar consulta, evidências e versões por todo o prazo de retenção. | P1 | Definir ciclo de vida, acesso histórico, restauração e bloqueio de descarte. |

---

## 9. Decisões e pendências que precisam de resolução

| ID | Questão | Situação | Decisão necessária |
|---|---|---|---|
| DEC01 | Uma solicitação pode conter um ou vários dispositivos/itens? | Divergência documental | Definir cardinalidade e semântica de solicitação, item, unidade física e amostra operacional. |
| DEC02 | Qual a entidade persistente para todos os itens do recebimento? | Proposta ainda não incorporada | Aprovar `ReceiptItem` ou `ReceiptLine`, inclusive para itens não apresentados. |
| DEC03 | Como representar entrega posterior de item não apresentado? | Regra principal definida; exceção pendente | Definir nova solicitação ou evento complementar autorizado, sem segundo recebimento principal. |
| DEC04 | Como se relacionam `ReceiptItem`, `ReceiptSample` e `DeviceSample`? | Não fechado | Definir cardinalidades, estados e transição para amostra operacional. |
| DEC05 | Como distinguir dispositivo, unidade recebida, amostra de ensaio e corpo de prova? | Não fechado | Definir glossário e modelo de domínio com exemplos reais do SEFI. |
| DEC06 | Qual a regra de numeração do protocolo SEFI? | Pendente | Definir formato, escopo, sequência, reinício por ano (se aplicável) e não reutilização. |
| DEC07 | O identificador institucional será global entre laboratórios? | Diretriz geral definida | Definir entidade geradora e escopo de unicidade institucional. |
| DEC08 | Como migrar amostras antigas sem solicitação vinculada? | Pendente de desenho | Definir vínculo confiável, dados sem correspondência e tratamento de registros legados. |
| DEC09 | Quais atos exigem assinatura eletrônica e quais significados? | Pendente de matriz | Mapear criação, aceite, recusa, coordenação, execução, revisão, aprovação e emissão. |
| DEC10 | Quais categorias de material e documentos/checklists se aplicam? | Parâmetros institucionais pendentes | Aprovar catálogo, aplicabilidade, vigência e responsáveis. |
| DEC11 | Qual o modelo de laboratório/unidade organizacional? | Pendente | Definir se a primeira versão será SEFI-only com extensão prevista ou multi laboratório desde a base. |
| DEC12 | Qual a política de retenção, backup e recuperação? | Pendente | Aprovar prazos, RPO/RTO, guarda e responsabilidades. |

---

## 10. Sequenciamento recomendado

A recomendação é não iniciar imediatamente a implementação de todas as funcionalidades listadas. O trabalho deve seguir dependências arquiteturais.

### Fase 0 — Fechamento do modelo e decisões bloqueadoras

**Objetivo:** impedir que a primeira migração consolide uma modelagem incompleta.

Entregas:
1. resolver DEC01 — cardinalidade e semântica de itens;
2. aprovar modelo de domínio para solicitação, recebimento, item, dispositivo e amostra operacional;
3. definir relação entre `ReceiptItem`, conferência, checklist, decisão, custódia e `DeviceSample`;
4. fechar estratégia dos identificadores e compatibilidade com QR;
5. desenhar migração dos dados legados;
6. aprovar regras de exceção para entrega posterior.

**Critério de saída:** diagrama de entidades/relacionamentos, dicionário de dados, estados e transições aprovados, com cenários de migração e critérios de aceite.

### Fase 1 — Solicitação, recebimento e aceite

**Objetivo:** implementar o ingresso controlado sem quebrar o fluxo operacional existente.

Entregas:
- solicitação e itens declarados;
- recebimento único;
- persistência de todos os itens, inclusive não apresentados;
- checklist versionado e evidências;
- decisões por item e coordenação;
- criação atômica/idempotente de amostra após aceite;
- identificadores e custódia compatíveis com legado.

**Critério de saída:** testes de regras de negócio, concorrência, auditoria, assinatura, migração, QR e fluxos ponta a ponta aprovados.

### Fase 2 — Planejamento e execução laboratorial

**Objetivo:** separar o planejamento de cada ensaio de sua realização efetiva.

Entregas:
- catálogo e versões de métodos;
- planejamento e distribuição;
- execução independente;
- repetição/interrupção;
- equipamentos e condições ambientais;
- resultados, dados brutos e evidências.

**Critério de saída:** execução reproduzível e rastreável, com método, equipamento, executor, dados e resultado vinculados.

### Fase 3 — Revisão, aprovação e laudo

**Objetivo:** controlar a liberação técnica e documental.

Entregas:
- revisão técnica e devolução;
- aprovação consolidada;
- laudo por solicitação;
- assinatura e versionamento;
- retificação e substituição controladas.

**Critério de saída:** nenhum laudo emitido sem verificações e aprovações exigidas; versões anteriores preservadas.

### Fase 4 — Sistema da qualidade e implantação institucional

**Objetivo:** completar controles organizacionais e evidências de uso pretendido.

Entregas:
- documentos e métodos controlados;
- competência e autorização;
- equipamentos e situação metrológica;
- não conformidade e CAPA ampliadas;
- controle de mudanças;
- validação/qualificação, treinamento, backup, recuperação e procedimentos operacionais.

**Critério de saída:** requisitos rastreados a testes e evidências aprovadas, com avaliação institucional para uso.

### Fase 5 — Integrações e expansão

**Objetivo:** ampliar a eficiência e o alcance institucional sem comprometer a base validada.

Entregas possíveis:
- integração com instrumentos;
- integrações institucionais;
- notificações;
- painéis e indicadores;
- portal externo, somente após controles de isolamento e privacidade;
- suporte a múltiplos laboratórios.

---

## 11. Regras transversais obrigatórias

As regras abaixo não devem ser adiadas para uma fase final. Devem acompanhar todas as fases:

1. **Rastreabilidade:** toda entidade crítica deve ter identificação, autoria, data/hora e histórico.
2. **Integridade:** atos críticos devem ser transacionais; falha parcial não pode deixar estado inconsistente.
3. **Idempotência:** reenvio de uma operação crítica não pode criar duplicidade.
4. **Concorrência:** decisões simultâneas devem ser detectadas e tratadas explicitamente.
5. **Versionamento:** checklist, método, resultado e laudo devem preservar a versão efetivamente aplicada ou emitida.
6. **Auditoria:** novas entidades e transições devem integrar a trilha existente, sem lacunas.
7. **Assinatura:** assinatura deve estar vinculada ao ato, usuário, entidade, ação e significado corretos.
8. **Segregação de funções:** execução, revisão e aprovação devem respeitar as responsabilidades aprovadas.
9. **Migração segura:** dados legados não podem ser associados por inferência sem evidência confiável.
10. **Testabilidade:** cada regra deve possuir critério de aceite e teste automatizado compatível.
11. **Segurança e privacidade:** autorização deve ser aplicada no backend, inclusive em consultas, exportações e arquivos.
12. **Validação:** teste de software não deve ser apresentado como prova automática de conformidade ou validação institucional.

---

## 12. Relação com a ISO/IEC 17025 e demais requisitos

A matriz foi construída considerando a necessidade de apoiar rastreabilidade, competência, métodos, equipamentos, registros técnicos, validade dos resultados, revisão e emissão de relatórios. Ela não constitui uma declaração de conformidade com a ISO/IEC 17025, 21 CFR Part 11, RDC Anvisa 665/2022 ou ALCOA+.

A aplicabilidade de cada requisito deve ser confirmada pela instituição, considerando o escopo do laboratório, procedimentos, legislação e uso pretendido do sistema. A conformidade depende também de processos, pessoas, controles organizacionais, validação e evidências — não apenas da presença de funcionalidades no software.

---

## 13. Controle de acompanhamento

Esta seção deve ser atualizada a cada decisão ou entrega relevante. Recomenda-se manter o status em um dos seguintes valores: **Não iniciado**, **Em análise**, **Aguardando decisão**, **Desenhado**, **Aprovado**, **Em implementação**, **Implementado**, **Testado** ou **Validado para uso pretendido**.

| Marco | Status inicial | Evidência a registrar |
|---|---|---|
| Fase 0 — modelo de domínio e decisões | Em análise | Diagrama, dicionário, decisões DEC01–DEC12 e aprovação |
| Fase 1 — solicitação e recebimento | Não iniciado | PR, migrações, testes, evidências funcionais |
| Fase 2 — execução laboratorial | Não iniciado | Modelo, testes de execução e rastreabilidade |
| Fase 3 — revisão e laudo | Não iniciado | Fluxos, assinaturas, versões e testes |
| Fase 4 — qualidade e implantação | Não iniciado | Procedimentos, matriz de requisitos e evidências de validação |
| Fase 5 — integrações e expansão | Não iniciado | Contratos de integração, testes e avaliação de risco |

### Registro de decisões

| Data | ID | Decisão / alteração | Responsável | Documento ou PR relacionado |
|---|---|---|---|---|
| 09/11/2026 | Inicial | Matriz criada como instrumento de acompanhamento arquitetural. Nenhuma implementação autorizada. | — | Este documento |

---

## 14. Próxima atividade recomendada

A próxima atividade deve ser uma **revisão do modelo de domínio da Fase 0**, antes de qualquer migração ou implementação da Etapa 1.

A revisão deve produzir, em conjunto:

1. glossário dos conceitos: solicitação, item solicitado, unidade física recebida, recebimento, dispositivo, amostra operacional, amostra de ensaio e corpo de prova;
2. diagrama ER com cardinalidades e opcionalidades;
3. máquina de estados de solicitação, recebimento e item;
4. relação entre `ReceiptItem`, checklist, decisão, custódia e `DeviceSample`;
5. estratégia de migração dos registros existentes;
6. cenários de teste e critérios de aceite.

**Regra de governança:** este documento registra lacunas e recomendações. Não autoriza alterações no backend, frontend, API, banco de dados, migrações ou implantação. Cada etapa de implementação dependerá de aprovação expressa do desenho correspondente.

---

## 15. Histórico de revisão

| Versão | Data | Descrição |
|---|---|---|
| 1.0 | 09/11/2026 | Criação da matriz consolidada a partir do diagnóstico técnico-funcional, do desenho de solicitação/recebimento e da documentação do repositório. |
