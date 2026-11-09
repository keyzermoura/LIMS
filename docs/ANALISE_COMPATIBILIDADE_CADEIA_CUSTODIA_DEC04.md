# Análise de Compatibilidade da Cadeia de Custódia — DEC04

**Identificador:** ANL-LIMS-CUST-001  
**Versão:** 0.2  
**Situação:** Análise técnica documental; recomendação para revisão arquitetural. Não aprovada para implementação.  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Data:** 2026-11-09

---

## 1. Objetivo

Inspecionar a implementação existente de DeviceSample e ChainOfCustody para avaliar como acomodar as diretrizes DEC04/DEC05 aprovadas para o desenho do projeto:

- a custódia começa na chegada física, antes do aceite e da criação da amostra operacional;
- ObjetoCustodia é a unidade de guarda e rastreabilidade;
- cada ObjetoCustodia pode originar no máximo uma DeviceSample;
- os eventos novos devem permanecer em uma única cadeia cronológica, sem duplicação do evento de chegada;
- registros legados devem continuar consultáveis, sem associação retroativa presumida.

Esta análise é documental e estática. Não foram alterados código, modelos, banco, migrações, API, frontend ou infraestrutura. Nenhum teste foi executado nesta atividade.

## 2. Escopo e fontes inspecionadas

Arquivos consultados na branch main:

| Área | Arquivo |
|---|---|
| Modelo de amostra | backend/app/models/device_sample.py |
| Modelo de custódia | backend/app/models/chain_of_custody.py |
| Registro dos modelos | backend/app/models/__init__.py |
| Serviço de amostras | backend/app/services/sample_service.py |
| Serviço de custódia | backend/app/services/custody_service.py |
| Rotas de amostras | backend/app/api/v1/routes/samples.py |
| Rotas de custódia | backend/app/api/v1/routes/custody.py |
| Schemas API | backend/app/schemas/sample.py |
| Migração inicial | backend/alembic/versions/a1cd5ac5805f_schema_inicial.py |
| Guardas PostgreSQL | backend/alembic/versions/0002_guards.py |
| SQL de imutabilidade | backend/app/db/sql/001_immutability.sql |
| SQL de índices | backend/app/db/sql/002_indexes.sql |
| Inicialização de banco | backend/app/db/database.py |
| Testes de fluxo | backend/tests/test_api_flow.py |
| Testes de guardas PostgreSQL | backend/tests/test_postgres_guards.py |
| Fixtures de teste | backend/tests/conftest.py |
| Tipos frontend | frontend/src/lib/types.ts |
| Painel frontend | frontend/src/pages/Dashboard.tsx |
| Tela de ensaios | frontend/src/pages/Tests.tsx |
| Trilha de auditoria | frontend/src/pages/AuditTrail.tsx |

A inspeção representa os arquivos versionados consultados. Não equivale a uma execução do sistema nem a uma inspeção de banco de dados implantado.

## 3. Situação técnica encontrada

### 3.1 DeviceSample

O modelo atual:

- usa a tabela device_samples e chave primária UUID;
- possui accession_number obrigatório, único e indexado;
- exige serial_number, lot_number, manufacturer e commercial_name;
- possui restrição única composta por serial_number, lot_number e manufacturer;
- exige received_at e received_by_id;
- mantém current_custodian_id e current_location diretamente na amostra;
- não possui FK para ObjetoCustodia;
- não declara relacionamento ORM com ChainOfCustody.

A restrição de identidade serial/lote/fabricante e a obrigatoriedade de número de série precisam ser reavaliadas à luz da DEC05. A diretriz aprovada não exige serial para todo material e admite objetos agrupados. Não se deve alterar esses campos sem avaliar os registros atuais, as regras de duplicidade, as consultas e os contratos de API.

### 3.2 ChainOfCustody

O modelo atual usa a tabela chain_of_custody. Cada evento contém:

- device_sample_id obrigatório, FK para device_samples com ON DELETE RESTRICT;
- from_custodian_id opcional;
- to_custodian_id obrigatório;
- transferred_at obrigatório;
- reason obrigatório;
- location_from opcional e location_to obrigatório;
- seal_number opcional;
- signature_id opcional;
- notes opcional.

A documentação do modelo estabelece que from_custodian_id é nulo apenas no evento inicial de recebimento. A tabela possui índice de consulta por amostra e instante de transferência.

O modelo não possui campo ou FK para ObjetoCustodia. Portanto, hoje não é possível registrar um evento de custódia antes de existir DeviceSample.

### 3.3 Criação atual da amostra

O serviço sample_service.create_sample executa, em uma mesma unidade transacional:

1. verifica ID e duplicidade pela combinação serial/lote/fabricante;
2. gera accession_number;
3. cria DeviceSample;
4. define received_by_id e custodiante inicial como o usuário que executou a criação;
5. cria o evento inicial ChainOfCustody com from_custodian_id nulo e device_sample_id preenchido;
6. vincula a assinatura ao snapshot da amostra e do evento;
7. grava auditoria e confirma a transação.

Esse fluxo é coerente com o desenho atual, no qual recebimento e criação da amostra acontecem juntos. Não atende à diretriz nova, na qual a chegada física e a custódia antecedem conferência, aceite e criação da amostra.

### 3.4 Transferência atual

custody_service.transfer:

- localiza e bloqueia DeviceSample com SELECT FOR UPDATE;
- verifica status e versão otimista;
- verifica se o ator pode transferir a guarda;
- cria ChainOfCustody referenciada diretamente à amostra;
- atualiza current_custodian_id, current_location e version na DeviceSample;
- vincula assinatura, registra auditoria e confirma a transação.

A operação não pode ser reutilizada diretamente para um ObjetoCustodia ainda sem DeviceSample, pois depende de identificador, status, versão e estado corrente da amostra.

### 3.5 Histórico e timeline

As consultas atuais de histórico filtram ChainOfCustody.device_sample_id. A timeline de amostra também consulta apenas eventos associados diretamente a device_sample_id.

Consequência: mesmo que um evento pré-amostra fosse gravado em outra entidade, as rotas atuais de histórico da amostra não o recuperariam automaticamente. A timeline deverá combinar eventos legados ligados diretamente à amostra e eventos novos ligados ao ObjetoCustodia associado à amostra.

Há ainda um detalhe atual a revisar futuramente: o evento RECEIPT sintético da timeline usa sample.current_location, que pode representar a localização atual após transferências, e não necessariamente o local original da chegada. O evento inicial da ChainOfCustody já guarda location_to do recebimento. A fonte de localização histórica do evento RECEIPT deve ser definida para evitar apresentação incorreta.

## 4. Migrações, triggers e ambientes

### 4.1 Estrutura física atual

A migração inicial define chain_of_custody.device_sample_id como NOT NULL, com FK para device_samples e ON DELETE RESTRICT. Também cria índices para device_sample_id, custodiante de origem/destino e transferred_at.

A alteração necessária para suportar eventos pré-amostra não é apenas adicionar uma FK: o vínculo legado obrigatório com DeviceSample precisa tornar-se opcional para novos eventos ligados a ObjetoCustodia, preservando os registros existentes. Além disso, o modelo lógico CustodyEvent prevê event_type e recorded_by_id, mas esses campos não existem hoje em ChainOfCustody; sua inclusão e obrigatoriedade para eventos novos precisam ser definidas no mapeamento físico. O campo atual transferred_at corresponde ao instante do evento e created_at pode servir como instante de registro.

### 4.2 Imutabilidade

A migração 0002_guards.py instala trigger append-only que bloqueia UPDATE e DELETE em chain_of_custody. O arquivo 001_immutability.sql contém a mesma proteção para ambientes que inicializam o schema por metadata e scripts SQL.

A extensão da tabela deve preservar a natureza append-only dos eventos. Correções de eventos formais devem ser representadas por retificação ou evento compensatório, conforme regra institucional; não se deve desativar a proteção para permitir edição retroativa.

### 4.3 Diferença entre produção e testes

Em produção, a configuração documentada usa Alembic para aplicar schema e guardas antes da API subir. No fluxo de teste, conftest.py cria tabelas pelo metadata SQLAlchemy e instala 001_immutability.sql e 002_indexes.sql em PostgreSQL. Em SQLite, os testes criam o metadata sem triggers PL/pgSQL.

Assim, qualquer alteração física futura deverá manter alinhados:

1. modelo SQLAlchemy e metadata;
2. migração Alembic nova e aditiva;
3. scripts SQL usados no setup de teste/desenvolvimento, quando aplicável;
4. testes SQLite e PostgreSQL;
5. documentação do schema e plano de reversão.

A migração 0002 é um snapshot histórico das guardas e não deve ser reescrita para acomodar a nova estrutura. A alteração deve ser feita em uma nova migração, preservando o histórico de versões.

## 5. Contratos de API e frontend afetados

### 5.1 API

O contrato atual apresenta as seguintes dependências:

- POST /samples cria diretamente a amostra e exige assinatura vinculada à entidade DeviceSample;
- POST /custody/transfer recebe device_sample_id;
- GET /custody/{sample_id}/history consulta histórico por amostra;
- GET /samples/{sample_id}/custody também consulta histórico por amostra;
- GET /samples/{sample_id}/timeline consulta timeline vinculada à amostra;
- CustodyOut exige device_sample_id.

Para o novo fluxo, o contrato de evento precisará representar qual objeto está sendo custodiado. Recomenda-se preservar os endpoints e respostas legados durante a transição, acrescentando capacidade de consulta/transferência por ObjetoCustodia. O campo device_sample_id do schema de evento não poderá continuar obrigatório para os eventos novos que antecedem a amostra.

### 5.2 Assinatura e auditoria

A assinatura eletrônica atual é emitida e consumida vinculada a entity_type, entity_id e action. A criação inicial vincula a assinatura a DeviceSample; a transferência também é assinada no contexto da amostra.

No novo fluxo, a chegada ocorre antes da amostra. Portanto, o alvo da assinatura e o conteúdo do snapshot precisam corresponder ao ato efetivamente assinado (por exemplo, recebimento, item de recebimento ou objeto de custódia). A definição de quais atos exigem assinatura permanece condicionada à decisão EST07 e à governança institucional.

O AuditLog aceita entity_type e entity_id genéricos, mas os relatórios, filtros e rótulos de frontend devem reconhecer os novos tipos de entidade. Não se deve presumir que a flexibilidade técnica do AuditLog resolva, por si só, a semântica de auditoria.

### 5.3 Frontend

O Dashboard:

- cria DeviceSample diretamente;
- exige número de série e lote no formulário;
- solicita assinatura em nome de DeviceSample;
- consome a timeline por sample_id;
- transfere custódia enviando device_sample_id;
- exibe current_custodian e received_at da DeviceSample.

Os tipos TypeScript de CustodyEvent também exigem device_sample_id. O fluxo novo demandará ajustes futuros no contrato e na interface para permitir a visualização de objetos recebidos, pendentes ou recusados antes de existir amostra. Nenhum ajuste frontend foi feito nesta análise.

## 6. Testes existentes e lacunas

Foram identificados testes que:

- criam amostra pela rota atual e verificam accession_number e custodiante inicial;
- verificam a presença dos tipos RECEIPT e CUSTODY na timeline;
- verificam autorização da transferência por custodiante atual;
- exercitam o fluxo de assinatura e auditoria.

A suíte PostgreSQL instala o trigger append-only da cadeia de custódia. Entretanto, no arquivo test_postgres_guards.py consultado não foi identificado teste específico que tente atualizar ou excluir um registro de chain_of_custody e confirme o bloqueio.

Não foram identificados testes para:

- evento de custódia ligado a ObjetoCustodia antes de DeviceSample;
- consulta unificada de eventos legados e novos;
- criação de DeviceSample vinculada a exatamente um ObjetoCustodia;
- prevenção de duas DeviceSamples para o mesmo ObjetoCustodia;
- ausência de evento inicial duplicado no aceite;
- preservação de received_at e received_by_id da chegada física;
- concorrência/idempotência do aceite e da criação da amostra;
- histórico de objeto recusado ou pendente sem DeviceSample.

Esta lista é uma análise dos arquivos consultados, não uma afirmação de que nenhum teste indireto exista em todo ambiente.

## 7. Recomendação técnica de compatibilização

### 7.1 Preservar uma única tabela de eventos

A recomendação preliminar é estender a tabela existente chain_of_custody, em vez de criar um segundo histórico físico para o mesmo tipo de evento.

Proposta lógica:

- manter device_sample_id como FK nullable para preservar eventos legados;
- adicionar custody_object_id como FK nullable para CustodyObject;
- garantir por CHECK que exatamente um dos dois campos esteja preenchido em cada evento;
- manter FKs explícitas e ON DELETE RESTRICT;
- manter append-only, timestamps, autoria, localização, justificativa, selo e referência de assinatura;
- reconhecer que o modelo físico atual não possui event_type nem recorded_by_id explícitos; ambos precisam ser avaliados como colunas aditivas ou ter seu significado formalmente mapeado, sem inferência retroativa;
- transferred_at representa o instante do evento e created_at pode representar o registro no sistema; location_from/location_to são textos, não FKs de localização;
- notes pode guardar observações livres, mas não substitui automaticamente condition_note estruturado nem vínculos de evidência.
- criar índice de consulta por custody_object_id e transferred_at;
- eventos do fluxo novo devem apontar para CustodyObject, inclusive depois da criação da amostra;
- eventos legados continuam apontando para DeviceSample;
- a amostra nova consulta a cadeia por meio de seu ObjetoCustodia, sem duplicar o evento de chegada.

A regra de alvo exclusivo evita FK polimórfica sem integridade referencial. A constraint deve ser avaliada para compatibilidade com PostgreSQL e SQLite e declarada também no metadata SQLAlchemy.

### 7.2 Vínculo de DeviceSample

Manter a regra aprovada DEC04/DEC05:

- DeviceSample recebe FK nullable custody_object_id para CustodyObject;
- criar UNIQUE para impedir mais de uma amostra por ObjetoCustodia;
- manter nulabilidade para amostras legadas;
- exigir o vínculo no serviço de aceite do fluxo novo;
- não preencher vínculos em amostras antigas sem evidência documental.

A relação é 1:0..1 no schema de compatibilidade; para amostras novas do fluxo de aceite, o vínculo é obrigatório. A constraint UNIQUE, isoladamente, não garante que toda amostra nova tenha um objeto; essa obrigação precisa ser protegida pelo fluxo transacional e por regra adicional de integridade compatível com a preservação do legado.

### 7.3 Consulta unificada

Para uma DeviceSample nova vinculada a CustodyObject, o histórico deverá consultar eventos cujo custody_object_id corresponda ao objeto. Para uma amostra legada sem vínculo, deverá continuar consultando device_sample_id.

A consulta por ObjetoCustodia deve funcionar mesmo antes da criação da amostra, permitindo acompanhar material pendente, recusado ou aguardando validação.

A API deve preservar compatibilidade dos endpoints legados e acrescentar consultas por ObjetoCustodia. A resposta de evento deve identificar o alvo sem ambiguidade.

### 7.4 Transação de aceite

No aceite final, a transação deverá:

1. bloquear o ObjetoCustodia e verificar sua situação;
2. confirmar que o objeto está elegível para aceite e ainda não possui DeviceSample;
3. criar DeviceSample com custody_object_id;
4. copiar received_at e received_by_id da chegada física original, sem substituir pelo instante ou usuário que executa o aceite;
5. preservar accession_number e o QR Code existentes;
6. manter a cadeia já registrada no ObjetoCustodia, sem inserir outro evento de recebimento;
7. atualizar eventual projeção de custodiante/localização da amostra, se esses campos forem mantidos;
8. registrar auditoria, assinatura quando exigida, idempotência e commit na mesma unidade transacional.

A operação deve impedir que reenvio ou concorrência crie duas amostras para o mesmo objeto.

## 8. Pontos que exigem decisão/revisão antes do mapeamento físico

| ID | Ponto | Situação |
|---|---|---|
| COMP01 | Adotar uma tabela chain_of_custody com dois alvos explícitos e CHECK de alvo exclusivo | Recomendação técnica; revisão arquitetural pendente |
| COMP02 | Definir o conteúdo do evento inicial e se a chegada exige assinatura | Depende de EST07 e governança |
| COMP03 | Definir se current_custodian_id/current_location em DeviceSample serão projeção sincronizada ou campos legados em descontinuação | Pendente |
| COMP04 | Definir compatibilidade dos campos de identidade, especialmente serial_number obrigatório e UNIQUE serial/lote/fabricante | Pendente; revisar DEC05 |
| COMP05 | Definir resposta/API para eventos ligados a ObjetoCustodia e histórico unificado | Pendente |
| COMP06 | Definir eventos de fracionamento, agrupamento, devolução e destinação sem quebra de cadeia | Pendente de regra funcional e técnica |
| COMP07 | Definir testes de append-only, alvo exclusivo, concorrência, idempotência e continuidade do histórico | Proposta de cobertura |

## 9. Conclusão

A estrutura atual não suporta diretamente a custódia anterior à criação de DeviceSample, porque chain_of_custody exige device_sample_id e os serviços/rotas operam exclusivamente sobre amostras.

A compatibilização parece tecnicamente viável sem criar uma segunda tabela de histórico: estender ChainOfCustody com FK para CustodyObject, tornar a FK legada para DeviceSample nullable, impor alvo exclusivo e manter os eventos novos vinculados ao objeto de custódia. Essa é uma recomendação de desenho, ainda sujeita à revisão arquitetural e à confirmação de compatibilidade das consultas e contratos externos.

A maior mudança não é apenas relacional. O fluxo de criação direta de amostra deverá coexistir temporariamente com o fluxo novo, e a API, assinatura, timeline, transferência, frontend e testes precisarão ser adaptados em etapa posterior.

**Nenhuma implementação, migração ou alteração de banco foi realizada.**

## 10. Próxima atividade recomendada

1. Revisar esta recomendação de extensão de ChainOfCustody e confirmar se o desenho de alvo exclusivo atende à governança de custódia.
2. Detalhar o contrato de histórico unificado, a consulta de eventos pré-amostra e a transação de aceite.
3. Resolver COMP02–COMP07 e DEC07/DEC08 nos pontos que afetam persistência, assinatura e compatibilidade.
4. Submeter o mapeamento lógico à revisão arquitetural e funcional.
5. Somente após revisão e autorização específica, elaborar a proposta de migração aditiva e os testes. Não executar migrações nesta etapa.

## 11. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-09 | Análise estática dos modelos, serviços, rotas, migrações, triggers, schemas, testes e frontend; recomendação de extensão de ChainOfCustody com alvo exclusivo para legado e novo fluxo. |
| 0.2 | 2026-11-09 | Complemento do mapeamento: identificação de event_type e recorded_by_id como campos não existentes no schema atual e necessidade de avaliá-los como extensões aditivas. |
