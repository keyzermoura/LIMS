# LIMS — Desenho técnico proposto da Etapa 1: solicitação e recebimento

**Repositório:** `keyzermoura/LIMS`  
**Base de análise:** branch `main`, após o commit de documentação da matriz de recebimento de 09/11/2026.  
**Status:** proposta técnica para revisão e aprovação.  
**Escopo:** banco de dados, API, regras transacionais, permissões, integração com o fluxo existente e testes.  
**Fora do escopo desta entrega:** implementação, migrações, alteração de código ou implantação.

> Este documento é uma proposta de desenho. Os nomes de tabelas, campos e endpoints são sugestões técnicas a validar. Não constituem autorização para implementação.

## 1. Objetivo e premissas

Implementar futuramente a Etapa 1 do fluxo SEFI, mantendo as decisões funcionais aprovadas:

- uma solicitação corresponde a um único dispositivo;
- uma solicitação admite no máximo um recebimento físico;
- quantidade declarada e quantidade recebida são informações distintas;
- o conferente registra a conferência e formaliza a decisão inicial;
- a coordenação valida apenas exceções previstas ou encaminhadas;
- bloqueios impeditivos não podem ser contornados por aceite com ressalvas;
- o protocolo SEFI só é gerado após aceite final e validação favorável, quando exigida;
- decisões, correções, checklist e validações devem permanecer auditáveis.

A proposta considera a arquitetura atualmente observada no repositório: FastAPI, SQLAlchemy 2, Pydantic, PostgreSQL 16, Alembic, autenticação/RBAC, auditoria e frontend React/TypeScript.

## 2. Diagnóstico técnico que condiciona a solução

### 2.1 Componentes existentes a reutilizar

| Componente atual | Uso proposto |
|---|---|
| `DeviceSample` / `device_samples` | Continuar como cadastro operacional do dispositivo recebido, ampliando sua relação com a solicitação. |
| `LabTest` / `lab_tests` | Continuar representando os ensaios planejados para o dispositivo. Não transformar cada execução em um novo `LabTest`. |
| `User` / `users` | Identificar solicitante interno, recebedor, conferente e coordenador, observando os papéis existentes. |
| Serviço de auditoria | Registrar eventos de solicitação, recebimento, conferência, decisão e validação. |
| Cadeia de custódia | Reutilizar para movimentações físicas posteriores, sem confundir movimentação com recebimento inicial. |
| Assinatura eletrônica | Reavaliar sua aplicação a decisões formais segundo política institucional; não presumir que todo registro operacional exige assinatura eletrônica. |

### 2.2 Ajustes necessários

O modelo atual de `DeviceSample` contém campos de identificação e recebimento diretamente na amostra, incluindo número de série e lote não nulos e restrição única por série/lote/fabricante. Essa estrutura precisa ser revista com cuidado:

- número de série deve admitir ausência quando o dispositivo não possuir série individual;
- a identidade comercial não deve impedir solicitações diferentes do mesmo fabricante, lote ou produto;
- o protocolo SEFI deve ser a chave operacional do processo, sem depender da combinação fabricante/lote/série;
- dados da solicitação devem existir antes do recebimento físico;
- dados do recebimento, conferência e decisão devem ser entidades próprias;
- não se deve apagar nem substituir o histórico de decisões.

A alteração da restrição de unicidade e da obrigatoriedade dos campos existentes exige análise de dados legados e migração reversível sempre que tecnicamente possível.

## 3. Modelo lógico proposto

### 3.1 Entidades novas e relações

| Entidade proposta | Finalidade | Relação principal |
|---|---|---|
| `solicitations` | Demanda cadastrada por solicitante externo ou servidor | Uma solicitação para um dispositivo |
| `receipts` | Registro da chegada física e conferência | Solicitação 1 : 0..1 recebimento |
| `receipt_checklist_templates` | Versões dos modelos de checklist | Um modelo possui critérios |
| `receipt_checklist_criteria` | Critérios configurados por versão | Um critério pode ser respondido em vários recebimentos |
| `receipt_checklist_responses` | Respostas imutáveis da conferência | Recebimento + critério + versão |
| `receipt_exceptions` | Exceções, bloqueios e providências | Vinculada ao recebimento/resposta |
| `coordination_reviews` | Decisões da coordenação | Vinculada à exceção e à decisão do conferente |
| `solicitation_status_history` | Histórico de transições, se não integralmente coberto pela auditoria atual | Solicitação |

A tabela `device_samples` deverá receber uma referência única à solicitação (`solicitation_id`), ou a relação equivalente escolhida após a avaliação das convenções ORM. A cardinalidade deve ser 1:1. A solicitação poderá existir antes da amostra ser operacionalmente liberada.

### 3.2 Campos conceituais

**`solicitations`**

| Campo | Tipo conceitual | Regra |
|---|---|---|
| id | UUID | Chave primária |
| request_number | string | Identificador da solicitação, único e gerado no cadastro |
| requester_user_id | UUID, opcional | Usuário externo autenticado, se aplicável |
| requester_name / requester_email | string | Identificação de contato preservada no momento do cadastro |
| submitted_by_user_id | UUID | Usuário que efetivamente cadastrou/submeteu |
| origin_unit | string | Unidade/organização solicitante |
| purpose | text | Finalidade do encaminhamento |
| request_type | FK/código | Catálogo institucional |
| priority | FK/código | Catálogo institucional |
| priority_justification | text, opcional | Obrigatória para prioridade excepcional |
| declared_quantity | decimal/integer | Maior que zero |
| unit_of_measure | FK/código | Catálogo controlado |
| status | enum/string controlada | Transições validadas no serviço |
| submitted_at | timestamptz, opcional | Data/hora de submissão |
| created_at / updated_at | timestamptz | Auditoria técnica |

Os campos de identificação do dispositivo podem permanecer em `device_samples`, desde que o vínculo 1:1 seja garantido e os dados sejam cadastráveis antes da chegada. A decisão entre manter o cadastro completo em `device_samples` ou criar uma entidade `solicitation_device` deve ser tomada após verificar os relacionamentos e dependências existentes.

**`receipts`**

| Campo | Tipo conceitual | Regra |
|---|---|---|
| id | UUID | Chave primária |
| solicitation_id | UUID | FK única; impede segundo recebimento |
| arrived_at | timestamptz | Data/hora efetiva da chegada |
| received_by_id | UUID | Usuário que recebeu fisicamente |
| checked_by_id | UUID | Conferente responsável |
| received_quantity | decimal/integer | Maior que zero |
| delivery_method | string/código | Quando aplicável |
| packaging_condition | string/código | Registro objetivo |
| device_condition | string/código | Registro objetivo |
| observations | text | Ocorrências relevantes |
| status | enum/string controlada | Estados de recebimento/conferência |
| created_at / updated_at | timestamptz | Auditoria técnica |

A unicidade de `solicitation_id` deve ser garantida no banco, não apenas na aplicação. Uma nova tentativa de POST não pode criar outro recebimento.

**`receipt_checklist_templates` e `receipt_checklist_criteria`**

- template: código, versão, nome, vigência, estado e autor da publicação;
- critério: template, código estável (C01–C20 na versão inicial), texto, classe, obrigatoriedade, regra de aplicabilidade, exigência de justificativa e ordem;
- publicação de nova versão não altera critérios já usados em conferências concluídas;
- critério publicado não deve ser editado retroativamente; correções geram nova versão.

**`receipt_checklist_responses`**

- recebimento;
- critério e versão;
- resultado: `CONFORME`, `NAO_CONFORME`, `NAO_APLICAVEL`;
- justificativa/observação;
- usuário responsável e data/hora;
- referência aos anexos/evidências;
- restrição única para impedir duas respostas correntes do mesmo critério no mesmo checklist, com estratégia de revisão/histórico definida no detalhamento físico.

**`receipt_exceptions`**

- recebimento e resposta relacionada;
- categoria: impeditiva, sujeita à coordenação ou administrativa;
- descrição factual, evidências, avaliação de risco/impacto;
- ação requerida, responsável e prazo, quando aplicável;
- estado: aberta, aguardando coordenação, devolvida, em regularização, resolvida ou encerrada;
- registro de resolução sem exclusão do apontamento inicial.

**`coordination_reviews`**

- exceção/decisão submetida;
- decisão: aprovada, devolvida para complementação ou rejeitada;
- justificativa obrigatória;
- coordenador responsável e data/hora;
- referência à versão da matriz/regra aplicada;
- histórico append-only: nova avaliação gera novo registro, sem sobrescrever anterior.

## 4. Restrições e integridade no PostgreSQL

Recomendações:

1. FK de `device_samples.solicitation_id` com `UNIQUE` e `NOT NULL` quando a migração e os dados existentes permitirem.
2. FK única de `receipts.solicitation_id` para impor no máximo um recebimento por solicitação.
3. `CHECK (declared_quantity > 0)` e `CHECK (received_quantity > 0)`, com tipo numérico adequado à unidade.
4. `CHECK`/enum para resultados de checklist, classes e estados, alinhado ao padrão atual de enums SQLAlchemy.
5. FKs para usuários com `ON DELETE RESTRICT`, preservando autoria.
6. Índices por número da solicitação, protocolo SEFI, estado, solicitante, data e fila de validação.
7. Protocolo SEFI único e não nulo somente depois de gerado; considerar coluna inicialmente nula com índice único parcial no PostgreSQL.
8. Transições de estado e regra de bloqueio centralizadas no serviço de domínio; constraints no banco como segunda barreira.
9. Controle de concorrência otimista já utilizado no projeto, ou bloqueio transacional explícito, para impedir duas decisões concorrentes.
10. Não armazenar arquivo binário diretamente nas tabelas de negócio sem decisão arquitetural; metadados e integridade do anexo devem ser registrados, com armazenamento controlado.

A regra de “coordenação não pode dispensar bloqueio impeditivo” deve existir no serviço de domínio e ser coberta por testes; não deve depender apenas da interface web.

## 5. Fluxo transacional proposto

### 5.1 Cadastro e submissão

- criar solicitação em elaboração;
- identificar solicitante e autor do cadastro;
- cadastrar um único dispositivo;
- validar campos obrigatórios conforme tipo;
- ao submeter, validar consistência e mudar para aguardando recebimento;
- registrar evento de auditoria.

### 5.2 Registro de recebimento

Uma transação deverá:

1. consultar a solicitação e verificar se está apta a receber;
2. bloquear concorrência sobre a solicitação ou usar controle otimista;
3. verificar ausência de recebimento anterior;
4. criar o recebimento com quantidade e responsáveis;
5. alterar estado para em conferência;
6. registrar evento de auditoria;
7. confirmar a transação.

A restrição única no banco será a proteção final contra duplicidade, inclusive em requisições simultâneas.

### 5.3 Conferência e decisão

- carregar a versão ativa do checklist aplicável;
- gravar respostas e evidências;
- calcular bloqueios a partir da classificação versionada dos critérios;
- não permitir concluir se houver critério obrigatório sem resposta;
- se houver impeditivo não resolvido, manter pendência e impedir aceite;
- se houver exceção sujeita à coordenação, criar encaminhamento e deixar decisão aguardando validação;
- se não houver bloqueio nem exceção, permitir decisão do conferente;
- registrar decisão como evento não sobrescrevível.

### 5.4 Validação da coordenação

- verificar perfil/permissão e segregação de funções conforme política a aprovar;
- validar que a decisão encaminhada ainda corresponde à versão corrente do recebimento;
- verificar novamente todos os bloqueios impeditivos no servidor;
- permitir aprovar ou devolver/rejeitar com justificativa;
- gravar revisão e auditoria na mesma transação;
- uma aprovação não pode, por si só, alterar respostas não conformes impeditivas.

### 5.5 Geração do protocolo SEFI

A geração deve ser operação transacional e idempotente:

- pré-condições: decisão favorável final, checklist concluído, sem impeditivos abertos e coordenação validada quando exigida;
- alocar número segundo padrão institucional ainda pendente;
- impor unicidade no banco;
- persistir protocolo e transição para recebida/apta ao planejamento na mesma transação;
- em repetição da mesma requisição, retornar o protocolo já atribuído, sem gerar outro;
- em falha, não deixar processo parcialmente protocolado.

## 6. API REST proposta

Prefixo sugerido: `/api/v1`, mantendo o padrão de roteadores já existente.

| Método | Endpoint proposto | Ação | Permissão principal |
|---|---|---|---|
| POST | `/solicitations` | Criar solicitação | Solicitante externo ou servidor SEFI |
| GET | `/solicitations` | Listar solicitações conforme escopo | Próprias solicitações ou perfil interno |
| GET | `/solicitations/{id}` | Consultar detalhes | Dono da solicitação ou perfil interno |
| PATCH | `/solicitations/{id}` | Corrigir enquanto em elaboração/pendência autorizada | Autor/dono ou servidor autorizado |
| POST | `/solicitations/{id}/submit` | Submeter solicitação | Solicitante autorizado |
| POST | `/solicitations/{id}/receipt` | Registrar entrega física única | Recebedor/conferente autorizado |
| GET | `/receipts/{id}` | Consultar recebimento | Perfil interno autorizado |
| GET | `/receipts/{id}/checklist` | Obter checklist aplicável | Recebedor/conferente |
| PUT | `/receipts/{id}/checklist` | Registrar respostas e evidências | Conferente responsável |
| POST | `/receipts/{id}/decision` | Formalizar decisão do conferente | Conferente responsável |
| POST | `/receipts/{id}/coordination-review` | Aprovar/devolver/rejeitar | Coordenação autorizada |
| POST | `/solicitations/{id}/sefi-protocol` | Solicitar geração idempotente do protocolo | Serviço/perfil interno autorizado |
| GET | `/coordination/reviews` | Consultar fila de validação | Coordenação |
| GET | `/receipt-checklists/active` | Consultar checklist ativo | Perfis internos |

A API deve retornar erros de domínio claros, sem expor detalhes internos:

- `409 Conflict`: recebimento já existente, estado incompatível ou conflito de concorrência;
- `422 Unprocessable Entity`: campos inválidos, checklist incompleto ou regra impeditiva;
- `403 Forbidden`: usuário autenticado sem permissão;
- `404 Not Found`: registro inexistente ou não visível no escopo do usuário;
- `201 Created`: criação bem-sucedida;
- `200 OK`: consulta ou transição concluída.

A resposta de erro deve trazer código estável de domínio, mensagem objetiva e identificador de correlação. A implementação deve respeitar os esquemas Pydantic e o tratamento de erros já existente.

## 7. Segurança, perfis e segregação de funções

A autorização deve ser aplicada no backend, não apenas ocultando botões no frontend.

| Ação | Solicitante externo | Servidor SEFI | Conferente | Coordenação |
|---|---:|---:|---:|---:|
| Criar solicitação própria | Sim | Sim, inclusive em nome de terceiro | Conforme perfil | Conforme perfil |
| Consultar solicitação própria | Sim | Sim | Conforme atribuição | Sim |
| Consultar solicitação de terceiros | Não | Conforme atribuição institucional | Conforme atribuição | Conforme atribuição |
| Registrar chegada física | Não | Conforme autorização | Sim | Conforme política |
| Preencher checklist | Não | Conforme designação | Sim | Consulta |
| Formalizar decisão inicial | Não | Se designado conferente | Sim | Não substitui conferente |
| Validar exceção | Não | Não, salvo perfil formalmente autorizado | Não | Sim |
| Gerar protocolo SEFI | Não | Serviço após pré-condições | Não diretamente | Não diretamente |

A tabela é uma matriz inicial de permissões, não uma afirmação de que os papéis atuais já correspondam a esses perfis. Será necessário mapear `UserRole` e as dependências RBAC existentes antes de definir novos papéis ou permissões granulares.

## 8. Organização provável do backend

Sugestão de organização, compatível com os diretórios existentes:

- `app/models/solicitation.py`
- `app/models/receipt.py`
- `app/models/receipt_checklist.py`
- `app/models/receipt_exception.py`
- `app/models/coordination_review.py`
- `app/schemas/solicitation.py`
- `app/schemas/receipt.py`
- `app/schemas/receipt_checklist.py`
- `app/api/v1/routes/solicitations.py`
- `app/api/v1/routes/receipts.py`
- `app/api/v1/routes/coordination.py`
- `app/services/solicitation_service.py`
- `app/services/receipt_service.py`
- `app/services/receipt_decision_service.py`
- `app/services/sefi_protocol_service.py`

Os serviços devem concentrar regras de negócio e transações. As rotas devem validar entrada, autenticar/autorizar e delegar ao serviço. Os modelos não devem conter regras complexas de transição.

## 9. Frontend proposto

Telas/fluxos mínimos:

1. **Nova solicitação:** dados do solicitante, dispositivo, finalidade, tipo e prioridade.
2. **Minhas solicitações:** status, número, data e pendências visíveis ao solicitante.
3. **Recebimento SEFI:** localizar solicitação, registrar chegada, quantidade, recebedor e condição física.
4. **Conferência:** checklist versionado, observações, evidências e alertas de bloqueio.
5. **Decisão:** resumo automático dos impeditivos/exceções e formalização pelo conferente.
6. **Fila da coordenação:** exceções pendentes, evidências, decisão do conferente e ações disponíveis.
7. **Detalhe/rastreabilidade:** linha do tempo de submissão, chegada, checklist, decisão, validação e protocolo.

A interface deve exibir claramente a diferença entre “recebido fisicamente”, “aceito” e “liberado para planejamento/ensaios”. O frontend não deve calcular sozinho se um bloqueio pode ser ignorado; deve apresentar a decisão do backend.

## 10. Estratégia de migração e compatibilidade

A migração deve ser incremental, evitando interromper o fluxo atual:

1. mapear registros atuais de `device_samples`, `lab_tests`, recebimento e QR;
2. identificar duplicidades e registros que seriam afetados pela atual restrição de identidade;
3. criar tabelas de solicitação/recebimento/checklist sem remover colunas antigas;
4. migrar dados históricos para a nova estrutura quando houver informação suficiente, marcando origem e incerteza;
5. manter campos legados durante período de compatibilidade;
6. adicionar relação 1:1 e validar integridade;
7. alterar nulabilidade e restrições de unicidade somente após plano de saneamento;
8. adaptar serviços/rotas e frontend;
9. executar testes de migração upgrade/downgrade em banco descartável;
10. retirar campos legados apenas em entrega posterior e autorizada.

Não se deve inventar solicitante, data de recebimento, conferente ou decisão para registros antigos quando essas informações não existirem. Dados históricos incompletos devem ser identificados como migrados/incompletos, não apresentados como se fossem registros contemporâneos completos.

## 11. Plano de testes da Etapa 1

### 11.1 Testes de modelo e migração
- cardinalidade 1:1 solicitação/dispositivo;
- no máximo um recebimento por solicitação;
- campos opcionais para lote/série conforme aplicabilidade;
- integridade de FKs e restrições;
- migração com banco vazio e com dados legados;
- upgrade/downgrade sem perda silenciosa.

### 11.2 Testes de serviço e regras
- cadastro externo e interno;
- cadastro em nome de terceiro;
- isolamento de dados entre solicitantes;
- submissão e correção por estado;
- entrega única inclusive em chamadas simultâneas;
- checklist completo/incompleto;
- cada bloqueio C01–C08;
- cada exceção C09–C15;
- correções administrativas C16–C20;
- não aplicabilidade justificada;
- bloqueio impeditivo não contornável;
- aceite, ressalva, recusa e devolução da coordenação;
- protocolo idempotente, único e transacional;
- auditoria de todas as transições.

### 11.3 Testes de API e interface
- códigos HTTP e mensagens de domínio;
- autorização por papel e por propriedade do registro;
- ausência de exposição de solicitações de terceiros;
- concorrência/duplo clique/reenvio;
- estados exibidos coerentes com backend;
- evidências anexadas e acessíveis apenas a perfis autorizados.

## 12. Sequência de implementação sugerida após aprovação

| Subetapa | Entrega | Critério para avançar |
|---|---|---|
| 1A | Modelagem final e migração aditiva | Revisão do esquema e estratégia de dados legados |
| 1B | Serviços e API de solicitação | Testes de cadastro, submissão, autorização |
| 1C | Recebimento e checklist versionado | Testes de entrega única e checklist |
| 1D | Decisão e validação da coordenação | Testes de bloqueios e exceções |
| 1E | Geração de protocolo SEFI | Testes de idempotência e transação |
| 1F | Frontend e integração ponta a ponta | Testes funcionais e aceite do usuário |
| 1G | Revisão de segurança, auditoria e documentação | Revisão final e aprovação antes de implantação |

Cada subetapa deve ser executada em branch de feature própria ou na branch de trabalho expressamente aprovada, com PR e CI. Não realizar commits diretamente em `main`.

## 13. Decisões ainda necessárias antes da implementação

1. O solicitante externo terá conta autenticada própria desde a primeira versão ou haverá cadastro assistido pelo servidor do SEFI?
2. Quais perfis internos existentes corresponderão a recebedor, conferente e coordenação? Será necessário criar permissões granulares?
3. A decisão do conferente e a validação da coordenação exigirão assinatura eletrônica formal ou autenticação com registro auditável será suficiente nesta etapa?
4. Qual padrão de numeração será usado para solicitação e protocolo SEFI?
5. Quais documentos serão obrigatórios por categoria de dispositivo?
6. Como serão definidos os prazos e responsáveis por pendências/ressalvas?
7. Qual será a política de anexos: formatos, tamanho máximo, retenção, antivírus e armazenamento?
8. A solicitação poderá ser editada após submissão em quais situações e por quais perfis?
9. A instituição permitirá cancelamento após recebimento físico? Em que condições?
10. O protocolo SEFI será gerado automaticamente ao final do aceite ou por ação explícita do servidor?

## 14. Aprovação necessária

Solicita-se revisar este desenho técnico, especialmente:

- entidades e cardinalidades;
- estratégia de reaproveitamento de `DeviceSample`;
- endpoints e matriz de permissões;
- fluxo de decisão/coordenação;
- estratégia de migração dos registros existentes;
- decisões institucionais pendentes.

**Nenhuma alteração de código, banco, migração, endpoint ou interface foi realizada nesta entrega.** A implementação só deverá começar após aprovação explícita deste desenho e definição dos parâmetros institucionais necessários.
