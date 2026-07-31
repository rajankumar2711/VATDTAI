"""
Common Step Definitions and Navigation Utilities for VAT DTAI Tests
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
from pytest_bdd import given, when
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
    """Check if currently on login page"""
    try:
        url = page.url
        # URL hex-encodes page names: PageSelectClient = 5061676553656c656374436c69656e74
        return "5061676553656c656374436c69656e74" in url or "login.microsoftonline.com" in url
    except Exception:
        return False


def is_on_home_page(page: Page) -> bool:
    """Check if currently on VAT DTAI home page"""
    try:
        url = page.url
        return "PageTEAMSStartup" in url or "PageFW" in url
    except Exception:
        return False


def is_on_dtai_dashboard(page: Page) -> bool:
    """Check if currently on DTAI VAT dashboard"""
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


def get_current_page_state(page: Page) -> str:
    """
    Detect current page state
    Returns: 'login', 'client_selection', 'home', 'dtai_dashboard', or 'unknown'
    """
    try:
        url = page.url
        if "login.microsoftonline.com" in url:
            return "login"
        # URL hex-encodes page names: PageSelectClient = 5061676553656c656374436c69656e74
        if "5061676553656c656374436c69656e74" in url:
            return "client_selection"
        if is_on_dtai_dashboard(page):
            return "dtai_dashboard"
        if is_on_home_page(page):
            return "home"
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
        # Check if login page
        login_inputs = page.locator("input[type='text']:visible")
        sign_in = page.get_by_role("button", name=re.compile(r"^Sign In$", re.I))
        if login_inputs.count() >= 2 and sign_in.count() > 0:
            return "login"

        # Check if home page (after client selection)
        page_text = page.inner_text("body")
        has_dtai = bool(re.search(r"Digital\s+Tax\s+Administration\s+Insights", page_text, re.I))
        if has_dtai:
            return "home"

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
        if "5061676553656c656374436c69656e74" in page.url:
            page.wait_for_timeout(1000)
            elapsed += 1000
            continue
        page_text = page.inner_text("body")
        # Check if reached home page with DTAI content
        has_dtai = bool(re.search(r"Digital\s+Tax\s+Administration\s+Insights", page_text, re.I))
        if has_dtai:
            return
        page.wait_for_timeout(1000)
        elapsed += 1000
    raise AssertionError("Home page was not found after login and client selection.")


# ==========================================
# REUSABLE NAVIGATION IMPLEMENTATIONS
# ==========================================

def perform_login(page: Page, role: str = "Admin") -> LaunchAppPage:
    """
    Complete login flow to VAT DTAI application
    
    Args:
        page: Playwright Page object
        role: User role - "Admin" or "Country Owner"
    
    Returns:
        LaunchAppPage: Launch app page object instance
        
    Raises:
        pytest.skip: If credentials not configured
    """
    logger.info("\n=== Starting Login ===")
    
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
        # After login, wait for page to transition
        page.wait_for_timeout(get_post_login_wait_ms())
    
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
    
    # Wait for page to settle after login
    page.wait_for_timeout(3000)
    
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
        dtai_present = bool(re.search(r"Digital\s+Tax\s+Administration\s+Insights", page_text, re.I))
        if not dtai_present:
            # Still need to wait for home page
            logger.info("Waiting for home page to be ready...")
            wait_for_home(page)
    
    logger.info(f"Home page ready. Final URL: {page.url}")
    logger.info("=== Client Selection Complete ===\n")


def perform_dtai_navigation(page: Page, launch_page: LaunchAppPage):
    """
    Navigate to DTAI VAT application dashboard
    Flow: Click Consumption Tax → Locate DTAI section → Click DTAI VAT app
    
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
    6. Click DTAI VAT app
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
        logger.info("On DTAI dashboard, navigating back to home")
        page.locator("role=tab[name='Home' i]").click()
        page.wait_for_timeout(2000)
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
# COMMON CONTEXT FIXTURE
# ==========================================

@pytest.fixture()
def vat_context() -> Dict[str, Any]:
    """
    Shared context for storing test state across steps
    Use this fixture in all VAT DTAI test modules
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


@when("I navigate to VAT DTAI application")
def step_navigate_to_vat_dtai(get_page: Page, vat_context: Dict):
    """
    Navigate to VAT DTAI application by clicking through:
    - Consumption Tax category
    - Digital Tax Administration Insights - VAT app
    """
    launch_page = vat_context.get("launch_page")
    if not launch_page:
        # Fallback if launch_page not in context
        print("WARNING: launch_page not in context, creating new instance")
        launch_page = LaunchAppPage(get_page)
        vat_context["launch_page"] = launch_page
    
    perform_dtai_navigation(get_page, launch_page)


@when("User clicks the DTAI VAT tile")
def step_click_dtai_tile(get_page: Page, vat_context: Dict):
    """Click the DTAI VAT tile to launch the application"""
    step_navigate_to_vat_dtai(get_page, vat_context)


@given("I click OK on the application popup")
@when("I click OK on the application popup")
def step_dismiss_application_popup(get_page: Page):
    """Dismiss the analytics/alert popup that appears on the DTAI dashboard after navigation.
    The popup takes ~4-5 seconds to appear after navigation, so we wait up to 8 seconds.
    Falls back to a page-wide OK button search if the overlay locator is not found.
    """
    # Allow time for the popup to appear after DTAI navigation
    get_page.wait_for_timeout(3000)

    # Attempt 1: look for the customAlertoverlay container (up to 8s)
    try:
        overlay = get_page.locator("div.customAlertoverlay").first
        overlay.wait_for(state="visible", timeout=8000)
        logger.info(f"[WHEN] Analytics popup overlay detected")
        for btn_sel in [
            "button:has-text('OK')",
            "button:has-text('Ok')",
            "button.btn-default",
            "button",
        ]:
            btn = overlay.locator(btn_sel).first
            try:
                if btn.count() > 0 and btn.is_visible(timeout=1000):
                    btn.click()
                    logger.info(f"[OK] Clicked overlay button: '{btn.inner_text().strip()}'")
                    get_page.wait_for_timeout(1500)
                    return
            except Exception:
                continue
        # If no button found inside overlay, remove it via JS
        logger.warning("[WARNING] Overlay found but no button - removing via JS")
        get_page.evaluate("(el) => el.remove()", overlay.element_handle())
        get_page.wait_for_timeout(500)
        return
    except Exception:
        pass

    # Attempt 2: page-wide fallback – look for any visible OK / btn-default button
    try:
        for sel in [
            "button.btn-default:has-text('OK')",
            "button.btn-default:has-text('Ok')",
            "button:has-text('OK'):visible",
        ]:
            btn = get_page.locator(sel).first
            if btn.count() > 0 and btn.is_visible(timeout=1000):
                btn.click()
                logger.info(f"[OK] Clicked page-level OK button via: {sel}")
                get_page.wait_for_timeout(1500)
                return
    except Exception:
        pass

    logger.info("[OK] No analytics popup detected - continuing")


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


@when("I navigate to VAT DTAI application")
def step_navigate_to_vat_dtai(get_page: Page, vat_context: Dict):
    """
    Navigate to VAT DTAI application by clicking through:
    - Consumption Tax category
    - Digital Tax Administration Insights - VAT app
    """
    launch_page = vat_context.get("launch_page")
    if not launch_page:
        # Fallback if launch_page not in context
        print("WARNING: launch_page not in context, creating new instance")
        launch_page = LaunchAppPage(get_page)
        vat_context["launch_page"] = launch_page
    
    perform_dtai_navigation(get_page, launch_page)


@when("User clicks the DTAI VAT tile")
def step_click_dtai_tile(get_page: Page, vat_context: Dict):
    """Click the DTAI VAT tile to launch the application"""
    step_navigate_to_vat_dtai(get_page, vat_context)
