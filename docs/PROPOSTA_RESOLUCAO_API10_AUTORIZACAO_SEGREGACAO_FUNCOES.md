# Proposta de Resolução da Decisão API10 — Autorização e Segregação de Funções

**Identificador:** PROP-LIMS-API10-001  
**Versão:** 0.7  
**Data:** 2026-11-10  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Situação:** Proposta técnica para revisão; não aprovada para implementação

---

## 1. Objetivo e limites

Definir uma proposta conceitual para autorização das operações do fluxo de solicitação, recebimento e custódia, incluindo segregação de funções, escopo de acesso e identificação dos atores.

Este documento não declara que os papéis aqui descritos já existam na FUNED, não cria delegações de competência e não substitui normas, portarias, procedimentos ou decisões da autoridade institucional competente. Os papéis e regras são capacidades propostas, sujeitas a validação funcional, técnica, de segurança e institucional.

A proposta não autoriza alterações em código, banco de dados, migrações, endpoints, frontend, OpenAPI, testes, build, CI ou infraestrutura.

## 2. Princípios orientadores

1. **Negação por padrão:** toda operação é negada, salvo concessão explícita de permissão compatível com o escopo.
2. **Menor privilégio:** conceder somente as ações e os dados necessários à atribuição funcional vigente.
3. **Autorização no servidor:** a interface pode ocultar ações, mas a decisão efetiva deve ocorrer no backend em toda requisição.
4. **Autenticação não é autorização:** JWT válido identifica uma sessão/principal; não concede, por si só, direito de executar qualquer operação.
5. **Identidade do ator confiável:** o usuário autenticado que registra uma ação deve ser obtido do contexto de segurança, não aceito livremente como identidade declarada no payload.
6. **Segregação proporcional ao risco:** separar execução, validação e assinatura quando a natureza do ato ou a política institucional exigir.
7. **Rastreabilidade:** registrar concessões relevantes, decisões de autorização, alterações de atribuição e exceções administrativas com autoria e instante.
8. **Sem bypass de critérios técnicos:** nenhum papel de coordenação, administração ou validação pode dispensar requisito impeditivo, evidência obrigatória ou regra técnica do recebimento.
9. **Escopo limitado:** acesso deve respeitar setor, unidade organizacional, atribuição ao processo e necessidade de conhecimento, conforme política aprovada.
10. **Sem acesso externo na primeira entrega:** solicitantes externos não recebem contas nem acesso direto à API nesta etapa; o cadastro é assistido por usuário interno.

## 3. Modelo conceitual de autorização

Recomenda-se avaliar uma abordagem híbrida:

- **RBAC (controle baseado em papéis):** agrupa capacidades funcionais, como registrar chegada, conferir, decidir aceite ou consultar auditoria.
- **Atributos/escopo (ABAC):** restringe a permissão por unidade/setor, atribuição ao recebimento, estado do objeto, classe de material, vínculo com a operação e outras condições relevantes.

A combinação é uma recomendação arquitetural para avaliação, não uma decisão de tecnologia. A implementação deverá evitar permissões exclusivamente globais quando o processo exigir escopo por unidade ou atribuição.

### 3.1 Dimensões da decisão de autorização

Para cada requisição, avaliar no mínimo:

- principal autenticado e situação da conta;
- capacidade/permissão necessária à operação;
- escopo organizacional e atribuição válida ao registro;
- estado atual do agregado e pré-condições do fluxo;
- eventual conflito de interesse ou regra de segregação;
- autorização específica para exceção, quando prevista;
- autorização atual no momento da execução, inclusive em repetição idempotente.

A autorização deve ser reavaliada no servidor em cada operação. Não confiar em permissões antigas armazenadas apenas no frontend ou em claims de sessão que possam ter sido revogadas, sem mecanismo adequado de atualização/revalidação.

## 4. Papéis funcionais propostos — não presumidos como existentes

Os nomes abaixo representam capacidades conceituais. A instituição deverá definir nomenclatura, lotação, autoridade, substituição e critérios de atribuição.

| Papel/capacidade proposta | Atuação possível | Limites importantes |
|---|---|---|
| Registrador de solicitação/chegada | Cadastrar solicitação assistida e formalizar dados da chegada conforme procedimento | Não se torna automaticamente recebedor físico, conferente ou decisor |
| Recebedor físico | Confirmar quem recebeu material e o instante/local da chegada | Identidade deve refletir a pessoa que efetivamente recebeu; não pode ser substituída pelo usuário que digitou posteriormente |
| Conferente | Executar checklist, registrar condição, divergências, evidências e pendências | Não pode alterar critérios nem declarar aceite fora de sua competência |
| Executor de regularização | Registrar saneamento e evidências de pendências | Não apaga conferência anterior nem valida automaticamente o próprio saneamento |
| Decisor de aceite/recusa | Praticar decisão formal sobre item/objeto, dentro de competência definida | Não pode dispensar critérios impeditivos ou evidências obrigatórias |
| Validador/coordenação | Revisar e validar etapas quando o fluxo exigir | Não substitui requisitos técnicos nem pode forçar aceite incompatível com critérios |
| Custodiante | Entregar/receber responsabilidade de guarda e confirmar transferência conforme procedimento | Não equivale automaticamente a administrador ou decisor técnico |
| Signatário | Assinar conteúdo/ato específico para o qual possua competência | Assinatura deve corresponder à pessoa real, ao alvo e ao conteúdo apresentados |
| Administrador técnico | Gerenciar configuração técnica e acessos conforme delegação | Não recebe automaticamente poderes de decisão laboratorial ou de alteração de registros de negócio |
| Auditor/consulta | Consultar registros e trilhas dentro do escopo autorizado | Preferencialmente sem capacidade de mutação; acesso a dados sensíveis deve ser justificado e registrado |

Uma mesma pessoa poderá acumular capacidades somente quando isso for permitido pela matriz institucional de segregação e não houver conflito de interesse ou impedimento específico.

## 5. Matriz preliminar de operações e capacidades

Legenda: **P** = permissão necessária proposta; **C** = condicional ao procedimento/escopo; **—** = não concedida por padrão. A matriz não atribui competências a cargos reais.

| Operação | Registrador | Recebedor físico | Conferente | Executor regularização | Decisor | Validador/coordenação | Custodiante | Signatário | Admin técnico | Auditor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Consultar solicitação/recebimento | P | C | P | C | P | P | C | C | C | P |
| Criar solicitação assistida | P | — | — | — | — | C | — | — | — | — |
| Formalizar chegada | P | C | — | — | — | C | — | C | — | — |
| Registrar identidade do recebedor físico | C | P/C | — | — | — | C | — | — | — | — |
| Executar conferência/checklist | — | C | P | — | — | C | — | C | — | — |
| Registrar evidência/pendência | C | C | P | P | C | C | C | — | — | — |
| Registrar regularização | — | — | C | P | — | C | — | — | — | — |
| Validar regularização | — | — | C | — | C | P/C | — | C | — | — |
| Aceitar/recusar objeto | — | — | C | — | P/C | P/C | — | C | — | — |
| Transferir custódia | — | — | — | — | — | C | P/C | C | — | — |
| Registrar mudança de localização | — | — | — | — | — | C | P/C | C | — | — |
| Devolver/destinar/encerrar | — | — | — | — | P/C | P/C | C | C | — | — |
| Retificar registro formal | — | — | C | C | C | P/C | — | C | — | — |
| Consultar histórico/auditoria | C | C | P | C | P | P | C | C | C | P |
| Administrar usuários/permissões | — | — | — | — | — | — | — | — | P/C | C |

A matriz deve ser detalhada por operação, classe de material, unidade/setor, etapa do processo e nível de risco. “C” exige definição expressa antes da implementação; não é autorização implícita.

### 5.1 Regra validada em revisão — formalização da chegada física

O responsável pelo projeto validou, em revisão, a seguinte diretriz para a operação de formalização da chegada física:

- Qualquer servidor que possua permissão específica para essa operação poderá formalizar a chegada, mesmo que não seja a pessoa que recebeu materialmente o objeto.
- O registro deve identificar corretamente o recebedor físico efetivo (`received_by`) e preservar separadamente o usuário autenticado que realizou o lançamento (`recorded_by`).
- A identidade do recebedor físico não pode ser preenchida automaticamente com a identidade do registrador, nem substituída pelo usuário que posteriormente confere ou aceita o objeto.
- A permissão para formalizar a chegada deve ser concedida explicitamente e respeitar o escopo organizacional/funcional aplicável.
- Essa formalização registra a chegada e inicia a custódia; não representa conferência concluída, aceite técnico ou criação automática de `DeviceSample`.

A validação acima é uma diretriz do projeto em revisão, não uma aprovação institucional de competência funcional nem autorização para implementação. Permanecem pendentes a definição dos perfis institucionais reais, do mecanismo de comprovação do recebedor físico, dos escopos e das demais operações da matriz.


### 5.2 Regra validada em revisão — conferência dos materiais

O responsável pelo projeto validou, em revisão, a seguinte diretriz para a operação de conferência dos materiais apresentados:

- A conferência poderá ser executada por servidor com permissão específica de conferente, respeitado o escopo organizacional/funcional aplicável.
- O conferente poderá registrar os itens efetivamente apresentados, as quantidades recebidas, as condições físicas e de integridade, as divergências identificadas, as evidências e as pendências pertinentes.
- A permissão de conferência, isoladamente, não concede competência para decidir o aceite ou a recusa do material.
- A decisão de aceite/recusa permanece atribuída ao papel/capacidade de decisor definido na matriz institucional, observadas as validações adicionais exigidas pelo fluxo.
- O registro da conferência deve preservar autoria, instante e histórico das informações, sem apagar ou sobrescrever silenciosamente registros anteriores.

A validação acima é uma diretriz do projeto em revisão, não uma aprovação institucional da competência de cargos ou servidores nem autorização para implementação. Permanecem pendentes a definição dos perfis institucionais reais, eventuais regras de segregação/validação da conferência, os requisitos específicos por classe de material e a compatibilização com os contratos das APIs relacionadas.

### 5.3 Regra validada em revisão — registro e validação da regularização

O responsável pelo projeto concordou, em revisão, com a seguinte diretriz para a regularização de pendências:

- Servidor com permissão específica poderá registrar a regularização da pendência que executou.
- O registro deverá conter a providência adotada, as evidências correspondentes, a identificação de quem executou a regularização e a data/hora do registro, mantendo referência inequívoca à pendência original.
- A regularização não apaga, substitui ou sobrescreve a pendência nem os registros anteriores; o histórico deve permanecer rastreável.
- Quando o fluxo exigir validação da regularização, esta deverá ser realizada por outro servidor autorizado, distinto do executor.
- A permissão para registrar a regularização não concede automaticamente permissão para validá-la nem para decidir o aceite/recusa do material.

A validação acima é uma diretriz do projeto em revisão, não uma aprovação institucional de competências funcionais nem autorização para implementação. Permanecem pendentes a definição dos casos em que a validação será obrigatória, dos critérios de validação, dos perfis institucionais e da compatibilização com os contratos e estados das APIs relacionadas.

### 5.4 Regra validada em revisão — decisão de aceite ou recusa

O responsável pelo projeto concordou, em revisão, com a seguinte diretriz para a decisão sobre o material recebido:

- O aceite ou a recusa constituem atribuição específica, concedida a servidor com permissão de decisor e escopo compatível.
- A permissão de decisor é independente das permissões de conferência e de registro de regularização; possuir uma dessas permissões não concede automaticamente a outra.
- Antes de decidir, o decisor deverá avaliar os registros da conferência, as pendências e suas regularizações e os critérios obrigatórios aplicáveis ao material.
- A decisão deverá ser formalmente registrada e vinculada ao objeto recebido, com identificação do decisor, instante e justificativa quando houver recusa.
- A decisão não poderá dispensar critérios técnicos impeditivos, evidências obrigatórias ou outras pré-condições do fluxo. A coordenação não poderá contornar esses controles.

A validação acima é uma diretriz do projeto em revisão, não uma aprovação institucional de competências funcionais nem autorização para implementação. Permanecem pendentes a definição dos perfis institucionais e autoridades competentes, os critérios específicos por classe de material, os casos de validação adicional/assinatura e a compatibilização técnica com os contratos e estados das APIs relacionadas.

### 5.5 Regra validada em revisão — validação pela coordenação

O responsável pelo projeto concordou, em revisão, com a seguinte diretriz para a validação pela coordenação:

- A validação da coordenação será condicional, não constituindo etapa obrigatória para todos os recebimentos.
- Sua exigência deverá decorrer de critérios e situações previamente definidos em procedimento institucional aprovado, considerando, por exemplo, classe de material, risco, ocorrência ou regra específica do processo, sem presumir esses critérios antes da definição institucional.
- Quando exigida, a coordenação poderá revisar a documentação e as evidências, verificar o cumprimento das etapas obrigatórias e registrar a validação ou apontar inconsistências.
- A validação da coordenação não substitui a decisão formal de aceite/recusa atribuída ao decisor autorizado.
- A coordenação não poderá dispensar critérios técnicos impeditivos, evidências obrigatórias ou pré-condições do fluxo, nem forçar aceite incompatível com essas regras.
- A decisão de exigir ou não a validação deverá ser rastreável, com fundamento no critério/procedimento aplicável.

A validação acima é uma diretriz do projeto em revisão, não uma aprovação institucional dos critérios de obrigatoriedade nem autorização para implementação. Permanecem pendentes a definição institucional dos casos, critérios e autoridade de coordenação, além da compatibilização com os estados e contratos das APIs relacionadas.

### 5.6 Regra validada em revisão — transferência de custódia

O responsável pelo projeto concordou, em revisão, com a seguinte diretriz para a transferência de custódia:

- A transferência deverá ser realizada por usuário com permissão específica de custodiante e escopo compatível com o objeto e a operação.
- O registro deverá identificar expressamente o custodiante responsável pela entrega e o custodiante responsável pelo recebimento. A identidade de ambos não poderá ser presumida apenas a partir do usuário que registrou a operação.
- A transferência deverá gerar registro rastreável, vinculado ao objeto sob custódia, preservando a autoria do registro e o instante efetivo da transferência.
- Como conteúdo mínimo proposto para o evento, deverão ser registrados o objeto transferido, custodiante de origem/entrega, custodiante de destino/recebimento, data e hora efetivas e local de origem e destino. Motivo/justificativa deverá ser registrado quando aplicável conforme procedimento.
- A permissão para transferir custódia não concede automaticamente permissão para decidir aceite/recusa, validar recebimento ou alterar dados da conferência.
- A operação deverá preservar a sequência histórica dos eventos, sem sobrescrever transferências anteriores.

A validação acima é uma diretriz do projeto em revisão, não aprovação institucional da política de custódia, dos perfis ou da modalidade de confirmação dos participantes, nem autorização para implementação. Permanecem pendentes a definição institucional dos papéis, escopos, forma de confirmação da entrega/recebimento, exceções operacionais e compatibilização técnica com API04, API05, API06, API07 e o modelo de custódia.

## 6. Segregação de funções e autoaprovação

### 6.1 Regra de desenho

Recomenda-se que a política institucional defina, para cada ato decisório:

- se o autor do registro pode também executar a conferência;
- se o conferente pode regularizar a própria pendência;
- se quem registrou a chegada pode decidir o aceite;
- se quem executou o ensaio/conferência pode validar o próprio resultado;
- se o mesmo usuário pode ser custodiante de origem e destino;
- se o signatário pode ser também o executor ou validador;
- quais combinações exigem pessoa distinta e quais são permitidas em situações justificadas.

Não se presume uma proibição universal de acumulação de papéis. Entretanto, para operações de maior impacto — especialmente aceite/recusa, validação final, retificação formal, destinação e encerramento — recomenda-se avaliar segregação entre executor e aprovador, com prevenção de autoaprovação quando exigida pela política institucional.

### 6.2 Controle de autoaprovação

Quando a regra aplicável exigir atores distintos, o backend deve comparar identidades autenticadas/registradas dos participantes relevantes e bloquear a operação se houver coincidência vedada. A regra deve ser aplicada no servidor e na transação, não apenas por desabilitação de botão.

Se a política permitir acumulação em determinada situação, registrar a base normativa/procedimental e a justificativa quando exigido. Não criar exceção silenciosa nem permitir que o próprio usuário altere sua permissão para contornar o bloqueio.

### 6.3 Coordenação e critérios impeditivos

A validação de coordenação deve funcionar como etapa de revisão dentro dos critérios aprovados. Não pode:

- dispensar requisito classificado como impeditivo;
- substituir evidência obrigatória por justificativa genérica;
- converter item não apresentado em apresentado;
- alterar retroativamente a chegada física;
- aceitar objeto que não cumpriu pré-condições técnicas;
- criar amostra operacional sem aceite e validações obrigatórias.

## 7. Identidades e autoria: campos semanticamente distintos

A autorização não deve colapsar pessoas diferentes em um único campo genérico de usuário. Manter as distinções conceituais:

| Identidade | Significado |
|---|---|
| `recorded_by` | Usuário autenticado que persistiu o registro no sistema |
| `received_by` | Pessoa que efetivamente recebeu fisicamente o material |
| `performed_by` | Pessoa que executou a atividade operacional |
| `validated_by` | Pessoa que validou/revisou a etapa, quando exigido |
| `signer` | Pessoa que assinou o conteúdo/ato |
| `from_custodian` | Responsável pela guarda antes da transferência |
| `to_custodian` | Responsável pela guarda após a transferência |

Uma pessoa pode ocupar mais de uma dessas posições apenas quando permitido. O usuário que registra uma chegada em nome de outra pessoa não deve ser automaticamente gravado como recebedor físico. Da mesma forma, quem aceita o objeto não substitui o recebedor original nem o custodiante efetivo.

A API deve derivar `recorded_by` da sessão. Campos que representem terceiros ou participantes devem ter semântica e validação próprias; não podem ser usados para forjar a identidade do ator autenticado.

## 8. Relação com API05 — assinatura eletrônica

A autorização para executar uma operação e a assinatura do ato são controles diferentes:

- estar autorizado não significa que a operação exige assinatura;
- apresentar uma assinatura não concede autorização para a operação;
- autenticação JWT e registro em AuditLog não equivalem a assinatura eletrônica;
- o signatário deve ter permissão para assinar aquele tipo de ato e aquele alvo;
- a autorização e a segregação devem ser verificadas antes de concluir o ato assinado.

A matriz final API05 × API10 deverá identificar, por operação, se a assinatura é obrigatória, condicional ou não exigida, quem pode assinar e se o signatário deve ser distinto do executor/validador. Preservar o snapshot imutável e o vínculo com o alvo definidos na proposta API05.

## 9. Relação com API06, API07 e API09

1. **API06 — concorrência:** autorização, estado, versão e segregação devem ser verificados dentro da operação protegida contra concorrência. Não permitir que uma requisição autorizada sobre estado antigo conclua uma ação incompatível com o estado atual.
2. **API07 — idempotência:** em replay, revalidar a autorização atual do principal antes de revelar o snapshot/resposta original. Uma chave idempotente não é credencial nem concede acesso. Se a permissão tiver sido revogada, negar a resposta protegida sem executar novamente o efeito.
3. **API09 — objeto já aceito:** a resposta de nova operação para objeto já aceito não deve revelar identificadores, dados ou existência de amostra a principal sem autorização de consulta adequada. A regra de precedência semântica de API09 não elimina a autorização. Preservar o replay da mesma chave/hash, sujeito à revalidação de autorização atual prevista em API07.

A política de autorização deve ser aplicada antes de expor detalhes de estado que permitam enumeração de objetos ou amostras. A escolha entre 403 e resposta indistinguível de 404 para recursos fora do escopo deve ser definida pela política de segurança e documentada de forma consistente.

## 10. Administração de acessos e exceções

### 10.1 Administração

- Separar administração técnica de concessão de competência funcional.
- Exigir atribuição explícita e rastreável de permissões, escopos e períodos de validade.
- Registrar autor da concessão, aprovador quando exigido, destinatário, escopo, motivo, início/fim e alterações/revogação.
- Impedir que uma conta técnica ou administrador obtenha automaticamente capacidade de aceitar, recusar ou assinar atos laboratoriais.
- Prever revisão periódica de acessos, desligamento, afastamento, mudança de setor e substituição temporária.
- Não permitir autoconcessão de privilégios sem controle independente formalmente aprovado.

### 10.2 Exceções emergenciais

Se a instituição admitir acesso emergencial (“break-glass”), a política deverá definir previamente:

- situações objetivas que o justificam;
- quem pode acioná-lo e quais dados/ações ficam liberados;
- justificativa obrigatória e prazo curto de validade;
- alerta/notificação e revisão posterior independente;
- trilha imutável do acesso e de todas as ações;
- operações que permanecem proibidas mesmo em emergência.

A proposta não cria autorização emergencial por si só. Na ausência de política aprovada, a regra é negar.

## 11. Respostas e comportamento HTTP — orientação conceitual

- **401 Unauthorized:** ausência de autenticação válida ou sessão não aceita.
- **403 Forbidden:** principal autenticado sem permissão para a operação ou fora do escopo, quando a política não exigir ocultação do recurso.
- **404 Not Found:** pode ser usado para não revelar existência de recurso fora do escopo, desde que a política de segurança escolha essa estratégia de forma consistente.
- **409 Conflict:** reservado a conflito de estado/negócio ou regras de concorrência, como VERSION_CONFLICT e OBJECT_ALREADY_ACCEPTED; não deve substituir indiscriminadamente falhas de autorização.

A API não deve aceitar papel, permissão ou escopo como declaração livre do cliente. O payload pode identificar o participante funcional de um ato quando necessário, mas o servidor deve verificar se a pessoa indicada existe, está ativa, tem vínculo válido e pode ocupar aquela função.

## 12. Requisitos de auditoria

Registrar, conforme criticidade e política de retenção:

- principal autenticado e identidade efetiva;
- operação e recurso/alvo;
- decisão de autorização (permitida/negada) e motivo/código interno;
- escopo avaliado e versão relevante da política/permissão;
- participantes funcionais envolvidos;
- concessão, revogação ou alteração de acesso;
- acionamento de exceção e revisão posterior;
- data/hora de registro e correlação da requisição.

Evitar registrar tokens, segredos ou dados excessivos. A trilha de auditoria não deve permitir alteração silenciosa por quem executa a operação auditada.

## 13. Questões que exigem validação funcional e institucional

1. Quais unidades/setores e funções reais participarão de cada etapa?
2. Quem pode formalizar a chegada e como será comprovado o recebedor físico?
3. Quais operações exigem dupla atuação ou ator distinto?
4. O conferente pode regularizar a própria pendência? Quem valida a regularização?
5. Quem possui competência para aceitar/recusar cada classe de material?
6. Em quais casos a coordenação valida e quais critérios são impeditivos?
7. Quais atos exigem assinatura e quais regras de independência do signatário? (API05)
8. Como serão atribuídos e revogados escopos por unidade, setor, processo e substituição?
9. Haverá exceção emergencial? Qual autoridade, prazo, escopo e revisão?
10. Qual estratégia de ocultação de recursos fora do escopo será adotada (403 ou 404)?
11. Quais dados de auditoria de autorização serão retidos e quem poderá consultá-los?
12. Como a política será aplicada a contas administrativas e integrações técnicas?

## 14. Critérios de aceite documental da API10

A proposta somente poderá ser considerada fechada após:

- matriz de operações e capacidades revisada pelos responsáveis funcionais;
- papéis reais, escopos e delegações confirmados institucionalmente;
- regras de segregação e autoaprovação definidas por operação;
- integração com API05 (assinatura) e API06/API07/API09 (concorrência, replay e objeto aceito) reconciliada;
- política de administração, exceções, auditoria e ocultação de recursos aprovada;
- revisão técnica de segurança e autorização server-side;
- contratos HTTP e modelo de dados atualizados como propostas documentais, sem alteração física antecipada.

## 15. Encaminhamento e controle de execução

**Atividade realizada:** elaboração da proposta API10 e registro das validações, em revisão do projeto, (i) da formalização da chegada por servidor especificamente autorizado, distinto do recebedor físico, preservando `recorded_by` e `received_by`; (ii) da conferência por servidor autorizado, sem competência automática para decidir aceite/recusa; e (iii) do registro da regularização pelo executor, com validação independente por outro servidor autorizado quando exigida; e (iv) da decisão de aceite/recusa como atribuição específica, independente das permissões de conferência e regularização, sem dispensa de critérios impeditivos; e (v) da validação da coordenação como etapa condicional, exigida somente nos casos definidos institucionalmente e sem substituir o decisor ou dispensar critérios impeditivos; e (vi) da transferência de custódia por usuário com permissão específica, identificando expressamente quem entrega e quem recebe e mantendo registro rastreável.

**Não realizado:** alterações em código, banco de dados, migrações, endpoints, frontend, OpenAPI, testes, build, CI ou infraestrutura.

**Estado:** regras gerais das Operações 1 (formalização da chegada física), 2 (conferência dos materiais), 3 (regularização de pendências), 4 (decisão de aceite/recusa), 5 (validação condicional pela coordenação) e 6 (transferência de custódia com identificação dos responsáveis pela entrega e pelo recebimento) validadas pelo responsável pelo projeto em revisão. Definição institucional dos casos e critérios de validação obrigatória, demais operações, perfis e autoridades institucionais, escopos, segregação, revisão técnica e aprovação institucional permanecem pendentes. Implementação bloqueada até fechamento documental, aprovações aplicáveis e autorização específica.

## 16. Histórico de alterações

| Versão | Data | Alteração |
|---|---|---|
| 0.1 | 2026-11-10 | Criação da proposta técnica API10 para autorização, escopo, segregação, autoria, auditoria e integração com API05–API09. |
| 0.2 | 2026-11-10 | Registro da validação em revisão da regra de formalização da chegada por servidor autorizado distinto do recebedor físico, preservando `recorded_by` e `received_by`. |
| 0.3 | 2026-11-10 | Registro da validação em revisão da conferência por servidor especificamente autorizado, sem competência automática para decidir aceite/recusa. |
| 0.4 | 2026-11-10 | Registro da validação em revisão do registro de regularização pelo executor e da validação independente por outro servidor autorizado quando exigida. |
| 0.5 | 2026-11-10 | Registro da validação em revisão da decisão de aceite/recusa como atribuição específica, independente da conferência e regularização, sem dispensa de critérios impeditivos. |
| 0.6 | 2026-11-10 | Registro da validação em revisão da validação condicional pela coordenação, exigida somente nos casos definidos institucionalmente e sem substituir o decisor ou dispensar critérios impeditivos. |
| 0.7 | 2026-11-10 | Registro da validação em revisão da transferência de custódia com permissão específica, identificação expressa dos responsáveis pela entrega e pelo recebimento e histórico rastreável. |
