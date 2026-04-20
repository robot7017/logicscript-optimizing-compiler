"""Phase 3 Optimizer for the LogicScript compiler."""

from __future__ import annotations

from typing import Any, Sequence


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
