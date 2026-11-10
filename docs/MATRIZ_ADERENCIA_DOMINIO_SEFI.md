# Matriz de Aderência — Domínio Existente × Domínio SEFI Aprovado

**Identificador:** MAT-ADER-SEFI-001  
**Versão:** 1.0  
**Data:** 2026-11-10  
**Repositório:** `keyzermoura/LIMS`  
**Branch examinada:** `main`  
**Natureza:** diagnóstico documental de aderência; não constitui especificação de implementação, homologação ou aprovação do Gate G0.

---

## 1. Objetivo e escopo

Confrontar o domínio atualmente implementado no repositório com a baseline funcional SEFI ratificada em D01–D20 e com a estrutura de domínio M0.1/M0.2 adotada para o projeto.

A análise considera o código efetivamente localizado em modelos ORM, enums, schemas Pydantic, rotas, serviços e testes. A classificação é funcional: a existência de uma tabela ou rota com nome semelhante não significa que ela satisfaça a semântica e os controles definidos para o processo SEFI.

**Limite importante:** esta é uma inspeção estática de código e documentação. Não foram executados testes, migrações, build, containers ou consultas a banco real nesta etapa. A presença de um teste no repositório não equivale à comprovação de sua execução bem-sucedida no HEAD examinado.

## 2. Critérios de classificação

| Classificação | Significado |
|---|---|
| **Reutilizável sem alteração** | O componente existente atende ao requisito funcional e pode ser mantido como está, sujeito às evidências de teste/homologação. |
| **Reutilizável com adaptação** | Há capacidade ou componente aproveitável, mas exige extensão, separação de conceitos ou ajuste de regra para aderir ao domínio SEFI. |
| **Insuficiente** | Há implementação relacionada, mas faltam atributos, estados, eventos, barreiras ou controles essenciais. Não deve ser considerada aderente. |
| **Inexistente** | Não foi identificado componente próprio que represente o conceito ou processo no conjunto inspecionado. |
| **Fora do escopo** | Não se aplica ao MVP funcional considerado. Não foi atribuído a nenhum requisito D01–D20 nesta versão. |

A classificação descreve a aderência observada, não a qualidade geral do código.

## 3. Síntese executiva

A implementação atual possui uma base aproveitável de autenticação, perfis, amostras, ensaios, transferência de custódia, assinatura eletrônica e auditoria. Entretanto, seu fluxo central começa no cadastro direto de uma `DeviceSample`, enquanto o domínio SEFI aprovado exige uma cadeia anterior e distinta: solicitação → chegada/recebimento → itens recebidos → objetos individualizados sob custódia → conferência e decisão → aceite formal → amostra operacional.

A principal divergência não é apenas ausência de campos. É uma diferença de modelo: conceitos que o SEFI precisa manter separados estão hoje concentrados ou representados por uma entidade de amostra. Não se deve assumir equivalência automática entre `DeviceSample` e `AmostraOperacional`, nem entre `DeviceSample` e `ObjetoCustodia`.

**Resultado:** a aderência global é **parcial e insuficiente para o fluxo de admissão SEFI**. A base de segurança, assinatura e auditoria pode ser aproveitada, mas a camada de domínio de solicitação, recebimento, conferência, pendências, recusa, objetos de custódia e aceite precisa ser modelada e validada antes de qualquer implementação.

## 4. Matriz de aderência por decisão D01–D20

| ID | Requisito SEFI aprovado | Evidência localizada no domínio atual | Classificação | Lacuna principal / encaminhamento |
|---|---|---|---|---|
| **D01** | Recepção registra a chegada; recebimento e conferência são eventos distintos, ainda que executados pela mesma pessoa quando autorizada. | `UserRole` contém ADMIN, FISCAL, TECNICO, CUSTODIANTE e AUDITOR; não foi localizado perfil RECEPÇÃO. `POST /samples` cria a amostra diretamente e registra `received_by_id`. | **Insuficiente** | Criar o conceito de chegada/recebimento independente da amostra e separar autoria, horário e evento de conferência. Definir perfis/permissões de recepção e acumulação de funções conforme a matriz institucional. |
| **D02** | Registrar solicitação vinculada, horários efetivos e de registro, recebedor, entregador, volumes, descrição externa, embalagem, avarias, documentos e evidências pertinentes. | `SampleCreate` contém dados do dispositivo, `storage_location` e `received_at`; `DeviceSample` contém `received_at` e `received_by_id`. | **Insuficiente** | Faltam solicitação, entregador/ausência declarada, volumes, condição de embalagem, avarias, documentos apresentados e evidências vinculadas ao recebimento. Distinguir horário efetivo de chegada do timestamp de registro. |
| **D03** | Preservar quantidades declarada, apresentada, aceita, recusada e não apresentada; justificar divergências e permitir recebimento parcial. | Não foram identificados atributos ou entidade própria para essas quantidades no modelo `DeviceSample` ou nos schemas examinados. | **Inexistente** | Criar controle quantitativo no nível de item de recebimento, com reconciliação, justificativas e regras que impeçam geração de amostra para quantidades recusadas/não apresentadas. |
| **D04** | Um item recebido pode originar vários objetos de custódia, com decisões, quantidades, evidências e históricos independentes. | `DeviceSample` representa diretamente um dispositivo/amostra; `ChainOfCustody` referencia `device_sample_id`. Não foram localizadas entidades `ItemRecebimento` ou `ObjetoCustodia`. | **Insuficiente** | Modelar cardinalidade item recebido → um ou vários objetos de custódia. Cada objeto precisa de identificador, quantidade, condição, decisão e histórico próprios. |
| **D05** | Pendências saneáveis individualizadas, com responsável, comunicação, prazo, alertas, prorrogação justificada e reavaliação; vencimento não recusa automaticamente. | Não foi localizada entidade/rota específica para pendências de recebimento e seu ciclo de vida. `CapaAction` é CAPA ligada a amostra/ensaio, não substitui pendência documental ou de admissão. | **Inexistente** | Criar conceito próprio de pendência, separado de CAPA, com estados, prazos, comunicações, prorrogação e reavaliação. |
| **D06** | Recusa motivada, evidenciada e decidida por autoridade competente; comunicação e destinação efetiva; recusa não encerra automaticamente a custódia. | `SampleStatus` inclui REPROVADO e DESCARTADO; não foi identificada entidade/fluxo de recusa de item ou objeto, nem registro de devolução/destinação efetiva. | **Insuficiente** | Não equiparar reprovação de ensaio ou descarte de amostra a recusa de recebimento. Criar decisão de recusa por objeto, validações exigidas, comunicação e evento comprovado de destinação. |
| **D07** | Transferência de custódia como evento próprio, com entregador, recebedor, horários, localização e confirmação do novo custodiante; responsabilidade permanece com o anterior até confirmação. | `ChainOfCustody` registra origem/destino, custodiante anterior/novo, `transferred_at`, motivo, locais e assinatura. `POST /custody/transfer` efetua a transferência. | **Reutilizável com adaptação** | O evento atual é centrado em `DeviceSample` e tem um único horário de transferência; o fluxo não evidencia confirmação autônoma do recebedor como condição para efetivar a mudança. Adaptar para `ObjetoCustodia`, horários efetivo/registro e aceite do novo custodiante. |
| **D08** | Mudança de localização é evento distinto da transferência e não altera o custodiante. | `DeviceSample.current_location` e `ChainOfCustody.location_from/location_to` registram localização no contexto da amostra/transferência. Não foi localizada rota ou evento próprio de movimentação sem transferência. | **Insuficiente** | Criar evento de movimentação física independente, com origem, destino, responsável, horários e justificativa, preservando o custodiante. |
| **D09** | Retificação excepcional com valores original/corrigido, justificativa, evidência, autorização prévia, assinatura e avaliação de impacto em amostras, ensaios e laudos. | `LabTestResult` mantém versões e o schema `LabTestResultIn` prevê `amendment_reason`; o serviço de ensaios trata emenda de resultado. | **Reutilizável com adaptação** | A emenda de resultado não equivale a retificação geral dos dados de solicitação, recebimento, item ou objeto. Falta fluxo transversal de autorização prévia e avaliação/registro de impacto sobre ensaios e laudos. |
| **D10** | Acumulação de funções permitida conforme permissões; autoaprovação bloqueada quando independência for obrigatória; administrador não ganha autoridade técnica automaticamente. | Existem perfis e verificações RBAC; rotas usam `require_roles`; ensaios podem ser atribuídos a técnico. Não foi localizada matriz de competências, substituições ou regra geral de independência por ato. | **Insuficiente** | Preservar RBAC como base, mas implementar matriz de competências/autoridades, substitutos formalmente designados e validação independente por tipo de decisão. |
| **D11** | Checklists por categoria com critérios E/S/I, aprovação, versão e preservação da versão aplicada em cada recebimento. | Não foram localizadas entidades, schemas ou rotas de checklist e critérios de conferência por categoria. | **Inexistente** | Criar estrutura versionada de checklist, critérios E/S/I, evidências e resultado por objeto/recebimento; congelar a versão aplicada. |
| **D12** | Governança de checklist: elaboração técnica, revisão da Qualidade, aprovação da Coordenação/autoridade e publicação administrativa após aprovação. | `UserRole` possui papéis gerais, mas não foi localizado fluxo de elaboração, revisão, aprovação, publicação e vigência de checklist. | **Inexistente** | Modelar ciclo de vida e trilha de aprovação do checklist. A permissão administrativa de publicação não deve permitir alteração autônoma de critério técnico aprovado. |
| **D13** | Documentos e evidências vinculados à solicitação, recebimento, item ou ocorrência; original preservado, versionamento, hash, acesso e auditoria. | O README e a inspeção anterior registram ausência de armazenamento de anexos; não foram localizados modelos/serviços próprios de anexos e evidências. Campos JSON de metadados não constituem repositório de evidências. | **Inexistente** | Definir entidade de metadados e serviço de armazenamento/versionamento de anexos, vínculo contextual, hash, acesso, retenção e tratamento de duplicidade/concorrência. |
| **D14** | Trilha cronológica e individualizada, protegida contra alteração/exclusão, com ator, horário, operação, valores anteriores/posteriores e justificativa. | `AuditLog`, `audit_service`, rotas `/audit`, hash encadeado/HMAC e guardas PostgreSQL. Schema contempla ator, ação, entidade, valores anteriores/posteriores, justificativa e contexto. | **Reutilizável com adaptação** | É a base mais aderente. Garantir cobertura dos novos eventos SEFI, auditoria de documentos/evidências e eventos de recebimento/objeto. A proteção por trigger não é, isoladamente, imutabilidade contra administrador privilegiado do banco. |
| **D15** | Contas individuais, menor privilégio, concessão/revogação formal, rastreabilidade e bloqueio de contas inativas ou de pessoas desligadas/mudadas de função. | `User` tem usuário individual, email, papel, `is_active`, bloqueio por tentativas e sessões; `auth_service` e RBAC controlam autenticação/permissões. | **Reutilizável com adaptação** | Faltam evidências de workflow formal de concessão, revisão periódica e revogação por mudança de vínculo/função, bem como histórico de alterações de perfil e matriz granular para as novas atividades SEFI. |
| **D16** | Assinatura vinculada ao conteúdo/decisão, identidade inequívoca, intenção, data/hora, autenticação reforçada e evidências de verificação; modalidade sujeita a decisão institucional/jurídica. | `ElectronicSignature` mantém snapshots de identidade/perfil, significado, motivo, ação, manifesto/hash, payload, horário e token de uso único. Serviço em duas etapas reautentica por senha. | **Reutilizável com adaptação** | Aproveitar o manifesto e o vínculo ao conteúdo. Avaliar autenticação reforçada/MFA e modalidade jurídica/institucional. Integrar assinatura às decisões de aceite, recusa, pendência, retificação e confirmação de custódia. |
| **D17** | Backup segregado e protegido de banco, documentos e evidências; monitoramento, retenção, testes de restauração e continuidade. | `docker-compose.yml` define volume persistente PostgreSQL; não foi localizada evidência de política executável de backup/restauração, cópia segregada ou recuperação de anexos. | **Inexistente** | Persistência em volume não é backup. Definir e comprovar política de cópia, segregação, retenção, monitoramento, RPO/RTO, testes de restauração e continuidade para banco e anexos. |
| **D18** | Identificadores independentes, únicos, permanentes e não reutilizáveis para solicitação, recebimento, objeto, amostra e ensaio, mantendo relacionamentos. | Há UUIDs nas entidades e `accession_number` sequencial para `DeviceSample`; há sequência de CAPA e QR associado à amostra. | **Insuficiente** | Reaproveitar UUID/sequence como mecanismos técnicos, mas criar identificadores de negócio independentes por agregado SEFI: solicitação, recebimento, objeto de custódia, amostra e ensaio. Definir padrão institucional e política de não reutilização. |
| **D19** | Chegada posterior vinculada à solicitação original, com novo evento e conferência; custódia só começa na chegada; reabertura autorizada ou nova solicitação vinculada quando encerrada. | Não foi localizada entidade de solicitação nem fluxo de recebimentos parciais/complementares ou reabertura vinculada. | **Inexistente** | Depende da modelagem de Solicitação, Recebimento e ItemRecebimento. Criar novo recebimento vinculado, sem reescrever eventos anteriores, com regra de reabertura/autorização. |
| **D20** | Barreira formal de aceite antes da criação da amostra operacional; exigir conferência, quantidades, critérios impeditivos, pendências resolvidas, aceite, validações e custódia registrada. | `POST /samples` cria diretamente `DeviceSample` com status RECEBIDO, número de accession e evento inicial de custódia. O teste de fluxo verifica criação direta e assinatura, mas não uma etapa anterior de aceite SEFI. | **Insuficiente — bloqueador crítico** | Separar registro da chegada, conferência e aceite da criação da amostra operacional. Implementar barreira transacional que impeça amostra sem objeto aceito, quantidades reconciliadas, critérios impeditivos atendidos, pendências impeditivas resolvidas e validações/assinaturas exigidas. |

## 5. Aderência por entidade do domínio

| Conceito da baseline SEFI | Componente encontrado | Aderência | Observação |
|---|---|---|---|
| Solicitação | Não identificado no conjunto de modelos ORM registrado | **Inexistente** | Não há raiz de processo para vincular entregas, itens e chegadas posteriores. |
| Item declarado / ItemRecebimento | Não identificado | **Inexistente** | Não há entidade para quantidades declaradas/apresentadas/aceitas/recusadas e reconciliação. |
| Recebimento | Campos de recebimento em `DeviceSample` e evento inicial em `ChainOfCustody` | **Insuficiente** | Dados/eventos estão associados à criação direta da amostra, sem agregado próprio de recebimento. |
| ObjetoCustodia | `DeviceSample` é referenciado por `ChainOfCustody` | **Insuficiente** | Não assumir equivalência: objeto de custódia SEFI precisa existir antes da amostra e admitir desfechos próprios. |
| AmostraOperacional | `DeviceSample` | **Insuficiente / candidato a adaptação** | O modelo atual mistura identificação de amostra, dados do dispositivo, recebimento inicial e estado de custódia. A equivalência deve ser decidida no desenho de domínio. |
| Ensaio | `LabTest` | **Reutilizável com adaptação** | Há associação à amostra, método, parâmetros, limites, responsável, estado e resultado. Rever vínculo à amostra operacional SEFI e a regras de admissão. |
| Versão de resultado | `LabTestResult` | **Reutilizável com adaptação** | Há histórico/versionamento e emenda; integrar com avaliação de impacto e laudo. |
| Evento de custódia | `ChainOfCustody` | **Reutilizável com adaptação** | Transferência implementada, mas precisa operar sobre ObjetoCustodia e separar movimentação de local. |
| Pendência / Recusa / Checklist | Não identificados como entidades próprias | **Inexistente** | Não substituir por CAPA, status de ensaio ou metadados genéricos. |
| Documento / Evidência | Não identificado como serviço/modelo próprio | **Inexistente** | Necessário armazenamento e versionamento controlados. |
| Usuário / Assinatura / Auditoria | `User`, `ElectronicSignature`, `AuditLog` | **Reutilizável com adaptação** | Base técnica significativa; ampliar permissões, decisões e cobertura de eventos SEFI. |

## 6. Aderência por camada técnica

| Camada | Evidência no repositório | Diagnóstico |
|---|---|---|
| Modelos ORM | `DeviceSample`, `ChainOfCustody`, `LabTest`, `LabTestResult`, `CapaAction`, `AuditLog`, `ElectronicSignature`, `User`, `RefreshToken` | Domínio centrado em amostra, ensaio e segurança; faltam agregados centrais do processo de recebimento SEFI. |
| Enums e estados | `UserRole`, `SampleStatus`, `TestStatus`, `TestOutcome`, `CapaStatus`, `AuditAction`, `SignatureMeaning` | Estados atuais não representam o ciclo de solicitação, chegada, conferência, pendência, recusa, aceite e objeto de custódia. |
| Schemas | `app/schemas/sample.py`, `test.py`, `audit.py` | Contratos HTTP espelham os modelos atuais; não há contratos identificados para os novos agregados SEFI. |
| Rotas | `/samples`, `/custody`, `/tests`, `/audit`, `/auth` | Não foram identificadas rotas próprias de solicitação, recebimento, conferência, pendências, checklists, recusas, documentos ou aceite. |
| Serviços | `sample_service`, `custody_service`, `test_service`, `signature_service`, `audit_service`, `auth_service` | Serviços reutilizáveis como infraestrutura/domínio adjacente; falta orquestração do processo de admissão SEFI. |
| Testes | `test_api_flow.py`, `test_postgres_guards.py` | Há cobertura de fluxos existentes (amostra direta, transferência, ensaio, assinatura, auditoria e guardas PostgreSQL). Não foi identificada cobertura dos cenários D01–D20 como fluxo de admissão SEFI. |
| Migrações | Alembic configurado; revisões existentes | Existência de mecanismo de migração não demonstra que o modelo SEFI esteja implementado nem que migrações tenham sido executadas/homologadas. |

## 7. Componentes que devem ser preservados como candidatos a reutilização

1. **Autenticação e identidade:** `User`, `RefreshToken`, Argon2id, JWT e bloqueio de conta.
2. **Autorização:** dependências RBAC e verificação de papéis, sujeitas à ampliação para competências SEFI.
3. **Assinatura eletrônica:** manifesto, snapshots, hash do conteúdo, significado, motivo, reautenticação e token de uso único.
4. **Auditoria:** snapshots, valores anteriores/posteriores, sequência, hash encadeado, HMAC e integração transacional.
5. **Concorrência:** versionamento otimista em entidades e bloqueio de linha em operações críticas já implementadas.
6. **Ensaios e resultados:** `LabTest` e `LabTestResult`, após revisão dos vínculos com a amostra operacional.
7. **Infraestrutura PostgreSQL/Alembic:** como base técnica, condicionada à execução e validação de migrações e testes no ambiente de referência.

A reutilização deve ser confirmada por testes de regressão e rastreabilidade; não implica manter sem revisão os contratos atuais.

## 8. Lacunas estruturais prioritárias

| Prioridade | Lacuna | Por que bloqueia |
|---|---|---|
| **P0** | Ausência da cadeia Solicitação → Recebimento → ItemRecebimento → ObjetoCustodia → Aceite → AmostraOperacional | Sem ela não há como representar corretamente o processo SEFI aprovado nem garantir a barreira D20. |
| **P0** | Criação direta de `DeviceSample` no endpoint `POST /samples` | Permite iniciar no modelo atual sem demonstrar conferência, reconciliação quantitativa, critérios impeditivos e aceite formal. |
| **P0** | Ausência de quantidades segregadas e fracionamento por objeto | Impede recebimento parcial, desfechos independentes e rastreabilidade de quantidade. |
| **P0** | Ausência de pendências, recusas, checklists e seus ciclos de aprovação | Impede aplicar os critérios E/S/I, saneamento e decisão formal antes do aceite. |
| **P1** | Custódia não separa integralmente confirmação do recebedor e movimentação de localização | Pode atribuir responsabilidade ou localização sem reproduzir as regras D07/D08. |
| **P1** | Anexos/evidências sem serviço de armazenamento e versionamento identificado | Compromete evidência documental e fotográfica, hash, preservação e recuperação. |
| **P1** | Retificação não transversal | Emenda de resultado não cobre alterações de solicitação, recebimento, objeto e dados que afetem ensaios/laudos. |
| **P1** | Competências e autoridades não formalizadas no modelo de autorização | Papéis gerais não bastam para independência, substituição e validação por decisão. |
| **P1** | Backup e restauração sem evidência operacional | Volume persistente não atende sozinho à continuidade e recuperação exigidas. |

## 9. Recomendação de arquitetura de domínio

A recomendação é **não ampliar imediatamente `DeviceSample` para absorver todos os conceitos ausentes**. Isso perpetuaria a divergência semântica observada.

Antes de codificar, produzir um desenho lógico revisado com:

1. **Solicitação** como raiz de vínculo administrativo e de itens declarados.
2. **ItemDeclarado** como item solicitado, com identificação do material e quantidade declarada.
3. **Recebimento** como evento/agregado de chegada física, admitindo mais de uma chegada vinculada à solicitação.
4. **ItemRecebimento** como registro da quantidade efetivamente apresentada e de sua reconciliação com o declarado.
5. **ObjetoCustodia** como unidade física individualizável, passível de divisão e de decisões independentes.
6. **ChecklistAplicado**, **Pendência** e **Decisão de Aceite/Recusa** como registros versionados e auditáveis.
7. **AmostraOperacional** criada somente após a barreira D20, vinculada ao objeto aceito.
8. **EventoCustodia** e **EventoLocalizacao** como eventos distintos, preservando autoria, horários e confirmação.
9. **Documento/Evidência** como entidade própria, vinculada ao contexto de negócio e ao armazenamento controlado.
10. **Ensaio/Resultado/Laudo** vinculados à amostra operacional, com avaliação de impacto em retificações.

O desenho deve explicitar cardinalidades, invariantes, estados, transições, eventos, regras de idempotência, concorrência, assinatura e auditoria. A migração do domínio atual deve ser tratada separadamente, sem presumir equivalência automática dos registros históricos.

## 10. Plano recomendado de trabalho — ainda sem autorização de implementação

| Etapa | Entregável | Critério de saída |
|---|---|---|
| **A** | Matriz de aderência (este documento) | Lacunas e componentes reutilizáveis identificados com evidências. |
| **B** | Modelo lógico revisado M0.3 | Entidades, atributos, cardinalidades, estados, invariantes e eventos aprovados pelo responsável pela validação. |
| **C** | Matriz de rastreabilidade D01–D20 × entidade × regra × API × teste | Cada decisão ligada a uma regra e a evidência verificável; lacunas sem cobertura identificadas. |
| **D** | Estratégia de coexistência/migração do domínio atual | Mapeamento de dados, preservação histórica, reconciliação e rollback documentados. |
| **E** | Plano de testes de domínio e integração | Cenários positivos, negativos, concorrência, idempotência, assinatura, auditoria e barreiras de admissão definidos. |
| **F** | Revisão técnica e decisão formal de Gate G0 | Bloqueadores resolvidos e evidências institucionais/técnicas aceitas. |

A execução das etapas B–F deve ocorrer como trabalho de análise e documentação até que haja autorização expressa para implementação.

## 11. Conclusão e situação formal

- **Aderência do domínio existente ao domínio SEFI:** parcial; insuficiente para o processo de admissão aprovado.
- **Principal divergência:** o código inicia o processo pela criação direta de `DeviceSample`, sem representar a cadeia de solicitação, recebimento, itens, objetos de custódia, conferência e aceite formal.
- **Reutilização recomendada:** autenticação, RBAC como base, assinatura eletrônica, auditoria, mecanismos de concorrência e módulo de ensaios, todos sujeitos às adaptações descritas.
- **Decisão técnica recomendada:** revisar o modelo lógico antes de alterar o código; não tratar `DeviceSample` como sinônimo de `ObjetoCustodia` ou `AmostraOperacional`.

**Gate G0: NÃO APROVADO.**  
**Implementação: NÃO AUTORIZADA.**  
**Escopo desta matriz: inspeção estática e documentação; nenhum código, banco, API, frontend, CI ou infraestrutura foi alterado.**

## 12. Evidências consultadas

Arquivos do repositório examinados nesta versão:

- `docs/DECISOES_PREVALIDACAO_SEFI_D01_D20.md` — versão 1.7, baseline D01–D20 e condições remanescentes.
- `docs/MATRIZ_PRONTIDAO_GATE_G0.md` — versão 0.2, situação do Gate G0 e limitações da inspeção.
- `backend/app/models/__init__.py` — registro dos modelos ORM.
- `backend/app/models/device_sample.py`
- `backend/app/models/chain_of_custody.py`
- `backend/app/models/lab_test.py`
- `backend/app/models/capa_action.py`
- `backend/app/models/audit_log.py`
- `backend/app/models/electronic_signature.py`
- `backend/app/models/user.py`
- `backend/app/models/enums.py`
- `backend/app/schemas/sample.py`
- `backend/app/schemas/test.py`
- `backend/app/schemas/audit.py`
- `backend/app/api/v1/routes/samples.py`
- `backend/app/api/v1/routes/custody.py`
- `backend/app/api/v1/routes/tests.py`
- `backend/app/api/v1/routes/audit.py`
- `backend/app/api/v1/routes/auth.py`
- `backend/app/services/sample_service.py`
- `backend/app/services/custody_service.py`
- `backend/app/services/test_service.py`
- `backend/app/services/signature_service.py`
- `backend/app/services/auth_service.py`
- `backend/app/services/audit_service.py`
- `backend/tests/test_api_flow.py`
- `backend/tests/test_postgres_guards.py`

**Limitação de evidência:** os testes foram lidos, mas não executados nesta atividade. A classificação “inexistente” significa que o componente não foi localizado no conjunto inspecionado; não é afirmação de inexistência em todo e qualquer branch, ambiente ou artefato não consultado.
