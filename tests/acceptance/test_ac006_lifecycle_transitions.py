# SPDX-License-Identifier: MIT
"""AC-006, AC-007 and AC-008 — the lifecycle acceptance criteria.

AC-006: illegal transitions are rejected.
AC-007: modified Standard content invalidates the old review digest.
AC-008: missing mandatory gates prevent a verified promotion.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import records

STANDARD = "PAISL-ENG-001"
STANDARD_PATH = "standards/engineering/owasp-asvs.yaml"


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


def _digest(repo) -> str:
    path = repo / STANDARD_PATH
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_review(repo, data: dict) -> None:
    path = repo / "governance" / "reviews" / "REV-0002.yaml"
    path.write_text(
        "\n".join(
            [
                "# SPDX-License-Identifier: CC-BY-4.0",
                f"id: {data['id']}",
                f'schema_version: "{data["schema_version"]}"',
                f"standard_id: {data['standard_id']}",
                f'standard_version: "{data["standard_version"]}"',
                f"from_status: {data['from_status']}",
                f"to_status: {data['to_status']}",
                f'reviewed_content_sha256: "{data["reviewed_content_sha256"]}"',
                f'reviewer: "{data["reviewer"]}"',
                f'reviewed_at: "{data["reviewed_at"]}"',
                f"decision: {data['decision']}",
                f"rationale: {data['rationale']}",
                "evidence_ids: []",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _review(from_status: str, to_status: str, decision: str = "approved"):
    return {
        "id": "REV-0002",
        "schema_version": "0.2.0",
        "standard_id": STANDARD,
        "standard_version": "0.1.0",
        "from_status": from_status,
        "to_status": to_status,
        "reviewed_content_sha256": "",
        "reviewer": "reviewer-id",
        "reviewed_at": "2026-11-21T12:00:00Z",
        "decision": decision,
        "rationale": "Reviewed for the acceptance test.",
    }


def test_ac006_illegal_transition_is_rejected(repo_copy):
    """A draft may not jump straight to verified."""
    data = _review("draft", "verified")
    data["reviewed_content_sha256"] = _digest(repo_copy)
    _write_review(repo_copy, data)

    result = _cli(repo_copy, "validate")

    assert result.returncode == 1
    assert "illegal transition draft -> verified" in result.stdout


def test_ac006_legal_transition_is_accepted(repo_copy):
    """A draft may enter review."""
    data = _review("draft", "review")
    data["reviewed_content_sha256"] = _digest(repo_copy)
    _write_review(repo_copy, data)

    result = _cli(repo_copy, "validate")

    assert result.returncode == 0, result.stdout
    assert "illegal transition" not in result.stdout


def test_ac007_changed_content_invalidates_the_review(repo_copy):
    """Changing the Standard content invalidates the old digest."""
    records.review(repo_copy, "REV-0002")
    path = repo_copy / STANDARD_PATH
    text = path.read_text(encoding="utf-8")
    path.write_text(text + "\n# a later edit\n", encoding="utf-8")

    result = _cli(repo_copy, "validate")

    assert result.returncode == 1
    assert "the reviewed content digest does not match" in result.stdout
    assert "changed but its version stayed 0.1.0" in result.stdout


def test_ac007_version_update_keeps_the_record_consistent(repo_copy):
    """A content change with a version change is reported, not fatal."""
    records.review(repo_copy, "REV-0002")
    path = repo_copy / STANDARD_PATH
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("\nversion: 0.1.0\n", "\nversion: 0.2.0\n")
        + "\n# a later edit\n",
        encoding="utf-8",
    )

    result = _cli(repo_copy, "validate")

    assert "changed but its version stayed" not in result.stdout
    assert "the reviewed content digest does not match" in result.stdout


def test_ac008_verified_promotion_needs_every_gate(repo_copy):
    """A Standard that claims verified must clear the gates."""
    path = repo_copy / STANDARD_PATH
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("status: draft", "status: verified"), encoding="utf-8")

    result = _cli(repo_copy, "validate")

    assert result.returncode == 1
    assert "does not clear the gate" in result.stdout


def test_ac008_gates_are_reported(repo_copy):
    """The governance report lists every gate of a Standard."""
    result = _cli(repo_copy, "governance", "check", "--format", "json")

    assert result.returncode == 0

    payload = json.loads(result.stdout)
    gates = payload["governance"]["standards"][STANDARD]["gates"]

    assert [gate["name"] for gate in gates] == [
        "valid-standard-yaml",
        "current-bilingual-review",
        "reviewed-evidence-coverage",
        "no-blocking-conflicts",
        "mandatory-evaluation-cases",
        "approved-review-record",
        "repository-authorization",
    ]

    authorization = [
        gate for gate in gates
        if gate["name"] == "repository-authorization"
    ][0]

    assert authorization["status"] == "enforced externally"
