import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lexer import normalize_variable_token, run_lexer, tokenize_line


class TestLexer(unittest.TestCase):
    def test_normalize_variable_token_valid(self):
        self.assertEqual(normalize_variable_token("p"), "VAR_P")
        self.assertEqual(normalize_variable_token("x"), "VAR_X")

    def test_normalize_variable_token_invalid(self):
        with self.assertRaises(ValueError):
            normalize_variable_token("P")
        with self.assertRaises(ValueError):
            normalize_variable_token("ab")

    def test_tokenize_line_keywords_literals_operators_symbols_and_vars(self):
        line = "let p = (NOT (q OR F))"
        tokens = tokenize_line(line, 3)
        self.assertEqual(
            tokens,
            [
                "LET",
                "VAR_P",
                "EQ",
                "L_PAREN",
                "NOT",
                "L_PAREN",
                "VAR_Q",
                "OR",
                "FALSE",
                "R_PAREN",
                "R_PAREN",
            ],
        )

    def test_tokenize_line_without_spaces_around_symbols(self):
        line = "if(T AND q)then print p"
        tokens = tokenize_line(line, 1)
        self.assertEqual(
            tokens,
            [
                "IF",
                "L_PAREN",
                "TRUE",
                "AND",
                "VAR_Q",
                "R_PAREN",
                "THEN",
                "PRINT",
                "VAR_P",
            ],
        )

    def test_tokenize_line_invalid_character(self):
        with self.assertRaises(ValueError) as context:
            tokenize_line("let p = T;", 7)
        self.assertIn("line 7", str(context.exception))
        self.assertIn("invalid character", str(context.exception))

    def test_tokenize_line_invalid_word_token(self):
        with self.assertRaises(ValueError) as context:
            tokenize_line("let prop = T", 4)
        self.assertIn("line 4", str(context.exception))
        self.assertIn("invalid token", str(context.exception))

    def test_run_lexer_skips_empty_lines_and_preserves_original_line_numbers(self):
        source_lines = [
            "let p = T",
            "",
            "   ",
            "print p",
        ]

        rows = run_lexer(source_lines)

        self.assertEqual(
            rows,
            [
                {"line": 1, "tokens": ["LET", "VAR_P", "EQ", "TRUE"]},
                {"line": 4, "tokens": ["PRINT", "VAR_P"]},
            ],
        )

    def test_run_lexer_fail_fast_on_first_lexical_error(self):
        source_lines = [
            "let p = T",
            "let qq = F",
            "print p",
        ]

        with self.assertRaises(ValueError) as context:
            run_lexer(source_lines)
        self.assertIn("line 2", str(context.exception))


if __name__ == "__main__":
    unittest.main()
