import os
import json
import httpretty
import pytest
import shutil
import time
from spintest import logger, spintest
from urllib.parse import urlparse

logger.disabled = True

PATH = os.path.abspath(".")
REPORT_DIR = os.path.join(PATH, "report_status")


@pytest.fixture(scope="module", autouse=True)
def create_delete_report_dir():
    os.makedirs(REPORT_DIR, exist_ok=True)
    yield
    shutil.rmtree(REPORT_DIR)


def read_report(report_path):
    with open(report_path, "r") as f:
        return json.load(f)


def validate_report(report_path):
    spintest_reports = read_report(report_path)

    for suite_report in spintest_reports:
        url = urlparse(suite_report["url"])
        if url.scheme not in ("http", "https"):
            return False
        for task_report in suite_report["reports"]:
            output = task_report["output"]
            if "__token__" in output and not \
                    all(char == "*" for char in output["__token__"]):
                return False

    return True


@httpretty.activate
def test_manager_basic_generate_report():
    """Test spintest with generate report"""
    report_path = os.path.join(REPORT_DIR, "basic_report.json")
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
        generate_report=report_path,
    )

    assert True is result

    assert True is os.path.isfile(report_path)

    assert True is validate_report(report_path)


@httpretty.activate
def test_manager_basic_generate_report_with_token():
    """Test spintest with generate report"""
    report_path = os.path.join(REPORT_DIR, "basic_report_token.json")
    token = "ABC"
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
        generate_report=report_path,
        token=token,
    )

    assert True is result

    assert True is os.path.isfile(report_path)

    assert True is validate_report(report_path)


def httpretty_body_that_waits_and_returns(duration, return_value):
    def inner(_req, _uri, _headers):
        time.sleep(duration)
        return return_value
    return inner


@httpretty.activate
def test_manager_reports_durations():
    """Test spintest reports per-task & total duration"""

    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test",
        body=httpretty_body_that_waits_and_returns(0.1, [200, {}, "Hello!"])
    )

    report_path = os.path.join(REPORT_DIR, "duration_report.json")
    spintest(
        ["http://test.com"],
        [{"method": "GET", "route": "/test"}] * 2,
        generate_report=report_path,
    )
    spintest_reports = read_report(report_path)

    first_task_report = spintest_reports[0]["reports"][0]
    assert first_task_report["duration_sec"] == pytest.approx(0.1, abs=0.02)

    total_duration = spintest_reports[0]["total_duration_sec"]
    assert total_duration == pytest.approx(0.2, abs=0.02)


@httpretty.activate
def test_manager_reports_duration_including_failure():
    """Test spintest reports task & total durations, including failure"""

    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/long_failed",
        body=httpretty_body_that_waits_and_returns(0.5, None)
    )

    report_path = os.path.join(REPORT_DIR, "duration_report_with_failure.json")
    spintest(
        ["http://test.com"],
        [
            # Fails but does not retry and is ignored
            {"method": "GET", "route": "/long_failed", "delay": 0, "ignore": True},
        ],
        generate_report=report_path,
    )
    spintest_reports = read_report(report_path)

    first_task_report = spintest_reports[0]["reports"][0]
    assert first_task_report["duration_sec"] == pytest.approx(0.5, abs=0.02)

    total_duration = spintest_reports[0]["total_duration_sec"]
    assert total_duration == pytest.approx(0.5, abs=0.02)


@httpretty.activate
def test_manager_reports_duration_including_delays_and_retries():
    """Test spintest reports task & total durations, including delays & retries"""

    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/long_500",
        body=httpretty_body_that_waits_and_returns(0.1, [500, {}, "Hello!"])
    )

    report_path = os.path.join(REPORT_DIR, "duration_report_with_delay_and_retry.json")
    spintest(
        ["http://test.com"],
        [
            # Errors and retries once with 1sec delay
            {"method": "GET", "route": "/long_500", "retry": 1, "delay": 1},
        ],
        generate_report=report_path,
    )
    spintest_reports = read_report(report_path)

    first_task_report = spintest_reports[0]["reports"][0]
    assert first_task_report["duration_sec"] == pytest.approx(1.2, abs=0.02)

    total_duration = spintest_reports[0]["total_duration_sec"]
    assert total_duration == pytest.approx(1.2, abs=0.02)


@httpretty.activate
def test_manager_reports_total_duration():
    """Test spintest reports proper total duration"""

    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test_1",
        body=httpretty_body_that_waits_and_returns(0.1, [200, {}, "Hello!"])
    )
    httpretty.register_uri(
        httpretty.GET,
        "http://test.com/test_2",
        body=httpretty_body_that_waits_and_returns(0.4, [200, {}, "World!"])
    )

    report_path = os.path.join(REPORT_DIR, "duration_report_with_delay_and_retry.json")
    spintest(
        ["http://test.com"],
        [
            {"method": "GET", "route": "/test_1"},
            {"method": "GET", "route": "/test_2"},
        ],
        generate_report=report_path,
    )
    spintest_reports = read_report(report_path)

    total_duration = spintest_reports[0]["total_duration_sec"]
    assert total_duration == pytest.approx(0.5, abs=0.04)
