"""
Step definitions for Global Insights And Data Enrichment For e-Invoicing Data Lake IP module.
Connects Vat_Data_Lake_IP.feature with vat_data_lake_ip_page.py.
"""
import logging
from typing import Dict, Any

import pytest
from playwright.sync_api import Page
from pytest_bdd import scenario, when, then, parsers

from pageobjects.vat_data_lake_ip_page import VatDataLakeIPPage
from tests.step_defs.VAT_Common_Library import *  # noqa: F401,F403

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(name)s - %(message)s")


@pytest.fixture()
def get_page(vat_session) -> Page:
    """[Option B] Reuse the single session-scoped authenticated page across all Data Lake IP
    scenarios, so login + client selection + DTAI navigation happen only once for the run.
    Overrides the function-scoped get_page from conftest for this module only."""
    return vat_session["page"]


@pytest.fixture()
def vat_context(get_page: Page) -> Dict[str, Any]:
    logger.info("Initializing VAT context for Data Lake IP test")
    return {
        "user_role": "Admin",
    }


@pytest.fixture()
def data_lake_ip_page(get_page: Page) -> VatDataLakeIPPage:
    return VatDataLakeIPPage(get_page)


@scenario(
    "../features/Vat_Data_Lake_IP.feature",
    "Verify authorized Global Insights And Data Enrichment For e-Invoicing user can navigate to Data Lake IP tab and all mandatory page sections render successfully",
)
def test_data_lake_ip_module_access(get_page, vat_context, data_lake_ip_page):
    pass


@when("I navigate to Data Lake IP tab")
def step_navigate_to_data_lake_ip_tab(data_lake_ip_page: VatDataLakeIPPage):
    logger.info("[WHEN] Navigating to Data Lake IP tab")
    clicked = data_lake_ip_page.navigate_to_data_lake_ip_tab()
    assert clicked, "Could not click Data Lake IP tab"
    assert data_lake_ip_page.is_data_lake_ip_tab_accessible(), "Data Lake IP tab is not accessible after navigation"
    logger.info("[OK] Data Lake IP tab opened")


@then(parsers.parse('Data Lake IP tab is accessible and displayed with header "{header}"'))
@then('Data Lake IP tab is accessible and displayed with header "Data Lake IP"')
def step_verify_data_lake_ip_header(data_lake_ip_page: VatDataLakeIPPage, header: str = "Data Lake IP"):
    logger.info(f"[THEN] Verifying Data Lake IP header: {header}")
    assert data_lake_ip_page.is_data_lake_ip_tab_accessible(), "Data Lake IP tab is not accessible"
    actual = data_lake_ip_page.get_data_lake_ip_header()
    assert header.lower() in actual.lower(), f"Expected header '{header}' but got '{actual}'"
    logger.info(f"[OK] Data Lake IP header verified: {actual}")


@then("Data Lake IP tab is showing 4 sections Business Rules & Logic section,Processing Logic Flow section,Dashboard Filters section and Data Lake IP Dashboard section.")
def step_verify_all_mandatory_sections(data_lake_ip_page: VatDataLakeIPPage):
    logger.info("[THEN] Verifying all mandatory Data Lake IP sections")
    missing = data_lake_ip_page.get_missing_mandatory_sections()
    assert not missing, f"Missing mandatory Data Lake IP sections: {', '.join(missing)}"
    logger.info("[OK] All mandatory Data Lake IP sections are visible")


@then("Data Lake IP filter section is visible")
def step_verify_filter_section(data_lake_ip_page: VatDataLakeIPPage):
    logger.info("[THEN] Verifying Data Lake IP filter section visibility")
    assert data_lake_ip_page.is_data_lake_ip_filter_section_visible(), "Data Lake IP filter section is not visible"
    logger.info("[OK] Data Lake IP filter section is visible")


@then("Data Lake IP dashboard section is visible")
def step_verify_dashboard_section(data_lake_ip_page: VatDataLakeIPPage):
    logger.info("[THEN] Verifying Data Lake IP dashboard section visibility")
    assert data_lake_ip_page.is_data_lake_ip_dashboard_section_visible(), "Data Lake IP dashboard section is not visible"
    logger.info("[OK] Data Lake IP dashboard section is visible")


@then("Country field is displayed and read-only")
def step_verify_country_readonly(data_lake_ip_page: VatDataLakeIPPage):
    logger.info("[THEN] Verifying Country field is displayed and read-only")
    assert data_lake_ip_page.is_country_field_visible(), "Country field is not visible in Data Lake IP tab"
    assert data_lake_ip_page.is_country_field_readonly(), "Country field appears editable in Data Lake IP tab"
    logger.info("[OK] Country field is displayed and read-only")
