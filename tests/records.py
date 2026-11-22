# SPDX-License-Identifier: MIT
"""Helpers that write real governance records into a repository copy.

The reference instances under `evidence/`, `governance/`, and
`evaluations/` document the shape of the contracts. They record no
decision, so the tooling ignores them. A test that needs a record
that actually counts writes one with these helpers.
"""

from __future__ import annotations

import hashlib
import pathlib

import yaml

STANDARD = "PAISL-ENG-001"
STANDARD_PATH = "standards/engineering/owasp-asvs.yaml"


def digest(repo: pathlib.Path, relative: str = STANDARD_PATH) -> str:
    """Return the digest of a file in the repository."""
    path = repo / relative

    if not path.is_file():
        return ""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(repo: pathlib.Path, relative: str, data: dict) -> pathlib.Path:
    """Write a record into the repository copy."""
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def evidence(
    repo: pathlib.Path,
    evidence_id: str = "EVD-0002",
    status: str = "reviewed",
) -> pathlib.Path:
    """Write an evidence record that counts."""
    data = {
        "id": evidence_id,
        "schema_version": "0.2.0",
        "title": "OWASP ASVS project documentation",
        "source": {
            "url": "https://owasp.org/www-project-application-security-verification-standard/",
            "type": "official",
            "publisher": "OWASP",
            "retrieved_at": "2026-11-22T00:00:00Z",
            "accessed": True,
        },
        "review": {
            "status": status,
            "reviewed_by": "reviewer-id",
            "reviewed_at": "2026-11-22T00:00:00Z",
            "rationale": "The source was inspected.",
        },
        "notes": None,
    }

    if status != "reviewed":
        data["review"] = {
            "status": status,
            "reviewed_by": None,
            "reviewed_at": None,
            "rationale": None,
        }
        data["source"]["retrieved_at"] = None
        data["source"]["accessed"] = False

    return write(repo, f"evidence/records/{evidence_id}.yaml", data)


def link(
    repo: pathlib.Path,
    evidence_id: str = "EVD-0002",
    relationship: str = "supports",
    standard_id: str = STANDARD,
) -> pathlib.Path:
    """Link a rule to an evidence record."""
    data = {
        "schema_version": "0.2.0",
        "standard_id": standard_id,
        "standard_version": "0.1.0",
        "rules": [
            {
                "rule_id": "R001",
                "evidence": [
                    {
                        "evidence_id": evidence_id,
                        "relationship": relationship,
                        "locator": "Project overview",
                        "note": None,
                    }
                ],
            }
        ],
    }

    return write(repo, f"evidence/links/{standard_id}.yaml", data)


def review(
    repo: pathlib.Path,
    review_id: str = "REV-0002",
    from_status: str = "draft",
    to_status: str = "review",
    decision: str = "approved",
    standard_id: str = STANDARD,
    content_digest: str | None = None,
) -> pathlib.Path:
    """Write a lifecycle review record that counts."""
    data = {
        "id": review_id,
        "schema_version": "0.2.0",
        "standard_id": standard_id,
        "standard_version": "0.1.0",
        "from_status": from_status,
        "to_status": to_status,
        "reviewed_content_sha256": content_digest or digest(repo),
        "reviewer": "reviewer-id",
        "reviewed_at": "2026-11-22T00:00:00Z",
        "decision": decision,
        "rationale": "Reviewed for the test.",
        "evidence_ids": [],
    }

    return write(repo, f"governance/reviews/{review_id}.yaml", data)


def semantic_review(
    repo: pathlib.Path,
    semantic_id: str = "SEM-0002",
    outcome: str = "pass",
    standard_id: str = STANDARD,
    content_digest: str | None = None,
) -> pathlib.Path:
    """Write a bilingual semantic review record that counts."""
    data = {
        "id": semantic_id,
        "schema_version": "0.2.0",
        "standard_id": standard_id,
        "standard_version": "0.1.0",
        "reviewed_content_sha256": content_digest or digest(repo),
        "languages": ["en", "zh-CN"],
        "reviewer": "reviewer-id",
        "reviewed_at": "2026-11-22T00:00:00Z",
        "outcome": outcome,
        "summary": {
            "en": "The English and the Chinese text agree.",
            "zh-CN": "中英文内容一致。",
        },
        "findings": [],
    }

    return write(repo, f"governance/reviews/{semantic_id}.yaml", data)
