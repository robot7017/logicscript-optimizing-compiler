"""Phase 2 Parser stubs for the LogicScript compiler."""

from __future__ import annotations

from typing import Sequence, TypeAlias

ExpressionAST: TypeAlias = str | list["ExpressionAST"]
StatementAST: TypeAlias = list[object]


def parse_expression(tokens: Sequence[str], start_index: int = 0) -> tuple[ExpressionAST, int]:
    """Parse an expression from token sequence and return (expression_ast, next_index)."""
    raise NotImplementedError("Phase 2 expression parsing is not implemented yet.")


def parse_statement(tokens: Sequence[str]) -> StatementAST:
    """Parse one tokenized line into a statement AST in prefix-nested-list format."""
    raise NotImplementedError("Phase 2 statement parsing is not implemented yet.")


def run_parser(phase_1_rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    """Parse Phase 1 output rows and return phase_2_parser JSON-ready records."""
    raise NotImplementedError("Phase 2 parser pipeline is not implemented yet.")
