# Safety Limits Contract - V1

`SafetyLimits` is immutable. Default v1 values are:

| Field | Default | Counting rule |
|---|---:|---|
| `maximum_source_length` | `10000` | Number of Python string characters in the source query. |
| `maximum_parse_tree_depth` | `100` | Root expression starts at 1; each nested global function call, method call, or path expression node increments depth by 1. |
| `maximum_function_or_method_arguments` | `64` | Number of parsed arguments; a trailing comma does not count as an argument. |
| `maximum_path_depth` | `32` | Number of bracketed segments in a path expression. |
| `maximum_query_nesting` | `16` | Runtime `.query(...)` nesting depth; the outermost reached query call is depth 1. |

Limit failures raise `limit-exceeded` with `limit_name`, `limit_value`, and `actual_value`.

Filter expressions cannot configure, raise, lower, or disable safety limits. Limits are set only through `FilterConfig`.

`SafetyLimits.default()` returns the documented default limits. Constructing `SafetyLimits()` with no arguments is equivalent to `SafetyLimits.default()`.
