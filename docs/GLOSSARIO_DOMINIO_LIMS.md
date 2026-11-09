# Glossário do Domínio LIMS

**Identificador:** GLO-DOM-001  
**Versão:** 1.0  
**Situação:** Proposta de glossário para revisão funcional  
**Repositório:** `keyzermoura/LIMS`  
**Branch:** `main`  
**Data:** 2026-11-09

---

## 1. Objetivo

Estabelecer uma linguagem comum para os conceitos utilizados no LIMS, especialmente no fluxo de solicitação, chegada física, recebimento, conferência, aceite e encaminhamento de materiais para atividades laboratoriais.

Este glossário é um artefato de análise e alinhamento. Não autoriza implementação nem substitui decisões institucionais ainda pendentes.

## 2. Regras de interpretação

- **Conceito funcional:** termo utilizado para descrever o processo institucional, independentemente da estrutura atual do código.
- **Entidade de software:** registro persistido que poderá representar um conceito funcional. A existência e o nome definitivo da entidade dependem do modelo de domínio aprovado.
- **Termo aprovado:** definição já respaldada por decisão expressa no desenho funcional ou por orientação do responsável pelo projeto.
- **Termo proposto:** definição de trabalho que precisa de revisão antes de ser tratada como requisito definitivo.
- Os nomes de classes apresentados entre crases são referências ao código atual ou sugestões conceituais; não representam autorização para criar ou renomear classes.

## 3. Glossário

| Termo | Definição de trabalho | Distinções e observações | Situação |
|---|---|---|---|
| **Solicitante** | Pessoa, órgão ou instituição que demanda a avaliação laboratorial ou serviço. | Na primeira entrega, o cadastro é realizado por usuário interno em nome do solicitante; não há portal externo previsto. | Aprovado no escopo inicial |
| **Solicitação** | Registro administrativo que formaliza a demanda e identifica o solicitante, o contexto e os itens cuja avaliação é requerida. | Não equivale ao recebimento físico nem à amostra operacional. Uma solicitação pode relacionar vários itens, conforme decisão funcional mais recente, ainda sujeita à consolidação da DEC-001. | Definição funcional aprovada; cardinalidade em consolidação |
| **Item declarado** | Cada produto, dispositivo ou conjunto de unidades informado na solicitação como objeto da demanda. | Representa o que foi declarado, não necessariamente o que chegou fisicamente. Deve permanecer rastreável mesmo se não for apresentado. | Aprovado conceitualmente |
| **Unidade física** | Unidade individual materialmente apresentada ao laboratório. | Pode corresponder a uma unidade comercial, embalagem ou exemplar, conforme o tipo de dispositivo e o procedimento de recebimento. A regra de contagem deve ser definida por categoria de produto. | Proposto; requer regra por tipo |
| **Chegada física** | Evento em que o material e/ou documentação chegam ao local institucional de recebimento. | Marca o início da custódia física, mesmo que ainda não exista uma amostra operacional no LIMS. Deve preservar data, hora e responsável efetivo pela recepção. | Aprovado conceitualmente |
| **Recebimento** | Registro formal da chegada física associada à solicitação, com dados gerais, conferência e rastreabilidade. | Foi decidido um único registro principal de recebimento por solicitação. Não deve ser confundido com a criação da amostra. | Aprovado conceitualmente |
| **Item de recebimento** | Representação, dentro do recebimento, da situação de apresentação e conferência de cada item declarado. | Permite registrar apresentado, não apresentado, pendente, aceito ou recusado conforme dimensões distintas; não se deve misturar estado de apresentação com decisão técnica. | Proposta de entidade; regras conceituais aprovadas |
| **Conferência** | Verificação administrativa e física do item apresentado, segundo critérios e checklist aplicáveis. | Deve registrar executor, data/hora, resultado, observações, justificativas e evidências, quando aplicável. | Aprovado conceitualmente |
| **Checklist de recebimento** | Conjunto versionado de verificações aplicáveis à conferência de um item. | Deve permitir identificar quais critérios foram avaliados e quais evidências sustentam a conclusão. O catálogo e a versionamento ainda serão especificados. | Proposto |
| **Evidência** | Documento, imagem, arquivo ou outro registro que sustenta uma informação, conferência ou decisão. | Deve ter vínculo explícito com a etapa/item correspondente, autoria, data/hora, integridade, acesso e política de retenção. | Aprovado conceitualmente; requisitos técnicos pendentes |
| **Não apresentado** | Situação em que um item declarado não foi fisicamente entregue na chegada registrada. | Não significa recusa técnica, não inicia custódia daquele item e não gera amostra operacional. A entrega posterior não pode ser registrada retroativamente como se tivesse ocorrido na chegada original. | Aprovado |
| **Pendência** | Condição que impede a conclusão do recebimento ou aceite do item até que informação, documento ou condição exigida seja regularizada. | A regularização deve ocorrer no mesmo recebimento quando permitida, preservando histórico das avaliações anteriores. | Aprovado conceitualmente |
| **Aceite** | Decisão formal de que o item cumpriu os requisitos necessários para ser admitido no fluxo laboratorial. | Deve ser individual por item e respeitar validações obrigatórias. O aceite não é sinônimo de resultado analítico aprovado. | Aprovado conceitualmente |
| **Recusa** | Decisão formal de não admitir o item no fluxo laboratorial, com fundamento e rastreabilidade. | É distinta de “não apresentado” e de reprovação em ensaio. | Aprovado conceitualmente |
| **Validação da coordenação** | Etapa de revisão/validação por autoridade ou função de coordenação, quando exigida pelo fluxo. | Não pode dispensar critérios impeditivos nem substituir evidências obrigatórias. | Aprovado conceitualmente; matriz de permissões pendente |
| **Custódia** | Responsabilidade documentada pela guarda, localização e transferência do material sob controle institucional. | Inicia na chegada física, antes da criação da amostra operacional. Eventos devem preservar responsáveis, local, data/hora e motivo. | Aprovado conceitualmente |
| **Amostra operacional** | Registro institucional individual criado após o aceite final e as validações obrigatórias, para controlar o material no ciclo laboratorial. | No código atual, o conceito é representado por `DeviceSample`. A compatibilidade e a evolução desse modelo serão definidas na estratégia de migração. | Conceito aprovado; desenho técnico pendente |
| **Identificador institucional** | Código único atribuído pelo LIMS a cada amostra operacional aceita. | Não depende da existência de número Harpya. A referência Harpya, quando existente, é externa e complementar. O formato final ainda não foi aprovado. | Aprovado conceitualmente; formato pendente |
| **Número Harpya** | Identificador externo informado pela vigilância sanitária quando aplicável. | Não substitui a chave primária nem o identificador institucional do LIMS. | Aprovado |
| **Referência externa** | Código originado em sistema ou processo externo, associado à solicitação ou ao item/amostra conforme sua natureza. | Deve ser opcional e não deve ser usado como chave primária do LIMS. | Aprovado conceitualmente |
| **Protocolo local** | Código complementar utilizado por laboratório, setor ou processo interno para organização e rastreamento. | Não substitui o identificador institucional único da amostra. | Aprovado conceitualmente |
| **Ensaio** | Atividade técnica planejada e executada para avaliar uma amostra segundo método e critérios definidos. | No código atual, é representado principalmente por `LabTest`; a separação entre catálogo, planejamento, execução, dados brutos e revisão será avaliada. | Conceito existente; refinamento pendente |
| **Resultado de ensaio** | Dado ou conclusão produzido pela execução de um ensaio. | O código atual mantém estado corrente em `LabTest` e versões históricas em `LabTestResult`. Resultado analítico não se confunde com decisão de aceite do recebimento. | Conceito existente |
| **Corpo de prova** | Porção, unidade ou espécime preparado/selecionado para a execução de um ensaio específico. | Pode derivar de uma amostra operacional e pode exigir rastreabilidade própria; não deve ser tratado automaticamente como sinônimo de amostra ou item declarado. | Proposto; requer definição por ensaio |
| **Cadeia de custódia** | Histórico cronológico e íntegro dos eventos de guarda, movimentação e transferência de responsabilidade. | No código atual, `ChainOfCustody` depende diretamente de `DeviceSample`; o período anterior à criação da amostra ainda precisa de representação no novo domínio. | Conceito aprovado; arquitetura pendente |
| **Trilha de auditoria** | Registro cronológico das ações relevantes, com ator, data/hora, entidade, ação e dados necessários à reconstrução. | No código atual, representada por `AuditLog`; a cobertura das novas entidades deverá ser definida. | Conceito existente |
| **Assinatura eletrônica** | Manifestação eletrônica atribuída a usuário identificado, vinculada a conteúdo/ação e com significado declarado. | O modelo atual registra snapshots e manifesto; os requisitos institucionais e a validação de uso permanecem pendentes. | Conceito existente; validação pendente |
| **Regularização** | Ação que supre uma pendência identificada durante o recebimento. | Deve preservar o histórico, a autoria e os horários das avaliações e alterações, sem apagar o estado anterior. | Aprovado conceitualmente |
| **Exceção institucional** | Tratamento formalmente autorizado para situação que não pode ser resolvida pelas regras ordinárias do fluxo. | Não deve ser usada para contornar critérios impeditivos sem autoridade, justificativa, escopo e auditoria definidos. | Proposto; governança pendente |

## 4. Distinções fundamentais do domínio

### 4.1 Item declarado × unidade física

O item declarado expressa o objeto da demanda. A unidade física expressa o que efetivamente chegou. Um item declarado pode representar mais de uma unidade física; a regra de correspondência precisa ser definida conforme o tipo de produto e a solicitação.

### 4.2 Recebimento × amostra operacional

O recebimento documenta a chegada e a conferência. A amostra operacional é criada somente depois do aceite final e das validações obrigatórias. A data/hora de chegada e o recebedor físico original devem ser preservados, mesmo que o registro da amostra seja criado posteriormente.

### 4.3 Não apresentado × recusado × pendente

- **Não apresentado:** o item declarado não chegou fisicamente.
- **Recusado:** o item foi apresentado, mas houve decisão formal de não admiti-lo.
- **Pendente:** o item foi apresentado, mas falta requisito ou regularização para concluir a decisão.

Essas situações não devem ser representadas como um único campo de status sem preservar a dimensão a que cada estado pertence.

### 4.4 Aceite de recebimento × resultado analítico

O aceite verifica se o item pode ingressar no fluxo laboratorial. O resultado analítico expressa a conclusão de um ou mais ensaios. Um item aceito pode posteriormente apresentar resultado reprovado, sem que isso altere retroativamente a decisão de recebimento.

### 4.5 Identificador institucional × referência externa

O identificador institucional é atribuído pelo LIMS à amostra operacional. Número Harpya e outras referências externas são identificadores complementares e podem não existir para todos os casos.

## 5. Termos que exigem decisão antes da modelagem

1. **Item declarado e unidade física:** definir quando um item representa uma unidade, um conjunto ou múltiplas unidades.
2. **Amostra operacional e corpo de prova:** definir quando haverá um ou vários corpos de prova por amostra e se algum exige identificador próprio.
3. **Identificador institucional:** definir formato visual, política de sequência e apresentação em documentos/QR Code, preservando a unicidade técnica.
4. **Referências externas:** decidir em quais níveis podem ser associadas (solicitação, item declarado, unidade física ou amostra).
5. **Exceções de recebimento:** definir autoridade, justificativa, limites e trilha de aprovação para entregas posteriores ou situações excepcionais.
6. **Catálogo de checklist:** definir critérios por categoria de dispositivo, versão e vigência.
7. **Estados:** consolidar nomes, transições permitidas, permissões e eventos auditáveis na especificação de estados.

## 6. Relação com outros documentos

- `ETAPA_1_DESENHO_TECNICO_SOLICITACAO_RECEBIMENTO.md`: fluxo funcional de solicitação e recebimento.
- `MATRIZ_LACUNAS_ARQUITETURAIS_LIMS.md`: lacunas entre o sistema atual e o escopo pretendido.
- `PLANO_DIRETOR_PROJETO_LIMS.md`: fases, portões e governança do projeto.
- `INVENTARIO_TECNICO_FASE_0_1.md`: estrutura técnica, modelos, migrações e CI observados.

Em caso de divergência, decisões formalmente aprovadas e registradas prevalecem sobre definições provisórias deste glossário. Divergências devem ser encaminhadas à matriz de decisões, sem resolução por inferência.

## 7. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 1.0 | 2026-11-09 | Primeira versão do glossário de domínio para revisão funcional. |
