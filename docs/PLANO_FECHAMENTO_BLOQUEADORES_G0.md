# Plano de Fechamento Acelerado dos Bloqueadores do Gate G0

**Versão:** 1.2  
**Data:** 2026-11-22  
**Baseline examinada:** branch `main`, commit `e276c8739c4726155f4e228f9b5092cff1f0699a`  
**Natureza:** plano de auditoria e preparação de correções; não autoriza implementação.

## 1. Objetivo e regra de execução

Reduzir o retrabalho e o número de intervenções institucionais agrupando os achados por causa-raiz. A execução será feita em pacotes de trabalho, com auditoria estática, proposta de correção, critérios de aceite e evidências requeridas. A documentação pode ser consolidada; código, banco, migrações, testes, frontend, workflows, configuração e infraestrutura permanecem bloqueados até autorização expressa e aprovação do Gate G0.

## 2. Situação CI confirmada no baseline

Workflow `CI`, run [44972881963](https://github.com/keyzermoura/LIMS/actions/runs/44972881963), associado exatamente ao commit `e276c8739c4726155f4e228f9b5092cff1f0699a`:
- Backend: **failure**.
- Docker: **failure**.
- Segurança (SAST/SCA): **success**.
- Front-end: **failure**.

### 2.1 Causas-raiz objetivamente confirmadas

**CI-01 — Identificador de revisão Alembic excede o limite do banco.**  
A migração `0022_official_reports_attributes_immutable` define revision ID com 38 caracteres. O PostgreSQL cria `alembic_version.version_num` com `varchar(32)` no fluxo de CI e falha ao atualizar a revisão. O `backend/alembic/env.py` já configura `version_num_length=64`, mas a configuração do contexto não altera retroativamente a coluna criada no banco de teste. A falha ocorre durante `alembic upgrade head`; os testes PostgreSQL subsequentes não são alcançados. A proposta de correção deve avaliar a criação explícita de `alembic_version` com largura compatível antes da primeira migração, preservando compatibilidade com bancos já existentes e com o caminho SQLite. Não encurtar identificadores ou alterar migrações sem avaliar histórico e ambientes implantados.

**CI-02 — package.json e package-lock.json estão dessincronizados.**  
`frontend/package.json` declara `@playwright/test ^1.49.0`, enquanto o lockfile não contém os pacotes `@playwright/test`, `playwright` e `playwright-core` requeridos pelo manifesto. `npm ci` falha tanto no job Front-end quanto na etapa de build Docker. O lockfile também mantém versão raiz `0.1.0`, enquanto o manifesto está em `1.1.0`. A correção proposta é regenerar o lockfile a partir do manifesto e verificar a versão resolvida, scripts E2E e reprodutibilidade; não editar o lock manualmente.

### 2.2 Efeito no alcance dos testes

Como as migrações falham antes dos testes PostgreSQL, e a instalação frontend falha antes do typecheck/build, os jobs não demonstram esses resultados. O Docker falha no estágio de instalação do frontend; build das imagens e smoke test integral não são comprovados. O job de segurança passou nessa execução, sem que isso equivalha a homologação do produto.

## 3. Pacotes de trabalho por causa-raiz

| Pacote | Escopo agrupado | Saída necessária | Dependência |
|---|---|---|---|
| P1 — Reprodutibilidade CI | Alembic/PostgreSQL, lock npm, build Docker, ordem dos testes | Proposta técnica única, CI verde em execução completa, logs e artefatos | Autorização técnica |
| P2 — Admissão e custódia | Solicitação, itens apresentados/não apresentados, conferência, aceite, recusa, transferência e encerramento | Fluxo canônico, matriz de transições, invariantes e cenários negativos | Baseline D01–D20/G0-P01–P30; validação institucional quando houver ambiguidade |
| P3 — Segurança contextual | Autorização por ação, vínculo organizacional, escopo de solicitação/amostra/evidência, segregação de funções | Matriz ator × ação × recurso × contexto, testes de negação e trilha | P2 para recursos e estados canônicos |
| P4 — Integridade transacional | Idempotência, concorrência, locks, atomicidade, histórico e eventos | Matriz de comandos críticos, invariantes de banco e testes concorrentes | P2/P3 |
| P5 — Ensaios, revisão e laudos | Execução, resultados, revisão, emissão, imutabilidade, emendas e CAPA | Ciclo de vida verificável, transições e testes | P2/P4 |
| P6 — Continuidade operacional | Backup, restauração, PITR, segredos, readiness e recuperação | Evidências de backup/restore, política RPO/RTO e validação de operação | Decisões de infraestrutura |
| P7 — Qualidade e homologação | CA01–CA37, SIM01–SIM12, pacotes GOV e Gate G0 | Rastreabilidade teste–execução–log–resultado–aceite | P1–P6 e participação SEFI |

## 4. Ordem de execução acelerada

1. Fechar diagnóstico estático P1 e elaborar proposta de correção agrupada.
2. Auditar P2 e P3 em conjunto, pois estados de admissão determinam os contextos de autorização.
3. Auditar P4 sobre os comandos e transições canônicos definidos em P2.
4. Auditar P5 em conjunto com os invariantes de integridade P4.
5. Tratar P6 em paralelo, sem misturar evidência de infraestrutura com evidência funcional.
6. Atualizar matrizes centrais e só então executar a reconciliação final CA/SIM/GOV.
7. Submeter os pontos institucionais pendentes em blocos de até 5–10 decisões, sem solicitar microaprovações técnicas.

## 5. Papéis e responsabilidades

- **Auditoria/arquitetura:** inspeção, rastreabilidade, análise de causa-raiz, proposta técnica e critérios de teste.
- **Desenvolvimento/DevOps:** implementação e execução de correções após autorização.
- **Responsável institucional SEFI:** validação dos fluxos, critérios operacionais e evidências de uso.
- **Coordenação/gestão competente:** decisões de governança, designações, políticas e aceite formal.
- **Infraestrutura/TI:** parâmetros de segurança, backup, retenção, recuperação e operação.

Nenhum nome individual é presumido neste plano.

## 6. Critérios mínimos para encerrar cada pacote

- **P1:** migrações aplicam do zero em PostgreSQL e SQLite quando suportado; `alembic check` sem drift; `npm ci` reproduz dependências; typecheck/build passam; Docker build e smoke test executam; testes relevantes têm logs e resultados identificáveis.
- **P2:** estados, eventos, transições e regras de custódia não apresentam contradições com baseline; casos de exceção e rejeição cobertos; histórico preservado.
- **P3:** toda operação sensível valida ator, papel, vínculo, recurso, estado e contexto; testes positivos e negativos comprovam negação por padrão.
- **P4:** comandos críticos são atômicos e idempotentes; concorrência não duplica protocolo, amostra, transferência ou emissão; trilha não é sobrescrita.
- **P5:** execução, revisão, aprovação, emissão e emenda são separadas e auditáveis; laudo oficial e evidências preservam imutabilidade conforme regra aprovada.
- **P6:** backup é agendado, monitorado e retido; falhas não são mascaradas; restauração independente é demonstrada; RPO/RTO são aprovados.
- **P7:** cada CA tem requisito, teste, execução, resultado e evidência; cada SIM tem protocolo, participantes, registros e aceite; Gate é deliberado formalmente.

## 7. Decisões que podem exigir validação institucional

Somente serão escaladas decisões sem resposta inequívoca nos documentos aprovados, por exemplo: papéis e substituições; exigência de dupla conferência; critérios de aceite/recusa; prazos e canais; política de assinatura; regras de transferência e encerramento físico; destinação de itens recusados; RPO/RTO e retenção; critérios de homologação. A auditoria deverá apresentar opções, impactos e recomendação, evitando perguntas abertas desnecessárias.

## 8. Limites e parecer

Esta versão confirma duas causas-raiz de CI por logs e leitura estática: largura insuficiente do identificador Alembic no banco de teste e lock npm incompatível com o manifesto. Não altera qualquer arquivo técnico. A análise dos pacotes P2–P7 ainda requer auditoria por causa-raiz e evidência atualizada.

**Gate G0: NÃO APROVADO. Implementação SEFI: NÃO AUTORIZADA.**  
Este plano organiza o fechamento; não representa aceite, homologação nem autorização de mudança técnica.


## 9. Auditoria estática inicial P2/P3 — 2026-11-22

Leitura estática dos arquivos no mesmo HEAD `e276c8739c4726155f4e228f9b5092cff1f0699a`. Os achados abaixo são constatações do código inspecionado; não substituem teste de exploração, execução automatizada ou análise de todas as rotas.

### 9.1 P2 — Admissão e custódia

**P2-01 — Modelo implementado de recebimento diverge do fluxo aprovado para item não apresentado.**  
Em `backend/app/services/receipt_service.py`, `create_receipt` cria cada `ReceiptItem` com `PresentationStatus.PRESENTED`, usa a quantidade declarada como apresentada e cria imediatamente `CustodyObject` em `SOB_GUARDA` com evento de ingresso. Não há, nesse trecho, captura individual da quantidade realmente apresentada nem alternativa para `NAO_APRESENTADO`. Isso conflita com EST-REC-001, que separa apresentação de decisão e proíbe iniciar custódia para item não apresentado. Correlaciona-se com SIM02 e achados anteriores sobre criação prematura de custódia. Requer redesign do comando de recebimento, não apenas ajuste de tela.

**P2-02 — Transferência de custódia é efetivada pelo ato de quem entrega, sem aceite do destinatário.**  
Em `backend/app/services/custody_service.py`, `transfer` registra evento, atualiza imediatamente `current_custodian_id` e localização para o destino, e confirma a transação. A rota exige assinatura do usuário autenticado que solicita a transferência, mas não há etapa de confirmação/assinatura do destinatário nesse fluxo. O estado passa a refletir nova guarda antes de evidência de recebimento pelo destino. Diverge da proposta EST-REC-001 e SIM07, que exigem transferência pendente até confirmação. A correção deve modelar solicitação e confirmação como eventos/estados distintos.

**P2-03 — API legada de amostras mantém trilha paralela ao novo recebimento.**  
As rotas `/samples` e `/solicitations/{id}/receipt` expõem fluxos distintos para registrar amostras/entrada e formalizar recebimento. A rota de criação de amostra exige assinatura, mas a trilha de recebimento cria objetos de custódia e ainda não demonstra a integração de aceite/checklist com o accession institucional da amostra. Necessário definir uma única fronteira de criação da amostra operacional após decisão favorável, evitando que rotas paralelas contornem o fluxo de admissão.

### 9.2 P3 — Segurança contextual

**P3-01 — Autorização observada é predominantemente por papel, sem escopo por recurso/organização nos caminhos examinados.**  
As rotas de solicitações usam `CurrentUser` ou `require_roles`; as rotas de amostras e histórico de custódia também autenticam o usuário. Entretanto, `solicitation_service.get_solicitation` consulta somente pelo UUID e `list_solicitations` não aplica filtro por criador, organização ou vínculo. `sample_service.get_sample/list_samples` igualmente consulta sem filtro contextual. Isso permite, para qualquer conta autenticada com acesso à rota, que a autorização por papel seja insuficiente para separar solicitações/amostras por escopo institucional. O impacto efetivo depende da política de acesso aprovada e dos perfis habilitados, mas a defesa contextual não está demonstrada nesses caminhos.

**P3-02 — Conta externa/solicitante declarado não está separada por autorização contextual na API examinada.**  
O modelo `Solicitation` armazena dados declarados do solicitante e `created_by_id` do usuário autenticado, mas os caminhos de leitura não demonstram vínculo entre a identidade autenticada e a solicitação. Isso não prova que exista uma conta externa habilitada; demonstra que a API examinada não aplica esse vínculo nas consultas citadas. A separação conceitual entre solicitante declarado e usuário autenticado precisa ser refletida em política e consultas.

**P3-03 — QR de verificação expõe dados cadastrais e não tem expiração temporal.**  
A rota `/samples/verify` exige usuário autenticado, mas o token QR é validado com `verify_exp=False` e a resposta retorna número de série, lote, fabricante, nome comercial e status. A decisão de tornar esse conteúdo acessível por QR e sua retenção temporal precisa ser alinhada à política institucional de confidencialidade e rastreabilidade. O achado é de exposição/escopo e governança de dados; não se conclui exploração externa, pois a rota requer autenticação.

### 9.3 Sinais positivos que devem ser preservados

- Transferência usa `SELECT ... FOR UPDATE` e versão otimista da amostra.
- Eventos de custódia e registros de auditoria são persistidos na mesma transação do comando examinado.
- A criação da amostra exige token de assinatura vinculado à entidade e ação.
- A API aplica autenticação nas rotas de leitura examinadas.

Esses controles são positivos, mas não corrigem a ausência de confirmação do destinatário nem substituem autorização contextual por recurso.

### 9.4 Encaminhamento

P2-01/P2-02 devem ser tratados como um único redesenho de admissão e custódia; P2-03 depende desse desenho para consolidar a criação de amostra. P3-01/P3-02 formam uma única camada de autorização contextual (ator × organização/vínculo × recurso × estado × ação). P3-03 requer decisão de política de exposição do QR e revisão técnica separada.

**Limites:** não foram executados testes, chamadas exploratórias ou alterações técnicas. A análise abrange os caminhos e arquivos explicitamente citados, não todas as rotas do sistema.


## 10. Auditoria aprofundada P2/P3 e rechecagem CI — 2026-11-22

### 10.1 Rechecagem CI após publicação documental

A execução mais recente no HEAD `80ed9a5ee745d89f1cf78f3f2d2b11565cc1c6a1`, run `44973391327`, repetiu o mesmo quadro: Backend FAILURE, Front-end FAILURE, Docker FAILURE e Segurança SUCCESS. Os logs confirmam novamente:
- PostgreSQL: `value too long for type character varying(32)` ao atualizar `alembic_version.version_num` para `0022_official_reports_attributes_immutable`.
- Front-end: `npm ci` falha porque `@playwright/test@1.65.1`, `playwright@1.65.1` e `playwright-core@1.65.1` estão ausentes do lockfile.
- Docker: falha no estágio `RUN npm ci --no-audit --no-fund`, antes de build e smoke test completos.

Isso demonstra que a publicação de documentação não alterou nem resolveu os bloqueadores técnicos. CI continua não verde.

### 10.2 P2 — refinamento dos achados de admissão e custódia

**P2-04 — Aceite técnico pode ser invocado sem comprovação de conferência concluída.**  
O serviço `receipt_service.accept_custody_object` verifica que o objeto está `SOB_GUARDA` e que a versão corresponde, mas não verifica diretamente que o `ReceiptItem` esteja com conferência concluída, apresentação positiva e decisão compatível com o aceite. Como o objeto é criado no recebimento inicial, a rota de aceite pode, pela lógica examinada, ser chamada antes da conferência. É necessário tornar o aceite dependente de pré-condições explícitas e testadas.

**P2-05 — Conferência pode alterar apresentação após criação de custódia sem reconciliar os objetos.**  
`conference_item` atualiza `presentation_status`, `presented_quantity`, `conference_status` e `decision`, mas não cria, ajusta, bloqueia ou encerra os `CustodyObject` já criados para o item. Assim, a situação física conferida pode divergir da quantidade/estado representado pelos objetos em custódia. Deve existir reconciliação transacional entre resultado da conferência e objetos físicos; itens não apresentados não podem permanecer representados como objetos sob guarda.

**P2-06 — Transferência de objeto não exige aceite do destinatário e não usa bloqueio pessimista no carregamento mostrado.**  
`transfer_custody` carrega o objeto por `get_custody_object`, compara versão e altera custodiante/local na mesma operação, sem etapa de confirmação do destinatário e sem `SELECT FOR UPDATE` no trecho examinado. O controle otimista existe, mas precisa ser avaliado sob concorrência real e não substitui o fluxo de confirmação exigido pelo domínio. O endpoint legado `/custody/transfer` também realiza transferência imediata e mantém outra representação de custódia.

**P2-07 — Duas APIs de transferência e dois modelos de custódia permanecem ativos.**  
O sistema mantém o fluxo legado de `DeviceSample/ChainOfCustody` (`/custody/transfer`) e o novo fluxo de `CustodyObject/CustodyEvent` (`/custody/objects/{id}/transfers`). Também coexistem criação direta de amostra em `POST /samples` e geração de amostra via aceite de objeto. É necessária uma decisão arquitetural de consolidação, compatibilidade e desativação controlada; não se deve remover legado sem mapear dados e consumidores.

### 10.3 P3 — refinamento da autorização e QR

**P3-04 — Modelo de usuário não contém vínculo organizacional/institucional.**  
O modelo `User` examinado contém papel, credenciais e atributos de segurança, mas não apresenta campo ou relacionamento de unidade/organização/laboratório. As consultas de solicitação e amostra não aplicam filtro contextual. A política multiunidade e a distinção entre acesso global institucional e acesso restrito por unidade ainda precisam ser modeladas; não basta acrescentar filtro sem definir os papéis e exceções aprovados.

**P3-05 — QR não verifica expiração temporal.**  
`verify_qr_payload` chama `jwt.decode` com `options={... "verify_exp": False}`. A rota `GET /samples/verify` exige usuário autenticado, mas o token QR não tem expiração efetivamente verificada nesse caminho. A resposta retorna identificador/acession, série, lote, fabricante, nome comercial e status. Requer decisão institucional sobre validade, revogação, finalidade e conjunto mínimo de dados exibidos.

### 10.4 P2/P3 — recomendação de arquitetura convergente

A proposta consolidada é adotar uma única cadeia de estados:
1. Solicitação submetida.
2. Chegada física registrada, sem presumir apresentação integral.
3. Conferência item a item, com quantidade efetiva e estado de apresentação.
4. Objetos de custódia criados somente para material efetivamente apresentado e sob guarda, vinculados à quantidade física observada.
5. Transferência com estado pendente até confirmação pelo destinatário; somente então muda o custodiante efetivo.
6. Aceite técnico condicionado à conferência concluída e decisão favorável.
7. Geração do identificador institucional da amostra após aceite favorável, vinculada ao objeto de custódia e ao histórico.
8. Recusa e destinação física registradas separadamente, sem apagar a trilha.

Para segurança, adotar autorização contextual baseada em ator, papel, unidade institucional, recurso, estado e ação, com negação por padrão; contas de serviço recebem escopos próprios. A política deve prever explicitamente os perfis com acesso transversal. QR deve carregar identificador opaco e mínimo de informação, com validade e revogação conforme política aprovada.

### 10.5 Itens que exigem validação institucional consolidada

A auditoria deverá levar à validação SEFI, em bloco:
- Quem pode registrar chegada, conferir, decidir aceite/recusa, transferir e confirmar recebimento.
- Se conferência e aceite podem ser feitos pela mesma pessoa ou quando se exige revisão independente.
- Tratamento de divergência entre quantidade declarada e apresentada.
- Destinação e registro de material recusado/não apresentado.
- Quais unidades podem consultar solicitações/amostras de outras unidades e quais papéis possuem acesso transversal.
- Finalidade do QR, dados visíveis, validade, revogação e público autorizado.
- Política de compatibilidade e migração dos dois modelos legados de custódia/amostra.

**Limites:** constatações baseadas na leitura estática dos arquivos indicados e logs do run citado. Não houve execução local de testes, exploração dinâmica, alteração de código ou decisão sobre política institucional.
