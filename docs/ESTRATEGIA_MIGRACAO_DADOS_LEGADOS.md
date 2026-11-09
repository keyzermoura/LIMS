# Estratégia de Migração e Convivência com Dados Legados

**Identificador:** MIG-LIMS-001  
**Versão:** 0.2  
**Situação:** Proposta técnica para revisão; não aprovada para execução  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Data:** 2026-11-09

---

## 1. Objetivo

Definir uma abordagem conservadora para evoluir o banco de dados atual do LIMS, incorporando futuramente solicitação, recebimento físico, conferência por item e custódia pré-amostra, sem perder nem reinterpretar indevidamente os registros já existentes.

A estratégia busca preservar:
- identificadores internos e institucionais já atribuídos;
- `DeviceSample.accession_number` e o funcionamento dos QR Codes existentes;
- datas, autoria, status, resultados, assinaturas e trilhas de auditoria;
- eventos históricos de `ChainOfCustody`;
- referências e vínculos atualmente válidos.

Este documento é uma proposta de planejamento. Não autoriza alterações no banco, criação de migrações Alembic, execução de scripts, backfill, alteração de API ou implantação.

## 2. Escopo e limites da evidência

A estratégia considera o inventário estático do repositório e os modelos conceituais documentados. O inventário identificou PostgreSQL 16 como banco de referência, SQLAlchemy 2 assíncrono e Alembic, com cadeia de migrações composta pela migração inicial, `0002_guards` e `0003_audit_export`.

O CI consultado passou em ambiente efêmero, incluindo migrações e testes SQLite/PostgreSQL. Isso não comprova o estado, volume, qualidade ou configuração de qualquer banco institucional.

Ainda não foram inspecionados nesta atividade:
- banco de desenvolvimento, homologação ou produção;
- quantidade e distribuição real dos registros;
- existência de dados órfãos, duplicados ou inconsistentes;
- backups existentes e sua capacidade comprovada de restauração;
- consumidores externos ou integrações que dependam do formato atual do QR Code;
- relatórios, exportações ou rotinas operacionais não versionadas no repositório.

Esses itens são pré-requisitos de planejamento detalhado, não pressupostos.

## 3. Princípios obrigatórios

1. **Preservação:** não apagar nem sobrescrever dados históricos para adequá-los ao novo modelo.
2. **Migração aditiva:** preferir novas tabelas, colunas opcionais, índices e restrições introduzidos gradualmente.
3. **Compatibilidade:** manter os fluxos existentes funcionando durante a transição, salvo decisão formal em contrário.
4. **Sem associação fictícia:** não criar solicitação, item declarado, recebimento ou unidade física retroativos sem evidência documental confiável.
5. **Identidade estável:** não renumerar amostras nem reutilizar identificadores.
6. **Histórico imutável:** não reescrever datas, autoria, eventos de custódia, assinaturas ou resultados para simular o novo fluxo.
7. **Rastreabilidade:** toda associação legada realizada deve ter origem, critério, responsável e evidência registrados.
8. **Repetibilidade:** scripts de migração e reconciliação devem ser idempotentes ou possuir controles equivalentes contra execução duplicada.
9. **Integridade transacional:** operações que criem amostra e identificador devem preservar atomicidade e unicidade no banco.
10. **Rollback planejado:** toda etapa deve ter estratégia de recuperação compatível com os efeitos já produzidos.

## 4. Classificação dos registros existentes

A migração deverá distinguir, no mínimo, os seguintes grupos:

| Grupo | Tratamento proposto |
|---|---|
| Amostras existentes em `DeviceSample` | Preservar como registros legados; não exigir vínculo com solicitação ou recebimento novo. |
| `accession_number` existentes | Preservar literalmente; não recalcular nem renumerar. |
| QR Codes e dados usados para sua validação | Preservar compatibilidade e testar leitura/validação antes e depois de cada etapa. |
| Eventos `ChainOfCustody` existentes | Preservar sequência, conteúdo, autoria e timestamps; não converter retroativamente em eventos de recebimento. |
| Ensaios e resultados | Preservar relações, versões, assinaturas e histórico. |
| Auditoria e assinaturas eletrônicas | Preservar registros e mecanismos de integridade; não recalcular hashes como se fossem eventos novos. |
| Amostras com dados incompletos ou inconsistentes | Não corrigir automaticamente; classificar para análise e tratamento autorizado. |
| Amostras com documentação externa confiável | Permitir associação futura somente após regra de correspondência aprovada e registro da evidência. |

A classificação definitiva dependerá de diagnóstico somente leitura sobre uma cópia controlada do banco.

## 5. Estratégia para identificadores e QR Code

### 5.1 Campo `DeviceSample.accession_number`

O inventário registra que o campo atual é gerado no formato `LIMS-AAAA-######` por sequence. A diretriz funcional é que cada amostra operacional aceita receba identificador institucional único, global no âmbito institucional e independente do laboratório.

Antes de qualquer mudança, deve-se:
1. mapear todos os usos de `accession_number` no backend, frontend, QR Code, relatórios, exportações, testes e integrações;
2. verificar constraints, índices, sequence e regras de geração atuais;
3. confirmar se o valor atual satisfaz os requisitos institucionais de identificador;
4. confirmar com os responsáveis se o formato visual atual pode ser mantido;
5. documentar consumidores e contratos de compatibilidade.

**Recomendação preliminar:** não criar um segundo campo que represente o mesmo identificador sem demonstrar necessidade. Se `accession_number` cumprir a função institucional, formalizar seu papel e preservar valores existentes. Se não cumprir, avaliar campo adicional com migração aditiva e período de compatibilidade, sem substituir ou reinterpretar os valores antigos.

### 5.2 QR Code

- Não alterar algoritmo, payload, segredo HMAC, rota de resolução ou semântica do QR sem análise de impacto e autorização.
- Testar QR Codes históricos e novos em conjunto.
- Não presumir que o QR contém apenas o identificador visível; inspecionar implementação e consumidores.
- Planejar compatibilidade durante todo o período em que documentos ou etiquetas antigas estiverem em circulação.
- Não invalidar nem regenerar QR histórico como efeito colateral de migração.

## 6. Modelo de convivência entre legado e novo fluxo

A arquitetura deverá permitir que amostras antigas permaneçam válidas sem preencher artificialmente os novos relacionamentos.

Requisitos conceituais:
- vínculos de amostra com solicitação/recebimento devem ser opcionais para registros legados;
- ausência de vínculo deve ser representável como legado não associado, e não como erro de integridade;
- novas amostras criadas pelo fluxo novo devem exigir os vínculos e validações aplicáveis;
- regras distintas para legado e novos registros devem ser explícitas, auditáveis e temporárias quando possível;
- consultas, relatórios, QR e telas devem continuar tratando corretamente os dois grupos.

Não se recomenda atribuir um recebimento fictício a todas as amostras antigas apenas para satisfazer uma nova chave estrangeira.

## 7. Abordagem técnica por etapas — expand/contract

Adotar, como estratégia preferencial, evolução em etapas compatíveis (expand/contract). A sequência abaixo é indicativa e depende da aprovação do modelo físico e das decisões DEC04, DEC05, DEC07 e DEC08.

### Etapa A — Baseline e diagnóstico

- Confirmar commit, versão do schema e revisão Alembic do ambiente-alvo.
- Obter inventário somente leitura das tabelas, constraints, índices, sequences e triggers.
- Levantar volumes, nulos, duplicidades, órfãos e distribuições relevantes.
- Mapear relações de `DeviceSample`, `LabTest`, `LabTestResult`, `ChainOfCustody`, `AuditLog` e `ElectronicSignature`.
- Identificar relatórios, integrações e consumidores do identificador/QR.
- Registrar baseline de contagens e verificações de integridade.

### Etapa B — Expandir o schema

Somente após aprovação do modelo relacional:
- criar novas tabelas de solicitação, itens declarados, recebimento, itens de recebimento e demais entidades aprovadas;
- introduzir novas colunas de vínculo em tabelas existentes como opcionais inicialmente;
- adicionar índices e constraints compatíveis com dados legados;
- preservar tabelas, colunas e relações atuais;
- manter o fluxo atual de criação de amostras durante a fase de coexistência.

As entidades e nomes físicos definitivos não estão aprovados por este documento.

### Etapa C — Implantar o novo fluxo sem exigir backfill

- Implementar e testar o novo fluxo para novas solicitações/recebimentos.
- Fazer com que novas amostras originadas pelo novo fluxo recebam os vínculos obrigatórios no mesmo limite transacional.
- Manter o caminho legado explicitamente identificado enquanto houver necessidade autorizada.
- Não misturar criação direta de amostra e criação via recebimento de forma ambígua.
- Monitorar erros, duplicidade, integridade e compatibilidade.

### Etapa D — Associação seletiva de legado (opcional)

Só executar se houver benefício funcional comprovado e decisão aprovada:
- definir critérios determinísticos de correspondência;
- usar documentos ou registros de origem verificáveis;
- classificar correspondências como confirmadas, ambíguas ou sem evidência;
- associar apenas casos confirmados;
- manter os casos ambíguos/sem evidência sem vínculo;
- registrar método, evidência, operador, data/hora e resultado;
- produzir relatório de antes/depois e lista de exceções.

É vedado inferir solicitação ou recebimento apenas por proximidade de datas, semelhança textual ou coincidência de fabricante/lote.

### Etapa E — Contrair (somente após decisão específica)

A remoção, bloqueio ou descontinuação de fluxos antigos só poderá ocorrer após:
- comprovar que não há consumidores dependentes;
- verificar que os novos fluxos cobrem os casos operacionais;
- concluir testes de regressão e aceitação;
- aprovar plano de reversão;
- obter autorização institucional específica.

A etapa de contração pode não ser necessária para todos os componentes. Não remover campos ou rotas apenas para simplificar o schema.

## 8. Regras de integridade e transação

O desenho físico deve prever:
- unicidade do identificador institucional no escopo aprovado;
- criação de amostra e identificador na mesma transação;
- idempotência contra repetição de requisição;
- proteção contra concorrência, inclusive por constraints no banco;
- vínculos opcionais para legado e obrigatórios no fluxo novo conforme regra aprovada;
- preservação da data/hora original de chegada e do recebedor físico;
- continuidade auditável entre custódia pré-amostra e custódia da amostra;
- integridade referencial sem associações artificiais;
- proteção das tabelas append-only e dos mecanismos existentes de auditoria/assinatura.

Não definir agora nomes de colunas, constraints, sequences ou triggers. Esses detalhes dependem do modelo entidade-relacionamento aprovado e da revisão do schema real.

### 8.1 Compatibilidade com o conceito de ObjetoCustodia

A recomendação conceitual mais recente é que novos eventos de custódia sejam vinculados a um ObjetoCustodia persistente, que represente uma unidade física ou agrupamento homogêneo. A implementação deverá preservar integralmente os eventos atuais de `ChainOfCustody`, sem convertê-los retroativamente em eventos de ObjetoCustodia.

Se for aprovada uma nova estrutura de custódia:
- manter os registros históricos existentes e suas chaves;
- criar relações entre novos objetos de custódia e amostras apenas para eventos originados no novo fluxo;
- estabelecer associação entre amostra legada e ObjetoCustodia somente quando houver evidência e regra aprovada;
- não copiar eventos antigos para a nova tabela como se tivessem sido produzidos pelo novo fluxo;
- documentar como consultas e linhas do tempo apresentarão, em sequência temporal, eventos legados e novos sem duplicidade.

A forma de coexistência entre `ChainOfCustody` e o novo modelo precisa ser definida no modelo físico e testada antes de qualquer migração.

## 9. Plano de validação e reconciliação

Cada migração deverá produzir evidências antes e depois. A matriz mínima proposta:

| Verificação | Critério |
|---|---|
| Contagem de registros | Contagens por tabela crítica reconciliadas; diferenças explicadas e aprovadas. |
| Identificadores | Nenhum `accession_number` histórico alterado, duplicado ou ausente por efeito da migração. |
| QR Code | Amostra de QR históricos e novos validada pelo mecanismo oficial; nenhum contrato quebrado. |
| Custódia | Quantidade, sequência, autoria e timestamps históricos preservados. |
| Ensaios/resultados | Relações e versões históricas preservadas. |
| Assinaturas/auditoria | Hashes, HMACs, snapshots e verificações existentes continuam íntegros. |
| Integridade referencial | Ausência de novos órfãos; exceções preexistentes documentadas. |
| Idempotência | Reexecução controlada não duplica entidades nem identificadores. |
| Concorrência | Testes demonstram que requisições simultâneas não criam duplicidade. |
| Compatibilidade | API, frontend, relatórios e integrações críticas continuam funcionando. |
| Performance | Índices e consultas críticas avaliados com volume representativo. |
| Recuperação | Restauração de backup e plano de rollback exercitados em ambiente isolado. |

Os limites quantitativos, amostragem, responsáveis e evidências formais deverão constar dos critérios de aceite da Fase 1.

## 10. Backup, recuperação e rollback

Antes de qualquer migração em ambiente persistente:
1. identificar responsável institucional pelo banco e pela autorização da mudança;
2. obter backup consistente, com registro de data/hora, escopo, método e localização controlada;
3. comprovar restauração em ambiente isolado;
4. registrar versão do código, revisão Alembic e versão do banco;
5. suspender ou controlar gravações conforme plano de mudança;
6. executar migração em ambiente de homologação com cópia representativa;
7. comparar resultados com baseline;
8. obter aprovação para produção, caso aplicável.

**Rollback:** preferir restauração testada ou correção compensatória planejada. Downgrade Alembic não deve ser presumido seguro quando houver dados novos, alterações irreversíveis, triggers ou operações de backfill. Cada revisão deverá declarar limitações de downgrade e procedimento de recuperação.

Não definir RPO, RTO, retenção ou periodicidade de backup neste documento; dependem de política institucional (DEC12).

## 11. Ambientes e sequência de promoção

Sequência recomendada:
1. ambiente local de desenvolvimento com dados sintéticos;
2. CI com PostgreSQL da mesma versão principal do ambiente-alvo;
3. homologação com cópia mascarada ou conjunto representativo autorizado;
4. produção somente após aprovação institucional e plano de mudança.

Dados reais não devem ser copiados para ambientes de desenvolvimento sem autorização, base legal, controles de acesso e proteção adequados. Seeds de demonstração não podem ser confundidos com dados operacionais.

## 12. Riscos e controles

| Risco | Consequência | Controle proposto |
|---|---|---|
| Associação retroativa sem evidência | História falsa e rastreabilidade comprometida | Não associar; manter legado sem vínculo. |
| Alteração de `accession_number` | QR, relatórios e documentos deixam de localizar amostras | Preservação literal e testes de compatibilidade. |
| Recriação de eventos de custódia | Duplicidade ou distorção da cadeia histórica | Preservar eventos existentes; iniciar novo modelo apenas para eventos novos. |
| Constraint nova incompatível com legado | Migração falha ou bloqueia operação | Diagnóstico, colunas opcionais e constraints graduais. |
| Duplo fluxo de criação | Amostras duplicadas ou sem origem inequívoca | Idempotência, unicidade e regras explícitas de transição. |
| Downgrade destrutivo | Perda de dados novos | Backup restaurável e plano por etapa; não confiar apenas no downgrade. |
| Diferença entre schema e metadata | Drift entre ambientes | Alembic como caminho controlado e verificações CI. |
| QR ou integração não mapeada | Falha operacional após implantação | Inventário de consumidores e regressão ponta a ponta. |

## 13. Decisões e informações necessárias antes da execução

| ID | Dependência | Situação |
|---|---|---|
| DEC04 | Modelo aprovado de custódia pré-amostra e transferência para amostra | Pendente |
| DEC05 | Granularidade item/unidade/amostra/corpo de prova | Pendente |
| DEC07 | Papel definitivo de `accession_number`, escopo e compatibilidade QR | Diretriz funcional definida; análise técnica pendente |
| DEC08 | Política de associação ou manutenção do legado sem vínculo | Pendente |
| DEC12 | Backup, retenção, recuperação e continuidade | Pendente |
| CT-MIG-01 | Inventário somente leitura do banco-alvo e consumidores | Não realizado |
| CT-MIG-02 | Baseline de contagens e integridade | Não realizado |
| CT-MIG-03 | Plano de teste de restauração e rollback | Não realizado |
| CT-MIG-04 | Aprovação do modelo físico e das migrações | Não realizada |

## 14. Critérios para considerar a estratégia pronta para detalhamento

- DEC04, DEC05, DEC07 e DEC08 resolvidas ou com tratamento explícito aprovado.
- Modelo entidade-relacionamento físico revisado.
- Inventário do banco-alvo concluído.
- Consumidores de identificadores e QR mapeados.
- Política de convivência do fluxo legado definida.
- Plano de backup/restauração validado pela TI responsável.
- Plano de validação, reconciliação e rollback aprovado.
- Critérios de aceite e responsáveis definidos.
- Autorização específica para implementação e execução emitida.

## 15. Conclusão

A recomendação é evoluir o LIMS por migração aditiva e compatível, mantendo as amostras antigas como registros válidos mesmo quando não possuam solicitação ou recebimento associados. A história existente — identificadores, QR Codes, custódia, resultados, assinaturas e auditoria — deve ser preservada.

A associação de dados legados deve ser seletiva e baseada em evidência. Na ausência de evidência confiável, a ausência de vínculo é preferível a uma associação inferida.

Este documento não autoriza implementação, backfill, migração de banco ou alteração de ambiente. A próxima atividade é revisar a estratégia com os responsáveis funcionais e técnicos, obter os dados de diagnóstico necessários e resolver as decisões bloqueadoras antes do portão G0.

## 16. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-09 | Primeira proposta de estratégia de migração aditiva, convivência com legado, validação e recuperação. |\n| 0.2 | 2026-11-09 | Alinhamento da estratégia com a recomendação conceitual de ObjetoCustodia e preservação de ChainOfCustody legado. |
