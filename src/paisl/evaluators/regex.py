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

# The bound that applies when no timer is available.
FALLBACK_INPUT_LENGTH = 8192

# Constructs that make the backtracking engine work without end.
# A quantified group whose body carries a quantifier, and a
# backreference, are the shapes that cost the most.
DANGEROUS_PATTERNS = (
    r"\([^)]*[+*]\)[+*]",
    r"\([^)]*\{[0-9,]+\}\)[+*]",
    r"\([^)]*\|[^)]*\)[+*]",
    r"\\\d",
)


class RegexTimeout(Exception):
    """Raised when a match takes longer than the allowed time."""


def timeout_available() -> bool:
    """Report whether a match can be given a time limit here.

    A timer needs SIGALRM and the main thread. Without one, the
    evaluator has to refuse the dangerous shapes instead.
    """
    return (
        hasattr(signal, "SIGALRM")
        and hasattr(signal, "setitimer")
        and threading.current_thread() is threading.main_thread()
    )


def is_dangerous(pattern: str) -> str | None:
    """Return why a pattern may match without end, or None."""
    for dangerous in DANGEROUS_PATTERNS:
        if re.search(dangerous, pattern):
            return "the pattern uses a construct that can match without end"

    return None


def _timeout_handler(signum, frame):
    raise RegexTimeout("The regular expression took too long.")


def _bounded_search(pattern: str, text: str):
    """Search with a time limit where the platform allows one."""
    if not timeout_available():
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

        # The dangerous shapes are refused everywhere. A timer only
        # adds a time limit on top, where the platform offers one.
        danger = is_dangerous(pattern)

        if danger is not None:
            return EvaluationResult(
                status=ERROR,
                message=danger,
                details={"parameter": "pattern"},
            )

        limit = MAX_INPUT_LENGTH if timeout_available() else FALLBACK_INPUT_LENGTH
        text = output[:limit]

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
                "truncated": len(output) > limit,
            },
        )
