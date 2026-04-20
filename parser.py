"""Phase 2 Parser stubs for the LogicScript compiler."""

from __future__ import annotations

from typing import Sequence, TypeAlias

ExpressionAST: TypeAlias = str | list["ExpressionAST"]
StatementAST: TypeAlias = list[object]


class ParserSyntaxError(Exception):
    """Syntax error with source line number for Phase 2 fail-fast behavior."""

    def __init__(self, line: int, message: str) -> None:
        self.line = line
        self.message = message
        super().__init__(f"Syntax error on line {line}: {message}")


def _is_variable_token(token: str) -> bool:
    return len(token) == 5 and token.startswith("VAR_") and token[4].isalpha() and token[4].isupper()


def parse_expression(
    tokens: Sequence[str],
    start_index: int = 0,
    line_number: int = 0,
) -> tuple[ExpressionAST, int]:
    """Parse an expression from token sequence and return (expression_ast, next_index)."""
    token_list = list(tokens)
    if start_index >= len(token_list):
        raise ParserSyntaxError(line_number, "Expected expression but reached end of tokens")

    token = token_list[start_index]
    if token in {"TRUE", "FALSE"} or _is_variable_token(token):
        return token, start_index + 1

    if token != "L_PAREN":
        raise ParserSyntaxError(line_number, f"Invalid expression token {token!r}")

    if start_index + 1 >= len(token_list):
        raise ParserSyntaxError(line_number, "Missing expression content after L_PAREN")

    next_token = token_list[start_index + 1]
    if next_token == "NOT":
        operand_ast, next_index = parse_expression(
            token_list,
            start_index=start_index + 2,
            line_number=line_number,
        )
        if next_index >= len(token_list) or token_list[next_index] != "R_PAREN":
            raise ParserSyntaxError(line_number, "Missing closing R_PAREN for NOT expression")
        return ["NOT", operand_ast], next_index + 1

    left_ast, operator_index = parse_expression(
        token_list,
        start_index=start_index + 1,
        line_number=line_number,
    )

    if operator_index >= len(token_list):
        raise ParserSyntaxError(line_number, "Missing binary operator and right operand")

    operator_token = token_list[operator_index]
    if operator_token not in {"AND", "OR", "IMPLIES"}:
        raise ParserSyntaxError(
            line_number,
            f"Expected binary operator AND/OR/IMPLIES, got {operator_token!r}",
        )

    right_ast, next_index = parse_expression(
        token_list,
        start_index=operator_index + 1,
        line_number=line_number,
    )
    if next_index >= len(token_list) or token_list[next_index] != "R_PAREN":
        raise ParserSyntaxError(line_number, "Missing closing R_PAREN for binary expression")

    return [operator_token, left_ast, right_ast], next_index + 1


def _parse_statement_at(
    tokens: Sequence[str],
    start_index: int,
    line_number: int,
) -> tuple[StatementAST, int]:
    token_list = list(tokens)
    if start_index >= len(token_list):
        raise ParserSyntaxError(line_number, "Expected statement but reached end of tokens")

    statement_start = token_list[start_index]

    if statement_start == "LET":
        if start_index + 1 >= len(token_list) or not _is_variable_token(token_list[start_index + 1]):
            raise ParserSyntaxError(line_number, "LET must be followed by a variable token")
        if start_index + 2 >= len(token_list) or token_list[start_index + 2] != "EQ":
            raise ParserSyntaxError(line_number, "LET statement is missing EQ")

        expr_ast, next_index = parse_expression(
            token_list,
            start_index=start_index + 3,
            line_number=line_number,
        )
        return ["LET", token_list[start_index + 1], expr_ast], next_index

    if statement_start == "PRINT":
        if start_index + 1 >= len(token_list) or not _is_variable_token(token_list[start_index + 1]):
            raise ParserSyntaxError(line_number, "PRINT must be followed by a variable token")
        return ["PRINT", token_list[start_index + 1]], start_index + 2

    if statement_start == "IF":
        condition_ast, next_index = parse_expression(
            token_list,
            start_index=start_index + 1,
            line_number=line_number,
        )
        if next_index >= len(token_list) or token_list[next_index] != "THEN":
            raise ParserSyntaxError(line_number, "IF statement is missing THEN")

        nested_statement_ast, statement_end = _parse_statement_at(
            token_list,
            start_index=next_index + 1,
            line_number=line_number,
        )
        return ["IF", condition_ast, nested_statement_ast], statement_end

    raise ParserSyntaxError(line_number, f"Invalid statement start token {statement_start!r}")


def parse_statement(tokens: Sequence[str], line_number: int = 0) -> StatementAST:
    """Parse one tokenized line into a statement AST in prefix-nested-list format."""
    statement_ast, next_index = _parse_statement_at(tokens, start_index=0, line_number=line_number)
    token_count = len(tokens)
    if next_index != token_count:
        raise ParserSyntaxError(line_number, f"Trailing tokens after valid statement at index {next_index}")
    return statement_ast


def parse_tokens(line_no: int, tokens: list[str]) -> dict:
    """Parse one Phase 1 token row into the Phase 2 external row contract."""
    statement_ast = parse_statement(tokens, line_number=line_no)
    return {"line": line_no, "ast": statement_ast}


def run_parser(phase_1_rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    """Parse Phase 1 output rows and return phase_2_parser JSON-ready records."""
    phase_2_rows: list[dict[str, object]] = []

    for row in phase_1_rows:
        line_number = int(row["line"])
        tokens = list(row["tokens"])
        phase_2_rows.append(parse_tokens(line_number, tokens))

    return phase_2_rows
