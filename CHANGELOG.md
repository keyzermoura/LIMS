# Changelog — LIMS (Fiscalização Pós-Mercado de Dispositivos Médicos)

Todas as alterações notáveis deste projeto serão documentadas neste arquivo.
O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

---

## [1.1.0] - 2026-11-18

### Adicionado
- **Lookup por Código de Barras / DataMatrix (H3.3):** Busca de amostras por `accession_number`, `serial_number` ou `lot_number` através do endpoint `GET /api/v1/samples/lookup/barcode/{barcode}`.
- **Emissão e Assinatura em Lote de Laudos Periciais (H3.5):** Rota `POST /api/v1/reports/official/batch` com assinatura eletrônica única (21 CFR Part 11) que assina todo o lote, sequences monotônicas individuais e cálculo de manifesto criptográfico agregado (`batch_manifest_hash`).
- **Orquestração Cloud-Native Kubernetes (`deploy/k8s/`):** Manifestos declarativos para `configmap`, `secret-template`, `deployment-api`, `service-api`, `deployment-frontend`, `service-frontend`, `ingress` com TLS/HSTS e `kustomization.yaml`.
- **Harness de Testes de Carga e Estresse:** Suite assíncrona (`backend/tests/load_test_concurrency.py`) validando 126 req/s em consultas e 115 req/s em verificação pública com rate limiting ativo.
- **Relatório EGLM-006:** Isolamento estrito de schemas de teste em PostgreSQL (`lims_test_*`) e paridade total de 23 triggers DDL de imutabilidade.

### Modificado
- **Segurança da UI (P0.5):** Painel de contas de demonstração (`DEMO_ACCOUNTS`) condicionado a `import.meta.env.DEV`, eliminando credenciais de teste dos bundles de produção.
- **Redirecionamento HTTPS (P0.1):** Nginx do Docker Compose configurado com bloco dedicado na porta 80 emitindo `return 301 https://$host$request_uri`.
- **Harmonização de Versões:** Versão unificada em `1.1.0` no backend (`config.py`, `pyproject.toml`) e frontend (`package.json`).

---

## [1.0.0] - 2026-11-17

### Adicionado
- **Gate G-A (Integridade ALCOA+ e Auditoria):**
  - Trilha de auditoria encadeada com hash SHA-256 e HMAC inviolável.
  - Triggers de imutabilidade PostgreSQL contra alteração, deleção e truncamento em tabelas críticas (`audit_logs`, `lab_test_results`, `chain_of_custody_events`, `electronic_signatures`).
- **Gate G-B (Segurança de Acesso e Laudos Periciais):**
  - Desafio de segundo fator MFA/TOTP no fluxo de login (`mfa_pending` / `verify_login_mfa`) com segredos cifrados via Fernet.
  - Emissões de laudos periciais com geração de PDF real via ReportLab e hash SHA-256.
  - Versionamento formal de emendas aos laudos periciais (ISO/IEC 17025 §7.8.8) com rastreabilidade de justificativa técnica e supersedes.
  - Verificação pública de integridade de laudos por QR Code assinado.
- **Gate G-C (Núcleo Laboratorial e Qualidade Analítica):**
  - Gestão de reagentes, padrões e materiais de referência certificados (CRM) com controle de lote, validade e baixa atômica via `with_for_update()`.
  - Fluxo completo de OOS/OOT com investigação Fase I/Fase II, CAPA automática e intertravamento de laudos.
  - Controle Estatístico de Processo (CEP) com 5 regras de Westgard ativas bloqueando emissão em caso de violação.
  - Armazenamento, contraprova e termo de descarte seguro com dupla assinatura eletrônica e segregação de funções.
- **Gate G-D (Interoperabilidade e Ecossistema):**
  - Contas de serviço M2M autenticadas por Bearer Token e verificação de idempotência (`Idempotency-Key`).
  - Padrão Transactional Outbox com worker assíncrono contínuo via `SKIP LOCKED` e suporte a dead-letter queue.
  - Gateway de integração de instrumentos laboratoriais (parser ASTM E1394).
- **Validação Computadorizada (CSV):**
  - Dossiê consolidado de validação GAMP 5 / Guia Anvisa nº 33/2020 (`DOSSIE_VALIDACAO_SISTEMA_COMPUTADORIZADO_CSV_V1_0_0.md`).
