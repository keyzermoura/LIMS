# Proposta de Resolução API08 — Payload mínimo e identidade da DeviceSample por classe de material

**Identificador:** PROP-LIMS-API08-001  
**Versão:** 0.2  
**Situação:** Regras gerais validadas pelo responsável pelo projeto em revisão (2026-11-09); fechamento funcional/técnico e aprovação institucional pendentes — implementação bloqueada  
**Repositório:** keyzermoura/LIMS  
**Branch:** main  
**Data:** 2026-11-10

---

## 1. Objetivo e limites

Definir uma política de identificação e um payload mínimo para a criação de `DeviceSample` no novo fluxo de recebimento e aceite, considerando que o laboratório recebe classes distintas de dispositivos médicos e que nem todas possuem número de série individual.

A proposta busca equilibrar:
- rastreabilidade metrológica e laboratorial;
- identificação suficiente do material submetido a ensaio;
- compatibilidade com o fluxo de solicitação, recebimento e `CustodyObject`;
- preservação dos registros e contratos legados;
- ausência de valores artificiais usados apenas para satisfazer campos obrigatórios.

Esta é uma proposta documental. Não altera código, modelos SQLAlchemy, banco, migrações Alembic, endpoints, frontend ou OpenAPI. Não foram executados testes, build, CI ou validação automática. Não há autorização de implementação.

## 2. Evidências e situação atual

A inspeção estática registrada em `INV-TEC-001` e na especificação de contratos identificou que:

- `DeviceSample` representa atualmente a amostra operacional e possui `accession_number`, identidade do dispositivo, status, recebimento e custódia atual;
- o schema legado `SampleCreate` exige `serial_number`, `lot_number`, `manufacturer`, `commercial_name` e `storage_location`;
- o serviço legado verifica duplicidade pela combinação serial + lote + fabricante;
- há uma restrição única composta associada a serial, lote e fabricante;
- a criação legada gera `accession_number`, evento inicial de custódia, assinatura e auditoria;
- não há evidência de que o ambiente implantado ou o banco-alvo tenham sido inspecionados nesta proposta.

A combinação serial + lote + fabricante não é uma chave universal de identidade para todos os dispositivos. Ela pode rejeitar registros legítimos de materiais sem serial individual, bem como confundir unidades/agrupamentos que exigem rastreabilidade operacional independente.

A proposta API03/DEC05 distingue `ItemDeclarado`, `ItemRecebimento`, `ObjetoCustodia` e `DeviceSample`. Portanto, a identidade da amostra operacional não deve ser confundida com a descrição declarada pelo solicitante nem com a identidade de cada unidade física.

## 3. Princípios de modelagem

1. **Amostra operacional não é sinônimo de unidade física.** Sua granularidade decorre do agrupamento de `CustodyObject` aprovado conforme API03/DEC05.
2. **Serial não é universal.** Número de série individual só deve ser exigido quando a classe/material efetivamente possuir serial aplicável e o procedimento exigir sua captura.
3. **Lote é condicional à aplicabilidade.** Quando o produto for identificado por lote, o lote deve ser capturado. Não se deve inventar lote ou usar texto genérico como “N/A”.
4. **Fabricante e nome comercial são dados de identificação relevantes.** Devem estar preenchidos para uma amostra aceita, admitindo-se pendência controlada durante a conferência quando a informação ainda não puder ser confirmada.
5. **Classe de material deve ser explícita.** A classe controla validações condicionais e não deve ser inferida exclusivamente do nome comercial.
6. **Atributos específicos não devem ser forçados em campos universais.** Calibre, dimensões, modelo, tipo de conexão e outras características dependem da classe e do ensaio.
7. **Localização física pertence à custódia.** `storage_location` não deve ser tratado como atributo imutável da identidade do dispositivo; localização atual deve ser representada pelo estado/evento de custódia.
8. **Dados declarados e dados confirmados devem ser distinguíveis.** A informação inicialmente fornecida pode ser corrigida/confirmada durante a conferência, preservando autoria, histórico e evidência.
9. **O identificador institucional da amostra permanece independente.** `accession_number` continua sendo o identificador operacional emitido pelo LIMS; não deve ser substituído por serial, lote ou identificador do fabricante.
10. **Compatibilidade legada é requisito.** A proposta não autoriza tornar campos legados nulos, remover constraints ou alterar o comportamento de rotas existentes sem revisão e migração aprovadas.

## 4. Alternativas avaliadas

### Alternativa A — Manter todos os campos atuais obrigatórios

Manter `serial_number`, `lot_number`, `manufacturer`, `commercial_name` e `storage_location` obrigatórios para todas as amostras.

**Não recomendada para o novo fluxo.** Exige serial mesmo quando inexistente/não aplicável e mistura localização operacional com identidade. Pode incentivar valores fictícios e rejeitar materiais legítimos.

### Alternativa B — Tornar todos os campos de identidade opcionais

Permitir a criação de amostra com identidade incompleta, sem regras por classe.

**Não recomendada.** Enfraquece rastreabilidade e pode gerar amostras aceitas sem fabricante, descrição ou identificadores de lote aplicáveis.

### Alternativa C — Identidade comum mínima com validações condicionais por classe

Adotar uma base comum de identificação e regras condicionais explícitas para serial, lote e atributos técnicos, com validação antes do aceite.

**Recomendada.** Permite representar materiais sem serial individual sem perder rastreabilidade e evita impor atributos específicos a todas as classes.

## 5. Identidade mínima proposta

### 5.1 Campos comuns da amostra operacional

| Campo lógico | Regra proposta para amostra aceita | Observação |
|---|---|---|
| `accession_number` | Obrigatório, gerado pelo LIMS | Identificador institucional único; preservar formato e QR legado. |
| `device_class` | Obrigatório | Classe controlada, por exemplo agulha, seringa, equipo, cateter ou outra classe cadastrada. |
| `manufacturer` | Obrigatório | Fabricante confirmado; não confundir com distribuidor/fornecedor. |
| `commercial_name` | Obrigatório | Nome comercial ou descrição padronizada suficiente para identificar o produto. |
| `lot_number` | Obrigatório quando aplicável à classe/produto | Quando não aplicável, registrar condição estruturada e justificativa; não usar texto fictício. |
| `serial_number` | Obrigatório somente quando aplicável e exigido | Nulo quando não existir ou não for aplicável; não preencher com “N/A”, zero ou número inventado. |
| `model_reference` | Condicional | Modelo/referência do fabricante, quando disponível ou necessário para distinguir o produto. |
| `manufacturer_catalog_code` | Condicional | Código de catálogo/referência comercial do fabricante, quando existente. |
| `identification_notes` | Opcional e complementar | Não substitui campos estruturados obrigatórios nem evidências. |

Os nomes acima são nomes lógicos candidatos, não nomes físicos aprovados de colunas ou propriedades.

### 5.2 Campos que não devem compor a identidade universal

- `storage_location`: dado de custódia/localização, não identificador permanente do dispositivo.
- `received_at` e `received_by_id`: dados do evento de chegada, preservados a partir de `Receipt.arrived_at` e do recebedor físico real.
- `accession_number`: identificador institucional da amostra, não atributo comercial do produto.
- quantidade recebida: pertence ao item/objeto de recebimento e às regras de agrupamento API03; não deve ser usada isoladamente como identidade do produto.

## 6. Regras condicionais por classe de material

A classe deve ser selecionada de catálogo controlado. A tabela a seguir é uma matriz inicial de aplicabilidade, sujeita à validação do responsável técnico/laboratorial e dos procedimentos de ensaio.

| Classe | Fabricante | Nome comercial/descrição | Lote | Serial individual | Atributos específicos possíveis |
|---|---|---|---|---|---|
| Agulha | Obrigatório | Obrigatório | Obrigatório quando informado/aplicável ao produto | Geralmente não aplicável à unidade individual; não exigir por padrão | calibre, comprimento, tipo de ponta, conexão/canhão, referência do fabricante |
| Seringa | Obrigatório | Obrigatório | Obrigatório quando aplicável | Não exigir por padrão; capturar se houver serial individual | capacidade nominal, tipo de ponta/conexão, material, graduação |
| Equipo | Obrigatório | Obrigatório | Obrigatório quando aplicável | Não exigir por padrão | tipo de equipo, comprimento, câmara, filtro, conexão |
| Cateter | Obrigatório | Obrigatório | Obrigatório quando aplicável | Condicional; capturar se o produto possuir serial individual | calibre, comprimento, material, tipo de ponta/conexão |
| Outra classe | Obrigatório | Obrigatório | Conforme regra cadastrada para a classe | Conforme regra cadastrada para a classe | Atributos definidos em catálogo e procedimento |

**Importante:** a tabela não declara requisitos normativos universais para cada produto. Ela indica uma proposta de validação do LIMS. A matriz definitiva deve ser aprovada pelo responsável técnico e alinhada aos métodos, regulamentos e procedimentos aplicáveis.

### 6.1 Ausência, não aplicabilidade e desconhecimento

Distinguir explicitamente:
- **Não aplicável:** a classe/produto não possui aquele identificador.
- **Não disponível:** o identificador existe, mas não foi apresentado/observado na chegada.
- **Pendente de confirmação:** informação recebida, mas ainda não verificada.
- **Informado:** valor capturado, sujeito à validação.
- **Confirmado:** valor conferido e aceito para a amostra.

Não usar string vazia, zero, “N/A”, “SEM SERIAL” ou valores fictícios como substitutos de nulo/estado estruturado. Quando um campo obrigatório para a classe estiver ausente, o item permanece pendente e não pode ser aceito até regularização ou exceção formal permitida.

## 7. Separação entre declaração, recebimento e amostra

O payload deve respeitar as entidades e etapas do domínio:

### 7.1 SolicitationItem / ItemDeclarado

Guarda a informação declarada pelo solicitante:
- classe/tipo declarado;
- fabricante, nome comercial e referência, se informados;
- lote/serial, se informados;
- quantidade e unidade declaradas;
- atributos específicos declarados;
- observações/documentos de origem.

Esses dados não comprovam, por si só, que o material foi fisicamente apresentado ou confirmado.

### 7.2 ReceiptItem / ItemRecebimento

Registra:
- situação de apresentação;
- quantidade efetivamente apresentada;
- conferência dos identificadores;
- divergências entre declaração e material;
- pendências e evidências;
- valores confirmados e histórico de correções.

Itens não apresentados não geram objeto de custódia nem amostra operacional.

### 7.3 CustodyObject / ObjetoCustodia

Representa a unidade física ou agrupamento homogêneo sob guarda, conforme API03/DEC05. Deve carregar ou referenciar a identidade física necessária à rastreabilidade do objeto, incluindo quantidade/unidade e atributos relevantes para distingui-lo de outros objetos do mesmo ReceiptItem.

Se unidades exigirem resultados, decisões ou destinações independentes, devem ser representadas por objetos distintos. A criação de vários objetos não implica automaticamente serial individual.

### 7.4 DeviceSample / AmostraOperacional

É criada somente após aceite e validações exigidas. Deve:
- vincular-se ao `CustodyObject` conforme DEC05;
- receber `accession_number` gerado pelo LIMS;
- receber a identidade confirmada do produto/objeto;
- preservar `received_at = Receipt.arrived_at` e o recebedor físico original;
- permitir vários ensaios e corpos de prova conforme o fluxo laboratorial;
- não criar evento de chegada duplicado.

A amostra não deve ser criada diretamente a partir de dados ainda não confirmados do item declarado.

## 8. Payload recomendado — estrutura lógica

Recomenda-se um payload tipado por classe ou um objeto comum com seção de identificação específica. Para evitar uma proliferação precoce de endpoints, a proposta inicial é um contrato comum com `device_class` e objeto `identification`, submetido a validação condicional por catálogo.

Exemplo ilustrativo de identificação confirmada de material sem serial individual:

~~~json
{
  "custody_object_id": "uuid",
  "expected_version": 3,
  "device_class": "NEEDLE",
  "identification": {
    "manufacturer": "Fabricante informado e confirmado",
    "commercial_name": "Agulha hipodérmica",
    "lot_number": "LOTE-ABC-2026",
    "serial_number": null,
    "serial_status": "NOT_APPLICABLE",
    "model_reference": "REF-001",
    "attributes": {
      "gauge": "25G",
      "length_mm": 25
    }
  }
}
~~~

Este exemplo ilustra a estrutura conceitual do payload de aceite; não é um contrato OpenAPI aprovado. O identificador do objeto e a versão são coerentes com as propostas API06/API09, mas os nomes e tipos finais dependem do fechamento conjunto das decisões.

### 8.1 Regras de validação do payload

- `device_class` deve pertencer ao catálogo ativo.
- `manufacturer` e `commercial_name` devem estar preenchidos para aceite.
- `lot_number` deve estar preenchido quando a regra da classe/produto o exigir.
- `serial_number` pode ser nulo somente quando a política de aplicabilidade permitir; estado de não aplicabilidade/ausência deve ser explícito.
- `attributes` deve respeitar o schema específico da classe, com unidades e domínios controlados quando aplicável.
- campos desconhecidos ou incompatíveis com a classe devem ser rejeitados, não silenciosamente ignorados.
- atributos essenciais ao ensaio devem ser confirmados antes da criação da amostra, conforme método e procedimento aplicáveis.
- a identidade confirmada deve ser preservada em snapshot/auditoria da operação de aceite, conforme API04/API05.
- dados do ator, recebedor físico, timestamps de chegada e custodiante não devem ser aceitos como valores livres no payload quando são derivados de sessão, Receipt ou eventos de custódia.

## 9. Unicidade e prevenção de duplicidade

### 9.1 Não usar serial + lote + fabricante como chave universal

A restrição atual composta pode permanecer para compatibilidade do fluxo legado enquanto não houver plano aprovado. Entretanto, não deve ser considerada a regra universal de identidade do novo fluxo.

A identidade operacional da amostra deve ser assegurada principalmente por:
- `accession_number` único e imutável;
- vínculo único entre `CustodyObject` aceito e `DeviceSample`, conforme DEC05;
- integridade do recebimento e do objeto;
- idempotência API07;
- concorrência API06;
- auditoria e regras de domínio.

A combinação fabricante + lote + serial pode ser usada como indício de duplicidade ou regra complementar quando aplicável, mas não deve bloquear automaticamente dois objetos distintos que legitimamente compartilhem fabricante/lote e não possuam serial individual.

### 9.2 Duplicidade não é sempre identidade

Duas unidades ou agrupamentos podem ter a mesma classe, fabricante, nome comercial e lote. Isso não significa que sejam a mesma amostra operacional. A decisão depende da granularidade do `CustodyObject`, do recebimento e da necessidade de resultados/destinos independentes.

A regra de deduplicação deve distinguir:
- repetição da mesma operação (API07);
- tentativa concorrente de aceitar o mesmo objeto (API06 + constraint);
- objeto já aceito por uma operação anterior (API09);
- dois objetos físicos distintos com identidade comercial igual (API03/DEC05).

## 10. Compatibilidade com o legado

A transição deve seguir abordagem expand/contract e preservar integralmente:
- rotas legadas de amostras e custódia;
- formato e unicidade de `accession_number`;
- QR Code e mecanismo de consulta existente;
- dados históricos e assinaturas/auditoria;
- semântica dos campos atualmente obrigatórios nas rotas legadas.

Não se deve:
- tornar campos legados opcionais sem migração aprovada;
- preencher serial ausente com valor fictício;
- reescrever registros antigos para simular a nova identidade;
- alterar a constraint única antes de analisar dados e consumidores;
- atribuir `CustodyObject` artificial a amostras antigas;
- remover `storage_location` de contratos antigos nesta decisão.

O novo fluxo poderá ter schema de entrada próprio, mapeando para a entidade operacional após validação, mas o desenho físico deve esclarecer como atributos condicionais serão persistidos sem quebrar o modelo atual.

## 11. Armazenamento de atributos específicos

Duas alternativas devem ser avaliadas no desenho relacional:

**A. Colunas tipadas por classe:** maior integridade e validação SQL para atributos estáveis e consultados frequentemente, porém amplia o schema e exige migrações quando surgem novos atributos.

**B. Estrutura JSON validada por schema:** maior flexibilidade para atributos variáveis, porém exige validação rigorosa na aplicação, versionamento do schema e cuidado com consultas/relatórios.

Recomendação preliminar: manter campos comuns de identificação estruturados e avaliar JSON versionado apenas para atributos específicos de classe, quando não houver justificativa para colunas tipadas. Não armazenar toda a identidade em um JSON genérico nem usar JSON como substituto de campos críticos de rastreabilidade.

A decisão depende de frequência de consulta, necessidade de indexação, relatórios, validação, auditoria e política institucional de dados.

## 12. Dependências e questões em aberto

- **API03/DEC05:** granularidade de CustodyObject, quantidade/unidade e quando separar objetos.
- **API04:** eventos, autoria e timestamps; preservar origem e confirmação de dados.
- **API05:** alvo e snapshot de assinatura do aceite.
- **API06/API07:** concorrência e idempotência do comando de aceite.
- **API09:** comportamento quando o objeto já foi aceito.
- **API10:** autorização para confirmar identidade, corrigir divergências e aceitar.
- **DEC10/DEC11:** regras institucionais de identidade e classificação, conforme matriz de decisões de domínio.
- **Responsável técnico/laboratorial:** matriz final de aplicabilidade de serial, lote e atributos por classe.
- **Cadastro de materiais:** catálogo controlado de classes, fabricantes, nomes comerciais e referências, se houver.
- **Modelo relacional:** estratégia de persistência dos atributos específicos e convivência com campos/constraints legados.
- **Runtime/banco-alvo:** confirmar metadata, migrações aplicadas, constraints reais, dados nulos/duplicados e consumidores antes de qualquer alteração.

## 13. Recomendação final

Adotar a Alternativa C: identidade comum mínima para toda amostra aceita, com classe de material obrigatória e validações condicionais explícitas.

Como regra geral proposta:
- `accession_number`, classe, fabricante e nome comercial são obrigatórios na amostra aceita;
- lote é obrigatório quando aplicável ao produto/classe;
- serial é obrigatório somente quando existir e for exigido para aquela classe/produto/procedimento;
- ausência e não aplicabilidade devem ser representadas explicitamente, sem valores fictícios;
- atributos específicos devem seguir schema por classe;
- localização pertence à custódia, não à identidade universal;
- unicidade operacional deve ser baseada no accession_number e no vínculo CustodyObject–DeviceSample, complementada por API06/API07/API09;
- contratos e dados legados devem permanecer compatíveis até aprovação de plano específico.

A matriz definitiva de campos e exceções precisa de validação do responsável técnico/laboratorial, cadastro de materiais, arquitetura e autoridade institucional aplicável. Até lá, API08 permanece bloqueadora e não implementável.

## 14. Registro da validação em revisão do projeto

Em 2026-11-09, o usuário validou as regras gerais recomendadas nesta proposta, como diretriz do responsável pelo projeto em revisão. O registro abrange:

1. não exigir número de série individual para todas as classes de materiais;
2. exigir fabricante e nome comercial confirmados no aceite;
3. exigir lote conforme sua aplicabilidade ao produto/classe;
4. utilizar atributos específicos conforme a classe de material;
5. tratar localização física no domínio da custódia, e não como identidade universal;
6. não alterar restrições e contratos legados antes de análise e plano de migração aprovados.

Esta validação não equivale à aprovação institucional formal, não fecha a matriz definitiva de aplicabilidade por classe e não autoriza implementação. Permanecem necessárias a validação funcional/técnica dos detalhes, a confirmação pelo responsável técnico/laboratorial e cadastro de materiais, a revisão de compatibilidade com runtime/banco-alvo e a aprovação institucional aplicável.

## 15. Controle de execução

**Realizado:** recuperação da matriz API01–API12, especificação de contratos, modelo relacional preliminar, estratégia de migração e inventário técnico; elaboração desta proposta documental com base nas evidências estáticas disponíveis.

**Não realizado:** inspeção de código/runtime nesta atividade; consulta ao banco implantado; alterações em código, modelos, banco, migrações, endpoints, frontend, especificação funcional ou OpenAPI; testes, build, CI ou validação automática.

**Situação:** proposta técnica para revisão. Não há autorização de implementação.

## 16. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 0.1 | 2026-11-10 | Primeira proposta de identidade mínima e payload condicional por classe de material, com compatibilidade legada. |
| 0.2 | 2026-11-09 | Registro da validação das regras gerais pelo responsável pelo projeto em revisão; fechamento funcional/técnico e aprovação institucional permanecem pendentes. |
