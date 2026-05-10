# Assertion Coverage Contract - V1

The implementation must maintain an assertion matrix that maps each assertion below to one of these statuses:

| Status | Meaning |
|---|---|
| `covered` | The assertion is covered by one or more executable tests. |
| `covered-by-contract` | The assertion is guaranteed by a public contract test, type-level test, or invariant test rather than a dedicated scenario test. |

The matrix must not use documented exclusions for v1 assertions. If an assertion cannot be implemented, the spec and plan must be revised before the implementation can be considered complete.

## Happy Path

| ID | Assertion |
|---|---|
| `HP-001` | Parsing and evaluating `[first_name].eq("john")` returns only records whose `first_name` is exactly `"john"`. |
| `HP-002` | `parse(query)` returns an `AST` without consulting runtime data, registries, or interpreter-specific methods. |
| `HP-003` | `interpret(ast, data)` validates against the in-memory runtime model and returns `FinalResult.result` plus elapsed validation/evaluation time. |
| `HP-004` | `evaluate(query, data)` returns the same `FinalResult.result` as `parse(query)` followed by `interpret(ast, data)`. |
| `HP-005` | Successful `interpret(...)` or `evaluate(...)` sets `FinalResult.elapsed` to a non-negative `float` millisecond duration from a monotonic clock. |
| `HP-006` | Omitted `config` uses the documented default `FilterConfig` for `parse`, `interpret`, and `evaluate`. |
| `HP-007` | `evaluate(query, data, config=custom_config)` uses the same config for parsing and interpretation. |
| `HP-008` | `[first_name] . eq ( "john" , )` parses to the same expression topology, literal values, path segments, function names, method names, and argument order as `[first_name].eq("john")`, excluding source spans. |
| `HP-009` | `//` line comments and `/* ... */` block comments are ignored as trivia and do not create AST nodes; source spans still reflect the actual input source. |
| `HP-010` | Escaped quotes and backslashes in string literals are stored as unescaped string values in the AST. |
| `HP-011` | `[age].ge(21)` compares integer values using numeric ordering. |
| `HP-012` | `[balance].lt(.5)` compares decimal values using numeric ordering. |
| `HP-013` | Integer and decimal values may be compared through numeric equality, such as `[age].eq(.5)` or `[balance].eq(1)`. |
| `HP-014` | `[name].gt("Jane")` compares strings using lexicographic ordering. |
| `HP-015` | `[title].regex(".*snow white.*")` matches strings with case-sensitive regex semantics. |
| `HP-016` | `[customer].[address].[city].eq("Paris")` resolves chained dictionary path segments before evaluating the final value. |
| `HP-017` | `[roles].query([role], [role].[name].eq("root"))` returns true when at least one list item satisfies the nested query. |
| `HP-018` | `[last_ips].query([ip], [ip].regex("10\\.238\\.115\\..*"))` supports scalar list item aliases and regex matching. |
| `HP-019` | Sibling `.query(...)` calls may reuse the same alias name because each declaration has its own scope. |
| `HP-020` | Nested `.query(...)` calls may reference both outer and inner aliases. |
| `HP-021` | `[is_active].isTrue()` returns true only for Python `True`. |
| `HP-022` | Python `True` and `False` are runtime `Boolean` values, not `Integer` values. |
| `HP-023` | `[count].isTrue()` treats zero as false and nonzero numeric values as true. |
| `HP-024` | `[deleted_at].isNull()` returns true when the existing field value is `None`. |
| `HP-025` | `Date` comparisons keep the receiver as runtime `Date`, parse the string argument, and compare by the `Date` contract. |
| `HP-026` | `Time` comparisons keep the receiver as runtime `Time`, parse the string argument, and compare by the `Time` contract. |
| `HP-027` | `DateTime` comparisons keep the receiver as runtime `DateTime`, parse the string argument, and compare by the `DateTime` contract. |
| `HP-028` | Temporal components such as `[created_at].[year]` and `[created_at].[hour]` behave as integer comparison values. |
| `HP-029` | A custom regex evaluator supplied through `FilterConfig` is used by `.regex(...)` without changing the AST. |
| `HP-030` | A custom global function supplied through `FilterConfig` parses as generic syntax and dispatches through the in-memory runtime config. |
| `HP-031` | A parsed AST can be passed to the in-memory interpreter without reparsing the source. |

## Edge Cases

| ID | Assertion |
|---|---|
| `EC-001` | A trailing comma after the final method or function argument parses successfully. |
| `EC-002` | Decimal literals `5.`, `-5.`, `.5`, and `-.5` parse successfully as decimals. |
| `EC-003` | `and(...)` accepts one argument and evaluates it. |
| `EC-004` | `or(...)` accepts one argument and evaluates it. |
| `EC-005` | `and(...)` evaluates left to right and short-circuits false without evaluating later arguments. |
| `EC-006` | `or(...)` evaluates left to right and short-circuits true without evaluating later arguments. |
| `EC-007` | Record-dependent errors in unreached short-circuited branches are not raised for that record. |
| `EC-008` | `.query(...)` over an empty list returns false. |
| `EC-009` | `.query(...)` over mixed dictionary and scalar list items evaluates each item according to the nested query and runtime type. |
| `EC-010` | `.query(...)` continues after successfully evaluated nonmatching items. |
| `EC-011` | `isNull()` on an existing non-`None` value returns false. |
| `EC-012` | `.regex(...)` returns true for partial matches using Python `re.search` semantics, not full-string matching. |
| `EC-013` | Evaluating any valid filter against an empty record list returns an empty `FinalResult.result` without error. |
| `EC-014` | `Time` comparisons with different offsets normalize to UTC time-of-day and ignore date rollover. |

## Error States

| ID | Assertion |
|---|---|
| `ERR-001` | Malformed syntax raises a structured syntax exception with source location. |
| `ERR-002` | Bracketed field or alias segments with non-ASCII characters or a leading digit raise structured syntax errors. |
| `ERR-003` | Function or method symbols with non-ASCII characters, a leading digit, or hyphens raise structured syntax errors. |
| `ERR-004` | Unsupported or unterminated string escape sequences raise structured syntax errors. |
| `ERR-005` | A complete bare field reference or chained path expression raises `invalid-predicate`. |
| `ERR-006` | Missing fields or nested path segments raise structured runtime exceptions and are not treated as null. |
| `ERR-007` | Chained path access through an unsupported non-dictionary value raises `invalid-path-access`. |
| `ERR-008` | Calling `.regex(...)` on an integer, such as `[age].regex(".*")`, raises `unsupported-method`. |
| `ERR-009` | Calling `[first_name].eq(1)` when `first_name` is a string raises `wrong-argument-type`. |
| `ERR-010` | Calling `[age].ge("21")` when `age` is an integer raises `wrong-argument-type`. |
| `ERR-011` | Calling `.query(...)` on a value whose runtime type does not support it raises `unsupported-method`. |
| `ERR-012` | A `.query(...)` first argument that is not a single bracketed segment raises `invalid-alias-declaration`. |
| `ERR-013` | Any structured runtime exception inside `.query(...)` fails the whole filter instead of skipping the item. |
| `ERR-014` | Any reached structured runtime exception inside `and(...)` or `or(...)` fails the whole filter. |
| `ERR-015` | A bracketed name that is not an active alias resolves as a root field reference. |
| `ERR-016` | Declaring `.query([role], ...)` inside an active `role` alias scope raises `alias-collision`. |
| `ERR-017` | `.query([role], ...)` raises `runtime-alias-root-field-collision` when a reached root record contains key `role`. |
| `ERR-018` | `.query([ip], ...)` raises `runtime-alias-root-field-collision` when the root record contains key `ip`, including scalar item queries. |
| `ERR-019` | Invalid regex patterns passed to `.regex(...)` raise `invalid-regex` at runtime. |
| `ERR-020` | Invalid date, time, or datetime strings passed to corresponding temporal methods raise `invalid-temporal-string`. |
| `ERR-021` | Default `and()` with no arguments raises `wrong-argument-count`. |
| `ERR-022` | Default `or()` with no arguments raises `wrong-argument-count`. |
| `ERR-023` | Default `not(...)` with zero or more than one argument raises `wrong-argument-count`. |
| `ERR-024` | Bare field references or chained paths passed where logical functions require predicates raise `invalid-predicate`. |
| `ERR-025` | Exceeding source length, parse tree depth, argument count, path depth, or query nesting limits raises `limit-exceeded`. |
| `ERR-026` | Custom safety limits or runtime extensions in one `FilterConfig` call do not affect later calls using omitted or different configs. |
| `ERR-027` | Direct time or datetime comparison with timezone-awareness mismatch raises `temporal-awareness-mismatch`. |
| `ERR-029` | Supported runtime data in an unsupported interpreter position raises `invalid-record`. |
| `ERR-030` | Runtime `float` values that are `NaN`, `inf`, or `-inf` raise `unsupported-runtime-value`. |
| `ERR-031` | Python values that cannot map to supported internal runtime types raise `unsupported-runtime-value`. |
| `ERR-032` | Dictionary data with non-string keys ignores those keys for path lookup and alias/root-field collision checks. |
| `ERR-033` | Structured exceptions expose stable identity, developer-readable message, and applicable machine-readable context fields. |

## Anti-Behaviors

| ID | Assertion |
|---|---|
| `AB-001` | The interpreter must not evaluate Python object attributes or class instances in v1. |
| `AB-002` | Parser and interpreter must not use `eval`, `exec`, dynamic imports, host object method invocation, or callables discovered from filter source, AST nodes, or record values; explicitly configured `FilterConfig` extension callables are the only allowed runtime extension invocation path. |
| `AB-003` | The parser must not accept list, dictionary, boolean, null, date, time, or datetime literals. |
| `AB-004` | `isNull()` must not treat missing fields or missing path segments as null. |
| `AB-005` | `.regex()` must not use glob semantics; `*` follows regex rules. |
| `AB-006` | `.regex()` must not perform case-insensitive matching unless a future explicit option adds it. |
| `AB-007` | Default `not(...)` must not accept more than one argument. |
| `AB-008` | Default `and(...)` and `or(...)` must not accept zero arguments. |
| `AB-009` | Runtime validation must not happen during parsing in a way that requires record data. |
| `AB-010` | Filter evaluation must not mutate input records. |
| `AB-011` | The v1 default in-memory interpreter must not translate filters into SQL or ORM queries. |

## Integration

| ID | Assertion |
|---|---|
| `INT-001` | Passing a list of dictionaries to the in-memory interpreter evaluates each dictionary independently and returns matching records without mutation. |
| `INT-002` | Multiple matches are returned in original input order. |
| `INT-003` | Successful evaluation returns the original input dictionary objects in `FinalResult.result`. |
| `INT-004` | A runtime exception on any input dictionary fails the whole evaluation at the first exception and returns no partial matches. |
| `INT-005` | A parsed AST can be reused against multiple record lists without reparsing. |
| `INT-006` | Future interpreters must consume the same stable AST contract rather than requiring a separate parser. |
