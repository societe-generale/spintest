import pytest
import os


@pytest.fixture(scope="session", autouse=True)
def set_proxy():
    print("set proxy to empty value")
    os.environ["http_proxy"] = ""
    os.environ["https_proxy"] = ""
    os.environ["ftp_proxy"] = ""
