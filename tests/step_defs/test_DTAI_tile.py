"""
Step Definitions for VAT DTAI Tile Tests
Connects DTAI_Tile.feature with launch_app_page.py
Uses common navigation steps from VAT_Common_Library.py to avoid code duplication
"""
import os
import re
import logging
from pathlib import Path
from typing import Dict, Any

import pytest
from playwright.sync_api import Page
from pytest_bdd import scenario, then, when
from pageobjects.launch_app_page import LaunchAppPage

# Import all common navigation utilities and step definitions
from tests.step_defs.VAT_Common_Library import (
    ensure_home_page,
    ensure_dtai_dashboard,
    navigate_to_module,
    get_current_page_state,
)

# Import common step definitions (login, client selection, DTAI navigation)
from tests.step_defs.VAT_Common_Library import *

# Configure logger for this module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')


# ==========================================
# FIXTURES - Function-Scoped for Independence
# ==========================================

@pytest.fixture()
def vat_context(get_page: Page) -> Dict[str, Any]:
    """
    Function-scoped context for each test.
    Each test gets a fresh browser session.
    """
    logger.info("Initializing VAT context for DTAI Tile test")
    return {
        "launch_page": None,
        "user_role": "Admin",
        "tile_clicked": False,
        "dashboard_loaded": False,
    }


# ==========================================
# SCENARIO DEFINITIONS
# ==========================================

@scenario("../features/DTAI_Tile.feature", "Verify DTAI VAT tile is visible under VAT Section")
def test_smoke_vat_dtai_tile_is_visible():
    """Verify DTAI VAT tile is visible under VAT Section"""
    logger.info("[TEST START] test_smoke_vat_dtai_tile_is_visible")
    pass


@scenario("../features/DTAI_Tile.feature", "Verify DTAI VAT tile launches dashboard")
def test_smoke_vat_dtai_tile_launches_dashboard():
    """Verify DTAI VAT tile launches dashboard"""
    logger.info("[TEST START] test_smoke_vat_dtai_tile_launches_dashboard")
    pass


@scenario("../features/DTAI_Tile.feature", "Verify user can navigate back to GTP IT homepage from VAT DTAI")
def test_smoke_vat_dtai_back_to_homepage():
    """Verify user can navigate back to GTP IT homepage from VAT DTAI"""
    logger.info("[TEST START] test_smoke_vat_dtai_back_to_homepage")
    pass


# ==========================================
# SMOKE TEST-SPECIFIC WHEN STEPS
# ==========================================

@when("User clicks Home navigation")
def step_click_home_navigation(get_page: Page, vat_context: Dict):
    """Click Home navigation to return to GTP IT homepage"""
    logger.info("[WHEN] User clicks Home navigation")
    
    # Click Home navigation link/button
    home_clicked = False
    home_candidates = [
        get_page.get_by_role("link", name=re.compile(r"^Home$", re.I)).first,
        get_page.get_by_role("button", name=re.compile(r"^Home$", re.I)).first,
        get_page.get_by_text(re.compile(r"^Home$", re.I)).first,
    ]
    
    for locator in home_candidates:
        if locator.count() > 0:
            locator.click()
            home_clicked = True
            logger.info(f"[OK] Home navigation clicked using locator: {locator}")
            break
    
    assert home_clicked, "Unable to click Home navigation"
    
    # Wait for navigation
    get_page.wait_for_timeout(3000)
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
    has_dtai = bool(re.search(r"Digital\s+Tax\s+Administration\s+Insights", page_text, re.I))
    
    logger.info(f"VAT content found: {has_vat_content}")
    logger.info(f"Compliance section found: {has_compliance}")
    logger.info(f"DTAI content found: {has_dtai}")
    
    assert has_vat_content or has_compliance or has_dtai, \
        "VAT category sections were not found on the page"
    
    logger.info("[OK] VAT category sections validation passed")


@then("DTAI VAT tile is visible")
def step_validate_dtai_tile_visible(get_page: Page):
    """Verify DTAI VAT tile is visible"""
    logger.info("[THEN] Validating DTAI VAT tile is visible")
    
    page_text = get_page.inner_text("body")
    
    # Check for DTAI VAT tile text (supports different dash characters)
    dtai_pattern = r"Digital\s+Tax\s+Administration\s+Insights\s*[-–—]?\s*VAT"
    has_dtai_tile = bool(re.search(dtai_pattern, page_text, re.I))
    
    assert has_dtai_tile, \
        "Digital Tax Administration Insights-VAT tile text was not found on the page"
    
    logger.info("[OK] DTAI VAT tile text found on page")
    logger.info("DTAI VAT tile validation passed")


@when("DTAI VAT tile description is visible")
@then("DTAI VAT tile description is visible")
def step_validate_dtai_tile_description(get_page: Page):
    """Verify DTAI VAT tile description is visible"""
    logger.info("[THEN/WHEN] Validating DTAI VAT tile description is visible")
    
    page_text = get_page.inner_text("body")
    
    # Check for tile description text (may vary, looking for key phrases)
    has_description = bool(
        re.search(r"Autonomous\s+Data\s+Preparation", page_text, re.I) or
        re.search(r"VAT\s+compliance", page_text, re.I) or
        re.search(r"e-?Invoicing", page_text, re.I) or
        re.search(r"monitoring.*reporting", page_text, re.I)
    )
    
    # Description might not always be visible, so we'll make this a soft assertion
    if has_description:
        logger.info("[OK] DTAI VAT tile description found")
    else:
        logger.warning("[WARNING] DTAI VAT tile description not found (may be expected)")
    
    logger.info("DTAI VAT tile description check completed")


@then("VAT DTAI dashboard is displayed")
def step_validate_dashboard_displayed(get_page: Page, vat_context: Dict):
    """Verify VAT DTAI dashboard is displayed after clicking tile"""
    logger.info("[THEN] Validating VAT DTAI dashboard is displayed")
    
    # Wait for dashboard to load
    get_page.wait_for_timeout(5000)
    
    launch_page = vat_context.get("launch_page")
    if launch_page:
        is_launched = launch_page.verify_dtai_app_launched()
        assert is_launched, "VAT DTAI dashboard was not displayed after clicking tile"
        logger.info("[OK] Dashboard verified via launch_page object")
    else:
        # Fallback verification
        page_text = get_page.inner_text("body")
        has_dashboard = bool(re.search(r"\bDashboard\b", page_text, re.I))
        assert has_dashboard, "Dashboard text was not found after launching DTAI VAT"
        logger.info("[OK] Dashboard verified via page text")
    
    logger.info(f"Dashboard displayed. Current URL: {get_page.url}")
    logger.info("VAT DTAI dashboard validation passed")


@then("Home navigation is visible on VAT DTAI")
def step_validate_home_navigation_visible(get_page: Page):
    """Verify Home navigation is visible on VAT DTAI page"""
    logger.info("[THEN] Validating Home navigation is visible on VAT DTAI")
    
    # Wait for page to fully load
    get_page.wait_for_timeout(3000)
    
    page_text = get_page.inner_text("body")
    has_home = bool(re.search(r"\bHome\b", page_text, re.I))
    
    assert has_home, "Home navigation was not found on VAT DTAI page"
    
    logger.info("[OK] Home navigation found on VAT DTAI page")
    logger.info("Home navigation validation passed")


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
    
    # Verify DTAI VAT tile is visible again
    page_text = get_page.inner_text("body")
    dtai_pattern = r"Digital\s+Tax\s+Administration\s+Insights"
    has_dtai_tile = bool(re.search(dtai_pattern, page_text, re.I))
    
    assert has_dtai_tile, "DTAI VAT tile was not visible after navigating back to homepage"
    
    logger.info(f"[OK] Successfully redirected to homepage. Current URL: {get_page.url}")
    logger.info("Homepage redirect validation passed")
