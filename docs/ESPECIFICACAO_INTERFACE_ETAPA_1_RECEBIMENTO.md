# Especificação de Interface — Etapa 1: Recebimento e Conferência

**Identificador:** UI-LIMS-001  
**Versão:** 0.1  
**Situação:** Proposta de interface para revisão funcional; não aprovada para implementação  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Data:** 2026-11-09

---

## 1. Objetivo

Consolidar a interface da Etapa 1 do LIMS para cadastro/consulta de solicitação, registro da chegada física, conferência dos itens, decisões individuais e encerramento administrativo do recebimento.

A proposta organiza o trabalho em **duas telas principais** e **uma janela modal de conferência por item**. A janela modal não é uma terceira tela nem representa uma etapa independente do processo.

Este documento detalha a experiência de uso, os componentes, as ações, as mensagens e os comportamentos esperados. Não autoriza desenvolvimento de frontend, backend, API, banco de dados, migrações ou implantação.

## 2. Premissas funcionais

1. A primeira entrega é de uso interno. Um usuário institucional cadastra a solicitação em nome do solicitante/representante; não há portal ou conta externa nesta etapa.
2. Uma solicitação pode conter vários itens declarados.
3. Cada solicitação admite no máximo um recebimento físico principal.
4. Uma segunda tentativa de registrar a chegada deve localizar e exibir o recebimento existente, sem criar outro.
5. Todos os itens declarados devem aparecer na relação do recebimento, inclusive os não apresentados.
6. Quantidade declarada e quantidade efetivamente apresentada são informações distintas.
7. Apresentação, conferência, decisão e custódia são dimensões diferentes e não devem ser condensadas em um único status.
8. Cada item apresentado tem conferência e decisão próprias.
9. Item não apresentado não gera custódia de material ausente nem amostra operacional.
10. A custódia do material apresentado começa na chegada física, antes da criação da amostra operacional.
11. A amostra operacional e seu identificador institucional só são criados após aceite final e validações obrigatórias.
12. Item recusado permanece sob custódia até devolução ou destinação autorizada efetivamente registrada.
13. O material entregue posteriormente e ausente na chegada original não pode ser incluído retroativamente nesse recebimento, salvo exceção institucional formal e auditável.
14. As duas telas permitem salvar o andamento e retomá-lo. Não constituem um assistente linear obrigatório.

## 3. Arquitetura de navegação

### Tela principal 1 — Recebimento e conferência

Responsável por:
- localizar e selecionar uma solicitação;
- apresentar os dados cadastrais essenciais;
- registrar a chegada física uma única vez;
- apresentar todos os itens declarados;
- registrar a condição de apresentação e quantidades;
- abrir a janela modal para conferência detalhada do item selecionado;
- acompanhar o estado da conferência e da custódia.

### Janela modal — Conferência do item

Abre sobre a Tela 1 para o item selecionado. Responsável por:
- apresentar a identificação do item e o contexto da solicitação/recebimento;
- carregar o checklist versionado aplicável;
- registrar respostas, observações, justificativas e evidências;
- salvar rascunho ou concluir a conferência;
- preservar histórico e alertar sobre alterações não salvas.

### Tela principal 2 — Decisões e encerramento

Responsável por:
- apresentar a situação individual de cada item;
- registrar decisão do conferente;
- encaminhar exceções à coordenação quando exigido;
- apresentar decisões da coordenação e pendências;
- exibir identificador institucional somente após a criação efetiva da amostra;
- apresentar resumo do recebimento e permitir conclusão administrativa quando os critérios forem atendidos.

## 4. Elementos comuns às duas telas

### 4.1 Cabeçalho de contexto

Exibir, de forma consistente:
- número da solicitação;
- identificação do solicitante/unidade de origem;
- tipo/finalidade da demanda;
- número do recebimento, quando criado;
- data/hora da chegada física;
- recebedor físico;
- estado global resumido do recebimento.

O cabeçalho deve permitir retornar à consulta/localização da solicitação sem perder alterações já salvas. Dados cadastrais de contato devem respeitar as permissões e a necessidade de acesso.

### 4.2 Indicadores de estado

Usar rótulos textuais, não apenas cores. Exemplos:
- Aguardando chegada;
- Apresentado;
- Não apresentado;
- Aguardando conferência;
- Em conferência;
- Pendente de regularização;
- Aguardando coordenação;
- Aceito;
- Recusado;
- Custódia ativa;
- Devolvido/destinação concluída.

Os estados globais de solicitação/recebimento devem ser exibidos separadamente dos estados de cada item. Não apresentar “recebimento aceito” quando existirem itens pendentes ou recusados sem deixar claro o resultado individual.

## 5. Tela principal 1 — Recebimento e conferência

### 5.1 Composição

**Área A — Localizar solicitação**
- campo de busca por número da solicitação;
- filtros adicionais autorizados, como solicitante, origem, período e estado;
- ação de pesquisar;
- lista de resultados com identificação suficiente para evitar seleção equivocada.

**Área B — Dados da chegada**
- solicitação selecionada;
- data/hora efetiva da chegada;
- recebedor físico;
- identificação de quem está registrando, quando diferente;
- observações gerais da entrega;
- condição geral da embalagem/transporte, quando aplicável;
- ação “Registrar chegada” antes da criação do recebimento;
- após o registro, exibir número/estado do recebimento e bloquear novo registro principal.

A data/hora da chegada deve representar o evento real. Não deve ser alterada para acomodar entrega posterior ou correção informal. Correção excepcional exige permissão, justificativa, histórico e auditoria.

**Área C — Relação de itens declarados**

Colunas recomendadas:

| Coluna | Conteúdo |
|---|---|
| Nº | Ordem/identificador visual do item na solicitação |
| Item | Descrição declarada do material/dispositivo |
| Fabricante/modelo | Quando informado |
| Lote/série | Quando aplicável; não presumir série obrigatória |
| Qtd. declarada | Quantidade informada na solicitação |
| Qtd. apresentada | Quantidade conferida na chegada |
| Apresentação | Aguardando chegada, apresentado ou não apresentado |
| Conferência | Não iniciada, em andamento ou concluída |
| Custódia | Situação resumida do material efetivamente apresentado |
| Ação | Conferir/consultar |

A grade deve listar todos os itens declarados. Item não apresentado permanece visível e deve ser explicitamente marcado, com justificativa quando exigida.

### 5.2 Ações da Tela 1

- **Registrar chegada:** cria o único recebimento principal da solicitação, com data/hora real e recebedor físico.
- **Marcar apresentado:** registra que o material foi efetivamente entregue e informa a quantidade apresentada.
- **Marcar não apresentado:** registra a ausência do item, sem criar custódia ou amostra.
- **Abrir conferência:** abre o modal para item apresentado.
- **Consultar histórico:** permite visualizar eventos e alterações já registrados, conforme permissão.
- **Salvar andamento:** preserva os dados não decisórios já preenchidos.

A interface não deve permitir que “não apresentado” seja confundido com “recusado”. A recusa é uma decisão posterior sobre material que foi apresentado.

### 5.3 Wireframe de referência

~~~text
┌──────────────────────────────────────────────────────────────────────────┐
│ LIMS / RECEBIMENTO E CONFERÊNCIA                                        │
├──────────────────────────────────────────────────────────────────────────┤
│ Solicitação [ SOL-2026-000145                         ] [Pesquisar]      │
│ Solicitante: Unidade solicitante     Origem: ...                         │
├──────────────────────────────────────────────────────────────────────────┤
│ CHEGADA FÍSICA                                                          │
│ Data/hora: [09/11/2026 09:15]  Recebedor: [Usuário autenticado      ]   │
│ Observações gerais: [______________________________________________]   │
│ [Registrar chegada]     Estado: RECEBIMENTO REGISTRADO                  │
├──────────────────────────────────────────────────────────────────────────┤
│ ITENS DA SOLICITAÇÃO                                                     │
│ Nº  Item       Qtd declarada  Qtd apresentada  Apresentação  Conferência │
│ 01  Agulha     10             10               Apresentado   Concluída   │
│ 02  Seringa    05             05               Apresentado   Em andamento│
│ 03  Equipo     02             —                Não apresentado —         │
│                                                                          │
│ [Conferir item] [Registrar não apresentado] [Consultar histórico]       │
├──────────────────────────────────────────────────────────────────────────┤
│ [Salvar andamento]                           [Ir para decisões →]       │
└──────────────────────────────────────────────────────────────────────────┘
~~~

Os valores são ilustrativos. A interface definitiva deverá refletir os campos e estados aprovados.

## 6. Janela modal — Conferência detalhada do item

### 6.1 Identificação e contexto

No topo, exibir:
- solicitação e recebimento;
- número/ordem do item;
- descrição e identificação declarada;
- quantidade apresentada;
- situação de custódia resumida;
- checklist aplicável e sua versão.

### 6.2 Conteúdo do checklist

Cada critério deve apresentar:
- código e descrição;
- classe/criticidade, quando definida;
- indicação de obrigatoriedade;
- resposta controlada: Conforme, Não conforme ou Não aplicável;
- campo de observação/justificativa, conforme regra;
- opção de anexar ou consultar evidência, quando aplicável.

Critérios não aplicáveis devem exigir justificativa quando assim definido na versão do checklist. Critérios obrigatórios sem resposta impedem a conclusão da conferência.

### 6.3 Evidências e histórico

A janela deve permitir:
- anexar evidência autorizada;
- consultar evidências já registradas;
- identificar autor e data/hora de cada resposta;
- distinguir rascunho, resposta salva e conferência concluída;
- preservar versões anteriores após regularização ou correção autorizada.

Não permitir apagar silenciosamente resposta ou evidência que já tenha integrado uma conferência formalizada.

### 6.4 Ações e fechamento

Ações:
- **Salvar rascunho:** grava o andamento sem concluir a conferência;
- **Concluir conferência:** valida obrigatoriedade e registra a versão avaliada;
- **Cancelar/Fechar:** retorna à Tela 1.

Se houver alteração não salva, solicitar confirmação antes de fechar. Fechar o modal não significa aceitar o item nem concluir o recebimento.

### 6.5 Comportamento para item não apresentado

Para item não apresentado:
- não carregar checklist técnico como se o material estivesse disponível;
- permitir registrar justificativa da ausência e evidência administrativa, quando aplicável;
- manter o item na relação;
- não criar objeto de custódia de material inexistente;
- não habilitar decisão de aceite/recusa técnica enquanto não houver apresentação física.

### 6.6 Wireframe de referência

~~~text
┌──────────────────────────────────────────────────────────────────────────┐
│ CONFERÊNCIA DO ITEM 02 — SERINGA                                  [ X ] │
│ Solicitação SOL-2026-000145 | Recebimento REC-... | Qtd. apresentada: 5 │
│ Checklist: SERINGAS — versão vigente                                   │
├──────────────────────────────────────────────────────────────────────────┤
│ Critério                         Resposta             Observação        │
│ C01 Identificação da embalagem   [Conforme ▼]         [___________]     │
│ C02 Integridade da embalagem     [Não conforme ▼]     [___________]     │
│ C03 Identificação do fabricante  [Conforme ▼]         [___________]     │
│ C04 Identificação do lote        [Não aplicável ▼]    [Justificativa]   │
│                                                                          │
│ Evidências: [Adicionar arquivo]  [Consultar evidências]                 │
│                                                                          │
│ Histórico de respostas: [Consultar]                                     │
├──────────────────────────────────────────────────────────────────────────┤
│ [Salvar rascunho]                          [Concluir conferência]       │
└──────────────────────────────────────────────────────────────────────────┘
~~~

Os critérios e textos do wireframe são exemplos, não checklist normativo aprovado.

## 7. Tela principal 2 — Decisões por item e encerramento

### 7.1 Composição

**Área A — Contexto do recebimento**
- número da solicitação e do recebimento;
- chegada física e recebedor;
- estado global do recebimento;
- quantidade de itens declarados e situação agregada.

**Área B — Grade de resultados individuais**

Colunas recomendadas:
- número/identificação do item;
- descrição;
- apresentação;
- estado da conferência;
- pendências/exceções abertas;
- situação da coordenação;
- decisão vigente;
- identificador institucional da amostra, se criada;
- ação disponível.

**Área C — Decisão do item selecionado**
- resultado: Aceitar, Manter pendente ou Recusar;
- justificativa obrigatória conforme regra;
- consulta ao checklist e evidências;
- indicação de critérios impeditivos;
- encaminhamento à coordenação, quando exigido;
- histórico de decisões e regularizações.

**Área D — Resumo e encerramento**
- quantidade de itens aceitos;
- quantidade pendente;
- quantidade recusada;
- quantidade não apresentada;
- quantidade aguardando coordenação;
- histórico de custódia e decisões;
- ação de conclusão administrativa, habilitada somente quando as regras de fechamento forem atendidas.

### 7.2 Regras de decisão

- Decisão é individual por item; não propagar uma decisão para os demais itens da solicitação.
- A decisão deve referenciar a conferência, checklist e versão efetivamente avaliados.
- Critério impeditivo não conforme bloqueia aceite.
- Exceção sujeita à coordenação mantém o item bloqueado até decisão formal.
- Coordenação pode aprovar, devolver para complementação ou rejeitar nos limites de sua competência; não pode dispensar critério impeditivo.
- Regularização gera nova avaliação e preserva histórico anterior.
- Item recusado continua sob custódia até devolução ou destinação autorizada efetivamente registrada.
- Item não apresentado não recebe decisão técnica de aceite/recusa.
- A criação da amostra e do identificador não é uma edição manual: é consequência transacional do aceite final.

### 7.3 Identificador institucional

- Não exibir identificador como se já existisse antes da criação da amostra.
- Não permitir digitação, edição ou escolha manual do identificador.
- Após a criação bem-sucedida, exibir o identificador institucional e permitir consulta à amostra.
- O formato e o papel definitivo de `accession_number` dependem da decisão DEC07 e da verificação de compatibilidade com QR Codes.

### 7.4 Wireframe de referência

~~~text
┌──────────────────────────────────────────────────────────────────────────┐
│ LIMS / DECISÕES E ENCERRAMENTO                                          │
├──────────────────────────────────────────────────────────────────────────┤
│ Solicitação: SOL-...   Recebimento: REC-...   Chegada: ...               │
├──────────────────────────────────────────────────────────────────────────┤
│ RESULTADO POR ITEM                                                       │
│ Nº  Item       Conferência     Coordenação       Decisão       Amostra   │
│ 01  Agulha     Concluída       Não exigida       Aceita         LIMS-... │
│ 02  Seringa    Concluída       Aguardando        Pendente       —        │
│ 03  Equipo     Não apresentado —                 Não se aplica  —        │
├──────────────────────────────────────────────────────────────────────────┤
│ ITEM SELECIONADO: 02 — SERINGA                                          │
│ Decisão: ( ) Aceitar  ( ) Manter pendente  ( ) Recusar                   │
│ Justificativa: [____________________________________________________]    │
│ [Consultar checklist/evidências] [Histórico]                             │
│ Encaminhamento: [Salvar decisão] [Submeter à coordenação]                │
├──────────────────────────────────────────────────────────────────────────┤
│ RESUMO: 1 aceito | 1 aguardando coordenação | 1 não apresentado          │
│ [Histórico de custódia] [Histórico de decisões]                          │
│ [Concluir etapa]                                                         │
└──────────────────────────────────────────────────────────────────────────┘
~~~

Dados ilustrativos. O botão “Concluir etapa” deve permanecer desabilitado enquanto houver condições impeditivas ou pendências que impeçam o encerramento segundo regra aprovada.

## 8. Custódia na interface

A custódia começa na chegada física, antes da criação da amostra operacional.

A interface deve permitir consultar:
- data/hora efetiva de início;
- responsável pelo recebimento físico;
- localização/condição inicial de guarda;
- transferências posteriores;
- responsável que entrega e que recebe;
- data/hora efetiva da transferência;
- situação atual e destinação final.

O conceito de ObjetoCustodia está em avaliação no modelo de domínio. A interface não deve pressupor que toda unidade física terá registro individual: o agrupamento homogêneo pode ser permitido quando validado pelo procedimento técnico. A quantidade e o critério de agrupamento devem ser transparentes.

Quando a amostra operacional for criada, a interface deve mostrar continuidade entre custódia pré-amostra e custódia laboratorial, sem reiniciar ou reescrever o histórico.

## 9. Salvamento, retomada e concorrência

- Rascunhos e respostas em andamento podem ser salvos sem formalizar decisão.
- A interface deve informar claramente “salvo”, “alterações não salvas” ou “falha ao salvar”.
- A retomada deve recuperar a última versão persistida e apresentar autoria/data/hora.
- Se outro usuário tiver alterado o registro, detectar conflito e impedir sobrescrita silenciosa.
- Decisões formais, aceite, recusa, validação e encerramento exigem ação explícita e confirmação.
- Reenvio de operação de aceite não pode gerar nova amostra nem novo identificador.
- Falhas de rede não podem ser apresentadas como sucesso.
- O backend permanece responsável pela validação final; a interface apenas orienta e apresenta o resultado.

## 10. Permissões e visibilidade

Os controles devem ser apresentados conforme permissões efetivas retornadas pelo backend. Ocultar um botão não substitui autorização no servidor.

A matriz definitiva depende de EST01–EST03 e EST10. Como regra de interface:
- usuário sem permissão pode consultar apenas o que seu perfil/atribuição permitir;
- recebedor registra chegada e dados físicos conforme designação;
- conferente registra checklist e decisão inicial quando autorizado;
- coordenação visualiza fila e decide apenas os casos formalmente encaminhados;
- administrador técnico não recebe automaticamente competência para decidir tecnicamente;
- auditor consulta trilhas e evidências conforme escopo, sem alterar registros.

Não presumir equivalência automática entre perfis existentes (ADMIN, FISCAL, TECNICO, CUSTODIANTE e AUDITOR) e funções propostas.

## 11. Requisitos de usabilidade, acessibilidade e responsividade

- Interface responsiva para as resoluções institucionais suportadas.
- Modal amplo, com rolagem interna e cabeçalho/ações identificáveis.
- Rótulos textuais para estados; cor nunca como único indicador.
- Campos obrigatórios identificados antes do envio.
- Mensagens de erro próximas ao campo e resumo dos erros no topo quando houver muitos.
- Confirmação explícita para ações irreversíveis ou formais.
- Preservar contexto ao alternar entre as telas.
- Navegação por teclado e foco visível.
- Contraste, tamanho de fonte e alvos de interação adequados.
- Tabelas devem oferecer alternativa de visualização em telas estreitas, sem ocultar dados essenciais.
- Evitar mensagens técnicas internas, stack traces ou detalhes de banco ao usuário.

## 12. Mensagens e bloqueios recomendados

| Situação | Mensagem/Comportamento |
|---|---|
| Solicitação já possui recebimento | “Esta solicitação já possui recebimento registrado. Consulte o registro existente.” |
| Item não apresentado | “O item foi registrado como não apresentado. Não será aberta conferência técnica nem criada amostra.” |
| Checklist incompleto | “Existem critérios obrigatórios sem resposta. Conclua a conferência antes de registrar a decisão.” |
| Critério impeditivo não conforme | “O aceite está bloqueado por critério impeditivo não conforme.” |
| Validação da coordenação pendente | “O item aguarda validação da coordenação e não pode ser aceito neste momento.” |
| Alteração concorrente | “Este registro foi alterado por outro usuário. Atualize os dados antes de continuar.” |
| Falha ao salvar | “Não foi possível salvar. Os dados não foram confirmados; tente novamente.” |
| Amostra criada | Exibir o identificador institucional retornado pelo servidor, sem gerar outro na interface. |
| Tentativa de entrega posterior | Informar que material ausente na chegada original exige nova solicitação ou exceção formal aprovada. |

## 13. Critérios de aceite da interface

| ID | Critério verificável | Evidência esperada |
|---|---|---|
| UI01 | As duas telas principais compartilham o contexto da solicitação/recebimento. | Roteiro de navegação. |
| UI02 | A primeira tela localiza a solicitação e lista todos os itens declarados. | Teste com solicitação de múltiplos itens. |
| UI03 | A chegada física pode ser registrada uma única vez. | Teste de repetição e concorrência. |
| UI04 | A segunda tentativa de recebimento exibe o existente sem duplicar registros. | Teste funcional/API. |
| UI05 | Quantidade declarada e apresentada são visualmente distintas. | Teste com divergência de quantidade. |
| UI06 | Item não apresentado permanece visível e não abre conferência técnica como apresentado. | Teste de estado. |
| UI07 | A conferência detalhada abre em modal e retorna à lista sem perda de contexto. | Teste de interface. |
| UI08 | O modal permite checklist, justificativas, observações e evidências. | Teste funcional. |
| UI09 | Alterações não salvas geram aviso antes de fechar. | Teste de interação. |
| UI10 | A segunda tela mostra decisões individuais e estados de cada item. | Teste com resultados mistos. |
| UI11 | Critério impeditivo bloqueia aceite; a interface não oferece atalho para contorná-lo. | Teste negativo e autorização no backend. |
| UI12 | A coordenação só recebe casos encaminhados e não pode dispensar impeditivo. | Teste por perfil. |
| UI13 | O identificador aparece somente após a criação efetiva da amostra. | Teste de fluxo transacional. |
| UI14 | O histórico de custódia, decisões e regularizações pode ser consultado. | Teste de rastreabilidade. |
| UI15 | É possível salvar e retomar o andamento sem sobrescrita silenciosa. | Teste de persistência e concorrência. |
| UI16 | A interface funciona nas resoluções suportadas e é operável por teclado. | Testes responsivos e de acessibilidade. |

## 14. Decisões ainda necessárias

A interface pode ser revisada visualmente, mas os seguintes pontos devem ser resolvidos antes do congelamento do desenho:

| Referência | Decisão pendente | Impacto na interface |
|---|---|---|
| DEC04 | Estrutura final da custódia pré-amostra e vínculo com amostra | Linha do tempo e painel de custódia |
| DEC05 | Granularidade item/unidade/agrupamento/amostra/corpo de prova | Grade, quantidades e detalhamento |
| DEC07 | Papel definitivo de `accession_number` e formato do identificador | Exibição do identificador e QR |
| EST01–EST03 | Perfis, recebedor/conferente e situações que exigem coordenação | Ações disponíveis e encaminhamentos |
| EST04 | Destino de material recusado | Ações de custódia e encerramento |
| EST05 | Fechamento do recebimento com itens não apresentados | Habilitação do encerramento |
| EST06 | Critérios impeditivos, saneáveis e informativos | Bloqueios e mensagens |
| EST07 | Atos que exigem assinatura eletrônica | Confirmações e evidências |
| EST08–EST09 | Correções excepcionais e prazos de pendência | Histórico e alertas |
| EST10 | Segregação de funções e autoaprovação | Visibilidade e autorização |

## 15. Próxima atividade recomendada

Após revisão funcional desta especificação:
1. validar os wireframes com usuários que executam recebimento e conferência;
2. validar exemplos de materiais e quantidades para resolver DEC05;
3. confirmar perfis e regras de encaminhamento à coordenação;
4. alinhar a interface com o modelo relacional e os contratos de API;
5. consolidar critérios de aceite e submeter o pacote ao portão G0.

A implementação permanece bloqueada até aprovação institucional do escopo/desenho e autorização específica.

## 16. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-09 | Consolidação da interface em duas telas principais e modal de conferência por item. |
