# SPDX-License-Identifier: MIT
"""AC-001 — the existing command keeps working.

The acceptance criteria require the pre-v0.2.0 command to remain
usable. The check runs in a clean copy of the repository without any
installation step, which is how the command was used before.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

FIXTURES = (
    pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "legacy"
)


def test_legacy_command_runs_without_installation(repo_copy, run_validator):
    """`python scripts/validate.py` works in an uninstalled checkout."""
    result = run_validator(repo_copy)

    assert result.returncode == 0, result.stdout
    assert result.stdout.startswith("\n=== PAISL Validation Report ===")
    assert "Validation PASSED" in result.stdout


def test_legacy_command_output_is_unchanged(repo_copy, run_validator):
    """The legacy command reproduces the recorded v0.1.x output."""
    expected = json.loads(
        (FIXTURES / "pass.json").read_text(encoding="utf-8")
    )

    result = run_validator(repo_copy)

    assert result.stdout == expected["stdout"]
    assert result.returncode == expected["exit_code"]


def test_legacy_command_needs_no_third_party_install(repo_copy):
    """The wrapper bootstraps the package path on its own."""
    script = repo_copy / "scripts" / "validate.py"
    text = script.read_text(encoding="utf-8")

    assert "sys.path.insert" in text
    assert "/ \"src\"" in text


def test_package_is_importable_without_installation(repo_copy):
    """The package resolves from the repository source tree."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import paisl; print(paisl.__version__)",
        ],
        cwd=repo_copy,
        capture_output=True,
        text=True,
        env={
            "PYTHONPATH": str(repo_copy / "src"),
            "PATH": "/usr/bin:/bin:/usr/local/bin",
        },
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "0.2.0"
