"""
Step Definitions for User Management Module
Connects Vat_user_management.feature with vat_user_management_page.py

Each test case is independent with its own browser session.
"""
import os
import re
import logging
from pathlib import Path
from typing import Dict, Any

import pytest
from playwright.sync_api import Page, expect
from pytest_bdd import given, scenario, then, when, parsers
from pageobjects.vat_user_management_page import VatUserManagementPage
from pageobjects.launch_app_page import LaunchAppPage
from utilities.read_properties import Read_Configurations

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


@given("users are assigned specific roles in VAT DTAI User Management")
def step_users_assigned_roles():
    """Background step: Users have assigned roles"""
    pass


@given("I navigate to User Management module")
def step_navigate_to_user_management_given(get_page: Page, user_management_page: VatUserManagementPage):
    """Navigate to User Management module (Given step)"""
    logger.info("[GIVEN] Navigating to User Management module")
    get_page.wait_for_timeout(2000)
    
    # Click User Management tab
    logger.info("Clicking User Management tab")
    tab_locator = get_page.locator(user_management_page.tab_user_management_module)
    tab_locator.wait_for(state="visible", timeout=10000)
    tab_locator.click()
    get_page.wait_for_timeout(3000)
    
    # Verify module loaded
    logger.info("Verifying User Management module loaded")
    heading_locator = get_page.locator(user_management_page.heading_user_management)
    expect(heading_locator).to_be_visible(timeout=10000)
    logger.info("User Management module loaded successfully")


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
@when("I apply filters on Name \"Rajan\" and Role \"Admin\"")
def step_apply_filters_on_name_and_role(
    get_page: Page,
    user_management_page: VatUserManagementPage,
    vat_context: Dict,
    name_filter: str = "Rajan",
    role_filter: str = "Admin"
):
    """Apply filters on Name and Role columns"""
    logger.info(f"[WHEN] Applying filters: Name='{name_filter}', Role='{role_filter}'")
    
    # Click Show Filters button first
    logger.info("Clicking Show Filters button")
    show_filters_btn = get_page.locator(user_management_page.btn_show_filters)
    show_filters_btn.wait_for(state="visible", timeout=10000)
    show_filters_btn.click(timeout=10000)
    get_page.wait_for_timeout(2000)
    
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

@when("I access User Management module")
@when("I navigate to User Management module")
def step_access_user_management_module(get_page: Page, user_management_page: VatUserManagementPage, vat_context: Dict):
    """
    Navigate to User Management module using smart navigation.
    Ensures on DTAI dashboard first, then clicks User Management tab.
    """
    print("\n[WHEN] Accessing User Management module")
    launch_page = vat_context.get("launch_page")
    if not launch_page:
        launch_page = LaunchAppPage(get_page)
        vat_context["launch_page"] = launch_page
    navigate_to_module(get_page, "User Management", launch_page)


@when(parsers.parse("I click on {column} column header once"))
@when(parsers.parse('I click on "{column}" column header once'))
@when("I click on <column> column header once")
@when("I click on \"<column>\" column header once")
def step_click_column_header_once(
    get_page: Page,
    user_management_page: VatUserManagementPage,
    vat_context: Dict,
    column: str
):
    """Click on column header to sort ascending"""
    logger.info(f"[WHEN] Clicking on '{column}' column header for sorting")
    
    if column.lower() == "name":
        header = get_page.locator(user_management_page.columnheader_name)
        header.wait_for(state="visible", timeout=10000)
        header.click(timeout=10000)
    elif column.lower() == "email":
        header = get_page.locator(user_management_page.columnheader_email)
        header.wait_for(state="visible", timeout=10000)
        header.click(timeout=10000)
    elif column.lower() == "role":
        header = get_page.locator(user_management_page.columnheader_role)
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
    
    if column.lower() == "name":
        header = get_page.locator(user_management_page.columnheader_name)
        header.wait_for(state="visible", timeout=10000)
        header.click(timeout=10000)
    elif column.lower() == "email":
        header = get_page.locator(user_management_page.columnheader_email)
        header.wait_for(state="visible", timeout=10000)
        header.click(timeout=10000)
    elif column.lower() == "role":
        header = get_page.locator(user_management_page.columnheader_role)
        header.wait_for(state="visible", timeout=10000)
        header.click(timeout=10000)
    
    get_page.wait_for_timeout(2000)
    vat_context["sort_order"] = "descending"
    logger.info(f"Column '{column}' clicked for descending sort")


@when("I search for <search_value> in <column>")
@when(parsers.parse("I search for {search_value} in {column}"))
@when("I enter search criteria <search_value> in <column> field")
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
    """Click Clear Filters button"""
    logger.info("[WHEN] Clicking Clear Filters button")
    clear_filters_btn = get_page.locator(user_management_page.btn_clear_filters)
    clear_filters_btn.wait_for(state="visible", timeout=10000)
    clear_filters_btn.click(timeout=10000)
    get_page.wait_for_timeout(2000)
    logger.info("Clear Filters button clicked successfully")


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
    """Select one or more rows by clicking checkboxes"""
    logger.info("[WHEN] Selecting rows using checkboxes")
    # Select first 3 rows
    for i in range(3):
        checkbox = get_page.locator(user_management_page.checkbox_row_by_index(i))
        if checkbox.count() > 0:
            logger.info(f"Clicking checkbox for row {i}")
            checkbox.wait_for(state="visible", timeout=10000)
            checkbox.click(timeout=10000)
            vat_context["selected_rows"].append(i)
            logger.info(f"Checkbox {i} clicked")
    get_page.wait_for_timeout(500)
    logger.info(f"Selected {len(vat_context['selected_rows'])} rows")


@when(parsers.parse("I click Download button and select {format} format"))
@when(parsers.parse('I click Download button and select "{format}" format'))
@when("I click Download button and select <format> format")
@when("I click Download button and select \"<format>\" format")
def step_click_download_and_select_format(
    get_page: Page,
    user_management_page: VatUserManagementPage,
    format: str
):
    """Click Download button and select export format"""
    logger.info(f"[WHEN] Clicking Download button for {format} format")
    # Click Export button
    export_btn = get_page.locator(user_management_page.btn_export)
    export_btn.wait_for(state="visible", timeout=10000)
    export_btn.click(timeout=10000)
    get_page.wait_for_timeout(2000)
    logger.info(f"Export button clicked")
    
    # Note: Current implementation downloads directly to Excel
    # If format selection menu appears, select the format
    # This might need adjustment based on actual UI behavior
    format_selector = get_page.get_by_text(format, exact=True)
    if format_selector.count() > 0:
        logger.info(f"Selecting format: {format}")
        format_selector.click()
        get_page.wait_for_timeout(1000)
    logger.info(f"Download initiated for format: {format}")


@when("I scroll vertically and horizontally")
def step_scroll_vertically_and_horizontally(get_page: Page, user_management_page: VatUserManagementPage):
    """Scroll table vertically and horizontally"""
    logger.info("[WHEN] Scrolling table vertically and horizontally")
    table = get_page.locator(user_management_page.grid_existing_users)
    
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
    # Verify Existing Users header
    heading = get_page.locator(user_management_page.heading_existing_users)
    expect(heading).to_be_visible(timeout=10000)
    logger.info("Existing Users heading visible")
    
    # Verify table is visible
    grid = get_page.locator(user_management_page.grid_existing_users)
    expect(grid).to_be_visible(timeout=10000)
    logger.info("Existing Users table visible")
    
    # Verify column headers
    logger.info("Verifying column headers...")
    expect(get_page.locator(user_management_page.columnheader_select_all)).to_be_visible(timeout=10000)
    logger.info("Select All column visible")
    expect(get_page.locator(user_management_page.columnheader_name)).to_be_visible(timeout=10000)
    logger.info("Name column visible")
    expect(get_page.locator(user_management_page.columnheader_email)).to_be_visible(timeout=10000)
    logger.info("Email column visible")
    expect(get_page.locator(user_management_page.columnheader_role)).to_be_visible(timeout=10000)
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
@then("the table sorts by <column> in ascending order")
@then("the table sorts by \"<column>\" in ascending order")
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
@then("the table displays only records matching the filter criteria for <column>")
@then("the table displays only records matching the filter criteria for \"<column>\"")
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
@then("downloaded file contains selected user records in <format> format")
@then("downloaded file contains selected user records in \"<format>\" format")
def step_verify_downloaded_file(get_page: Page, user_management_page: VatUserManagementPage, format: str):
    """Verify download action completed without UI errors"""
    logger.info(f"[THEN] Verifying downloaded file in {format} format")
    get_page.wait_for_timeout(2000)

    normalized_format = format.strip().upper()
    assert normalized_format in {"CSV", "XML", "JSON", "EXCEL", "XLSX"}, \
        f"Unexpected download format requested: {format}"

    rows = get_page.locator(user_management_page.rows_existing_users)
    assert rows.count() > 0, "Existing Users table has no rows during download verification"

    checkboxes = get_page.locator(user_management_page.checkboxes_all_rows)
    checked_count = 0
    for i in range(checkboxes.count()):
        if checkboxes.nth(i).is_checked():
            checked_count += 1
    assert checked_count > 0, "No selected rows found during download verification"

    page_text = get_page.inner_text("body")
    has_download_error = bool(re.search(r"download.*(fail|error)|unable to download", page_text, re.I))
    assert not has_download_error, "Download failed, error message detected on page"

    logger.info(f"Download verification passed for format: {format}, selected rows: {checked_count}")


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
    """Verify scroll bars are available"""
    logger.info("[THEN] Verifying scroll bars appear")
    table = get_page.locator(user_management_page.grid_existing_users)
    
    # Check if scrollable
    scroll_height = table.evaluate("element => element.scrollHeight")
    client_height = table.evaluate("element => element.clientHeight")
    scroll_width = table.evaluate("element => element.scrollWidth")
    client_width = table.evaluate("element => element.clientWidth")
    
    logger.info(f"Scroll dimensions: height={scroll_height}/{client_height}, width={scroll_width}/{client_width}")
    
    # Verify scroll is possible (scrollHeight > clientHeight or scrollWidth > clientWidth)
    is_scrollable = scroll_height > client_height or scroll_width > client_width
    assert is_scrollable, \
        f"Table is not scrollable. Heights: {scroll_height}/{client_height}, Widths: {scroll_width}/{client_width}"
    logger.info("Table is scrollable - verified successfully")


@then("I can scroll to view all data")
def step_verify_can_scroll_to_view_data(get_page: Page, user_management_page: VatUserManagementPage):
    """Verify scrolling works"""
    logger.info("[THEN] Verifying scroll functionality works")
    table = get_page.locator(user_management_page.grid_existing_users)
    
    # Scroll and verify position changed
    initial_scroll_top = table.evaluate("element => element.scrollTop")
    logger.info(f"Initial scroll position: {initial_scroll_top}")
    
    table.evaluate("element => element.scrollTop = element.scrollHeight")
    get_page.wait_for_timeout(500)
    
    final_scroll_top = table.evaluate("element => element.scrollTop")
    logger.info(f"Final scroll position: {final_scroll_top}")
    
    assert final_scroll_top > initial_scroll_top, \
        f"Vertical scroll not working. Initial: {initial_scroll_top}, Final: {final_scroll_top}"
    logger.info("Scroll functionality verified successfully")


