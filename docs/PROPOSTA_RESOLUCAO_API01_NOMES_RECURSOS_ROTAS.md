# Proposta de Resolução API01 — Nomes de Recursos e Rotas HTTP

**Identificador:** PROP-LIMS-API01-001  
**Versão:** 0.1  
**Situação:** Proposta técnica para revisão; validação funcional/arquitetural pendente — bloqueadora  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Data:** 2026-11-10

---

## 1. Objetivo e limites

Resolver documentalmente a decisão API01 da matriz `MAT-LIMS-API-001`: padronizar os nomes públicos dos recursos e a estrutura das rotas HTTP do fluxo de solicitação, recebimento e custódia.

A análise considera a especificação funcional da API v0.1, o OpenAPI 3.1 v0.1, a interface UI-LIMS-001 e o modelo relacional MOD-REL-001 v0.3.

Este documento é uma proposta. Não altera nem aprova automaticamente os contratos existentes. Não autoriza alterações em código, endpoints, frontend, OpenAPI, banco de dados ou migrações. Rotas legadas devem permanecer preservadas até decisão formal e plano de compatibilidade.

## 2. Problema identificado

A proposta atual já apresenta uma estrutura relativamente coerente, mas algumas escolhas precisam ser explicitadas para evitar renomeações posteriores:

- recursos principais usam nomes no plural: `solicitations`, `receipts` e `samples`;
- o recebimento principal é um recurso singular subordinado à solicitação: `/solicitations/{solicitation_id}/receipt`;
- objetos de custódia são organizados sob o agrupador `/custody/objects`;
- o histórico é exposto como sub-recurso de leitura: `/history`;
- transferências são uma coleção de eventos: `/transfers`;
- o aceite é exposto como sub-recurso singular: `/acceptance`;
- rotas legadas usam convenções anteriores, por exemplo `/custody/transfer` e `/custody/{sample_id}/history`.

A coexistência dessas formas não é, por si só, um erro. O ponto a resolver é estabelecer uma convenção para as rotas novas e impedir que uma padronização cosmética provoque quebra dos consumidores legados.

## 3. Convenção recomendada

Adotar as seguintes regras para novos contratos:

1. **Recursos em substantivos, sem verbos de ação no path.** A operação é expressa pelo método HTTP e pelo recurso/sub-recurso.
2. **Coleções no plural.** Exemplos: `/solicitations`, `/receipts`, `/samples`, `/transfers`.
3. **Recurso subordinado singular quando a cardinalidade for 1:1 ou no máximo um.** Exemplo: uma solicitação possui no máximo um recebimento principal; por isso `/solicitations/{solicitation_id}/receipt` é semanticamente adequado.
4. **Sub-recurso de coleção no plural.** Exemplo: um objeto de custódia pode ter vários eventos de transferência; usar `/transfers`.
5. **Sub-recurso singular para resultado/ato único.** Exemplo: `/acceptance`, desde que o contrato represente o ato/resultado de aceite do objeto e não uma coleção de tentativas.
6. **Sub-recursos de consulta com substantivos estáveis.** `/history` e, se mantido, `/timeline` representam visões de leitura; não devem criar eventos nem produzir efeitos colaterais.
7. **Identificadores no path em snake_case**, seguindo o padrão de parâmetros já proposto: `{solicitation_id}`, `{receipt_id}`, `{custody_object_id}`, `{sample_id}`.
8. **Sem barra final**, salvo se o padrão global efetivo da aplicação determinar o contrário.
9. **Método HTTP com semântica consistente:** GET para consulta sem efeito colateral; POST para criação de recursos/eventos ou comandos transacionais; não usar GET para formalizar recebimento, aceite ou transferência.
10. **Agrupamento por domínio somente quando agregar significado.** Manter `/custody/objects` como coleção de objetos do domínio de custódia; não alternar sem motivo entre `/custody/objects` e `/custody-objects`.

## 4. Catálogo de rotas novas recomendado

A proposta recomenda manter, como nomenclatura candidata canônica, as rotas novas já descritas na especificação funcional e no OpenAPI v0.1:

| Recurso/propósito | Método | Rota candidata | Justificativa |
|---|---|---|---|
| Formalizar chegada e criar recebimento principal | POST | `/api/v1/solicitations/{solicitation_id}/receipt` | Relação 1:0..1 entre solicitação e recebimento principal; o path identifica o contexto e evita criar recebimento órfão. |
| Consultar recebimento da solicitação | GET | `/api/v1/solicitations/{solicitation_id}/receipt` | Consulta o recurso singular associado; retorna 404 quando ainda não existe. |
| Consultar recebimento por identificador | GET | `/api/v1/receipts/{receipt_id}` | Acesso direto ao recurso pela sua identidade própria. |
| Consultar histórico do objeto de custódia | GET | `/api/v1/custody/objects/{custody_object_id}/history` | Histórico é uma visão de leitura subordinada ao objeto, válida antes e depois da criação da amostra. |
| Registrar transferência de custódia | POST | `/api/v1/custody/objects/{custody_object_id}/transfers` | Cada transferência cria um evento; a coleção é plural e admite múltiplos registros ao longo do tempo. |
| Formalizar aceite do objeto | POST | `/api/v1/custody/objects/{custody_object_id}/acceptance` | Representa o ato/resultado singular de aceite que pode criar no máximo uma amostra operacional. |
| Consultar timeline do objeto (opcional) | GET | `/api/v1/custody/objects/{custody_object_id}/timeline` | Visão agregada de leitura; opcional, não substitui o histórico mínimo de custódia. |

O catálogo não resolve os payloads, códigos HTTP, idempotência, concorrência, assinatura ou cardinalidade de objetos. Esses pontos permanecem nas decisões API02–API12 e nos documentos próprios.

## 5. Nomes dos recursos e correspondência com o domínio

| Conceito de domínio | Nome lógico proposto | Nome de coleção/rota | Observação |
|---|---|---|---|
| Solicitação | Solicitation | `solicitations` | Demanda formal anterior à chegada. |
| Item declarado | SolicitationItem | Incorporado à representação da solicitação | Não criar rota própria na primeira versão sem necessidade de consulta/manutenção independente. |
| Recebimento principal | Receipt | `receipts`; relação singular `solicitations/{id}/receipt` | Um por solicitação, conforme regra funcional. |
| Item de recebimento | ReceiptItem | Incorporado ao recurso `receipts` | Conferência e decisão individual; rota própria somente se caso de uso justificar. |
| Objeto de custódia | CustodyObject | `custody/objects` | Unidade de guarda/rastreabilidade; não confundir com amostra operacional. |
| Evento de custódia | ChainOfCustody / evento | Histórico e coleção de `transfers` | Preservar a cadeia única e a semântica definida em DEC04/API04. |
| Amostra operacional | DeviceSample | `samples` | Recurso existente; não renomear nem confundir com solicitação ou objeto. |
| Aceite | Acceptance | Sub-recurso singular `acceptance` | A decisão e sua cardinalidade ainda dependem das regras funcionais/EST. |

Os nomes lógicos em inglês acompanham a convenção técnica já presente no código e nos contratos propostos. A interface pode apresentar rótulos em português sem alterar os identificadores públicos da API.

## 6. Compatibilidade com rotas legadas

As rotas existentes não devem ser renomeadas, removidas, redirecionadas ou ter método, payload, status, cabeçalhos ou semântica alterados como parte da resolução API01.

Permanecem fora do escopo de renomeação, entre outras rotas legadas já identificadas:

- `POST /api/v1/samples`;
- `GET /api/v1/samples`;
- `GET /api/v1/samples/{sample_id}`;
- `POST /api/v1/custody/transfer`;
- `GET /api/v1/custody/{sample_id}/history`;
- `GET /api/v1/samples/{sample_id}/custody`;
- `GET /api/v1/samples/{sample_id}/timeline`;
- rotas existentes de QR Code.

A listagem acima é ilustrativa e não substitui inventário completo do runtime. O contrato efetivo de cada rota legada deverá ser confirmado no código e nos schemas atuais antes de ser reproduzido no OpenAPI.

Não se recomenda criar aliases automáticos para rotas POST legadas: redirecionamentos e aliases podem alterar comportamento de clientes, autenticação, idempotência, assinatura e tratamento de respostas. Se uma rota legada vier a ser descontinuada, isso exige decisão própria, versionamento, comunicação, período de convivência e evidência de migração dos consumidores.

## 7. Alternativas consideradas

### Alternativa A — Renomear todas as rotas para uma convenção REST uniforme

Exemplo: migrar tudo para coleções no plural e nomes uniformes, incluindo as rotas existentes.

**Não recomendada.** A uniformidade estética não justifica breaking changes em endpoints já consumidos. Exigiria inventário completo dos clientes, versionamento ou aliases e plano de descontinuação. Não é necessária para estabilizar os novos contratos.

### Alternativa B — Manter todas as rotas propostas sem registrar convenção

**Não recomendada.** Embora o conjunto atual seja em grande parte compreensível, a ausência de regras explícitas permite que novas rotas usem verbos, plurais/singulares inconsistentes ou hierarquias concorrentes.

### Alternativa C — Congelar uma convenção para rotas novas e preservar integralmente as legadas

**Recomendada.** Mantém as rotas novas já documentadas como candidatas canônicas, explica o uso de singular/plural pela cardinalidade e pelo tipo de sub-recurso, e impede renomeação retroativa das rotas legadas.

## 8. Regras de nomenclatura para erros, operações e parâmetros

- `operationId` deve ser único, estável, em lowerCamelCase e orientado à operação/recurso, por exemplo `createSolicitationReceipt`, `getReceipt`, `getCustodyObjectHistory`, `createCustodyObjectTransfer` e `acceptCustodyObject`.
- Tags OpenAPI devem agrupar operações por domínio funcional: `Solicitações`, `Recebimento`, `Custódia`, `Amostras` e `Compatibilidade legada`. A separação final depende da organização aprovada da API; tags não alteram paths.
- Parâmetros de path devem identificar o recurso, não o papel do usuário ou um dado mutável.
- Nomes JSON continuam em snake_case, conforme convenção já proposta; não misturar camelCase no corpo.
- Códigos de erro devem ser estáveis, em UPPER_SNAKE_CASE, e descrever condição de domínio, não detalhes internos.
- O idioma da rota e dos campos permanece inglês técnico; rótulos, mensagens humanas e interface podem ser em português.
- Não criar rota para cada tabela do banco. A API deve expor recursos e operações de domínio, não espelhar mecanicamente o modelo relacional.

## 9. Dependências e decisões que permanecem abertas

API01 pode ser considerada tecnicamente encaminhada quanto à nomenclatura geral, mas o fechamento integral depende de:

- API02: formalização única da chegada e seus comandos;
- API03: quantidade, agrupamento e cardinalidade dos objetos;
- API04: catálogo de eventos e semântica de autoria/timestamps;
- API05: assinatura por operação;
- API06: mecanismo de concorrência;
- API07/API09: idempotência e comportamento do aceite repetido;
- API08: payload mínimo de DeviceSample;
- API10: autorização e segregação de funções;
- API11/API12: paginação, snapshot e datas/fuso;
- confirmação do inventário runtime das rotas legadas.

A resolução de API01 não implica que o contrato esteja pronto para implementação. Em especial, nomes de rotas não resolvem semântica de operação, autorização, estados, cardinalidade ou compatibilidade.

## 10. Recomendação final

Adotar a Alternativa C: manter como candidatas canônicas as rotas novas já presentes na especificação v0.1 e aplicar as convenções das seções 3 e 8; preservar integralmente as rotas legadas; não introduzir aliases nem renomeações retroativas nesta etapa.

Após validação funcional/arquitetural, atualizar de forma coordenada a especificação funcional e o OpenAPI, registrando a versão e a decisão aprovada. Até lá, os paths permanecem propostas documentais.

## 11. Controle de execução

**Realizado:** recuperação da decisão API01 na matriz vigente; comparação documental entre especificação de API, OpenAPI, interface e modelo relacional; elaboração desta proposta.

**Não realizado:** alteração de código, modelos, banco de dados, migrações, endpoints, frontend ou OpenAPI; execução de testes, build, CI ou validação automática; alteração de rotas legadas.

**Situação:** proposta validada pelo responsável pelo projeto em revisão em 2026-11-10, como diretriz de nomenclatura e organização das novas rotas. A validação mantém a preservação integral dos contratos legados e não autoriza aliases, renomeações ou alterações retroativas. Permanece pendente a conferência técnica final do inventário runtime e dos contratos legados antes de atualizar a especificação/OpenAPI ou considerar implementação. Esta decisão de revisão do projeto não equivale a aprovação institucional nem a autorização de implementação.

## 12. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-10 | Primeira proposta de padronização de recursos e rotas HTTP, com convenção para rotas novas e preservação de compatibilidade legada. |
| 0.2 | 2026-11-10 | Registro da validação pelo responsável pelo projeto em revisão; conferência runtime e aprovação institucional permanecem pendentes. |
