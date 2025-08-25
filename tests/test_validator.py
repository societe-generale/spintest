"""Test schema validation."""

import pytest

from spintest.validator import input_validator, TASK_SCHEMA


def test_TASK_SCHEMA():
    right_input = {"method": "GET", "route": "/foo/bar"}
    wrong_input = {"foo": "bar"}

    assert input_validator(right_input, TASK_SCHEMA)
    assert not input_validator(wrong_input, TASK_SCHEMA)


def test_task_schema_with_optional_key_expected_match_set_to_strict():
    right_input = {
        "method": "string",
        "route": "string",
        "expected": {"expected_match": "strict"},
    }

    assert input_validator(right_input, TASK_SCHEMA)


def test_task_schema_with_optional_key_expected_match_set_to_partial():
    right_input = {
        "method": "string",
        "route": "string",
        "expected": {"expected_match": "partial"},
    }

    assert input_validator(right_input, TASK_SCHEMA)


def test_task_schema_with_optional_key_expected_match_set_to_dummy_value():
    right_input = {
        "method": "string",
        "route": "string",
        "expected": {"expected_match": "dummy_value"},
    }

    assert None is input_validator(right_input, TASK_SCHEMA)


@pytest.mark.parametrize("match_mode", ["strict", "partial"])
def test_task_schema_with_optional_key_fail_on_and_match_accepted(match_mode):
    right_input = {
        "method": "string",
        "route": "string",
        "fail_on": [{"expected_match": match_mode}],
    }

    assert input_validator(right_input, TASK_SCHEMA)


def test_task_schema_with_optional_key_fail_on_and_code():
    right_input = {
        "method": "string",
        "route": "string",
        "fail_on": [{"code": 405}],
    }
    assert input_validator(right_input, TASK_SCHEMA)


def test_task_schema_with_optional_key_fail_on_and_body():
    right_input = {
        "method": "string",
        "route": "string",
        "fail_on": [{"body": {"key": "value"}}],
    }
    assert input_validator(right_input, TASK_SCHEMA)
