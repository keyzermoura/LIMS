# 04 — Critérios de Qualidade e Gates

## 1. Princípios inegociáveis

- O backend é a autoridade final para autorizar e validar gravações.
- A interface pode orientar e antecipar erros, mas não substitui validação do servidor.
- Registro definitivo, evento de auditoria e consumo da assinatura devem manter atomicidade quando o fluxo exigir assinatura.
- Históricos e artefatos emitidos não podem ser silenciosamente sobrescritos.
- Toda exceção precisa de regra formal, autorizador, justificativa, prazo e trilha.
- Dados históricos devem preservar contexto e versão das regras utilizadas.
- Nenhuma mudança de schema ocorre sem migração versionada e estratégia de rollback.
- Nenhuma credencial, token, chave ou senha pode ser commitada.

## 2. Regras específicas

### Autorização

- Verificar usuário ativo, permissão para a ação e escopo organizacional do registro.
- Aplicar princípio do menor privilégio.
- Proteger operações administrativas e de autoelevação.
- Definir comportamento explícito para permissões herdadas, conflitantes e negadas.
- Testar acesso direto à API; esconder botão no frontend não é controle de segurança.
- Preservar compatibilidade durante migração de roles.

### Habilitação técnica

- Verificar pessoa, método e versão aplicável.
- Verificar status, vigência, escopo e requisitos de competência.
- Registrar qual qualificação/evidência foi considerada na operação.
- Definir comportamento para expiração ou revogação durante uma execução aberta.
- Não confundir permissão de sistema com competência técnica.

### Metrologia

- Verificar estado operacional, situação de calibração, validade, escopo/faixa e restrições.
- Decidir a validade pela data/hora definida na política do domínio, não apenas pela data corrente.
- Registrar o instrumento e snapshot do certificado/documento usados.
- Preservar histórico de calibrações e documentos.
- Exceções não podem ser silenciosas ou editáveis depois do fechamento.

### Revisão e laudo

- Separar versões de dados, revisões documentais e controle de concorrência.
- Conferir segregação e conflito de interesse.
- Fixar os dados/fatos que compõem o laudo emitido.
- Manter artefato e hash verificáveis.
- Uma correção deve ser emenda/revisão formal, nunca substituição invisível.

### Auditoria e logs

- Capturar ator, ação, entidade, tempo, razão e contexto.
- Registrar antes/depois quando aplicável, evitando credenciais e dados desnecessários.
- Correlacionar logs técnicos por request ID sem converter log técnico em prova de auditoria de negócio.
- Não mascarar uma falha como sucesso nem descartar exceção relevante.
- Proteger acesso e retenção dos logs.

### Backup e recuperação

- Definir escopo e consistência entre banco e documentos.
- Proteger cópias em trânsito e em repouso conforme política institucional.
- Separar permissões de administração da aplicação e acesso aos backups.
- Monitorar execução, tamanho, idade e resultado da cópia.
- Testar restauração com frequência definida e armazenar evidências do teste.

## 3. Tipos de teste esperados

- Unitário: regras de domínio, datas, validade, precedência e máquina de estados.
- Integração: banco, transações, concorrência, auditoria, assinatura e migrações.
- API: autenticação, autorização, casos negativos e fluxos reais.
- PostgreSQL: triggers, locks, sequences, constraints e comportamento específico.
- Frontend: fluxos, visibilidade por permissão, estados e mensagens; nunca como única prova de controle.
- Segurança: privilege escalation, IDOR/escopo, replay de assinatura, mutação de histórico e exposição de dados.
- Recuperação: restauração banco + arquivos e verificação de hashes.

## 4. Gates de mudança

### Gate G0 — Diagnóstico
- Mapa do comportamento atual.
- Baseline de testes e CI.
- Lacunas confirmadas e não confirmadas separadas.
- Nenhuma implementação estrutural iniciada sem evidências.

### Gate G1 — Projeto técnico
- Requisitos e contratos aprovados.
- Modelo de dados e migrações revisados.
- Decisões arquiteturais registradas.
- Riscos e rollback documentados.

### Gate G2 — Implementação
- Critérios de aceite atendidos.
- Testes unitários e de integração.
- Casos negativos e concorrência quando aplicável.
- Auditoria e assinatura verificadas.

### Gate G3 — Revisão independente
- Diff revisado.
- Segurança e permissões avaliadas.
- Migração/rollback verificados.
- Documentação atualizada.
- Findings bloqueadores resolvidos.

### Gate G4 — Validação integrada
- Suíte completa pertinente.
- PostgreSQL real.
- Fluxos fim a fim.
- Evidências documentadas e limitações aceitas.
- Responsáveis funcionais/técnicos aprovam.

### Gate G5 — Liberação
- PR aprovado.
- Backup e rollback disponíveis quando necessários.
- Plano de implantação e monitoramento.
- Integração em main somente por decisão explícita.
- Deploy em produção exige autorização separada.

## 5. Evidência mínima por entrega

- Identificador da tarefa e commit.
- Requisitos e critérios de aceite.
- Arquivos e componentes afetados.
- Comandos de teste executados, ambiente e resultado.
- Relatório de revisão.
- Migração e estratégia de rollback.
- Logs/artefatos de teste sem dados sensíveis.
- Riscos residuais, limitações e aprovação.
