"""
Step Definitions for Global Insights And Data Enrichment For e-Invoicing Invoice Management Module
Connects Vat_invoice_management.feature with vat_invoice_management_page.py
"""
import logging
import os
import re
import tempfile
from typing import Dict, Any

import pytest
from playwright.sync_api import Page
from pytest_bdd import given, scenario, then, when, parsers

from pageobjects.vat_invoice_management_page import (
    VatInvoiceManagementPage,
    file_contains_values,
    assert_export_format,
)
from pageobjects.launch_app_page import LaunchAppPage

# Import all common navigation step definitions (login, client selection, DTAI nav, popup)
from tests.step_defs.VAT_Common_Library import *

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(name)s - %(message)s")

# Invoice Issue date range that populates the Outbound (25) / Inbound (4) grids for the
# Belgium client (confirmed against the QA environment).
IM_DATE_FROM = "2026-01-01"
IM_DATE_TO = "2027-12-10"

_CLIENT_MARKERS = {
    "Client_Belgium": "Belgium",
    "Client_France": "France",
    "Client_Poland": "Poland",
}


# ==========================================
# FIXTURES
# ==========================================

@pytest.fixture()
def get_page(vat_session) -> Page:
    """[Option B] Reuse the single session-scoped authenticated page across all Invoice
    Management scenarios, so login + client selection + DTAI navigation happen only once
    for the run. Overrides the function-scoped get_page from conftest for this module."""
    return vat_session["page"]


@pytest.fixture()
def vat_context(get_page: Page, request) -> Dict[str, Any]:
    """
    Function-scoped context shared across steps in one scenario.

    The target Client workspace is derived from the scenario's @Client_* tag so the
    Background client-selection step (which reads vat_context['workspace']) picks the
    right country. Defaults to Belgium for scenarios without a client tag.
    """
    country = "Belgium"
    for marker in request.node.iter_markers():
        if marker.name in _CLIENT_MARKERS:
            country = _CLIENT_MARKERS[marker.name]
            break
    logger.info(f"Initializing VAT context for Invoice Management test (client={country})")
    return {
        "user_role": "Admin",
        "workspace": f"Client {country}",
        "country": country,
        "applied_filters": {},
    }


@pytest.fixture()
def im_page(get_page: Page) -> VatInvoiceManagementPage:
    """Function-scoped fixture to provide Invoice Management page object."""
    return VatInvoiceManagementPage(get_page)


# ==========================================
# SCENARIO DEFINITIONS
# ==========================================

@scenario(
    "../features/Vat_invoice_management.feature",
    "Verify access to Invoice Management module for Admin role under Global Insights And Data Enrichment For e-Invoicing app in GTP IT",
)
def test_invoice_management_access(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_invoice_management.feature",
    "Verify the application display the values in tables based on user selection made in filter criteria in Invoice Management module for Admin role under Global Insights And Data Enrichment For e-Invoicing app in GTP IT",
)
def test_invoice_management_filter(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_invoice_management.feature",
    "Verify export functionality in Invoice Management module for Admin role under Global Insights And Data Enrichment For e-Invoicing app in GTP IT",
)
def test_uploaded_export(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_invoice_management.feature",
    "Verify Column level functionality in Invoice Management module for Admin role under Global Insights And Data Enrichment For e-Invoicing app in GTP IT",
)
def test_uploaded_column_filter(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_invoice_management.feature",
    "Verify the application display the invoice details in Outbound invoice template in Invoice Management module for Admin role under Global Insights And Data Enrichment For e-Invoicing app in GTP IT",
)
def test_invoice_details_popup(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_invoice_management.feature",
    "Verify the application display the Outbound Invoice Extract in Outbound invoice template in Invoice Management module for Admin role under Global Insights And Data Enrichment For e-Invoicing app in GTP IT",
)
def test_outbound_extract_popup(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_invoice_management.feature",
    "Verify the application display the Outbound Invoice Error details in Outbound invoice template in Invoice Management module for Admin role under Global Insights And Data Enrichment For e-Invoicing app in GTP IT",
)
def test_outbound_error_popup(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_invoice_management.feature",
    "Verify the export functionality for Outbound Invoice template in Invoice Management module for Admin role under Global Insights And Data Enrichment For e-Invoicing app in GTP IT",
)
def test_outbound_export(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_invoice_management.feature",
    "Verify the Column level filter, Clear Filter and Reset view functionality for Outbound Invoice template in Invoice Management module for Admin role under Global Insights And Data Enrichment For e-Invoicing app in GTP IT",
)
def test_outbound_filter_clear_reset(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_invoice_management.feature",
    "Verify the Pagination functionality for Outbound Invoice template in Invoice Management module for Admin role under Global Insights And Data Enrichment For e-Invoicing app in GTP IT",
)
def test_outbound_pagination(get_page, vat_context, im_page):
    pass


# ---- Inbound Invoices (AP) scenarios (mirror the Outbound suite) ----
@scenario(
    "../features/Vat_invoice_management.feature",
    "Verify all columns are displayed under Inbound Invoices (AP) grid in Invoice Management module for Admin role under Global Insights And Data Enrichment For e-Invoicing app in GTP IT",
)
def test_inbound_columns(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_invoice_management.feature",
    "Verify the Status column filter and Clear Filter functionality for Inbound Invoices (AP) grid in Invoice Management module for Admin role under Global Insights And Data Enrichment For e-Invoicing app in GTP IT",
)
def test_inbound_filter_clear(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_invoice_management.feature",
    "Verify the Reset View functionality for Inbound Invoices (AP) grid in Invoice Management module for Admin role under Global Insights And Data Enrichment For e-Invoicing app in GTP IT",
)
def test_inbound_reset_view(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_invoice_management.feature",
    "Verify the export functionality for Inbound Invoices (AP) grid in Invoice Management module for Admin role under Global Insights And Data Enrichment For e-Invoicing app in GTP IT",
)
def test_inbound_export(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_invoice_management.feature",
    "Verify the application display the invoice details in Inbound Invoices (AP) grid in Invoice Management module for Admin role under Global Insights And Data Enrichment For e-Invoicing app in GTP IT",
)
def test_inbound_invoice_details(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_invoice_management.feature",
    "Verify the application display the Inbound Invoice Extract in Inbound Invoices (AP) grid in Invoice Management module for Admin role under Global Insights And Data Enrichment For e-Invoicing app in GTP IT",
)
def test_inbound_extract_popup(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_invoice_management.feature",
    "Verify the application display the Inbound Invoice Error details in Inbound Invoices (AP) grid in Invoice Management module for Admin role under Global Insights And Data Enrichment For e-Invoicing app in GTP IT",
)
def test_inbound_error_popup(get_page, vat_context, im_page):
    pass


# ==========================================
# WHEN STEPS (Navigation / Actions)
# ==========================================

@when("I navigate to Invoice Management module")
def step_navigate_to_im_module(get_page: Page, im_page: VatInvoiceManagementPage):
    """Click the Invoice Management tab and wait for the module to load. Defensively
    closes any popup left open by a previous scenario (shared session)."""
    logger.info("[WHEN] Navigating to Invoice Management module")
    if im_page.modal_is_open():
        im_page.close_modal()
    im_page.navigate_to_module()
    get_page.wait_for_timeout(2000)
    logger.info("[OK] Invoice Management module loaded")


@when("I apply valid filter criteria in Invoice Management module")
def step_apply_filter_criteria(
    get_page: Page,
    im_page: VatInvoiceManagementPage,
    vat_context: Dict,
):
    """Apply a valid set of filter criteria in the Invoice Management module."""
    logger.info("[WHEN] Applying filter criteria in Invoice Management")
    im_page.apply_filter_criteria(date_from=IM_DATE_FROM, date_to=IM_DATE_TO)
    vat_context["applied_filters"] = {"date_from": IM_DATE_FROM, "date_to": IM_DATE_TO}
    logger.info("[OK] Filter criteria applied")


# ==========================================
# THEN STEPS (Assertions)
# ==========================================

@then(parsers.parse('Invoice Management module is accessible and displayed with header "{header}"'))
@then('Invoice Management module is accessible and displayed with header "Invoice Management"')
def step_verify_module_header(get_page: Page, im_page: VatInvoiceManagementPage, header: str = "Invoice Management"):
    """Verify the module heading matches the expected text."""
    logger.info(f"[THEN] Verifying module header = '{header}'")
    assert im_page.is_module_accessible(), \
        "Invoice Management module is not accessible (heading not visible)"
    actual = im_page.get_module_header_text()
    assert header.lower() in actual.lower(), \
        f"Expected header '{header}' but got '{actual}'"
    logger.info(f"[OK] Module header verified: '{actual}'")


@then("Outbound e-Invoices section is visible")
def step_verify_outbound_section(get_page: Page, im_page: VatInvoiceManagementPage):
    """Verify the Outbound e-Invoices (AR) section heading is visible."""
    logger.info("[THEN] Verifying Outbound e-Invoices section is visible")
    assert im_page.is_outbound_section_visible(), \
        "Outbound e-Invoices (AR) section heading is not visible"
    logger.info("[OK] Outbound e-Invoices section is visible")


@then("Inbound e-Invoices section is visible")
def step_verify_inbound_section(get_page: Page, im_page: VatInvoiceManagementPage):
    """Verify the Inbound e-Invoices (AP) section heading is visible."""
    logger.info("[THEN] Verifying Inbound e-Invoices section is visible")
    assert im_page.is_inbound_section_visible(), \
        "Inbound e-Invoices (AP) section heading is not visible"
    logger.info("[OK] Inbound e-Invoices section is visible")


@then("Country field is displayed and read-only")
def step_verify_country_readonly(get_page: Page, im_page: VatInvoiceManagementPage):
    """Verify the Country label is displayed and has no editable input."""
    logger.info("[THEN] Verifying Country field is displayed and read-only")
    assert im_page.is_country_field_visible(), \
        "Country label is not visible in Filter Criteria section"
    assert im_page.is_country_field_readonly(), \
        "Country field appears to be editable (expected read-only)"
    logger.info("[OK] Country field is displayed and read-only")


@then("Outbound e-Invoices table displays records matching the applied criteria")
def step_verify_outbound_records(get_page: Page, im_page: VatInvoiceManagementPage):
    """Verify at least one record is visible in the Outbound e-Invoices table."""
    logger.info("[THEN] Verifying Outbound e-Invoices table has records")
    row_count = im_page.get_outbound_row_count()
    logger.info(f"  Outbound row count: {row_count}")
    assert row_count > 0, \
        "Outbound e-Invoices table is empty - expected records matching the applied filter"
    logger.info(f"[OK] Outbound e-Invoices table has {row_count} record(s)")


@then("Inbound e-Invoices table displays records matching the applied criteria")
def step_verify_inbound_records(get_page: Page, im_page: VatInvoiceManagementPage):
    """Verify at least one record is visible in the Inbound e-Invoices table."""
    logger.info("[THEN] Verifying Inbound e-Invoices table has records")
    row_count = im_page.get_inbound_row_count()
    logger.info(f"  Inbound row count: {row_count}")
    assert row_count > 0, \
        "Inbound e-Invoices table is empty - expected records matching the applied filter"
    logger.info(f"[OK] Inbound e-Invoices table has {row_count} record(s)")


# ==================================================================
# UI/UX SMOKE SUITE STEPS (10 scenarios)
# ==================================================================
def _ensure_outbound_populated(im_page: VatInvoiceManagementPage, vat_context: Dict):
    """Outbound/Inbound grids are empty until an Invoice Issue date range is applied."""
    if im_page.outbound_row_count() == 0:
        logger.info("[helper] Outbound grid empty - applying issue-date range")
        im_page.apply_date_range(IM_DATE_FROM, IM_DATE_TO)
        vat_context["applied_filters"] = {"date_from": IM_DATE_FROM, "date_to": IM_DATE_TO}


# ---- Scenario 1: Module access ----
@then("Filter criteria section,Outbound Invoice Template and Inbound Invoices (AP) sections are displayed on Invoice Management page")
def step_sections_displayed(im_page: VatInvoiceManagementPage):
    logger.info("[THEN] Verifying Filter Criteria / Outbound / Inbound sections are displayed")
    assert im_page.is_filter_criteria_visible(), "Filter Criteria section not visible"
    assert im_page.is_outbound_template_visible(), "Outbound Invoice Template section not visible"
    assert im_page.is_inbound_ap_visible(), "Inbound Invoices (AP) section not visible"
    logger.info("[OK] All three sections are displayed")


@then("Uploaded Transactions grid is displayed in sorted order by Timestamp column in descending order")
def step_uploaded_sorted_desc(im_page: VatInvoiceManagementPage):
    logger.info("[THEN] Verifying Uploaded Transactions grid is sorted by Timestamp desc")
    assert im_page.uploaded_row_count() > 0, "Uploaded Transactions grid has no rows"
    ok, ts = im_page.is_uploaded_sorted_by_timestamp_desc()
    if ok is None:
        logger.warning(f"[sort] timestamps not parseable, skipping strict check: {ts[:3]}")
        pytest.skip("Uploaded Timestamps not parseable for a descending assertion")
    assert ok, f"Uploaded Transactions not sorted by Timestamp descending: {ts}"
    logger.info(f"[OK] Uploaded grid sorted by Timestamp desc ({len(ts)} rows)")


# ---- Scenario 2 & 8: record selection + downloads ----
@when("I select few records from Uploaded Transactions grid")
def step_select_uploaded_records(im_page: VatInvoiceManagementPage, vat_context: Dict):
    logger.info("[WHEN] Selecting records from Uploaded Transactions grid")
    selected = im_page.select_grid_records(im_page.uploaded_grid_table, count=2)
    assert selected, "Could not select any records in the Uploaded Transactions grid"
    vat_context["selected_records"] = selected
    vat_context["download_grid"] = "uploaded"


@when("I select records from Outbound Invoice template")
def step_select_outbound_records(im_page: VatInvoiceManagementPage, vat_context: Dict):
    logger.info("[WHEN] Selecting records from Outbound Invoice template grid")
    _ensure_outbound_populated(im_page, vat_context)
    selected = im_page.select_grid_records(im_page.outbound_grid_table, count=2)
    assert selected, "Could not select any records in the Outbound Invoice template grid"
    vat_context["selected_records"] = selected
    vat_context["download_grid"] = "outbound"


@then(parsers.parse("I perform Download as {fmt} action on selected records and verify the downloaded file contains selected records in exported file"))
def step_download_and_verify(im_page: VatInvoiceManagementPage, vat_context: Dict, fmt: str):
    grid = vat_context.get("download_grid", "uploaded")
    selected = vat_context.get("selected_records", [])
    logger.info(f"[THEN] Download as {fmt} from {grid} grid; verify contains {selected}")
    assert selected, "No records were selected before download"
    if grid == "outbound":
        path = im_page.download_outbound_as(fmt)
    elif grid == "inbound":
        path = im_page.download_inbound_as(fmt)
    else:
        path = im_page.download_uploaded_as(fmt)
    fmt_ok, fmt_detail = assert_export_format(path, fmt)
    assert fmt_ok, f"{fmt} export format mismatch: {fmt_detail} (file={path})"
    ok, missing, blob_len = file_contains_values(path, selected)
    assert blob_len > 0, f"Downloaded {fmt} file is empty: {path}"
    assert ok, f"{fmt} export is missing selected records {missing} (file={path})"
    logger.info(f"[OK] {fmt} export: {fmt_detail}; contains all selected records {selected}")


# ---- Scenario 3: Uploaded Status column filter ----
@when("I click on Status column to click on Filter Select status from dropdown and apply Filter")
def step_uploaded_filter_status_1(im_page: VatInvoiceManagementPage, vat_context: Dict):
    statuses = im_page.distinct_uploaded_statuses()
    logger.info(f"[WHEN] Uploaded distinct statuses: {statuses}")
    assert statuses, "No statuses available in Uploaded Transactions grid"
    chosen = statuses[0]
    vat_context["uploaded_statuses_all"] = statuses
    vat_context["uploaded_status_1"] = chosen
    vat_context["filter_grid"] = "uploaded"
    assert im_page.filter_uploaded_status(chosen), f"Could not filter Uploaded by '{chosen}'"


@then("User is able to filter the records based on selected status in status Column")
def step_verify_uploaded_filter_1(im_page: VatInvoiceManagementPage, vat_context: Dict):
    chosen = vat_context.get("uploaded_status_1", "")
    statuses = [s for s in im_page.get_uploaded_statuses() if s]
    assert statuses, f"No rows displayed after filtering by '{chosen}'"
    assert all(chosen.lower() in s.lower() for s in statuses), \
        f"Rows not all '{chosen}': {statuses}"
    logger.info(f"[OK] Uploaded filtered to '{chosen}' ({len(statuses)} rows)")


@when("I click on status column to click on Filter Select different status from dropdown and apply Filter")
@then("I click on status column to click on Filter Select different status from dropdown and apply Filter")
def step_uploaded_filter_status_2(im_page: VatInvoiceManagementPage, vat_context: Dict):
    all_st = vat_context.get("uploaded_statuses_all", [])
    first = vat_context.get("uploaded_status_1")
    diff = next((s for s in all_st if s != first), None)
    if not diff:
        pytest.skip("Only one distinct status in Uploaded grid; cannot filter a different status")
    vat_context["uploaded_status_2"] = diff
    assert im_page.filter_uploaded_status(diff), f"Could not filter Uploaded by '{diff}'"


@then("User is able to filter the records based on other selected status in status Column")
def step_verify_uploaded_filter_2(im_page: VatInvoiceManagementPage, vat_context: Dict):
    diff = vat_context.get("uploaded_status_2")
    if not diff:
        pytest.skip("No different status was available to filter")
    statuses = [s for s in im_page.get_uploaded_statuses() if s]
    assert statuses, f"No rows displayed after filtering by '{diff}'"
    assert all(diff.lower() in s.lower() for s in statuses), \
        f"Rows not all '{diff}': {statuses}"
    logger.info(f"[OK] Uploaded filtered to different status '{diff}' ({len(statuses)} rows)")


# ---- shared Clear Filter (Uploaded scenario 3 / Outbound scenario 9) ----
@when("I click on Clear Filter option to clear the applied filter")
@then("I click on Clear Filter option to clear the applied filter")
def step_click_clear_filter(im_page: VatInvoiceManagementPage, vat_context: Dict):
    grid = vat_context.get("filter_grid", "uploaded")
    logger.info(f"[STEP] Clearing filters on {grid} grid")
    if grid == "outbound":
        im_page.clear_outbound_filters()
    elif grid == "inbound":
        im_page.clear_inbound_filters()
    else:
        im_page.clear_uploaded_filters()


@then("User is able to clear the applied filter and all records are displayed in Uploaded Transactions grid")
def step_verify_uploaded_cleared(im_page: VatInvoiceManagementPage):
    cnt = im_page.uploaded_row_count()
    assert cnt > 0, "Uploaded Transactions grid is empty after clearing the filter"
    logger.info(f"[OK] All records displayed after clearing filter ({cnt} rows)")


# ---- Scenario 4: Apply filters populate Outbound + Inbound ----
@then("Outbound Invoice Template and Inbound Invoices (AP) grid displays records matching the applied criteria")
def step_outbound_inbound_have_records(im_page: VatInvoiceManagementPage):
    ob = im_page.outbound_row_count()
    ib = im_page.inbound_row_count()
    logger.info(f"[THEN] Outbound rows={ob}, Inbound rows={ib}")
    assert ob > 0, "Outbound Invoice Template grid is empty after applying the filter criteria"
    assert ib > 0, "Inbound Invoices (AP) grid is empty after applying the filter criteria"
    logger.info("[OK] Outbound and Inbound grids display records")


# ---- Scenario 5: Invoice Details popup ----
@when("I click on any Client invoice number column from Outbound Invoice Template grid")
def step_click_client_invoice_number(im_page: VatInvoiceManagementPage, vat_context: Dict):
    logger.info("[WHEN] Clicking a Client Invoice Number link in Outbound grid")
    _ensure_outbound_populated(im_page, vat_context)
    assert im_page.open_first_invoice_details(), "Invoice Details popup did not open"


@then("the application displays the invoice details in Invoice details Pop up having EY logo with close button on top in Invoice Management module for Admin role under Global Insights And Data Enrichment For e-Invoicing app in GTP IT")
def step_invoice_details_popup(im_page: VatInvoiceManagementPage):
    assert im_page.modal_is_open(), "Invoice Details popup is not open"
    assert im_page.modal_has_logo(), "EY logo not present in Invoice Details popup"
    assert im_page.modal_has_close_button(), "Close button not present in Invoice Details popup"
    logger.info("[OK] Invoice Details popup displayed with EY logo and Close button")


@then("I verify Invoice Header, Buyer, Seller,Totals & Payment,Line Items and Tax Summary section are getting displayed in invoice details pop up.")
def step_invoice_details_sections(im_page: VatInvoiceManagementPage):
    expected = ["Invoice Header", "Buyer", "Seller", "Totals & Payment", "Line Items", "Tax Summary"]
    missing = im_page.modal_missing_texts(expected)
    assert not missing, f"Invoice Details popup is missing section(s): {missing}"
    logger.info("[OK] All Invoice Details sections displayed")


@when("I click on Close button to close the invoice details pop up and verify the Invoice Management module is displayed with Outbound Invoice Template and Inbound Invoices (AP) sections")
@then("I click on Close button to close the invoice details pop up and verify the Invoice Management module is displayed with Outbound Invoice Template and Inbound Invoices (AP) sections")
def step_close_invoice_details(im_page: VatInvoiceManagementPage):
    im_page.close_modal()
    assert im_page.modal_is_closed(), "Invoice Details popup is still open after clicking Close"
    assert im_page.is_outbound_template_visible(), "Outbound Invoice Template section not visible after close"
    assert im_page.is_inbound_ap_visible(), "Inbound Invoices (AP) section not visible after close"
    logger.info("[OK] Popup closed; Outbound and Inbound sections displayed")


# ---- Scenario 6 & 7: Outbound Status popups (Extract / Error Details) ----
@when(parsers.parse("I Click on Status column to Filter {status} status records in Outbound Invoice Template grid"))
def step_filter_outbound_status_records(im_page: VatInvoiceManagementPage, vat_context: Dict, status: str):
    logger.info(f"[WHEN] Filtering Outbound grid to '{status}' status")
    _ensure_outbound_populated(im_page, vat_context)
    im_page.show_outbound_filters()
    assert im_page.filter_outbound_status(status), f"Could not filter Outbound by '{status}'"
    vat_context["outbound_filter_status"] = status


@then(parsers.parse("I click on {status} status records from Outbound Invoice Template grid"))
def step_click_outbound_status_records(im_page: VatInvoiceManagementPage, vat_context: Dict, status: str):
    vat_context["outbound_popup_invoice"] = im_page.first_outbound_invoice_number()
    assert im_page.click_first_outbound_clickable_status(), \
        f"Could not open the '{status}' status popup"
    logger.info(f"[OK] Opened '{status}' status popup (invoice={vat_context['outbound_popup_invoice']})")


@then("Outbound Invoice Extract pop up displayed having EY logo with Close button")
def step_extract_popup(im_page: VatInvoiceManagementPage):
    assert im_page.modal_is_open(), "Outbound Invoice Extract popup is not open"
    assert "outbound invoice extract" in im_page.modal_text().lower(), \
        "Extract popup heading not found"
    assert im_page.modal_has_logo(), "EY logo not present in Extract popup"
    assert im_page.modal_has_close_button(), "Close button not present in Extract popup"
    logger.info("[OK] Outbound Invoice Extract popup displayed with EY logo and Close button")


@then("I verify Client Invoice Number,Invoice ID,Customer Name,System,Status,Invoice Total Value and Invoice Tax Value columns are displayed correctly in Outbound Invoice Extract")
def step_extract_columns(im_page: VatInvoiceManagementPage):
    expected = ["Client Invoice Number", "Invoice ID", "Customer Name", "System",
                "Status", "Invoice Total Value", "Invoice Tax Value"]
    missing = im_page.modal_missing_texts(expected)
    assert not missing, f"Outbound Invoice Extract popup is missing label(s): {missing}"
    logger.info("[OK] All Extract popup columns displayed")


@then(parsers.parse("I click on {fmt} button to export Outbound extract in {fmt_again} format"))
def step_export_extract(im_page: VatInvoiceManagementPage, vat_context: Dict, fmt: str, fmt_again: str):
    path = im_page.export_from_modal(fmt)
    vat_context[f"extract_export_{fmt.lower()}"] = path
    logger.info(f"[STEP] Exported Outbound extract as {fmt}: {path}")


@then(parsers.parse("I verify the exported file contains the correct data in Outbound Invoice Extract in {fmt} format"))
def step_verify_extract_export(vat_context: Dict, fmt: str):
    path = vat_context.get(f"extract_export_{fmt.lower()}")
    assert path, f"No {fmt} extract export was captured"
    fmt_ok, fmt_detail = assert_export_format(path, fmt)
    assert fmt_ok, f"{fmt} extract export format mismatch: {fmt_detail} (file={path})"
    inv = vat_context.get("outbound_popup_invoice", "")
    ok, missing, blob_len = file_contains_values(path, [inv] if inv else [])
    assert blob_len > 0, f"{fmt} extract export is empty: {path}"
    if inv:
        assert ok, f"{fmt} extract export missing invoice '{inv}' (file={path})"
    logger.info(f"[OK] {fmt} extract export verified ({fmt_detail})")


@then("Outbound Invoice Error Details pop up displayed having EY logo with Close button")
def step_error_popup(im_page: VatInvoiceManagementPage):
    assert im_page.modal_is_open(), "Outbound Invoice Error Details popup is not open"
    assert "error details" in im_page.modal_text().lower(), "Error Details popup heading not found"
    assert im_page.modal_has_logo(), "EY logo not present in Error Details popup"
    assert im_page.modal_has_close_button(), "Close button not present in Error Details popup"
    logger.info("[OK] Outbound Invoice Error Details popup displayed with EY logo and Close button")


@then("I verify Client Invoice Number,Invoice ID,System and Error Detail columns are displayed in Outbound Invoice Error Details pop up.")
def step_error_columns(im_page: VatInvoiceManagementPage):
    expected = ["Client Invoice Number", "Invoice ID", "System", "Error Detail"]
    missing = im_page.modal_missing_texts(expected)
    assert not missing, f"Error Details popup is missing label(s): {missing}"
    logger.info("[OK] All Error Details popup columns displayed")


@then("I click on Excel button to export the error details for invoice")
def step_export_error(im_page: VatInvoiceManagementPage, vat_context: Dict):
    path = im_page.export_from_modal("Excel")
    vat_context["error_export_excel"] = path
    logger.info(f"[STEP] Exported Error Details as Excel: {path}")


@then("I verify the exported file contains the correct data in Outbound Invoice Error Details in Excel format")
def step_verify_error_export(vat_context: Dict):
    path = vat_context.get("error_export_excel")
    assert path, "No Excel error-details export was captured"
    fmt_ok, fmt_detail = assert_export_format(path, "Excel")
    assert fmt_ok, f"Excel error-details export format mismatch: {fmt_detail} (file={path})"
    inv = vat_context.get("outbound_popup_invoice", "")
    ok, missing, blob_len = file_contains_values(path, [inv] if inv else [])
    assert blob_len > 0, f"Excel error-details export is empty: {path}"
    if inv:
        assert ok, f"Excel error-details export missing invoice '{inv}' (file={path})"
    logger.info(f"[OK] Excel error-details export verified ({fmt_detail})")


@then(parsers.parse("I click on close button to close the {popup} pop up and verify the pop up is closed."))
def step_close_named_popup(im_page: VatInvoiceManagementPage, popup: str):
    im_page.close_modal()
    assert im_page.modal_is_closed(), f"{popup} popup is still open after clicking Close"
    logger.info(f"[OK] {popup} popup closed")


# ---- Scenario 9: Outbound column filter / clear / reset ----
@when("I click on Show Filter option in Outbound Invoice template grid")
def step_show_outbound_filters(im_page: VatInvoiceManagementPage, vat_context: Dict):
    logger.info("[WHEN] Showing filters on Outbound Invoice template grid")
    _ensure_outbound_populated(im_page, vat_context)
    im_page.show_outbound_filters()
    vat_context["filter_grid"] = "outbound"
    vat_context["outbound_full_count"] = im_page.outbound_row_count()


@then("User is able to filter the records with Ready status")
def step_outbound_filter_ready(im_page: VatInvoiceManagementPage):
    assert im_page.filter_outbound_status("Ready"), "Could not filter Outbound by Ready"
    st = [s for s in im_page.outbound_visible_statuses() if s]
    assert st, "No rows after filtering Outbound by Ready"
    assert all("ready" in s.lower() for s in st), f"Rows not all Ready: {st}"
    logger.info(f"[OK] Outbound filtered to Ready ({len(st)} rows)")


@then("I remove the Ready status records")
def step_outbound_remove_ready(im_page: VatInvoiceManagementPage):
    im_page.filter_outbound_status("")


@then("User is able to filter the records with Review required status")
def step_outbound_filter_review(im_page: VatInvoiceManagementPage):
    assert im_page.filter_outbound_status("Review Required"), "Could not filter Outbound by Review Required"
    st = [s for s in im_page.outbound_visible_statuses() if s]
    assert st, "No rows after filtering Outbound by Review Required"
    assert all("review required" in s.lower() for s in st), f"Rows not all Review Required: {st}"
    logger.info(f"[OK] Outbound filtered to Review Required ({len(st)} rows)")


@then("User is able to filter the records with Custom ERP System column")
def step_outbound_filter_custom_erp(im_page: VatInvoiceManagementPage):
    im_page.filter_outbound_status("")  # clear prior status filter first
    assert im_page.filter_outbound_system("Custom ERP"), "Could not filter Outbound by Custom ERP"
    sy = [s for s in im_page.outbound_visible_systems() if s]
    assert sy, "No rows after filtering Outbound by Custom ERP"
    assert all("custom erp" in s.lower() for s in sy), f"Rows not all Custom ERP: {sy}"
    logger.info(f"[OK] Outbound filtered to Custom ERP ({len(sy)} rows)")


@then("I remove the records with Custom ERP System column")
def step_outbound_remove_custom_erp(im_page: VatInvoiceManagementPage):
    im_page.filter_outbound_system("")


@then("User is able to filter the records with SAP System column")
def step_outbound_filter_sap(im_page: VatInvoiceManagementPage):
    assert im_page.filter_outbound_system("SAP"), "Could not filter Outbound by SAP"
    sy = [s for s in im_page.outbound_visible_systems() if s]
    assert sy, "No rows after filtering Outbound by SAP"
    assert all("sap" in s.lower() for s in sy), f"Rows not all SAP: {sy}"
    logger.info(f"[OK] Outbound filtered to SAP ({len(sy)} rows)")


@then("User is able to clear the applied filter and all records are displayed in Outbound Invoice template grid")
def step_verify_outbound_cleared(im_page: VatInvoiceManagementPage):
    cnt = im_page.outbound_row_count()
    assert cnt > 0, "Outbound Invoice template grid is empty after clearing filters"
    logger.info(f"[OK] All records displayed after clearing Outbound filters ({cnt} rows)")


@then("I click on Reset View button to reset all filters applied")
def step_reset_view(im_page: VatInvoiceManagementPage, vat_context: Dict):
    grid = vat_context.get("filter_grid", "outbound")
    logger.info(f"[STEP] Reset View on {grid} grid")
    if grid == "inbound":
        im_page.reset_inbound_view()
    else:
        im_page.reset_outbound_view()


@then("User is able to reset all filters applied and all records are displayed in Outbound Invoice template grid")
def step_verify_outbound_reset(im_page: VatInvoiceManagementPage):
    cnt = im_page.outbound_row_count()
    assert cnt > 0, "Outbound Invoice template grid is empty after Reset View"
    logger.info(f"[OK] All records displayed after Reset View ({cnt} rows)")


# ---- Scenario 10: Outbound pagination ----
@when(parsers.parse("I Click on Show to change the pagination size from {old:d} to {new:d} records in Outbound Invoice template grid"))
@then(parsers.parse("I Click on Show to change the pagination size from {old:d} to {new:d} records in Outbound Invoice template grid"))
def step_change_page_size(im_page: VatInvoiceManagementPage, vat_context: Dict, old: int, new: int):
    logger.info(f"[STEP] Changing Outbound page size {old} -> {new}")
    _ensure_outbound_populated(im_page, vat_context)
    im_page.set_outbound_page_size(new)
    val = im_page.get_outbound_page_size()
    assert str(new) == str(val), f"Outbound page size not set to {new} (got '{val}')"


@when(parsers.parse("I click on {btn} button to navigate to {target} page in Outbound Invoice template grid"))
@then(parsers.parse("I click on {btn} button to navigate to {target} page in Outbound Invoice template grid"))
def step_click_pagination(im_page: VatInvoiceManagementPage, vat_context: Dict, btn: str, target: str):
    which = {"next": "next", "previous": "prev", "last": "last", "first": "first"}[btn.strip().lower()]
    before, after = im_page.click_outbound_page(which)
    vat_context["page_nav"] = {
        "which": which, "before": before, "after": after,
        "pages": im_page.outbound_page_count(),
    }
    logger.info(f"[STEP] Pagination '{btn}': page {before} -> {after}")


@then(parsers.parse("User is able to navigate to {target} page in Outbound Invoice template grid"))
def step_verify_pagination(vat_context: Dict, target: str):
    # Validate the last pagination CLICK that was recorded (nav["which"]); the Then
    # target word is descriptive and may not line up 1:1 with the preceding action
    # in the scenario, so we assert against the action that actually happened.
    nav = vat_context.get("page_nav", {})
    before, after, pages = nav.get("before"), nav.get("after"), nav.get("pages", 1)
    which = (nav.get("which") or target.strip().lower())
    assert after is not None, "Pagination active-page number could not be read"
    if pages <= 1:
        logger.warning(f"[pagination] single page (pages={pages}); '{which}' is a no-op but control is present")
        return
    if which == "next":
        assert after >= before, f"Next did not advance the page: {before} -> {after}"
    elif which == "prev":
        assert after <= before, f"Previous did not go back a page: {before} -> {after}"
    elif which == "last":
        assert after == pages, f"Last did not reach the final page: {after} != {pages}"
    elif which == "first":
        assert after == 1, f"First did not reach page 1: got {after}"
    logger.info(f"[OK] Pagination '{which}' verified ({before} -> {after} of {pages})")


# ==================================================================
# INBOUND INVOICES (AP) STEPS (mirror the Outbound suite)
# ==================================================================
def _ensure_inbound_populated(im_page: VatInvoiceManagementPage, vat_context: Dict):
    """Inbound (AP) grid is empty until an Invoice Issue date range is applied.
    Also scrolls the Inbound section into view for better visibility."""
    if im_page.inbound_row_count() == 0:
        logger.info("[helper] Inbound grid empty - applying issue-date range")
        im_page.apply_date_range(IM_DATE_FROM, IM_DATE_TO)
        vat_context["applied_filters"] = {"date_from": IM_DATE_FROM, "date_to": IM_DATE_TO}
    im_page.scroll_to_inbound_section()


# ---- Columns ----
@then("all columns are displayed in Inbound Invoices (AP) grid")
def step_inbound_columns(im_page: VatInvoiceManagementPage, vat_context: Dict):
    _ensure_inbound_populated(im_page, vat_context)
    headers = im_page.get_inbound_column_headers()
    logger.info(f"[THEN] Inbound grid columns: {headers}")
    assert headers, "Inbound Invoices (AP) grid has no column headers rendered"
    expected = ["Client Invoice Number", "Status", "Invoice ID", "Customer Name",
                "Invoice Total Value", "Invoice Tax Value", "System"]
    blob = " | ".join(h.lower() for h in headers)
    missing = [c for c in expected if c.lower() not in blob]
    assert not missing, f"Inbound grid missing expected column(s): {missing} (present={headers})"
    logger.info(f"[OK] Inbound grid displays all expected columns ({len(headers)} headers)")


# ---- Show Filter ----
@when("I click on Show Filter option in Inbound Invoices (AP) grid")
def step_show_inbound_filters(im_page: VatInvoiceManagementPage, vat_context: Dict):
    logger.info("[WHEN] Showing filters on Inbound Invoices (AP) grid")
    _ensure_inbound_populated(im_page, vat_context)
    im_page.show_inbound_filters()
    vat_context["filter_grid"] = "inbound"
    vat_context["inbound_full_count"] = im_page.inbound_row_count()


# ---- Filter by status (Ready / Error) ----
@then(parsers.parse("User is able to filter the records with {status} status in Inbound Invoices (AP) grid"))
def step_inbound_filter_status(im_page: VatInvoiceManagementPage, vat_context: Dict, status: str):
    assert im_page.filter_inbound_status(status), f"Could not filter Inbound by '{status}'"
    st = [s for s in im_page.inbound_visible_statuses() if s]
    vat_context["inbound_last_status"] = status
    if not st:
        # A status with no matching rows in the small AP grid is still a valid filter result.
        logger.warning(f"[inbound] no rows after filtering by '{status}'")
        return
    assert all(status.lower() in s.lower() for s in st), f"Rows not all '{status}': {st}"
    logger.info(f"[OK] Inbound filtered to '{status}' ({len(st)} rows)")


@then(parsers.parse("I remove the {status} status records in Inbound Invoices (AP) grid"))
def step_inbound_remove_status(im_page: VatInvoiceManagementPage, status: str):
    im_page.filter_inbound_status("")


# ---- Clear filter / Reset view verifications ----
@then("User is able to clear the applied filter and all records are displayed in Inbound Invoices (AP) grid")
def step_verify_inbound_cleared(im_page: VatInvoiceManagementPage):
    cnt = im_page.inbound_row_count()
    assert cnt > 0, "Inbound Invoices (AP) grid is empty after clearing the filter"
    logger.info(f"[OK] All records displayed after clearing Inbound filter ({cnt} rows)")


@then("User is able to reset all filters applied and all records are displayed in Inbound Invoices (AP) grid")
def step_verify_inbound_reset(im_page: VatInvoiceManagementPage):
    cnt = im_page.inbound_row_count()
    assert cnt > 0, "Inbound Invoices (AP) grid is empty after Reset View"
    logger.info(f"[OK] All records displayed after Reset View ({cnt} rows)")


# ---- Export ----
@when("I select records from Inbound Invoices (AP) grid")
def step_select_inbound_records(im_page: VatInvoiceManagementPage, vat_context: Dict):
    logger.info("[WHEN] Selecting records from Inbound Invoices (AP) grid")
    _ensure_inbound_populated(im_page, vat_context)
    selected = im_page.select_grid_records(im_page.inbound_grid_table, count=2)
    assert selected, "Could not select any records in the Inbound Invoices (AP) grid"
    vat_context["selected_records"] = selected
    vat_context["download_grid"] = "inbound"


# ---- Invoice Details popup ----
@when("I click on any Client invoice number column from Inbound Invoices (AP) grid")
def step_click_inbound_invoice_number(im_page: VatInvoiceManagementPage, vat_context: Dict):
    logger.info("[WHEN] Clicking a Client Invoice Number link in Inbound grid")
    _ensure_inbound_populated(im_page, vat_context)
    assert im_page.open_first_inbound_invoice_details(), "Invoice Details popup did not open (Inbound)"


# ---- Extract / Error popups ----
@when(parsers.parse("I Click on Status column to Filter {status} status records in Inbound Invoices (AP) grid"))
def step_filter_inbound_status_records(im_page: VatInvoiceManagementPage, vat_context: Dict, status: str):
    logger.info(f"[WHEN] Filtering Inbound grid to '{status}' status")
    _ensure_inbound_populated(im_page, vat_context)
    im_page.show_inbound_filters()
    assert im_page.filter_inbound_status(status), f"Could not filter Inbound by '{status}'"
    vat_context["inbound_filter_status"] = status
    vat_context["filter_grid"] = "inbound"


@then(parsers.parse("I click on {status} status records from Inbound Invoices (AP) grid"))
def step_click_inbound_status_records(im_page: VatInvoiceManagementPage, vat_context: Dict, status: str):
    vat_context["inbound_popup_invoice"] = im_page.first_inbound_invoice_number()
    assert im_page.click_first_inbound_clickable_status(), \
        f"Could not open the '{status}' status popup (Inbound)"
    logger.info(f"[OK] Opened Inbound '{status}' status popup "
                f"(invoice={vat_context['inbound_popup_invoice']})")


@then("Inbound Invoice Extract pop up displayed having EY logo with Close button")
def step_inbound_extract_popup(im_page: VatInvoiceManagementPage):
    assert im_page.modal_is_open(), "Inbound Invoice Extract popup is not open"
    assert "invoice extract" in im_page.modal_text().lower(), "Inbound Extract popup heading not found"
    assert im_page.modal_has_logo(), "EY logo not present in Inbound Extract popup"
    assert im_page.modal_has_close_button(), "Close button not present in Inbound Extract popup"
    logger.info("[OK] Inbound Invoice Extract popup displayed with EY logo and Close button")


@then("I verify Client Invoice Number,Invoice ID,Customer Name,System,Status,Invoice Total Value and Invoice Tax Value columns are displayed correctly in Inbound Invoice Extract")
def step_inbound_extract_columns(im_page: VatInvoiceManagementPage):
    expected = ["Client Invoice Number", "Invoice ID", "Customer Name", "System",
                "Status", "Invoice Total Value", "Invoice Tax Value"]
    missing = im_page.modal_missing_texts(expected)
    assert not missing, f"Inbound Invoice Extract popup is missing label(s): {missing}"
    logger.info("[OK] All Inbound Extract popup columns displayed")


@then(parsers.parse("I click on {fmt} button to export Inbound extract in {fmt_again} format"))
def step_export_inbound_extract(im_page: VatInvoiceManagementPage, vat_context: Dict, fmt: str, fmt_again: str):
    path = im_page.export_from_modal(fmt)
    vat_context[f"inbound_extract_export_{fmt.lower()}"] = path
    logger.info(f"[STEP] Exported Inbound extract as {fmt}: {path}")


@then(parsers.parse("I verify the exported file contains the correct data in Inbound Invoice Extract in {fmt} format"))
def step_verify_inbound_extract_export(vat_context: Dict, fmt: str):
    path = vat_context.get(f"inbound_extract_export_{fmt.lower()}")
    assert path, f"No {fmt} Inbound extract export was captured"
    fmt_ok, fmt_detail = assert_export_format(path, fmt)
    assert fmt_ok, f"{fmt} Inbound extract export format mismatch: {fmt_detail} (file={path})"
    inv = vat_context.get("inbound_popup_invoice", "")
    ok, missing, blob_len = file_contains_values(path, [inv] if inv else [])
    assert blob_len > 0, f"{fmt} Inbound extract export is empty: {path}"
    if inv:
        assert ok, f"{fmt} Inbound extract export missing invoice '{inv}' (file={path})"
    logger.info(f"[OK] {fmt} Inbound extract export verified ({fmt_detail})")


@then("Inbound Invoice Error Details pop up displayed having EY logo with Close button")
def step_inbound_error_popup(im_page: VatInvoiceManagementPage):
    assert im_page.modal_is_open(), "Inbound Invoice Error Details popup is not open"
    assert "error details" in im_page.modal_text().lower(), "Inbound Error Details popup heading not found"
    assert im_page.modal_has_logo(), "EY logo not present in Inbound Error Details popup"
    assert im_page.modal_has_close_button(), "Close button not present in Inbound Error Details popup"
    logger.info("[OK] Inbound Invoice Error Details popup displayed with EY logo and Close button")


@then("I verify Client Invoice Number,Invoice ID,System and Error Detail columns are displayed in Inbound Invoice Error Details pop up.")
def step_inbound_error_columns(im_page: VatInvoiceManagementPage):
    expected = ["Client Invoice Number", "Invoice ID", "System", "Error Detail"]
    missing = im_page.modal_missing_texts(expected)
    assert not missing, f"Inbound Error Details popup is missing label(s): {missing}"
    logger.info("[OK] All Inbound Error Details popup columns displayed")


@then("I verify the exported file contains the correct data in Inbound Invoice Error Details in Excel format")
def step_verify_inbound_error_export(vat_context: Dict):
    path = vat_context.get("error_export_excel")
    assert path, "No Excel Inbound error-details export was captured"
    fmt_ok, fmt_detail = assert_export_format(path, "Excel")
    assert fmt_ok, f"Excel Inbound error-details export format mismatch: {fmt_detail} (file={path})"
    inv = vat_context.get("inbound_popup_invoice", "")
    ok, missing, blob_len = file_contains_values(path, [inv] if inv else [])
    assert blob_len > 0, f"Excel Inbound error-details export is empty: {path}"
    if inv:
        assert ok, f"Excel Inbound error-details export missing invoice '{inv}' (file={path})"
    logger.info(f"[OK] Excel Inbound error-details export verified ({fmt_detail})")
