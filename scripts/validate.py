#!/usr/bin/env python3
"""PAISL v0.1.1 standard registry and Skill reference validator."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "standard.schema.json"
CATALOG = ROOT / "catalog" / "standards.yaml"
CATEGORIES = ROOT / "catalog" / "categories.yaml"
STANDARDS = ROOT / "standards"
SKILLS = ROOT / "skills"

PREFIXES = {
    "communication": "COMM",
    "reasoning": "REAS",
    "productivity": "PROD",
    "visualization": "VIS",
    "verification": "VER",
    "engineering": "ENG",
}

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

SKILL_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n", re.S)
SKILL_HEADING_RE = re.compile(r"^##[ \t]+(.+)$", re.M)
SKILL_TABLE_ROW_RE = re.compile(r"^\|[ \t]*([a-z0-9][a-z0-9-]*)[ \t]*\|", re.M)
LOOSE_ID_RE = re.compile(r"PAISL-[A-Za-z]{1,8}-\d{1,5}")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def heading_key(heading: str) -> str:
    """Return the English part of a bilingual heading."""
    return heading.split("/")[0].strip()


def read_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_standards(
    schema: dict,
    validator: Draft202012Validator,
    catalog: dict,
    errors: list,
    warnings: list,
) -> int:
    checked = 0
    seen_ids = set()
    seen_paths = set()

    for entry in catalog.get("standards", []):
        if not isinstance(entry, dict):
            errors.append("Invalid catalog entry")
            continue

        sid = entry.get("id")
        relative = entry.get("path")

        if not isinstance(sid, str):
            errors.append("Catalog ID must be a string")
            continue

        if not isinstance(relative, str):
            errors.append(f"{sid}: path must be a string")
            continue

        if sid in seen_ids:
            errors.append(f"Duplicate standard ID: {sid}")
        seen_ids.add(sid)

        if relative in seen_paths:
            errors.append(f"Duplicate catalog path: {relative}")
        seen_paths.add(relative)

        path = (ROOT / relative).resolve()

        if not path.is_relative_to(STANDARDS.resolve()):
            errors.append(f"Path outside standards/: {relative}")
            continue

        if not path.is_file():
            errors.append(f"Missing standard file: {relative}")
            continue

        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            errors.append(f"{relative}: YAML error: {exc}")
            continue

        if not isinstance(data, dict):
            errors.append(f"{relative}: expected YAML mapping")
            continue

        checked += 1

        for issue in validator.iter_errors(data):
            location = ".".join(map(str, issue.absolute_path))
            errors.append(f"{relative} [{location}]: {issue.message}")

        if data.get("id") != sid:
            errors.append(f"{relative}: catalog ID mismatch")

        category = data.get("category")
        prefix = PREFIXES.get(category)

        if prefix and not sid.startswith(f"PAISL-{prefix}-"):
            errors.append(f"{relative}: ID/category mismatch")

        if category and path.parent.name != category:
            errors.append(f"{relative}: directory/category mismatch")

        rule_ids = []
        for rule in data.get("rules", []):
            if isinstance(rule, dict):
                rule_ids.append(rule.get("id"))

        if len(rule_ids) != len(set(rule_ids)):
            errors.append(f"{relative}: duplicate rule IDs")

        for index, source in enumerate(data.get("sources", [])):
            if not isinstance(source, dict):
                continue

            url = source.get("url", "")
            if not isinstance(url, str):
                errors.append(f"{relative}: invalid source URL at {index}")
                continue

            parsed = urlparse(url)

            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                errors.append(f"{relative}: invalid source URL: {url}")

        if data.get("status") == "verified":
            warnings.append(f"{relative}: verified requires evidence review")

    actual_files = {
        path.relative_to(ROOT).as_posix()
        for path in STANDARDS.rglob("*.yaml")
    }

    for relative in sorted(actual_files - seen_paths):
        errors.append(f"Uncataloged standard: {relative}")

    return checked


def validate_catalog_meta(
    schema: dict,
    catalog: dict,
    errors: list,
    warnings: list,
) -> None:
    """Check Catalog metadata that is not covered by the Schema."""
    version = catalog.get("catalog_version")

    if not isinstance(version, str) or not SEMVER_RE.match(version):
        errors.append(f"Invalid catalog_version: {version!r}")

    # The Catalog stores only ID and path. Category, number, and version
    # are derived from the ID and the referenced standard file.
    prefix_to_category = {
        prefix: category for category, prefix in PREFIXES.items()
    }
    numbers: dict = {}
    standard_versions = set()

    for entry in catalog.get("standards", []):
        if not isinstance(entry, dict):
            continue

        sid = entry.get("id")
        relative = entry.get("path")

        if not isinstance(sid, str) or not isinstance(relative, str):
            continue

        parts = sid.split("-")

        if len(parts) != 3 or not parts[2].isdigit():
            continue

        prefix = parts[1]
        category = prefix_to_category.get(prefix)

        if category is None:
            errors.append(f"{sid}: unknown ID prefix")
            continue

        numbers.setdefault(category, []).append(int(parts[2]))

        target = ROOT / relative

        if target.is_file():
            data = read_yaml(target)

            if isinstance(data, dict):
                standard_versions.add(data.get("version"))

    for category, values in sorted(numbers.items()):
        values = sorted(values)

        if values and values != list(range(1, len(values) + 1)):
            warnings.append(
                f"Non-contiguous standard numbering in {category}: {values}"
            )

    if CATEGORIES.is_file():
        try:
            declared = read_yaml(CATEGORIES)
        except (OSError, yaml.YAMLError) as exc:
            errors.append(f"catalog/categories.yaml: YAML error: {exc}")
        else:
            keys = set((declared or {}).get("categories", {}))
            allowed = set(schema["properties"]["category"]["enum"])

            for missing in sorted(allowed - keys):
                errors.append(f"catalog/categories.yaml: missing category {missing}")

            for unknown in sorted(keys - allowed):
                errors.append(
                    f"catalog/categories.yaml: unknown category {unknown}"
                )
    else:
        errors.append("Missing catalog/categories.yaml")

    if isinstance(version, str) and standard_versions:
        if version not in standard_versions:
            warnings.append(
                f"catalog_version {version} does not match "
                f"standard version(s) {sorted(v for v in standard_versions if v)}"
            )


def skill_frontmatter(text: str, errors: list) -> dict | None:
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


def validate_skills(
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

    if not SKILLS.is_dir():
        errors.append("Missing skills/ directory")
        return 0

    skill_files = sorted(
        path for path in SKILLS.glob("*/SKILL.md") if path.is_file()
    )

    directories = {
        path.name
        for path in SKILLS.iterdir()
        if path.is_dir()
    }

    checked = 0

    for path in skill_files:
        relative = path.relative_to(ROOT).as_posix()
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

        section = re.search(
            r"^##[ \t]+Referenced Standards[^\n]*\n(.*?)(?=^##[ \t]|\Z)",
            text,
            re.M | re.S,
        )

        if not section:
            continue

        body = section.group(1)

        for candidate in sorted(set(LOOSE_ID_RE.findall(body))):
            if not id_pattern.fullmatch(candidate):
                errors.append(
                    f"{relative}: malformed standard ID reference: {candidate}"
                )

        for candidate in sorted({
            match.group(0) for match in id_pattern.finditer(body)
        }):
            if candidate not in index:
                errors.append(
                    f"{relative}: unknown standard ID reference: {candidate}"
                )
                continue

            entry = index[candidate]
            target = ROOT / entry["path"]

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

    validate_skill_docs(skill_files, directories, errors, warnings)

    return checked


def validate_skill_docs(
    skill_files: list,
    directories: set,
    errors: list,
    warnings: list,
) -> None:
    """Check that the READMEs list exactly the existing Skills."""
    for readme in (ROOT / "README.md", ROOT / "README.zh-CN.md"):
        if not readme.is_file():
            continue

        relative = readme.relative_to(ROOT).as_posix()
        text = readme.read_text(encoding="utf-8")

        listed = set(SKILL_TABLE_ROW_RE.findall(text))

        for name in sorted(listed - directories):
            errors.append(f"{relative}: unknown Skill listed: {name}")

        for name in sorted(directories - listed):
            warnings.append(f"{relative}: Skill not listed: {name}")


def main() -> int:
    errors = []
    warnings = []
    checked = 0
    skills_checked = 0

    try:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)

        validator = Draft202012Validator(
            schema,
            format_checker=FormatChecker(),
        )

        catalog = yaml.safe_load(
            CATALOG.read_text(encoding="utf-8")
        )

        if not isinstance(catalog, dict):
            raise ValueError("Catalog must be a mapping")

        entries = catalog.get("standards")

        if not isinstance(entries, list):
            raise ValueError("Catalog standards must be a list")

    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: Initialization failed: {exc}")
        return 1

    checked = validate_standards(
        schema, validator, catalog, errors, warnings
    )

    validate_catalog_meta(schema, catalog, errors, warnings)

    skills_checked = validate_skills(
        schema, catalog, errors, warnings
    )

    print("\n=== PAISL Validation Report ===")
    print(f"Standards checked: {checked}")
    print(f"Skills checked: {skills_checked}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")

    for message in errors:
        print(f"ERROR: {message}")

    for message in warnings:
        print(f"WARNING: {message}")

    if errors:
        print("\nValidation FAILED")
        return 1

    print("\nValidation PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
