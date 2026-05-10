# AST Contract - V1

The AST is a pure immutable data contract. It must not contain Python callables, compiled regular expressions, host record values, interpreter objects, mutable collections, or process-global state.

## Source Span

`SourceSpan` identifies a source range.

| Field | Type | Meaning |
|---|---|---|
| `start_offset` | `int` | Zero-based character offset where the span starts. |
| `end_offset` | `int` | Zero-based character offset immediately after the span ends. |
| `start_line` | `int` | One-based line number where the span starts. |
| `start_column` | `int` | One-based column number where the span starts. |
| `end_line` | `int` | One-based line number where the span ends. |
| `end_column` | `int` | One-based column number immediately after the span ends. |

Line and column values are counted after normal Python string decoding by the caller. The parser is not responsible for byte offsets.

## AST Root

The root container type is `AST`.

| Field | Type | Meaning |
|---|---|---|
| `root` | `ExpressionNode` | Root parsed expression. |
| `source_span` | `SourceSpan` | Span covering the complete parsed expression. |

`ExpressionNode` is the union of the node variants below. Every node must expose `source_span`.

| Node | Fields | Meaning |
|---|---|---|
| `StringLiteral` | `value: str`, `source_span: SourceSpan` | User-authored string after supported escape sequences are unescaped. |
| `IntegerLiteral` | `value: int`, `source_span: SourceSpan` | User-authored integer literal. |
| `DecimalLiteral` | `value: float`, `source_span: SourceSpan` | User-authored decimal literal stored as the v1 decimal runtime category value. |
| `PathExpression` | `segments: tuple[str, ...]`, `source_span: SourceSpan` | One or more bracketed path segments without brackets. |
| `GlobalFunctionCall` | `name: str`, `arguments: tuple[ExpressionNode, ...]`, `source_span: SourceSpan` | Generic global call. The parser does not validate whether the function exists. |
| `MethodCall` | `receiver: PathExpression`, `method_name: str`, `arguments: tuple[ExpressionNode, ...]`, `source_span: SourceSpan` | Generic method call on a path expression. The parser does not validate whether the method exists on the resolved runtime receiver. |

The parser must not accept method calls on string literals, numeric literals, global function calls, or other method calls in v1. Runtime validation determines whether a parsed path receiver supports the method.
