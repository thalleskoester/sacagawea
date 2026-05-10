# Public API Contract - V1

The package root must export these stable public names:

| Name | Kind | Contract |
|---|---|---|
| `parse` | function | Accepts `query: str` and optional `FilterConfig`; returns `AST`; performs only syntactic parsing and parse-time validation. |
| `interpret` | function | Accepts `ast: AST`, `data: list[dict]`, and optional `FilterConfig`; returns `FinalResult`; performs runtime validation and in-memory evaluation. |
| `evaluate` | function | Accepts `query: str`, `data: list[dict]`, and optional `FilterConfig`; returns `FinalResult`; equivalent to `parse` followed by `interpret` using the same config object. |
| `FilterConfig` | immutable data object | Constructible with keyword fields from `filter-config.md`; exposes `FilterConfig.default()` for the documented default call-scoped configuration. |
| `SafetyLimits` | immutable data object | Constructible with keyword fields from `safety-limits.md`; exposes `SafetyLimits.default()` for the documented deterministic default limits. |
| `FinalResult` | immutable data object | Exposes `result` and `elapsed`. |
| `AST` | immutable data object | Holds the parsed root expression. |
| `SourceSpan` | immutable data object | Source range metadata used by AST nodes and syntax-related errors. |
| `StringLiteral` | immutable data object | AST node for string literals. |
| `IntegerLiteral` | immutable data object | AST node for integer literals. |
| `DecimalLiteral` | immutable data object | AST node for decimal literals. |
| `PathExpression` | immutable data object | AST node for bracketed path expressions. |
| `GlobalFunctionCall` | immutable data object | AST node for generic global function calls. |
| `MethodCall` | immutable data object | AST node for generic method calls on path expressions. |
| `FilterError` | exception class | Common base for library-defined structured exceptions. |
| `FilterSyntaxError` | exception class | Base for parser-originated syntax and parse-time validation failures. |
| `FilterRuntimeError` | exception class | Base for runtime validation, interpretation, and extension failures. |
| `FilterParseError` | exception class | Dedicated class for `syntax-error`. |
| `MissingFieldOrPathSegmentError` | exception class | Dedicated class for `missing-field-or-path-segment`. |
| `InvalidPathAccessError` | exception class | Dedicated class for `invalid-path-access`. |
| `InvalidAliasDeclarationError` | exception class | Dedicated class for `invalid-alias-declaration`. |
| `UnsupportedMethodError` | exception class | Dedicated class for `unsupported-method`. |
| `WrongArgumentCountError` | exception class | Dedicated class for `wrong-argument-count`. |
| `WrongArgumentTypeError` | exception class | Dedicated class for `wrong-argument-type`. |
| `InvalidRegexError` | exception class | Dedicated class for `invalid-regex`. |
| `InvalidTemporalStringError` | exception class | Dedicated class for `invalid-temporal-string`. |
| `TemporalAwarenessMismatchError` | exception class | Dedicated class for `temporal-awareness-mismatch`. |
| `InvalidPredicateError` | exception class | Dedicated class for `invalid-predicate`. |
| `AliasCollisionError` | exception class | Dedicated class for `alias-collision`. |
| `RuntimeAliasRootFieldCollisionError` | exception class | Dedicated class for `runtime-alias-root-field-collision`. |
| `LimitExceededError` | exception class | Public catch-all base class for all `limit-exceeded` failures. |
| `ParseLimitExceededError` | exception class | Dedicated class for parse-time `limit-exceeded` failures. |
| `RuntimeLimitExceededError` | exception class | Dedicated class for runtime `limit-exceeded` failures. |
| `InvalidRecordError` | exception class | Dedicated class for `invalid-record`. |
| `UnsupportedRuntimeValueError` | exception class | Dedicated class for `unsupported-runtime-value`. |
| `RuntimeExtensionError` | exception class | Dedicated class for `runtime-extension-error`. |

`FinalResult.result` contains the original matching dictionary objects in input order. `FinalResult.elapsed` is a non-negative `float` measured in milliseconds with a monotonic clock.

All public immutable data objects must expose readable fields by name. Public constructors must not require process-global state or runtime data.
