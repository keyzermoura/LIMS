# Recomendação Funcional — DEC04 e DEC05: Custódia e Granularidade da Amostra

**Identificador:** REC-LIMS-DEC-001  
**Versão:** 0.1  
**Situação:** Recomendação técnica para validação funcional; não constitui decisão institucional aprovada  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Data:** 2026-11-09

---

## 1. Objetivo

Apresentar uma recomendação prática para resolver DEC04 e DEC05, utilizando exemplos de materiais ensaiados pelo laboratório: agulhas, seringas, equipos e cateteres.

O foco é definir em que nível registrar:
- o item declarado na solicitação;
- o item efetivamente apresentado no recebimento;
- a unidade física;
- o objeto mantido sob custódia;
- a amostra operacional do LIMS;
- o corpo de prova utilizado em cada ensaio.

A recomendação procura evitar tanto a individualização excessiva (um cadastro para cada unidade sem necessidade técnica) quanto o agrupamento que elimina rastreabilidade de resultados ou de destino.

**Limite:** trata-se de proposta para discussão e aprovação do responsável funcional/técnico. Não altera o modelo relacional, não aprova formalmente DEC04/DEC05 e não autoriza implementação.

## 2. Recomendação executiva

Recomenda-se adotar as seguintes regras-base:

1. **Uma linha declarada gera exatamente um ItemRecebimento** no recebimento principal, inclusive quando o material não for apresentado.
2. **Um ItemRecebimento pode originar zero ou vários ObjetosCustodia.** Zero quando não houve apresentação; um ou vários quando o material foi apresentado, conforme a forma de guarda e a necessidade de rastreabilidade.
3. **ObjetoCustodia é a unidade de guarda e rastreabilidade física**, podendo representar uma unidade individual ou um agrupamento homogêneo explicitamente identificado.
4. **Um ObjetoCustodia aceito gera no máximo uma AmostraOperacional.** Para o fluxo ordinário de materiais que serão ensaiados no LIMS, recomenda-se que gere exatamente uma. Objeto recusado, não apresentado ou ainda pendente não gera amostra.
5. **Uma AmostraOperacional pode possuir vários ensaios e vários corpos de prova.** Não se cria uma nova amostra apenas porque haverá outro ensaio ou corpo de prova.
6. **Quando unidades de um mesmo ItemRecebimento precisarem de resultados, decisões ou destinos independentes, devem ser separadas em ObjetosCustodia distintos antes da criação das amostras.**
7. **Não adotar relação N:M entre ObjetoCustodia e DeviceSample no desenho-base.** Recomenda-se relação 1:0..1, mais simples e rastreável. Necessidade excepcional de uma amostra reunir objetos diferentes deverá ser demonstrada por caso real e tratada como decisão específica.
8. **A custódia começa na chegada física**, independentemente de aceite ou da criação da amostra. O evento inicial deve apontar para o ObjetoCustodia.
9. **Não criar entidade UnidadeFisica independente na primeira versão**, salvo quando houver requisito real de rastrear individualmente unidades internas de um agrupamento. A individualização poderá ser introduzida de forma aditiva quando necessária.

Esta proposta separa três conceitos que não devem ser confundidos: quantidade apresentada, unidade sob custódia e amostra operacional.

## 3. Vocabulário operacional recomendado

| Conceito | Significado operacional | Exemplo |
|---|---|---|
| ItemDeclarado | Linha de material informada na solicitação, com descrição e quantidade declarada. | Agulha hipodérmica, lote X, quantidade declarada 10. |
| ItemRecebimento | Registro daquela linha no recebimento, incluindo quantidade apresentada e situação de apresentação. | Da linha de 10 agulhas, foram apresentadas 8. |
| Unidade física | Peça individual existente no mundo físico. Só precisa ser cadastrada individualmente quando a rastreabilidade exigir. | Uma seringa com número de série próprio. |
| ObjetoCustodia | Unidade lógica de guarda/rastreabilidade no LIMS. Pode representar uma peça ou um conjunto homogêneo. | Uma seringa serializada ou um conjunto de 8 agulhas do mesmo lote. |
| AmostraOperacional | Registro que controla a avaliação laboratorial no LIMS após o aceite. | Conjunto de agulhas aceito para avaliação de diâmetro. |
| Corpo de prova | Unidade ou porção efetivamente selecionada/preparada para um ensaio, conforme método. | Uma agulha selecionada do conjunto para determinada medição. |

A quantidade declarada e a apresentada pertencem ao nível do item. A quantidade do ObjetoCustodia informa o que aquele objeto representa. O número de corpos de prova decorre do método/plano de ensaio.

## 4. Cardinalidades recomendadas

| Origem | Destino | Cardinalidade recomendada | Regra |
|---|---|---:|---|
| Solicitation | SolicitationItem | 1:N | Uma solicitação possui uma ou mais linhas declaradas. |
| SolicitationItem | ReceiptItem | 1:0..1 antes do recebimento; 1:1 depois de criado | Cada linha declarada aparece uma única vez no recebimento principal. |
| ReceiptItem | CustodyObject | 1:0..N | Zero se não apresentado; um ou vários se apresentado. |
| CustodyObject | CustodyEvent | 1:N | Todo objeto apresentado tem evento inicial e histórico de custódia. |
| CustodyObject | DeviceSample | 1:0..1 | Um objeto pode ainda não ter amostra; após aceite e criação, associa-se a uma única amostra. |
| DeviceSample | LabTest | 1:N | Uma amostra pode receber vários ensaios, preservando o vínculo existente. |
| DeviceSample / plano de ensaio | Corpo de prova | 1:N | Quantidade e seleção determinadas pelo método/plano aplicável. |

### 4.1 Por que não usar N:M entre ObjetoCustodia e AmostraOperacional?

A relação N:M permite que uma amostra reúna objetos diferentes e que um objeto seja distribuído entre várias amostras. Embora flexível, ela cria perguntas adicionais difíceis de responder sem regras específicas:
- Qual objeto originou um resultado reprovado?
- Como devolver apenas parte de um agrupamento?
- Como manter a cadeia de custódia se a amostra for subdividida?
- Como impedir que a mesma unidade física seja usada em duas amostras?
- Como reconciliar quantidade recebida, quantidade ensaiada e quantidade remanescente?

No desenho-base, recomenda-se que a divisão necessária seja representada por vários ObjetosCustodia, cada um vinculado a no máximo uma amostra. A eventual divisão física de um objeto já sob custódia deve ser registrada por operação controlada, com objetos-filhos e evento de fracionamento, se esse cenário for confirmado como necessário.

### 4.2 Quando admitir uma amostra para várias unidades?

Quando as unidades forem tratadas como um conjunto homogêneo pelo procedimento técnico, e a decisão/resultado for emitido para o conjunto ou lote, o conjunto pode ser um único ObjetoCustodia e gerar uma única AmostraOperacional.

Isso não impede que o plano de ensaio registre vários corpos de prova ou unidades selecionadas dentro daquela amostra. A identificação do corpo de prova deve permitir rastrear o resultado até a amostra e, quando necessário, até a unidade selecionada.

## 5. Aplicação a materiais do laboratório

Os cenários abaixo são recomendações ilustrativas. A regra final deve seguir o procedimento técnico, o plano de amostragem, a norma aplicável e a forma como o laboratório emite decisões e resultados.

### 5.1 Agulhas — várias unidades do mesmo lote, avaliação como conjunto

**Cenário:** solicitação declara 10 agulhas do mesmo fabricante, modelo, calibre e lote. As 10 são apresentadas. O laboratório realiza medições em unidades selecionadas conforme plano de ensaio e emite avaliação para o conjunto/lote.

| Nível | Registro recomendado |
|---|---|
| ItemDeclarado | Uma linha: agulhas, quantidade 10. |
| ItemRecebimento | Uma linha, quantidade apresentada 10. |
| ObjetoCustodia | Um objeto agrupado, quantidade 10, lote e critério de homogeneidade registrados. |
| AmostraOperacional | Uma amostra para o conjunto, após aceite. |
| Corpos de prova | Unidades selecionadas para cada ensaio, identificadas conforme o plano. |

**Justificativa:** evita criar dez amostras quando a decisão laboratorial é do conjunto e não há necessidade de rastreabilidade individual de cada agulha.

**Condição:** o procedimento deve permitir que as unidades sejam tratadas como conjunto. Se houver resultados ou decisões individuais por agulha, aplicar o cenário 5.2.

### 5.2 Agulhas — resultados individuais por unidade

**Cenário:** 10 agulhas são recebidas, mas o laboratório precisa identificar individualmente quais unidades foram medidas e associar resultado/reprovação a cada peça.

| Nível | Registro recomendado |
|---|---|
| ItemDeclarado | Uma linha, quantidade 10. |
| ItemRecebimento | Uma linha, quantidade apresentada 10. |
| ObjetoCustodia | Dez objetos individuais, ou agrupamento inicial com individualização formal antes do uso analítico. |
| AmostraOperacional | Uma por objeto que será avaliado e reportado individualmente. |
| Corpos de prova | Conforme o método; não criar automaticamente um corpo de prova adicional por ensaio sem necessidade. |

**Justificativa:** a rastreabilidade individual é necessária para identificar a unidade responsável por um resultado ou decisão específica.

### 5.3 Seringas — unidades com números de série distintos

**Cenário:** três seringas com números de série diferentes, cada uma sujeita a conferência, ensaio ou destinação independente.

| Nível | Registro recomendado |
|---|---|
| ItemDeclarado | Uma linha de seringas, quantidade 3, se declaradas juntas. |
| ItemRecebimento | Uma linha, quantidade apresentada 3. |
| ObjetoCustodia | Três objetos individuais, cada um com seu número de série. |
| AmostraOperacional | Três amostras, uma para cada objeto aceito, se a avaliação for independente. |
| Corpos de prova | Um ou vários por amostra, conforme o método. |

**Justificativa:** o número de série identifica unidades distintas e a independência de avaliação/destino exige rastreabilidade separada.

Se as três unidades forem formalmente avaliadas como conjunto e o relatório não individualizar os resultados, o responsável técnico poderá justificar um objeto agrupado. A existência de números de série, por si só, não obriga a emitir três amostras se a regra de avaliação for coletiva; contudo, a identificação individual deve ser preservada.

### 5.4 Equipo — um dispositivo submetido a vários ensaios

**Cenário:** um equipo é recebido e submetido a diferentes ensaios físicos, eventualmente com vários corpos de prova ou regiões do mesmo dispositivo.

| Nível | Registro recomendado |
|---|---|
| ItemDeclarado | Uma linha, quantidade 1. |
| ItemRecebimento | Uma linha, quantidade apresentada 1. |
| ObjetoCustodia | Um objeto individual. |
| AmostraOperacional | Uma amostra após aceite. |
| Ensaios | Vários LabTest associados à mesma amostra. |
| Corpos de prova | Vários, se o método exigir cortes, segmentos ou regiões específicas. |

**Justificativa:** multiplicar amostras por ensaio fragmentaria artificialmente a identidade do mesmo dispositivo e dificultaria consolidar seus resultados.

Cada corpo de prova deve ser identificado de modo suficiente para associar resultado, método e localização/segmento do dispositivo, conforme aplicável.

### 5.5 Cateter — avaliação por segmentos ou regiões

**Cenário:** um cateter é recebido como uma peça, mas diferentes segmentos são utilizados em ensaios distintos.

**Recomendação:** um ObjetoCustodia e uma AmostraOperacional para o cateter. Os segmentos são corpos de prova ou unidades de ensaio vinculadas ao plano/ensaio, não novas amostras operacionais, salvo se o procedimento exigir avaliação e destinação independente de segmentos como unidades autônomas.

**Justificativa:** preserva a identidade do dispositivo de origem e evita confundir preparação de corpos de prova com recebimento de novas amostras.

### 5.6 Quantidade declarada maior que a apresentada

**Cenário:** solicitação declara 10 unidades; somente 5 são apresentadas na chegada.

| Nível | Registro recomendado |
|---|---|
| ItemDeclarado | Quantidade declarada 10. |
| ItemRecebimento | Quantidade apresentada 5; apresentação parcial registrada. |
| ObjetoCustodia | Representa somente as 5 unidades efetivamente apresentadas, agrupadas ou individualizadas conforme a regra técnica. |
| AmostraOperacional | Somente após aceite dos objetos apresentados. |
| Unidades ausentes | Permanecem registradas como não apresentadas; não geram custódia nem amostra. |

A quantidade não apresentada não pode ser incorporada posteriormente à chegada original. A entrega posterior exige nova solicitação ou exceção institucional formal.

### 5.7 Embalagem coletiva sem identificação individual interna

**Cenário:** é recebida uma embalagem lacrada contendo várias unidades sem identificação individual visível ou necessária na etapa de recebimento.

**Recomendação:** um ObjetoCustodia agrupado, identificado pela embalagem, lote, quantidade declarada/apresentada e condição do lacre. A individualização pode ocorrer posteriormente, se exigida pelo procedimento, com evento de abertura/fracionamento e registro dos objetos-filhos.

**Condição:** não usar o agrupamento para ocultar unidades com identidades, lotes ou condições diferentes. Se a embalagem contiver sublotes ou materiais heterogêneos, separar os objetos.

## 6. Regras de decisão para agrupar ou individualizar

Recomenda-se aplicar a seguinte ordem:

1. **Identidade individual obrigatória:** se houver número de série, código individual ou requisito normativo/procedimental de rastrear cada unidade, criar ObjetosCustodia individuais.
2. **Resultado ou decisão independente:** se o laboratório precisa emitir resultado, aprovação, reprovação ou destinação por unidade, individualizar.
3. **Conjunto homogêneo com avaliação coletiva:** se unidades têm mesma especificação/lote e são avaliadas como conjunto, permitir um ObjetoCustodia agrupado com quantidade explícita.
4. **Vários ensaios no mesmo dispositivo:** manter uma amostra operacional e associar vários ensaios/corpos de prova.
5. **Dúvida sobre a independência:** preferir individualização dos ObjetosCustodia, sem necessariamente criar amostras imediatamente; a criação de amostra ocorre apenas após aceite e conforme a unidade de decisão laboratorial aprovada.

O agrupamento deve registrar pelo menos:
- quantidade representada;
- unidade de medida;
- fabricante/modelo/lote e demais identificadores disponíveis;
- critério de homogeneidade;
- procedimento ou justificativa que autoriza o tratamento conjunto;
- responsável e data/hora do agrupamento;
- possibilidade de individualização posterior e respectivo histórico.

## 7. Regras de custódia recomendadas — DEC04

1. A custódia começa na chegada física do material apresentado, não no aceite e não na criação de DeviceSample.
2. O evento inicial deve preservar arrived_at e received_by_id, correspondentes ao fato físico real.
3. A custódia é vinculada ao ObjetoCustodia; a amostra criada depois herda o vínculo de rastreabilidade, sem reiniciar a cadeia.
4. Material pendente ou recusado permanece sob custódia até devolução ou outra destinação formalmente registrada.
5. Item não apresentado não gera ObjetoCustodia nem evento de custódia.
6. Transferência deve registrar origem, destino, entregador, recebedor, data/hora e confirmação aplicável.
7. Correções não apagam eventos; devem gerar retificação auditável.
8. O registro de custódia deve permitir consultar a história antes e depois da criação da amostra.

### 7.1 Compatibilidade com ChainOfCustody existente

Recomenda-se não criar um segundo histórico independente.

A alternativa preferencial a detalhar tecnicamente é estender a estrutura de custódia existente para suportar o objeto pré-amostra, mantendo compatibilidade de leitura com os eventos ligados diretamente a DeviceSample. A decisão física depende de inspeção das FKs, consultas, triggers, relatórios e testes atuais.

Se não for seguro estender a tabela, a solução deverá fornecer uma única visão cronológica e auditável dos eventos antigos e novos. Não duplicar o evento de chegada quando DeviceSample for criado.

## 8. Implicações no modelo relacional

A recomendação de cardinalidade para o desenho-base é:

- SolicitationItem 1:0..1 ReceiptItem (um ReceiptItem obrigatório para cada linha declarada quando o recebimento é criado);
- ReceiptItem 1:0..N CustodyObject;
- CustodyObject 1:0..N CustodyEvent;
- CustodyObject 1:0..1 DeviceSample;
- DeviceSample 1:N LabTest;
- DeviceSample/plano de ensaio 1:N corpos de prova.

Recomenda-se retirar do DER-base a associação N:M entre DeviceSample e CustodyObject e substituí-la por FK única/nullable ou tabela associativa com UNIQUE em custody_object_id, caso a compatibilidade física exija tabela intermediária. A decisão deve preservar a possibilidade de amostras legadas sem vínculo.

Se for necessário fracionar um ObjetoCustodia:
- não alterar silenciosamente a quantidade ou identidade original;
- registrar evento de fracionamento;
- criar objetos-filhos com quantidade reconciliada;
- manter referência ao objeto de origem;
- impedir que a soma das quantidades-filhas exceda a quantidade disponível;
- definir se o objeto-pai permanece como registro histórico não movimentável após fracionamento.

Não criar tabela UnidadeFisica na primeira entrega sem evidência de que o rastreamento individual de unidades dentro de agrupamentos é requisito recorrente. Caso seja necessário, introduzi-la em evolução aditiva.

## 9. Decisões recomendadas para atualização da matriz

| Decisão | Recomendação proposta | O que ainda requer validação |
|---|---|---|
| DEC04 | Custódia vinculada ao ObjetoCustodia desde a chegada; continuidade ao criar amostra; não duplicar ChainOfCustody. | Forma física de compatibilização com tabela atual; eventos para recusa/devolução. |
| DEC05-A | Um ReceiptItem por ItemDeclarado no recebimento. | Confirmar se há exceção operacional de divisão de uma linha em entregas/subconjuntos no mesmo recebimento. |
| DEC05-B | ReceiptItem pode originar zero ou vários ObjetosCustodia. | Regras de agrupamento, fracionamento e reconciliação quantitativa. |
| DEC05-C | Um ObjetoCustodia gera no máximo uma DeviceSample; no fluxo ordinário aceito e ensaiado, exatamente uma. | Confirmar se há caso real em que uma amostra precise representar objetos recebidos distintos. |
| DEC05-D | Uma DeviceSample comporta vários ensaios e corpos de prova. | Confirmar se existe corpo de prova que precise ser rastreado como entidade independente já na primeira entrega. |
| DEC05-E | Não criar UnidadeFisica como tabela obrigatória na primeira entrega. | Confirmar exigência de rastreio individual para categorias específicas. |

## 10. Casos que precisam ser conferidos pelo responsável técnico

Antes de aprovar DEC04/DEC05, recomenda-se verificar ao menos um caso real anonimizado de cada situação abaixo:

| Caso | Pergunta objetiva |
|---|---|
| Agulhas de mesmo lote avaliadas em conjunto | O laudo/decisão é do conjunto ou cada agulha recebe resultado próprio? |
| Agulhas com resultado individual | É necessário localizar fisicamente a unidade reprovada depois do ensaio? |
| Seringas serializadas | Cada número de série pode ter decisão/destino independente? |
| Equipo com vários ensaios | Os resultados são consolidados em uma amostra ou o laboratório atualmente abre registros independentes? |
| Cateter cortado em segmentos | Os segmentos são corpos de prova do mesmo dispositivo ou materiais independentes para fins de rastreabilidade? |
| Embalagem coletiva | O laboratório precisa rastrear cada unidade interna antes de abrir a embalagem? |
| Material recusado | Onde permanece guardado, quem responde pela guarda e como se comprova a devolução? |

Não é necessário incluir dados pessoais ou informações sigilosas. Os exemplos podem ser descritos com códigos fictícios, mantendo apenas a estrutura operacional necessária.

## 11. Critérios para considerar DEC04/DEC05 suficientemente definidas

As decisões poderão ser encaminhadas para aprovação quando:

- cada exemplo tiver sido classificado como unidade individual ou agrupamento;
- estiver claro se a decisão/resultado é individual ou coletiva;
- a relação ObjetoCustodia–DeviceSample estiver confirmada;
- estiver definido se e como ocorre fracionamento após a chegada;
- custódia de material recusado e devolução estiverem descritas;
- a continuidade com ChainOfCustody estiver tecnicamente demonstrada;
- o responsável técnico confirmar a compatibilidade com os procedimentos de ensaio e emissão de laudos;
- o responsável funcional e a autoridade competente registrarem a aprovação.

## 12. Próxima ação

Submeter esta recomendação ao responsável técnico do laboratório para validação dos cenários de agulhas, seringas, equipos e cateteres. Após essa revisão, atualizar DEC04/DEC05 na matriz de decisões e ajustar o modelo relacional. Até lá, manter a versão 0.1 como proposta, sem iniciar migrações ou implementação.

## 13. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-09 | Primeira recomendação de cardinalidades e regras de agrupamento, custódia e criação de amostra, com cenários de dispositivos médicos. |
