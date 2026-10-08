# Guia de Contribuição - DonaBe

Obrigado por se interessar em contribuir com o DonaBe! Este guia cobre as melhores práticas para cada tipo de contribuição.

## Índice

- [Guia de Contribuição - DonaBe](#guia-de-contribuição---donabe)
  - [Índice](#índice)
  - [Parte 1: Boas Práticas](#parte-1-boas-práticas)
    - [Etiqueta](#etiqueta)
    - [Ambiente de Desenvolvimento](#ambiente-de-desenvolvimento)
  - [Parte 2: Trabalhando com Issues](#parte-2-trabalhando-com-issues)
    - [Como Abrir uma Issue](#como-abrir-uma-issue)
    - [Antes de Submeter](#antes-de-submeter)
    - [Para Mais Informações](#para-mais-informações)
  - [Parte 3: Contribuindo com Código](#parte-3-contribuindo-com-código)
    - [Quando Modificar o Código](#quando-modificar-o-código)
    - [Nunca modifique o código para:](#nunca-modifique-o-código-para)
    - [Processo de Contribuição](#processo-de-contribuição)
    - [Comentários no Código](#comentários-no-código)
      - [Commits](#commits)
      - [Executando Testes](#executando-testes)
  - [Dúvidas?](#dúvidas)

## Parte 1: Boas Práticas

### Etiqueta

Ao contribuir para o DonaBe, lembre-se:

- Escreva títulos claros e concisos para as Issues
  - Não coloque a descrição inteira no título da issue
- Evite duplicações
  - Verifique se a issue ou PR que você quer abrir já existe
- Uma coisa por vez
  - Uma issue ou PR por problema/feature
- Qualidade primeiro
  - Priorize código bem escrito e testado

> [!TIP]
> Use a barra de busca antes de abrir uma nova issue. Muitas vezes, alguém já reportou o mesmo problema!

### Ambiente de Desenvolvimento

Siga o [docs/SETUP.MD](SETUP.MD) para configurar o ambiente. O código é escrito em inglês (nomes de arquivos, classes, funções, variáveis, rotas e colunas); os textos que o usuário vê e a documentação ficam em português.

## Parte 2: Trabalhando com Issues

### Como Abrir uma Issue

1. Acesse a aba [Issues](https://github.com/Dona-Be/DonaBe/issues) do repositório
2. Clique em **New Issue**
3. Escolha o template apropriado que melhor descreve sua necessidade
4. Preencha todos os campos obrigatórios com o máximo de detalhes
5. Submeta a issue

> [!IMPORTANT]
> Todos os campos marcados como obrigatórios no template devem ser preenchidos. Issues incompletas podem ser fechadas.

### Antes de Submeter

- Procure duplicatas
    - Use a barra de busca para verificar se a issue já foi reportada
- Complete o checklist
    - Preencha todos os campos solicitados no template
- Seja específico
    - Quanto mais detalhes, melhor poderemos ajudar

### Para Mais Informações

Para uma descrição detalhada de cada tipo de issue disponível, consulte [docs/ISSUES.MD](ISSUES.MD).

## Parte 3: Contribuindo com Código

### Quando Modificar o Código

Você deve modificar o código quando:

- Corrigir um bug reportado e confirmado
- Implementar uma feature que foi solicitada e aprovada em uma issue
- Melhorar a qualidade do código existente (refatoração, otimização)
- Atualizar documentação que está desatualizada ou incompleta

> [!TIP]
> Sempre abra uma issue antes de começar a trabalhar. Assim, a discussão pode acontecer antes do trabalho ser feito!

### Nunca modifique o código para:

- Adicionar funcionalidades não solicitadas
- Mudar estilos visuais sem discussão prévia
- Refatorar código sem abrir uma issue de manutenção
- Mergear grandes mudanças sem review

> [!CAUTION]
> PRs que violarem essas regras podem ser rejeitadas sem revisão. Sempre discuta antes de implementar!

### Processo de Contribuição

1. Crie uma issue primeiro - Descreva o que você pretende fazer
2. Aguarde feedback
3. Atualize a `dev` localmente: `git switch dev && git pull`
4. Crie uma branch descritiva a partir da `dev`:
   - `fix/nome-do-bug` para correções
   - `feature/nome-da-funcionalidade` para novas features
   - `docs/descricao` para documentação
5. Implemente suas mudanças com commits bem descritos
6. Execute as validações locais (lint e testes)
7. Push da sua branch para o repositório
8. Abra um Pull Request (PR) para a **`dev`** referenciando a issue original
9. O PR precisa do check **CI** verde e de 1 aprovação de outra pessoa antes do merge

A `dev` integra o trabalho de todos. Quando ela estiver pronta para ir ao ar, um PR da `dev` para a `main` publica a versão em produção.

### Comentários no Código

Comentários são escritos em inglês, como o código. Escreva comentários úteis, não óbvios:

Evite:
```typescript
// Increment counter
counter++;

// Check if user is null
if (user != null) { ... }

// Test - remove later
console.log(data); // REMOVE!
```

Prefira:
```typescript
// Bump the session version so the tokens of the other devices stop working
sessionVersion++;

// User may be null when not authenticated yet
if (user != null) { ... }

// Validate that the date follows the ISO 8601 format
if (validateISODate(data)) { ... }
```

> [!TIP]
> Comentários devem explicar o "por quê", não o "o quê". O código já diz o que está fazendo!

#### Commits

Escreva mensagens de commit claras e descritivas:

```bash
fix: corrigir redirecionamento depois do login
feature: adicionar busca de instituições por proximidade
docs: atualizar instruções de instalação
test: adicionar testes para o serviço de usuários
```

> [!IMPORTANT]
> Commits devem ser atômicos - cada commit deve representar uma mudança lógica única.

#### Executando Testes

Sempre execute as validações antes de criar uma PR. O `make test` precisa do ambiente virtual do backend ativo (`source server/.venv/bin/activate`) e do banco no ar (`make up`), porque os testes do backend rodam contra o banco de testes:

```bash
# Lint do backend e do site
make lint

# Testes do backend (contra o banco de testes) e do site
make test
```

Seu código deve:
- Passar em todos os testes existentes
- Incluir novos testes para funcionalidades novas
- Manter a cobertura de testes consistente

> [!CAUTION]
> Nenhuma PR será aceita se os testes não passarem. Garanta que seu código está funcionando!

## Dúvidas?

Se tiver dúvidas sobre como contribuir:

- Abra uma issue perguntando
- Consulte a documentação do projeto
- Converse com algum dos membros da equipe
