# SPDX-License-Identifier: MIT
"""Unit tests for the v0.2.0 data contracts.

Each contract is checked with a valid reference instance and with
instances that must be rejected.
"""

from __future__ import annotations

import json
import pathlib

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"

# The contract, the reference instance, and the instances that must
# be rejected.
CONTRACTS = {
    "evidence": (
        ROOT / "evidence" / "records" / "EVD-0001.yaml",
        [
            "missing source",
            "unknown source type",
            "reviewed without a reviewer",
            "reviewed without a rationale",
            "malformed identifier",
            "unknown property",
        ],
    ),
    "rule-evidence": (
        ROOT / "evidence" / "links" / "PAISL-ENG-001.yaml",
        [
            "unknown standard",
            "unknown rule identifier",
            "unknown evidence identifier",
            "unknown relationship",
            "empty evidence list",
        ],
    ),
    "review": (
        ROOT / "governance" / "reviews" / "REV-0001.yaml",
        [
            "unknown status",
            "unknown decision",
            "malformed digest",
            "empty reviewer",
        ],
    ),
    "semantic-review": (
        ROOT / "governance" / "reviews" / "SEM-0001.yaml",
        [
            "unknown outcome",
            "unknown language",
            "missing bilingual summary",
            "malformed finding identifier",
        ],
    ),
    "evaluation-case": (
        ROOT / "evaluations" / "cases" / "COMM-001-CASE-001.yaml",
        [
            "unknown evaluator",
            "unknown severity",
            "absolute fixture path",
            "empty assertion list",
            "unknown standard",
        ],
    ),
    "evaluation-suite": (
        ROOT / "evaluations" / "suites" / "core-regression.yaml",
        [
            "malformed identifier",
            "missing bilingual title",
            "unknown case identifier",
            "empty case list",
        ],
    ),
    "conflict": (
        ROOT / "governance" / "conflicts" / "CONFLICT-0001.yaml",
        [
            "single rule",
            "unknown classification",
            "unknown status",
            "resolved without a reviewer",
        ],
    ),
}


def load_validator(name: str) -> Draft202012Validator:
    schema = json.loads(
        (SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def load_instance(path: pathlib.Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_every_contract_has_a_schema():
    """Each contract must have a schema file."""
    for name in CONTRACTS:
        assert (SCHEMAS / f"{name}.schema.json").is_file(), (
            f"missing schema for contract {name}"
        )


@pytest.mark.parametrize("name", sorted(CONTRACTS))
def test_reference_instance_is_valid(name):
    """The reference instance must satisfy its contract."""
    instance_path, _ = CONTRACTS[name]
    validator = load_validator(name)
    instance = load_instance(instance_path)

    errors = list(validator.iter_errors(instance))

    assert not errors, [
        f"{instance_path.name}: {error.message}" for error in errors
    ]


def _mutate(name: str) -> list:
    """Return one invalid instance per contract."""
    instances = []

    if name == "evidence":
        base = load_instance(CONTRACTS[name][0])
        missing = json.loads(json.dumps(base))
        del missing["source"]
        instances.append(missing)
        bad_type = json.loads(json.dumps(base))
        bad_type["source"]["type"] = "blog"
        instances.append(bad_type)
        no_reviewer = json.loads(json.dumps(base))
        no_reviewer["review"] = {
            "status": "reviewed",
            "reviewed_by": None,
            "reviewed_at": None,
            "rationale": None,
        }
        instances.append(no_reviewer)
        no_rationale = json.loads(json.dumps(base))
        no_rationale["review"]["status"] = "reviewed"
        no_rationale["review"]["reviewed_by"] = "reviewer-id"
        no_rationale["review"]["reviewed_at"] = "2026-11-21T12:00:00Z"
        instances.append(no_rationale)
        bad_id = json.loads(json.dumps(base))
        bad_id["id"] = "EVIDENCE-1"
        instances.append(bad_id)
        extra = json.loads(json.dumps(base))
        extra["unexpected"] = True
        instances.append(extra)

    elif name == "rule-evidence":
        base = load_instance(CONTRACTS[name][0])
        bad_standard = json.loads(json.dumps(base))
        bad_standard["standard_id"] = "PAISL-XXX-001"
        instances.append(bad_standard)
        bad_rule = json.loads(json.dumps(base))
        bad_rule["rules"][0]["rule_id"] = "R1"
        instances.append(bad_rule)
        bad_evidence = json.loads(json.dumps(base))
        bad_evidence["rules"][0]["evidence"][0]["evidence_id"] = "EVD-99"
        instances.append(bad_evidence)
        bad_relation = json.loads(json.dumps(base))
        bad_relation["rules"][0]["evidence"][0]["relationship"] = "proves"
        instances.append(bad_relation)
        empty = json.loads(json.dumps(base))
        empty["rules"][0]["evidence"] = []
        instances.append(empty)

    elif name == "review":
        base = load_instance(CONTRACTS[name][0])
        bad_status = json.loads(json.dumps(base))
        bad_status["to_status"] = "approved"
        instances.append(bad_status)
        bad_decision = json.loads(json.dumps(base))
        bad_decision["decision"] = "maybe"
        instances.append(bad_decision)
        bad_digest = json.loads(json.dumps(base))
        bad_digest["reviewed_content_sha256"] = "not-a-digest"
        instances.append(bad_digest)
        no_reviewer = json.loads(json.dumps(base))
        no_reviewer["reviewer"] = ""
        instances.append(no_reviewer)

    elif name == "semantic-review":
        base = load_instance(CONTRACTS[name][0])
        bad_outcome = json.loads(json.dumps(base))
        bad_outcome["outcome"] = "approved"
        instances.append(bad_outcome)
        bad_language = json.loads(json.dumps(base))
        bad_language["languages"] = ["en", "fr"]
        instances.append(bad_language)
        missing_zh = json.loads(json.dumps(base))
        del missing_zh["summary"]["zh-CN"]
        instances.append(missing_zh)
        bad_finding = json.loads(json.dumps(base))
        bad_finding["findings"][0]["id"] = "F001"
        instances.append(bad_finding)

    elif name == "evaluation-case":
        base = load_instance(CONTRACTS[name][0])
        bad_evaluator = json.loads(json.dumps(base))
        bad_evaluator["assertions"][0]["evaluator"] = "execute_python"
        instances.append(bad_evaluator)
        bad_severity = json.loads(json.dumps(base))
        bad_severity["assertions"][0]["severity"] = "critical"
        instances.append(bad_severity)
        absolute = json.loads(json.dumps(base))
        absolute["fixture"]["input"] = "/etc/passwd"
        instances.append(absolute)
        empty = json.loads(json.dumps(base))
        empty["assertions"] = []
        instances.append(empty)
        bad_standard = json.loads(json.dumps(base))
        bad_standard["standard_id"] = "PAISL-ZZZ-001"
        instances.append(bad_standard)

    elif name == "evaluation-suite":
        base = load_instance(CONTRACTS[name][0])
        bad_id = json.loads(json.dumps(base))
        bad_id["id"] = "Core Regression"
        instances.append(bad_id)
        missing_zh = json.loads(json.dumps(base))
        del missing_zh["title"]["zh-CN"]
        instances.append(missing_zh)
        bad_case = json.loads(json.dumps(base))
        bad_case["cases"] = ["COMM-001-CASE-99"]
        instances.append(bad_case)
        empty = json.loads(json.dumps(base))
        empty["cases"] = []
        instances.append(empty)

    elif name == "conflict":
        base = load_instance(CONTRACTS[name][0])
        single = json.loads(json.dumps(base))
        single["rules"] = single["rules"][:1]
        instances.append(single)
        bad_classification = json.loads(json.dumps(base))
        bad_classification["classification"] = "certain"
        instances.append(bad_classification)
        bad_status = json.loads(json.dumps(base))
        bad_status["status"] = "closed"
        instances.append(bad_status)
        resolved = json.loads(json.dumps(base))
        resolved["status"] = "resolved"
        resolved["resolution"] = "Reviewed and accepted."
        instances.append(resolved)

    return instances


@pytest.mark.parametrize("name", sorted(CONTRACTS))
def test_invalid_instances_are_rejected(name):
    """Every invalid instance must be refused by its contract."""
    validator = load_validator(name)
    instances = _mutate(name)

    assert instances, f"contract {name} has no negative cases"

    for index, instance in enumerate(instances):
        assert list(validator.iter_errors(instance)), (
            f"{name}: invalid instance {index} was accepted"
        )


def test_schemas_check_shape_not_existence():
    """Identifiers are checked for shape, not for existence.

    Whether a referenced Standard, rule, evidence record, or
    evaluation case exists is a referential integrity question. The
    validator answers it in a later work package; the contract only
    constrains the shape of the reference.
    """
    validator = load_validator("rule-evidence")
    instance = load_instance(CONTRACTS["rule-evidence"][0])

    instance["rules"][0]["evidence"][0]["evidence_id"] = "EVD-9999"

    assert not list(validator.iter_errors(instance))


def test_evidence_review_requires_inspection():
    """A reviewed record must carry a reviewer, a time, and a reason."""
    validator = load_validator("evidence")
    instance = load_instance(CONTRACTS["evidence"][0])

    instance["review"] = {
        "status": "reviewed",
        "reviewed_by": "reviewer-id",
        "reviewed_at": "2026-11-21T12:00:00Z",
        "rationale": "Source inspected.",
    }

    assert not list(validator.iter_errors(instance))


def test_conflict_resolution_requires_a_reviewer():
    """A resolved conflict must carry both a rationale and a reviewer."""
    validator = load_validator("conflict")
    instance = load_instance(CONTRACTS["conflict"][0])

    instance["status"] = "resolved"
    instance["resolution"] = "Reviewed and accepted."

    assert list(validator.iter_errors(instance))

    instance["reviewer"] = "reviewer-id"

    assert not list(validator.iter_errors(instance))
