# SPDX-License-Identifier: MIT
"""The evidence registry.

The registry answers two questions: which rules are supported by
evidence, and is that evidence strong enough for a Standard to be
verified.
"""

from __future__ import annotations

import pathlib

import pytest
import yaml

from paisl.evidence import (
    check_evidence,
    evidence_coverage,
    evidence_records,
    rule_evidence,
)
from paisl.registry import load_records

import records

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _write(path: pathlib.Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _records(root: pathlib.Path) -> list:
    errors: list = []
    records = load_records(root, errors)
    assert not errors, errors
    return records


def _reviewed_evidence() -> dict:
    return {
        "id": "EVD-0002",
        "schema_version": "0.2.0",
        "title": "ASVS requirement catalogue",
        "source": {
            "url": "https://owasp.org/www-project-application-security-verification-standard/",
            "type": "official",
            "publisher": "OWASP",
            "retrieved_at": "2026-11-21T12:00:00Z",
            "accessed": True,
        },
        "review": {
            "status": "reviewed",
            "reviewed_by": "reviewer-id",
            "reviewed_at": "2026-11-21T12:00:00Z",
            "rationale": "Requirement catalogue inspected.",
        },
        "notes": None,
    }


def test_evidence_records_are_indexed(repo_copy):
    """Every evidence record that counts is reachable by its identifier."""
    records.evidence(repo_copy, "EVD-0002")
    index = evidence_records(_records(repo_copy))

    assert "EVD-0002" in index
    assert index["EVD-0002"].data["review"]["status"] == "reviewed"


def test_a_reference_record_is_not_indexed(repo_root):
    """A reference instance records no evidence and never counts."""
    index = evidence_records(_records(repo_root))

    assert "EVD-0001" not in index


def test_rule_evidence_is_grouped(repo_root):
    """The links are grouped by Standard and rule."""
    grouped = rule_evidence(_records(repo_root))

    assert ("PAISL-ENG-001", "R001") in grouped
    assert grouped[("PAISL-ENG-001", "R001")].supporting


def test_unreviewed_evidence_is_not_sufficient(repo_root):
    """An unreviewed record does not satisfy the evidence requirement."""
    coverage = evidence_coverage(_records(repo_root))
    standard = coverage["standards"]["PAISL-ENG-001"]

    assert standard["rules"]["R001"]["supporting"] == 1
    assert standard["rules"]["R001"]["reviewed_supporting"] == 0
    assert standard["sufficient_for_verification"] is False


def test_reviewed_evidence_is_sufficient(repo_copy):
    """A reviewed record that supports a rule is sufficient."""
    _write(
        repo_copy / "evidence" / "records" / "EVD-0002.yaml",
        _reviewed_evidence(),
    )

    path = repo_copy / "evidence" / "links" / "PAISL-ENG-001.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["rules"][0]["evidence"].append(
        {
            "evidence_id": "EVD-0002",
            "relationship": "supports",
            "locator": "Requirement catalogue",
            "note": None,
        }
    )
    _write(path, data)

    coverage = evidence_coverage(_records(repo_copy))
    standard = coverage["standards"]["PAISL-ENG-001"]

    assert standard["rules"]["R001"]["reviewed_supporting"] == 1
    assert standard["sufficient_for_verification"] is True


def test_context_does_not_satisfy_the_requirement(repo_copy):
    """A context link is not supporting evidence."""
    path = repo_copy / "evidence" / "links" / "PAISL-ENG-001.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["rules"][0]["evidence"][0]["relationship"] = "context"
    _write(path, data)

    coverage = evidence_coverage(_records(repo_copy))
    rule = coverage["standards"]["PAISL-ENG-001"]["rules"]["R001"]

    assert rule["supporting"] == 0
    assert rule["context"] == 1
    assert rule["sufficient_for_verification"] is False


def test_rejected_evidence_used_as_support_is_rejected(repo_copy):
    """A rejected record must not support a rule."""
    records.evidence(repo_copy, "EVD-0002", status="rejected")
    records.link(repo_copy, "EVD-0002")

    errors: list = []
    warnings: list = []
    check_evidence(_records(repo_copy), errors, warnings)

    assert any(
        "rejected evidence EVD-0002 is linked to rule R001" in message
        for message in errors
    )


def test_contradicting_evidence_is_surfaced(repo_copy):
    """A contradicting link must be surfaced for review."""
    records.evidence(repo_copy, "EVD-0002")
    records.link(repo_copy, "EVD-0002", relationship="contradicts")

    errors: list = []
    warnings: list = []
    check_evidence(_records(repo_copy), errors, warnings)

    assert not errors
    assert any(
        "rule R001 is contradicted by EVD-0002" in message
        for message in warnings
    )


def test_reference_instances_pass_the_evidence_checks(repo_root):
    """The reference instances must satisfy the evidence rules."""
    errors: list = []
    warnings: list = []

    check_evidence(_records(repo_root), errors, warnings)

    assert not errors
    assert not warnings
