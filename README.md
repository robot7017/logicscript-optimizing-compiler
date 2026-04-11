# LogicScript Optimizing Compiler (Course Project)

This repository contains a staged Python implementation of a 4-phase LogicScript compiler for the UFUG2106 project.

## Pipeline Overview

1. Phase 1: Lexer  
   Convert each source line into a list of standardized tokens.

2. Phase 2: Parser  
   Validate source syntax and convert token rows into nested prefix AST rows.

3. Phase 3: Optimizer  
   Recursively simplify logical expressions using allowed propositional logic laws.

4. Phase 4: Verification + Execution  
   Verify equivalence between original and optimized expressions, then execute and export a JSON trace.

## Command-Line Usage

```bash
python logic_compiler.py <input_file> <output_file>
```

Example:

```bash
python logic_compiler.py program.txt compiler_trace.json
```

## Input / Output

### Input

A multi-line LogicScript source file. Each non-empty line should be a valid LogicScript statement.

### Output

A JSON trace file containing:
- `phase_1_lexer`
- `phase_2_parser`
- `phase_3_optimizer`
- `phase_4_execution`
- `error` (if compilation halts early)

Boolean values in trace output must be uppercase strings: `"TRUE"` / `"FALSE"`.

## Minimal Example

Input (`program.txt`):

```text
let p = T
print p
```

Expected high-level behavior:
- Phase 1 tokenizes both lines.
- Phase 2 parses them into AST rows.
- Phase 4 records printed output `"TRUE"` in the JSON trace.

## Project Layout

- `logic_compiler.py` - main entry point, command-line handling, and pipeline orchestration
- `lexer.py` - Phase 1 lexical analysis
- `parser.py` - Phase 2 syntax validation and AST generation
- `optimizer.py` - Phase 3 expression optimization
- `executor.py` - Phase 4 equivalence verification and execution
- `SPEC.md` - stable token, grammar, AST, CLI, JSON, and error-handling contract
- `tests/` - test inputs and validation cases

## Development Status

Implemented:
- repository skeleton
- command-line/file I/O skeleton in `logic_compiler.py`
- stable interface contract in `SPEC.md`

In progress:
- Phase 1 lexer
- Phase 2 parser

Pending:
- Phase 3 optimizer
- Phase 4 verification and execution
- complete test suite

## Testing

The `tests/` directory is reserved for:
- valid LogicScript programs
- lexical error cases
- syntax error cases
- optimization / execution checks

## Constraints

- Python standard library only
- No external parsing or AST libraries
- Keep token names and AST formats stable and consistent with `SPEC.md`
