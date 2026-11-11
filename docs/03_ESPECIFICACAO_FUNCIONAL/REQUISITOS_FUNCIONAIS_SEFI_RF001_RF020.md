# Catálogo de Requisitos Funcionais SEFI — RF-001 a RF-020

**Identificador:** ESP-FUN-SEFI-001  
**Versão:** 0.1  
**Data:** 2026-11-11  
**Natureza:** decomposição documental das decisões ratificadas D01–D20; não cria decisões novas nem autoriza implementação.  
**Status:** primeira versão para integração e revisão.

## 1. Objetivo e regra de origem

Converter as decisões D01–D20 em requisitos funcionais de alto nível, identificáveis e rastreáveis. O texto de cada requisito é uma organização editorial do conteúdo ratificado; os limites, exceções e dependências continuam regidos pelo documento-fonte `DEC-SEFI-001 v1.7`.

**Regra:** um requisito marcado como ratificado deriva de uma decisão ratificada. Isso não significa que seus parâmetros, procedimentos, telas, contratos técnicos, testes ou evidências estejam concluídos.

## 2. Catálogo de requisitos

| ID | Requisito | Fonte primária | G0 relacionado | Situação |
|---|---|---|---|---|
| RF-001 | Registro da chegada física | D01 | P11, P13, P16 | Derivado de decisão ratificada |
| RF-002 | Registro dos dados da chegada | D02 | P07, P09, P11, P24 | Derivado de decisão ratificada |
| RF-003 | Controle e reconciliação de quantidades | D03 | P07, P26 | Derivado de decisão ratificada; parâmetros pendentes |
| RF-004 | Individualização em objetos de custódia | D04 | P26 | Derivado de decisão ratificada |
| RF-005 | Gestão de pendências saneáveis | D05 | P03, P09, P18 | Derivado de decisão ratificada; parâmetros pendentes |
| RF-006 | Registro e tratamento de recusas | D06 | P01, P04, P20 | Derivado de decisão ratificada; procedimento pendente |
| RF-007 | Transferência de custódia | D07 | P08, P23 | Derivado de decisão ratificada |
| RF-008 | Mudança de localização | D08 | P08 | Derivado de decisão ratificada |
| RF-009 | Retificação e avaliação de impacto | D09 | P05, P10, P27 | Derivado de decisão ratificada; metodologia pendente |
| RF-010 | Acumulação de funções e validação independente | D10 | P01, P13, P16 | Derivado de decisão ratificada; designações pendentes |
| RF-011 | Checklists técnicos por categoria | D11 | P02, P17 | Derivado de decisão ratificada; conteúdo por categoria pendente |
| RF-012 | Governança de checklists | D12 | P01, P02, P13, P17 | Derivado de decisão ratificada |
| RF-013 | Gestão de documentos e evidências | D13 | P09, P24, P30 | Derivado de decisão ratificada; arquitetura pendente |
| RF-014 | Trilha de auditoria | D14 | P13, P25 | Derivado de decisão ratificada; arquitetura/parametrização pendentes |
| RF-015 | Controle de acesso e ciclo de vida de contas | D15 | P21, P29 | Derivado de decisão ratificada; política externa pendente |
| RF-016 | Assinatura eletrônica | D16 | P05, P19 | Derivado de decisão ratificada; modalidade pendente |
| RF-017 | Backup, recuperação e continuidade | D17 | P06 | Derivado de decisão ratificada; parâmetros pendentes |
| RF-018 | Identificadores institucionais e laboratoriais | D18 | P07, P22, P28 | Derivado de decisão ratificada; padrão pendente |
| RF-019 | Chegada posterior/complementar | D19 | P11, P18, P22, P23, P26 | Derivado de decisão ratificada; regra de exceção pendente |
| RF-020 | Barreira formal de aceite e criação de amostra | D20 | P11, P12, P14, P15, P17, P23, P26 | Derivado de decisão ratificada; validação e evidências pendentes |

## 3. Especificação resumida por requisito

### RF-001 — Registro da chegada física

O sistema deve permitir que usuário com permissão de RECEPÇÃO registre a chegada física. A mesma pessoa pode realizar também a conferência se possuir ambas as permissões, mas registro da chegada e conferência devem permanecer como eventos distintos, com autoria e horários próprios.

**Limites:** registrar a chegada não equivale a concluir conferência, decidir aceite ou criar amostra. A chegada física pode ser registrada mesmo com divergência ou documentação incompleta.

### RF-002 — Registro dos dados da chegada

O sistema deve registrar solicitação vinculada, data/hora efetivas, recebedor identificado, entregador quando disponível ou ausência dessa informação, volumes, descrição externa, condição da embalagem, observações/avarias, documentos apresentados, fotos quando pertinentes e timestamp automático do registro.

**Limites:** instante efetivo do fato e instante de registro devem permanecer distinguíveis. A ausência de dado não deve ser preenchida por inferência.

### RF-003 — Controle e reconciliação de quantidades

O sistema deve preservar separadamente quantidades declarada, apresentada, aceita, recusada e não apresentada, permitir recebimento parcial e exigir justificativa para divergências.

**Limites:** unidade, precisão, conversão, arredondamento e regra numérica por categoria ainda dependem de definição técnica/institucional. Não presumir equivalência entre quantidade e número de objetos.

### RF-004 — Individualização em objetos de custódia

Um ItemRecebimento pode originar múltiplos ObjetosCustodia, cada qual com identificação, quantidade/unidade representada, evidências, decisão e histórico próprios. O sistema deve permitir desfechos distintos por objeto.

**Limites:** somente material efetivamente apresentado pode gerar objeto. Critérios de agrupamento, fracionamento e linhagem por categoria ainda dependem de validação técnica. Não equiparar automaticamente objeto a unidade física.

### RF-005 — Gestão de pendências saneáveis

O sistema deve permitir registrar pendência individual com descrição, classificação, responsável, comunicação formal, timestamp, prazo conforme tabela institucional, alertas, prorrogação justificada/autorizada, evidência e reavaliação obrigatória.

**Limites:** vencimento deve produzir condição PRAZO_VENCIDO, sem recusa ou encerramento automático. Recebimento de evidência não regulariza pendência sem reavaliação favorável. Valores de prazo e canais oficiais permanecem pendentes.

### RF-006 — Registro e tratamento de recusas

O sistema deve permitir registrar motivo, critério não atendido quando aplicável, justificativa técnica, evidências, decisor, validação da coordenação nos casos previstos, comunicação ao solicitante e forma de devolução/destinação.

**Limites:** recusa não encerra custódia. O encerramento exige comprovação da destinação efetiva. Procedimento, formulários, representantes e alçadas concretas permanecem pendentes.

### RF-007 — Transferência de custódia

O sistema deve registrar transferência como evento próprio, com objeto, entregador, recebedor, horários efetivo e de registro, localização quando aplicável e confirmação do novo custodiante.

**Limites:** até a confirmação do recebedor, a responsabilidade permanece com o custodiante anterior. A modalidade de confirmação/assinatura depende da política aplicável.

### RF-008 — Mudança de localização

O sistema deve registrar mudança de localização como evento separado da transferência, identificando objeto, origem, destino, responsável, horários e justificativa conforme o tipo.

**Limites:** mudança de localização não altera o custodiante. Inventário de locais, códigos e permissões dependem de detalhamento institucional.

### RF-009 — Retificação e avaliação de impacto

O sistema deve suportar procedimento excepcional de retificação com valores original e corrigido preservados, justificativa, evidências, autorização/validação prévia, assinatura eletrônica e avaliação de impacto sobre amostras, ensaios e laudos.

**Limites:** não apagar histórico nem simular retroatividade. Alçadas, formulários e metodologia por tipo de alteração permanecem pendentes.

### RF-010 — Acumulação de funções e validação independente

O sistema deve permitir acumulação de funções conforme permissões e bloquear autoaprovação quando independência for obrigatória. Nesses casos, deve encaminhar a outro servidor habilitado ou autoridade/substituto formalmente designado.

**Limites:** perfil administrador não confere autoridade técnica automática. Designações nominais e substituições formais permanecem pendentes.

### RF-011 — Checklists técnicos por categoria

O sistema deve suportar checklists específicos por categoria, com critérios E (eliminatório), S (saneável) e I (informativo), aprovação formal, versionamento e histórico, preservando a versão efetivamente aplicada em cada recebimento.

**Limites:** critérios técnicos específicos e checklists concretos por categoria ainda precisam ser elaborados e aprovados. Critério E não pode ser dispensado discricionariamente; S exige saneamento/reavaliação; I não cria bloqueio por si só.

### RF-012 — Governança de checklists

O sistema deve suportar fluxo de elaboração/proposição por especialista técnico, revisão pela Qualidade, aprovação pela Coordenação ou autoridade designada e publicação administrativa após aprovação.

**Limites:** administrador não pode alterar critérios técnicos publicados sem aprovação formal. Responsáveis nominais, vigência e fluxo concreto dependem de designação/procedimento.

### RF-013 — Gestão de documentos e evidências

O sistema deve vincular anexos à solicitação, recebimento, item ou ocorrência; identificar tipo, autor, data/hora e descrição; preservar original; criar nova versão em substituição; impedir exclusão definitiva de evidência vinculada a evento formalizado; registrar hash, controlar acesso e manter auditoria.

**Limites:** formatos, limites, algoritmo de hash, armazenamento, retenção e recuperação dependem de especificação técnica e institucional.

### RF-014 — Trilha de auditoria

O sistema deve manter trilha cronológica, individualizada e protegida contra alteração/exclusão indevida, registrando usuário, data/hora, operação, valores anteriores e posteriores, justificativas e eventos críticos. Correções devem gerar novos eventos, sem apagar histórico.

**Limites:** cobertura de eventos SEFI, segregação de privilégios, verificação periódica e eventual ancoragem/WORM dependem de arquitetura e avaliação técnica.

### RF-015 — Controle de acesso e ciclo de vida de contas

O sistema deve utilizar contas individuais, permissões por perfil/função e menor privilégio; concessões, alterações e revogações devem ser formalmente autorizadas. Deve haver tratamento de contas inativas ou de servidores desligados/mudados de função e rastreabilidade de acessos/operações críticas.

**Limites:** identidade, autenticação e vínculo de solicitantes externos, recuperação de acesso e isolamento por solicitação/anexo dependem de política institucional e arquitetura.

### RF-016 — Assinatura eletrônica

O sistema deve vincular assinatura ao conteúdo e à decisão, com autenticação reforçada para operações críticas, identificação inequívoca do signatário, intenção, data/hora e evidências de verificação.

**Limites:** tecnologia específica, modalidade jurídica, certificado/plataforma e atos sujeitos à assinatura dependem de análise institucional, jurídica e de infraestrutura. Assinatura não substitui autorização ou validação independente.

### RF-017 — Backup, recuperação e continuidade

O sistema deve estar sujeito a política formal que cubra banco de dados, documentos e evidências; cópias segregadas do ambiente principal, proteção contra alteração/exclusão, monitoramento, retenção definida, testes de restauração e procedimento de continuidade/recuperação.

**Limites:** frequência, retenção, RPO, RTO e infraestrutura permanecem para definição institucional e técnica. Persistência em volume não equivale a backup comprovado.

### RF-018 — Identificadores institucionais e laboratoriais

O sistema deve utilizar identificadores independentes, únicos, permanentes e não reutilizáveis para solicitação, recebimento, objeto de custódia, amostra e ensaio, mantendo os relacionamentos. Deve permitir QR Code/código de barras conforme padrão definido.

**Limites:** protocolo SEFI, accession laboratorial e QR Code possuem semânticas distintas. Formato, máscara, prefixos, política de numeração e migração permanecem pendentes.

### RF-019 — Chegada posterior/complementar

O sistema deve permitir registrar chegada posterior vinculada à solicitação original, com novo evento, data/hora, responsável, evidências e nova conferência, preservando o histórico anterior. Custódia inicia somente na chegada física.

**Limites:** se solicitação/recebimento estiver encerrado, exige reabertura autorizada ou nova solicitação vinculada, conforme regra institucional. A proposta EventoApresentacao de M0.3 não está aprovada por este requisito.

### RF-020 — Barreira formal de aceite e criação de amostra

O sistema deve estabelecer barreira formal de admissão laboratorial, exigindo solicitação/recebimento vinculados, material apresentado, conferência concluída, quantidades registradas, critérios impeditivos atendidos, pendências impeditivas resolvidas, aceite formal, validações exigidas e custódia registrada. A amostra deve possuir identificador próprio e vínculo ao objeto.

**Limites:** criação deve permanecer bloqueada enquanto houver requisito impeditivo. A transação de aceite/amostra, idempotência e concorrência dependem de contrato técnico e testes. O fluxo atual de criação direta de DeviceSample não deve ser presumido aderente.

## 4. Regras de leitura e rastreabilidade

- Cada RF-001–RF-020 deriva de D01–D20, na mesma numeração, para facilitar auditoria.
- G0-P01–P30 aparecem como decisões complementares que aprovam modelos/processos de detalhamento; não significam que os entregáveis estejam concluídos.
- Os relacionamentos com entidades, estados, eventos, invariantes, CA e SIM são mantidos na matriz `MAT-TRC-SEFI-D01-D20-001`.
- A decomposição em RF não altera o conteúdo das decisões-fonte e não substitui EST-REC-001, M0.2 ou M0.3.

## 5. Pendências de detalhamento

1. Decomposição de cada requisito em regras menores verificáveis, sem duplicar ou conflitar com a fonte.
2. Critérios de aceitação associados, com distinção entre CA01–CA24 e CA25–CA37.
3. Vínculos CA/SIM e evidências de execução.
4. Responsáveis institucionais e competências formalmente designados.
5. Parâmetros técnicos e operacionais ainda pendentes no registro D01–D20/G0-P01–P30.
6. Revisão de consistência com M0.2, M0.3, EST-REC-001, MOD-REL-001 e CTR-LIMS-CUST-001.

## 6. Situação formal

- RF-001–RF-020: **DECOMPOSIÇÃO DOCUMENTAL INICIAL — DERIVADA DE D01–D20 RATIFICADAS**.
- M0.2: **APROVADO FUNCIONALMENTE**.
- M0.3: **AGUARDANDO REVISÃO/VALIDAÇÃO**.
- CA01–CA37: **DOCUMENTADOS; VÍNCULO A TESTES E EXECUÇÃO PENDENTES**.
- SIM01–SIM12: **SIMULAÇÃO DOCUMENTAL; VALIDAÇÃO OPERACIONAL PENDENTE**.
- Gate G0: **NÃO APROVADO**.
- Implementação: **NÃO AUTORIZADA**.
