# Reusable Test Automation Framework - Agent Guide

A shareable blueprint for scaffolding a **Playwright + Python + pytest-bdd** UI/API test
automation framework using the **Page Object Model (POM)** and **BDD (Gherkin)**.

Hand this file to a teammate or an AI coding agent to generate the initial skeleton
framework from scratch. It contains no application-specific data, URLs, credentials, or
business logic - only the reusable architecture, conventions, and templates.

---

## 1. Objective

Build a maintainable, scalable end-to-end test framework that:

- Drives browsers via **Playwright (sync API)**.
- Expresses tests as human-readable **BDD scenarios** (`.feature` files) bound to Python
  step definitions with **pytest-bdd**.
- Isolates UI locators and actions inside **Page Object** classes extending a shared
  `BasePage`.
- Reads all environment/config from an **external, gitignored `config.ini`** (never hardcode).
- Produces rich reports (pytest-html, Allure, and a custom executive summary) with
  screenshots on failure and per-test logs.
- Supports multiple environments (e.g. `qa`, `uat`, `prod`) selected via a CLI flag.

---

## 2. Target Directory Structure

```
project_root/
├── conftest.py                     # Pytest fixtures + reporting hooks (framework core)
├── pytest.ini                      # Pytest config: markers, addopts, testpaths
├── requirements.txt                # Python dependencies
├── package.json                    # Optional: JS Playwright dep for tooling/codegen
├── .env                            # Optional local env vars (gitignored)
├── .gitignore
│
├── configuration/
│   ├── __init__.py
│   ├── config.ini                  # REAL values - gitignored, never committed
│   ├── config.ini.example          # Template with placeholders - committed
│   └── global_directories.py       # Centralized path constants
│
├── pageobjects/
│   ├── __init__.py
│   ├── base_page.py                # Reusable Playwright action wrappers
│   ├── login_page.py               # Example page object (login flow)
│   └── <feature>_page.py           # One page object per screen/module
│
├── tests/
│   ├── __init__.py
│   ├── features/                   # Gherkin .feature files
│   │   └── <feature>.feature
│   ├── step_defs/                  # pytest-bdd step definitions
│   │   ├── __init__.py
│   │   ├── common_library.py       # Shared/background steps (login, navigation)
│   │   └── test_<feature>.py       # @scenario bindings + when/then steps
│   └── test_documents/             # Static test data files (optional)
│
├── utilities/
│   ├── __init__.py
│   ├── read_properties.py          # Config reader (env-aware)
│   ├── custom_logger.py            # Singleton logger, per-run log files
│   ├── common_utilities.py         # Small shared helpers
│   └── report_generator.py         # Custom HTML report builder (optional)
│
├── reports/                        # Generated: html, allure-results, logs
└── screenshots/                    # Generated: failure screenshots
```

> **Convention:** every Python package directory contains an empty `__init__.py`.

---

## 3. Dependencies

Create `requirements.txt` with the core stack (pin versions in real projects):

```
# --- Core test stack ---
playwright
pytest
pytest-bdd
pytest-playwright
pytest-xdist          # parallel execution (-n auto)
pytest-html           # self-contained HTML report
pytest-metadata
allure-pytest         # Allure results
pytest-base-url

# --- Config / data / utils ---
requests
pandas                # optional: data-driven / Excel export
openpyxl              # optional: .xlsx read
xlsxwriter            # optional: .xlsx write
styleframe            # optional: styled Excel export
python-dateutil
pytz
```

`package.json` (optional, only if you want the JS Playwright tooling / `codegen`):

```json
{
  "dependencies": {
    "@playwright/test": "^1.59.1"
  }
}
```

**Setup commands:**

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Unix: source .venv/bin/activate
pip install -r requirements.txt
playwright install            # download browser binaries
```

---

## 4. Configuration Layer (externalized, never hardcode secrets)

### 4.1 `configuration/config.ini.example` (committed template)

Use placeholder values only. Real `config.ini` is a copy of this, filled locally, and
**gitignored**.

```ini
# Copy this file to config.ini and fill in real values locally.
# config.ini is gitignored and must never be committed (contains secrets).
[application details QA]
base_url = https://<your-app-host>/
username = <your-username>
password = <your-password>
browser = chrome
channel = chrome
headless = false
slow_motion = 500
post_login_wait_ms = 25000

[application details UAT]
base_url = https://<your-uat-host>/
username = <your-username>
password = <your-password>
browser = chrome
```

### 4.2 `configuration/global_directories.py`

```python
import os

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_SET_PATH = os.path.join(ROOT_DIR, "dataset")
```

### 4.3 `utilities/read_properties.py` (env-aware config reader)

```python
import configparser
import os

current_file_path = os.path.abspath(__file__)
base_directory = os.path.dirname(os.path.dirname(current_file_path))

configuration = configparser.RawConfigParser()
configuration.read(os.path.join(base_directory, "configuration", "config.ini"))


class Read_Configurations:
    configuration = configuration
    _env_mapping = {
        "qa": "application details QA",
        "uat": "application details UAT",
        # "prod": "application details PROD",
    }
    _env_section = None

    @classmethod
    def initialize(cls, env: str):
        cls._env_section = cls._env_mapping.get(env.lower())
        if not cls._env_section:
            raise ValueError(f"Unknown environment: {env}")

    @classmethod
    def get_value(cls, key: str, env: str = None) -> str:
        if cls._env_section is None:
            raise RuntimeError("Environment not initialized. Call initialize(env) first.")
        section = cls._env_mapping.get(env.lower(), cls._env_section) if env else cls._env_section
        return cls.configuration.get(section, key)

    @classmethod
    def get_browser_configurations(cls) -> dict:
        return {
            "headless": cls.configuration.getboolean(cls._env_section, "headless"),
            "channel": cls.configuration.get(cls._env_section, "channel"),
            "slow_mo": cls.configuration.getint(cls._env_section, "slow_motion"),
        }
```

---

## 5. Logging Utility (`utilities/custom_logger.py`)

Singleton logger that writes one timestamped log file per run under `reports/logs/`.

```python
import logging
import os
from datetime import datetime
from utilities.common_utilities import get_current_test_method_name


class LogGen:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if LogGen._initialized:
            return
        LogGen._initialized = True

        test_name = get_current_test_method_name()
        self.logger = logging.getLogger("FrameworkLogger")
        self.logger.setLevel(logging.DEBUG)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(base_dir, "reports", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = f"{log_dir}/{test_name}_{timestamp}.log"

        if not any(isinstance(h, logging.FileHandler) for h in self.logger.handlers):
            fh = logging.FileHandler(log_file)
            fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
            self.logger.addHandler(fh)

    def log_step(self, message, level="info", **kwargs):
        extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
        getattr(self.logger, level.lower(), self.logger.info)(f"{message} {extra}")
```

`utilities/common_utilities.py`:

```python
import inspect


def get_current_test_method_name():
    for frame_info in reversed(inspect.stack()):
        if frame_info.function.startswith("test_"):
            return frame_info.function
    return "Unknown"
```

---

## 6. Base Page (`pageobjects/base_page.py`)

Wrap common Playwright interactions so page objects stay concise and consistent.

```python
class BasePage:
    def __init__(self, page):
        self.page = page

    # --- Waits ---
    def wait_for_element_visible(self, selector):
        self.page.wait_for_selector(selector, state="visible")

    def wait_for_element_invisibility(self, selector):
        self.page.wait_for_selector(selector, state="hidden")

    def wait_for_page_load(self):
        self.page.wait_for_load_state("load")

    # --- Actions ---
    def enter_text(self, locator, value):
        self.page.locator(locator).fill(value)

    def clear_text(self, locator):
        self.page.fill(locator, "")

    def element_click(self, locator):
        self.page.locator(locator).click()

    def select_dropdown_with_value(self, locator, value):
        self.page.locator(locator).select_option(value=value)

    def mouse_hover(self, selector):
        self.page.hover(selector)

    # --- Reads / assertions ---
    def get_text(self, locator):
        return self.page.locator(locator).inner_text()

    def is_checked(self, locator):
        return self.page.locator(locator).is_checked()

    def validate_element_text(self, selector, expected_text):
        return self.page.text_content(selector) == expected_text

    def verify_element_enabled(self, selector):
        return self.page.is_enabled(selector)

    # --- Navigation ---
    def navigate_to_url(self, url):
        self.page.goto(url)

    def refresh_page(self):
        self.page.reload()
```

### Example page object (`pageobjects/login_page.py`)

```python
from pageobjects.base_page import BasePage


class LoginPage(BasePage):
    USERNAME_INPUT = "#username"
    PASSWORD_INPUT = "#password"
    SUBMIT_BUTTON = "button[type='submit']"

    def login_with_credentials(self, username, password):
        self.enter_text(self.USERNAME_INPUT, username)
        self.enter_text(self.PASSWORD_INPUT, password)
        self.element_click(self.SUBMIT_BUTTON)
        self.wait_for_page_load()
```

---

## 7. Pytest Fixtures & Reporting (`conftest.py`)

The framework core. Responsibilities:

1. `pytest_addoption` - add `--env` CLI flag (default `qa`).
2. `launch_browser` (session scope) - launch chrome/edge/firefox/webkit from config.
3. `get_context` / `get_page` (function scope) - fresh context/page per test.
4. `authenticated_page` (module scope) - **login once, reuse session** across a module.
5. `pytest_bdd_apply_tag` - map Gherkin tags to pytest markers.
6. `pytest_runtest_makereport` - capture screenshot on failure, attach logs/trace/video.
7. `pytest_terminal_summary` - build custom executive HTML summary + Allure report.

```python
import logging
import pytest
from datetime import datetime
from pathlib import Path
from playwright.sync_api import Playwright
from utilities.read_properties import Read_Configurations
from utilities.custom_logger import LogGen

logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="qa",
                     help="Test environment (qa, uat, prod)")


def pytest_bdd_apply_tag(tag, function):
    return getattr(pytest.mark, tag, lambda x: x)(function)


@pytest.fixture(scope="session")
def launch_browser(playwright: Playwright, request):
    env = request.config.getoption("--env").lower()
    Read_Configurations.initialize(env)
    browser_type = Read_Configurations.get_value("browser").lower()
    launch_args = {"headless": False, "args": ["--start-maximized"]}

    if browser_type == "edge":
        browser = playwright.chromium.launch(channel="msedge", **launch_args)
    elif browser_type == "chrome":
        browser = playwright.chromium.launch(channel="chrome", **launch_args)
    elif browser_type == "firefox":
        browser = playwright.firefox.launch(headless=False)
    elif browser_type == "webkit":
        browser = playwright.webkit.launch(headless=False)
    else:
        raise ValueError(f"Unsupported browser type: {browser_type}")

    yield browser
    browser.close()


@pytest.fixture()
def get_context(launch_browser):
    context = launch_browser.new_context(no_viewport=True)
    yield context
    context.close()


@pytest.fixture()
def get_page(get_context):
    page = get_context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="module")
def authenticated_page(launch_browser, request):
    """Login once per module and reuse the authenticated session."""
    from pageobjects.login_page import LoginPage

    context = launch_browser.new_context(no_viewport=True)
    page = context.new_page()

    env = request.config.getoption("--env").lower()
    Read_Configurations.initialize(env)
    base_url = Read_Configurations.get_value("base_url")
    username = Read_Configurations.get_value("username")
    password = Read_Configurations.get_value("password")

    page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
    LoginPage(page).login_with_credentials(username, password)

    yield {"page": page, "authenticated": True}

    page.close()
    context.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when == "call" and report.outcome == "failed":
        page = None
        if "authenticated_page" in item.funcargs:
            page = item.funcargs["authenticated_page"]["page"]
        elif "get_page" in item.funcargs:
            page = item.funcargs["get_page"]
        if page:
            shot_dir = Path(item.config.rootpath) / "screenshots"
            shot_dir.mkdir(parents=True, exist_ok=True)
            name = item.nodeid.replace("::", "_").replace("/", "_").replace("\\", "_")
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            page.screenshot(path=str(shot_dir / f"{name}_{ts}.png"), full_page=True)
```

> **Fixture scope tip:** use function-scoped `get_page` for isolated tests; use the
> module-scoped `authenticated_page` when many scenarios share one login to save time.

---

## 8. Pytest Configuration (`pytest.ini`)

```ini
[pytest]
addopts = -vs -rf --alluredir=reports/allure-results
testpaths = tests
python_files = test_*.py

markers =
    smoke: Smoke suite
    regression: Regression suite
    P1: Priority 1 tests
    P2: Priority 2 tests
    P3: Priority 3 tests
    login: Login/authentication tests
    navigation: Navigation tests
    <module>: <describe the module here>

[pytest-html-reporter]
output = reports/pytest_html_report.html
open = False
showEnvironment = True
showSummary = True
```

> Register a marker for every Gherkin tag you use so `pytest_bdd_apply_tag` can map them
> without warnings. Keep marker names generic and meaningful (module, priority, suite).

---

## 9. BDD Layer

### 9.1 Feature file (`tests/features/login.feature`)

```gherkin
@smoke @login @P1
Feature: Application Login
  As an authorized user
  I want to log in to the application
  So that I can access protected features

  Background:
    Given I am on the login page

  @P1
  Scenario: Successful login with valid credentials
    When I enter valid username and password
    And I click the login button
    Then I should land on the home page

  @P2
  Scenario: Login fails with invalid credentials
    When I enter an invalid username and password
    And I click the login button
    Then I should see an authentication error message
```

### 9.2 Step definitions (`tests/step_defs/test_login.py`)

```python
import logging
import pytest
from playwright.sync_api import Page
from pytest_bdd import scenario, given, when, then

from pageobjects.login_page import LoginPage
from utilities.read_properties import Read_Configurations

logger = logging.getLogger(__name__)


@pytest.fixture()
def login_page(get_page: Page) -> LoginPage:
    return LoginPage(get_page)


@scenario("../features/login.feature", "Successful login with valid credentials")
def test_successful_login(get_page, login_page):
    pass


@scenario("../features/login.feature", "Login fails with invalid credentials")
def test_failed_login(get_page, login_page):
    pass


@given("I am on the login page")
def open_login_page(get_page: Page):
    base_url = Read_Configurations.get_value("base_url")
    get_page.goto(base_url, wait_until="domcontentloaded")


@when("I enter valid username and password")
def enter_valid_credentials(login_page: LoginPage):
    login_page.enter_text(login_page.USERNAME_INPUT, Read_Configurations.get_value("username"))
    login_page.enter_text(login_page.PASSWORD_INPUT, Read_Configurations.get_value("password"))


@when("I enter an invalid username and password")
def enter_invalid_credentials(login_page: LoginPage):
    login_page.enter_text(login_page.USERNAME_INPUT, "invalid_user")
    login_page.enter_text(login_page.PASSWORD_INPUT, "wrong_password")


@when("I click the login button")
def click_login(login_page: LoginPage):
    login_page.element_click(login_page.SUBMIT_BUTTON)


@then("I should land on the home page")
def verify_home_page(login_page: LoginPage):
    assert "home" in login_page.page.url.lower()


@then("I should see an authentication error message")
def verify_error(login_page: LoginPage):
    assert login_page.page.locator(".error-message").is_visible()
```

### 9.3 Shared/common steps (`tests/step_defs/common_library.py`)

Put reusable `Background` steps (login, navigation, popups) here and import them into
feature step files with:

```python
from tests.step_defs.common_library import *  # noqa: F401,F403
```

---

## 10. Running Tests

```bash
# Run everything on the default (qa) environment
pytest

# Choose an environment
pytest --env uat

# Run by marker (tag)
pytest -m "smoke and P1"
pytest -m "login"

# Run a single feature's step file
pytest tests/step_defs/test_login.py

# Parallel execution
pytest -n auto

# Generate + open Allure report (requires Allure CLI installed)
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

Reports produced:
- `reports/pytest_html_report.html` - self-contained HTML.
- `reports/allure-results/` - Allure raw results.
- `reports/logs/` - per-run log files.
- `screenshots/` - failure screenshots.

---

## 11. `.gitignore` essentials

```gitignore
# Secrets / local config
configuration/config.ini
.env

# Python
__pycache__/
*.pyc
.venv/
.pytest_cache/

# Generated artifacts
reports/
screenshots/
node_modules/
```

---

## 12. Conventions & Best Practices

- **Never hardcode** URLs, usernames, passwords, API keys, or tokens. Read them from
  `config.ini` via `Read_Configurations`. Only `config.ini.example` (placeholders) is committed.
- **One page object per screen/module**, all extending `BasePage`. Keep locators as class
  constants at the top of each page object.
- **Keep step definitions thin**: they orchestrate; the page objects do the work.
- **Feature files describe behavior**, not implementation. No CSS selectors in Gherkin.
- **Register every Gherkin tag** as a marker in `pytest.ini`.
- **Prefer role/text-based Playwright locators** (`get_by_role`, `get_by_text`) for
  resilience; fall back to stable `data-*` / `id` selectors.
- **Choose fixture scope deliberately**: function-scoped for isolation, module-scoped
  `authenticated_page` when sharing a login speeds up a suite.
- **Log meaningful steps** with the singleton logger and let failures auto-capture screenshots.

---

## 13. Agent Task Checklist (to scaffold the skeleton)

1. Create the directory tree in section 2 (with empty `__init__.py` files).
2. Write `requirements.txt` and `package.json`; create venv, install deps, run `playwright install`.
3. Add `configuration/config.ini.example`, `global_directories.py`; create local `config.ini` (gitignored).
4. Implement `utilities/`: `read_properties.py`, `custom_logger.py`, `common_utilities.py`.
5. Implement `pageobjects/base_page.py` and one example page object (`login_page.py`).
6. Implement `conftest.py` fixtures + reporting hooks.
7. Write `pytest.ini` with markers and addopts.
8. Add an example `features/login.feature` + `step_defs/test_login.py` + `common_library.py`.
9. Add `.gitignore`.
10. Run `pytest --env qa -m smoke` and confirm the report/log/screenshot pipeline works.
```
