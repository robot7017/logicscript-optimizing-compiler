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
    if len(identifier) == 1 and identifier.isalpha() and identifier.islower():
        return f"VAR_{identifier.upper()}"
    raise ValueError(f"Invalid variable identifier: {identifier!r}")


def tokenize_line(line: str, line_number: int) -> list[str]:
    """Tokenize one source line into spec tokens for LogicScript."""
    tokens: list[str] = []
    index = 0

    while index < len(line):
        char = line[index]

        if char.isspace():
            index += 1
            continue

        if char in TOKEN_MAP and char in {"=", "(", ")"}:
            tokens.append(TOKEN_MAP[char])
            index += 1
            continue

        if char.isalpha():
            start = index
            while index < len(line) and line[index].isalpha():
                index += 1

            lexeme = line[start:index]
            if lexeme in TOKEN_MAP:
                tokens.append(TOKEN_MAP[lexeme])
                continue

            try:
                tokens.append(normalize_variable_token(lexeme))
            except ValueError as exc:
                raise ValueError(
                    f"Lexical error on line {line_number}: invalid token {lexeme!r}"
                ) from exc
            continue

        raise ValueError(
            f"Lexical error on line {line_number}: invalid character {char!r}"
        )

    return tokens


def run_lexer(source_lines: Sequence[str]) -> list[dict[str, object]]:
    """Tokenize all source lines and return phase_1_lexer JSON-ready records."""
    phase_1_rows: list[dict[str, object]] = []

    for line_number, source_line in enumerate(source_lines, start=1):
        if not source_line.strip():
            continue

        token_row = tokenize_line(source_line, line_number)
        phase_1_rows.append({"line": line_number, "tokens": token_row})

    return phase_1_rows
