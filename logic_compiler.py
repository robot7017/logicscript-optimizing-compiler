#!/usr/bin/env python3
"""Command-line entry point for the LogicScript compiler pipeline."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import executor
import lexer
import optimizer
import parser


def build_initial_trace() -> dict[str, Any]:
    """Return the stable top-level JSON shape used by the project specification."""
    return {
        "phase_1_lexer": [],
        "phase_2_parser": [],
        "phase_3_optimizer": [],
        "phase_4_execution": {
            "verifications": [],
            "final_state_dictionary": {},
            "printed_output": [],
        },
    }


def _extract_line_number(error_text: str) -> int:
    """Best-effort line-number extraction from phase exception messages."""
    match = re.search(r"line\s+(\d+)", error_text)
    if match:
        return int(match.group(1))
    return 0


def _run_phase_1(source_lines: list[str]) -> tuple[list[dict[str, object]], dict[str, object] | None]:
    rows: list[dict[str, object]] = []

    for line_number, source_line in enumerate(source_lines, start=1):
        if not source_line.strip():
            continue
        try:
            tokens = lexer.tokenize_line(source_line, line_number)
        except ValueError as exc:
            return rows, {"phase": "phase_1_lexer", "line": _extract_line_number(str(exc))}
        rows.append({"line": line_number, "tokens": tokens})

    return rows, None


def _run_phase_2(
    phase_1_rows: list[dict[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object] | None]:
    rows: list[dict[str, object]] = []

    for row in phase_1_rows:
        line_number = int(row["line"])
        tokens = list(row["tokens"])
        try:
            rows.append(parser.parse_tokens(line_number, tokens))
        except parser.ParserSyntaxError as exc:
            return rows, {"phase": "phase_2_parser", "line": exc.line}

    return rows, None


def _clean_phase_3_rows(phase_3_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    cleaned_rows: list[dict[str, object]] = []
    for row in phase_3_rows:
        cleaned_rows.append({k: v for k, v in row.items() if k != "original_ast"})
    return cleaned_rows


def main(argv: list[str] | None = None) -> int:
    """Validate CLI args, run phases, and write the compiler trace JSON."""
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 2:
        print("Usage: python logic_compiler.py <input_file> <output_file>")
        return 1

    input_path = Path(argv[0])
    output_path = Path(argv[1])

    try:
        source_text = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Failed to read input file: {exc}", file=sys.stderr)
        return 1

    source_lines = source_text.splitlines()
    pipeline_results_dict = build_initial_trace()

    phase_1_rows, phase_1_error = _run_phase_1(source_lines)
    pipeline_results_dict["phase_1_lexer"] = phase_1_rows

    if phase_1_error is not None:
        pipeline_results_dict["error"] = phase_1_error
    else:
        phase_2_rows, phase_2_error = _run_phase_2(phase_1_rows)
        pipeline_results_dict["phase_2_parser"] = phase_2_rows

        if phase_2_error is not None:
            pipeline_results_dict["error"] = phase_2_error
        else:
            phase_3_rows = optimizer.run_optimizer(phase_2_rows)
            pipeline_results_dict["phase_3_optimizer"] = _clean_phase_3_rows(phase_3_rows)

            executor_results = executor.run_executor(phase_3_rows)
            if "error" in executor_results:
                pipeline_results_dict["error"] = executor_results.pop("error")
            pipeline_results_dict["phase_4_execution"] = executor_results

    try:
        output_path.write_text(
            json.dumps(pipeline_results_dict, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"Failed to write output file: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
