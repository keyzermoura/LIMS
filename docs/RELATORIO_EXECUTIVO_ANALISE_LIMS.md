# Relatório Executivo — Análise Técnica e Estratégica do LIMS

**Data:** 16/11/2026
**Base analisada:** `main` @ `97c7b33` (Fases 1–4) e `feature/fase-5-integracoes-expansao` @ `7cef52d` (Fase 5)
**Natureza:** parecer técnico sênior (não é auditoria formal de validação)
**Público:** direção da SEFI, gestão de projeto, responsável técnico e qualidade

---

## 1. Veredito em uma página

O LIMS possui **fundação de engenharia acima da média** para um sistema público customizado. O que falta não é arquitetura: é **fechamento de escopo** e **disciplina de integridade de dados**.

| Dimensão | Situação | Leitura |
|---|---|---|
| Modelagem do domínio (solicitação, recebimento, custódia, execução, revisão) | **Boa** | Estados ricos, custódia assinada, separação planejamento × tentativa |
| Qualidade metrológica (GUM, ILAC-G8, CAPA) | **Boa** | Incerteza e regra de decisão implementadas de fato, não só documentadas |
| Engenharia e CI (ruff, mypy, Alembic, pytest SQLite+PG, smoke Docker) | **Boa** | 103 testes, paridade modelo↔migração verificada no pipeline |
| Integridade de dados (ALCOA+, imutabilidade) | **Parcial** | Triggers cobrem metade das tabelas críticas; laudo é mutável |
| Segurança de acesso | **Insuficiente** | Sem MFA real, sem TLS no repositório, rotas da Fase 5 sem autorização por papel |
| Escopo laboratorial para acreditação | **Incompleto** | Sem reagentes/padrões, sem OOS/OOT, sem alíquotas, sem armazenamento/descarte |
| Interoperabilidade | **Embrionária** | Importação de arquivo unidirecional; sem ASTM/HL7/OPC, sem integração corporativa |
| Rastreabilidade de release | **Insuficiente** | Nenhuma tag git; versão `0.1.0` após quatro fases entregues |

**Três conclusões que exigem decisão da direção:**

1. **A Fase 5 não deve ser promovida como está.** Os indicadores analíticos retornam valores fabricados (TAT, conformidade, eficácia de CAPA e 16 pontos de carta de controle fixos no código) quando não há dados. Em sistema validado, isso invalida o dossiê de validação inteiro.
2. **O artefato de maior valor probatório é o mais frágil.** O laudo oficial é o único registro que pode ser alterado sem trigger de imutabilidade, sem versionamento e com numeração sujeita a colisão sob concorrência.
3. **O sistema hoje é um LIMS de fiscalização, não de acreditação.** Falta o núcleo metrológico de bancada (reagentes e padrões, OOS/OOT, alíquotas, armazenamento e descarte) exigido pela ISO/IEC 17025 em escopo analítico.

---

## 2. O que está pronto e deve ser preservado

- **Cadeia de custódia e recebimento** (`solicitations`, `receipts`, `receipt_items`, `custody_objects`, `custody_events`, `receipt_decisions`) com conferência, apresentação e decisão formal.
- **Trilha de auditoria encadeada por hash**, append-only, com ancoragem que detecta restauração de backup antigo.
- **Assinatura eletrônica em duas etapas**, com TTL de 300 s e vínculo ao registro (`require_signature`).
- **Gate de competência e calibração**: não se executa ensaio sem analista qualificado e equipamento com calibração vigente.
- **Revisão por pares com bloqueio de auto-revisão**.
- **Incerteza GUM completa e regra ILAC-G8** com banda de guarda e declaração de conformidade.
- **Laudo com hash SHA-256 e verificação pública** por token.
- **Pipeline de CI completo**, incluindo PostgreSQL 16 real e smoke de Docker.

Esses ativos reduzem o esforço de correção: o problema é de **cobertura**, não de redesenho.

---

## 3. Os cinco riscos que importam

| # | Risco | Consequência se ignorado | Severidade |
|---|---|---|---|
| 1 | Imutabilidade parcial; laudo mutável e sem emenda; numeração `count+1` | Questionamento de validade probatória do laudo; não conformidade 21 CFR Part 11 §11.10(e); erro em emissão concorrente | **Alta** |
| 2 | Indicadores fabricados no analytics (Fase 5) | Perda de credibilidade do dossiê CSV; decisão gerencial sobre dado falso; não conformidade ALCOA+ | **Alta** |
| 3 | MFA inexistente (flag morta), TLS fora do repositório, `/docs` exposto, rotas sem autorização por papel, sem backup/PITR | Acesso indevido a dado sensível; perda total em falha de host; auditor não consegue demonstrar controle de acesso | **Alta** |
| 4 | Ausência de reagentes/padrões, OOS/OOT, alíquotas, armazenamento/descarte, código de barras | Impossibilidade de acreditação no escopo analítico; retrabalho e erro de transcrição na bancada | **Alta** |
| 5 | Interoperabilidade só por arquivo; sem autenticação máquina-a-máquina; sem baseline de release | Cada integração vira ETL no banco (proibido pela validação); impossibilidade de provar qual versão foi validada | **Média-Alta** |

Detalhamento técnico, evidências de código e plano de correção: ver documentos anexos.

---

## 4. O que se pede à direção

### Decisões (não técnicas)

1. **Bloquear a promoção da Fase 5 para produção** até que os riscos 1, 2 e 3 estejam fechados. Custo do bloqueio: baixo. Custo de promover: retrabalho de validação e exposição institucional.
2. **Declarar explicitamente o escopo de acreditação pretendido.** O roadmap de 12 meses depende de quais ensaios entrarão no escopo. Sem essa definição, o risco 4 não pode ser dimensionado.
3. **Instituir baseline versionado de release** (tag git + CHANGELOG) como pré-requisito de qualquer novo ciclo de validação CSV.
4. **Definir a política de retenção e descarte de amostras e dados**, hoje inexistente no sistema e exigida por BPL/RDC 786.

### Investimento estimado

Premissa: 2 desenvolvedores full-stack, 0,5 QA e 0,3 DevOps. Unidade: **semana-pessoa (SP)**, margem ±30%.

| Frente | Esforço | Janela |
|---|---|---|
| Fechamento dos riscos 1–3 (integridade, segurança, infraestrutura) | ~35 SP | 0–90 dias |
| Núcleo laboratorial (reagentes, OOS/OOT, armazenamento, alíquotas) | ~29 SP | 90–210 dias |
| Interoperabilidade e disciplina de release | ~38 SP | 180–365 dias |
| **Total** | **~102 SP** | **12 meses** |

### Critério de "pronto para uso institucional"

O sistema só deve ser apresentado como pronto quando **todos** forem verdadeiros:

- [ ] Toda tabela regulada possui trigger de imutabilidade ou de congelamento pós-conclusão, com teste automatizado em PostgreSQL.
- [ ] Nenhum endpoint retorna valor sintético ou *fallback* numérico.
- [ ] MFA ativo para ADMIN e FISCAL; TLS obrigatório; `/docs` desabilitado em produção.
- [ ] Backup com PITR e **restauração testada e registrada** nos últimos 90 dias.
- [ ] Laudo emitido é imutável, versionável por emenda e numerado por sequence.
- [ ] Existe tag de release assinada e CHANGELOG correspondente ao binário validado.

---

## 5. Anexos

| Documento | Conteúdo |
|---|---|
| `ROADMAP_90_180_365_LIMS.md` | Roadmap por horizonte, gates, dependências e critérios de aceite |
| `PLANO_CORRECAO_RISCOS_1_3_LIMS.md` | Plano de implementação detalhado de integridade, analytics e segurança |
| `ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md` | Especificação da camada de integração e autenticação máquina-a-máquina |
