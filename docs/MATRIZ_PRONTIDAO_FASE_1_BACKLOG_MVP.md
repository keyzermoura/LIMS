# Matriz de Prontidão da Fase 1 e Backlog Priorizado do MVP

**Identificador:** MPR-LIMS-F1-001  
**Versão:** 0.1  
**Data:** 2026-11-10  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Situação:** Proposta de planejamento para revisão; não aprovada institucionalmente e não autoriza implementação.

## 1. Objetivo e limites

Consolidar a avaliação multidisciplinar (PM, PO, arquitetura, liderança técnica e QA), identificar bloqueadores da primeira entrega, propor o MVP e organizar o backlog em incrementos verificáveis.

Esta matriz é uma linha de trabalho proposta. As validações do responsável pelo projeto registradas em documentos anteriores não equivalem a aprovação institucional. Nenhuma atividade deste documento autoriza alteração de código, banco, migrações, API, frontend, OpenAPI, infraestrutura ou ambiente de produção.

## 2. Decisão de escopo registrada

O MVP da Fase 1 deve contemplar **anexação de arquivos reais**, incluindo fotografias, PDFs e documentos, e não somente referências textuais a evidências.

Os arquivos devem poder ser associados, conforme autorização e desenho final, aos registros pertinentes de solicitação, recebimento, item recebido e ocorrência/pendência. O escopo inclui upload, metadados, consulta/download autorizado, integridade, auditoria e tratamento de falhas.

A decisão não fixa ainda fornecedor ou tecnologia de armazenamento, limites de tamanho, lista definitiva de extensões, prazo de retenção, política de descarte, mecanismo antivírus ou infraestrutura de produção. Esses itens precisam ser definidos antes da implementação do componente de arquivos.

## 3. Diagnóstico integrado

| Área | Situação observada/documentada | Impacto para Fase 1 | Encaminhamento |
|---|---|---|---|
| Produto e operação | O fluxo atual está centrado na criação direta de DeviceSample; solicitação e recebimento ainda não estão materializados como fluxo próprio no runtime inspecionado. | Alto | Entregar fluxo vertical de solicitação, chegada, conferência, decisão e aceite. |
| Domínio | DEC04/DEC05 definem custódia pré-amostra e separação entre item declarado, item recebido, objeto de custódia e amostra. | Crítico | Preservar cardinalidades e semântica na modelagem. |
| Custódia | A estrutura legada ChainOfCustody está ligada obrigatoriamente a DeviceSample. | Crítico | Fechar compatibilização legada/nova antes da migração. |
| Identidade | DeviceSample contém campos obrigatórios que podem não estar disponíveis para todas as classes de materiais. | Alto | Fechar matriz de identidade por classe e regras de aceite (API08). |
| Concorrência/idempotência | Há propostas documentais para expected_version, Idempotency-Key e objeto já aceito; o comportamento final precisa ser demonstrado em runtime e banco. | Crítico | Fechar contrato e critérios de teste API06/API07/API09. |
| Governança | Diretrizes de autorização, autoria, auditoria e assinatura foram validadas em revisão em vários conjuntos; formalização institucional e fechamento técnico continuam pendentes. | Crítico | Delimitar matriz mínima operacional e autoridade institucional. |
| Evidências binárias | Critérios anteriores mencionavam evidências, mas não fechavam ciclo de upload/armazenamento/download seguro. | Alto | Tratar como componente explícito do MVP, com critérios CT-F23 a CT-T15. |
| Migração | Amostras, custódia, QR e demais relações legadas precisam permanecer íntegros. | Crítico | Exigir migração aditiva, reconciliação e plano de recuperação testado. |
| Qualidade | Há critérios propostos e pipeline automatizado; execução verde não substitui homologação funcional nem validação institucional. | Alto | Planejar testes negativos, concorrência, regressão e evidências de aceite. |
| Infraestrutura | Limites do rate limiting em memória e controles de produção não equivalem, isoladamente, a bloqueio do MVP. | Médio/condicional | Registrar riscos e exigir controles proporcionais ao ambiente de implantação. |

**Limite da inspeção:** diagnóstico baseado em documentação e inspeção estática do repositório; não houve execução de testes, build, CI, migração, inspeção de banco implantado ou validação de produção nesta atividade.

## 4. Escopo proposto do MVP

### Incluído
1. Cadastro interno assistido e consulta de solicitação.
2. Solicitação com itens declarados e quantidades.
3. Formalização única da chegada física.
4. Registro de apresentação e conferência individual dos itens.
5. Registro explícito de itens não apresentados.
6. Checklist, observações, divergências, pendências e regularizações versionadas.
7. Anexação de fotografias, PDFs e documentos reais, com metadados e controle de acesso.
8. Custódia desde a chegada física para materiais apresentados, inclusive pendentes ou recusados enquanto estiverem sob guarda.
9. Decisão por item e validação da coordenação quando exigida.
10. Aceite e criação transacional/idempotente de DeviceSample, preservando chegada, recebedor físico, identificadores e QR legado.
11. Histórico e auditoria dos atos críticos.
12. Compatibilidade com registros legados.

### Fora do MVP inicial, salvo exigência institucional
- Portal externo e contas de solicitantes.
- Aplicativo móvel nativo.
- Integrações com instrumentos laboratoriais.
- Painéis analíticos avançados.
- SSO corporativo, se não for pré-requisito institucional de segurança.
- Alta disponibilidade multi-região, cluster de armazenamento e arquitetura WORM dedicada.
- Reformulação integral dos módulos de execução de ensaios e emissão de laudos.

A exclusão de uma tecnologia específica não dispensa controles institucionais de segurança, integridade, retenção, continuidade ou validação que sejam aplicáveis.

## 5. Matriz de bloqueadores e decisões necessárias

| ID | Tema | Estado | Bloqueia implementação? | Saída necessária |
|---|---|---|---|---|
| B01 | Cardinalidade e granularidade DEC01/DEC05 | DEC05 validada como diretriz; fechamento institucional e detalhes operacionais pendentes | Sim, para modelo definitivo | Modelo e exemplos aprovados |
| B02 | Custódia pré-amostra DEC04 | Diretriz validada; compatibilidade legada proposta | Sim | Contrato de custódia e migração revisados |
| B03 | Estados EST01–EST10 | Proposta documental pendente de fechamento | Sim | Matriz de estados/transições e exceções |
| B04 | Eventos e autoria API04/API12 | Catálogo e semântica geral validados; compatibilidade pendente | Sim | Contrato de eventos e timestamps |
| B05 | Identidade API08 | Regras gerais validadas; matriz por classe pendente | Sim | Campos mínimos por classe e validações |
| B06 | Concorrência API06 | Estratégia geral validada; fechamento técnico pendente | Sim | Contrato único de versão e conflitos |
| B07 | Idempotência API07 | Regras gerais validadas; detalhes operacionais pendentes | Sim | Persistência, escopo, retenção e replay |
| B08 | Objeto já aceito API09 | Regras validadas; fechamento técnico pendente | Sim | Precedência de conflitos e testes |
| B09 | Autorização/segregação API10 e GOV | Diretrizes validadas em revisão; autoridade e matriz operacional pendentes | Sim | Matriz de permissão e autoridade formal |
| B10 | Assinatura API05/GOV-P05/P06 | Princípios validados; modalidade e matriz institucional pendentes | Sim para atos que exigem assinatura | Matriz de atos/signatários e contrato |
| B11 | Evidências binárias | Inclusão no MVP confirmada pelo responsável pelo projeto; arquitetura operacional em aberto | Sim para o recurso de anexos | Política e desenho de armazenamento/acesso |
| B12 | Migração e compatibilidade legada | Estratégia proposta; reconciliação real pendente | Sim | Plano de migração/recuperação e evidência |
| B13 | Aprovação institucional e Gate M0 | Pendente | Sim, para iniciar implementação | Aprovação formal e autorização específica |

Itens condicionais: antivírus, WORM, SSO/MFA, rate limiting distribuído e armazenamento externo devem ser avaliados por risco e ambiente; se a política institucional ou o cenário de implantação os tornar obrigatórios, passam a ser bloqueadores.

## 6. Requisitos mínimos do componente de anexos

### 6.1 Modelo lógico e associação
- Cada arquivo deve ter identidade própria e metadados persistidos.
- O vínculo de domínio deve ser explícito e restrito a alvos autorizados.
- Não presumir que qualquer usuário possa anexar a qualquer entidade.
- O arquivo deve permanecer associado ao alvo original mesmo após aceite e criação da DeviceSample.
- A associação deve ser auditável e consultável no histórico pertinente.
- Substituição ou retificação deve gerar novo registro/versão, preservando o original conforme política aprovada.

### 6.2 Metadados mínimos propostos
- Identificador interno do arquivo.
- Nome original informado pelo usuário, tratado como dado não confiável.
- Tipo MIME declarado e tipo efetivamente detectado.
- Extensão validada.
- Tamanho em bytes.
- Hash SHA-256 do conteúdo.
- Identidade autenticada de quem enviou.
- Instante de registro pelo sistema.
- Alvo de domínio e identificador do registro relacionado.
- Estado de processamento/segurança.
- Referência interna de armazenamento, sem expor caminho físico ou URL pública.
- Dados de versão, retenção e descarte quando definidos.

### 6.3 Armazenamento e segurança
- Conteúdo binário em armazenamento privado; metadados e referência controlada no banco.
- Não armazenar arquivos em diretório público do frontend nem servir conteúdo por URL pública permanente.
- Downloads devem passar por autorização no servidor.
- Validar tamanho, extensão, MIME declarado e assinatura/formato real do arquivo.
- Definir allowlist de formatos e limites antes da implementação.
- Verificar conteúdo malicioso antes de disponibilizar o arquivo; quarentena ou controle compensatório formalmente aprovado quando aplicável.
- Evitar execução/preview de conteúdo ativo; tratar HTML, SVG, macros e formatos executáveis como risco específico.
- Definir política de backup, restauração, retenção e descarte.
- Tratar falhas entre gravação binária e transação de metadados, com reconciliação de objetos órfãos.
- Hash comprova igualdade/integridade do conteúdo comparado; não prova, isoladamente, autoria, autenticidade da origem ou imutabilidade do armazenamento.

### 6.4 Escolha tecnológica ainda não fechada
Recomendação arquitetural preliminar: criar uma abstração de armazenamento privado e manter o banco responsável por metadados, estados e vínculos. A implementação pode usar volume privado controlado ou object storage compatível, conforme infraestrutura, backup, capacidade, operação e segurança disponíveis. Não escolher MinIO, S3, WORM ou outro fornecedor antes de levantamento do ambiente e aprovação.

### 6.5 Parâmetros que exigem decisão
- Limite máximo por arquivo e por recebimento.
- Formatos permitidos.
- Quantidade máxima de anexos por alvo.
- Política de retenção e descarte.
- Ferramenta e responsabilidade pela análise antimalware.
- Regras para anexos pendentes, rejeitados e substituídos.
- Perfil autorizado para upload, consulta, download e exclusão lógica.
- Estratégia de backup e teste de restauração.

## 7. Backlog priorizado

| Épico | Prioridade | Entregas/itens | Dependências | Critério de saída |
|---|---|---|---|---|
| E0 — Governança e Gate M0 | P0 | Aprovação de escopo, autoridade, riscos, critérios e autorização de implementação | Decisões institucionais | Gate M0 formalmente registrado |
| E1 — Domínio e estados | P0 | Modelo relacional, cardinalidades, estados, eventos, glossário | DEC01, DEC04, DEC05, EST01–10, API03/04 | Sem ambiguidades bloqueadoras |
| E2 — Identidade e legado | P0 | Matriz por classe, accession_number, QR, migração aditiva e reconciliação | API08, DEC07/08 | Compatibilidade demonstrável |
| E3 — Segurança e governança operacional | P0 | Permissões, segregação, assinatura por ato, autoria, auditoria e exceções | API05/10, GOV-P02/03/05–11 | Matriz e autoridade definidas |
| E4 — Confiabilidade transacional | P0 | expected_version, Idempotency-Key, unicidade, locks e replay | API06/07/09 | Testes concorrentes e de falha |
| E5 — Solicitação e chegada | P1 | Cadastro assistido, itens, chegada única, recebedor físico, retomada | E1, E2, E3 | Fluxo de chegada persistente |
| E6 — Conferência e decisão | P1 | Checklist, quantidades, não apresentado, pendências, regularização, coordenação, aceite/recusa | E1, E3 | Cenários funcionais aprovados |
| E7 — Anexos e evidências | P1 | Upload, validação, armazenamento, hash, antimalware/quarentena, download autorizado, auditoria e backup | E3, E5, política de arquivos | CT-F23–CT-T15 aprovados |
| E8 — Custódia e amostra | P1 | Objeto de custódia, eventos, aceite atômico, DeviceSample, QR e histórico | E1–E4, E6 | Sem duplicidade e sem perda histórica |
| E9 — QA e homologação | P1 | Testes unitários, integração, PostgreSQL, E2E, regressão, segurança e evidências | E5–E8 | Critérios bloqueadores demonstrados |
| E10 — Preparação operacional | P2 | Backup/restauração, monitoramento, procedimentos, treinamento e suporte | E9 e aprovação institucional | Prontidão operacional decidida |

P0 representa pré-condições de desenho, governança e autorização; P1 representa construção funcional após o Gate M0; P2 representa preparação para o uso pretendido. A numeração não equivale a autorização de início.

## 8. Incrementos verticais sugeridos

1. **Incremento A — Solicitação e chegada:** cadastrar solicitação, declarar itens, formalizar chegada única e preservar recebedor/instante físico.
2. **Incremento B — Conferência:** apresentar todos os itens, registrar quantidades, checklist, divergências, não apresentados e pendências.
3. **Incremento C — Evidências:** anexar e recuperar arquivos com controle de acesso, metadados, hash e auditoria.
4. **Incremento D — Decisão e custódia:** registrar custódia de materiais apresentados, inclusive pendentes/recusados, e decisão independente por item.
5. **Incremento E — Aceite e amostra:** criar DeviceSample somente após aceite, com transação, idempotência, concorrência e compatibilidade de QR.
6. **Incremento F — Homologação:** regressão, testes de segurança, migração, restauração e evidências.

## 9. Critérios mínimos de qualidade específicos dos anexos

- Arquivo permitido pode ser enviado e recuperado pelo usuário autorizado.
- Arquivo inválido, corrompido, acima do limite ou com tipo real divergente é rejeitado ou colocado em quarentena.
- Usuário sem autorização não consegue consultar nem baixar o conteúdo, mesmo conhecendo o identificador.
- Nome original não é usado como caminho físico nem como identificador confiável.
- Hash recalculado confere com o hash registrado.
- Reenvio idempotente não duplica anexos indevidamente.
- Substituição preserva vínculo e histórico anterior.
- Falha parcial entre armazenamento e banco é detectável e recuperável.
- Backup e restauração incluem binários e metadados de forma consistente.
- Logs não expõem conteúdo sensível, credenciais ou tokens.

## 10. Riscos principais

| Risco | Consequência | Mitigação proposta |
|---|---|---|
| Definição incompleta de alvos de anexos | Evidências sem contexto ou associação ambígua | Fixar alvos permitidos e regras de vínculo |
| Arquivos maliciosos | Comprometimento do ambiente ou usuários | Allowlist, detecção de tipo, antimalware/quarentena e download controlado |
| Exposição por URL/caminho público | Acesso indevido a evidências | Armazenamento privado e autorização por requisição |
| Perda de binário ou metadado órfão | Evidência incompleta | Operação em etapas, reconciliação e backup testado |
| Retenção indefinida ou descarte indevido | Risco legal/operacional | Política institucional de retenção e descarte |
| Escolha prematura de tecnologia | Custo e complexidade desnecessários | Decidir após levantamento da infraestrutura |
| Expansão do escopo | Atraso do MVP | Congelar formatos, limites e alvos essenciais |
| Migração incompatível | Perda ou quebra de histórico legado | Migração aditiva, cópia representativa e reconciliação |

## 11. Decisões ainda abertas para o componente de arquivos

As seguintes definições permanecem pendentes e não são inferidas pela inclusão de anexos no MVP:
1. Limite por arquivo e por recebimento.
2. Lista permitida de formatos e política para arquivos com macros/conteúdo ativo.
3. Número máximo de arquivos por alvo.
4. Política institucional de retenção, descarte e suspensão de descarte.
5. Ferramenta antimalware e tratamento de indisponibilidade.
6. Armazenamento disponível, backup, restauração e responsáveis operacionais.
7. Permissões detalhadas para anexar, visualizar, baixar, retificar e descartar.
8. Se haverá preview no navegador ou apenas download.
9. Tratamento de dados pessoais/sensíveis contidos nos anexos.

## 12. Gate Review M0 — pauta recomendada

A reunião de M0 deve produzir decisões documentadas sobre:
- escopo do MVP, incluindo anexos reais;
- modelo de domínio, cardinalidades e estados;
- compatibilidade da custódia pré-amostra com legado;
- identidade da amostra e QR;
- contratos de concorrência, idempotência e eventos;
- matriz de autorização, assinatura e auditoria;
- política mínima de anexos e armazenamento;
- plano de migração, rollback/recuperação e critérios de teste;
- responsáveis técnicos, funcionais e institucionais;
- autorização expressa e delimitada para iniciar implementação.

**Resultado esperado:** lista de decisões aprovadas, pendências com responsável e prazo, riscos aceitos formalmente e registro inequívoco do que está ou não autorizado.

## 13. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-10 | Primeira matriz integrada de prontidão, escopo do MVP com anexos reais e backlog priorizado. |
