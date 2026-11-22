# SPDX-License-Identifier: MIT
"""The governance of a Standard that changes revision.

Two things have to hold at the same time.

A legitimate version upgrade must not be held back for ever by the
history of the review. The records of the earlier revision stay in the
repository, they are reported, and they do not block.

An approval of the earlier revision must never authorise the content
that came after it. The promotion gates ask for a record that matches
the digest of the current content, and a record that claims the
current revision but matches older content is an error.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
STANDARD = "PAISL-ENG-001"
STANDARD_PATH = "standards/engineering/owasp-asvs.yaml"


def _cli(repo: pathlib.Path, *args: str):
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


def _write(repo: pathlib.Path, relative: str, data: dict) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# SPDX-License-Identifier: CC-BY-4.0\n"
        + yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _digest(repo: pathlib.Path) -> str:
    return hashlib.sha256(
        (repo / STANDARD_PATH).read_bytes()
    ).hexdigest()


def _upgrade(repo: pathlib.Path, status: str = "draft") -> str:
    """Move the Standard to the next revision and return its digest."""
    path = repo / STANDARD_PATH
    text = path.read_text(encoding="utf-8")
    text = text.replace("version: 0.1.0", "version: 0.2.0")
    text = text.replace("status: draft", f"status: {status}")
    path.write_text(text + "\n# the next revision\n", encoding="utf-8")

    return _digest(repo)


def _promotion_material(repo: pathlib.Path, digest: str) -> None:
    """Add the records that a promotion to `verified` needs."""
    _write(repo, "governance/reviews/REV-0002.yaml", {
        "id": "REV-0002",
        "schema_version": "0.2.0",
        "standard_id": STANDARD,
        "standard_version": "0.2.0",
        "from_status": "review",
        "to_status": "verified",
        "reviewed_content_sha256": digest,
        "reviewer": "maintainer-id",
        "reviewed_at": "2026-11-22T12:00:00Z",
        "decision": "approved",
        "rationale": "The evidence, the bilingual text, and the "
                     "evaluation all support the verification.",
        "evidence_ids": ["EVD-0002"],
    })

    _write(repo, "governance/reviews/SEM-0002.yaml", {
        "id": "SEM-0002",
        "schema_version": "0.2.0",
        "standard_id": STANDARD,
        "standard_version": "0.2.0",
        "reviewed_content_sha256": digest,
        "languages": ["en", "zh-CN"],
        "reviewer": "reviewer-id",
        "reviewed_at": "2026-11-22T12:00:00Z",
        "outcome": "pass",
        "summary": {
            "en": "The English and the Chinese text agree.",
            "zh-CN": "中英文内容一致。",
        },
        "findings": [],
    })

    _write(repo, "evidence/records/EVD-0002.yaml", {
        "id": "EVD-0002",
        "schema_version": "0.2.0",
        "title": "OWASP ASVS project documentation",
        "source": {
            "url": "https://owasp.org/www-project-application-security-"
                   "verification-standard/",
            "type": "official",
            "publisher": "OWASP",
            "retrieved_at": "2026-11-22T00:00:00Z",
            "accessed": True,
        },
        "review": {
            "status": "reviewed",
            "reviewed_by": "reviewer-id",
            "reviewed_at": "2026-11-22T00:00:00Z",
            "rationale": "The source was inspected and it describes the "
                         "requirement.",
        },
        "notes": None,
    })

    link = yaml.safe_load(
        (repo / "evidence" / "links" / "PAISL-ENG-001.yaml").read_text(
            encoding="utf-8"
        )
    )
    link["standard_version"] = "0.2.0"
    link["rules"][0]["evidence"].append({
        "evidence_id": "EVD-0002",
        "relationship": "supports",
        "locator": "Requirement catalogue",
        "note": None,
    })
    _write(repo, "evidence/links/PAISL-ENG-001.yaml", link)


def _init_git(repo: pathlib.Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
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
            "publish",
        ],
        cwd=repo,
        check=True,
    )


def test_a_legitimate_version_upgrade_does_not_block(repo_copy):
    """The history of the review does not hold back a new revision.

    The content changed and the version moved with it, so the record
    of the earlier revision belongs to the earlier revision. It is
    reported, and the Standard is not held back.
    """
    _upgrade(repo_copy)

    result = _cli(repo_copy, "governance", "check")

    assert result.returncode == 0, (
        f"a version upgrade must not be blocked:\n{result.stdout}"
    )
    assert "does not match" in result.stdout, (
        "the record of the earlier revision must be reported"
    )
    assert "ERROR" not in result.stdout


def test_a_complete_promotion_clears_every_gate(repo_copy):
    """A promotion with the records of the current revision passes.

    The historical records stay in the repository. They do not stop
    the promotion, and they do not have to be deleted to make it
    happen.
    """
    digest = _upgrade(repo_copy, status="verified")
    _promotion_material(repo_copy, digest)

    result = _cli(repo_copy, "governance", "check")

    assert result.returncode == 0, (
        f"a complete promotion must pass:\n{result.stdout}"
    )
    assert "ERROR" not in result.stdout


def test_the_gates_are_satisfied_for_a_complete_promotion(repo_copy):
    """Every gate that is checked locally is satisfied."""
    digest = _upgrade(repo_copy, status="verified")
    _promotion_material(repo_copy, digest)

    report_path = repo_copy / "governance-report.json"

    result = _cli(
        repo_copy,
        "governance",
        "check",
        "--all",
        "--format",
        "json",
        "--output",
        str(report_path),
    )

    assert result.returncode == 0, result.stdout

    report = json.loads(report_path.read_text(encoding="utf-8"))["governance"]
    gates = report["standards"][STANDARD]["gates"]

    for gate in gates:
        assert gate["status"] in ("satisfied", "enforced externally"), (
            f"the gate {gate['name']} is not satisfied: {gate['detail']}"
        )


def test_an_approval_of_the_earlier_revision_cannot_authorise_the_content(
    repo_copy,
):
    """The approval of the old revision does not carry the new content.

    The Standard is verified and the only approval is the record of
    the earlier revision. The gate asks for a record that matches the
    current content, and it is not satisfied.
    """
    _upgrade(repo_copy, status="verified")

    result = _cli(repo_copy, "governance", "check")

    assert result.returncode == 1, (
        "an approval of the earlier revision must not verify a Standard"
    )
    assert "approved-review-record" in result.stdout
    assert "current-bilingual-review" in result.stdout


def test_an_approval_that_claims_the_current_revision_must_match_it(
    repo_copy,
):
    """A record that claims the current revision has to match it.

    The version of the record was moved forward, but the digest is
    the one of the earlier content. The record says it approved the
    revision that is there now, and it did not.
    """
    digest = _upgrade(repo_copy, status="verified")
    _promotion_material(repo_copy, digest)

    old = _digest(repo_copy)
    path = repo_copy / "standards" / "engineering" / "owasp-asvs.yaml"
    path.write_text(
        path.read_text(encoding="utf-8") + "\n# one more edit\n",
        encoding="utf-8",
    )

    _write(repo_copy, "governance/reviews/REV-0003.yaml", {
        "id": "REV-0003",
        "schema_version": "0.2.0",
        "standard_id": STANDARD,
        "standard_version": "0.2.0",
        "from_status": "review",
        "to_status": "verified",
        "reviewed_content_sha256": old,
        "reviewer": "maintainer-id",
        "reviewed_at": "2026-11-22T12:00:00Z",
        "decision": "approved",
        "rationale": "The approval of the earlier revision, moved forward.",
        "evidence_ids": ["EVD-0002"],
    })

    result = _cli(repo_copy, "governance", "check")

    assert result.returncode == 1, (
        "a record that does not match the current content must not pass"
    )
    assert "REV-0003.yaml" in result.stdout


def test_a_published_review_record_may_not_be_modified(repo_copy):
    """The content of a published record is fixed.

    The check compares the content with the content that was
    published, and not the number of commits. A record that was
    edited and then restored is published again, so the finding goes
    away and the repository does not stay broken for ever.
    """
    _init_git(repo_copy)

    path = repo_copy / "governance" / "reviews" / "REV-0001.yaml"
    original = path.read_text(encoding="utf-8")

    data = yaml.safe_load(original)
    data["rationale"] = "A different rationale after the fact."
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    result = _cli(repo_copy, "governance", "check")

    assert result.returncode == 1, (
        "a published review record must not be edited"
    )
    assert "must not be modified" in result.stdout

    # Restoring the published content clears the finding.
    path.write_text(original, encoding="utf-8")

    result = _cli(repo_copy, "governance", "check")

    assert "must not be modified" not in result.stdout, (
        "the finding must not survive the restoration of the record"
    )


def test_the_history_of_a_record_does_not_block_the_next_revision(
    repo_copy,
):
    """The records of the earlier revision are reported, not blocking.

    Both a lifecycle review and a bilingual review of the earlier
    revision are in the repository. The Standard moves on, and the
    checks pass.
    """
    digest = _upgrade(repo_copy, status="verified")
    _promotion_material(repo_copy, digest)

    result = _cli(repo_copy, "governance", "check")

    assert result.returncode == 0, result.stdout
    assert "ERROR" not in result.stdout


def test_the_evidence_of_another_domain_resolves(repo_copy):
    """A record of one domain names a record of another domain.

    The review names the evidence, and the evidence is in another
    domain. The index holds every record, so the reference resolves
    and the gate sees the evidence.
    """
    digest = _upgrade(repo_copy, status="verified")
    _promotion_material(repo_copy, digest)

    result = _cli(repo_copy, "governance", "check")

    failures = [
        line
        for line in result.stdout.splitlines()
        if line.startswith("ERROR")
    ]

    assert not failures, failures
    assert "unknown evidence reference" not in result.stdout
    assert not any(
        "reviewed-evidence-coverage" in line for line in failures
    ), failures
