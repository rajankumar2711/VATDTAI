"""Step definitions for the VAT DTAI PowerBI Dashboard (UAT only).

Binds Dashboard.feature to DashboardPage. The whole feature is tagged @uat_only,
so conftest auto-skips it outside --env uat; a capability check on
HAS_POWERBI_DASHBOARD guards the case where UAT itself has PowerBI disabled.

Reuses the shared authenticated session and the common login/client/navigation
steps (wildcard import) exactly like the other module test modules.
"""
import logging
from typing import Dict, Any

import pytest
from playwright.sync_api import Page
from pytest_bdd import scenario, when, then, parsers

from pageobjects.dashboard_page import DashboardPage
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
    return {"launch_page": None, "user_role": "Admin", "dashboard": None}


def _dashboard(get_page: Page, vat_context: Dict) -> DashboardPage:
    dash = vat_context.get("dashboard")
    if dash is None:
        dash = DashboardPage(get_page)
        vat_context["dashboard"] = dash
    return dash


# ==========================================
# SCENARIO BINDINGS
# ==========================================
@scenario("../features/Dashboard.feature", "PowerBI dashboard report is displayed on the Dashboards tab")
def test_dashboard_report_displayed():
    pass


@scenario("../features/Dashboard.feature", "All dashboard metrics are displayed appropriately")
def test_dashboard_metrics():
    pass


@scenario("../features/Dashboard.feature", "Operational cards expose drill-through to all invoice report pages")
def test_dashboard_drill_targets():
    pass


@scenario("../features/Dashboard.feature", "Card drill-through navigates to the target report page and back")
def test_dashboard_drill_through():
    pass


# ==========================================
# BACKGROUND (dashboard-specific)
# ==========================================
@then("the VAT DTAI dashboard is loaded")
def step_dashboard_loaded(get_page: Page, vat_context: Dict):
    if not env_has_powerbi_dashboard():
        pytest.skip("PowerBI dashboard is not configured in this environment (HAS_POWERBI_DASHBOARD=false)")
    dash = _dashboard(get_page, vat_context)
    dismiss_application_popup(get_page)  # noqa: F405 (from common library)
    dash.open_dashboards_tab()
    loaded = dash.wait_until_loaded()
    assert loaded, "PowerBI dashboard did not finish loading on the Dashboards tab"
    logger.info("[dashboard] loaded and rendered")


# ==========================================
# THEN STEPS - presence / visuals
# ==========================================
@then("the PowerBI report is present")
def step_report_present(get_page: Page, vat_context: Dict):
    dash = _dashboard(get_page, vat_context)
    assert dash.is_powerbi_report_present(), "PowerBI report iframe was not found on the dashboard"
    logger.info("[dashboard] PowerBI iframe present")


@then("all dashboard visuals are displayed")
def step_visuals_displayed(get_page: Page, vat_context: Dict):
    dash = _dashboard(get_page, vat_context)
    titles_blob = " | ".join(dash.visual_titles()).lower()
    text_blob = dash.dashboard_text().lower()
    missing = []
    for name in dash.EXPECTED_VISUALS:
        n = name.lower()
        if n not in titles_blob and n not in text_blob:
            missing.append(name)
    assert not missing, f"Expected dashboard visuals were not found: {missing}"
    logger.info(f"[dashboard] all {len(dash.EXPECTED_VISUALS)} expected visuals present")


# ==========================================
# THEN STEPS - metrics
# ==========================================
@then("the Total Invoices metric shows a numeric value")
def step_total_invoices(get_page: Page, vat_context: Dict):
    dash = _dashboard(get_page, vat_context)
    metrics = dash.read_metrics()
    vat_context["metrics"] = metrics
    val = metrics.get("total_invoices")
    assert val is not None, "Total Invoices metric was not found on the dashboard"
    assert int(val.replace(",", "")) >= 0, f"Total Invoices is not a valid number: {val}"
    logger.info(f"[dashboard] Total Invoices = {val}")


@then("the Success Rate metric shows a percentage value")
def step_success_rate(get_page: Page, vat_context: Dict):
    dash = _dashboard(get_page, vat_context)
    metrics = vat_context.get("metrics") or dash.read_metrics()
    val = metrics.get("success_rate")
    assert val is not None, "Success Rate metric was not found on the dashboard"
    pct = float(val.replace("%", "").strip())
    assert 0.0 <= pct <= 100.0, f"Success Rate out of range: {val}"
    logger.info(f"[dashboard] Success Rate = {val}")


@then("the operational status breakdown reconciles with Total Invoices")
def step_status_reconciles(get_page: Page, vat_context: Dict):
    dash = _dashboard(get_page, vat_context)
    metrics = vat_context.get("metrics") or dash.read_metrics()
    breakdown = metrics.get("status_breakdown") or {}
    assert breakdown, "By Operational Status breakdown could not be read from its visual"
    breakdown_sum = sum(int(v) for v in breakdown.values())
    total = metrics.get("total_invoices")
    assert total is not None, "Total Invoices missing for reconciliation"
    total_n = int(total.replace(",", ""))
    assert breakdown_sum == total_n, \
        f"Operational status breakdown {breakdown} (sum {breakdown_sum}) != Total Invoices {total_n}"
    logger.info(f"[dashboard] status breakdown {breakdown} reconciles with Total Invoices {total_n}")


# ==========================================
# DRILL-THROUGH
# ==========================================
@then(parsers.parse('the "{card}" card offers drill-through to all invoice report pages'))
def step_card_offers_targets(get_page: Page, vat_context: Dict, card: str):
    dash = _dashboard(get_page, vat_context)
    missing = dash.missing_drill_targets(card)
    assert not missing, f"Card '{card}' does not offer drill-through to: {missing}"
    logger.info(f"[dashboard] '{card}' offers drill-through to all invoice report pages")


@when(parsers.parse('I drill through the "{card}" card to "{target}"'))
def step_drill_through(get_page: Page, vat_context: Dict, card: str, target: str):
    dash = _dashboard(get_page, vat_context)
    ok = dash.drill_through(target, card=card)
    vat_context["drill_ok"] = ok
    assert ok, f"Drill-through from '{card}' to '{target}' could not be performed"


@then(parsers.parse('the "{target}" report page is displayed'))
def step_on_target_page(get_page: Page, vat_context: Dict, target: str):
    dash = _dashboard(get_page, vat_context)
    get_page.wait_for_timeout(2000)
    assert dash.is_on_report_page(target), f"'{target}' report page was not displayed after drill-through"
    logger.info(f"[dashboard] drill-through landed on '{target}'")


@when("I click the back button")
def step_click_back(get_page: Page, vat_context: Dict):
    dash = _dashboard(get_page, vat_context)
    ok = dash.go_back()
    assert ok, "Back button could not be clicked to return to the dashboard"


@then("the dashboard page is displayed again")
def step_back_on_dashboard(get_page: Page, vat_context: Dict):
    dash = _dashboard(get_page, vat_context)
    get_page.wait_for_timeout(2000)
    assert dash.wait_until_loaded(timeout_ms=60000), "Dashboard did not re-render after going back"
    logger.info("[dashboard] returned to dashboard via back button")
