# Filter Language - COCA Spec

## Context

This feature is a new Python backend library for defining, parsing, validating, and interpreting a small filter language. The library is intended to be installable by other developers and embedded into their own Python projects rather than tied to one specific web application.

The language exists because dynamic application filters were becoming complex enough to resemble a programming language. Instead of continuing with ad hoc filter construction, the goal is to define a proper language with explicit syntax, parsing, runtime validation, and an interpreter model that can grow over time.

The first supported use case is filtering in-memory Python records. A developer should be able to pass a filter expression string, parse it into an abstract filter tree, and evaluate that tree against runtime data.

Example valid expressions:

```text
[title].regex(".*snow white.*")
```

```text
and(
    // This is a comment
    [first_name].eq("john",),
    [last_name].regex("d.*e",),
    [age].ge(21,),
    [balance].lt(.5),
    /*
    This is a
    multiline comment
    */
    or(
        [created_at].lt("2024-04-01T00:00:00Z"),
        [created_at].gt("2024-09-01T00:00:00Z"),
    ),
    or(
        [roles].query([role], [role].[name].eq("root")),
        [permissions].query(
            [permission],
            [permission].[name].regex("osiris\\.users\\.actions\\..*")
        )
    )
)
```

The language model is object-oriented from the caller's perspective. Field references such as `[age]`, `[title]`, or `[created_at]` behave like objects with type-dependent methods, such as `.eq(...)`, `.lt(...)`, `.ge(...)`, `.regex(...)`, or `.query(...)`.

The language also includes global logical functions:

```text
and(...)
or(...)
not(...)
```

Parsing and runtime validation are separate concerns. The parser should accept syntactically valid expressions and produce an abstract filter tree without consulting runtime language objects, global function registries, method registries, host record data, or interpreter-specific method definitions. Function and method names and argument lists are parsed as generic call structure. The grammar must not know which methods exist, including `.query(...)`. Runtime validation and interpretation determine whether a global function or method exists, whether its argument count is valid, whether its argument types are valid, whether `.query(...)` alias declarations and alias scopes are valid, and whether the final expression evaluates to `Boolean`. Predicate validity is also a runtime concern: bare field references, chained path expressions, and bare paths passed as logical-function arguments may parse successfully, but the default runtime rejects them with `invalid-predicate` when they are evaluated as predicates. For example, `[age].regex(".*")` may parse successfully but should fail during runtime validation or interpretation if `age` resolves to an integer.

The abstract filter tree is a core contract of the library. The first interpreter will evaluate filters against in-memory Python dictionaries, but the interpreter model must be extensible so future implementations can translate the same abstract filter tree into other targets, such as ORM query calls, SQL predicates, or other query backends.

The abstract filter tree must be a pure data representation. It must not contain Python callables, bound host objects, compiled regex objects, or interpreter-specific state. It must preserve enough structure for all interpreters to distinguish bracketed path references, literal values, global function calls, method calls, and argument order. Alias references and `.query(...)` alias scopes are resolved by runtime validation from the generic call and path structure, not by the parser. Syntax-originated exceptions should be able to report source locations from parser output or parse diagnostics.

Each stable language version must have a stable abstract filter tree contract. The AST does not need a separate public version number in v1; AST compatibility is tied to the stable version of the filter language and library contract. The v1 `AST` contract must define a stable set of pure-data node variants for literals, bracketed paths, global function calls, and method calls. Each node must preserve argument order and source location when available.

Current known actors are Python developers using the library inside backend applications. End users may author filter strings indirectly or directly through a web application, but the library itself is developer-facing and should treat filter strings as untrusted input.

## Outcome

When v1 is complete, a Python developer can install the library and use it to parse and evaluate dynamic filter strings against a list of dictionaries.

A minimal successful demo should look like this from the developer's perspective:

1. The developer provides records as a list of Python dictionaries.
2. The developer passes a filter expression string to the library.
3. The library parses the expression into an abstract filter tree.
4. The developer passes the abstract filter tree and records to the in-memory interpreter.
5. The interpreter returns a `FinalResult` object containing only the dictionaries that match the filter and elapsed execution time in milliseconds.
6. If the filter is malformed or semantically invalid for the runtime data, the library raises structured, developer-friendly exceptions that the host application can handle.
7. If evaluation of any record encounters a runtime exception, the interpreter raises the first runtime exception and does not return partial matches.

The v1 public contract must expose these entry points:

```python
parse(query: str, config: FilterConfig | None = None) -> AST
interpret(ast: AST, data: list[dict], config: FilterConfig | None = None) -> FinalResult
evaluate(query: str, data: list[dict], config: FilterConfig | None = None) -> FinalResult
```

`parse(...)` performs syntactic parsing and parse-time validation and returns a pure abstract filter tree. `interpret(...)` performs runtime validation and in-memory evaluation for an existing abstract filter tree. `evaluate(...)` is a convenience API equivalent to parsing the query and then interpreting the resulting tree against the provided data using the same configuration object for both phases. `FinalResult` is an object with a `result` property containing the matched dictionaries returned by the in-memory interpreter and an `elapsed` property containing the elapsed execution time in milliseconds. `FinalResult.elapsed` is a non-negative `float` measured in milliseconds using a monotonic clock. It includes the full duration of the public entry point call excluding caller-side setup. Implementations must not guarantee exact precision, and tests must assert that it is numeric and non-negative rather than equal to a specific value. For `interpret(...)`, elapsed time covers runtime validation and evaluation. For `evaluate(...)`, elapsed time covers parsing, runtime validation, and evaluation. User-caused failures from these entry points are raised as library-defined structured exceptions rather than returned as ordinary values.

`FilterConfig` is the code-level configuration object for v1. If `config` is omitted, the library uses the documented default configuration. Host applications may create explicit `FilterConfig` values to override safety limits, replace the regex evaluator, and extend, replace, or remove runtime global functions. Configuration is scoped to the entry point call that receives it and must not mutate process-global language behavior.

The first version should support dictionary data such as:

```python
records = [
    {
        "first_name": "john",
        "last_name": "doe",
        "age": 28,
        "balance": 0.25,
        "roles": [{"name": "root"}],
        "permissions": [{"name": "osiris.users.actions.create"}],
        "is_active": True,
        "last_ips": [
            "10.238.115.209",
            "10.238.110.162",
        ],
        "created_at": datetime.datetime(2026, 3, 12, tzinfo=datetime.timezone.utc),
    }
]
```

The developer-visible success case is that expressions like the examples above can be parsed into an abstract filter tree and evaluated correctly against in-memory dictionaries.

The first version must support these field and value method families:

```text
eq
lt
le
gt
ge
regex
query
isNull
isTrue
isFalse
```

The first version must support these global logical functions:

```text
and
or
not
```

The library should also raise structured exceptions for invalid input. These exceptions should be useful to developers integrating the library and should cover syntax errors, missing field/path segments, invalid path access, unsupported methods, wrong argument counts, wrong argument types, invalid regex patterns, invalid temporal strings, and alias declaration or collision errors.

The abstract filter tree should be reusable across interpreters. The first interpreter evaluates in-memory dictionaries, but the same parsed tree should be suitable for future interpreters that compile or translate filters to ORM calls, SQL predicates, or other query systems.

## Constraints

- The v1 implementation must be a Python backend library.
- The parser must produce an abstract filter tree before interpretation.
- Parser output must not depend on the current record data.
- The parser must treat function and method calls as generic syntax and must not special-case runtime method names.
- Runtime validation and interpretation must determine whether methods are valid for the resolved runtime values.
- The first interpreter must support filtering a list of Python dictionaries.
- Python class instances and object attribute access are out of scope for v1.
- Filter expressions must be treated as untrusted input.
- Field visibility policy is the host application's responsibility in v1. The library does not provide a field allowlist or denylist; host applications that expose filter strings to end users must pass only records and fields that those users are allowed to query.
- The library must not use Python `eval`, `exec`, dynamic imports, object attribute access, host object method invocation, or any other Python execution primitive while parsing or evaluating filters.

### Type Model

The interpreter recognizes these runtime/internal types:

```text
String
Integer
Decimal
Boolean
List
Dictionary
Date
Time
DateTime
Null
```

Only these runtime/internal types are constructible by users as literals in filter expressions:

```text
String
Integer
Decimal
```

Examples:

```text
"john" -> String
21 -> Integer
.5 -> Decimal
```

All other runtime/internal types can only come from Python record data passed by the host application.

Python runtime values are mapped to internal runtime types before method dispatch. Mapping must be performed in an order that avoids Python subclass ambiguity: Python `None` maps to `Null`, Python `True` and `False` map to `Boolean`, Python `datetime.datetime` maps to `DateTime`, Python `datetime.date` maps to `Date`, Python `datetime.time` maps to `Time`, Python `int` values map to `Integer`, and finite Python `float` values map to `Decimal`. The integer values `0` and `1` are `Integer` values; only Python `True` and `False` map to `Boolean`. The internal `Decimal` type name describes the filter-language numeric category, not exact base-10 decimal arithmetic. Decimal comparisons involving Python `float` values use Python float comparison semantics. Non-finite Python float values, including `NaN`, `inf`, and `-inf`, are unsupported runtime values and must raise `unsupported-runtime-value` when reached.

`isNull()` is valid on any resolved field or path value, including `Null`. It returns true only when the field or path exists and resolves to Python `None`. Missing fields or path segments remain structured runtime exceptions and are never treated as null. No methods other than `isNull()` are valid on `Null` in v1.

### Configurable Safety Limits

Because filter expressions are untrusted input, the library must expose configurable safety limits for:

```text
maximum source length
maximum parse tree depth
maximum function or method arguments
maximum path depth
maximum query nesting
```

When a configured safety limit is exceeded, the library raises a structured limit-exceeded exception instead of continuing to parse or evaluate the expression.

The library must provide default safety-limit values. The exact default values may be implementation-defined for v1, but they must be documented, stable within a released version, covered by tests, and overrideable through `FilterConfig`. Filter expressions themselves cannot configure, raise, lower, or disable safety limits.

Safety-limit counting rules must be deterministic and documented. Path depth is the number of bracketed segments in a chained path. Function or method argument count excludes a trailing comma. Query nesting starts at 1 for the outermost runtime `.query(...)` call and is enforced during runtime validation because the parser treats method names generically. Parse tree depth starts at 1 for the root expression and increments for each nested global function call, method call, or path expression node.

### Syntax

- Whitespace is insignificant between tokens.
- Trailing commas are allowed in function and method argument lists.
- Line comments use `//`.
- Block comments use `/* ... */`.
- Numeric literals must support integer and decimal forms.
- String literals may use double quotes or single quotes.
- Field references use bracketed path segments.

String literals must support escaped quote characters, escaped backslashes, newline escapes, and tab escapes for both single-quoted and double-quoted strings. Supported escape sequences are `\\`, `\"`, `\'`, `\n`, and `\t`. Regex patterns are ordinary string literal values passed to the regex evaluator after string-literal unescaping. For example, `"osiris\\.users"` produces a runtime regex pattern containing `\.`.

Identifiers are ASCII-only and must not start with a digit. Each bracketed field or alias segment must match this pattern:

```text
/^\[[A-Za-z_][A-Za-z0-9_-]*\]$/
```

Function and method symbols use the same identifier rule without hyphens:

```text
/^[A-Za-z_][A-Za-z0-9_]*$/
```

Chained field access consists of one or more valid bracketed segments separated by dots.

This must be valid:

```text
[first_name] . eq ( "john" , )
```

These decimal literal forms must be valid:

```text
0.5
-0.5
5.
-5.
.5
-.5
```

Field access supports chained path segments:

```text
[first_name]
[customer].[address].[city]
```

Chained field access is valid anywhere. Each segment resolves through a dictionary key or a runtime component exposed by an internal type, such as `[created_at].[year]`.

A complete filter expression must evaluate to `Boolean`. A top-level bare field reference or chained path expression is invalid at runtime for the same reason a bare field reference is invalid as a logical-function argument. The parser may still produce an abstract filter tree for these syntactically valid expressions because predicate validation belongs to the runtime phase.

### Global Functions

Global functions are runtime language objects. The parser does not need to know which global functions exist or what arity they require. The default runtime provides `and(...)`, `or(...)`, and `not(...)`, and host applications may extend, replace, or remove global functions through `FilterConfig`.

Runtime extension is code-level extension through Python APIs, not function definition syntax inside the filter language. Custom global functions in `FilterConfig` are required for v1. The v1 custom global function contract must be documented and stable within the stable language/library version. A custom global function is registered by symbol and is invoked by the in-memory runtime with the current evaluation context and ordered argument expressions from the AST. The runtime context must provide the supported way for custom functions to evaluate argument expressions, inspect argument count, raise library-defined structured exceptions, and return a runtime value. A custom global function used where a predicate is required must return `Boolean`; otherwise the runtime raises `invalid-predicate` or `wrong-argument-type`, depending on the failing context.

For v1, custom global function extension applies to the default in-memory interpreter. Host applications may also implement additional interpreters that consume the same abstract filter tree, including SQL or ORM interpreters, but the v1 default library only needs to ship the in-memory interpreter.

Runtime validation is performed as part of `interpret(...)`. Validation that depends only on the AST and `FilterConfig` may happen before record iteration. Validation that depends on record values, path resolution, alias/root-field collisions, or runtime types happens while evaluating each record. Runtime validation follows reachability: validation errors inside an expression branch that is not evaluated because of default logical-function short-circuiting are not raised during that record evaluation, unless the error is detectable without evaluating record data or runtime values during AST/config-only validation. Evaluation fails at the first record and expression position that produces a structured runtime exception, and no partial result is returned.

`and(...)` is variadic, requires at least one argument, and evaluates arguments from left to right. It short-circuits and returns false as soon as one argument evaluates to false. It returns true only when every reached argument evaluates to true. If any reached argument evaluation raises a structured exception, the whole filter evaluation fails with that exception.

`or(...)` is variadic, requires at least one argument, and evaluates arguments from left to right. It short-circuits and returns true as soon as one argument evaluates to true. It returns false only when every reached argument evaluates to false. If any reached argument evaluation raises a structured exception, the whole filter evaluation fails with that exception.

`not(...)` accepts exactly one argument. It evaluates that argument once and returns the negated result. If the argument evaluation raises a structured exception, the whole filter evaluation fails with that exception.

Global logical functions accept predicate expressions whose evaluation result is `Boolean`. Bare field references or chained path expressions are not valid predicates unless wrapped in a method or function that produces a `Boolean` result, such as `isTrue()`, `isFalse()`, `isNull()`, a comparison method, `regex()`, `query()`, `and(...)`, `or(...)`, or `not(...)`.

### Runtime Method Model

`List` supports:

```text
isNull()
query(<item_alias>, <query>)
```

`query` is only valid on runtime Python lists in v1. It returns true when at least one item in the list satisfies the nested query.

If any item evaluation inside `.query(...)` raises a structured runtime exception, the whole filter evaluation fails with that exception. Invalid items are not silently skipped. Items that evaluate successfully but do not satisfy the nested query simply count as nonmatches.

```text
[roles].query([role], [role].[name].eq("root"))
[last_ips].query([ip], [ip].regex("10\\.238\\.115\\..*"))
```

The item alias is scoped only to the query body where it is declared. After that scope ends, the same bracketed name no longer resolves as that alias. The parser treats `.query(...)` as an ordinary method call; the `.query(...)` runtime method contract is responsible for validating that the first argument is a single bracketed segment and for establishing alias scope while validating and interpreting the query body.

Alias collisions are invalid within the currently active alias scope. A `.query(...)` alias declaration must be rejected if it collides with another alias already active in an outer or current query scope. Reusing the same alias name in separate sibling `.query(...)` calls is valid because the first alias scope has ended before the second begins.

A `.query(...)` alias declaration must also be rejected at runtime if the root record being evaluated contains a dictionary key with the same name as the alias. This avoids ambiguous references between query aliases and root fields. Because this rule depends on the current root record, the interpreter may fail when evaluation reaches the first conflicting record; it does not need to pre-scan the entire input before filtering.

A first bracketed segment resolves as an alias reference only when its segment name matches an alias currently in scope. Otherwise, it resolves as a field reference against the current root record. Subsequent bracketed segments resolve against the previous path value, whether the path started from a root field or an alias. Inside nested `.query(...)` bodies, outer aliases remain visible unless shadowed, and shadowing is rejected by the alias-collision rule.

These alias uses are valid:

```text
and(
    [roles].query([role], or([role].[name].eq("root"), [role].[name].eq("super_root")))
)
```

```text
or(
    [roles].query([role], [role].[name].eq("root")),
    [roles].query([role], [role].[name].eq("super_root"))
)
```

```text
and(
    [roles].query(
        [role],
        [role].[permissions].query([permission], [permission].[name].eq("osiris.users.actions.read"))
    ),
    [permissions].query([permission], [permission].[name].eq("datahub.dashboards.actions.create"))
)
```

```text
[roles].query(
    [role],
    [role].[permissions].query(
        [permission],
        and(
            [role].[name].eq("root"),
            [permission].[name].eq("osiris.users.actions.read")
        )
    )
)
```

These alias uses are invalid:

```text
[roles].query([role], [role].[permissions].query([role], [role].[name].eq("osiris.users.actions.read")))
```

The nested `[role]` declaration is invalid because `[role]` is already an active alias in the outer query scope.

```text
[last_ips].query([ip], [ip].eq("10.238.115.209"))
```

The `[ip]` alias declaration is invalid when the root record contains a dictionary key named `ip`.

`Dictionary` supports chained path-segment access through dictionary keys:

```text
[customer].[address].[city]
[role].[name]
```

Bracketed path segments can only name string keys representable by the filter-language identifier syntax. Dictionary keys that are not strings are ignored by path lookup and alias/root-field collision checks in v1.

`Boolean` supports:

```text
isNull()
isTrue()
isFalse()
```

`Integer` and `Decimal` support:

```text
isNull()
isTrue()
isFalse()
eq(<integer_or_decimal>)
gt(<integer_or_decimal>)
ge(<integer_or_decimal>)
lt(<integer_or_decimal>)
le(<integer_or_decimal>)
```

Numeric truthiness follows zero/nonzero behavior:

```text
0.isTrue() -> false
nonzero.isTrue() -> true
0.isFalse() -> true
nonzero.isFalse() -> false
```

`String` supports:

```text
isNull()
eq(<string>)
gt(<string>)
ge(<string>)
lt(<string>)
le(<string>)
regex(<regex_pattern>)
```

String ordering uses lexicographic comparison. `regex` uses the regex evaluator from `FilterConfig`. The default evaluator uses Python `re.search` semantics, not glob or wildcard semantics. Regex matching is case-sensitive. Invalid regex patterns are runtime validation/interpreter exceptions, not parse exceptions.

The default Python regex engine can be vulnerable to catastrophic backtracking when host applications accept regex patterns from untrusted end users. The library must explicitly document this risk. Host applications that expose untrusted regex input are responsible for enforcing an execution timeout or supplying a safer regex evaluator through `FilterConfig`. When a host application supplies a replacement regex evaluator, `.regex(...)` dispatches to that evaluator without changing the abstract filter tree.

`Date` supports comparison against `String` arguments:

```text
isNull()
eq(<string>)
gt(<string>)
ge(<string>)
lt(<string>)
le(<string>)
```

The argument remains a `String` literal in the language. The `Date` method accepts that `String` and performs runtime parsing/validation according to the `Date` method contract.

`Date` exposes:

```text
[year]
[month]
[day]
```

These components behave as integers and support `eq`, `gt`, `ge`, `lt`, and `le` against integer arguments.

`Time` supports comparison against `String` arguments:

```text
isNull()
eq(<string>)
gt(<string>)
ge(<string>)
lt(<string>)
le(<string>)
```

The runtime `Time` value and the string argument must be timezone-aware for direct time comparison. Time comparison normalizes offsets into UTC time-of-day before comparing. Because `Time` has no date component, day rollover is ignored in a time-only context. For example, `09:30:00Z` and `06:30:00-03:00` compare as equal.

`Time` exposes:

```text
[hour]
[minute]
[second]
```

These components behave as integers and support numeric comparison methods.

`DateTime` supports comparison against `String` arguments:

```text
isNull()
eq(<string>)
gt(<string>)
ge(<string>)
lt(<string>)
le(<string>)
```

The runtime `DateTime` value and the string argument must be timezone-aware for direct datetime comparison. DateTime comparison normalizes offsets and compares the represented instant.

`DateTime` exposes:

```text
[year]
[month]
[day]
[hour]
[minute]
[second]
```

These components behave as integers and support numeric comparison methods.

### Temporal String Formats

`Date` comparison methods accept ISO 8601 `String` values formatted as:

```text
YYYY-MM-DD
```

`Time` comparison methods accept timezone-aware ISO 8601 `String` values. Accepted examples:

```text
09:30:00Z
09:30:00+00:00
09:30:00-03:00
```

`DateTime` comparison methods accept timezone-aware ISO 8601 `String` values. Accepted examples:

```text
2024-01-01T12:30:00Z
2024-01-01T12:30:00+00:00
2024-01-01T12:30:00-03:00
```

### Null and Missing Path Behavior

`isNull()` means the field or path segment exists and its resolved value is Python `None`.

Missing dictionary keys are not null. Missing fields or missing nested path segments raise structured runtime exceptions.

### Errors

The library must raise structured, developer-friendly exceptions for these stable error identities:

```text
syntax-error
missing-field-or-path-segment
invalid-path-access
invalid-alias-declaration
unsupported-method
wrong-argument-count
wrong-argument-type
invalid-regex
invalid-temporal-string
temporal-awareness-mismatch
invalid-predicate
alias-collision
runtime-alias-root-field-collision
limit-exceeded
invalid-record
unsupported-runtime-value
```

Structured exceptions must include a stable programmatic error identity and developer-readable message. The stable identity may be represented by the concrete exception class, by a string `code` field, or by both, but host applications must be able to distinguish every listed error identity without parsing the message. Structured exceptions must inherit from a common library-defined base exception, such as `FilterError`. Parser-originated exceptions must inherit from a syntax-oriented base class, such as `FilterSyntaxError`. Runtime validation and interpretation exceptions must inherit from a runtime-oriented base class, such as `FilterRuntimeError`. Each listed error identity may be represented by a dedicated subclass of the relevant syntax or runtime base class. A separate `phase` field is not required because the exception hierarchy identifies the error category.

Structured exceptions must expose stable machine-readable context fields in addition to the developer-readable message. All structured exceptions must expose `message`. A `code` field is optional when the concrete exception class already provides the stable programmatic identity. Fields that do not apply may be omitted or set to `None`, but field names must not vary by implementation. Exceptions caused by custom runtime extensions must either be raised as library-defined structured exceptions by the extension or wrapped in a library-defined structured exception that preserves the original exception as `cause`.

Minimum stable context fields by error identity:

| Error identity | Required context fields |
| --- | --- |
| `syntax-error` | `source_span` |
| `missing-field-or-path-segment` | `path`, `missing_segment`, `record_index` |
| `invalid-path-access` | `path`, `receiver_type`, `record_index` |
| `invalid-alias-declaration` | `alias`, `source_span` |
| `unsupported-method` | `path`, `receiver_type`, `method`, `record_index` |
| `wrong-argument-count` | `target`, `expected`, `received` |
| `wrong-argument-type` | `target`, `argument_index`, `expected`, `received` |
| `invalid-regex` | `pattern`, `argument_index`, `cause` |
| `invalid-temporal-string` | `target_type`, `value`, `method`, `argument_index` |
| `temporal-awareness-mismatch` | `target_type`, `value`, `method`, `argument_index` |
| `invalid-predicate` | `target`, `source_span` |
| `alias-collision` | `alias` |
| `runtime-alias-root-field-collision` | `alias`, `record_index` |
| `limit-exceeded` | `limit_name`, `limit_value`, `actual_value` |
| `invalid-record` | `record_index`, `received` |
| `unsupported-runtime-value` | `path`, `python_type`, `record_index` |

`source_span` identifies the relevant source range when the error is tied to query syntax. `record_index` identifies the input record that caused a runtime failure; it may be `None` for failures that occur before record iteration. `cause` preserves an underlying Python exception or extension-provided failure when available.

All function and method arity failures use the stable error identity `wrong-argument-count`. Empty `and()`, empty `or()`, and invalid `not(...)` arity are specific instances of that error and must include the target name plus expected and received argument counts.

All invalid date, time, and datetime string failures use the stable error identity `invalid-temporal-string`. The exception context must identify whether the failed target type was `Date`, `Time`, or `DateTime`.

`invalid-record` is used when a supported runtime data type appears in a place the in-memory interpreter does not accept, such as passing a dictionary where the interpreter requires the top-level list of records, or passing a list containing a supported non-dictionary value where a top-level record dictionary is required. `unsupported-runtime-value` is used when the interpreter receives or reaches a Python value whose type cannot be mapped to a supported internal runtime type, including non-finite Python float values.

### Non-Goals

The v1 library does not support:

```text
Python object attribute access
Python eval/exec/dynamic-import execution
host object method invocation
list literals
dictionary literals
boolean literals
null literals
date literals
time literals
datetime literals
built-in SQL translation
built-in ORM translation
frontend execution
mutation or side effects
method definition syntax inside filter expressions
case-insensitive regex matching
glob or wildcard search semantics
```

## Assertions

### Happy Path

- When the developer parses `[first_name].eq("john")` and evaluates it against a list of dictionaries, then only records whose `first_name` value is exactly `"john"` are returned.
- When the developer calls `parse(query)`, then the library returns an `AST` without consulting runtime data, function registries, method registries, or interpreter-specific method definitions.
- When the developer calls `interpret(ast, data)`, then the library validates the `AST` against the in-memory runtime model and returns a `FinalResult` whose `result` contains only the matching dictionaries and whose `elapsed` contains elapsed runtime validation and evaluation time in milliseconds.
- When the developer calls `evaluate(query, data)`, then the library produces the same `FinalResult.result` as calling `parse(query)` and then `interpret(ast, data)`.
- When `interpret(...)` or `evaluate(...)` succeeds, then `FinalResult.elapsed` is a non-negative `float` millisecond duration measured with a monotonic clock.
- When the developer omits `config`, then `parse(...)`, `interpret(...)`, and `evaluate(...)` use the documented default `FilterConfig`.
- When the developer calls `evaluate(query, data, config=custom_config)`, then the library uses the same `FilterConfig` for both parsing and interpretation.
- When the developer parses `[first_name] . eq ( "john" , )`, then the parser accepts it and produces the same abstract filter tree as `[first_name].eq("john")`.
- When the developer parses a filter containing `//` line comments or `/* ... */` block comments, then comments are ignored and do not affect the abstract filter tree.
- When the developer parses a string literal containing escaped quotes or escaped backslashes, then the abstract filter tree stores the unescaped string value.
- When the developer evaluates `[age].ge(21)` against integer values, then integer comparison uses numeric ordering.
- When the developer evaluates `[balance].lt(.5)` against decimal values, then decimal comparison uses numeric ordering.
- When the developer evaluates `[age].eq(.5)` or `[balance].eq(1)`, then integer and decimal values may be compared through numeric equality.
- When the developer evaluates `[name].gt("Jane")`, then string comparison uses lexicographic ordering.
- When the developer evaluates `[title].regex(".*snow white.*")`, then records match only when the string value satisfies the regex pattern with case-sensitive matching.
- When the developer evaluates `[customer].[address].[city].eq("Paris")`, then the interpreter resolves each path segment through dictionary keys and evaluates the final value.
- When the developer evaluates `[roles].query([role], [role].[name].eq("root"))`, then the expression returns true if at least one list item satisfies the nested query.
- When the developer evaluates `[last_ips].query([ip], [ip].regex("10\\.238\\.115\\..*"))`, then the expression returns true if at least one scalar list item satisfies the regex.
- When the developer evaluates sibling query calls such as `or([roles].query([role], [role].[name].eq("root")), [roles].query([role], [role].[name].eq("super_root")))`, then reusing `[role]` is valid because each alias declaration belongs to a separate query scope.
- When the developer evaluates a nested query such as `[roles].query([role], [role].[permissions].query([permission], and([role].[name].eq("root"), [permission].[name].eq("osiris.users.actions.read"))))`, then the inner query may reference both the outer `[role]` alias and the inner `[permission]` alias.
- When the developer evaluates `[is_active].isTrue()`, then the expression returns true only for Python `True`.
- When the developer evaluates `[is_active].isTrue()` against Python `True` or `False`, then the runtime value is treated as `Boolean` and not as `Integer`.
- When the developer evaluates `[count].isTrue()`, then zero is false and nonzero numeric values are true.
- When the developer evaluates `[deleted_at].isNull()` and `deleted_at` exists with value `None`, then the expression returns true.
- When the developer evaluates `[created_date].gt("2024-01-01")` against a Python `datetime.date` value, then the receiver remains a runtime `Date`, the argument remains a language `String`, and the `Date.gt` method parses and compares the string according to the `Date` contract.
- When the developer evaluates `[start_time].lt("09:30:00-03:00")` against a timezone-aware Python `datetime.time` value, then the receiver remains a runtime `Time`, the argument remains a language `String`, and the `Time.lt` method parses and compares the string according to the `Time` contract.
- When the developer evaluates `[created_at].lt("2024-01-01T12:30:00Z")` against a timezone-aware Python `datetime.datetime` value, then the receiver remains a runtime `DateTime`, the argument remains a language `String`, and the `DateTime.lt` method parses and compares the string according to the `DateTime` contract.
- When the developer evaluates `[created_at].[year].eq(2026)` or `[created_at].[hour].ge(9)`, then the accessed temporal component behaves as an integer.
- When the host application supplies a custom regex evaluator through `FilterConfig`, then `.regex(...)` uses that evaluator without changing the parsed abstract filter tree.
- When the host application registers a custom global function through `FilterConfig`, then the parser still treats that function call as generic syntax and the in-memory runtime dispatches the call through the configured runtime function.
- When the developer parses an expression, then the produced abstract filter tree can be passed to the in-memory interpreter without reparsing the original source.

### Edge Cases

- When a method call includes a trailing comma after the final argument, then parsing succeeds.
- When a decimal literal is written as `5.`, `-5.`, `.5`, or `-.5`, then parsing succeeds and the value is represented as a decimal.
- When `and(...)` receives one argument, then it evaluates that single argument.
- When `or(...)` receives one argument, then it evaluates that single argument.
- When `and(...)` evaluates arguments left to right and reaches an argument that evaluates to false, then it returns false without evaluating later arguments.
- When `or(...)` evaluates arguments left to right and reaches an argument that evaluates to true, then it returns true without evaluating later arguments.
- When an unreached short-circuited branch would raise a runtime validation or interpretation exception only after record-dependent evaluation, then that exception is not raised for that record.
- When a `.query(...)` list is empty, then the query result is false.
- When a `.query(...)` list contains dictionaries and scalar values, then each item is evaluated according to the nested query and its runtime type.
- When a `.query(...)` list contains an item that evaluates successfully but does not match the nested query, then evaluation continues to later items.
- When `isNull()` is called on an existing field whose value is not `None`, then it returns false.
- When a regex pattern matches only part of a string, then `.regex(...)` returns true because it uses Python `re.search` semantics rather than full-string matching.
- When the developer evaluates any valid filter against an empty list of records, then the interpreter returns a `FinalResult` whose `result` is an empty list without raising an exception.

### Error States

- When malformed syntax is parsed, then the library raises a structured syntax exception with source location.
- When a bracketed field or alias segment contains non-ASCII characters or starts with a digit, then parsing raises a structured syntax exception with source location.
- When a function or method symbol contains non-ASCII characters, starts with a digit, or contains a hyphen, then parsing raises a structured syntax exception with source location.
- When a string literal contains an unsupported or unterminated escape sequence, then parsing raises a structured syntax exception with source location.
- When a complete filter expression is a bare field reference or chained path expression, then the library raises a structured invalid-predicate exception.
- When evaluation reaches a missing field or nested path segment, then the library raises a structured runtime exception instead of treating the value as null.
- When evaluation attempts chained path access through a non-dictionary value that does not expose the requested internal component, then the library raises a structured invalid-path-access exception.
- When `[age].regex(".*")` is evaluated and `age` is an integer, then the interpreter raises a structured unsupported-method exception.
- When `[first_name].eq(1)` is evaluated and `first_name` is a string, then the interpreter raises a structured wrong-argument-type exception.
- When `[age].ge("21")` is evaluated and `age` is an integer, then the interpreter raises a structured wrong-argument-type exception because numeric comparison requires an integer or decimal argument.
- When `[roles].query([role], [role].[name].eq("root"))` is evaluated and `roles` resolves to a type that does not define `.query(...)`, then the interpreter raises a structured unsupported-method exception.
- When `.query(...)` receives a first argument that is not a single bracketed path segment, then the interpreter raises a structured invalid-alias-declaration exception.
- When any item evaluation inside `.query(...)` raises a structured runtime exception, then the whole filter evaluation fails with that exception instead of skipping the invalid item.
- When `and(...)` or `or(...)` reaches an argument that raises a structured runtime exception, then the whole filter evaluation fails with that exception.
- When a bracketed name is not an active alias, then it resolves as a root field reference rather than as an out-of-scope alias reference.
- When `.query([role], ...)` is declared inside a scope that already contains an active alias named `role`, then the library raises a structured alias-collision exception.
- When `.query([role], ...)` is evaluated and the first reached root record containing a dictionary key named `role` is encountered, then the interpreter raises a structured runtime alias/root-field collision exception.
- When `.query([ip], ...)` is evaluated against a root record that contains a dictionary key named `ip`, then the interpreter raises a structured runtime alias/root-field collision exception even if `[ip]` would otherwise be a valid alias for scalar list items.
- When an invalid regex pattern is passed to `.regex(...)`, then the interpreter raises a structured invalid-regex exception at runtime.
- When an invalid date, time, or datetime string is passed to the corresponding runtime type method, then the interpreter raises a structured invalid-temporal-string exception.
- When the default `and()` global function is evaluated with no arguments, then the interpreter raises a structured wrong-argument-count exception.
- When the default `or()` global function is evaluated with no arguments, then the interpreter raises a structured wrong-argument-count exception.
- When the default `not(...)` global function receives zero or more than one argument, then the interpreter raises a structured wrong-argument-count exception.
- When a bare field reference or chained path expression is passed to a default logical function where that function requires a predicate expression, then the interpreter raises a structured invalid-predicate exception.
- When parsing or evaluation exceeds a configured source length, parse tree depth, argument count, path depth, or query nesting limit, then the library raises a structured limit-exceeded exception.
- When one call uses a `FilterConfig` with custom safety limits or runtime extensions, then those settings do not change the behavior of later calls that omit `config` or use a different `FilterConfig`.
- When direct time or datetime comparison is attempted with a non-timezone-aware runtime value or string argument, then the interpreter raises a structured temporal-awareness-mismatch exception.
- When a `Time` comparison uses different timezone offsets, then the interpreter normalizes both values to UTC time-of-day and ignores date rollover; for example, `09:30:00Z` and `06:30:00-03:00` compare as equal.
- When a supported runtime data type appears in a place the interpreter does not accept, then the interpreter raises a structured invalid-record exception.
- When evaluation reaches a Python `float` value that is `NaN`, `inf`, or `-inf`, then the interpreter raises a structured unsupported-runtime-value exception.
- When evaluation reaches a Python value whose type cannot be mapped to a supported internal runtime type, then the interpreter raises a structured unsupported-runtime-value exception.
- When dictionary data contains non-string keys, then path lookup and alias/root-field collision checks ignore those keys.
- When a structured exception is raised, then the exception exposes its stable programmatic identity, developer-readable message, and the applicable machine-readable context fields defined for that error identity.

### Anti-Behaviors

- The interpreter must not evaluate Python object attributes or class instances in v1.
- The parser and interpreter must not use Python `eval`, `exec`, dynamic imports, host object method invocation, or other Python execution primitives.
- The parser must not accept list literals, dictionary literals, boolean literals, null literals, date literals, time literals, or datetime literals.
- `isNull()` must not treat missing fields or missing path segments as null.
- `.regex()` must not use glob semantics; `*` must follow regex rules.
- `.regex()` must not perform case-insensitive matching unless a future explicit option adds that behavior.
- The default `not(...)` global function must not accept more than one argument.
- The default `and(...)` and `or(...)` global functions must not accept zero arguments.
- Runtime validation must not be performed during parsing in a way that requires record data.
- Evaluating a filter must not mutate the input records.
- The v1 default in-memory interpreter must not translate filters into SQL or ORM queries.

### Integration

- When a host application passes a list of dictionaries into the in-memory interpreter, then the interpreter evaluates each dictionary independently and returns a `FinalResult.result` list containing the matching records without mutating the original list or dictionaries.
- When multiple records match, then `FinalResult.result` contains matching dictionaries in their original input order.
- When evaluation succeeds, then dictionaries in `FinalResult.result` are the original input dictionary objects.
- When evaluation of any dictionary in the input list raises a runtime exception, then the interpreter fails the whole evaluation at the first runtime exception and does not return partial matches.
- When the host application reuses a parsed abstract filter tree against multiple record lists, then the interpreter can evaluate the tree without reparsing the source expression.
- When future interpreters are added, then they must consume the same abstract filter tree contract for the stable language version rather than requiring a separate parser.
