import logging
from pageobjects.base_page import BasePage

# Configure logger for this module
logger = logging.getLogger(__name__)


class VatUserManagementPage(BasePage):
    """
    Page Object Model for Global Insights And Data Enrichment For e-Invoicing User Management Module
    Based on Feature: Global Insights And Data Enrichment For e-Invoicing User Management - P1 Test Cases
    Supports role-based access for Admin and Country Owner
    """
    
    def __init__(self, get_page):
        super().__init__(get_page)
        
        # ==========================================
        # MODULE NAVIGATION LOCATORS
        # ==========================================
        # Locator for module header/title "User Management"
        self.heading_user_management = "role=heading[level=2][name='User Management']"
        
        # ==========================================
        # COUNTRY FIELD LOCATORS
        # ==========================================
        # Locator for Country information container (uses unique ID from User Management module)
        self.container_country = "#vatdtai_usermanagement_country"
        # Alternative locator using class name for the country display element
        self.container_country_alt = ".vatdtai-country-display"
        # Locator for the Country value text
        self.text_country_value = "#vatdtai_usermanagement_country"
        
        # ==========================================
        # EXISTING USERS SECTION LOCATORS
        # ==========================================
        # Locator for "Existing Users" section header (implicit-level <h3>; the role= string
        # engine does not compute implicit heading levels, so match by name only)
        self.heading_existing_users = "role=heading[name='Existing Users']"
        self.heading_existing_users_alt = "text=Existing Users"
        
        # Locator for Existing Users table grid
        self.grid_existing_users = "role=grid"
        
        # ==========================================
        # EXISTING USERS TABLE - COLUMN HEADERS
        # ==========================================
        # Locator for "Select all on this page" column header
        self.columnheader_select_all = "role=columnheader[name='Select all on this page']"
        
        # Locator for "Email" column header
        self.columnheader_email = "role=columnheader[name='⋮ Email']"
        
        # ==========================================
        # EXISTING USERS TABLE - ROWS & CELLS
        # ==========================================
        # Locator for all table rows
        self.rows_existing_users = "role=grid >> role=row"
        
        # ==========================================
        # CHECKBOX LOCATORS
        # ==========================================
        # Locator for "Select All" checkbox in table header
        self.checkbox_select_all = "role=columnheader[name='Select all on this page'] >> role=checkbox"
        
        # Locator for all row checkboxes (for verification and selection)
        self.checkboxes_all_rows = "role=gridcell[name='Select row'] >> role=checkbox"
        
        # ==========================================
        # TOOLBAR CONTROLS
        # ==========================================
        # Download control - a Bootstrap dropdown whose toggle opens a menu with the supported
        # export formats (Download as CSV / JSON / XML). Select a format to trigger the download.
        self.btn_download_toggle = "[data-id='vatdtai_um_download'] >> button.dropdown-toggle"
        self.download_menu = "[data-id='vatdtai_um_download'] .dropdown-menu"
        
        # Toolbar buttons. The title-based locators are the PRIMARY ones because run analysis
        # (2026-08-25) showed the data-id wrappers are not present in the live DOM: every
        # data-id primary click timed out (30s/8s/10s) before falling back to the title
        # locator that actually works. The data-id form is kept as a defensive fallback in
        # case a future build restores those wrappers.
        # Show Filters button - toggle filters visibility.
        self.btn_show_filters = "[title='Show Filters'] >> button"
        self.btn_show_filters_alt = "[data-id='btnShowFilterDiv'] >> button"
        
        # Clear Filters button - clears all filter values.
        self.btn_clear_filters = "[title='Clear Filters'] >> button"
        self.btn_clear_filters_alt = "[data-id='btnClearFilterDiv'] >> button"
        
        # Reset View button - resets sorting and filters.
        self.btn_reset_view = "[title='Reset View'] >> button"
        self.btn_reset_view_alt = "[data-id='btnResetViewDiv'] >> button"
        
        # ==========================================
        # PAGINATION CONTROLS
        # ==========================================
        # Locator for rows per page dropdown (Tabulator page-size select in the footer)
        self.combobox_rows_per_page = "select.tabulator-page-size"
        self.combobox_rows_per_page_alt = "div.tabulator-footer select"
        
        # Locator for First Page button
        self.btn_first_page = "role=button[name='First Page']"
        
        # Locator for Previous Page button
        self.btn_prev_page = "role=button[name='Prev Page']"
        
        # Locator for Next Page button
        self.btn_next_page = "role=button[name='Next Page']"
        
        # Locator for Last Page button
        self.btn_last_page = "role=button[name='Last Page']"
        
        # Real scrollable container for the Existing Users grid (Tabulator's tableHolder has
        # overflow:auto; the outer role=grid/.tabulator wrapper is overflow:hidden and never scrolls)
        self.grid_scroll_container = ".tabulator-tableHolder"
        
        # ==========================================
        # FILTER INPUT FIELDS (visible after clicking Show Filters button)
        # ==========================================
        # Filter input fields for Name, Email, Role columns
        self.input_filter_name = "role=columnheader[name*='Name'] >> role=searchbox"
        self.input_filter_email = "role=columnheader[name*='Email'] >> role=searchbox"
        self.input_filter_role = "role=columnheader[name*='Role'] >> role=searchbox"
        
        # NOTE: The download dropdown supports CSV, JSON and XML (no Excel). Each option triggers
        # a real browser download (Users_Export.<ext>); the download steps capture and verify it.
        
        # ==========================================
        # UTILITY METHODS
        # ==========================================
    
    def show_filters(self):
        """Click Show Filters button to reveal filter input fields below column headers"""
        logger.info("Clicking Show Filters button to reveal filter input fields")
        try:
            # Try primary locator first
            self.element_click(self.btn_show_filters)
            logger.info("Successfully clicked Show Filters button (primary locator)")
        except Exception as e:
            logger.warning(f"Primary Show Filters locator failed: {e}, trying alternative")
            self.element_click(self.btn_show_filters_alt)
            logger.info("Successfully clicked Show Filters button (alternative locator)")
        # Wait for filter fields to become visible
        self.page.wait_for_timeout(1000)
        logger.info("Filter input fields should now be visible")
