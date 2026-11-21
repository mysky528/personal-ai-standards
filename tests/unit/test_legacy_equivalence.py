# SPDX-License-Identifier: MIT
"""Equivalence between the v0.2.0 implementation and the v0.1.x one.

The expected outputs were captured from the pre-v0.2.0 validator
before the implementation moved into the `paisl` package. The
validator must keep producing exactly the same output and the same
exit codes.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from scenarios import SCENARIOS

FIXTURES = (
    pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "legacy"
)


def expected_result(scenario: str) -> dict:
    """Load the recorded result for a scenario."""
    path = FIXTURES / f"{scenario}.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_validator_output_matches_legacy(
    repo_copy, run_validator, scenario
):
    """Every scenario must reproduce the recorded legacy behaviour."""
    expected = expected_result(scenario)

    for mutation in SCENARIOS[scenario]:
        mutation(repo_copy)

    result = run_validator(repo_copy)

    assert result.stdout == expected["stdout"], (
        f"scenario {scenario}: stdout differs from the legacy baseline"
    )
    assert result.returncode == expected["exit_code"], (
        f"scenario {scenario}: exit code differs from the legacy baseline"
    )


def test_legacy_baselines_are_present():
    """Every scenario must have a recorded baseline."""
    for scenario in SCENARIOS:
        assert (FIXTURES / f"{scenario}.json").is_file(), (
            f"missing baseline for scenario {scenario}"
        )
