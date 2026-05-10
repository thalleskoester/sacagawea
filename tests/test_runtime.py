import datetime as dt
import math
from typing import cast

import pytest

from sacagawea import (
    AliasCollisionError,
    FilterConfig,
    InvalidPredicateError,
    InvalidRecordError,
    MissingFieldOrPathSegmentError,
    RuntimeAliasRootFieldCollisionError,
    RuntimeExtensionError,
    RuntimeLimitExceededError,
    SafetyLimits,
    TemporalAwarenessMismatchError,
    UnsupportedRuntimeValueError,
    WrongArgumentCountError,
    WrongArgumentTypeError,
    evaluate,
    interpret,
    parse,
)


def test_evaluate_filters_original_records_in_order_and_reports_elapsed():
    first = {"first_name": "john"}
    second = {"first_name": "jane"}
    third = {"first_name": "john"}

    result = evaluate('[first_name].eq("john")', [first, second, third])

    assert result.result == [first, third]
    assert result.result[0] is first
    assert result.result[1] is third
    assert isinstance(result.elapsed, float)
    assert result.elapsed >= 0.0


def test_interpret_reuses_parsed_ast_and_does_not_mutate_input_records():
    ast = parse("[age].ge(21)")
    records = [{"age": 20}, {"age": 21}]

    result = interpret(ast, records)

    assert result.result == [records[1]]
    assert records == [{"age": 20}, {"age": 21}]


@pytest.mark.parametrize(
    ("query", "records", "expected"),
    [
        ("[balance].lt(.5)", [{"balance": 0.25}, {"balance": 1.0}], [0]),
        ("[age].eq(.5)", [{"age": 1}, {"age": 0}], []),
        ('[name].gt("Jane")', [{"name": "John"}, {"name": "Adam"}], [0]),
        ('[title].regex(".*snow white.*")', [{"title": "snow white tale"}, {"title": "Snow White tale"}], [0]),
        ("[is_active].isTrue()", [{"is_active": True}, {"is_active": 1}], [0, 1]),
        ("[count].isTrue()", [{"count": 0}, {"count": 2}], [1]),
        ("[deleted_at].isNull()", [{"deleted_at": None}, {"deleted_at": ""}], [0]),
        (
            '[customer].[address].[city].eq("Paris")',
            [{"customer": {"address": {"city": "Paris"}}}, {"customer": {"address": {"city": "Lyon"}}}],
            [0],
        ),
    ],
)
def test_runtime_scalar_methods(query, records, expected):
    result = evaluate(query, records)

    assert result.result == [records[index] for index in expected]


def test_logical_functions_short_circuit_unreached_record_errors():
    records = [{"name": "john"}]

    assert evaluate('or([name].eq("john"), [missing].eq("x"))', records).result == [records[0]]
    assert evaluate('and([name].eq("jane"), [missing].eq("x"))', records).result == []

    with pytest.raises(WrongArgumentCountError):
        evaluate("and()", records)


def test_query_supports_aliases_nested_queries_and_sibling_alias_reuse():
    records = [
        {"roles": [{"name": "user"}, {"name": "root"}], "groups": [{"name": "wheel"}]},
        {"roles": [{"name": "user"}], "groups": [{"name": "users"}]},
    ]

    result = evaluate('[roles].query([role], [role].[name].eq("root"))', records)
    sibling = evaluate(
        'and([roles].query([item], [item].[name].eq("root")), [groups].query([item], [item].[name].eq("wheel")))',
        records,
    )
    nested = evaluate(
        '[roles].query([role], [groups].query([group], and([role].[name].eq("root"), [group].[name].eq("wheel"))))',
        records,
    )

    assert result.result == [records[0]]
    assert sibling.result == [records[0]]
    assert nested.result == [records[0]]


def test_query_alias_collisions_and_nesting_limit_are_structured():
    with pytest.raises(AliasCollisionError):
        evaluate(
            "[items].query([item], [children].query([item], [item].isNull()))", [{"items": [1], "children": [None]}]
        )

    with pytest.raises(RuntimeAliasRootFieldCollisionError):
        evaluate("[items].query([item], [item].isNull())", [{"items": [None], "item": "root"}])

    config = FilterConfig(safety_limits=SafetyLimits(maximum_query_nesting=1))
    with pytest.raises(RuntimeLimitExceededError) as exc_info:
        evaluate(
            "[items].query([item], [children].query([child], [child].isNull()))",
            [{"items": [1], "children": [None]}],
            config=config,
        )

    assert exc_info.value.limit_name == "maximum_query_nesting"


def test_custom_regex_and_global_functions_are_call_scoped():
    def regex_evaluator(pattern, value):
        return pattern == value[::-1]

    def starts_with(context, arguments):
        if context.argument_count() != 2:
            raise WrongArgumentCountError(
                message="bad", target="starts_with", expected="2", received=context.argument_count()
            )
        value = context.evaluate(arguments[0])
        prefix = context.evaluate(arguments[1])
        return isinstance(value, str) and isinstance(prefix, str) and value.startswith(prefix)

    config = FilterConfig(regex_evaluator=regex_evaluator, global_functions={"starts_with": starts_with})

    assert evaluate('[name].regex("nhoj")', [{"name": "john"}], config=config).result == [{"name": "john"}]
    assert evaluate('starts_with([name], "jo")', [{"name": "john"}, {"name": "ann"}], config=config).result == [
        {"name": "john"}
    ]
    assert evaluate('[name].regex("nhoj")', [{"name": "john"}]).result == []


def test_custom_extension_failures_are_wrapped():
    def bad_regex(pattern, value):
        raise ValueError("broken")

    with pytest.raises(RuntimeExtensionError) as exc_info:
        evaluate('[name].regex("x")', [{"name": "x"}], config=FilterConfig(regex_evaluator=bad_regex))

    assert isinstance(exc_info.value.cause, ValueError)


def test_temporal_comparisons_and_components():
    records = [
        {
            "date": dt.date(2026, 5, 10),
            "time": dt.time(6, 30, tzinfo=dt.timezone(dt.timedelta(hours=-3))),
            "created_at": dt.datetime(2026, 5, 10, 12, 0, tzinfo=dt.UTC),
        },
        {
            "date": dt.date(2026, 5, 9),
            "time": dt.time(6, 30, tzinfo=dt.UTC),
            "created_at": dt.datetime(2025, 5, 10, 12, 0, tzinfo=dt.UTC),
        },
    ]

    assert evaluate('[date].eq("2026-05-10")', records).result == [records[0]]
    assert evaluate('[time].eq("09:30:00Z")', records).result == [records[0]]
    assert evaluate('[created_at].ge("2026-05-10T09:00:00-03:00")', records).result == [records[0]]
    assert evaluate("[created_at].[year].eq(2026)", records).result == [records[0]]

    with pytest.raises(TemporalAwarenessMismatchError):
        evaluate('[time].eq("09:30:00Z")', [{"time": dt.time(9, 30)}])


def test_runtime_errors_are_structured_and_fail_without_partial_results():
    with pytest.raises(MissingFieldOrPathSegmentError) as missing:
        evaluate("[missing].isNull()", [{"name": "john"}])
    assert missing.value.record_index == 0

    with pytest.raises(InvalidPredicateError):
        evaluate("[name]", [{"name": "john"}])

    with pytest.raises(WrongArgumentTypeError):
        evaluate("[name].eq(1)", [{"name": "john"}])

    with pytest.raises(InvalidRecordError):
        evaluate("[name].isNull()", cast("list[dict]", [{"name": "john"}, "bad"]))

    with pytest.raises(UnsupportedRuntimeValueError):
        evaluate("[value].isNull()", [{"value": math.inf}])
