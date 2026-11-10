# Proposta de fechamento GOV-P10 — Exceções administrativas e acesso emergencial

**Identificador:** PROP-LIMS-GOV-EXC-001  
**Versão:** 0.1  
**Data:** 2026-11-10  
**Branch:** `main`  
**Estado:** proposta para revisão do responsável pelo projeto; recomendações ainda não validadas; definição institucional e fechamento técnico pendentes; implementação bloqueada.

## 1. Objetivo e limites

Esta proposta detalha GOV-P10 do Pacote 1, tratando de exceções administrativas, operacionais e de acesso emergencial. Busca permitir continuidade controlada em situações justificadas sem transformar exceções em permissões permanentes, dispensas de requisitos ou mecanismos para contornar segregação, assinatura, auditoria e controles de integridade.

A proposta é documental. Não define quais autoridades ou cargos reais podem aprovar exceções, não estabelece prazos institucionais, não declara que exista mecanismo técnico de exceção implantado e não autoriza alteração de código, banco, infraestrutura ou configuração.

## 2. Princípios de controle

1. **Regra ordinária primeiro:** a operação deve seguir o fluxo, as competências e os controles regulares sempre que disponíveis.
2. **Exceção explícita:** não inferir autorização por urgência, hierarquia informal, indisponibilidade ou conveniência.
3. **Autoridade independente:** a exceção deve ser aprovada por autoridade formalmente competente, distinta do beneficiário quando exigido pela política de segregação.
4. **Menor privilégio:** limitar capacidade, recurso, escopo, unidade, finalidade e período ao estritamente necessário.
5. **Não dispensar impedimentos absolutos:** exceção não afasta requisito legal/normativo, critério técnico impeditivo, segurança do paciente/usuário, integridade de evidência ou obrigação de assinatura.
6. **Rastreabilidade append-only:** registrar solicitação, aprovação, execução, revisão, encerramento e eventual incidente, sem apagar ou reescrever fatos anteriores.
7. **Temporalidade:** toda exceção deve ter instante de início e expiração ou condição objetiva de encerramento.
8. **Revisão posterior:** uso emergencial deve ser revisado por pessoa independente, conforme prazo formal a definir.
9. **Revogabilidade:** mudança de contexto, risco, escopo ou necessidade encerra ou restringe a exceção.
10. **Sem privilégio permanente:** não converter exceção em concessão ordinária; necessidades recorrentes devem seguir processo regular de concessão de competência (GOV-P02/P03).

## 3. Categorias de exceção propostas

| Categoria | Exemplos de situação | Limite principal |
|---|---|---|
| Continuidade operacional | Indisponibilidade temporária de usuário/serviço responsável, com atividade que não pode aguardar | Não dispensar requisitos técnicos ou legais; documentar substituição e revisão |
| Acesso emergencial (break-glass) | Acesso excepcional a recurso ou informação para tratar incidente ou risco imediato | Escopo mínimo, prazo curto, alerta e revisão independente |
| Segregação excepcional | Impossibilidade temporária de separar executor e outro papel em situação excepcional | Somente quando a independência não for requisito absoluto; controles compensatórios e revisão posterior |
| Retificação/lançamento tardio | Registro posterior de fato ocorrido anteriormente, com justificativa | Preservar occurred_at e recorded_at distintos; nunca retroagir registro ou alterar cronologia |
| Contingência de auditoria/assinatura | Indisponibilidade de serviço crítico de auditoria, chave ou assinatura | Por padrão, bloquear atos críticos; qualquer contingência depende de procedimento institucional formal e reconciliação verificável |
| Acesso excepcional a auditoria | Consulta/exportação de detalhe sensível fora do fluxo ordinário | Finalidade, escopo, minimização, justificativa e registro de acesso |

A classificação definitiva, hipóteses admissíveis e atos proibidos dependem da instituição.

## 4. Registro mínimo da exceção

Cada exceção deve possuir registro identificável, contendo, conforme aplicabilidade:

- identificador único e categoria;
- solicitante/beneficiário e identidade autenticada;
- recurso, operação, capacidade, escopo e finalidade;
- situação concreta, justificativa e risco que motivou o pedido;
- controles ordinários indisponíveis ou impedimento que motivou a exceção;
- autoridade autorizadora, fundamento da competência e evidência da aprovação;
- instante da solicitação, decisão, início efetivo e registro;
- expiração ou condição objetiva de encerramento;
- controles compensatórios e restrições;
- executor técnico/operacional, quando diferente do beneficiário;
- referência à assinatura eletrônica exigida e ao snapshot aprovado;
- eventos executados sob a exceção, resultados e correlação com a exceção;
- responsável e prazo da revisão posterior;
- resultado da revisão, incidentes, providências e encerramento.

O cliente não deve poder declarar livremente que possui autorização. A identidade do solicitante/ator deve derivar da sessão autenticada; autoridade e competência precisam ser verificadas no backend.

## 5. Fluxo proposto

1. **Solicitação:** registrar situação, finalidade, beneficiário, operação/recurso, escopo e período pretendido.
2. **Classificação:** identificar categoria, urgência, riscos, requisitos legais/normativos e controles que seriam afetados.
3. **Elegibilidade:** verificar se a exceção é admissível; rejeitar se exigir dispensa de requisito impeditivo ou se não houver autoridade competente.
4. **Autorização:** autoridade institucional aprova ou rejeita com justificativa, escopo, controles e expiração; assinatura formal conforme matriz GOV-P05/P06.
5. **Ativação:** sistema ou administrador autorizado aplica exatamente o escopo aprovado, vinculado à decisão original; não ampliar prazo ou capacidade.
6. **Execução:** cada operação verifica novamente a exceção, validade, escopo, contexto, competência e impedimentos.
7. **Monitoramento:** gerar evento auditável de ativação, uso, negação, alteração, revogação e encerramento.
8. **Encerramento:** expirar automaticamente ou encerrar por condição objetiva; revogar efeitos e acessos temporários.
9. **Revisão independente:** examinar necessidade, uso real, aderência ao escopo, evidências, segregação e efeitos; registrar conclusão e ações corretivas.

A aprovação da exceção não significa aprovação antecipada de qualquer operação futura: cada comando deve continuar sujeito à autorização contextual e aos controles aplicáveis.

## 6. Regras de acesso emergencial (break-glass)

- O acesso emergencial deve ser excepcional, não uma alternativa conveniente ao fluxo de concessão ordinário.
- Deve exigir justificativa concreta, beneficiário, finalidade, recurso, escopo mínimo, duração e autoridade ou procedimento emergencial formalmente designado.
- Quando a urgência impedir aprovação prévia, só poderá existir fluxo de ativação unilateral se a instituição o aprovar expressamente, definir hipóteses objetivas, controles compensatórios, alerta imediato e revisão independente posterior.
- Não presumir que a indisponibilidade de uma autoridade autorize automaticamente o administrador técnico a conceder a si próprio competência funcional.
- O acesso deve ser encerrado automaticamente ao expirar o prazo ou cessar a condição de emergência.
- Acesso emergencial não concede automaticamente leitura irrestrita de auditoria, administração de chaves, alteração de registros históricos ou capacidade de apagar evidências.
- Toda consulta, exportação e mutação executada sob break-glass deve ser correlacionável à exceção.
- Revisão posterior deve verificar também tentativas negadas e se o escopo concedido foi maior que o necessário.

## 7. Segregação e controles compensatórios

1. Executor não valida a própria regularização quando a validação independente for obrigatória; exceção não pode afastar essa regra sem fundamento institucional/legal que permita expressamente o procedimento alternativo.
2. Beneficiário não aprova a própria exceção quando houver exigência de independência.
3. Administrador técnico apenas executa a autorização formal; não cria competência funcional por conta própria.
4. Quando acumulação excepcional de papéis for admissível, registrar a incompatibilidade temporariamente mitigada, motivo, duração e revisão independente.
5. Controles compensatórios possíveis: dupla conferência posterior, assinatura reforçada, restrição de escopo, bloqueio de exportação, monitoramento em tempo real e revisão independente.
6. Controles compensatórios não substituem requisito legal ou técnico impeditivo.

## 8. Contingência de auditoria, assinatura ou infraestrutura

- A indisponibilidade de AuditLog, serviço de assinatura ou material criptográfico não deve produzir sucesso silencioso.
- Regra padrão recomendada: bloquear operações críticas cuja auditoria/assinatura obrigatória não possa ser concluída atomicamente.
- Procedimento excepcional de contingência só pode ser usado se previamente aprovado pela instituição, com atos elegíveis explicitamente enumerados, autoridade, formulário/registro controlado, sequência inviolável, evidências, prazo e reconciliação posterior.
- Não presumir modo offline, armazenamento local confiável ou sincronização posterior como mecanismo disponível.
- A reconciliação deve preservar os instantes efetivos e de registro, identificar lançamento tardio, impedir duplicidade e registrar a indisponibilidade e a cadeia de aprovação.
- Se não houver mecanismo institucional e técnico aprovado, manter o bloqueio e acionar procedimento operacional externo formal.

## 9. Relação com outras decisões

- **GOV-P01/P04:** aplicar autorização por capacidade + escopo + contexto e independência obrigatória quando exigida.
- **GOV-P02/P03:** autoridade de concessão, revisão, suspensão e revogação ainda depende de definição institucional; exceção não substitui concessão ordinária.
- **GOV-P05/P06:** assinatura formal da autorização de exceção e verificação de competência no momento da aprovação e do uso, conforme matriz institucional.
- **GOV-P07:** preservar participantes semanticamente distintos e occurred_at/recorded_at/signed_at.
- **GOV-P08:** registrar solicitação, decisão, ativação, uso, negação, revisão e encerramento na cadeia de auditoria existente.
- **GOV-P09:** indisponibilidade de chave/append/validação deve seguir contingência formal; não enfraquecer imutabilidade.
- **GOV-P11:** acesso emergencial a auditoria deve respeitar finalidade, escopo, minimização, rastreabilidade e revisão.
- **API06/API07:** comandos excepcionais continuam sujeitos a concorrência e idempotência; replay não amplia autorização nem revela resultado sem autorização atual.
- **API10:** preservar segregação das operações de recebimento, decisão, custódia e administração de competências.

## 10. Decisões propostas para manifestação

| ID | Recomendação | Limite que exige definição institucional |
|---|---|---|
| EXC-P10-01 | Adotar registro único e identificável para cada exceção, com solicitante, beneficiário, autoridade, escopo, finalidade, justificativa, período e evidências. | Campos obrigatórios por categoria e autoridade competente. |
| EXC-P10-02 | Exigir autorização formal prévia como regra; exceção emergencial sem aprovação prévia somente por procedimento institucional expresso. | Hipóteses, autoridade substituta, canal e condições de aprovação posterior. |
| EXC-P10-03 | Delimitar capacidade, recurso, unidade/escopo, finalidade e duração; vedar concessão genérica ou permanente. | Catálogo de escopos e prazos máximos por categoria. |
| EXC-P10-04 | Impedir que exceção dispense requisito legal/normativo ou critério técnico impeditivo. | Identificação institucional dos requisitos absolutos e atos não excepcionáveis. |
| EXC-P10-05 | Exigir controles compensatórios e revisão independente posterior quando houver urgência ou acumulação excepcional de papéis. | Responsável, prazo, evidência e critérios de conclusão da revisão. |
| EXC-P10-06 | Encerrar automaticamente a exceção por expiração ou condição objetiva; revogar efeitos e registrar encerramento. | Prazos, eventos de encerramento e tratamento de falha de revogação. |
| EXC-P10-07 | Auditar solicitação, aprovação, execução, uso, negação, revisão, incidente e encerramento, correlacionando cada ato à exceção. | Retenção, acesso, alertas e classificação dos eventos. |
| EXC-P10-08 | Na indisponibilidade de auditoria/assinatura, bloquear atos críticos por padrão; contingência somente mediante procedimento formal aprovado e reconciliação. | Atos elegíveis, autoridade, registro alternativo e critérios de reconciliação. |
| EXC-P10-09 | Tratar break-glass como capacidade temporária separada, sem acesso irrestrito automático a auditoria, chaves ou administração. | Autoridades, gatilhos, monitoramento e revisão posterior. |
| EXC-P10-10 | Não permitir autoaprovação de exceção pelo beneficiário nem autoatribuição de competência pelo administrador técnico. | Definir exceções institucionais admissíveis sem violar requisitos de independência. |

## 11. Critérios de fechamento

GOV-P10 somente poderá ser considerado fechado quando:

1. categorias e hipóteses admissíveis/proibidas estiverem aprovadas institucionalmente;
2. autoridades, delegações, substituições e procedimento emergencial estiverem formalizados;
3. campos, estados, prazos, expiração e encerramento estiverem definidos;
4. segregação e controles compensatórios estiverem aprovados;
5. matriz de assinatura e política de auditoria estiverem alinhadas;
6. contingência e reconciliação estiverem formalizadas e tecnicamente demonstradas;
7. revisão independente e retenção estiverem definidas;
8. revisão técnica, aprovação institucional e autorização específica de implementação estiverem registradas.

## 12. Controle de execução

**Realizado:** elaboração documental da proposta GOV-P10, alinhada às diretrizes GOV01–GOV05, às recomendações GOV-P07/P08 validadas em revisão e à proposta GOV-P09/P11.

**Não realizado:** alteração de código, modelos, banco, migrações, serviços, rotas, frontend, OpenAPI, secrets, triggers, grants, infraestrutura, testes, build, CI ou configuração de produção. Não houve acesso a banco ou ambiente operacional.

**Estado:** EXC-P10-01 a EXC-P10-10 ainda não validadas. GOV-P10 permanece aberta; definições institucionais, fechamento técnico e autorização de implementação pendentes.

## 13. Histórico

| Versão | Data | Alteração |
|---|---|---|
| 0.1 | 2026-11-10 | Criação da proposta para revisão de exceções administrativas, acesso emergencial, controles compensatórios e contingência. |
