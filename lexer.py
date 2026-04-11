"""Phase 1 Lexer stubs for the LogicScript compiler."""

from __future__ import annotations

from typing import Sequence

TOKEN_MAP: dict[str, str] = {
    "let": "LET",
    "if": "IF",
    "then": "THEN",
    "print": "PRINT",
    "T": "TRUE",
    "F": "FALSE",
    "AND": "AND",
    "OR": "OR",
    "NOT": "NOT",
    "IMPLIES": "IMPLIES",
    "=": "EQ",
    "(": "L_PAREN",
    ")": "R_PAREN",
}


def normalize_variable_token(identifier: str) -> str:
    """Convert a single lowercase variable name into spec format, e.g. 'p' -> 'VAR_P'."""
    raise NotImplementedError("Phase 1 variable normalization is not implemented yet.")


def tokenize_line(line: str, line_number: int) -> list[str]:
    """Tokenize one source line into spec tokens for LogicScript."""
    raise NotImplementedError("Phase 1 line tokenization is not implemented yet.")


def run_lexer(source_lines: Sequence[str]) -> list[dict[str, object]]:
    """Tokenize all source lines and return phase_1_lexer JSON-ready records."""
    raise NotImplementedError("Phase 1 lexer pipeline is not implemented yet.")
