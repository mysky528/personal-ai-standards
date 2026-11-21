# SPDX-License-Identifier: MIT
"""Repository scenarios used to verify validator behaviour.

Each scenario is a list of mutations applied to a throwaway copy of
the repository. The mutations are plain Python so they behave the
same on every platform.

The expected results live in `tests/fixtures/legacy/*.json` and were
captured from the pre-v0.2.0 validator implementation. The
equivalence test compares the current implementation against them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

Mutation = Callable[[Path], None]


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace(old, new), encoding="utf-8")


def _prepend_blank_line(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text("\n" + text, encoding="utf-8")


def _delete_heading_block(path: Path, heading: str, extra: int) -> None:
    """Delete the heading line plus `extra` following lines."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    kept: list[str] = []
    skipping = False
    remaining = 0
    for line in lines:
        if not skipping and line.startswith(f"## {heading}"):
            skipping = True
            remaining = extra
            continue
        if skipping:
            remaining -= 1
            if remaining < 0:
                skipping = False
            continue
        kept.append(line)
    path.write_text("".join(kept), encoding="utf-8")


def _unknown_skill_reference(root: Path) -> None:
    _replace(
        root / "skills" / "security-review" / "SKILL.md",
        "PAISL-ENG-001",
        "PAISL-ENG-999",
    )


def _malformed_id(root: Path) -> None:
    _replace(
        root / "skills" / "task-clarification" / "SKILL.md",
        "PAISL-PROD-001",
        "PAISL-PRD-001",
    )


def _missing_section(root: Path) -> None:
    _delete_heading_block(
        root / "skills" / "ai-output-review" / "SKILL.md",
        "Limitations",
        2,
    )


def _license_scope_mismatch(root: Path) -> None:
    _replace(
        root / "catalog" / "standards.yaml",
        "SPDX-License-Identifier: CC-BY-4.0",
        "SPDX-License-Identifier: MIT",
    )


def _version_drift(root: Path) -> None:
    _replace(
        root / "catalog" / "standards.yaml",
        "catalog_version: 0.1.1",
        "catalog_version: 0.1.0",
    )


def _readme_unknown_skill(root: Path) -> None:
    _replace(root / "README.md", "| ste-writing |", "| stee-writing |")


def _missing_standard_file(root: Path) -> None:
    _replace(
        root / "catalog" / "standards.yaml",
        "standards/communication/bluf.yaml",
        "standards/communication/missing.yaml",
    )


def _frontmatter_not_first(root: Path) -> None:
    _prepend_blank_line(root / "skills" / "ste-writing" / "SKILL.md")


def _skill_name_mismatch(root: Path) -> None:
    _replace(
        root / "skills" / "ste-writing" / "SKILL.md",
        "name: ste-writing",
        "name: ste-writin",
    )


SCENARIOS: dict[str, list[Mutation]] = {
    "pass": [],
    "unknown_skill_ref": [_unknown_skill_reference],
    "malformed_id": [_malformed_id],
    "missing_section": [_missing_section],
    "license_scope": [_license_scope_mismatch],
    "version_drift": [_version_drift],
    "readme_unknown_skill": [_readme_unknown_skill],
    "missing_standard_file": [_missing_standard_file],
    "frontmatter_blank_line": [_frontmatter_not_first],
    "skill_name_mismatch": [_skill_name_mismatch],
}
