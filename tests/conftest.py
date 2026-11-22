# SPDX-License-Identifier: MIT
"""Shared fixtures for the PAISL test suite."""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Make the scenario helpers importable from the test modules.
if str(ROOT / "tests") not in sys.path:
    sys.path.insert(0, str(ROOT / "tests"))

IGNORE = shutil.ignore_patterns(
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "docs/planning",
    "*.egg-info",
)


@pytest.fixture(scope="session")
def repo_root() -> pathlib.Path:
    """Return the repository under test."""
    return ROOT


@pytest.fixture
def repo_copy(tmp_path, repo_root) -> pathlib.Path:
    """Return a throwaway copy of the repository."""
    destination = tmp_path / "repo"
    shutil.copytree(repo_root, destination, ignore=IGNORE)
    return destination


@pytest.fixture
def run_validator():
    """Return a callable that runs the legacy validator entry point."""

    def _run(repo: pathlib.Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "scripts/validate.py"],
            cwd=repo,
            capture_output=True,
            text=True,
        )

    return _run
