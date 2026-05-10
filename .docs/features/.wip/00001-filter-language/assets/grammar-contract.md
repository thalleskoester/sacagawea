# Grammar Contract - V1

The parser must implement the v1 syntax in this file using the standard-library parser strategy from `.docs/features/.wip/00001-filter-language/assets/parser-strategy.md`.

## Tokens And Trivia

Whitespace is insignificant between tokens.

Comments are trivia and do not appear in the AST:

| Comment | Form |
|---|---|
| Line comment | `//` through the end of the line |
| Block comment | `/*` through the next `*/` |

## Identifiers

Bracketed path segments match:

```text
[A-Za-z_][A-Za-z0-9_-]*
```

Function and method symbols match:

```text
[A-Za-z_][A-Za-z0-9_]*
```

Function and method symbols do not allow hyphens. All identifiers are ASCII-only and must not start with a digit.

## Literals

Supported user literals:

| Literal | Examples |
|---|---|
| `String` | `"john"`, `'john'` |
| `Integer` | `21`, `-21` |
| `Decimal` | `0.5`, `-0.5`, `5.`, `-5.`, `.5`, `-.5` |

String literals must support these escape sequences in both single-quoted and double-quoted strings:

```text
\\
\"
\'
\n
\t
```

Unsupported literals are syntax errors in v1: list, dictionary, boolean, null, date, time, and datetime literals.

## Expressions

The grammar supports:

| Expression | Shape |
|---|---|
| String literal | `"john"`, `'john'` |
| Integer literal | `21`, `-21` |
| Decimal literal | `0.5`, `-0.5`, `5.`, `-5.`, `.5`, `-.5` |
| Path | `[first_name]`, `[customer].[address].[city]` |
| Global function call | `and(...)`, `or(...)`, `not(...)`, or any syntactically valid symbol |
| Method call | `<path>.<method>(...)` |

Method-call receivers are path expressions in v1. The parser must not accept method calls on string literals, numeric literals, global function calls, or other method calls.

Trailing commas are allowed in function and method argument lists and do not create an extra argument.

The parser must parse function and method names generically. Runtime validation decides whether the function or method exists.

Operator precedence is not configurable in v1. There are no infix operators; calls and paths are the only composition forms.
