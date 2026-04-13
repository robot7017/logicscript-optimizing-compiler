import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from executor import evaluate_expression, verify_equivalence, run_executor


class TestExecutor(unittest.TestCase):
    def test_evaluate_expression_demorgan(self):
        state = {"VAR_P": "TRUE", "VAR_Q": "FALSE"}

        expr_demorgan = ["NOT", ["OR", ["NOT", "VAR_P"], ["NOT", "VAR_Q"]]]
        expr_simplified = ["AND", "VAR_P", "VAR_Q"]

        self.assertEqual(evaluate_expression(expr_demorgan, state), "FALSE")
        self.assertEqual(evaluate_expression(expr_simplified, state), "FALSE")

        state2 = {"VAR_P": "TRUE", "VAR_Q": "TRUE"}
        self.assertEqual(evaluate_expression(expr_demorgan, state2), "TRUE")
        self.assertEqual(evaluate_expression(expr_simplified, state2), "TRUE")

    def test_evaluate_expression_missing_variable_raises_execution_error(self):
        with self.assertRaises(Exception) as context:
            evaluate_expression("VAR_Z", {})
        self.assertIn("Variable VAR_Z referenced before assignment", str(context.exception))

        with self.assertRaises(Exception) as context:
            evaluate_expression(["AND", "VAR_Z", "TRUE"], {})
        self.assertIn("Variable VAR_Z referenced before assignment", str(context.exception))

    def test_evaluate_expression_deeply_nested_ast(self):
        nested = "TRUE"
        for _ in range(201):
            nested = ["NOT", nested]

        self.assertEqual(evaluate_expression(nested, {}), "FALSE")

    def test_verify_equivalence_variable_order_sorted(self):
        original_expr = ["AND", "VAR_Q", "VAR_P"]
        optimized_expr = ["AND", "VAR_P", "VAR_Q"]

        result = verify_equivalence(original_expr, optimized_expr)

        self.assertEqual(result["variables_tested"], ["VAR_P", "VAR_Q"])
        self.assertEqual(result["ast_original_column"], result["ast_optimized_column"])
        self.assertEqual(result["is_equivalent"], "TRUE")

    def test_verify_equivalence_complex_mock(self):
        original_expr = [
            "IMPLIES",
            ["AND", "VAR_P", ["OR", "VAR_Q", "TRUE"]],
            ["OR", ["NOT", "VAR_P"], "VAR_Q"],
        ]
        optimized_expr = ["OR", ["NOT", "VAR_P"], "VAR_Q"]

        result = verify_equivalence(original_expr, optimized_expr)

        self.assertEqual(result["is_equivalent"], "TRUE")
        self.assertEqual(result["ast_original_column"], result["ast_optimized_column"])
        self.assertEqual(result["variables_tested"], ["VAR_P", "VAR_Q"])
        self.assertEqual(len(result["ast_original_column"]), 4)

    def test_run_executor_full_flow(self):
        mock_phase_3_rows = [
            {
                "line": 1,
                "ast": ["LET", "VAR_P", "TRUE"],
                "original_ast": ["LET", "VAR_P", "TRUE"],
            },
            {
                "line": 2,
                "ast": ["LET", "VAR_Q", "TRUE"],
                "original_ast": ["LET", "VAR_Q", "TRUE"],
            },
            {
                "line": 3,
                "ast": [
                    "LET",
                    "VAR_R",
                    ["OR", ["NOT", "VAR_P"], "VAR_Q"],
                ],
                "original_ast": [
                    "LET",
                    "VAR_R",
                    [
                        "IMPLIES",
                        ["AND", "VAR_P", ["OR", "VAR_Q", "TRUE"]],
                        ["OR", ["NOT", "VAR_P"], "VAR_Q"],
                    ],
                ],
            },
            {
                "line": 4,
                "ast": ["IF", ["OR", "VAR_P", "VAR_Q"], ["PRINT", "VAR_P"]],
                "original_ast": ["IF", ["OR", "VAR_P", "VAR_Q"], ["PRINT", "VAR_P"]],
            },
        ]

        result = run_executor(mock_phase_3_rows)

        self.assertIsInstance(result, dict)
        self.assertIn("verifications", result)
        self.assertIn("final_state_dictionary", result)
        self.assertIn("printed_output", result)
        self.assertEqual(result["final_state_dictionary"].get("VAR_P"), "TRUE")
        self.assertEqual(result["final_state_dictionary"].get("VAR_Q"), "TRUE")
        self.assertEqual(result["final_state_dictionary"].get("VAR_R"), "TRUE")
        self.assertEqual(result["printed_output"], [{"line": 4, "output": "TRUE"}])
        self.assertEqual(len(result["verifications"]), 4)

        print(json.dumps(result, indent=2))

    def test_run_executor_uninitialized_variable_fails_fast(self):
        mock_phase_3_rows = [
            {
                "line": 1,
                "ast": ["LET", "VAR_P", "TRUE"],
                "original_ast": ["LET", "VAR_P", "TRUE"],
            },
            {
                "line": 2,
                "ast": ["PRINT", "VAR_Q"],
                "original_ast": ["PRINT", "VAR_Q"],
            },
        ]

        result = run_executor(mock_phase_3_rows)

        self.assertIn("error", result)
        self.assertEqual(result["error"], {"phase": "phase_4_execution", "line": 2})
        self.assertEqual(result["final_state_dictionary"], {"VAR_P": "TRUE"})
        self.assertEqual(result["printed_output"], [])
        self.assertEqual(len(result["verifications"]), 1)


if __name__ == "__main__":
    unittest.main()
