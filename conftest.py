from contextlib import contextmanager
import pytest
from playwright.sync_api import Playwright, Page, sync_playwright
from utilities.read_properties import Read_Configurations
from playwright.sync_api import Browser, Page, BrowserContext
from datetime import datetime
from pathlib import Path
import logging
import os
import re
import subprocess
import shutil
from collections import defaultdict
from html import escape as html_escape
from utilities.Custom_logger import LogGen
from utilities import evidence

# Configure logger for conftest
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Playwright evidence capture (trace + video).
# Trace is captured per-test as a chunk on the (shared) context so every test
# gets its own .zip. Video is recorded once for the shared session context
# (Option B) and linked to every test row.
# ---------------------------------------------------------------------------
_traced_contexts = []
_session_video_path = None
# The run folder and its artifact subdirs are (re)pointed in pytest_configure so
# every producer writes straight into one timestamped folder per run.
_run_dir = None
_run_log_dir = None
_run_log_name = None
_trace_dir = Path(__file__).resolve().parent / "reports" / "traces"
_video_dir = Path(__file__).resolve().parent / "reports" / "videos"

# Friendly labels for the scope portion of the run-folder name.
_MODULE_LABELS = {
    "test_tile": "Tile",
    "test_user_management": "User_Management",
    "test_data_ingestion": "Data_Ingestion",
    "test_data_lake_ip": "Data_Lake_IP",
    "test_invoice_management": "Invoice_Management",
    "test_reconciliation": "Reconciliation",
    "test_reports": "Reports",
}
_SUITE_MARKERS = [
    ("GIDEI_Smoke", "Smoke_Suite"),
    ("GIDEI_Sanity", "Sanity_Suite"),
    ("Regression", "Regression"),
]


def _module_label(path):
    stem = Path(str(path).split("::")[0]).stem
    if stem in _MODULE_LABELS:
        return _MODULE_LABELS[stem]
    if stem.startswith("test_"):
        stem = stem[len("test_"):]
    return stem.replace(" ", "_").title() or "Module"


def _resolve_scope_label(markexpr, arg_paths):
    """Derive the run-folder scope: marker suite > single module > full suite."""
    if markexpr:
        for marker, label in _SUITE_MARKERS:
            if re.search(rf"\b{re.escape(marker)}\b", markexpr):
                return label
    modules = []
    for arg in arg_paths or []:
        head = str(arg).split("::")[0]
        if head.endswith(".py") and "test_" in head:
            modules.append(head)
    modules = sorted(set(modules))
    if len(modules) == 1:
        return _module_label(modules[0])
    return "Full_Suite"


_SUITE_LABELS = {"Smoke_Suite", "Sanity_Suite", "Regression", "Full_Suite"}


def _run_log_basename(scope, arg_paths):
    """Meaningful base for the run log file, e.g. 'Smoke_Suite_Reports'."""
    parts = [scope]
    if scope in _SUITE_LABELS:
        for arg in arg_paths or []:
            head = str(arg).split("::")[0]
            if head.endswith(".py") and "test_" in head:
                label = _module_label(head)
                if label not in parts:
                    parts.append(label)
    return "_".join(parts)


def _start_tracing(context):
    """Begin tracing on a freshly created context (safe to call once per context)."""
    try:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        _traced_contexts.append(context)
    except Exception as exc:
        logger.debug(f"tracing.start failed: {exc}")


def _stop_tracing(context):
    """Stop tracing on a context before it is closed."""
    try:
        if context in _traced_contexts:
            context.tracing.stop()
            _traced_contexts.remove(context)
    except Exception as exc:
        logger.debug(f"tracing.stop failed: {exc}")


def _start_test_trace_chunk(item):
    """Open a per-test trace chunk on every active traced context."""
    for ctx in list(_traced_contexts):
        try:
            ctx.tracing.start_chunk(title=item.name)
        except Exception as exc:
            logger.debug(f"tracing.start_chunk failed: {exc}")


def _stop_test_trace_chunk(item):
    """Close the per-test trace chunk and return the primary trace file path."""
    primary = None
    for ctx in list(_traced_contexts):
        try:
            _trace_dir.mkdir(parents=True, exist_ok=True)
            safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", item.nodeid)[:120]
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            trace_file = _trace_dir / f"{safe}_{ts}.zip"
            ctx.tracing.stop_chunk(path=str(trace_file))
            if primary is None and trace_file.exists():
                primary = str(trace_file)
        except Exception as exc:
            logger.debug(f"tracing.stop_chunk failed: {exc}")
    return primary


def _current_log_file():
    """Return the active scenario log file path from the singleton logger."""
    if _singleton_logger is None:
        return None
    for handler in _singleton_logger.logger.handlers:
        if isinstance(handler, logging.FileHandler):
            return handler.baseFilename
    return None


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
    parser.addoption(
        "--debug-shots",
        action="store_true",
        default=False,
        help="Capture diagnostic screenshots during page-object steps (off by default)",
    )


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """Set up the per-run artifact folder and populate the pytest-html 'Base URL'.
    Runs last so the Base URL overrides the empty value pytest-base-url would set."""
    global _run_dir, _run_log_dir, _trace_dir, _video_dir, _run_log_name
    # Unify the environment switch: a single --env drives every config read,
    # including VAT_Common_Library.get_vat_config_value which keys off VAT_DTAI_ENV.
    try:
        os.environ["VAT_DTAI_ENV"] = config.getoption("--env").lower()
    except Exception:
        pass
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arg_paths = list(getattr(config, "args", []) or [])
        scope = _resolve_scope_label(getattr(config.option, "markexpr", "") or "", arg_paths)
        _run_dir = Path(config.rootpath) / "reports" / "runs" / f"{scope}_GIDEI_{timestamp}"
        _trace_dir = _run_dir / "traces"
        _video_dir = _run_dir / "videos"
        _run_log_dir = _run_dir / "logs"
        _screenshot_dir = _run_dir / "screenshots"
        for directory in (_trace_dir, _video_dir, _run_log_dir, _screenshot_dir):
            directory.mkdir(parents=True, exist_ok=True)
        os.environ["GIDEI_RUN_SCREENSHOT_DIR"] = str(_screenshot_dir)
        _run_log_name = f"{_run_log_basename(scope, arg_paths)}_Logs_{timestamp}"
        logger.info(f"=== Run folder: {_run_dir} ===")
    except Exception as exc:
        logger.debug(f"Run folder setup skipped: {exc}")
    if config.getoption("--debug-shots"):
        os.environ["GIDEI_DEBUG_SHOTS"] = "1"
    try:
        env = config.getoption("--env").lower()
        Read_Configurations.initialize(env)
        base_url = Read_Configurations.get_value("VAT_DTAI_URL")
        if not base_url:
            return
        if getattr(config.option, "base_url", None) in (None, ""):
            config.option.base_url = base_url
        try:
            from pytest_metadata.plugin import metadata_key
            config.stash[metadata_key]["Base URL"] = base_url
        except Exception:
            meta = getattr(config, "_metadata", None)
            if isinstance(meta, dict):
                meta["Base URL"] = base_url
    except Exception as exc:
        logger.debug(f"Base URL metadata population skipped: {exc}")


def pytest_collection_modifyitems(config, items):
    """Auto-skip environment-scoped scenarios so a single suite is safe in both
    environments: `uat_only` runs only under --env uat, `qa_only` only under --env qa."""
    env = (config.getoption("--env") or "qa").lower()
    skip_uat = pytest.mark.skip(reason="uat_only scenario: skipped outside UAT (--env uat)")
    skip_qa = pytest.mark.skip(reason="qa_only scenario: skipped outside QA (--env qa)")
    for item in items:
        if "uat_only" in item.keywords and env != "uat":
            item.add_marker(skip_uat)
        if "qa_only" in item.keywords and env != "qa":
            item.add_marker(skip_qa)


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
    _start_tracing(context)
    yield context
    _stop_tracing(context)
    context.close()


# Page fixture for general tests (function-scoped)
@pytest.fixture()
def get_page(get_context):
    """Create new page for each test"""
    page = get_context.new_page()
    yield page
    page.close()


# Session-scoped authenticated Global Insights And Data Enrichment For e-Invoicing session (Option B: login once for the whole run).
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

    session_video_dir = _video_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_video_dir.mkdir(parents=True, exist_ok=True)
    context = launch_browser.new_context(
        no_viewport=True,
        accept_downloads=True,
        record_video_dir=str(session_video_dir),
    )
    _start_tracing(context)
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
    global _session_video_path
    _stop_tracing(context)
    try:
        page.close()
        context.close()
    except Exception:
        pass
    # The single session video is finalized on context close; pick it up.
    try:
        webms = sorted(session_video_dir.glob("*.webm"), key=lambda p: p.stat().st_mtime)
        if webms:
            _session_video_path = str(webms[-1])
            logger.info(f"=== [vat_session] Session video: {_session_video_path} ===")
    except Exception as exc:
        logger.debug(f"session video resolution failed: {exc}")


# Global Insights And Data Enrichment For e-Invoicing Test Context - Shared state across navigation steps (function-scoped)
@pytest.fixture()
def vat_context():
    """
    Function-scoped context for storing test-specific state.
    Used by tests that need per-test isolation.
    """
    return {
        "launch_page": None,
        "role": "Admin",
        "workspace": "Client Belgium",
        "test_data": {},
    }


# Singleton logger instance for the whole test session
_singleton_logger = None
_stakeholder_results = []

@pytest.fixture(autouse=True)
def scenario_logger(request):
    global _singleton_logger
    if _singleton_logger is None:
        _singleton_logger = LogGen(
            str(_run_log_dir) if _run_log_dir else None,
            _run_log_name,
        )
    # Per-scenario log slicing + the single "Scenario Logs" attachment are handled
    # in pytest_runtest_call / pytest_runtest_makereport to avoid duplicate entries.
    yield


def _to_file_url(path_value):
    if not path_value:
        return None
    normalized = Path(path_value).resolve().as_posix()
    return f"file:///{normalized}"


def _build_run_index_html(run_dir, results, total_duration, report_links):
    total = len(results)
    passed = sum(1 for r in results if r["outcome"] == "passed")
    failed = sum(1 for r in results if r["outcome"] == "failed")
    skipped = sum(1 for r in results if r["outcome"] == "skipped")

    entries = [
        ("Test report (Stakeholder + Enterprise)", report_links.get("combined")),
        ("Detailed HTML report", report_links.get("detailed")),
        ("Allure report", report_links.get("allure")),
        ("Allure single-file report", report_links.get("allure_single")),
        ("Run log", report_links.get("run_log")),
    ]
    for label, sub in (("Traces", "traces"), ("Videos", "videos"), ("Logs", "logs")):
        if (run_dir / sub).exists():
            entries.append((label, f"{sub}/"))

    items = []
    for label, href in entries:
        if href:
            items.append(
                f"<li><b>{html_escape(label)}:</b> <a href='{html_escape(href)}'>{html_escape(href)}</a></li>"
            )
        else:
            items.append(f"<li><b>{html_escape(label)}:</b> <span class='muted'>Not available</span></li>")
    links_html = "".join(items)

    return f"""<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <title>Test Run: {html_escape(run_dir.name)}</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; margin: 24px; color: #1e1e1e; background: #f6f8fb; }}
    .wrap {{ max-width: 960px; margin: 0 auto; }}
    h1 {{ margin: 0 0 4px; font-size: 20px; }}
    .meta {{ color: #606a7a; margin-bottom: 18px; font-size: 13px; }}
    .cards {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 18px; }}
    .card {{ background: #fff; border-radius: 10px; padding: 12px; box-shadow: 0 2px 10px rgba(0,0,0,.06); }}
    .label {{ color: #6b7280; font-size: 11px; text-transform: uppercase; letter-spacing: .4px; }}
    .value {{ font-size: 24px; font-weight: 700; margin-top: 2px; }}
    .ok {{ color: #0f7b0f; }} .bad {{ color: #c62828; }} .warn {{ color: #9a6700; }}
    .panel {{ background: #fff; border-radius: 10px; padding: 16px; box-shadow: 0 2px 10px rgba(0,0,0,.06); }}
    ul {{ margin: 0; padding-left: 18px; }}
    li {{ margin: 6px 0; font-size: 14px; }}
    a {{ color: #0658d3; text-decoration: none; }}
    .muted {{ color: #9aa3af; }}
  </style>
</head>
<body>
  <div class='wrap'>
    <h1>Test Run: {html_escape(run_dir.name)}</h1>
    <div class='meta'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} &middot; Duration: {total_duration:.1f}s</div>
    <div class='cards'>
      <div class='card'><div class='label'>Total</div><div class='value'>{total}</div></div>
      <div class='card'><div class='label'>Passed</div><div class='value ok'>{passed}</div></div>
      <div class='card'><div class='label'>Failed</div><div class='value bad'>{failed}</div></div>
      <div class='card'><div class='label'>Skipped</div><div class='value warn'>{skipped}</div></div>
      <div class='card'><div class='label'>Time</div><div class='value'>{total_duration:.0f}s</div></div>
    </div>
    <div class='panel'>
      <h3>Artifacts</h3>
      <ul>{links_html}</ul>
    </div>
  </div>
</body>
</html>"""


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """Open a per-test Playwright trace chunk and mark the log offset."""
    log_file = _current_log_file()
    try:
        item._log_offset = os.path.getsize(log_file) if log_file and os.path.exists(log_file) else 0
    except Exception:
        item._log_offset = 0
    _start_test_trace_chunk(item)
    yield


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
        # Close the per-test trace chunk and link the resulting trace file.
        trace_file = _stop_test_trace_chunk(item)
        if trace_file:
            trace_url = _to_file_url(trace_file)

        log_file = _current_log_file()
        if log_file:
            try:
                offset = getattr(item, "_log_offset", 0)
                with open(log_file, "r", encoding="utf-8") as f:
                    f.seek(offset)
                    log_content = f.read()
                if log_content.strip():
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
                if "get_page" in item.funcargs:
                    page = item.funcargs["get_page"]
                
                if page:
                    # Route the failure screenshot into the run folder.
                    test_name = item.nodeid.replace("::", "_").replace("/", "_").replace("\\", "_")
                    screenshot_path = evidence.failure_shot(page, test_name)

                    if screenshot_path:
                        logger.info(f"Screenshot captured on failure: {screenshot_path}")
                        screenshot_url = _to_file_url(str(screenshot_path))
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


def _generate_allure_reports(allure_source_dir, allure_results_dir, allure_report_dir,
                             run_dir, timestamp, terminalreporter):
    """Copy raw Allure results into the run folder and build the multi-file and
    single-file reports. Called last so a slow/hung Allure CLI cannot block the
    core artifacts. Uses DEVNULL (no inherited stdout pipe) plus a timeout so an
    orphaned java grandchild can never make the call hang forever."""
    if not (allure_source_dir.exists() and any(allure_source_dir.iterdir())):
        return
    try:
        shutil.copytree(allure_source_dir, allure_results_dir, dirs_exist_ok=True)
        terminalreporter.write_line(f"Allure results copied to: {allure_results_dir}")
    except Exception as e:
        logger.warning(f"Failed to copy allure results: {str(e)}")

    allure_cmd = shutil.which("allure")
    if not allure_cmd:
        terminalreporter.write_line(
            "Warning: Allure CLI not found. Results collected but HTML report not generated."
        )
        return
    try:
        terminalreporter.write_line("Generating Allure HTML report...")
        subprocess.run(
            [allure_cmd, "generate", str(allure_results_dir), "-o", str(allure_report_dir), "--clean"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180,
        )
        terminalreporter.write_sep("=", f"Allure report: {allure_report_dir / 'index.html'}")
    except Exception as e:
        logger.warning(f"Failed to generate Allure report: {str(e)}")
        terminalreporter.write_line(f"Warning: Allure report generation failed: {str(e)}")

    try:
        single_tmp_dir = run_dir / f"allure-report-single_{timestamp}"
        subprocess.run(
            [allure_cmd, "generate", str(allure_results_dir), "-o", str(single_tmp_dir),
             "--single-file", "--clean"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180,
        )
        single_src = single_tmp_dir / "index.html"
        if single_src.exists():
            shutil.copyfile(single_src, run_dir / "allure-single-report.html")
            shutil.rmtree(single_tmp_dir, ignore_errors=True)
            terminalreporter.write_sep(
                "=", f"Allure single-file report: {run_dir / 'allure-single-report.html'}"
            )
    except Exception as e:
        logger.warning(f"Failed to generate single-file Allure report: {str(e)}")
        terminalreporter.write_line(f"Warning: single-file Allure report generation failed: {str(e)}")


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not _stakeholder_results:
        return

    # Consolidate every artifact for this run under one timestamped folder.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_reports_dir = Path(config.rootpath) / "reports"
    run_dir = _run_dir or (base_reports_dir / "runs" / f"Full_Suite_GIDEI_{timestamp}")
    run_dir.mkdir(parents=True, exist_ok=True)

    total_duration = sum(r["duration"] for r in _stakeholder_results)
    detailed_html = getattr(config.option, "htmlpath", None)

    # Allure directories inside the run folder (clean names; folder is already timestamped).
    allure_source_dir = base_reports_dir / "allure-results"  # live collection dir (--alluredir)
    allure_results_dir = run_dir / "allure-results"
    allure_report_dir = run_dir / "allure-report"
    
    # Whether an Allure report will be produced (generated last, below).
    allure_available = bool(
        shutil.which("allure")
        and allure_source_dir.exists()
        and any(allure_source_dir.iterdir())
    )

    # Link the single shared-session video to every test row (Option B: one
    # context per run, so one recording covers all scenarios).
    if _session_video_path:
        session_video_url = _to_file_url(_session_video_path)
        for row in _stakeholder_results:
            if not row.get("video_url"):
                row["video_url"] = session_video_url

    # Copy the pytest-html detailed report and the run log into the run folder.
    report_html_name = None
    if detailed_html:
        src_html = Path(detailed_html)
        if src_html.exists():
            dest_html = run_dir / "report.html"
            try:
                if src_html.resolve() != dest_html.resolve():
                    shutil.copyfile(src_html, dest_html)
                report_html_name = "report.html"
            except Exception as e:
                logger.warning(f"Failed to copy detailed HTML report: {str(e)}")

    src_log = base_reports_dir / "pytest_run.log"
    run_log_name = None
    if src_log.exists():
        try:
            shutil.copyfile(src_log, run_dir / "pytest_run.log")
            run_log_name = "pytest_run.log"
        except Exception as e:
            logger.warning(f"Failed to copy run log: {str(e)}")

    # Related-artifact links (relative so the run folder stays portable).
    allure_index_rel = "allure-report/index.html" if allure_available else None
    allure_single_rel = "allure-single-report.html" if allure_available else None
    related_links = {
        "detailed": report_html_name,
        "allure": allure_index_rel,
        "allure_single": allure_single_rel,
        "run_log": run_log_name,
    }

    # Combined Stakeholder + Enterprise report, written inside the run folder.
    env = config.getoption("--env", default="qa").upper()
    combined_report_name = "GIDEI_Stakeholder_Enterprise_Test_Report.html"
    combined_report_path = run_dir / combined_report_name
    combined_name = None
    try:
        from utilities.report_generator import TestReportGenerator
        report_generator = TestReportGenerator(
            config=config,
            test_results=_stakeholder_results,
            total_duration=total_duration,
            environment=env,
            related_links=related_links,
        )
        report_generator.generate_report(combined_report_path)
        combined_name = combined_report_name
        terminalreporter.write_sep("=", f"Test report generated: {combined_report_path}")
    except Exception as e:
        logger.warning(f"Failed to generate test report: {str(e)}")
        terminalreporter.write_line(f"Warning: Test report generation failed: {str(e)}")

    report_links = {
        "combined": combined_name,
        "detailed": report_html_name,
        "allure": allure_index_rel,
        "allure_single": allure_single_rel,
        "run_log": run_log_name,
    }

    # Honour an explicit --stakeholder-summary override by copying the combined report there.
    override = config.getoption("stakeholder_summary")
    if override and combined_report_path.exists():
        try:
            override_path = Path(override)
            override_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(combined_report_path, override_path)
        except Exception as e:
            logger.warning(f"Failed to write report override: {str(e)}")

    # Landing page linking every artifact in the run folder.
    try:
        index_html = _build_run_index_html(
            run_dir=run_dir,
            results=_stakeholder_results,
            total_duration=total_duration,
            report_links=report_links,
        )
        (run_dir / "index.html").write_text(index_html, encoding="utf-8")
        terminalreporter.write_sep("=", f"Run folder: {run_dir}")
        terminalreporter.write_sep("=", f"Run index: {run_dir / 'index.html'}")
    except Exception as e:
        logger.warning(f"Failed to build run index: {str(e)}")

    # Allure last: a slow/hung Allure CLI must never block the artifacts above.
    _generate_allure_reports(
        allure_source_dir, allure_results_dir, allure_report_dir, run_dir, timestamp, terminalreporter
    )
