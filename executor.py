"""Phase 4 Executor placeholder for the LogicScript compiler."""

from __future__ import annotations

from itertools import product
from typing import Any, Sequence


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
