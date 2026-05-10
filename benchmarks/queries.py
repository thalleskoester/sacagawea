"""Named benchmark query workloads for sacagawea."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

BenchmarkOperation = Literal["parse", "interpret", "evaluate"]


@dataclass(frozen=True, slots=True)
class QueryCase:
    """One reusable benchmark query case."""

    name: str
    group: str
    description: str
    query: str


def _many_arguments_query() -> str:
    arguments = ["[is_active].isTrue()"]
    arguments.extend("[score].ge(0)" for _ in range(63))
    return f"and({', '.join(arguments)})"


def _nested_not_query(depth: int) -> str:
    query = "[is_active].isTrue()"
    for _ in range(depth):
        query = f"not({query})"
    return query


QUERY_CASES: Final[tuple[QueryCase, ...]] = (
    QueryCase(
        name="scalar_eq",
        group="scalar",
        description="Baseline string equality on a root field.",
        query='[first_name].eq("john")',
    ),
    QueryCase(
        name="numeric_and",
        group="logical",
        description="Several common numeric, Boolean, and string predicates.",
        query=(
            "and("
            "[is_active].isTrue(), "
            "[age].ge(18), "
            "[balance].ge(0), "
            '[email].regex("^[a-z0-9._%+-]+@(?:example\\\\.com|other\\\\.test)$")'
            ")"
        ),
    ),
    QueryCase(
        name="many_args",
        group="logical",
        description="A variadic and(...) call at the default 64-argument limit.",
        query=_many_arguments_query(),
    ),
    QueryCase(
        name="deep_expression",
        group="parse",
        description="Nested not(...) calls that increase parse tree depth.",
        query=_nested_not_query(depth=20),
    ),
    QueryCase(
        name="deep_path_8",
        group="path",
        description="Dictionary traversal through an 8-segment path.",
        query='[deep].[level_01].[level_02].[level_03].[level_04].[level_05].[level_06].[value].eq("target")',
    ),
    QueryCase(
        name="deep_path_32",
        group="path",
        description="Dictionary traversal at the default 32-segment path limit.",
        query=("[deep]" + "".join(f".[level_{level:02d}]" for level in range(1, 31)) + '.[value].eq("target")'),
    ),
    QueryCase(
        name="query_fanout",
        group="query",
        description="A list-of-dictionaries .query(...) with early exit on matching items.",
        query='[roles].query([role], [role].[name].eq("root"))',
    ),
    QueryCase(
        name="query_nested",
        group="query",
        description="Nested .query(...) calls that reference inner list item fields.",
        query=(
            "[teams].query("
            "[team], "
            "[team].[members].query("
            "[member], "
            'and([member].[active].isTrue(), [member].[email].regex("@example\\\\.com$"))'
            ")"
            ")"
        ),
    ),
    QueryCase(
        name="scalar_list_regex",
        group="query",
        description="A scalar list alias combined with regex matching.",
        query='[last_ips].query([ip], [ip].regex("^10\\\\.238\\\\.115\\\\.[0-9]+$"))',
    ),
    QueryCase(
        name="regex_simple",
        group="regex",
        description="A practical anchored email regex.",
        query='[email].regex("^[a-z0-9._%+-]+@example\\\\.com$")',
    ),
    QueryCase(
        name="regex_complex",
        group="regex",
        description="Alternation, grouping, numeric ranges, and anchors.",
        query='[tracking_code].regex("^(ORD|INV)-[0-9]{4}-(alpha|beta|gamma)-(north|south|east|west)$")',
    ),
    QueryCase(
        name="short_circuit_and",
        group="short_circuit",
        description="False-first and(...) that avoids evaluating a missing field.",
        query='and([record_id].lt(0), [missing].eq("unreached"))',
    ),
    QueryCase(
        name="short_circuit_or",
        group="short_circuit",
        description="True-first or(...) that avoids evaluating a missing field.",
        query='or([record_id].ge(0), [missing].eq("unreached"))',
    ),
    QueryCase(
        name="temporal_component",
        group="temporal",
        description="DateTime component extraction and integer comparison.",
        query="[created_at].[year].eq(2026)",
    ),
)

QUERY_CASES_BY_NAME: Final[dict[str, QueryCase]] = {case.name: case for case in QUERY_CASES}
DEFAULT_OPERATIONS: Final[tuple[BenchmarkOperation, ...]] = ("parse", "interpret", "evaluate")
