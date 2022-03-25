"""Test of rollback feature."""

import asyncio
import httpretty
import json

from spintest import logger, spintest, TaskManager

logger.disabled = True


def test_rollback_unkwnown_ref():
    """Test spintest with unknown rollback reference."""
    result = spintest(
        ["http://test.com"],
        [
            {"method": "POST", "route": "/test", "rollback": ["delete_test"]},
            {"method": "GET", "route": "/test"},
            {"method": "DELETE", "route": "/test"},
        ],
    )

    assert result is False


def test_rollback_unkwnown_ref_parallel():
    """Test spintest with unknown rollback reference parallel."""
    result = spintest(
        ["http://test.com"],
        [
            {"method": "POST", "route": "/test", "rollback": ["delete_test"]},
            {"method": "GET", "route": "/test"},
            {"method": "DELETE", "route": "/test"},
        ],
        parallel=True,
    )

    assert result is False


def test_rollback_with_output_value():
    """Test spintest with unknown rollback reference."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET, "http://test.com/test", status=201,
        body='{"id": "1234-5678"}',
    )
    httpretty.register_uri(httpretty.DELETE, "http://test.com/test/1234-5678", status=201)

    result = spintest(
        ["http://test.com"],
        [
            {
                "method": "GET",
                "route": "/test",
                "output": "test_output",
                "expected": {"code": 400},
                "rollback": ["test_rollback"],
            },
            {
                "name": "test_rollback",
                "method": "DELETE",
                "route": "/test/{{ test_output['id'] }}",
                "expected": {"code": 201}
            },
        ],
    )
    httpretty.disable()
    httpretty.reset()

    assert result is False


def test_rollback_invalid_schema():
    """Test spintest with unknown rollback reference."""
    result = spintest(
        ["http://test.com"],
        [
            {"method": "POST", "route": "/test", "rollback": [["toto"]]},
            {"method": "GET", "route": "/test"},
            {"method": "DELETE", "route": "/test"},
        ],
    )

    assert result is False


def test_rollback_ref():
    """Test spintest with rollback reference."""
    httpretty.enable()
    httpretty.register_uri(httpretty.POST, "http://test.com/test", status=201)
    httpretty.register_uri(httpretty.GET, "http://test.com/test", status=500)
    httpretty.register_uri(httpretty.DELETE, "http://test.com/test", status=204)

    loop = asyncio.new_event_loop()
    manager = TaskManager(
        ["http://test.com"],
        [
            {"method": "POST", "route": "/test", "rollback": ["delete_test"]},
            {"method": "GET", "route": "/test"},
            {"name": "delete_test", "method": "DELETE", "route": "/test"},
        ],
    )

    for _ in range(3):
        result = loop.run_until_complete(manager.next())

    assert result["name"] == "delete_test"
    assert result["ignore"] is True

    httpretty.disable()
    httpretty.reset()


def test_rollback_ref_parallel():
    """Test spintest with rollback parallel."""
    httpretty.enable()
    httpretty.register_uri(httpretty.POST, "http://test.com/test", status=201)
    httpretty.register_uri(httpretty.GET, "http://test.com/test", status=500)
    httpretty.register_uri(httpretty.DELETE, "http://test.com/test", status=204)

    spintest(
        ["http://test.com"],
        [
            {"method": "POST", "route": "/test", "rollback": ["delete_test"]},
            {"method": "GET", "route": "/test"},
            {"name": "delete_test", "method": "DELETE", "route": "/test"},
        ],
        parallel=True,
    )

    assert httpretty.last_request().method == httpretty.DELETE

    httpretty.disable()
    httpretty.reset()


def test_rollback_task():
    """Test spintest with rollback task."""
    httpretty.enable()
    httpretty.register_uri(httpretty.POST, "http://test.com/test", status=201)
    httpretty.register_uri(httpretty.GET, "http://test.com/test", status=500)
    httpretty.register_uri(httpretty.DELETE, "http://test.com/test", status=204)

    loop = asyncio.new_event_loop()
    manager = TaskManager(
        ["http://test.com"],
        [
            {
                "method": "POST",
                "route": "/test",
                "rollback": [
                    {"name": "rollback_test", "method": "DELETE", "route": "/test"}
                ],
            },
            {"method": "GET", "route": "/test"},
        ],
    )

    for _ in range(3):
        result = loop.run_until_complete(manager.next())

    assert result["name"] == "rollback_test"
    assert result["ignore"] is True

    httpretty.disable()
    httpretty.reset()


def test_rollback_multi_urls():
    """Test spintest with rollback on multiple URLS."""
    httpretty.enable()
    httpretty.register_uri(httpretty.POST, "http://foo.com/test", status=201)
    httpretty.register_uri(httpretty.GET, "http://foo.com/test", status=500)
    httpretty.register_uri(httpretty.DELETE, "http://foo.com/test", status=204)
    httpretty.register_uri(httpretty.POST, "http://bar.com/test", status=201)
    httpretty.register_uri(httpretty.GET, "http://bar.com/test", status=200)
    httpretty.register_uri(httpretty.DELETE, "http://bar.com/test", status=204)

    loop = asyncio.new_event_loop()
    manager = TaskManager(
        ["http://foo.com", "http://bar.com"],
        [
            {"method": "POST", "route": "/test", "rollback": ["delete_test"]},
            {"method": "GET", "route": "/test"},
            {"name": "delete_test", "method": "DELETE", "route": "/test"},
        ],
    )

    for _ in range(3):
        result = loop.run_until_complete(manager.next())

    assert result["name"] == "delete_test"
    assert result["ignore"] is True

    for _ in range(3):
        result = loop.run_until_complete(manager.next())

    assert result["name"] == "delete_test"
    assert result["ignore"] is False

    httpretty.disable()
    httpretty.reset()


def test_rollback_multi_urls_parallel():
    """Test spintest with rollback on multiple URLS parallel."""
    httpretty.enable()
    httpretty.register_uri(httpretty.POST, "http://foo.com/test", status=201)
    httpretty.register_uri(httpretty.GET, "http://foo.com/test", status=500)
    httpretty.register_uri(httpretty.DELETE, "http://foo.com/test", status=204)
    httpretty.register_uri(httpretty.POST, "http://bar.com/test", status=201)
    httpretty.register_uri(httpretty.GET, "http://bar.com/test", status=200)
    httpretty.register_uri(httpretty.DELETE, "http://bar.com/test", status=204)

    loop = asyncio.new_event_loop()
    manager = TaskManager(
        ["http://foo.com", "http://bar.com"],
        [
            {"method": "POST", "route": "/test", "rollback": ["delete_test"]},
            {"method": "GET", "route": "/test"},
            {"name": "delete_test", "method": "DELETE", "route": "/test"},
        ],
        parallel=True,
    )

    for _ in range(4):
        result = loop.run_until_complete(manager.next())

    assert result["name"] == "delete_test"
    assert result["ignore"] is True

    httpretty.disable()
    httpretty.reset()


def test_rollback_multi_rollbacks():
    """Test spintest with multiple rollbacks."""
    httpretty.enable()
    httpretty.register_uri(httpretty.POST, "http://test.com/test", status=201)
    httpretty.register_uri(httpretty.GET, "http://test.com/test", status=500)
    httpretty.register_uri(httpretty.DELETE, "http://test.com/test", status=500)
    httpretty.register_uri(httpretty.DELETE, "http://test.com/test_2", status=204)

    loop = asyncio.new_event_loop()
    manager = TaskManager(
        ["http://test.com"],
        [
            {
                "method": "POST",
                "route": "/test",
                "rollback": ["delete_test", "delete_test_2"],
            },
            {"method": "GET", "route": "/test"},
            {"name": "delete_test", "method": "DELETE", "route": "/test"},
            {"name": "delete_test_2", "method": "DELETE", "route": "/test_2"},
        ],
    )

    for _ in range(4):
        result = loop.run_until_complete(manager.next())

    assert result["name"] == "delete_test_2"
    assert result["ignore"] is True

    httpretty.disable()
    httpretty.reset()


def test_rollback_multi_rollbacks_parallel():
    """Test spintest with multiple rollbacks parallel."""
    httpretty.enable()
    httpretty.register_uri(httpretty.POST, "http://test.com/test", status=201)
    httpretty.register_uri(httpretty.GET, "http://test.com/test", status=500)
    httpretty.register_uri(httpretty.DELETE, "http://test.com/test", status=500)
    httpretty.register_uri(httpretty.DELETE, "http://test.com/test_2", status=204)

    loop = asyncio.new_event_loop()
    manager = TaskManager(
        ["http://test.com"],
        [
            {
                "method": "POST",
                "route": "/test",
                "rollback": ["delete_test", "delete_test_2"],
            },
            {"method": "GET", "route": "/test"},
            {"name": "delete_test", "method": "DELETE", "route": "/test"},
            {"name": "delete_test_2", "method": "DELETE", "route": "/test_2"},
        ],
    )

    for _ in range(4):
        result = loop.run_until_complete(manager.next())

    assert result["name"] == "delete_test_2"
    assert result["ignore"] is True

    httpretty.disable()
    httpretty.reset()


def test_rollback_templating():
    """Test spintest with templating."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.POST, "http://test.com/test", body=json.dumps({"foo": "bar"})
    )
    httpretty.register_uri(httpretty.GET, "http://test.com/test", status=500)
    httpretty.register_uri(httpretty.DELETE, "http://test.com/bar", status=204)

    spintest(
        ["http://test.com"],
        [
            {
                "method": "POST",
                "route": "/test",
                "output": "test",
                "rollback": ["delete_test"],
            },
            {"method": "GET", "route": "/test"},
            {"name": "delete_test", "method": "DELETE", "route": "/{{ test['foo'] }}"},
        ],
    )

    assert httpretty.last_request().method == httpretty.DELETE

    httpretty.disable()
    httpretty.reset()


def test_rollback_templating_definition_inside():
    """Test spintest with templating inside rollback."""
    httpretty.enable()
    httpretty.register_uri(httpretty.POST, "http://test.com/test", status=500)
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"foo": "bar"}),
        status=200,
    )
    httpretty.register_uri(httpretty.DELETE, "http://test.com/bar", status=204)

    spintest(
        ["http://test.com"],
        [
            {
                "method": "POST",
                "route": "/test",
                "rollback": [
                    {"method": "GET", "route": "/test", "output": "test"},
                    {"method": "DELETE", "route": "/{{ test['foo'] }}"},
                ],
            }
        ],
    )

    assert httpretty.last_request().method == httpretty.DELETE

    httpretty.disable()
    httpretty.reset()


def test_rollback_templating_definition_inside_parallel():
    """Test spintest with templating inside rollback."""
    httpretty.enable()
    httpretty.register_uri(httpretty.POST, "http://test.com/test", status=500)
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=json.dumps({"foo": "bar"}),
        status=200,
    )
    httpretty.register_uri(httpretty.DELETE, "http://test.com/bar", status=204)

    spintest(
        ["http://test.com"],
        [
            {
                "method": "POST",
                "route": "/test",
                "rollback": [
                    {"method": "GET", "route": "/test", "output": "test"},
                    {"method": "DELETE", "route": "/{{ test['foo'] }}"},
                ],
            }
        ],
        parallel=True,
    )

    assert httpretty.last_request().method == httpretty.DELETE

    httpretty.disable()
    httpretty.reset()


def test_rollback_templating_parallel():
    """Test spintest with templating parallel."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.POST, "http://test.com/test", body=json.dumps({"foo": "bar"})
    )
    httpretty.register_uri(httpretty.GET, "http://test.com/test", status=500)
    httpretty.register_uri(httpretty.DELETE, "http://test.com/bar", status=204)

    spintest(
        ["http://test.com"],
        [
            {
                "method": "POST",
                "route": "/test",
                "output": "test",
                "rollback": ["delete_test"],
            },
            {"method": "GET", "route": "/test"},
            {"name": "delete_test", "method": "DELETE", "route": "/{{ test['foo'] }}"},
        ],
        parallel=True,
    )

    assert httpretty.last_request().method == httpretty.DELETE

    httpretty.disable()
    httpretty.reset()


def test_rollback_failed():
    """Test spintest with failed rollback."""
    httpretty.enable()
    httpretty.register_uri(httpretty.POST, "http://test.com/test", status=201)
    httpretty.register_uri(httpretty.GET, "http://test.com/test", status=500)
    httpretty.register_uri(httpretty.DELETE, "http://test.com/test", status=500)

    spintest(
        ["http://test.com"],
        [
            {"method": "POST", "route": "/test", "rollback": ["delete_test"]},
            {"method": "GET", "route": "/test"},
            {"name": "delete_test", "method": "DELETE", "route": "/test"},
        ],
    )

    assert httpretty.last_request().method == httpretty.DELETE

    httpretty.disable()
    httpretty.reset()


def test_rollback_failed_parallel():
    """Test spintest with failed rollback."""
    httpretty.enable()
    httpretty.register_uri(httpretty.POST, "http://test.com/test", status=201)
    httpretty.register_uri(httpretty.GET, "http://test.com/test", status=500)
    httpretty.register_uri(httpretty.DELETE, "http://test.com/test", status=500)

    spintest(
        ["http://test.com"],
        [
            {"method": "POST", "route": "/test", "rollback": ["delete_test"]},
            {"method": "GET", "route": "/test"},
            {"name": "delete_test", "method": "DELETE", "route": "/test"},
        ],
        parallel=True,
    )

    assert httpretty.last_request().method == httpretty.DELETE

    httpretty.disable()
    httpretty.reset()
