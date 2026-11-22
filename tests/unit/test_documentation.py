# SPDX-License-Identifier: MIT
"""The documentation and the command line stay in step.

A command that exists but is not documented is a command nobody
finds. A command that is documented but does not exist is worse.
The tests below hold the two together.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

# The commands the tool offers, with the arguments they need.
COMMANDS = {
    "validate": "paisl validate",
    "coverage": "paisl coverage",
    "evidence check": "paisl evidence check",
    "governance check": "paisl governance check",
    "conflicts check": "paisl conflicts check",
    "evaluate": "paisl evaluate",
    "report": "paisl report",
    "compare": "paisl compare",
}


def _readme() -> str:
    return (ROOT / "README.md").read_text(encoding="utf-8")


def _guide() -> str:
    return (
        ROOT / "docs" / "user-guide" / "USER_GUIDE.zh-CN.md"
    ).read_text(encoding="utf-8")


def _architecture() -> str:
    return (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")


def _help(*args) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "paisl", *args, "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={
            "PYTHONPATH": str(ROOT / "src"),
            "PATH": "/usr/bin:/bin:/usr/local/bin",
        },
    )

    assert result.returncode == 0, result.stderr

    return result.stdout


def test_the_tool_offers_the_documented_commands():
    """The commands exist."""
    for name in COMMANDS:
        parts = name.split()
        output = _help(parts[0])

        assert parts[0] in output, (
            f"the command {parts[0]} is not offered by the tool"
        )

        if len(parts) > 1:
            assert parts[1] in output, (
                f"the command {name} is not offered by the tool"
            )


def test_the_readme_names_every_command():
    """The README names every command."""
    text = _readme()

    for name, invocation in COMMANDS.items():
        assert f"`{invocation}" in text, (
            f"the README does not name the command {name}"
        )


def test_the_user_guide_names_every_command():
    """The user guide names every command."""
    text = _guide()

    for name, invocation in COMMANDS.items():
        assert f"paisl {name}" in text, (
            f"the user guide does not name the command {name}"
        )


def test_the_architecture_document_names_every_command():
    """The architecture document names every command."""
    text = _architecture()

    for name in COMMANDS:
        assert f"`{name}`" in text, (
            f"the architecture document does not name the command {name}"
        )


def test_no_stage_description_survives_in_the_code():
    """The code does not describe a stage of the work any more.

    A comment that says only one command exists, or that a feature
    is still to come, misleads the next reader and the next agent.
    """
    patterns = (
        r"only the `\w+` command exists",
        r"at this stage",
        r"not implemented in this release",
        r"deliberately absent",
        r"are introduced by their work packages",
    )

    for path in sorted(
        list((ROOT / "src").rglob("*.py"))
        + list((ROOT / "scripts").rglob("*.py"))
    ):
        text = path.read_text(encoding="utf-8")

        for pattern in patterns:
            assert not re.search(pattern, text, re.IGNORECASE), (
                f"{path.relative_to(ROOT)} still carries the stage "
                f"description {pattern!r}"
            )


def test_the_user_guide_tells_the_difference_between_the_commands():
    """The user guide tells a check apart from a report."""
    text = _guide()

    assert "强制校验" in text, (
        "the user guide does not say which commands enforce"
    )
    assert "只查看" in text, (
        "the user guide does not say which commands only report"
    )


def test_no_stage_description_survives_in_the_documents():
    """The documents do not describe a stage of the work any more.

    A heading that says the tooling is still in development, or a
    module that is marked as planned, misleads the next reader and
    the next agent. The release moves the work on, and the text has
    to move with it.
    """
    patterns = (
        r"in development",
        r"\(planned\)",
        r"\bplanned\b(?!\s+but\s+not\s+implemented)",
        r"not implemented in this release",
        r"is now (?:here|available)",
    )

    # The governance document states that a dedicated Skill is planned
    # but not implemented. That is a statement about the coverage of a
    # Standard, not a stage of the work, so it is allowed.
    allowed = ("docs/governance.md",)

    documents = [
        ROOT / "README.md",
        ROOT / "README.zh-CN.md",
        ROOT / "docs" / "architecture.md",
        ROOT / "docs" / "governance.md",
        ROOT / "docs" / "user-guide" / "USER_GUIDE.zh-CN.md",
        ROOT / "docs" / "promotion-checklist.md",
        ROOT / "CHANGELOG.md",
    ]

    for path in documents:
        relative = path.relative_to(ROOT).as_posix()

        if relative in allowed:
            continue

        text = path.read_text(encoding="utf-8")

        for pattern in patterns:
            assert not re.search(pattern, text, re.IGNORECASE), (
                f"{relative} still carries the stage description "
                f"{pattern!r}"
            )
