"""Public entry points for parsing and interpreting filters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sacagawea._config import FilterConfig
from sacagawea._parser import parse_source
from sacagawea._runtime import interpret_ast

if TYPE_CHECKING:
    from sacagawea._ast import AST
    from sacagawea._result import FinalResult


def parse(query: str, config: FilterConfig | None = None) -> AST:
    """Parse filter source into a pure AST."""
    effective_config = FilterConfig.default() if config is None else config
    return parse_source(query, effective_config)


def interpret(ast: AST, data: list[dict], config: FilterConfig | None = None) -> FinalResult:
    """Interpret a parsed AST against in-memory dictionary records."""
    effective_config = FilterConfig.default() if config is None else config
    return interpret_ast(ast, data, effective_config)


def evaluate(query: str, data: list[dict], config: FilterConfig | None = None) -> FinalResult:
    """Parse and interpret a filter query with one shared configuration."""
    effective_config = FilterConfig.default() if config is None else config
    return interpret(parse(query, effective_config), data, effective_config)
