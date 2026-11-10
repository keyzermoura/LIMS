# Proposta de Resolução API07 — Idempotência das Operações HTTP

**Identificador:** PROP-LIMS-API07-001  
**Versão:** 0.2  
**Situação:** Regras gerais validadas pelo responsável pelo projeto em revisão (2026-11-10); fechamento operacional, técnico e institucional pendente — implementação bloqueada  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Data:** 2026-11-10

---

## 1. Objetivo e limites

Definir uma política uniforme para identificar e reconhecer a repetição da mesma tentativa lógica de escrita, especialmente quando a resposta se perde após o servidor confirmar a transação.

O escopo abrange os contratos novos de recebimento, custódia, aceite e demais comandos que criem registros ou alterem estado de forma não repetível.

Esta é uma proposta documental. Não altera código, modelos, banco, migrações, endpoints, frontend ou OpenAPI e não autoriza implementação. Não foram executados testes, build, CI ou validação automática.

## 2. Problema e evidências atuais

A especificação funcional e o OpenAPI preliminar já mencionam o cabeçalho `Idempotency-Key`:

- obrigatório na formalização do recebimento;
- obrigatório no aceite;
- recomendado na transferência de custódia.

A especificação ainda não define escopo, formato, armazenamento, hash do conteúdo, retenção, resposta de replay ou conflito por reutilização com conteúdo diferente.

O OpenAPI usa respostas 409 genéricas que agrupam conflitos de estado, concorrência e idempotência. A matriz de decisões identifica API07 como bloqueadora.

A proposta API02 estabelece que:
- a formalização cria Receipt, ReceiptItems, objetos/eventos de custódia e auditoria em uma transação;
- uma repetição idêntica deve recuperar o resultado original;
- se já existir recebimento e não for replay reconhecido, deve retornar conflito sem criar outro.

A proposta API06 recomenda `expected_version` no corpo e 409 `VERSION_CONFLICT` para uma nova operação baseada em versão desatualizada. API07 deve ser processada em conjunto com API06.

## 3. Conceitos e distinções

- **Tentativa lógica:** uma intenção do cliente de executar uma operação uma única vez, mesmo que seja necessário transmitir a requisição mais de uma vez.
- **Chave idempotente:** identificador opaco enviado pelo cliente no cabeçalho `Idempotency-Key`.
- **Replay:** resposta equivalente à operação original, sem repetir seus efeitos.
- **Reutilização incompatível:** apresentação da mesma chave no mesmo escopo com conteúdo diferente.
- **Conflito de domínio:** operação diferente que não pode ocorrer porque o estado atual não permite, por exemplo, objeto já aceito.
- **Conflito de versão:** operação nova baseada em versão desatualizada, conforme API06.

Idempotência não substitui constraints, transações, controle de versão, autorização ou regras de domínio. Ela protege a repetição de uma tentativa lógica; não garante, sozinha, que duas tentativas distintas não produzam efeitos duplicados.

## 4. Alternativas avaliadas

### Alternativa A — Idempotência somente na interface

O frontend desabilita o botão após o primeiro clique e evita reenviar enquanto aguarda resposta.

**Não recomendada.** Não protege contra timeout, recarga, múltiplas abas, repetição por proxy, retry de rede, falha do aplicativo ou requisições concorrentes. O servidor deve ser a autoridade.

### Alternativa B — Chave idempotente persistida no servidor

O servidor recebe a chave, calcula a impressão digital do escopo e da requisição, registra o resultado e reconhece repetições.

**Recomendada.** Permite replay consistente após perda de resposta, coordena requisições concorrentes e mantém a lógica centralizada no backend.

### Alternativa C — Apenas constraints de negócio

Usar unicidade do recebimento por solicitação, vínculo único entre objeto e amostra e outras constraints para bloquear duplicidades.

**Insuficiente isoladamente.** Constraints são obrigatórias e devem continuar existindo, mas não permitem recuperar a resposta original de uma operação que foi confirmada e cuja resposta se perdeu. Também não distinguem necessariamente um retry legítimo de uma segunda tentativa diferente.

## 5. Política recomendada

Adotar a Alternativa B, complementada pelas constraints de domínio da Alternativa C.

### 5.1 Cabeçalho e formato

Usar o cabeçalho:

`Idempotency-Key: <valor-opaco>`

Regras propostas:

- obrigatório em todos os comandos novos de criação de recebimento, transferência de custódia e aceite;
- obrigatório também em futuros comandos POST/PUT/PATCH que registrem eventos, decisões, regularizações ou outras alterações não repetíveis;
- não exigido em GET/HEAD sem efeito colateral;
- valor opaco, gerado pelo cliente com alta entropia; UUID v4 é formato recomendado para o frontend;
- comprimento aceito: 16 a 128 caracteres ASCII visíveis, sem espaços de controle;
- não conter nome, CPF, e-mail, número de protocolo ou outro dado pessoal/semântico;
- o cliente deve gerar uma chave nova para cada nova intenção de operação;
- em retry da mesma intenção, deve reutilizar exatamente a chave original e o mesmo conteúdo.

A chave não deve ser criada pelo servidor após receber a requisição, pois o cliente precisa conhecê-la para repetir com segurança a mesma tentativa.

### 5.2 Escopo de unicidade

A chave deve ser única dentro do seguinte escopo lógico:

`principal_autenticado + método_HTTP + rota_normalizada + recurso_alvo + Idempotency-Key`

O escopo deve considerar a versão da API e os identificadores de recurso do path. O principal autenticado deve ser vinculado à chave para impedir que outro usuário recupere a resposta de uma operação alheia.

A mesma sequência de chave pode ser usada em operações distintas ou por principais distintos sem colisão, pois o escopo é diferente. Ainda assim, recomenda-se gerar uma chave nova para cada tentativa lógica.

A unicidade deve ser garantida no banco por constraint/índice persistente equivalente. Não depender de cache local, memória do processo ou sessão do navegador.

### 5.3 Impressão digital da requisição

Para cada chave, calcular e persistir um hash criptográfico da requisição normalizada.

A impressão digital deve considerar:
- método HTTP;
- rota normalizada e parâmetros de path;
- versão da API;
- corpo JSON após normalização canônica;
- parâmetros de query que alterem a semântica da operação, se houver.

Não deve considerar:
- token Authorization;
- X-Request-ID/correlation ID;
- cabeçalhos de transporte;
- timestamps de envio gerados pelo cliente que não pertençam ao conteúdo de negócio.

O campo `expected_version` faz parte do corpo e, portanto, integra o hash. Uma tentativa com a mesma chave e versão/corpo diferente não é o mesmo pedido.

Usar SHA-256 ou algoritmo equivalente aprovado para a impressão digital. A chave original não precisa ser armazenada em texto puro: recomenda-se persistir seu hash/digest, desde que a comparação e a unicidade sejam seguras. Não registrar a chave original em logs.

## 6. Persistência e ciclo de vida

Recomenda-se uma entidade/tabela técnica de idempotência, sem substituir as tabelas de domínio ou a auditoria.

Campos lógicos candidatos:

| Campo | Regra/uso |
|---|---|
| id | PK técnica. |
| principal_id | Identidade autenticada que originou a operação. |
| api_version | Versão do contrato, por exemplo v1. |
| http_method | Método normalizado. |
| route_scope | Rota normalizada e escopo do recurso-alvo. |
| key_digest | Digest da chave; único dentro do escopo. |
| request_hash | Hash da requisição canônica. |
| status | IN_PROGRESS ou COMPLETED, conforme estratégia transacional escolhida. |
| response_status | Status HTTP original concluído. |
| response_body | Snapshot JSON mínimo necessário ao replay, com proteção de dados. |
| response_headers | Lista permitida de cabeçalhos relevantes, nunca tokens/segredos. |
| resource_type / resource_id | Referência ao recurso principal criado/alterado, quando aplicável. |
| created_at | Início/registro da tentativa. |
| completed_at | Momento da conclusão. |
| replay_expires_at | Fim da janela de replay exato. |
| tombstone_until / retention_class | Política de retenção do marcador após expirar o corpo, conforme política institucional. |

Os nomes são lógicos e não determinam nomes físicos.

### 6.1 Atomicidade

Para operações de domínio, a gravação do resultado idempotente e os efeitos de negócio devem ser coordenados transacionalmente.

Regra essencial: não pode existir resposta marcada como concluída sem que os efeitos de negócio correspondentes estejam confirmados; tampouco pode haver efeito confirmado sem registro suficiente para reconhecer a repetição.

Estratégia preferencial a avaliar:
1. abrir transação;
2. reservar/inserir a chave no escopo único;
3. validar hash e estado;
4. executar a operação de domínio;
5. persistir resultado/status/corpo de resposta e referência do recurso;
6. confirmar efeitos de negócio e resultado idempotente na mesma transação.

Uma requisição concorrente com a mesma chave deve aguardar a resolução da primeira transação ou receber resposta transitória definida pelo contrato. A constraint única é a salvaguarda final contra duas execuções simultâneas.

Se a transação inicial for revertida antes do commit, não deve permanecer operação concluída nem efeito parcial; a mesma chave poderá ser tentada novamente, desde que o hash seja o mesmo.

A estratégia concreta para representar IN_PROGRESS, bloqueios, timeout de espera e recuperação após falha do processo deve ser definida no desenho técnico. Não manter uma reserva IN_PROGRESS abandonada indefinidamente: se houver reserva fora da transação de negócio, deverá existir lease, recuperação e auditoria explícitos.

### 6.2 Replay do resultado

Quando chegar uma requisição com chave já concluída e hash idêntico:
- não executar novamente a operação de domínio;
- não criar outro Receipt, evento, transferência, aceite, DeviceSample ou assinatura;
- retornar o status HTTP original e o corpo persistido da resposta;
- retornar somente cabeçalhos de resposta permitidos e estáveis;
- indicar, se adotado, que a resposta é replay, sem alterar a semântica do corpo.

O replay não deve recalcular a resposta a partir do estado corrente se isso puder produzir conteúdo diferente do resultado original. O snapshot armazenado deve ser mínimo e protegido; pode conter identificadores e dados necessários à resposta original, sem armazenar tokens ou segredos.

Antes de revelar o snapshot, o servidor deve autenticar e revalidar a autorização atual do principal para acessar a operação/recurso. A chave não pode funcionar como credencial de acesso. Se a autorização tiver sido revogada, responder conforme política de segurança, sem expor o corpo armazenado.

## 7. Comportamentos normativos por cenário

| Cenário | Comportamento proposto |
|---|---|
| Primeira requisição, chave nova e válida | Executar normalmente; persistir resultado idempotente junto com a transação. |
| Mesma chave, mesmo escopo e mesmo hash, operação concluída | Replay do status e corpo originais; nenhum efeito adicional. |
| Mesma chave e mesmo hash enquanto a primeira requisição ainda está em processamento | Aguardar a primeira transação por intervalo limitado; se não for possível concluir a espera, responder conflito transitório com código específico e orientação de retry usando a mesma chave. |
| Mesma chave no mesmo escopo, mas hash diferente | HTTP 409 `IDEMPOTENCY_KEY_REUSED`; não executar a segunda requisição. |
| Chave ausente em operação que a exige | HTTP 400 ou 422 conforme convenção geral aprovada; recomenda-se 400 `IDEMPOTENCY_KEY_REQUIRED`, por ser ausência de cabeçalho obrigatório. |
| Chave malformada | HTTP 400 `INVALID_IDEMPOTENCY_KEY`. |
| Falha transitória antes do commit (ex. rollback/erro interno) | Não marcar como concluída; nenhuma alteração parcial. A mesma chave e conteúdo podem ser reenviados. |
| Erro de domínio terminal após a requisição ser admitida e processada | Persistir o resultado terminal para replay consistente, desde que a transação não tenha efeitos parciais. Nova tentativa lógica, após mudança de estado/dados, usa nova chave. |
| Mesmo conteúdo, mas nova chave | Nova tentativa lógica; aplicar regras de estado, unicidade e versão. Não presumir replay. |
| Requisição idêntica após expirar a janela de replay | Não reexecutar automaticamente; responder `IDEMPOTENCY_KEY_EXPIRED` se o marcador ainda existir. O cliente deve consultar o recurso e iniciar nova operação somente após verificar o estado. |
| Chave desconhecida depois de a retenção do marcador terminar | As constraints de domínio continuam obrigatórias; a política de retenção deve evitar que uma chave antiga volte a ser aceita inadvertidamente. |

## 8. Códigos HTTP e envelope de erro

Códigos propostos:

| HTTP | Código | Significado |
|---:|---|---|
| 400 | `IDEMPOTENCY_KEY_REQUIRED` | Cabeçalho obrigatório ausente. |
| 400 | `INVALID_IDEMPOTENCY_KEY` | Formato inválido. |
| 409 | `IDEMPOTENCY_KEY_REUSED` | Mesma chave e escopo com conteúdo diferente. |
| 409 | `IDEMPOTENCY_REQUEST_IN_PROGRESS` | Primeira tentativa ainda está sendo processada; repetir com a mesma chave após aguardar. |
| 409 | `IDEMPOTENCY_KEY_EXPIRED` | Janela de replay terminou; não executar novamente com a chave antiga. |
| 409 | `VERSION_CONFLICT` | Nova tentativa lógica com versão desatualizada, conforme API06. |
| 409 | Código de conflito de domínio | Estado atual impede nova operação, por exemplo objeto já aceito; API09 define resposta específica. |

Para `IDEMPOTENCY_REQUEST_IN_PROGRESS`, pode ser enviado `Retry-After` com intervalo curto, se suportado pela infraestrutura. Esse cabeçalho não autoriza gerar uma chave nova.

Exemplo de erro por reutilização incompatível:

~~~json
{
  "error": {
    "code": "IDEMPOTENCY_KEY_REUSED",
    "message": "A chave de idempotência já foi utilizada com conteúdo diferente.",
    "details": {
      "retry_with_same_key": false
    },
    "request_id": "correlation-id"
  }
}
~~~

Exemplo de processamento ainda em curso:

~~~json
{
  "error": {
    "code": "IDEMPOTENCY_REQUEST_IN_PROGRESS",
    "message": "A operação associada a esta chave ainda está sendo processada.",
    "details": {
      "retry_with_same_key": true
    },
    "request_id": "correlation-id"
  }
}
~~~

As respostas de erro não devem revelar hash interno, digest da chave, conteúdo sensível ou detalhes de SQL.

## 9. Retenção e privacidade

Recomendação preliminar:

1. Manter o snapshot necessário ao replay exato por **7 dias corridos** após a conclusão.
2. Após a janela, não reexecutar a chave antiga. Se o marcador for mantido, responder `IDEMPOTENCY_KEY_EXPIRED`.
3. Preservar um marcador mínimo (escopo, digest da chave, hash da requisição, referência do recurso e datas) pelo prazo definido na política institucional de retenção/auditoria, evitando reutilização inadvertida.
4. O prazo de 7 dias é uma proposta operacional, não requisito normativo ou decisão institucional; deve ser validado por segurança, governança documental e responsável funcional.
5. Aplicar controle de acesso, criptografia em repouso quando disponível, minimização de dados e política de descarte ao snapshot.
6. Nunca armazenar Authorization, cookies, tokens de assinatura, segredos ou cabeçalhos completos.
7. Não incluir a chave original nem dados completos de requisição em logs. Registrar digest, escopo, status, request_id e referências técnicas suficientes para auditoria.

A retenção do marcador e a retenção do corpo de resposta são conceitos distintos. Expirar o snapshot não deve significar aceitar silenciosamente a mesma chave como uma nova operação.

## 10. Aplicação aos fluxos LIMS

### 10.1 Registrar chegada/recebimento

- Chave obrigatória.
- Escopo inclui principal autenticado, POST, rota de recebimento e solicitation_id.
- Mesmo conteúdo e chave após commit: replay do 201 original, sem novo Receipt, ReceiptItem, CustodyObject ou evento inicial.
- Mesmo chave com itens/quantidades/horário/local diferentes: 409 `IDEMPOTENCY_KEY_REUSED`.
- Nova chave quando já existe Receipt: conflito de domínio com referência ao recebimento existente; nunca criar segundo Receipt.
- Constraint única de Receipt por Solicitation permanece obrigatória.

### 10.2 Transferir custódia

- Chave obrigatória, e não apenas recomendada.
- Escopo inclui principal, POST, rota e custody_object_id.
- Replay da mesma transferência retorna o resultado original sem inserir segundo evento nem incrementar a versão novamente.
- Uma nova chave representa uma nova intenção; deve passar pela validação de `expected_version` (API06) e das regras de estado.
- A cadeia de custódia permanece append-only e protegida por integridade referencial.

### 10.3 Aceitar objeto e criar DeviceSample

- Chave obrigatória.
- Escopo inclui principal, POST, rota e custody_object_id.
- Replay da mesma operação retorna a resposta original e não cria segunda DeviceSample, assinatura ou evento.
- Chave diferente para objeto já aceito não é replay. O comportamento de domínio (retornar amostra existente ou conflito) pertence à API09.
- A relação CustodyObject–DeviceSample e a criação atômica continuam protegidas por constraint de unicidade e transação.

### 10.4 Conferência, pendências e decisões progressivas

Todo comando novo que crie evidência, pendência, regularização ou decisão deve ter chave obrigatória se puder gerar registro/evento não repetível. Atualizações idempotentes de estado também devem usar chave quando o retry puder produzir efeitos acessórios (auditoria, assinatura, notificação ou evento).

A granularidade do escopo deve acompanhar o recurso-alvo (por exemplo ReceiptItem ou CustodyObject), conforme API03 e API06.

## 11. Ordem de processamento com API06 e API09

Para uma chave previamente concluída, o reconhecimento do replay deve ocorrer antes da validação de `expected_version`. Caso contrário, um retry legítimo de uma operação já confirmada seria rejeitado porque a primeira execução incrementou a versão.

Ordem lógica proposta:

1. autenticar o principal;
2. validar formato e presença da chave;
3. determinar escopo e calcular hash da requisição;
4. procurar/reservar a chave com garantia de unicidade;
5. se concluída e hash idêntico, revalidar autorização para revelar o resultado e executar replay;
6. se hash divergente, retornar `IDEMPOTENCY_KEY_REUSED`;
7. se em processamento, aguardar ou retornar `IDEMPOTENCY_REQUEST_IN_PROGRESS`;
8. somente para uma nova tentativa lógica, validar `expected_version`, estado e regras de domínio;
9. executar a operação e persistir efeitos + resultado idempotente atomicamente;
10. responder com o resultado concluído.

API09 continua necessária para definir o comportamento de uma nova chave quando o objeto já foi aceito. Idempotência não resolve essa regra semântica.

## 12. Impactos documentais após validação

Após aprovação, atualizar coordenadamente:

- especificação funcional da API: tornar Idempotency-Key obrigatória para transferência e demais comandos críticos; definir escopo, replay, erros e retenção;
- OpenAPI: descrever formato, obrigatoriedade por operação, respostas 409 específicas, Retry-After quando aplicável e cabeçalhos de replay se aprovados;
- modelo relacional: incluir entidade técnica/constraint de idempotência, política de snapshot e retenção;
- frontend: gerar chave por tentativa lógica, mantê-la durante retries, descartá-la ao iniciar nova intenção e não gerar outra chave automaticamente após timeout;
- observabilidade: correlação e métricas sem expor a chave original nem payload sensível;
- política de segurança e retenção: validar minimização, acesso e descarte.

Não foram realizadas essas atualizações nesta atividade.

## 13. Dependências e questões em aberto

- API06: ordem de verificação da chave e da versão; a proposta define replay antes de validar a versão para operações já concluídas.
- API09: nova chave para objeto já aceito.
- API10: autorização atual antes de revelar resposta armazenada.
- API03: granularidade do escopo por item/objeto.
- Política institucional de retenção: validar janela de replay de 7 dias e retenção do marcador.
- Arquitetura de persistência: definir transação, concorrência, bloqueios, timeout e recuperação de IN_PROGRESS.
- Segurança: aprovar formato, digest, proteção do snapshot e gestão de dados.
- Observabilidade: definir métricas e política de logs.

## 14. Recomendação final

Adotar Idempotency-Key obrigatória nos comandos novos que criem recebimentos, eventos de custódia, aceites e decisões/regularizações não repetíveis. Persistir o resultado de forma transacional, com unicidade por principal + operação/rota + recurso-alvo + chave, hash canônico do conteúdo e replay do status/corpo original.

A mesma chave e o mesmo conteúdo devem reproduzir o resultado original sem efeitos adicionais. A mesma chave com conteúdo diferente deve retornar 409 `IDEMPOTENCY_KEY_REUSED`. A repetição durante processamento deve aguardar ou retornar 409 `IDEMPOTENCY_REQUEST_IN_PROGRESS`. A janela preliminar de replay exato é de 7 dias; após isso, não reexecutar a chave antiga, preservando marcador mínimo conforme política institucional.

Manter constraints de domínio, transações e controle de versão API06 como salvaguardas independentes. Preservar integralmente as rotas e contratos legados nesta decisão.

## 15. Controle de execução

**Realizado:** recuperação da decisão API07 na matriz vigente; análise da especificação de API, OpenAPI, proposta API02, proposta API06 e modelo relacional; elaboração da proposta e registro da validação das regras gerais pelo responsável pelo projeto em revisão em 2026-11-10.

**Não realizado:** alterações em código, modelos, banco, migrações, endpoints, frontend, especificação funcional ou OpenAPI; testes, build, CI ou validação automática.

**Pendências de fechamento:** definir transação, reserva/estado IN_PROGRESS, bloqueios, timeout e recuperação; validar janela de 7 dias e retenção do marcador; fechar segurança e proteção do snapshot; resolver API09 (nova chave para objeto já aceito), API10 (autorização), API03 (granularidade) e compatibilidade runtime; obter aprovação institucional aplicável.

**Situação:** regras gerais validadas em revisão do projeto; fechamento operacional, técnico e institucional pendente. Não há autorização de implementação.

## 16. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-10 | Primeira proposta de política de idempotência, persistência, replay, retenção e compatibilidade com API06/API09. |
| 0.2 | 2026-11-10 | Registro da validação das regras gerais pelo responsável pelo projeto em revisão; detalhes operacionais, retenção, segurança, dependências e aprovação institucional permanecem pendentes. |
