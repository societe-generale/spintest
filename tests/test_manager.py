import os
import json
import httpretty
import pytest
import shutil
from spintest import logger, spintest

logger.disabled = True

PATH = os.path.abspath(".")
REPORT_DIR = os.path.join(PATH, "report_status")


@pytest.fixture(scope="module", autouse=True)
def create_delete_report_dir():
    os.makedirs(REPORT_DIR, exist_ok=True)
    yield
    shutil.rmtree(REPORT_DIR)


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

    httpretty.disable()
    httpretty.reset()
