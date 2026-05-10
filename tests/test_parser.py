import pytest

from sacagawea import (
    DecimalLiteral,
    FilterConfig,
    FilterParseError,
    GlobalFunctionCall,
    IntegerLiteral,
    MethodCall,
    ParseLimitExceededError,
    PathExpression,
    SafetyLimits,
    StringLiteral,
    parse,
)


def topology(node):
    if isinstance(node, StringLiteral | IntegerLiteral | DecimalLiteral):
        return type(node), node.value
    if isinstance(node, PathExpression):
        return PathExpression, node.segments
    if isinstance(node, GlobalFunctionCall):
        return GlobalFunctionCall, node.name, tuple(topology(argument) for argument in node.arguments)
    if isinstance(node, MethodCall):
        return (
            MethodCall,
            topology(node.receiver),
            node.method_name,
            tuple(topology(argument) for argument in node.arguments),
        )
    raise AssertionError(f"Unexpected node {node!r}")


def test_parse_method_call_with_path_receiver_and_string_literal():
    ast = parse('[first_name].eq("john")')

    assert isinstance(ast.root, MethodCall)
    assert ast.root.receiver.segments == ("first_name",)
    assert ast.root.method_name == "eq"
    assert ast.root.arguments == (StringLiteral("john", ast.root.arguments[0].source_span),)
    assert ast.source_span.start_offset == 0
    assert ast.source_span.end_offset == len('[first_name].eq("john")')
    assert ast.root.receiver.source_span.start_column == 1
    assert ast.root.arguments[0].source_span.start_column == 17


def test_parse_ignores_whitespace_comments_and_trailing_commas_without_changing_topology():
    compact = parse('[first_name].eq("john")')
    spaced = parse('/* leading */ [first_name] . eq ( "john" , ) // trailing')

    assert topology(spaced.root) == topology(compact.root)
    assert spaced.source_span.start_offset == 14


def test_parse_string_escapes_in_both_quote_styles():
    left = parse(r"""[name].eq("jo\"hn\\\n")""")
    right = parse(r"[name].eq('jo\'hn\t')")

    assert isinstance(left.root, MethodCall)
    assert isinstance(right.root, MethodCall)
    assert isinstance(left.root.arguments[0], StringLiteral)
    assert isinstance(right.root.arguments[0], StringLiteral)
    assert left.root.arguments[0].value == 'jo"hn\\\n'
    assert right.root.arguments[0].value == "jo'hn\t"


@pytest.mark.parametrize(
    ("source", "expected_node", "expected_value"),
    [
        ("21", IntegerLiteral, 21),
        ("-21", IntegerLiteral, -21),
        ("0.5", DecimalLiteral, 0.5),
        ("-0.5", DecimalLiteral, -0.5),
        ("5.", DecimalLiteral, 5.0),
        ("-5.", DecimalLiteral, -5.0),
        (".5", DecimalLiteral, 0.5),
        ("-.5", DecimalLiteral, -0.5),
    ],
)
def test_parse_numeric_literals(source, expected_node, expected_value):
    ast = parse(source)

    assert isinstance(ast.root, expected_node)
    assert ast.root.value == expected_value


def test_parse_generic_global_calls_and_nested_argument_calls():
    ast = parse('custom([name].unknown("x"), other(1, .5,))')

    assert isinstance(ast.root, GlobalFunctionCall)
    assert ast.root.name == "custom"
    assert len(ast.root.arguments) == 2
    assert isinstance(ast.root.arguments[0], MethodCall)
    assert isinstance(ast.root.arguments[1], GlobalFunctionCall)


@pytest.mark.parametrize(
    "source",
    [
        '"x".eq("x")',
        "other(1).eq(1)",
        "[name].eq(1).gt(0)",
        "true",
        "null",
        "[]",
        "{}",
        "bad-name()",
        "1bad()",
        "[1bad]",
        "[naïve]",
        r'"bad\z"',
        '"unterminated',
    ],
)
def test_parse_rejects_unsupported_or_malformed_syntax(source):
    with pytest.raises(FilterParseError) as exc_info:
        parse(source)

    assert exc_info.value.code == "syntax-error"
    assert exc_info.value.source_span.start_offset >= 0


def test_parse_limits_are_configurable_and_structured():
    config = FilterConfig(
        safety_limits=SafetyLimits(
            maximum_source_length=5,
            maximum_parse_tree_depth=10,
            maximum_function_or_method_arguments=10,
            maximum_path_depth=10,
            maximum_query_nesting=10,
        ),
    )

    with pytest.raises(ParseLimitExceededError) as exc_info:
        parse("[name]", config=config)

    assert exc_info.value.limit_name == "maximum_source_length"
    assert exc_info.value.limit_value == 5
    assert exc_info.value.actual_value == 6


def test_parse_enforces_argument_depth_and_path_limits():
    with pytest.raises(ParseLimitExceededError) as arg_error:
        parse("many(1, 2)", config=FilterConfig(safety_limits=SafetyLimits(maximum_function_or_method_arguments=1)))

    with pytest.raises(ParseLimitExceededError) as path_error:
        parse("[a].[b]", config=FilterConfig(safety_limits=SafetyLimits(maximum_path_depth=1)))

    assert arg_error.value.limit_name == "maximum_function_or_method_arguments"
    assert path_error.value.limit_name == "maximum_path_depth"
