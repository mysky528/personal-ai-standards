# SPDX-License-Identifier: MIT
"""Exception hierarchy and process exit code mapping."""

from __future__ import annotations

EXIT_SUCCESS = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2
EXIT_EXECUTION = 3


class PaislError(Exception):
    """Base class for every error raised by the tooling."""

    exit_code = EXIT_EXECUTION


class ValidationError(PaislError):
    """A repository, record, or fixture failed validation."""

    exit_code = EXIT_VALIDATION


class UsageError(PaislError):
    """Command line arguments or configuration are invalid."""

    exit_code = EXIT_USAGE


class ExecutionError(PaislError):
    """The tool could not complete because of an execution failure."""

    exit_code = EXIT_EXECUTION


class UnsafePathError(ValidationError):
    """A path resolved outside the repository root."""


class InitializationError(ValidationError):
    """The repository could not be loaded."""


class UnsupportedCommandError(UsageError):
    """The requested command is not implemented in this release."""
