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
