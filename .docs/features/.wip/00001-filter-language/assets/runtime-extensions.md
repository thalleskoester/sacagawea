# Runtime Extension Contracts - V1

Runtime extensions are code-level Python APIs supplied through `FilterConfig`. They are not syntax inside the filter language.

## Regex Evaluator

`RegexEvaluator` is a callable contract:

| Input | Meaning |
|---|---|
| `pattern: str` | The unescaped string literal passed to `.regex(...)`. |
| `value: str` | The runtime string receiver value. |

The callable returns `bool`.

Default evaluator behavior:

* Uses Python `re.search`.
* Is case-sensitive.
* Raises `invalid-regex` when Python rejects the pattern.
* Preserves the underlying Python regex exception as `cause`.

Custom evaluator behavior:

* Must return `bool`.
* May raise library-defined structured exceptions directly.
* Unexpected exceptions are wrapped in `RuntimeExtensionError` from `.docs/features/.wip/00001-filter-language/assets/errors.md`, preserving the original exception as `cause`.
* Returning any value other than `bool` is an extension contract failure and is wrapped in `RuntimeExtensionError`.
* Must not change the AST.

## Global Function

`GlobalFunction` is a callable invoked by the in-memory runtime with:

| Argument | Meaning |
|---|---|
| `context` | Runtime context for the current record, alias scope, config, and source expression. |
| `arguments` | Ordered AST argument expressions from the parsed call. |

The callable returns a raw Python value. The library classifies that value through the same runtime value mapping used for record data in `.docs/features/.wip/00001-filter-language/assets/runtime-values.md`. When a global function call appears where a predicate is required, the classified return value must be `Boolean`.

The runtime context must provide these capabilities:

| Capability | Meaning |
|---|---|
| `evaluate(expression)` | Evaluate an AST expression in the current runtime context and return the raw Python value for the expression result. |
| `evaluate_predicate(expression)` | Evaluate an AST expression, require a `Boolean` result, and return a Python `bool`. |
| `argument_count()` | Return the number of argument expressions. |
| `record_index` | Current root record index, or `None` before record iteration. |
| `config` | Current `FilterConfig`. |
| direct structured exception raising | Supported way for custom functions to raise library-defined structured exceptions. |

Unexpected exceptions from custom global functions are wrapped in `RuntimeExtensionError` from `.docs/features/.wip/00001-filter-language/assets/errors.md`, preserving the original exception as `cause`. This wrapper is for extension implementation failures. Library-defined structured exceptions raised directly by an extension propagate unchanged.

If a custom global function returns a Python value that cannot be classified as a supported runtime value, the interpreter raises `unsupported-runtime-value`.

Default global functions:

| Function | Arity | Evaluation |
|---|---|---|
| `and` | at least 1 | Evaluates predicate arguments left to right; returns false on the first false; short-circuits unreached arguments. |
| `or` | at least 1 | Evaluates predicate arguments left to right; returns true on the first true; short-circuits unreached arguments. |
| `not` | exactly 1 | Evaluates its predicate argument once and returns the negated Boolean. |

All function arity failures use `wrong-argument-count`.
