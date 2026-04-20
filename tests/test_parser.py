import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from parser import ParserSyntaxError, parse_tokens, run_parser


class TestParser(unittest.TestCase):
    def test_valid_let_with_literal(self):
        row = parse_tokens(1, ["LET", "VAR_P", "EQ", "TRUE"])
        self.assertEqual(row, {"line": 1, "ast": ["LET", "VAR_P", "TRUE"]})

    def test_valid_let_with_nested_expression(self):
        tokens = [
            "LET",
            "VAR_R",
            "EQ",
            "L_PAREN",
            "NOT",
            "L_PAREN",
            "L_PAREN",
            "NOT",
            "VAR_P",
            "R_PAREN",
            "AND",
            "VAR_Q",
            "R_PAREN",
            "R_PAREN",
        ]
        row = parse_tokens(2, tokens)
        self.assertEqual(
            row,
            {
                "line": 2,
                "ast": [
                    "LET",
                    "VAR_R",
                    ["NOT", ["AND", ["NOT", "VAR_P"], "VAR_Q"]],
                ],
            },
        )

    def test_valid_print(self):
        row = parse_tokens(3, ["PRINT", "VAR_P"])
        self.assertEqual(row, {"line": 3, "ast": ["PRINT", "VAR_P"]})

    def test_valid_if_then_print(self):
        row = parse_tokens(4, ["IF", "VAR_R", "THEN", "PRINT", "VAR_P"])
        self.assertEqual(row, {"line": 4, "ast": ["IF", "VAR_R", ["PRINT", "VAR_P"]]})

    def test_valid_if_with_nested_if_statement(self):
        tokens = ["IF", "VAR_R", "THEN", "IF", "VAR_P", "THEN", "PRINT", "VAR_Q"]
        row = parse_tokens(5, tokens)
        self.assertEqual(
            row,
            {
                "line": 5,
                "ast": ["IF", "VAR_R", ["IF", "VAR_P", ["PRINT", "VAR_Q"]]],
            },
        )

    def test_syntax_error_missing_then(self):
        with self.assertRaises(ParserSyntaxError) as context:
            parse_tokens(10, ["IF", "VAR_R", "PRINT", "VAR_P"])
        self.assertEqual(context.exception.line, 10)
        self.assertIn("missing THEN", str(context.exception))

    def test_syntax_error_missing_operand(self):
        tokens = ["LET", "VAR_P", "EQ", "L_PAREN", "VAR_Q", "AND", "R_PAREN"]
        with self.assertRaises(ParserSyntaxError) as context:
            parse_tokens(11, tokens)
        self.assertEqual(context.exception.line, 11)
        self.assertIn("Invalid expression token", str(context.exception))

    def test_syntax_error_mismatched_parentheses(self):
        tokens = ["LET", "VAR_P", "EQ", "L_PAREN", "NOT", "VAR_Q"]
        with self.assertRaises(ParserSyntaxError) as context:
            parse_tokens(12, tokens)
        self.assertEqual(context.exception.line, 12)
        self.assertIn("Missing closing R_PAREN", str(context.exception))

    def test_syntax_error_trailing_tokens(self):
        with self.assertRaises(ParserSyntaxError) as context:
            parse_tokens(13, ["PRINT", "VAR_P", "TRUE"])
        self.assertEqual(context.exception.line, 13)
        self.assertIn("Trailing tokens", str(context.exception))

    def test_run_parser_fail_fast_and_line_number(self):
        phase_1_rows = [
            {"line": 1, "tokens": ["LET", "VAR_P", "EQ", "TRUE"]},
            {"line": 2, "tokens": ["IF", "VAR_P", "PRINT", "VAR_Q"]},
            {"line": 3, "tokens": ["PRINT", "VAR_P"]},
        ]
        with self.assertRaises(ParserSyntaxError) as context:
            run_parser(phase_1_rows)
        self.assertEqual(context.exception.line, 2)


if __name__ == "__main__":
    unittest.main()
