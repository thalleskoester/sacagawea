"""Handwritten recursive-descent parser for v1 filter syntax."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sacagawea._ast import (
    AST,
    DecimalLiteral,
    GlobalFunctionCall,
    IntegerLiteral,
    MethodCall,
    PathExpression,
    SourceSpan,
    StringLiteral,
)
from sacagawea._errors import FilterParseError, ParseLimitExceededError

if TYPE_CHECKING:
    from sacagawea._ast import ExpressionNode
    from sacagawea._config import FilterConfig


@dataclass(frozen=True, slots=True)
class _Position:
    offset: int
    line: int
    column: int


class _Parser:
    """Parse one filter source string into an AST."""

    def __init__(self, source: str, config: FilterConfig) -> None:
        self._source = source
        self._config = config
        self._offset = 0
        self._line = 1
        self._column = 1

    def parse(self) -> AST:
        """Parse the configured source."""
        limit = self._config.safety_limits.maximum_source_length
        actual = len(self._source)
        if actual > limit:
            raise ParseLimitExceededError(
                message="Filter source exceeds maximum length",
                limit_name="maximum_source_length",
                limit_value=limit,
                actual_value=actual,
            )

        self._skip_trivia()
        expression = self._parse_expression()
        self._skip_trivia()
        if not self._at_end():
            self._syntax("Unexpected trailing syntax")

        self._enforce_tree_depth(expression)
        return AST(root=expression, source_span=expression.source_span)

    def _parse_expression(self) -> ExpressionNode:
        self._skip_trivia()
        if self._at_end():
            self._syntax("Expected expression")

        char = self._peek()
        if char in {'"', "'"}:
            return self._parse_string()
        if char == "[":
            return self._parse_path_or_method()
        if char == "-" or char == "." or char.isdigit():
            return self._parse_number()
        if self._is_identifier_start(char):
            return self._parse_global_call()
        self._syntax("Expected expression")
        raise AssertionError

    def _parse_string(self) -> StringLiteral:
        start = self._position()
        quote = self._consume()
        value_parts: list[str] = []
        escapes = {"\\": "\\", '"': '"', "'": "'", "n": "\n", "t": "\t"}
        while not self._at_end():
            char = self._consume()
            if char == quote:
                return StringLiteral(value="".join(value_parts), source_span=self._span(start, self._position()))
            if char == "\\":
                if self._at_end():
                    self._syntax("Unterminated string escape", start)
                escaped = self._consume()
                if escaped not in escapes:
                    self._syntax("Unsupported string escape", start)
                value_parts.append(escapes[escaped])
            else:
                value_parts.append(char)
        self._syntax("Unterminated string", start)
        raise AssertionError

    def _parse_number(self) -> IntegerLiteral | DecimalLiteral:
        start = self._position()
        text = ""
        if self._peek() == "-":
            text += self._consume()
        digits_before = self._consume_digits()
        text += digits_before
        is_decimal = False
        if self._peek_or_none() == ".":
            is_decimal = True
            text += self._consume()
            digits_after = self._consume_digits()
            text += digits_after
            if digits_before == "" and digits_after == "":
                self._syntax("Expected decimal digits", start)
        elif digits_before == "":
            self._syntax("Expected number", start)

        span = self._span(start, self._position())
        if is_decimal:
            return DecimalLiteral(value=float(text), source_span=span)
        return IntegerLiteral(value=int(text), source_span=span)

    def _parse_path_or_method(self) -> PathExpression | MethodCall:
        start = self._position()
        first = self._parse_bracketed_segment()
        segments = [first]
        self._enforce_path_depth(len(segments))
        path_end = self._position()
        path = PathExpression(segments=tuple(segments), source_span=self._span(start, path_end))
        self._skip_trivia()
        while self._peek_or_none() == ".":
            self._consume()
            self._skip_trivia()
            if self._peek_or_none() == "[":
                segment = self._parse_bracketed_segment()
                segments.append(segment)
                self._enforce_path_depth(len(segments))
                path_end = self._position()
                path = PathExpression(segments=tuple(segments), source_span=self._span(start, path_end))
                self._skip_trivia()
                continue

            method_name = self._parse_symbol()
            self._skip_trivia()
            if self._peek_or_none() != "(":
                self._syntax("Expected method call")
            arguments, end = self._parse_arguments()
            return MethodCall(
                receiver=path,
                method_name=method_name,
                arguments=arguments,
                source_span=self._span(path.source_span, end),
            )
        return path

    def _parse_path(self) -> PathExpression:
        start = self._position()
        first = self._parse_bracketed_segment()
        segments = [first]
        self._enforce_path_depth(len(segments))
        return PathExpression(segments=tuple(segments), source_span=self._span(start, self._position()))

    def _parse_bracketed_segment(self) -> str:
        self._expect("[")
        start = self._position()
        if self._at_end() or not self._is_identifier_start(self._peek()):
            self._syntax("Expected path segment")
        text = self._consume()
        while not self._at_end() and self._is_path_identifier_continue(self._peek()):
            text += self._consume()
        if self._peek_or_none() != "]":
            self._syntax("Expected closing bracket", start)
        self._consume()
        return text

    def _parse_global_call(self) -> GlobalFunctionCall:
        start = self._position()
        name = self._parse_symbol()
        self._skip_trivia()
        if self._peek_or_none() != "(":
            self._syntax("Expected function call", start)
        arguments, end = self._parse_arguments()
        return GlobalFunctionCall(name=name, arguments=arguments, source_span=self._span(start, end))

    def _parse_symbol(self) -> str:
        if self._at_end() or not self._is_identifier_start(self._peek()):
            self._syntax("Expected identifier")
        text = self._consume()
        while not self._at_end() and self._is_symbol_continue(self._peek()):
            text += self._consume()
        return text

    def _parse_arguments(self) -> tuple[tuple[ExpressionNode, ...], _Position]:
        self._expect("(")
        arguments: list[ExpressionNode] = []
        self._skip_trivia()
        if self._peek_or_none() == ")":
            self._consume()
            return (), self._position()
        while True:
            arguments.append(self._parse_expression())
            self._enforce_argument_count(len(arguments))
            self._skip_trivia()
            if self._peek_or_none() == ",":
                self._consume()
                self._skip_trivia()
                if self._peek_or_none() == ")":
                    self._consume()
                    return tuple(arguments), self._position()
                continue
            if self._peek_or_none() == ")":
                self._consume()
                return tuple(arguments), self._position()
            self._syntax("Expected comma or closing parenthesis")

    def _skip_trivia(self) -> None:
        while not self._at_end():
            char = self._peek()
            if char.isspace():
                self._consume()
                continue
            if self._source.startswith("//", self._offset):
                while not self._at_end() and self._peek() != "\n":
                    self._consume()
                continue
            if self._source.startswith("/*", self._offset):
                start = self._position()
                self._consume()
                self._consume()
                while not self._at_end() and not self._source.startswith("*/", self._offset):
                    self._consume()
                if self._at_end():
                    self._syntax("Unterminated block comment", start)
                self._consume()
                self._consume()
                continue
            break

    def _consume_digits(self) -> str:
        text = ""
        while not self._at_end() and self._peek().isdigit():
            text += self._consume()
        return text

    def _expect(self, expected: str) -> None:
        if self._peek_or_none() != expected:
            self._syntax(f"Expected {expected}")
        self._consume()

    def _consume(self) -> str:
        char = self._source[self._offset]
        self._offset += 1
        if char == "\n":
            self._line += 1
            self._column = 1
        else:
            self._column += 1
        return char

    def _peek(self) -> str:
        return self._source[self._offset]

    def _peek_or_none(self) -> str | None:
        if self._at_end():
            return None
        return self._peek()

    def _at_end(self) -> bool:
        return self._offset >= len(self._source)

    def _position(self) -> _Position:
        return _Position(self._offset, self._line, self._column)

    def _span(self, start: _Position | SourceSpan, end: _Position) -> SourceSpan:
        if isinstance(start, SourceSpan):
            return SourceSpan(
                start_offset=start.start_offset,
                end_offset=end.offset,
                start_line=start.start_line,
                start_column=start.start_column,
                end_line=end.line,
                end_column=end.column,
            )
        return SourceSpan(
            start_offset=start.offset,
            end_offset=end.offset,
            start_line=start.line,
            start_column=start.column,
            end_line=end.line,
            end_column=end.column,
        )

    def _syntax(self, message: str, start: _Position | None = None) -> None:
        position = self._position() if start is None else start
        span = SourceSpan(
            start_offset=position.offset,
            end_offset=position.offset,
            start_line=position.line,
            start_column=position.column,
            end_line=position.line,
            end_column=position.column,
        )
        raise FilterParseError(message=message, source_span=span)

    def _enforce_argument_count(self, actual: int) -> None:
        limit = self._config.safety_limits.maximum_function_or_method_arguments
        if actual > limit:
            raise ParseLimitExceededError(
                message="Function or method argument count exceeds maximum",
                limit_name="maximum_function_or_method_arguments",
                limit_value=limit,
                actual_value=actual,
            )

    def _enforce_path_depth(self, actual: int) -> None:
        limit = self._config.safety_limits.maximum_path_depth
        if actual > limit:
            raise ParseLimitExceededError(
                message="Path depth exceeds maximum",
                limit_name="maximum_path_depth",
                limit_value=limit,
                actual_value=actual,
            )

    def _enforce_tree_depth(self, expression: ExpressionNode) -> None:
        actual = _tree_depth(expression)
        limit = self._config.safety_limits.maximum_parse_tree_depth
        if actual > limit:
            raise ParseLimitExceededError(
                message="Parse tree depth exceeds maximum",
                limit_name="maximum_parse_tree_depth",
                limit_value=limit,
                actual_value=actual,
            )

    def _is_identifier_start(self, char: str) -> bool:
        return char.isascii() and (char.isalpha() or char == "_")

    def _is_symbol_continue(self, char: str) -> bool:
        return char.isascii() and (char.isalnum() or char == "_")

    def _is_path_identifier_continue(self, char: str) -> bool:
        return char.isascii() and (char.isalnum() or char in {"_", "-"})


def _tree_depth(expression: ExpressionNode) -> int:
    if isinstance(expression, StringLiteral | IntegerLiteral | DecimalLiteral):
        return 1
    if isinstance(expression, PathExpression):
        return 1
    if isinstance(expression, GlobalFunctionCall):
        child_depth = max((_tree_depth(argument) for argument in expression.arguments), default=0)
        return 1 + child_depth
    if isinstance(expression, MethodCall):
        child_depth = max((_tree_depth(argument) for argument in expression.arguments), default=0)
        return 1 + max(_tree_depth(expression.receiver), child_depth)
    raise AssertionError


def parse_source(query: str, config: FilterConfig) -> AST:
    """Parse source with the v1 parser."""
    return _Parser(query, config).parse()
