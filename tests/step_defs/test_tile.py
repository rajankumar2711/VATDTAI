"""
Step Definitions for VAT Tile Tests
Connects Vat_tile.feature with launch_app_page.py
Uses common navigation steps from VAT_Common_Library.py to avoid code duplication
"""
import re
import logging
from typing import Dict, Any

import pytest
from playwright.sync_api import Page
from pytest_bdd import scenario, then, when

# ensure_home_page is called directly below; the wildcard import registers the common
# Background step definitions (login, client selection, DTAI navigation, popup dismissal).
from tests.step_defs.VAT_Common_Library import ensure_home_page
from tests.step_defs.VAT_Common_Library import *

# Configure logger for this module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')


# ==========================================
# FIXTURES - Function-Scoped for Independence
# ==========================================

@pytest.fixture()
def get_page(vat_session) -> Page:
    """[Option B] Reuse the single session-scoped authenticated page across all VAT Tile
    scenarios, so login + client selection + DTAI navigation happen only once for the run.
    Overrides the function-scoped get_page from conftest for this module only."""
    return vat_session["page"]


@pytest.fixture()
def vat_context(get_page: Page) -> Dict[str, Any]:
    """Per-scenario state. The browser session itself is shared (see get_page override);
    only this lightweight context is recreated for each scenario."""
    logger.info("Initializing VAT context for VAT Tile test")
    return {
        "launch_page": None,
        "user_role": "Admin",
    }


# ==========================================
# SCENARIO DEFINITIONS
# ==========================================

@scenario("../features/Vat_tile.feature", "Verify Global Insights And Data Enrichment For e-Invoicing tile is visible under VAT Section")
def test_smoke_vat_dtai_tile_is_visible():
    """Verify Global Insights And Data Enrichment For e-Invoicing tile is visible under VAT Section"""
    logger.info("[TEST START] test_smoke_vat_dtai_tile_is_visible")
    pass


@scenario("../features/Vat_tile.feature", "Verify Global Insights And Data Enrichment For e-Invoicing tile launches dashboard")
def test_smoke_vat_dtai_tile_launches_dashboard():
    """Verify Global Insights And Data Enrichment For e-Invoicing tile launches dashboard"""
    logger.info("[TEST START] test_smoke_vat_dtai_tile_launches_dashboard")
    pass


@scenario("../features/Vat_tile.feature", "Verify user can navigate back to GTP IT homepage from Global Insights And Data Enrichment For e-Invoicing")
def test_smoke_vat_dtai_back_to_homepage():
    """Verify user can navigate back to GTP IT homepage from Global Insights And Data Enrichment For e-Invoicing"""
    logger.info("[TEST START] test_smoke_vat_dtai_back_to_homepage")
    pass


# ==========================================
# SMOKE TEST-SPECIFIC WHEN STEPS
# ==========================================

@when("User clicks Home navigation")
def step_click_home_navigation(get_page: Page, vat_context: Dict):
    """Dismiss any application popup, then navigate back to the GTP IT home page.

    After launching the DTAI tile an analytics popup (modal-scrollable overlay) can appear
    and intercept pointer events, so it must be dismissed before clicking Home. Reuses the
    shared ensure_home_page helper for robust dashboard->home navigation."""
    logger.info("[WHEN] User clicks Home navigation")

    dismiss_application_popup(get_page)
    launch_page = ensure_home_page(get_page, vat_context.get("launch_page"))
    vat_context["launch_page"] = launch_page

    get_page.wait_for_timeout(2000)
    logger.info(f"[OK] Navigation complete. Current URL: {get_page.url}")
    logger.info("Home navigation click completed")


# ==========================================
# THEN STEPS (Assertions)
# ==========================================

@then("VAT category sections are visible")
def step_validate_vat_category_sections(get_page: Page):
    """Verify VAT category sections are visible on the home page"""
    logger.info("[THEN] Validating VAT category sections are visible")
    
    page_text = get_page.inner_text("body")
    
    # Check for VAT-related content (could be VAT section, Compliance section, etc.)
    has_vat_content = bool(re.search(r"\bVAT\b", page_text, re.I))
    has_compliance = bool(re.search(r"\bCompliance\b", page_text, re.I))
    has_dtai = bool(re.search(r"Global\s+Insights\s+And\s+Data\s+Enrichment\s+For\s+e-?Invoicing", page_text, re.I))
    
    logger.info(f"VAT content found: {has_vat_content}")
    logger.info(f"Compliance section found: {has_compliance}")
    logger.info(f"App tile content found: {has_dtai}")
    
    assert has_vat_content or has_compliance or has_dtai, \
        "VAT category sections were not found on the page"
    
    logger.info("[OK] VAT category sections validation passed")


@then("Global Insights And Data Enrichment For e-Invoicing tile is visible")
def step_validate_dtai_tile_visible(get_page: Page):
    """Verify Global Insights And Data Enrichment For e-Invoicing tile is visible"""
    logger.info("[THEN] Validating Global Insights And Data Enrichment For e-Invoicing tile is visible")
    
    page_text = get_page.inner_text("body")
    
    # Check for the "Global Insights And Data Enrichment For e-Invoicing" tile text
    dtai_pattern = r"Global\s+Insights\s+And\s+Data\s+Enrichment\s+For\s+e-?Invoicing"
    has_dtai_tile = bool(re.search(dtai_pattern, page_text, re.I))
    
    assert has_dtai_tile, \
        "Global Insights And Data Enrichment For e-Invoicing tile text was not found on the page"
    
    logger.info("[OK] Global Insights And Data Enrichment For e-Invoicing tile text found on page")
    logger.info("Global Insights And Data Enrichment For e-Invoicing tile validation passed")


@when("Global Insights And Data Enrichment For e-Invoicing tile description is visible")
@then("Global Insights And Data Enrichment For e-Invoicing tile description is visible")
def step_validate_dtai_tile_description(get_page: Page):
    """Verify Global Insights And Data Enrichment For e-Invoicing tile description is visible"""
    logger.info("[THEN/WHEN] Validating Global Insights And Data Enrichment For e-Invoicing tile description is visible")
    
    page_text = get_page.inner_text("body")
    
    # Check for tile description text (may vary, looking for key phrases)
    has_description = bool(
        re.search(r"Autonomous\s+Data\s+Preparation", page_text, re.I) or
        re.search(r"VAT\s+compliance", page_text, re.I) or
        re.search(r"e-?Invoicing", page_text, re.I) or
        re.search(r"monitoring.*reporting", page_text, re.I)
    )
    
    assert has_description, (
        "Global Insights And Data Enrichment For e-Invoicing tile description was not found on the page (expected phrasing about "
        "Autonomous Data Preparation / VAT compliance / e-Invoicing / monitoring & reporting)"
    )
    logger.info("[OK] Global Insights And Data Enrichment For e-Invoicing tile description found")
    logger.info("Global Insights And Data Enrichment For e-Invoicing tile description check completed")


@then("Global Insights And Data Enrichment For e-Invoicing dashboard is displayed")
def step_validate_dashboard_displayed(get_page: Page, vat_context: Dict):
    """Verify Global Insights And Data Enrichment For e-Invoicing dashboard is displayed after clicking tile"""
    logger.info("[THEN] Validating Global Insights And Data Enrichment For e-Invoicing dashboard is displayed")
    
    # Wait for dashboard to load
    get_page.wait_for_timeout(5000)
    
    launch_page = vat_context.get("launch_page")
    if launch_page:
        is_launched = launch_page.verify_dtai_app_launched()
        assert is_launched, "Global Insights And Data Enrichment For e-Invoicing dashboard was not displayed after clicking tile"
        logger.info("[OK] Dashboard verified via launch_page object")
    else:
        # Fallback verification
        page_text = get_page.inner_text("body")
        has_dashboard = bool(re.search(r"\bDashboard\b", page_text, re.I))
        assert has_dashboard, "Dashboard text was not found after launching Global Insights And Data Enrichment For e-Invoicing"
        logger.info("[OK] Dashboard verified via page text")
    
    logger.info(f"Dashboard displayed. Current URL: {get_page.url}")
    logger.info("Global Insights And Data Enrichment For e-Invoicing dashboard validation passed")


@then("User is redirected to GTP IT homepage without re-authentication")
def step_validate_redirected_to_homepage(get_page: Page):
    """Verify user is redirected to GTP IT homepage without re-authentication"""
    logger.info("[THEN] Validating user is redirected to GTP IT homepage without re-authentication")
    
    # Wait for navigation to complete
    get_page.wait_for_timeout(5000)
    
    # Import helper to check page state
    from tests.step_defs.VAT_Common_Library import wait_for_ready_state
    
    # Check that we're back on home page (not login page)
    logger.info("Checking page state after navigation...")
    state = wait_for_ready_state(get_page, timeout_ms=30000)
    logger.info(f"Page state detected: {state}")
    
    assert state != "login", "User was asked to re-authenticate (should not happen)"
    assert state == "home", "User was not redirected to GTP IT homepage"
    
    # Verify the app tile is visible again
    page_text = get_page.inner_text("body")
    dtai_pattern = r"Global\s+Insights\s+And\s+Data\s+Enrichment\s+For\s+e-?Invoicing"
    has_dtai_tile = bool(re.search(dtai_pattern, page_text, re.I))
    
    assert has_dtai_tile, "Global Insights And Data Enrichment For e-Invoicing tile was not visible after navigating back to homepage"
    
    logger.info(f"[OK] Successfully redirected to homepage. Current URL: {get_page.url}")
    logger.info("Homepage redirect validation passed")
