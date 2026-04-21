# LogicScript Optimizing Compiler

This repository contains our implementation of a 4-phase LogicScript compiler for the UFUG2106 course project.

## Table of Contents
- [Project Goal](#project-goal)
- [Pipeline Overview](#pipeline-overview)
- [Repository Structure](#repository-structure)
- [Requirements](#requirements)
- [Command-Line Usage](#command-line-usage)
- [Input Format](#input-format)
- [Output Format](#output-format)
- [Example Test Files](#example-test-files)
- [How to Run Example Cases](#how-to-run-example-cases)
- [Testing](#testing)
- [Development Notes](#development-notes)
- [Final Submission Packaging](#final-submission-packaging)
- [Constraints and Design Choices](#constraints-and-design-choices)
- [Authors / Collaboration](#authors--collaboration)

## Project Goal

The compiler reads a multi-line LogicScript source file, validates its structure, simplifies logical expressions, verifies that optimization preserves meaning, executes the optimized program, and exports a structured JSON trace.

The pipeline is based on:
- Propositional Logic
- Recursive Definitions
- State Environments using mappings / relations

## Pipeline Overview

### Phase 1: Lexer
Convert each source line into a list of standardized tokens.

Examples:
- `let` -> `LET`
- `T` -> `TRUE`
- `p` -> `VAR_P`
- `(` -> `L_PAREN`
- `)` -> `R_PAREN`

### Phase 2: Parser
Validate token order and convert token rows into nested prefix AST rows.

Examples:
- `(NOT p)` -> `["NOT", "VAR_P"]`
- `(p AND q)` -> `["AND", "VAR_P", "VAR_Q"]`
- `let x = (p OR T)` -> `["LET", "VAR_X", ["OR", "VAR_P", "TRUE"]]`

### Phase 3: Optimizer
Recursively simplify logical expressions using allowed propositional logic laws.

Implemented simplifications include:
- Constant folding
- Double negation
- De Morgan’s laws
- AND / OR simplifications
- IMPLIES simplifications

Examples:
- `A OR TRUE` -> `TRUE`
- `A AND FALSE` -> `FALSE`
- `NOT (NOT A)` -> `A`
- `NOT (A AND B)` -> `(NOT A) OR (NOT B)`

### Phase 4: Verification + Execution
For each simplified expression:
1. Generate a truth-table-based equivalence check between the original AST and optimized AST
2. Execute the optimized statements
3. Update the final state dictionary
4. Record printed outputs

## Repository Structure

- `logic_compiler.py` — main entry point and pipeline orchestration
- `lexer.py` — Phase 1 lexical analysis
- `parser.py` — Phase 2 syntax validation and AST generation
- `optimizer.py` — Phase 3 logical optimization
- `executor.py` — Phase 4 equivalence verification and execution
- `logic_compiler_single.py` — self-contained single-file submission version
- `SPEC.md` — project contract for tokens, grammar, AST shape, CLI, JSON format, and error handling
- `example/` — sample valid and invalid LogicScript programs
- `tests/` — test files for lexer, parser, and executor
- `docs/` — project handout / reference materials

## Requirements

- Python 3.10+ recommended
- Python standard library only
- No external parsing libraries
- No external AST libraries

## Command-Line Usage

Run the compiler with:

```bash
python logic_compiler.py <input_file> <output_file>
```

Example:

```bash
python logic_compiler.py example/program_valid.txt compiler_trace.json
```

## Input Format

The input file must contain one LogicScript statement per non-empty line.

Supported statements:
- `let <variable> = <expression>`
- `if <expression> then <statement>`
- `print <variable>`

Supported expressions:
- Base cases:
  - `T`
  - `F`
  - single lowercase variable such as `p`
- Recursive cases:
  - `(NOT E)`
  - `(E1 AND E2)`
  - `(E1 OR E2)`
  - `(E1 IMPLIES E2)`

## Output Format

The compiler writes a JSON trace file containing:

- `phase_1_lexer`
- `phase_2_parser`
- `phase_3_optimizer`
- `phase_4_execution`
- `error` (if compilation halts early)

All boolean values in JSON output are uppercase strings:
- `"TRUE"`
- `"FALSE"`

## Example Test Files

### Valid programs
- `example/program_valid.txt`
- `example/program_valid_implies.txt`

### Error cases
- `example/program_error_lexical_invalid_char.txt`
- `example/program_error_missing_operand.txt`
- `example/program_error_syntax_missing_then.txt`
- `example/program_error_execution_uninitialized.txt`

## How to Run Example Cases

```bash
# 1. Successful compilation
python logic_compiler.py example/program_valid.txt out_valid.json

# 2. Valid implication example
python logic_compiler.py example/program_valid_implies.txt out_implies.json

# 3. Lexical error case
python logic_compiler.py example/program_error_lexical_invalid_char.txt out_lex_error.json

# 4. Syntax error case
python logic_compiler.py example/program_error_missing_operand.txt out_syntax_error.json

# 5. Missing then syntax error case
python logic_compiler.py example/program_error_syntax_missing_then.txt out_missing_then.json

# 6. Execution error case

python logic_compiler.py example/program_error_execution_uninitialized.txt out_exec_error.json
```
## Testing

Unit test files are located in `tests/`:
- `tests/test_lexer.py`
- `tests/test_parser.py`
- `tests/test_executor.py`

If you run tests manually, make sure you are in the project root directory.

Example:
```bash
python tests/test_lexer.py
python tests/test_parser.py
python tests/test_executor.py
```

## Development Notes

This repository is organized in modular development form for readability and collaboration.

## Final Submission Packaging

This repository is kept in modular form for development, debugging, and collaboration. 

For the final course submission that requires a self-contained single Python file, use:

- `logic_compiler_single.py`
  
The modular files (`lexer.py`, `parser.py`, `optimizer.py`, `executor.py`, and the orchestrating `logic_compiler.py`) are preserved in the repository for readability and testing.

## Constraints and Design Choices

- Token names and AST formats follow `SPEC.md`
- The optimizer preserves statement structure and only simplifies expressions
- Equivalence checking is truth-table-based
- Errors are reported gracefully in JSON rather than crashing with a Python traceback


## Authors / Collaboration

This project was developed collaboratively by our team, with different members focusing on different phases of the compiler pipeline while maintaining shared understanding of the full system.
