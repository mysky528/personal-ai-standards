# SPDX-License-Identifier: MIT
"""Loading and resolving the v0.2.0 records.

The registry must reject a record that points at something that does
not exist, and the coverage report must describe what is missing
without failing the build.
"""

from __future__ import annotations

import json
import pathlib

import pytest
import yaml

from paisl.coverage import build_coverage
from paisl.registry import (
    build_standard_index,
    load_catalog,
    load_records,
    resolve_references,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _schema(root: pathlib.Path) -> dict:
    return json.loads(
        (root / "schemas" / "standard.schema.json").read_text(
            encoding="utf-8"
        )
    )


def _write(path: pathlib.Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _errors(root: pathlib.Path) -> list:
    errors: list = []
    catalog = load_catalog(root)
    records = load_records(root, errors)
    resolve_references(
        root, records, build_standard_index(root, catalog), errors
    )
    return errors


def test_records_are_loaded(repo_root):
    """Every reference instance must be discovered."""
    errors: list = []
    records = load_records(repo_root, errors)

    kinds = sorted({record.kind for record in records})

    assert not errors
    assert kinds == [
        "conflict",
        "evaluation-case",
        "evaluation-suite",
        "evidence",
        "review",
        "rule-evidence",
        "semantic-review",
    ]


def test_reference_instances_resolve(repo_root):
    """The reference instances must resolve against the repository."""
    errors = _errors(repo_root)

    assert not errors


def test_unknown_standard_reference_is_rejected(repo_copy):
    """A link to a Standard that does not exist must be reported."""
    path = repo_copy / "evidence" / "links" / "PAISL-ENG-001.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["standard_id"] = "PAISL-ENG-999"
    _write(path, data)

    errors = _errors(repo_copy)

    assert any(
        "unknown standard reference: PAISL-ENG-999" in message
        for message in errors
    )


def test_unknown_rule_reference_is_rejected(repo_copy):
    """A link to a rule that does not exist must be reported."""
    path = repo_copy / "evidence" / "links" / "PAISL-ENG-001.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["rules"][0]["rule_id"] = "R009"
    _write(path, data)

    errors = _errors(repo_copy)

    assert any(
        "unknown rule reference: R009" in message for message in errors
    )


def test_unknown_evidence_reference_is_rejected(repo_copy):
    """A link to an evidence record that does not exist is reported."""
    path = repo_copy / "evidence" / "links" / "PAISL-ENG-001.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["rules"][0]["evidence"][0]["evidence_id"] = "EVD-9999"
    _write(path, data)

    errors = _errors(repo_copy)

    assert any(
        "unknown evidence reference: EVD-9999" in message
        for message in errors
    )


def test_unknown_evaluation_case_reference_is_rejected(repo_copy):
    """A suite that names a case that does not exist is reported."""
    path = repo_copy / "evaluations" / "suites" / "core-regression.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["cases"] = ["COMM-001-CASE-999"]
    _write(path, data)

    errors = _errors(repo_copy)

    assert any(
        "unknown evaluation case reference: COMM-001-CASE-999" in message
        for message in errors
    )


def test_fixture_path_outside_the_repository_is_rejected(repo_copy):
    """A fixture that points outside the repository is reported."""
    path = repo_copy / "evaluations" / "cases" / "COMM-001-CASE-001.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["fixture"]["input"] = "../outside.txt"
    _write(path, data)

    errors = _errors(repo_copy)

    assert any(
        "fixture path escapes the repository" in message
        for message in errors
    )


def test_missing_fixture_file_is_rejected(repo_copy):
    """A fixture that does not exist is reported."""
    path = repo_copy / "evaluations" / "cases" / "COMM-001-CASE-001.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["fixture"]["output"] = "evaluations/fixtures/absent.txt"
    _write(path, data)

    errors = _errors(repo_copy)

    assert any(
        "fixture file missing: evaluations/fixtures/absent.txt" in message
        for message in errors
    )


def test_record_that_breaks_its_contract_is_rejected(repo_copy):
    """A record that violates its contract is reported."""
    path = repo_copy / "governance" / "conflicts" / "CONFLICT-0001.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["status"] = "closed"
    _write(path, data)

    errors = _errors(repo_copy)

    assert any("CONFLICT-0001.yaml" in message for message in errors)


def test_unknown_record_kind_is_rejected(repo_copy):
    """A record with an unknown identifier prefix is reported."""
    path = repo_copy / "governance" / "reviews" / "ZZZ-0001.yaml"
    _write(path, {"id": "ZZZ-0001", "schema_version": "0.2.0"})

    errors = _errors(repo_copy)

    assert any("unknown record kind" in message for message in errors)


def test_coverage_reports_missing_links_without_failing(repo_root):
    """A standard without a Skill reference is reported, not failed."""
    catalog = load_catalog(repo_root)
    errors: list = []
    records = load_records(repo_root, errors)
    coverage = build_coverage(
        repo_root, _schema(repo_root), catalog, records
    )

    assert not errors
    assert coverage["standards"]["total"] == 12
    assert coverage["standards"]["without_skill_references"] == []
    assert coverage["standards"]["with_evidence_links"] == 1
    assert "PAISL-ENG-001" not in coverage["standards"]["without_evidence_links"]
    assert "PAISL-COMM-001" in coverage["standards"]["without_evidence_links"]


def test_coverage_reports_a_standard_without_skill_references(repo_copy):
    """Removing every reference to a Standard is reported."""
    # PAISL-COMM-003 is referenced by ste-writing only.
    path = repo_copy / "skills" / "ste-writing" / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("- PAISL-COMM-003", "- (removed)"), encoding="utf-8"
    )

    catalog = load_catalog(repo_copy)
    errors: list = []
    records = load_records(repo_copy, errors)
    coverage = build_coverage(
        repo_copy, _schema(repo_copy), catalog, records
    )

    assert "PAISL-COMM-003" in coverage["standards"]["without_skill_references"]
    assert coverage["standards"]["with_skill_references"] == 11
