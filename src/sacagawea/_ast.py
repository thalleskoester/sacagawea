"""Pure immutable AST data contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """A zero-based source offset range with one-based line and column metadata."""

    start_offset: int
    end_offset: int
    start_line: int
    start_column: int
    end_line: int
    end_column: int


@dataclass(frozen=True, slots=True)
class StringLiteral:
    """A string literal expression."""

    value: str
    source_span: SourceSpan


@dataclass(frozen=True, slots=True)
class IntegerLiteral:
    """An integer literal expression."""

    value: int
    source_span: SourceSpan


@dataclass(frozen=True, slots=True)
class DecimalLiteral:
    """A decimal literal expression."""

    value: float
    source_span: SourceSpan


@dataclass(frozen=True, slots=True)
class PathExpression:
    """A bracketed path expression."""

    segments: tuple[str, ...]
    source_span: SourceSpan


@dataclass(frozen=True, slots=True)
class GlobalFunctionCall:
    """A generic global function call expression."""

    name: str
    arguments: tuple[ExpressionNode, ...]
    source_span: SourceSpan


@dataclass(frozen=True, slots=True)
class MethodCall:
    """A generic method call expression on a path receiver."""

    receiver: PathExpression
    method_name: str
    arguments: tuple[ExpressionNode, ...]
    source_span: SourceSpan


ExpressionNode = StringLiteral | IntegerLiteral | DecimalLiteral | PathExpression | GlobalFunctionCall | MethodCall


@dataclass(frozen=True, slots=True)
class AST:
    """A parsed filter tree root."""

    root: ExpressionNode
    source_span: SourceSpan
