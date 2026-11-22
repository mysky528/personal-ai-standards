# SPDX-License-Identifier: MIT
"""The deterministic evaluators."""

from __future__ import annotations

import json

import pytest

from paisl.evaluators import (
    ERROR,
    FAIL,
    PASS,
    allowed_names,
    get_evaluator,
)
from paisl.evaluators.contains import ContainsEvaluator
from paisl.evaluators.excludes import ExcludesEvaluator
from paisl.evaluators.json_path import JsonPathEvaluator
from paisl.evaluators.regex import (
    MAX_PATTERN_LENGTH,
    RegexEvaluator,
)


def test_only_the_designed_evaluators_are_allowed():
    """The allowlist holds exactly the four designed evaluators."""
    assert allowed_names() == [
        "contains",
        "excludes",
        "json_path",
        "regex",
    ]
    assert get_evaluator("execute_python") is None


def test_contains_passes_and_fails():
    """The contains evaluator looks for an exact substring."""
    evaluator = ContainsEvaluator()

    result = evaluator.evaluate("Restart the service now.", {"text": "Restart"})
    assert result.status == PASS

    result = evaluator.evaluate("Restart the service now.", {"text": "Stop"})
    assert result.status == FAIL


def test_contains_needs_a_text_parameter():
    """A missing parameter is a failure, not a crash."""
    result = ContainsEvaluator().evaluate("anything", {})

    assert result.status == FAIL
    assert "text" in result.message


def test_excludes_passes_and_fails():
    """The excludes evaluator looks for an absent substring."""
    evaluator = ExcludesEvaluator()

    result = evaluator.evaluate("Restart the service now.", {"text": "maybe"})
    assert result.status == PASS

    result = evaluator.evaluate("maybe restart the service", {"text": "maybe"})
    assert result.status == FAIL


def test_regex_passes_and_fails():
    """The regex evaluator matches a pattern."""
    evaluator = RegexEvaluator()

    result = evaluator.evaluate("order-42", {"pattern": r"order-\d+"})
    assert result.status == PASS

    result = evaluator.evaluate("order-42", {"pattern": r"invoice-\d+"})
    assert result.status == FAIL


def test_regex_rejects_an_invalid_pattern():
    """A pattern that does not compile is an error."""
    result = RegexEvaluator().evaluate("anything", {"pattern": "([unclosed"})

    assert result.status == ERROR


def test_regex_rejects_a_long_pattern():
    """A pattern beyond the limit is an error."""
    result = RegexEvaluator().evaluate(
        "anything", {"pattern": "a" * (MAX_PATTERN_LENGTH + 1)}
    )

    assert result.status == ERROR
    assert str(MAX_PATTERN_LENGTH) in result.message


def test_regex_rejects_a_pattern_that_cannot_finish():
    """A construct that matches without end is refused."""
    result = RegexEvaluator().evaluate(
        "a" * 40 + "!", {"pattern": r"(a+)+$"}
    )

    assert result.status == ERROR
    assert "without end" in result.message


def test_regex_bounds_the_input():
    """A long output is truncated before it is matched."""
    evaluator = RegexEvaluator()

    result = evaluator.evaluate("x" * 100000, {"pattern": "x"})

    assert result.status == PASS
    assert result.details["truncated"] is True


def test_json_path_reads_a_value():
    """The path syntax addresses object keys and array indices."""
    evaluator = JsonPathEvaluator()
    document = json.dumps({
        "order": {"id": 42, "lines": [10, 20]},
    })

    result = evaluator.evaluate(
        document, {"path": "order.id", "equals": 42}
    )
    assert result.status == PASS

    result = evaluator.evaluate(document, {"path": "order.lines.1"})
    assert result.status == PASS


def test_json_path_reports_a_missing_path():
    """A path that is not present fails."""
    result = JsonPathEvaluator().evaluate(
        json.dumps({"order": {}}), {"path": "order.id"}
    )

    assert result.status == FAIL


def test_json_path_rejects_a_non_numeric_index():
    """The path syntax does not accept a name for an array."""
    result = JsonPathEvaluator().evaluate(
        json.dumps({"lines": [1, 2]}), {"path": "lines.first"}
    )

    assert result.status == FAIL


def test_json_path_reports_invalid_json():
    """An output that is not JSON is an error."""
    result = JsonPathEvaluator().evaluate("not json", {"path": "a"})

    assert result.status == ERROR


def test_json_path_is_not_jsonpath():
    """The path syntax does not support filters or wildcards."""
    result = JsonPathEvaluator().evaluate(
        json.dumps({"lines": [1, 2]}), {"path": "lines[0]"}
    )

    assert result.status == FAIL
