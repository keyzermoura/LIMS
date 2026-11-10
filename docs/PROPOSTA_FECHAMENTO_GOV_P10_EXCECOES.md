# Proposta de fechamento GOV-P10 — Exceções administrativas e acesso emergencial

**Identificador:** PROP-LIMS-GOV-EXC-001  
**Versão:** 0.1  
**Data:** 2026-11-10  
**Branch:** main  
**Estado:** recomendações GOV10-01 a GOV10-11 validadas em revisão pelo responsável pelo projeto em 2026-11-10; definições institucionais e fechamento técnico pendentes; implementação bloqueada.

## 1. Objetivo e limites

Detalhar as regras gerais de exceções administrativas e acesso emergencial previstas no Pacote 1 de Governança, autorização e responsabilidade. Esta proposta complementa GOV01–GOV05, PROP-LIMS-GOV-002, PROP-LIMS-GOV-AUD-001 e PROP-LIMS-GOV-SEC-001.

A validação registrada neste documento é uma diretriz de desenho no âmbito da revisão do projeto. Não constitui aprovação institucional, não designa autoridades ou cargos, não cria competências funcionais e não autoriza implementação.

## 2. Diretrizes validadas em revisão

Em 2026-11-10, o responsável pelo projeto validou em revisão as seguintes recomendações:

| ID | Diretriz | Regra de desenho validada |
|---|---|---|
| GOV10-01 | Autorização formal | Toda exceção deve ser autorizada por autoridade institucional competente, formalmente designada para a hipótese e o escopo aplicáveis. |
| GOV10-02 | Justificativa | Registrar situação concreta, motivo, fundamento e necessidade da exceção. |
| GOV10-03 | Escopo mínimo | Identificar beneficiário, capacidade, recurso, operações e contexto/estado abrangidos, limitando a exceção ao estritamente necessário. |
| GOV10-04 | Prazo limitado | Definir início e término ou condição objetiva de encerramento; não admitir privilégio temporário sem limite verificável. |
| GOV10-05 | Critérios impeditivos | Exceção administrativa não pode dispensar requisito legal, normativo ou critério técnico impeditivo. |
| GOV10-06 | Acesso emergencial | Prever procedimento específico para emergência, com autorização, escopo mínimo, controles compensatórios, rastreabilidade e revisão posterior. |
| GOV10-07 | Segregação de funções | A exceção não elimina automaticamente a independência entre executor e validador quando exigida. Eventual acumulação excepcional deve ser justificada e submetida à revisão independente posterior, quando aplicável. |
| GOV10-08 | Auditoria | Registrar solicitação, autorização, identidade dos participantes, execução, alterações, resultado, encerramento e revisão, conforme aplicabilidade. |
| GOV10-09 | Expiração e revogação | A exceção deve perder validade ao atingir o prazo ou condição de encerramento e admitir revogação antecipada por autoridade competente. |
| GOV10-10 | Revisão posterior | Exceções emergenciais e demais casos definidos pela política institucional devem ser submetidos a revisão posterior por pessoa autorizada e independente, quando aplicável. |
| GOV10-11 | Preservação histórica | A exceção não pode apagar, substituir ou modificar retroativamente fatos, registros, decisões ou trilhas anteriores. |

## 3. Fluxo conceitual recomendado

1. **Solicitação:** registrar situação, motivo, beneficiário, capacidade/escopo pretendidos, recursos/operações, duração e controles compensatórios propostos.
2. **Análise:** verificar admissibilidade, critérios impeditivos, conflito de interesses, segregação e necessidade de revisão/assinatura.
3. **Autorização:** autoridade institucional competente decide e registra fundamento, limites e validade. O beneficiário não autoriza a própria exceção quando houver exigência de independência.
4. **Execução:** administrador ou executor tecnicamente autorizado aplica somente a exceção aprovada, sem ampliar seu escopo.
5. **Monitoramento:** registrar uso, tentativas negadas, alterações e eventos relevantes.
6. **Expiração/encerramento:** retirar automaticamente ou revogar o acesso/competência excepcional ao fim da validade ou condição.
7. **Revisão posterior:** avaliar necessidade, conformidade, ações realizadas, controles compensatórios e eventuais incidentes; registrar conclusão e responsável.

Este fluxo é conceitual. Estados, transições, prazos e autoridades reais dependem de definição institucional e de compatibilização técnica.

## 4. Conteúdo mínimo do registro de exceção

O registro deve contemplar, conforme aplicabilidade:

- identificador único e categoria da exceção;
- solicitante e beneficiário;
- autoridade autorizadora e evidência de sua competência;
- executor técnico, quando houver;
- justificativa e fundamento;
- capacidade, escopo, recurso, operações e contexto/estado abrangidos;
- início, término ou condição objetiva de encerramento;
- controles compensatórios e restrições;
- exigência de assinatura e revisão independente;
- eventos de utilização, negação, alteração, revogação e encerramento;
- revisor posterior, instante, resultado e providências.

A autoria deve preservar os papéis distintos: solicitante, beneficiário, autoridade que autorizou, executor técnico e revisor. Os instantes do fato e do registro devem seguir a semântica de API04 e GOV-P07.

## 5. Limites de segurança e integridade

- Exceção não é mecanismo para contornar critérios legais, normativos, técnicos ou de segurança impeditivos.
- Não pode criar competência permanente nem ampliar privilégios além do escopo aprovado.
- Não deve permitir autoaprovação quando a política exigir autoridade independente.
- Acesso emergencial deve ser temporário, mínimo, monitorado e revisado.
- A falha ou indisponibilidade do fluxo ordinário não autoriza, por si só, acesso informal ou credenciais compartilhadas.
- A exceção não altera retroativamente a cronologia nem substitui retificação formal.
- A autorização e sua execução devem ser auditáveis; falha de auditoria obrigatória deve seguir a política de contingência institucional, sem sucesso silencioso.
- Assinatura eletrônica deve seguir a matriz por natureza do ato de GOV-P05/GOV-P06; esta proposta não define modalidade legal nem signatários institucionais.

## 6. Exemplos de aplicação e não aplicação

### 6.1 Substituição temporária por afastamento

Pode ser considerada exceção quando a autoridade competente autorizar capacidade e escopo limitados, prazo definido e registro do executor técnico. A substituição não transfere automaticamente todas as competências do servidor afastado.

### 6.2 Acesso emergencial para continuidade operacional

Pode ser considerado mediante hipótese institucional previamente definida, justificativa concreta, autorização, escopo mínimo, controles compensatórios, expiração e revisão posterior. A emergência não dispensa auditoria nem requisitos impeditivos.

### 6.3 Pedido para dispensar critério técnico impeditivo

Não é exceção administrativa admissível. O sistema e o procedimento não devem permitir que autorização administrativa substitua requisito legal, normativo ou técnico impeditivo.

## 7. Definições institucionais ainda necessárias

A validação das regras gerais não resolve:

- autoridade competente e cadeia de delegação para cada categoria;
- hipóteses admissíveis e não admissíveis de exceção;
- critérios objetivos para classificar uma emergência;
- prazos máximos, horários de cobertura e condições de encerramento;
- controles compensatórios por operação e nível de risco;
- quem realiza revisão posterior e em qual prazo;
- situações em que a revisão independente é obrigatória;
- modalidade e nível de assinatura, signatários por ato e contingência;
- retenção, preservação e acesso aos registros;
- tratamento de indisponibilidade de autenticação, autorização ou auditoria.

Essas definições devem ser formalizadas pela instituição e alinhadas às políticas de segurança, gestão de pessoas, privacidade, gestão documental e qualidade.

## 8. Dependências e critérios de fechamento

Dependências principais: GOV-P01/P02/P03 (modelo, autoridade e ciclo de vida das competências), GOV-P04 (segregação), GOV-P05/P06 (assinatura), GOV-P07/P08 (autoria e auditoria), GOV-P09/P11 (integridade e acesso à auditoria), API06 (concorrência), API07 (idempotência), API10 (autorização/segregação) e API12, conforme aplicabilidade.

GOV-P10 somente poderá ser considerada institucional e tecnicamente fechada quando:
- autoridades, hipóteses admissíveis e delegações estiverem formalizadas;
- fluxo ordinário e emergencial, prazos, controles e revisões estiverem aprovados;
- matriz de assinatura e segregação estiver harmonizada;
- eventos e autoria estiverem cobertos pela auditoria;
- expiração/revogação e comportamento em falhas estiverem especificados e tecnicamente verificados;
- compatibilidade com os contratos e mecanismos existentes estiver demonstrada;
- aprovação institucional e autorização específica de implementação estiverem registradas.

## 9. Controle e limitações

Documento exclusivamente documental. Não houve alteração de código, modelos, banco, migrações, serviços, rotas, frontend, OpenAPI, testes, build, CI, infraestrutura ou produção. Não foram definidos cargos, autoridades, prazos institucionais ou permissões finais. A validação em revisão não equivale a aprovação institucional e não autoriza implementação.

## 10. Histórico

| Versão | Data | Alteração |
|---|---|---|
| 0.1 | 2026-11-10 | Criação da proposta e registro da validação em revisão de GOV10-01 a GOV10-11 pelo responsável pelo projeto; definições institucionais e fechamento técnico permanecem pendentes. |
