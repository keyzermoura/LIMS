# 05 — Registro de Decisões

Este registro distingue decisões de gestão já adotadas de decisões técnicas ainda abertas.

## D-001 — Criar branch dedicada

**Estado:** ACEITA  
**Decisão:** conduzir esta iniciativa em `feature/evolucao-governanca-metrologia`, criada a partir do HEAD de `main` em 17/11/2026 (`e9b7675866640ba424be319919ee1f3b029c32a5`).  
**Motivo:** isolar escopo e documentação da linha principal e de branches de fases anteriores.  
**Consequência:** todo trabalho desta iniciativa deve ocorrer nesta branch até revisão e PR.

## D-002 — Documentar antes de implementar

**Estado:** ACEITA  
**Decisão:** iniciar com diagnóstico, plano, backlog, critérios de qualidade e registro de decisões; não alterar código de aplicação nesta etapa.  
**Motivo:** há componentes existentes e risco de duplicação/regressão.  
**Consequência:** tarefas devem alcançar Definition of Ready antes de entrar em desenvolvimento.

## D-003 — Evoluir componentes existentes

**Estado:** ACEITA COMO DIRETRIZ  
**Decisão:** priorizar extensão de modelos e serviços existentes (equipamentos, qualificação, revisão, laudo e auditoria), evitando entidades duplicadas sem justificativa.  
**Motivo:** o repositório já contém bases de domínio para as propostas.  
**Consequência:** novos modelos exigem lacuna demonstrada e ADR.

## D-004 — Separar autorização organizacional de competência técnica

**Estado:** ACEITA COMO DIRETRIZ  
**Decisão:** autorização administrativa por recurso/ação/escopo e habilitação para método/atividade serão verificações distintas e cumulativas quando o caso exigir.  
**Motivo:** acesso ao módulo não prova competência para executar um método.  
**Consequência:** modelos, policies e testes devem manter essa separação.

## D-005 — Separar revisão do resultado e revisão documental

**Estado:** ACEITA COMO DIRETRIZ  
**Decisão:** versões dos dados laboratoriais e revisões do laudo oficial terão ciclos de vida distintos e relações explícitas.  
**Motivo:** evitar ambiguidade e preservar rastreabilidade de resultados e documentos.  
**Consequência:** não reutilizar o campo genérico `version` sem definir semântica e regras.

## D-006 — Não declarar conformidade por implementação

**Estado:** ACEITA  
**Decisão:** documentos e telas não declararão conformidade ou acreditação apenas porque controles foram implementados.  
**Motivo:** a avaliação depende de uso pretendido, procedimentos, validação e evidências do laboratório.  
**Consequência:** requisitos e decisões regulatórias devem ser aprovados por responsáveis competentes.

## D-007 — Padrão documental da iniciativa

**Estado:** ACEITA  
**Decisão:** usar documentação Markdown em `docs/evolucao-governanca-metrologia/`, IDs `EGLM-NNN`, decisões numeradas e histórico de mudanças.  
**Motivo:** tornar o trabalho rastreável e revisável.  
**Consequência:** issues, commits, PRs e evidências devem referenciar os IDs.

## D-008 — Modelo de entidades e perfis configuráveis

**Estado:** PENDENTE  
**Questão:** árvore de entidades, memberships múltiplos, herança, negação, delegação e escopo são necessários em quais contextos?  
**Opções:** RBAC com escopo por entidade; RBAC + políticas contextuais; alternativas avaliadas após inventário de endpoints.  
**Responsável:** produto e arquitetura.  
**Próximo passo:** EGLM-010 e EGLM-011.

## D-009 — Momento da verificação metrológica

**Estado:** PENDENTE  
**Questão:** elegibilidade será verificada na seleção, início, momento da medição, gravação definitiva ou em múltiplos momentos?  
**Opções:** validação no início e fechamento; validação em cada medição; regras por tipo de instrumento.  
**Responsável:** responsável técnico/metrologia.  
**Próximo passo:** EGLM-030 e EGLM-031.

## D-010 — Expiração da habilitação durante execução

**Estado:** PENDENTE  
**Questão:** como tratar uma execução iniciada quando a habilitação era válida, mas encerrada após a data de expiração ou revogação?  
**Responsável:** qualidade e responsável técnico.  
**Próximo passo:** EGLM-020.

## D-011 — Numeração de revisões do laudo

**Estado:** PENDENTE  
**Questão:** definir padrão oficial da numeração R00/R01, quando reiniciar sequência, como tratar reemissão e relação com número do laudo.  
**Responsável:** coordenação e qualidade.  
**Próximo passo:** EGLM-041.

## D-012 — Destino, retenção e recuperação de backup

**Estado:** PENDENTE  
**Questão:** definir share/rede, credenciais, periodicidade, retenção, criptografia, RPO/RTO e responsabilidade operacional.  
**Responsável:** TI e gestor do laboratório.  
**Próximo passo:** EGLM-053.

## D-013 — Layout FUNED e conteúdo do PDF

**Estado:** PENDENTE  
**Questão:** obter modelo oficial aprovado, cabeçalho, textos, campos obrigatórios, regra de decisão, assinatura e QR.  
**Responsável:** qualidade/coordenação.  
**Próximo passo:** EGLM-042.

