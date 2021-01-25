"""Input validation."""

import typing

from schema import Schema, SchemaError, Or, Optional


TASK_SCHEMA = Schema(
    {
        "method": str,
        Optional("route", default="/"): str,
        Optional("name"): str,
        Optional("body"): dict,
        Optional(
            "headers",
            default={"Accept": "application/json", "Content-Type": "application/json"},
        ): dict,
        Optional("output"): str,
        Optional("expected"): {
            Optional("code"): int,
            Optional("body"): Or(dict, str),
            Optional("expected_match", default="strict"): Or("partial", "strict"),
        },
        Optional("fail_on"): [{
            Optional("code"): int,
            Optional("body"): Or(dict, str),
            Optional("expected_match", default="strict"): Or("partial", "strict"),
        }],
        Optional("retry", default=0): int,
        Optional("delay", default=1): int,
        Optional("ignore", default=False): bool,
        Optional("rollback"): [Or(str, dict)],
    }
)


def input_validator(input, input_schema) -> typing.Optional[dict]:
    try:
        return input_schema.validate(input)
    except SchemaError:
        return None
