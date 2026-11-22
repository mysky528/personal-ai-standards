# SPDX-License-Identifier: MIT
"""The `json_path` evaluator.

The path syntax is deliberately narrow. It addresses object keys and
numeric array indices, separated by dots. It is not JSONPath and it
does not support filters, wildcards, or recursive descent.
"""

from __future__ import annotations

import json

from . import ERROR, FAIL, PASS, EvaluationResult

MAX_DEPTH = 32


class JsonPathEvaluator:
    """Check a value inside a JSON output."""

    name = "json_path"

    def evaluate(self, output: str, params: dict) -> EvaluationResult:
        path = params.get("path")

        if not isinstance(path, str) or not path:
            return EvaluationResult(
                status=FAIL,
                message="The assertion needs a string parameter 'path'.",
                details={"parameter": "path"},
            )

        try:
            document = json.loads(output)
        except json.JSONDecodeError as exc:
            return EvaluationResult(
                status=ERROR,
                message=f"The output is not valid JSON: {exc}",
                details={"parameter": "path"},
            )

        value, missing = self._resolve(document, path)

        if missing:
            return EvaluationResult(
                status=FAIL,
                message=f"The path {path!r} is not present in the output.",
                details={"path": path, "found": False},
            )

        if "equals" in params:
            expected = params["equals"]
            matched = value == expected

            return EvaluationResult(
                status=PASS if matched else FAIL,
                message=(
                    f"The value at {path!r} equals the expected value."
                    if matched
                    else f"The value at {path!r} differs from the expected value."
                ),
                details={
                    "path": path,
                    "found": True,
                    "matched": matched,
                    "expected": expected,
                    "actual": value,
                },
            )

        return EvaluationResult(
            status=PASS,
            message=f"The path {path!r} is present in the output.",
            details={"path": path, "found": True},
        )

    def _resolve(self, document, path: str):
        """Walk the path and return the value, or report it missing."""
        current = document

        parts = path.split(".")

        if len(parts) > MAX_DEPTH:
            return None, True

        for part in parts:
            if isinstance(current, dict):
                if part not in current:
                    return None, True
                current = current[part]
            elif isinstance(current, list):
                if not part.isdigit():
                    return None, True
                index = int(part)

                if index >= len(current):
                    return None, True
                current = current[index]
            else:
                return None, True

        return current, False
