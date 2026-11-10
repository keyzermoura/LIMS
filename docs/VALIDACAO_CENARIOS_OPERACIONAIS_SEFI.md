# Simulação de Mesa — Cenários Operacionais do Recebimento SEFI no LIMS

**Identificador:** SIM-SEFI-REC-001  
**Versão:** 1.2
**Data:** 2026-11-10  
**Base:** EST-REC-001 v1.5; MOD-DOM-001 v0.5; CA01–CA37; revisão REV-MD-LIMS-002 v1.0.  
**Situação:** decisões D01–D20 ratificadas institucionalmente; SIM01–SIM12 permanecem simulação documental, sem validação operacional com usuários do SEFI nem teste de software. Não autoriza implementação.

---

## 1. Objetivo e premissas

Percorrer os cenários operacionais recomendados após a revisão multidisciplinar, verificando estados, atores, pré-condições, eventos e critérios de aceitação.

Premissas comuns:
- Solicitação submetida com um ou mais ItemDeclarado.
- Cada ItemDeclarado possui seu ItemRecebimento.
- Material fisicamente apresentado gera um ou mais ObjetosCustodia conforme granularidade justificada.
- Custódia inicia na chegada física, antes do aceite.
- AmostraOperacional só pode ser criada após aceite final e validações obrigatórias.
- O estado agregado não substitui o histórico individual.
- Todos os tempos do fato e do registro são distintos quando aplicável.
- Os nomes dos estados são os definidos em EST-REC-001 v1.5.

## 2. Cenários simulados

### SIM01 — Recebimento integral com aceite

**Situação:** solicitação com dois itens; ambos apresentados integralmente e sem divergências.

**Fluxo:**
1. SOLICITANTE submete Solicitação; ItemDeclarado 1 e 2 ficam vinculados.
2. RECEPÇÃO registra chegada física; Recebimento passa a REGISTRADO.
3. Cada ItemRecebimento passa de AGUARDANDO_CHEGADA para APRESENTADO.
4. Para cada material apresentado, é criado ObjetoCustodia em SOB_GUARDA, com quantidade/unidade representada, custodiante e localização.
5. CONFERENTE inicia conferência com checklist versionado; respostas ficam EM_ANDAMENTO.
6. Critérios obrigatórios são respondidos e conferência passa a CONCLUIDA.
7. Decisões ACEITA são formalizadas com assinatura exigida.
8. Se houver validação independente obrigatória, permanece bloqueado até sua conclusão.
9. AmostraOperacional é criada de forma atômica/idempotente para cada ObjetoCustodia elegível.

**Resultado esperado:** Recebimento pode ser CONCLUIDO quando todos os itens/objetos tiverem desfecho permitido e não houver pendência, validação ou custódia sem destino. Amostras vinculadas sem duplicidade.

**Critérios:** CA01–CA05, CA14, CA16–CA18, CA24, CA31–CA33, CA37.

**Veredito documental:** coerente, condicionado à definição dos checklists concretos, competência e assinatura.

### SIM02 — Recebimento parcial com item não apresentado

**Situação:** solicitação com três itens; dois chegam e o terceiro não é apresentado.

**Fluxo:**
1. RECEPÇÃO registra chegada e os tempos reais.
2. Itens 1 e 2 passam a APRESENTADO; item 3 passa a NAO_APRESENTADO.
3. Apenas itens apresentados originam ObjetoCustodia e eventos RECEIPT.
4. Itens 1 e 2 seguem conferência e recebem decisões formais.
5. Item 3 permanece sem objeto, custódia, decisão técnica ou amostra.
6. Recebimento pode ser CONCLUIDO administrativamente se não houver pendências/validações abertas nem objeto sob custódia sem destino.

**Resultado esperado:** conclusão administrativa permitida, mantendo item 3 visível como NAO_APRESENTADO; não há aceite presumido.

**Critérios:** CA07, CA08, CA23, CA28, CA36.

**Veredito documental:** coerente. A data/hora da ausência deve corresponder ao registro real da chegada, não a horário inferido.

### SIM03 — Divergência entre quantidade declarada e apresentada

**Situação:** solicitação declara 10 unidades; recepção observa 8 unidades.

**Fluxo:**
1. ItemDeclarado preserva quantidade declarada = 10.
2. Recebimento registra quantidade apresentada = 8, unidade observada e evidência aplicável.
3. A diferença de 2 é registrada como divergência, sem corrigir a declaração original.
4. A regra/checklist aplicável determina se a divergência é E, S ou I.
5. Se saneável, abre-se Pendência; se impeditiva, aceite fica bloqueado; a coordenação não pode dispensar critério E.

**Resultado esperado:** declaração e observação permanecem auditáveis; nenhum objeto/amostra é criado para quantidade não apresentada.

**Critérios:** CA04–CA08, CA26–CA27.

**Veredito documental:** parcialmente dependente. A regra de domínio está definida, mas os checklists concretos e a política de fracionamento/agrupamento precisam determinar a consequência técnica para cada categoria.

### SIM04 — Um item com dois objetos, um aceito e outro recusado

**Situação:** item declarado é apresentado em dois conjuntos rastreáveis; um atende aos requisitos e outro não.

**Fluxo:**
1. ItemRecebimento fica APRESENTADO.
2. São criados dois ObjetosCustodia com quantidades representadas e justificativa de separação.
3. Cada objeto é conferido e decidido independentemente.
4. Objeto A recebe ACEITA e pode gerar AmostraOperacional após todas as validações.
5. Objeto B recebe RECUSADA após validação da coordenação e assinatura.
6. Objeto B permanece SOB_GUARDA até RETURN ou DISPOSITION efetivo e CLOSURE.
7. ItemRecebimento apresenta estado agregado PARCIALMENTE_DECIDIDO; não aparece como integralmente aceito.

**Resultado esperado:** decisão de um objeto não contamina o outro; a recusa não encerra custódia.

**Critérios:** CA09, CA14, CA18, CA20, CA27, CA37.

**Veredito documental:** coerente. A granularidade dos objetos depende de justificativa técnica e não pode ser usada para fracionar artificialmente decisão sem rastreabilidade.

### SIM05 — Pendência saneável com comunicação, vencimento, prorrogação e reavaliação

**Situação:** critério S não conforme, solicitante precisa complementar documentação.

**Fluxo:**
1. CONFERENTE registra não conformidade saneável e abre Pendência.
2. Sistema registra responsável, providência, prazo e comunicação formal comprovável.
3. A contagem começa na comunicação formal, não na simples abertura.
4. Prazo vence sem resposta; sistema registra PRAZO_VENCIDO e escalonamento, mantendo pendência aberta.
5. Coordenação autoriza prorrogação justificada; prazo original e novo prazo ficam no histórico.
6. Solicitante apresenta evidência; pendência passa a AGUARDANDO_REAVALIACAO.
7. CONFERENTE reavalia; somente avaliação favorável leva a REGULARIZADA.
8. Decisão de aceite pode prosseguir se não houver outro bloqueio.

**Resultado esperado:** vencimento não gera recusa; evidência não encerra pendência sem reavaliação; custódia permanece.

**Critérios:** CA05, CA12, CA13, CA14, CA26.

**Veredito documental:** coerente. Prazos, canais e autoridades precisam de formalização institucional.

### SIM06 — Recusa com permanência em custódia e posterior devolução

**Situação:** objeto não atende a critério impeditivo e é recusado.

**Fluxo:**
1. CONFERENTE documenta critério E não conforme e evidências.
2. Coordenação independente valida a recusa, quando exigida.
3. Decisão RECUSADA é assinada formalmente.
4. Objeto permanece sob custodiante/localização vigentes.
5. Quando o representante autorizado comparece, a entrega é registrada como RETURN, com identidade e comprovante aplicável.
6. CLOSURE é formalizado após confirmação da entrega.

**Resultado esperado:** RECUSADA não equivale a ENCERRADA; custódia termina somente após devolução efetiva e documentada.

**Critérios:** CA04, CA09, CA14, CA15.

**Veredito documental:** coerente. Procedimentos de identificação do representante, comprovante e destinação precisam ser aprovados pela instituição.

### SIM07 — Transferência entre responsáveis

**Situação:** material será transferido do servidor A para o servidor B.

**Fluxo:**
1. Custodiante A solicita transferência; evento TRANSFER ainda não é confirmado.
2. Objeto fica TRANSFERENCIA_PENDENTE; A continua responsável.
3. B recebe fisicamente, confirma identidade, horário e localização.
4. Evento TRANSFER confirmado atualiza custodiante e localização projetados.
5. Histórico mantém responsável e localização anteriores.

**Resultado esperado:** transferência só se efetiva com confirmação do recebedor; sem confirmação, responsabilidade permanece com A.

**Critérios:** CA10, CA11, CA29, CA30.

**Veredito documental:** coerente. A instituição deve definir se a confirmação exige assinatura formal ou autenticação operacional com evidência, conforme a política de custódia.

### SIM08 — Mudança de localização sem troca de custodiante

**Situação:** servidor A desloca material do armário para outra sala, permanecendo responsável.

**Fluxo:**
1. A registra LOCATION_CHANGE com localização anterior/nova, motivo e tempo do fato.
2. Custodiante continua A.
3. A projeção atualiza somente a localização.
4. Histórico mantém a sequência de localizações.

**Resultado esperado:** não criar evento TRANSFER nem alterar responsável.

**Critérios:** CA29, CA34.

**Veredito documental:** coerente; o inventário de locais e regras de autorização para movimentação dependem de configuração institucional.

### SIM09 — Retificação após criação de amostra e início de ensaio

**Situação:** decisão de aceite foi formalizada, amostra criada e ensaio iniciado; posteriormente se identifica erro relevante no registro original.

**Fluxo:**
1. Solicitante da retificação registra motivo e evidências.
2. Coordenação avalia e autoriza previamente a retificação.
3. Antes de ação operacional, é feita avaliação de impacto sobre amostra, localização, ensaios e laudos.
4. Novo ato retificador referencia a decisão original, preservando-a.
5. Assinatura formal é vinculada ao conteúdo novo.
6. Providências sobre amostra/ensaio seguem procedimento próprio; nada é apagado automaticamente.

**Resultado esperado:** original preservado; retificação auditável; impacto avaliado antes de efeitos; ensaio/laudo não são excluídos automaticamente.

**Critérios:** CA19, CA20, CA22.

**Veredito documental:** coerente no princípio, mas bloqueado por falta de procedimento institucional detalhado para bloquear/revisar ensaios e laudos em andamento.

### SIM10 — Reenvio concorrente e alteração com versão obsoleta

**Situação:** dois usuários ou reenvios de rede tentam criar o mesmo recebimento/amostra; outro usuário altera o mesmo agregado.

**Fluxo:**
1. Duas requisições com mesma chave idempotente e mesmo conteúdo chegam simultaneamente.
2. Apenas uma execução produz o efeito; a segunda recebe estado de processamento ou resultado original, conforme contrato.
3. Reenvio posterior com mesma chave/conteúdo retorna o resultado original.
4. Reutilização da chave com conteúdo diferente é rejeitada.
5. Duas alterações com mesmo expected_version: uma confirma; a outra recebe VERSION_CONFLICT, sem sobrescrita.

**Resultado esperado:** nenhum recebimento/amostra duplicado; nenhuma atualização concorrente perdida.

**Critérios:** CA16, CA17, CA31, CA32, CA33.

**Veredito documental:** requisito definido, mas ainda sem contrato técnico completo de armazenamento/expiração, códigos HTTP e recuperação. Não é possível declarar comportamento implementado sem testes.

### SIM11 — Solicitante tenta acessar solicitação/evidência de terceiro

**Situação:** usuário externo autenticado tenta consultar identificador de solicitação de outro solicitante.

**Fluxo:**
1. Solicitação de leitura/listagem/download chega à API.
2. Servidor valida identidade, vínculo e escopo do recurso.
3. Sem vínculo autorizado, acesso é negado sem revelar conteúdo ou existência indevida.
4. Tentativa é registrada conforme política de segurança.

**Resultado esperado:** isolamento no servidor em todas as rotas e anexos; não depender de filtro visual no frontend.

**Critérios:** CA01, CA25, CA35.

**Veredito documental:** requisito definido. A habilitação de contas externas, prova de identidade, recuperação de acesso e vínculo de representantes continuam pendentes de arquitetura/governança.

### SIM12 — Material chega após conclusão como não apresentado

**Situação:** recebimento foi concluído com item NAO_APRESENTADO; o material chega em data posterior.

**Fluxo:**
1. Recebimento original permanece CONCLUIDO; item continua NAO_APRESENTADO.
2. Não se altera retroativamente o evento de chegada nem o estado original.
3. Instituição abre nova solicitação ou autoriza exceção formal.
4. Nova chegada gera novo evento RECEIPT com received_at = occurred_at e recorded_at real.
5. Novo ObjetoCustodia passa a SOB_GUARDA; o vínculo com a solicitação original só ocorre se houver fundamento formal e rastreável.

**Resultado esperado:** sem retroatividade; novo fato e novo vínculo formal; histórico original preservado.

**Critérios:** CA07, CA23, CA28, CA36.

**Veredito documental:** coerente. O procedimento de exceção e a numeração de protocolo precisam de decisão institucional.

## 3. Resultado consolidado da simulação

| Resultado | Cenários |
|---|---|
| Coerente documentalmente, pendente de formalização institucional | SIM01, SIM02, SIM05, SIM06, SIM07, SIM08, SIM12 |
| Coerente com dependência de regra/checklist por categoria | SIM03, SIM04 |
| Coerente no princípio, exige procedimento institucional adicional | SIM09 |
| Especificação técnica incompleta e depende de testes reais | SIM10, SIM11 |

Nenhum cenário demonstrou contradição que exija reabrir EST01–EST10 ou alterar as cardinalidades M0.2. Foram identificadas dependências institucionais e técnicas que precisam ser resolvidas antes do Gate G0.

## 4. Lacunas que devem permanecer visíveis

1. Regras por categoria para quantidade divergente, agrupamento e fracionamento.
2. Procedimento de devolução, representante autorizado e destinação alternativa.
3. Regra de assinatura/autenticação para confirmação de transferência.
4. Procedimento de impacto sobre ensaios/laudos após retificação.
5. Contratos de idempotência, expected_version, persistência e expiração.
6. Identidade externa, vínculo de solicitante e isolamento de anexos.
7. Numeração do protocolo SEFI, accession e conteúdo do QR.
8. Inventário de localizações, política de retenção e evidências.
9. Procedimento de reconciliação dos dados legados.

## 5. Próxima ação recomendada

Realizar validação de mesa com representantes da recepção, conferência, coordenação e qualidade do SEFI, percorrendo SIM01–SIM12. Para cada cenário, registrar: concordância, divergência, regra institucional aplicável, evidência esperada, responsável pela decisão e eventual ajuste documental.

**Este documento não é homologação operacional, teste automatizado nem aprovação do Gate G0. Nenhum código, banco, API, frontend ou infraestrutura foi alterado.**

## 6. Histórico

| Versão | Data | Descrição |
|---|---|---|
| 1.0 | 2026-11-10 | Simulação documental de mesa dos 12 cenários operacionais mínimos do fluxo SEFI. |


## 7. Adendo — decisões pré-validadas D01–D20 e cenários

A matriz completa está em `docs/DECISOES_PREVALIDACAO_SEFI_D01_D20.md`. A validação operacional com o SEFI deverá relacionar cada decisão aos cenários existentes e acrescentar verificações específicas:

- D01–D04: SIM01–SIM04 — autoria da chegada, metadados, quantidades e múltiplos objetos.
- D05–D06: SIM05–SIM06 — ciclo de pendências, recusa, comunicação e custódia até destinação.
- D07–D08: SIM07–SIM08 — transferência confirmada e mudança de localização sem troca de custodiante.
- D09–D10: SIM09 e SIM01/SIM04/SIM06 — retificação com impacto e independência de validação.
- D11–D12: SIM01–SIM06 — checklist correto, versão congelada e governança de publicação.
- D13–D16: SIM09–SIM11 — evidências, trilha, autorização, assinatura e segregação de acesso.
- D17: cenários de falha/recuperação ainda precisam ser acrescentados à validação técnica.
- D18: SIM01/SIM10/SIM12 — unicidade e vínculo entre protocolo, recebimento, objetos e amostras.
- D19: SIM12 — chegada posterior sem retroatividade.
- D20: SIM01–SIM06 e SIM09 — bloqueio de admissão até cumprimento das pré-condições.

Os SIM01–SIM12 permanecem simulação documental, não teste automatizado nem homologação. Acrescentar cenários de restauração de backup, integridade de anexos/hash, autorização e assinatura, acesso indevido a anexos e conflitos de concorrência na etapa de QA.

**Situação:** decisões D01–D20 ratificadas institucionalmente pelo responsável designado; SIM01–SIM12 permanecem simulação documental, com validação operacional por usuários/representantes do SEFI pendente; Gate G0 não aprovado; implementação não autorizada.

### Histórico de versões

| 1.1 | 2026-11-10 | Adendo de rastreabilidade dos cenários às decisões D01–D20 pré-validadas. |
| 1.2 | 2026-11-10 | Atualização após ratificação institucional integral de D01–D20; permanece pendente a validação operacional de SIM01–SIM12. |
