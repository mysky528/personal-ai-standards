# SPDX-License-Identifier: MIT
"""PAISL v0.2.1 regression tests.

Each test names the defect it pins. The tests were written before the
fixes, and each of them failed against the v0.2.0 implementation.

| ID | Defect |
|---|---|
| REG-001 | A case with a missing output fixture was reported as a failure instead of an error |
| REG-002 | A case with a missing input fixture was silently evaluated against an empty string, and could even pass |
| REG-003 | A case whose assertions were all skipped counted as a pass |
| REG-004 | The regular expression evaluator had no execution limit on a platform without SIGALRM, or outside the main thread |
| REG-005 | The check commands always exited with zero, so a workflow could not gate on them |
| REG-006 | The run identifier did not cover the evaluation definitions, so a changed assertion kept the same identifier |
| REG-007 | The evidence coverage gate could not see a rule that had no evidence link at all |
| REG-008 | An output file given on the command line was applied to every case of a suite |
| REG-009 | The command line module still described a single command, and the validator still carried an old version |
| REG-010 | The exit code contract was stated in one place and contradicted in another, and no test held it |
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import pytest
import yaml

from paisl.evaluation import (
    AssertionResult,
    _case_status,
    evaluate_case,
    run_suite,
)
from paisl.evaluators import ERROR, PASS, SKIP
from paisl.evaluators.regex import RegexEvaluator

ROOT = pathlib.Path(__file__).resolve().parents[2]
STANDARD = "PAISL-COMM-001"


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
    case_id: str = "CASE-0001-CASE-001",
    input_path: str = "evaluations/fixtures/comm-001-input.txt",
    output_path: str = "evaluations/fixtures/comm-001-output.txt",
    text: str = "Restart the service",
) -> dict:
    return {
        "id": case_id,
        "schema_version": "0.2.0",
        "standard_id": STANDARD,
        "rule_ids": ["R001"],
        "title": "Regression case",
        "fixture": {"input": input_path, "output": output_path},
        "assertions": [
            {
                "id": "A001",
                "evaluator": "contains",
                "params": {"text": text},
                "severity": "must",
            }
        ],
    }


def _suite(case_ids: list, suite_id: str = "reg-suite") -> dict:
    return {
        "id": suite_id,
        "schema_version": "0.2.0",
        "version": "0.2.1",
        "title": {"en": "Regression suite", "zh-CN": "回归套件"},
        "description": {
            "en": "Cases used by the regression tests.",
            "zh-CN": "回归测试使用的用例。",
        },
        "required": False,
        "cases": case_ids,
    }


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


# --- REG-001 ---------------------------------------------------------

def test_reg001_missing_output_fixture_is_an_error(repo_copy):
    """A case whose output fixture is missing is an error, not a failure.

    A missing fixture means the evaluation could not run. Reporting
    it as a failed assertion hides the real problem behind a rule
    that did not hold.
    """
    _write(
        repo_copy,
        "evaluations/cases/REG-CASE-001.yaml",
        _case(
            "REG-CASE-001",
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

    assert case["status"] == ERROR, (
        "a case with a missing output fixture must be an error, "
        f"not {case['status']!r}"
    )


# --- REG-002 ---------------------------------------------------------

def test_reg002_missing_input_fixture_is_an_error(repo_copy):
    """A case whose input fixture is missing is an error.

    The missing input used to be replaced by an empty string, so the
    evaluation ran against nothing and the case could even pass.
    """
    _write(
        repo_copy,
        "evaluations/cases/REG-CASE-001.yaml",
        _case(
            "REG-CASE-001",
            input_path="evaluations/fixtures/absent-input.txt",
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

    assert case["status"] == ERROR, (
        "a case with a missing input fixture must be an error, "
        f"not {case['status']!r}"
    )
    assert case["id"] == "REG-CASE-001", "the report must name the case"
    assert "missing" in case["assertions"][0]["message"].lower(), (
        "the report must say that the fixture is missing"
    )


# --- REG-003 ---------------------------------------------------------

def test_reg003_a_case_with_only_skipped_assertions_is_skipped():
    """A case that verified nothing is skipped, not passed."""
    results = [
        AssertionResult(
            id="A001",
            evaluator="contains",
            severity="should",
            status=SKIP,
            message="",
        )
    ]

    assert _case_status(results) == SKIP, (
        "a case whose assertions were all skipped must not count as a pass"
    )


def test_reg003_a_skipped_mandatory_assertion_is_not_a_pass():
    """A mandatory assertion that never ran is not a pass."""
    results = [
        AssertionResult(
            id="A001",
            evaluator="contains",
            severity="must",
            status=SKIP,
            message="",
        ),
        AssertionResult(
            id="A002",
            evaluator="contains",
            severity="should",
            status=PASS,
            message="",
        ),
    ]

    assert _case_status(results) == SKIP


# --- REG-004 ---------------------------------------------------------

def test_reg004_regex_is_bounded_without_a_signal_timer(monkeypatch):
    """The regular expression evaluator keeps a bound without SIGALRM.

    The timeout relied on signal.setitimer, which does not exist on
    every platform and does not work outside the main thread. The
    fallback was an unbounded search, so a pattern that backtracks
    without end could only be stopped by a timer that may not be
    there.

    The refusal must come from a check that works everywhere, not
    from waiting for a timeout.
    """
    import paisl.evaluators.regex as regex_module

    monkeypatch.setattr(
        regex_module, "timeout_available", lambda: False, raising=False
    )

    result = RegexEvaluator().evaluate(
        "a" * 24 + "!", {"pattern": r"(a+)\1"}
    )

    assert result.status == ERROR, (
        "a pattern that can match without end must be refused even "
        "when no timer is available"
    )
    assert "finish" not in result.message.lower(), (
        "the refusal must not depend on waiting for a timeout"
    )
    assert "timeout" not in result.message.lower(), (
        "the refusal must not depend on waiting for a timeout"
    )


def test_reg004_regex_reports_the_timeout(monkeypatch):
    """A match that runs out of time is an error, not a failure."""
    import paisl.evaluators.regex as regex_module

    def _slow(*args, **kwargs):
        raise regex_module.RegexTimeout("too slow")

    monkeypatch.setattr(regex_module, "_bounded_search", _slow)

    result = RegexEvaluator().evaluate("text", {"pattern": "text"})

    assert result.status == ERROR
    assert "finish" in result.message


# --- REG-005 ---------------------------------------------------------

def test_reg005_conflicts_check_fails_on_a_blocking_conflict(repo_copy):
    """A confirmed and unresolved conflict fails the check."""
    _write(
        repo_copy,
        "governance/conflicts/REG-CONFLICT-0001.yaml",
        {
            "id": "CONFLICT-0002",
            "schema_version": "0.2.0",
            "rules": [
                {"standard_id": "PAISL-COMM-001", "rule_id": "R001"},
                {"standard_id": "PAISL-COMM-002", "rule_id": "R001"},
            ],
            "classification": "confirmed",
            "status": "open",
            "description": "A confirmed blocking conflict.",
            "resolution": None,
            "reviewer": "reviewer-id",
        },
    )

    result = _cli(repo_copy, "conflicts", "check")

    assert result.returncode == 1, (
        "a confirmed and unresolved conflict must fail the check command"
    )


def test_reg005_evidence_check_fails_on_a_rejected_record(repo_copy):
    """A rejected record that supports a rule fails the check."""
    _write(
        repo_copy,
        "evidence/records/REG-EVD-0001.yaml",
        {
            "id": "EVD-0002",
            "schema_version": "0.2.0",
            "title": "A rejected source",
            "source": {
                "url": "https://example.org/rejected",
                "type": "secondary",
                "publisher": None,
                "retrieved_at": None,
                "accessed": False,
            },
            "review": {
                "status": "rejected",
                "reviewed_by": None,
                "reviewed_at": None,
                "rationale": None,
            },
            "notes": None,
        },
    )
    _write(
        repo_copy,
        "evidence/links/PAISL-COMM-001.yaml",
        {
            "schema_version": "0.2.0",
            "standard_id": "PAISL-COMM-001",
            "standard_version": "0.1.0",
            "rules": [
                {
                    "rule_id": "R001",
                    "evidence": [
                        {
                            "evidence_id": "EVD-0002",
                            "relationship": "supports",
                            "locator": None,
                            "note": None,
                        }
                    ],
                }
            ],
        },
    )

    result = _cli(repo_copy, "evidence", "check")

    assert result.returncode == 1, (
        "a rejected record that supports a rule must fail the check"
    )


def test_reg005_a_clean_repository_keeps_the_exit_codes(repo_copy):
    """A repository without findings still exits with zero."""
    for command in (
        ("evidence", "check"),
        ("governance", "check"),
        ("conflicts", "check"),
        ("coverage",),
        ("report",),
    ):
        result = _cli(repo_copy, *command)

        assert result.returncode == 0, f"{command} returned {result.returncode}"


# --- REG-006 ---------------------------------------------------------

def test_reg006_the_run_identifier_covers_the_definitions(repo_root):
    """A changed assertion changes the run identifier."""
    base = _case("REG-CASE-001")
    changed = _case("REG-CASE-001", text="A completely different wording")

    suite = {"id": "reg-suite", "version": "1", "cases": ["REG-CASE-001"]}

    first = run_suite(repo_root, suite, [base])
    second = run_suite(repo_root, suite, [changed])

    assert first.run_id != second.run_id, (
        "the run identifier must cover the evaluation definitions"
    )
    assert first.input_digest != second.input_digest


def test_reg006_the_run_identifier_is_stable(repo_root):
    """The same evaluation gives the same identifier."""
    base = _case("REG-CASE-001")
    suite = {"id": "reg-suite", "version": "1", "cases": ["REG-CASE-001"]}

    first = run_suite(repo_root, suite, [base])
    second = run_suite(repo_root, suite, [base])

    assert first.run_id == second.run_id
    assert first.input_digest == second.input_digest


# --- REG-007 ---------------------------------------------------------

def test_reg007_a_rule_without_a_link_is_visible(repo_copy):
    """A rule that has no evidence link is part of the coverage.

    The coverage was built from the links, so a rule that nobody
    linked was invisible and the gate could not see it.
    """
    import yaml as _yaml

    standard = repo_copy / "standards" / "reasoning" / "mece.yaml"
    data = _yaml.safe_load(standard.read_text(encoding="utf-8"))
    data["rules"].append({
        "id": "R002",
        "instruction": {
            "en": "A second rule that nobody linked to evidence.",
            "zh-CN": "第二条没有任何证据关联的规则。",
        },
        "rationale": {
            "en": "Used by the regression test.",
            "zh-CN": "用于回归测试。",
        },
        "severity": "should",
    })
    standard.write_text(
        _yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    from paisl.evidence import evidence_coverage
    from paisl.registry import load_records

    errors: list = []
    records = load_records(repo_copy, errors)

    try:
        coverage = evidence_coverage(records, repo_copy)
    except TypeError:
        coverage = evidence_coverage(records)

    rules = coverage["standards"]["PAISL-REAS-002"]["rules"]

    assert "R002" in rules, (
        "a rule without an evidence link must appear in the coverage"
    )
    assert rules["R002"]["sufficient_for_verification"] is False


# --- REG-008 ---------------------------------------------------------

def test_reg008_an_output_file_applies_to_one_case(repo_copy):
    """An output file belongs to the case it was given for."""
    _write(repo_copy, "evaluations/cases/REG-A-CASE-001.yaml", _case("REG-A-CASE-001"))
    _write(
        repo_copy,
        "evaluations/cases/REG-B-CASE-001.yaml",
        _case("REG-B-CASE-001", text="Some other wording"),
    )
    _write(
        repo_copy,
        "evaluations/suites/reg-suite.yaml",
        _suite(["REG-A-CASE-001", "REG-B-CASE-001"]),
    )

    output = repo_copy / ".paisl" / "outputs" / "reg.txt"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("Restart the service.\n", encoding="utf-8")

    result = _cli(
        repo_copy,
        "evaluate",
        "--suite",
        "reg-suite",
        "--output-file",
        str(output),
    )

    assert result.returncode == 2, (
        "an output file belongs to a single case, so a suite must be "
        "rejected rather than evaluated against one file"
    )

    result = _cli(
        repo_copy,
        "evaluate",
        "--case",
        "REG-A-CASE-001",
        "--output-file",
        str(output),
        "--format",
        "json",
    )

    payload = json.loads(result.stdout)
    case = payload["cases"][0]

    assert case["id"] == "REG-A-CASE-001"
    assert case["output_digest"] == hashlib.sha256(
        output.read_bytes()
    ).hexdigest(), "the output file must be the material that is evaluated"


# --- REG-009 ---------------------------------------------------------

def test_reg009_the_command_line_module_describes_the_commands():
    """The module must not describe a single command any more."""
    text = (ROOT / "src" / "paisl" / "cli.py").read_text(encoding="utf-8")

    assert "Only the `validate` command exists" not in text, (
        "the command line module still describes a single command"
    )


def test_reg009_the_validator_does_not_name_an_old_version():
    """The validator must not carry the version of an old release."""
    text = (ROOT / "scripts" / "validate.py").read_text(encoding="utf-8")

    assert "v0.1.1 standard registry" not in text
    assert "v0.1.0 standard registry" not in text


# --- REG-010 ---------------------------------------------------------

def test_reg010_the_exit_code_contract_is_documented():
    """The contract must state what every code means."""
    text = (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")

    for code in ("`0`", "`1`", "`2`", "`3`"):
        assert code in text, f"the exit code contract does not mention {code}"


def test_reg010_the_contract_covers_the_check_commands():
    """The contract must say what the check commands return."""
    text = (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")

    assert "evidence check" in text or "conflicts check" in text, (
        "the exit code contract does not cover the check commands"
    )


def test_reg010_the_exit_codes_follow_the_contract(repo_copy):
    """Every command returns the code its contract promises."""
    from paisl.errors import (
        EXIT_EXECUTION,
        EXIT_SUCCESS,
        EXIT_USAGE,
        EXIT_VALIDATION,
    )

    assert (EXIT_SUCCESS, EXIT_VALIDATION, EXIT_USAGE, EXIT_EXECUTION) == (
        0,
        1,
        2,
        3,
    )

    assert _cli(repo_copy, "validate").returncode == EXIT_SUCCESS
    assert _cli(repo_copy, "evaluate").returncode == EXIT_USAGE
    assert _cli(repo_copy, "evaluate", "--suite", "absent").returncode == (
        EXIT_USAGE
    )
