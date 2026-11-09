# Política de Documentação e Controle de Versões do LIMS

**Identificador:** POL-DOC-001  
**Versão:** 1.0  
**Situação:** Adotada para o desenvolvimento do projeto  
**Repositório:** `keyzermoura/LIMS`  
**Branch de documentação:** `main`  
**Data de emissão:** 2026-11-09

---

## 1. Objetivo

Estabelecer regras para produzir, revisar, aprovar, versionar e manter a documentação do LIMS, assegurando rastreabilidade entre necessidades institucionais, decisões, requisitos, arquitetura, implementação, testes e validação.

A documentação é parte integrante do desenvolvimento. Não deve ser tratada como atividade opcional ou realizada apenas ao final do projeto.

## 2. Princípios obrigatórios

1. Decisões relevantes não podem existir somente em conversas, mensagens ou memória dos participantes: devem ser registradas no repositório.
2. Nenhuma funcionalidade será considerada concluída sem documentação compatível com o seu escopo e evidências de verificação.
3. Requisitos, decisões e critérios de aceitação devem possuir identificadores estáveis.
4. A documentação deve distinguir claramente o que foi proposto, decidido, implementado, testado, aprovado e validado.
5. A existência de código ou de teste automatizado não demonstra, isoladamente, que o sistema está validado para uso institucional.
6. Alterações devem preservar histórico e rastreabilidade; não se deve apagar silenciosamente decisões ou registros anteriores.
7. A documentação deve refletir o estado real do projeto. Não declarar como implementado, testado ou validado algo que não tenha evidência correspondente.

## 3. Fonte oficial e organização

O repositório GitHub `keyzermoura/LIMS` é a fonte oficial da documentação técnica do projeto. Documentos locais, mensagens e rascunhos podem apoiar o trabalho, mas não substituem o registro versionado.

A organização de referência para a documentação evolutiva será:

| Pasta | Conteúdo |
|---|---|
| `docs/01_GOVERNANCA/` | Governança, política, papéis, plano diretor e decisões |
| `docs/02_REQUISITOS/` | Requisitos funcionais e não funcionais, glossário e critérios de aceitação |
| `docs/03_ARQUITETURA/` | Arquitetura, componentes, integrações, segurança e modelo de dados |
| `docs/04_PROCESSOS/` | Processos institucionais e especificações funcionais |
| `docs/05_DESENVOLVIMENTO/` | Especificações técnicas, padrões e registros de implementação |
| `docs/06_TESTES/` | Planos, casos, resultados e evidências de testes |
| `docs/07_VALIDACAO/` | Plano e relatórios de validação do sistema para o uso pretendido |
| `docs/08_OPERACAO/` | Implantação, operação, backup, recuperação e suporte |
| `docs/09_HISTORICO/` | Registros históricos e relatórios consolidados |

Os documentos já existentes diretamente em `docs/` serão mantidos em seus caminhos atuais por enquanto. A reorganização, se necessária, será feita de forma controlada, atualizando referências e links. Não será realizada movimentação em massa apenas para adequação estética.

## 4. Conjunto documental do projeto

O conjunto documental será desenvolvido progressivamente. Os documentos abaixo são os artefatos de referência:

| Documento | Finalidade |
|---|---|
| Plano Diretor do Projeto | Escopo, fases, cronograma, responsabilidades, riscos e portões de aprovação |
| Política de Documentação e Controle de Versões | Regras estabelecidas neste documento |
| Diagnóstico Técnico-Funcional | Registro do estado observado do repositório em uma referência específica |
| Matriz de Lacunas Arquiteturais | Lacunas, riscos e necessidades de evolução |
| Matriz de Requisitos | Requisitos funcionais e não funcionais, prioridades e critérios de aceitação |
| Glossário | Definições e uso uniforme dos termos do domínio |
| Matriz de Decisões | Decisões, justificativas, responsáveis, impactos e situação |
| Arquitetura do Sistema | Componentes, responsabilidades, limites e integrações |
| Modelo de Dados | Entidades, relacionamentos, cardinalidades, restrições e migrações |
| Especificações Funcionais | Fluxos, regras de negócio, perfis, estados e comportamento esperado |
| Especificações Técnicas | Contratos, APIs, estruturas, segurança e detalhes de implementação |
| Plano de Testes | Estratégia, cenários, dados, ambiente e critérios de aprovação |
| Relatórios de Testes | Resultados efetivamente obtidos e evidências |
| Plano e Relatório de Validação | Evidências de adequação do sistema ao uso pretendido |

Nem todos os documentos precisam ser arquivos separados desde o primeiro dia. É permitido consolidar conteúdos relacionados, desde que os identificadores, responsabilidades, histórico e rastreabilidade sejam preservados.

## 5. Identificação e rastreabilidade

Serão utilizados identificadores estáveis e não reutilizáveis:

- Requisitos funcionais: `RF-001`, `RF-002`...
- Requisitos não funcionais: `RNF-001`, `RNF-002`...
- Decisões: `DEC-001`, `DEC-002`...
- Casos de teste: `CT-001`, `CT-002`...
- Riscos: `R-001`, `R-002`...
- Critérios de aceitação, quando individualizados: `CA-001`, `CA-002`...

Um identificador não deve ser reutilizado, mesmo que o requisito ou decisão seja cancelado. Sua situação deve ser atualizada e o histórico preservado.

Sempre que aplicável, manter a cadeia:

**necessidade institucional → requisito → decisão → desenho → implementação → caso de teste → resultado/evidência → validação.**

Uma funcionalidade não deve ser declarada concluída se houver requisito aplicável sem tratamento ou justificativa documentada.

## 6. Registro de decisões

Decisões que afetem regras de negócio, arquitetura, dados, segurança, auditoria, integridade, operação, escopo ou critérios de aceitação devem ser registradas na Matriz de Decisões.

Cada registro deve conter, no mínimo:

- identificador;
- título e contexto;
- questão a decidir;
- alternativas consideradas, quando aplicável;
- decisão adotada;
- justificativa;
- impactos funcionais e técnicos;
- riscos e dependências;
- responsável pela decisão;
- data;
- situação;
- documentos e requisitos relacionados.

Situações permitidas:

- **Proposta:** alternativa apresentada, ainda não decidida;
- **Em análise:** depende de avaliação ou informação;
- **Aprovada:** decisão formalmente adotada pelo responsável competente;
- **Rejeitada:** alternativa não adotada, com justificativa;
- **Substituída:** decisão superada por outra, mantendo referência à sucessora.

Uma decisão técnica do desenvolvedor não substitui aprovação institucional quando a matéria envolver política, processo, responsabilidade, uso pretendido ou regra institucional.

## 7. Ciclo documental de cada funcionalidade

Cada funcionalidade relevante deve possuir registros proporcionais ao risco e à complexidade, cobrindo cinco momentos:

1. **Planejamento:** objetivo, escopo, requisitos, dependências, riscos e critérios de aceitação.
2. **Desenho:** fluxo, regras, estados, modelo de dados, contratos e impactos.
3. **Implementação:** arquivos/componentes alterados, migrações, decisões técnicas e referência ao commit.
4. **Verificação:** testes executados, ambiente, resultado, falhas, correções e evidências.
5. **Conclusão:** situação final, requisitos atendidos, limitações conhecidas, pendências e aprovação necessária.

Para mudanças pequenas, os registros podem estar reunidos em um único documento ou pull request. A simplificação não elimina a necessidade de evidência.

## 8. Controle de versões no GitHub

1. O histórico Git é o registro das alterações documentais e de código.
2. Commits devem descrever objetivamente o conteúdo da alteração.
3. Alterações de documentação devem ser revisáveis e, sempre que possível, isoladas de alterações de código.
4. Não reescrever o histórico compartilhado nem apagar evidências de decisões ou testes.
5. Documentos aprovados devem indicar versão, situação, data e histórico de alterações.
6. Alterações substanciais em documento aprovado devem gerar nova versão e registro do motivo.
7. Referências a código devem indicar branch e/ou commit quando isso for necessário para reproduzir a inspeção.
8. A branch `main` será usada para documentação de referência nesta etapa, respeitando as regras de proteção e revisão existentes no repositório.

### 8.1 Convenção de nomes

Usar nomes descritivos, estáveis e sem espaços, preferencialmente em maiúsculas e separados por sublinhado, por exemplo:

- `MATRIZ_DE_REQUISITOS.md`
- `MATRIZ_DE_DECISOES.md`
- `MODELO_DE_DADOS.md`
- `PLANO_DE_TESTES.md`

Não incluir número de versão no nome do arquivo quando o histórico Git e o cabeçalho do documento forem suficientes para controlar versões.

## 9. Situação e aprovação dos documentos

Todo documento sujeito a aprovação deve declarar sua situação no cabeçalho:

- **Rascunho:** em elaboração;
- **Em revisão:** submetido à análise;
- **Aprovado:** aprovado pelo responsável competente;
- **Obsoleto:** substituído, preservado para consulta histórica.

A aprovação deve registrar quem aprovou, em qual função, quando e, se aplicável, qual versão foi aprovada. Um commit no GitHub comprova que o conteúdo foi registrado, mas não representa automaticamente aprovação institucional.

Documentos de desenho técnico podem ser aprovados para orientar implementação sem que isso signifique autorização para uso operacional do sistema.

## 10. Testes, verificação e validação

Os termos devem ser usados de forma distinta:

- **Verificação:** demonstra que uma entrega atende às especificações e aos critérios definidos, por inspeção, análise ou teste.
- **Teste automatizado:** execução repetível de verificações implementadas em código; é uma modalidade de verificação.
- **Validação:** evidência documentada de que o sistema, em sua configuração e ambiente definidos, atende ao uso pretendido e às necessidades institucionais.
- **Homologação:** avaliação e aceite pelos representantes designados para o processo ou produto, conforme critérios previamente definidos.

Resultados de testes devem informar, quando aplicável: identificação do teste, versão/commit, ambiente, pré-condições, dados utilizados, passos, resultado esperado, resultado obtido, situação, evidências, responsável e data.

A aprovação de testes de desenvolvimento não autoriza, por si só, a utilização do LIMS em rotina institucional. A validação para o uso pretendido deverá possuir planejamento, responsabilidades, critérios, evidências e aprovação próprios.

## 11. Documentação de requisitos regulatórios e normativos

Quando um requisito for relacionado à ISO/IEC 17025, legislação, regulamentação sanitária, política institucional ou outro documento normativo, registrar:

- referência e edição aplicável;
- cláusula ou requisito pertinente, quando identificado;
- interpretação adotada para o sistema;
- funcionalidade, controle ou evidência que dará suporte ao atendimento;
- método de verificação;
- limitações e responsabilidades que permanecem fora do software.

Não declarar conformidade integral com uma norma apenas porque uma funcionalidade foi implementada. A conformidade depende do sistema de gestão, dos processos, das pessoas, dos registros e das evidências aplicáveis.

## 12. Papéis e responsabilidades

| Papel | Responsabilidade |
|---|---|
| Responsável institucional/funcional | Definir necessidades, confirmar regras de negócio e aprovar decisões institucionais dentro de sua competência |
| Desenvolvedor principal | Inspecionar a base técnica, propor soluções, implementar somente o escopo autorizado, manter documentação técnica e evidências de verificação |
| Responsável técnico do laboratório | Avaliar adequação dos processos laboratoriais, critérios técnicos e uso pretendido |
| Revisor técnico/funcional | Revisar documentos e entregas conforme designação |
| Responsável pela validação | Planejar, coordenar ou aprovar as atividades de validação conforme a governança institucional |

Uma mesma pessoa pode acumular papéis quando institucionalmente permitido, mas a responsabilidade exercida deve ficar explícita. O apoio do ChatGPT não substitui designação formal, aprovação institucional, revisão independente ou responsabilidade técnica.

## 13. Gestão de alterações e não conformidades documentais

Quando uma alteração modificar requisito, regra, decisão, arquitetura ou critério de aceitação:

1. identificar os documentos e artefatos impactados;
2. avaliar impactos e riscos;
3. registrar ou atualizar a decisão correspondente;
4. atualizar os requisitos e desenhos afetados;
5. implementar somente após as aprovações necessárias;
6. executar e registrar as verificações aplicáveis;
7. atualizar a situação e as referências cruzadas.

Erros documentais devem ser corrigidos com histórico rastreável. Quando uma decisão anterior se tornar inadequada, registrar sua substituição, sem apagar o fundamento histórico.

## 14. Rotina de acompanhamento

O acompanhamento do projeto deve registrar periodicamente:

- fase e atividade em andamento;
- situação (não iniciada, em andamento, bloqueada, concluída);
- entregáveis produzidos;
- commits ou referências verificáveis;
- testes e evidências;
- decisões pendentes;
- riscos, impedimentos e impactos;
- próxima atividade e responsável.

A situação do projeto deve ser baseada em evidências fornecidas ou verificáveis. Não se presumirá que tarefas foram executadas fora do ambiente observado.

## 15. Aplicação e revisão desta política

Esta política passa a orientar a documentação do desenvolvimento do LIMS a partir de sua publicação no repositório. Ela poderá ser revisada quando a governança do projeto, o escopo institucional ou as necessidades de controle evoluírem.

A adoção desta política não aprova automaticamente requisitos, decisões funcionais, arquitetura, cronograma, implementação ou uso operacional. Cada matéria mantém seu próprio processo de análise e aprovação.

## 16. Histórico de alterações

| Versão | Data | Descrição |
|---|---|---|
| 1.0 | 2026-11-09 | Emissão inicial da política de documentação e controle de versões. |
