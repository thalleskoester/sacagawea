"""Structured public exception hierarchy."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from sacagawea._ast import SourceSpan


class FilterError(Exception):
    """Common base for library-defined structured exceptions."""

    code: ClassVar[str] = "filter-error"

    def __init__(self, message: str, *, cause: BaseException | None = None, **context: object) -> None:
        """Create a structured library exception."""
        super().__init__(message)
        self.message = message
        self.cause = cause
        for key, value in context.items():
            setattr(self, key, value)


class FilterSyntaxError(FilterError):
    """Base for parser-originated syntax and parse-time validation failures."""


class FilterRuntimeError(FilterError):
    """Base for runtime validation, interpretation, and extension failures."""


class FilterParseError(FilterSyntaxError):
    """Malformed source syntax."""

    code = "syntax-error"
    source_span: SourceSpan


class MissingFieldOrPathSegmentError(FilterRuntimeError):
    """A field or path segment was absent from the reached data."""

    code = "missing-field-or-path-segment"
    path: tuple[str, ...]
    missing_segment: str
    record_index: int


class InvalidPathAccessError(FilterRuntimeError):
    """Path traversal attempted to continue through a non-dictionary value."""

    code = "invalid-path-access"
    path: tuple[str, ...]
    receiver_type: str
    record_index: int


class InvalidAliasDeclarationError(FilterRuntimeError):
    """A query alias declaration is not a single bracketed segment."""

    code = "invalid-alias-declaration"
    alias: str
    source_span: SourceSpan


class UnsupportedMethodError(FilterRuntimeError):
    """The resolved runtime type does not support a requested method."""

    code = "unsupported-method"
    path: tuple[str, ...]
    receiver_type: str
    method: str
    record_index: int


class WrongArgumentCountError(FilterRuntimeError):
    """A function or method received the wrong number of arguments."""

    code = "wrong-argument-count"
    target: str
    expected: str
    received: int


class WrongArgumentTypeError(FilterRuntimeError):
    """A function or method received an argument with the wrong runtime type."""

    code = "wrong-argument-type"
    target: str
    argument_index: int
    expected: str
    received: str


class InvalidRegexError(FilterRuntimeError):
    """A regex pattern is invalid for the configured evaluator."""

    code = "invalid-regex"
    pattern: str
    argument_index: int


class InvalidTemporalStringError(FilterRuntimeError):
    """A temporal string argument has an invalid format or value."""

    code = "invalid-temporal-string"
    target_type: str
    value: object
    method: str
    argument_index: int


class TemporalAwarenessMismatchError(FilterRuntimeError):
    """A temporal comparison mixed timezone-aware and timezone-naive values."""

    code = "temporal-awareness-mismatch"
    target_type: str
    value: object
    method: str
    argument_index: int


class InvalidPredicateError(FilterRuntimeError):
    """An expression used as a predicate did not evaluate to Boolean."""

    code = "invalid-predicate"
    target: str
    source_span: SourceSpan


class AliasCollisionError(FilterRuntimeError):
    """A query alias shadows an already active alias."""

    code = "alias-collision"
    alias: str


class RuntimeAliasRootFieldCollisionError(FilterRuntimeError):
    """A query alias collides with a root record string key."""

    code = "runtime-alias-root-field-collision"
    alias: str
    record_index: int


class LimitExceededError(FilterError):
    """Common public base for parse-time and runtime limit failures."""

    code = "limit-exceeded"


class ParseLimitExceededError(LimitExceededError, FilterSyntaxError):
    """A parse-time safety limit was exceeded."""

    limit_name: str
    limit_value: int
    actual_value: int


class RuntimeLimitExceededError(LimitExceededError, FilterRuntimeError):
    """A runtime safety limit was exceeded."""

    limit_name: str
    limit_value: int
    actual_value: int


class InvalidRecordError(FilterRuntimeError):
    """Runtime data is not a top-level dictionary record."""

    code = "invalid-record"
    record_index: int
    received: str


class UnsupportedRuntimeValueError(FilterRuntimeError):
    """A reached Python value cannot be mapped to a supported runtime value."""

    code = "unsupported-runtime-value"
    path: tuple[str, ...]
    python_type: str
    record_index: int


class RuntimeExtensionError(FilterRuntimeError):
    """A configured runtime extension failed unexpectedly."""

    code = "runtime-extension-error"
    extension_name: str
    record_index: int


def context(error: FilterError) -> dict[str, Any]:
    """Return machine-readable context fields for a structured error."""
    excluded = {"args", "message", "cause"}
    return {key: value for key, value in vars(error).items() if key not in excluded}
