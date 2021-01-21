import json
import asyncio
import httpretty
from spintest import logger, spintest, TaskManager


logger.disabled = True


@httpretty.activate
def test_raise():
    """Test spintest with generate report"""
    httpretty.register_uri(
        httpretty.GET, "http://test.com/test", body=json.dumps({"status": "CREATING"})
    )
    httpretty.register_uri(
        httpretty.GET, "http://test.com/test", body=json.dumps({"status": "CREATING"})
    )
    httpretty.register_uri(
        httpretty.GET, "http://test.com/test", body=json.dumps({"status": "FAILED"})
    )
    loop = asyncio.new_event_loop()
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
            }
        ],
    )

    result1 = loop.run_until_complete(manager.next())
    print(result1)
    result2 = loop.run_until_complete(manager.next())
    print(result2)

    result3 = loop.run_until_complete(manager.next())
    print(result2)
    assert False is result3
