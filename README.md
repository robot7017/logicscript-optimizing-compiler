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
**Convert** each source line into a list of standardized tokens.

Examples:
- `let` -> `LET`
- `T` -> `TRUE`
- `p` -> `VAR_P`
- `(` -> `L_PAREN`
- `)` -> `R_PAREN`

### Phase 2: Parser
**Validate** token order and **convert** token rows into nested prefix AST rows.

Examples:
- `(NOT p)` -> `["NOT", "VAR_P"]`
- `(p AND q)` -> `["AND", "VAR_P", "VAR_Q"]`
- `let x = (p OR T)` -> `["LET", "VAR_X", ["OR", "VAR_P", "TRUE"]]`

### Phase 3: Optimizer
**Recursively simplify** logical expressions using allowed propositional logic laws.

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
1. **Generate** a truth-table-based equivalence check between the original AST and optimized AST.
2. **Execute** the optimized statements.
3. **Update** the final state dictionary.
4. **Record** printed outputs.

## Repository Structure

- `logic_compiler.py` — main entry point and pipeline orchestration
- `lexer.py` — Phase 1 lexical analysis
- `parser.py` — Phase 2 syntax validation and AST generation
- `optimizer.py` — Phase 3 logical optimization
- `executor.py` — Phase 4 equivalence verification and execution
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
