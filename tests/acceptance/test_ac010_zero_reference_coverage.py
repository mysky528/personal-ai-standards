# SPDX-License-Identifier: MIT
"""AC-010 — a standard without a Skill reference is reported, not failed.

The acceptance criteria require the coverage report to list standards
that no Skill refers to, and require that the build does not fail
because of it.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

FIXTURES = (
    pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "legacy"
)


def _cli(repo, *args):
    return subprocess.run(
        [sys.executable, "-m", "paisl", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        env={
            "PYTHONPATH": str(repo / "src"),
            "PATH": "/usr/bin:/bin:/usr/local/bin",
        },
    )


def test_coverage_report_lists_unreferenced_standards(repo_copy):
    """The report names the standards without a Skill reference."""
    # PAISL-ENG-001 is referenced by security-review only.
    path = repo_copy / "skills" / "security-review" / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("- PAISL-ENG-001", "- (removed)"), encoding="utf-8"
    )

    result = _cli(repo_copy, "coverage", "--format", "json")

    assert result.returncode == 0

    payload = json.loads(result.stdout)
    standards = payload["coverage"]["standards"]

    assert "PAISL-ENG-001" in standards["without_skill_references"]
    assert standards["with_skill_references"] == 11


def test_unreferenced_standard_does_not_fail_the_build(repo_copy):
    """The build stays green when a standard has no Skill."""
    path = repo_copy / "skills" / "security-review" / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("- PAISL-ENG-001", "- (removed)"), encoding="utf-8"
    )

    result = _cli(repo_copy, "validate")

    assert result.returncode == 0, result.stdout
    assert "Validation PASSED" in result.stdout


def test_coverage_report_is_available_in_text_form(repo_copy):
    """The text report names the standards it lists."""
    result = _cli(repo_copy, "coverage")

    assert result.returncode == 0
    assert "=== PAISL Coverage Report ===" in result.stdout
    assert "Standards: 12" in result.stdout
