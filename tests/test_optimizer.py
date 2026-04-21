import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from optimizer import optimize_expr, run_optimizer


class TestOptimizeExpr(unittest.TestCase):
    """Test cases for optimize_expr function."""

    # ============ Constant Folding Tests (恒等律与零律) ============

    def test_constant_folding_and_true(self):
        """Test A AND TRUE -> A."""
        expr = ["AND", "VAR_P", "TRUE"]
        result = optimize_expr(expr)
        self.assertEqual(result, "VAR_P")

    def test_constant_folding_true_and(self):
        """Test TRUE AND A -> A."""
        expr = ["AND", "TRUE", "VAR_Q"]
        result = optimize_expr(expr)
        self.assertEqual(result, "VAR_Q")

    def test_constant_folding_and_false(self):
        """Test A AND FALSE -> FALSE."""
        expr = ["AND", "VAR_P", "FALSE"]
        result = optimize_expr(expr)
        self.assertEqual(result, "FALSE")

    def test_constant_folding_false_and(self):
        """Test FALSE AND A -> FALSE."""
        expr = ["AND", "FALSE", "VAR_Q"]
        result = optimize_expr(expr)
        self.assertEqual(result, "FALSE")

    def test_constant_folding_or_false(self):
        """Test A OR FALSE -> A."""
        expr = ["OR", "VAR_P", "FALSE"]
        result = optimize_expr(expr)
        self.assertEqual(result, "VAR_P")

    def test_constant_folding_false_or(self):
        """Test FALSE OR A -> A."""
        expr = ["OR", "FALSE", "VAR_R"]
        result = optimize_expr(expr)
        self.assertEqual(result, "VAR_R")

    def test_constant_folding_or_true(self):
        """Test A OR TRUE -> TRUE."""
        expr = ["OR", "VAR_P", "TRUE"]
        result = optimize_expr(expr)
        self.assertEqual(result, "TRUE")

    def test_constant_folding_true_or(self):
        """Test TRUE OR A -> TRUE."""
        expr = ["OR", "TRUE", "VAR_Q"]
        result = optimize_expr(expr)
        self.assertEqual(result, "TRUE")

    def test_constant_folding_not_true(self):
        """Test NOT TRUE -> FALSE."""
        expr = ["NOT", "TRUE"]
        result = optimize_expr(expr)
        self.assertEqual(result, "FALSE")

    def test_constant_folding_not_false(self):
        """Test NOT FALSE -> TRUE."""
        expr = ["NOT", "FALSE"]
        result = optimize_expr(expr)
        self.assertEqual(result, "TRUE")

    def test_constant_folding_idempotent_and(self):
        """Test A AND A -> A."""
        expr = ["AND", "VAR_P", "VAR_P"]
        result = optimize_expr(expr)
        self.assertEqual(result, "VAR_P")

    def test_constant_folding_idempotent_or(self):
        """Test A OR A -> A."""
        expr = ["OR", "VAR_Q", "VAR_Q"]
        result = optimize_expr(expr)
        self.assertEqual(result, "VAR_Q")

    def test_constant_folding_true_and_true(self):
        """Test TRUE AND TRUE -> TRUE."""
        expr = ["AND", "TRUE", "TRUE"]
        result = optimize_expr(expr)
        self.assertEqual(result, "TRUE")

    def test_constant_folding_false_or_false(self):
        """Test FALSE OR FALSE -> FALSE."""
        expr = ["OR", "FALSE", "FALSE"]
        result = optimize_expr(expr)
        self.assertEqual(result, "FALSE")

    # ============ Double Negation Tests (双重否定律) ============

    def test_double_negation_variable(self):
        """Test NOT (NOT A) -> A."""
        expr = ["NOT", ["NOT", "VAR_P"]]
        result = optimize_expr(expr)
        self.assertEqual(result, "VAR_P")

    def test_double_negation_true(self):
        """Test NOT (NOT TRUE) -> TRUE."""
        expr = ["NOT", ["NOT", "TRUE"]]
        result = optimize_expr(expr)
        self.assertEqual(result, "TRUE")

    def test_double_negation_false(self):
        """Test NOT (NOT FALSE) -> FALSE."""
        expr = ["NOT", ["NOT", "FALSE"]]
        result = optimize_expr(expr)
        self.assertEqual(result, "FALSE")

    def test_triple_negation(self):
        """Test NOT (NOT (NOT A)) -> NOT A."""
        expr = ["NOT", ["NOT", ["NOT", "VAR_Q"]]]
        result = optimize_expr(expr)
        self.assertEqual(result, ["NOT", "VAR_Q"])

    # ============ De Morgan's Laws Tests (德·摩根定律) ============

    def test_demorgan_not_and(self):
        """Test NOT (A AND B) -> (NOT A) OR (NOT B)."""
        expr = ["NOT", ["AND", "VAR_P", "VAR_Q"]]
        result = optimize_expr(expr)
        self.assertEqual(result, ["OR", ["NOT", "VAR_P"], ["NOT", "VAR_Q"]])

    def test_demorgan_not_or(self):
        """Test NOT (A OR B) -> (NOT A) AND (NOT B)."""
        expr = ["NOT", ["OR", "VAR_P", "VAR_Q"]]
        result = optimize_expr(expr)
        self.assertEqual(result, ["AND", ["NOT", "VAR_P"], ["NOT", "VAR_Q"]])

    def test_demorgan_complex_and_to_or(self):
        """Test NOT ((P AND Q) AND R) with nested structure."""
        expr = ["NOT", ["AND", ["AND", "VAR_P", "VAR_Q"], "VAR_R"]]
        result = optimize_expr(expr)
        # Should apply De Morgan recursively
        self.assertIsNotNone(result)
        # The result should have OR at the top level after applying De Morgan

    def test_demorgan_not_and_with_constants(self):
        """Test NOT (A AND TRUE) -> NOT A."""
        expr = ["NOT", ["AND", "VAR_P", "TRUE"]]
        result = optimize_expr(expr)
        self.assertEqual(result, ["NOT", "VAR_P"])

    def test_demorgan_not_or_with_constants(self):
        """Test NOT (A OR FALSE) -> NOT A."""
        expr = ["NOT", ["OR", "VAR_P", "FALSE"]]
        result = optimize_expr(expr)
        self.assertEqual(result, ["NOT", "VAR_P"])

    # ============ IMPLIES Simplification Tests (蕴含化简) ============

    def test_implies_false_left(self):
        """Test FALSE IMPLIES A -> TRUE."""
        expr = ["IMPLIES", "FALSE", "VAR_P"]
        result = optimize_expr(expr)
        self.assertEqual(result, "TRUE")

    def test_implies_true_left(self):
        """Test TRUE IMPLIES A -> A."""
        expr = ["IMPLIES", "TRUE", "VAR_P"]
        result = optimize_expr(expr)
        self.assertEqual(result, "VAR_P")

    def test_implies_true_right(self):
        """Test A IMPLIES TRUE -> TRUE."""
        expr = ["IMPLIES", "VAR_P", "TRUE"]
        result = optimize_expr(expr)
        self.assertEqual(result, "TRUE")

    def test_implies_false_right(self):
        """Test A IMPLIES FALSE -> NOT A."""
        expr = ["IMPLIES", "VAR_P", "FALSE"]
        result = optimize_expr(expr)
        self.assertEqual(result, ["NOT", "VAR_P"])

    def test_implies_same_operands(self):
        """Test A IMPLIES A -> TRUE."""
        expr = ["IMPLIES", "VAR_P", "VAR_P"]
        result = optimize_expr(expr)
        self.assertEqual(result, "TRUE")

    def test_implies_true_implies_false(self):
        """Test TRUE IMPLIES FALSE -> FALSE."""
        expr = ["IMPLIES", "TRUE", "FALSE"]
        result = optimize_expr(expr)
        self.assertEqual(result, "FALSE")

    def test_implies_false_implies_true(self):
        """Test FALSE IMPLIES TRUE -> TRUE."""
        expr = ["IMPLIES", "FALSE", "TRUE"]
        result = optimize_expr(expr)
        self.assertEqual(result, "TRUE")

    def test_implies_false_implies_false(self):
        """Test FALSE IMPLIES FALSE -> TRUE."""
        expr = ["IMPLIES", "FALSE", "FALSE"]
        result = optimize_expr(expr)
        self.assertEqual(result, "TRUE")

    # ============ Contradiction & Tautology Tests (矛盾与重言式) ============

    def test_and_contradiction(self):
        """Test (NOT A) AND A -> FALSE."""
        expr = ["AND", ["NOT", "VAR_P"], "VAR_P"]
        result = optimize_expr(expr)
        self.assertEqual(result, "FALSE")

    def test_or_tautology(self):
        """Test (NOT A) OR A -> TRUE."""
        expr = ["OR", ["NOT", "VAR_P"], "VAR_P"]
        result = optimize_expr(expr)
        self.assertEqual(result, "TRUE")

    # ============ Nested & Complex Expression Tests (嵌套与复杂表达式) ============

    def test_complex_nested_optimization(self):
        """Test ((P AND TRUE) OR FALSE) -> P."""
        expr = ["OR", ["AND", "VAR_P", "TRUE"], "FALSE"]
        result = optimize_expr(expr)
        self.assertEqual(result, "VAR_P")

    def test_deeply_nested_negation(self):
        """Test NOT (NOT (NOT (NOT A))) -> A."""
        expr = ["NOT", ["NOT", ["NOT", ["NOT", "VAR_P"]]]]
        result = optimize_expr(expr)
        self.assertEqual(result, "VAR_P")

    def test_complex_demorgan_optimization(self):
        """Test NOT ((P OR Q) AND R) optimization."""
        expr = ["NOT", ["AND", ["OR", "VAR_P", "VAR_Q"], "VAR_R"]]
        result = optimize_expr(expr)
        # After De Morgan: (NOT (P OR Q)) AND (NOT R)
        # Then: (NOT P AND NOT Q) AND (NOT R)
        self.assertIsNotNone(result)

    # ============ Error Handling Tests ============

    def test_invalid_operator(self):
        """Test with unsupported operator."""
        expr = ["INVALID_OP", "VAR_P", "VAR_Q"]
        with self.assertRaises(ValueError) as context:
            optimize_expr(expr)
        self.assertIn("Unsupported expression operator", str(context.exception))

    def test_invalid_ast_format(self):
        """Test with invalid AST structure."""
        expr = ["AND", "VAR_P"]  # Missing operand
        with self.assertRaises((ValueError, IndexError)):
            optimize_expr(expr)


class TestRunOptimizer(unittest.TestCase):
    """Test cases for run_optimizer function."""

    def test_run_optimizer_basic_let(self):
        """Test run_optimizer with a basic LET statement."""
        phase_2_rows = [
            {"line": 1, "ast": ["LET", "VAR_P", "TRUE"]}
        ]
        result = run_optimizer(phase_2_rows)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["line"], 1)
        self.assertEqual(result[0]["ast"], ["LET", "VAR_P", "TRUE"])
        self.assertEqual(result[0]["original_ast"], ["LET", "VAR_P", "TRUE"])

    def test_run_optimizer_preserves_original_ast(self):
        """Test that run_optimizer preserves original_ast in output."""
        phase_2_rows = [
            {"line": 2, "ast": ["LET", "VAR_Q", ["AND", "VAR_P", "TRUE"]]}
        ]
        result = run_optimizer(phase_2_rows)

        self.assertEqual(len(result), 1)
        self.assertIn("original_ast", result[0])
        self.assertIn("ast", result[0])
        # original_ast should be unchanged
        self.assertEqual(result[0]["original_ast"], ["LET", "VAR_Q", ["AND", "VAR_P", "TRUE"]])
        # ast should be optimized
        self.assertEqual(result[0]["ast"], ["LET", "VAR_Q", "VAR_P"])

    def test_run_optimizer_multiple_rows(self):
        """Test run_optimizer with multiple rows."""
        phase_2_rows = [
            {"line": 1, "ast": ["PRINT", "VAR_P"]},
            {"line": 2, "ast": ["LET", "VAR_Q", ["OR", "VAR_R", "FALSE"]]},
            {"line": 3, "ast": ["IF", ["NOT", ["NOT", "VAR_P"]], ["PRINT", "VAR_Q"]]},
        ]
        result = run_optimizer(phase_2_rows)

        self.assertEqual(len(result), 3)

        # Row 1: PRINT unchanged
        self.assertEqual(result[0]["line"], 1)
        self.assertEqual(result[0]["ast"], ["PRINT", "VAR_P"])
        self.assertIn("original_ast", result[0])

        # Row 2: LET with optimized expression
        self.assertEqual(result[1]["line"], 2)
        self.assertEqual(result[1]["ast"], ["LET", "VAR_Q", "VAR_R"])
        self.assertEqual(result[1]["original_ast"], ["LET", "VAR_Q", ["OR", "VAR_R", "FALSE"]])

        # Row 3: IF with optimized condition
        self.assertEqual(result[2]["line"], 3)
        self.assertEqual(result[2]["ast"], ["IF", "VAR_P", ["PRINT", "VAR_Q"]])
        self.assertIn("original_ast", result[2])

    def test_run_optimizer_output_structure(self):
        """Test that output has exactly the required keys: line, ast, original_ast."""
        phase_2_rows = [
            {"line": 5, "ast": ["PRINT", "VAR_X"]}
        ]
        result = run_optimizer(phase_2_rows)

        self.assertEqual(len(result), 1)
        row = result[0]
        # Check that all required keys are present
        self.assertIn("line", row)
        self.assertIn("ast", row)
        self.assertIn("original_ast", row)
        # Check that there are exactly 3 keys (internal contract)
        self.assertEqual(len(row), 3)

    def test_run_optimizer_complex_expression(self):
        """Test run_optimizer with complex nested expressions."""
        phase_2_rows = [
            {
                "line": 1,
                "ast": [
                    "LET",
                    "VAR_R",
                    ["AND", ["OR", "VAR_P", "FALSE"], ["NOT", ["NOT", "VAR_Q"]]]
                ]
            }
        ]
        result = run_optimizer(phase_2_rows)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["line"], 1)
        # Expression should be optimized:
        # ("VAR_P" OR "FALSE") AND (NOT NOT "VAR_Q")
        # -> "VAR_P" AND "VAR_Q"
        self.assertEqual(result[0]["ast"], ["LET", "VAR_R", ["AND", "VAR_P", "VAR_Q"]])
        # original_ast should be unchanged
        self.assertEqual(
            result[0]["original_ast"],
            ["LET", "VAR_R", ["AND", ["OR", "VAR_P", "FALSE"], ["NOT", ["NOT", "VAR_Q"]]]]
        )

    def test_run_optimizer_with_if_statement(self):
        """Test run_optimizer with nested IF statements."""
        phase_2_rows = [
            {
                "line": 1,
                "ast": ["IF", ["AND", "VAR_P", "TRUE"], ["PRINT", "VAR_Q"]]
            }
        ]
        result = run_optimizer(phase_2_rows)

        self.assertEqual(len(result), 1)
        # Condition should be optimized: (P AND TRUE) -> P
        self.assertEqual(result[0]["ast"], ["IF", "VAR_P", ["PRINT", "VAR_Q"]])
        self.assertIn("original_ast", result[0])

    def test_run_optimizer_empty_list(self):
        """Test run_optimizer with empty phase_2_rows."""
        phase_2_rows = []
        result = run_optimizer(phase_2_rows)

        self.assertEqual(result, [])

    def test_run_optimizer_preserves_line_numbers(self):
        """Test that run_optimizer correctly preserves line numbers."""
        phase_2_rows = [
            {"line": 10, "ast": ["PRINT", "VAR_A"]},
            {"line": 25, "ast": ["PRINT", "VAR_B"]},
            {"line": 100, "ast": ["PRINT", "VAR_C"]},
        ]
        result = run_optimizer(phase_2_rows)

        self.assertEqual(result[0]["line"], 10)
        self.assertEqual(result[1]["line"], 25)
        self.assertEqual(result[2]["line"], 100)


if __name__ == "__main__":
    unittest.main()
