#!/usr/bin/env python3
"""PAISL v0.1.0 standard registry validator."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/standard.schema.json"
CATALOG = ROOT / "catalog/standards.yaml"
STANDARDS = ROOT / "standards"

PREFIXES = {
    "communication": "COMM",
    "reasoning": "REAS",
    "productivity": "PROD",
    "visualization": "VIS",
    "verification": "VER",
    "engineering": "ENG",
}


def main() -> int:
    errors = []
    warnings = []
    checked = 0

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

    seen_ids = set()
    seen_paths = set()

    for entry in entries:
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
            location = ".".join(
                map(str, issue.absolute_path)
            )
            errors.append(
                f"{relative} [{location}]: {issue.message}"
            )

        if data.get("id") != sid:
            errors.append(f"{relative}: catalog ID mismatch")

        category = data.get("category")
        prefix = PREFIXES.get(category)

        if prefix and not sid.startswith(f"PAISL-{prefix}-"):
            errors.append(f"{relative}: ID/category mismatch")

        if category and path.parent.name != category:
            errors.append(
                f"{relative}: directory/category mismatch"
            )

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
                errors.append(
                    f"{relative}: invalid source URL at {index}"
                )
                continue

            parsed = urlparse(url)

            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                errors.append(
                    f"{relative}: invalid source URL: {url}"
                )

        if data.get("status") == "verified":
            warnings.append(
                f"{relative}: verified requires evidence review"
            )

    actual_files = {
        path.relative_to(ROOT).as_posix()
        for path in STANDARDS.rglob("*.yaml")
    }

    for relative in sorted(actual_files - seen_paths):
        errors.append(f"Uncataloged standard: {relative}")

    print("\n=== PAISL Validation Report ===")
    print(f"Standards checked: {checked}")
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
