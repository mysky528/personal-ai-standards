# SPDX-License-Identifier: MIT
"""Catalog and Standard registry resolution.

This module owns everything that turns a Catalog entry into a
Standard definition, plus the Catalog metadata checks that are not
covered by the Standard Schema.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from .paths import read_yaml
from .schema_validation import (
    append_rule_id_errors,
    append_schema_errors,
    append_source_url_errors,
)

# Category to identifier prefix, per the Standard Schema.
PREFIXES = {
    "communication": "COMM",
    "reasoning": "REAS",
    "productivity": "PROD",
    "visualization": "VIS",
    "verification": "VER",
    "engineering": "ENG",
}

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

CHANGELOG_RELEASE_RE = re.compile(
    r"^##\s+\[(\d+\.\d+\.\d+)\]", re.M
)

README_VERSION_PATTERNS = (
    ("README.md", r"\*\*Version:\*\*\s*(\d+\.\d+\.\d+)"),
    ("README.zh-CN.md", r"\*\*版本：\*\*\s*(\d+\.\d+\.\d+)"),
)


def latest_release_version(root: Path) -> str | None:
    """Return the newest release version declared in the CHANGELOG."""
    changelog = root / "CHANGELOG.md"

    if not changelog.is_file():
        return None

    versions = CHANGELOG_RELEASE_RE.findall(
        changelog.read_text(encoding="utf-8")
    )

    if not versions:
        return None

    return max(
        versions,
        key=lambda value: tuple(map(int, value.split("."))),
    )


def load_catalog(root: Path) -> dict:
    """Load the Catalog and verify its top level shape."""
    catalog = read_yaml(root / "catalog" / "standards.yaml")

    if not isinstance(catalog, dict):
        raise ValueError("Catalog must be a mapping")

    if not isinstance(catalog.get("standards"), list):
        raise ValueError("Catalog standards must be a list")

    return catalog


def validate_standards(
    root: Path,
    validator,
    catalog: dict,
    errors: list,
    warnings: list,
) -> int:
    """Validate every Catalog entry against the Schema and the registry."""
    checked = 0
    seen_ids = set()
    seen_paths = set()
    standards_root = (root / "standards").resolve()

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

        path = (root / relative).resolve()

        if not path.is_relative_to(standards_root):
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

        append_schema_errors(data, validator, relative, errors)

        if data.get("id") != sid:
            errors.append(f"{relative}: catalog ID mismatch")

        category = data.get("category")
        prefix = PREFIXES.get(category)

        if prefix and not sid.startswith(f"PAISL-{prefix}-"):
            errors.append(f"{relative}: ID/category mismatch")

        if category and path.parent.name != category:
            errors.append(f"{relative}: directory/category mismatch")

        append_rule_id_errors(data, relative, errors)

        append_source_url_errors(data, relative, errors)

        if data.get("status") == "verified":
            warnings.append(f"{relative}: verified requires evidence review")

    actual_files = {
        path.relative_to(root).as_posix()
        for path in (root / "standards").rglob("*.yaml")
    }

    for relative in sorted(actual_files - seen_paths):
        errors.append(f"Uncataloged standard: {relative}")

    return checked


def validate_catalog_meta(
    root: Path,
    schema: dict,
    catalog: dict,
    errors: list,
    warnings: list,
) -> None:
    """Check Catalog metadata that is not covered by the Schema."""
    version = catalog.get("catalog_version")

    if not isinstance(version, str) or not SEMVER_RE.match(version):
        errors.append(f"Invalid catalog_version: {version!r}")

    # The Catalog stores only ID and path. Category and number are
    # derived from the ID. Standard versions are tracked per standard
    # and are independent of the library release version.
    prefix_to_category = {
        prefix: category for category, prefix in PREFIXES.items()
    }
    numbers: dict = {}

    for entry in catalog.get("standards", []):
        if not isinstance(entry, dict):
            continue

        sid = entry.get("id")

        if not isinstance(sid, str):
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

    for category, values in sorted(numbers.items()):
        values = sorted(values)

        if values and values != list(range(1, len(values) + 1)):
            warnings.append(
                f"Non-contiguous standard numbering in {category}: {values}"
            )

    categories_path = root / "catalog" / "categories.yaml"

    if categories_path.is_file():
        try:
            declared = read_yaml(categories_path)
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

    if isinstance(version, str):
        release = latest_release_version(root)

        if release and version != release:
            errors.append(
                f"catalog_version {version} does not match "
                f"the latest release {release}"
            )

        for readme, pattern in README_VERSION_PATTERNS:
            path = root / readme

            if not path.is_file():
                continue

            match = re.search(
                pattern, path.read_text(encoding="utf-8")
            )

            if match and match.group(1) != version:
                errors.append(
                    f"{readme}: version {match.group(1)} does not match "
                    f"catalog_version {version}"
                )
