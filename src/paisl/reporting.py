# SPDX-License-Identifier: MIT
"""Report rendering.

The text renderer reproduces the output of the v0.1.x validator
byte for byte, so the compatibility wrapper keeps working unchanged.
"""

from __future__ import annotations

import io
import json

REPORT_SCHEMA_VERSION = "0.2.0"


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
