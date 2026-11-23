# SPDX-License-Identifier: MIT
"""The size of a file that the caller names.

The material under evaluation and the reports of a comparison are
read into the memory of the process. A file of any size was read as
well, and the process paid for it twice over: the bytes and the text.

The tests below hold the boundary:

- a file within the limit is read
- a file over the limit is refused, with a finding that names it
- the size is checked before the content is read
- a file that is not UTF-8 text is refused as well
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

from paisl.errors import EXIT_USAGE, FileTooLargeError, UsageError
from paisl.paths import MAX_NAMED_FILE_BYTES, read_named_text


def _cli(repo: pathlib.Path, *args: str):
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


def _write(path: pathlib.Path, size: int) -> pathlib.Path:
    """Write a file of exactly a given size."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("wb") as handle:
        remaining = size
        block = b"x" * 65536

        while remaining > 0:
            chunk = block[:min(len(block), remaining)]
            handle.write(chunk)
            remaining -= len(chunk)

    return path


def test_a_named_file_within_the_limit_is_read(tmp_path):
    """A file that fits is read as it is."""
    path = _write(tmp_path / "output.txt", 1024)

    assert read_named_text(path, "output file") == "x" * 1024


def test_a_named_file_at_the_limit_is_read(tmp_path):
    """A file of exactly the limit is still read."""
    path = _write(tmp_path / "output.txt", MAX_NAMED_FILE_BYTES)

    assert len(read_named_text(path, "output file")) == MAX_NAMED_FILE_BYTES


def test_a_named_file_over_the_limit_is_refused(tmp_path):
    """A file that does not fit is refused."""
    path = _write(tmp_path / "output.txt", MAX_NAMED_FILE_BYTES + 1)

    with pytest.raises(FileTooLargeError) as failure:
        read_named_text(path, "output file")

    message = str(failure.value)

    assert "output file" in message
    assert "larger than the tool reads" in message
    assert str(path) in message
    assert str(MAX_NAMED_FILE_BYTES) in message


def test_the_size_is_checked_before_the_file_is_read(tmp_path, monkeypatch):
    """A file that does not fit is never read.

    The bytes of a file that is too large have to stay out of the
    memory of the process, so the size is asked for first.
    """
    path = _write(tmp_path / "output.txt", MAX_NAMED_FILE_BYTES + 1)

    def _no_read(self, *args, **kwargs):
        raise AssertionError("the file was read")

    monkeypatch.setattr(pathlib.Path, "read_text", _no_read)

    with pytest.raises(FileTooLargeError):
        read_named_text(path, "output file")


def test_a_named_file_that_is_not_utf8_is_refused(tmp_path):
    """A file that is not text is refused with a clear finding."""
    path = tmp_path / "output.bin"
    path.write_bytes(b"\xff\xfe\x00binary")

    with pytest.raises(UsageError) as failure:
        read_named_text(path, "output file")

    assert "not UTF-8 text" in str(failure.value)


def test_the_cli_refuses_an_output_file_that_is_too_large(repo_copy, tmp_path):
    """The evaluation refuses a material that does not fit."""
    path = _write(tmp_path / "huge.txt", MAX_NAMED_FILE_BYTES + 1)

    result = _cli(
        repo_copy,
        "evaluate",
        "--case",
        "COMM-001-CASE-001",
        "--output-file",
        str(path),
    )

    assert result.returncode == EXIT_USAGE
    assert "larger than the tool reads" in result.stdout
    assert "output file" in result.stdout


def test_the_cli_refuses_a_baseline_report_that_is_too_large(
    repo_copy, tmp_path
):
    """The comparison refuses a report that does not fit."""
    path = _write(tmp_path / "huge.json", MAX_NAMED_FILE_BYTES + 1)
    other = tmp_path / "small.json"
    other.write_text("{}", encoding="utf-8")

    result = _cli(
        repo_copy,
        "compare",
        "--baseline",
        str(path),
        "--current",
        str(other),
    )

    assert result.returncode == EXIT_USAGE
    assert "larger than the tool reads" in result.stdout
    assert "baseline report" in result.stdout


def test_the_cli_still_reads_a_report_that_fits(repo_copy, tmp_path):
    """The comparison still works for a report of a normal size."""
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"

    payload = {
        "schema_version": "0.2.0",
        "run_id": "run",
        "suite": {"id": "core-regression", "version": "0.2.1"},
        "cases": [],
        "summary": {"pass": 0, "fail": 0, "skip": 0, "error": 0},
    }

    baseline.write_text(json.dumps(payload), encoding="utf-8")
    current.write_text(json.dumps(payload), encoding="utf-8")

    result = _cli(
        repo_copy,
        "compare",
        "--baseline",
        str(baseline),
        "--current",
        str(current),
    )

    assert result.returncode == 0, result.stdout
