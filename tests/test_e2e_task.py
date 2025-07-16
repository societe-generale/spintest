import pytest
from spintest.e2e_task import E2ETask
from unittest.mock import AsyncMock, patch

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
    assert task.ignore == valid_task["ignore"]
    assert task.response is None

def test_e2e_task_response_success(valid_task, url):
    task = E2ETask(url, valid_task)
    response = task._response("SUCCESS", "Task executed successfully.")
    assert response["status"] == "SUCCESS"
    assert response["message"] == "Task executed successfully."
    assert response["name"] == valid_task["name"]
    assert response["url"] == url

def test_e2e_task_response_failure(valid_task, url):
    task = E2ETask(url, valid_task)
    response = task._response("FAILURE", "Task failed.")
    assert response["status"] == "FAILURE"
    assert response["message"] == "Task failed."
    assert response["name"] == valid_task["name"]
    assert response["url"] == url

@pytest.mark.asyncio
async def test_e2e_task_run_success(valid_task, url):
    valid_task["target"].return_value = True
    with patch("spintest.validator.input_validator_e2e_task", return_value=valid_task):
        task = E2ETask(url, valid_task)
        response = await task.run()
        assert response["status"] == "SUCCESS"
        assert response["message"] == "Task executed successfully."
        assert response["duration_sec"] is not None

@pytest.mark.asyncio
async def test_e2e_task_run_failure_assertion(valid_task, url):
    valid_task["target"].side_effect = AssertionError("Test assertion error")
    with patch("spintest.validator.input_validator_e2e_task", return_value=valid_task):
        task = E2ETask(url, valid_task)
        response = await task.run()
        assert response["status"] == "FAILURE"
        assert "assertion error" in response["message"]

@pytest.mark.asyncio
async def test_e2e_task_run_failure_exception(valid_task, url):
    valid_task["target"].side_effect = Exception("Test exception")
    with patch("spintest.validator.input_validator_e2e_task", return_value=valid_task):
        task = E2ETask(url, valid_task)
        response = await task.run()
        assert response["status"] == "ERROR"
        assert "encountered an error" in response["message"]

@pytest.mark.asyncio
async def test_e2e_task_initialization_invalid_task(invalid_task, url):
    invalid_task["target"] = None  # Ensure target is invalid
    with pytest.raises(ValueError, match="E2E task must have a callable 'target'."):
        task = E2ETask(url, invalid_task)
        response = await task.run()
        assert response["status"] == "FAILURE"
        assert "must follow the schema" in response["message"]
