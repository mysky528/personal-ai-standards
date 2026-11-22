# SPDX-License-Identifier: MIT
"""AC-016 to AC-019 — the conflict and bilingual acceptance criteria.

AC-016: explicit conflicts can be validated and reviewed.
AC-017: unresolved confirmed blocking conflicts prevent a verified
promotion.
AC-018: missing required language fields fail.
AC-019: changed bilingual content invalidates the prior semantic review.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import yaml

import records


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


def test_ac016_a_declared_conflict_can_be_validated(repo_copy):
    """The declared conflict is read and reported."""
    result = _cli(repo_copy, "conflicts", "check", "--format", "json")

    assert result.returncode == 0

    payload = json.loads(result.stdout)["conflicts"]
    declared = payload["declared"]

    assert declared["total"] == 1

    conflict = declared["conflicts"][0]

    assert conflict["id"] == "CONFLICT-0001"
    assert conflict["classification"] == "potential"
    assert conflict["status"] == "open"
    assert conflict["rules"] == [
        "PAISL-COMM-001/R001",
        "PAISL-COMM-002/R001",
    ]


def test_ac016_candidates_are_listed_as_candidates(repo_copy):
    """The report lists candidates without calling them contradictions."""
    result = _cli(repo_copy, "conflicts", "check")

    assert result.returncode == 0
    assert "Candidate conflicts:" in result.stdout
    assert "It is not a contradiction" in result.stdout


def test_ac017_a_blocking_conflict_prevents_promotion(repo_copy):
    """A confirmed and unresolved conflict blocks a promotion."""
    path = repo_copy / "governance" / "conflicts" / "CONFLICT-0001.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["classification"] = "confirmed"
    data["reviewer"] = "reviewer-id"
    data["rules"] = [
        {"standard_id": "PAISL-ENG-001", "rule_id": "R001"},
        {"standard_id": "PAISL-COMM-001", "rule_id": "R001"},
    ]
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    standard = repo_copy / "standards" / "engineering" / "owasp-asvs.yaml"
    data = yaml.safe_load(standard.read_text(encoding="utf-8"))
    data["status"] = "verified"
    standard.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    result = _cli(repo_copy, "validate")

    assert result.returncode == 1
    assert "no-blocking-conflicts" in result.stdout


def test_ac018_a_missing_translation_fails(repo_copy):
    """A Standard without a Chinese field does not pass."""
    path = repo_copy / "standards" / "engineering" / "owasp-asvs.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    del data["name"]["zh-CN"]
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    result = _cli(repo_copy, "validate")

    assert result.returncode == 1
    assert "zh-CN" in result.stdout


def test_ac019_changed_content_invalidates_the_semantic_review(repo_copy):
    """A bilingual review no longer describes changed content."""
    records.semantic_review(repo_copy, "SEM-0002", outcome="pass")
    path = repo_copy / "standards" / "engineering" / "owasp-asvs.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(text + "\n# a later edit\n", encoding="utf-8")

    result = _cli(repo_copy, "validate")

    assert result.returncode == 1
    assert "the bilingual review of PAISL-ENG-001 is stale" in result.stdout


def test_ac019_the_stale_review_is_listed(repo_copy):
    """The conflict report names the stale review."""
    records.semantic_review(repo_copy, "SEM-0002", outcome="pass")
    path = repo_copy / "standards" / "engineering" / "owasp-asvs.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(text + "\n# a later edit\n", encoding="utf-8")

    result = _cli(repo_copy, "conflicts", "check", "--format", "json")

    assert result.returncode == 0

    payload = json.loads(result.stdout)["conflicts"]

    assert "governance/reviews/SEM-0002.yaml" in payload["semantic_reviews"]["stale"]
