"""Call-scoped configuration contracts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from sacagawea._ast import ExpressionNode

if TYPE_CHECKING:
    from collections.abc import Mapping

RegexEvaluator = Callable[[str, str], bool]
GlobalFunction = Callable[[Any, tuple[ExpressionNode, ...]], object]


@dataclass(frozen=True, slots=True)
class SafetyLimits:
    """Deterministic parser and runtime safety limits."""

    maximum_source_length: int = 10000
    maximum_parse_tree_depth: int = 100
    maximum_function_or_method_arguments: int = 64
    maximum_path_depth: int = 32
    maximum_query_nesting: int = 16

    @classmethod
    def default(cls) -> SafetyLimits:
        """Return the documented default safety limits."""
        return cls()


@dataclass(frozen=True, slots=True)
class FilterConfig:
    """Immutable or mutation-safe filter evaluation configuration."""

    safety_limits: SafetyLimits = field(default_factory=SafetyLimits.default)
    regex_evaluator: RegexEvaluator | None = None
    include_default_global_functions: bool = True
    global_functions: Mapping[str, GlobalFunction | None] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Freeze mutable mapping input supplied by callers."""
        object.__setattr__(self, "global_functions", MappingProxyType(dict(self.global_functions)))

    @classmethod
    def default(cls) -> FilterConfig:
        """Return the documented default filter configuration."""
        return cls()
