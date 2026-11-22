# SPDX-License-Identifier: MIT
"""The lifecycle engine.

The engine decides whether a Standard may change status. The checks
that matter most are the negative ones: an illegal transition, a
stale review, and a promotion without the required gates.
"""

from __future__ import annotations

import hashlib
import pathlib
import subprocess

import pytest
import yaml

from paisl.lifecycle import (
    ALLOWED_TRANSITIONS,
    check_review_records,
    check_status_trail,
    check_verified_standards,
    file_digest,
    promotion_gates,
)
from paisl.registry import (
    build_standard_index,
    load_catalog,
    load_records,
)
from paisl.schema_validation import build_validator

ROOT = pathlib.Path(__file__).resolve().parents[2]
STANDARD = "PAISL-ENG-001"
STANDARD_PATH = "standards/engineering/owasp-asvs.yaml"


def _write(path: pathlib.Path, data: dict) -> None:
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _records(root: pathlib.Path) -> list:
    errors: list = []
    records = load_records(root, errors)
    assert not errors, errors
    return records


def _index(root: pathlib.Path) -> dict:
    return build_standard_index(root, load_catalog(root))


def _validator(root: pathlib.Path):
    schema = yaml.safe_load(
        (root / "schemas" / "standard.schema.json").read_text(
            encoding="utf-8"
        )
    )
    return build_validator(schema)


def _review(
    digest: str,
    from_status: str = "draft",
    to_status: str = "review",
    decision: str = "approved",
    standard_version: str = "0.1.0",
) -> dict:
    return {
        "id": "REV-0002",
        "schema_version": "0.2.0",
        "standard_id": STANDARD,
        "standard_version": standard_version,
        "from_status": from_status,
        "to_status": to_status,
        "reviewed_content_sha256": digest,
        "reviewer": "reviewer-id",
        "reviewed_at": "2026-11-21T12:00:00Z",
        "decision": decision,
        "rationale": "Reviewed for the lifecycle test.",
        "evidence_ids": [],
    }


def _write_review(repo: pathlib.Path, data: dict) -> None:
    _write(repo / "governance" / "reviews" / "REV-0002.yaml", data)


def _digest(repo: pathlib.Path) -> str:
    return file_digest(repo / STANDARD_PATH)


def _init_git(repo: pathlib.Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    _commit(repo, "init")


def _commit(repo: pathlib.Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "user.name=test",
            "commit",
            "-qm",
            message,
        ],
        cwd=repo,
        check=True,
    )


def test_allowed_transitions_match_the_design():
    """The transition table must match the technical design."""
    assert ("draft", "review") in ALLOWED_TRANSITIONS
    assert ("review", "draft") in ALLOWED_TRANSITIONS
    assert ("review", "verified") in ALLOWED_TRANSITIONS
    assert ("verified", "review") in ALLOWED_TRANSITIONS
    assert ("verified", "deprecated") in ALLOWED_TRANSITIONS
    assert ("deprecated", "draft") in ALLOWED_TRANSITIONS

    assert ("draft", "verified") not in ALLOWED_TRANSITIONS
    assert ("draft", "deprecated") not in ALLOWED_TRANSITIONS
    assert ("review", "deprecated") not in ALLOWED_TRANSITIONS
    assert ("deprecated", "verified") not in ALLOWED_TRANSITIONS


def test_reference_records_pass_the_lifecycle_checks(repo_root):
    """The reference instances must satisfy the lifecycle rules."""
    errors: list = []
    warnings: list = []

    check_review_records(
        repo_root, _records(repo_root), _index(repo_root), errors, warnings
    )
    check_status_trail(repo_root, _records(repo_root), _index(repo_root), errors)

    assert not errors
    assert not warnings


def test_illegal_transition_is_rejected(repo_copy):
    """A draft may not jump straight to verified."""
    _write_review(repo_copy, _review(_digest(repo_copy), "draft", "verified"))

    errors: list = []
    warnings: list = []

    check_review_records(
        repo_copy, _records(repo_copy), _index(repo_copy), errors, warnings
    )

    assert any(
        "illegal transition draft -> verified" in message
        for message in errors
    )


def test_legal_transition_is_accepted(repo_copy):
    """A draft may enter review."""
    _write_review(repo_copy, _review(_digest(repo_copy), "draft", "review"))

    errors: list = []
    warnings: list = []

    check_review_records(
        repo_copy, _records(repo_copy), _index(repo_copy), errors, warnings
    )

    assert not errors


def test_stale_digest_is_reported(repo_copy):
    """A review of content that changed no longer applies."""
    path = repo_copy / STANDARD_PATH
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("\nversion: 0.1.0\n", "\nversion: 0.2.0\n"),
        encoding="utf-8",
    )

    errors: list = []
    warnings: list = []

    check_review_records(
        repo_copy, _records(repo_copy), _index(repo_copy), errors, warnings
    )

    assert any(
        "the reviewed content digest does not match" in message
        for message in warnings
    )


def test_changed_content_requires_a_version_update(repo_copy):
    """A content change without a version change is an error."""
    path = repo_copy / STANDARD_PATH
    text = path.read_text(encoding="utf-8")
    path.write_text(text + "\n# an unrelated comment\n", encoding="utf-8")

    errors: list = []
    warnings: list = []

    check_review_records(
        repo_copy, _records(repo_copy), _index(repo_copy), errors, warnings
    )

    assert any(
        "changed but its version stayed 0.1.0" in message
        for message in errors
    )


def test_modified_review_record_is_rejected(repo_copy):
    """A published review record must not be edited."""
    _init_git(repo_copy)

    path = repo_copy / "governance" / "reviews" / "REV-0002.yaml"
    _write_review(repo_copy, _review(_digest(repo_copy)))
    _commit(repo_copy, "publish")

    errors: list = []
    warnings: list = []
    check_review_records(
        repo_copy, _records(repo_copy), _index(repo_copy), errors, warnings
    )
    assert not errors

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["rationale"] = "A different rationale after the fact."
    _write(path, data)
    _commit(repo_copy, "edit")

    errors = []
    warnings = []
    check_review_records(
        repo_copy, _records(repo_copy), _index(repo_copy), errors, warnings
    )

    assert any(
        "must not be modified" in message for message in errors
    )


def test_status_without_a_review_record_is_rejected(repo_copy):
    """A Standard that left draft needs an approved record."""
    path = repo_copy / STANDARD_PATH
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("status: draft", "status: review"), encoding="utf-8")

    errors: list = []
    check_status_trail(repo_copy, _records(repo_copy), _index(repo_copy), errors)

    # The approved record exists, but it describes content that has
    # changed, so it no longer backs the status.
    assert any(
        "status 'review' is not backed by a review record that matches "
        "the current content" in message
        for message in errors
    )


def test_status_without_any_review_record_is_rejected(repo_copy):
    """A Standard that left draft needs an approved record at all."""
    path = repo_copy / STANDARD_PATH
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("status: draft", "status: review"), encoding="utf-8")

    # Remove the only review record of the Standard.
    (repo_copy / "governance" / "reviews" / "REV-0001.yaml").unlink()

    errors: list = []
    check_status_trail(repo_copy, _records(repo_copy), _index(repo_copy), errors)

    assert any(
        "status 'review' has no approved review record" in message
        for message in errors
    )


def test_verified_status_must_clear_every_gate(repo_copy):
    """A Standard that claims verified needs every local gate."""
    path = repo_copy / STANDARD_PATH
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("status: draft", "status: verified"), encoding="utf-8")

    errors: list = []
    check_verified_standards(
        repo_copy,
        _records(repo_copy),
        _index(repo_copy),
        _validator(repo_copy),
        errors,
    )

    assert any(
        "does not clear the gate" in message for message in errors
    )


def test_repository_authorization_is_external(repo_root):
    """The identity of a reviewer cannot be established locally."""
    gates = promotion_gates(
        repo_root,
        STANDARD,
        _records(repo_root),
        _index(repo_root),
        _validator(repo_root),
    )

    gate = [g for g in gates if g.name == "repository-authorization"][0]

    assert gate.status == "enforced externally"
    assert "never identity authenticity" in gate.detail


def test_gates_cover_the_designed_conditions(repo_root):
    """The gates must match the technical design."""
    gates = promotion_gates(
        repo_root,
        STANDARD,
        _records(repo_root),
        _index(repo_root),
        _validator(repo_root),
    )

    assert [gate.name for gate in gates] == [
        "valid-standard-yaml",
        "current-bilingual-review",
        "reviewed-evidence-coverage",
        "no-blocking-conflicts",
        "mandatory-evaluation-cases",
        "approved-review-record",
        "repository-authorization",
    ]


def test_digest_matches_the_file_bytes(repo_root):
    """The digest is taken over the file bytes."""
    path = repo_root / STANDARD_PATH
    expected = hashlib.sha256(path.read_bytes()).hexdigest()

    assert file_digest(path) == expected
