# SPDX-License-Identifier: MIT
"""The `regex` evaluator.

A regular expression can consume an unbounded amount of time, so the
evaluator restricts what it accepts and bounds how long a match may
run.
"""

from __future__ import annotations

import re
import signal
import threading

from . import ERROR, FAIL, PASS, EvaluationResult

# The limits keep a single assertion from stalling a run.
MAX_PATTERN_LENGTH = 512
MAX_INPUT_LENGTH = 65536
MATCH_TIMEOUT_SECONDS = 1.0

# Constructs that make the backtracking engine work without end.
DANGEROUS_PATTERNS = (
    r"\([^)]*[+*]\)[+*]",
    r"\([^)]*\{[0-9,]+\}\)[+*]",
    r"\([^)]*\|[^)]*\)[+*]",
)


class RegexTimeout(Exception):
    """Raised when a match takes longer than the allowed time."""


def _timeout_handler(signum, frame):
    raise RegexTimeout("The regular expression took too long.")


def _bounded_search(pattern: str, text: str):
    """Search with a time limit where the platform allows one."""
    can_signal = (
        hasattr(signal, "SIGALRM")
        and hasattr(signal, "setitimer")
        and threading.current_thread() is threading.main_thread()
    )

    if not can_signal:
        return re.search(pattern, text)

    previous = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.setitimer(signal.ITIMER_REAL, MATCH_TIMEOUT_SECONDS)

    try:
        return re.search(pattern, text)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


class RegexEvaluator:
    """Check a regular expression against the output."""

    name = "regex"

    def evaluate(self, output: str, params: dict) -> EvaluationResult:
        pattern = params.get("pattern")

        if not isinstance(pattern, str) or not pattern:
            return EvaluationResult(
                status=FAIL,
                message="The assertion needs a string parameter 'pattern'.",
                details={"parameter": "pattern"},
            )

        if len(pattern) > MAX_PATTERN_LENGTH:
            return EvaluationResult(
                status=ERROR,
                message=(
                    f"The pattern is longer than {MAX_PATTERN_LENGTH} "
                    f"characters."
                ),
                details={"parameter": "pattern", "limit": MAX_PATTERN_LENGTH},
            )

        for dangerous in DANGEROUS_PATTERNS:
            if re.search(dangerous, pattern):
                return EvaluationResult(
                    status=ERROR,
                    message=(
                        "The pattern uses a construct that can match "
                        "without end."
                    ),
                    details={"parameter": "pattern"},
                )

        text = output[:MAX_INPUT_LENGTH]

        try:
            match = _bounded_search(pattern, text)
        except RegexTimeout:
            return EvaluationResult(
                status=ERROR,
                message=(
                    f"The pattern did not finish within "
                    f"{MATCH_TIMEOUT_SECONDS} seconds."
                ),
                details={"parameter": "pattern"},
            )
        except re.error as exc:
            return EvaluationResult(
                status=ERROR,
                message=f"The pattern is not a valid regular expression: {exc}",
                details={"parameter": "pattern"},
            )

        found = match is not None

        return EvaluationResult(
            status=PASS if found else FAIL,
            message=(
                "The output matches the pattern."
                if found
                else "The output does not match the pattern."
            ),
            details={
                "pattern": pattern,
                "found": found,
                "truncated": len(output) > MAX_INPUT_LENGTH,
            },
        )
