# SPDX-License-Identifier: MIT
"""The time limit of the regular expression evaluator.

A regular expression can consume an unbounded amount of time. The
evaluator has to hold that bound on every platform, not only where a
timer happens to exist.

The tests below cover the three places where the bound can fail:

- a platform without SIGALRM, which is what Windows looks like
- a match outside the main thread, where a timer cannot be armed
- a pattern that backtracks without end
"""

from __future__ import annotations

import re
import signal
import threading
import time

import pytest

from paisl.evaluators import ERROR, FAIL, PASS
from paisl.evaluators.regex import (
    MATCH_TIMEOUT_SECONDS,
    RegexEvaluator,
    RegexTimeout,
    is_dangerous,
    timeout_available,
)


@pytest.fixture
def without_a_timer(monkeypatch):
    """Remove the timer, the way a platform without SIGALRM looks."""
    monkeypatch.delattr(signal, "setitimer", raising=False)
    monkeypatch.delattr(signal, "SIGALRM", raising=False)

    assert not timeout_available()


def test_the_platform_has_a_timer_in_the_main_thread():
    """The usual path arms a timer."""
    assert timeout_available()


def test_a_platform_without_a_timer_is_detected(without_a_timer):
    """The evaluator knows that it cannot arm a timer."""
    assert not timeout_available()


def test_a_match_without_a_timer_is_still_bounded(without_a_timer):
    """Without a timer the match runs where it can be terminated."""
    result = RegexEvaluator().evaluate(
        "order-42", {"pattern": r"order-\d+"}
    )

    assert result.status == PASS
    assert result.details["found"] is True


def test_a_match_without_a_timer_reports_a_failure(without_a_timer):
    """A pattern that does not match still fails."""
    result = RegexEvaluator().evaluate(
        "order-42", {"pattern": r"invoice-\d+"}
    )

    assert result.status == FAIL


def test_a_match_outside_the_main_thread_is_bounded():
    """A match in a worker thread cannot arm a timer, so it is bounded."""
    outcome = {}

    def worker():
        outcome["result"] = RegexEvaluator().evaluate(
            "order-42", {"pattern": r"order-\d+"}
        )

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout=30)

    assert not thread.is_alive(), "the evaluation did not finish"
    assert outcome["result"].status == PASS


def test_a_match_outside_the_main_thread_refuses_a_dangerous_shape():
    """The shape check does not depend on the thread."""
    outcome = {}

    def worker():
        outcome["result"] = RegexEvaluator().evaluate(
            "a" * 40 + "!", {"pattern": r"(a+)\1"}
        )

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout=30)

    assert not thread.is_alive()
    assert outcome["result"].status == ERROR


def test_a_catastrophic_pattern_is_refused():
    """A pattern that backtracks without end never runs."""
    result = RegexEvaluator().evaluate(
        "a" * 40 + "!", {"pattern": r"(a+)+$"}
    )

    assert result.status == ERROR
    assert "without end" in result.message


def test_a_backreference_is_refused():
    """A backreference is one of the shapes that cost the most."""
    assert is_dangerous(r"(a+)\1") is not None
    assert is_dangerous(r"(a|aa)+$") is not None
    assert is_dangerous(r"order-\d+") is None


def test_a_pattern_that_slips_past_the_shape_check_is_still_bounded(
    without_a_timer,
):
    """A pattern the shape check misses must not stall the run.

    The shape check cannot enumerate every shape that backtracks
    without end. The time limit is what catches the rest, so it has
    to hold where no timer exists.
    """
    start = time.monotonic()

    result = RegexEvaluator().evaluate(
        "a" * 40 + "!", {"pattern": r"(?:a?){40}a{40}"}
    )

    elapsed = time.monotonic() - start

    assert result.status in (PASS, FAIL, ERROR)
    assert elapsed < MATCH_TIMEOUT_SECONDS * 5, (
        "the match was not bounded without a timer"
    )


def test_the_timeout_is_reported_as_an_error(monkeypatch):
    """A match that runs out of time is an error, not a failure."""
    import paisl.evaluators.regex as regex_module

    def _slow(*args, **kwargs):
        raise regex_module.RegexTimeout("too slow")

    monkeypatch.setattr(regex_module, "_bounded_search", _slow)

    result = RegexEvaluator().evaluate("text", {"pattern": "text"})

    assert result.status == ERROR
    assert "finish" in result.message


def test_an_invalid_pattern_is_reported_as_an_error():
    """A pattern that does not compile is an error."""
    result = RegexEvaluator().evaluate("text", {"pattern": "([unclosed"})

    assert result.status == ERROR
    assert "not a valid regular expression" in result.message


def test_a_long_pattern_is_refused():
    """A pattern beyond the limit is refused."""
    result = RegexEvaluator().evaluate("text", {"pattern": "a" * 600})

    assert result.status == ERROR


def test_a_long_output_is_truncated():
    """A long output is bounded before it is matched."""
    result = RegexEvaluator().evaluate("x" * 100000, {"pattern": "x"})

    assert result.status == PASS
    assert result.details["truncated"] is True


def test_the_child_process_path_is_used_without_a_timer(
    without_a_timer, monkeypatch
):
    """The evaluator reaches for a killable process, not an open search."""
    import paisl.evaluators.regex as regex_module

    used = []

    def _child(pattern, text):
        used.append("child")
        return regex_module._Found(True)

    monkeypatch.setattr(regex_module, "_search_in_child_process", _child)

    result = RegexEvaluator().evaluate("text", {"pattern": "text"})

    assert used == ["child"]
    assert result.status == PASS


def test_a_pattern_is_refused_when_no_bound_is_available(monkeypatch):
    """Without a timer and without a child process the pattern is refused.

    A thread is not a bound: a runaway regular expression keeps the
    lock of the interpreter, so the waiting thread is released late
    and the worker keeps burning. Refusing the pattern is honest,
    hanging is not.
    """
    import paisl.evaluators.regex as regex_module

    monkeypatch.setattr(regex_module, "timeout_available", lambda: False)

    def _no_child(pattern, text):
        raise regex_module._NoChildProcess("no child")

    monkeypatch.setattr(regex_module, "_search_in_child_process", _no_child)

    result = RegexEvaluator().evaluate("text", {"pattern": "text"})

    assert result.status == ERROR
    assert "safely" in result.message
