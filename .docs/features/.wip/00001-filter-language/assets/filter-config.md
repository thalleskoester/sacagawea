# FilterConfig Contract - V1

`FilterConfig` is immutable or mutation-safe. It is scoped to the public call that receives it and must not mutate process-global behavior.

| Field | Type | Default | Meaning |
|---|---|---|---|
| `safety_limits` | `SafetyLimits` | `SafetyLimits.default()` | Safety limits used by parse-time and runtime validation. |
| `regex_evaluator` | `RegexEvaluator \| None` | `None` | `None` means use the default Python `re.search` evaluator. |
| `include_default_global_functions` | `bool` | `True` | Whether the effective global function registry starts with default `and`, `or`, and `not`. |
| `global_functions` | mapping from `str` to `GlobalFunction \| None` | empty mapping | Overlay for the effective global registry. A callable adds or replaces a function. `None` removes a function when defaults are included. |

`FilterConfig.default()` returns the documented default configuration. Constructing `FilterConfig()` with no arguments is equivalent to `FilterConfig.default()`.

Effective global function registry rules:

1. If `include_default_global_functions` is true, start with default `and`, `or`, and `not`; otherwise start empty.
2. For each `global_functions` entry whose value is callable, add or replace that symbol.
3. For each `global_functions` entry whose value is `None`, remove that symbol if present.
4. The resulting registry applies only to the current public call.

Function symbols in config must use the same ASCII identifier rule as parsed function symbols.
