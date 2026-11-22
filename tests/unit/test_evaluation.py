# SPDX-License-Identifier: MIT
"""The evaluation engine.

The engine must give the same answer every time, must never leak the
material it evaluated, and must not let a skipped mandatory
assertion pass.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from paisl.evaluation import (
    evaluate_case,
    redact,
    render_evaluation_json,
    render_evaluation_markdown,
    resolve_fixture,
    run_suite,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _suite() -> dict:
    return {
        "id": "core-regression",
        "version": "0.2.0",
        "cases": ["COMM-001-CASE-001"],
    }


def _case() -> dict:
    return {
        "id": "COMM-001-CASE-001",
        "schema_version": "0.2.0",
        "standard_id": "PAISL-COMM-001",
        "rule_ids": ["R001"],
        "title": "Explicit action instruction",
        "fixture": {
            "input": "evaluations/fixtures/comm-001-input.txt",
            "output": "evaluations/fixtures/comm-001-output.txt",
        },
        "assertions": [
            {
                "id": "A001",
                "evaluator": "contains",
                "params": {"text": "Restart the service"},
                "severity": "must",
            },
            {
                "id": "A002",
                "evaluator": "excludes",
                "params": {"text": "maybe restart"},
                "severity": "should",
            },
        ],
    }


def test_reference_case_passes(repo_root):
    """The reference case passes against its own fixture."""
    result = evaluate_case(repo_root, _case())

    assert result.status == "pass"
    assert len(result.assertions) == 2


def test_the_report_is_reproducible(repo_root):
    """Two runs of the same suite give the same report."""
    first = run_suite(repo_root, _suite(), [_case()])
    second = run_suite(repo_root, _suite(), [_case()])

    assert first.as_dict() == second.as_dict()
    assert first.run_id == second.run_id
    assert first.input_digest == second.input_digest


def test_the_report_holds_no_unstable_field(repo_root):
    """The report has no timestamp, no random identifier, no absolute path."""
    result = run_suite(repo_root, _suite(), [_case()])
    payload = json.loads(render_evaluation_json(result))
    text = json.dumps(payload)

    assert str(ROOT) not in text
    assert "timestamp" not in text
    assert "generated_at" not in text

    # The run identifier is derived from the content, not random.
    assert payload["run_id"] == result.run_id
    assert len(payload["run_id"]) == 32


def test_a_skipped_mandatory_assertion_does_not_pass(repo_root):
    """A skipped case never counts as a pass."""
    result = run_suite(
        repo_root,
        _suite(),
        [_case()],
        skip_cases=("COMM-001-CASE-001",),
    )

    assert result.summary["skip"] == 1
    assert result.summary["pass"] == 0
    assert result.passed is False


def test_an_unknown_evaluator_produces_an_error(repo_root):
    """A case cannot select an evaluator that is not allowed."""
    case = _case()
    case["assertions"][0]["evaluator"] = "execute_python"

    result = evaluate_case(repo_root, case)

    assert result.status == "error"
    assert "not allowed" in result.assertions[0].message


def test_the_report_redacts_a_secret(repo_root):
    """The report never carries a value that looks like a credential."""
    case = _case()
    case["fixture"]["output"] = "evaluations/fixtures/comm-001-output.txt"

    output = (
        "Restart the service.\n"
        "export API_KEY=ghp_abcdefghijklmnopqrstuvwxyz012345\n"
    )

    result = evaluate_case(repo_root, case, output_text=output)

    assert "ghp_abcdefghijklmnopqrstuvwxyz012345" not in result.output_excerpt
    assert "[redacted]" in result.output_excerpt


def test_redaction_covers_common_shapes():
    """The redaction covers the usual credential shapes."""
    assert "ghp_" not in redact("token ghp_abcdefghijklmnopqrstuvwxyz01")
    assert "sk-" not in redact("key sk-abcdefghijklmnopqrstuvwxyz")
    assert "secret" not in redact("secret = hunter2").lower()


def test_a_fixture_outside_the_repository_is_not_read(repo_root):
    """A fixture that leaves the repository is never resolved."""
    assert resolve_fixture(repo_root, "../outside.txt") is None
    assert resolve_fixture(repo_root, "evaluations/fixtures/absent.txt") is None
    assert resolve_fixture(
        repo_root, "evaluations/fixtures/comm-001-input.txt"
    ) is not None


def test_the_report_has_a_markdown_form(repo_root):
    """The result can be read as Markdown."""
    result = run_suite(repo_root, _suite(), [_case()])
    markdown = render_evaluation_markdown(result)

    assert "# PAISL Evaluation Report" in markdown
    assert "COMM-001-CASE-001" in markdown


def test_the_report_has_a_json_form(repo_root):
    """The result can be read as JSON."""
    result = run_suite(repo_root, _suite(), [_case()])
    payload = json.loads(render_evaluation_json(result))

    assert payload["suite_id"] == "core-regression"
    assert payload["status"] == "passed"
    assert payload["summary"] == {
        "pass": 1, "fail": 0, "skip": 0, "error": 0,
    }
    assert payload["cases"][0]["output_digest"]
