# SPDX-License-Identifier: MIT
"""The deterministic evaluators.

Only the evaluators in this package may run. A case cannot select
arbitrary code: the evaluation contract allowlists the names, and
this registry is the only place that resolves them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

EVALUATOR_VERSION = "0.2.0"

PASS = "pass"
FAIL = "fail"
SKIP = "skip"
ERROR = "error"

STATUSES = (PASS, FAIL, SKIP, ERROR)


@dataclass(frozen=True)
class EvaluationResult:
    """The outcome of one assertion."""

    status: str
    message: str
    details: dict = field(default_factory=dict)


class Evaluator(Protocol):
    """The interface every evaluator implements."""

    name: str

    def evaluate(
        self,
        output: str,
        params: dict,
    ) -> EvaluationResult:
        """Evaluate one assertion against an output."""


_REGISTRY: dict = {}


def register(evaluator: Evaluator) -> Evaluator:
    """Add an evaluator to the allowlist."""
    _REGISTRY[evaluator.name] = evaluator
    return evaluator


def get_evaluator(name: str) -> Evaluator | None:
    """Return an evaluator by name, or None when it is not allowed."""
    return _REGISTRY.get(name)


def allowed_names() -> list:
    """Return the names of the allowed evaluators."""
    return sorted(_REGISTRY)


from . import contains, excludes, json_path, regex  # noqa: E402

register(contains.ContainsEvaluator())
register(excludes.ExcludesEvaluator())
register(json_path.JsonPathEvaluator())
register(regex.RegexEvaluator())
