# SPDX-License-Identifier: MIT
"""AC-011 to AC-014 — the evaluation acceptance criteria.

AC-011: the built-in evaluators produce correct pass and fail results.
AC-012: invalid fixtures and unknown evaluators produce an error status.
AC-013: identical fixtures produce identical normalised results.
AC-014: path traversal is rejected.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys


def _cli(repo, *args):
    return subprocess.run(
        [sys.executable, "-m", "paisl", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        env={
            "PYTHONPATH": str(repo / "src"),
            "PATH": "/usr/bin:/bin:/usr/local/bin",
        },
    )


def test_ac011_the_suite_passes(repo_copy):
    """The reference suite passes against its own fixtures."""
    result = _cli(repo_copy, "evaluate", "--suite", "core-regression")

    assert result.returncode == 0, result.stdout
    assert "2 passed, 0 failed" in result.stdout


def test_ac011_a_wrong_output_fails(repo_copy):
    """An output that breaks the rule fails the case."""
    output = repo_copy / ".paisl" / "outputs" / "comm-001.txt"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("maybe restart the service\n", encoding="utf-8")

    result = _cli(
        repo_copy,
        "evaluate",
        "--case",
        "COMM-001-CASE-001",
        "--output-file",
        str(output),
        "--format",
        "json",
    )

    assert result.returncode == 1

    payload = json.loads(result.stdout)
    case = payload["cases"][0]

    assert case["status"] == "fail"
    assert case["assertions"][0]["status"] == "fail"
    assert case["assertions"][1]["status"] == "fail"


def test_ac012_an_unknown_evaluator_produces_an_error(repo_copy):
    """A case that selects an evaluator that is not allowed errors."""
    path = repo_copy / "evaluations" / "cases" / "COMM-001-CASE-001.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("evaluator: contains", "evaluator: execute_python"),
        encoding="utf-8",
    )

    result = _cli(
        repo_copy,
        "evaluate",
        "--case",
        "COMM-001-CASE-001",
        "--format",
        "json",
    )

    assert result.returncode == 1

    payload = json.loads(result.stdout)
    case = payload["cases"][0]

    assert case["status"] == "error"
    assert "not allowed" in case["assertions"][0]["message"]


def test_ac012_an_invalid_fixture_is_reported(repo_copy):
    """A fixture that does not exist is reported."""
    path = repo_copy / "evaluations" / "cases" / "COMM-001-CASE-001.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace(
            "evaluations/fixtures/comm-001-output.txt",
            "evaluations/fixtures/absent.txt",
        ),
        encoding="utf-8",
    )

    result = _cli(repo_copy, "validate")

    assert result.returncode == 1
    assert "fixture file missing" in result.stdout


def test_ac013_the_report_is_reproducible(repo_copy):
    """Two runs of the same suite give the same report."""
    first = _cli(
        repo_copy, "evaluate", "--suite", "core-regression", "--format", "json"
    )
    second = _cli(
        repo_copy, "evaluate", "--suite", "core-regression", "--format", "json"
    )

    assert first.stdout == second.stdout
    assert first.returncode == second.returncode == 0


def test_ac013_the_report_holds_no_absolute_path(repo_copy):
    """The report does not carry the path of the machine that made it."""
    result = _cli(
        repo_copy, "evaluate", "--suite", "core-regression", "--format", "json"
    )

    assert str(repo_copy) not in result.stdout


def test_ac014_path_traversal_is_rejected(repo_copy):
    """A fixture that leaves the repository is refused."""
    path = repo_copy / "evaluations" / "cases" / "COMM-001-CASE-001.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace(
            "evaluations/fixtures/comm-001-input.txt",
            "../outside.txt",
        ),
        encoding="utf-8",
    )

    result = _cli(repo_copy, "validate")

    assert result.returncode == 1
    assert "fixture path escapes the repository" in result.stdout


def test_evaluate_needs_a_suite_or_a_case(repo_copy):
    """The command needs to know what to run."""
    result = _cli(repo_copy, "evaluate")

    assert result.returncode == 2
