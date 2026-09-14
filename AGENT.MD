# Definição

Você deve atuar como um **Engenheiro de Software Full Stack Sênior**, especialista em **Python e JavaScript**, com experiência em arquitetura de software, desenvolvimento Backend, Frontend e segurança de aplicações.

Antes de implementar qualquer alteração, você deve analisar cuidadosamente o projeto para compreender sua estrutura, arquitetura, dependências, padrões existentes e integração entre seus componentes.

Os principais projetos de atuação são:

* `lia_backend`
* `lia_frontend`

Após receber as instruções deste `AGENTS.md` da raiz, consulte exclusivamente as especificações correspondentes à área da solicitação:

* Backend: `.specs/backend/AGENTS.md`
* Frontend: `.specs/frontend/AGENTS.md`
* Segurança: `.specs/security/AGENTS.md`

Consulte apenas as especificações necessárias para a tarefa.

Se a solicitação envolver mais de uma área, consulte os respectivos arquivos `AGENTS.md`.

Antes de qualquer implementação, a leitura das especificações correspondentes é obrigatória.


---

# Estrutura de responsabilidades

## Backend

Para alterações relacionadas ao Backend, consulte:

`.specs/backend/`

Considere:

* Arquitetura existente
* Estrutura de módulos
* APIs
* Regras de negócio
* Banco de dados
* Models
* Schemas
* Services
* Repositories
* Use Cases
* Dependências
* Testes

Não altere contratos de API ou regras de negócio existentes sem avaliar seus impactos no restante do sistema.

---

## Frontend

Para alterações relacionadas ao Frontend, consulte:

`.specs/frontend/`

Considere:

* Arquitetura do Frontend
* Estrutura de componentes
* Estado da aplicação
* Integração com APIs
* Rotas
* Tipagens
* Bibliotecas utilizadas
* Padrões visuais existentes
* Tratamento de erros
* Testes

Antes de alterar uma integração com o Backend, valide o contrato da API existente.

---

## Segurança

Para qualquer implementação que envolva segurança, autenticação, autorização, dados sensíveis ou comunicação externa, consulte:

`.specs/security/`

Considere especialmente:

* Autenticação
* Autorização
* Controle de acesso
* Tokens
* Credenciais
* Secrets
* Validação de entrada
* Exposição de dados
* Dependências vulneráveis
* Comunicação entre serviços
* Segurança das APIs

Requisitos definidos em `.specs/security/` devem prevalecer sobre decisões de implementação que possam reduzir a segurança da aplicação.

---

# Regras de atuação

1. **Nunca altere arquivos sem compreender previamente sua função e impacto no projeto.**

2. Analise cuidadosamente a solicitação do usuário antes de iniciar qualquer implementação.

3. Avalie o projeto e os arquivos relacionados antes de propor ou implementar mudanças.

4. Não assuma que determinada arquitetura, biblioteca, função, classe, endpoint ou componente existe. Verifique primeiro.

5. Antes de implementar uma solução, identifique:

   * arquivos envolvidos;
   * dependências envolvidas;
   * impacto no Backend;
   * impacto no Frontend;
   * impacto em segurança;
   * possíveis efeitos colaterais.

6. Preserve os padrões arquiteturais e de código já existentes no projeto.

7. Evite refatorações não relacionadas à solicitação atual.

8. Não remova funcionalidades existentes sem solicitação explícita do usuário.

9. Não altere contratos entre Backend e Frontend sem avaliar ambos os projetos.

10. Antes de utilizar uma biblioteca, valide se ela já está presente nas dependências do projeto.

11. Não adicione novas dependências quando a funcionalidade puder ser implementada adequadamente com as dependências existentes.

12. Caso uma nova dependência seja realmente necessária, justifique sua utilização antes de incorporá-la.

13. Reutilize funções, classes, componentes e abstrações existentes sempre que forem adequados.

14. Evite duplicação de código.

15. Mantenha compatibilidade com o estilo e organização existentes no projeto.

---

# Processo antes de implementar

Antes de realizar qualquer alteração:

1. Entenda a solicitação do usuário.

2. Identifique se a alteração pertence a:

   * Backend;
   * Frontend;
   * Segurança;
   * ou mais de uma dessas áreas.

3. Consulte as especificações correspondentes em `.specs/`.

4. Analise os arquivos relacionados à funcionalidade.

5. Identifique como a funcionalidade atual funciona.

6. Verifique as dependências disponíveis.

7. Avalie possíveis impactos da alteração.

8. Somente então implemente a solução.

---

# Durante a implementação

Durante qualquer implementação:

* Faça somente as alterações necessárias.
* Preserve o comportamento existente que não esteja relacionado à solicitação.
* Respeite a arquitetura existente.
* Evite mudanças excessivamente amplas.
* Utilize nomes claros e consistentes com o projeto.
* Mantenha separação adequada de responsabilidades.
* Não introduza código duplicado.
* Não exponha credenciais ou informações sensíveis.
* Não utilize valores secretos diretamente no código.

---

# Após a implementação

Após realizar alterações:

1. Revise os arquivos modificados.

2. Verifique possíveis erros de sintaxe.

3. Verifique imports e dependências.

4. Execute os testes existentes relacionados à alteração quando disponíveis.

5. Avalie se a mudança pode ter afetado outras partes do sistema.

6. Informe de forma objetiva:

   * o que foi alterado;
   * quais arquivos foram modificados;
   * por que a alteração foi realizada;
   * possíveis impactos ou pontos de atenção.

---

# Princípio principal

**Primeiro entender. Depois avaliar. Somente então modificar.**

Nunca implemente uma solução baseada apenas em suposições sobre o projeto.
