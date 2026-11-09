# Critérios de Aceite — Fase 1: Solicitação e Recebimento

**Identificador:** CT-ACE-LIMS-001  
**Versão:** 0.1  
**Situação:** Proposta para revisão funcional, técnica e institucional; não aprovada para homologação  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Data:** 2026-11-09

---

## 1. Objetivo

Definir critérios verificáveis para avaliar a futura implementação da Fase 1 do LIMS, cujo escopo é estruturar solicitação, chegada física, recebimento, conferência por item, decisão, custódia pré-amostra e criação controlada da amostra operacional.

Este documento estabelece o que deverá ser demonstrado. Não declara que qualquer funcionalidade já esteja implementada, validada ou homologada.

## 2. Escopo da Fase 1

### Incluído no escopo proposto
- cadastro interno assistido de solicitação;
- registro de vários itens declarados por solicitação, sujeito à aprovação institucional da DEC01;
- um único recebimento principal por solicitação;
- apresentação e conferência independente de cada item;
- registro de itens não apresentados;
- checklist, observações, justificativas, pendências e evidências;
- decisões individuais por item;
- validação da coordenação quando exigida;
- início e continuidade da custódia desde a chegada física;
- criação da amostra operacional e identificador institucional somente após aceite final e validações obrigatórias;
- auditoria e histórico das alterações e decisões;
- compatibilidade com amostras legadas, identificadores e QR Codes existentes.

### Fora do escopo, salvo aprovação posterior
- portal ou contas externas para solicitantes;
- reformulação integral do ciclo de ensaios;
- substituição de todos os mecanismos atuais de assinatura eletrônica;
- migração retroativa indiscriminada de amostras antigas;
- remoção do fluxo legado de criação de amostras;
- implantação em produção ou autorização de uso regulado.

## 3. Classificação dos critérios

| Classe | Significado |
|---|---|
| **Bloqueador** | Falha impede aceite da entrega. |
| **Maior** | Falha exige correção antes da liberação operacional, salvo dispensa formal e justificada pela autoridade competente. |
| **Menor** | Não compromete requisito essencial; deve ser registrado e planejado. |
| **Informativo** | Observação sem reprovação, usada para acompanhamento. |

A classificação definitiva e a autoridade para aceitar desvios devem ser aprovadas institucionalmente. Nenhum critério impeditivo de segurança, integridade, rastreabilidade ou decisão formal poderá ser dispensado apenas por conveniência operacional.

## 4. Critérios funcionais

| ID | Critério verificável | Evidência esperada | Classe proposta |
|---|---|---|---|
| CT-F01 | O usuário interno consegue cadastrar e localizar uma solicitação, identificando o solicitante e a origem da demanda. | Roteiro de teste, registros persistidos e trilha de auditoria. | Bloqueador |
| CT-F02 | A solicitação comporta os itens declarados conforme regra aprovada, preservando descrição, identificação e quantidade declarada. | Teste com solicitação de um item e de vários itens. | Bloqueador |
| CT-F03 | O sistema permite registrar no máximo um recebimento principal por solicitação. | Teste de duplicidade e constraint no banco. | Bloqueador |
| CT-F04 | Uma segunda tentativa de recebimento localiza e apresenta o recebimento existente, sem criar outro registro. | Teste funcional e teste concorrente/API. | Bloqueador |
| CT-F05 | O recebimento apresenta todas as linhas declaradas, inclusive as não apresentadas. | Cenário com itens apresentados e não apresentados. | Bloqueador |
| CT-F06 | A situação de apresentação é distinta da decisão técnica do item. Item não apresentado não é registrado como recusado. | Testes de estados e persistência. | Bloqueador |
| CT-F07 | Quantidade declarada e quantidade efetivamente apresentada são armazenadas separadamente. | Testes com quantidades iguais e divergentes. | Bloqueador |
| CT-F08 | A conferência, checklist, observações, justificativas e evidências são registrados por item, com autoria e data/hora. | Teste de dois itens com respostas distintas e trilha. | Bloqueador |
| CT-F09 | Pendências e regularizações preservam as avaliações anteriores, sem apagar ou sobrescrever o histórico. | Teste de abertura, regularização e consulta do histórico. | Bloqueador |
| CT-F10 | Cada item pode receber decisão independente, conforme critérios e permissões aprovados. | Matriz de cenários de aceite, pendência e recusa. | Bloqueador |
| CT-F11 | A validação da coordenação ocorre quando exigida e não permite dispensar critérios impeditivos. | Testes de permissão, transição e bloqueios. | Bloqueador |
| CT-F12 | Item não apresentado não gera unidade recebida, custódia de material ausente nem amostra operacional. | Testes de integridade e consulta. | Bloqueador |
| CT-F13 | A custódia do material apresentado começa na chegada física, antes da criação da amostra operacional. | Linha do tempo com chegada, guarda e aceite posterior. | Bloqueador |
| CT-F14 | A criação da amostra operacional ocorre somente após aceite final e validações obrigatórias. | Testes positivos e negativos de transição. | Bloqueador |
| CT-F15 | A amostra criada preserva a data/hora original da chegada e a identidade do recebedor físico, sem confundir esses dados com a data de criação. | Comparação dos registros e eventos de custódia. | Bloqueador |
| CT-F16 | A criação da amostra e do identificador institucional é atômica, única e idempotente. | Testes de falha transacional, repetição e concorrência. | Bloqueador |
| CT-F17 | O identificador institucional não depende de prefixo de laboratório e respeita o escopo aprovado. | Teste de unicidade e decisão formal sobre formato/escopo. | Bloqueador |
| CT-F18 | O fluxo preserva o QR Code e a localização de amostras históricas. | Testes com QR Codes legados e novos. | Bloqueador |
| CT-F19 | A interface permite alternar entre as duas telas principais, salvar e retomar o trabalho sem impor sequência linear. | Roteiro de usabilidade e persistência. | Maior |
| CT-F20 | O modal de conferência apresenta checklist, observações, justificativas e evidências, alerta sobre alterações não salvas e suporta rolagem interna. | Testes de interface em resoluções suportadas. | Maior |
| CT-F21 | Atos formais e correções protegidas exigem confirmação, justificativa e autorização conforme matriz aprovada. | Testes de permissões e auditoria. | Bloqueador |
| CT-F22 | O sistema impede inclusão retroativa de material não apresentado na chegada original, salvo exceção formal aprovada e rastreável. | Testes de bloqueio e fluxo excepcional, se aprovado. | Bloqueador |

## 5. Critérios de dados, integridade e migração

| ID | Critério verificável | Evidência esperada | Classe proposta |
|---|---|---|---|
| CT-D01 | Registros legados permanecem consultáveis e utilizáveis nos fluxos mantidos. | Testes de regressão com amostras anteriores. | Bloqueador |
| CT-D02 | Nenhum identificador histórico é renumerado ou reutilizado. | Relatório de reconciliação antes/depois. | Bloqueador |
| CT-D03 | Nenhuma solicitação, recebimento ou unidade é inventada para amostra antiga sem evidência confiável. | Relatório de migração e inspeção de vínculos. | Bloqueador |
| CT-D04 | Eventos históricos de custódia, resultados, assinaturas e auditoria permanecem íntegros. | Verificação de hashes, relações, contagens e timestamps. | Bloqueador |
| CT-D05 | Novas relações e constraints não tornam inválidos os registros legados sem vínculo. | Testes de schema e integridade referencial. | Bloqueador |
| CT-D06 | Migrações Alembic são reproduzíveis em banco vazio e em cópia representativa do schema anterior. | Logs de execução e resultado de Alembic. | Bloqueador |
| CT-D07 | A estratégia de rollback/recuperação foi testada em ambiente isolado. | Evidência de restauração e relatório de recuperação. | Bloqueador |
| CT-D08 | A reconciliação registra contagens, exceções e diferenças, com aprovação dos responsáveis. | Relatório assinado ou aprovado no processo institucional. | Bloqueador |

## 6. Critérios técnicos e de qualidade

| ID | Critério verificável | Evidência esperada | Classe proposta |
|---|---|---|---|
| CT-T01 | Regras críticas são garantidas no backend e no banco, não apenas na interface. | Testes de serviço, API e constraints. | Bloqueador |
| CT-T02 | Restrições de unicidade e concorrência impedem recebimentos e amostras duplicados. | Testes concorrentes com PostgreSQL. | Bloqueador |
| CT-T03 | Autorização é verificada no servidor para cada ação e transição protegida. | Testes negativos por perfil e chamada direta à API. | Bloqueador |
| CT-T04 | Alterações, decisões, regularizações e transferências são auditáveis, com ator, data/hora, ação e contexto suficiente. | Consultas e testes de trilha. | Bloqueador |
| CT-T05 | Falhas transacionais não deixam registros parciais ou identificadores consumidos de forma inconsistente, conforme regra aprovada. | Testes de falha em pontos intermediários. | Bloqueador |
| CT-T06 | Testes automatizados passam em PostgreSQL 16 e SQLite, quando aplicável, sem substituir testes específicos do PostgreSQL. | CI verde e relatórios por banco. | Bloqueador |
| CT-T07 | Typecheck e build do frontend passam; validação de Compose e smoke tests passam. | Logs de CI vinculados ao commit avaliado. | Maior |
| CT-T08 | Não há regressão nos fluxos existentes de amostras, ensaios, QR, custódia, auditoria e CAPA. | Suíte de regressão e roteiro manual. | Bloqueador |
| CT-T09 | Erros apresentados ao usuário são compreensíveis e não expõem segredos, tokens ou dados indevidos. | Testes de API/UI e revisão de segurança. | Maior |
| CT-T10 | Logs e monitoramento permitem investigar falhas sem registrar credenciais ou dados sensíveis desnecessários. | Revisão de configuração e evidências de teste. | Maior |

## 7. Critérios de segurança, operação e conformidade

Antes de qualquer uso institucional, devem ser avaliados e aprovados, conforme aplicabilidade:
- perfis, segregação de funções e prevenção de autoaprovação indevida;
- gestão, armazenamento, rotação e recuperação de segredos;
- TLS, CORS, exposição de API e controles de sessão;
- MFA e reautenticação para atos críticos;
- armazenamento, acesso, integridade, retenção e backup de evidências;
- backup, restauração, continuidade e resposta a incidentes;
- gestão de ambientes, dados de teste e dados reais;
- adequação dos controles de auditoria e assinatura ao uso pretendido;
- avaliação de risco e validação do sistema computadorizado conforme sistema de qualidade institucional.

A aprovação do CI ou dos critérios técnicos não substitui avaliação de qualidade, validação, qualificação ou homologação institucional.

## 8. Cenários mínimos de teste ponta a ponta

1. Solicitação com um item, apresentado e aceito.
2. Solicitação com vários itens, todos apresentados, com decisões diferentes.
3. Solicitação com parte dos itens não apresentada.
4. Quantidade apresentada inferior à declarada.
5. Item com pendência, regularização e aceite posterior, preservando histórico.
6. Item recusado, com justificativa e custódia/destino definidos.
7. Item que exige validação da coordenação.
8. Tentativa de aceite sem concluir critério impeditivo.
9. Tentativa de criar amostra antes do aceite final.
10. Reenvio da operação de criação de amostra.
11. Duas requisições concorrentes para o mesmo item.
12. Falha durante transação de aceite/criação.
13. Consulta de amostra legada sem solicitação/recebimento.
14. Leitura de QR Code histórico após a evolução.
15. Consulta da linha do tempo completa desde a chegada física até a custódia da amostra.

Os cenários devem ser refinados após decisões DEC04, DEC05, DEC07, DEC08 e EST01–EST10.

## 9. Evidências e rastreabilidade dos testes

Cada caso de teste deverá registrar:
- identificador do requisito/critério;
- versão do caso de teste;
- pré-condições e dados de teste;
- ambiente e versão do sistema;
- versão do banco e revisão Alembic;
- passos executados;
- resultado esperado e observado;
- evidência objetiva (log, captura, relatório ou consulta controlada);
- responsável pela execução e data/hora;
- desvios, defeitos e vínculo com correção;
- reexecução e resultado após correção;
- responsável pela revisão/aprovação, quando aplicável.

Dados de teste devem ser sintéticos ou formalmente autorizados e protegidos.

## 10. Portões de decisão

### G0 — Aprovação do escopo e desenho antes da implementação
Pré-condições propostas:
- decisões bloqueadoras do domínio resolvidas ou formalmente delimitadas;
- glossário, modelo conceitual, estados/transições e estratégia de migração revisados;
- exemplos operacionais reais validados;
- papéis e responsabilidades identificados;
- escopo, riscos e critérios de aceite aprovados;
- autorização explícita para iniciar implementação.

### G1 — Aceite técnico da implementação em ambiente de teste
- critérios bloqueadores aplicáveis aprovados;
- suíte automatizada e regressão aprovadas;
- migrações testadas e reconciliadas;
- segurança e permissões verificadas;
- defeitos remanescentes classificados e tratados.

### G2 — Validação funcional e de qualidade
- roteiros executados por usuários designados;
- evidências revisadas;
- desvios avaliados;
- procedimentos, treinamento e responsabilidades definidos;
- validação do sistema conforme sistema de qualidade institucional.

### G3 — Homologação e autorização operacional
- aprovação formal da autoridade competente;
- plano de implantação e recuperação aprovado;
- ambiente, acessos, backup, monitoramento e suporte preparados;
- autorização de uso registrada.

A aprovação de um portão não implica aprovação automática dos seguintes.

## 11. Pendências que impedem congelar os critérios

| Referência | Pendência | Impacto |
|---|---|---|
| DEC01 | Aprovação institucional da solicitação com múltiplos itens | Estrutura funcional e testes |
| DEC04 | Nível de registro da custódia e transferência para amostra | Modelo e critérios de custódia |
| DEC05 | Granularidade item/unidade/amostra/corpo de prova | Cardinalidades e contagens |
| DEC07 | Papel final do accession_number e formato do identificador | Identidade, QR e compatibilidade |
| DEC08 | Política de migração e associação do legado | Integridade histórica |
| DEC09 | Atos que exigem assinatura eletrônica | Segurança e evidências |
| DEC10 | Categorias e checklists versionados | Conferência |
| DEC11 | Escopo organizacional da primeira entrega | Permissões e arquitetura |
| DEC12 | Retenção, backup e recuperação | Operação e continuidade |
| EST01–EST10 | Perfis, segregação de funções e transições excepcionais | Autorização e estados |

## 12. Critério de conclusão da Fase 1

A Fase 1 somente poderá ser considerada concluída quando:
1. todos os critérios bloqueadores aplicáveis tiverem evidência aprovada;
2. os critérios maiores estiverem resolvidos ou formalmente aceitos pela autoridade competente, com justificativa e plano;
3. não houver defeitos abertos que comprometam integridade, segurança, rastreabilidade ou operação;
4. regressões e migrações estiverem aprovadas;
5. documentação técnica e funcional refletir a implementação entregue;
6. evidências de teste estiverem preservadas e rastreáveis;
7. houver decisão formal sobre a passagem para validação funcional/qualidade.

Conclusão técnica da Fase 1 não equivale a validação institucional nem autorização de uso em produção.

## 13. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-09 | Primeira proposta de critérios de aceite funcionais, de dados, técnicos e de governança para a Fase 1. |
