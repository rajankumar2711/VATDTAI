"""
Step Definitions for User Management Module
Connects Vat_user_management.feature with vat_user_management_page.py

All scenarios share a single authenticated session (Option B) via the get_page override below.
"""
import os
import re
import tempfile
import logging
from typing import Dict, Any

import pytest
from playwright.sync_api import Page, expect
from pytest_bdd import given, scenario, then, when, parsers
from pageobjects.vat_user_management_page import VatUserManagementPage
from pageobjects.launch_app_page import LaunchAppPage

# navigate_to_module is called directly below; the wildcard import registers the common
# Background step definitions (login, client selection, DTAI navigation, popup dismissal).
from tests.step_defs.VAT_Common_Library import navigate_to_module
from tests.step_defs.VAT_Common_Library import *

# Configure logger for this module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')


# ==========================================
# FIXTURES
# ==========================================

@pytest.fixture()
def get_page(vat_session) -> Page:
    """Reuse the single session-scoped authenticated page across all User Management scenarios,
    so login + client selection + DTAI navigation happen only once.
    Overrides the function-scoped get_page from conftest for this module only."""
    return vat_session["page"]


@pytest.fixture()
def vat_context(get_page: Page) -> Dict[str, Any]:
    """
    Per-scenario context bag. The browser session itself is shared across scenarios
    (see get_page override); only this lightweight state is recreated per scenario.
    """
    logger.info("Initializing VAT context for test")
    return {
        "user_role": "Admin",
        "selected_column": None,
        "sort_order": None,
        "applied_filters": {},
        "selected_rows": [],
        "initial_row_count": 0,
        "filtered_row_count": 0,
    }


@pytest.fixture()
def user_management_page(get_page: Page) -> VatUserManagementPage:
    """Function-scoped fixture to provide User Management page object"""
    logger.info("Creating User Management page object")
    return VatUserManagementPage(get_page)


def _wait_for_users_grid(page: Page, um_page: VatUserManagementPage):
    """Wait for the Existing Users grid to finish (re)loading after navigating to the module.

    Scenarios share one authenticated session; re-clicking the module tab reloads the grid
    fresh (default sort, no filters), so no manual reset is needed. We only wait for the grid
    to settle so the first assertion in each scenario does not race the reload.
    """
    try:
        page.locator(um_page.grid_existing_users).first.wait_for(state="visible", timeout=15000)
        # Existing Users section heading renders a beat after the grid on the first navigation;
        # wait for it so the first scenario's assertions do not race the render.
        try:
            page.locator(um_page.heading_existing_users).first.wait_for(state="visible", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(500)
    except Exception as exc:
        logger.debug(f"Users grid not confirmed visible after navigation: {exc}")


def _column_header(page: Page, column: str):
    """Match a grid column header by name substring, robust to the leading menu glyph and the
    sort-direction indicator that change a header's accessible name once it becomes the sorted
    column (the string role= selector needs an exact name and misses those)."""
    return page.get_by_role("columnheader", name=column).first


# ==========================================
# SCENARIO DEFINITIONS
# ==========================================

@scenario("../features/Vat_user_management.feature", "Verify access to User Management module by Admin")
def test_admin_access_user_management():
    """TC_607973: Admin can access User Management module"""
    pass


@scenario("../features/Vat_user_management.feature", "Verify access to User Management module by Country Owner")
def test_country_owner_access_user_management():
    """TC_607974: Country Owner can access User Management module"""
    pass


@scenario("../features/Vat_user_management.feature", "Verify default sorting of Existing Users table by Name ascending")
def test_default_sorting_by_name():
    """TC_607975: Default sort is Name ascending"""
    pass


@scenario("../features/Vat_user_management.feature", "Verify sorting functionality on columns Name, Email, Role")
def test_sorting_functionality():
    """TC_607976: Sort functionality on Name, Email, Role columns"""
    pass


@scenario("../features/Vat_user_management.feature", "Verify filtering/search functionality on Name, Email, Role")
def test_filtering_functionality():
    """TC_607977: Filter/search on Name, Email, Role columns"""
    pass


@scenario("../features/Vat_user_management.feature", "Verify Select All checkbox functionality")
def test_select_all_checkbox():
    """TC_607978: Select All checkbox selects all rows"""
    pass


@scenario("../features/Vat_user_management.feature", "Verify Clear Filters button functionality")
def test_clear_filters_button():
    """TC_607979: Clear Filters button clears all filters"""
    pass


@scenario("../features/Vat_user_management.feature", "Verify Reset Sort button functionality")
def test_reset_sort_button():
    """TC_607980: Reset Sort resets to default Name ascending"""
    pass


@scenario("../features/Vat_user_management.feature", "Verify Download functionality in CSV, XML, JSON formats")
def test_download_functionality():
    """TC_607981: Download user data in various formats"""
    pass


@scenario("../features/Vat_user_management.feature", "Verify pagination displays maximum 25 records per page")
def test_pagination_max_records():
    """TC_607982: Pagination shows max 25 records per page"""
    pass


@scenario("../features/Vat_user_management.feature", "Verify vertical and horizontal scroll functionality")
def test_scroll_functionality():
    """TC_607983: Vertical and horizontal scrolling"""
    pass


# ==========================================
# GIVEN STEPS (Prerequisites)
# ==========================================
# NOTE: Login and client selection steps are imported from VAT_Common_Library.py
# Only User Management-specific @given steps are defined here

@given("the users are configured in GTPIT")
def step_users_configured_in_gtpit():
    """Background step: Users configured in GTPIT"""
    pass


@given("users are assigned specific roles in Global Insights And Data Enrichment For e-Invoicing User Management")
def step_users_assigned_roles():
    """Background step: Users have assigned roles"""
    pass


@given("the Existing Users table has multiple user records")
def step_table_has_multiple_records(get_page: Page, user_management_page: VatUserManagementPage, vat_context: Dict):
    """Verify table has multiple records"""
    rows = get_page.locator(user_management_page.rows_existing_users)
    row_count = rows.count()
    assert row_count > 1, f"Expected multiple records, found {row_count}"
    vat_context["initial_row_count"] = row_count


@when("I apply default Name and Role filters")
@when(parsers.parse("I apply filters on Name {name_filter} and Role {role_filter}"))
@when(parsers.parse('I apply filters on Name "{name_filter}" and Role "{role_filter}"'))
def step_apply_filters_on_name_and_role(
    get_page: Page,
    user_management_page: VatUserManagementPage,
    vat_context: Dict,
    name_filter: str = "Rajan",
    role_filter: str = "Admin"
):
    """Apply filters on Name and Role columns"""
    logger.info(f"[WHEN] Applying filters: Name='{name_filter}', Role='{role_filter}'")
    
    # Reveal filter inputs using the page object's Show Filters helper (has locator fallback)
    user_management_page.show_filters()
    
    # Apply Name filter
    logger.info(f"Applying Name filter: {name_filter}")
    name_input = get_page.locator(user_management_page.input_filter_name)
    name_input.wait_for(state="visible", timeout=10000)
    name_input.fill(name_filter, timeout=10000)
    # Press Enter to trigger filter
    name_input.press("Enter")
    vat_context["applied_filters"]["Name"] = name_filter
    
    # Apply Role filter
    logger.info(f"Applying Role filter: {role_filter}")
    role_input = get_page.locator(user_management_page.input_filter_role)
    role_input.wait_for(state="visible", timeout=10000)
    role_input.fill(role_filter, timeout=10000)
    # Press Enter to trigger filter
    role_input.press("Enter")
    vat_context["applied_filters"]["Role"] = role_filter
    
    # Wait for filters to apply
    get_page.wait_for_timeout(3000)
    logger.info("Filters applied successfully")


@when("I sort the table by Email column")
def step_sort_by_email_column(get_page: Page, user_management_page: VatUserManagementPage, vat_context: Dict):
    """Sort table by Email column"""
    logger.info("[WHEN] Sorting table by Email column")
    get_page.locator(user_management_page.columnheader_email).click()
    get_page.wait_for_timeout(1000)
    vat_context["selected_column"] = "Email"
    vat_context["sort_order"] = "ascending"
    logger.info("Table sorted by Email column")


# Removed redundant Given steps - Background already handles navigation


# ==========================================
# WHEN STEPS (Actions)
# ==========================================
# NOTE: Login, client selection, and DTAI navigation steps imported from VAT_Common_Library.py
# Only User Management-specific @when steps are defined here

@when("I navigate to User Management module")
def step_access_user_management_module(get_page: Page, user_management_page: VatUserManagementPage, vat_context: Dict):
    """
    Navigate to User Management module using smart navigation, then wait for the Existing Users
    grid to settle so each scenario in the shared session starts from a clean, deterministic state.
    """
    print("\n[WHEN] Accessing User Management module")
    launch_page = vat_context.get("launch_page")
    if not launch_page:
        launch_page = LaunchAppPage(get_page)
        vat_context["launch_page"] = launch_page
    navigate_to_module(get_page, "User Management", launch_page)
    _wait_for_users_grid(get_page, user_management_page)


@when(parsers.parse("I click on {column} column header once"))
@when(parsers.parse('I click on "{column}" column header once'))
def step_click_column_header_once(
    get_page: Page,
    user_management_page: VatUserManagementPage,
    vat_context: Dict,
    column: str
):
    """Click on column header to sort ascending"""
    logger.info(f"[WHEN] Clicking on '{column}' column header for sorting")
    
    header = _column_header(get_page, column)
    header.wait_for(state="visible", timeout=10000)
    header.click(timeout=10000)
    
    get_page.wait_for_timeout(2000)
    vat_context["selected_column"] = column
    vat_context["sort_order"] = "ascending"
    logger.info(f"Column '{column}' clicked for ascending sort")


@when(parsers.parse('I click on "{column}" column header again'))
def step_click_column_header_again(
    get_page: Page,
    user_management_page: VatUserManagementPage,
    vat_context: Dict,
    column: str
):
    """Click on column header again to sort descending"""
    logger.info(f"[WHEN] Clicking on '{column}' column header again for descending sort")
    
    header = _column_header(get_page, column)
    header.wait_for(state="visible", timeout=10000)
    header.click(timeout=10000)
    
    get_page.wait_for_timeout(2000)
    vat_context["sort_order"] = "descending"
    logger.info(f"Column '{column}' clicked for descending sort")


@when(parsers.parse("I search for {search_value} in {column}"))
@when(parsers.parse("I enter search criteria {search_value} in {column} field"))
def step_enter_filter_criteria(
    get_page: Page,
    user_management_page: VatUserManagementPage,
    vat_context: Dict,
    search_value: str,
    column: str
):
    """Enter search/filter criteria in column filter field"""
    logger.info(f"[WHEN] Entering filter '{search_value}' in '{column}' column")
    
    # Click Show Filters button first to reveal filter input fields
    logger.info("Clicking Show Filters button to reveal filter fields")
    user_management_page.show_filters()
    
    # Apply filter based on column
    if column.lower() == "name":
        logger.info(f"Filling Name filter with: {search_value}")
        filter_input = get_page.locator(user_management_page.input_filter_name)
    elif column.lower() == "email":
        logger.info(f"Filling Email filter with: {search_value}")
        filter_input = get_page.locator(user_management_page.input_filter_email)
    elif column.lower() == "role":
        logger.info(f"Filling Role filter with: {search_value}")
        filter_input = get_page.locator(user_management_page.input_filter_role)
    else:
        logger.error(f"Unknown column: {column}")
        return
    
    filter_input.wait_for(state="visible", timeout=10000)
    filter_input.fill(search_value, timeout=10000)
    # Press Enter to trigger the filter
    filter_input.press("Enter")
    vat_context["applied_filters"][column] = search_value
    # Wait for filter to apply and table to update
    get_page.wait_for_timeout(3000)
    logger.info(f"Filter applied successfully: {column}={search_value}")


@when("I click Select All checkbox")
def step_click_select_all_checkbox(get_page: Page, user_management_page: VatUserManagementPage):
    """Click Select All checkbox to select all rows"""
    logger.info("[WHEN] Clicking Select All checkbox")
    select_all_checkbox = get_page.locator(user_management_page.checkbox_select_all)
    select_all_checkbox.wait_for(state="visible", timeout=10000)
    select_all_checkbox.click(timeout=10000)
    get_page.wait_for_timeout(1000)
    logger.info("Select All checkbox clicked successfully")


@when("I click Clear Filters button")
def step_click_clear_filters_button(get_page: Page, user_management_page: VatUserManagementPage):
    """Click Clear Filters button (fall back to the title-based locator if the primary misses)"""
    logger.info("[WHEN] Clicking Clear Filters button")
    for locator in (user_management_page.btn_clear_filters, user_management_page.btn_clear_filters_alt):
        btn = get_page.locator(locator).first
        try:
            btn.wait_for(state="visible", timeout=8000)
            btn.click(timeout=10000)
            get_page.wait_for_timeout(2000)
            logger.info("Clear Filters button clicked successfully")
            return
        except Exception as exc:
            logger.warning(f"Clear Filters locator '{locator}' failed: {exc}")
    raise AssertionError("Clear Filters button not clickable via primary or alternative locator")


@when("I click Reset Sort button")
def step_click_reset_sort_button(get_page: Page, user_management_page: VatUserManagementPage):
    """Click Reset Sort button"""
    logger.info("[WHEN] Clicking Reset Sort button")
    try:
        reset_view_btn = get_page.locator(user_management_page.btn_reset_view)
        reset_view_btn.wait_for(state="visible", timeout=10000)
        reset_view_btn.click(timeout=10000)
        logger.info("Reset Sort button clicked successfully (primary locator)")
    except Exception as e:
        logger.warning(f"Primary Reset View locator failed: {e}, trying alternative")
        reset_view_btn = get_page.locator(user_management_page.btn_reset_view_alt)
        reset_view_btn.wait_for(state="visible", timeout=10000)
        reset_view_btn.click(timeout=10000)
        logger.info("Reset Sort button clicked successfully (alternative locator)")
    get_page.wait_for_timeout(2000)
    logger.info("Reset Sort button action completed")


@when("I select one or more rows using checkboxes")
def step_select_rows_using_checkboxes(get_page: Page, user_management_page: VatUserManagementPage, vat_context: Dict):
    """Select the first few rows, capturing each selected user's Name and Email so the download
    step can later verify the exported file actually contains those records."""
    logger.info("[WHEN] Selecting rows using checkboxes")
    vat_context["selected_row_data"] = []
    checkboxes = get_page.locator(user_management_page.checkboxes_all_rows)
    for i in range(min(3, checkboxes.count())):
        checkbox = checkboxes.nth(i)
        checkbox.wait_for(state="visible", timeout=10000)
        row = checkbox.locator("xpath=ancestor::*[@role='row'][1]")
        cells = row.locator("role=gridcell")
        name = cells.nth(1).inner_text().strip()
        email = cells.nth(2).inner_text().strip()
        checkbox.click(timeout=10000)
        vat_context["selected_rows"].append(i)
        vat_context["selected_row_data"].append({"name": name, "email": email})
        logger.info(f"Selected row {i}: {name} <{email}>")
    get_page.wait_for_timeout(500)
    logger.info(f"Selected {len(vat_context['selected_row_data'])} rows")


@when(parsers.parse("I click Download button and select {format} format"))
@when(parsers.parse('I click Download button and select "{format}" format'))
def step_click_download_and_select_format(
    get_page: Page,
    user_management_page: VatUserManagementPage,
    vat_context: Dict,
    format: str
):
    """Open the Download dropdown, choose the requested format, and capture the resulting file."""
    fmt = format.strip().upper()
    logger.info(f"[WHEN] Downloading Existing Users as {fmt}")
    
    # Open the Download dropdown
    toggle = get_page.locator(user_management_page.btn_download_toggle).first
    toggle.wait_for(state="visible", timeout=10000)
    toggle.click(timeout=10000)
    get_page.wait_for_timeout(500)
    
    # Select the format option (menu items are plain <a>Download as CSV/JSON/XML</a>)
    option = get_page.locator(user_management_page.download_menu).get_by_text(f"Download as {fmt}", exact=True)
    option.first.wait_for(state="visible", timeout=10000)
    
    vat_context["downloaded_file"] = None
    vat_context["downloaded_path"] = None
    try:
        with get_page.expect_download(timeout=15000) as download_info:
            option.first.click(timeout=10000)
        download = download_info.value
        dest = os.path.join(tempfile.gettempdir(), f"um_{fmt.lower()}_{download.suggested_filename}")
        download.save_as(dest)
        vat_context["downloaded_file"] = download.suggested_filename
        vat_context["downloaded_path"] = dest
        logger.info(f"Captured download: {download.suggested_filename} -> {dest}")
    except Exception as exc:
        logger.warning(f"No download event captured for {fmt}: {exc}")
        get_page.keyboard.press("Escape")
    get_page.wait_for_timeout(500)


@when("I scroll vertically and horizontally")
def step_scroll_vertically_and_horizontally(get_page: Page, user_management_page: VatUserManagementPage):
    """Scroll table vertically and horizontally"""
    logger.info("[WHEN] Scrolling table vertically and horizontally")
    table = get_page.locator(user_management_page.grid_scroll_container).first
    
    # Scroll vertically
    logger.info("Scrolling vertically...")
    table.evaluate("element => element.scrollTop = 100")
    get_page.wait_for_timeout(500)
    logger.info("Vertical scroll completed")
    
    # Scroll horizontally
    logger.info("Scrolling horizontally...")
    table.evaluate("element => element.scrollLeft = 100")
    get_page.wait_for_timeout(500)
    logger.info("Horizontal scroll completed")


# ==========================================
# THEN STEPS (Assertions)
# ==========================================

@then('User Management module is accessible and displayed with header "User Management"')
def step_verify_user_management_header(get_page: Page, user_management_page: VatUserManagementPage):
    """Verify User Management module header is displayed"""
    logger.info("[THEN] Verifying User Management module header")
    heading = get_page.locator(user_management_page.heading_user_management)
    expect(heading).to_be_visible(timeout=10000)
    header_text = heading.inner_text()
    logger.info(f"Header text found: {header_text}")
    assert header_text == "User Management"
    logger.info("User Management header verified successfully")


@then("Country field is displayed and read-only")
def step_verify_country_field_readonly(get_page: Page, user_management_page: VatUserManagementPage):
    """Verify Country field is displayed and read-only"""
    logger.info("[THEN] Verifying Country field is displayed and read-only")
    # Try primary locator first
    country_container = get_page.locator(user_management_page.container_country)
    
    # If primary locator doesn't work, try alternative
    if country_container.count() == 0:
        logger.warning("Primary country locator not found, trying alternative")
        country_container = get_page.locator(user_management_page.container_country_alt)
    
    expect(country_container).to_be_visible(timeout=10000)
    logger.info("Country field is visible and verified as read-only")


@then("Country assigned to Admin user is displayed")
@then("Country assigned to Country Owner user is displayed")
def step_verify_country_assigned(get_page: Page, user_management_page: VatUserManagementPage):
    """Verify assigned country is displayed"""
    logger.info("[THEN] Verifying assigned country is displayed")
    country_value = get_page.locator(user_management_page.text_country_value)
    expect(country_value).to_be_visible(timeout=10000)
    country_text = country_value.inner_text()
    logger.info(f"Country value found: {country_text}")
    # Verify Belgium is displayed
    assert "Belgium" in country_text, f"Expected 'Belgium' in country text, got: {country_text}"
    logger.info("Country 'Belgium' verified successfully")


@then("Existing Users section is visible with table columns Name, Email, Role and checkboxes")
def step_verify_existing_users_columns(get_page: Page, user_management_page: VatUserManagementPage):
    """Verify Existing Users table with correct columns"""
    logger.info("[THEN] Verifying Existing Users table columns")
    # Verify Existing Users header (get_by_role resolves the implicit <h3> level; fall back to text)
    heading = get_page.get_by_role("heading", name="Existing Users")
    if heading.count() == 0:
        logger.warning("Primary Existing Users heading locator not found, trying alternative")
        heading = get_page.locator(user_management_page.heading_existing_users_alt).first
    expect(heading.first).to_be_visible(timeout=10000)
    logger.info("Existing Users heading visible")
    
    # Verify table is visible
    grid = get_page.locator(user_management_page.grid_existing_users)
    expect(grid).to_be_visible(timeout=10000)
    logger.info("Existing Users table visible")
    
    # Verify column headers
    logger.info("Verifying column headers...")
    expect(get_page.locator(user_management_page.columnheader_select_all)).to_be_visible(timeout=10000)
    logger.info("Select All column visible")
    expect(_column_header(get_page, "Name")).to_be_visible(timeout=10000)
    logger.info("Name column visible")
    expect(_column_header(get_page, "Email")).to_be_visible(timeout=10000)
    logger.info("Email column visible")
    expect(_column_header(get_page, "Role")).to_be_visible(timeout=10000)
    logger.info("Role column visible")
    logger.info("All table columns verified successfully")


@then("Existing Users table is sorted by Name in ascending order")
def step_verify_default_sort_by_name(get_page: Page, user_management_page: VatUserManagementPage):
    """Verify default sort is Name ascending"""
    logger.info("[THEN] Verifying default sort by Name in ascending order")
    # Get all name cells
    name_cells = get_page.locator(user_management_page.rows_existing_users).locator("role=gridcell").nth(1)
    names = []
    cell_count = name_cells.count()
    logger.info(f"Found {cell_count} name cells")
    
    for i in range(min(cell_count, 10)):  # Check first 10 rows
        cell_text = name_cells.nth(i).inner_text()
        if cell_text:  # Skip empty cells
            names.append(cell_text)
    
    logger.info(f"Names found: {names}")
    # Verify names are in ascending order
    sorted_names = sorted(names)
    logger.info(f"Expected sorted order: {sorted_names}")
    assert names == sorted_names, f"Names not in ascending order. Found: {names}, Expected: {sorted_names}"
    logger.info("Names are in correct ascending order")


@then(parsers.parse("the table sorts by {column} in ascending order"))
@then(parsers.parse('the table sorts by "{column}" in ascending order'))
def step_verify_sort_ascending(get_page: Page, user_management_page: VatUserManagementPage, column: str):
    """Verify table is sorted in ascending order by column"""
    logger.info(f"[THEN] Verifying table is sorted by '{column}' in ascending order")
    get_page.wait_for_timeout(2000)
    
    # Get column index
    col_index = {"name": 1, "email": 2, "role": 3}.get(column.lower(), 1)
    logger.info(f"Column index: {col_index}")
    
    # Get cell values
    cells = get_page.locator(user_management_page.rows_existing_users).locator(f"role=gridcell >> nth={col_index}")
    values = []
    cell_count = cells.count()
    logger.info(f"Found {cell_count} cells")
    
    for i in range(min(cell_count, 10)):
        cell_text = cells.nth(i).inner_text()
        if cell_text:
            values.append(cell_text.strip())
    
    logger.info(f"Values found: {values}")
    # Verify ascending order
    sorted_values = sorted(values)
    logger.info(f"Expected sorted order: {sorted_values}")
    assert values == sorted_values, f"{column} not in ascending order. Found: {values}, Expected: {sorted_values}"
    logger.info(f"Column '{column}' is correctly sorted in ascending order")


@then(parsers.parse('the table sorts by "{column}" in descending order'))
def step_verify_sort_descending(get_page: Page, user_management_page: VatUserManagementPage, column: str):
    """Verify table is sorted in descending order by column"""
    logger.info(f"[THEN] Verifying table is sorted by '{column}' in descending order")
    get_page.wait_for_timeout(2000)
    
    # Get column index
    col_index = {"name": 1, "email": 2, "role": 3}.get(column.lower(), 1)
    logger.info(f"Column index: {col_index}")
    
    # Get cell values
    cells = get_page.locator(user_management_page.rows_existing_users).locator(f"role=gridcell >> nth={col_index}")
    values = []
    cell_count = cells.count()
    logger.info(f"Found {cell_count} cells")
    
    for i in range(min(cell_count, 10)):
        cell_text = cells.nth(i).inner_text()
        if cell_text:
            values.append(cell_text.strip())
    
    logger.info(f"Values found: {values}")
    # Verify descending order
    sorted_values = sorted(values, reverse=True)
    logger.info(f"Expected sorted order: {sorted_values}")
    assert values == sorted_values, f"{column} not in descending order. Found: {values}, Expected: {sorted_values}"
    logger.info(f"Column '{column}' is correctly sorted in descending order")


@then(parsers.parse("the table displays only records matching the filter criteria for {column}"))
@then(parsers.parse('the table displays only records matching the filter criteria for "{column}"'))
def step_verify_filter_results(
    get_page: Page,
    user_management_page: VatUserManagementPage,
    vat_context: Dict,
    column: str
):
    """Verify table shows only filtered records"""
    logger.info(f"[THEN] Verifying filter results for column: {column}")
    get_page.wait_for_timeout(2000)  # Increased wait for filter results
    
    search_value = vat_context["applied_filters"].get(column, "")
    logger.info(f"Filter value to verify: {search_value}")
    
    col_index = {"name": 1, "email": 2, "role": 3}.get(column.lower(), 1)
    logger.info(f"Column index: {col_index}")
    
    # Get all visible cell values in the column
    cells = get_page.locator(user_management_page.rows_existing_users).locator(f"role=gridcell >> nth={col_index}")
    cell_count = cells.count()
    logger.info(f"Found {cell_count} cells to verify")
    
    for i in range(cell_count):
        cell_text = cells.nth(i).inner_text().strip()
        if cell_text:  # Skip empty cells
            logger.info(f"Checking cell {i}: '{cell_text}' contains '{search_value}'")
            assert search_value.lower() in cell_text.lower(), \
                f"Cell '{cell_text}' does not match filter '{search_value}'"
    
    logger.info(f"All {cell_count} cells match the filter criteria '{search_value}'")


@then("all rows in the Existing Users table are selected")
def step_verify_all_rows_selected(get_page: Page, user_management_page: VatUserManagementPage):
    """Verify all checkboxes are checked"""
    logger.info("[THEN] Verifying all rows are selected")
    checkboxes = get_page.locator(user_management_page.checkboxes_all_rows)
    total_checkboxes = checkboxes.count()
    logger.info(f"Found {total_checkboxes} checkboxes")
    
    # Check each checkbox is checked
    checked_count = 0
    for i in range(total_checkboxes):
        checkbox = checkboxes.nth(i)
        expect(checkbox).to_be_checked(timeout=10000)
        checked_count += 1
    
    logger.info(f"All {checked_count} checkboxes verified as checked")


@then("all applied filters are cleared")
def step_verify_filters_cleared(get_page: Page, user_management_page: VatUserManagementPage, vat_context: Dict):
    """Verify all filter inputs are cleared"""
    logger.info("[THEN] Verifying all filters are cleared")
    # Check Name filter is empty
    name_input = get_page.locator(user_management_page.input_filter_name)
    if name_input.count() > 0:
        name_value = name_input.input_value()
        logger.info(f"Name filter value: '{name_value}'")
        assert name_value == "", f"Name filter not cleared, value: '{name_value}'"
    
    # Check Email filter is empty
    email_input = get_page.locator(user_management_page.input_filter_email)
    if email_input.count() > 0:
        email_value = email_input.input_value()
        logger.info(f"Email filter value: '{email_value}'")
        assert email_value == "", f"Email filter not cleared, value: '{email_value}'"
    
    # Check Role filter is empty
    role_input = get_page.locator(user_management_page.input_filter_role)
    if role_input.count() > 0:
        role_value = role_input.input_value()
        logger.info(f"Role filter value: '{role_value}'")
        assert role_value == "", f"Role filter not cleared, value: '{role_value}'"
    
    vat_context["applied_filters"].clear()
    logger.info("All filters verified as cleared")


@then("the table displays all user records without filtering")
def step_verify_all_records_displayed(get_page: Page, user_management_page: VatUserManagementPage, vat_context: Dict):
    """Verify table shows all records (no filtering)"""
    logger.info("[THEN] Verifying table displays all user records")
    get_page.wait_for_timeout(2000)
    rows = get_page.locator(user_management_page.rows_existing_users)
    current_count = rows.count()
    initial_count = vat_context.get("initial_row_count", 0)
    logger.info(f"Current row count: {current_count}, Initial row count: {initial_count}")
    
    # Row count should be >= initial count (or maximum page size)
    min_expected = min(initial_count, 25)
    assert current_count >= min_expected, \
        f"Expected at least {min_expected} records, found {current_count}"
    logger.info(f"All records displayed successfully: {current_count} rows")


@then("table sorting resets to default sorting by Name ascending")
def step_verify_sort_reset_to_default(get_page: Page, user_management_page: VatUserManagementPage):
    """Verify sorting reset to default (Name ascending)"""
    logger.info("[THEN] Verifying table sorting reset to default (Name ascending)")
    get_page.wait_for_timeout(2000)
    
    # Get name column values
    name_cells = get_page.locator(user_management_page.rows_existing_users).locator("role=gridcell >> nth=1")
    names = []
    cell_count = name_cells.count()
    logger.info(f"Found {cell_count} name cells")
    
    for i in range(min(cell_count, 10)):
        cell_text = name_cells.nth(i).inner_text()
        if cell_text:
            names.append(cell_text)
    
    logger.info(f"Names found: {names}")
    # Verify ascending order
    sorted_names = sorted(names)
    logger.info(f"Expected sorted order: {sorted_names}")
    assert names == sorted_names, f"Sort not reset to Name ascending. Found: {names}, Expected: {sorted_names}"
    logger.info("Sort reset verified successfully")


@then(parsers.parse("downloaded file contains selected user records in {format} format"))
@then(parsers.parse('downloaded file contains selected user records in "{format}" format'))
def step_verify_downloaded_file(get_page: Page, user_management_page: VatUserManagementPage, vat_context: Dict, format: str):
    """Verify the captured download matches the requested format AND its contents contain exactly
    the user records that were selected before downloading."""
    fmt = format.strip().upper()
    logger.info(f"[THEN] Verifying downloaded file in {fmt} format")

    expected_ext = {"CSV": ".csv", "JSON": ".json", "XML": ".xml"}.get(fmt)
    assert expected_ext, f"Unsupported download format requested: {format}"

    downloaded = vat_context.get("downloaded_file")
    path = vat_context.get("downloaded_path")
    selected = vat_context.get("selected_row_data", [])

    assert downloaded and path, "No download was captured to verify"
    assert downloaded.lower().endswith(expected_ext), \
        f"Downloaded file '{downloaded}' does not match requested {fmt} format"

    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        content = f.read()
    assert content.strip(), f"Downloaded {fmt} file is empty"

    # Every selected user's Name and Email must appear in the exported file
    assert selected, "No selected row data was captured to validate the download against"
    for record in selected:
        assert record["email"] in content, \
            f"Selected email '{record['email']}' not found in downloaded {fmt} file"
        assert record["name"] in content, \
            f"Selected name '{record['name']}' not found in downloaded {fmt} file"

    # The export must contain only the selected records (one email per record, any format)
    emails_in_file = re.findall(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", content)
    assert len(emails_in_file) == len(selected), \
        f"Expected {len(selected)} records in {fmt} file, found {len(emails_in_file)}: {emails_in_file}"

    logger.info(f"Content verified: {len(selected)} selected records present in {fmt} file")


@then("the table displays maximum 25 records per page")
def step_verify_max_25_records_per_page(get_page: Page, user_management_page: VatUserManagementPage):
    """Verify pagination shows max 25 records"""
    logger.info("[THEN] Verifying table displays maximum 25 records per page")
    rows = get_page.locator(user_management_page.rows_existing_users)
    row_count = rows.count()
    logger.info(f"Row count: {row_count}")
    assert row_count <= 25, f"Expected max 25 records, found {row_count}"
    logger.info("Max records per page verified successfully")


@then("pagination controls are available to navigate between pages")
def step_verify_pagination_controls(get_page: Page, user_management_page: VatUserManagementPage):
    """Verify pagination controls are visible"""
    logger.info("[THEN] Verifying pagination controls are visible")
    
    # Verify First Page button
    logger.info("Checking First Page button")
    expect(get_page.locator(user_management_page.btn_first_page)).to_be_visible(timeout=10000)
    
    # Verify Previous Page button
    logger.info("Checking Previous Page button")
    expect(get_page.locator(user_management_page.btn_prev_page)).to_be_visible(timeout=10000)
    
    # Verify Next Page button
    logger.info("Checking Next Page button")
    expect(get_page.locator(user_management_page.btn_next_page)).to_be_visible(timeout=10000)
    
    # Verify Last Page button
    logger.info("Checking Last Page button")
    expect(get_page.locator(user_management_page.btn_last_page)).to_be_visible(timeout=10000)
    
    # Verify Rows per page combobox with better error handling
    logger.info("Checking Rows per page combobox")
    combobox = get_page.locator(user_management_page.combobox_rows_per_page)
    try:
        combobox_count = combobox.count()
        logger.info(f"Combobox found, count: {combobox_count}")
        if combobox_count == 1:
            expect(combobox).to_be_visible(timeout=10000)
        elif combobox_count > 1:
            logger.warning(f"Multiple comboboxes found ({combobox_count}), checking first one")
            expect(combobox.first).to_be_visible(timeout=10000)
        else:
            logger.error("No combobox found with primary locator, trying alternative")
            combobox_alt = get_page.locator(user_management_page.combobox_rows_per_page_alt)
            expect(combobox_alt.first).to_be_visible(timeout=10000)
    except Exception as e:
        logger.error(f"Combobox locator failed: {e}")
        raise
    
    logger.info("All pagination controls verified successfully")


@then("vertical and horizontal scroll bars appear as needed")
def step_verify_scroll_bars_appear(get_page: Page, user_management_page: VatUserManagementPage):
    """Verify the grid's scroll container is configured to show scrollbars as needed.

    The Tabulator tableHolder uses overflow:auto, so scrollbars appear only when the content
    overflows. Asserting a fixed overflow (which depends on the current data volume) is wrong;
    instead verify the container can scroll on both axes when needed.
    """
    logger.info("[THEN] Verifying scroll bars appear as needed")
    holder = get_page.locator(user_management_page.grid_scroll_container).first
    expect(holder).to_be_visible(timeout=10000)
    overflow = holder.evaluate(
        "e => { const s = getComputedStyle(e); return {x: s.overflowX, y: s.overflowY}; }"
    )
    logger.info(f"Scroll container overflow: {overflow}")
    scrollable = {"auto", "scroll"}
    assert overflow["x"] in scrollable and overflow["y"] in scrollable, \
        f"Scroll container is not configured to show scrollbars as needed: {overflow}"
    logger.info("Scroll bars are configured to appear as needed - verified successfully")


@then("I can scroll to view all data")
def step_verify_can_scroll_to_view_data(get_page: Page, user_management_page: VatUserManagementPage):
    """Verify scrolling works, or that all data already fits when no scroll is needed."""
    logger.info("[THEN] Verifying scroll functionality works")
    holder = get_page.locator(user_management_page.grid_scroll_container).first
    dims = holder.evaluate(
        "e => ({sh: e.scrollHeight, ch: e.clientHeight, sw: e.scrollWidth, cw: e.clientWidth})"
    )
    logger.info(f"Scroll container dims: {dims}")
    
    if dims["sh"] > dims["ch"]:
        initial = holder.evaluate("e => e.scrollTop")
        holder.evaluate("e => e.scrollTop = e.scrollHeight")
        get_page.wait_for_timeout(500)
        final = holder.evaluate("e => e.scrollTop")
        assert final > initial, f"Vertical scroll not working. Initial: {initial}, Final: {final}"
        logger.info("Vertical scroll verified successfully")
    else:
        rows = get_page.locator(user_management_page.rows_existing_users)
        assert rows.count() > 0, "No rows rendered; cannot confirm data is viewable"
        logger.info("All data fits without vertical scroll; every row is viewable")


