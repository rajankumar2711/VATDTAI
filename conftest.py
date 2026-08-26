import tempfile
import json
from styleframe import StyleFrame, Styler
import pandas as pd
from contextlib import contextmanager
import pytest
from playwright.sync_api import Playwright, Page, APIRequestContext, sync_playwright
from utilities.read_properties import Read_Configurations
from typing import Generator
from playwright.sync_api import Browser, Page, BrowserContext
from datetime import datetime
from pathlib import Path
import logging
import os
import subprocess
import shutil
from collections import defaultdict
from html import escape as html_escape
from utilities.Custom_logger import LogGen

# Configure logger for conftest
logger = logging.getLogger(__name__)


def pytest_bdd_apply_tag(tag, function):
    return getattr(pytest.mark, tag, lambda x: x)(function)


def _step_logger():
    """Return the shared scenario logger if initialised, else this module's logger.
    Using the shared LogGen instance ensures step logs land in the same file that the
    pytest-html 'Scenario Logs' attachment reads from."""
    global _singleton_logger
    if _singleton_logger is not None:
        return _singleton_logger.logger
    return logger


# ---------------------------------------------------------------------------
# pytest-bdd step lifecycle hooks: automatically log EVERY step (start / pass /
# fail) so reports capture a complete, accurate execution trail without relying
# on each step definition to log individually.
# ---------------------------------------------------------------------------
def pytest_bdd_before_scenario(request, feature, scenario):
    _step_logger().info(
        f"=== [SCENARIO START] {scenario.name} "
        f"(feature: {Path(feature.filename).name}) ==="
    )


def pytest_bdd_before_step(request, feature, scenario, step, step_func):
    _step_logger().info(f"[STEP ->] {step.keyword} {step.name}")


def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args):
    _step_logger().info(f"[STEP PASS] {step.keyword} {step.name}")


def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    _step_logger().error(
        f"[STEP FAIL] {step.keyword} {step.name} -> {type(exception).__name__}: {exception}"
    )


def pytest_bdd_after_scenario(request, feature, scenario):
    _step_logger().info(f"=== [SCENARIO END] {scenario.name} ===")

# This method will launch the browser
# It will take the parameter as browser type and other details from configuration
@pytest.fixture(scope="session")
def launch_browser(playwright: Playwright, request):
    """Launch browser once per session with proper cleanup"""
    env = request.config.getoption("--env").lower()
    Read_Configurations.initialize(env)
    browser_type = Read_Configurations.get_value("browser")
    
    # Browser launch arguments for maximization
    launch_args = {
        "headless": False,
        "args": ['--start-maximized']  # Maximize window on launch
    }
    
    if browser_type.lower() == "edge":
        browser = playwright.chromium.launch(channel="msedge", **launch_args)
    elif browser_type.lower() == "chrome":
        browser = playwright.chromium.launch(channel="chrome", **launch_args)
    elif browser_type.lower() == "chromium":
        browser = playwright.chromium.launch(**launch_args)
    elif browser_type.lower() == "firefox":
        # Firefox uses different approach
        browser = playwright.firefox.launch(headless=False, args=['--kiosk'])
    elif browser_type.lower() == "webkit":
        browser = playwright.webkit.launch(headless=False)
    else:
        raise ValueError(f"Unsupported browser type: {browser_type}")
    
    yield browser
    # Cleanup: Close browser after all tests
    browser.close()

def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default="qa",  # or "uat"
        help="Test environment (uat or qa)",
    )
    parser.addoption(
        "--stakeholder-summary",
        action="store",
        default=None,
        help="Path to stakeholder executive HTML summary report",
    )

@pytest.fixture(scope="session")
def config(request):
    env = request.config.getoption("--env").lower()
    Read_Configurations.initialize(env)
    return {
        #"TestAPIURL1": Read_Configurations.get_TestAPIURL1(),
        "TestAPIURL1": Read_Configurations.get_value("TestAPIURL1"),
        #"TestApplicationUserName2": Read_Configurations.get_TestApplicationUserName2(),
        "TestApplicationUserName2": Read_Configurations.get_value("TestApplicationUserName2"),
        #"TestApplicationPassword2": Read_Configurations.get_TestApplicationPassword2(),
        "TestApplicationPassword2": Read_Configurations.get_value("TestApplicationPassword2"),
        #"TokenBaseAPI": Read_Configurations.get_TokenBaseAPI(),
        "TokenBaseAPI": Read_Configurations.get_value("TokenBaseAPI"),
        #"baseUrl_UAT": Read_Configurations.get_baseUrl_UAT(),
        "baseUrl_UAT": Read_Configurations.get_value("baseUrl_UAT"),
        #"UploadPDF": Read_Configurations.get_UploadPDF(),
        "UploadPDF": Read_Configurations.get_value("UploadPDF"),
        #"TestDataRepository": Read_Configurations.get_TestDataRepository()
        "TestDataRepository": Read_Configurations.get_value("TestDataRepository"),
        "AppId": Read_Configurations.get_value("App_Id")
    }


# Browser context with maximized window (function-scoped for non-VAT tests)
@pytest.fixture()
def get_context(launch_browser):
    """Create browser context with maximized window"""
    context = launch_browser.new_context(
        no_viewport=True  # Use full browser window size
    )
    yield context
    context.close()


# Page fixture for general tests (function-scoped)
@pytest.fixture()
def get_page(get_context):
    """Create new page for each test"""
    page = get_context.new_page()
    yield page
    page.close()


# Session-scoped authenticated VAT DTAI session (Option B: login once for the whole run).
# Performs login -> client selection -> Consumption Tax/DTAI navigation -> OK popup ONCE.
# Modules opt in by overriding `get_page` to return vat_session["page"] (see test_data_ingestion.py).
@pytest.fixture(scope="session")
def vat_session(launch_browser, request):
    """One-time authenticated session shared across all opted-in scenarios."""
    from tests.step_defs.VAT_Common_Library import (
        perform_login,
        perform_client_selection,
        perform_dtai_navigation,
        dismiss_application_popup,
    )

    env = request.config.getoption("--env").lower()
    Read_Configurations.initialize(env)

    context = launch_browser.new_context(no_viewport=True, accept_downloads=True)
    page = context.new_page()

    logger.info("=== [vat_session] One-time login + navigation to DTAI dashboard ===")
    launch_page = perform_login(page, role="Admin")
    perform_client_selection(page, launch_page, "Client Belgium")
    perform_dtai_navigation(page, launch_page)
    dismiss_application_popup(page)
    logger.info(f"=== [vat_session] Ready. Current URL: {page.url} ===")

    session = {"page": page, "launch_page": launch_page}
    yield session

    logger.info("=== [vat_session] Closing shared session ===")
    try:
        page.close()
        context.close()
    except Exception:
        pass


# Module-scoped authenticated VAT DTAI fixture
@pytest.fixture(scope="module")
def authenticated_vat_page(launch_browser, request):
    """
    Module-scoped fixture: Login once per test module, reuse for all tests.
    Maximized browser window with authenticated session.
    """
    from pageobjects.launch_app_page import LaunchAppPage
    
    # Create context with no viewport restriction (use full browser window)
    context = launch_browser.new_context(
        no_viewport=True  # Allow browser window to determine size
    )
    
    page = context.new_page()
    
    # Get VAT DTAI config
    env = request.config.getoption("--env").lower()
    Read_Configurations.initialize(env)
    vat_url = Read_Configurations.get_value("VAT_DTAI_URL")
    vat_username = Read_Configurations.get_value("VAT_DTAI_USERNAME")
    vat_password = Read_Configurations.get_value("VAT_DTAI_PASSWORD")
    
    # Navigate to VAT DTAI URL first
    logger.info("\n=== Module Setup: Navigating to VAT DTAI URL ===")
    logger.info(f"URL: {vat_url}")
    page.goto(vat_url, wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(2000)
    
    # Perform login once
    logger.info("\n=== Module Setup: Performing One-Time Login ===")
    launch_page = LaunchAppPage(page)
    launch_page.login_with_credentials(vat_username, vat_password)
    logger.info(f"Login complete. Current URL: {page.url}")
    
    # Wait for post-login processing
    page.wait_for_timeout(25000)
    
    # Select workspace and continue
    launch_page.select_workspace_and_continue("Client Belgium")
    print(f"Workspace selected. Current URL: {page.url}")
    
    # Wait for home page
    page.wait_for_timeout(5000)
    
    # Navigate to DTAI dashboard
    print("\n=== Navigating to DTAI VAT Application ===")
    launch_page.navigate_to_dtai_vat_app()
    page.wait_for_timeout(3000)
    print(f"DTAI app loaded. Current URL: {page.url}")
    
    # Navigate to User Management module
    print("\n=== Navigating to User Management Module ===")
    user_mgmt_tab = page.locator("role=tab[name='User Management' i]")
    if user_mgmt_tab.count() > 0:
        user_mgmt_tab.click()
        page.wait_for_timeout(2000)
        print(f"User Management module loaded. Current URL: {page.url}")
    else:
        print("WARNING: User Management tab not found!")
    
    print("=== Module Setup Complete: Ready for Tests ===")
    
    # Store launch_page for tests to use
    vat_session_data = {
        "page": page,
        "launch_page": launch_page,
        "authenticated": True,
        "home_url": page.url
    }
    
    yield vat_session_data
    
    # Cleanup after all tests in module complete
    print("\n=== Module Teardown: Closing Session ===")
    page.close()
    context.close()


# VAT DTAI Test Context - Shared state across navigation steps (function-scoped)
@pytest.fixture()
def vat_context():
    """
    Function-scoped context for storing test-specific state.
    Used by tests that need per-test isolation.
    For module-scoped authenticated session, use authenticated_vat_page fixture.
    """
    return {
        "launch_page": None,
        "role": "Admin",
        "workspace": "Client Belgium",
        "test_data": {},
    }


# Module-scoped VAT context for shared session
@pytest.fixture(scope="module")
def vat_module_context():
    """
    Module-scoped context for storing shared state across all tests in module.
    Used with authenticated_vat_page for tests sharing authenticated session.
    """
    return {
        "launch_page": None,
        "role": "Admin",
        "workspace": "Client Belgium",
        "current_module": None,
        "tests_executed": [],
    }


# API Request Context
@pytest.fixture(scope="session")
def api_request_context(playwright: Playwright) -> Generator[APIRequestContext, None, None]:
    request_context = playwright.request.new_context(
        base_url=Read_Configurations.get_value("baseUrl_UAT"),
        ignore_https_errors=True
    )
    yield request_context
    request_context.dispose()



# Singleton logger instance for the whole test session
_singleton_logger = None
_stakeholder_results = []

@pytest.fixture(autouse=True)
def scenario_logger(request):
    global _singleton_logger
    if _singleton_logger is None:
        _singleton_logger = LogGen()
    logger_instance = _singleton_logger
    log_file = None
    for handler in logger_instance.logger.handlers:
        if isinstance(handler, logging.FileHandler):
            log_file = handler.baseFilename
            break
    yield
    # Attach log file to pytest-html report using the extra mechanism
    if log_file and hasattr(request.node, 'rep_call'):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            extra = getattr(request.node, 'extra', [])
            from pytest_html import extras
            extra.append(extras.text(log_content, 'Scenario Logs'))
            request.node.extra = extra
        except Exception:
            pass
        
def _to_file_url(path_value):
    if not path_value:
        return None
    normalized = Path(path_value).resolve().as_posix()
    return f"file:///{normalized}"


def _report_output_path(config, timestamp=None):
    output = config.getoption("stakeholder_summary")
    if output:
        return Path(output)
    
    # Add timestamp to stakeholder summary filename
    if timestamp:
        return Path(config.rootpath) / "reports" / f"stakeholder_executive_summary_{timestamp}.html"
    return Path(config.rootpath) / "reports" / "stakeholder_executive_summary.html"


def _build_executive_html(results, total_duration, detailed_report, allure_results):
    total = len(results)
    passed = sum(1 for r in results if r["outcome"] == "passed")
    failed = sum(1 for r in results if r["outcome"] == "failed")
    skipped = sum(1 for r in results if r["outcome"] == "skipped")

    module_map = defaultdict(lambda: {"passed": 0, "failed": 0, "skipped": 0, "duration": 0.0})
    for row in results:
        module_map[row["module"]][row["outcome"]] += 1
        module_map[row["module"]]["duration"] += row["duration"]

    module_rows = []
    for module_name, stats in sorted(module_map.items(), key=lambda x: (x[1]["failed"], x[0]), reverse=True):
        module_rows.append(
            f"<tr><td>{html_escape(module_name)}</td><td>{stats['passed']}</td><td>{stats['failed']}</td>"
            f"<td>{stats['skipped']}</td><td>{stats['duration']:.2f}s</td></tr>"
        )
    module_rows_html = "".join(module_rows) if module_rows else "<tr><td colspan='5'>No module data available</td></tr>"

    test_rows = []
    for row in results:
        trace_link = f"<a href='{html_escape(row['trace_url'])}' target='_blank'>trace</a>" if row.get("trace_url") else "-"
        video_link = f"<a href='{html_escape(row['video_url'])}' target='_blank'>video</a>" if row.get("video_url") else "-"
        test_rows.append(
            f"<tr><td>{html_escape(row['nodeid'])}</td><td>{row['outcome']}</td><td>{row['duration']:.2f}s</td>"
            f"<td>{trace_link}</td><td>{video_link}</td></tr>"
        )
    test_rows_html = "".join(test_rows) if test_rows else "<tr><td colspan='5'>No test data available</td></tr>"

    detailed_link = f"<a href='{html_escape(detailed_report)}' target='_blank'>Open detailed HTML report</a>" if detailed_report else "Not provided"
    allure_link = f"<a href='{html_escape(allure_results)}' target='_blank'>Open Allure results folder</a>" if allure_results else "Not provided"

    return f"""<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <title>Stakeholder Executive Test Summary</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; margin: 20px; color: #1e1e1e; background: #f6f8fb; }}
    .wrap {{ max-width: 1280px; margin: 0 auto; }}
    h1 {{ margin: 0 0 6px; }}
    .meta {{ color: #606a7a; margin-bottom: 18px; }}
    .cards {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 18px; }}
    .card {{ background: #fff; border-radius: 10px; padding: 14px; box-shadow: 0 2px 10px rgba(0,0,0,.06); }}
    .label {{ color: #6b7280; font-size: 12px; text-transform: uppercase; letter-spacing: .4px; }}
    .value {{ font-size: 28px; font-weight: 700; margin-top: 4px; }}
    .ok {{ color: #0f7b0f; }} .bad {{ color: #c62828; }} .warn {{ color: #9a6700; }}
    .panel {{ background: #fff; border-radius: 10px; padding: 14px; box-shadow: 0 2px 10px rgba(0,0,0,.06); margin-bottom: 14px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 8px; text-align: left; font-size: 13px; }}
    th {{ background: #f3f4f6; }}
    a {{ color: #0658d3; text-decoration: none; }}
  </style>
</head>
<body>
  <div class='wrap'>
    <h1>Stakeholder Executive Test Summary</h1>
    <div class='meta'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    <div class='cards'>
      <div class='card'><div class='label'>Total Tests</div><div class='value'>{total}</div></div>
      <div class='card'><div class='label'>Passed</div><div class='value ok'>{passed}</div></div>
      <div class='card'><div class='label'>Failed</div><div class='value bad'>{failed}</div></div>
      <div class='card'><div class='label'>Skipped</div><div class='value warn'>{skipped}</div></div>
      <div class='card'><div class='label'>Execution Time</div><div class='value'>{total_duration:.1f}s</div></div>
    </div>
    <div class='panel'><b>Detailed report:</b> {detailed_link}<br/><b>Allure results:</b> {allure_link}</div>
    <div class='panel'>
      <h3>Module-wise Results</h3>
      <table>
        <tr><th>Module</th><th>Passed</th><th>Failed</th><th>Skipped</th><th>Duration</th></tr>
        {module_rows_html}
      </table>
    </div>
    <div class='panel'>
      <h3>Test Case Details (with Trace/Video)</h3>
      <table>
        <tr><th>Test Case</th><th>Status</th><th>Duration</th><th>Trace</th><th>Video</th></tr>
        {test_rows_html}
      </table>
    </div>
  </div>
</body>
</html>"""


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
    global _singleton_logger, _stakeholder_results

    user_props = dict(getattr(item, "user_properties", []))
    trace_path = user_props.get("trace_path")
    video_path = user_props.get("video_path")
    trace_url = _to_file_url(trace_path)
    video_url = _to_file_url(video_path)

    extra = list(getattr(report, "extras", []))
    if report.when == "call":
        log_file = None
        if _singleton_logger is not None:
            logger_instance = _singleton_logger
            for handler in logger_instance.logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    log_file = handler.baseFilename
                    break

        if log_file:
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    log_content = f.read()
                from pytest_html import extras
                extra.append(extras.text(log_content, "Scenario Logs"))
            except Exception:
                pass

        try:
            from pytest_html import extras
            if trace_url:
                extra.append(extras.url(trace_url, name="Trace"))
            if video_url:
                extra.append(extras.url(video_url, name="Video"))
        except Exception:
            pass

        # Extract error message for failed tests
        error_message = None
        screenshot_url = None
        if report.outcome == "failed" and hasattr(report, "longrepr"):
            try:
                error_message = str(report.longrepr)
            except:
                error_message = "Error details not available"
            
            # Capture screenshot on failure
            try:
                # Try to get page from fixtures
                page = None
                if "authenticated_vat_page" in item.funcargs:
                    page = item.funcargs["authenticated_vat_page"]["page"]
                elif "get_page" in item.funcargs:
                    page = item.funcargs["get_page"]
                
                if page:
                    # Create screenshots directory
                    screenshot_dir = Path(item.config.rootpath) / "screenshots"
                    screenshot_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Generate screenshot filename
                    test_name = item.nodeid.replace("::", "_").replace("/", "_").replace("\\", "_")
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = screenshot_dir / f"{test_name}_{timestamp}.png"
                    
                    # Capture screenshot
                    page.screenshot(path=str(screenshot_path), full_page=True)
                    logger.info(f"Screenshot captured on failure: {screenshot_path}")
                    
                    # Convert to file URL
                    screenshot_url = _to_file_url(str(screenshot_path))
                    
                    # Add to HTML report extras
                    try:
                        from pytest_html import extras
                        extra.append(extras.url(screenshot_url, name="Screenshot on Failure"))
                    except:
                        pass
                        
            except Exception as e:
                logger.warning(f"Failed to capture screenshot: {str(e)}")
        
        _stakeholder_results.append(
            {
                "nodeid": item.nodeid,
                "module": item.nodeid.split("::")[0],
                "outcome": report.outcome,
                "duration": getattr(report, "duration", 0.0),
                "trace_url": trace_url,
                "video_url": video_url,
                "error_message": error_message,
                "test_name": item.name,
                "screenshot_url": screenshot_url,
            }
        )

    elif report.when == "teardown":
        for row in reversed(_stakeholder_results):
            if row["nodeid"] == item.nodeid:
                if trace_url:
                    row["trace_url"] = trace_url
                if video_url:
                    row["video_url"] = video_url
                break
        try:
            from pytest_html import extras
            if trace_url:
                extra.append(extras.url(trace_url, name="Trace"))
            if video_url:
                extra.append(extras.url(video_url, name="Video"))
        except Exception:
            pass

    report.extras = extra
    item.extra = extra


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not _stakeholder_results:
        return

    # Generate timestamp for this test run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate basic stakeholder summary
    output_path = _report_output_path(config, timestamp)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_duration = sum(r["duration"] for r in _stakeholder_results)
    detailed_html = getattr(config.option, "htmlpath", None)
    detailed_html_url = _to_file_url(detailed_html) if detailed_html else None
    
    # Get allure results and report directories with timestamp
    base_reports_dir = Path(__file__).resolve().parent / "reports"
    allure_source_dir = base_reports_dir / "allure-results"  # Original collection directory
    allure_results_dir = base_reports_dir / f"allure-results_{timestamp}"
    allure_report_dir = base_reports_dir / f"allure-report_{timestamp}"
    
    # Copy allure results to timestamped directory if they exist
    if allure_source_dir.exists() and any(allure_source_dir.iterdir()):
        try:
            shutil.copytree(allure_source_dir, allure_results_dir, dirs_exist_ok=True)
            terminalreporter.write_line(f"Allure results copied to: {allure_results_dir}")
        except Exception as e:
            logger.warning(f"Failed to copy allure results: {str(e)}")
            terminalreporter.write_line(f"Warning: Failed to copy allure results: {str(e)}")
    
    # Generate Allure HTML report if results exist and CLI is available
    allure_report_url = None
    if allure_results_dir.exists() and any(allure_results_dir.iterdir()):
        try:
            # Check if allure command is available
            allure_cmd = shutil.which("allure")
            if allure_cmd:
                # Generate Allure HTML report
                terminalreporter.write_line("Generating Allure HTML report...")
                subprocess.run(
                    [allure_cmd, "generate", str(allure_results_dir), "-o", str(allure_report_dir), "--clean"],
                    check=True,
                    capture_output=True,
                    text=True
                )
                allure_report_url = _to_file_url(str(allure_report_dir / "index.html"))
                terminalreporter.write_sep("=", f"Allure report: {allure_report_dir / 'index.html'}")
            else:
                terminalreporter.write_line(
                    "Warning: Allure CLI not found. Allure results collected but HTML report not generated."
                )
                terminalreporter.write_line(
                    "To install Allure CLI: https://docs.qameta.io/allure/#_installing_a_commandline"
                )
                terminalreporter.write_line(
                    f"Allure results saved in: {allure_results_dir}"
                )
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to generate Allure report: {e.stderr}")
            terminalreporter.write_line(f"Warning: Allure report generation failed: {e.stderr}")
        except Exception as e:
            logger.warning(f"Failed to generate Allure report: {str(e)}")
            terminalreporter.write_line(f"Warning: Allure report generation failed: {str(e)}")

    html_content = _build_executive_html(
        _stakeholder_results,
        total_duration,
        detailed_html_url,
        allure_report_url,
    )
    output_path.write_text(html_content, encoding="utf-8")
    terminalreporter.write_sep("=", f"Stakeholder executive summary: {output_path}")
    
    # Generate comprehensive enterprise report
    try:
        from utilities.report_generator import TestReportGenerator
        
        # Get environment from config
        env = config.getoption("--env", default="qa").upper()
        
        # Generate enterprise report with timestamp
        enterprise_report_path = Path(config.rootpath) / "reports" / f"enterprise_test_report_{timestamp}.html"
        report_generator = TestReportGenerator(
            config=config,
            test_results=_stakeholder_results,
            total_duration=total_duration,
            environment=env
        )
        report_generator.generate_report(enterprise_report_path)
        terminalreporter.write_sep("=", f"Enterprise test report generated: {enterprise_report_path}")
        
    except Exception as e:
        logger.warning(f"Failed to generate enterprise report: {str(e)}")
        terminalreporter.write_line(f"Warning: Enterprise report generation failed: {str(e)}")

@pytest.fixture
def excel_writer(request):
    def write_excel():
        name = getattr(request.node, 'excel_filename', 'default_output')
        df = getattr(request.node, 'excel_df', pd.DataFrame())
        basepath = tempfile.gettempdir()
        filename = f'{basepath}//{name}.xlsx'
        def try_json(val):
            if isinstance(val, str):
                try:
                    obj = json.loads(val)
                    return json.dumps(obj, indent=2)
                except Exception:
                    return val
            return val
        try:
            df_pretty = df.applymap(try_json)
        except Exception as e:
            print(f"Error processing DataFrame for Excel export: {e}")
            df_pretty = pd.DataFrame()
        sf = StyleFrame(df_pretty)
        sf.set_column_width_dict({col: 40 for col in sf.columns})
        wrap_style = Styler(wrap_text=True)
        for col in sf.columns:
            sf.apply_column_style(col, wrap_style)
        sf.to_excel(filename).close()
        print(f"Excel file written to {filename}")
    request.addfinalizer(write_excel)
    return lambda name_arg, df_arg: setattr(request.node, 'excel_filename', name_arg) or setattr(request.node, 'excel_df', df_arg)                   





