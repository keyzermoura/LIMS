# Proposta de Resolução da API03 — Quantidade e Agrupamento de Objetos de Custódia

**Identificador:** PROP-LIMS-API03-001  
**Versão:** 0.1  
**Situação:** Proposta técnica para validação funcional e institucional; não aprovada para implementação  
**Decisão relacionada:** API03 / DEC05 / COMP06  
**Data:** 2026-11-09  
**Repositório:** keyzermoura/LIMS — branch `main`

---

## 1. Objetivo

Propor uma regra operacional e um contrato de dados coerentes para representar quantidades apresentadas e sua distribuição em `CustodyObjects`, respeitando a diretriz DEC05 já aprovada pelo usuário como orientação de desenho.

O problema central é distinguir:

- quantas unidades/quantidade foram declaradas na solicitação;
- quanto material efetivamente chegou;
- quantos objetos lógicos de custódia foram criados;
- quanto material cada objeto representa;
- quando unidades precisam ser individualizadas;
- quando é legítimo manter unidades homogêneas agrupadas.

Esta proposta não decide procedimentos técnicos de ensaio por conta própria. A autorização de agrupamento deve ser compatível com o procedimento laboratorial e com a necessidade de resultados, decisões e destinações independentes.

## 2. Referências e premissas

1. DEC05, aprovada pelo usuário como diretriz de desenho em 2026-11-09, define que um `ItemRecebimento` pode originar zero ou vários `ObjetosCustodia`; um objeto pode originar no máximo uma `DeviceSample`.
2. Unidades homogêneas podem ser agrupadas quando avaliadas como conjunto e quando a decisão/resultado laboratorial for coletiva.
3. Quando houver identidade, resultado, decisão ou destinação independente por unidade, as unidades devem ser representadas por objetos de custódia distintos.
4. A existência de número de série, isoladamente, não obriga resultado individual, mas as identidades disponíveis devem ser preservadas.
5. Não se cria uma tabela obrigatória `UnidadeFisica` na primeira versão.
6. Material não apresentado não cria objeto de custódia nem amostra operacional.
7. Fracionamento posterior deve ser formal, auditável e quantitativamente reconciliado.

## 3. Vocabulário e grandezas distintas

| Conceito | Significado | Exemplo |
|---|---|---|
| Quantidade declarada | Quantidade informada na solicitação. | 10 agulhas. |
| Quantidade apresentada | Quantidade efetivamente entregue na chegada. | 8 agulhas. |
| Quantidade representada | Parcela do material apresentado representada por um CustodyObject. | Um objeto agrupado representa 5 agulhas. |
| Número de objetos de custódia | Quantidade de registros lógicos de guarda/rastreabilidade. | Dois objetos agrupados podem representar 8 agulhas. |
| Unidade física | Peça ou unidade material existente no mundo físico. | Uma agulha, seringa ou equipo. |

**Regra fundamental:** número de objetos de custódia não é sinônimo de quantidade física apresentada. Um objeto agrupado pode representar várias unidades físicas, desde que o agrupamento seja autorizado e a quantidade permaneça rastreável.

## 4. Regra proposta de cardinalidade

### 4.1 Relação ItemRecebimento → CustodyObject

- Um `ItemRecebimento` apresentado pode originar um ou vários `CustodyObjects`.
- Um `ItemRecebimento` não apresentado deve originar zero `CustodyObjects`.
- Um item apresentado com quantidade positiva deve originar ao menos um objeto, salvo se houver uma situação excepcional explicitamente modelada e autorizada. A proposta para o fluxo ordinário é não admitir apresentação sem objeto de custódia.
- Cada `CustodyObject` pertence a exatamente um `ItemRecebimento`.
- Um `CustodyObject` representa uma quantidade positiva, expressa em unidade de medida explícita.
- A soma das quantidades representadas pelos objetos de um item deve reconciliar exatamente com a quantidade apresentada, após conversões formalmente registradas quando necessárias.

### 4.2 Tipos de objeto

Manter, como proposto no modelo relacional, dois tipos lógicos:

- `INDIVIDUAL`: objeto representa uma unidade física ou unidade rastreável individual. Quantidade representada normalmente igual a 1 na unidade de contagem aplicável.
- `AGRUPADO`: objeto representa conjunto homogêneo de unidades sob guarda e avaliação coletiva autorizada. Quantidade representada maior que zero.

A regra “normalmente igual a 1” para objeto individual deve ser confirmada por unidade de medida e categoria de material. Não se deve codificar universalmente quantidade inteira sem avaliar materiais cuja unidade operacional seja comprimento, massa, volume ou outra grandeza.

## 5. Critério de agrupamento

O agrupamento é permitido somente quando todas as condições abaixo forem verdadeiras:

1. As unidades são suficientemente homogêneas para o objetivo de recebimento e para o plano de avaliação.
2. O procedimento técnico aplicável admite avaliação coletiva ou tratamento conjunto.
3. Não há necessidade prevista de emitir resultados, decisões de aceite/recusa ou destinações independentes por unidade.
4. As identidades individuais disponíveis (por exemplo, números de série, códigos, marcações ou identificadores de embalagem) são preservadas em informação estruturada ou evidência vinculada ao objeto.
5. A quantidade e a unidade de medida são inequívocas.
6. O critério de agrupamento, o responsável e a justificativa ficam registrados.

Se qualquer uma dessas condições não for atendida, a opção segura é individualizar os objetos na chegada.

**Atenção:** fabricante e lote iguais, por si sós, não são suficientes para autorizar agrupamento. São atributos relevantes de homogeneidade, mas não substituem a avaliação do procedimento, da identidade e da independência dos resultados.

## 6. Critério de individualização

Criar objetos distintos quando:

- cada unidade tiver número de série ou identificador que precise ser rastreado de forma independente no fluxo;
- resultados ou decisões precisarem ser atribuídos separadamente;
- unidades puderem ter destinos, condições de guarda, lacres ou responsáveis diferentes;
- o plano de ensaio exigir seleção/rastreabilidade individual;
- houver heterogeneidade relevante entre as unidades;
- o procedimento técnico ou requisito regulatório exigir identificação individual.

A existência de vários ensaios ou corpos de prova derivados de uma única amostra operacional não exige, por si só, vários objetos de custódia. A individualização deve ocorrer quando a unidade material precisar de trajetória decisória ou rastreabilidade independente, não apenas porque será submetida a mais de um ensaio.

## 7. Reconciliação quantitativa

Para cada `ItemRecebimento` apresentado:

`quantidade_apresentada = soma(quantidade_representada de cada CustodyObject)`

A igualdade deve ser calculada na mesma unidade de medida. Se a unidade de medida declarada e a unidade de contagem efetiva forem diferentes, a conversão deve ser explícita, documentada e sem perda de precisão relevante.

Regras propostas:

- quantidades devem ser positivas;
- não aceitar quantidade negativa ou zero em objeto persistido;
- não permitir soma superior ou inferior à quantidade apresentada;
- não permitir objetos com unidade de medida incompatível sem conversão registrada;
- não arredondar silenciosamente para forçar reconciliação;
- usar representação decimal adequada à grandeza, evitando ponto flutuante binário para valores quantitativos persistidos;
- a precisão e escala máximas devem ser definidas por unidade de medida/categoria de material.

A validação deve ocorrer no backend e na transação de recebimento. A interface pode antecipar mensagens, mas não é a autoridade de integridade.

### 7.1 Item não apresentado

Para `NOT_PRESENTED`:

- quantidade apresentada deve ser zero;
- lista de objetos deve ser vazia;
- não pode existir evento inicial de custódia para esse item;
- não pode ser criada amostra operacional.

### 7.2 Item apresentado

Para `PRESENTED`:

- quantidade apresentada deve ser maior que zero;
- deve existir pelo menos um objeto de custódia;
- cada objeto deve representar quantidade positiva;
- a soma deve reconciliar com a quantidade apresentada.

A distinção entre estado de apresentação e decisão técnica deve permanecer: item apresentado pode continuar pendente ou ser posteriormente aceito/recusado; isso não altera retroativamente sua quantidade de chegada.

## 8. Fracionamento após a chegada

Se um objeto agrupado precisar ser dividido posteriormente:

1. a operação deve ser autorizada conforme perfil e procedimento;
2. o objeto de origem deve permanecer no histórico;
3. devem ser criados objetos-filhos com referência explícita ao objeto de origem;
4. a soma das quantidades dos filhos deve ser igual à quantidade fracionada do objeto de origem;
5. o saldo remanescente, quando houver, deve permanecer representado de forma explícita;
6. registrar motivo, responsável, data/hora efetiva, data/hora do registro e evidências aplicáveis;
7. não alterar silenciosamente quantidade, identidade, tipo ou histórico do objeto original.

A modelagem física de relação pai-filho, saldo e eventos de fracionamento depende da análise de COMP02/COMP03 e da decisão institucional sobre correções/exceções (EST08). Esta proposta define o requisito de domínio, não a estrutura final de tabelas nem o endpoint.

## 9. Exemplos de aplicação

| Cenário | Quantidade apresentada | Objetos de custódia | Justificativa |
|---|---:|---|---|
| 10 agulhas do mesmo lote avaliadas como conjunto | 10 unidades | 1 agrupado, quantidade 10 | Avaliação coletiva permitida e sem decisões individuais. |
| 10 agulhas com resultados individuais | 10 unidades | 10 individuais, quantidade 1 cada | Resultado/decisão independente por agulha. |
| 3 seringas serializadas, avaliação coletiva autorizada | 3 unidades | 1 agrupado, quantidade 3, preservando os 3 seriais | Serialização não implica automaticamente decisão individual; identidade deve ser preservada. |
| 3 seringas serializadas, rastreabilidade individual obrigatória | 3 unidades | 3 individuais | Cada unidade exige trajetória independente. |
| 1 equipo submetido a vários ensaios | 1 unidade | 1 individual | Vários ensaios e corpos de prova podem derivar da mesma amostra operacional. |
| 1 cateter avaliado por segmentos para ensaios distintos, sem decisão independente por segmento | 1 unidade | 1 individual | Segmentos são corpos de prova, não necessariamente objetos de custódia. |
| 10 unidades declaradas, 5 entregues | 5 unidades | 1 ou mais objetos representando exatamente 5 | Quantidade declarada e apresentada são distintas; só as cinco entregues entram em custódia. |
| Embalagem coletiva mantida fechada como unidade de guarda | Quantidade conforme conteúdo comprovado e unidade definida | 1 agrupado, se o conteúdo e a contagem forem conhecidos; caso contrário, registrar a unidade de embalagem e a limitação de conferência | O objeto representa a unidade efetivamente sob guarda; não inventar conteúdo não verificado. |

Os exemplos são orientadores. A decisão concreta depende da unidade de medida, do procedimento técnico, da conferência possível na chegada e da necessidade de rastreabilidade.

## 10. Proposta para o contrato HTTP

Sem atualizar ainda a especificação nem o OpenAPI, recomenda-se que o contrato futuro represente separadamente:

- `presented_quantity` e `presented_unit_of_measure` no item de recebimento;
- `object_type` em cada objeto;
- `represented_quantity` e `unit_of_measure` em cada objeto;
- `grouping_basis` ou justificativa estruturada para objetos agrupados;
- identificação observada e identidades individuais disponíveis, sem obrigar serial universal;
- referência ao objeto de origem para fracionamentos posteriores, quando esse fluxo for definido.

A estrutura atual de exemplo contém `grouping_description` e `represented_quantity`, mas ainda não torna explícito o tipo de objeto, a unidade de medida, a justificativa controlada nem a reconciliação. Esses campos são candidatos, não nomes finais de contrato.

### 10.1 Validações HTTP candidatas

| Condição | Resultado de domínio proposto |
|---|---|
| `NOT_PRESENTED` com quantidade positiva ou objetos | Rejeitar validação. |
| `PRESENTED` com quantidade zero ou sem objetos | Rejeitar validação. |
| Objeto com quantidade nula, zero ou negativa | Rejeitar validação. |
| Soma dos objetos diferente da quantidade apresentada | Rejeitar validação. |
| Unidade de medida incompatível sem conversão explícita | Rejeitar validação. |
| Objeto agrupado sem justificativa/critérios exigidos | Rejeitar ou encaminhar para validação, conforme política a aprovar. |
| Identificadores individuais omitidos apesar de exigência de rastreabilidade | Rejeitar validação. |
| Objeto individual representando quantidade diferente da unidade individual definida para a categoria | Rejeitar validação ou exigir regra de unidade específica. |

Os códigos HTTP e o schema de erro devem ser padronizados em conjunto com API06/API07 e não são definidos nesta proposta.

## 11. Impactos no modelo relacional

Manter as entidades e cardinalidades de DEC05, com os seguintes requisitos lógicos:

- `ReceiptItem.quantity_presented` e sua unidade de medida devem representar o total apresentado.
- `CustodyObject.quantity` e `CustodyObject.unit_of_measure` devem ser não nulos para objetos persistidos.
- `CustodyObject.object_type` deve distinguir individual e agrupado.
- `grouping_basis` deve registrar o fundamento do agrupamento quando aplicável.
- Deve ser possível preservar identificadores observados, inclusive múltiplos identificadores em objeto agrupado.
- A integridade da soma entre ReceiptItem e seus CustodyObjects deve ser garantida por transação/serviço e, quando tecnicamente viável, por restrições adicionais.
- Não introduzir tabela obrigatória `PhysicalUnit`/ `UnidadeFisica` nesta primeira versão.
- Não criar N:M entre CustodyObject e DeviceSample.
- Não alterar constraints existentes de `DeviceSample` nesta decisão; API08/COMP04 permanece separada.

Uma restrição CHECK simples não consegue, em geral, validar soma agregada entre linhas filhas. A estratégia física para essa integridade deve ser escolhida após revisão do PostgreSQL e da arquitetura de persistência, sem presumir trigger ou constraint específica nesta etapa.

## 12. Questões que ainda exigem decisão

| ID | Questão | Recomendação técnica | Responsável |
|---|---|---|---|
| COMP06.1 | Quais categorias de material permitem agrupamento por padrão? | Não criar autorização universal; vincular a procedimento/categoria e permitir exceções justificadas. | Responsável técnico/laboratorial. |
| COMP06.2 | Qual catálogo de unidades de medida será adotado? | Vocabulário controlado, com dimensão e precisão; evitar texto livre como única fonte. | Responsável técnico e arquitetura de dados. |
| COMP06.3 | Como registrar múltiplos seriais/identificadores em objeto agrupado? | Preservar lista estruturada ou evidência verificável, sem exigir tabela de unidade física universal. | Responsável funcional e técnico. |
| COMP06.4 | Embalagem fechada sem contagem verificável: o que representa a quantidade? | Distinguir quantidade de embalagens e conteúdo declarado/não verificado. | Responsável pelo recebimento. |
| COMP06.5 | Quais situações exigem fracionamento e como representar saldo? | Definir operação auditável pai-filho com reconciliação quantitativa. | Responsável técnico e governança. |
| COMP06.6 | Quantidade individual deve ser sempre 1? | Não universalizar; definir conforme unidade de medida e classe de material. | Responsável técnico. |
| COMP06.7 | Quando agrupamento requer validação de coordenação? | Relacionar ao risco, procedimento e independência dos resultados; depende de EST03/EST10. | Responsável funcional e coordenação. |

## 13. Critérios para considerar API03 resolvida

API03 só poderá ser marcada como aprovada quando:

1. o responsável técnico confirmar categorias e condições de agrupamento;
2. o catálogo/unidade de medida e a precisão quantitativa forem definidos;
3. a preservação de identificadores em agrupamentos for especificada;
4. a regra de reconciliação for aceita;
5. fracionamento e saldo tiverem tratamento funcional definido;
6. a proposta for confrontada com os procedimentos de recebimento e ensaio aplicáveis;
7. os impactos no modelo relacional e no contrato HTTP forem revisados e aprovados;
8. a decisão e sua evidência forem registradas na matriz DEC e na matriz API.

Após a aprovação, atualizar coordenadamente a especificação HTTP, o OpenAPI, o modelo relacional e a interface. Somente depois de revisão e autorização específica poderá ser planejada implementação.

## 14. Controle de execução

**Realizado:** elaboração desta proposta documental de resolução da API03, baseada na DEC05 e nos achados REV01, REV02 e REV08.

**Não realizado:** alteração da especificação API existente, OpenAPI, modelo relacional, matriz DEC, código, banco de dados, migrações, endpoints, frontend, testes, build ou CI.

**Estado:** as regras gerais de quantidade, agrupamento, individualização, reconciliação e ausência de tabela universal obrigatória de UnidadeFisica foram validadas pelo responsável pelo projeto em revisão em 2026-11-10. O fechamento integral de API03 permanece pendente: categorias autorizadas, catálogo e precisão de unidades de medida, preservação de identificadores em agrupamentos, embalagem sem contagem verificável, fracionamento/saldo e necessidade de validação da coordenação ainda exigem definição pelos responsáveis técnicos e funcionais. A validação não equivale a aprovação institucional nem autoriza implementação.

## 15. Histórico de alterações

| Versão | Data | Alteração |
|---|---|---|
| 0.1 | 2026-11-09 | Criação da proposta de regra de quantidade, agrupamento, individualização, reconciliação e fracionamento para API03. |
| 0.2 | 2026-11-10 | Registro da validação das regras gerais pelo responsável pelo projeto em revisão; detalhes operacionais e aprovação institucional permanecem pendentes. |
