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
| REG-011 | A suite that named no case was reported as a success, because the counts of failures, errors, and skips were all zero |
| REG-012 | A fixture that exists but cannot be read ended the whole run instead of failing its own case, and the declared output fixture was required even when the caller supplied the output |
| REG-013 | A case that verified nothing counted as a success, and a skipped optional assertion was invisible in the summary |
| REG-014 | The check commands did not run the whole validation of their own domain, so a broken cross reference passed them, while their names suggested an enforcing check |
| REG-015 | The regression comparison did not notice that the evaluation definition changed, and compared two results that did not describe the same evaluation |
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
from paisl.evaluators import ERROR, FAIL, PASS, SKIP
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
    evaluator: str = "contains",
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
                "evaluator": evaluator,
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


# --- REG-011 ---------------------------------------------------------

def test_reg011_a_suite_without_cases_is_not_a_pass():
    """A suite that ran nothing does not pass."""
    from paisl.evaluation import SuiteResult

    empty = SuiteResult(
        suite_id="empty",
        suite_version="1",
        evaluator_version="1",
        run_id="",
        input_digest="",
        summary={"pass": 0, "fail": 0, "skip": 0, "error": 0},
        cases=[],
    )

    assert empty.passed is False, (
        "a suite that ran no case must not report a pass"
    )


def test_reg011_an_empty_suite_is_refused(repo_copy):
    """The command refuses a suite that names no case."""
    _write(
        repo_copy,
        "evaluations/suites/empty-suite.yaml",
        {
            "id": "empty-suite",
            "schema_version": "0.2.0",
            "version": "0.2.1",
            "title": {"en": "Empty", "zh-CN": "空"},
            "description": {"en": "No case.", "zh-CN": "没有用例。"},
            "required": False,
            "cases": [],
        },
    )

    result = _cli(repo_copy, "evaluate", "--suite", "empty-suite")

    assert result.returncode == 1, (
        "a suite that names no case must not report a success"
    )
    assert "no case" in result.stdout


def test_reg011_a_suite_with_cases_still_passes(repo_copy):
    """The fix does not turn a real suite into a failure."""
    result = _cli(repo_copy, "evaluate", "--suite", "core-regression")

    assert result.returncode == 0


# --- REG-012 ---------------------------------------------------------

def test_reg012_an_unreadable_fixture_fails_only_its_case(repo_copy):
    """A fixture that cannot be read fails its case, not the run.

    The three problems stay apart: a fixture that is missing, a
    fixture that leaves the repository, and a fixture that exists
    but cannot be read.
    """
    (repo_copy / "evaluations" / "fixtures" / "binary.txt").write_bytes(
        b"\xff\xfe\x00\x01 not text"
    )

    _write(repo_copy, "evaluations/cases/REG-BAD-CASE-001.yaml", _case(
        "REG-BAD-CASE-001",
        output_path="evaluations/fixtures/binary.txt",
    ))
    _write(
        repo_copy,
        "evaluations/suites/reg-suite.yaml",
        _suite(["REG-BAD-CASE-001", "REG-GOOD-CASE-001"]),
    )
    _write(repo_copy, "evaluations/cases/REG-GOOD-CASE-001.yaml", _case(
        "REG-GOOD-CASE-001",
    ))

    result = _cli(
        repo_copy, "evaluate", "--suite", "reg-suite", "--format", "json"
    )

    payload = json.loads(result.stdout)
    cases = {case["id"]: case for case in payload["cases"]}

    assert cases["REG-BAD-CASE-001"]["status"] == ERROR
    assert "could not be read" in (
        cases["REG-BAD-CASE-001"]["assertions"][0]["message"]
    )
    assert cases["REG-GOOD-CASE-001"]["status"] == PASS, (
        "an unreadable fixture must not end the whole run"
    )


def test_reg012_a_missing_fixture_is_not_an_empty_one(repo_copy):
    """A missing fixture never turns into empty content.

    An excludes assertion holds for the empty text, so a missing
    fixture that was read as an empty text would report a pass.
    """
    _write(repo_copy, "evaluations/cases/REG-MISS-CASE-001.yaml", _case(
        "REG-MISS-CASE-001",
        output_path="evaluations/fixtures/absent.txt",
    ))
    _write(
        repo_copy,
        "evaluations/suites/reg-suite.yaml",
        _suite(["REG-MISS-CASE-001"]),
    )

    result = _cli(
        repo_copy, "evaluate", "--suite", "reg-suite", "--format", "json"
    )

    payload = json.loads(result.stdout)
    case = payload["cases"][0]

    assert case["status"] == ERROR
    assert "missing" in case["assertions"][0]["message"]


def test_reg012_an_empty_fixture_is_content(repo_copy):
    """A fixture that exists and is empty is content, not a problem."""
    (repo_copy / "evaluations" / "fixtures" / "empty.txt").write_text(
        "", encoding="utf-8"
    )

    _write(repo_copy, "evaluations/cases/REG-EMPTY-CASE-001.yaml", _case(
        "REG-EMPTY-CASE-001",
        output_path="evaluations/fixtures/empty.txt",
    ))
    _write(
        repo_copy,
        "evaluations/suites/reg-suite.yaml",
        _suite(["REG-EMPTY-CASE-001"]),
    )

    result = _cli(
        repo_copy, "evaluate", "--suite", "reg-suite", "--format", "json"
    )

    payload = json.loads(result.stdout)
    case = payload["cases"][0]

    assert case["status"] == FAIL, (
        "an empty fixture is content, so a contains assertion fails on it "
        "rather than the case being an error"
    )
    assert "could not be read" not in case["assertions"][0]["message"]


def test_reg012_an_empty_fixture_satisfies_an_excludes_assertion(repo_copy):
    """An empty file holds for an excludes assertion.

    This is the reason a missing fixture must not be read as an
    empty text: the difference between the two is the difference
    between a qualified output and an unusable case.
    """
    (repo_copy / "evaluations" / "fixtures" / "empty.txt").write_text(
        "", encoding="utf-8"
    )

    _write(repo_copy, "evaluations/cases/REG-EXCL-CASE-001.yaml", _case(
        "REG-EXCL-CASE-001",
        output_path="evaluations/fixtures/empty.txt",
        text="maybe restart",
        evaluator="excludes",
    ))
    _write(
        repo_copy,
        "evaluations/suites/reg-suite.yaml",
        _suite(["REG-EXCL-CASE-001"]),
    )

    result = _cli(
        repo_copy, "evaluate", "--suite", "reg-suite", "--format", "json"
    )

    payload = json.loads(result.stdout)
    case = payload["cases"][0]

    assert case["status"] == PASS


def test_reg012_a_supplied_output_replaces_the_declared_fixture(repo_copy):
    """The declared output fixture is not required when the caller supplies one."""
    _write(repo_copy, "evaluations/cases/REG-SUP-CASE-001.yaml", _case(
        "REG-SUP-CASE-001",
        output_path="evaluations/fixtures/absent.txt",
    ))

    output = repo_copy / ".paisl" / "outputs" / "supplied.txt"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("Restart the service.\n", encoding="utf-8")

    result = _cli(
        repo_copy,
        "evaluate",
        "--case",
        "REG-SUP-CASE-001",
        "--output-file",
        str(output),
        "--format",
        "json",
    )

    assert result.returncode == 0, result.stdout

    payload = json.loads(result.stdout)
    case = payload["cases"][0]

    assert case["status"] == PASS


# --- REG-013 ---------------------------------------------------------

def test_reg013_a_case_without_assertions_is_not_a_pass():
    """A case that verified nothing is not a pass."""
    from paisl.evaluation import _case_status

    assert _case_status([]) == SKIP, (
        "a case without an assertion must not count as a success"
    )


def test_reg013_a_case_without_assertions_is_refused(repo_copy):
    """The command refuses a case that declares no assertion."""
    case = _case("REG-EMPTY-CASE-001")
    case["assertions"] = []

    _write(repo_copy, "evaluations/cases/REG-EMPTY-CASE-001.yaml", case)
    _write(
        repo_copy,
        "evaluations/suites/reg-suite.yaml",
        _suite(["REG-EMPTY-CASE-001"]),
    )

    result = _cli(repo_copy, "evaluate", "--suite", "reg-suite")

    assert result.returncode == 1, (
        "a case that declares no assertion must not report a success"
    )
    assert "no assertion" in result.stdout


def test_reg013_a_skipped_assertion_is_visible_in_the_summary(repo_copy):
    """A skipped assertion is counted in the summary.

    The case counts stay the four that the design names. The counts
    of the assertions sit beside them, because a skipped optional
    assertion is otherwise invisible.
    """
    case = _case("REG-SKIP-CASE-001")
    case["assertions"] = [
        {
            "id": "A001",
            "evaluator": "contains",
            "params": {"text": "Restart the service"},
            "severity": "must",
        },
        {
            "id": "A002",
            "evaluator": "contains",
            "params": {"text": "never there"},
            "severity": "should",
        },
    ]

    _write(repo_copy, "evaluations/cases/REG-SKIP-CASE-001.yaml", case)
    _write(
        repo_copy,
        "evaluations/suites/reg-suite.yaml",
        _suite(["REG-SKIP-CASE-001"]),
    )

    result = _cli(
        repo_copy, "evaluate", "--suite", "reg-suite", "--format", "json"
    )

    payload = json.loads(result.stdout)

    assert "assertions" in payload["summary"], (
        "the summary must count the assertions, not only the cases"
    )
    assert set(payload["summary"]["assertions"]) == {
        "pass", "fail", "skip", "error",
    }

    # The four case counts that the design names are still there.
    for key in ("pass", "fail", "skip", "error"):
        assert key in payload["summary"]


def test_reg013_a_skipped_case_is_counted(repo_copy):
    """A case that the caller skips is counted as skipped."""
    _write(repo_copy, "evaluations/cases/REG-CASE-001.yaml", _case("REG-CASE-001"))
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


# --- REG-014 ---------------------------------------------------------

def _broken_evidence_link(repo) -> None:
    """Write a link that names a Standard which does not exist."""
    _write(
        repo,
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


def test_reg014_evidence_check_resolves_its_references(repo_copy):
    """The evidence check resolves the references of its own domain."""
    _broken_evidence_link(repo_copy)

    result = _cli(repo_copy, "evidence", "check")

    assert result.returncode == 1, (
        "a reference to a Standard that does not exist must fail the check"
    )
    assert "PAISL-ENG-002" in result.stdout


def test_reg014_governance_check_resolves_its_references(repo_copy):
    """The governance check resolves the references of its own domain."""
    _write(
        repo_copy,
        "governance/reviews/REV-0002.yaml",
        {
            "id": "REV-0002",
            "schema_version": "0.2.0",
            "standard_id": "PAISL-ENG-002",
            "standard_version": "0.1.0",
            "from_status": "draft",
            "to_status": "review",
            "reviewed_content_sha256": "0" * 64,
            "reviewer": "reviewer-id",
            "reviewed_at": "2026-11-21T12:00:00Z",
            "decision": "approved",
            "rationale": "Reviewed.",
            "evidence_ids": [],
        },
    )

    result = _cli(repo_copy, "governance", "check")

    assert result.returncode == 1
    assert "PAISL-ENG-002" in result.stdout


def test_reg014_evaluate_resolves_the_references_of_its_cases(repo_copy):
    """The evaluation refuses a case that names a rule that is absent."""
    _write(repo_copy, "evaluations/cases/REG-REF-CASE-001.yaml", _case(
        "REG-REF-CASE-001",
    ))
    case_path = repo_copy / "evaluations" / "cases" / "REG-REF-CASE-001.yaml"
    data = yaml.safe_load(case_path.read_text(encoding="utf-8"))
    data["rule_ids"] = ["R999"]
    case_path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    _write(
        repo_copy,
        "evaluations/suites/reg-suite.yaml",
        _suite(["REG-REF-CASE-001"]),
    )

    result = _cli(repo_copy, "evaluate", "--suite", "reg-suite")

    assert result.returncode == 1, (
        "a case that names a rule that does not exist must not pass"
    )
    assert "R999" in result.stdout


def test_reg014_the_report_commands_never_fail(repo_copy):
    """The commands that only show a state never fail."""
    _broken_evidence_link(repo_copy)

    for command in (("coverage",), ("report",)):
        result = _cli(repo_copy, *command)

        assert result.returncode == 0, (
            f"{command} only shows a state and must not fail"
        )


# --- REG-015 ---------------------------------------------------------

def _definition_report(repo, text: str) -> dict:
    """Evaluate a case whose assertion expects the given text."""
    case = _case("REG-DEF-CASE-001")
    case["assertions"][0]["params"]["text"] = text

    _write(repo, "evaluations/cases/REG-DEF-CASE-001.yaml", case)
    _write(
        repo,
        "evaluations/suites/reg-suite.yaml",
        _suite(["REG-DEF-CASE-001"]),
    )

    result = _cli(
        repo, "evaluate", "--suite", "reg-suite", "--format", "json"
    )

    return json.loads(result.stdout)


def test_reg015_the_run_identifier_covers_the_assertions(repo_copy):
    """A changed assertion changes the run identifier."""
    first = _definition_report(repo_copy, "Restart the service")
    second = _definition_report(repo_copy, "A completely different text")

    assert first["run_id"] != second["run_id"], (
        "the run identifier must cover the assertions"
    )
    assert first["input_digest"] != second["input_digest"]


def test_reg015_the_report_carries_the_definition_digest(repo_copy):
    """The report states what it evaluated."""
    report = _definition_report(repo_copy, "Restart the service")

    assert report["definition_digest"]
    assert report["cases"][0]["definition_digest"]


def test_reg015_the_comparison_notices_a_changed_definition(repo_copy):
    """Two results that describe different evaluations are not compared."""
    first = _definition_report(repo_copy, "Restart the service")
    second = _definition_report(repo_copy, "A completely different text")

    baseline = repo_copy / "baseline.json"
    current = repo_copy / "current.json"
    baseline.write_text(json.dumps(first), encoding="utf-8")
    current.write_text(json.dumps(second), encoding="utf-8")

    result = _cli(
        repo_copy,
        "compare",
        "--baseline",
        str(baseline),
        "--current",
        str(current),
    )

    assert result.returncode == 1, (
        "two results that do not describe the same evaluation must not "
        "be compared as equal"
    )
    assert "definition changed" in result.stdout


def test_reg015_the_comparison_of_equal_results_still_works(repo_copy):
    """The comparison of two identical results still works."""
    first = _definition_report(repo_copy, "Restart the service")

    baseline = repo_copy / "baseline.json"
    current = repo_copy / "current.json"
    baseline.write_text(json.dumps(first), encoding="utf-8")
    current.write_text(json.dumps(first), encoding="utf-8")

    result = _cli(
        repo_copy,
        "compare",
        "--baseline",
        str(baseline),
        "--current",
        str(current),
    )

    assert result.returncode == 0
    assert "Newly failing cases: 0" in result.stdout
