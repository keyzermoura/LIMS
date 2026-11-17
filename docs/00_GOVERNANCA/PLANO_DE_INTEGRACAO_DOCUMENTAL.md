# Plano de Integração Documental — LIMS-SEFI

**Identificador:** PLN-INT-LIMS-SEFI-001  
**Versão:** 0.7  
**Data:** 2026-11-11  
**Branch:** `docs/integracao-especificacao-sefi`  
**Natureza:** plano de organização documental; não constitui aprovação funcional, institucional ou técnica.

## 1. Objetivo

Integrar os documentos existentes em uma especificação coerente do LIMS-SEFI, preservando documentos originais, decisões aprovadas, histórico e limites de validação. A integração deve reduzir duplicação e contradições sem reabrir decisões ratificadas nem promover propostas a requisitos aprovados.

## 2. Princípios mandatórios

1. **Preservação:** fontes existentes não serão sobrescritas ou apagadas.
2. **Rastreabilidade:** toda afirmação normativa da especificação integrada deverá apontar para uma fonte e, quando aplicável, seção/decisão.
3. **Precedência:** D01–D20 e G0-P01–G0-P30 permanecem regidas pelo registro institucional vigente.
4. **Separação de status:** aprovado, documentado, proposto, pendente, não verificado e validado operacionalmente são situações diferentes.
5. **Sem aprovação tácita:** organização editorial não altera o status de uma decisão.
6. **Sem inferência:** ausência de documento/evidência não será preenchida com suposição.
7. **Sem implementação:** esta iniciativa é exclusivamente documental.
8. **Controle de mudanças:** qualquer conflito com decisão aprovada será apresentado como divergência e não corrigido silenciosamente.
9. **Histórico preservado:** documentos de origem continuam acessíveis em seus caminhos e commits.
10. **Revisão verificável:** cada entrega terá fonte, versão, commit e readback registrados.

## 3. Escopo

### Incluído
- Inventário e classificação documental.
- Catálogo Mestre e índice de fontes.
- Consolidação editorial de decisões ratificadas.
- Especificação integrada de domínio e processos.
- Requisitos funcionais e não funcionais.
- Rastreabilidade entre decisões, requisitos, entidades, estados, eventos, invariantes, critérios CA, cenários SIM e evidências.
- Arquitetura-alvo em nível de especificação, condicionada às decisões institucionais pendentes.
- Registro de lacunas, conflitos, hipóteses e decisões necessárias.
- Critérios de validação e plano de verificação.

### Excluído
- Alterações em código-fonte, banco de dados, migrações, API, frontend, CI/CD e infraestrutura.
- Migração real de dados.
- Homologação operacional em nome do SEFI.
- Designação de autoridades, titulares ou substitutos.
- Aprovação jurídica ou escolha unilateral de modalidade de assinatura.
- Aprovação do Gate G0.
- Merge da branch documental em `main` sem autorização específica.

## 4. Pacotes de trabalho

| Pacote | Atividade | Saída | Critério de conclusão documental |
|---|---|---|---|
| PT-01 | Inventário documental completo | Catálogo Mestre atualizado | Fontes do repositório e referências externas identificadas; limitações explicitadas |
| PT-02 | Consolidação da baseline de decisões | Baseline D01–D20 e G0-P01–P30 | Todas as decisões preservadas com seus limites e dependências |
| PT-03 | Integração do domínio | Modelo de domínio integrado | Entidades, relações, cardinalidades, estados, eventos e invariantes rastreados às fontes |
| PT-04 | Integração dos processos | Especificação de processos SEFI | Fluxos principais, exceções, atores, permissões e bloqueios identificados; lacunas separadas |
| PT-05 | Especificação funcional | Requisitos funcionais e regras de negócio | RF-001–RF-020 e EDP-REC-SEFI-001 v0.1 (PROC-01–PROC-09) elaborados; revisão funcional, detalhamento PROC-10–PROC-16 e validação pendentes |
| PT-06 | Especificação não funcional e controles | Segurança, auditoria, assinatura, evidências, continuidade, consulta e retenção | Requisitos aprovados separados de parâmetros pendentes |
| PT-07 | Arquitetura-alvo | Visão lógica e técnica | Componentes, limites, contratos e decisões arquiteturais documentados sem iniciar implementação |
| PT-08 | Rastreabilidade e validação | Matriz D/ G0 × requisito × domínio × CA × SIM × evidência | Sem IDs ou resultados inventados; lacunas explícitas |
| PT-09 | Revisão de consistência | Relatório de conflitos e recomendações | Conflitos identificados, decisões necessárias destacadas e fontes preservadas |
| PT-10 | Dossiê integrado | Especificação integrada e índice final | Revisão cruzada documental concluída; validações pendentes identificadas |

## 5. Ordem de execução e dependências

1. Completar PT-01 antes de consolidar documentos que possam estar em outras pastas ou formatos.
2. PT-02 pode ser preparado com SRC-01, mas não deve alterar o registro-fonte.
3. PT-03 utiliza M0.3 como proposta de trabalho, mantendo M03-01 a M03-16 em aberto até validação.
4. PT-04 e PT-05 dependem da recuperação de EST-REC-001 e dos artefatos operacionais citados.
5. PT-06 aproveita D13–D17 e G0-P05/P06/P09/P19/P24/P25/P29/P30, sem escolher tecnologias ou parâmetros institucionais não aprovados.
6. PT-07 deve distinguir arquitetura existente, diagnóstico e arquitetura-alvo proposta.
7. PT-08 não pode atribuir critérios CA ou cenários SIM sem recuperar as fontes originais.
8. PT-09 registra conflitos; não decide questões institucionais.
9. PT-10 produz pacote para revisão e validação.

## 6. Registro de riscos documentais

| Risco | Tratamento |
|---|---|
| Documento aprovado não localizado | Registrar como referência não recuperada; não reconstruir como se fosse original |
| Versões conflitantes | Comparar histórico, identificar autoridade e submeter divergência |
| M0.3 confundido com decisão ratificada | Marcar cada elemento proposto e as pendências M03-01 a M03-16 |
| README/código tratados como baseline de domínio | Usar apenas como evidência do sistema existente |
| CA/SIM presumidos | Não preencher IDs, critérios ou resultados sem fonte |
| Aprovação de diretriz confundida com execução | Separar aprovação do método, execução, evidência e homologação |
| Branch documental confundida com autorização de implementação | Manter escopo documental e Gate G0 não aprovado |

## 7. Governança e entregas

Cada pacote será apresentado com:
- fontes utilizadas e suas versões;
- conteúdo produzido e localização;
- alterações realizadas exclusivamente na branch documental;
- lacunas, conflitos e hipóteses;
- status de aprovação de cada elemento;
- SHA do commit e resultado do readback.

A aprovação de um pacote documental não modifica automaticamente decisões anteriores nem autoriza implementação.

## 8. Progresso dos pacotes de trabalho — 2026-11-11

| Pacote | Situação atual | Evidência documental |
|---|---|---|
| PT-01 — Inventário | **Parcial** | Doze fontes recuperadas e registradas; inventário ainda não exaustivo porque a árvore completa do repositório não foi enumerada |
| PT-02 — Baseline de decisões | **Consolidado documentalmente** | SRC-01 preservado e referenciado; D01–D20 ratificadas e G0-P01–P30 aprovadas, com limites mantidos |
| PT-03 — Integração do domínio | **Primeira baseline consolidada elaborada** | BCDP-LIMS-SEFI-001 v0.1 reúne entidades, cardinalidades M0.2, dimensões de estado, eventos, invariantes e registro M03-01–M03-16; MAT-HARM-EST-SEFI-001 v0.1 mapeia estados/eventos EST × M0.3; revisão/validação pendentes |
| PT-04 — Integração dos processos | **Primeira versão ampliada** | Baseline de processos consolidada; mapa PROC-01–PROC-17 inclui continuidade/recuperação como controle transversal; validação operacional pendente |
| PT-05 — Especificação funcional | **Primeira versão elaborada** | RF-001–RF-020 derivados de D01–D20 |
| PT-06 — Requisitos transversais | **Primeira versão elaborada** | RT-001–RT-017 derivados de D01–D20/G0-P01–P30 |
| PT-07 — Arquitetura-alvo | **Não iniciada** | Depende da consolidação de domínio/processos e de decisões técnicas/institucionais |
| PT-08 — Rastreabilidade e validação | **Primeira versão ampliada** | Matrizes D01–D20 e G0-P01–P30 relacionadas a RF/RT/domínio/CA/SIM; plano de casos CA01–CA37; tudo não validado/não executado |
| PT-09 — Revisão de consistência | **Parcial, com consolidação inicial** | Divergências de estados, decisão/custódia, D19 e linhagem do ObjetoCustodia mapeadas na BCDP-LIMS-SEFI-001 e HARM-01–HARM-07; M03-01–M03-16 continuam pendentes |
| PT-10 — Dossiê integrado | **Em elaboração** | Especificação Integrada v0.2 referencia baseline de domínio/processos e mapa PROC-01–PROC-17; demais capítulos e validações pendentes |

As situações acima descrevem produção documental nesta branch. Não representam validação institucional, execução de testes, homologação, aprovação de arquitetura ou encerramento de bloqueadores do Gate G0.

## 9. Situação formal

- Caminho B: **ADOTADO PARA EXECUÇÃO DOCUMENTAL**.
- Branch documental isolada: criada.
- Repositório principal: permanece `keyzermoura/LIMS`.
- Documentos-fonte: preservados.
- Implementação: **NÃO AUTORIZADA**.
- Gate G0: **NÃO APROVADO**.
