import json
import httpretty

from spintest import logger, spintest
from spintest.types import Int, List, Float, Bool

logger.disabled = True


def test_task_with_custom_type_evaluation():
    """Test spintest with a strict match on custom body."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps(
            {"inner": {"foo": 2, "bar": "buz", "qux": 2.23, "foobar": True}}
        ),
        status=200,
    )
    httpretty.register_uri(httpretty.POST, "http://test.com/test", status=200)

    spintest(
        ["http://test.com"],
        [
            {"method": "GET", "route": "/test", "output": "test"},
            {
                "method": "POST",
                "route": "/test",
                "body": {
                    "int": Int("{{ test['inner']['foo'] }}"),
                    "list": List("{{ test['inner']['bar'] }}"),
                    "float": Float("{{ test['inner']['qux'] }}"),
                    "bool": Bool("{{ test['inner']['foobar'] }}"),
                },
            },
        ],
    )

    assert json.loads(httpretty.last_request().body) == {
        "int": 2,
        "list": ["b", "u", "z"],
        "float": 2.23,
        "bool": True,
    }

    httpretty.disable()
    httpretty.reset()
