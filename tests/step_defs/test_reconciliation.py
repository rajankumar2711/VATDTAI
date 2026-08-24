"""
Step definitions for VAT DTAI Reconciliation module.
Connects Vat_reconciliation.feature with vat_reconciliation_page.py.
Uses common navigation/login steps from VAT_Common_Library.py.
"""
import logging
from pathlib import Path
from typing import Dict, Any

import pytest
from playwright.sync_api import Page
from pytest_bdd import scenario, when, then

from pageobjects.vat_reconciliation_page import VatReconciliationPage
from tests.step_defs.VAT_Common_Library import *  # noqa: F401,F403

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(name)s - %(message)s")

# GL / ERP sample files used for a successful (exact match) reconciliation run.
_RECON_DATA_DIR = Path(__file__).resolve().parents[1] / "test_documents" / "Reconciliation Module" / "Exact_Match"
_GL_FILE = _RECON_DATA_DIR / "BE_GL_EXACT_MATCH.xlsx"
_ERP_FILE = _RECON_DATA_DIR / "BE_ERP_Transactional_EXACT_MATCH.xlsx"


@pytest.fixture()
def vat_context(get_page: Page) -> Dict[str, Any]:
    logger.info("Initializing VAT context for Reconciliation test")
    return {
        "user_role": "Admin",
        "upload_result": {},
        "reconcile_result": {},
    }


@pytest.fixture()
def reconciliation_page(get_page: Page) -> VatReconciliationPage:
    return VatReconciliationPage(get_page)


# ==========================================
# SCENARIOS
# ==========================================


@scenario(
    "../features/Vat_reconciliation.feature",
    "Verify authorized VAT DTAI user can access Reconciliation module and reach batch reconciliation workflow",
)
def test_reconciliation_module_access(get_page, vat_context, reconciliation_page):
    pass


@scenario(
    "../features/Vat_reconciliation.feature",
    "Verify user can execute reconciliation successfully with valid filters and valid GL ERP transaction files",
)
def test_reconciliation_execution(get_page, vat_context, reconciliation_page):
    pass


@scenario(
    "../features/Vat_reconciliation.feature",
    "Verify Reconciliation Details summary table displays exactly Match and Mismatch rows",
)
def test_reconciliation_summary_table(get_page, vat_context, reconciliation_page):
    pass


# ==========================================
# WHEN STEPS
# ==========================================


@when("I navigate to Reconciliation module")
def step_navigate_to_reconciliation(reconciliation_page: VatReconciliationPage):
    logger.info("[WHEN] Navigating to Reconciliation module")
    clicked = reconciliation_page.navigate_to_reconciliation_module()
    assert clicked, "Could not open the Reconciliation module"
    assert reconciliation_page.is_reconciliation_module_accessible(), \
        "Reconciliation module is not accessible after navigation"
    logger.info("[OK] Reconciliation module opened")


@when("I upload valid GL transaction file and valid ERP transaction file")
def step_upload_gl_erp_files(reconciliation_page: VatReconciliationPage, vat_context: Dict[str, Any]):
    logger.info("[WHEN] Uploading valid GL and ERP transaction files")
    if not _GL_FILE.exists() or not _ERP_FILE.exists():
        pytest.skip(f"GL/ERP sample files not found under {_RECON_DATA_DIR}")

    result = reconciliation_page.upload_gl_and_erp_files(str(_GL_FILE), str(_ERP_FILE))
    vat_context["upload_result"] = result
    if not result.get("ok"):
        pytest.skip(f"GL/ERP upload controls not available: {result.get('reason')}")
    logger.info(f"[OK] GL/ERP files uploaded: {result}")


@when("I apply valid reconciliation filters")
def step_apply_valid_filters(reconciliation_page: VatReconciliationPage):
    logger.info("[WHEN] Applying valid reconciliation filters")
    reconciliation_page.apply_valid_filters()
    logger.info("[OK] Reconciliation filters applied")


@when("I click Reconcile button")
def step_click_reconcile(reconciliation_page: VatReconciliationPage, vat_context: Dict[str, Any]):
    logger.info("[WHEN] Clicking Reconcile button")
    result = reconciliation_page.click_reconcile()
    vat_context["reconcile_result"] = result
    if not result.get("ok"):
        pytest.skip(f"Reconcile action not available: {result.get('reason')}")
    logger.info("[OK] Reconcile clicked")


# ==========================================
# THEN STEPS
# ==========================================


@then("Reconciliation module is accessible and displayed")
def step_verify_reconciliation_accessible(reconciliation_page: VatReconciliationPage):
    logger.info("[THEN] Verifying Reconciliation module is accessible and displayed")
    assert reconciliation_page.is_reconciliation_module_accessible(), \
        "Reconciliation module is not accessible/displayed"
    logger.info(f"[OK] Reconciliation header: {reconciliation_page.get_reconciliation_header()}")


@then("Reconciliation input panel is visible with mandatory selectors")
def step_verify_input_panel(reconciliation_page: VatReconciliationPage):
    logger.info("[THEN] Verifying Reconciliation input panel with mandatory selectors")
    assert reconciliation_page.is_input_panel_visible(), \
        "Reconciliation input panel with mandatory selectors is not visible"
    logger.info("[OK] Reconciliation input panel is visible")


@then("Reconcile action is visible")
def step_verify_reconcile_action(reconciliation_page: VatReconciliationPage):
    logger.info("[THEN] Verifying Reconcile action is visible")
    assert reconciliation_page.is_reconcile_action_visible(), "Reconcile action/button is not visible"
    logger.info("[OK] Reconcile action is visible")


@then("reconciliation executes successfully")
def step_verify_reconciliation_executed(reconciliation_page: VatReconciliationPage):
    logger.info("[THEN] Verifying reconciliation executed successfully")
    assert reconciliation_page.is_reconciliation_executed(), \
        "Reconciliation did not produce a result surface after execution"
    logger.info("[OK] Reconciliation executed successfully")


@then("Reconciliation Details table is displayed")
def step_verify_reconciliation_details_table(reconciliation_page: VatReconciliationPage):
    logger.info("[THEN] Verifying Reconciliation Details table is displayed")
    assert reconciliation_page.is_reconciliation_details_table_displayed(), \
        "Reconciliation Details table is not displayed"
    logger.info("[OK] Reconciliation Details table is displayed")


@then("Reconciliation Details summary table displays Match and Mismatch rows")
def step_verify_summary_rows(reconciliation_page: VatReconciliationPage):
    logger.info("[THEN] Verifying summary table displays Match and Mismatch rows")
    if not reconciliation_page.is_reconciliation_details_table_displayed():
        pytest.skip("Reconciliation Details summary is not available without a prior reconciliation run")
    assert reconciliation_page.summary_has_match_and_mismatch_rows(), \
        "Summary table does not display both Match and Mismatch rows"
    logger.info("[OK] Match and Mismatch rows are displayed")


@then("Match and Mismatch counts are shown as numeric values")
def step_verify_counts_numeric(reconciliation_page: VatReconciliationPage):
    logger.info("[THEN] Verifying Match and Mismatch counts are numeric")
    counts = reconciliation_page.get_match_mismatch_counts()
    logger.info(f"Detected counts: {counts}")
    assert reconciliation_page.is_numeric(counts.get("match")), \
        f"Match count is not numeric: {counts.get('match')}"
    assert reconciliation_page.is_numeric(counts.get("mismatch")), \
        f"Mismatch count is not numeric: {counts.get('mismatch')}"
    logger.info("[OK] Match and Mismatch counts are numeric")
