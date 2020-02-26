import os
import json
import httpretty
import pytest
import shutil
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
        spintest_report = json.load(f)

        result = []
        for iteration in range(len(spintest_report)):
            url = urlparse(spintest_report[iteration]["url"])
            if url.scheme in ["http", "https"]:
                result.append("True")
            else:
                result.append("False")
            for number in range(len(spintest_report[iteration]["reports"])):
                output = spintest_report[iteration]["reports"][number]["output"]
                if "**" in output["__token__"]:
                    result.append("True")
                else:
                    result.append("False")

        if "False" in result:
            return False
        else:
            return True


def test_manager_basic_generate_report():
    """Test spintest with generate report"""
    report_path = os.path.join(REPORT_DIR, "basic_report.json")
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
        generate_report=report_path,
    )

    assert True is result

    assert True is os.path.isfile(report_path)

    assert True is read_report(report_path)

    httpretty.disable()
    httpretty.reset()


def test_manager_basic_generate_report_with_token():
    """Test spintest with generate report"""
    report_path = os.path.join(REPORT_DIR, "basic_report_token.json")
    token = "ABC"
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
        generate_report=report_path,
        token=token,
    )

    assert True is result

    assert True is os.path.isfile(report_path)

    assert True is read_report(report_path)

    httpretty.disable()
    httpretty.reset()
