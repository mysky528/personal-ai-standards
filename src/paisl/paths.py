# SPDX-License-Identifier: MIT
"""Repository path resolution and safe file loading.

Every path used by the tooling is resolved through this module so
that a record can never point outside the repository root.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .errors import FileTooLargeError, UnsafePathError, UsageError

# A directory is a PAISL repository when it holds all of these.
REPO_MARKERS = (
    "catalog/standards.yaml",
    "schemas/standard.schema.json",
    "standards",
)

# The largest file that the tool reads when the caller names it.
#
# The material under evaluation and the reports of a comparison are
# read into the memory of the process. Without a limit a file of any
# size is read as well, and the process pays for it twice over: the
# bytes and the text. The size is therefore checked before the file
# is read, and a file that is too large is refused with a finding
# that names it.
MAX_NAMED_FILE_BYTES = 1024 * 1024


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


def read_named_text(
    path: Path,
    role: str,
    limit: int = MAX_NAMED_FILE_BYTES,
) -> str:
    """Read a file that the caller named, within a size limit.

    The role names the file in the finding, so that the reader knows
    which file was refused.

    The size is read from the file system before the content is, so a
    file that is too large never reaches the memory of the process.
    """
    size = path.stat().st_size

    if size > limit:
        raise FileTooLargeError(
            f"The {role} is larger than the tool reads: {path} "
            f"({size} bytes, the limit is {limit} bytes)"
        )

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise UsageError(
            f"The {role} is not UTF-8 text: {path}"
        ) from exc


def read_yaml(path: Path) -> Any:
    """Load a YAML document without constructing arbitrary objects."""
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def is_reference(record) -> bool:
    """Report whether a record is an illustrative instance.

    A reference record documents the shape of a contract. It records
    no decision, so it never counts as an approval, never satisfies a
    gate, and never goes stale.
    """
    data = getattr(record, "data", None)

    if not isinstance(data, dict):
        return False

    return data.get("reference") is True
