# Proposta de Resolução API06 — Controle de Concorrência

**Identificador:** PROP-LIMS-API06-001  
**Versão:** 0.1  
**Situação:** Proposta técnica para revisão; validação arquitetural/funcional pendente — bloqueadora  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Data:** 2026-11-10

---

## 1. Objetivo e limites

Resolver documentalmente a decisão API06: escolher um mecanismo único para que operações de escrita não sejam confirmadas com base em uma versão desatualizada do recurso.

O escopo abrange, no mínimo:

- formalização da chegada/recebimento;
- salvamento progressivo de conferência, pendências e decisões;
- transferência de custódia;
- aceite e criação de DeviceSample;
- operações futuras que alterem estado de recursos versionados.

Este documento é proposta técnica. Não altera código, modelos, banco, migrações, endpoints, frontend ou OpenAPI e não autoriza implementação. Não foram executados testes, build, CI ou validação automática.

## 2. Evidências do estado atual

A inspeção documental e estática da branch `main` identificou:

1. `OptimisticLockMixin` define `version` inteira, não nula, com valor inicial 1 e descreve o envio da versão pelo cliente.
2. `DeviceSample` herda `OptimisticLockMixin` e expõe `version` em `SampleOut`.
3. `SampleStatusUpdate` recebe `version` no corpo.
4. `CustodyTransferRequest` também recebe `version` no corpo.
5. `custody_service.transfer` bloqueia a linha da amostra com `SELECT ... FOR UPDATE`, compara `sample.version` com o valor recebido, retorna conflito se divergente e incrementa a versão após a alteração.
6. `sample_service.update_status` segue padrão equivalente: bloqueio da linha, comparação, incremento e commit.
7. O OpenAPI proposto contém um parâmetro `If-Match` opcional e, simultaneamente, `expected_version` obrigatório no schema de transferência e `expected_object_version` obrigatório no schema de aceite.
8. O OpenAPI define a resposta 409 para conflito de versão e 428 como possibilidade genérica quando uma pré-condição If-Match for adotada.

Portanto, o padrão legado observado é versão no corpo, enquanto a proposta nova está contraditória: mistura dois mecanismos e ainda usa nomes diferentes para o mesmo conceito.

**Limite da evidência:** a inspeção é estática e não demonstra o comportamento de todos os endpoints, middleware, clientes ou migrações. A presença de `version` no mixin não prova, por si só, que o banco de produção esteja integralmente migrado ou que o ORM use `version_id_col` automaticamente. A verificação operacional permanece fora do escopo.

## 3. Alternativas avaliadas

### Alternativa A — If-Match/ETag no cabeçalho

O servidor devolve um ETag que representa a versão atual do recurso. O cliente envia `If-Match` na escrita. O servidor só confirma a operação se a representação ainda corresponder ao ETag.

**Vantagens**
- utiliza mecanismo HTTP padronizado para pré-condições;
- separa metadado de concorrência do conteúdo de negócio;
- permite resposta 412 Precondition Failed quando a representação mudou;
- é adequado para recursos que já possuem representação consultável e ETag forte.

**Desvantagens no contexto atual**
- diverge do padrão legado de `version` no corpo;
- exige definir geração, força, escopo e estabilidade dos ETags;
- exige garantir que GET devolva ETag e que toda escrita relevante o valide;
- exige alinhar clientes existentes e novos, inclusive telas que trabalham com vários itens;
- introduz 412 e 428, além dos conflitos de domínio já tratados por 409;
- o OpenAPI atual não define ETag de resposta nem a semântica completa do cabeçalho.

### Alternativa B — expected_version no corpo

O cliente envia a versão lida do recurso no corpo da operação. O servidor compara o valor com a versão persistida dentro da transação, antes de alterar o estado.

**Vantagens**
- preserva o padrão já utilizado por `SampleStatusUpdate` e `CustodyTransferRequest`;
- exige menor adaptação do backend e dos clientes existentes;
- deixa explícito no schema qual recurso está sendo protegido;
- facilita formular operações de domínio que alteram recursos relacionados, sem depender de um ETag HTTP previamente obtido;
- permite padronizar os nomes `version` na representação e `expected_version` na requisição.

**Desvantagens**
- o campo de concorrência fica misturado ao payload da operação;
- cada comando de escrita precisa declarar a versão do alvo correto;
- a API precisa documentar claramente qual recurso e qual versão são esperados;
- não aproveita diretamente a semântica condicional de HTTP.

### Alternativa C — Aceitar If-Match e expected_version simultaneamente

**Não recomendada.** Criaria dois valores potencialmente divergentes para a mesma pré-condição. A API teria que definir precedência, equivalência e comportamento quando ambos fossem enviados. Isso mantém a ambiguidade que API06 pretende eliminar.

## 4. Recomendação

Adotar a **Alternativa B — `expected_version` no corpo** como mecanismo único de concorrência otimista para os comandos de escrita do novo fluxo.

A recomendação considera a compatibilidade com o padrão efetivamente observado no backend atual. O cabeçalho `If-Match` deve ser removido dos contratos novos, não sendo aceito como mecanismo alternativo para as mesmas operações.

### 4.1 Convenção de nomes

- Campo de leitura/resposta: `version`.
- Campo de pré-condição em comando de escrita: `expected_version`.
- Tipo: inteiro positivo, iniciando em 1.
- Não usar nomes equivalentes concorrentes como `expected_object_version`, `expected_sample_version` ou `version` em payloads novos.
- O significado de `expected_version` deve identificar-se pelo recurso-alvo da operação, descrito no contrato.

A escolha não exige renomear imediatamente o campo `version` dos contratos legados. A adaptação de payloads antigos, se necessária, deve ser tratada separadamente e sem breaking change.

## 5. Aplicação por operação

### 5.1 Formalização da chegada

A criação inicial de `Receipt` não possui uma versão anterior do próprio recebimento que o cliente possa apresentar. A proteção principal deve ser:

- transação única;
- bloqueio da solicitação enquanto a chegada é formalizada;
- constraint única persistente que impeça mais de um recebimento principal por solicitação;
- idempotência conforme API07;
- validação do estado da solicitação dentro da transação.

Não se recomenda inventar um ETag ou uma versão de Receipt ainda inexistente apenas para o comando de criação.

Se a Solicitation for alterável e sua versão fizer parte do contrato aprovado, o comando poderá receber `expected_version` referente à Solicitation. Isso depende de confirmar que a entidade e sua versão existem e são mantidas de forma confiável. Até essa confirmação, o bloqueio transacional e a unicidade são as salvaguardas mínimas da criação.

### 5.2 Salvamento progressivo da conferência e das decisões

Cada comando que altera uma entidade persistida deve exigir `expected_version` da entidade que está sendo alterada.

A versão deve ser associada ao agregado correto. Se a operação altera um `ReceiptItem`, a versão esperada é a do `ReceiptItem`; se altera uma entidade de conferência ou decisão independente, deve ser a versão dessa entidade, caso exista como recurso persistente.

Não se deve usar uma única versão global do recebimento para proteger automaticamente todos os itens independentes, pois isso pode gerar conflitos desnecessários entre usuários que trabalham em itens distintos. A escolha final depende da modelagem física dos agregados.

### 5.3 Transferência de custódia

A requisição deve conter `expected_version`, referente ao `CustodyObject), e não ao evento de transferência nem à DeviceSample vinculada.

Exemplo conceitual:

~~~json
{
  "to_custodian_id": "uuid-user-destino",
  "occurred_at": "2026-11-10T10:30:00-03:00",
  "reason": "Encaminhamento para área de ensaios",
  "location_to": "Laboratório de ensaios",
  "expected_version": 3
}
~~~

O servidor deve, dentro da transação:

1. localizar e bloquear o CustodyObject;
2. verificar se está em estado que permite transferência;
3. comparar `expected_version` com `CustodyObject.version`;
4. validar autorização e custodiante de destino;
5. registrar o evento de transferência;
6. atualizar a projeção de custodiante/localização, se mantida;
7. incrementar a versão exatamente uma vez;
8. confirmar evento, projeção e auditoria atomicamente.

O evento deve preservar a versão resultante ou uma referência/snapshot suficiente para reconstruir o estado, conforme a política de auditoria a aprovar. A cadeia de eventos continua append-only.

### 5.4 Aceite e criação da DeviceSample

A requisição deve conter `expected_version`, referente ao `CustodyObject). Substituir o nome provisório `expected_object_version` por `expected_version`.

O servidor deve:

1. bloquear o CustodyObject;
2. comparar a versão esperada com a versão persistida;
3. revalidar conferência, pendências, decisão e validação de coordenação;
4. confirmar que o objeto ainda não originou DeviceSample;
5. criar a amostra e vincular ao objeto;
6. atualizar o estado do objeto e incrementar sua versão uma única vez, se o modelo de estados aprovado exigir essa alteração;
7. gravar auditoria/assinatura aplicáveis;
8. confirmar tudo em uma única transação.

A regra de aceite único continua protegida também por constraint de unicidade e pela regra transacional. Controle de versão não substitui integridade persistente.

A resposta deverá expor a versão resultante do objeto (`version`) e a versão da amostra (`version`) se esta última estiver disponível no schema de resposta.

### 5.5 Rotas legadas

Preservar o campo `version` e o comportamento atualmente observados nas rotas legadas, inclusive:

- atualização de status de amostra;
- transferência legada de custódia por `device_sample_id`.

Não renomear esses campos para `expected_version` nesta decisão. A padronização proposta aplica-se aos novos contratos; qualquer alteração legada requer análise própria de compatibilidade.

## 6. Semântica transacional e de versão

A versão é um contador monotônico do estado mutável do recurso, não um número de evento nem um timestamp.

Regras propostas:

1. Versão inicial igual a 1.
2. Toda alteração confirmada do estado protegido incrementa a versão em exatamente 1.
3. Operação rejeitada, rollback ou falha não incrementa a versão.
4. A comparação e a alteração devem ocorrer na mesma transação, com bloqueio de linha ou atualização condicional atômica equivalente.
5. A operação não pode confiar apenas na comparação feita no frontend.
6. O servidor retorna a versão atual em conflito, quando autorizado e seguro.
7. Eventos append-only não incrementam isoladamente a versão se não alterarem o estado do agregado; se a operação também altera o agregado, incrementa-se a versão uma vez na mesma transação.
8. Uma alteração que afete vários agregados deve declarar quais versões protege e atualizar cada agregado afetado de modo atômico. Evitar campos genéricos sem alvo inequívoco.
9. A exclusão lógica, encerramento, mudança de custodiante, localização ou estado de aceite contam como alterações do recurso protegido quando modificam seu estado corrente.

O uso de `SELECT ... FOR UPDATE` com comparação explícita, como observado no serviço legado, é uma implementação possível. Também é possível usar atualização condicional com `WHERE id = ... AND version = ...`. A escolha concreta pertence ao desenho técnico e não é determinada por este contrato.

## 7. Respostas e erros HTTP

| Situação | HTTP recomendado | Código de domínio | Regra |
|---|---:|---|---|
| Escrita concluída | 200 ou 201 conforme natureza da operação | — | Retornar a versão resultante do recurso. |
| `expected_version` ausente ou inválido | 422 | `VALIDATION_ERROR` | Campo obrigatório no schema da operação protegida. |
| Versão desatualizada | 409 | `VERSION_CONFLICT` | Nenhuma alteração parcial; informar `current_version` quando permitido. |
| Estado incompatível, mesmo com versão atual | 409 | Código específico de estado | Não confundir conflito de versão com conflito de domínio. |
| Recurso inexistente | 404 | `NOT_FOUND` | Conforme política de visibilidade. |
| Ator sem autorização | 403 | `FORBIDDEN` | Não revelar dados de versão do recurso. |

A proposta mantém 409 para versão desatualizada, em coerência com os serviços legados observados. Não adotar 412 nem 428 para esse mecanismo, pois eles correspondem à alternativa If-Match que não é recomendada.

O formato de erro deverá seguir o envelope geral já proposto, por exemplo:

~~~json
{
  "error": {
    "code": "VERSION_CONFLICT",
    "message": "O registro foi alterado por outro usuário. Atualize os dados antes de tentar novamente.",
    "details": {
      "current_version": 4
    },
    "request_id": "correlation-id"
  }
}
~~~

## 8. Relação com idempotência e aceite repetido

API06 e API07 são complementares:

- idempotência identifica a repetição da mesma tentativa lógica;
- controle de versão impede a confirmação de uma nova tentativa baseada em estado desatualizado.

A ordem de processamento deve ser definida em conjunto com API07. Para uma requisição repetida com a mesma chave idempotente e o mesmo conteúdo, o servidor deve conseguir reconhecer a repetição e reproduzir o resultado original sem rejeitá-la apenas porque a versão avançou após a primeira execução.

A mesma chave com payload divergente deve seguir a regra de conflito de idempotência, não ser confundida com `VERSION_CONFLICT`.

API09 deverá definir a resposta para uma nova tentativa de aceite com chave diferente quando o objeto já estiver aceito. A versão, sozinha, não decide se a resposta correta é replay, retorno do recurso existente ou conflito semântico.

## 9. Impactos documentais necessários após validação

Após aprovação desta decisão, atualizar de forma coordenada:

1. especificação funcional dos contratos HTTP:
   - substituir `If-Match ou version` pela regra única `expected_version`;
   - uniformizar `expected_object_version` para `expected_version`;
   - esclarecer qual entidade é alvo da versão em cada comando;
   - documentar versão em respostas e conflitos;
2. OpenAPI:
   - remover o parâmetro `If-Match` dos novos endpoints;
   - padronizar schemas e exemplos;
   - documentar 409 `VERSION_CONFLICT`;
   - remover a resposta 428 se não houver outro uso aprovado;
   - incluir `version` nas respostas de recursos mutáveis quando aplicável;
3. modelo relacional:
   - confirmar coluna de versão monotônica nos agregados mutáveis do novo fluxo;
   - preservar `DeviceSample.version` legado;
   - não adicionar versão a entidades imutáveis ou eventos sem justificativa;
4. interface:
   - manter versão recebida do servidor;
   - enviar `expected_version` ao salvar;
   - em conflito, informar o usuário e permitir recarregar/comparar antes de nova tentativa;
   - não sobrescrever silenciosamente alterações de outro usuário.

Essas atualizações são posteriores à validação e não foram executadas nesta atividade.

## 10. Questões que permanecem dependentes de outras decisões

- API02: formalização da chegada em comando único e salvamento progressivo posterior.
- API03: granularidade dos objetos e, consequentemente, qual agregado terá versão independente.
- API04: eventos de custódia e snapshot do estado.
- API07: idempotência, replay e ordem de processamento.
- API08: dados e vínculo da DeviceSample.
- API09: aceite repetido.
- API10: autorização e segregação de funções.
- Revisão do modelo relacional: confirmar quais novas entidades são mutáveis e quais terão versão persistida.
- Inspeção de migrações e banco-alvo: confirmar a implantação efetiva de `DeviceSample.version` e eventuais diferenças de schema.

## 11. Recomendação final

Adotar `expected_version` no corpo como mecanismo único para comandos novos que alteram recursos versionados. Manter `version` nas respostas, usar 409 `VERSION_CONFLICT` para estado desatualizado e não aceitar If-Match como mecanismo concorrente nesses contratos.

Para criação inicial do recebimento, utilizar bloqueio transacional da solicitação, unicidade persistente e idempotência; exigir `expected_version` da Solicitation somente se sua versão estiver formalmente definida e persistida. Para conferência/decisões progressivas, proteger o agregado individual efetivamente alterado. Para transferência e aceite, proteger a versão do CustodyObject.

Preservar os contratos legados sem alteração nesta decisão.

## 12. Controle de execução

**Realizado:** recuperação da decisão API06 na matriz vigente; inspeção estática do mixin de versão, schemas e serviços legados; comparação com o OpenAPI proposto; elaboração desta proposta documental.

**Não realizado:** alterações em código, modelos, banco, migrações, endpoints, frontend ou OpenAPI; testes, build, CI, validação automática ou consulta ao banco em execução.

**Situação:** proposta técnica elaborada; validação arquitetural/funcional e eventual aprovação institucional pendentes. Não há autorização de implementação.

## 13. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-10 | Primeira proposta de padronização do controle de concorrência para comandos novos e preservação do contrato legado. |
