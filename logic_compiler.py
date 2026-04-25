#!/usr/bin/env python3
"""Single-file LogicScript compiler for final submission."""

from __future__ import annotations

import json
import re
import sys
from itertools import product
from pathlib import Path
from typing import Any, Sequence, TypeAlias

# =========================
# Phase 1: Lexer
# =========================

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

# =========================
# Phase 2: Parser
# =========================

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

# =========================
# Phase 3: Optimizer
# =========================

def _is_atomic_expr(node: object) -> bool:
    """Return True if node is an atomic expression: TRUE / FALSE / VAR_X."""
    return isinstance(node, str) and (
        node in {"TRUE", "FALSE"} or node.startswith("VAR_")
    )


def _is_not_of(left: object, right: object) -> bool:
    """Return True if left is exactly ['NOT', right]."""
    return isinstance(left, list) and len(left) == 2 and left[0] == "NOT" and left[1] == right


def _simplify_and(left: object, right: object) -> object:
    """Apply simplification rules for AND."""
    if left == "FALSE" or right == "FALSE":
        return "FALSE"
    if left == "TRUE":
        return right
    if right == "TRUE":
        return left
    if left == right:
        return left
    if _is_not_of(left, right) or _is_not_of(right, left):
        return "FALSE"
    return ["AND", left, right]


def _simplify_or(left: object, right: object) -> object:
    """Apply simplification rules for OR."""
    if left == "TRUE" or right == "TRUE":
        return "TRUE"
    if left == "FALSE":
        return right
    if right == "FALSE":
        return left
    if left == right:
        return left
    if _is_not_of(left, right) or _is_not_of(right, left):
        return "TRUE"
    return ["OR", left, right]


def _simplify_implies(left: object, right: object) -> object:
    """Apply simplification rules for IMPLIES."""
    if left == "FALSE":
        return "TRUE"
    if left == "TRUE":
        return right
    if right == "TRUE":
        return "TRUE"
    if right == "FALSE":
        return optimize_expr(["NOT", left])
    if left == right:
        return "TRUE"
    return ["IMPLIES", left, right]


def optimize_expr(expr: object) -> object:
    """
    Recursively optimize an expression AST.

    Valid expression forms:
    - "TRUE", "FALSE", "VAR_X"
    - ["NOT", expr]
    - ["AND", expr, expr]
    - ["OR", expr, expr]
    - ["IMPLIES", expr, expr]
    """
    if _is_atomic_expr(expr):
        return expr

    if not isinstance(expr, list) or not expr:
        raise ValueError(f"Invalid expression AST: {expr}")

    operator = expr[0]

    if operator == "NOT":
        operand = optimize_expr(expr[1])

        # Constant folding
        if operand == "TRUE":
            return "FALSE"
        if operand == "FALSE":
            return "TRUE"

        # Double negation: NOT (NOT A) => A
        if isinstance(operand, list) and operand and operand[0] == "NOT":
            return optimize_expr(operand[1])

        # De Morgan's Laws
        if isinstance(operand, list) and operand and operand[0] == "AND":
            left = optimize_expr(["NOT", operand[1]])
            right = optimize_expr(["NOT", operand[2]])
            return optimize_expr(["OR", left, right])

        if isinstance(operand, list) and operand and operand[0] == "OR":
            left = optimize_expr(["NOT", operand[1]])
            right = optimize_expr(["NOT", operand[2]])
            return optimize_expr(["AND", left, right])

        return ["NOT", operand]

    if operator == "AND":
        left = optimize_expr(expr[1])
        right = optimize_expr(expr[2])
        return _simplify_and(left, right)

    if operator == "OR":
        left = optimize_expr(expr[1])
        right = optimize_expr(expr[2])
        return _simplify_or(left, right)

    if operator == "IMPLIES":
        left = optimize_expr(expr[1])
        right = optimize_expr(expr[2])
        return _simplify_implies(left, right)

    raise ValueError(f"Unsupported expression operator: {operator}")


def optimize_statement(statement_ast: object) -> object:
    """
    Optimize a statement AST without changing statement structure.

    Valid statement forms:
    - ["LET", "VAR_X", expr]
    - ["PRINT", "VAR_X"]
    - ["IF", expr, statement]
    """
    if not isinstance(statement_ast, list) or not statement_ast:
        raise ValueError(f"Invalid statement AST: {statement_ast}")

    statement_type = statement_ast[0]

    if statement_type == "LET":
        _, variable_name, expr = statement_ast
        optimized_expr = optimize_expr(expr)
        return ["LET", variable_name, optimized_expr]

    if statement_type == "PRINT":
        # print does not contain a general expression; keep it unchanged
        _, variable_name = statement_ast
        return ["PRINT", variable_name]

    if statement_type == "IF":
        _, condition_expr, inner_statement = statement_ast
        optimized_condition = optimize_expr(condition_expr)
        optimized_inner = optimize_statement(inner_statement)
        return ["IF", optimized_condition, optimized_inner]

    raise ValueError(f"Unsupported statement type: {statement_type}")


def run_optimizer(phase_2_rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    """
    Optimize parser AST rows.

    Input rows:
        {"line": <int>, "ast": <statement_ast>}

    Output rows (internal contract with Phase 4):
        {"line": <int>, "ast": <optimized_statement_ast>, "original_ast": <original_statement_ast>}
    """
    optimized_rows: list[dict[str, object]] = []

    for row in phase_2_rows:
        line_num = row["line"]
        original_ast = row["ast"]
        optimized_ast = optimize_statement(original_ast)

        optimized_rows.append(
            {
                "line": line_num,
                "ast": optimized_ast,
                "original_ast": original_ast,
            }
        )

    return optimized_rows

# =========================
# Phase 4: Verification + Execution
# =========================

class ExecutionError(Exception):
    pass


def evaluate_expression(ast_node: object, state_dict: dict[str, str]) -> str:
    """Evaluate an expression AST node and return "TRUE" or "FALSE".

    Args:
        ast_node: An AST node as a nested prefix list or atomic string.
        state_dict: Mapping from variable names like "VAR_P" to "TRUE"/"FALSE".

    Returns:
        "TRUE" or "FALSE".
    """
    if isinstance(ast_node, str):
        if ast_node == "TRUE":
            return "TRUE"
        if ast_node == "FALSE":
            return "FALSE"
        if ast_node.startswith("VAR_"):
            if ast_node not in state_dict:
                raise ExecutionError(f"Variable {ast_node} referenced before assignment.")
            return state_dict[ast_node]
        raise ValueError(f"Unknown atomic AST node: {ast_node}")

    if not isinstance(ast_node, list) or not ast_node:
        raise ValueError(f"Invalid AST node: {ast_node}")

    operator = ast_node[0]
    if operator == "NOT":
        operand = evaluate_expression(ast_node[1], state_dict)
        return "FALSE" if operand == "TRUE" else "TRUE"

    left_value = evaluate_expression(ast_node[1], state_dict)
    right_value = evaluate_expression(ast_node[2], state_dict)

    if operator == "AND":
        return "TRUE" if left_value == "TRUE" and right_value == "TRUE" else "FALSE"
    if operator == "OR":
        return "TRUE" if left_value == "TRUE" or right_value == "TRUE" else "FALSE"
    if operator == "IMPLIES":
        return "FALSE" if left_value == "TRUE" and right_value == "FALSE" else "TRUE"

    raise ValueError(f"Unsupported operator in AST: {operator}")


def _collect_variables(ast_node: object, variables: set[str]) -> None:
    if isinstance(ast_node, str):
        if ast_node.startswith("VAR_"):
            variables.add(ast_node)
        return

    if not isinstance(ast_node, list):
        raise ValueError(f"Invalid AST node while collecting variables: {ast_node}")

    for child in ast_node[1:]:
        _collect_variables(child, variables)


def verify_equivalence(original_ast: object, optimized_ast: object) -> dict[str, object]:
    """Verify logical equivalence between original and optimized AST expressions."""
    variables: set[str] = set()
    _collect_variables(original_ast, variables)
    _collect_variables(optimized_ast, variables)
    variables_tested = sorted(variables)

    ast_original_column: list[str] = []
    ast_optimized_column: list[str] = []

    for values in product(("TRUE", "FALSE"), repeat=len(variables_tested)):
        state_dict = dict(zip(variables_tested, values))
        original_value = evaluate_expression(original_ast, state_dict)
        optimized_value = evaluate_expression(optimized_ast, state_dict)
        ast_original_column.append(original_value)
        ast_optimized_column.append(optimized_value)

    is_equivalent = "TRUE" if ast_original_column == ast_optimized_column else "FALSE"

    return {
        "variables_tested": variables_tested,
        "ast_original_column": ast_original_column,
        "ast_optimized_column": ast_optimized_column,
        "is_equivalent": is_equivalent,
    }


def execute_statement(
    statement_ast: object,
    state_dict: dict[str, str],
    printed_output: list[dict[str, str]],
    line_num: int,
) -> None:
    """Execute a statement AST and update state_dict / printed_output."""
    if not isinstance(statement_ast, list) or not statement_ast:
        raise ValueError(f"Invalid statement AST: {statement_ast}")

    statement_type = statement_ast[0]
    if statement_type == "LET":
        _, variable_name, expression = statement_ast
        value = evaluate_expression(expression, state_dict)
        state_dict[variable_name] = value
        return

    if statement_type == "PRINT":
        _, variable_name = statement_ast
        if variable_name not in state_dict:
            raise ExecutionError(f"Variable {variable_name} referenced before assignment.")
        output_value = state_dict[variable_name]
        printed_output.append({"line": line_num, "output": output_value})
        return

    if statement_type == "IF":
        _, condition_ast, inner_statement = statement_ast
        condition_value = evaluate_expression(condition_ast, state_dict)
        if condition_value == "TRUE":
            execute_statement(inner_statement, state_dict, printed_output, line_num)
        return

    raise ValueError(f"Unsupported statement type: {statement_type}")


def _is_expression_ast(ast_node: object) -> bool:
    if isinstance(ast_node, str):
        return ast_node in {"TRUE", "FALSE"} or ast_node.startswith("VAR_")
    if not isinstance(ast_node, list) or not ast_node:
        return False
    return ast_node[0] in {"NOT", "AND", "OR", "IMPLIES"}


def _collect_expression_asts(ast_node: object, expressions: list[object]) -> None:
    if isinstance(ast_node, str):
        if _is_expression_ast(ast_node):
            expressions.append(ast_node)
        return

    if not isinstance(ast_node, list) or not ast_node:
        return

    node_type = ast_node[0]
    if node_type == "LET":
        _, _, expr = ast_node
        expressions.append(expr)
        return

    if node_type == "IF":
        _, condition_ast, inner_statement = ast_node
        expressions.append(condition_ast)
        _collect_expression_asts(inner_statement, expressions)
        return

    if _is_expression_ast(ast_node):
        expressions.append(ast_node)
        return


def run_executor(phase_3_rows: Sequence[dict[str, object]]) -> dict[str, Any]:
    """Verify equivalence and execute optimized AST rows."""
    verifications: list[dict[str, object]] = []
    state_dict: dict[str, str] = {}
    printed_output: list[dict[str, str]] = []
    error_info: dict[str, object] | None = None

    for row in phase_3_rows:
        line_num = row.get("line")

        try:
            original_ast = row.get("original_ast")
            optimized_ast = row.get("ast")
            original_expressions: list[object] = []
            optimized_expressions: list[object] = []

            if original_ast is not None:
                _collect_expression_asts(original_ast, original_expressions)
            if optimized_ast is not None:
                _collect_expression_asts(optimized_ast, optimized_expressions)

            for original_expr, optimized_expr in zip(original_expressions, optimized_expressions):
                if original_expr != optimized_expr:
                    verification = verify_equivalence(original_expr, optimized_expr)
                    verification["line"] = line_num
                    verifications.append(verification)

            if optimized_ast is not None:
                execute_statement(optimized_ast, state_dict, printed_output, line_num)
        except ExecutionError:
            error_info = {
                "phase": "phase_4_execution",
                "line": line_num,
            }
            break

    result = {
        "verifications": verifications,
        "final_state_dictionary": state_dict,
        "printed_output": printed_output,
    }

    if error_info is not None:
        result["error"] = error_info

    return result

# =========================
# Main pipeline
# =========================

def build_initial_trace() -> dict[str, Any]:
    """Return an initially empty trace.

    Phases are added only after they successfully complete.
    """
    return {}


def _extract_line_number(error_text: str) -> int:
    """Best-effort line-number extraction from phase exception messages."""
    match = re.search(r"line\s+(\d+)", error_text)
    if match:
        return int(match.group(1))
    return 0


def _run_phase_1(source_lines: list[str]) -> tuple[list[dict[str, object]], dict[str, object] | None]:
    rows: list[dict[str, object]] = []

    for line_number, source_line in enumerate(source_lines, start=1):
        if not source_line.strip():
            continue
        try:
            tokens = tokenize_line(source_line, line_number)
        except ValueError as exc:
            return rows, {"phase": "phase_1_lexer", "line": _extract_line_number(str(exc))}
        rows.append({"line": line_number, "tokens": tokens})

    return rows, None


def _run_phase_2(
    phase_1_rows: list[dict[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object] | None]:
    rows: list[dict[str, object]] = []

    for row in phase_1_rows:
        line_number = int(row["line"])
        tokens = list(row["tokens"])
        try:
            rows.append(parse_tokens(line_number, tokens))
        except ParserSyntaxError as exc:
            return rows, {"phase": "phase_2_parser", "line": exc.line}

    return rows, None


def _clean_phase_3_rows(phase_3_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    cleaned_rows: list[dict[str, object]] = []
    for row in phase_3_rows:
        cleaned_rows.append({k: v for k, v in row.items() if k != "original_ast"})
    return cleaned_rows


def main(argv: list[str] | None = None) -> int:
    """Validate CLI args, run phases, and write the compiler trace JSON."""
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 2:
        print("Usage: python logic_compiler.py <input_file> <output_file>")
        return 1

    input_path = Path(argv[0])
    output_path = Path(argv[1])

    try:
        source_text = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Failed to read input file: {exc}", file=sys.stderr)
        return 1

    source_lines = source_text.splitlines()
    pipeline_results_dict = build_initial_trace()

    phase_1_rows, phase_1_error = _run_phase_1(source_lines)
    pipeline_results_dict["phase_1_lexer"] = phase_1_rows

    if phase_1_error is not None:
        pipeline_results_dict["error"] = phase_1_error
    else:
        phase_2_rows, phase_2_error = _run_phase_2(phase_1_rows)
        pipeline_results_dict["phase_2_parser"] = phase_2_rows

        if phase_2_error is not None:
            pipeline_results_dict["error"] = phase_2_error
        else:
            phase_3_rows = run_optimizer(phase_2_rows)
            pipeline_results_dict["phase_3_optimizer"] = _clean_phase_3_rows(phase_3_rows)

            executor_results = run_executor(phase_3_rows)
            if "error" in executor_results:
                pipeline_results_dict["error"] = executor_results["error"]
            else:
                pipeline_results_dict["phase_4_execution"] = executor_results

    try:
        output_path.write_text(
            json.dumps(pipeline_results_dict, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"Failed to write output file: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
