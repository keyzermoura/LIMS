# Requisitos Transversais e de Qualidade — LIMS-SEFI

**Identificador:** ESP-TRV-LIMS-SEFI-001  
**Versão:** 0.1  
**Data:** 2026-11-11  
**Natureza:** consolidação de requisitos transversais derivados de D01–D20 e G0-P01–P30; não escolhe tecnologias nem autoriza implementação.  
**Status:** versão documental inicial.

## 1. Objetivo

Reunir requisitos que atravessam vários processos/entidades do LIMS-SEFI e que não devem ser repetidos isoladamente em cada requisito funcional. As diretrizes foram ratificadas/aprovadas nas fontes, mas parâmetros, tecnologias, procedimentos, designações e evidências permanecem pendentes quando assim indicado.

## 2. Catálogo de requisitos transversais

| ID | Tema | Fontes | Diretriz consolidada | Detalhamentos ainda pendentes |
|---|---|---|---|---|
| RT-001 | Identidade e controle de acesso | D10, D15; G0-P01, P13, P16, P21, P29 | Contas individuais, menor privilégio, permissões por função/atividade, autorização no servidor e rastreabilidade de concessões/alterações/revogação. | Perfis finais, matriz de permissões, ciclo de vida de contas, identidade externa, MFA/SSO e designações. |
| RT-002 | Competência e independência | D10; G0-P01, P16 | RBAC/perfil não substitui competência ou designação; operações sujeitas a independência exigem ator diferente do autor/executor. | Matriz nominal, titulares, substitutos, alçadas, vigência e autoridade designante. |
| RT-003 | Assinatura eletrônica | D09, D16; G0-P05, P19 | Assinatura vinculada ao ato/conteúdo, signatário, intenção, data/hora, autenticação proporcional ao risco e evidência de verificação; distinta de validação independente. | Atos que exigem assinatura, modalidade jurídica, certificado/plataforma, tecnologia e política institucional. |
| RT-004 | Integridade e trilha de auditoria | D09, D13, D14; G0-P13, P25 | Trilha cronológica, individualizada e protegida; registrar ator, tempo, operação, antes/depois, justificativa e correlação; correções como novos atos. | Taxonomia completa, segregação de privilégios, verificação periódica, proteção contra superusuário, WORM/ancoragem e parâmetros. |
| RT-005 | Documentos, anexos e evidências | D02, D05, D06, D09, D13; G0-P09, P24, P30 | Evidências vinculadas ao fato/entidade, originais preservados, versionamento, hash, metadados, acesso controlado e auditoria. | Formatos, limites, algoritmos, armazenamento, retenção, backup, recuperação e detecção de corrupção/duplicidade. |
| RT-006 | Integridade transacional e persistência | D03, D04, D07, D14, D18, D20; G0-P14, P23 | Operações críticas devem preservar invariantes, vínculos, quantidades, eventos e decisões; evitar duplicidade, perda de atualização e estados inconsistentes. | Constraints, transações, locking, isolamento, comportamento de falha e validação em PostgreSQL real. |
| RT-007 | Idempotência, concorrência e versionamento | D07, D18, D20; G0-P23 | Contratos para chave idempotente, replay, chave com conteúdo diferente, requisição simultânea/em processamento, expected_version, conflito e atomicidade. | Escopo/expiração das chaves, hash canônico, códigos/contratos de resposta, recuperação e testes concorrentes. |
| RT-008 | Consulta histórica, paginação e exportação | D14, D15, D18; G0-P28 | Filtros, ordenação determinística, paginação estável, exportação autorizada e rastreável, preservando vínculos. | Campos, formatos, limites, filtros, política de exportação, desempenho e evidências de teste. |
| RT-009 | Backup, restauração e continuidade | D17; G0-P06 | Banco, documentos e evidências abrangidos por cópias segregadas/protegidas, monitoramento, retenção, testes de restauração e procedimento de continuidade. | Frequência, retenção, RPO, RTO, infraestrutura, responsáveis e resultados de restauração. |
| RT-010 | Migração e reconciliação de legado | D18, D19; G0-P22 | Inventariar, classificar, mapear, migrar controladamente e reconciliar; não criar vínculo histórico sem evidência confiável; registrar exceções. | Escopo, volume, critérios, cronograma, ferramentas, responsáveis e relatório de reconciliação. |
| RT-011 | Classificação, retenção e destinação da informação | D13, D14, D17; G0-P30 | Classificar informações, definir prazos de guarda, arquivamento, bloqueios legais/administrativos e eliminação autorizada com rastreabilidade. | Tabela de temporalidade, base institucional/jurídica, prazos, papéis e procedimento final. |
| RT-012 | Identidade externa e isolamento de solicitantes | D15; G0-P21 | Distinguir pessoa física, representante institucional e usuário interno; autorização no servidor por solicitação/anexo; inclusão, alteração, suspensão, revogação e recuperação de acesso. | Prova de identidade, autenticação, vínculo, recuperação, política de contas e tecnologia. |
| RT-013 | Proteção contra abuso e autenticação reforçada | D15, D16; G0-P29 | Avaliar risco e definir limites de tentativas, proteção contra requisições excessivas, monitoramento, alertas, bloqueios e recuperação. | MFA/SSO, ferramentas, limites, duração de bloqueio, desbloqueio e monitoramento. |
| RT-014 | Testes, CI e reprodutibilidade | D14, D17; G0-P11–P15 | Testes rastreáveis aos requisitos/CA; validação PostgreSQL real; E2E do fluxo crítico; pipeline reproduzível e evidências vinculadas ao commit. | Casos detalhados, ambiente, dados, logs, cobertura, resultados, defeitos, retestes e homologação. |
| RT-015 | Identificadores e rastreabilidade | D18; G0-P07, P22, P28 | Identificadores independentes, únicos, permanentes e não reutilizáveis; protocolo, accession e QR com semânticas próprias. | Formatos, máscaras, prefixos, momento de atribuição, interoperabilidade e política de migração. |
| RT-016 | Localização e movimentação física | D07, D08; G0-P08 | Catálogo controlado de locais e eventos de movimentação; mudança de localização não altera custodiante; transferência só após confirmação. | Inventário de locais, códigos, permissões e parâmetros de movimentação. |
| RT-017 | Prazos e comunicações | D05, D06, D09; G0-P03, P18 | Prazos por tipo de ocorrência; comunicação formal como marco inicial; alertas, prorrogação justificada/autorizada e decisão formal para encerramento. | Valores numéricos, dias/unidade de contagem por situação, canais oficiais, horários e modelos. |

## 3. Regras de aplicação

1. Requisitos transversais devem ser referenciados pelos requisitos funcionais e processos afetados; não devem gerar controles duplicados ou contraditórios.
2. RBAC, competência, designação, validação independente e assinatura são controles distintos.
3. Auditoria técnica e eventos de domínio são complementares e não devem duplicar semântica.
4. Hash/assinatura de evidência não substituem controle de acesso, retenção ou backup.
5. Backup não é comprovado pela existência de volume persistente; restauração precisa de evidência.
6. Teste automatizado não substitui validação operacional com usuários do SEFI.
7. Aprovação do modelo/metodologia em G0-P01–P30 não comprova execução do entregável nem encerramento do bloqueador correspondente.

## 4. Relação com os requisitos funcionais

Os requisitos transversais complementam RF-001–RF-020. A matriz de rastreabilidade deve identificar, para cada RF, quais RT se aplicam e quais evidências comprovam atendimento. Esta versão ainda não define parâmetros quantitativos nem tecnologia.

## 5. Situação formal

- RT-001–RT-017: **CONSOLIDAÇÃO DOCUMENTAL INICIAL** derivada de D01–D20 e G0-P01–P30.
- Parâmetros e tecnologias: **PENDENTES** conforme tabela.
- Arquitetura-alvo: **NÃO APROVADA**.
- Gate G0: **NÃO APROVADO**.
- Implementação: **NÃO AUTORIZADA**.
