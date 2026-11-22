# SPDX-License-Identifier: MIT
"""Conflicts and bilingual review.

The tool may point at a pair of rules that look alike. It may never
claim that they contradict each other, and it may never let an
automatic suggestion stand in for a human review.
"""

from __future__ import annotations

import pathlib

import pytest
import yaml

from paisl.conflicts import (
    bilingual_evaluation_coverage,
    check_conflicts,
    check_semantic_reviews,
    conflict_candidates,
)
from paisl.lifecycle import promotion_gates
from paisl.registry import (
    build_standard_index,
    load_catalog,
    load_records,
)

import records
from paisl.schema_validation import build_validator

ROOT = pathlib.Path(__file__).resolve().parents[2]


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


def test_candidates_are_found_by_deterministic_metadata(repo_root):
    """Rules that open with the same action verb are candidates."""
    candidates = conflict_candidates(repo_root, _index(repo_root))
    pairs = {
        (candidate.first, candidate.second) for candidate in candidates
    }

    assert ("PAISL-COMM-001/R001", "PAISL-COMM-003/R001") in pairs
    assert ("PAISL-ENG-001/R001", "PAISL-REAS-001/R001") in pairs


def test_candidates_do_not_claim_a_contradiction(repo_root):
    """A candidate only states a reason to look."""
    candidates = conflict_candidates(repo_root, _index(repo_root))

    assert candidates

    for candidate in candidates:
        assert candidate.signals
        assert all("the same" in signal for signal in candidate.signals)


def test_rules_of_one_standard_are_never_candidates(repo_root):
    """Two rules of one Standard cannot contradict each other."""
    candidates = conflict_candidates(repo_root, _index(repo_root))

    for candidate in candidates:
        assert candidate.first.split("/")[0] != candidate.second.split("/")[0]


def test_the_reference_records_pass_the_conflict_checks(repo_root):
    """The reference instances must satisfy the conflict rules."""
    errors: list = []
    warnings: list = []

    check_conflicts(repo_root, _records(repo_root), _index(repo_root), errors, warnings)
    check_semantic_reviews(
        repo_root, _records(repo_root), _index(repo_root), errors, warnings
    )

    assert not errors
    assert not warnings


def test_a_confirmed_conflict_needs_a_reviewer(repo_copy):
    """Confirming a conflict is a human judgement."""
    path = repo_copy / "governance" / "conflicts" / "CONFLICT-0001.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["classification"] = "confirmed"
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    errors: list = []
    warnings: list = []
    check_conflicts(repo_copy, _records(repo_copy), _index(repo_copy), errors, warnings)

    assert any(
        "a confirmed conflict needs a reviewer" in message
        for message in errors
    )


def test_a_closed_conflict_needs_a_reviewer(repo_copy):
    """Closing a conflict is a human judgement."""
    path = repo_copy / "governance" / "conflicts" / "CONFLICT-0001.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["status"] = "accepted_exception"
    data["resolution"] = "Both rules apply to different cases."
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    errors: list = []
    warnings: list = []
    check_conflicts(repo_copy, _records(repo_copy), _index(repo_copy), errors, warnings)

    assert any(
        "a conflict that is closed needs a reviewer" in message
        for message in errors
    )


def test_a_stale_bilingual_review_is_reported(repo_copy):
    """A bilingual review that no longer matches the content is stale."""
    records.semantic_review(repo_copy, "SEM-0002", outcome="pass")
    path = repo_copy / "standards" / "engineering" / "owasp-asvs.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(text + "\n# a later edit\n", encoding="utf-8")

    errors: list = []
    warnings: list = []
    check_semantic_reviews(
        repo_copy, _records(repo_copy), _index(repo_copy), errors, warnings
    )

    assert any(
        "the bilingual review of PAISL-ENG-001 is stale" in message
        for message in warnings
    )


def test_a_stale_review_of_a_reviewed_standard_is_reported(repo_copy):
    """A Standard in review may not keep a review that no longer fits.

    The promotion gate refuses a stale review on its own, so the
    finding is a warning here. The version rule is the part that
    blocks: a changed content needs a changed version.
    """
    records.semantic_review(repo_copy, "SEM-0002", outcome="pass")
    path = repo_copy / "standards" / "engineering" / "owasp-asvs.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("status: draft", "status: review")
        + "\n# a later edit\n",
        encoding="utf-8",
    )

    errors: list = []
    warnings: list = []
    check_semantic_reviews(
        repo_copy, _records(repo_copy), _index(repo_copy), errors, warnings
    )

    assert any(
        "the bilingual review of PAISL-ENG-001 is stale" in message
        for message in warnings
    )
    assert any(
        "changed but its version stayed 0.1.0" in message
        for message in errors
    )


def test_a_stale_review_of_a_verified_standard_is_an_error(repo_copy):
    """A Standard that claims to be verified may not keep a stale review."""
    records.semantic_review(repo_copy, "SEM-0002", outcome="pass")
    path = repo_copy / "standards" / "engineering" / "owasp-asvs.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("status: draft", "status: verified")
        + "\n# a later edit\n",
        encoding="utf-8",
    )

    errors: list = []
    warnings: list = []
    check_semantic_reviews(
        repo_copy, _records(repo_copy), _index(repo_copy), errors, warnings
    )

    assert any(
        "the bilingual review of PAISL-ENG-001 is stale" in message
        for message in errors
    )


def test_advisory_suggestions_never_satisfy_a_gate(repo_copy):
    """A suggestion from an automated tool is never authoritative."""
    path = repo_copy / "governance" / "reviews" / "SEM-0001.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["advisory_suggestions"] = [
        {
            "source": "llm-assistant",
            "text": "The Chinese description could be more detailed.",
            "field": "description.zh-CN",
        }
    ]
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    gates = {
        gate.name: gate
        for gate in promotion_gates(
            repo_copy,
            "PAISL-ENG-001",
            _records(repo_copy),
            _index(repo_copy),
            _validator(repo_copy),
        )
    }

    assert gates["current-bilingual-review"].status != "satisfied"


def test_bilingual_evaluation_coverage_is_reported(repo_root):
    """The coverage names the rules that lack a case in a language."""
    coverage = bilingual_evaluation_coverage(repo_root, _records(repo_root))

    assert coverage["rules_with_cases"] == 2
    assert "PAISL-COMM-001/R001" in coverage["rules_with_one_language"]
    assert "PAISL-ENG-001/R001" in coverage["rules_with_one_language"]
