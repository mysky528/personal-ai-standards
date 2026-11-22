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


def skill_reference_map(root: Path, id_pattern: re.Pattern) -> dict:
    """Map every Skill to the Standard IDs it references."""
    skills_root = root / "skills"
    mapping: dict = {}

    if not skills_root.is_dir():
        return mapping

    for path in sorted(skills_root.glob("*/SKILL.md")):
        if not path.is_file():
            continue

        text = path.read_text(encoding="utf-8")
        mapping[path.parent.name] = referenced_standard_ids(text, id_pattern)

    return mapping


def build_coverage(
    root: Path,
    schema: dict,
    catalog: dict,
    records: list,
) -> dict:
    """Describe how completely the repository is covered.

    A standard without a Skill reference is reported, never failed:
    a standard may be intended for direct use.
    """
    id_pattern = re.compile(
        schema["properties"]["id"]["pattern"].strip("^$")
    )

    standard_ids = sorted(
        entry["id"]
        for entry in catalog.get("standards", [])
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    )

    skills = skill_reference_map(root, id_pattern)

    referenced_by_skills: dict = {}

    for skill, ids in skills.items():
        for sid in ids:
            referenced_by_skills.setdefault(sid, []).append(skill)

    evidence_links: dict = {}
    cases: dict = {}
    reviews: dict = {}
    semantic_reviews: dict = {}
    conflicts: dict = {}

    for record in records:
        data = record.data

        if record.kind == "rule-evidence":
            sid = data.get("standard_id")

            if isinstance(sid, str):
                evidence_links.setdefault(sid, []).append(record.relative)

        elif record.kind == "evaluation-case":
            sid = data.get("standard_id")

            if isinstance(sid, str):
                cases.setdefault(sid, []).append(record.relative)

        elif record.kind == "review":
            sid = data.get("standard_id")

            if isinstance(sid, str):
                reviews.setdefault(sid, []).append(record.relative)

        elif record.kind == "semantic-review":
            sid = data.get("standard_id")

            if isinstance(sid, str):
                semantic_reviews.setdefault(sid, []).append(record.relative)

        elif record.kind == "conflict":
            for rule in data.get("rules", []):
                if not isinstance(rule, dict):
                    continue

                sid = rule.get("standard_id")

                if isinstance(sid, str):
                    conflicts.setdefault(sid, []).append(record.relative)

    def split(mapping: dict) -> tuple:
        with_ = [sid for sid in standard_ids if mapping.get(sid)]
        without = [sid for sid in standard_ids if not mapping.get(sid)]
        return with_, without

    skills_with, skills_without = split(referenced_by_skills)
    links_with, links_without = split(evidence_links)
    cases_with, cases_without = split(cases)
    reviews_with, reviews_without = split(reviews)
    semantic_with, semantic_without = split(semantic_reviews)

    linked_evidence = {
        link.get("evidence_id")
        for record in records
        if record.kind == "rule-evidence"
        for rule in record.data.get("rules", [])
        if isinstance(rule, dict)
        for link in rule.get("evidence", [])
        if isinstance(link, dict)
    }

    evidence_records = [
        record for record in records if record.kind == "evidence"
    ]

    unlinked_evidence = sorted(
        record.id
        for record in evidence_records
        if record.id not in linked_evidence
    )

    unresolved_blocking = sorted(
        record.relative
        for record in records
        if record.kind == "conflict"
        and record.data.get("classification") == "confirmed"
        and record.data.get("status") == "open"
    )

    return {
        "standards": {
            "total": len(standard_ids),
            "with_skill_references": len(skills_with),
            "without_skill_references": skills_without,
            "with_evidence_links": len(links_with),
            "without_evidence_links": links_without,
            "with_evaluation_cases": len(cases_with),
            "without_evaluation_cases": cases_without,
            "with_lifecycle_review": len(reviews_with),
            "without_lifecycle_review": reviews_without,
            "with_semantic_review": len(semantic_with),
            "without_semantic_review": semantic_without,
            "with_conflict_records": len(
                [sid for sid in standard_ids if conflicts.get(sid)]
            ),
        },
        "skills": {
            "total": len(skills),
            "with_standard_references": len(
                [name for name, ids in skills.items() if ids]
            ),
            "without_standard_references": sorted(
                name for name, ids in skills.items() if not ids
            ),
            "references": skills,
        },
        "evidence": {
            "total": len(evidence_records),
            "linked": len(linked_evidence),
            "unlinked": unlinked_evidence,
        },
        "conflicts": {
            "total": len(
                [record for record in records if record.kind == "conflict"]
            ),
            "unresolved_confirmed_blocking": unresolved_blocking,
        },
    }
