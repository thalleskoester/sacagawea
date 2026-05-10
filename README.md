# sacagawea

`sacagawea` is a Python backend library for parsing and evaluating a small filter language against in-memory lists of dictionaries.

## Public API

```python
from sacagawea import evaluate, interpret, parse

records = [{"first_name": "john"}, {"first_name": "jane"}]
ast = parse('[first_name].eq("john")')
result = interpret(ast, records)

assert result.result == [records[0]]
assert evaluate('[first_name].eq("john")', records).result == result.result
```

`parse(query)` returns a pure immutable AST. It does not inspect runtime data or validate whether methods and functions exist for a particular record.

`interpret(ast, data)` evaluates a parsed AST against a top-level `list[dict]`. Matching records are the original dictionary objects in input order, not copies.

`evaluate(query, data)` is a convenience wrapper that parses and interprets with the same `FilterConfig` instance.

## Configuration And Safety

`FilterConfig()` and `FilterConfig.default()` use `SafetyLimits.default()`, the default Python `re.search` regex evaluator, default logical functions, and no custom global functions.

Default safety limits are:

| Limit | Default |
|---|---:|
| `maximum_source_length` | `10000` |
| `maximum_parse_tree_depth` | `100` |
| `maximum_function_or_method_arguments` | `64` |
| `maximum_path_depth` | `32` |
| `maximum_query_nesting` | `16` |

Regex matching is case-sensitive and uses Python regex semantics by default. Host applications can supply a custom regex evaluator through `FilterConfig`.

Custom global functions are configured through `FilterConfig.global_functions`. They receive a runtime context and AST argument expressions, and their raw Python return value is classified through the same runtime value model used for record data.

Field visibility is the host application's responsibility. v1 does not include allowlists, denylists, SQL translation, ORM translation, object attribute access, or Python object-instance traversal.
