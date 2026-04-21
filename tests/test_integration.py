import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestIntegration(unittest.TestCase):
    """End-to-End Integration Tests for LogicScript Compiler."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.project_root = Path(__file__).resolve().parent.parent
        cls.example_dir = cls.project_root / "example"
        cls.logic_compiler = cls.project_root / "logic_compiler.py"

    def _run_compiler(self, input_file: Path) -> dict:
        """Run the compiler on an input file and return the JSON trace."""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp:
            output_file = Path(tmp.name)

        try:
            result = subprocess.run(
                [sys.executable, str(self.logic_compiler), str(input_file), str(output_file)],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # The program should always exit successfully (return code 0)
            self.assertEqual(result.returncode, 0,
                           f"Compiler exited with code {result.returncode}\n"
                           f"stdout: {result.stdout}\nstderr: {result.stderr}")

            # Read the JSON output
            with open(output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        finally:
            # Clean up temporary file
            if output_file.exists():
                output_file.unlink()

    def _get_valid_test_files(self) -> list[Path]:
        """Get all program_valid_*.txt files from example directory."""
        return sorted(self.example_dir.glob("program_valid_*.txt"))

    def _get_error_test_files(self) -> list[Path]:
        """Get all program_error_*.txt files from example directory."""
        return sorted(self.example_dir.glob("program_error_*.txt"))

    # ============ Tests for Valid Programs ============

    def test_valid_programs_produce_trace_with_four_phases(self):
        """Test that all valid programs produce JSON with four required top-level keys."""
        valid_files = self._get_valid_test_files()
        self.assertGreater(len(valid_files), 0, "No valid program files found")

        for input_file in valid_files:
            with self.subTest(file=input_file.name):
                trace = self._run_compiler(input_file)

                # Assert all four phase keys exist
                self.assertIn("phase_1_lexer", trace,
                             f"Missing 'phase_1_lexer' in {input_file.name}")
                self.assertIn("phase_2_parser", trace,
                             f"Missing 'phase_2_parser' in {input_file.name}")
                self.assertIn("phase_3_optimizer", trace,
                             f"Missing 'phase_3_optimizer' in {input_file.name}")
                self.assertIn("phase_4_execution", trace,
                             f"Missing 'phase_4_execution' in {input_file.name}")

    def test_valid_programs_have_no_error_key(self):
        """Test that valid programs do not produce an 'error' key."""
        valid_files = self._get_valid_test_files()

        for input_file in valid_files:
            with self.subTest(file=input_file.name):
                trace = self._run_compiler(input_file)
                self.assertNotIn("error", trace,
                               f"Valid program '{input_file.name}' should not have 'error' key, "
                               f"but got: {trace.get('error')}")

    def test_phase_3_optimizer_rows_have_no_original_ast(self):
        """
        Test that phase_3_optimizer output does not contain 'original_ast' keys.
        
        This verifies that the main program correctly cleaned internal data
        per the internal contract with Phase 4.
        """
        valid_files = self._get_valid_test_files()

        for input_file in valid_files:
            with self.subTest(file=input_file.name):
                trace = self._run_compiler(input_file)
                optimizer_rows = trace["phase_3_optimizer"]

                # Each row should have 'line' and 'ast', but NOT 'original_ast'
                for row_index, row in enumerate(optimizer_rows):
                    self.assertIn("line", row,
                                f"Row {row_index} in {input_file.name} missing 'line' key")
                    self.assertIn("ast", row,
                                f"Row {row_index} in {input_file.name} missing 'ast' key")
                    self.assertNotIn("original_ast", row,
                                   f"Row {row_index} in {input_file.name} should not have 'original_ast' key "
                                   f"(it should have been cleaned by _clean_phase_3_rows)")

    def test_valid_program_spec(self):
        """Test the specification example program."""
        input_file = self.example_dir / "program_valid_spec.txt"
        if input_file.exists():
            trace = self._run_compiler(input_file)
            self.assertNotIn("error", trace)
            self.assertIsInstance(trace["phase_1_lexer"], list)
            self.assertIsInstance(trace["phase_2_parser"], list)
            self.assertIsInstance(trace["phase_3_optimizer"], list)

    def test_valid_program_implies(self):
        """Test a program with IMPLIES operator."""
        input_file = self.example_dir / "program_valid_implies.txt"
        if input_file.exists():
            trace = self._run_compiler(input_file)
            self.assertNotIn("error", trace)

    def test_valid_program_nested_if(self):
        """Test a program with nested IF statements."""
        input_file = self.example_dir / "program_valid_nested_if.txt"
        if input_file.exists():
            trace = self._run_compiler(input_file)
            self.assertNotIn("error", trace)

    def test_valid_program_constant_folding(self):
        """Test a program that triggers constant folding optimization."""
        input_file = self.example_dir / "program_valid_constant_folding.txt"
        self.assertTrue(input_file.exists(), f"Test file {input_file} not found")
        trace = self._run_compiler(input_file)

        # Should complete without error
        self.assertNotIn("error", trace)
        # Optimizer should have optimized the expression
        self.assertIsInstance(trace["phase_3_optimizer"], list)
        self.assertGreater(len(trace["phase_3_optimizer"]), 0)

    # ============ Tests for Error Programs ============

    def test_error_programs_produce_error_key(self):
        """Test that all error programs produce JSON with an 'error' key."""
        error_files = self._get_error_test_files()
        self.assertGreater(len(error_files), 0, "No error program files found")

        for input_file in error_files:
            with self.subTest(file=input_file.name):
                trace = self._run_compiler(input_file)
                self.assertIn("error", trace,
                            f"Error program '{input_file.name}' should have 'error' key")

    def test_error_programs_complete_gracefully(self):
        """
        Test that error programs complete gracefully without raising exceptions.
        
        This verifies that the compiler catches and reports errors in JSON
        rather than crashing.
        """
        error_files = self._get_error_test_files()

        for input_file in error_files:
            with self.subTest(file=input_file.name):
                # Should not raise any exception
                trace = self._run_compiler(input_file)
                # Should have error information
                self.assertIsInstance(trace["error"], dict)
                self.assertIn("phase", trace["error"],
                            f"Error in {input_file.name} should have 'phase' key")

    def test_error_program_lexical_invalid_token(self):
        """Test lexical error from invalid token (multi-letter variable name)."""
        input_file = self.example_dir / "program_error_lexical_invalid_token.txt"
        self.assertTrue(input_file.exists(), f"Test file {input_file} not found")

        trace = self._run_compiler(input_file)
        self.assertIn("error", trace)
        self.assertEqual(trace["error"]["phase"], "phase_1_lexer",
                        "Should be a lexical error in phase_1_lexer")

    def test_error_program_syntax_mismatched_paren(self):
        """Test syntax error from mismatched parentheses."""
        input_file = self.example_dir / "program_error_syntax_mismatched_paren.txt"
        self.assertTrue(input_file.exists(), f"Test file {input_file} not found")

        trace = self._run_compiler(input_file)
        self.assertIn("error", trace)
        self.assertEqual(trace["error"]["phase"], "phase_2_parser",
                        "Should be a syntax error in phase_2_parser")

    def test_error_program_missing_then(self):
        """Test syntax error from missing THEN keyword."""
        input_file = self.example_dir / "program_error_syntax_missing_then.txt"
        if input_file.exists():
            trace = self._run_compiler(input_file)
            self.assertIn("error", trace)

    def test_error_program_uninitialized_variable(self):
        """Test execution error from uninitialized variable access."""
        input_file = self.example_dir / "program_error_execution_uninitialized.txt"
        if input_file.exists():
            trace = self._run_compiler(input_file)
            self.assertIn("error", trace)

    # ============ Boundary & Consistency Tests ============

    def test_phase_1_lexer_produces_tokens(self):
        """Test that phase_1_lexer produces well-formed token lists."""
        valid_files = self._get_valid_test_files()

        for input_file in valid_files:
            with self.subTest(file=input_file.name):
                trace = self._run_compiler(input_file)
                lexer_rows = trace["phase_1_lexer"]

                for row in lexer_rows:
                    self.assertIn("line", row)
                    self.assertIn("tokens", row)
                    self.assertIsInstance(row["tokens"], list)
                    self.assertGreater(len(row["tokens"]), 0)

    def test_phase_2_parser_produces_ast(self):
        """Test that phase_2_parser produces well-formed AST lists."""
        valid_files = self._get_valid_test_files()

        for input_file in valid_files:
            with self.subTest(file=input_file.name):
                trace = self._run_compiler(input_file)
                parser_rows = trace["phase_2_parser"]

                for row in parser_rows:
                    self.assertIn("line", row)
                    self.assertIn("ast", row)
                    self.assertIsInstance(row["ast"], list)
                    self.assertGreater(len(row["ast"]), 0)

    def test_phase_3_optimizer_produces_ast(self):
        """Test that phase_3_optimizer produces well-formed AST lists."""
        valid_files = self._get_valid_test_files()

        for input_file in valid_files:
            with self.subTest(file=input_file.name):
                trace = self._run_compiler(input_file)
                optimizer_rows = trace["phase_3_optimizer"]

                for row in optimizer_rows:
                    self.assertIn("line", row)
                    self.assertIn("ast", row)
                    # Should only have these two keys (no original_ast)
                    self.assertEqual(set(row.keys()), {"line", "ast"},
                                   f"Optimizer row should only have 'line' and 'ast' keys, "
                                   f"got {set(row.keys())}")

    def test_line_numbers_are_positive_integers(self):
        """Test that all line numbers in phases are positive integers."""
        valid_files = self._get_valid_test_files()

        for input_file in valid_files:
            with self.subTest(file=input_file.name):
                trace = self._run_compiler(input_file)

                for phase_key in ["phase_1_lexer", "phase_2_parser", "phase_3_optimizer"]:
                    rows = trace[phase_key]
                    for row in rows:
                        line_num = row["line"]
                        self.assertIsInstance(line_num, int, f"Line number should be int, got {type(line_num)}")
                        self.assertGreater(line_num, 0, f"Line number should be positive, got {line_num}")

    def test_compiler_cli_input_validation(self):
        """Test that compiler CLI validates input arguments."""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp:
            output_file = Path(tmp.name)

        try:
            # Test with missing arguments
            result = subprocess.run(
                [sys.executable, str(self.logic_compiler)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # Should fail with non-zero exit code
            self.assertNotEqual(result.returncode, 0)

            # Test with non-existent input file
            result = subprocess.run(
                [sys.executable, str(self.logic_compiler),
                 "/nonexistent/path/file.txt", str(output_file)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # Should fail with non-zero exit code
            self.assertNotEqual(result.returncode, 0)
        finally:
            if output_file.exists():
                output_file.unlink()


if __name__ == "__main__":
    unittest.main()
