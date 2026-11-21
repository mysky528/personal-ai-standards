# SPDX-License-Identifier: MIT
"""Skill reference integrity and coverage.

This module owns everything about the relationship between Skills
and Standards: parsing the referenced standard IDs, resolving them
against the Catalog, and checking that the READMEs list exactly the
Skills that exist.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from .paths import read_yaml

# A Skill must declare these sections. Each entry lists the accepted
# English names; the bilingual suffix is checked separately.
SKILL_REQUIRED_SECTIONS = {
    "purpose": ("Purpose",),
    "standards": ("Referenced Standards",),
    "input": ("Input",),
    "procedure": ("Procedure",),
    "output": ("Expected Output", "Output Contract"),
    "quality": ("Quality Checks",),
    "limitations": ("Limitations",),
}

SKILL_FRONTMATTER_RE = re.compile(
    r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n", re.S
)
SKILL_HEADING_RE = re.compile(r"^##[ \t]+(.+)$", re.M)
SKILL_TABLE_ROW_RE = re.compile(r"^\|[ \t]*([a-z0-9][a-z0-9-]*)[ \t]*\|", re.M)
SKILL_REFERENCED_SECTION_RE = re.compile(
    r"^##[ \t]+Referenced Standards[^\n]*\n(.*?)(?=^##[ \t]|\Z)",
    re.M | re.S,
)
LOOSE_ID_RE = re.compile(r"PAISL-[A-Za-z]{1,8}-\d{1,5}")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def heading_key(heading: str) -> str:
    """Return the English part of a bilingual heading."""
    return heading.split("/")[0].strip()


def skill_frontmatter(text: str, errors: list) -> dict | None:
    """Parse the YAML frontmatter of a Skill definition."""
    match = SKILL_FRONTMATTER_RE.match(text)

    if not match:
        errors.append(
            "SKILL.md must start with YAML frontmatter on the first line"
        )
        return None

    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        errors.append(f"Invalid frontmatter: {exc}")
        return None

    if not isinstance(data, dict):
        errors.append("Frontmatter must be a mapping")
        return None

    return data


def referenced_standard_ids(text: str, id_pattern: re.Pattern) -> list[str]:
    """Return the standard IDs referenced by a Skill definition."""
    section = SKILL_REFERENCED_SECTION_RE.search(text)

    if not section:
        return []

    body = section.group(1)

    return sorted({
        match.group(0) for match in id_pattern.finditer(body)
    })


def malformed_standard_ids(text: str, id_pattern: re.Pattern) -> list[str]:
    """Return ID shaped references that do not match the Schema pattern."""
    section = SKILL_REFERENCED_SECTION_RE.search(text)

    if not section:
        return []

    body = section.group(1)

    return sorted(
        candidate
        for candidate in set(LOOSE_ID_RE.findall(body))
        if not id_pattern.fullmatch(candidate)
    )


def validate_skills(
    root: Path,
    schema: dict,
    catalog: dict,
    errors: list,
    warnings: list,
) -> int:
    """Check that every Skill resolves to known Standard IDs."""
    index = {
        entry["id"]: entry
        for entry in catalog.get("standards", [])
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }

    id_pattern = re.compile(
        schema["properties"]["id"]["pattern"].strip("^$")
    )

    skills_root = root / "skills"

    if not skills_root.is_dir():
        errors.append("Missing skills/ directory")
        return 0

    skill_files = sorted(
        path for path in skills_root.glob("*/SKILL.md") if path.is_file()
    )

    directories = {
        path.name
        for path in skills_root.iterdir()
        if path.is_dir()
    }

    checked = 0

    for path in skill_files:
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")

        front = skill_frontmatter(text, errors)

        if front is None:
            continue

        checked += 1

        for key in ("name", "description", "version"):
            value = front.get(key)

            if not isinstance(value, str) or not value.strip():
                errors.append(f"{relative}: missing frontmatter '{key}'")

        name = front.get("name")

        if isinstance(name, str) and name != path.parent.name:
            errors.append(
                f"{relative}: frontmatter name '{name}' "
                f"does not match directory '{path.parent.name}'"
            )

        version = front.get("version")

        if isinstance(version, str) and not SEMVER_RE.match(version):
            errors.append(f"{relative}: invalid Skill version: {version}")

        if "SPDX-License-Identifier" not in text:
            warnings.append(f"{relative}: missing SPDX-License-Identifier")

        headings = SKILL_HEADING_RE.findall(text)
        keys = {heading_key(heading) for heading in headings}

        for label, accepted in SKILL_REQUIRED_SECTIONS.items():
            if not any(name_ in keys for name_ in accepted):
                errors.append(
                    f"{relative}: missing required section "
                    f"({', '.join(accepted)})"
                )

        for heading in headings:
            if "/" not in heading:
                warnings.append(
                    f"{relative}: section heading is not bilingual: {heading}"
                )

        for candidate in malformed_standard_ids(text, id_pattern):
            errors.append(
                f"{relative}: malformed standard ID reference: {candidate}"
            )

        for candidate in referenced_standard_ids(text, id_pattern):
            if candidate not in index:
                errors.append(
                    f"{relative}: unknown standard ID reference: {candidate}"
                )
                continue

            entry = index[candidate]
            target = root / entry["path"]

            if not target.is_file():
                errors.append(
                    f"{relative}: referenced standard file missing: "
                    f"{entry['path']}"
                )
                continue

            data = read_yaml(target)

            if isinstance(data, dict) and data.get("id") != candidate:
                errors.append(
                    f"{relative}: referenced standard {candidate} "
                    f"declares ID {data.get('id')}"
                )

    validate_skill_docs(root, directories, errors, warnings)

    return checked


def validate_skill_docs(
    root: Path,
    directories: set,
    errors: list,
    warnings: list,
) -> None:
    """Check that the READMEs list exactly the existing Skills."""
    for readme in ("README.md", "README.zh-CN.md"):
        path = root / readme

        if not path.is_file():
            continue

        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")

        listed = set(SKILL_TABLE_ROW_RE.findall(text))

        for name in sorted(listed - directories):
            errors.append(f"{relative}: unknown Skill listed: {name}")

        for name in sorted(directories - listed):
            warnings.append(f"{relative}: Skill not listed: {name}")
