"""Input validation."""

import typing
import inspect
from schema import Schema, SchemaError, Or, Optional


TASK_SCHEMA = Schema(
    {
        Optional("type", default="http_request"): Or("http_request", "e2e"),
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
        Optional("target"): callable,
        Optional("target_input", default={}): dict,
        Optional("fail_on"): [
            {
                Optional("code"): int,
                Optional("body"): Or(dict, str),
                Optional("expected_match", default="strict"): Or("partial", "strict"),
            }
        ],
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


def input_validator_e2e_task(task):
    if task.get("type") == "e2e":
        if "target" not in task or not callable(task["target"]):
            raise ValueError("E2E task must have a callable 'target'.")
        if not inspect.iscoroutinefunction(task["target"]):
            raise ValueError("E2E task's 'target' must be an async function.")
    else:
        raise ValueError("Task must be of type 'e2e'.")
