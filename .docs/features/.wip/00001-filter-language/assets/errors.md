# Structured Error Contract - V1

Every structured exception exposes:

| Field | Meaning |
|---|---|
| `message` | Developer-readable message. |
| `code` | Stable programmatic identity. |
| `cause` | Underlying Python or extension exception when available, otherwise `None`. |

Exception identity strategy:

* Every error identity has a dedicated public exception class.
* A single stable code value may have phase-specific subclasses when required by the syntax/runtime base hierarchy.
* Every dedicated exception class exposes the fixed `code` value listed below.
* Callers may distinguish failures by exception class or by `code`.
* Code values are stable kebab-case strings.

Exception hierarchy:

| Base | Meaning |
|---|---|
| `FilterError` | Common base for all library-defined structured exceptions. |
| `FilterSyntaxError` | Base for parser-originated syntax and parse-time validation failures. |
| `FilterRuntimeError` | Base for runtime validation and interpretation failures. |
| `LimitExceededError` | Common public base for all `limit-exceeded` failures. This class is not raised directly. |

Required error identities and context fields:

| Class | Base | Code | Required context fields |
|---|---|---|---|
| `FilterParseError` | `FilterSyntaxError` | `syntax-error` | `source_span` |
| `MissingFieldOrPathSegmentError` | `FilterRuntimeError` | `missing-field-or-path-segment` | `path`, `missing_segment`, `record_index` |
| `InvalidPathAccessError` | `FilterRuntimeError` | `invalid-path-access` | `path`, `receiver_type`, `record_index` |
| `InvalidAliasDeclarationError` | `FilterRuntimeError` | `invalid-alias-declaration` | `alias`, `source_span` |
| `UnsupportedMethodError` | `FilterRuntimeError` | `unsupported-method` | `path`, `receiver_type`, `method`, `record_index` |
| `WrongArgumentCountError` | `FilterRuntimeError` | `wrong-argument-count` | `target`, `expected`, `received` |
| `WrongArgumentTypeError` | `FilterRuntimeError` | `wrong-argument-type` | `target`, `argument_index`, `expected`, `received` |
| `InvalidRegexError` | `FilterRuntimeError` | `invalid-regex` | `pattern`, `argument_index`, `cause` |
| `InvalidTemporalStringError` | `FilterRuntimeError` | `invalid-temporal-string` | `target_type`, `value`, `method`, `argument_index` |
| `TemporalAwarenessMismatchError` | `FilterRuntimeError` | `temporal-awareness-mismatch` | `target_type`, `value`, `method`, `argument_index` |
| `InvalidPredicateError` | `FilterRuntimeError` | `invalid-predicate` | `target`, `source_span` |
| `AliasCollisionError` | `FilterRuntimeError` | `alias-collision` | `alias` |
| `RuntimeAliasRootFieldCollisionError` | `FilterRuntimeError` | `runtime-alias-root-field-collision` | `alias`, `record_index` |
| `ParseLimitExceededError` | `LimitExceededError`, `FilterSyntaxError` | `limit-exceeded` | `limit_name`, `limit_value`, `actual_value` |
| `RuntimeLimitExceededError` | `LimitExceededError`, `FilterRuntimeError` | `limit-exceeded` | `limit_name`, `limit_value`, `actual_value` |
| `InvalidRecordError` | `FilterRuntimeError` | `invalid-record` | `record_index`, `received` |
| `UnsupportedRuntimeValueError` | `FilterRuntimeError` | `unsupported-runtime-value` | `path`, `python_type`, `record_index` |
| `RuntimeExtensionError` | `FilterRuntimeError` | `runtime-extension-error` | `extension_name`, `record_index`, `cause` |

`RuntimeExtensionError` is used only when a custom runtime extension raises an unexpected non-library exception and no more specific spec-listed identity applies.

`ParseLimitExceededError` is used for parse-time limits: source length, parse tree depth, function or method argument count, and path depth. `RuntimeLimitExceededError` is used for runtime limits such as `.query(...)` nesting. Both expose the stable `limit-exceeded` code and both are catchable through `LimitExceededError`.

Each implementation phase must introduce the exact error identity and context fields for the behavior it adds. Later documentation phases may audit coverage, but they must not postpone error identity design.
