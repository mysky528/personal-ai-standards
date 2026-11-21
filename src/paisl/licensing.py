# SPDX-License-Identifier: MIT
"""License scope validation.

The path to license mapping lives in `LICENSE-DOCS` at the repository
root. This module parses that table and verifies that every file
declares a matching SPDX identifier.
"""

from __future__ import annotations

import re
from pathlib import Path

# Build artefacts and local caches are not part of the repository.
SKIP_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
}

# The root license files describe the licenses themselves.
EXEMPT_FILES = {
    "LICENSE",
    "LICENSE-DOCS",
    "LICENSE-CC-BY-4.0",
}

# Files that can carry an inline SPDX identifier.
COMMENT_EXTENSIONS = {
    ".md",
    ".yaml",
    ".yml",
    ".py",
    ".txt",
    ".json",
}

SPDX_RE = re.compile(r'SPDX-License-Identifier:\s*"?([A-Za-z0-9.\-]+)"?')


def license_mapping(root: Path) -> list:
    """Read the path to license mapping declared in LICENSE-DOCS."""
    notice = root / "LICENSE-DOCS"

    if not notice.is_file():
        return []

    mapping = []

    for line in notice.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue

        cells = [cell.strip() for cell in line.strip("|").split("|")]

        if len(cells) < 2 or cells[0] == "Path":
            continue

        paths = re.findall(r"`([^`]+)`", cells[0])

        if not paths:
            continue

        identifier = "CC-BY-4.0" if "CC BY" in cells[1] else "MIT"
        mapping.append((paths, identifier))

    return mapping


def expected_license(relative: str, mapping: list) -> str:
    """Return the license that applies to a repository path."""
    for paths, identifier in mapping:
        for pattern in paths:
            if pattern.endswith("/"):
                if relative.startswith(pattern):
                    return identifier
            elif pattern.startswith("*"):
                if "/" not in relative and relative.endswith(pattern[1:]):
                    return identifier
            elif relative == pattern:
                return identifier

    return "MIT"


def is_skipped(parts: tuple) -> bool:
    """Report whether a path is outside the scope of the check."""
    return any(
        part in SKIP_DIRECTORIES or part.endswith(".egg-info")
        for part in parts
    )


def validate_license_scope(root: Path, errors: list) -> None:
    """Check every file against the declared path to license mapping."""
    mapping = license_mapping(root)

    if not mapping:
        errors.append("LICENSE-DOCS: no path to license mapping found")
        return

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        parts = path.relative_to(root).parts
        relative = path.relative_to(root).as_posix()

        if relative in EXEMPT_FILES:
            continue

        if is_skipped(parts):
            continue

        identifier = expected_license(relative, mapping)
        text = path.read_text(encoding="utf-8", errors="replace")
        match = SPDX_RE.search(text)

        if not match:
            if path.suffix in COMMENT_EXTENSIONS:
                errors.append(f"{relative}: missing SPDX-License-Identifier")
            continue

        found = match.group(1)

        if found != identifier:
            errors.append(
                f"{relative}: SPDX identifier {found} does not match "
                f"the license mapping ({identifier})"
            )
