import dataclasses

import pytest

import sacagawea
from sacagawea import (
    AST,
    FilterConfig,
    FilterError,
    FilterParseError,
    FilterRuntimeError,
    FinalResult,
    IntegerLiteral,
    ParseLimitExceededError,
    SafetyLimits,
    SourceSpan,
)


def mutate_attribute(target, name, *, value):
    setattr(target, name, value)


def test_public_exports_match_documented_root_api():
    expected = {
        "parse",
        "interpret",
        "evaluate",
        "FilterConfig",
        "SafetyLimits",
        "FinalResult",
        "AST",
        "SourceSpan",
        "StringLiteral",
        "IntegerLiteral",
        "DecimalLiteral",
        "PathExpression",
        "GlobalFunctionCall",
        "MethodCall",
        "FilterError",
        "FilterSyntaxError",
        "FilterRuntimeError",
        "FilterParseError",
        "MissingFieldOrPathSegmentError",
        "InvalidPathAccessError",
        "InvalidAliasDeclarationError",
        "UnsupportedMethodError",
        "WrongArgumentCountError",
        "WrongArgumentTypeError",
        "InvalidRegexError",
        "InvalidTemporalStringError",
        "TemporalAwarenessMismatchError",
        "InvalidPredicateError",
        "AliasCollisionError",
        "RuntimeAliasRootFieldCollisionError",
        "LimitExceededError",
        "ParseLimitExceededError",
        "RuntimeLimitExceededError",
        "InvalidRecordError",
        "UnsupportedRuntimeValueError",
        "RuntimeExtensionError",
    }

    assert set(sacagawea.__all__) == expected
    for name in expected:
        assert getattr(sacagawea, name)


def test_config_and_safety_limits_defaults_are_immutable_and_equivalent():
    assert SafetyLimits() == SafetyLimits.default()
    assert SafetyLimits.default() == SafetyLimits(
        maximum_source_length=10000,
        maximum_parse_tree_depth=100,
        maximum_function_or_method_arguments=64,
        maximum_path_depth=32,
        maximum_query_nesting=16,
    )

    config = FilterConfig()
    assert config == FilterConfig.default()
    assert config.safety_limits == SafetyLimits.default()
    assert config.regex_evaluator is None
    assert config.include_default_global_functions is True
    assert config.global_functions == {}

    with pytest.raises(dataclasses.FrozenInstanceError):
        mutate_attribute(config, "include_default_global_functions", value=False)


def test_public_data_objects_are_keyword_constructible_and_immutable():
    span = SourceSpan(0, 2, 1, 1, 1, 3)
    literal = IntegerLiteral(value=10, source_span=span)
    ast = AST(root=literal, source_span=span)
    result = FinalResult(result=[{"age": 10}], elapsed=0.1)

    assert isinstance(ast.root, IntegerLiteral)
    assert ast.root.value == 10
    assert result.result == [{"age": 10}]

    with pytest.raises(dataclasses.FrozenInstanceError):
        mutate_attribute(literal, "value", value=11)


def test_structured_exceptions_expose_code_message_cause_and_context():
    span = SourceSpan(0, 1, 1, 1, 1, 2)
    error = FilterParseError(message="bad syntax", source_span=span)

    assert isinstance(error, FilterError)
    assert error.code == "syntax-error"
    assert error.message == "bad syntax"
    assert error.cause is None
    assert error.source_span == span

    limit = ParseLimitExceededError(
        message="too deep",
        limit_name="maximum_parse_tree_depth",
        limit_value=1,
        actual_value=2,
    )
    assert isinstance(limit, FilterError)
    assert isinstance(limit, FilterRuntimeError) is False
    assert limit.code == "limit-exceeded"
