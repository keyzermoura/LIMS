# Proposta de fechamento GOV-P02 — Autoridade e concessão de permissões

**Identificador:** PROP-LIMS-GOV-AUTH-001  
**Versão:** 0.1  
**Data:** 2026-11-10  
**Branch:** main  
**Estado:** modelo de governança validado em revisão pelo responsável pelo projeto em 2026-11-10; designações, delegações e procedimentos institucionais pendentes; fechamento técnico e implementação bloqueados.

## 1. Objetivo e limites

Definir o modelo de governança recomendado para solicitar, justificar, aprovar e executar concessões de competências funcionais no LIMS. Esta proposta complementa PROP-LIMS-GOV-002, PAC-LIMS-GOV-001 e PROP-LIMS-API10-001.

A validação em revisão estabelece uma diretriz de desenho do projeto. Não designa autoridades, não cria delegações, não atribui competências a cargos reais, não substitui atos institucionais e não autoriza implementação.

## 2. Modelo de três níveis validado em revisão

Em 2026-11-10, o responsável pelo projeto validou em revisão o seguinte modelo:

| Nível | Responsabilidade | Limites |
|---|---|---|
| 1. Autoridade institucional | Define a matriz de competências e delegações; designa formalmente quem pode aprovar concessões; estabelece limites e procedimentos. | A autoridade e a extensão de sua competência devem estar formalmente documentadas. |
| 2. Gestor/responsável funcional | Identifica a necessidade, solicita ou justifica o acesso e confirma a compatibilidade com as atribuições e o escopo de trabalho. Pode aprovar somente quando possuir delegação institucional expressa para isso. | A posição de chefia ou gestor, isoladamente, não presume competência para aprovar qualquer permissão. |
| 3. Administrador técnico | Executa a concessão, alteração, suspensão ou revogação aprovada; mantém configuração e evidência técnica. | Não decide autonomamente a competência funcional, não amplia escopo e não se autoatribui permissões funcionais. |

A instituição não precisa concentrar toda aprovação na autoridade máxima. Pode estabelecer uma matriz de competências e delegações para que gestores formalmente autorizados aprovem concessões dentro de limites definidos.

## 3. Diretrizes GOV02 validadas em revisão

| ID | Tema | Regra de desenho validada |
|---|---|---|
| GOV02-01 | Autoridade institucional | A instituição deve definir formalmente a matriz de competências e as autoridades/delegações responsáveis por aprovar concessões. |
| GOV02-02 | Delegação | Gestores ou responsáveis funcionais podem aprovar somente dentro da competência e dos limites expressamente delegados. |
| GOV02-03 | Solicitação | O servidor, sua chefia ou responsável funcional autorizado pode iniciar solicitação conforme procedimento institucional. |
| GOV02-04 | Justificativa funcional | A necessidade deve ser justificada em relação à atividade, atribuição, recurso, escopo e período necessários. |
| GOV02-05 | Aprovação prévia | A concessão deve ser aprovada pela autoridade competente antes de ser aplicada, salvo fluxo de contingência formalmente aprovado. |
| GOV02-06 | Execução técnica | O administrador técnico aplica exatamente a concessão autorizada e registra a execução. |
| GOV02-07 | Separação de responsabilidades | Solicitação/justificativa, aprovação e execução técnica devem ser identificáveis como atos distintos. A acumulação somente pode ocorrer quando formalmente permitida, justificada e controlada. |
| GOV02-08 | Autoconcessão | O beneficiário não pode aprovar a própria concessão; o administrador técnico não pode conceder a si próprio competência funcional sem autorização independente e formalmente rastreável. |
| GOV02-09 | Menor privilégio | A concessão deve limitar-se às capacidades, operações, recursos, escopos organizacionais, contextos e períodos necessários. |
| GOV02-10 | Registro e evidência | Registrar solicitante, justificativa, aprovador e fundamento de sua competência, beneficiário, permissões, escopo, validade, executor técnico, instante e resultado. |
| GOV02-11 | Negação por padrão | Na ausência de concessão válida e compatível com a operação, o sistema deve negar a autorização. |

## 4. Fluxo conceitual recomendado

1. **Solicitação:** servidor ou chefia registra a necessidade e o escopo solicitado.
2. **Justificativa funcional:** gestor/responsável funcional confirma a necessidade e a compatibilidade com as atribuições.
3. **Aprovação:** autoridade formalmente competente aprova ou rejeita, dentro da matriz de delegações.
4. **Execução técnica:** administrador técnico aplica somente o que foi aprovado.
5. **Registro e confirmação:** o sistema mantém trilha de solicitação, decisão, execução e vigência.
6. **Revisão do acesso:** mudanças de atribuição, lotação ou situação funcional acionam o processo GOV-P03 de revisão, suspensão ou revogação.

O fluxo é conceitual e depende de integração com os processos institucionais de gestão de pessoas e segurança.

## 5. Conteúdo mínimo da concessão

- identificador único;
- solicitante e justificativa;
- beneficiário;
- autoridade aprovadora;
- referência ao ato de designação/delegação que sustenta a competência do aprovador;
- capacidades/permissões concedidas;
- recursos, operações, escopo organizacional e contexto;
- início e, quando aplicável, fim ou condição de encerramento;
- executor técnico e instante de aplicação;
- decisão, resultado e evidência associada;
- vínculo com alteração, renovação, suspensão ou revogação posterior.

O sistema deve distinguir quem solicitou, quem justificou, quem aprovou, quem executou e quem recebeu a competência. Não aceitar identidade do aprovador ou executor como campo livre informado pelo solicitante.

## 6. Princípios de implementação futura

- Autorização deve ser aplicada no backend, não apenas ocultando controles na interface.
- Papéis podem agrupar capacidades, mas não devem substituir a avaliação de escopo e contexto.
- JWT identifica a sessão e o usuário; não constitui, isoladamente, prova de concessão vigente.
- Alterações e revogações devem ser refletidas nas decisões de autorização conforme política de atualização/revalidação.
- O administrador técnico não recebe automaticamente competências de negócio.
- Concessões devem ser auditáveis e compatíveis com GOV-P05/P06, GOV-P07/P08, GOV-P09/P11, API06, API07 e API10.
- O modelo não determina tecnologia, estrutura de tabelas, endpoints ou desenho final de interface.

## 7. Definições institucionais pendentes

- autoridade que aprova cada categoria de competência;
- cargos/funções formalmente delegados e limites de delegação;
- procedimento e evidências aceitas para solicitação e aprovação;
- tratamento de substituições e contingências;
- categorias de permissões que exigem assinatura formal;
- prazos e responsáveis por revisão, suspensão e revogação (GOV-P03);
- integração com gestão de pessoas e identidade institucional;
- retenção e acesso aos registros de concessão.

## 8. Critérios de fechamento

GOV-P02 somente poderá ser considerada fechada quando a instituição aprovar a matriz de competências e delegações, os procedimentos de solicitação/aprovação/execução, as evidências exigidas e as regras de segregação; e quando a revisão técnica demonstrar enforcement no backend, rastreabilidade e compatibilidade com os mecanismos existentes. A aprovação institucional e a autorização específica de implementação são etapas distintas.

## 9. Controle e histórico

Documento exclusivamente documental. Não foram alterados código, banco, migrações, serviços, rotas, frontend, OpenAPI, testes, build, CI ou infraestrutura. Não houve validação runtime ou em produção.

| Versão | Data | Alteração |
|---|---|---|
| 0.1 | 2026-11-10 | Criação da proposta e registro da validação em revisão do modelo de três níveis e das diretrizes GOV02-01 a GOV02-11. |
