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
