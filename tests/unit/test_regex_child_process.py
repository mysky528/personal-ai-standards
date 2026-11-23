# SPDX-License-Identifier: MIT
"""The boundaries of the result passing of the child process.

The regular expression evaluator runs the match in a child process
where no timer can be armed. The result travels back over a queue,
and every step of that journey has a boundary worth a test:

- a match and a miss both arrive
- an empty match is a match, not a miss
- a pattern that does not compile arrives as an error
- a child that ends without reporting does not hang the parent
- a child that runs out of time is terminated
- the two paths give the same answer for the same material, so the
  answer does not depend on the platform
"""

from __future__ import annotations

import multiprocessing
import os
import re
import time

import pytest

import paisl.evaluators.regex as regex_module
from paisl.evaluators import ERROR, FAIL, PASS
from paisl.evaluators.regex import (
    MATCH_TIMEOUT_SECONDS,
    MAX_INPUT_LENGTH,
    RegexEvaluator,
)

# The repetitions of the stress test. The short run keeps the suite
# quick, the long run repeats the search thousands of times.
REPETITIONS = 200
LONG_REPETITIONS = 3000


def _dying_context(real):
    """Return a context whose child ends without reporting anything."""

    class _Context:
        def __init__(self, real):
            self._real = real

        def Queue(self):
            return self._real.Queue()

        def Process(self, target=None, args=()):
            # The child leaves without putting anything on the queue.
            return self._real.Process(target=os._exit, args=(9,))

    return _Context(real)


def test_a_match_arrives_from_the_child():
    """A match that the child found arrives as a match."""
    result = regex_module._search_in_child_process("a+", "aaa")

    assert result.found is True
    assert bool(result) is True


def test_a_miss_arrives_from_the_child():
    """A match that the child did not find arrives as a miss."""
    result = regex_module._search_in_child_process("b+", "aaa")

    assert result.found is False
    assert bool(result) is False


def test_an_empty_match_is_a_match():
    """An empty match is a match, not a miss.

    The pattern holds at the first position of a text that does not
    contain it. The result travels back as a truth value, so a match
    that covers nothing has to stay a match.
    """
    result = regex_module._search_in_child_process("a*", "bbb")

    assert result.found is True


def test_a_pattern_error_arrives_as_an_error():
    """A pattern that does not compile arrives as an error.

    The child cannot raise into the parent, so the error travels back
    as a message and is raised again on this side.
    """
    with pytest.raises(re.error) as failure:
        regex_module._search_in_child_process("a(", "aaa")

    assert "position 1" in str(failure.value)


def test_a_child_that_ends_without_reporting_is_an_error(monkeypatch):
    """A child that dies without reporting does not hang the parent.

    The child cannot raise into the parent, and it may die before it
    puts anything on the queue. The parent has to say so, and it has
    to name the exit code of the child, because that is what tells
    the reader what went wrong.
    """
    real_context = multiprocessing.get_context("spawn")

    monkeypatch.setattr(
        regex_module.multiprocessing,
        "get_context",
        lambda name=None: _dying_context(real_context),
    )
    monkeypatch.setattr(regex_module, "timeout_available", lambda: False)

    start = time.monotonic()
    result = RegexEvaluator().evaluate("aaa", {"pattern": "a+"})
    elapsed = time.monotonic() - start

    assert result.status == ERROR
    assert "without reporting" in result.message
    assert "exit code 9" in result.message
    assert "Empty" not in result.message, (
        "the finding must not repeat the name of an internal exception"
    )
    assert elapsed < MATCH_TIMEOUT_SECONDS * 5, (
        "the parent waited for a child that was never going to report"
    )


def test_a_child_that_runs_out_of_time_is_terminated():
    """The parent terminates a child that runs out of time."""
    start = time.monotonic()

    with pytest.raises(regex_module.RegexTimeout):
        regex_module._search_in_child_process(
            r"(?:a?){40}a{40}", "a" * 40 + "!"
        )

    elapsed = time.monotonic() - start

    assert elapsed < MATCH_TIMEOUT_SECONDS * 5, (
        "the parent did not return within the bound"
    )


def test_the_result_passing_is_reliable():
    """The result arrives every time.

    A read that gives up too early turns a finished match into a
    failure, and such a failure appears at random. The search is
    repeated, and every answer has to be the same.
    """
    for _ in range(20):
        assert regex_module._search_in_child_process("a+", "aaa").found
        assert not regex_module._search_in_child_process("b+", "aaa").found


def _repeat_the_search(repetitions: int) -> list:
    """Search the same short text again and again, and collect the faults."""
    faults: list = []

    for _ in range(repetitions):
        try:
            result = regex_module._search_in_child_process("a+", "aaa")
        except Exception as exc:
            faults.append(f"{type(exc).__name__}: {exc}")
            continue

        if not result.found:
            faults.append("the match did not arrive")

    return faults


def test_the_result_passing_holds_under_repetition():
    """The result arrives every time, over many repetitions.

    A child that ends and a result that is still on its way are close
    to each other. The read waits for the result, so the two cannot
    be confused. The search is repeated, and every answer has to
    arrive.
    """
    faults = _repeat_the_search(REPETITIONS)

    assert not faults, (
        f"{len(faults)} of {REPETITIONS} searches did not return a "
        f"result: {faults[:3]}"
    )


@pytest.mark.slow
def test_the_result_passing_holds_under_a_long_repetition():
    """The result arrives every time, over thousands of repetitions.

    The fault this guards against is rare and random. A fault that
    happens once in a thousand is gone in a hundred runs and back in
    a thousand. The long run is the one that finds it.

    The test is marked slow and runs apart from the suite.
    """
    faults = _repeat_the_search(LONG_REPETITIONS)

    assert not faults, (
        f"{len(faults)} of {LONG_REPETITIONS} searches did not return a "
        f"result: {faults[:3]}"
    )


def test_both_paths_give_the_same_answer(monkeypatch):
    """The answer does not depend on the platform.

    One path arms a timer and runs the match in this process. The
    other runs it in a child process that can be terminated. The two
    have to answer the same question the same way, or a case passes
    on one platform and fails on another.
    """
    text = "x" * 9000 + "NEEDLE"

    with_timer = RegexEvaluator().evaluate(text, {"pattern": "NEEDLE"})

    monkeypatch.setattr(regex_module, "timeout_available", lambda: False)
    without_timer = RegexEvaluator().evaluate(text, {"pattern": "NEEDLE"})

    assert with_timer.status == PASS
    assert without_timer.status == PASS
    assert with_timer.details["found"] == without_timer.details["found"]
    assert with_timer.details["truncated"] == without_timer.details["truncated"]


def test_both_paths_report_the_same_truncation(monkeypatch):
    """A long output is cut at the same place on both paths."""
    text = "x" * (MAX_INPUT_LENGTH + 1000) + "NEEDLE"

    with_timer = RegexEvaluator().evaluate(text, {"pattern": "NEEDLE"})

    monkeypatch.setattr(regex_module, "timeout_available", lambda: False)
    without_timer = RegexEvaluator().evaluate(text, {"pattern": "NEEDLE"})

    assert with_timer.details["truncated"] is True
    assert without_timer.details["truncated"] is True
    assert with_timer.status == without_timer.status == FAIL


def test_a_match_outside_the_main_thread_gives_the_same_answer():
    """A match in a worker thread answers the same way.

    A worker thread cannot arm a timer, so it takes the child process
    path. The answer must not depend on the thread.
    """
    text = "x" * 9000 + "NEEDLE"

    in_thread: dict = {}

    def worker():
        in_thread["result"] = RegexEvaluator().evaluate(
            text, {"pattern": "NEEDLE"}
        )

    import threading

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout=30)

    assert not thread.is_alive()
    assert in_thread["result"].status == PASS


def test_the_search_does_not_leave_a_descriptor_open():
    """A search does not leave a descriptor behind.

    Every search opens the pipe of a queue. The parent has to let it
    go, otherwise a long suite runs out of descriptors.
    """
    def descriptors() -> int:
        for directory in ("/proc/self/fd", "/dev/fd"):
            if os.path.isdir(directory):
                return len(os.listdir(directory))
        return -1

    before = descriptors()

    if before < 0:  # pragma: no cover - the platform has no listing
        pytest.skip("the platform does not list its descriptors")

    for _ in range(30):
        regex_module._search_in_child_process("a+", "aaa")

    assert descriptors() <= before + 2, (
        "the searches left descriptors behind"
    )
