import asyncio
import json
import uuid
import httpretty
import pytest
from spintest import logger, spintest, TaskManager

logger.disabled = True


class FakeCreatedToken:
    """Function use to create token."""

    def __init__(self):
        self.call_count = 0

    def __call__(self):
        self.call_count += 1
        return str(self.call_count)


def test_task_with_token_token_is_not_visible_on_log():
    """Test spintest with a strict match on custom body."""
    TOKEN = str(uuid.uuid4())
    httpretty.enable()

    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"a": "a", "b": "b", "c": "c"}),
        status=200,
    )

    tasks = [
        {
            "method": "GET",
            "route": "/test",
            "expected": {
                "code": 200,
                "body": {"a": "a", "b": "b", "c": "c"},
                "expected_match": "strict",
            },
        }
    ]

    loop = asyncio.get_event_loop()
    results = []
    manager = TaskManager(["http://test.com"], tasks, token=TOKEN)

    for i in range(len(tasks)):
        result = loop.run_until_complete(manager.next())
        results.append(result)

    assert TOKEN not in results[0]["task"]["headers"]["Authorization"]

    httpretty.disable()
    httpretty.reset()


def test_task_with_fix_token_set_configuration():
    """Test spintest with a strict match on custom body."""
    httpretty.enable()

    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"a": "a", "b": "b", "c": "c"}),
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
                    "body": {"a": "a", "b": "b", "c": "c"},
                    "expected_match": "strict",
                },
            }
        ],
        token="ABC",
    )

    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_task_with_fuct_token_set_configuration():
    """Test spintest with a strict match on custom body."""
    httpretty.enable()

    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"a": "a", "b": "b", "c": "c"}),
        status=200,
    )

    token = FakeCreatedToken()
    result = spintest(
        ["http://test.com"],
        [
            {
                "method": "GET",
                "route": "/test",
                "expected": {
                    "code": 200,
                    "body": {"a": "a", "b": "b", "c": "c"},
                    "expected_match": "strict",
                },
            }
        ],
        token=token(),
    )

    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_two_tokens_are_generated_with_one_task_with_two_retry():
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        status=200,
        body=json.dumps({"status": "CREATED"}),
    )
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        status=200,
        body=json.dumps({"status": "CREATING"}),
    )
    loop = asyncio.new_event_loop()
    token_func = FakeCreatedToken()
    manager = TaskManager(
        ["http://test.com"],
        [
            {
                "method": "GET",
                "route": "/test",
                "expected": {"body": {"status": "CREATED"}},
                "retry": 1,
            }
        ],
        token=token_func,
    )
    result = loop.run_until_complete(manager.next())
    assert "SUCCESS" == result["status"]
    assert token_func.call_count == 2

    httpretty.disable()
    httpretty.reset()


def test_task_with_ayncio_loop_and_fuct_token_set_configuration():
    """Test spintest with a strict match on custom body."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"a": "a", "b": "b", "c": "c"}),
        status=200,
    )
    loop = asyncio.new_event_loop()
    token_func = FakeCreatedToken()
    manager = TaskManager(
        ["http://test.com"],
        [{"method": "GET", "route": "/test"}, {"method": "GET", "route": "/test"}],
        token=token_func,
    )
    result = loop.run_until_complete(manager.next())
    assert "SUCCESS" == result["status"]
    assert token_func.call_count == 1
    result1 = loop.run_until_complete(manager.next())
    assert "SUCCESS" == result1["status"]
    assert token_func.call_count == 2

    httpretty.disable()
    httpretty.reset()


def test_task_strict_all_keys():
    """Test spintest with a strict match on custom body."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"a": "a", "b": "b", "c": "c"}),
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
                    "body": {"a": "a", "b": "b", "c": "c"},
                    "expected_match": "strict",
                },
            }
        ],
    )

    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_task_partial_value_works_like_strict_keys_values():
    """Test spintest with a partial custom body."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"a": "a", "b": "b", "c": "c"}),
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
                    "body": {"a": "a", "b": "b", "c": "c"},
                    "expected_match": "partial",
                },
            }
        ],
    )

    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_task_strict_expected_complete_list_values():
    """Test spintest with a strict match on body with list."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"keys": ["a", "b", "c"]}),
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
                    "body": {"keys": ["a", "b", "c"]},
                    "expected_match": "strict",
                },
            }
        ],
    )
    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_task_strict_expected_cmp_list_with_multiple_identics_values():
    """Test spintest with a strict match on custom body."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"keys": ["a", "b", "c"]}),
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
                    "body": {"keys": ["a", "b", "b"]},
                    "expected_match": "strict",
                },
            }
        ],
    )
    assert False is result

    httpretty.disable()
    httpretty.reset()


def test_task_strict_expected_cmp_list_with_many_identics_double_values():
    """Test spintest with a strict match on custom body."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"keys": ["a", "b", "b"]}),
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
                    "body": {"keys": ["a", "b", "a", "a"]},
                    "expected_match": "strict",
                },
            }
        ],
    )
    assert False is result

    httpretty.disable()
    httpretty.reset()


def test_task_strict_expectedlist_multiple_None():
    """Test spintest with a None value in custom body."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"keys": ["a", "b", "c"]}),
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
                    "body": {"keys": [None, "a", None]},
                    "expected_match": "strict",
                },
            }
        ],
    )
    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_task_strict_expected_list_None():
    """Test spintest with a None value in custom body."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"keys": ["a", "b"]}),
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
                    "body": {"keys": [None, "a"]},
                    "expected_match": "strict",
                },
            }
        ],
    )
    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_task_stric_expected_partial_list():
    """Test spintest with a None value in custom body."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"keys": ["a", "b", "c"]}),
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
                    "body": {"keys": ["a"]},
                    "expected_match": "strict",
                },
            }
        ],
    )
    assert False is result

    httpretty.disable()
    httpretty.reset()


def test_task_partial_expected_list():
    """Test spintest with a partial match on custom body."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"keys": ["a", "b", "c"]}),
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
                    "body": {"keys": ["a"]},
                    "expected_match": "partial",
                },
            }
        ],
    )
    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_task_partial_expected_dict_keys():
    """Test spintest with a partial match on a custom body with dict."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"a": "a", "b": "b", "c": "c"}),
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
                    "body": {"b": "b"},
                    "expected_match": "partial",
                },
            }
        ],
    )
    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_task_partial_expected_dict_keys_failed():
    """Test spintest with a failed partial match on a custom body with dict."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"a": "a", "b": "b", "c": "c"}),
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
                    "body": {"d": "d"},
                    "expected_match": "partial",
                },
            }
        ],
    )
    assert False is result

    httpretty.disable()
    httpretty.reset()


def test_task_basic():
    """Test basic spintest."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET, "http://test.com/test", body=json.dumps({"foo": "bar"})
    )

    result = spintest(["http://test.com"], [{"method": "GET", "route": "/test"}])

    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_task_basic_no_verify():
    """Test basic spintest with verify set to false."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET, "http://test.com/test", body=json.dumps({"foo": "bar"})
    )

    result = spintest(
        ["http://test.com"], [{"method": "GET", "route": "/test"}], verify=False
    )

    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_task_basic_parallel():
    """Test spintest with parallel urls."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET, "http://test.com/test", body=json.dumps({"foo": "bar"})
    )

    result = spintest(
        ["http://test.com"], [{"method": "GET", "route": "/test"}], parallel=True
    )

    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_task_basic_token():
    """Test spintest with basic token."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET, "http://test.com/test", body=json.dumps({"foo": "bar"})
    )

    result = spintest(
        ["http://test.com"], [{"method": "GET", "route": "/test"}], token="string"
    )

    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_task_invalid_method():
    """Test spintest with invalid method."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET, "http://test.com/test", body=json.dumps({"foo": "bar"})
    )

    result = spintest(["http://test.com"], [{"method": "FOO", "route": "/test"}])

    assert False is result

    httpretty.disable()
    httpretty.reset()


def test_task_basic_templating():
    """Test spintest with templating."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET, "http://test.com/test", body=json.dumps({"foo": "bar"})
    )
    httpretty.register_uri(httpretty.GET, "http://test.com/bar")

    result = spintest(
        ["http://test.com"],
        [
            {"method": "GET", "route": "/test", "output": "test"},
            {"method": "GET", "route": "/{{ test['foo'] }}"},
        ],
    )

    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_task_invalid_task_no_method():
    """Test spintest with an invalid task."""
    httpretty.enable()
    httpretty.register_uri(httpretty.GET, "http://test.com/test")

    result = spintest(["http://test.com"], [{"route": "/test"}])

    assert False is result

    httpretty.disable()
    httpretty.reset()


def test_task_invalid_task_default_route():
    """Test spintest with an invalid task."""
    httpretty.enable()
    httpretty.register_uri(httpretty.GET, "http://test.com/")

    result = spintest(["http://test.com"], [{"method": "GET"}])

    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_task_bad_status_code():
    """Test spintest against an url with 404 status code."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"error": "foo"}),
        status=404,
    )

    result = spintest(["http://test.com"], [{"method": "GET", "route": "/test"}])

    assert False is result

    httpretty.disable()
    httpretty.reset()


def test_task_custom_status_code():
    """Test spintest with a custom statius code."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"error": "foo"}),
        status=404,
    )

    result = spintest(
        ["http://test.com"],
        [{"method": "GET", "route": "/test", "expected": {"code": 404}}],
    )

    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_task_custom_status_code_failed():
    """Test spintest with a wrong custom status code."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"error": "foo"}),
        status=404,
    )

    result = spintest(
        ["http://test.com"],
        [{"method": "GET", "route": "/test", "expected": {"code": 403}}],
    )

    assert False is result

    httpretty.disable()
    httpretty.reset()


def test_task_custom_body():
    """Test spintest with a custom body and status code."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"error": "foo"}),
        status=404,
    )

    result = spintest(
        ["http://test.com"],
        [
            {
                "method": "GET",
                "route": "/test",
                "expected": {"code": 404, "body": {"error": "foo"}},
            }
        ],
    )

    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_task_partial_body():
    """Test spintest with a partial custom body."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps(
            {
                "a": "a",
                "b": 1,
                "c": "c",
                "d": {"a": "a", "b": 1, "c": "c"},
                "e": {"a": "a", "b": 1, "c": "c"},
                "f": [{"a": "a", "b": 1, "c": "c"}, {"d": "d", "e": 2, "f": "f"}],
            }
        ),
        status=200,
    )

    result = spintest(
        ["http://test.com"],
        [
            {
                "method": "GET",
                "route": "/test",
                "expected": {
                    "body": {
                        "a": "a",
                        "b": 1,
                        "c": None,
                        "d": {"a": "a", "b": 1, "c": None},
                        "e": None,
                        "f": [
                            {"a": None, "b": None, "c": None},
                            {"d": "d", "e": 2, "f": None},
                        ],
                    }
                },
            }
        ],
    )

    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_partial_response_body_validation_with_expected_key_name_with_needed_param():
    """Test spintest can validate a response body with an expected partial
    body.
    """
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"a": "a", "b": "b", "c": "c"}),
        status=200,
    )
    result = spintest(
        ["http://test.com"],
        [
            {
                "method": "GET",
                "route": "/test",
                "expected": {
                    "body": {"a": "a", "b": "b", "c": "c"},
                    "expected_match": "strict",
                },
            }
        ],
    )
    assert True is result
    httpretty.disable()
    httpretty.reset()


def test_task_partial_body_invalid_type():
    """Test spintest with a failed partial custom body."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET, "http://test.com/test", body=json.dumps({"a": "a"}), status=200
    )

    result = spintest(
        ["http://test.com"],
        [{"method": "GET", "route": "/test", "expected": {"body": {"a": 1}}}],
    )

    assert False is result

    httpretty.disable()
    httpretty.reset()


def test_task_partial_body_invalid_list():
    """Test spintest with a failed partial custom body."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"a": [{"a": "a"}, {"b": "b"}]}),
        status=200,
    )

    result = spintest(
        ["http://test.com"],
        [
            {
                "method": "GET",
                "route": "/test",
                "expected": {"body": {"a": [{"c": "c"}]}},
            }
        ],
    )

    assert False is result

    httpretty.disable()
    httpretty.reset()


def test_task_custom_body_flat():
    """Test spintest with a flat body."""
    httpretty.enable()
    httpretty.register_uri(httpretty.GET, "http://test.com/test", body="text")

    result = spintest(
        ["http://test.com"],
        [{"method": "GET", "route": "/test", "expected": {"body": "text"}}],
    )

    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_task_custom_body_failed():
    """Test spintest with a wrong custom body."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"error": "foo"}),
        status=404,
    )

    result = spintest(
        ["http://test.com"],
        [
            {
                "method": "GET",
                "route": "/test",
                "expected": {"code": 404, "body": {"error": "bar"}},
            }
        ],
    )

    assert False is result

    httpretty.disable()
    httpretty.reset()


def test_task_next():
    """Test spintest accessing with next."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET, "http://test.com/test", body=json.dumps({"foo": "bar"})
    )

    loop = asyncio.new_event_loop()
    manager = TaskManager(["http://test.com"], [{"method": "GET", "route": "/test"}])
    result = loop.run_until_complete(manager.next())

    assert "SUCCESS" == result["status"]
    assert "OK." == result["message"]
    assert 200 == result["code"]
    assert {"foo": "bar"} == result["body"]
    assert "http://test.com" == result["url"]
    assert "/test" == result["route"]
    # Because comparing floats is hard and is not the goal of this test
    result["task"]["duration_sec"] = 42.0
    assert {
        "method": "GET",
        "route": "/test",
        "target_input": {},
        "headers": {"Accept": "application/json", "Content-Type": "application/json"},
        "retry": 0,
        "delay": 1,
        "ignore": False,
        "duration_sec": 42.0,
        "type": "http_request",
    } == result["task"]

    assert {"__token__": None} == result["output"]

    with pytest.raises(StopAsyncIteration):
        loop.run_until_complete(manager.next())

    httpretty.disable()
    httpretty.reset()


def test_task_next_async():
    """Test spintest accessing with next asynchronously."""
    httpretty.enable()
    httpretty.register_uri(httpretty.GET, "http://foo.com/test")
    httpretty.register_uri(httpretty.GET, "http://bar.com/test")

    loop = asyncio.new_event_loop()
    manager = TaskManager(
        ["http://foo.com", "http://bar.com"],
        [{"method": "GET", "route": "/test"}],
        parallel=True,
    )
    results = loop.run_until_complete(manager.next())

    for result in results:
        assert "SUCCESS" == result["status"]

    with pytest.raises(StopAsyncIteration):
        loop.run_until_complete(manager.next())

    httpretty.disable()
    httpretty.reset()


def test_task_next_async_failed():
    """Test spintest accessing with next asynchronously."""
    httpretty.enable()
    httpretty.register_uri(httpretty.GET, "http://foo.com/test")
    httpretty.register_uri(httpretty.GET, "http://bar.com/test", status=500)

    loop = asyncio.new_event_loop()
    manager = TaskManager(
        ["http://foo.com", "http://bar.com"],
        [{"method": "GET", "route": "/test"}],
        parallel=True,
    )
    results = loop.run_until_complete(manager.next())

    assert "SUCCESS" in [result["status"] for result in results]
    assert "FAILED" in [result["status"] for result in results]

    with pytest.raises(StopAsyncIteration):
        loop.run_until_complete(manager.next())

    httpretty.disable()
    httpretty.reset()


def test_task_with_ignore_option():
    """Test spintest with ignore option."""
    httpretty.enable()
    httpretty.register_uri(httpretty.GET, "http://test.com/test", status=500)

    result = spintest(
        ["http://test.com"], [{"method": "GET", "route": "/test", "ignore": True}]
    )

    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_task_with_ignore_option_followed_by_error():
    """Test spintest with ignore option."""
    httpretty.enable()
    httpretty.register_uri(httpretty.GET, "http://test.com/test", status=500)

    result = spintest(
        ["http://test.com"],
        [
            {"method": "GET", "route": "/test", "ignore": True},
            {"method": "GET", "route": "/test"},
        ],
    )

    assert False is result

    httpretty.disable()
    httpretty.reset()
