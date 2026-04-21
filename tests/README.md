# Tests

This folder contains module-level test files for the LogicScript compiler.

## Included Test Files

- `test_lexer.py` — tests for tokenization and lexical validation
- `test_parser.py` — tests for AST generation and syntax validation
- `test_executor.py` — tests for equivalence verification and execution behavior

## Purpose

The tests are used to check that:
- valid LogicScript input is handled correctly
- lexical errors are caught gracefully
- syntax errors are caught gracefully
- execution behavior matches the optimized AST
- output structures remain compatible with the project specification

## Suggested Manual Test Workflow

From the project root directory, run:

```bash
python tests/test_lexer.py
python tests/test_parser.py
python tests/test_executor.py

You should also manually run the compiler on sample input files in example/ to verify full pipeline behavior.
