import json

import asyncio
import httpretty

from spintest import logger, TaskManager


logger.disabled = True


@httpretty.activate
def test_raise_return_failure_response_immediately():
    """Test raise ignore retries and returns responses immediately."""
    fake_responses = [
        {"status": "FAILED"},
        {"status": "FAILED"},
        {"status": "CREATING"},
    ]
    for data in fake_responses:
        httpretty.register_uri(
            httpretty.GET, "http://test.com/test", body=json.dumps(data)
        )

    manager = TaskManager(
        ["http://test.com"],
        [
            {
                "method": "GET",
                "route": "/test",
                "expected": {
                    "body": {"status": "CREATED"},
                },
                "raise": {
                    "body": {"status": "FAILED"},
                },
                "retry": 2,
                "delay": 0,  # Make test quicker
            }
        ],
    )

    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(manager.next())
    assert 2 == len(httpretty.latest_requests()), "Should calling 2 times instead of 3 (first call + 2 retries)"
    assert "FAILED" == result["status"]
