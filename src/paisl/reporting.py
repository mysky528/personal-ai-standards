# SPDX-License-Identifier: MIT
"""Report rendering.

The text renderer reproduces the output of the v0.1.x validator
byte for byte, so the compatibility wrapper keeps working unchanged.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from .coverage import build_coverage
from .registry import (
    build_standard_index,
    load_catalog,
    load_records,
)

REPORT_SCHEMA_VERSION = "0.2.0"
QUALITY_REPORT_VERSION = "0.2.0"


def render_text_report(
    errors: list,
    warnings: list,
    standards_checked: int,
    skills_checked: int,
    strict: bool = False,
) -> str:
    """Render the validation report in the legacy text format."""
    out = io.StringIO()

    print("\n=== PAISL Validation Report ===", file=out)
    print(f"Standards checked: {standards_checked}", file=out)
    print(f"Skills checked: {skills_checked}", file=out)
    print(f"Errors: {len(errors)}", file=out)
    print(f"Warnings: {len(warnings)}", file=out)

    for message in errors:
        print(f"ERROR: {message}", file=out)

    for message in warnings:
        print(f"WARNING: {message}", file=out)

    if errors or (strict and warnings):
        print("\nValidation FAILED", file=out)
    else:
        print("\nValidation PASSED", file=out)

    return out.getvalue()


def render_json_report(
    errors: list,
    warnings: list,
    standards_checked: int,
    skills_checked: int,
    strict: bool = False,
) -> str:
    """Render the validation report as JSON."""
    failed = bool(errors) or (strict and bool(warnings))

    payload = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": "failed" if failed else "passed",
        "standards_checked": standards_checked,
        "skills_checked": skills_checked,
        "errors": list(errors),
        "warnings": list(warnings),
    }

    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _render_list(out, label: str, values: list) -> None:
    if not values:
        print(f"  {label}: none", file=out)
        return

    print(f"  {label}: {len(values)}", file=out)

    for value in values:
        print(f"    - {value}", file=out)


def render_coverage_text(coverage: dict) -> str:
    """Render the coverage report in the text format."""
    out = io.StringIO()
    standards = coverage["standards"]
    skills = coverage["skills"]
    evidence = coverage["evidence"]
    conflicts = coverage["conflicts"]

    print("\n=== PAISL Coverage Report ===", file=out)
    print(f"Standards: {standards['total']}", file=out)
    _render_list(
        out,
        "without Skill references",
        standards["without_skill_references"],
    )
    _render_list(
        out,
        "without evidence links",
        standards["without_evidence_links"],
    )
    _render_list(
        out,
        "without evaluation cases",
        standards["without_evaluation_cases"],
    )
    _render_list(
        out,
        "without lifecycle review",
        standards["without_lifecycle_review"],
    )
    _render_list(
        out,
        "without semantic review",
        standards["without_semantic_review"],
    )
    print(f"Skills: {skills['total']}", file=out)
    _render_list(
        out,
        "without standard references",
        skills["without_standard_references"],
    )
    print(f"Evidence records: {evidence['total']}", file=out)
    _render_list(out, "unlinked", evidence["unlinked"])
    print(f"Conflict records: {conflicts['total']}", file=out)
    _render_list(
        out,
        "unresolved confirmed blocking",
        conflicts["unresolved_confirmed_blocking"],
    )

    return out.getvalue()


def render_coverage_json(coverage: dict) -> str:
    """Render the coverage report as JSON."""
    payload = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "coverage": coverage,
    }

    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render_evidence_text(coverage: dict) -> str:
    """Render the evidence report in the text format."""
    out = io.StringIO()
    summary = coverage["summary"]

    print("\n=== PAISL Evidence Report ===", file=out)
    print(f"Standards with evidence links: {summary['standards_with_links']}", file=out)
    print(f"Rules with links: {summary['rules_total']}", file=out)
    print(
        "Rules with reviewed supporting evidence: "
        f"{summary['rules_with_reviewed_support']}",
        file=out,
    )

    for standard_id, standard in sorted(coverage["standards"].items()):
        print(f"  {standard_id}", file=out)

        for rule_id, rule in sorted(standard["rules"].items()):
            flags = []

            if rule["contradicting"]:
                flags.append("contradicting")

            if not rule["sufficient_for_verification"]:
                flags.append("not sufficient for verification")

            suffix = f" ({', '.join(flags)})" if flags else ""

            print(
                f"    {rule_id}: supporting={rule['supporting']} "
                f"reviewed={rule['reviewed_supporting']} "
                f"context={rule['context']} "
                f"contradicting={rule['contradicting']}{suffix}",
                file=out,
            )

    return out.getvalue()


def render_evidence_json(coverage: dict) -> str:
    """Render the evidence report as JSON."""
    payload = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "evidence": coverage,
    }

    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


_GATE_MARKERS = {
    "satisfied": "ok",
    "not satisfied": "MISSING",
    "enforced externally": "external",
}


def render_conflicts_text(report: dict) -> str:
    """Render the conflict report in the text format."""
    out = io.StringIO()

    print("\n=== PAISL Conflict Report ===", file=out)

    print(f"Declared conflicts: {report['declared']['total']}", file=out)

    for conflict in report["declared"]["conflicts"]:
        print(
            f"  {conflict['id']} ({conflict['classification']}, "
            f"{conflict['status']}): {conflict['rules']}",
            file=out,
        )

    print(
        "  confirmed and blocking: "
        f"{len(report['declared']['unresolved_confirmed_blocking'])}",
        file=out,
    )

    print(f"Candidate conflicts: {len(report['candidates'])}", file=out)

    for candidate in report["candidates"]:
        print(
            f"  {candidate['first']} <-> {candidate['second']}: "
            f"{'; '.join(candidate['signals'])}",
            file=out,
        )

    if report["candidates"]:
        print(
            "  A candidate is a pair of rules that look alike. It is not "
            "a contradiction and needs a human review.",
            file=out,
        )

    print(f"Bilingual semantic reviews: {report['semantic_reviews']['total']}", file=out)
    print(f"  stale: {len(report['semantic_reviews']['stale'])}", file=out)

    for stale in report["semantic_reviews"]["stale"]:
        print(f"    - {stale}", file=out)

    coverage = report["bilingual_evaluation"]
    print(
        f"Rules with an evaluation case: {coverage['rules_with_cases']} "
        f"({len(coverage['rules_with_both_languages'])} in both languages)",
        file=out,
    )

    return out.getvalue()


def render_conflicts_json(report: dict) -> str:
    """Render the conflict report as JSON."""
    payload = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "conflicts": report,
    }

    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render_governance_text(governance: dict, show_all: bool = False) -> str:
    """Render the governance report in the text format.

    By default only the Standards that left `draft` are listed,
    because the gates describe a promotion. The JSON report always
    holds every Standard.
    """
    out = io.StringIO()

    print("\n=== PAISL Governance Report ===", file=out)

    for status, count in sorted(governance["status_counts"].items()):
        print(f"Standards in {status}: {count}", file=out)

    print(f"Review records: {governance['review_records']['total']}", file=out)
    print(f"  approved: {governance['review_records']['approved']}", file=out)
    print(f"  rejected: {governance['review_records']['rejected']}", file=out)
    print(f"Semantic reviews: {governance['semantic_reviews']['total']}", file=out)

    listed = 0

    for sid, standard in sorted(governance["standards"].items()):
        if not show_all and standard["status"] == "draft":
            continue

        listed += 1
        print(f"  Promotion gates for {sid} ({standard['status']})", file=out)

        for gate in standard["gates"]:
            marker = _GATE_MARKERS.get(gate["status"], gate["status"])
            print(f"    [{marker}] {gate['name']}: {gate['detail']}", file=out)

    if not listed:
        print(
            "  No Standard is in the promotion path. Use --all to list "
            "every Standard.",
            file=out,
        )

    return out.getvalue()


def render_governance_json(governance: dict) -> str:
    """Render the governance report as JSON."""
    payload = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "governance": governance,
    }

    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def build_quality_report(
    root: Path,
    validation: dict | None = None,
    evaluation=None,
) -> dict:
    """Gather the quality of the repository into one report.

    The caller passes the outcome of the validation and of the
    evaluation, so that the report never runs them a second time.
    """
    from .conflicts import (
        bilingual_evaluation_coverage,
        conflict_candidates,
    )
    from .evidence import evidence_coverage

    catalog = load_catalog(root)
    errors: list = []
    records = load_records(root, errors)
    standard_index = build_standard_index(root, catalog)

    schema = json.loads(
        (root / "schemas" / "standard.schema.json").read_text(
            encoding="utf-8"
        )
    )

    coverage = build_coverage(root, schema, catalog, records)
    evidence = evidence_coverage(records, root)

    if validation is None:
        validation = {
            "status": "unknown",
            "standards_checked": 0,
            "skills_checked": 0,
            "errors": 0,
            "warnings": 0,
            "findings": [],
        }

    conflicts = [record for record in records if record.kind == "conflict"]
    blocking = [
        record.relative
        for record in conflicts
        if record.data.get("classification") == "confirmed"
        and record.data.get("status") == "open"
    ]

    reviews = [record for record in records if record.kind == "review"]
    semantic = [
        record for record in records if record.kind == "semantic-review"
    ]

    evaluation_state = {
        "suite_id": "",
        "run_id": "",
        "input_digest": "",
        "pass": 0,
        "fail": 0,
        "skip": 0,
        "error": 0,
    }

    if evaluation is not None:
        evaluation_state = {
            "suite_id": evaluation.suite_id,
            "run_id": evaluation.run_id,
            "input_digest": evaluation.input_digest,
            "pass": evaluation.summary.get("pass", 0),
            "fail": evaluation.summary.get("fail", 0),
            "skip": evaluation.summary.get("skip", 0),
            "error": evaluation.summary.get("error", 0),
        }

    return {
        "report_version": QUALITY_REPORT_VERSION,
        "validation": validation,
        "evidence": {
            "standards_with_links": evidence["summary"][
                "standards_with_links"
            ],
            "rules_total": evidence["summary"]["rules_total"],
            "rules_with_reviewed_support": evidence["summary"][
                "rules_with_reviewed_support"
            ],
        },
        "skill_coverage": {
            "total": coverage["skills"]["total"],
            "with_standard_references": coverage["skills"][
                "with_standard_references"
            ],
            "without_standard_references": coverage["skills"][
                "without_standard_references"
            ],
            "standards_without_skill_references": coverage["standards"][
                "without_skill_references"
            ],
        },
        "evaluation": evaluation_state,
        "conflicts": {
            "declared": len(conflicts),
            "unresolved_confirmed_blocking": blocking,
            "candidates": len(conflict_candidates(root, standard_index)),
        },
        "lifecycle": {
            "status_counts": coverage.get("status_counts", {}),
            "review_records": len(reviews),
            "semantic_reviews": len(semantic),
        },
        "reproducibility": {
            "evaluator_version": (
                evaluation.evaluator_version if evaluation else ""
            ),
            "run_id": evaluation_state["run_id"],
            "input_digest": evaluation_state["input_digest"],
        },
        "bilingual_evaluation": bilingual_evaluation_coverage(root, records),
    }


def render_quality_markdown(report: dict) -> str:
    """Render the quality report as Markdown."""
    lines: list = []

    lines.append("# PAISL Quality Report")
    lines.append("")
    lines.append(f"- Report version: `{report['report_version']}`")

    validation = report["validation"]
    lines.append(
        f"- Validation: **{validation['status']}** "
        f"({validation['errors']} errors, {validation['warnings']} warnings, "
        f"{validation['standards_checked']} standards, "
        f"{validation['skills_checked']} skills)"
    )

    evidence = report["evidence"]
    lines.append(
        f"- Evidence: {evidence['rules_with_reviewed_support']} of "
        f"{evidence['rules_total']} rules have reviewed supporting evidence"
    )

    skill = report["skill_coverage"]
    lines.append(
        f"- Skill coverage: {skill['with_standard_references']} of "
        f"{skill['total']} skills refer to a standard"
    )

    evaluation = report["evaluation"]
    lines.append(
        f"- Evaluation: {evaluation['pass']} passed, {evaluation['fail']} "
        f"failed, {evaluation['skip']} skipped, {evaluation['error']} errored"
    )

    conflicts = report["conflicts"]
    lines.append(
        f"- Conflicts: {conflicts['declared']} declared, "
        f"{len(conflicts['unresolved_confirmed_blocking'])} confirmed and "
        f"blocking, {conflicts['candidates']} candidates"
    )

    lifecycle = report["lifecycle"]
    lines.append(
        f"- Lifecycle: {lifecycle['review_records']} review records, "
        f"{lifecycle['semantic_reviews']} semantic reviews"
    )

    reproducibility = report["reproducibility"]
    lines.append(
        f"- Reproducibility: run `{reproducibility['run_id']}`, "
        f"input digest `{reproducibility['input_digest']}`"
    )

    lines.append("")

    if validation["findings"]:
        lines.append("## Findings")
        lines.append("")

        for finding in validation["findings"]:
            lines.append(f"- {finding}")

        lines.append("")

    return "\n".join(lines) + "\n"


def render_quality_json(report: dict) -> str:
    """Render the quality report as JSON."""
    return json.dumps(
        report, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"


def render_quality_text(report: dict) -> str:
    """Render the quality report in the text format."""
    out = io.StringIO()
    validation = report["validation"]

    print("", file=out)
    print("=== PAISL Quality Report ===", file=out)
    print(f"Validation: {validation['status']}", file=out)
    print(
        f"  standards: {validation['standards_checked']}  "
        f"skills: {validation['skills_checked']}  "
        f"errors: {validation['errors']}  "
        f"warnings: {validation['warnings']}",
        file=out,
    )

    evidence = report["evidence"]
    print(
        f"Evidence: {evidence['rules_with_reviewed_support']} of "
        f"{evidence['rules_total']} rules have reviewed supporting evidence",
        file=out,
    )

    skill = report["skill_coverage"]
    print(
        f"Skill coverage: {skill['with_standard_references']} of "
        f"{skill['total']} skills refer to a standard",
        file=out,
    )

    evaluation = report["evaluation"]
    print(
        f"Evaluation: {evaluation['pass']} passed, {evaluation['fail']} "
        f"failed, {evaluation['skip']} skipped, {evaluation['error']} errored",
        file=out,
    )

    conflicts = report["conflicts"]
    print(
        f"Conflicts: {conflicts['declared']} declared, "
        f"{len(conflicts['unresolved_confirmed_blocking'])} confirmed and "
        f"blocking, {conflicts['candidates']} candidates",
        file=out,
    )

    lifecycle = report["lifecycle"]
    print(
        f"Lifecycle: {lifecycle['review_records']} review records, "
        f"{lifecycle['semantic_reviews']} semantic reviews",
        file=out,
    )

    reproducibility = report["reproducibility"]
    print(
        f"Reproducibility: run {reproducibility['run_id']}, "
        f"input digest {reproducibility['input_digest']}",
        file=out,
    )

    return out.getvalue()


def _case_map(report: dict) -> dict:
    """Map every case of a report to its assertions and status."""
    mapping = {}

    for case in report.get("cases", []):
        mapping[case["id"]] = {
            "status": case.get("status"),
            "assertions": sorted(
                item.get("id", "") for item in case.get("assertions", [])
            ),
        }

    return mapping


def compare_evaluation_results(baseline: dict, current: dict) -> dict:
    """Compare two evaluation reports.

    The two reports must describe the same evaluation. When they do
    not, the comparison states why instead of pretending that the
    results mean the same thing.

    A report that was written before the definition digest existed
    does not carry one, and the comparison does not claim that the
    definitions are the same because it cannot know.
    """
    reasons: list = []

    if baseline.get("suite_id") != current.get("suite_id"):
        reasons.append(
            f"the suite differs: {baseline.get('suite_id')} and "
            f"{current.get('suite_id')}"
        )

    baseline_definition = baseline.get("definition_digest")
    current_definition = current.get("definition_digest")

    if baseline_definition and current_definition:
        if baseline_definition != current_definition:
            reasons.append(
                "the evaluation definition changed: the cases, their "
                "assertions, or the suite itself differ, so the results "
                "do not describe the same evaluation"
            )

    baseline_cases = _case_map(baseline)
    current_cases = _case_map(current)

    for case_id in sorted(set(baseline_cases) & set(current_cases)):
        first = baseline_cases[case_id]["assertions"]
        second = current_cases[case_id]["assertions"]

        if first != second:
            reasons.append(
                f"the definition of {case_id} changed: {first} and {second}"
            )

    if reasons:
        return {
            "compatible": False,
            "reasons": reasons,
            "newly_failing": [],
            "resolved": [],
            "still_failing": [],
            "added_cases": [],
            "removed_cases": [],
            "evaluator_version": {
                "from": baseline.get("evaluator_version"),
                "to": current.get("evaluator_version"),
            },
        }

    newly_failing = []
    resolved = []
    still_failing = []

    for case_id in sorted(set(baseline_cases) & set(current_cases)):
        first = baseline_cases[case_id]["status"]
        second = current_cases[case_id]["status"]

        if first != "fail" and second == "fail":
            newly_failing.append(case_id)
        elif first == "fail" and second != "fail":
            resolved.append(case_id)
        elif second == "fail":
            still_failing.append(case_id)

    added = sorted(set(current_cases) - set(baseline_cases))
    removed = sorted(set(baseline_cases) - set(current_cases))

    return {
        "compatible": True,
        "reasons": [],
        "newly_failing": newly_failing,
        "resolved": resolved,
        "still_failing": still_failing,
        "added_cases": added,
        "removed_cases": removed,
        "evaluator_version": {
            "from": baseline.get("evaluator_version"),
            "to": current.get("evaluator_version"),
        },
    }


def render_comparison_text(comparison: dict) -> str:
    """Render a regression comparison in the text format."""
    lines: list = []

    lines.append("")
    lines.append("=== PAISL Regression Comparison ===")

    if not comparison["compatible"]:
        lines.append("The two reports do not describe the same evaluation:")
        lines.append("")

        for reason in comparison["reasons"]:
            lines.append(f"  - {reason}")

        return "\n".join(lines) + "\n"

    versions = comparison["evaluator_version"]

    if versions["from"] != versions["to"]:
        lines.append(
            f"Evaluator version changed: {versions['from']} -> {versions['to']}"
        )

    lines.append(f"Newly failing cases: {len(comparison['newly_failing'])}")

    for case_id in comparison["newly_failing"]:
        lines.append(f"  - {case_id}")

    lines.append(f"Resolved failures: {len(comparison['resolved'])}")

    for case_id in comparison["resolved"]:
        lines.append(f"  - {case_id}")

    lines.append(f"Still failing: {len(comparison['still_failing'])}")

    for case_id in comparison["still_failing"]:
        lines.append(f"  - {case_id}")

    lines.append(f"Added cases: {len(comparison['added_cases'])}")

    for case_id in comparison["added_cases"]:
        lines.append(f"  - {case_id}")

    lines.append(f"Removed cases: {len(comparison['removed_cases'])}")

    for case_id in comparison["removed_cases"]:
        lines.append(f"  - {case_id}")

    return "\n".join(lines) + "\n"


def render_comparison_json(comparison: dict) -> str:
    """Render a regression comparison as JSON."""
    return json.dumps(
        comparison, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
