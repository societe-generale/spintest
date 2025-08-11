import pytest
from spintest.e2e_task import E2ETask
from unittest.mock import AsyncMock
from spintest import spintest
import httpretty
import json


@pytest.fixture
def valid_task():
    return {
        "type": "e2e",
        "name": "test_task",
        "target": AsyncMock(),
        "ignore": False,
    }


def test_valid_task_target_callable(valid_task):
    assert callable(valid_task["target"])


@pytest.fixture
def invalid_task():
    return {
        "type": "e2e",
        "name": "test_task",
        "target": None,  # Invalid target
        "ignore": False,
    }


@pytest.fixture
def url():
    return "http://example.com"


def test_e2e_task_initialization(valid_task, url):
    task = E2ETask(url, valid_task)
    assert task.url == url
    assert task.task == valid_task
    assert task.name == valid_task["name"]
    assert task.target == valid_task["target"]


def test_e2e_task_response_success(valid_task, url):
    task = E2ETask(url, valid_task)
    response = task._response("SUCCESS", "mock_target", "Task executed successfully.")
    assert response["status"] == "SUCCESS"
    assert response["message"] == "Task executed successfully."
    assert response["name"] == valid_task["name"]
    assert response["url"] == url


def test_e2e_task_response_failure(valid_task, url):
    task = E2ETask(url, valid_task)
    response = task._response("FAILURE", "mock_target", "Task failed.")
    assert response["status"] == "FAILURE"
    assert response["message"] == "Task failed."
    assert response["name"] == valid_task["name"]
    assert response["url"] == url


@pytest.mark.asyncio
async def test_e2e_task_run_success(valid_task, url):
    async def target(url):
        return None

    valid_task["target"] = target
    task = E2ETask(url, valid_task)
    response = await task.run()
    assert response["status"] == "SUCCESS"
    assert response["message"] == "Task executed successfully."
    assert response["duration_sec"] is not None


@pytest.mark.asyncio
async def test_e2e_task_run_failure_assertion(valid_task, url):
    async def failing_target(url):
        raise AssertionError("Test assertion error")

    valid_task["target"] = failing_target
    task = E2ETask(url, valid_task)
    response = await task.run()
    assert response["status"] == "FAILURE"
    assert (
        response["message"]
        == f"Task '{valid_task['name']}' failed due to assertion error: "
        "Test assertion error"
    )


@pytest.mark.asyncio
async def test_e2e_task_run_failure_exception(valid_task, url):
    async def failing_target(url):
        raise Exception("Test exception")

    valid_task["target"] = failing_target
    task = E2ETask(url, valid_task)
    response = await task.run()
    assert response["status"] == "ERROR"
    assert (
        response["message"]
        == f"Task '{valid_task['name']}' encountered an error: Test exception"
    )


@pytest.mark.asyncio
async def test_e2e_task_initialization_invalid_task(invalid_task, url):
    task = E2ETask(url, invalid_task)
    response = await task.run()
    assert response["status"] == "FAILURE"
    assert (
        response["message"]
        == f"Task '{invalid_task['name']}' schema validation failed: "
        "E2E task must have a callable 'target'."
    )


def test_e2e_task_success():

    async def target(url):
        # Simulate a successful E2E task
        assert url == "http://test.com"

    result = spintest(["http://test.com"], [{"type": "e2e", "target": target}])

    assert True is result


def test_e2e_task_invalid_target_not_callable():

    target = "invalid_target"  # Not callable

    result = spintest(["http://test.com"], [{"type": "e2e", "target": target}])

    assert False is result


def test_e2e_task_invalid_target_not_async():

    def target(url):
        # Simulate a non-async target
        assert url == "http://test.com"

    result = spintest(["http://test.com"], [{"type": "e2e", "target": target}])

    assert False is result


def test_e2e_task_invalid_type():

    async def target(url):
        # Simulate a successful E2E task
        assert url == "http://test.com"

    result = spintest(["http://test.com"], [{"type": "invalid_type", "target": target}])

    assert False is result


def test_e2e_task_missing_target():

    result = spintest(["http://test.com"], [{"type": "e2e"}])

    assert False is result


def test_e2e_task_missing_type():

    async def target(url):
        # Simulate a successful E2E task
        assert url == "http://test.com"

    result = spintest(["http://test.com"], [{"target": target}])

    assert False is result


def test_e2e_task_ignore_true():

    async def target(url):
        # Simulate a successful E2E task
        assert url == "http://test.com"

    result = spintest(
        ["http://test.com"], [{"type": "e2e", "target": target, "ignore": True}]
    )

    assert True is result


def test_e2e_task_and_http_task_success():

    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET, "http://test.com/test", body=json.dumps({"foo": "bar"})
    )

    async def target(url):
        # Simulate a successful E2E task
        assert url == "http://test.com"

    result = spintest(
        ["http://test.com"],
        [{"type": "e2e", "target": target}, {"method": "GET", "route": "/test"}],
    )
    assert True is result

    httpretty.disable()
    httpretty.reset()


def test_e2e_fail_and_http_success():

    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET, "http://test.com/test", body=json.dumps({"foo": "bar"})
    )

    async def target(url):
        # Simulate a failing E2E task
        raise Exception("Simulated failure")

    result = spintest(
        ["http://test.com"],
        [{"type": "e2e", "target": target}, {"method": "GET", "route": "/test"}],
    )
    assert False is result

    httpretty.disable()
    httpretty.reset()


def test_one_e2e_pass_and_one_fail():

    async def target_pass(url):
        # Simulate a successful E2E task
        assert url == "http://test.com/pass"

    async def target_fail(url):
        # Simulate a failing E2E task
        raise Exception("Simulated failure")

    result = spintest(
        ["http://test.com/pass", "http://test.com/fail"],
        [
            {"type": "e2e", "target": target_pass},
            {"type": "e2e", "target": target_fail},
        ],
    )

    assert False is result


def test_e2e_pass_and_http_fail():

    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET, "http://test.com/test", status=500, body="Internal Server Error"
    )

    async def target(url):
        # Simulate a successful E2E task
        assert url == "http://test.com"

    result = spintest(
        ["http://test.com"],
        [{"type": "e2e", "target": target}, {"method": "GET", "route": "/test"}],
    )
    assert False is result

    httpretty.disable()
    httpretty.reset()


def test_e2e_with_inputs_success():

    async def target(url, input_data):
        # Simulate a successful E2E task with inputs
        assert url == "http://test.com"
        assert input_data == {"key": "value"}

    result = spintest(
        ["http://test.com"],
        [
            {
                "type": "e2e",
                "target": target,
                "target_input": {"input_data": {"key": "value"}},
            }
        ],
    )

    assert True is result


def test_e2e_with_multiple_inputs_success():

    async def target(url, input_data1, input_data2):
        # Simulate a successful E2E task with multiple inputs
        assert url == "http://test.com"
        assert input_data1 == {"key1": "value1"}
        assert input_data2 == {"key2": "value2"}

    result = spintest(
        ["http://test.com"],
        [
            {
                "type": "e2e",
                "target": target,
                "target_input": {
                    "input_data1": {"key1": "value1"},
                    "input_data2": {"key2": "value2"},
                },
            }
        ],
    )

    assert True is result


def test_one_e2e_with_input_and_one_without_input():

    async def target_with_input(url, input_data):
        # Simulate a successful E2E task with inputs
        assert url == "http://test.com/"
        assert input_data == {"key": "value"}

    async def target_without_input(url):
        # Simulate a successful E2E task without inputs
        assert url == "http://test.com/"

    result = spintest(
        ["http://test.com/"],
        [
            {
                "type": "e2e",
                "target": target_with_input,
                "target_input": {"input_data": {"key": "value"}},
            },
            {"type": "e2e", "target": target_without_input},
        ],
    )

    assert True is result


def test_e2e_with_inputs_fail():

    async def target_with_input(url, a, b, c):
        # Simulate a successful E2E task with inputs
        assert url == "http://test.com"
        assert a + b != c

    result = spintest(
        ["http://test.com"],
        [
            {
                "type": "e2e",
                "target": target_with_input,
                "target_input": {"a": 1, "b": 2, "c": 3},
            }
        ],
    )

    assert False is result


def test_e2e_task_field_is_not_dict():

    async def target(url, input_data):
        # Simulate a successful E2E task with inputs
        assert url == "http://test.com"
        assert input_data == "not_a_dict"

    result = spintest(
        ["http://test.com"],
        [{"type": "e2e", "target": target, "target_input": "not_a_dict"}],
    )

    assert False is result


def test_e2e_task_with_rollback_success():
    async def target(url):
        # Simulate a successful E2E task
        assert url == "http://test.com"

    async def target_rollback(url):
        # Simulate a successful rollback task
        assert url == "http://test.com"

    tasks = [
        {
            "type": "e2e",
            "name": "main_task",
            "target": target,
            "rollback": ["rollback_task"],
        },
        {
            "type": "e2e",
            "name": "rollback_task",
            "target": target_rollback,
            "ignore": True,
        },
    ]

    result = spintest(["http://test.com"], tasks)

    assert True is result


def test_target_with_output():
    async def target(url):
        return {"result": "success"}

    async def target_check_output(url, result):
        assert url == "http://test.com"
        assert result == "success"

    tasks = [
        {
            "type": "e2e",
            "target": target,
            "target_input": {},
            "output": "task_output",
        },
        {
            "type": "e2e",
            "target": target_check_output,
            "target_input": "{{ task_output }}",
        },
    ]

    result = spintest(["http://test.com"], tasks)

    assert result is True


def test_target_with_output_and_more_input():
    async def target(url):
        return {"result": "success"}

    async def target_check_output(url, task_output, key):
        assert url == "http://test.com"
        assert task_output == "{'result': 'success'}"
        assert key == "extra_value"

    tasks = [
        {
            "type": "e2e",
            "target": target,
            "target_input": {},
            "output": "task_output",
        },
        {
            "type": "e2e",
            "target": target_check_output,
            "target_input": {
                "task_output": "{{ task_output }}",
                "key": "extra_value",
            },
        },
    ]

    result = spintest(["http://test.com"], tasks)

    assert result is True
