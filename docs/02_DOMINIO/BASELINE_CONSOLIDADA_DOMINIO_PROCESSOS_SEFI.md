# Baseline Consolidada do Domínio e dos Processos do LIMS-SEFI

**Identificador:** BCDP-LIMS-SEFI-001  
**Versão:** 0.1 — consolidação documental para revisão  
**Data:** 2026-11-11  
**Branch:** `docs/integracao-especificacao-sefi`  
**Fontes principais:** D01–D20; M0.2 v0.7; EST-REC-001 v1.7; SIM-SEFI-REC-001 v1.2; M0.3 v0.1; auditoria EST01–EST10; PROC-01–PROC-16; comparação M0.2 × M0.3.  
**Status:** referência integrada proposta; não aprovada como substituta das fontes; validação operacional pendente.

## 1. Finalidade e limites

Esta baseline reúne, em uma referência de leitura única, o domínio e os processos do LIMS-SEFI já documentados. Seu propósito é reduzir divergências de interpretação, explicitar a precedência das decisões aprovadas e separar regras consolidadas de refinamentos ainda pendentes.

Esta consolidação:
- preserva integralmente D01–D20 e G0-P01–P30;
- preserva as sete cardinalidades canônicas aprovadas em M0.2;
- adota as regras funcionais formalizadas em EST01–EST10 e na consolidação EST-REC-001, sem apagar seu histórico;
- aproveita M0.3 como detalhamento lógico, mas não transforma M03-01–M03-16 em decisões aprovadas;
- não define esquema físico, endpoints, telas, tecnologia, prazos numéricos, critérios técnicos por categoria ou designações nominais;
- não substitui os documentos-fonte e não autoriza implementação.

## 2. Precedência e tratamento de conflitos

Em caso de divergência, aplicar a seguinte ordem:

1. **D01–D20 ratificadas:** decisões funcionais/institucionais que não podem ser alteradas por consolidação editorial.
2. **Cardinalidades M0.2 v0.7 aprovadas:** relações canônicas do domínio.
3. **EST-REC-001 v1.7, especialmente decisões EST01–EST10 e consolidação das seções 25–30:** detalhamento funcional e máquina de estados, subordinados a D01–D20 e M0.2.
4. **SIM-SEFI-REC-001 v1.2:** cenários de simulação documental para verificar coerência e revelar lacunas; não são homologação.
5. **M0.3 v0.1:** detalhamento lógico proposto, útil para explicitar entidades, invariantes e compatibilidade; seus refinamentos pendentes não prevalecem sobre fontes aprovadas.
6. **Mapas, matrizes e requisitos integradores desta branch:** instrumentos analíticos derivados; não criam aprovação.

Se a divergência não puder ser resolvida pela precedência acima, ela permanece registrada como pendência. Não se escolhe uma alternativa física ou funcional por conveniência.

## 3. Princípios canônicos do domínio

1. Solicitação, recebimento, conferência, decisão, custódia e amostra são conceitos/ciclos distintos.
2. A chegada física pode ser registrada mesmo com divergência ou documentação incompleta; registrar chegada não significa aceite técnico.
3. A custódia começa com a chegada física do material apresentado, antes do aceite e da criação da AmostraOperacional.
4. Cada ItemDeclarado é representado por um ItemRecebimento, inclusive quando não apresentado.
5. Somente material efetivamente apresentado pode originar ObjetoCustodia.
6. A decisão é tomada na menor granularidade em que aceite, recusa, rastreabilidade, resultado ou destinação possam divergir.
7. A ausência de apresentação não é recusa.
8. Quantidades declarada, apresentada, aceita, recusada e não apresentada devem permanecer distintas e reconciliáveis; a quantidade representada por ObjetoCustodia é dimensão adicional de controle.
9. Transferência de custódia e mudança de localização são eventos diferentes.
10. Solicitação de transferência não altera o custodiante; somente a confirmação do recebedor efetiva a transferência.
11. Recusa não encerra custódia. O encerramento exige devolução/entrega/destinação efetiva e comprovada.
12. AmostraOperacional só é criada após aceite formal e cumprimento dos bloqueios e validações obrigatórios.
13. A criação da amostra não reinicia a custódia nem cria nova chegada.
14. Retificação é novo ato, com preservação do original, justificativa, evidência, autorização e avaliação de impacto aplicável.
15. Instante do fato e instante do registro são distintos e não podem ser artificialmente retroagidos.
16. Perfil/permissão, competência institucional, validação independente e assinatura eletrônica são controles diferentes.
17. Estado agregado é derivado dos estados/fatos filhos e nunca substitui o histórico individual.
18. Registros legados não recebem vínculos presumidos sem evidência confiável.

## 4. Modelo canônico de entidades

### 4.1 Solicitação e recebimento

| Entidade | Papel canônico | Regra |
|---|---|---|
| Solicitante | Pessoa, órgão ou instituição em nome de quem a demanda é registrada. | Não implica conta externa na primeira entrega. |
| Solicitação | Demanda administrativa e seu contexto. | Pode conter vários itens declarados. |
| ItemDeclarado | Linha de material/produto solicitada. | Preserva descrição, quantidade e unidade declaradas. |
| Recebimento | Registro da chegada física principal. | No máximo um por solicitação. |
| ItemRecebimento | Representação de cada ItemDeclarado no recebimento principal. | Existe também para item não apresentado. |

### 4.2 Material sob custódia

| Entidade | Papel canônico | Regra |
|---|---|---|
| ObjetoCustodia | Material efetivamente apresentado e mantido sob custódia, individual ou agrupado de forma homogênea e justificada. | É a referência canônica para custódia e para decisão individual quando os desfechos puderem divergir. |
| EventoCustodia | Fato imutável de início, transferência, mudança de localização, devolução, destinação, encerramento ou correção. | Referencia ObjetoCustodia; não substitui o objeto. |
| Localizacao | Catálogo conceitual de locais de guarda/movimentação. | Códigos e inventário dependem de definição institucional. |

### 4.3 Conferência, decisão e admissão

| Entidade | Papel canônico | Regra |
|---|---|---|
| ChecklistModelo / VersaoChecklist | Modelo e versão publicada de critérios aplicáveis. | Governança e versionamento conforme D11/D12. |
| CriterioChecklist | Requisito com classe E/S/I. | A classe pertence à versão publicada; operador não a escolhe. |
| RespostaChecklist | Resultado de critério aplicado. | Preserva versão, avaliador, instante, justificativa e evidência. |
| Pendencia | Providência requerida e seu ciclo. | Pode se vincular ao item ou objeto conforme alcance. |
| DecisaoRecebimento | Ato formal de aceite, pendência ou recusa. | No ObjetoCustodia se houver desfecho independente; no ItemRecebimento apenas se o resultado for único. |
| ValidacaoCoordenacao | Revisão independente quando exigida. | Autor/executor não valida a própria decisão nos casos obrigatórios. |
| AmostraOperacional | Registro laboratorial criado após aceite final. | No máximo uma por ObjetoCustodia. |
| Ensaio | Atividade analítica vinculada à amostra. | Ciclo laboratorial posterior permanece fora do escopo de recebimento. |

### 4.4 Conceitos transversais

Evidencia, VinculoEvidencia, Retificacao, ReferenciaExterna, UsuarioInterno, Perfil/Permissao, DesignacaoCompetencia, AssinaturaEletronica e EventoAuditoria são conceitos transversais. Sua existência lógica não define, por si só, tabela, endpoint, tecnologia de armazenamento ou política institucional final.

## 5. Cardinalidades canônicas preservadas

As seguintes sete relações foram aprovadas em M0.2 e são mantidas sem alteração:

| Origem | Cardinalidade | Destino | Regra |
|---|---:|---|---|
| Solicitante | 1:N | Solicitação | Um solicitante pode originar várias solicitações. |
| Solicitação | 1:N | ItemDeclarado | Uma solicitação possui um ou mais itens declarados. |
| Solicitação | 1:0..1 | Recebimento principal | No máximo um recebimento principal por solicitação. |
| ItemDeclarado | 1:1 | ItemRecebimento | Cada linha declarada possui uma representação no recebimento principal. |
| ItemRecebimento | 1:0..N | ObjetoCustodia | Somente material apresentado pode gerar objeto(s). |
| ObjetoCustodia | 1:0..1 | AmostraOperacional | No máximo uma amostra por objeto aceito. |
| AmostraOperacional | 1:N | Ensaio | Uma amostra pode originar vários ensaios. |

**Regra de preservação:** M0.3 pode detalhar a origem e a linhagem dos objetos, mas não pode substituir nem enfraquecer a relação canônica ItemRecebimento 1:0..N ObjetoCustodia. A relação adicional com EventoApresentacao permanece refinamento proposto, não cardinalidade aprovada.

## 6. Granularidade, apresentação e quantidades

### 6.1 Quantidades que não podem ser confundidas

- **Declarada:** informada no ItemDeclarado.
- **Apresentada:** observada em cada ocorrência de chegada/apresentação.
- **Representada sob custódia:** quantidade/unidade atribuída a cada ObjetoCustodia.
- **Aceita:** escopo/quantidade abrangido por decisão favorável.
- **Recusada:** escopo/quantidade abrangido por decisão desfavorável.
- **Não apresentada:** parcela declarada que não foi apresentada na ocorrência pertinente.

Não somar ou converter unidades incompatíveis sem regra aprovada. A reconciliação deve permitir explicar diferenças sem sobrescrever a declaração original.

### 6.2 Individualização, agrupamento e fracionamento

ObjetoCustodia pode representar unidade individual ou agrupamento homogêneo quando guarda, avaliação, decisão, rastreabilidade e destinação forem comuns. Não agrupar materiais cujos desfechos possam divergir. Fracionamento, agrupamento por categoria, critérios de homogeneidade, unidades e linhagem detalhada permanecem dependentes de G0-P26 e M03-02/M03-03.

## 7. Chegada principal e chegada posterior — D19

1. A solicitação possui no máximo um Recebimento principal.
2. O recebimento principal representa todas as linhas declaradas, inclusive as não apresentadas.
3. D19 permite complementação vinculada à solicitação original, registrada como novo fato/evento, com data/hora efetivas, responsável, evidências e nova conferência.
4. A chegada complementar não altera nem retroage a chegada original.
5. Se a solicitação/recebimento estiver encerrado, a continuidade exige reabertura autorizada ou nova solicitação vinculada, conforme regra institucional.
6. Se o material não estava fisicamente presente na ocasião original, não se pode retificar o registro NAO_APRESENTADO como se estivesse presente. Aplica-se a regra de material entregue posteriormente.
7. Se havia presença física na ocasião original e o registro de ausência foi erro comprovável, a correção é retificação excepcional, com evidência, validação prévia da coordenação e assinatura, preservando o original.
8. A entidade específica `EventoApresentacao` é proposta de M0.3 (M03-01), não decisão aprovada. Até validação, a especificação deve exigir o registro do novo fato sem impor essa entidade como solução física/lógica definitiva.
9. A origem exata de cada ObjetoCustodia em uma apresentação específica, e a possibilidade de um objeto agregar material de mais de uma apresentação, permanecem questões M03-01 a M03-03.

## 8. Máquina de estados — separação das dimensões

A [Matriz de Harmonização de Estados, Transições e Eventos](MATRIZ_HARMONIZACAO_ESTADOS_TRANSICOES_EVENTOS_SEFI.md) detalha a correspondência entre EST-REC-001 e M0.3, incluindo eventos, projeções e questões HARM-01–HARM-07. Esta baseline e a matriz são análises documentais, não validação funcional.

Não usar um único estado global para representar todo o processo. Manter pelo menos as dimensões abaixo, com projeções agregadas quando aplicável.

### 8.1 Solicitação

RASCUNHO → SUBMETIDA → RECEBIMENTO_REGISTRADO → EM_TRATAMENTO → CONCLUIDA; CANCELADA somente conforme permissão e procedimento. Conclusão administrativa não significa aceite universal.

### 8.2 Recebimento

Estados funcionais documentados: REGISTRADO, EM_CONFERENCIA, AGUARDANDO_REGULARIZACAO, AGUARDANDO_COORDENACAO, PARCIALMENTE_DECIDIDO, CONCLUIDO e CANCELADO. O agregado deriva dos itens/objetos e dos bloqueios; CONCLUIDO não implica aceite de todos nem encerramento automático de custódia.

### 8.3 ItemRecebimento

Separar:
- apresentação: AGUARDANDO_CHEGADA, APRESENTADO, NAO_APRESENTADO;
- conferência: NAO_INICIADA, EM_ANDAMENTO, CONCLUIDA;
- consolidação decisória: NAO_DECIDIDO, PARCIALMENTE_DECIDIDO, ACEITO, PENDENTE, RECUSADO ou MISTO, derivada dos objetos e das regras aplicáveis.

`APRESENTACAO_PARCIAL` consta como refinamento em M0.3. Sua adoção como estado persistido ou projeção calculada permanece pendente; não deve substituir os registros de quantidade e apresentação.

### 8.4 Conferência e checklist

Conferência: NAO_INICIADA → EM_ANDAMENTO → CONCLUIDA.  
Resultado de critério: CONFORME, NAO_CONFORME ou NAO_APLICAVEL.  
Classe: E, S ou I, definida na versão publicada do checklist. Respostas formalizadas e a versão aplicada são preservadas.

### 8.5 Pendência

PENDENTE → EM_REGULARIZACAO → AGUARDANDO_REAVALIACAO → REGULARIZADA, com possibilidade de PRAZO_VENCIDO, NAO_REGULARIZAVEL ou CANCELADA conforme regra e autorização.

PRAZO_VENCIDO é condição temporal/indicador, não encerramento nem recusa automática. A contagem inicia com comunicação formal comprovável. Evidência recebida exige reavaliação; só avaliação favorável regulariza.

### 8.6 Decisão e validação

Resultados de decisão: ACEITA, RECUSADA ou PENDENTE, no nível apropriado. A máquina proposta de DecisaoRecebimento em M0.3 (ACEITE_PROPOSTO, ACEITE_VALIDADO, PENDENCIA, RECUSA_PROPOSTA, RECUSADA, SUBSTITUIDA) detalha o ciclo, mas deve ser harmonizada com os estados/transições funcionais EST-REC-001 antes de se tornar vocabulário canônico.

Validação da coordenação: NAO_EXIGIDA, AGUARDANDO, APROVADA, DEVOLVIDA ou REJEITADA. A validação não dispensa critério E e não pode ser realizada pelo autor/executor quando a independência for obrigatória.

### 8.7 Custódia, decisão e localização — três dimensões

- **Custódia física:** SOB_GUARDA; TRANSFERENCIA_PENDENTE; SOB_NOVA_RESPONSABILIDADE após confirmação; ENCERRADA após entrega/devolução/destinação efetiva comprovada.
- **Decisão técnica:** ACEITA, RECUSADA ou PENDENTE, com o ciclo de proposta/validação a harmonizar.
- **Localização:** local atual e histórico de mudanças, sem alterar custodiante.

Os rótulos M0.3 SOB_CUSTODIA/ENCERRADO podem ser mapeados semanticamente para SOB_GUARDA/ENCERRADA, mas não manter como valores concorrentes. Os estados M0.3 EM_CONFERENCIA, PENDENTE, AGUARDANDO_VALIDACAO, ACEITO e RECUSADO não devem ser misturados em um único estado de custódia: representam etapa de conferência, pendência, validação ou resultado decisório.

### 8.8 AmostraOperacional

No escopo de recebimento, usar a condição NÃO_CRIADA, APTA_PARA_CRIACAO (calculada), CRIADA ou BLOQUEADA (calculada), conforme EST-REC-001 seção 26.9. A cardinalidade é ObjetoCustodia 1:0..1 AmostraOperacional.

Os estados posteriores CRIADA, ATIVA, EM_ENSAIO, ENCERRADA e CANCELADA_COM_HISTORICO propostos em M0.3 são dependentes de M03-16 e da compatibilização com o workflow de ensaios existente. Não redefinir o ciclo de ensaios nesta baseline de recebimento.

## 9. Processos operacionais consolidados

O fluxo ponta a ponta é:

**Solicitação → chegada física principal → apresentação dos itens → individualização e início da custódia → conferência → pendências/reavaliação, quando houver → decisão → validação independente, quando exigida → aceite e criação da AmostraOperacional ou recusa e destinação → continuidade da custódia, ensaios e histórico.**

| ID | Processo | Regra central | Fonte decisória |
|---|---|---|---|
| PROC-01 | Registrar/submeter solicitação | Solicitante identificado; ao menos um ItemDeclarado; autor autorizado. | D02, D18; EST-REC-001 |
| PROC-02 | Registrar chegada física principal | Registrar fato mesmo com divergência/documentação incompleta; chegada não é aceite. | D01, D02 |
| PROC-03 | Registrar apresentação e quantidades | Representar todos os itens; distinguir quantidades e não apresentação. | D02, D03, D19 |
| PROC-04 | Individualizar material e iniciar custódia | Somente material apresentado gera ObjetoCustodia; justificar agrupamento. | D03, D04, D07, D08 |
| PROC-05 | Executar conferência | Checklist publicado/versionado; respostas, avaliador e evidências preservados. | D01, D10, D11, D12 |
| PROC-06 | Abrir/comunicar/tratar pendência | Prazo começa com comunicação comprovável; vencimento não gera recusa automática. | D05, EST09 |
| PROC-07 | Formalizar aceite/recusa | Decidir no menor nível em que resultados possam divergir. | D04, D05, D06 |
| PROC-08 | Validar decisão | Coordenação independente nos casos obrigatórios; sem autoaprovação. | D06, D09, D10 |
| PROC-09 | Admitir objeto e criar amostra | Barreira formal D20; aceite e validações/bloqueios válidos; operação atômica/idempotente. | D20 |
| PROC-10 | Transferir custódia | Custodiante muda somente após confirmação do recebedor. | D07 |
| PROC-11 | Alterar localização | Registra origem/destino sem mudar custodiante. | D08 |
| PROC-12 | Devolver/destinar material recusado | Recusa não encerra custódia; encerrar somente após execução comprovada. | D06, D07 |
| PROC-13 | Retificar ato/dado formalizado | Novo ato, justificativa, evidência, autorização, validação/assinatura aplicáveis e impacto. | D09, D14, D16 |
| PROC-14 | Registrar chegada posterior | Novo fato sem retroatividade; reabertura autorizada ou nova solicitação vinculada quando exigido. | D19, EST08 |
| PROC-15 | Vincular/preservar evidências | Original preservado; versões, integridade, acesso e auditoria. | D13, D14 |
| PROC-16 | Consultar histórico/exportar | Escopo e permissões controlados; reconstrução de decisões e custódia. | D13–D15, D18 |
| PROC-17 | Assegurar continuidade e recuperação | Backup de dados/documentos/evidências, segregação, retenção e restauração testada. Processo transversal, não etapa do recebimento. | D17, G0-P06 |

Os processos PROC-01–PROC-16 detalham o fluxo de negócio. PROC-17 é controle transversal de continuidade, não cria uma etapa operacional de recebimento.

## 10. Regras de competência, autorização, assinatura e auditoria

1. Perfis funcionais: SOLICITANTE, RECEPÇÃO, CONFERENTE, COORDENAÇÃO e ADMINISTRADOR.
2. Permissões são explícitas e verificadas no momento da operação; acumulação de funções é permitida quando autorizada e compatível.
3. ADMINISTRADOR não possui autoridade técnica implícita.
4. Competência institucional deve ser sustentada por designação formal; perfil técnico não substitui designação.
5. Independência é obrigatória nos casos definidos; autor/executor não valida a própria decisão.
6. Indisponibilidade de validador não dispensa validação; decisão permanece bloqueada até atuação de autoridade independente formalmente competente.
7. Assinatura eletrônica formal e validação independente são controles distintos. A assinatura vincula signatário, intenção, ato e conteúdo exato.
8. Aceite final, validação da coordenação, encerramento da custódia e retificações excepcionais observam os requisitos de assinatura formal consolidados na EST07/EST-REC-001.
9. Toda operação crítica preserva ator, papel/permissão, competência aplicável, instante, alvo, conteúdo, justificativa e evidência conforme sua natureza.
10. Trilha de auditoria não substitui eventos de domínio; ambos devem ter semântica clara e encadeamento verificável.

## 11. Catálogo mínimo de eventos de domínio

Os eventos representam fatos, não apenas mudanças de status. Devem distinguir instante efetivo (`occurred_at`), instante de registro (`recorded_at`) e autor do registro (`recorded_by`); recebedor físico/decisor pode ser outro ator.

| Grupo | Eventos mínimos documentados |
|---|---|
| Solicitação | SOLICITACAO_CRIADA, SOLICITACAO_SUBMETIDA, SOLICITACAO_CANCELADA |
| Chegada/apresentação | CHEGADA_REGISTRADA, ITEM_APRESENTADO, ITEM_NAO_APRESENTADO; apresentação complementar como novo fato/evento conforme D19, sem impor ainda a entidade EventoApresentacao |
| Custódia | OBJETO_CUSTODIA_CRIADO, CUSTODIA_INICIADA, TRANSFERENCIA_SOLICITADA, TRANSFERENCIA_CONFIRMADA, LOCALIZACAO_ALTERADA |
| Conferência | CONFERENCIA_INICIADA, RESPOSTA_CHECKLIST_REGISTRADA, CONFERENCIA_CONCLUIDA |
| Pendência | PENDENCIA_ABERTA, PENDENCIA_COMUNICADA, PENDENCIA_PRORROGADA, REGULARIZACAO_RECEBIDA, PENDENCIA_REGULARIZADA, PENDENCIA_NAO_REGULARIZAVEL |
| Decisão/validação | DECISAO_ACEITE_REGISTRADA, DECISAO_RECUSA_REGISTRADA, VALIDACAO_COORDENACAO_REGISTRADA |
| Destinação | DEVOLUCAO_AUTORIZADA, DEVOLUCAO_REALIZADA, DESTINACAO_AUTORIZADA, DESTINACAO_REALIZADA, RECEBIMENTO_CONCLUIDO |
| Admissão | AMOSTRA_OPERACIONAL_CRIADA |
| Integridade/histórico | RETIFICACAO_REGISTRADA, EVIDENCIA_VINCULADA |

A taxonomia é lógica. A correspondência com eventos técnicos de auditoria, armazenamento e contrato físico será definida na arquitetura.

## 12. Invariantes essenciais

A lista completa INV-01–INV-34 permanece em M0.3 e deverá ser rastreada na matriz própria. Para leitura executiva, os invariantes essenciais são:

- recebimento principal único por solicitação;
- um ItemRecebimento por ItemDeclarado;
- ausência de apresentação não gera objeto, custódia, recusa técnica ou amostra;
- todo objeto tem origem rastreável e evento inicial de custódia;
- quantidades e unidades permanecem distinguíveis/reconciliáveis;
- agrupamento não esconde desfechos independentes;
- transferência exige confirmação; mudança de localização não altera custodiante;
- custódia só termina após destinação efetiva comprovada;
- checklist e respostas preservam a versão aplicada;
- pendência vencida permanece aberta e evidência recebida exige reavaliação;
- decisão ocorre na menor granularidade necessária;
- validação independente não admite autoaprovação;
- amostra exige aceite formal e bloqueios resolvidos, e é única por objeto;
- retificação preserva o original;
- fato e registro têm tempos separados;
- identificadores internos são distintos, únicos e não reutilizáveis;
- vínculos legados não são presumidos;
- toda operação crítica é autorizada e auditável;
- recebimento concluído não implica aceite universal nem encerramento automático de custódia;
- chegada complementar não retroage o fato original.

## 13. Registro de pendências e refinamentos não aprovados

| ID | Tema | Tratamento nesta baseline | Condição para encerramento |
|---|---|---|---|
| M03-01 | EventoApresentacao e apresentação parcial/chegada complementar | Regra D19 preservada; entidade específica não adotada como canônica. | Validar SIM12, exceção/reabertura e linhagem do objeto. |
| M03-02 | Agrupamento/fracionamento | Princípio de homogeneidade e decisão independente preservado. | Regras por categoria, exemplos reais e linhagem aprovados. |
| M03-03 | Unidades/conversão/reconciliação | Dimensões separadas; sem fórmulas presumidas. | Catálogo de unidades e regras técnicas aprovados. |
| M03-04 | Devolução/destinação | Custódia termina apenas após execução comprovada. | Procedimento, formulários, alçadas e comprovantes (G0-P04/P20). |
| M03-05 | Checklists E/S/I concretos | Estrutura e governança preservadas. | Checklists por categoria elaborados/revisados/aprovados (G0-P02/P17). |
| M03-06 | Competências nominais | Perfis funcionais separados de designação. | Ato formal, titulares, substitutos e vigências (G0-P01/P16). |
| M03-07 | Prazos/canais | Prazo inicia com comunicação formal comprovável. | Parâmetros e canais aprovados (G0-P03/P18). |
| M03-08 | Assinatura | Requisitos funcionais preservados; tecnologia/nível jurídico em aberto. | Deliberação institucional/jurídica (G0-P05/P19). |
| M03-09 | Protocolo/accession/QR | Semânticas distintas. | Padrão institucional aprovado (G0-P07). |
| M03-10 | Identidade externa | Solicitante não pressupõe conta externa na primeira entrega. | Modelo de identidade, vínculo e isolamento aprovado (G0-P21). |
| M03-11 | Anexos/evidências | Conceitos lógicos preservados. | Arquitetura, integridade, acesso, retenção (G0-P09/P24/P30). |
| M03-12 | Backup/continuidade | Requisito transversal, fora do domínio transacional. | RPO/RTO, retenção, responsáveis e restauração comprovada (G0-P06). |
| M03-13 | Retificação e impacto | Novo ato e preservação do original. | Matriz de impacto por etapa e casos (G0-P10/P27). |
| M03-14 | Migração/legado | Sem vínculo presumido. | Inventário, reconciliação e exceções (G0-P22). |
| M03-15 | Modelo físico de custódia | EventoCustodia como conceito lógico, sem escolher schema. | Revisão de arquitetura/contrato histórico. |
| M03-16 | Estados de amostra e workflow de ensaio | Estados de recebimento separados do ciclo de ensaio. | Mapeamento e regressão do workflow atual. |

## 14. Divergências explicitamente controladas

| Divergência | Regra de consolidação nesta versão | Situação |
|---|---|---|
| SOB_GUARDA × SOB_CUSTODIA | Usar SOB_GUARDA como rótulo funcional da custódia corrente, pois consta na máquina consolidada EST. SOB_CUSTODIA fica como rótulo proposto de M0.3. | Harmonização editorial proposta; validar na revisão integrada. |
| ENCERRADA × ENCERRADO | Usar ENCERRADA para situação da custódia, mantendo concordância com o conceito; ENCERRADO em M0.3 é rótulo proposto. | Harmonização editorial proposta. |
| ACEITA × ACEITO / ACEITE_VALIDADO | ACEITA é resultado decisório; ACEITO não deve ser estado de custódia. ACEITE_VALIDADO é estágio proposto do workflow decisório, a harmonizar. | Não consolidar em enum único. |
| RECUSADA × RECUSADO | RECUSADA é resultado da decisão; RECUSADO não deve ser estado de custódia. | Não consolidar em enum único. |
| TRANSFERENCIA_PENDENTE × TRANSFERENCIA_SOLICITADA | A solicitação é evento; TRANSFERENCIA_PENDENTE é projeção/condição enquanto não confirmada. | Mapeamento semântico, sujeito à especificação técnica. |
| APRESENTACAO_PARCIAL | Manter como informação/condição agregada proposta; não substituir apresentação e quantidades observadas por ocorrência. | M03-01/M03-03 pendentes. |
| EventoApresentacao | Não tornar entidade canônica nesta versão; registrar novo fato de apresentação de modo auditável e preservar vínculo ao item/recebimento. | M03-01 pendente. |
| Origem do ObjetoCustodia | Relação canônica obrigatória com ItemRecebimento; origem por ocorrência específica ainda a definir. | M03-01/M03-02/M03-03 pendentes. |

## 15. Rastreabilidade e evidências

A [Matriz de Harmonização de Estados, Transições e Eventos](MATRIZ_HARMONIZACAO_ESTADOS_TRANSICOES_EVENTOS_SEFI.md) complementa esta baseline para a correspondência de vocabulário. A rastreabilidade completa deve permanecer nas matrizes:
- D01–D20 × entidades/estados/eventos/invariantes/CA/SIM;
- G0-P01–P30 × RF/RT/artefatos;
- RF-001–RF-020 × processos e critérios;
- RT-001–RT-017 × controles e evidências;
- CA01–CA37 e SIM01–SIM12 × processos e regras.

As associações feitas nas matrizes são analíticas até validação. Caso uma associação não esteja expressamente demonstrada na fonte, deve ser rotulada como proposta/inferência, não como evidência executada.

## 16. Critérios de consistência para a próxima revisão

Antes de considerar a baseline pronta para validação operacional:
1. Conferir cada regra contra D01–D20 e as seções decisórias EST01–EST10.
2. Verificar as sete cardinalidades aprovadas, sem introduzir relações obrigatórias adicionais.
3. Verificar que estados de custódia, decisão, conferência, validação, pendência e localização não estejam fundidos.
4. Verificar D19 e EST08 com SIM12 e cenários de retificação, sem retroatividade.
5. Verificar agrupamento/fracionamento e reconciliação com SIM03/SIM04.
6. Verificar a barreira D20 com SIM01/SIM04 e critérios de aceite.
7. Verificar recusa, permanência em custódia e destinação com SIM06.
8. Verificar transferência e localização com SIM07/SIM08.
9. Verificar retificação após amostra/ensaio com SIM09 e D09.
10. Verificar concorrência/idempotência e acesso com SIM10/SIM11.
11. Não declarar testes executados nem simulações homologadas sem evidência específica.
12. Atualizar matrizes e catálogo apenas após readback e conferência dos vínculos.

## 17. Situação formal

- D01–D20: **RATIFICADAS; preservadas**.
- Cardinalidades canônicas M0.2: **PRESERVADAS**.
- EST01–EST10: **decisões funcionais aprovadas; regras consolidadas como fontes**.
- M0.3: **proposta lógica em revisão; refinamentos M03-01–M03-16 não presumidos como resolvidos**.
- Esta baseline: **CONSOLIDAÇÃO DOCUMENTAL v0.1 — NÃO VALIDADA**.
- Validação operacional SIM01–SIM12: **PENDENTE**.
- CA01–CA37: **especificação documental; execução não comprovada**.
- Gate G0: **NÃO APROVADO**.
- Implementação: **NÃO AUTORIZADA**.

## 18. Histórico

| Versão | Data | Alteração |
|---|---|---|
| 0.1 | 2026-11-11 | Primeira consolidação de domínio e processos; preserva decisões/cardinalidades, separa dimensões de estado e explicita refinamentos pendentes. |
