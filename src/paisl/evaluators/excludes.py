# SPDX-License-Identifier: MIT
"""The `excludes` evaluator."""

from __future__ import annotations

from . import FAIL, PASS, EvaluationResult


class ExcludesEvaluator:
    """Check that a substring is absent."""

    name = "excludes"

    def evaluate(self, output: str, params: dict) -> EvaluationResult:
        text = params.get("text")

        if not isinstance(text, str):
            return EvaluationResult(
                status=FAIL,
                message="The assertion needs a string parameter 'text'.",
                details={"parameter": "text"},
            )

        found = text in output

        return EvaluationResult(
            status=PASS if not found else FAIL,
            message=(
                f"The output does not contain {text!r}."
                if not found
                else f"The output contains {text!r}."
            ),
            details={"text": text, "found": found},
        )
