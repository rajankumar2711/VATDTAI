"""Step definitions for the VAT DTAI Detect and Suggest module (UAT only).

Binds DetectSuggest.feature to DetectSuggestPage. The whole feature is tagged
@uat_only, so conftest auto-skips it outside --env uat; a capability check on
HAS_POWERBI_DASHBOARD guards the case where UAT itself has PowerBI disabled.

Reuses the shared authenticated session and the common login/client/navigation
steps (wildcard import) exactly like the Dashboard module test module.
"""
import logging
from typing import Dict, Any

import pytest
from playwright.sync_api import Page
from pytest_bdd import scenario, when, then, parsers

from pageobjects.detect_suggest_page import DetectSuggestPage
from tests.step_defs.VAT_Common_Library import env_has_powerbi_dashboard
from tests.step_defs.VAT_Common_Library import *  # noqa: F401,F403 (registers common Background steps)

logger = logging.getLogger(__name__)


# ==========================================
# FIXTURES
# ==========================================
@pytest.fixture()
def get_page(vat_session) -> Page:
    """Reuse the single session-scoped authenticated page (Option B)."""
    return vat_session["page"]


@pytest.fixture()
def vat_context(get_page: Page) -> Dict[str, Any]:
    return {"launch_page": None, "user_role": "Admin", "detect": None}


def _detect(get_page: Page, vat_context: Dict) -> DetectSuggestPage:
    det = vat_context.get("detect")
    if det is None:
        det = DetectSuggestPage(get_page)
        vat_context["detect"] = det
    return det


# ==========================================
# SCENARIO BINDINGS
# ==========================================
@scenario("../features/DetectSuggest.feature", "PowerBI report is displayed on the Detect and Suggest tab")
def test_detect_report_displayed():
    pass


@scenario("../features/DetectSuggest.feature", "Detect and Suggest KPI metrics are displayed appropriately")
def test_detect_metrics():
    pass


@scenario("../features/DetectSuggest.feature", "Drill sources expose drill-through to all their invoice report pages")
def test_detect_drill_targets():
    pass


@scenario("../features/DetectSuggest.feature", "Drill-through navigates to the target report page and back")
def test_detect_drill_through():
    pass


# ==========================================
# BACKGROUND (module-specific)
# ==========================================
@then("the Detect and Suggest report is loaded")
def step_detect_loaded(get_page: Page, vat_context: Dict):
    if not env_has_powerbi_dashboard():
        pytest.skip("PowerBI is not configured in this environment (HAS_POWERBI_DASHBOARD=false)")
    det = _detect(get_page, vat_context)
    dismiss_application_popup(get_page)  # noqa: F405 (from common library)
    det.open_detect_suggest_tab()
    loaded = det.wait_until_loaded()
    assert loaded, "Detect and Suggest PowerBI report did not finish loading on the tab"
    logger.info("[detect] loaded and rendered")


# ==========================================
# THEN STEPS - presence / visuals
# ==========================================
@then("the Detect and Suggest PowerBI report is present")
def step_report_present(get_page: Page, vat_context: Dict):
    det = _detect(get_page, vat_context)
    assert det.is_powerbi_report_present(), "Detect and Suggest PowerBI report iframe was not found"
    logger.info("[detect] PowerBI iframe present")


@then("all Detect and Suggest visuals are displayed")
def step_visuals_displayed(get_page: Page, vat_context: Dict):
    det = _detect(get_page, vat_context)
    missing = det.missing_visuals()
    assert not missing, f"Expected Detect and Suggest visuals were not found: {missing}"
    logger.info(f"[detect] all {len(det.EXPECTED_VISUALS)} expected visuals present")


# ==========================================
# THEN STEPS - metrics
# ==========================================
@then("the Invoices metric shows a numeric value")
def step_invoices_numeric(get_page: Page, vat_context: Dict):
    det = _detect(get_page, vat_context)
    metrics = det.read_metrics()
    vat_context["metrics"] = metrics
    val = metrics.get("invoices")
    assert val is not None, "Invoices metric was not found on the Detect and Suggest report"
    assert int(val.replace(",", "")) >= 0, f"Invoices is not a valid number: {val}"
    logger.info(f"[detect] Invoices = {val}")


@then("the Accepted, Overridden and Rejected cards show valid percentages with counts")
def step_outcome_cards_valid(get_page: Page, vat_context: Dict):
    det = _detect(get_page, vat_context)
    metrics = vat_context.get("metrics") or det.read_metrics()
    problems = []
    for label in det.OUTCOME_CARDS:
        card = metrics.get(label.lower()) or {}
        pct, count = card.get("pct"), card.get("count")
        if pct is None:
            problems.append(f"{label}: percentage missing")
        else:
            p = float(pct.replace("%", "").strip())
            if not (0.0 <= p <= 100.0):
                problems.append(f"{label}: percentage out of range ({pct})")
        if count is None or not count.isdigit():
            problems.append(f"{label}: count missing or non-numeric ({count})")
    assert not problems, f"Detect and Suggest KPI cards invalid: {problems}"
    logger.info("[detect] Accepted/Overridden/Rejected cards show valid percentages with counts")


# ==========================================
# DRILL-THROUGH
# ==========================================
@then(parsers.parse('the "{source}" offers drill-through to all its invoice report pages'))
def step_source_offers_targets(get_page: Page, vat_context: Dict, source: str):
    det = _detect(get_page, vat_context)
    missing = det.missing_drill_targets(source)
    assert not missing, f"Drill source '{source}' does not offer drill-through to: {missing}"
    logger.info(f"[detect] '{source}' offers drill-through to all its invoice report pages")


@when(parsers.parse('I drill through the "{source}" to "{target}"'))
def step_drill_through(get_page: Page, vat_context: Dict, source: str, target: str):
    det = _detect(get_page, vat_context)
    ok = det.drill_through(target, source=source)
    vat_context["drill_ok"] = ok
    assert ok, f"Drill-through from '{source}' to '{target}' could not be performed"


@then(parsers.parse('the "{target}" report page is displayed'))
def step_on_target_page(get_page: Page, vat_context: Dict, target: str):
    det = _detect(get_page, vat_context)
    get_page.wait_for_timeout(2000)
    assert det.is_on_report_page(target), f"'{target}' report page was not displayed after drill-through"
    logger.info(f"[detect] drill-through landed on '{target}'")


@when("I click the back button")
def step_click_back(get_page: Page, vat_context: Dict):
    det = _detect(get_page, vat_context)
    ok = det.go_back()
    assert ok, "Back button could not be clicked to return to the Detect and Suggest report"


@then("the Detect and Suggest page is displayed again")
def step_back_on_report(get_page: Page, vat_context: Dict):
    det = _detect(get_page, vat_context)
    get_page.wait_for_timeout(2000)
    assert det.wait_until_loaded(timeout_ms=60000), "Detect and Suggest did not re-render after going back"
    logger.info("[detect] returned to Detect and Suggest via back button")
