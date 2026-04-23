# LogicScript Optimizing Compiler (Submission Prep)

This branch (`submission-prep`) packages the project as a **single-file compiler** for final submission.

## What This Branch Contains

- `logic_compiler.py`: complete end-to-end implementation of all 4 phases in one file
- `example/`: sample input programs (valid and error cases)
- `README.md`: usage and submission-oriented documentation

If you are looking for the modular version (`lexer.py`, `parser.py`, `optimizer.py`, `executor.py`), use the main development branch instead.

## Compiler Pipeline

The single compiler file implements the full pipeline:

1. Phase 1 Lexer: source text -> token rows
2. Phase 2 Parser: token rows -> statement AST rows
3. Phase 3 Optimizer: AST simplification
4. Phase 4 Verification + Execution: equivalence checks and runtime output

## Requirements

- Python 3.10 or newer
- Standard library only (no third-party dependencies)

## Command-Line Usage

```bash
python logic_compiler.py <input_file> <output_file>
```

Example:

```bash
python logic_compiler.py example/program_valid_spec.txt compiler_trace.json
```

## Input Language Summary

Statements:

- `let <variable> = <expression>`
- `print <variable>`
- `if <expression> then <statement>`

Expressions:

- Base: `T`, `F`, single variable (`p`, `q`, ...)
- Recursive (parentheses required):
  - `(NOT E)`
  - `(E1 AND E2)`
  - `(E1 OR E2)`
  - `(E1 IMPLIES E2)`

## Output JSON Structure

The compiler writes a trace with these top-level keys:

- `phase_1_lexer`
- `phase_2_parser`
- `phase_3_optimizer`
- `phase_4_execution`
- `error` (only when compilation halts early)

Boolean values are serialized as uppercase strings: `"TRUE"` and `"FALSE"`.

## Error Handling Behavior

The compiler fails fast on the first error and still writes a valid JSON output:

- preserves completed phases
- stops later phases
- reports root-level error:

```json
{
  "error": {
    "phase": "phase_2_parser",
    "line": 2
  }
}
```

## Example Inputs

`example/` includes both valid and invalid programs:

- Valid:
  - `program_valid.txt`
  - `program_valid_spec.txt`
  - `program_valid_implies.txt`
  - `program_valid_nested_if.txt`
- Error:
  - `program_error_lexical_invalid_char.txt`
  - `program_error_missing_operand.txt`
  - `program_error_syntax_missing_then.txt`
  - `program_error_execution_uninitialized.txt`

## Quick Checks

Run a valid case:

```bash
python logic_compiler.py example/program_valid.txt out_valid.json
```

Run an error case:

```bash
python logic_compiler.py example/program_error_missing_operand.txt out_error.json
```

## Notes

- This README is intentionally aligned with the **single-file submission layout** in this branch.
- Keep token names, AST formats, and output schema consistent with the project specification used by your grader.
