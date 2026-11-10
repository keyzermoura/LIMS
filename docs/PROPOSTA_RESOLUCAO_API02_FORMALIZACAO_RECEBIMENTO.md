# Proposta de Resolução da API02 — Formalização do Recebimento

**Identificador:** PROP-LIMS-API02-001  
**Versão:** 0.1  
**Situação:** Proposta técnica para validação funcional, operacional e institucional; não aprovada para implementação  
**Decisão relacionada:** API02 / DEC01–DEC05 / DEC04 / DEC05 / EST-REC-001 / UI-LIMS-001  
**Data:** 2026-11-09  
**Repositório:** keyzermoura/LIMS — branch `main`

---

## 1. Objetivo

Definir em que momento o recebimento físico se torna um registro oficial, como preservar a custódia desde a chegada e como permitir que conferências e decisões sejam salvas e retomadas sem transformar o recebimento em um conjunto de gravações parciais inconsistentes.

A decisão central é distinguir:

1. a preparação de dados ainda não formalizados;
2. a formalização única da chegada física e do recebimento principal;
3. o salvamento progressivo da conferência, das pendências, das evidências e das decisões por item;
4. o aceite final, que somente depois das validações exigidas cria a amostra operacional.

## 2. Referências e premissas

A proposta considera os documentos existentes na branch `main`:

- `ESTADOS_E_TRANSICOES_SOLICITACAO_RECEBIMENTO.md` (EST-REC-001);
- `ESPECIFICACAO_INTERFACE_ETAPA_1_RECEBIMENTO.md` (UI-LIMS-001);
- `ESPECIFICACAO_CONTRATOS_API_RECEBIMENTO_CUSTODIA.md` (API-LIMS-REC-CUST-001);
- `MODELO_CONCEITUAL_DOMINIO_SOLICITACAO_RECEBIMENTO.md` (MOD-DOM-001);
- `MATRIZ_RESOLUCAO_DECISOES_API_LIMS.md`.

Premissas funcionais já registradas:

1. A primeira entrega é de uso interno: usuário institucional cadastra a solicitação em nome do solicitante/representante; não há portal externo nesta etapa.
2. Cada solicitação admite no máximo um recebimento físico principal.
3. Uma segunda tentativa de registrar a chegada deve localizar e exibir o recebimento existente, sem criar outro.
4. Todos os itens declarados devem aparecer no recebimento, inclusive os não apresentados.
5. Apresentação, conferência, decisão e custódia são dimensões distintas.
6. A custódia começa na chegada física do material apresentado, antes da criação da amostra operacional.
7. O checklist, as pendências e as decisões podem ser salvos e retomados.
8. A amostra operacional somente é criada após aceite final e validações obrigatórias.
9. Itens não apresentados não geram custódia nem amostra.
10. A interface prevista possui duas telas principais e uma janela modal de conferência individual; não é um assistente linear obrigatório.

## 3. Alternativas avaliadas

### Alternativa A — Um único comando para todo o ciclo, incluindo conferência e decisões

O cliente enviaria chegada, apresentação, conferência, evidências, decisões e validações em uma única operação.

**Vantagens**
- Uma única transação abrangendo todo o processo.
- Menor número de estados intermediários.

**Desvantagens**
- A conferência pode demandar tempo, mais de um servidor ou regularização posterior.
- Não permite salvar e retomar adequadamente a análise por item.
- A chegada física e o início da custódia ficariam condicionados à conclusão de tarefas que podem ocorrer depois.
- Aumenta o risco de perda de dados em falhas de rede ou interrupção do trabalho.
- Mistura fatos ocorridos em momentos diferentes e executados por atores diferentes.

**Avaliação:** não recomendada.

### Alternativa B — Rascunho de recebimento persistente seguido de confirmação posterior

O sistema criaria um objeto Receipt em estado provisório, permitiria editar seus itens e só depois o converteria em recebimento oficial.

**Vantagens**
- Permite preparação colaborativa antes da confirmação.
- Evita manter todos os dados apenas no cliente.

**Desvantagens**
- Exige distinguir Receipt provisório de Receipt oficial ou introduzir estados e regras de expiração/cancelamento.
- Pode confundir a existência de um registro de recebimento com o início efetivo da custódia.
- Cria risco de material fisicamente recebido permanecer sem custódia registrada enquanto o rascunho não é confirmado.
- Exige regras específicas para quem pode editar, confirmar, cancelar e expirar o rascunho.
- Aumenta a complexidade de concorrência, auditoria e idempotência.
- Pode conflitar com a regra de um único recebimento principal se rascunhos abandonados forem tratados como recebimentos reais.

**Avaliação:** não recomendada como modelo padrão da primeira entrega. Poderá ser reavaliada apenas se houver necessidade operacional comprovada de preparação persistente pré-chegada.

### Alternativa C — Formalização única da chegada, seguida de salvamento progressivo da conferência

A chegada física é formalizada em um comando único e atômico, que cria o recebimento principal, representa todos os itens declarados, registra quais foram apresentados e inicia a custódia dos materiais apresentados. A conferência detalhada, checklist, evidências, pendências e decisões são salvos progressivamente em operações próprias, sem recriar o recebimento.

**Vantagens**
- A custódia começa no momento em que a chegada é formalizada, sem aguardar checklist ou decisão.
- Evita Receipt parcialmente criado, com itens omitidos ou eventos iniciais faltantes.
- Preserva a regra de um recebimento principal por solicitação.
- Permite que a conferência seja realizada em etapas, retomada e distribuída entre usuários autorizados.
- Separa os fatos de chegada dos atos posteriores de conferência, validação e aceite.
- Mantém o fluxo coerente com as duas telas da UI-LIMS-001.

**Desvantagens**
- Exige definir com precisão quais dados mínimos são obrigatórios para formalizar a chegada.
- Requer idempotência e controle de concorrência no comando de formalização.
- Exige operações de gravação independentes e auditáveis para checklist, evidências, pendências e decisões.

**Avaliação:** recomendada.

## 4. Recomendação

Adotar a **Alternativa C** como desenho-base da primeira entrega:

> O recebimento físico principal deve ser formalizado por um único comando transacional. Depois da formalização, conferências, checklists, evidências, pendências, regularizações e decisões devem ser salvos progressivamente, por item, sem criar outro recebimento e sem alterar retroativamente os fatos da chegada.

A recomendação não significa que todo o processo de conferência precise estar concluído no momento da chegada. Significa apenas que o fato da chegada e a custódia inicial devem ser registrados de forma íntegra e atômica.

## 5. Separação entre preparação, chegada e conferência

### 5.1 Preparação não formalizada

A interface pode permitir que o usuário selecione a solicitação e prepare informações antes de confirmar a chegada. Essa preparação não constitui `Receipt`, não altera o estado oficial da solicitação e não inicia custódia.

Para a primeira entrega, recomenda-se não persistir um objeto de domínio `Receipt` em estado de rascunho. O conteúdo ainda não formalizado pode permanecer como formulário de interface até a confirmação. Se houver requisito de salvamento pré-chegada entre sessões ou usuários, deverá ser aberto requisito próprio e avaliado sem confundir o rascunho com o recebimento principal.

### 5.2 Formalização da chegada

A ação explícita **“Registrar chegada”** deve executar uma única operação de domínio. O comando deve conter, no mínimo:

- solicitação válida e submetida;
- instante efetivo da chegada, com timezone explícito;
- recebedor físico real;
- local inicial de recebimento, conforme regra operacional;
- todos os itens declarados, cada um representado exatamente uma vez;
- situação de apresentação de cada item;
- quantidade apresentada e unidade, quando aplicável;
- dados mínimos necessários para criar os objetos de custódia dos itens apresentados, conforme DEC05/API03;
- informações gerais e evidências da chegada, quando exigidas pelo procedimento.

A identidade de quem registra o comando deve ser obtida da sessão autenticada. Ela não deve substituir automaticamente o recebedor físico.

O comando deve criar, atomicamente:

1. o `Receipt` principal;
2. todos os `ReceiptItems` correspondentes aos itens declarados;
3. os `CustodyObjects` aplicáveis aos itens apresentados, conforme granularidade aprovada;
4. o evento inicial de custódia de cada objeto, com a semântica definida na proposta API04;
5. os registros de auditoria necessários;
6. o vínculo e o estado oficial da solicitação.

Se qualquer validação ou gravação obrigatória falhar, nenhuma parte do recebimento formal deve permanecer persistida.

### 5.3 Conferência e decisões após a chegada

Depois da formalização, o sistema deve permitir salvar e retomar, por item:

- abertura e progresso da conferência;
- respostas do checklist versionado;
- observações e justificativas;
- anexação de evidências;
- pendências e regularizações;
- conclusão da conferência;
- decisão do conferente;
- encaminhamento e resposta da coordenação, quando exigidos;
- decisão final de aceite ou recusa.

Cada operação deve ter autoria, data/hora, versão e histórico próprios. O salvamento de um item não deve sobrescrever a conferência ou decisão de outro item.

A conclusão da conferência não cria, por si só, uma `DeviceSample`. A criação ocorre somente no aceite final, após validações obrigatórias, conforme o fluxo específico de aceite.

## 6. Dados mínimos e limite da formalização

A formalização não deve exigir que o checklist esteja concluído, nem que a decisão técnica esteja tomada.

Entretanto, deve exigir dados suficientes para que o sistema saiba:

- qual solicitação chegou;
- quando chegou;
- quem recebeu fisicamente;
- quais itens declarados chegaram e quais não chegaram;
- quais materiais apresentados passaram a estar sob custódia institucional;
- onde se iniciou a guarda, quando o procedimento exigir esse dado.

A classificação de apresentação e a reconciliação de quantidades devem respeitar API03 e DEC05. Como API03 ainda está pendente de validação, este documento não fixa regras finais de agrupamento, unidade de medida ou número de objetos por item.

Se a conferência física inicial identificar divergência de quantidade ou identidade, o recebimento deve registrar o fato observado e a divergência como pendência/ocorrência auditável. Não se deve omitir o item nem alterar silenciosamente a quantidade declarada.

## 7. Contrato HTTP conceitual

### 7.1 Comando de formalização

Manter como candidato um comando único, por exemplo:

`POST /api/v1/solicitations/{solicitation_id}/receipt`

A rota é ilustrativa e não é aprovada nesta proposta. O nome final pertence à API01.

Cabeçalhos conceituais:
- autenticação obrigatória;
- `Idempotency-Key` obrigatória;
- controle de concorrência conforme decisão API06;
- identificador de correlação, se suportado pela infraestrutura.

O payload deve representar todos os itens declarados exatamente uma vez. A forma final dos objetos, quantidades e agrupamentos depende de API03.

### 7.2 Consulta e retomada

Após a formalização, a interface deve consultar o recebimento existente e recuperar seu estado persistido. A retomada não deve reenviar o comando de criação como se fosse um novo recebimento.

A consulta deve devolver:
- dados da chegada;
- recebedor físico;
- itens e estados individuais;
- objetos de custódia e situação corrente;
- progresso da conferência;
- pendências e evidências;
- decisões e validações;
- versão do recurso para controle de concorrência.

### 7.3 Salvamento progressivo

Operações de checklist, evidência, pendência, regularização e decisão devem possuir comandos próprios ou recursos versionados, conforme desenho posterior. Não devem ser implementadas como atualizações integrais do Receipt que substituam o documento completo a cada salvamento.

A escolha dos paths, verbos HTTP, códigos de resposta e schemas permanece pendente de API01, API05, API06, API07 e API10.

## 8. Idempotência, concorrência e tentativas repetidas

- A formalização deve ser idempotente para a mesma tentativa lógica, com política detalhada em API07.
- A unicidade do recebimento principal por solicitação deve ser garantida no banco, não apenas na interface.
- Se a mesma chave idempotente e o mesmo conteúdo forem reenviados, o sistema deve recuperar a resposta da operação original, conforme política API07.
- Se já existir recebimento para a solicitação e a requisição não for replay idêntico reconhecido, o sistema deve retornar conflito com referência ao recebimento existente, sem criar outro.
- Se dois usuários tentarem formalizar simultaneamente, apenas uma operação poderá vencer; a outra deverá receber resposta de conflito e a referência do registro criado.
- Se houver conflito de versão em alterações posteriores de conferência ou decisão, o sistema deve impedir sobrescrita silenciosa e permitir recarregar a versão atual.
- Uma falha de comunicação após o commit não pode induzir criação duplicada no reenvio.

Os detalhes de retenção, escopo e replay da chave pertencem à API07; o mecanismo único de versão pertence à API06.

## 9. Falhas e tratamento operacional

| Situação | Comportamento proposto |
|---|---|
| Falha antes do commit da formalização | Não deve existir recebimento parcial; permitir nova tentativa após corrigir a causa. |
| Resposta perdida após commit | Reenvio com a mesma chave deve recuperar o resultado original; não criar novo recebimento. |
| Solicitação já possui recebimento | Exibir o recebimento existente; bloquear nova criação. |
| Item declarado ausente na chegada | Registrar `NOT_PRESENTED`; não criar objeto de custódia nem amostra para material ausente. |
| Item apresentado com pendência | Formalizar chegada e custódia; manter conferência/decisão pendente até regularização ou desfecho. |
| Checklist incompleto | Permitir salvar rascunho da conferência; não impedir a formalização da chegada. |
| Falha ao salvar checklist depois da chegada | Preservar o recebimento e a custódia já formalizados; informar falha e permitir nova tentativa sem duplicar eventos de chegada. |
| Falha no aceite | Não criar amostra parcial; manter objeto sob custódia e decisão no estado válido anterior. |
| Usuário sem permissão | Rejeitar no backend; ocultar botão na interface não é controle suficiente. |

## 10. Alinhamento com as duas telas da UI-LIMS-001

### Tela 1 — Recebimento e conferência

1. Localizar solicitação submetida.
2. Exibir todos os itens declarados.
3. Registrar data/hora da chegada e recebedor físico.
4. Identificar apresentação e quantidade observada de cada item.
5. Executar a ação explícita **“Registrar chegada”**.
6. Após sucesso, exibir o recebimento oficial e a custódia iniciada.
7. Abrir o modal individual para preencher e salvar checklist, observações e evidências.
8. Permitir sair e retomar a conferência com base no estado persistido.

Antes da formalização, a tela deve indicar claramente que os dados ainda não constituem recebimento oficial. Após sucesso, deve indicar número/identificador do recebimento e bloquear a criação de um segundo recebimento principal.

### Tela 2 — Decisões e encerramento

1. Exibir o progresso e a situação individual de cada item.
2. Permitir formalizar decisão do conferente quando os requisitos estiverem atendidos.
3. Encaminhar casos à coordenação quando exigido.
4. Permitir registrar regularizações e novas decisões preservando o histórico.
5. Criar a amostra operacional somente após aceite final e validações obrigatórias.
6. Concluir administrativamente o recebimento apenas quando todos os itens e destinos de custódia atenderem às regras de encerramento.

A interface não deve apresentar o recebimento como integralmente concluído quando ainda houver material sob custódia sem destinação ou ação obrigatória pendente.

## 11. Compatibilidade com estados e domínio

A proposta é coerente com os estados conceituais existentes:

- Solicitação: `SUBMETIDA` → `RECEBIMENTO_REGISTRADO` após a formalização atômica.
- Recebimento: criado em `REGISTRADO`; evolui conforme conferência, regularização, validação e decisão dos itens.
- Item: todos os declarados recebem representação no recebimento; cada um é marcado como apresentado ou não apresentado.
- Custódia: inicia na chegada para os objetos dos materiais apresentados.
- Amostra operacional: criada somente após aceite final e validações obrigatórias.

O estado global do recebimento deve continuar derivado dos estados individuais, sem substituir a história de cada item.

## 12. Decisões e dependências ainda pendentes

| ID | Questão | Tratamento nesta proposta |
|---|---|---|
| API01 | Nome final dos recursos e rotas | Path sugerido é ilustrativo; não aprovado. |
| API03 | Quantidade, agrupamento e cardinalidade dos objetos | Dados mínimos dependem da proposta API03 e de sua validação. |
| API04 | Evento inicial, autoria e timestamps | Evento inicial deve acompanhar a formalização; semântica detalhada depende da validação API04. |
| API05 | Assinatura eletrônica por operação | Não presumir assinatura universal; definir por ato. |
| API06 | Controle de concorrência | Obrigatório, mecanismo único ainda pendente. |
| API07 | Idempotência | Obrigatória para formalização; política detalhada pendente. |
| API10 | Autorização e segregação de funções | Recebedor, conferente e validador dependem de matriz aprovada. |
| API12 | Datas retroativas e fuso | Aplicar política a definir; não permitir retrodatação livre. |
| DEC01/DEC02 | Cardinalidade e presença de todos os itens | Preservar uma representação por item declarado. |
| DEC04/DEC05 | Custódia e granularidade dos objetos | Preservar as diretrizes aprovadas para o desenho; formalização institucional pendente. |
| EST08 | Correções excepcionais | Preservar versões e eventos; mecanismo formal de retificação ainda pendente. |

## 13. Critérios para considerar API02 resolvida

API02 somente poderá ser marcada como resolvida após:

1. validação funcional de que a chegada será formalizada em comando único;
2. confirmação dos dados mínimos obrigatórios para formalização;
3. validação de que a conferência e as decisões serão salvas progressivamente após a chegada;
4. confirmação de que não haverá `Receipt` provisório persistido na primeira entrega, salvo requisito operacional adicional;
5. alinhamento do contrato HTTP com API01, API03, API04, API06 e API07;
6. confirmação de idempotência e unicidade sob concorrência;
7. revisão da interface de duas telas e dos estados;
8. aprovação institucional do procedimento de recebimento e custódia.

## 14. Controle de execução

**Realizado:** elaboração desta proposta documental, comparando comando único para todo o processo, rascunho persistente de recebimento e formalização única da chegada com conferência progressiva.

**Não realizado:** alteração da especificação HTTP existente, OpenAPI, modelo relacional, estados, interface, código, modelos ORM, banco, migrações, endpoints, frontend, testes, build ou CI.

**Estado:** a Alternativa C foi validada pelo responsável pelo projeto em revisão em 2026-11-10: formalização única da chegada física, seguida de salvamento progressivo da conferência, evidências, pendências e decisões. A validação não fecha integralmente API02: permanecem pendentes a confirmação dos dados mínimos, o alinhamento com API03/API04/API06/API07, a revisão da interface/estados e a aprovação institucional do procedimento. Não há autorização de implementação.

## 15. Histórico de alterações

| Versão | Data | Alteração |
|---|---|---|
| 0.1 | 2026-11-09 | Criação da proposta de formalização única da chegada com salvamento progressivo de conferência e decisões. |
| 0.2 | 2026-11-10 | Registro da validação da Alternativa C pelo responsável pelo projeto em revisão; dependências contratuais e aprovação institucional permanecem pendentes. |
