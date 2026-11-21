# SPDX-License-Identifier: MIT
"""Equivalence between the v0.2.0 implementation and the v0.1.x one.

Nine of the ten recorded scenarios were captured from the pre-v0.2.0
validator before the implementation moved into the `paisl` package.
Those must keep producing exactly the same output and exit codes.

The tenth scenario is marked as extended. The v0.2.0 record checks
add one finding to it, because a broken Catalog entry makes a
conflict record unresolvable. That scenario keeps its pre-v0.2.0
output next to the current expectation, and the test proves that the
baseline findings are preserved rather than replaced.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from scenarios import SCENARIOS

FIXTURES = (
    pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "legacy"
)

EXTENDED_SCENARIOS = {
    "missing_standard_file",
}


def expected_result(scenario: str) -> dict:
    """Load the recorded result for a scenario."""
    path = FIXTURES / f"{scenario}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def error_lines(text: str) -> set:
    """Return the error findings of a report."""
    return {
        line for line in text.splitlines() if line.startswith("ERROR:")
    }


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_validator_output_matches_recorded(
    repo_copy, run_validator, scenario
):
    """Every scenario must reproduce its recorded behaviour."""
    expected = expected_result(scenario)

    for mutation in SCENARIOS[scenario]:
        mutation(repo_copy)

    result = run_validator(repo_copy)

    assert result.stdout == expected["stdout"], (
        f"scenario {scenario}: stdout differs from the recorded baseline"
    )
    assert result.returncode == expected["exit_code"], (
        f"scenario {scenario}: exit code differs from the recorded baseline"
    )


@pytest.mark.parametrize(
    "scenario", sorted(set(SCENARIOS) - EXTENDED_SCENARIOS)
)
def test_legacy_scenarios_are_byte_identical(
    repo_copy, run_validator, scenario
):
    """The v0.1.x behaviour must be preserved exactly."""
    expected = expected_result(scenario)

    assert expected.get("provenance") == "legacy", (
        f"scenario {scenario} lost its legacy provenance"
    )

    for mutation in SCENARIOS[scenario]:
        mutation(repo_copy)

    result = run_validator(repo_copy)

    assert result.stdout == expected["stdout"]
    assert result.returncode == expected["exit_code"]


def test_extension_adds_findings_without_replacing_them(
    repo_copy, run_validator
):
    """The v0.2.0 checks extend the baseline, they never replace it."""
    scenario = "missing_standard_file"
    legacy = json.loads(
        (FIXTURES / f"{scenario}.legacy.json").read_text(encoding="utf-8")
    )
    current = expected_result(scenario)

    for mutation in SCENARIOS[scenario]:
        mutation(repo_copy)

    result = run_validator(repo_copy)

    assert error_lines(legacy["stdout"]) <= error_lines(result.stdout), (
        "the v0.2.0 checks removed a baseline finding"
    )
    assert result.stdout == current["stdout"]


def test_legacy_baselines_are_present():
    """Every scenario must have a recorded baseline."""
    for scenario in SCENARIOS:
        assert (FIXTURES / f"{scenario}.json").is_file(), (
            f"missing baseline for scenario {scenario}"
        )
