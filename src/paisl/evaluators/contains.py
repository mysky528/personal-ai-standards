# SPDX-License-Identifier: MIT
"""The `contains` evaluator."""

from __future__ import annotations

from . import FAIL, PASS, EvaluationResult


class ContainsEvaluator:
    """Check for an exact substring."""

    name = "contains"

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
            status=PASS if found else FAIL,
            message=(
                f"The output contains {text!r}."
                if found
                else f"The output does not contain {text!r}."
            ),
            details={"text": text, "found": found},
        )
