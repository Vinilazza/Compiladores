# CACHOEIRA — a linguagem de programação

> "é loko, cachoeira! memo, cachoeira, memo"

Linguagem de programação criada para o trabalho da matéria de Compiladores,
inspirada no vídeo viral do "Cachoeira" (o famoso caso de assalto/facada em
mercado que virou meme na internet). O projeto segue a mesma pegada da
[BIRL](https://birl-language.github.io/) — sintaxe baseada em memes
brasileiros — só que em cima de outro vídeo.

Todas as palavras-chave vêm direto das falas do vídeo. O resto (operadores,
parênteses, números) é convencional, senão não dava pra escrever nada sério.

## Por que "CACHOEIRA"?

O vídeo original tem essas falas, usadas como base pra cada palavra-chave:

- "é loko, cachoeira! memo, cachoeira, memo"
- "só por deus irmão, só por deus"
- "se é louco cachoeira"
- "eu não assumo esse B.O"
- "sou de São Paulo fi, nóis rouba de pistola"
- "não sou nem envolvido no crime, nóis rouba de pistola"
- "só trabalhador, só zé povinho"

## Tabela de palavras-chave

| Bordão (meme)                                              | Token          | Significado                          |
|--------------------------------------------------------------|----------------|---------------------------------------|
| `MEMO`                                                        | `VAR`          | declara uma variável                  |
| `É LOKO, CACHOEIRA!`                                          | `PRINT`        | imprime um valor na tela              |
| `SE É LOUCO CACHOEIRA (...)`                                  | `IF`           | estrutura condicional                 |
| `SÓ TRABALHADOR SÓ ZÉ POVINHO`                                | `ELSE`         | ramo alternativo do `if`              |
| `SÓ POR DEUS IRMÃO (...)`                                     | `WHILE`        | laço de repetição                     |
| `SÓ POR DEUS IRMÃO TENTANDO`                                  | `TRY`          | início de bloco protegido             |
| `EU NÃO ASSUMO ESSE B.O`                                      | `CATCH`        | captura erro em tempo de execução     |
| `SOU DE SÃO PAULO FI, NÓIS ROUBA DE PISTOLA nome(params)`     | `FUNC`         | define uma função                     |
| `NÃO SOU NEM ENVOLVIDO NO CRIME`                              | `RETURN`       | retorna um valor da função            |
| `MEMO, CACHOEIRA, MEMO`                                       | `END`          | fecha qualquer bloco (if/while/try/função) |
| `FI`                                                           | `TRUE`         | literal booleano verdadeiro           |
| `NUNCA NA VIDA`                                                | `FALSE`        | literal booleano falso                |

Extras que a linguagem precisa pra ser útil (não vêm do vídeo, são convenção
normal de qualquer linguagem): números, strings entre `"..."`, identificadores,
operadores aritméticos (`+ - * /`), comparação (`== != < > <= >=`), lógicos
(`&& || !`), vírgula e parênteses. Comentários começam com `#`.

Curiosidade de design: `SÓ POR DEUS IRMÃO` serve tanto pra `while` quanto pra
início de `try` — o parser decide olhando se a próxima palavra é `TENTANDO`
("só por deus irmão, tentando...") ou uma condição entre parênteses. É o
mesmo token léxico resolvido de forma diferente pelo parser, dependendo do
contexto — um bom gancho pra explicar análise sintática preditiva na
apresentação.

## Exemplo

```
# fibonacci.cch
SOU DE SÃO PAULO FI, NÓIS ROUBA DE PISTOLA fib(n)
    SE É LOUCO CACHOEIRA (n <= 1)
        NÃO SOU NEM ENVOLVIDO NO CRIME n
    MEMO, CACHOEIRA, MEMO
    NÃO SOU NEM ENVOLVIDO NO CRIME fib(n - 1) + fib(n - 2)
MEMO, CACHOEIRA, MEMO

MEMO i = 0
SÓ POR DEUS IRMÃO (i < 10)
    É LOKO, CACHOEIRA! fib(i)
    i = i + 1
MEMO, CACHOEIRA, MEMO
```

Tratamento de erro:

```
MEMO a = 10
MEMO b = 0

SÓ POR DEUS IRMÃO TENTANDO
    É LOKO, CACHOEIRA! a / b
EU NÃO ASSUMO ESSE B.O
    É LOKO, CACHOEIRA! "eu não assumo esse B.O, mas rolou divisão por zero"
MEMO, CACHOEIRA, MEMO
```

Mais exemplos em [`examples/`](examples/).

## Como rodar

Requer só Python 3 (sem dependências externas):

```bash
python3 main.py examples/fibonacci.cch
```

Rodar os testes:

```bash
python3 -m unittest tests/test_cachoeira.py -v
```

## Arquitetura do compilador/interpretador

O pipeline é o clássico de um interpretador de matéria de Compiladores:

```
código .cch → LÉXICO → tokens → PARSER → AST → INTERPRETADOR → saída
             (lexer.py)         (parser.py)      (interpreter.py)
```

- **`src/cachoeira/lexer.py`** — análise léxica. Casa primeiro as frases-meme
  (da mais longa pra mais curta, pra não confundir `MEMO, CACHOEIRA, MEMO`
  com `MEMO` sozinho) via expressões regulares, depois cai pros tokens
  genéricos (número, string, identificador, símbolos).
- **`src/cachoeira/ast_nodes.py`** — definição dos nós da árvore sintática
  (Program, If, While, Try, FuncDef, BinOp, etc).
- **`src/cachoeira/parser.py`** — parser recursivo-descendente que consome
  a lista de tokens e monta a AST, respeitando a gramática em
  [`grammar.ebnf`](grammar.ebnf) e a precedência de operadores.
- **`src/cachoeira/interpreter.py`** — percorre a AST (tree-walking
  interpreter) e executa o programa, com escopos aninhados (`Environment`),
  chamadas de função com closures e exceções Python usadas internamente pra
  implementar `return` (`ReturnSignal`) e `try/catch`
  (`CachoeiraRuntimeError`).
- **`src/cachoeira/errors.py`** — erros de sintaxe (`CachoeiraSyntaxError`)
  e de execução (`CachoeiraRuntimeError`), essa última capturável dentro do
  próprio código CACHOEIRA via `EU NÃO ASSUMO ESSE B.O`.

## Roteiro sugerido pra apresentação

1. Mostrar o vídeo/print do meme e ler as falas.
2. Mostrar a tabela de bordão → palavra-chave (slide único, é o "wow" da
   apresentação).
3. Rodar `examples/ola_mundo.cch` ao vivo.
4. Explicar o pipeline lexer → parser → AST → interpretador com um exemplo
   pequeno, mostrando os tokens gerados (dá pra printar `tokenize(...)` no
   terminal) e depois a AST.
5. Rodar `examples/fibonacci.cch` (função + recursão) e
   `examples/loop_e_tentativa.cch` (while + try/catch) pra mostrar que a
   linguagem é Turing-completa na prática (condicional, laço, função,
   recursão, tratamento de erro).
6. Fechar com a piada: "é loko, cachoeira" também é o `print` — quem não
   entendeu o meme não entendeu a linguagem.
