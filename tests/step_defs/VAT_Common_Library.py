"""
Common Step Definitions and Navigation Utilities for Global Insights And Data Enrichment For e-Invoicing Tests
- Configuration helpers
- Page state detection functions
- Navigation utility functions  
- pytest-bdd step definitions for login, client selection, and DTAI navigation

Import these steps and utilities in specific test modules to avoid duplication.
"""
import os
import re
import logging
from typing import Dict, Any
import pytest
from playwright.sync_api import Page
from pytest_bdd import given, when, then, parsers
from pageobjects.launch_app_page import LaunchAppPage
from utilities.read_properties import Read_Configurations

# Configure logger for this module
logger = logging.getLogger(__name__)


# ==========================================
# CONFIGURATION HELPERS
# ==========================================

DEFAULT_BASE_URL = "https://vatdtaiqa-fpgfhdgxgtaccyhv.eastus-01.azurewebsites.net/"
DEFAULT_POST_LOGIN_WAIT_MS = 25000


def get_vat_config_value(key: str, default=None):
    """Get configuration value from environment or config file"""
    env_value = os.getenv(key)
    if env_value:
        return env_value
    try:
        Read_Configurations.initialize(os.getenv("VAT_DTAI_ENV", "qa"))
        value = Read_Configurations.get_value(key)
        if value not in (None, ""):
            return value
    except Exception:
        pass
    return default


def env_has_powerbi_dashboard() -> bool:
    """Capability flag: does the active environment ship the PowerBI dashboard?
    Driven by HAS_POWERBI_DASHBOARD in the env's config section (UAT=true, QA=false)."""
    val = get_vat_config_value("HAS_POWERBI_DASHBOARD", "false")
    return str(val).strip().lower() in ("1", "true", "yes", "on")


def get_post_login_wait_ms() -> int:
    """Get post-login wait time in milliseconds"""
    value = get_vat_config_value("VAT_DTAI_POST_LOGIN_WAIT_MS", str(DEFAULT_POST_LOGIN_WAIT_MS))
    try:
        return int(value)
    except Exception:
        return DEFAULT_POST_LOGIN_WAIT_MS


# ==========================================
# PAGE STATE DETECTION FUNCTIONS
# ==========================================

def is_on_login_page(page: Page) -> bool:
    """Check if currently on a login page (env-agnostic).
    QA: Microsoft/text login. UAT: EY SSO landing (/sso, 'I am EY employee') then Microsoft."""
    try:
        url = (page.url or "").lower()
        if ("login.microsoftonline.com" in url or "/sso" in url
                or "login.ey.com" in url or "adfs" in url or "saml2" in url):
            return True
        # DOM fallbacks for the UAT EY SSO account-type page / Microsoft email step.
        if page.locator("text=I am EY employee").count() > 0:
            return True
        if page.locator("input[type='email'], input[name='loginfmt'], #i0116").count() > 0:
            return True
    except Exception:
        pass
    return False


def is_on_home_page(page: Page) -> bool:
    """Check if currently on Global Insights And Data Enrichment For e-Invoicing home page"""
    try:
        url = page.url or ""
        # URL hex-encodes page names: PageTEAMSStartup = 506167655445414d5353746172747570
        return ("PageTEAMSStartup" in url or "PageFW" in url
                or "506167655445414d5353746172747570" in url)
    except Exception:
        return False


def is_on_dtai_dashboard(page: Page) -> bool:
    """Check if currently on Global Insights And Data Enrichment For e-Invoicing dashboard"""
    try:
        url = page.url
        # Check for DTAI dashboard indicators
        if "PageVATDTAI" in url or "show/506167655445414d5356415444544149" in url:
            return True
        # Also check for dashboard heading
        dashboard_heading = page.locator("role=heading[level=2][name*='VATDTAI']")
        if dashboard_heading.count() > 0:
            return True
    except Exception:
        pass
    return False


def is_authenticated(page: Page) -> bool:
    """Robustly detect whether we are inside the authenticated app shell.
    Handles being on the home page, the DTAI dashboard, or any module tab within it.
    """
    try:
        if is_on_login_page(page):
            return False
        if get_current_page_state(page) in ("home", "dtai_dashboard"):
            return True
        # Inside the DTAI SPA the module tabs are present regardless of the active tab.
        if page.locator("role=tab[name='Data Ingestion' i]").count() > 0:
            return True
        body = page.inner_text("body")
        if re.search(r"Global\s+Insights\s+And\s+Data\s+Enrichment\s+For\s+e-?Invoicing", body, re.I) and "Welcome to the" not in body:
            return True
    except Exception:
        pass
    return False


def get_current_page_state(page: Page) -> str:
    """
    Detect current page state
    Returns: 'login', 'client_selection', 'home', 'dtai_dashboard', or 'unknown'
    """
    try:
        url = (page.url or "").lower()
        # Client selection first (its URL would otherwise be caught by broad login checks).
        if "5061676553656c656374436c69656e74" in url:
            return "client_selection"
        if ("login.microsoftonline.com" in url or "/sso" in url
                or "login.ey.com" in url or "adfs" in url or "saml2" in url):
            return "login"
        if is_on_dtai_dashboard(page):
            return "dtai_dashboard"
        if is_on_home_page(page):
            return "home"
        # DOM fallback: EY SSO account-type page or Microsoft email step.
        if page.locator("text=I am EY employee").count() > 0:
            return "login"
        if page.locator("input[type='email'], input[name='loginfmt'], #i0116").count() > 0:
            return "login"
    except Exception:
        pass
    return "unknown"


# ==========================================
# NAVIGATION HELPER FUNCTIONS
# ==========================================

def wait_for_ready_state(page: Page, timeout_ms: int = 120000) -> str:
    """
    Wait for page to be in login or home state
    
    Returns:
        "login" - if on login page
        "home" - if on home page
        "timeout" - if timeout exceeded
    """
    elapsed = 0
    while elapsed < timeout_ms:
        # Login detection (env-agnostic): UAT EY SSO landing / Microsoft, or QA text form.
        try:
            url = (page.url or "").lower()
            if ("login.microsoftonline.com" in url or "/sso" in url
                    or "login.ey.com" in url or "adfs" in url or "saml2" in url):
                return "login"
            if page.locator("text=I am EY employee").count() > 0:
                return "login"
            if page.locator("input[type='email'], input[name='loginfmt'], #i0116").count() > 0:
                return "login"
            login_inputs = page.locator("input[type='text']:visible")
            sign_in = page.get_by_role("button", name=re.compile(r"^Sign In$", re.I))
            if login_inputs.count() >= 2 and sign_in.count() > 0:
                return "login"
        except Exception:
            pass

        # Home page (after client selection)
        try:
            page_text = page.inner_text("body")
            if re.search(r"Global\s+Insights\s+And\s+Data\s+Enrichment\s+For\s+e-?Invoicing", page_text, re.I):
                return "home"
        except Exception:
            pass

        page.wait_for_timeout(1000)
        elapsed += 1000
    return "timeout"


def wait_for_home(page: Page, timeout_ms: int = 120000) -> None:
    """
    Wait until home page is loaded (after client selection)
    
    Raises:
        AssertionError: If home page not reached within timeout
    """
    elapsed = 0
    while elapsed < timeout_ms:
        # URL hex-encodes page names: PageSelectClient = 5061676553656c656374436c69656e74
        if "5061676553656c656374436c69656e74" in (page.url or ""):
            page.wait_for_timeout(1000)
            elapsed += 1000
            continue
        # UAT lands on the GTP startup/home page (DTAI tile only appears after choosing a
        # category); QA's default view already shows the DTAI content. Accept either.
        if is_on_home_page(page):
            return
        try:
            page_text = page.inner_text("body")
            if re.search(r"Global\s+Insights\s+And\s+Data\s+Enrichment\s+For\s+e-?Invoicing", page_text, re.I):
                return
        except Exception:
            pass
        page.wait_for_timeout(1000)
        elapsed += 1000
    raise AssertionError("Home page was not found after login and client selection.")


def wait_for_post_login_ready(page: Page, timeout_ms: int = None) -> str:
    """Dynamically wait after login until the app is ready to interact with, instead of a fixed
    sleep. Returns as soon as one of these is detected:
      - 'client_selection' : the client picker + Continue button are rendered
      - 'home' / 'dtai_dashboard' : a shared session is already inside the app
      - 'timeout' : fell through the max wait (caller continues with its own checks)
    `timeout_ms` defaults to the configured post-login budget, but polling means we usually
    return in well under a second once the page settles.
    """
    if timeout_ms is None:
        timeout_ms = get_post_login_wait_ms()
    elapsed = 0
    poll_ms = 250
    while elapsed < timeout_ms:
        state = get_current_page_state(page)
        if state in ("home", "dtai_dashboard"):
            return state
        try:
            has_continue = page.locator("role=button[name='Continue' i]").count() > 0
            if has_continue and page.locator("select.selectpicker, button.selectpicker").count() > 0:
                return "client_selection"
            if has_continue and "Welcome to the" in page.inner_text("body"):
                return "client_selection"
        except Exception:
            pass
        page.wait_for_timeout(poll_ms)
        elapsed += poll_ms
    return "timeout"


# ==========================================
# REUSABLE NAVIGATION IMPLEMENTATIONS
# ==========================================

def perform_login(page: Page, role: str = "Admin") -> LaunchAppPage:
    """
    Complete login flow to Global Insights And Data Enrichment For e-Invoicing application
    
    Args:
        page: Playwright Page object
        role: User role - "Admin" or "Country Owner"
    
    Returns:
        LaunchAppPage: Launch app page object instance
        
    Raises:
        pytest.skip: If credentials not configured
    """
    logger.info("\n=== Starting Login ===")

    # Idempotency: if the shared session is already authenticated (home/dashboard or any
    # module tab inside the app), skip the expensive goto + credential flow entirely.
    if is_authenticated(page):
        logger.info("[perform_login] Already authenticated; skipping login")
        return LaunchAppPage(page)

    username = get_vat_config_value("VAT_DTAI_USERNAME")
    password = get_vat_config_value("VAT_DTAI_PASSWORD")
    base_url = get_vat_config_value("VAT_DTAI_URL", DEFAULT_BASE_URL)

    if not username or not password:
        pytest.skip("VAT credentials are not configured. Set VAT_DTAI_USERNAME/VAT_DTAI_PASSWORD in config.ini")

    # Navigate to application
    page.goto(base_url, wait_until="domcontentloaded")
    state = wait_for_ready_state(page)
    assert state != "timeout", "Login page/homepage was not ready within timeout."

    # Create launch app page object
    launch_page = LaunchAppPage(page)

    # Perform login if needed
    if state == "login":
        launch_page.login_with_credentials(username, password)
        # After login, wait dynamically for the client-selection page (or app shell) to be ready,
        # returning as soon as it appears instead of a fixed post-login sleep.
        wait_for_post_login_ready(page)
    
    logger.info(f"Login complete. Current URL: {page.url}")
    logger.info("=== Login Complete ===\n")
    
    return launch_page


def perform_client_selection(page: Page, launch_page: LaunchAppPage, workspace_name: str = "Client Belgium"):
    """
    Select workspace and continue to home page
    
    Args:
        page: Playwright Page object
        launch_page: LaunchAppPage object instance
        workspace_name: Name of workspace/client to select
    """
    logger.info("\n=== Starting Client Selection ===")
    logger.info(f"Current URL: {page.url}")

    # Idempotency: already past client selection (inside the app) -> nothing to do.
    if is_authenticated(page):
        logger.info("[perform_client_selection] Already past client selection; skipping")
        return

    # Dynamically wait for the client-selection UI (or app shell) to be ready, rather than a
    # fixed settle sleep.
    wait_for_post_login_ready(page, timeout_ms=15000)

    # Check if on client selection page
    page_text = page.inner_text("body")
    logger.info(f"Page text preview (first 300 chars): {page_text[:300]}")
    
    # Check for Continue button (more reliable than URL check)
    continue_button = page.locator("role=button[name='Continue' i]")
    
    # If Continue button is visible, we're on client selection page
    if continue_button.count() > 0 and "Welcome to the" in page_text:
        logger.info(f"On client selection page - selecting workspace: {workspace_name}")
        launch_page.select_workspace_and_continue(workspace_name)
        page.wait_for_timeout(3000)
        logger.info(f"After selection, URL: {page.url}")
        # Wait for home page to be ready
        logger.info("Waiting for home page to be ready...")
        wait_for_home(page)
    else:
        logger.info("Already past client selection page or on home page")
        # Verify we're on home page
        dtai_present = bool(re.search(r"Global\s+Insights\s+And\s+Data\s+Enrichment\s+For\s+e-?Invoicing", page_text, re.I))
        if not dtai_present:
            # Still need to wait for home page
            logger.info("Waiting for home page to be ready...")
            wait_for_home(page)
    
    logger.info(f"Home page ready. Final URL: {page.url}")
    logger.info("=== Client Selection Complete ===\n")


def perform_dtai_navigation(page: Page, launch_page: LaunchAppPage):
    """
    Navigate to Global Insights And Data Enrichment For e-Invoicing application dashboard
    Flow: Click Consumption Tax → Locate DTAI section → Click Global Insights And Data Enrichment For e-Invoicing app
    
    Args:
        page: Playwright Page object
        launch_page: LaunchAppPage object instance
        
    Raises:
        AssertionError: If DTAI application does not launch successfully
    """
    logger.info("\n=== Starting DTAI Navigation ===")
    logger.info(f"Current URL before navigation: {page.url}")
    
    # Navigate using the launch page method
    launch_page.navigate_to_dtai_vat_app()

    # Verify and retry once if flaky redirection keeps us on home page
    if not launch_page.verify_dtai_app_launched():
        logger.warning("[WARNING] DTAI app not detected after first click, retrying navigation once")
        page.wait_for_timeout(2000)
        try:
            ok_btn = page.locator("button.btn-default:has-text('OK'), button:has-text('OK'):visible").first
            if ok_btn.count() > 0 and ok_btn.is_visible(timeout=1000):
                ok_btn.click()
                page.wait_for_timeout(1000)
        except Exception:
            pass
        launch_page.navigate_to_dtai_vat_app()

    # Final verification
    assert launch_page.verify_dtai_app_launched(), "DTAI application did not launch successfully"
    
    logger.info(f"Current URL after navigation: {page.url}")
    logger.info("=== DTAI Navigation Complete ===\n")


def perform_complete_navigation_flow(page: Page, role: str = "Admin", workspace: str = "Client Belgium") -> LaunchAppPage:
    """
    Execute complete navigation flow from login to DTAI dashboard
    
    Steps:
    1. Login with credentials
    2. Select workspace/client
    3. Click Continue
    4. Navigate to home page
    5. Click Consumption Tax
    6. Click Global Insights And Data Enrichment For e-Invoicing app
    7. Reach DTAI dashboard
    
    Args:
        page: Playwright Page object
        role: User role (Admin/Country Owner)
        workspace: Workspace name to select
        
    Returns:
        LaunchAppPage: Initialized launch page object
    """
    # Step 1: Login
    launch_page = perform_login(page, role)
    
    # Step 2: Select client and continue
    perform_client_selection(page, launch_page, workspace)
    
    # At this point, we're on the home page
    # DTAI navigation will be done separately based on test needs
    
    return launch_page


# ==========================================
# SMART NAVIGATION FUNCTIONS
# ==========================================

def ensure_home_page(page: Page, launch_page: LaunchAppPage = None) -> LaunchAppPage:
    """
    Smart navigation: Ensure we're on home page, perform login/navigation only if needed.
    Use with module-scoped authenticated sessions.
    
    Args:
        page: Playwright Page object
        launch_page: Optional existing LaunchAppPage instance
        
    Returns:
        LaunchAppPage: Initialized launch page object
    """
    current_state = get_current_page_state(page)
    logger.info(f"Current page state: {current_state}")
    
    if current_state == "home":
        logger.info("Already on home page, skipping navigation")
        if not launch_page:
            launch_page = LaunchAppPage(page)
        return launch_page
    
    if current_state == "dtai_dashboard":
        logger.info("On DTAI dashboard, navigating back to GTP IT home page")
        # The DTAI app returns to the GTP IT home page via a breadcrumb/link/button "Home"
        # (NOT a tab). Try each candidate and confirm we actually reached the home page.
        home_locators = [
            page.locator("role=listitem >> role=link[name='Home' i]").first,
            page.get_by_role("link", name=re.compile(r"^Home$", re.I)).first,
            page.get_by_role("button", name=re.compile(r"^Home$", re.I)).first,
            page.get_by_text(re.compile(r"^Home$", re.I)).first,
        ]
        reached_home = False
        for locator in home_locators:
            try:
                if locator.count() == 0:
                    continue
                locator.click(timeout=5000)
                page.wait_for_timeout(2000)
                if get_current_page_state(page) == "home":
                    reached_home = True
                    logger.info("Returned to GTP IT home page from DTAI dashboard")
                    break
            except Exception as exc:
                logger.info(f"Home locator attempt failed, trying next: {exc}")
                continue
        if not reached_home:
            logger.warning("Could not click a Home control; performing full navigation to home")
            launch_page = perform_login(page)
            perform_client_selection(page, launch_page)
        if not launch_page:
            launch_page = LaunchAppPage(page)
        return launch_page
    
    # If not on home or dashboard, perform full navigation
    logger.info("Not on home page, performing full navigation")
    launch_page = perform_login(page)
    perform_client_selection(page, launch_page)
    return launch_page


def ensure_dtai_dashboard(page: Page, launch_page: LaunchAppPage = None) -> LaunchAppPage:
    """
    Smart navigation: Ensure we're on DTAI dashboard, navigate only if needed.
    Use with module-scoped authenticated sessions.
    
    Args:
        page: Playwright Page object
        launch_page: Optional existing LaunchAppPage instance
        
    Returns:
        LaunchAppPage: Initialized launch page object
    """
    current_state = get_current_page_state(page)
    print(f"Current page state: {current_state}")
    
    if current_state == "dtai_dashboard":
        print("Already on DTAI dashboard, skipping navigation")
        if not launch_page:
            launch_page = LaunchAppPage(page)
        return launch_page
    
    # Ensure we're at least on home page
    launch_page = ensure_home_page(page, launch_page)
    
    # Navigate to DTAI dashboard
    print("Navigating to DTAI dashboard")
    perform_dtai_navigation(page, launch_page)
    
    return launch_page


def navigate_to_module(page: Page, module_name: str, launch_page: LaunchAppPage = None) -> LaunchAppPage:
    """
    Smart navigation: Navigate to specific module tab (User Management, Data Ingestion, etc.)
    Ensures we're on DTAI dashboard first, then clicks the module tab.
    
    Args:
        page: Playwright Page object
        module_name: Module tab name (e.g., "User Management", "Data Ingestion")
        launch_page: Optional existing LaunchAppPage instance
        
    Returns:
        LaunchAppPage: Initialized launch page object
    """
    # Ensure on DTAI dashboard
    launch_page = ensure_dtai_dashboard(page, launch_page)
    
    # Click module tab
    print(f"Navigating to {module_name} module")
    module_tab = page.locator(f"role=tab[name='{module_name}' i]")
    
    if module_tab.count() > 0:
        module_tab.click()
        page.wait_for_timeout(2000)
        print(f"Successfully navigated to {module_name} module")
    else:
        print(f"WARNING: {module_name} tab not found")
    
    return launch_page


# ==========================================
# SHARED SESSION HELPERS (Option B: login once, reuse session)
# ==========================================

def dismiss_session_timeout_if_present(page: Page) -> bool:
    """Dismiss the "signed in from another browser window" session-timeout dialog if shown."""
    try:
        dialog = page.locator("text=You have signed in from another browser window").first
        if dialog.count() > 0 and dialog.is_visible(timeout=1000):
            logger.warning("[session] Timeout dialog detected - dismissing")
            for sel in ["button:has-text('Ok')", "button:has-text('OK')", "button.btn-default"]:
                btn = page.locator(sel).first
                if btn.count() > 0 and btn.is_visible(timeout=1000):
                    btn.click()
                    page.wait_for_timeout(1500)
                    return True
    except Exception:
        pass
    return False


def dismiss_application_popup(page: Page) -> None:
    """Dismiss the analytics/alert popup that appears on the DTAI dashboard after navigation.
    Idempotent: silently returns if no popup is present.
    """
    # Allow time for the popup to appear after DTAI navigation
    page.wait_for_timeout(3000)

    # Attempt 1: the customAlertoverlay container (up to 8s)
    try:
        overlay = page.locator("div.customAlertoverlay").first
        overlay.wait_for(state="visible", timeout=8000)
        logger.info("[popup] Analytics overlay detected")
        for btn_sel in ["button:has-text('OK')", "button:has-text('Ok')", "button.btn-default", "button"]:
            btn = overlay.locator(btn_sel).first
            try:
                if btn.count() > 0 and btn.is_visible(timeout=1000):
                    btn.click()
                    logger.info(f"[popup] Clicked overlay button: '{btn.inner_text().strip()}'")
                    page.wait_for_timeout(1500)
                    return
            except Exception:
                continue
        logger.warning("[popup] Overlay found but no button - removing via JS")
        page.evaluate("(el) => el.remove()", overlay.element_handle())
        page.wait_for_timeout(500)
        return
    except Exception:
        pass

    # Attempt 2: page-wide fallback - any visible OK / btn-default button
    try:
        for sel in [
            "button.btn-default:has-text('OK')",
            "button.btn-default:has-text('Ok')",
            "button:has-text('OK'):visible",
        ]:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_visible(timeout=1000):
                btn.click()
                logger.info(f"[popup] Clicked page-level OK via: {sel}")
                page.wait_for_timeout(1500)
                return
    except Exception:
        pass

    logger.info("[popup] No analytics popup detected - continuing")


def ensure_on_module(page: Page, module_name: str, launch_page: LaunchAppPage = None) -> LaunchAppPage:
    """Self-healing entry point used by every module's Background.
    Re-authenticates only if the shared session dropped, then clicks the target module tab.
    """
    # Self-heal: handle session-timeout dialog, then re-auth if we are no longer inside the app.
    dismiss_session_timeout_if_present(page)
    if not is_authenticated(page):
        logger.warning("[ensure_on_module] Session not authenticated - re-running full navigation flow")
        launch_page = perform_login(page)
        perform_client_selection(page, launch_page)
        perform_dtai_navigation(page, launch_page)
        dismiss_application_popup(page)

    if launch_page is None:
        launch_page = LaunchAppPage(page)

    # Inside the DTAI SPA the module tabs are always present; a direct tab click is the
    # cheap per-scenario reset. Fall back to a full dashboard navigation only if not found.
    module_tab = page.locator(f"role=tab[name='{module_name}' i]")
    if module_tab.count() == 0:
        logger.info(f"[ensure_on_module] Tab '{module_name}' not visible - ensuring DTAI dashboard first")
        launch_page = ensure_dtai_dashboard(page, launch_page)
        module_tab = page.locator(f"role=tab[name='{module_name}' i]")

    if module_tab.count() > 0:
        module_tab.first.click()
        page.wait_for_timeout(1500)
        logger.info(f"[ensure_on_module] Switched to '{module_name}' module")
    else:
        logger.warning(f"[ensure_on_module] Tab '{module_name}' not found")
    return launch_page


# ==========================================
# COMMON CONTEXT FIXTURE
# ==========================================

@pytest.fixture()
def vat_context() -> Dict[str, Any]:
    """
    Shared context for storing test state across steps
    Use this fixture in all Global Insights And Data Enrichment For e-Invoicing test modules
    """
    return {
        "launch_page": None,
        "role": "Admin",
        "workspace": "Client Belgium",
    }


# ==========================================
# COMMON GIVEN STEPS (Preconditions)
# ==========================================

@given("I login as Admin user", target_fixture="login_result")
def step_login_as_admin(get_page: Page, vat_context: Dict) -> Page:
    """Login to application as Admin user"""
    print("\n=== STEP: Login as Admin user ===")
    launch_page = perform_login(get_page, role="Admin")
    vat_context["launch_page"] = launch_page
    vat_context["role"] = "Admin"
    return get_page


@given("I login as Country Owner user", target_fixture="login_result")
def step_login_as_country_owner(get_page: Page, vat_context: Dict) -> Page:
    """Login to application as Country Owner user"""
    print("\n=== STEP: Login as Country Owner user ===")
    launch_page = perform_login(get_page, role="Country Owner")
    vat_context["launch_page"] = launch_page
    vat_context["role"] = "Country Owner"
    return get_page


@given("I login as Admin", target_fixture="login_result")
def step_login_admin_short(get_page: Page, vat_context: Dict) -> Page:
    """Login to application as Admin (short version)"""
    return step_login_as_admin(get_page, vat_context)


@given("I login as <role> user", target_fixture="login_result")
def step_login_as_role(get_page: Page, vat_context: Dict, role: str) -> Page:
    """Login to application with specific role (parameterized)"""
    print(f"\n=== STEP: Login as {role} user ===")
    launch_page = perform_login(get_page, role=role)
    vat_context["launch_page"] = launch_page
    vat_context["role"] = role
    return get_page


# ==========================================
# COMMON WHEN STEPS (Actions)
# ==========================================

@when("I select the Client from dropdown and clicked on continue button")
def step_select_client_and_continue(get_page: Page, vat_context: Dict):
    """Select Client Belgium from dropdown and click continue"""
    launch_page = vat_context.get("launch_page")
    if not launch_page:
        launch_page = LaunchAppPage(get_page)
        vat_context["launch_page"] = launch_page
    
    workspace = vat_context.get("workspace", "Client Belgium")
    perform_client_selection(get_page, launch_page, workspace)


@when("I navigate to Global Insights And Data Enrichment For e-Invoicing application")
def step_navigate_to_vat_dtai(get_page: Page, vat_context: Dict):
    """
    Navigate to Global Insights And Data Enrichment For e-Invoicing application by clicking through:
    - Consumption Tax category
    - Global Insights And Data Enrichment For e-Invoicing app
    """
    launch_page = vat_context.get("launch_page")
    if not launch_page:
        # Fallback if launch_page not in context
        print("WARNING: launch_page not in context, creating new instance")
        launch_page = LaunchAppPage(get_page)
        vat_context["launch_page"] = launch_page
    
    perform_dtai_navigation(get_page, launch_page)


@when("User clicks the Global Insights And Data Enrichment For e-Invoicing tile")
def step_click_dtai_tile(get_page: Page, vat_context: Dict):
    """Click the Global Insights And Data Enrichment For e-Invoicing tile to launch the application"""
    step_navigate_to_vat_dtai(get_page, vat_context)


@given("I click OK on the application popup")
@when("I click OK on the application popup")
def step_dismiss_application_popup(get_page: Page):
    """Dismiss the analytics/alert popup that appears on the DTAI dashboard after navigation."""
    dismiss_application_popup(get_page)


# New consolidated navigation step (Consumption Tax -> Global Insights And Data Enrichment For e-Invoicing app), idempotent.
@given("I click on Consumption Tax and navigate to Global Insights And Data Enrichment For e-Invoicing application")
@when("I click on Consumption Tax and navigate to Global Insights And Data Enrichment For e-Invoicing application")
def step_consumption_tax_to_dtai(get_page: Page, vat_context: Dict):
    """Navigate from the home page (Consumption Tax) into the Global Insights And Data Enrichment For e-Invoicing application.
    Idempotent: no-op when already on the DTAI dashboard (shared session)."""
    launch_page = ensure_dtai_dashboard(get_page, vat_context.get("launch_page"))
    vat_context["launch_page"] = launch_page


# Dynamic, self-healing per-module navigation used by every feature file's Background.
@given(parsers.parse('I navigate to the "{module_name}" module'))
@when(parsers.parse('I navigate to the "{module_name}" module'))
@then(parsers.parse('I navigate to the "{module_name}" module'))
def step_navigate_to_module_dynamic(get_page: Page, vat_context: Dict, module_name: str):
    """Navigate to the module-specific tab (Data Lake IP, Data Ingestion, Invoice Management,
    Reconciliation, Reports, User Management). Self-heals the session if it dropped."""
    launch_page = ensure_on_module(get_page, module_name, vat_context.get("launch_page"))
    vat_context["launch_page"] = launch_page


# Ensure the shared session is on the GTP IT home page (where the Consumption Tax tiles live).
# Used by the VAT Tile Background so tile-visibility/launch scenarios start from home even when a
# shared session was left inside the DTAI application by a previous scenario.
@given("I am on the GTP IT home page")
@when("I am on the GTP IT home page")
@then("I am on the GTP IT home page")
def step_ensure_on_home_page(get_page: Page, vat_context: Dict):
    """Navigate back to the GTP IT home page if the session is currently inside the DTAI app."""
    launch_page = ensure_home_page(get_page, vat_context.get("launch_page"))
    vat_context["launch_page"] = launch_page
