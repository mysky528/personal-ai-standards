# SPDX-License-Identifier: MIT
"""Repository path resolution and safe file loading.

Every path used by the tooling is resolved through this module so
that a record can never point outside the repository root.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .errors import UnsafePathError, UsageError

# A directory is a PAISL repository when it holds all of these.
REPO_MARKERS = (
    "catalog/standards.yaml",
    "schemas/standard.schema.json",
    "standards",
)


def package_repo_root() -> Path:
    """Return the repository that contains this package.

    Correct for editable installs, where the package lives inside
    the repository it validates.
    """
    return Path(__file__).resolve().parents[2]


def find_repo_root(start: Path | None = None) -> Path:
    """Locate the repository root by walking up from start.

    Defaults to the current working directory.
    """
    current = (start or Path.cwd()).resolve()

    for candidate in (current, *current.parents):
        if all((candidate / marker).exists() for marker in REPO_MARKERS):
            return candidate

    raise UsageError(f"Not a PAISL repository: {current}")


def resolve_within_repo(relative: str | Path, root: Path) -> Path:
    """Resolve a path and guarantee it stays inside the repository.

    Raises UnsafePathError when the path escapes the repository root.
    """
    base = root.resolve()
    candidate = (base / relative).resolve()

    if not candidate.is_relative_to(base):
        raise UnsafePathError(
            f"Path escapes the repository root: {relative}"
        )

    return candidate


def read_text(path: Path) -> str:
    """Read a text file as UTF-8."""
    return path.read_text(encoding="utf-8")


def read_yaml(path: Path) -> Any:
    """Load a YAML document without constructing arbitrary objects."""
    return yaml.safe_load(path.read_text(encoding="utf-8"))
