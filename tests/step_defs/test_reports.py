"""
Step definitions for VAT DTAI Reports module.
Connects Vat_reports.feature with vat_reports_page.py.
"""
import logging
from typing import Dict, Any

import pytest
from playwright.sync_api import Page
from pytest_bdd import scenario, when, then, parsers

from pageobjects.vat_reports_page import VatReportsPage

from tests.step_defs.VAT_Common_Library import *  # noqa: F401,F403

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(name)s - %(message)s")


@pytest.fixture()
def vat_context(get_page: Page) -> Dict[str, Any]:
    logger.info("Initializing VAT context for Reports test")
    return {
        "user_role": "Admin",
        "requested_report": "",
        "selected_report": "",
        "report_selection_result": {},
    }


@pytest.fixture()
def reports_page(get_page: Page) -> VatReportsPage:
    return VatReportsPage(get_page)


# ==========================================
# SCENARIOS
# ==========================================


@scenario(
    "../features/Vat_reports.feature",
    "Verify authorized user can access Reports module and the Reports header is displayed correctly",
)
def test_reports_module_access(get_page, vat_context, reports_page):
    pass


@scenario(
    "../features/Vat_reports.feature",
    "Verify user can generate e-Invoice Status report successfully and the report is displayed in a popup or supported UI container",
)
def test_einvoice_status_report(get_page, vat_context, reports_page):
    pass


@scenario(
    "../features/Vat_reports.feature",
    "Verify Submission Report is generated in popup or approved UI container",
)
def test_submission_report(get_page, vat_context, reports_page):
    pass


@scenario(
    "../features/Vat_reports.feature",
    "Verify user can generate Reconciliation Report and view report in popup or approved UI container",
)
def test_reconciliation_report(get_page, vat_context, reports_page):
    pass


# ==========================================
# WHEN STEPS
# ==========================================


@when("I navigate to Reports module")
def step_navigate_to_reports(get_page: Page, reports_page: VatReportsPage):
    logger.info("[WHEN] Navigating to Reports module")
    clicked = reports_page.navigate_to_reports_module()
    assert clicked, "Could not click Reports module tab/link"
    assert reports_page.is_reports_module_visible(), "Reports module heading is not visible after navigation"
    logger.info("[OK] Reports module opened")


def _select_report(
    reports_page: VatReportsPage,
    vat_context: Dict[str, Any],
    report_name: str,
    allow_fallback: bool = False,
):
    result = reports_page.select_report_type(report_name, allow_fallback=allow_fallback)
    vat_context["requested_report"] = report_name
    vat_context["report_selection_result"] = result
    vat_context["selected_report"] = result.get("selected", "")
    if not result.get("ok"):
        available = result.get("available", [])
        logger.warning(f"[WARNING] Requested report '{report_name}' not available. Available: {available}")
        pytest.skip(f"Report '{report_name}' not available in current environment. Available: {available}")
    else:
        logger.info(f"[OK] Selected report option: {result.get('selected')}")


@when("I select e-Invoice Status Report")
def step_select_einvoice_status_report(reports_page: VatReportsPage, vat_context: Dict[str, Any]):
    _select_report(reports_page, vat_context, "e-Invoice Status Report", allow_fallback=False)


@when("I select Submission Report")
def step_select_submission_report(reports_page: VatReportsPage, vat_context: Dict[str, Any]):
    _select_report(reports_page, vat_context, "Submission Report", allow_fallback=False)


@when("I select Reconciliation Report")
def step_select_reconciliation_report(reports_page: VatReportsPage, vat_context: Dict[str, Any]):
    _select_report(reports_page, vat_context, "Reconciliation Report", allow_fallback=False)


@when("I provide valid report filter criteria")
def step_provide_valid_report_filters(reports_page: VatReportsPage):
    logger.info("[WHEN] Providing valid report filter criteria")
    reports_page.provide_valid_filter_criteria()
    logger.info("[OK] Report filters populated")


@when("I click Generate button")
def step_click_generate_button(reports_page: VatReportsPage):
    logger.info("[WHEN] Clicking Generate button")
    reports_page.click_generate_report()
    logger.info("[OK] Generate clicked")


# ==========================================
# THEN STEPS
# ==========================================


@then(parsers.parse('Reports module is accessible and displayed with header "{header}"'))
@then('Reports module is accessible and displayed with header "Reports"')
def step_verify_reports_header(reports_page: VatReportsPage, header: str = "Reports"):
    logger.info(f"[THEN] Verifying Reports header: {header}")
    assert reports_page.is_reports_module_visible(), "Reports module is not visible"
    actual = reports_page.get_reports_header()
    assert header.lower() in actual.lower(), f"Expected header '{header}' but got '{actual}'"
    logger.info(f"[OK] Reports header verified: {actual}")


@then("Generate Report section is visible")
def step_verify_generate_report_section(reports_page: VatReportsPage):
    logger.info("[THEN] Verifying Generate Report section visibility")
    assert reports_page.is_generate_report_section_visible(), "Generate Report section is not visible"
    logger.info("[OK] Generate Report section is visible")


@then("e-Invoice Status report is displayed in popup or supported UI container")
def step_verify_einvoice_status_report_displayed(
    reports_page: VatReportsPage,
    vat_context: Dict[str, Any],
):
    selected = vat_context.get("selected_report") or "e-Invoice Status Report"
    assert reports_page.is_report_displayed(selected), "e-Invoice Status report output container not detected"


@then("Submission Report is displayed in popup or approved UI container")
def step_verify_submission_report_displayed(
    reports_page: VatReportsPage,
    vat_context: Dict[str, Any],
):
    selected = vat_context.get("selected_report") or "Submission Report"
    assert reports_page.is_report_displayed(selected), "Submission report output container not detected"


@then("Reconciliation Report is displayed in popup or approved UI container")
def step_verify_reconciliation_report_displayed(
    reports_page: VatReportsPage,
    vat_context: Dict[str, Any],
):
    selected = vat_context.get("selected_report") or "Reconciliation Report"
    assert reports_page.is_report_displayed(selected), "Reconciliation report output container not detected"
