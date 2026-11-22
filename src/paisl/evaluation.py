# SPDX-License-Identifier: MIT
"""The evaluation engine.

The engine loads a suite and its cases, resolves the fixtures, runs
the assertions through the allowed evaluators, and produces a result
that is reproducible: the same inputs always give the same report.

The report holds digests and short redacted excerpts instead of the
raw output, so that running an evaluation never publishes the
material it looked at.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .evaluators import (
    ERROR,
    EVALUATOR_VERSION,
    FAIL,
    PASS,
    SKIP,
    EvaluationResult,
    allowed_names,
    get_evaluator,
)

REPORT_SCHEMA_VERSION = "0.2.0"

MAX_EXCERPT_LENGTH = 200

# Patterns that look like a credential. An excerpt never carries one.
SECRET_PATTERNS = (
    re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(
        r"(?i)\b(?:bearer|token|password|secret|api[_-]?key)\b\s*[:=]\s*\S+"
    ),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


def redact(text: str, limit: int = MAX_EXCERPT_LENGTH) -> str:
    """Return a short excerpt with anything that looks like a secret removed."""
    excerpt = text

    for pattern in SECRET_PATTERNS:
        excerpt = pattern.sub("[redacted]", excerpt)

    excerpt = excerpt.strip()

    if len(excerpt) > limit:
        excerpt = excerpt[:limit] + "..."

    return excerpt


def digest_text(text: str) -> str:
    """Return the SHA-256 digest of a text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class AssertionResult:
    """The outcome of one assertion."""

    id: str
    evaluator: str
    severity: str
    status: str
    message: str
    details: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "evaluator": self.evaluator,
            "severity": self.severity,
            "status": self.status,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class CaseResult:
    """The outcome of one evaluation case."""

    id: str
    standard_id: str
    rule_ids: list
    status: str
    assertions: list
    input_digest: str
    output_digest: str
    output_excerpt: str

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "standard_id": self.standard_id,
            "rule_ids": list(self.rule_ids),
            "status": self.status,
            "input_digest": self.input_digest,
            "output_digest": self.output_digest,
            "output_excerpt": self.output_excerpt,
            "assertions": [item.as_dict() for item in self.assertions],
        }


@dataclass
class SuiteResult:
    """The outcome of one evaluation suite."""

    suite_id: str
    suite_version: str
    evaluator_version: str
    run_id: str
    input_digest: str
    summary: dict
    cases: list
    skipped_cases: list = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """A suite passes when every case passed.

        A skipped mandatory assertion never counts as a pass.
        """
        return (
            self.summary.get("fail", 0) == 0
            and self.summary.get("error", 0) == 0
            and self.summary.get("skip", 0) == 0
        )

    def as_dict(self) -> dict:
        return {
            "schema_version": REPORT_SCHEMA_VERSION,
            "suite_id": self.suite_id,
            "suite_version": self.suite_version,
            "run_id": self.run_id,
            "evaluator_version": self.evaluator_version,
            "input_digest": self.input_digest,
            "summary": dict(self.summary),
            "cases": [case.as_dict() for case in self.cases],
            "skipped_cases": list(self.skipped_cases),
        }


def resolve_fixture(root: Path, relative: str) -> str | None:
    """Read a fixture that must stay inside the repository."""
    if not isinstance(relative, str) or not relative:
        return None

    candidate = (root / relative).resolve()

    if not candidate.is_relative_to(root.resolve()):
        return None

    if not candidate.is_file():
        return None

    return candidate.read_text(encoding="utf-8")


def evaluate_case(
    root: Path,
    case: dict,
    output_text: str | None = None,
    skipped: bool = False,
) -> CaseResult:
    """Run one evaluation case."""
    case_id = case.get("id", "")
    standard_id = case.get("standard_id", "")
    rule_ids = list(case.get("rule_ids", []))

    if skipped:
        return CaseResult(
            id=case_id,
            standard_id=standard_id,
            rule_ids=rule_ids,
            status=SKIP,
            assertions=[],
            input_digest="",
            output_digest="",
            output_excerpt="",
        )

    fixture = case.get("fixture", {}) or {}

    input_text = resolve_fixture(root, fixture.get("input", "")) or ""

    if output_text is None:
        output_text = resolve_fixture(root, fixture.get("output", "")) or ""

    results: list = []

    for assertion in case.get("assertions", []):
        if not isinstance(assertion, dict):
            continue

        assertion_id = assertion.get("id", "")
        evaluator_name = assertion.get("evaluator", "")
        severity = assertion.get("severity", "may")
        params = assertion.get("params", {}) or {}

        evaluator = get_evaluator(evaluator_name)

        if evaluator is None:
            outcome = EvaluationResult(
                status=ERROR,
                message=(
                    f"The evaluator {evaluator_name!r} is not allowed. "
                    f"Allowed evaluators: {', '.join(allowed_names())}."
                ),
                details={"evaluator": evaluator_name},
            )
        else:
            try:
                outcome = evaluator.evaluate(output_text, params)
            except Exception as exc:  # pragma: no cover - defensive
                outcome = EvaluationResult(
                    status=ERROR,
                    message=f"The evaluator failed: {exc}",
                    details={"evaluator": evaluator_name},
                )

        results.append(AssertionResult(
            id=assertion_id,
            evaluator=evaluator_name,
            severity=severity,
            status=outcome.status,
            message=outcome.message,
            details=outcome.details,
        ))

    status = _case_status(results)

    return CaseResult(
        id=case_id,
        standard_id=standard_id,
        rule_ids=rule_ids,
        status=status,
        assertions=results,
        input_digest=digest_text(input_text),
        output_digest=digest_text(output_text),
        output_excerpt=redact(output_text),
    )


def _case_status(results: list) -> str:
    """Aggregate the assertion outcomes into the status of a case."""
    if any(item.status == ERROR for item in results):
        return ERROR

    if any(item.status == FAIL for item in results):
        return FAIL

    if any(
        item.status == SKIP and item.severity == "must"
        for item in results
    ):
        return SKIP

    return PASS


def run_suite(
    root: Path,
    suite: dict,
    cases: list,
    skip_cases: tuple = (),
    output_text: str | None = None,
) -> SuiteResult:
    """Run every case of a suite and collect the result."""
    results: list = []
    skipped: list = []

    for case in cases:
        case_id = case.get("id", "")

        if case_id in skip_cases:
            skipped.append(case_id)
            results.append(evaluate_case(root, case, skipped=True))
            continue

        results.append(evaluate_case(root, case, output_text))

    summary = {"pass": 0, "fail": 0, "skip": 0, "error": 0}

    for result in results:
        summary[result.status] = summary.get(result.status, 0) + 1

    input_digest = digest_text("\n".join(
        f"{result.id}:{result.input_digest}:{result.output_digest}"
        for result in results
    ))

    run_id = digest_text(
        "|".join([
            suite.get("id", ""),
            suite.get("version", ""),
            EVALUATOR_VERSION,
            input_digest,
        ])
    )[:32]

    return SuiteResult(
        suite_id=suite.get("id", ""),
        suite_version=suite.get("version", ""),
        evaluator_version=EVALUATOR_VERSION,
        run_id=run_id,
        input_digest=input_digest,
        summary=summary,
        cases=results,
        skipped_cases=skipped,
    )


def evaluate_standard(root: Path, sid: str, cases: list) -> dict:
    """Run the evaluation cases that cover one Standard.

    Returns the number of cases, how many of them passed, and the
    identifiers of the ones that did not.
    """
    relevant = [
        case for case in cases
        if case.get("standard_id") == sid
    ]

    if not relevant:
        return {
            "cases": 0,
            "passed": 0,
            "failed": [],
            "status": SKIP,
        }

    suite = {
        "id": f"standard-{sid}",
        "version": "",
        "cases": [case.get("id", "") for case in relevant],
    }

    result = run_suite(root, suite, relevant)

    failed = [
        case.id for case in result.cases
        if case.status != PASS
    ]

    return {
        "cases": len(relevant),
        "passed": result.summary.get(PASS, 0),
        "failed": failed,
        "status": PASS if not failed else FAIL,
    }


def render_evaluation_markdown(result: SuiteResult) -> str:
    """Render an evaluation result as Markdown."""
    lines: list = []

    lines.append("# PAISL Evaluation Report")
    lines.append("")
    lines.append(f"- Suite: `{result.suite_id}` version `{result.suite_version}`")
    lines.append(f"- Evaluator version: `{result.evaluator_version}`")
    lines.append(f"- Run ID: `{result.run_id}`")
    lines.append(f"- Input digest: `{result.input_digest}`")
    lines.append(
        "- Summary: "
        f"{result.summary.get('pass', 0)} passed, "
        f"{result.summary.get('fail', 0)} failed, "
        f"{result.summary.get('skip', 0)} skipped, "
        f"{result.summary.get('error', 0)} errored"
    )
    lines.append("")
    lines.append("## Cases")
    lines.append("")
    lines.append("| Case | Standard | Status | Assertions |")
    lines.append("|---|---|---|---|")

    for case in result.cases:
        passed = sum(
            1 for item in case.assertions if item.status == PASS
        )
        lines.append(
            f"| `{case.id}` | `{case.standard_id}` | {case.status} | "
            f"{passed}/{len(case.assertions)} passed |"
        )

    lines.append("")

    for case in result.cases:
        if not case.assertions:
            continue

        lines.append(f"### `{case.id}`")
        lines.append("")

        for item in case.assertions:
            lines.append(
                f"- `{item.id}` [{item.severity}] {item.evaluator}: "
                f"**{item.status}** — {item.message}"
            )

        lines.append("")

    return "\n".join(lines) + "\n"


def render_evaluation_json(result: SuiteResult) -> str:
    """Render an evaluation result as JSON."""
    payload = result.as_dict()
    payload["status"] = "passed" if result.passed else "failed"

    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_evaluation_text(result: SuiteResult) -> str:
    """Render an evaluation result in the text format."""
    lines: list = []

    lines.append("")
    lines.append("=== PAISL Evaluation Report ===")
    lines.append(f"Suite: {result.suite_id} ({result.suite_version})")
    lines.append(f"Evaluator version: {result.evaluator_version}")
    lines.append(f"Run ID: {result.run_id}")
    lines.append(
        "Summary: "
        f"{result.summary.get('pass', 0)} passed, "
        f"{result.summary.get('fail', 0)} failed, "
        f"{result.summary.get('skip', 0)} skipped, "
        f"{result.summary.get('error', 0)} errored"
    )

    for case in result.cases:
        lines.append(f"  {case.id} [{case.status}] {case.standard_id}")

        for item in case.assertions:
            lines.append(
                f"    {item.id} [{item.severity}] {item.evaluator}: "
                f"{item.status} — {item.message}"
            )

    lines.append("")

    return "\n".join(lines) + "\n"
