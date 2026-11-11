# Comparação de Domínio — M0.2 aprovado × M0.3 proposto

**Identificador:** CMP-DOM-SEFI-M02-M03-001  
**Versão:** 0.1  
**Data:** 2026-11-11  
**Natureza:** análise comparativa documental; não altera nem reabre decisões aprovadas.  
**Status:** análise inicial; divergências de nomenclatura e refinamentos sujeitos a validação.

## 1. Objetivo

Comparar o modelo conceitual M0.2, aprovado funcionalmente, com o modelo lógico M0.3, elaborado para revisão, verificando:
- preservação das cardinalidades aprovadas;
- novos conceitos e refinamentos;
- compatibilidade com EST-REC-001 v1.7 e SIM-SEFI-REC-001 v1.2;
- diferenças de nomenclatura de estados/eventos;
- pontos que precisam de validação antes de consolidar a especificação integrada.

## 2. Fontes e status

| Fonte | Versão | Situação declarada |
|---|---|---|
| `docs/MODELO_CONCEITUAL_DOMINIO_SOLICITACAO_RECEBIMENTO.md` (MOD-DOM-001) | 0.7 | M0.2 aprovado funcionalmente; validação operacional e complementos técnicos pendentes; não aprovado para implementação |
| `docs/MODELO_LOGICO_REVISADO_DOMINIO_SEFI_M0_3.md` (MOD-LOG-SEFI-003) | 0.1 | Proposta documental para revisão; aguarda validação |
| `docs/ESTADOS_E_TRANSICOES_SOLICITACAO_RECEBIMENTO.md` (EST-REC-001) | 1.7 | Proposta documental consolidada; validação operacional pendente; não aprovada para implementação |
| `docs/VALIDACAO_CENARIOS_OPERACIONAIS_SEFI.md` (SIM-SEFI-REC-001) | 1.2 | Simulação documental; SIM01–SIM12 sem validação operacional e sem teste de software |

A precedência é: D01–D20 ratificadas e cardinalidades aprovadas em M0.2 prevalecem; M0.3 e demais propostas refinam/documentam, mas não modificam a baseline sem validação explícita.

## 3. Cardinalidades canônicas — preservadas

M0.2 seção 15.2 registra como canônicas e aprovadas as seguintes cardinalidades. M0.3 seção 6 repete essas relações:

| Relação | M0.2 | M0.3 | Resultado |
|---|---|---|---|
| Solicitante 1:N Solicitação | Sim | Sim | Preservada |
| Solicitação 1:N ItemDeclarado | Sim | Sim | Preservada |
| Solicitação 1:0..1 Recebimento principal | Sim | Sim | Preservada |
| ItemDeclarado 1:1 ItemRecebimento | Sim | Sim | Preservada |
| ItemRecebimento 1:0..N ObjetoCustodia | Sim | Sim | Preservada |
| ObjetoCustodia 1:0..1 AmostraOperacional | Sim | Sim | Preservada |
| AmostraOperacional 1:N Ensaio | Sim | Sim | Preservada |

**Conclusão:** não foi identificada alteração explícita das sete cardinalidades canônicas aprovadas em M0.2. Isso é compatível com a afirmação de M0.3 de que preserva M0.2.

## 4. Novos refinamentos introduzidos em M0.3

| Refinamento | Base M0.2 / D01–D20 | Tratamento em M0.3 | Situação |
|---|---|---|---|
| EventoApresentacao | D19 exige nova ocorrência de chegada posterior sem retroagir fato original; M0.2 mantém um único recebimento principal | Novo conceito ligado a ItemRecebimento, com múltiplas apresentações e tempos/atores/evidências próprios | Proposta; M03-01 pendente |
| Quantidades por dimensão | M0.2 e D03 distinguem declarado e apresentado | Formaliza declarada, apresentada, sob custódia, aceita, recusada e não apresentada | Refinamento útil; unidades, precisão e reconciliação pendentes (M03-02/M03-03) |
| Granularidade por ObjetoCustodia | Cardinalidade ItemRecebimento 1:0..N ObjetoCustodia aprovada | Define objeto individual ou agrupamento homogêneo justificado, com linhagem e reconciliação | Princípio descrito; regras por categoria pendentes |
| Separação de custódia | M0.2 já separa ObjetoCustodia de EventoCustodia | Formaliza evento inicial, transferência, localização, devolução/destinação e estado derivado | Refinamento; compatibilidade dos estados precisa ser harmonizada |
| Checklists versionados | D11–D12 e estrutura aprovada em G0-P02/P17 | Explicita ChecklistModelo, VersaoChecklist, CriterioChecklist e RespostaChecklist | Estrutura conceitual; conteúdo e governança detalhada pendentes |
| Evidências | D13 e G0-P09/P24 | Explicita Evidencia e VinculoEvidencia | Proposta lógica; arquitetura/armazenamento/retensão pendentes |
| Retificação | D09 e G0-P10/P27 | Entidade Retificacao com original, corrigido, autorização, impacto e evidência | Proposta lógica; metodologia institucional pendente |
| Competência e designação | D10/D15 e G0-P01/P16 | DesignacaoCompetencia separada de Perfil/Permissao | Conceito necessário; designações nominais pendentes |
| Invariantes | Regras de integridade em M0.2/EST-REC-001 | Catálogo INV-01–INV-34 | Formalização proposta; rastreabilidade CA/SIM e validação pendentes |

## 5. Diferenças de nomenclatura e semântica a harmonizar

As diferenças abaixo não são automaticamente contradições funcionais, mas impedem uma especificação integrada inequívoca enquanto não houver mapeamento explícito.

| Conceito | EST-REC-001 v1.7 / SIM v1.2 | M0.3 v0.1 | Análise / ação necessária |
|---|---|---|---|
| Estado de custódia sob guarda | `SOB_GUARDA` | `SOB_CUSTODIA` | Confirmar equivalência semântica e definir um identificador canônico; não manter dois rótulos concorrentes sem motivo |
| Estado de custódia encerrada | `ENCERRADA` | `ENCERRADO` | Alinhar nomenclatura e esclarecer se o alvo é estado da custódia ou do objeto |
| Decisão favorável | `ACEITA` (Decisão do item/objeto) | `ACEITE_VALIDADO` (DecisaoRecebimento) e `ACEITO` (ObjetoCustodia) | Separar estado da decisão e estado agregado do objeto; documentar transição/mapeamento |
| Decisão desfavorável | `RECUSADA` (Decisão) | `RECUSADA` (DecisaoRecebimento) e `RECUSADO` (ObjetoCustodia) | Separar resultado decisório de situação do objeto e harmonizar rótulos |
| Transferência | `TRANSFERENCIA_PENDENTE`, `SOB_NOVA_RESPONSABILIDADE` (estados de custódia em EST) | Eventos `TRANSFERENCIA_SOLICITADA` e `TRANSFERENCIA_CONFIRMADA`; custódia projetada separa situação, custodiante e localização | Confirmar se a máquina de estados M0.3 representa os mesmos marcos como eventos/projeções; preservar a regra de confirmação do recebedor |
| Apresentação parcial | EST-REC-001 v1.7 lista AGUARDANDO_CHEGADA, APRESENTADO e NAO_APRESENTADO; SIM03 descreve quantidades divergentes | M0.3 acrescenta `APRESENTACAO_PARCIAL` | Novo estado/refinamento; validar se é estado persistido ou projeção calculada e como se relaciona com apresentações sucessivas |
| Eventos de chegada complementar | EST e SIM12 preveem nova solicitação ou exceção formal sem retroatividade | M0.3 propõe `EventoApresentacao` e `APRESENTACAO_COMPLEMENTAR_REGISTRADA` | Validar a proposta M03-01; não tratá-la como regra institucional já decidida |

## 6. Ponto estrutural a esclarecer: origem do ObjetoCustodia

M0.3 mantém a cardinalidade aprovada `ItemRecebimento 1:0..N ObjetoCustodia` e propõe também `EventoApresentacao 1:0..N ObjetoCustodia`, além do invariante INV-06, segundo o qual todo ObjetoCustodia tem origem rastreável em ItemRecebimento e apresentação correspondente.

A combinação é plausível, mas exige uma regra explícita para:
1. se cada ObjetoCustodia nasce de exatamente um EventoApresentacao;
2. se um objeto pode agregar material apresentado em mais de uma ocorrência;
3. como tratar fracionamento posterior de objeto originado de apresentação anterior;
4. como reconciliar quantidade do item, das apresentações e dos objetos;
5. como impedir duplicidade de origem ou dupla contagem.

Este ponto está relacionado a M03-01, M03-02 e M03-03 e deve ser resolvido conceitualmente antes de qualquer desenho físico.

## 7. Compatibilidade com a simulação e critérios

- SIM01–SIM12 foram escritos com a nomenclatura de EST-REC-001 v1.5/v1.7, incluindo `SOB_GUARDA`.
- M0.3 introduz rótulos diferentes (`SOB_CUSTODIA`, `ENCERRADO`, `APRESENTACAO_PARCIAL`) e, portanto, precisa de um quadro de correspondência.
- CA01–CA37 são critérios documentais; CA25–CA37 aparecem como complementos propostos no histórico de revisão multidisciplinar.
- A matriz D01–D20 × CA/SIM deve refletir as associações declaradas nas fontes e distinguir associações analíticas.
- A simulação não comprova validação operacional nem execução de testes.

## 8. Questões M03-01 a M03-16

M0.3 registra dezesseis questões pendentes. Para fins desta comparação, destacam-se:
- M03-01 — EventoApresentacao/D19;
- M03-02 — agrupamento/fracionamento e linhagem;
- M03-03 — unidades, precisão, conversão e reconciliação;
- M03-04 — devolução/destinação;
- M03-05 — checklists concretos;
- M03-06 — matriz nominal de competências;
- M03-07 — prazos e canais;
- M03-08 — modalidade/nível jurídico da assinatura;
- M03-09 — protocolo, accession e QR;
- M03-10 — identidade externa;
- M03-11 — anexos/evidências;
- M03-12 — backup/continuidade;
- M03-13 — retificação e impacto;
- M03-14 — migração/legado;
- M03-15 — modelo físico de custódia;
- M03-16 — estados da AmostraOperacional e compatibilidade com workflow atual.

Nenhuma dessas questões é declarada resolvida por este relatório.

## 9. Parecer comparativo

1. As cardinalidades canônicas aprovadas em M0.2 foram preservadas nominalmente em M0.3.
2. M0.3 amplia a formalização do domínio e explicita invariantes, mas contém refinamentos novos que aguardam validação.
3. A proposta EventoApresentacao é a alteração conceitual mais sensível por afetar D19, apresentações múltiplas, linhagem e quantidades.
4. A nomenclatura de estados entre EST-REC-001, SIM e M0.3 precisa ser harmonizada antes de consolidar uma máquina de estados única.
5. O M0.2 deve permanecer preservado como referência aprovada; M0.3 não o substitui até validação explícita.
6. O modelo relacional preliminar e o contrato de histórico/aceite permanecem propostas técnicas, não decisões de implementação.

## 10. Encaminhamento

- Manter M0.2 v0.7 como baseline conceitual aprovada.
- Manter M0.3 v0.1 como proposta lógica para revisão.
- Registrar as diferenças deste documento na especificação integrada.
- Harmonizar nomenclatura de estados e eventos em uma tabela de correspondência, sem alterar os documentos-fonte.
- Resolver M03-01 a M03-03 e demais questões aplicáveis por análise e validação, não por inferência.
- Só depois revisar o modelo relacional e contratos técnicos.
- Não alterar código, banco, API, frontend, CI ou infraestrutura.

## 11. Situação formal

- Comparação M0.2 × M0.3: **ANÁLISE DOCUMENTAL INICIAL**.
- M0.2: **APROVADO FUNCIONALMENTE**, conforme fonte.
- M0.3: **AGUARDANDO REVISÃO/VALIDAÇÃO**.
- Gate G0: **NÃO APROVADO**.
- Implementação: **NÃO AUTORIZADA**.
