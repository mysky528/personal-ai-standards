# SPDX-License-Identifier: MIT
"""Command line interface behaviour."""

from __future__ import annotations

import subprocess
import sys

import pytest

from paisl.errors import (
    EXIT_EXECUTION,
    EXIT_SUCCESS,
    EXIT_USAGE,
    EXIT_VALIDATION,
    ExecutionError,
    PaislError,
    UsageError,
    ValidationError,
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


def test_exit_code_mapping():
    """Errors map onto the documented exit codes."""
    assert EXIT_SUCCESS == 0
    assert EXIT_VALIDATION == 1
    assert EXIT_USAGE == 2
    assert EXIT_EXECUTION == 3

    assert ValidationError().exit_code == EXIT_VALIDATION
    assert UsageError().exit_code == EXIT_USAGE
    assert ExecutionError().exit_code == EXIT_EXECUTION
    assert PaislError().exit_code == EXIT_EXECUTION


def test_validate_succeeds_on_a_valid_repository(repo_copy):
    """A valid repository exits with zero."""
    result = _cli(repo_copy, "validate")

    assert result.returncode == EXIT_SUCCESS
    assert "Validation PASSED" in result.stdout


def test_validate_fails_on_an_invalid_repository(repo_copy):
    """An invalid repository exits with one."""
    (repo_copy / "catalog" / "standards.yaml").write_text(
        "catalog_version: 0.1.1\nstandards: []\n", encoding="utf-8"
    )

    result = _cli(repo_copy, "validate")

    assert result.returncode == EXIT_VALIDATION
    assert "Validation FAILED" in result.stdout


def test_json_report_is_machine_readable(repo_copy):
    """The JSON format emits a parseable report."""
    import json

    result = _cli(repo_copy, "validate", "--format", "json")

    assert result.returncode == EXIT_SUCCESS

    payload = json.loads(result.stdout)

    assert payload["status"] == "passed"
    assert payload["standards_checked"] == 12
    assert payload["skills_checked"] == 7
    assert payload["errors"] == []


def test_invalid_arguments_exit_with_usage_code(repo_copy):
    """Invalid command line arguments exit with two."""
    result = _cli(repo_copy, "validate", "--format", "bogus")

    assert result.returncode == EXIT_USAGE


def test_unknown_command_is_rejected(repo_copy):
    """Only implemented commands are exposed."""
    result = _cli(repo_copy, "coverage")

    assert result.returncode == EXIT_USAGE


def test_strict_mode_promotes_warnings(repo_copy):
    """Strict mode turns warnings into failures."""
    readme = repo_copy / "README.md"
    text = readme.read_text(encoding="utf-8")
    readme.write_text(
        text.replace("| ste-writing |", "| removed-skill |"),
        encoding="utf-8",
    )

    lenient = _cli(repo_copy, "validate")
    strict = _cli(repo_copy, "validate", "--strict")

    assert lenient.returncode == EXIT_VALIDATION
    assert strict.returncode == EXIT_VALIDATION


@pytest.mark.parametrize("flag", ["--help", "--version"])
def test_help_and_version_are_available(repo_copy, flag):
    """The CLI exposes help and version information."""
    result = _cli(repo_copy, flag)

    assert result.returncode == EXIT_SUCCESS
    assert result.stdout.strip()
