# SPDX-License-Identifier: MIT
"""Entry point for `python -m paisl`."""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
