# Registro de Validação Institucional das Decisões SEFI — D01 a D20

**Identificador:** DEC-SEFI-001  
**Versão:** 1.6  
**Data:** 2026-11-10  
**Repositório:** `keyzermoura/LIMS`  
**Branch:** `main`  
**Situação:** D01–D20 ratificadas integralmente pelo responsável pela Validação Institucional do LIMS – SEFI, em 2026-11-10. A ratificação das regras não equivale à homologação operacional, aprovação do Gate G0 ou autorização de implementação.

## 1. Objetivo e limites

Consolidar as vinte decisões tomadas sequencialmente e ratificadas integralmente pelo responsável pela Validação Institucional do LIMS – SEFI em 2026-11-10. Este registro complementa EST-REC-001, MOD-DOM-001, a auditoria EST01–EST10, a revisão multidisciplinar e a simulação SIM01–SIM12.

As decisões abaixo constituem a baseline funcional ratificada institucionalmente pelo responsável designado para essa validação. A ratificação não substitui definições institucionais complementares, análise jurídica quando aplicável, validação operacional com usuários, testes de aceitação ou homologação. Nenhuma alteração de código, banco de dados, API, frontend, CI ou infraestrutura está autorizada por este registro.

## 2. Matriz consolidada

| ID | Tema | Decisão pré-validada |
|---|---|---|
| D01 | Responsável pelo registro da chegada | Perfil RECEPÇÃO registra a chegada. A mesma pessoa pode também conferir se possuir ambas as permissões; recebimento e conferência permanecem eventos distintos, com autoria e horários próprios. |
| D02 | Dados da chegada | Registrar solicitação vinculada, data/hora efetivas, recebedor identificado, entregador quando disponível ou ausência dessa informação, volumes, descrição externa, condição da embalagem, observações/avarias, documentos apresentados, fotos quando pertinentes e timestamp automático do registro. A chegada física pode ser registrada mesmo com divergência ou documentação incompleta. |
| D03 | Quantidades | Preservar separadamente quantidades declarada, apresentada, aceita, recusada e não apresentada; justificar divergências; permitir recebimento parcial; itens recusados ou não apresentados não geram amostras. |
| D04 | Divisão de item | Um ItemRecebimento pode originar múltiplos ObjetosCustodia, cada qual com identificação, quantidade, evidências, decisão e histórico próprios. Permitir desfechos distintos por objeto; amostra somente para objeto aceito e validado. |
| D05 | Pendências saneáveis | Registrar pendência individual, descrição, classificação, responsável, comunicação formal, timestamp, prazo conforme tabela institucional, alertas, prorrogação justificada/autorizada, evidência e reavaliação obrigatória. Vencimento gera PRAZO_VENCIDO, sem recusa ou encerramento automático. |
| D06 | Recusa | Registrar motivo, critério não atendido quando aplicável, justificativa técnica, evidências, decisor, validação da coordenação nos casos previstos, comunicação ao solicitante e forma de devolução/destinação. Recusa não encerra custódia; encerramento exige comprovação da destinação efetiva. |
| D07 | Transferência de custódia | Evento próprio com objeto, entregador, recebedor, horários efetivo e de registro, localização quando aplicável e confirmação do novo custodiante. Até a confirmação, responsabilidade permanece com o custodiante anterior. |
| D08 | Mudança de localização | Evento separado da transferência, registrando objeto, origem, destino, responsável, horários e justificativa conforme o tipo. Não altera o custodiante. |
| D09 | Retificação após amostra/ensaio | Procedimento excepcional, justificado, com valores original e corrigido preservados, evidências, autorização/validação prévia, assinatura eletrônica e avaliação de impacto sobre amostras, ensaios e laudos. Sem apagar histórico ou simular retroatividade. |
| D10 | Acumulação e validação independente | Permitir acumulação de funções conforme permissões. Bloquear autoaprovação quando independência for obrigatória. Encaminhar a outro servidor habilitado ou autoridade/substituto formalmente designado. Perfil administrador não confere autoridade técnica automática. |
| D11 | Checklists | Checklists específicos por categoria, com critérios E (eliminatório), S (saneável) e I (informativo), aprovação formal, versionamento e histórico. Preservar a versão efetivamente aplicada em cada recebimento. |
| D12 | Governança dos checklists | Especialista técnico elabora/propõe; Qualidade revisa; Coordenação ou autoridade designada aprova; Administrador publica após aprovação. Registrar responsáveis, justificativas, versões e vigência. Administrador não altera critérios técnicos em produção sem aprovação formal. |
| D13 | Documentos e evidências | Vincular anexos à solicitação, recebimento, item ou ocorrência; identificar tipo, autor, data/hora e descrição; preservar original; substituição gera nova versão; impedir exclusão definitiva de evidência vinculada a evento formalizado; registrar hash, controlar acesso e manter auditoria. |
| D14 | Trilha de auditoria | Adotar trilha cronológica, individualizada e protegida contra alteração/exclusão indevida. Registrar usuário, data/hora, operação, valores anteriores e posteriores, justificativas e eventos críticos. Correções geram novos eventos, sem apagar histórico. |
| D15 | Controle de acesso | Contas individuais; permissões por perfil/função e menor privilégio; concessões, alterações e revogações formalmente autorizadas; bloqueio de contas inativas ou de servidores desligados/mudados de função; rastreabilidade de acessos e operações críticas. |
| D16 | Assinatura eletrônica | Assinatura vinculada ao conteúdo e à decisão, com autenticação reforçada para operações críticas, identificação inequívoca do signatário, intenção, data/hora e evidências de verificação. Tecnologia específica fica para análise institucional, jurídica e de infraestrutura. |
| D17 | Backup e recuperação | Política formal cobrindo banco de dados, documentos e evidências; cópias segregadas do ambiente principal, proteção contra alteração/exclusão, monitoramento, retenção definida, testes de restauração e procedimento de continuidade/recuperação. |
| D18 | Identificadores | Identificadores independentes, únicos, permanentes e não reutilizáveis para solicitação, recebimento, objeto de custódia, amostra e ensaio; manter relacionamentos. Permitir QR Code/código de barras. Padrão de nomenclatura será definido antes da implementação. |
| D19 | Chegada posterior | Complementação de recebimento vinculada à solicitação original, com novo evento, data/hora, responsável, evidências e nova conferência. Preservar histórico; custódia inicia somente na chegada física. Solicitação encerrada exige reabertura autorizada ou nova solicitação vinculada, conforme regra institucional. |
| D20 | Aceite e criação da amostra | Estabelecer barreira formal de admissão laboratorial. Exigir solicitação/recebimento vinculados, material apresentado, conferência concluída, quantidades registradas, critérios impeditivos atendidos, pendências impeditivas resolvidas, aceite formal, validações exigidas e custódia registrada. Criar amostra com identificador próprio e vínculo ao objeto; bloquear enquanto houver requisito impeditivo. |

## 3. Condições e dependências que permanecem abertas

A ratificação institucional de D01–D20 está concluída. Isso não significa que todos os parâmetros necessários à implantação estejam definidos ou que os cenários operacionais tenham sido homologados. As pendências abaixo permanecem sujeitas a definição, evidência e/ou validação específica:

As decisões são funcionais e não definem, por si só, todos os parâmetros institucionais ou técnicos. Permanecem para definição e validação:

1. Matriz nominal/institucional de competências, substituições e autoridades.
2. Checklists concretos por categoria, critérios E/S/I e critérios técnicos de aceitação.
3. Prazos, canais oficiais, horários de atendimento e regras de prorrogação.
4. Procedimento de devolução, identificação de representantes e destinação alternativa.
5. Tecnologia, nível jurídico e política institucional de assinatura eletrônica.
6. Política de retenção, RPO/RTO, frequência de backup e infraestrutura de recuperação.
7. Formato do protocolo SEFI, accession, QR Code e política de não reutilização.
8. Inventário de localizações e regras de movimentação.
9. Contratos técnicos de anexos, hash, idempotência, concorrência, paginação e recuperação.
10. Procedimento de impacto de retificações sobre ensaios e laudos em andamento.
11. Regra institucional para reabertura/exceção quando houver chegada posterior.
12. Evidência de validação dos cenários SIM01–SIM12 com representantes e operadores do SEFI.

## 4. Rastreabilidade documental e operacional

| Documento/artefato | Complemento esperado |
|---|---|
| EST-REC-001 | Estados, transições, atores, pré-condições, eventos, bloqueios, assinatura, custódia, anexos e trilha de auditoria. |
| MOD-DOM-001 | Entidades, atributos, identificadores, cardinalidades, anexos, objetos de custódia, amostras e relacionamentos. |
| AUD-EST-001 | Verificação de consistência das decisões EST01–EST10 com D01–D20 e registro das lacunas. |
| REV-MD-LIMS-002 | Parecer multidisciplinar atualizado, riscos, dependências e situação do Gate G0. |
| SIM-SEFI-REC-001 | Cenários SIM01–SIM12, critérios de aceitação e cenários adicionais derivados das decisões. |

## 5. Critérios para validação operacional e Gate G0

**Etapa concluída:** ratificação institucional das decisões D01–D20 pelo responsável pela Validação Institucional do LIMS – SEFI, em 2026-11-10.

Antes de propor aprovação do Gate G0, ainda obter:
- validação operacional dos fluxos e cenários por usuários/representantes de recepção, conferência, coordenação e qualidade, com evidências registradas;
- confirmação das competências e autoridades institucionais;
- aprovação dos checklists e regras operacionais aplicáveis;
- definição dos parâmetros institucionais ainda abertos;
- rastreabilidade entre decisão, cenário, critério de aceitação, documento e responsável;
- plano de testes, segurança, continuidade e homologação;
- parecer de prontidão sem pendências impeditivas.

**Validação institucional das decisões D01–D20: CONCLUÍDA, com ratificação integral e sem ressalvas pelo responsável designado.**  
**Gate G0: NÃO APROVADO por este registro.**  
**Implementação: NÃO AUTORIZADA por este registro.**  
**Escopo desta consolidação: documentação exclusivamente.**


## 7. Decisões institucionais do Gate G0 — bloco G0-P01 a G0-P05

Em 2026-11-10, o responsável pela Validação Institucional do LIMS – SEFI aprovou integralmente, sem ressalvas, as cinco propostas do primeiro bloco de pendências do Gate G0:

| ID | Tema | Decisão | Limites e detalhamentos pendentes |
|---|---|---|---|
| G0-P01 | Matriz de competências e autoridades | **Aprovada integralmente** | Aprovado o modelo de matriz com atividades, titular, substituto, limites de autoridade e validação independente quando exigida. Designações nominais e formais permanecem pendentes. |
| G0-P02 | Checklists técnicos e critérios E/S/I | **Aprovada integralmente** | Aprovada a estrutura e governança de checklists controlados por versão, categoria, critérios, classe E/S/I, fundamentação, evidência, aceitação, responsáveis e vigência. Critérios técnicos específicos devem ser definidos por categoria, sem presumir valores. |
| G0-P03 | Prazos e comunicações | **Aprovada integralmente** | Aprovado o modelo de prazos por tipo de ocorrência, comunicação formal como marco inicial, dias úteis como padrão salvo regra específica, prorrogação justificada/autorizada, alerta de vencimento e encerramento apenas por decisão formal. Valores numéricos e canais institucionais permanecem pendentes. |
| G0-P04 | Devolução e destinação | **Aprovada integralmente** | Aprovado o procedimento com rastreabilidade da custódia, motivo/decisão, representante autorizado, responsáveis pela entrega, data/hora, quantidade/condição, confirmação e comprovante. Formulário e designações institucionais permanecem para detalhamento. |
| G0-P05 | Assinatura eletrônica | **Aprovada integralmente** | Aprovados os requisitos funcionais de identificação individual, autenticação proporcional ao risco, intenção explícita, vínculo ao conteúdo/versão, data/hora, integridade, prevenção de reutilização indevida e trilha de auditoria. Modalidade jurídica e tecnologia permanecem sujeitas à avaliação institucional competente. |

A aprovação deste bloco ratifica os modelos, requisitos e diretrizes acima, mas não declara concluídas as dependências e definições explicitamente indicadas na última coluna.

**Resultado do bloco:** 5 de 5 propostas aprovadas integralmente, sem ressalvas.  
**Situação do Gate G0:** permanece **NÃO APROVADO** até a conclusão das demais pendências e evidências de validação requeridas.  
**Implementação:** permanece **NÃO AUTORIZADA**.


## 9. Decisões institucionais do Gate G0 — bloco G0-P06 a G0-P10

Em 2026-11-10, o responsável pela Validação Institucional do LIMS – SEFI aprovou integralmente, sem ressalvas, as cinco propostas do segundo bloco de pendências do Gate G0:

| ID | Tema | Decisão | Limites e detalhamentos pendentes |
|---|---|---|---|
| G0-P06 | Backup, restauração e continuidade | **Aprovada integralmente** | Aprovado o modelo de governança abrangendo banco de dados, documentos e evidências, cópias segregadas e protegidas, monitoramento, testes de restauração e procedimento de recuperação. Frequência, retenção, RPO, RTO e infraestrutura permanecem para definição institucional e técnica. |
| G0-P07 | Identificadores e protocolo SEFI | **Aprovada integralmente** | Aprovados os princípios de identificadores independentes, únicos, permanentes e não reutilizáveis, com vínculos preservados e possibilidade de QR Code/código de barras. Formato, máscara, prefixos e padrão visual permanecem pendentes. |
| G0-P08 | Localizações e movimentação física | **Aprovada integralmente** | Aprovado o modelo de cadastro controlado de locais e registro de movimentações, com origem, destino, objeto, responsável, horários e justificativa, distinguindo localização de transferência de custódia. Inventário físico, códigos e permissões dos locais permanecem para detalhamento. |
| G0-P09 | Documentos, anexos e evidências digitais | **Aprovada integralmente** | Aprovados os requisitos funcionais de vínculo, identificação, preservação de originais, versionamento, hash, controle de acesso, auditoria e tratamento de falhas, duplicidade e concorrência. Formatos permitidos, limites, algoritmo de hash, armazenamento e retenção permanecem para especificação técnica. |
| G0-P10 | Retificações e impacto sobre amostras, ensaios e laudos | **Aprovada integralmente** | Aprovado o modelo de solicitação justificada, preservação dos valores original e corrigido, evidências, autorização prévia, avaliação de impacto, rastreabilidade e vedação de retroatividade. Alçadas, formulários e regras específicas por tipo de alteração permanecem para detalhamento institucional. |

Não foram apresentadas observações ou ressalvas pelo responsável pela Validação Institucional.

A aprovação deste bloco ratifica os modelos e requisitos acima, mas não declara concluídas as dependências e definições explicitamente indicadas na última coluna.

**Resultado do bloco:** 5 de 5 propostas aprovadas integralmente, sem ressalvas.  
**Situação do Gate G0:** permanece **NÃO APROVADO** até a conclusão das demais pendências e evidências de validação requeridas.  
**Implementação:** permanece **NÃO AUTORIZADA**.



## 11. Decisões institucionais do Gate G0 — bloco G0-P11 a G0-P15

Em 2026-11-10, o responsável pela Validação Institucional do LIMS – SEFI aprovou integralmente, sem ressalvas, as cinco propostas do terceiro bloco de pendências do Gate G0:

| ID | Tema | Decisão | Limites e detalhamentos pendentes |
|---|---|---|---|
| G0-P11 | Validação operacional dos cenários SIM01–SIM12 | **Aprovada integralmente** | Aprovada a metodologia de validação de mesa com representantes dos perfis envolvidos, percorrendo os cenários e registrando concordâncias, divergências, regra aplicável, evidência esperada, responsável e ajustes. A execução com participantes reais e seus registros ainda precisa ocorrer; esta aprovação não declara a validação executada. |
| G0-P12 | Critérios de aceitação CA01–CA37 e rastreabilidade de testes | **Aprovada integralmente** | Aprovado o princípio de converter os critérios em casos de teste rastreáveis, com pré-condições, passos, resultado esperado, evidências, resultado obtido e tratamento de falhas. A especificação detalhada e a execução dos testes permanecem pendentes. |
| G0-P13 | Revisão de arquitetura e segurança | **Aprovada integralmente** | Aprovada a realização de avaliação documentada de arquitetura, segurança, controle de acesso, auditoria, proteção de dados/evidências, gestão de privilégios e continuidade, baseada em evidências do repositório e do ambiente. A revisão técnica e seus achados permanecem pendentes. |
| G0-P14 | Persistência, integridade e concorrência em PostgreSQL | **Aprovada integralmente** | Aprovada a exigência de verificar integridade transacional, constraints, idempotência, concorrência e recuperação em PostgreSQL real, incluindo pipeline de CI; SQLite pode permanecer para testes rápidos, sem ser tratado como substituto da validação no banco-alvo. Implementação e execução dos testes permanecem pendentes. |
| G0-P15 | Testes ponta a ponta do fluxo crítico | **Aprovada integralmente** | Aprovada a cobertura E2E do fluxo crítico, incluindo autenticação, recebimento, conferência, assinatura e auditoria, com evidências e rastreabilidade aos critérios de aceitação. Os casos concretos, ambiente, resultados e correções permanecem pendentes. |

Não foram apresentadas observações ou ressalvas pelo responsável pela Validação Institucional.

A aprovação deste bloco ratifica a necessidade, o escopo e a abordagem de validação e QA. Não significa que as atividades já tenham sido executadas, que os testes tenham passado ou que a revisão técnica tenha emitido parecer favorável.

**Resultado do bloco:** 5 de 5 propostas aprovadas integralmente, sem ressalvas.  
**Situação do Gate G0:** permanece **NÃO APROVADO** até a execução das atividades, apresentação das evidências e resolução das pendências impeditivas.  
**Implementação:** permanece **NÃO AUTORIZADA** por este registro.

## 13. Decisões institucionais do Gate G0 — bloco G0-P16 a G0-P20

Em 2026-11-10, o responsável pela Validação Institucional do LIMS – SEFI aprovou integralmente, sem ressalvas, as cinco propostas do quarto bloco de pendências do Gate G0:

| ID | Tema | Decisão | Limites e detalhamentos pendentes |
|---|---|---|---|
| G0-P16 | Designação formal de responsáveis e substitutos | **Aprovada integralmente** | Aprovado o modelo de matriz nominal vinculada a funções e permissões, com titular, substituto, autoridade responsável pela designação, limites de atuação, validação independente, vigência e histórico. As designações individuais e sua formalização institucional permanecem pendentes. |
| G0-P17 | Desenvolvimento e aprovação dos checklists por categoria | **Aprovada integralmente** | Aprovado o fluxo de inventário de categorias, identificação das referências aplicáveis, elaboração de critérios objetivos, classificação E/S/I fundamentada, revisão da Qualidade, aprovação técnica competente e controle de versão/vigência. Os checklists concretos e seus critérios técnicos ainda precisam ser elaborados e aprovados; checklist não aprovado não deve ser utilizado. |
| G0-P18 | Prazos e canais oficiais de comunicação | **Aprovada integralmente** | Aprovado o processo de definição de prazos por ocorrência, marcos iniciais, unidades de contagem, regras de prorrogação, canais oficiais, responsáveis e evidências de comunicação. Valores, canais e regras concretas dependem de definição e aprovação institucional antes da parametrização. |
| G0-P19 | Modalidade de assinatura eletrônica | **Aprovada integralmente** | Aprovado o processo de levantamento das decisões que exigem assinatura, classificação de risco e avaliação jurídica, normativa e tecnológica, com participação das áreas competentes. A modalidade, o certificado, a plataforma e a solução tecnológica não foram escolhidos e permanecem pendentes de avaliação e decisão institucional. |
| G0-P20 | Procedimento institucional de devolução e destinação | **Aprovada integralmente** | Aprovado o processo de elaboração do procedimento para autorização, comprovação de representação, identificação e condição dos materiais, responsáveis pela entrega/recebimento, data/hora, confirmação e tratamento de retirada não realizada ou divergência. Formulários, alçadas e designações concretas permanecem pendentes. |

Não foram apresentadas observações ou ressalvas pelo responsável pela Validação Institucional.

A aprovação deste bloco ratifica os processos, requisitos e diretrizes acima. Não significa que as designações nominais, checklists concretos, prazos/canais, solução de assinatura ou formulários/alçadas estejam definidos ou publicados.

**Resultado do bloco:** 5 de 5 propostas aprovadas integralmente, sem ressalvas.  
**Situação do Gate G0:** permanece **NÃO APROVADO** até a conclusão das definições, atividades e evidências de validação requeridas.  
**Implementação:** permanece **NÃO AUTORIZADA** por este registro.

## 14. Decisões institucionais do Gate G0 — bloco G0-P21 a G0-P25

Em 2026-11-10, o responsável pela Validação Institucional do LIMS – SEFI aprovou integralmente, sem ressalvas, as cinco propostas do quinto bloco de pendências do Gate G0:

| ID | Tema | Decisão | Limites e detalhamentos pendentes |
|---|---|---|---|
| G0-P21 | Identidade, autenticação e vínculo dos solicitantes externos | **Aprovada integralmente** | Aprovado o processo de definição de identidade, autenticação e vínculo dos solicitantes, incluindo distinção entre pessoa física, representante institucional e usuário interno que cadastra em nome do solicitante; inclusão, alteração, suspensão e revogação de vínculos; recuperação de acesso; e autorização no servidor por solicitação e anexo. Tecnologia, política final e habilitação efetiva dos usuários permanecem pendentes. |
| G0-P22 | Migração e reconciliação dos dados legados | **Aprovada integralmente** | Aprovado o processo de inventário, classificação, mapeamento, migração controlada, reconciliação quantitativa/qualitativa e tratamento de exceções. Escopo, volume, cronograma e dados efetivamente migráveis permanecem pendentes; não se admite associação sem evidência confiável. |
| G0-P23 | Contratos de idempotência, concorrência e versionamento | **Aprovada integralmente** | Aprovada a elaboração de contratos para chaves de idempotência, repetição com mesmo ou diferente conteúdo, requisições simultâneas/em processamento, expected_version, conflitos, recuperação, expiração e atomicidade das operações de negócio com eventos de auditoria. Parâmetros e implementação permanecem pendentes de especificação e validação por testes. |
| G0-P24 | Gestão técnica de anexos e evidências digitais | **Aprovada integralmente** | Aprovada a elaboração da especificação técnica para armazenamento, metadados, formatos, limites, hash, integridade, detecção de corrupção/duplicidade/indisponibilidade, versionamento, retenção, backup e recuperação. Fornecedor, arquitetura e tecnologia permanecem pendentes. |
| G0-P25 | Proteção da trilha de auditoria e evidência de integridade | **Aprovada integralmente** | Aprovado o processo de especificação dos eventos, segregação de privilégios, detecção de alteração/exclusão/interrupção, verificação periódica, retenção e avaliação de ancoragem externa ou WORM. Solução tecnológica, periodicidade e parâmetros operacionais permanecem pendentes de avaliação e decisão. |

Não foram apresentadas observações ou ressalvas pelo responsável pela Validação Institucional.

A aprovação deste bloco ratifica os processos e diretrizes de especificação. Não significa que os mecanismos técnicos, parâmetros, políticas finais, fornecedores ou tecnologias estejam escolhidos, implantados ou validados.

**Resultado do bloco:** 5 de 5 propostas aprovadas integralmente, sem ressalvas.
**Situação do Gate G0:** permanece **NÃO APROVADO** até a conclusão das definições, atividades e evidências de validação requeridas.
**Implementação:** permanece **NÃO AUTORIZADA** por este registro.

## 12. Histórico

| Versão | Data | Descrição |
|---|---|---|
| 1.0 | 2026-11-10 | Consolidação inicial das decisões D01–D20 pré-validadas. |
| 1.1 | 2026-11-10 | Atualização do status após ratificação institucional integral de D01–D20 pelo responsável designado; mantidos Gate G0 não aprovado e implementação não autorizada. |
| 1.2 | 2026-11-10 | Registro da aprovação integral das propostas G0-P01 a G0-P05, sem ressalvas; mantidos Gate G0 não aprovado e implementação não autorizada. |
| 1.3 | 2026-11-10 | Registro da aprovação integral das propostas G0-P06 a G0-P10, sem ressalvas; mantidos Gate G0 não aprovado e implementação não autorizada. |
| 1.4 | 2026-11-10 | Registro da aprovação integral das propostas G0-P11 a G0-P15, sem ressalvas; mantidos Gate G0 não aprovado e implementação não autorizada. |
| 1.5 | 2026-11-10 | Registro da aprovação integral das propostas G0-P16 a G0-P20, sem ressalvas; mantidos Gate G0 não aprovado e implementação não autorizada. |
| 1.6 | 2026-11-10 | Registro da aprovação integral das propostas G0-P21 a G0-P25, sem ressalvas; mantidos Gate G0 não aprovado e implementação não autorizada. |
