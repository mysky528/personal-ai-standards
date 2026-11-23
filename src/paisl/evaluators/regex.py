# SPDX-License-Identifier: MIT
"""The `regex` evaluator.

A regular expression can consume an unbounded amount of time, so the
evaluator bounds the work in three layers:

- the shape of the pattern is refused when it may match without end,
- the length of the pattern and of the input is bounded, and
- the match itself is given a time limit.

The time limit has to work everywhere. Where the platform offers a
timer, the match runs in the current process under that timer. Where
it does not, the match runs in a child process that can be
terminated, so a pattern that slips past the shape check still
cannot stall the run.
"""

from __future__ import annotations

import multiprocessing
import re
import signal
import threading
import time

from . import ERROR, FAIL, PASS, EvaluationResult

# The limits keep a single assertion from stalling a run.
MAX_PATTERN_LENGTH = 512
MAX_INPUT_LENGTH = 65536
MATCH_TIMEOUT_SECONDS = 1.0

# The time the parent waits for the result of a child that has ended.
RESULT_TIMEOUT_SECONDS = 0.5

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


class _NoChildProcess(Exception):
    """Raised when a child process cannot be started."""


class _ChildDidNotReport(Exception):
    """Raised when a child process ends without reporting a result."""


def timeout_available() -> bool:
    """Report whether a match can be given a time limit in this process.

    A timer needs SIGALRM and the main thread. Without one, the match
    has to run somewhere that can be terminated.
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


def _search_with_timer(pattern: str, text: str):
    """Search under a timer, in the current process.

    The timer of the process belongs to the caller as much as to the
    evaluator. What was armed before the match is armed again
    afterwards, with the time that the match took taken off, so that
    the deadline of the caller stays where it was.
    """
    previous_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    started = time.monotonic()

    signal.setitimer(signal.ITIMER_REAL, MATCH_TIMEOUT_SECONDS)

    try:
        return re.search(pattern, text)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        _restore_timer(previous_timer, started)


def _restore_timer(previous: tuple, started: float) -> None:
    """Give the caller back the timer that was found.

    The deadline of the caller does not move. The time that the match
    took is taken off the time that was left, and a deadline that
    passed while the match ran fires at once, so that the caller is
    told as soon as it may be told.
    """
    delay, interval = previous

    if delay <= 0:
        # The caller had no timer armed. There is nothing to give back.
        return

    elapsed = time.monotonic() - started
    remaining = delay - elapsed

    if remaining > 0:
        signal.setitimer(signal.ITIMER_REAL, remaining, interval)
        return

    signal.setitimer(signal.ITIMER_REAL, 0.000001, interval)


def _match_worker(pattern: str, text: str, queue) -> None:
    """Search in a child process and report the outcome."""
    try:
        queue.put(("ok", re.search(pattern, text) is not None))
    except re.error as exc:
        queue.put(("error", str(exc)))
    except Exception:  # pragma: no cover - defensive
        queue.put(("error", "the match failed"))


def _search_in_child_process(pattern: str, text: str):
    """Search in a child process that can be terminated.

    This is the path for a platform without a timer and for a match
    outside the main thread. The child is terminated when it takes
    longer than the limit, so a pattern that slips past the shape
    check still cannot stall the run.

    The result travels back over a queue. The read waits for a short
    time instead of asking for whatever is there at that moment: a
    child that has ended may still have its result on the way, and a
    read that gives up too early turns a finished match into a
    failure.
    """
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    process = context.Process(
        target=_match_worker, args=(pattern, text, queue)
    )

    try:
        process.start()
    except (OSError, ValueError, RuntimeError) as exc:
        queue.close()
        raise _NoChildProcess(str(exc)) from exc

    try:
        process.join(MATCH_TIMEOUT_SECONDS)

        if process.is_alive():
            process.terminate()
            process.join(1)

            if process.is_alive():  # pragma: no cover - defensive
                process.kill()
                process.join(1)

            raise RegexTimeout(
                f"The pattern did not finish within "
                f"{MATCH_TIMEOUT_SECONDS} seconds."
            )

        try:
            outcome, value = queue.get(timeout=RESULT_TIMEOUT_SECONDS)
        except Exception as exc:
            # The child never reported. The usual reason is that the
            # main module cannot be imported again, which the spawn
            # method needs.
            raise _ChildDidNotReport(
                f"the child process ended without reporting a result "
                f"(exit code {process.exitcode}). The main module of "
                f"the caller has to be importable again, which the "
                f"spawn method needs."
            ) from exc

        if outcome == "error":
            raise re.error(value)

        return _Found(value)
    finally:
        queue.close()
        try:
            queue.join_thread()
        except (AssertionError, OSError, ValueError):  # pragma: no cover
            pass


def _search_in_thread(pattern: str, text: str):
    """Search in a thread. Not a safe bound, kept for the last resort.

    A runaway regular expression holds the lock of the interpreter,
    so the waiting thread is released late and the worker keeps
    burning. The evaluator does not use this path to claim a bound.
    """
    outcome: dict = {}

    def worker():
        try:
            outcome["match"] = re.search(pattern, text)
        except re.error as exc:
            outcome["error"] = exc

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(MATCH_TIMEOUT_SECONDS)

    if thread.is_alive():
        raise RegexTimeout(
            f"The pattern did not finish within "
            f"{MATCH_TIMEOUT_SECONDS} seconds."
        )

    if "error" in outcome:
        raise outcome["error"]

    return outcome.get("match")


class _Found:
    """The result of a match that ran in a child process."""

    def __init__(self, found: bool):
        self.found = found

    def __bool__(self) -> bool:
        return self.found


def _bounded_search(pattern: str, text: str):
    """Search with a time limit on every platform.

    A timer in the current process is the cheapest bound and it
    interrupts a runaway match. Without one, the match has to run
    where it can be terminated.
    """
    if timeout_available():
        return _search_with_timer(pattern, text)

    try:
        return _search_in_child_process(pattern, text)
    except _NoChildProcess as exc:
        # A thread would not hold the bound, because a runaway
        # regular expression keeps the lock of the interpreter. The
        # pattern is refused instead of being run without a limit.
        raise _NoChildProcess(
            "the pattern could not be evaluated with a time limit: "
            f"no timer and no child process ({exc})"
        ) from exc


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

        # The bound on the input is the same on every platform. The
        # match is bounded by the time limit, and the child process
        # can be terminated, so a shorter input would only make the
        # answer depend on the platform: the same case would pass
        # where a timer exists and fail where it does not.
        limit = MAX_INPUT_LENGTH
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
        except _ChildDidNotReport as exc:
            return EvaluationResult(
                status=ERROR,
                message=f"The pattern could not be evaluated safely: {exc}",
                details={"parameter": "pattern"},
            )
        except _NoChildProcess as exc:
            return EvaluationResult(
                status=ERROR,
                message=f"The pattern could not be evaluated safely: {exc}",
                details={"parameter": "pattern"},
            )
        except re.error as exc:
            return EvaluationResult(
                status=ERROR,
                message=f"The pattern is not a valid regular expression: {exc}",
                details={"parameter": "pattern"},
            )

        found = bool(match)

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
