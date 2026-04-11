# LogicScript Compiler Spec Summary

This file summarizes the stable interface contract for the project.

## 1) Exact Token Mapping (Phase 1)

### Keywords
- `let` -> `LET`
- `if` -> `IF`
- `then` -> `THEN`
- `print` -> `PRINT`

### Boolean literals
- `T` -> `TRUE`
- `F` -> `FALSE`

### Operators
- `AND` -> `AND`
- `OR` -> `OR`
- `NOT` -> `NOT`
- `IMPLIES` -> `IMPLIES`

### Symbols
- `=` -> `EQ`
- `(` -> `L_PAREN`
- `)` -> `R_PAREN`

### Variables
- Any single lowercase letter `[a-z]` maps to `VAR_<UPPERCASE_LETTER>`
- Example: `p` -> `VAR_P`, `x` -> `VAR_X`

---

## 1.5) Phase 1 External Contract (Per-Line Rows)

- `phase_1_lexer` is a list of rows.
- Each row is `{"line": <int>, "tokens": <list[str>>}`.
- Tokenization is reported per source line (external contract), even if implementation internals use other traversal strategies.

---

## 2) AST Representation (Phase 2)

AST uses nested prefix lists.

### Expression AST
- Literal / variable:
  - `"TRUE"`
  - `"FALSE"`
  - `"VAR_X"`
- Unary:
  - `["NOT", <expr>]`
- Binary:
  - `["AND", <left_expr>, <right_expr>]`
  - `["OR", <left_expr>, <right_expr>]`
  - `["IMPLIES", <left_expr>, <right_expr>]`

### Statement AST
- Assignment:
  - `["LET", "VAR_X", <expr>]`
- Print:
  - `["PRINT", "VAR_X"]`
- Conditional:
  - `["IF", <expr>, <statement>]`

### Program representation for phase output
- `phase_2_parser` is a list of rows:
  - `{"line": <int>, "ast": <statement_ast>}`

---

## 2.5) Source Grammar Constraints

### Valid expressions

Base cases:
- `T`
- `F`
- single variable, e.g. `p`, `q`, `x`

Recursive cases (parentheses required):
- `(NOT E)`
- `(E1 AND E2)`
- `(E1 OR E2)`
- `(E1 IMPLIES E2)`

Examples that are not valid by this project grammar:
- `NOT p`
- `p AND q`

### Valid statements

- `let <variable> = <expression>`
- `if <expression> then <statement>`
- `print <variable>`

Notes:
- `print` accepts only a variable, not a general expression.
- `if <expression> then <statement>` is recursive, so `<statement>` can itself be `LET`, `PRINT`, or another `IF`.

### AST node convention

- Atomic values are strings: `"TRUE"`, `"FALSE"`, `"VAR_X"`.
- Compound nodes are lists: `["NOT", ...]`, `["AND", ...]`, `["LET", ...]`, `["IF", ...]`, etc.

---

## 2.6) Whitespace / Empty Line Policy

- Leading and trailing whitespace should be ignored.
- Multiple spaces between tokens are allowed.
- Empty lines are skipped, but original source line numbers are preserved for JSON `line` fields.

---

## 3) Command-Line Usage

```bash
python logic_compiler.py <input_file> <output_file>
```

- Read LogicScript source from `<input_file>`
- Write JSON trace to `<output_file>`
- Do not hardcode filenames

---

## 4) JSON Output Structure

Top-level object (stable keys):

```json
{
  "phase_1_lexer": [
    {"line": 1, "tokens": ["LET", "VAR_P", "EQ", "TRUE"]}
  ],
  "phase_2_parser": [
    {"line": 1, "ast": ["LET", "VAR_P", "TRUE"]}
  ],
  "phase_3_optimizer": [
    {"line": 1, "ast": ["LET", "VAR_P", "TRUE"]}
  ],
  "phase_4_execution": {
    "verifications": [
      {
        "line": 3,
        "variables_tested": ["VAR_P", "VAR_Q"],
        "ast_original_column": ["TRUE", "TRUE", "FALSE", "TRUE"],
        "ast_optimized_column": ["TRUE", "TRUE", "FALSE", "TRUE"],
        "is_equivalent": "TRUE"
      }
    ],
    "final_state_dictionary": {
      "VAR_P": "TRUE"
    },
    "printed_output": [
      {"line": 4, "output": "TRUE"}
    ]
  }
}
```

Notes:
- Boolean values in output must be uppercase strings: `"TRUE"` / `"FALSE"`.
- Internal note for Phase 3 / 4:
  - Even though `phase_3_optimizer` reports optimized AST rows in JSON, the implementation must preserve each original expression internally for `phase_4_execution` equivalence verification.

---

## 5) Error Handling Policy

- Fail fast on first lexical or syntax error.
- Do not crash with Python traceback in normal invalid-input scenarios.
- Preserve completed phases in output.
- Add an `error` object when compilation halts:

```json
{
  "error": {
    "phase": "phase_2_parser",
    "line": 2
  }
}
```

- Error row emission policy:
  - If lexical analysis fails on a line, that line must not be emitted as a successful `phase_1_lexer` row.
  - If syntax parsing fails on a line, `phase_1_lexer` may still contain that line's token row, but `phase_2_parser` must not emit a successful AST row for that line.
- If a phase fails, later phases must not run.
