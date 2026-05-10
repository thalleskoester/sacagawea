"""In-memory interpreter for parsed filter ASTs."""

from __future__ import annotations

import datetime as dt
import math
import re
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from sacagawea._ast import (
    DecimalLiteral,
    GlobalFunctionCall,
    IntegerLiteral,
    MethodCall,
    PathExpression,
    StringLiteral,
)
from sacagawea._errors import (
    AliasCollisionError,
    FilterError,
    InvalidAliasDeclarationError,
    InvalidPathAccessError,
    InvalidPredicateError,
    InvalidRecordError,
    InvalidRegexError,
    InvalidTemporalStringError,
    MissingFieldOrPathSegmentError,
    RuntimeAliasRootFieldCollisionError,
    RuntimeExtensionError,
    RuntimeLimitExceededError,
    TemporalAwarenessMismatchError,
    UnsupportedMethodError,
    UnsupportedRuntimeValueError,
    WrongArgumentCountError,
    WrongArgumentTypeError,
)
from sacagawea._result import FinalResult

if TYPE_CHECKING:
    from collections.abc import Callable

    from sacagawea._ast import AST, ExpressionNode
    from sacagawea._config import FilterConfig


@dataclass(frozen=True, slots=True)
class _RuntimeValue:
    type_name: str
    value: object
    path: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _ExtensionContext:
    runtime: _RuntimeContext
    arguments: tuple[ExpressionNode, ...]

    @property
    def record_index(self) -> int:
        """Current root record index."""
        return self.runtime.record_index

    @property
    def config(self) -> FilterConfig:
        """Current call-scoped configuration."""
        return self.runtime.config

    def evaluate(self, expression: ExpressionNode) -> object:
        """Evaluate an expression and return the raw Python value."""
        return self.runtime.evaluate(expression).value

    def evaluate_predicate(self, expression: ExpressionNode) -> bool:
        """Evaluate an expression as a Boolean predicate."""
        return self.runtime.evaluate_predicate(expression)

    def argument_count(self) -> int:
        """Return the number of AST arguments."""
        return len(self.arguments)


@dataclass(slots=True)
class _RuntimeContext:
    record: dict
    record_index: int
    config: FilterConfig
    aliases: dict[str, object]
    query_depth: int = 0

    def child(self, alias: str, value: object, query_depth: int) -> _RuntimeContext:
        """Create a nested query context."""
        aliases = dict(self.aliases)
        aliases[alias] = value
        return _RuntimeContext(
            record=self.record,
            record_index=self.record_index,
            config=self.config,
            aliases=aliases,
            query_depth=query_depth,
        )

    def evaluate_predicate(self, expression: ExpressionNode) -> bool:
        """Evaluate an expression and require a Boolean result."""
        value = self.evaluate(expression)
        if value.type_name != "Boolean":
            raise InvalidPredicateError(
                message="Predicate expression must evaluate to Boolean",
                target="predicate",
                source_span=expression.source_span,
            )
        return bool(value.value)

    def evaluate(self, expression: ExpressionNode) -> _RuntimeValue:
        """Evaluate an AST expression in the current context."""
        if isinstance(expression, StringLiteral):
            return _RuntimeValue("String", expression.value, ())
        if isinstance(expression, IntegerLiteral):
            return _RuntimeValue("Integer", expression.value, ())
        if isinstance(expression, DecimalLiteral):
            return _RuntimeValue("Decimal", expression.value, ())
        if isinstance(expression, PathExpression):
            return self._resolve_path(expression.segments)
        if isinstance(expression, MethodCall):
            return self._evaluate_method(expression)
        if isinstance(expression, GlobalFunctionCall):
            return self._evaluate_global_function(expression)
        raise AssertionError

    def _resolve_path(self, segments: tuple[str, ...]) -> _RuntimeValue:
        first = segments[0]
        if first in self.aliases:
            value = self.aliases[first]
            path = (first,)
            remaining = segments[1:]
        else:
            value = self._lookup_dictionary(self.record, first, (first,))
            path = (first,)
            remaining = segments[1:]

        for segment in remaining:
            classified = self._classify(value, path)
            component = self._temporal_component(classified, segment)
            if component is not None:
                value = component
                path = (*path, segment)
                continue
            if isinstance(value, dict):
                value = self._lookup_dictionary(value, segment, (*path, segment))
                path = (*path, segment)
                continue
            raise InvalidPathAccessError(
                message="Path segment cannot be read from this runtime value",
                path=path,
                receiver_type=classified.type_name,
                record_index=self.record_index,
            )
        return self._classify(value, path)

    def _lookup_dictionary(self, value: dict, segment: str, path: tuple[str, ...]) -> object:
        if segment in value and isinstance(segment, str):
            return value[segment]
        raise MissingFieldOrPathSegmentError(
            message="Missing field or path segment",
            path=path,
            missing_segment=segment,
            record_index=self.record_index,
        )

    def _classify(self, value: object, path: tuple[str, ...]) -> _RuntimeValue:
        if value is None:
            return _RuntimeValue("Null", value, path)
        if isinstance(value, bool):
            return _RuntimeValue("Boolean", value, path)
        if isinstance(value, dt.datetime):
            return _RuntimeValue("DateTime", value, path)
        if isinstance(value, dt.date):
            return _RuntimeValue("Date", value, path)
        if isinstance(value, dt.time):
            return _RuntimeValue("Time", value, path)
        if isinstance(value, int):
            return _RuntimeValue("Integer", value, path)
        if isinstance(value, float) and math.isfinite(value):
            return _RuntimeValue("Decimal", value, path)
        if isinstance(value, float):
            raise UnsupportedRuntimeValueError(
                message="Unsupported runtime value",
                path=path,
                python_type=type(value).__name__,
                record_index=self.record_index,
            )
        if isinstance(value, str):
            return _RuntimeValue("String", value, path)
        if isinstance(value, list):
            return _RuntimeValue("List", value, path)
        if isinstance(value, dict):
            return _RuntimeValue("Dictionary", value, path)
        raise UnsupportedRuntimeValueError(
            message="Unsupported runtime value",
            path=path,
            python_type=type(value).__name__,
            record_index=self.record_index,
        )

    def _evaluate_method(self, expression: MethodCall) -> _RuntimeValue:
        receiver = self._resolve_path(expression.receiver.segments)
        method = expression.method_name
        if method == "isNull":
            self._require_count(method, expression.arguments, 0)
            return _RuntimeValue("Boolean", receiver.type_name == "Null", receiver.path)
        if method in {"isTrue", "isFalse"}:
            return self._evaluate_truth_method(receiver, method, expression.arguments)
        if method in {"eq", "gt", "ge", "lt", "le"}:
            return self._evaluate_comparison(receiver, method, expression.arguments)
        if method == "regex":
            return self._evaluate_regex(receiver, expression.arguments)
        if method == "query":
            return self._evaluate_query(receiver, expression.arguments)
        raise UnsupportedMethodError(
            message="Unsupported method",
            path=receiver.path,
            receiver_type=receiver.type_name,
            method=method,
            record_index=self.record_index,
        )

    def _evaluate_truth_method(
        self,
        receiver: _RuntimeValue,
        method: str,
        arguments: tuple[ExpressionNode, ...],
    ) -> _RuntimeValue:
        self._require_count(method, arguments, 0)
        if receiver.type_name == "Boolean":
            result = receiver.value is True
        elif receiver.type_name in {"Integer", "Decimal"}:
            result = receiver.value != 0
        else:
            raise UnsupportedMethodError(
                message="Unsupported method",
                path=receiver.path,
                receiver_type=receiver.type_name,
                method=method,
                record_index=self.record_index,
            )
        return _RuntimeValue("Boolean", result if method == "isTrue" else not result, receiver.path)

    def _evaluate_comparison(
        self,
        receiver: _RuntimeValue,
        method: str,
        arguments: tuple[ExpressionNode, ...],
    ) -> _RuntimeValue:
        self._require_count(method, arguments, 1)
        argument = self.evaluate(arguments[0])
        if receiver.type_name in {"Integer", "Decimal"}:
            if argument.type_name not in {"Integer", "Decimal"}:
                self._wrong_type(method, 0, "Integer or Decimal", argument.type_name)
            if not isinstance(receiver.value, int | float) or not isinstance(argument.value, int | float):
                raise AssertionError
            return _RuntimeValue("Boolean", _compare_number(receiver.value, argument.value, method), receiver.path)
        if receiver.type_name == "String":
            if argument.type_name != "String":
                self._wrong_type(method, 0, "String", argument.type_name)
            if not isinstance(receiver.value, str) or not isinstance(argument.value, str):
                raise AssertionError
            return _RuntimeValue("Boolean", _compare_text(receiver.value, argument.value, method), receiver.path)
        if receiver.type_name in {"Date", "Time", "DateTime"}:
            if argument.type_name != "String":
                self._wrong_type(method, 0, "String", argument.type_name)
            other = self._parse_temporal(receiver.type_name, str(argument.value), method, 0)
            base = self._temporal_receiver_value(receiver, method, 0)
            if receiver.type_name == "Date":
                return _RuntimeValue(
                    "Boolean", _compare_date(cast("dt.date", base), cast("dt.date", other), method), receiver.path
                )
            if receiver.type_name == "Time":
                return _RuntimeValue(
                    "Boolean", _compare_time(cast("dt.time", base), cast("dt.time", other), method), receiver.path
                )
            return _RuntimeValue(
                "Boolean",
                _compare_datetime(cast("dt.datetime", base), cast("dt.datetime", other), method),
                receiver.path,
            )
        raise UnsupportedMethodError(
            message="Unsupported method",
            path=receiver.path,
            receiver_type=receiver.type_name,
            method=method,
            record_index=self.record_index,
        )

    def _evaluate_regex(self, receiver: _RuntimeValue, arguments: tuple[ExpressionNode, ...]) -> _RuntimeValue:
        self._require_count("regex", arguments, 1)
        if receiver.type_name != "String":
            raise UnsupportedMethodError(
                message="Unsupported method",
                path=receiver.path,
                receiver_type=receiver.type_name,
                method="regex",
                record_index=self.record_index,
            )
        argument = self.evaluate(arguments[0])
        if argument.type_name != "String":
            self._wrong_type("regex", 0, "String", argument.type_name)
        pattern = str(argument.value)
        evaluator = self.config.regex_evaluator
        try:
            if evaluator is None:
                result = re.search(pattern, str(receiver.value)) is not None
            else:
                result = evaluator(pattern, str(receiver.value))
        except re.error as exc:
            raise InvalidRegexError(
                message="Invalid regex pattern", pattern=pattern, argument_index=0, cause=exc
            ) from exc
        except FilterError:
            raise
        except Exception as exc:
            raise RuntimeExtensionError(
                message="Regex evaluator failed",
                extension_name="regex_evaluator",
                record_index=self.record_index,
                cause=exc,
            ) from exc
        if not isinstance(result, bool):
            raise RuntimeExtensionError(
                message="Regex evaluator returned a non-Boolean value",
                extension_name="regex_evaluator",
                record_index=self.record_index,
                cause=None,
            )
        return _RuntimeValue("Boolean", result, receiver.path)

    def _evaluate_query(self, receiver: _RuntimeValue, arguments: tuple[ExpressionNode, ...]) -> _RuntimeValue:
        self._require_count("query", arguments, 2)
        if receiver.type_name != "List":
            raise UnsupportedMethodError(
                message="Unsupported method",
                path=receiver.path,
                receiver_type=receiver.type_name,
                method="query",
                record_index=self.record_index,
            )
        alias_expression = arguments[0]
        if not isinstance(alias_expression, PathExpression) or len(alias_expression.segments) != 1:
            alias = (
                alias_expression.segments[0]
                if isinstance(alias_expression, PathExpression) and alias_expression.segments
                else ""
            )
            raise InvalidAliasDeclarationError(
                message="Query alias must be a single bracketed path segment",
                alias=alias,
                source_span=alias_expression.source_span,
            )
        alias = alias_expression.segments[0]
        if alias in self.aliases:
            raise AliasCollisionError(message="Query alias collides with an active alias", alias=alias)
        if alias in {key for key in self.record if isinstance(key, str)}:
            raise RuntimeAliasRootFieldCollisionError(
                message="Query alias collides with a root record field",
                alias=alias,
                record_index=self.record_index,
            )
        next_depth = self.query_depth + 1
        limit = self.config.safety_limits.maximum_query_nesting
        if next_depth > limit:
            raise RuntimeLimitExceededError(
                message="Query nesting exceeds maximum",
                limit_name="maximum_query_nesting",
                limit_value=limit,
                actual_value=next_depth,
            )
        items = receiver.value
        if not isinstance(items, list):
            raise AssertionError
        for item in items:
            child = self.child(alias, item, next_depth)
            if child.evaluate_predicate(arguments[1]):
                return _RuntimeValue("Boolean", value=True, path=receiver.path)
        return _RuntimeValue("Boolean", value=False, path=receiver.path)

    def _evaluate_global_function(self, expression: GlobalFunctionCall) -> _RuntimeValue:
        if (
            expression.name == "and"
            and self.config.include_default_global_functions
            and expression.name not in self.config.global_functions
        ):
            self._require_at_least("and", expression.arguments, 1)
            for argument in expression.arguments:
                if not self.evaluate_predicate(argument):
                    return _RuntimeValue("Boolean", value=False, path=())
            return _RuntimeValue("Boolean", value=True, path=())
        if (
            expression.name == "or"
            and self.config.include_default_global_functions
            and expression.name not in self.config.global_functions
        ):
            self._require_at_least("or", expression.arguments, 1)
            for argument in expression.arguments:
                if self.evaluate_predicate(argument):
                    return _RuntimeValue("Boolean", value=True, path=())
            return _RuntimeValue("Boolean", value=False, path=())
        if (
            expression.name == "not"
            and self.config.include_default_global_functions
            and expression.name not in self.config.global_functions
        ):
            self._require_count("not", expression.arguments, 1)
            return _RuntimeValue("Boolean", not self.evaluate_predicate(expression.arguments[0]), ())

        function = self._effective_global_function(expression.name)
        if function is None:
            raise UnsupportedMethodError(
                message="Unsupported global function",
                path=(),
                receiver_type="GlobalFunction",
                method=expression.name,
                record_index=self.record_index,
            )
        context = _ExtensionContext(runtime=self, arguments=expression.arguments)
        try:
            value = function(context, expression.arguments)
        except FilterError:
            raise
        except Exception as exc:
            raise RuntimeExtensionError(
                message="Global function failed",
                extension_name=expression.name,
                record_index=self.record_index,
                cause=exc,
            ) from exc
        return self._classify(value, ())

    def _effective_global_function(
        self, name: str
    ) -> Callable[[_ExtensionContext, tuple[ExpressionNode, ...]], object] | None:
        if name in self.config.global_functions:
            return self.config.global_functions[name]
        return None

    def _require_count(self, target: str, arguments: tuple[ExpressionNode, ...], expected: int) -> None:
        if len(arguments) != expected:
            raise WrongArgumentCountError(
                message="Wrong argument count",
                target=target,
                expected=str(expected),
                received=len(arguments),
            )

    def _require_at_least(self, target: str, arguments: tuple[ExpressionNode, ...], expected: int) -> None:
        if len(arguments) < expected:
            raise WrongArgumentCountError(
                message="Wrong argument count",
                target=target,
                expected=f"at least {expected}",
                received=len(arguments),
            )

    def _wrong_type(self, target: str, argument_index: int, expected: str, received: str) -> None:
        raise WrongArgumentTypeError(
            message="Wrong argument type",
            target=target,
            argument_index=argument_index,
            expected=expected,
            received=received,
        )

    def _temporal_component(self, value: _RuntimeValue, segment: str) -> int | None:
        components = {
            "Date": {"year", "month", "day"},
            "Time": {"hour", "minute", "second"},
            "DateTime": {"year", "month", "day", "hour", "minute", "second"},
        }
        if segment not in components.get(value.type_name, set()):
            return None
        temporal = value.value
        if isinstance(temporal, dt.datetime):
            datetime_components = {
                "year": temporal.year,
                "month": temporal.month,
                "day": temporal.day,
                "hour": temporal.hour,
                "minute": temporal.minute,
                "second": temporal.second,
            }
            return datetime_components[segment]
        if isinstance(temporal, dt.date):
            date_components = {"year": temporal.year, "month": temporal.month, "day": temporal.day}
            return date_components[segment]
        if isinstance(temporal, dt.time):
            time_components = {"hour": temporal.hour, "minute": temporal.minute, "second": temporal.second}
            return time_components[segment]
        return None

    def _parse_temporal(self, target_type: str, value: str, method: str, argument_index: int) -> object:
        if target_type == "Date":
            try:
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                    raise ValueError
                return dt.date.fromisoformat(value)
            except ValueError as exc:
                raise InvalidTemporalStringError(
                    message="Invalid temporal string",
                    target_type=target_type,
                    value=value,
                    method=method,
                    argument_index=argument_index,
                ) from exc
        if target_type == "Time":
            if not re.fullmatch(r"\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})", value):
                raise InvalidTemporalStringError(
                    message="Invalid temporal string",
                    target_type=target_type,
                    value=value,
                    method=method,
                    argument_index=argument_index,
                )
            parsed = dt.time.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise TemporalAwarenessMismatchError(
                    message="Temporal awareness mismatch",
                    target_type=target_type,
                    value=value,
                    method=method,
                    argument_index=argument_index,
                )
            return _utc_time_of_day(parsed)
        if target_type == "DateTime":
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})", value):
                raise InvalidTemporalStringError(
                    message="Invalid temporal string",
                    target_type=target_type,
                    value=value,
                    method=method,
                    argument_index=argument_index,
                )
            parsed_datetime = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed_datetime.tzinfo is None:
                raise TemporalAwarenessMismatchError(
                    message="Temporal awareness mismatch",
                    target_type=target_type,
                    value=value,
                    method=method,
                    argument_index=argument_index,
                )
            return parsed_datetime.astimezone(dt.UTC)
        raise AssertionError(target_type)

    def _temporal_receiver_value(self, receiver: _RuntimeValue, method: str, argument_index: int) -> object:
        if receiver.type_name == "Date":
            return receiver.value
        if receiver.type_name == "Time":
            value = receiver.value
            if isinstance(value, dt.time) and value.tzinfo is not None and value.utcoffset() is not None:
                return _utc_time_of_day(value)
        if receiver.type_name == "DateTime":
            value = receiver.value
            if isinstance(value, dt.datetime) and value.tzinfo is not None and value.utcoffset() is not None:
                return value.astimezone(dt.UTC)
        raise TemporalAwarenessMismatchError(
            message="Temporal awareness mismatch",
            target_type=receiver.type_name,
            value=receiver.value,
            method=method,
            argument_index=argument_index,
        )


def _compare_number(left: int | float, right: int | float, method: str) -> bool:
    if method == "eq":
        return left == right
    if method == "gt":
        return left > right
    if method == "ge":
        return left >= right
    if method == "lt":
        return left < right
    if method == "le":
        return left <= right
    raise AssertionError(method)


def _compare_text(left: str, right: str, method: str) -> bool:
    if method == "eq":
        return left == right
    if method == "gt":
        return left > right
    if method == "ge":
        return left >= right
    if method == "lt":
        return left < right
    if method == "le":
        return left <= right
    raise AssertionError(method)


def _compare_date(left: dt.date, right: dt.date, method: str) -> bool:
    if method == "eq":
        return left == right
    if method == "gt":
        return left > right
    if method == "ge":
        return left >= right
    if method == "lt":
        return left < right
    if method == "le":
        return left <= right
    raise AssertionError(method)


def _compare_time(left: dt.time, right: dt.time, method: str) -> bool:
    if method == "eq":
        return left == right
    if method == "gt":
        return left > right
    if method == "ge":
        return left >= right
    if method == "lt":
        return left < right
    if method == "le":
        return left <= right
    raise AssertionError(method)


def _compare_datetime(left: dt.datetime, right: dt.datetime, method: str) -> bool:
    if method == "eq":
        return left == right
    if method == "gt":
        return left > right
    if method == "ge":
        return left >= right
    if method == "lt":
        return left < right
    if method == "le":
        return left <= right
    raise AssertionError(method)


def _utc_time_of_day(value: dt.time) -> dt.time:
    date_time = dt.datetime.combine(dt.date(2000, 1, 1), value)
    return date_time.astimezone(dt.UTC).time().replace(tzinfo=dt.UTC)


def interpret_ast(ast: AST, data: list[dict], config: FilterConfig) -> FinalResult:
    """Evaluate an AST against a top-level list of dictionaries."""
    if not isinstance(data, list):
        raise InvalidRecordError(
            message="Runtime data must be a list of dictionaries",
            record_index=-1,
            received=type(data).__name__,
        )

    start = time.perf_counter()
    matches: list[dict] = []
    for index, record in enumerate(data):
        if not isinstance(record, dict):
            raise InvalidRecordError(
                message="Runtime record must be a dictionary",
                record_index=index,
                received=type(record).__name__,
            )
        context = _RuntimeContext(record=record, record_index=index, config=config, aliases={})
        if context.evaluate_predicate(ast.root):
            matches.append(record)
    elapsed = (time.perf_counter() - start) * 1000
    return FinalResult(result=matches, elapsed=elapsed)
