# 02 — Diagnóstico Técnico Inicial

**Escopo da inspeção:** documentação principal, árvore do repositório, modelos, serviços, rotas e testes identificados na `main` em 17/11/2026.
**Commit examinado:** `e9b7675866640ba424be319919ee1f3b029c32a5`.
**Natureza:** leitura estática remota. Os testes não foram executados nesta inspeção.

## 1. Arquitetura observada

- API: Python, FastAPI, Pydantic v2, SQLAlchemy 2 assíncrono.
- Banco: PostgreSQL 16, asyncpg, JSONB, Alembic e SQL para triggers/índices.
- Frontend: React, TypeScript, Vite, Tailwind e componentes Radix/shadcn-style.
- Infraestrutura: Docker Compose com PostgreSQL, migração, API e web.
- Validação: pytest, testes de API e suítes de fases; CI em GitHub Actions.

Fonte inicial: README.md, docker-compose.yml, backend/app/main.py e estrutura do repositório.

## 2. Componentes encontrados

| Domínio | Evidência | Estado preliminar |
|---|---|---|
| Equipamentos | `backend/app/models/equipment.py`, `equipment_service.py` | Base existente |
| Dados de instrumentos | `instrument_data.py` | Base existente para importação e hash |
| Qualificação técnica | `qualification.py`, `qualification_service.py` | Base existente |
| Métodos | `test_method.py` | Modelo existente |
| Execução | `test_execution.py` e modelos relacionados | Exige mapeamento aprofundado |
| Revisão técnica | `test_review.py`, `lab_test.py` | Base existente |
| Laudos oficiais | `official_report.py`, `report_service.py` | Emissão, PDF, hash e emenda existentes |
| Auditoria | `audit_log.py`, `audit_service.py`, `audit.py` | Base criptográfica e consultas/exportação |
| RBAC | `core/rbac.py`, `api/deps.py`, `models/user.py` | Perfis e permissões fixos |
| Contexto de requisição | `core/context.py`, middleware em `main.py` | Request ID e tempo de processamento |
| Persistência | `docker-compose.yml` | Volume nomeado PostgreSQL local |

## 3. Achados técnicos com evidência

### 3.1 Equipamentos

O modelo `LaboratoryEquipment` contém:

- código, nome, tipo, fabricante, modelo, número de série e localização;
- situação de calibração;
- data da última calibração e data de vencimento;
- número do certificado e entidade calibradora;
- propriedade `is_calibration_valid`.

O serviço `equipment_service.py` contém cadastro, atualização, atualização de calibração e snapshot de auditoria com valores antigos/novos em alterações.

A relação de `LabTest` com `equipment_id` existe. O diagnóstico completo deve confirmar o vínculo para execução, os pontos de gravação definitiva e se o bloqueio está aplicado em todo caminho de escrita.

**Lacunas a confirmar:** tag patrimonial; arquivo do certificado; histórico de calibração independente do cadastro corrente; hash/assinatura do documento; snapshot congelado no ato da execução; bloqueio transacional nas rotas/serviços de execução e resultado; políticas para equipamento fora de uso, manutenção, calibração não aplicável e uso excepcional autorizado.

### 3.2 Competência técnica

O modelo `AnalystQualification` vincula `user_id` e `method_id`, registra status, concessão, validade, autorizador, assinatura, escopo e observações. `TrainingRecord` mantém treinamento, provedor, data, horas e código de certificado.

O serviço `qualification_service.py` oferece verificação por analista/método, concessão, suspensão/revogação e auditoria.

**Lacunas a confirmar:** ligação obrigatória do check com todas as operações de execução/edição/assinatura; qualificação por versão/revisão do método; evidências anexas e avaliação de eficácia; requalificação; competência de conferentes e emissores; gestão de substituições e escopos; regras sobre atividades iniciadas antes do vencimento.

### 3.3 Revisão e laudo oficial

O modelo `OfficialReport` registra número, amostra, conclusão, PDF binário, SHA-256, token de autenticidade, versão otimista, raiz, documento substituído, status de último e motivo da emenda.

O serviço `report_service.py` valida que os ensaios pertencem à amostra, estão concluídos e aprovados na revisão; também contém bloqueios de investigação OOS e violações CEP/Westgard. A rota `reports.py` oferece emissão, emenda, consulta, download PDF e verificação pública.

**Lacunas a confirmar:** workflow ponta a ponta Recebimento/SGA → execução → conferência técnica → coordenação/emissão; estados e transições; matriz de papéis por etapa; segregação executor/conferente/emissor; sequência R00/R01 distinta da versão de registro; snapshot de regra de decisão, método, incerteza e equipamentos; hashes/identificação das assinaturas no PDF; layout FUNED aprovado; log de reimpressões e política de retenção.

### 3.4 Autorização

O modelo `User` usa enum `UserRole`. `core/rbac.py` contém `ROLE_PERMISSIONS` estático e `api/deps.py` expõe `require_roles`.

**Lacunas a confirmar:** ausência/presença de modelos de organização/entidade, membership, perfil customizado e permissão persistida; escopo de permissões por entidade e hierarquia; política de herança e negação; delegação temporária; segregação de funções; gestão de contas privilegiadas e auditoria de alterações de permissões.

### 3.5 Auditoria e observabilidade

O sistema usa `AuditLog` e serviços de append/verify/export assinados. `RequestContext` transporta IP, user-agent e request_id. O middleware de `main.py` gera/propaga `X-Request-ID`, tempo e log de método/rota/status.

**Lacunas a confirmar:** cobertura uniforme de antes/depois em todos os cadastros e ações; auditoria de visualização e reimpressão; política de mascaramento de dados; logs estruturados e correlação de exceções; retenção e rotação dos logs técnicos; monitoramento/alertas.

### 3.6 Backup e continuidade

O Docker Compose monta volume nomeado `lims_pgdata` em `/var/lib/postgresql/data`.

**Lacunas a confirmar:** rotina automatizada `pg_dump`, consistência de PDFs e anexos, cópia externa para destino de rede, criptografia, controle de acesso, política de retenção, monitoramento de falhas, RPO/RTO acordados e restauração ensaiada.

## 4. Testes identificados no repositório

A árvore de testes contém arquivos para equipamentos, qualificação, revisões, relatórios oficiais, governança, integrações e operações de fases posteriores. Exemplos identificados:

- `backend/tests/test_phase5_instruments.py`
- `backend/tests/test_phase4_qualifications.py`
- `backend/tests/test_phase3_reviews.py`
- `backend/tests/test_phase6_report_amendments.py`
- `backend/tests/test_postgres_guards.py`
- `backend/tests/test_api_flow.py` (referenciado no README)

A presença de testes não foi interpretada como prova de execução ou aprovação. A próxima etapa deve mapear cada caso de teste aos critérios de aceite desta iniciativa e executar a suíte no ambiente apropriado.

## 5. Conclusão

O LIMS já possui fundações relevantes nos domínios metrológico, técnico, documental e de integridade. O foco recomendado é **integração, fechamento de lacunas e comprovação por testes**, não duplicação de módulos.

## 6. Itens que exigem investigação antes de implementar

1. Identificar todos os caminhos de criação/edição/assinatura de execução e resultado.
2. Mapear os relacionamentos de TestExecution, LabTest, TestReview e OfficialReport.
3. Inspecionar frontend para identificar o fluxo operacional atualmente exposto.
4. Ler migrações e SQL de proteção para avaliar a imutabilidade efetivamente aplicada.
5. Catalogar RBAC atual e todos os endpoints que dependem de roles.
6. Mapear documentos/anexos e armazenamento físico atual.
7. Examinar CI e executar testes de base, incluindo PostgreSQL real.
8. Examinar branches e PRs de fases paralelas para evitar conflito ou retrabalho.

## 7. Referências internas

- `README.md`
- `backend/app/models/equipment.py`
- `backend/app/services/equipment_service.py`
- `backend/app/models/qualification.py`
- `backend/app/services/qualification_service.py`
- `backend/app/models/official_report.py`
- `backend/app/services/report_service.py`
- `backend/app/api/v1/routes/reports.py`
- `backend/app/core/rbac.py`
- `backend/app/api/deps.py`
- `backend/app/core/context.py`
- `backend/app/main.py`
- `docker-compose.yml`
- `backend/tests/`
