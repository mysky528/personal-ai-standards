# SPDX-License-Identifier: MIT
"""JSON Schema validation for Standard definitions."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, FormatChecker


def build_validator(schema: dict) -> Draft202012Validator:
    """Build a validator for the Standard schema."""
    Draft202012Validator.check_schema(schema)

    return Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )


def append_schema_errors(
    data: dict,
    validator: Draft202012Validator,
    relative: str,
    errors: list,
) -> None:
    """Append every schema violation found in a Standard definition."""
    for issue in validator.iter_errors(data):
        location = ".".join(map(str, issue.absolute_path))
        errors.append(f"{relative} [{location}]: {issue.message}")


def append_rule_id_errors(
    data: dict,
    relative: str,
    errors: list,
) -> None:
    """Append an error when a Standard reuses a rule identifier."""
    rule_ids = []

    for rule in data.get("rules", []):
        if isinstance(rule, dict):
            rule_ids.append(rule.get("id"))

    if len(rule_ids) != len(set(rule_ids)):
        errors.append(f"{relative}: duplicate rule IDs")


def append_source_url_errors(
    data: dict,
    relative: str,
    errors: list,
) -> None:
    """Append an error for every malformed source URL."""
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


def collect_rule_ids(data: dict) -> list:
    """Return the rule identifiers declared by a Standard definition."""
    return [
        rule.get("id")
        for rule in data.get("rules", [])
        if isinstance(rule, dict)
    ]


def as_mapping(value: Any) -> dict:
    """Return value when it is a mapping, otherwise an empty mapping."""
    return value if isinstance(value, dict) else {}
