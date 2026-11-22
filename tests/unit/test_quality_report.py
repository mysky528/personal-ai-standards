# SPDX-License-Identifier: MIT
"""The quality report and the regression comparison."""

from __future__ import annotations

import json
import pathlib

import pytest

from paisl.evaluation import run_suite
from paisl.registry import load_records
from paisl.reporting import (
    build_quality_report,
    compare_evaluation_results,
    render_comparison_json,
    render_quality_json,
    render_quality_markdown,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _report(root: pathlib.Path) -> dict:
    errors: list = []
    records = load_records(root, errors)
    assert not errors, errors

    suite = {
        "id": "core-regression",
        "version": "0.2.0",
        "cases": ["COMM-001-CASE-001"],
    }
    case = next(
        record.data
        for record in records
        if record.kind == "evaluation-case"
    )

    evaluation = run_suite(root, suite, [case])

    return build_quality_report(
        root,
        {
            "status": "passed",
            "standards_checked": 12,
            "skills_checked": 7,
            "errors": 0,
            "warnings": 0,
            "findings": [],
        },
        evaluation,
    )


def test_the_quality_report_covers_every_required_measure(repo_root):
    """The report holds every measure the acceptance criteria ask for."""
    report = _report(repo_root)

    assert "validation" in report
    assert "evidence" in report
    assert "skill_coverage" in report
    assert "evaluation" in report
    assert "conflicts" in report
    assert "lifecycle" in report
    assert "reproducibility" in report


def test_the_quality_report_has_json_and_markdown(repo_root):
    """The report can be read as JSON and as Markdown."""
    report = _report(repo_root)

    payload = json.loads(render_quality_json(report))
    markdown = render_quality_markdown(report)

    assert payload["validation"]["status"] == "passed"
    assert "# PAISL Quality Report" in markdown
    assert "Reproducibility" in markdown


def _evaluation_report(**overrides) -> dict:
    report = {
        "suite_id": "core-regression",
        "suite_version": "0.2.0",
        "evaluator_version": "0.2.0",
        "cases": [
            {
                "id": "COMM-001-CASE-001",
                "status": "pass",
                "assertions": [{"id": "A001"}, {"id": "A002"}],
            }
        ],
    }
    report.update(overrides)
    return report


def test_two_identical_reports_show_no_difference():
    """An unchanged evaluation shows nothing new."""
    comparison = compare_evaluation_results(
        _evaluation_report(), _evaluation_report()
    )

    assert comparison["compatible"] is True
    assert comparison["newly_failing"] == []
    assert comparison["resolved"] == []
    assert comparison["added_cases"] == []
    assert comparison["removed_cases"] == []


def test_a_new_failure_is_reported():
    """A case that started failing is named."""
    baseline = _evaluation_report()
    current = _evaluation_report()
    current["cases"][0]["status"] = "fail"

    comparison = compare_evaluation_results(baseline, current)

    assert comparison["compatible"] is True
    assert comparison["newly_failing"] == ["COMM-001-CASE-001"]


def test_a_resolved_failure_is_reported():
    """A case that started passing is named."""
    baseline = _evaluation_report()
    baseline["cases"][0]["status"] = "fail"
    current = _evaluation_report()

    comparison = compare_evaluation_results(baseline, current)

    assert comparison["resolved"] == ["COMM-001-CASE-001"]


def test_added_and_removed_cases_are_reported():
    """Cases that came or went are named."""
    baseline = _evaluation_report()
    current = _evaluation_report()
    current["cases"].append({
        "id": "COMM-002-CASE-001",
        "status": "pass",
        "assertions": [{"id": "A001"}],
    })

    comparison = compare_evaluation_results(baseline, current)

    assert comparison["added_cases"] == ["COMM-002-CASE-001"]
    assert comparison["removed_cases"] == []


def test_a_changed_evaluator_version_is_reported():
    """A change of the evaluator version is named."""
    comparison = compare_evaluation_results(
        _evaluation_report(evaluator_version="0.2.0"),
        _evaluation_report(evaluator_version="0.3.0"),
    )

    assert comparison["evaluator_version"] == {
        "from": "0.2.0",
        "to": "0.3.0",
    }


def test_a_different_suite_is_not_compared():
    """Two reports of different suites are not compared as equal."""
    comparison = compare_evaluation_results(
        _evaluation_report(),
        _evaluation_report(suite_id="other-suite"),
    )

    assert comparison["compatible"] is False
    assert comparison["reasons"]
    assert comparison["newly_failing"] == []


def test_a_changed_definition_is_not_compared():
    """Two reports that describe different cases are not compared."""
    baseline = _evaluation_report()
    current = _evaluation_report()
    current["cases"][0]["assertions"] = [{"id": "A001"}]

    comparison = compare_evaluation_results(baseline, current)

    assert comparison["compatible"] is False
    assert any(
        "the definition of" in reason for reason in comparison["reasons"]
    )


def test_an_incompatible_comparison_says_so():
    """The rendered comparison states that it does not compare."""
    comparison = compare_evaluation_results(
        _evaluation_report(),
        _evaluation_report(suite_id="other-suite"),
    )

    rendered = render_comparison_json(comparison)

    assert "compatible" in rendered
    assert "reasons" in rendered
