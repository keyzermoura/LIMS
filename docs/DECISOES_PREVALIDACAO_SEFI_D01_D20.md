# Registro de Validação Institucional das Decisões SEFI — D01 a D20

**Identificador:** DEC-SEFI-001  
**Versão:** 1.1  
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

## 8. Histórico

| Versão | Data | Descrição |
|---|---|---|
| 1.0 | 2026-11-10 | Consolidação inicial das decisões D01–D20 pré-validadas. |
| 1.1 | 2026-11-10 | Atualização do status após ratificação institucional integral de D01–D20 pelo responsável designado; mantidos Gate G0 não aprovado e implementação não autorizada. |
| 1.2 | 2026-11-10 | Registro da aprovação integral das propostas G0-P01 a G0-P05, sem ressalvas; mantidos Gate G0 não aprovado e implementação não autorizada. |
