import os
import subprocess
import sys
import tempfile
import time
import urllib.request

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

PORT = 5099
BASE = "http://127.0.0.1:%d" % PORT
PORTAL = os.environ.get("PORTAL_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "portal"))
SCREENS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "screens")


@pytest.fixture(scope="session")
def server():
    folder = tempfile.mkdtemp(prefix="portal_test_")
    code = (
        "import sys; sys.path.insert(0, %r); from app import create_app; "
        "a = create_app({'DATABASE': %r}); "
        "a.users.create('admin', 'Администратор портала', 'Admin2026!', 'admin@konferencii.test', '+79000000000', 'admin'); "
        "a.run(host='127.0.0.1', port=%d)"
    ) % (os.path.abspath(PORTAL), os.path.join(folder, "test.db"), PORT)
    log = open(os.path.join(folder, "server.log"), "w", encoding="utf-8")
    proc = subprocess.Popen([sys.executable, "-c", code], stdout=log, stderr=log, cwd=os.path.abspath(PORTAL),
                            env=dict(os.environ, PYTHONUTF8="1"))
    for _ in range(60):
        try:
            urllib.request.urlopen(BASE + "/", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    yield BASE
    proc.terminate()


@pytest.fixture
def driver(server, request):
    options = Options()
    if not os.environ.get("HEADED"):
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--lang=ru")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    drv = webdriver.Chrome(options=options)
    drv.implicitly_wait(0)
    yield drv
    failed = getattr(request.node, "rep_call", None) is not None and request.node.rep_call.failed
    if failed:
        os.makedirs(SCREENS, exist_ok=True)
        drv.save_screenshot(os.path.join(SCREENS, request.node.name.replace("/", "_")[:80] + ".png"))
    drv.quit()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    setattr(item, "rep_" + outcome.get_result().when, outcome.get_result())
