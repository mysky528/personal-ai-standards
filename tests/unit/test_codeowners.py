# SPDX-License-Identifier: MIT
"""The CODEOWNERS file.

The owners are asked for a review when a pull request changes a
governance critical path. The test keeps the list complete: a new
critical directory has to be added to the file.
"""

from __future__ import annotations

import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
CODEOWNERS = ROOT / ".github" / "CODEOWNERS"

# Every path that decides what a Standard means, or who may change
# it, must have an owner.
CRITICAL_PATHS = (
    "/schemas/",
    "/standards/",
    "/catalog/",
    "/evidence/",
    "/governance/",
    "/evaluations/",
    "/src/",
    "/scripts/",
    "/tests/",
    "/skills/",
    "/.github/",
)


def _rules() -> list:
    rules = []

    for line in CODEOWNERS.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        parts = stripped.split()

        rules.append((parts[0], parts[1:]))

    return rules


def test_the_codeowners_file_exists():
    """The repository must name the owners of its critical paths."""
    assert CODEOWNERS.is_file(), ".github/CODEOWNERS is missing"


def test_every_critical_path_has_an_owner():
    """No critical path may be left without an owner."""
    covered = {pattern for pattern, _ in _rules()}

    missing = [
        path for path in CRITICAL_PATHS
        if path not in covered
    ]

    assert not missing, f"paths without an owner: {missing}"


def test_every_rule_names_an_owner():
    """A rule without an owner would silently do nothing."""
    for pattern, owners in _rules():
        assert owners, f"{pattern} has no owner"
        assert all(
            owner.startswith("@") for owner in owners
        ), f"{pattern} has a malformed owner"


def test_the_codeowners_file_is_licensed():
    """The file must carry the licence of its directory."""
    text = CODEOWNERS.read_text(encoding="utf-8")

    assert "SPDX-License-Identifier: MIT" in text
