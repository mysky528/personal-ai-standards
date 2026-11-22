# SPDX-License-Identifier: MIT
"""Command line interface for the PAISL tooling.

Only the `validate` command exists at this stage of v0.2.0. The
remaining commands are introduced by their work packages; they are
deliberately absent so that nothing is described as existing before
it is implemented.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml
from jsonschema.exceptions import SchemaError

from . import __version__
from .errors import (
    EXIT_SUCCESS,
    EXIT_USAGE,
    EXIT_VALIDATION,
    PaislError,
)
from .coverage import build_coverage, validate_skills
from .evidence import check_evidence, evidence_coverage
from .lifecycle import (
    check_review_records,
    check_status_trail,
    check_verified_standards,
    promotion_gates,
)
from .licensing import validate_license_scope
from .paths import find_repo_root
from .registry import (
    build_standard_index,
    load_catalog,
    load_records,
    resolve_references,
    validate_catalog_meta,
    validate_standards,
)
from .reporting import (
    render_coverage_json,
    render_coverage_text,
    render_evidence_json,
    render_evidence_text,
    render_governance_json,
    render_governance_text,
    render_json_report,
    render_text_report,
)
from .schema_validation import build_validator


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the supported commands."""
    parser = argparse.ArgumentParser(
        prog="paisl",
        description="Tooling for the Personal AI Standards Library.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"paisl {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate the standard registry, Catalog, and Skills.",
    )
    validate_parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Repository root. Defaults to the current directory.",
    )
    validate_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Report format.",
    )
    validate_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write the report to this file instead of standard output.",
    )
    validate_parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures.",
    )

    coverage_parser = subparsers.add_parser(
        "coverage",
        help="Report how completely the repository is covered.",
    )
    coverage_parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Repository root. Defaults to the current directory.",
    )
    coverage_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Report format.",
    )
    coverage_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write the report to this file instead of standard output.",
    )

    evidence_parser = subparsers.add_parser(
        "evidence",
        help="Work with the evidence registry.",
    )
    evidence_subparsers = evidence_parser.add_subparsers(
        dest="evidence_command",
        required=True,
    )

    evidence_check_parser = evidence_subparsers.add_parser(
        "check",
        help="Check the evidence registry and report its coverage.",
    )
    evidence_check_parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Repository root. Defaults to the current directory.",
    )
    evidence_check_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Report format.",
    )
    evidence_check_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write the report to this file instead of standard output.",
    )

    governance_parser = subparsers.add_parser(
        "governance",
        help="Work with the lifecycle governance.",
    )
    governance_subparsers = governance_parser.add_subparsers(
        dest="governance_command",
        required=True,
    )

    governance_check_parser = governance_subparsers.add_parser(
        "check",
        help="Check the review records and report the promotion gates.",
    )
    governance_check_parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Repository root. Defaults to the current directory.",
    )
    governance_check_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Report format.",
    )
    governance_check_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write the report to this file instead of standard output.",
    )
    governance_check_parser.add_argument(
        "--all",
        action="store_true",
        help="List the gates of every Standard, not only those in the "
        "promotion path.",
    )

    return parser


def run_validation(root: Path) -> tuple[list, list, int, int]:
    """Run every validation check and collect the findings.

    Returns the errors, the warnings, the number of standards
    checked, and the number of skills checked.
    """
    errors: list = []
    warnings: list = []

    schema = json.loads(
        (root / "schemas" / "standard.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validator = build_validator(schema)
    catalog = load_catalog(root)

    standards_checked = validate_standards(
        root, validator, catalog, errors, warnings
    )

    validate_catalog_meta(
        root, schema, catalog, errors, warnings
    )

    skills_checked = validate_skills(
        root, schema, catalog, errors, warnings
    )

    validate_license_scope(root, errors)

    # v0.2.0 extends the baseline checks with the governance and
    # evaluation records. The original checks keep their behaviour and
    # their order; the records are reported only when they are wrong.
    records = load_records(root, errors)
    standard_index = build_standard_index(root, catalog)
    resolve_references(root, records, standard_index, errors)
    check_evidence(records, errors, warnings)
    check_review_records(root, records, standard_index, errors, warnings)
    check_status_trail(root, records, standard_index, errors)
    check_verified_standards(
        root, records, standard_index, validator, errors
    )

    return errors, warnings, standards_checked, skills_checked


def run_coverage(root: Path) -> dict:
    """Collect the coverage report."""
    schema = json.loads(
        (root / "schemas" / "standard.schema.json").read_text(
            encoding="utf-8"
        )
    )
    catalog = load_catalog(root)
    errors: list = []
    records = load_records(root, errors)

    return build_coverage(root, schema, catalog, records)


def _write_report(report: str, output: Path | None) -> None:
    if output is None:
        sys.stdout.write(report)
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")


def _run_validate(args: argparse.Namespace) -> int:
    try:
        root = args.repo.resolve() if args.repo else find_repo_root()
        errors, warnings, standards, skills = run_validation(root)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: Initialization failed: {exc}")
        return EXIT_VALIDATION
    except SchemaError as exc:
        print(f"ERROR: Initialization failed: {exc}")
        return EXIT_VALIDATION
    except PaislError as exc:
        print(f"ERROR: {exc}")
        return exc.exit_code

    if args.format == "json":
        report = render_json_report(
            errors, warnings, standards, skills, args.strict
        )
    else:
        report = render_text_report(
            errors, warnings, standards, skills, args.strict
        )

    _write_report(report, args.output)

    if errors or (args.strict and warnings):
        return EXIT_VALIDATION

    return EXIT_SUCCESS


def _run_coverage(args: argparse.Namespace) -> int:
    try:
        root = args.repo.resolve() if args.repo else find_repo_root()
        coverage = run_coverage(root)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: Initialization failed: {exc}")
        return EXIT_VALIDATION
    except PaislError as exc:
        print(f"ERROR: {exc}")
        return exc.exit_code

    if args.format == "json":
        report = render_coverage_json(coverage)
    else:
        report = render_coverage_text(coverage)

    _write_report(report, args.output)

    return EXIT_SUCCESS


def run_evidence_coverage(root: Path) -> dict:
    """Collect the evidence coverage report."""
    errors: list = []
    records = load_records(root, errors)

    return evidence_coverage(records)


def _run_evidence_check(args: argparse.Namespace) -> int:
    try:
        root = args.repo.resolve() if args.repo else find_repo_root()
        coverage = run_evidence_coverage(root)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: Initialization failed: {exc}")
        return EXIT_VALIDATION
    except PaislError as exc:
        print(f"ERROR: {exc}")
        return exc.exit_code

    if args.format == "json":
        report = render_evidence_json(coverage)
    else:
        report = render_evidence_text(coverage)

    _write_report(report, args.output)

    return EXIT_SUCCESS


def run_governance(root: Path) -> dict:
    """Collect the governance report."""
    schema = json.loads(
        (root / "schemas" / "standard.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validator = build_validator(schema)
    catalog = load_catalog(root)
    errors: list = []
    records = load_records(root, errors)
    standard_index = build_standard_index(root, catalog)

    status_counts = {"draft": 0, "review": 0, "verified": 0, "deprecated": 0}

    for entry in standard_index.values():
        status = entry.get("status") or "draft"
        status_counts[status] = status_counts.get(status, 0) + 1

    reviews = [record for record in records if record.kind == "review"]
    semantic = [
        record for record in records if record.kind == "semantic-review"
    ]

    gates = {
        sid: {
            "status": standard_index[sid].get("status") or "draft",
            "gates": [
                {
                    "name": gate.name,
                    "description": gate.description,
                    "status": gate.status,
                    "detail": gate.detail,
                }
                for gate in promotion_gates(
                    root, sid, records, standard_index, validator
                )
            ],
        }
        for sid in sorted(standard_index)
    }

    return {
        "status_counts": status_counts,
        "review_records": {
            "total": len(reviews),
            "approved": len(
                [r for r in reviews if r.data.get("decision") == "approved"]
            ),
            "rejected": len(
                [r for r in reviews if r.data.get("decision") == "rejected"]
            ),
        },
        "semantic_reviews": {"total": len(semantic)},
        "standards": gates,
    }


def _run_governance_check(args: argparse.Namespace) -> int:
    try:
        root = args.repo.resolve() if args.repo else find_repo_root()
        governance = run_governance(root)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: Initialization failed: {exc}")
        return EXIT_VALIDATION
    except PaislError as exc:
        print(f"ERROR: {exc}")
        return exc.exit_code

    if args.format == "json":
        report = render_governance_json(governance)
    else:
        report = render_governance_text(governance, args.all)

    _write_report(report, args.output)

    return EXIT_SUCCESS


def main(argv: list[str] | None = None) -> int:
    """Run the command line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        return _run_validate(args)

    if args.command == "coverage":
        return _run_coverage(args)

    if args.command == "evidence":
        if args.evidence_command == "check":
            return _run_evidence_check(args)

    if args.command == "governance":
        if args.governance_command == "check":
            return _run_governance_check(args)

    parser.error(f"Unknown command: {args.command}")

    return EXIT_USAGE


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
