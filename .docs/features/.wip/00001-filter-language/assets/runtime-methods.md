# Runtime Method Contract - V1

Runtime method dispatch is based on the resolved runtime/internal type from `.docs/features/.wip/00001-filter-language/assets/runtime-values.md`.

All method arity failures use `wrong-argument-count`. All method argument type failures use `wrong-argument-type`.

## List

Supported methods:

| Method | Contract |
|---|---|
| `isNull()` | Returns true only when the resolved existing value is Python `None`. |
| `query(<item_alias>, <query>)` | Valid only on runtime Python lists. Returns true when at least one list item satisfies the nested query. |

`.query(...)` alias contract:

* The first argument must be a single bracketed path segment such as `[role]`.
* Invalid first arguments raise `invalid-alias-declaration`.
* The alias is scoped only to the query body where it is declared.
* A nested query body can reference active outer aliases and its own alias.
* Reusing an alias in sibling `.query(...)` calls is valid because sibling calls have separate scopes.
* Declaring an alias that matches any currently active alias raises `alias-collision`.
* For each reached root record, declaring an alias that collides with a string key in that root record raises `runtime-alias-root-field-collision`.
* During query body evaluation, a first bracketed segment resolves to an active alias before it resolves to a root field.
* A bracketed name that is not an active alias resolves as a root field reference.
* Empty lists return false.
* Item evaluation stops at the first matching item and returns true.
* Structured runtime exceptions raised while evaluating a reached item fail the whole evaluation; invalid items are not skipped after an error.

## Dictionary

Supported methods:

```text
isNull()
```

`Dictionary` supports chained path-segment access through string keys that match the filter-language bracketed identifier syntax.

Dictionary keys that are not strings are ignored by path lookup and alias/root-field collision checks.

## Boolean

Supported methods:

```text
isNull()
isTrue()
isFalse()
```

`isTrue()` returns true only for Python `True`. `isFalse()` returns true only for Python `False`.

## Integer And Decimal

Supported methods:

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

Numeric truthiness follows zero/nonzero behavior. Numeric equality may compare integers and decimals.

## String

Supported methods:

```text
isNull()
eq(<string>)
gt(<string>)
ge(<string>)
lt(<string>)
le(<string>)
regex(<regex_pattern>)
```

String ordering uses lexicographic comparison. `regex` uses the evaluator from `FilterConfig`; the default evaluator uses Python `re.search` semantics and is case-sensitive.

## Date

Supported methods:

```text
isNull()
eq(<string>)
gt(<string>)
ge(<string>)
lt(<string>)
le(<string>)
```

Supported components:

```text
[year]
[month]
[day]
```

Components support:

```text
isNull()
eq(<integer>)
gt(<integer>)
ge(<integer>)
lt(<integer>)
le(<integer>)
```

Temporal components are derived integer values for comparison. They do not add `isTrue()` or `isFalse()` in v1.

## Time

Supported methods:

```text
isNull()
eq(<string>)
gt(<string>)
ge(<string>)
lt(<string>)
le(<string>)
```

Supported components:

```text
[hour]
[minute]
[second]
```

Components support:

```text
isNull()
eq(<integer>)
gt(<integer>)
ge(<integer>)
lt(<integer>)
le(<integer>)
```

Temporal components are derived integer values for comparison. They do not add `isTrue()` or `isFalse()` in v1.

## DateTime

Supported methods:

```text
isNull()
eq(<string>)
gt(<string>)
ge(<string>)
lt(<string>)
le(<string>)
```

Supported components:

```text
[year]
[month]
[day]
[hour]
[minute]
[second]
```

Components support:

```text
isNull()
eq(<integer>)
gt(<integer>)
ge(<integer>)
lt(<integer>)
le(<integer>)
```

Temporal components are derived integer values for comparison. They do not add `isTrue()` or `isFalse()` in v1.

## Null

Only `isNull()` is valid on `Null` in v1.

Missing fields or path segments are not `Null`; they raise `missing-field-or-path-segment`.
