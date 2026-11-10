# Proposta de Resolução API09 — Comportamento quando o objeto já foi aceito

**Identificador:** PROP-LIMS-API09-001  
**Versão:** 0.1  
**Situação:** Proposta técnica para revisão; validação funcional, técnica e institucional pendente — implementação bloqueada  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Data:** 2026-11-09

---

## 1. Objetivo e limites

Definir o comportamento do comando de aceite quando um `CustodyObject` já possui uma `DeviceSample`, distinguindo replay da mesma operação, nova tentativa com chave diferente, concorrência entre operações, reutilização indevida de chave e conflito de versão.

A proposta preserva DEC05: um `CustodyObject` aceito gera no máximo uma `DeviceSample`; no fluxo ordinário, exatamente uma. Aceite, criação da amostra, vínculo e identificador devem ser atômicos e protegidos contra concorrência.

Documento exclusivamente documental. Não altera código, modelos SQLAlchemy, banco, migrações Alembic, endpoints, frontend, especificação funcional ou OpenAPI. Não foram executados testes, build, CI ou validação automática. Não há autorização de implementação.

## 2. Dependências e contexto

- **API06 — concorrência:** `expected_version` no corpo dos novos comandos mutáveis; `version` nas respostas; 409 `VERSION_CONFLICT`; aceite protegido pela versão do `CustodyObject`.
- **API07 — idempotência:** `Idempotency-Key` obrigatória para aceite; mesma chave e mesmo hash reproduzem o resultado original; mesma chave com hash diferente resulta em 409 `IDEMPOTENCY_KEY_REUSED`; replay concluído é reconhecido antes da validação de versão.
- **DEC05/API03:** um objeto origina no máximo uma amostra operacional. Objetos distintos podem compartilhar atributos comerciais sem representar a mesma amostra.

As regras gerais de API06 e API07 foram validadas pelo responsável pelo projeto em revisão, mas ainda dependem de fechamento técnico e aprovação institucional. Esta proposta não equivale a aprovação institucional nem autoriza implementação.

## 3. Distinções semânticas

| Situação | Definição | Tratamento proposto |
|---|---|---|
| Replay idempotente | Mesma operação lógica, mesma chave/escopo e mesmo conteúdo normalizado, já concluída | Reproduzir status e corpo originais; não executar novamente. |
| Reutilização indevida da chave | Mesma chave no mesmo escopo, conteúdo/hash diferente | 409 `IDEMPOTENCY_KEY_REUSED`. |
| Objeto já aceito | Nova operação lógica, com nova chave, para objeto que já possui amostra | 409 `OBJECT_ALREADY_ACCEPTED`; não criar outra amostra. |
| Mesma chave em processamento | Requisições simultâneas para a mesma operação lógica | Aplicar API07: aguardar ou retornar 409 transitório `IDEMPOTENCY_REQUEST_IN_PROGRESS`; nunca executar duas vezes. |
| Aceites concorrentes com chaves diferentes | Duas operações distintas tentam aceitar o mesmo objeto | Uma vence; a outra reavalia o estado persistido e recebe 409 `OBJECT_ALREADY_ACCEPTED`. |
| Versão desatualizada | Objeto ainda não aceito, mas comando usa versão antiga | 409 `VERSION_CONFLICT`, conforme API06. |

A comparação de fabricante, nome comercial, lote ou serial não substitui a identidade do `CustodyObject`. A decisão é sobre o objeto, não sobre deduplicação global de atributos comerciais.

## 4. Alternativas avaliadas

### Alternativa A — Nova tentativa retorna sucesso com a amostra existente

Uma nova chave, mesmo representando nova intenção, recebe sucesso com a amostra já criada.

**Não recomendada.** Confunde uma nova operação com replay, pode mascarar erro do cliente e pode sugerir que um novo aceite foi executado.

### Alternativa B — Conflito de estado explícito

Uma nova operação lógica para objeto já aceito recebe 409 `OBJECT_ALREADY_ACCEPTED`. O corpo pode conter referência mínima à amostra existente, somente se o chamador estiver autorizado.

**Recomendada.** Distingue replay da tentativa nova, preserva a unicidade e permite à interface direcionar o usuário ao registro existente.

### Alternativa C — Criar outra amostra e sinalizar duplicidade depois

**Rejeitada.** Viola DEC05 e fragiliza a rastreabilidade.

## 5. Comportamento proposto por cenário

| Cenário | Resultado | Efeito de domínio |
|---|---|---|
| Primeira tentativa válida, objeto elegível e ainda não aceito | 201 Created, sujeito à confirmação do contrato API01 | Criar uma única `DeviceSample`, vínculo e `accession_number`. |
| Mesma chave, mesmo escopo e mesmo hash, operação concluída | Reproduzir status/corpo originais | Nenhum efeito adicional. |
| Mesma chave e hash diferente | 409 `IDEMPOTENCY_KEY_REUSED` | Nenhum efeito adicional. |
| Mesma chave ainda em processamento | Política API07; proposta-base 409 `IDEMPOTENCY_REQUEST_IN_PROGRESS` ou espera controlada | Nenhuma segunda execução. |
| Nova chave para objeto já aceito | 409 `OBJECT_ALREADY_ACCEPTED` | Não criar outra amostra; referência mínima somente se autorizada. |
| Duas chaves diferentes tentam aceitar simultaneamente | Uma operação conclui; a outra recebe 409 `OBJECT_ALREADY_ACCEPTED` após reavaliar o estado | Exatamente uma amostra. |
| Versão desatualizada para objeto ainda não aceito | 409 `VERSION_CONFLICT` | Nenhum efeito. |
| Objeto inelegível por pendência, recusa ou outro estado impeditivo | Erro de domínio específico a consolidar | Nenhuma amostra; não converter em `OBJECT_ALREADY_ACCEPTED`. |
| Chamador sem autorização para consultar objeto/amostra | 403 ou 404, conforme API10 | Não revelar existência nem dados do recurso. |

O 201 para o primeiro aceite é recomendação inicial, não contrato aprovado. A escolha final deve ser coerente com API01 e com o contrato de criação de recursos.

## 6. Corpo do conflito e proteção de informação

Para uma nova chave direcionada a objeto já aceito, recomenda-se envelope de erro com código estável `OBJECT_ALREADY_ACCEPTED`, mensagem funcional e, quando autorizado, referência mínima à amostra existente. Não retornar cópia integral da amostra, dados de solicitante ou conteúdo de assinatura.

Exemplo ilustrativo, não aprovado como schema OpenAPI:

~~~json
{
  "detail": {
    "code": "OBJECT_ALREADY_ACCEPTED",
    "message": "Este objeto de custódia já foi aceito e possui amostra operacional vinculada.",
    "custody_object_id": "uuid",
    "existing_sample": {
      "id": "uuid",
      "accession_number": "LIMS-2026-000123"
    }
  }
}
~~~

A referência à amostra é condicional à autorização atual. Se sua divulgação não for permitida, omitir os dados ou aplicar a resposta 403/404 definida pela API10. A chave idempotente não é credencial nem substitui autorização.

## 7. Ordem lógica de processamento proposta

1. Autenticar o principal e aplicar as verificações de autorização pertinentes.
2. Normalizar método, rota, recurso-alvo e conteúdo; localizar/reservar a chave no escopo API07.
3. Se a chave já estiver concluída: hash igual reproduz o resultado original após revalidar autorização atual; hash diferente retorna 409 `IDEMPOTENCY_KEY_REUSED`.
4. Se a mesma chave estiver em processamento, aplicar espera/timeout ou 409 transitório conforme API07; não executar paralelamente.
5. Para nova operação lógica, iniciar transação e bloquear o `CustodyObject`, serializando tentativas de aceite.
6. Revalidar autorização, existência e estado do objeto.
7. Verificar se já existe `DeviceSample` vinculada. Se existir, não executar aceite; retornar 409 `OBJECT_ALREADY_ACCEPTED`, com referência mínima apenas se autorizada.
8. Se ainda não aceito, comparar `expected_version` com a versão persistida, conforme API06.
9. Validar elegibilidade e identidade; criar a amostra, estabelecer vínculo único, gerar `accession_number` e registrar auditoria/assinatura exigíveis, preservando chegada e recebedor originais.
10. Persistir efeitos de domínio e resultado idempotente na unidade transacional apropriada, com commit atômico.
11. Retornar a resposta de criação definida pelo contrato final.

A ordem é conceitual. O mecanismo concreto de reserva da chave, bloqueios, isolamento e recuperação de falhas depende do fechamento técnico de API06/API07.

## 8. Precedência entre objeto já aceito e versão desatualizada

Após o primeiro aceite, a versão do objeto provavelmente terá avançado. Uma nova chave com versão antiga pode, portanto, encontrar simultaneamente objeto já aceito e versão desatualizada.

Se o servidor responder sempre `VERSION_CONFLICT`, o cliente pode interpretar que basta atualizar a versão para repetir o aceite. Se responder `OBJECT_ALREADY_ACCEPTED`, comunica o estado terminal do domínio.

**Recomendação:** para uma nova operação lógica, após autenticação/autorização e leitura transacional protegida, verificar primeiro se o objeto já foi aceito. Se sim, retornar `OBJECT_ALREADY_ACCEPTED` sem mutação, independentemente de `expected_version`. Se ainda não foi aceito, comparar a versão e, se divergente, retornar `VERSION_CONFLICT`.

Essa precedência não se aplica ao replay de chave já concluída: API07 exige reproduzir o resultado original antes da validação de versão.

A regra depende de confirmação conjunta com API06/API07, inclusive quanto à serialização transacional e autorização.

## 9. Garantias de integridade e atomicidade

A solução final deverá garantir:

1. unicidade persistente de `DeviceSample` por `CustodyObject` no novo fluxo;
2. serialização de operações concorrentes sobre o mesmo objeto;
3. comparação da versão sob proteção transacional;
4. criação da amostra, vínculo, `accession_number`, auditoria, assinatura exigível e resultado idempotente na unidade atômica apropriada;
5. rollback integral se qualquer etapa obrigatória falhar;
6. impossibilidade de objeto marcado como aceito sem amostra correspondente ou amostra criada sem vínculo/aceite correspondente;
7. preservação dos registros legados, sem atribuir objetos artificiais às amostras históricas;
8. ausência de evento inicial de custódia duplicado, respeitando API04/DEC04;
9. preservação do instante original de chegada e do recebedor físico;
10. tratamento explícito de colisões de unicidade como concorrência/estado já aceito, sem erro 500 genérico.

A constraint única é salvaguarda final, não substitui bloqueio transacional nem regra de domínio. A forma física da constraint depende da revisão relacional e do schema real do banco.

## 10. Compatibilidade legada

- Preservar rotas e contratos legados nesta decisão.
- Não vincular automaticamente amostras antigas a novos objetos de custódia.
- Não reinterpretar a constraint legada serial + lote + fabricante como substituta da unicidade objeto–amostra.
- Não alterar `accession_number`, QR Code ou mecanismos de consulta.
- Aplicar `OBJECT_ALREADY_ACCEPTED` ao novo fluxo de aceite de `CustodyObject`; não projetar automaticamente o erro em operações legadas.
- Confirmar runtime e compatibilidade de clientes antes de qualquer implementação.

## 11. Impactos documentais após validação

- **API06:** incorporar precedência entre estado já aceito e `VERSION_CONFLICT`.
- **API07:** explicitar que nova chave para objeto já aceito não é replay; mesma chave concluída continua reproduzindo resultado original.
- **API01/especificação de contratos:** fixar status de sucesso inicial, envelope de conflito e política de exposição da referência existente.
- **OpenAPI:** atualizar somente após fechamento das decisões e autorização documental específica; esta proposta não altera o arquivo.
- **Modelo relacional:** confirmar vínculo único `CustodyObject`–`DeviceSample`, integridade e tratamento legado.
- **API10:** definir autorização para visualizar objeto e amostra referenciada.
- **API05:** alinhar atomicidade e assinatura do aceite.

## 12. Dependências e questões em aberto

- API06: precedência proposta e mecanismo de bloqueio/versionamento no runtime.
- API07: processamento concorrente da mesma chave, timeout, recuperação e retenção.
- API10: autorização e comportamento 403/404, inclusive para a referência à amostra.
- API05: assinatura exigida, alvo assinado e transação.
- API04: catálogo de eventos e prevenção de evento duplicado.
- API03/DEC05: granularidade e vínculo único do objeto.
- Modelo relacional: constraint/índice único e tratamento dos registros legados.
- API01: status HTTP e envelope final.
- Runtime/banco-alvo: constraints, bloqueios, migrações aplicadas e comportamento real.
- Política institucional: aprovação da semântica de conflito e exposição mínima de identificadores.

## 13. Recomendação final

Adotar a **Alternativa B**:

- primeira operação válida: cria uma única `DeviceSample` e retorna a resposta de criação definida no contrato final;
- mesma chave e mesmo conteúdo: replay exato do resultado original, conforme API07;
- mesma chave com conteúdo diferente: 409 `IDEMPOTENCY_KEY_REUSED`;
- nova chave para objeto já aceito: 409 `OBJECT_ALREADY_ACCEPTED`, sem nova amostra e com referência mínima somente quando autorizada;
- aceites concorrentes com chaves diferentes: apenas um conclui; o outro recebe `OBJECT_ALREADY_ACCEPTED`;
- versão desatualizada em objeto ainda não aceito: 409 `VERSION_CONFLICT`;
- nova operação para objeto já aceito tem precedência sobre conflito de versão; replay concluído da mesma chave tem precedência sobre ambos.

A proposta preserva DEC05 e coordena as salvaguardas de API06/API07. Não autoriza implementação nem alteração de contratos existentes.

## 14. Controle de execução

**Realizado:** recuperação das propostas API06/API07 e da matriz API01–API12 na branch `main); elaboração documental da proposta API09, com cenários de replay, nova chave, chave divergente, concorrência, estado já aceito, precedência de erros e exposição autorizada da referência existente.

**Não realizado:** alterações em código, modelos, banco, migrações, endpoints, frontend, OpenAPI, testes, build, CI ou infraestrutura; consulta ao banco/runtime; validação automática.

**Pendências:** validação funcional e técnica da proposta; confirmação conjunta da precedência API06/API07; fechamento da autorização API10, assinatura API05, envelope API01 e integridade relacional; aprovação institucional aplicável. Implementação permanece bloqueada.

## 15. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-09 | Primeira proposta de comportamento para objeto já aceito, distinguindo replay idempotente, nova chave, concorrência e conflito de versão. |
