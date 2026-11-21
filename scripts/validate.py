#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compatibility wrapper around the PAISL validator.

The implementation moved into the `paisl` package in v0.2.0. This
script keeps the original command working: the same output, the same
exit codes, and no installation step required.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Make the package importable without installing it.
sys.path.insert(0, str(REPO_ROOT / "src"))

from paisl.cli import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(
        main(
            [
                "validate",
                "--repo",
                str(REPO_ROOT),
                "--format",
                "text",
            ]
        )
    )
