# SPDX-License-Identifier: MIT
"""The regression matrix.

One test per scenario of the review list, with the identifier of the
list, so that every scenario can be accepted on its own.

| ID | Scenario | Expected |
|---|---|---|
| REG-001 | A suite that names no case | A failure or an error |
| REG-002 | A fixture path that does not exist | An error |
| REG-003 | An excludes assertion and a missing output | An error, never a pass |
| REG-004 | Every assertion is skipped | A skip, never a pass |
| REG-005 | A hard regular expression without a timer or in a thread | It ends within the limit |
| REG-006 | An assertion changes while the material stays | The run identifier or the definition digest changes |
| REG-007 | The evidence holds an invalid reference | The evidence check exits non-zero |
| REG-008 | A verified Standard has no valid approval | The governance check exits non-zero |
| REG-009 | A historical review does not match the current content | Handled by the version and the lifecycle policy |
| REG-010 | Sound data throughout | The behaviour stays as it was |
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import threading
import time

import pytest
import yaml

from paisl.evaluation import (
    AssertionResult,
    _case_status,
    evaluate_case,
    run_suite,
)
from paisl.evaluators import ERROR, PASS, SKIP
from paisl.evaluators.regex import (
    MATCH_TIMEOUT_SECONDS,
    RegexEvaluator,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
STANDARD = "PAISL-COMM-001"
ENGINEERING = "PAISL-ENG-001"


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


def _write(repo: pathlib.Path, relative: str, data: dict) -> pathlib.Path:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# SPDX-License-Identifier: CC-BY-4.0\n"
        + yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def _case(
    case_id: str = "REG-CASE-001",
    standard_id: str = STANDARD,
    rule_ids=None,
    evaluator: str = "contains",
    text: str = "Restart the service",
    severity: str = "must",
    input_path: str = "evaluations/fixtures/comm-001-input.txt",
    output_path: str = "evaluations/fixtures/comm-001-output.txt",
) -> dict:
    return {
        "id": case_id,
        "schema_version": "0.2.0",
        "standard_id": standard_id,
        "rule_ids": rule_ids or ["R001"],
        "title": "Regression case",
        "fixture": {"input": input_path, "output": output_path},
        "assertions": [
            {
                "id": "A001",
                "evaluator": evaluator,
                "params": {"text": text},
                "severity": severity,
            }
        ],
    }


def _suite(case_ids, suite_id: str = "reg-suite", required: bool = False) -> dict:
    return {
        "id": suite_id,
        "schema_version": "0.2.0",
        "version": "0.2.1",
        "title": {"en": "Regression suite", "zh-CN": "回归套件"},
        "description": {
            "en": "Cases used by the regression matrix.",
            "zh-CN": "回归矩阵使用的用例。",
        },
        "required": required,
        "cases": case_ids,
    }


# --- REG-001 ---------------------------------------------------------

def test_reg001_a_suite_without_a_case_fails(repo_copy):
    """A suite that names no case does not pass."""
    _write(
        repo_copy,
        "evaluations/suites/reg-suite.yaml",
        _suite([]),
    )

    result = _cli(repo_copy, "evaluate", "--suite", "reg-suite")

    assert result.returncode == 1, (
        "a suite that names no case must not report a success"
    )
    assert "no case" in result.stdout


def test_reg001_an_empty_suite_result_is_not_a_pass(repo_root):
    """The result of an empty suite does not pass."""
    suite = _suite([])
    result = run_suite(repo_root, suite, [])

    assert result.passed is False
    assert result.summary == {
        "pass": 0, "fail": 0, "skip": 0, "error": 0,
        "assertions": {"pass": 0, "fail": 0, "skip": 0, "error": 0},
    }


# --- REG-002 ---------------------------------------------------------

def test_reg002_a_missing_input_fixture_is_an_error(repo_copy):
    """A case whose input fixture does not exist is an error."""
    _write(
        repo_copy,
        "evaluations/cases/REG-CASE-001.yaml",
        _case(input_path="evaluations/fixtures/absent-input.txt"),
    )
    _write(
        repo_copy,
        "evaluations/suites/reg-suite.yaml",
        _suite(["REG-CASE-001"]),
    )

    result = _cli(
        repo_copy, "evaluate", "--suite", "reg-suite", "--format", "json"
    )

    payload = json.loads(result.stdout)
    case = payload["cases"][0]

    assert case["status"] == ERROR
    assert "missing" in case["assertions"][0]["message"]


def test_reg002_a_missing_output_fixture_is_an_error(repo_copy):
    """A case whose output fixture does not exist is an error."""
    _write(
        repo_copy,
        "evaluations/cases/REG-CASE-001.yaml",
        _case(output_path="evaluations/fixtures/absent-output.txt"),
    )
    _write(
        repo_copy,
        "evaluations/suites/reg-suite.yaml",
        _suite(["REG-CASE-001"]),
    )

    result = _cli(
        repo_copy, "evaluate", "--suite", "reg-suite", "--format", "json"
    )

    payload = json.loads(result.stdout)

    assert payload["cases"][0]["status"] == ERROR


# --- REG-003 ---------------------------------------------------------

def test_reg003_an_excludes_assertion_with_a_missing_output_is_an_error(
    repo_copy,
):
    """A missing output never becomes the empty text.

    An excludes assertion holds for the empty text, so a missing
    output that was read as empty content would report a pass.
    """
    _write(
        repo_copy,
        "evaluations/cases/REG-CASE-001.yaml",
        _case(
            evaluator="excludes",
            text="maybe restart",
            output_path="evaluations/fixtures/absent-output.txt",
        ),
    )
    _write(
        repo_copy,
        "evaluations/suites/reg-suite.yaml",
        _suite(["REG-CASE-001"]),
    )

    result = _cli(
        repo_copy, "evaluate", "--suite", "reg-suite", "--format", "json"
    )

    payload = json.loads(result.stdout)
    case = payload["cases"][0]

    assert case["status"] != PASS, (
        "a missing output must never be reported as a qualified output"
    )
    assert case["status"] == ERROR

    # The assertion itself must not have been judged on empty content.
    assert case["assertions"][0]["status"] == ERROR
    assert "missing" in case["assertions"][0]["message"]


# --- REG-004 ---------------------------------------------------------

def test_reg004_a_case_with_only_skipped_assertions_is_skipped():
    """A case whose assertions were all skipped is skipped."""
    results = [
        AssertionResult(
            id="A001",
            evaluator="contains",
            severity="should",
            status=SKIP,
            message="",
        )
    ]

    assert _case_status(results) == SKIP
    assert _case_status(results) != PASS


def test_reg004_a_skipped_case_does_not_pass_the_suite(repo_copy):
    """A case the caller skipped is counted as skipped."""
    _write(
        repo_copy,
        "evaluations/cases/REG-CASE-001.yaml",
        _case(),
    )
    _write(
        repo_copy,
        "evaluations/suites/reg-suite.yaml",
        _suite(["REG-CASE-001"]),
    )

    result = _cli(
        repo_copy,
        "evaluate",
        "--suite",
        "reg-suite",
        "--skip",
        "REG-CASE-001",
        "--format",
        "json",
    )

    payload = json.loads(result.stdout)

    assert payload["summary"]["skip"] == 1
    assert payload["summary"]["pass"] == 0
    assert result.returncode == 1, (
        "a suite whose only case was skipped does not pass"
    )


# --- REG-005 ---------------------------------------------------------

def test_reg005_a_hard_pattern_ends_without_a_timer(repo_copy, monkeypatch):
    """A pattern that backtracks without end ends within the limit.

    The platform without a timer is what Windows looks like.
    """
    import signal

    import paisl.evaluators.regex as regex_module

    monkeypatch.delattr(signal, "setitimer", raising=False)
    monkeypatch.delattr(signal, "SIGALRM", raising=False)

    assert not regex_module.timeout_available()

    start = time.monotonic()
    result = RegexEvaluator().evaluate(
        "a" * 28 + "!", {"pattern": r"(?:a?){28}a{28}"}
    )
    elapsed = time.monotonic() - start

    assert elapsed < MATCH_TIMEOUT_SECONDS * 5, (
        "the match was not bounded without a timer"
    )
    assert result.status in (ERROR, PASS)


def test_reg005_a_hard_pattern_ends_in_a_thread(repo_root):
    """A match outside the main thread ends within the limit."""
    outcome = {}

    def worker():
        start = time.monotonic()
        outcome["result"] = RegexEvaluator().evaluate(
            "a" * 28 + "!", {"pattern": r"(?:a?){28}a{28}"}
        )
        outcome["elapsed"] = time.monotonic() - start

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout=MATCH_TIMEOUT_SECONDS * 10)

    assert not thread.is_alive(), "the evaluation did not finish"
    assert outcome["elapsed"] < MATCH_TIMEOUT_SECONDS * 5


# --- REG-006 ---------------------------------------------------------

def test_reg006_a_changed_assertion_changes_the_run_identifier(repo_copy):
    """Changing an assertion changes the identifier, the material stays."""
    def evaluate(text: str) -> dict:
        _write(
            repo_copy,
            "evaluations/cases/REG-CASE-001.yaml",
            _case(text=text),
        )
        _write(
            repo_copy,
            "evaluations/suites/reg-suite.yaml",
            _suite(["REG-CASE-001"]),
        )
        result = _cli(
            repo_copy,
            "evaluate",
            "--suite",
            "reg-suite",
            "--format",
            "json",
        )
        return json.loads(result.stdout)

    first = evaluate("Restart the service")
    second = evaluate("A completely different wording")

    assert first["run_id"] != second["run_id"], (
        "the run identifier must cover the assertions"
    )
    assert first["definition_digest"] != second["definition_digest"]

    # The material did not change.
    assert (
        first["cases"][0]["input_digest"]
        == second["cases"][0]["input_digest"]
    )
    assert (
        first["cases"][0]["output_digest"]
        == second["cases"][0]["output_digest"]
    )


# --- REG-007 ---------------------------------------------------------

def test_reg007_an_invalid_reference_in_the_evidence_fails_the_check(
    repo_copy,
):
    """The evidence check exits non-zero on an invalid reference."""
    _write(
        repo_copy,
        "evidence/links/PAISL-ENG-002.yaml",
        {
            "schema_version": "0.2.0",
            "standard_id": "PAISL-ENG-002",
            "standard_version": "0.1.0",
            "rules": [
                {
                    "rule_id": "R001",
                    "evidence": [
                        {
                            "evidence_id": "EVD-0001",
                            "relationship": "supports",
                            "locator": "L",
                            "note": None,
                        }
                    ],
                }
            ],
        },
    )

    result = _cli(repo_copy, "evidence", "check")

    assert result.returncode == 1, (
        "an invalid reference must fail the evidence check"
    )
    assert "PAISL-ENG-002" in result.stdout


# --- REG-008 ---------------------------------------------------------

def test_reg008_a_verified_standard_without_an_approval_fails_the_check(
    repo_copy,
):
    """The governance check exits non-zero on an unapproved promotion."""
    path = repo_copy / "standards" / "engineering" / "owasp-asvs.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("status: draft", "status: verified"), encoding="utf-8"
    )

    result = _cli(repo_copy, "governance", "check")

    assert result.returncode == 1, (
        "a Standard that claims to be verified without an approval must "
        "fail the governance check"
    )
    assert "verified" in result.stdout


# --- REG-009 ---------------------------------------------------------

def test_reg009_a_review_of_an_earlier_revision_is_only_a_warning(
    repo_copy,
):
    """A review of an earlier revision does not block the Standard.

    The content changed and the version moved with it, so the review
    belongs to the earlier revision. It is reported, and the Standard
    is not held back.
    """
    path = repo_copy / "standards" / "engineering" / "owasp-asvs.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("version: 0.1.0", "version: 0.2.0")
        + "\n# a later edit\n",
        encoding="utf-8",
    )

    result = _cli(repo_copy, "governance", "check")

    assert result.returncode == 0, (
        "a review of an earlier revision must not block the Standard"
    )
    assert "does not match" in result.stdout, (
        "the review of the earlier revision must be reported"
    )


def test_reg009_a_content_change_without_a_version_update_is_an_error(
    repo_copy,
):
    """A content change without a version update is an error."""
    path = repo_copy / "standards" / "engineering" / "owasp-asvs.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(text + "\n# a later edit\n", encoding="utf-8")

    result = _cli(repo_copy, "governance", "check")

    assert result.returncode == 1
    assert "version stayed" in result.stdout


def test_reg009_a_verified_standard_with_a_stale_review_is_an_error(
    repo_copy,
):
    """A verified Standard may not keep a review that no longer fits."""
    path = repo_copy / "standards" / "engineering" / "owasp-asvs.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("status: draft", "status: verified")
        + "\n# a later edit\n",
        encoding="utf-8",
    )

    result = _cli(repo_copy, "governance", "check")

    assert result.returncode == 1
    assert "approved-review-record" in result.stdout, (
        "the gate that the stale review fails must be named"
    )


# --- REG-010 ---------------------------------------------------------

def test_reg010_sound_data_keeps_the_behaviour(repo_copy):
    """With sound data every command succeeds."""
    for command in (
        ("validate",),
        ("coverage",),
        ("evidence", "check"),
        ("governance", "check"),
        ("conflicts", "check"),
        ("evaluate", "--suite", "core-regression"),
        ("report", "--suite", "core-regression"),
    ):
        result = _cli(repo_copy, *command)

        assert result.returncode == 0, (
            f"{command} returned {result.returncode}: {result.stdout}"
        )


def test_reg010_the_legacy_command_is_unchanged(repo_copy):
    """The compatibility wrapper keeps its output and its exit code."""
    expected = json.loads(
        (
            ROOT / "tests" / "fixtures" / "legacy" / "pass.json"
        ).read_text(encoding="utf-8")
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate.py"],
        cwd=repo_copy,
        capture_output=True,
        text=True,
    )

    assert result.returncode == expected["exit_code"]
    assert result.stdout == expected["stdout"]
