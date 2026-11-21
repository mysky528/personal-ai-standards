# SPDX-License-Identifier: MIT
"""AC-005 — unreviewed evidence cannot satisfy verified evidence coverage.

The acceptance criteria require that a Standard only counts as
supported when the evidence behind it has been reviewed.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


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


def test_unreviewed_evidence_does_not_satisfy_coverage(repo_copy):
    """The reference evidence is unreviewed, so it is not sufficient."""
    result = _cli(repo_copy, "evidence", "check", "--format", "json")

    assert result.returncode == 0

    payload = json.loads(result.stdout)
    standard = payload["evidence"]["standards"]["PAISL-ENG-001"]

    assert standard["rules"]["R001"]["reviewed_supporting"] == 0
    assert standard["sufficient_for_verification"] is False
    assert (
        payload["evidence"]["summary"]["rules_with_reviewed_support"] == 0
    )


def test_reviewed_evidence_satisfies_coverage(repo_copy):
    """A reviewed record makes the rule sufficient."""
    record = repo_copy / "evidence" / "records" / "EVD-0002.yaml"
    record.write_text(
        "\n".join(
            [
                "# SPDX-License-Identifier: CC-BY-4.0",
                "id: EVD-0002",
                'schema_version: "0.2.0"',
                'title: "ASVS requirement catalogue"',
                "source:",
                "  url: https://owasp.org/www-project-application-security-verification-standard/",
                "  type: official",
                "  publisher: OWASP",
                '  retrieved_at: "2026-11-21T12:00:00Z"',
                "  accessed: true",
                "review:",
                "  status: reviewed",
                "  reviewed_by: reviewer-id",
                '  reviewed_at: "2026-11-21T12:00:00Z"',
                "  rationale: Requirement catalogue inspected.",
                "notes: null",
                "",
            ]
        ),
        encoding="utf-8",
    )

    link = repo_copy / "evidence" / "links" / "PAISL-ENG-001.yaml"
    text = link.read_text(encoding="utf-8")
    link.write_text(
        text.replace(
            "        note: >-",
            "      - evidence_id: EVD-0002\n"
            "        relationship: supports\n"
            '        locator: "Requirement catalogue"\n'
            "        note: >-",
        ),
        encoding="utf-8",
    )

    result = _cli(repo_copy, "evidence", "check", "--format", "json")

    assert result.returncode == 0, result.stdout

    payload = json.loads(result.stdout)
    standard = payload["evidence"]["standards"]["PAISL-ENG-001"]

    assert standard["rules"]["R001"]["reviewed_supporting"] == 1
    assert standard["sufficient_for_verification"] is True


def test_reviewed_evidence_without_inspection_is_rejected(repo_copy):
    """A reviewed record must document that the source was inspected."""
    record = repo_copy / "evidence" / "records" / "EVD-0001.yaml"
    text = record.read_text(encoding="utf-8")
    record.write_text(
        text.replace("  status: unreviewed", "  status: reviewed")
        .replace(
            "  reviewed_by: null",
            "  reviewed_by: reviewer-id",
        )
        .replace(
            "  reviewed_at: null",
            '  reviewed_at: "2026-11-21T12:00:00Z"',
        )
        .replace(
            "  rationale: null",
            "  rationale: Source inspected.",
        ),
        encoding="utf-8",
    )

    result = _cli(repo_copy, "validate")

    assert result.returncode == 1
    assert "EVD-0001.yaml" in result.stdout
