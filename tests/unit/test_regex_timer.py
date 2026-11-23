# SPDX-License-Identifier: MIT
"""The timer of the caller around a match.

The evaluator arms SIGALRM for the length of a match. The timer of
the process belongs to the caller as much as to the evaluator, so
what was armed before the match has to be armed again afterwards.

The tests below stand in for a caller that keeps its own deadline
with SIGALRM. They cover three things:

- the alarm of the caller still fires
- its deadline does not move
- the evaluator leaves no timer of its own behind
"""

from __future__ import annotations

import signal
import time

import pytest

import paisl.evaluators.regex as regex_module
from paisl.evaluators import ERROR, PASS
from paisl.evaluators.regex import MATCH_TIMEOUT_SECONDS, RegexEvaluator


@pytest.fixture
def caller_timer():
    """Arm a timer the way a caller with its own deadline would."""
    fired: list = []

    def handler(signum, frame):
        fired.append(time.monotonic())

    previous = signal.signal(signal.SIGALRM, handler)

    try:
        yield fired
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_the_callers_alarm_still_fires(caller_timer):
    """A caller that armed a timer keeps it.

    The evaluator borrows the timer of the process. It gives the
    handler back, and it gives the time back as well, so the alarm of
    the caller still reaches it.
    """
    signal.setitimer(signal.ITIMER_REAL, 0.5)

    result = RegexEvaluator().evaluate("order-42", {"pattern": r"order-\d+"})

    assert result.status == PASS
    assert signal.getitimer(signal.ITIMER_REAL)[0] > 0, (
        "the timer of the caller was destroyed"
    )

    deadline = time.monotonic() + 1.5

    while not caller_timer and time.monotonic() < deadline:
        time.sleep(0.01)

    assert caller_timer, "the alarm of the caller never fired"


def test_the_callers_deadline_does_not_move(caller_timer):
    """The match does not postpone the deadline of the caller.

    The time that the match took is taken off the time that was left,
    so the alarm reaches the caller at the moment it was going to
    reach it anyway.
    """
    signal.setitimer(signal.ITIMER_REAL, 0.5)

    deadline = time.monotonic() + 0.5

    RegexEvaluator().evaluate("order-42", {"pattern": r"order-\d+"})

    while not caller_timer and time.monotonic() < deadline + 1:
        time.sleep(0.01)

    assert caller_timer, "the alarm of the caller never fired"

    drift = abs(caller_timer[0] - deadline)

    assert drift < 0.25, (
        f"the deadline of the caller moved by {drift:.3f} seconds"
    )


def test_the_callers_handler_is_restored(caller_timer):
    """The handler of the caller is the handler again."""
    signal.setitimer(signal.ITIMER_REAL, 0.5)

    RegexEvaluator().evaluate("order-42", {"pattern": r"order-\d+"})

    assert signal.getsignal(signal.SIGALRM) is not regex_module._timeout_handler


def test_the_evaluator_leaves_no_timer_behind(caller_timer):
    """A caller without a timer gets no timer.

    The evaluator gives back what it found. A caller that had no
    timer armed must not find one afterwards.
    """
    signal.setitimer(signal.ITIMER_REAL, 0)

    RegexEvaluator().evaluate("order-42", {"pattern": r"order-\d+"})

    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)


def test_the_evaluator_still_bounds_its_own_match(caller_timer):
    """The limit of the evaluator holds while a caller has a timer.

    The timer of the caller does not shorten the limit of the
    evaluator, and the limit of the evaluator does not lengthen the
    timer of the caller.
    """
    signal.setitimer(signal.ITIMER_REAL, 30.0)

    start = time.monotonic()
    result = RegexEvaluator().evaluate(
        "a" * 40 + "!", {"pattern": r"(?:a?){40}a{40}"}
    )
    elapsed = time.monotonic() - start

    assert result.status in (PASS, ERROR)
    assert elapsed < MATCH_TIMEOUT_SECONDS * 5, (
        "the match was not bounded"
    )

    remaining = signal.getitimer(signal.ITIMER_REAL)[0]

    assert 0 < remaining <= 30.0, (
        "the timer of the caller was not given back"
    )


def test_a_deadline_that_passed_during_the_match_fires_at_once(
    caller_timer,
):
    """A deadline that passed while the match ran is not lost.

    The match took longer than the time that was left. The alarm has
    to reach the caller as soon as it may reach it.
    """
    signal.setitimer(signal.ITIMER_REAL, 0.05)

    RegexEvaluator().evaluate("order-42", {"pattern": r"order-\d+"})

    deadline = time.monotonic() + 1.5

    while not caller_timer and time.monotonic() < deadline:
        time.sleep(0.01)

    assert caller_timer, "the alarm of the caller never fired"
