# Propostas de Decisões Complementares — Gate G0 LIMS-SEFI

**Identificador:** PDC-G0-001  
**Versão:** 0.1 — minuta para validação institucional  
**Data:** 2026-11-22  
**Estado:** PROPOSTA NÃO APROVADA  
**Referência:** D01–D20 e G0-P01–G0-P30, ratificadas; PCR-G0-001 v1.0.

## 1. Finalidade e regra de governança

Este documento organiza as definições complementares que ainda faltam para transformar os modelos já ratificados em parâmetros institucionais, especificações executáveis e evidências de validação.

**Não reabre nem substitui D01–D20 ou G0-P01–G0-P30.** Esses registros aprovam modelos, processos e diretrizes. Os detalhes listados abaixo permanecem pendentes conforme os próprios registros de aprovação.

As recomendações são propostas para apreciação. Nenhuma passa a ser regra institucional até validação explícita e, quando necessário, aprovação da autoridade competente, Qualidade, Jurídico ou TI.

## 2. Resumo executivo dos pacotes

| Pacote | Temas | Referências aprovadas | Situação |
|---|---|---|---|
| A — Governança operacional | Competências, checklists, prazos/comunicações, recusa/devolução/destinação | D05, D06, D10–D12; G0-P01–P04, P16–P18 | Modelo aprovado; parâmetros e designações pendentes |
| B — Identidade e atos eletrônicos | Solicitante externo, autenticação, assinatura, proteção de acesso | D16; G0-P05, P21, P29 | Requisitos/processo aprovados; modalidade, tecnologia e política final pendentes |
| C — Informação e continuidade | Classificação, retenção, backup, RPO/RTO, anexos e trilha de auditoria | D13, D17; G0-P06, P09, P24, P25, P30 | Modelo aprovado; política, parâmetros e arquitetura pendentes |
| D — Regras técnicas de negócio | Resultados/laudos, retificações, agrupamento/fracionamento, migração, consulta/exportação | D09, D18; G0-P10, P22–P23, P26–P28 | Processo aprovado; regras técnicas e parâmetros por categoria pendentes |

## 3. Pacote A — Governança operacional

### A1. Matriz de competências, titulares e substitutos
**Base aprovada:** G0-P01 e G0-P16; D10.

**Pendência real:** designações individuais e formalização institucional. A matriz-modelo já foi aprovada; não é necessário reaprovar o conceito.

**Recomendação:**
- Manter matriz de competências por atividade e ato, não apenas por perfil genérico.
- Cada competência deve identificar titular, substituto formal, autoridade designante, unidade, vigência e limites.
- Distinguir permissão administrativa de autoridade técnica.
- Quando a regra exigir independência, impedir autoaprovação e exigir outro servidor habilitado; substituto só atua durante designação/vigência válida.
- Manter trilha de alterações e revogações.

**Decisão solicitada:** validar esta orientação como padrão de detalhamento; as designações nominais devem ser preenchidas e formalizadas pela autoridade competente, sem inventar nomes ou delegações no LIMS.

### A2. Checklists por categoria e critérios E/S/I
**Base aprovada:** D11–D12; G0-P02 e G0-P17.

**Pendência real:** inventário de categorias e checklists concretos, com referências técnicas e critérios aprovados.

**Recomendação:**
- Não publicar checklist genérico como critério técnico universal.
- Cada checklist deve conter categoria, referência normativa/procedimental e edição, requisito, classe E/S/I, método de verificação, evidência, regra de aceitação, responsável técnico, revisor da Qualidade, aprovador e vigência.
- Critério eliminatório (E) não pode ser convertido em saneável por decisão informal; saneamento (S) deve ter condição objetiva e reavaliação.
- Registrar a versão efetivamente aplicada em cada recebimento; mudança posterior não altera retroativamente recebimentos anteriores.
- Checklist sem aprovação e vigência não pode determinar aceite/recusa.

**Decisão solicitada:** validar estes controles mínimos e a regra de não utilizar checklist ainda não aprovado. Valores e critérios por dispositivo ficam para especialistas técnicos e aprovação formal.

### A3. Prazos, comunicações e prorrogações
**Base aprovada:** D05; G0-P03 e G0-P18.

**Pendência real:** valores, canais oficiais, horários, responsáveis e regras concretas.

**Recomendação:**
- Manter tabela parametrizada por tipo de ocorrência, sem prazo fixo embutido no código.
- Cada regra deve indicar prazo, unidade (dias úteis/corridos), calendário aplicável, marco inicial, canal, destinatário, responsável, antecedência dos alertas e autoridade para prorrogar.
- A contagem só começa após comunicação formal comprovável.
- Prorrogação deve registrar justificativa, solicitante, autorizador e prazo anterior/novo.
- Vencimento gera alerta/estado de atraso; nunca recusa ou encerra automaticamente a pendência.

**Decisão solicitada:** validar a parametrização e as salvaguardas; não propor números de prazo nem canais sem tabela institucional aprovada.

### A4. Recusa, devolução e destinação
**Base aprovada:** D06; G0-P04.

**Pendência real:** formulário, representantes aceitos, alçadas e procedimento de destinação alternativa.

**Recomendação:**
- Separar decisão de recusa do encerramento físico da custódia.
- Exigir motivo, critério, justificativa técnica, evidências, decisor e validação da coordenação quando aplicável.
- Exigir identificação e autorização do representante, conferência de quantidade/condição, entregador, recebedor, data/hora e comprovante.
- Manter custódia sob responsabilidade atual até a confirmação da entrega; destino alternativo exige autorização e comprovante de execução.
- Não encerrar automaticamente por prazo vencido, cancelamento administrativo ou comunicação de recusa.

**Decisão solicitada:** validar o conjunto mínimo de evidências e a separação recusa × destinação efetiva. Formulário, autoridades e fluxos excepcionais serão formalizados pelos setores competentes.

## 4. Pacote B — Identidade e atos eletrônicos

### B1. Solicitantes externos e representantes
**Base aprovada:** G0-P21.

**Pendência real:** política final, prova de identidade, tecnologia e habilitação dos usuários.

**Recomendação:**
- Separar pessoa/organização solicitante, representante declarado e usuário autenticado que opera no sistema.
- Um usuário interno pode registrar solicitação em nome de terceiro, mas não se torna o solicitante.
- Vincular autorização do representante à organização/solicitação, com escopo, vigência e evidência.
- Prever ativação, alteração, suspensão, revogação e recuperação de acesso, com revisão e auditoria.
- Autorizar leitura e ações por solicitação/anexo, não por acesso amplo a todos os registros.

**Decisão solicitada:** validar esses princípios. Método de prova de identidade, federação/SSO e fluxo de recuperação devem ser definidos com TI e autoridade competente.

### B2. Assinatura eletrônica
**Base aprovada:** D16; G0-P05 e G0-P19.

**Pendência real:** modalidade, nível jurídico, certificado/plataforma e tecnologia.

**Recomendação:**
- Fazer inventário dos atos que exigem assinatura e classificá-los por risco e consequência.
- Exigir identificação inequívoca, autenticação proporcional ao risco, intenção explícita, vínculo ao conteúdo/versão, data/hora, integridade e evidência verificável.
- Não escolher previamente certificado, fornecedor ou plataforma.
- Submeter atos com efeito jurídico relevante à avaliação Jurídica e da autoridade competente; envolver TI/Segurança na arquitetura.
- Assinatura não substitui revisão independente ou competência formal.

**Decisão solicitada:** validar a abordagem por classificação de risco e inventário de atos; a modalidade final fica expressamente reservada à avaliação jurídica/institucional.

### B3. Autenticação reforçada e abuso de acesso
**Base aprovada:** G0-P29.

**Pendência real:** decisão de MFA/SSO, limites, alertas, bloqueios, desbloqueio e parâmetros.

**Recomendação:**
- Exigir MFA para administradores e atos críticos, salvo exceção formal com justificativa e controle compensatório.
- Adotar limitação progressiva de tentativas, proteção contra automação/abuso, alertas e trilha de desbloqueio.
- Não bloquear contas de forma irreversível; prever recuperação segura e suporte.
- Definir parâmetros com avaliação de risco, usabilidade e capacidade operacional.

**Decisão solicitada:** validar MFA como recomendação para perfis privilegiados e operações críticas; parâmetros e exceções dependem de TI/Segurança e autoridade competente.

## 5. Pacote C — Informação e continuidade

### C1. Classificação, retenção e destinação da informação
**Base aprovada:** G0-P30; D13 e D17.

**Pendência real:** inventário, classes, prazos, bloqueios legais, arquivamento e eliminação autorizada.

**Recomendação:**
- Classificar separadamente dados cadastrais, registros de solicitação/recebimento, cadeia de custódia, resultados, laudos, assinaturas, auditoria, anexos e logs técnicos.
- Definir por classe: finalidade, responsável, acesso, prazo de guarda, evento inicial de contagem, suspensão por litígio/auditoria, destinação e autoridade aprovadora.
- Não eliminar evidência vinculada a ato formalizado enquanto houver obrigação de guarda ou bloqueio.
- Proibir prazo único para todo o acervo sem análise documental e jurídica.
- Preservar vínculo e proveniência de originais e versões.

**Decisão solicitada:** validar a estrutura de classificação e a regra de que nenhum prazo concreto será parametrizado sem tabela aprovada por autoridade competente/Jurídico/gestão documental.

### C2. Backup, RPO, RTO e recuperação
**Base aprovada:** D17; G0-P06.

**Pendência real:** frequência, retenção, RPO/RTO, cópias segregadas, infraestrutura e testes.

**Recomendação:**
- Definir objetivos por serviço/dado (banco, anexos, PDFs/laudos, auditoria e integrações), em vez de um único número indiscriminado.
- Estabelecer cópias segregadas, criptografia, controle de acesso, proteção contra alteração/exclusão, monitoramento e retenção aprovada.
- Distinguir backup de alta disponibilidade e de arquivamento.
- Exigir testes periódicos de restauração e PITR, com evidência de integridade e medição do RPO/RTO obtido.
- Não declarar recuperação validada por existência de script ou job agendado.

**Decisão solicitada:** validar o modelo por classes de serviço e exigir RPO/RTO formalmente aprovados. Os valores numéricos devem ser definidos por TI/Infraestrutura com os responsáveis pelo processo e aprovados pela autoridade competente.

### C3. Anexos e trilha de auditoria
**Base aprovada:** D13; G0-P09, G0-P24 e G0-P25.

**Pendência real:** formatos, limites, armazenamento, hash, retenção, verificação, WORM/ancoragem e periodicidade.

**Recomendação:**
- Preservar original, versionar substituições e registrar autor, data/hora, finalidade, vínculo, tipo, tamanho e hash.
- Definir lista permitida de formatos e limites por tipo de documento; validar conteúdo real, não apenas extensão.
- Separar autorização de leitura, inclusão, substituição e exportação.
- Proteger logs contra alteração por administradores operacionais; prever verificação de integridade, alertas e retenção.
- Avaliar WORM/ancoragem externa proporcionalmente ao risco, sem assumir tecnologia antes de estudo.
- Registrar e auditar exportações de dados e documentos.

**Decisão solicitada:** validar controles funcionais mínimos; arquitetura, algoritmos, limites e periodicidade serão propostos por TI/Segurança e Qualidade.

## 6. Pacote D — Regras técnicas de negócio

### D1. Resultados reprovados, inconclusivos e emissão de laudos
**Base relacionada:** D01–D20, G0-P12–P15; pendência explicitada no PCR-G0-001.

**Pendência real:** regra de negócio que distingue emitir um laudo com resultado desfavorável de declarar conformidade/aprovação global.

**Recomendação técnica para decisão:**
- Separar **emissão documental** de **conclusão técnica favorável**.
- Um resultado reprovado não deve ser omitido nem convertido em aprovado; o laudo pode, em princípio, documentar resultados desfavoráveis se isso estiver previsto no procedimento e houver revisão/autorização competente.
- Resultado inconclusivo, inválido, não executado ou pendente deve ser explicitamente identificado; não pode ser tratado como aprovado.
- A conclusão global deve derivar de regra aprovada para o conjunto de ensaios aplicáveis, incluindo tratamento de ensaio não aplicável, repetição, invalidação e critérios de decisão.
- Bloquear conclusão favorável quando existir resultado obrigatório reprovado/inconclusivo/pendente, salvo regra técnica formal específica e justificada.
- Não assumir que qualquer resultado reprovado impede a emissão documental; isso pode eliminar evidência necessária à vigilância e à rastreabilidade.

**Decisão solicitada:** validar a separação entre emissão do documento e conclusão favorável. A regra final por tipo de laudo/ensaio deve ser aprovada pelo responsável técnico e Qualidade.

### D2. Agrupamento, fracionamento e amostragem por categoria
**Base aprovada:** G0-P26; M0.2 aprovado; M0.3 ainda sujeito à validação.

**Pendência real:** matriz técnica por categoria, unidades, quantidades, equivalência e categorias fracionáveis.

**Recomendação:**
- Agrupar apenas materiais homogêneos para guarda, avaliação, decisão e destinação.
- Manter quantidade declarada, apresentada, conferida, aceita, fracionada e encaminhada como dimensões distintas, com unidade e reconciliação.
- Cada fracionamento deve preservar origem, motivo, responsável, quantidade anterior/nova, vínculos e trilha.
- Não criar entidade de unidade física universal nesta fase; usar ObjetoCustodia para granularidade quando necessário, conforme M0.2.
- Critérios e quantidades por dispositivo devem vir de matriz técnica aprovada; não presumir conversões ou arredondamentos.

**Decisão solicitada:** validar princípios de homogeneidade e reconciliação. Quantidades e regras por categoria serão submetidas em matriz própria aos especialistas.

### D3. Retificações e impacto em ensaios/laudos
**Base aprovada:** D09; G0-P10 e G0-P27.

**Pendência real:** metodologia detalhada, alçadas, formulários e critérios por etapa.

**Recomendação:**
- Toda retificação após formalização deve preservar original e corrigido, justificativa, evidência, autor, aprovador, data/hora e vínculo entre atos.
- Avaliar impacto antes da autorização: identidade da amostra, plano de ensaio, resultados, incerteza, revisão e laudo.
- Quando afetar identidade/rastreabilidade ou validade de resultado, bloquear continuidade até decisão técnica competente; reensaio ou emenda de laudo conforme análise documentada.
- Nunca alterar retroativamente a evidência original ou ocultar laudo substituído.
- Matriz de impacto deve definir por tipo de campo/etapa se requer revisão, repetição, invalidação, comunicação ou emenda.

**Decisão solicitada:** validar a exigência de avaliação de impacto prévia e trilha imutável; matriz de impacto detalhada será submetida à Qualidade e responsáveis técnicos.

### D4. Migração, idempotência e concorrência
**Base aprovada:** G0-P22 e G0-P23.

**Pendência real:** escopo e cronograma da migração; contratos de repetição, concorrência, versionamento e recuperação.

**Recomendação:**
- Migração somente com inventário, mapeamento de origem, regras de qualidade, reconciliação quantitativa/qualitativa, tratamento de exceções e aprovação dos responsáveis pelos dados.
- Não inferir vínculo de registros sem evidência confiável; manter órfãos/ambiguidades em fila de exceção.
- Para comandos críticos, definir chave de idempotência, escopo, janela de validade, resposta a repetição idêntica/divergente e recuperação após timeout.
- Concorrência deve usar versão esperada, conflito explícito e transação atômica para alteração e auditoria.
- Testar no PostgreSQL alvo; SQLite não substitui prova de concorrência.

**Decisão solicitada:** validar estes princípios. Escopo/cronograma de migração e parâmetros técnicos serão definidos após inventário e análise.

### D5. Consulta histórica, paginação e exportação
**Base aprovada:** G0-P28.

**Pendência real:** filtros, campos, formatos, limites e rastreabilidade.

**Recomendação:**
- Ordenação determinística com desempate por identificador estável; paginação estável sob inserções/alterações.
- Exportação limitada ao escopo autorizado, com finalidade, filtros, usuário, instante, volume e hash/identificador do artefato quando aplicável.
- Campos mínimos por perfil e proteção de dados; não exportar anexos ou dados sensíveis por padrão.
- Limites e formatos definidos por política e capacidade operacional.

**Decisão solicitada:** validar controles de rastreabilidade, escopo e minimização; parâmetros e campos serão definidos em especificação.

## 7. Quadro de decisões solicitadas nesta rodada

Para acelerar a validação, propõe-se apreciar os quatro pacotes em sequência, sem reabrir os modelos já ratificados:

| Pacote | Orientação recomendada para validação | O que permanece fora desta aprovação |
|---|---|---|
| A | Validar controles mínimos de governança operacional A1–A4 | Nomes, designações, critérios técnicos, prazos, canais e formulários concretos |
| B | Validar princípios de identidade externa, assinatura por risco e MFA para perfis privilegiados/atos críticos | Tecnologia, modalidade jurídica, parâmetros, exceções e habilitação real |
| C | Validar classificação por classes, retenção aprovada, recuperação por serviço e controles de anexos/auditoria | Prazos, RPO/RTO, frequência, formatos, limites, infraestrutura e tecnologia |
| D | Validar princípios para laudos, agrupamento/fracionamento, retificação, migração, idempotência e exportação | Regra técnica final por ensaio/categoria, quantidades, cronograma e parâmetros técnicos |

## 8. Limites de efeito

A validação deste documento, se concedida, será validação das orientações e critérios de detalhamento aqui propostos. Não equivale a:
- designar pessoas ou delegar competência;
- aprovar checklist técnico específico;
- fixar prazo, canal, RPO, RTO ou retenção numérica;
- escolher certificado, fornecedor ou plataforma;
- aprovar procedimento técnico por categoria;
- aprovar M0.3, SIM executado, CA aprovado, homologação ou Gate G0;
- autorizar alterações de código, banco, testes, migrações, workflows ou infraestrutura.

## 9. Histórico

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-22 | Primeira minuta de propostas agrupadas para fechamento de decisões complementares pendentes do Gate G0. |
