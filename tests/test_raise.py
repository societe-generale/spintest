import json

import httpretty

from spintest import logger, spintest

logger.disabled = True


@httpretty.activate
def test_fail_on_in_partial_mode():
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"keys": ["ko", "waiting"]}),
        status=200,
    )

    result = spintest(
        ["http://test.com"],
        [
            {
                "method": "GET",
                "route": "/test",
                "expected": {
                    "code": 200,
                    "body": {"keys": ["ok"]},
                    "expected_match": "strict",
                },
                "fail_on": [
                    {
                        "body": {"keys": ["ko"]},
                        "expected_match": "partial",
                    }
                ],
                "retry": 1,
                "delay": 0,  # Make test quicker
            }
        ],
    )
    assert False is result
    expected_call_nb = 1  # No retry
    assert expected_call_nb == len(httpretty.latest_requests())


@httpretty.activate
def test_fail_on_in_strict_mode():
    for _i in range(2):
        httpretty.register_uri(
            httpretty.GET,
            "http://test.com/test",
            body=json.dumps({"keys": ["ko", "waiting"]}),
            status=200,
        )

    result = spintest(
        ["http://test.com"],
        [
            {
                "method": "GET",
                "route": "/test",
                "expected": {
                    "code": 200,
                    "body": {"keys": ["ok"]},
                    "expected_match": "strict",
                },
                "fail_on": [
                    {
                        "body": {"keys": ["ko"]},
                        "expected_match": "strict",
                    }
                ],
                "retry": 1,
                "delay": 0,  # Make test quicker
            }
        ],
    )
    assert False is result
    expected_call_nb = 2  # First call and then retry
    assert expected_call_nb == len(httpretty.latest_requests())


@httpretty.activate
def test_return_failure_immediately_when_response_is_in_fail_on_body():
    """Test raise ignore retries and returns responses immediately."""
    fake_responses = [
        {"resource": "FAILED"},
        {"resource": "FAILED"},
        {"resource": "CREATING"},
    ]
    for data in fake_responses:
        httpretty.register_uri(
            httpretty.GET, "http://test.com/test", body=json.dumps(data)
        )

    result = spintest(
        ["http://test.com"],
        [
            {
                "method": "GET",
                "route": "/test",
                "expected": {
                    "body": {"resource": "CREATED"},
                },
                "fail_on": [
                    {
                        "body": {"resource": "FAILED"},
                    }
                ],
                "retry": 2,
                "delay": 0,  # Make test quicker
            }
        ],
    )

    expected_call_nb = 2  # First call (CREATING) and retry (FAILED)
    assert expected_call_nb == len(httpretty.latest_requests())
    assert result is False


@httpretty.activate
def test_return_failure_immediately_when_response_is_in_the_second_fail_on_body():
    """Test raise ignore retries and returns responses immediately."""
    fake_responses = [
        {"resource": "FAILED"},
        {"resource": "FAILED"},
        {"resource": "CREATING"},
    ]
    for data in fake_responses:
        httpretty.register_uri(
            httpretty.GET, "http://test.com/test", body=json.dumps(data)
        )

    result = spintest(
        ["http://test.com"],
        [
            {
                "method": "GET",
                "route": "/test",
                "expected": {
                    "body": {"resource": "CREATED"},
                },
                "fail_on": [
                    {"body": {"resource": "ERROR"}},
                    {"body": {"resource": "FAILED"}},
                ],
                "retry": 2,
                "delay": 0,  # Make test quicker
            }
        ],
    )

    expected_call_nb = 2  # First call (CREATING) and retry (FAILED)
    assert expected_call_nb == len(httpretty.latest_requests())
    assert result is False


@httpretty.activate
def test_return_failure_immediately_when_response_is_in_fail_on_code():
    """Test raise ignore retries and returns responses immediately."""

    httpretty.register_uri(httpretty.GET, "http://test.com/test", status=404)

    result = spintest(
        ["http://test.com"],
        [
            {
                "method": "GET",
                "route": "/test",
                "expected": {
                    "body": {"resource": "CREATED"},
                },
                "fail_on": [{"code": 404}],
                "retry": 1,
                "delay": 0,  # Make test quicker
            }
        ],
    )

    expected_call_nb = 1  # First call (404)
    assert expected_call_nb == len(httpretty.latest_requests())
    assert result is False
