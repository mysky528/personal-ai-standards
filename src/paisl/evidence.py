# SPDX-License-Identifier: MIT
"""Evidence registry.

This module owns the rules that span evidence records and the links
that connect them to Standard rules. The shape of a record is
constrained by its schema; the relationships between records are
checked here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .paths import is_reference

SUPPORT = "supports"
CONTEXT = "context"
CONTRADICTS = "contradicts"

# Only a reviewed record that supports a rule can satisfy the
# evidence requirement of a verified Standard.
QUALIFYING_RELATIONSHIPS = (SUPPORT,)


@dataclass
class RuleEvidence:
    """The evidence that is linked to one rule."""

    standard_id: str
    rule_id: str
    links: list = field(default_factory=list)

    @property
    def supporting(self) -> list:
        return [
            link for link in self.links
            if link.get("relationship") == SUPPORT
        ]

    @property
    def contradicting(self) -> list:
        return [
            link for link in self.links
            if link.get("relationship") == CONTRADICTS
        ]


def evidence_records(records: list) -> dict:
    """Index the evidence records by identifier."""
    return {
        record.id: record
        for record in records
        if record.kind == "evidence"
        and record.id
        and not is_reference(record)
    }


def rule_evidence(records: list) -> dict:
    """Group the evidence links by Standard and rule."""
    grouped: dict = {}

    for record in records:
        if record.kind != "rule-evidence":
            continue

        standard_id = record.data.get("standard_id")

        if not isinstance(standard_id, str):
            continue

        for rule in record.data.get("rules", []):
            if not isinstance(rule, dict):
                continue

            rule_id = rule.get("rule_id")

            if not isinstance(rule_id, str):
                continue

            key = (standard_id, rule_id)
            entry = grouped.setdefault(
                key, RuleEvidence(standard_id, rule_id)
            )
            entry.links.extend(
                link for link in rule.get("evidence", [])
                if isinstance(link, dict)
            )

    return grouped


def check_evidence(records: list, errors: list, warnings: list) -> None:
    """Check the rules that span evidence records and their links."""
    index = evidence_records(records)

    for record in records:
        if record.kind != "rule-evidence":
            continue

        relative = record.relative

        for rule in record.data.get("rules", []):
            if not isinstance(rule, dict):
                continue

            rule_id = rule.get("rule_id")

            for link in rule.get("evidence", []):
                if not isinstance(link, dict):
                    continue

                evidence_id = link.get("evidence_id")
                relationship = link.get("relationship")
                target = index.get(evidence_id)

                if target is None:
                    continue

                status = (
                    target.data.get("review", {}) or {}
                ).get("status")

                if status == "rejected":
                    errors.append(
                        f"{relative}: rejected evidence {evidence_id} "
                        f"is linked to rule {rule_id}"
                    )
                elif relationship == CONTRADICTS:
                    warnings.append(
                        f"{relative}: rule {rule_id} is contradicted by "
                        f"{evidence_id}; the conflict needs a review"
                    )


def evidence_coverage(records: list, root=None) -> dict:
    """Describe how well the rules of each Standard are supported.

    The rules come from the Standard definitions, not from the
    links. A rule that nobody linked is uncovered, and the coverage
    has to show it, otherwise the gate cannot see it.
    """
    index = evidence_records(records)
    grouped = rule_evidence(records)

    rules_by_standard: dict = {}

    if root is not None:
        rules_by_standard = _standard_rules(root, records)

    standards: dict = {}

    keys = set(grouped)

    for standard_id, rule_ids in rules_by_standard.items():
        for rule_id in rule_ids:
            keys.add((standard_id, rule_id))

    for key in sorted(keys):
        standard_id, rule_id = key
        entry = grouped.get(key) or RuleEvidence(standard_id, rule_id)
        reviewed_supporting = 0
        supporting = entry.supporting
        context = [
            link for link in entry.links
            if link.get("relationship") == CONTEXT
        ]

        for link in supporting:
            target = index.get(link.get("evidence_id"))

            if target is None:
                continue

            review = target.data.get("review", {}) or {}

            if review.get("status") == "reviewed":
                reviewed_supporting += 1

        rules = standards.setdefault(standard_id, {"rules": {}})
        rules["rules"][rule_id] = {
            "supporting": len(supporting),
            "reviewed_supporting": reviewed_supporting,
            "context": len(context),
            "contradicting": len(entry.contradicting),
            "sufficient_for_verification": reviewed_supporting > 0,
        }

    for standard in standards.values():
        rules = standard["rules"].values()
        standard["rules_total"] = len(rules)
        standard["rules_with_reviewed_support"] = len(
            [rule for rule in rules if rule["sufficient_for_verification"]]
        )
        standard["sufficient_for_verification"] = all(
            rule["sufficient_for_verification"] for rule in rules
        ) if rules else False

    return {
        "standards": standards,
        "summary": {
            "standards_with_links": len(standards),
            "rules_total": sum(
                standard["rules_total"] for standard in standards.values()
            ),
            "rules_with_reviewed_support": sum(
                standard["rules_with_reviewed_support"]
                for standard in standards.values()
            ),
        },
    }


def _standard_rules(root, records: list) -> dict:
    """Return the rule identifiers of every Standard in the repository."""
    import yaml

    from .registry import build_standard_index, load_catalog

    try:
        catalog = load_catalog(root)
    except (OSError, ValueError):
        return {}

    index = build_standard_index(root, catalog)
    rules: dict = {}

    for sid, entry in sorted(index.items()):
        path = root / entry["path"]

        if not path.is_file():
            continue

        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            continue

        if not isinstance(data, dict):
            continue

        rule_ids = [
            rule.get("id")
            for rule in data.get("rules", [])
            if isinstance(rule, dict) and isinstance(rule.get("id"), str)
        ]

        if rule_ids:
            rules[sid] = rule_ids

    return rules
