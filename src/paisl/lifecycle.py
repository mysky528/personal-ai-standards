# SPDX-License-Identifier: MIT
"""Lifecycle governance.

This module owns the rules that decide whether a Standard may change
status. It checks the review records, the trail between a status and
the record that explains it, and the gates that a promotion to
`verified` must clear.

One boundary matters. A repository-local check cannot establish the
real identity or the authority of a reviewer from a YAML string.
Reviewer authorization is therefore enforced outside the repository,
by protected branches, CODEOWNERS, and required review rules. The
checks here establish record integrity, never identity authenticity.
"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .paths import is_reference

ALLOWED_TRANSITIONS = frozenset({
    ("draft", "review"),
    ("review", "draft"),
    ("review", "verified"),
    ("verified", "review"),
    ("verified", "deprecated"),
    ("deprecated", "draft"),
})

REACTIVATION_TRANSITION = ("deprecated", "draft")

SATISFIED = "satisfied"
NOT_SATISFIED = "not satisfied"
ENFORCED_EXTERNALLY = "enforced externally"


@dataclass
class Gate:
    """One condition that a promotion has to clear."""

    name: str
    description: str
    status: str
    detail: str

    @property
    def satisfied(self) -> bool:
        return self.status == SATISFIED


def file_digest(path: Path) -> str | None:
    """Return the SHA-256 digest of a file, or None when it is absent."""
    if not path.is_file():
        return None

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_path(root: Path, relative: str) -> str | None:
    """Return the path of a file as the Git repository names it.

    The repository under test may live inside a larger repository, so
    the path is resolved against the top of the working tree.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-prefix"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None

    if result.returncode != 0:
        return None

    return f"{result.stdout.strip()}{relative}"


def _commits_for(root: Path, relative: str) -> list:
    """Return the commits that touched a file, the newest first."""
    path = _git_path(root, relative)

    if path is None:
        return []

    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "log",
                "--format=%H",
                "--",
                f":(top){path}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []

    if result.returncode != 0:
        return []

    return [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def published_content(root: Path, relative: str) -> bytes | None:
    """Return the content of a file as it was first published.

    Returns None when the answer is unknown, for example when the
    repository history is unavailable or the file was never published.

    The content is compared, not the number of commits. A record that
    was edited and then restored is published again, and a check that
    counted the commits would keep it in error for ever, with no way
    out. Comparing the content keeps the rule recoverable.
    """
    commits = _commits_for(root, relative)

    if not commits:
        return None

    path = _git_path(root, relative)

    if path is None:
        return None

    # The oldest commit that touched the file introduced it.
    first = commits[-1]

    try:
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"{first}:{path}"],
            capture_output=True,
            check=False,
        )
    except OSError:
        return None

    if result.returncode != 0:
        return None

    return result.stdout


def _same_content(published: bytes, current: bytes) -> bool:
    """Compare two contents, ignoring the line endings."""
    return published.replace(b"\r\n", b"\n") == current.replace(b"\r\n", b"\n")


def stale_record_blocks(data: dict, current_version: object) -> bool:
    """Decide whether a record that no longer matches the content blocks.

    A record that belongs to an earlier revision of a Standard cannot
    authorise the content that came after it, whatever it says. It is
    reported, and it does not block, so that a legitimate version
    upgrade is never held back by the history of the review.

    The safety does not depend on this finding. The promotion gates
    ask for a record that matches the digest of the current content,
    so an approval of an earlier revision never authorises new
    content.

    A record that belongs to the current revision has to match it. It
    claims to describe the content that is there now, and it does
    not, so it blocks.
    """
    version = data.get("standard_version")

    if isinstance(current_version, str) and isinstance(version, str):
        return version == current_version

    return True


def _standard_path(root: Path, standard_index: dict, sid: str) -> Path | None:
    entry = standard_index.get(sid)

    if not entry:
        return None

    return root / entry["path"]


def _approved_reviews(records: list, sid: str) -> list:
    return [
        record
        for record in records
        if record.kind == "review"
        and record.data.get("standard_id") == sid
        and record.data.get("decision") == "approved"
        and not is_reference(record)
    ]


def _semantic_reviews(records: list, sid: str) -> list:
    return [
        record
        for record in records
        if record.kind == "semantic-review"
        and record.data.get("standard_id") == sid
        and not is_reference(record)
    ]


def check_review_records(
    root: Path,
    records: list,
    standard_index: dict,
    errors: list,
    warnings: list,
) -> None:
    """Check every lifecycle review record."""
    for record in records:
        if record.kind != "review":
            continue

        relative = record.relative
        data = record.data
        sid = data.get("standard_id")
        from_status = data.get("from_status")
        to_status = data.get("to_status")
        digest = data.get("reviewed_content_sha256")

        if isinstance(sid, str) and sid not in standard_index:
            errors.append(f"{relative}: unknown standard reference: {sid}")

        if (from_status, to_status) not in ALLOWED_TRANSITIONS:
            errors.append(
                f"{relative}: illegal transition "
                f"{from_status} -> {to_status}"
            )

        if not data.get("reviewer"):
            errors.append(f"{relative}: reviewer must not be empty")

        if not data.get("rationale"):
            errors.append(f"{relative}: rationale must be recorded")

        path = _standard_path(root, standard_index, sid) if isinstance(sid, str) else None

        if (
            path is not None
            and isinstance(digest, str)
            and not is_reference(record)
        ):
            current = file_digest(path)

            if current is not None and current != digest:
                message = (
                    f"{relative}: the reviewed content digest does not "
                    f"match {path.name}"
                )

                declared = standard_index.get(sid, {}).get("version")

                # A record that approves a verification must still
                # describe the content it verified. A record of an
                # earlier revision cannot authorise the content that
                # came after it, whatever it says, so it is reported
                # and it does not block the Standard.
                if (
                    to_status == "verified"
                    and stale_record_blocks(data, declared)
                ):
                    errors.append(message)
                else:
                    warnings.append(message)

                version = data.get("standard_version")

                if (
                    isinstance(declared, str)
                    and isinstance(version, str)
                    and version == declared
                ):
                    errors.append(
                        f"{relative}: the content of {sid} changed but "
                        f"its version stayed {declared}"
                    )

        published = published_content(root, relative)

        if published is not None:
            current_bytes = (
                record.path.read_bytes() if record.path.is_file() else b""
            )

            if not _same_content(published, current_bytes):
                errors.append(
                    f"{relative}: a published review record must not be "
                    f"modified"
                )


def check_status_trail(
    root: Path,
    records: list,
    standard_index: dict,
    errors: list,
) -> None:
    """A Standard that left `draft` must have an approved record."""
    for sid, entry in sorted(standard_index.items()):
        status = _current_status(root, entry)

        if status is None or status == "draft":
            continue

        approved = _approved_reviews(records, sid)

        if not approved:
            errors.append(
                f"{entry['path']}: status '{status}' has no approved "
                f"review record"
            )
            continue

        path = _standard_path(root, standard_index, sid)
        current = file_digest(path) if path is not None else None

        if current is None:
            continue

        matching = [
            record
            for record in approved
            if record.data.get("reviewed_content_sha256") == current
        ]

        if not matching:
            errors.append(
                f"{entry['path']}: status '{status}' is not backed by a "
                f"review record that matches the current content"
            )


def _current_status(root: Path, entry: dict) -> str | None:
    path = root / entry["path"]

    if not path.is_file():
        return None

    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        return None

    status = data.get("status")

    return status if isinstance(status, str) else None


def promotion_gates(
    root: Path,
    sid: str,
    records: list,
    standard_index: dict,
    validator,
) -> list:
    """Return the gates that a promotion to `verified` must clear."""
    gates: list = []
    entry = standard_index.get(sid, {})
    path = _standard_path(root, standard_index, sid)
    current = file_digest(path) if path is not None else None

    # Gate 1: the Standard definition is valid.
    valid = False
    detail = f"{sid} has no definition"

    if path is not None and path.is_file():
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8"))

        if isinstance(data, dict):
            problems = list(validator.iter_errors(data))
            valid = not problems
            detail = (
                "the definition satisfies the Standard Schema"
                if valid
                else "; ".join(problem.message for problem in problems)
            )

    gates.append(Gate(
        "valid-standard-yaml",
        "The Standard definition satisfies the Standard Schema.",
        SATISFIED if valid else NOT_SATISFIED,
        detail,
    ))

    # Gate 2: a current bilingual review.
    semantic = _semantic_reviews(records, sid)
    current_reviews = [
        record
        for record in semantic
        if current is not None
        and record.data.get("reviewed_content_sha256") == current
    ]
    passing = [
        record for record in current_reviews
        if record.data.get("outcome") == "pass"
    ]

    gates.append(Gate(
        "current-bilingual-review",
        "A bilingual semantic review of the current content passed.",
        SATISFIED if passing else NOT_SATISFIED,
        (
            f"semantic review {passing[0].id} covers the current content"
            if passing
            else f"{sid} has no passing semantic review of the current content"
        ),
    ))

    # Gate 3: reviewed evidence coverage for every rule.
    from .evidence import evidence_coverage

    coverage = evidence_coverage(records, root)
    standard_coverage = coverage["standards"].get(sid, {"rules": {}})
    rules = standard_coverage.get("rules", {})

    approved = _approved_reviews(records, sid)
    exceptions: dict = {}

    for record in approved:
        for exception in record.data.get("exceptions", []) or []:
            if isinstance(exception, dict):
                rule_id = exception.get("rule_id")

                if isinstance(rule_id, str):
                    exceptions[rule_id] = exception

    uncovered = [
        rule_id
        for rule_id, rule in rules.items()
        if not rule["sufficient_for_verification"]
        and rule_id not in exceptions
    ]

    gates.append(Gate(
        "reviewed-evidence-coverage",
        "Every rule has reviewed supporting evidence or an approved exception.",
        SATISFIED if rules and not uncovered else NOT_SATISFIED,
        (
            "every rule is covered"
            if rules and not uncovered
            else f"rules without reviewed evidence: {', '.join(uncovered) or 'no rule is linked yet'}"
        ),
    ))

    # Gate 4: no unresolved confirmed blocking conflict.
    blocking = [
        record.relative
        for record in records
        if record.kind == "conflict"
        and record.data.get("classification") == "confirmed"
        and record.data.get("status") == "open"
        and any(
            isinstance(rule, dict)
            and rule.get("standard_id") == sid
            for rule in record.data.get("rules", [])
        )
    ]

    gates.append(Gate(
        "no-blocking-conflicts",
        "No unresolved confirmed conflict blocks the Standard.",
        SATISFIED if not blocking else NOT_SATISFIED,
        (
            "no blocking conflict"
            if not blocking
            else f"blocking conflicts: {', '.join(blocking)}"
        ),
    ))

    # Gate 5: the mandatory evaluation cases pass.
    from .evaluation import evaluate_standard

    cases = [
        record.data
        for record in records
        if record.kind == "evaluation-case"
    ]
    outcome = evaluate_standard(root, sid, cases)

    if not outcome["cases"]:
        gates.append(Gate(
            "mandatory-evaluation-cases",
            "The mandatory evaluation cases of the Standard pass.",
            NOT_SATISFIED,
            f"{sid} has no evaluation case",
        ))
    elif outcome["failed"]:
        gates.append(Gate(
            "mandatory-evaluation-cases",
            "The mandatory evaluation cases of the Standard pass.",
            NOT_SATISFIED,
            f"failing cases: {', '.join(outcome['failed'])}",
        ))
    else:
        gates.append(Gate(
            "mandatory-evaluation-cases",
            "The mandatory evaluation cases of the Standard pass.",
            SATISFIED,
            f"{outcome['passed']} of {outcome['cases']} cases passed",
        ))

    # Gate 6: an approved review record that matches the content.
    matching = [
        record
        for record in approved
        if record.data.get("to_status") == "verified"
        and current is not None
        and record.data.get("reviewed_content_sha256") == current
    ]

    gates.append(Gate(
        "approved-review-record",
        "An approved review record matches the content digest.",
        SATISFIED if matching else NOT_SATISFIED,
        (
            f"review record {matching[0].id} approves the current content"
            if matching
            else f"{sid} has no approved review record for the current content"
        ),
    ))

    # Gate 7: repository level authorisation.
    gates.append(Gate(
        "repository-authorization",
        "The repository enforces who may approve a transition.",
        ENFORCED_EXTERNALLY,
        "reviewer authorisation is enforced by protected branches, "
        "CODEOWNERS, and required GitHub review rules. A local check "
        "establishes record integrity, never identity authenticity.",
    ))

    return gates


def check_verified_standards(
    root: Path,
    records: list,
    standard_index: dict,
    validator,
    errors: list,
) -> None:
    """A Standard that claims `verified` must clear every local gate."""
    for sid, entry in sorted(standard_index.items()):
        status = _current_status(root, entry)

        if status != "verified":
            continue

        for gate in promotion_gates(
            root, sid, records, standard_index, validator
        ):
            if gate.status == NOT_SATISFIED:
                errors.append(
                    f"{entry['path']}: status 'verified' does not clear "
                    f"the gate '{gate.name}': {gate.detail}"
                )
