# SPDX-License-Identifier: MIT
"""Conflicts and bilingual review.

Two kinds of conflict handling live here.

The first is explicit. A conflict record is a declaration by a
person that two rules may contradict each other. Such a record is
only meaningful once a human looked at it.

The second is a candidate. The tool compares rules by deterministic
metadata, the action verb and the wording, and reports the pairs
that look alike. A candidate is not a contradiction. Wording that
resembles wording is a reason to look, never a proof, and the report
says so.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .paths import is_reference

# Words that carry no meaning when they start an instruction.
FUNCTION_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "if", "in", "is", "it", "of", "on", "or", "that", "the", "this",
    "to", "when", "with",
}

# A pair of rules needs a strong wording overlap to be a candidate.
WORD_OVERLAP_THRESHOLD = 0.5

# A pair of rules needs a strong wording overlap in Chinese too.
BIGRAM_OVERLAP_THRESHOLD = 0.5


@dataclass
class Candidate:
    """A pair of rules that a human should look at."""

    first: str
    second: str
    signals: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "first": self.first,
            "second": self.second,
            "signals": list(self.signals),
        }


def _instructions(root: Path, standard_index: dict) -> dict:
    """Read the instruction of every rule of every Standard."""
    import yaml

    instructions: dict = {}

    for sid, entry in sorted(standard_index.items()):
        path = root / entry["path"]

        if not path.is_file():
            continue

        data = yaml.safe_load(path.read_text(encoding="utf-8"))

        if not isinstance(data, dict):
            continue

        for rule in data.get("rules", []):
            if not isinstance(rule, dict):
                continue

            # A Standard names its rules with "id"; a conflict record
            # names them with "rule_id".
            rule_id = rule.get("id")
            instruction = rule.get("instruction")

            if not isinstance(rule_id, str):
                continue

            if not isinstance(instruction, dict):
                continue

            instructions[(sid, rule_id)] = {
                "en": instruction.get("en", ""),
                "zh-CN": instruction.get("zh-CN", ""),
            }

    return instructions


def _english_words(text: str) -> set:
    """Return the significant words of an English instruction."""
    words = re.findall(r"[A-Za-z][A-Za-z\-]*", text.lower())

    return {
        word for word in words
        if len(word) >= 4 and word not in FUNCTION_WORDS
    }


def _chinese_bigrams(text: str) -> set:
    """Return the character pairs of a Chinese instruction."""
    characters = re.findall(r"[\u4e00-\u9fff]", text)

    return {
        characters[index] + characters[index + 1]
        for index in range(len(characters) - 1)
    }


def _action_verb(text: str) -> str:
    """Return the action verb that opens an English instruction."""
    words = re.findall(r"[A-Za-z][A-Za-z\-]*", text)

    if not words:
        return ""

    verb = words[0].lower()

    if verb in FUNCTION_WORDS or len(verb) < 3:
        return ""

    return verb


def _jaccard(first: set, second: set) -> float:
    """Return the similarity of two sets."""
    if not first or not second:
        return 0.0

    union = first | second

    if not union:
        return 0.0

    return len(first & second) / len(union)


def conflict_candidates(
    root: Path,
    standard_index: dict,
) -> list:
    """Find the pairs of rules that look alike.

    The result is a list of candidates that need a human review. The
    signals are deterministic, and no signal proves a contradiction.
    """
    instructions = _instructions(root, standard_index)
    candidates: dict = {}

    keys = sorted(instructions)

    for index, first in enumerate(keys):
        for second in keys[index + 1:]:
            # Rules of one Standard cannot contradict each other.
            if first[0] == second[0]:
                continue

            signals: list = []

            left = instructions[first]
            right = instructions[second]

            verb_left = _action_verb(left["en"])
            verb_right = _action_verb(right["en"])

            if verb_left and verb_left == verb_right:
                signals.append(
                    f"the same action verb in English: {verb_left}"
                )

            overlap = _jaccard(
                _english_words(left["en"]), _english_words(right["en"])
            )

            if overlap >= WORD_OVERLAP_THRESHOLD:
                signals.append(
                    f"the same wording in English: {overlap:.2f}"
                )

            chinese = _jaccard(
                _chinese_bigrams(left["zh-CN"]), _chinese_bigrams(right["zh-CN"])
            )

            if chinese >= BIGRAM_OVERLAP_THRESHOLD:
                signals.append(
                    f"the same wording in Chinese: {chinese:.2f}"
                )

            if not signals:
                continue

            pair = (f"{first[0]}/{first[1]}", f"{second[0]}/{second[1]}")
            candidates[pair] = Candidate(pair[0], pair[1], signals)

    return [candidates[pair] for pair in sorted(candidates)]


def check_conflicts(
    root: Path,
    records: list,
    standard_index: dict,
    errors: list,
    warnings: list,
) -> None:
    """Check the declared conflict records."""
    for record in records:
        if record.kind != "conflict":
            continue

        relative = record.relative
        data = record.data
        classification = data.get("classification")
        status = data.get("status")
        reviewer = data.get("reviewer")

        if status in ("resolved", "accepted_exception") and not reviewer:
            errors.append(
                f"{relative}: a conflict that is closed needs a reviewer"
            )

        if classification == "confirmed" and not reviewer:
            errors.append(
                f"{relative}: a confirmed conflict needs a reviewer"
            )

        if status == "resolved" and not data.get("resolution"):
            errors.append(
                f"{relative}: a resolved conflict needs a resolution"
            )


def check_semantic_reviews(
    root: Path,
    records: list,
    standard_index: dict,
    errors: list,
    warnings: list,
) -> None:
    """Check that a bilingual review still describes the content."""
    from .lifecycle import file_digest, stale_record_blocks

    for record in records:
        if record.kind != "semantic-review":
            continue

        if is_reference(record):
            # An illustrative instance records no review, so it can
            # never go stale and never block a Standard.
            continue

        relative = record.relative
        data = record.data
        sid = data.get("standard_id")
        digest = data.get("reviewed_content_sha256")
        entry = standard_index.get(sid) if isinstance(sid, str) else None

        if entry is None:
            continue

        path = root / entry["path"]
        current = file_digest(path)

        if current is None or not isinstance(digest, str):
            continue

        if current == digest:
            continue

        outcome = data.get("outcome")
        status = entry.get("status") or "draft"
        declared = entry.get("version")

        # A Standard that claims to be verified may not keep a bilingual
        # review that no longer describes it. For a Standard that is
        # still in review, the promotion gate already refuses a stale
        # review, so the finding is a warning.
        #
        # A review of an earlier revision cannot authorise the content
        # that came after it, whatever it says. It is reported and it
        # does not block, so that a legitimate version upgrade is never
        # held back by the history of the review.
        if (
            status == "verified"
            and stale_record_blocks(data, declared)
        ):
            errors.append(
                f"{relative}: the bilingual review of {sid} is stale, the "
                f"content changed after the review"
            )
        else:
            warnings.append(
                f"{relative}: the bilingual review of {sid} is stale, the "
                f"content changed after the review"
            )

        version = data.get("standard_version")

        if (
            isinstance(declared, str)
            and isinstance(version, str)
            and version == declared
        ):
            errors.append(
                f"{relative}: the content of {sid} changed but its "
                f"version stayed {declared}"
            )


def blocking_conflicts(records: list) -> list:
    """Return the conflicts that block a promotion.

    A conflict is blocking when a reviewer confirmed it and it is
    still open.
    """
    return [
        record
        for record in records
        if record.kind == "conflict"
        and record.data.get("classification") == "confirmed"
        and record.data.get("status") == "open"
    ]


def bilingual_evaluation_coverage(root: Path, records: list) -> dict:
    """Describe which rules have an evaluation case in which language."""
    import yaml

    cases = [record for record in records if record.kind == "evaluation-case"]
    by_rule: dict = {}

    for record in cases:
        sid = record.data.get("standard_id")
        language = record.data.get("language")

        if not isinstance(sid, str):
            continue

        for rule_id in record.data.get("rule_ids", []):
            languages = by_rule.setdefault(f"{sid}/{rule_id}", set())

            if isinstance(language, str):
                languages.add(language)

    complete = []
    partial = []

    for rule, languages in sorted(by_rule.items()):
        if {"en", "zh-CN"} <= languages:
            complete.append(rule)
        else:
            partial.append(rule)

    return {
        "rules_with_cases": len(by_rule),
        "rules_with_both_languages": complete,
        "rules_with_one_language": partial,
    }
