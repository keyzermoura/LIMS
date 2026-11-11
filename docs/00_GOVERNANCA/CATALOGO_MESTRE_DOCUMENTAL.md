# Catálogo Mestre Documental — LIMS-SEFI

**Identificador:** CAT-DOC-LIMS-SEFI-001  
**Versão:** 0.2  
**Data de elaboração:** 2026-11-11  
**Branch de trabalho:** `docs/integracao-especificacao-sefi`  
**Branch de referência:** `main`  
**Commit de referência identificado:** `e52e4d74374d5339b622b55a1ebdae7b53056824`  
**Situação:** inventário inicial verificado; levantamento exaustivo da árvore do repositório ainda pendente.

## 1. Finalidade

Este catálogo inicia a organização integrada do patrimônio documental do LIMS-SEFI. Seu objetivo é identificar fontes, registrar sua situação conhecida, estabelecer precedência e impedir que documentos aprovados sejam substituídos, reescritos ou reinterpretados silenciosamente.

Este catálogo não aprova conteúdo novo, não altera decisões ratificadas e não constitui aprovação do Gate G0.

## 2. Regras de preservação e classificação

1. Documentos-fonte permanecem preservados em seus caminhos e históricos originais.
2. A especificação integrada referencia as fontes; não as substitui.
3. Decisões D01–D20 e G0-P01–G0-P30 permanecem ratificadas conforme seus registros, incluindo limites e dependências.
4. Conteúdo proposto em M0.3 continua proposta até validação explícita.
5. Status de aprovação de uma diretriz não significa que seus parâmetros, procedimentos, testes ou evidências estejam concluídos.
6. Divergências serão registradas como achados, sem harmonização unilateral.
7. Código e infraestrutura ficam fora do escopo desta reorganização documental.

Classificações utilizadas:
- **Ratificado/aprovado:** decisão expressamente registrada como tal na fonte.
- **Documento elaborado — validar:** artefato existente que aguarda validação.
- **Diagnóstico:** análise de situação; não equivale a especificação aprovada.
- **Referência técnica:** descrição do estado/arquitetura do software; não é baseline funcional SEFI.
- **Referenciado, não localizado no caminho testado:** citado por outra fonte, mas não recuperado no caminho nominal tentado. Não significa inexistência no repositório.

## 3. Fontes recuperadas e verificadas em `main`

| ID | Documento | Caminho | Versão/situação registrada | SHA do blob | Uso na integração |
|---|---|---|---|---|---|
| SRC-01 | Registro de Validação Institucional das Decisões SEFI — D01 a D20 | `docs/DECISOES_PREVALIDACAO_SEFI_D01_D20.md` | v1.7; D01–D20 ratificadas; G0-P01–P30 aprovadas integralmente, com limites/dependências preservados | `f6140132035363c0ef2b4af5ef4d5c94b9c2d22e` | Fonte primária das decisões ratificadas e aprovadas |
| SRC-02 | Matriz Consolidada de Prontidão — Gate G0 | `docs/MATRIZ_PRONTIDAO_GATE_G0.md` | v0.3; Gate G0 não aprovado; bloqueadores e evidências pendentes | `4953116324ab820581c324c1b087c9edc6f3cb51` | Fonte de gestão de entregáveis, evidências e prontidão |
| SRC-03 | Matriz de Aderência — Domínio Existente × Domínio SEFI Aprovado | `docs/MATRIZ_ADERENCIA_DOMINIO_SEFI.md` | v1.1; diagnóstico de aderência parcial/insuficiente para admissão SEFI | `607ead785c7d01b8f2eaa821d825cbd0083627ee` | Fonte de diagnóstico entre software existente e domínio SEFI |
| SRC-04 | Modelo Lógico Revisado do Domínio SEFI — M0.3 | `docs/MODELO_LOGICO_REVISADO_DOMINIO_SEFI_M0_3.md` | v0.1; elaborado, aguardando revisão/validação; contém propostas M03-01 a M03-16 | `2044edf92d2e6d34c5a2645e476e5903216dee51` | Modelo lógico de trabalho; propostas não são promovidas a decisões aprovadas |
| SRC-05 | README do LIMS | `README.md` | Documento técnico descritivo; sem versão formal de aprovação identificada | `0bc0deedcf804edeac8146f0041410ce4c265a13` | Referência para stack, arquitetura e fluxos atualmente descritos no produto |
| SRC-06 | Modelo Conceitual do Domínio — Solicitação e Recebimento (M0.2) | `docs/MODELO_CONCEITUAL_DOMINIO_SOLICITACAO_RECEBIMENTO.md` | v0.7; M0.2 aprovado funcionalmente; validação operacional e complementos técnicos pendentes; não aprovado para implementação | `937ad0327016a01c49f514b280d32a047d7e0031` | Fonte conceitual aprovada para cardinalidades e conceitos; prevalência formal conforme seções 14–16 |
| SRC-07 | Estados e Transições — Solicitação e Recebimento | `docs/ESTADOS_E_TRANSICOES_SOLICITACAO_RECEBIMENTO.md` | v1.7; proposta documental consolidada; validação operacional pendente; não aprovada para implementação | `fb8ea208deb2e63d9d76572b35fdc6a6ba31e3d2` | Fonte de estados, transições e critérios funcionais CA01–CA37; propostas e limites devem ser preservados |
| SRC-08 | Modelo Relacional Preliminar do LIMS | `docs/MODELO_RELACIONAL_PRELIMINAR_LIMS.md` | v0.3; proposta técnica preliminar; revisão arquitetural/institucional e autorização de implementação pendentes | `ba6b0592e977056dbc2b87c0c2f2026a390f0bea` | Referência técnica de compatibilidade, não esquema aprovado |
| SRC-09 | Contrato do Histórico Unificado e da Transação de Aceite | `docs/CONTRATO_HISTORICO_UNIFICADO_E_ACEITE.md` | v0.1; proposta técnica para revisão funcional e arquitetural; não aprovada para implementação | `b81e786de482639394a40b601df0fec5a2a3f0a1` | Proposta de contrato histórico/transacional; não equivale a decisão aprovada |
| SRC-10 | Auditoria de Consistência das Decisões EST01–EST10 | `docs/AUDITORIA_CONSISTENCIA_EST01_EST10.md` | v1.3; achados AUD01–AUD22 tratados documentalmente; validação operacional e dependências técnicas pendentes | `27576bb201503dc586ce8530e0f0a9eb661b67f5` | Fonte de auditoria funcional/documental e achados residuais |
| SRC-11 | Revisão Multidisciplinar — Máquina de Estados e Critérios de Aceitação | `docs/REVISAO_MULTIDISCIPLINAR_MAQUINA_ESTADOS_CA01_CA24.md` | v1.2; revisão documental concluída; dependências e validação operacional pendentes | `f72581d3d386422a8663f22507b42c77671f0c23` | Parecer multidisciplinar, revisão CA01–CA24 e propostas CA25–CA37 |
| SRC-12 | Simulação de Mesa — Cenários Operacionais do Recebimento SEFI | `docs/VALIDACAO_CENARIOS_OPERACIONAIS_SEFI.md` | v1.2; SIM01–SIM12 simulados documentalmente; sem validação operacional com usuários e sem teste de software | `c0a079d9a520e029339e35555ea9e48afd471679` | Fonte dos cenários e sua relação declarada com CA e D01–D20 |

### 3.1 Referências de histórico verificadas

| Commit | Alteração identificada | Arquivo |
|---|---|---|
| `ef571403f6f1bb279fb2f57649ab11fc46660369` | Correção dos limites e status da inspeção técnica G0 | `docs/MATRIZ_PRONTIDAO_GATE_G0.md` |
| `99a5ed06aa21e0410048f885c8d3b2445843ece1` | Consolidação da auditoria cruzada do Gate G0 | `docs/MATRIZ_PRONTIDAO_GATE_G0.md` |
| `7fc72d133f855341318e85a487bd66c263a315db` | Criação da matriz de aderência | `docs/MATRIZ_ADERENCIA_DOMINIO_SEFI.md` |
| `4cbcabc91da82f0239a1b3d5a87b9765e8b0ad3f` | Atualização da matriz de aderência com auditoria cruzada | `docs/MATRIZ_ADERENCIA_DOMINIO_SEFI.md` |
| `e52e4d74374d5339b622b55a1ebdae7b53056824` | Criação do modelo lógico revisado M0.3 | `docs/MODELO_LOGICO_REVISADO_DOMINIO_SEFI_M0_3.md` |

O commit `e52e4d74374d5339b622b55a1ebdae7b53056824` foi o commit mais recente retornado pela consulta de histórico realizada em 2026-11-11 e é usado como referência de partida da branch documental. A consulta não substitui uma enumeração completa de todos os objetos do repositório.

## 4. Referências citadas e identificadores harmonizados

As fontes consultadas utilizam identificadores documentais e nomes de arquivo descritivos que nem sempre coincidem. Foram confirmadas as seguintes correspondências:

- `EST-REC-001` → `docs/ESTADOS_E_TRANSICOES_SOLICITACAO_RECEBIMENTO.md`;
- `MOD-DOM-001` → `docs/MODELO_CONCEITUAL_DOMINIO_SOLICITACAO_RECEBIMENTO.md`;
- `MOD-REL-001` → `docs/MODELO_RELACIONAL_PRELIMINAR_LIMS.md`;
- `CTR-LIMS-CUST-001` → `docs/CONTRATO_HISTORICO_UNIFICADO_E_ACEITE.md`;
- `AUD-LIMS-001` (referido como auditoria de consistência EST01–EST10) → `docs/AUDITORIA_CONSISTENCIA_EST01_EST10.md`;
- `REV-MD-LIMS-002` → `docs/REVISAO_MULTIDISCIPLINAR_MAQUINA_ESTADOS_CA01_CA24.md`;
- `SIM-SEFI-REC-001` → `docs/VALIDACAO_CENARIOS_OPERACIONAIS_SEFI.md`.

Os caminhos curtos `docs/<IDENTIFICADOR>.md` não existem para vários desses identificadores; os arquivos foram localizados pelos nomes descritivos acima. A enumeração integral do repositório continua pendente, portanto esta lista não declara que todos os documentos foram identificados.

## 5. Artefatos integradores produzidos nesta branch

Os seguintes documentos foram criados nesta linha de trabalho, sem modificar as fontes em `main`:

| Artefato | Caminho | Finalidade | Status |
|---|---|---|---|
| Catálogo Mestre | `docs/00_GOVERNANCA/CATALOGO_MESTRE_DOCUMENTAL.md` | Inventário e precedência documental | v0.3; inicial, não exaustivo |
| Plano de Integração | `docs/00_GOVERNANCA/PLANO_DE_INTEGRACAO_DOCUMENTAL.md` | Pacotes de trabalho e governança | v0.1 |
| Especificação Integrada | `docs/00_GOVERNANCA/ESPECIFICACAO_INTEGRADA_LIMS_SEFI.md` | Documento integrador e índice | v0.1; estrutura inicial |
| Comparação M0.2 × M0.3 | `docs/02_DOMINIO/COMPARACAO_M0_2_M0_3.md` | Preservação das cardinalidades e divergências | v0.1; análise inicial |
| Matriz D01–D20 | `docs/05_RASTREABILIDADE/MATRIZ_RASTREABILIDADE_D01_D20.md` | Relação D × domínio × CA × SIM | v0.3; não validada |
| Requisitos Funcionais RF-001–RF-020 | `docs/03_ESPECIFICACAO_FUNCIONAL/REQUISITOS_FUNCIONAIS_SEFI_RF001_RF020.md` | Decomposição das decisões ratificadas em requisitos funcionais | v0.1; inicial |
| Plano de Casos de Teste CA01–CA37 | `docs/06_VALIDACAO/PLANO_CASOS_TESTE_CA01_CA37.md` | Casos de teste preliminares com pré-condições, ações, resultados e evidências sugeridas | v0.1; rascunho, não executado |

## 6. Lacunas do inventário

O inventário é inicial, não exaustivo. O conector GitHub utilizado nesta etapa permitiu recuperar arquivos por caminho conhecido, metadados de repositório, commits e branches, mas não forneceu uma listagem completa da árvore de diretórios. Portanto, ainda não se declara que todos os documentos do repositório foram localizados.

Também precisam ser conferidos:
- demais documentos em `docs/` e subdiretórios;
- artefatos de simulação, critérios CA01–CA37 e cenários SIM01–SIM12;
- documentos de arquitetura, segurança, contratos e auditorias;
- evidências de aprovação/validação que estejam fora do repositório;
- arquivos e registros de conversas anteriores que ainda não estejam representados em `main`.

## 7. Precedência documental provisória

Para evitar conflitos durante a integração:

1. Para o conteúdo de D01–D20 e G0-P01–G0-P30, prevalece o registro SRC-01, respeitando os limites e dependências nele expressos.
2. Para situação de prontidão, entregáveis, bloqueadores e evidências G0, prevalece SRC-02 como matriz de acompanhamento.
3. Para diagnóstico de aderência do software atual, SRC-03 é a referência diagnóstica recuperada.
4. Para estrutura lógica proposta, SRC-04 é fonte de trabalho sujeita a validação; não altera SRC-01.
5. README e código descrevem o produto existente; não prevalecem sobre decisões de domínio ratificadas.
6. Havendo conflito entre fontes de mesmo nível ou falta de fonte, registrar a divergência e encaminhar para decisão; não inferir aprovação.

## 8. Histórico

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-11 | Inventário ampliado para doze fontes recuperadas, incluindo M0.2, estados/transições, modelo relacional e contrato de histórico/aceite; inclui auditoria, revisão multidisciplinar e simulação documental; a enumeração integral da árvore do repositório continua pendente; limitações do levantamento registradas. |

## 9. Situação formal

- Inventário documental: **INICIAL — NÃO EXAUSTIVO**.
- Decisões D01–D20: **RATIFICADAS**, conforme SRC-01.
- Decisões G0-P01–G0-P30: **APROVADAS**, conforme SRC-01, com detalhamentos ainda pendentes.
- M0.3: **ELABORADO — AGUARDANDO REVISÃO/VALIDAÇÃO**.
- Gate G0: **NÃO APROVADO**.
- Implementação: **NÃO AUTORIZADA**.
- Alterações de código, banco, API, frontend, CI e infraestrutura: **NENHUMA**.
