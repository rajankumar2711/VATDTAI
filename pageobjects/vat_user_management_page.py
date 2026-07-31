import logging
from pageobjects.base_page import BasePage
from conftest import get_page

# Configure logger for this module
logger = logging.getLogger(__name__)


class VatUserManagementPage(BasePage):
    """
    Page Object Model for VAT DTAI User Management Module
    Based on Feature: VAT DTAI User Management - P1 Test Cases
    Supports role-based access for Admin and Country Owner
    """
    
    def __init__(self, get_page):
        super().__init__(get_page)
        
        # ==========================================
        # MODULE NAVIGATION LOCATORS
        # ==========================================
        # Locator for User Management tab in the module navigation
        self.tab_user_management_module = "role=tab[name='User Management']"
        
        # Locator for module header/title "User Management"
        self.heading_user_management = "role=heading[level=2][name='User Management']"
        
        # ==========================================
        # COUNTRY FIELD LOCATORS
        # ==========================================
        # Locator for Country information container (uses unique ID from User Management module)
        self.container_country = "#vatdtai_usermanagement_country"
        # Alternative locator using class name for the country display element
        self.container_country_alt = ".vatdtai-country-display"
        
        # Locator for Country information text (includes label and value)
        self.text_country_info = "#vatdtai_usermanagement_country"
        self.text_country_info_alt = ".vatdtai-country-display"
        
        # Alternative locators for Country label and value separately
        # Use more specific selector within the Country container
        self.text_country_label = "#vatdtai_usermanagement_country"
        self.text_country_label_alt = ".vatdtai-country-display"
        self.text_country_value = "#vatdtai_usermanagement_country"
        self.text_country_value_alt = "text=Belgium"
        
        # ==========================================
        # EXISTING USERS SECTION LOCATORS
        # ==========================================
        # Locator for "Existing Users" section header
        self.heading_existing_users = "role=heading[level=3][name='Existing Users']"
        
        # Locator for Existing Users table grid
        self.grid_existing_users = "role=grid"
        
        # ==========================================
        # EXISTING USERS TABLE - COLUMN HEADERS
        # ==========================================
        # Locator for "Select all on this page" column header
        self.columnheader_select_all = "role=columnheader[name='Select all on this page']"
        
        # Locator for "Name" column header
        self.columnheader_name = "role=columnheader[name='⋮ Name']"
        
        # Locator for "Email" column header
        self.columnheader_email = "role=columnheader[name='⋮ Email']"
        
        # Locator for "Role" column header
        self.columnheader_role = "role=columnheader[name='⋮ Role']"
        
        # ==========================================
        # EXISTING USERS TABLE - ROWS & CELLS
        # ==========================================
        # Locator for all table rows
        self.rows_existing_users = "role=grid >> role=row"
        
        # Locator for a specific row by index (use lambda for dynamic selection)
        self.row_by_index = lambda idx: f"role=grid >> role=row >> nth={idx}"
        
        # Locator for Name cell by user name
        self.gridcell_name_by_text = lambda name: f"role=gridcell[name='{name}']"
        
        # Locator for Email cell by email address
        self.gridcell_email_by_text = lambda email: f"role=gridcell[name='{email}']"
        
        # Locator for Role cell by role text
        self.gridcell_role_by_text = lambda role: f"role=gridcell[name='{role}']"
        
        # ==========================================
        # CHECKBOX LOCATORS
        # ==========================================
        # Locator for "Select All" checkbox in table header
        self.checkbox_select_all = "role=columnheader[name='Select all on this page'] >> role=checkbox"
        
        # Locator for individual row checkbox by index
        self.checkbox_row_by_index = lambda idx: f"role=gridcell[name='Select row'] >> nth={idx} >> role=checkbox"
        
        # Locator for all row checkboxes (for verification)
        self.checkboxes_all_rows = "role=gridcell[name='Select row'] >> role=checkbox"
        
        # ==========================================
        # TOOLBAR CONTROLS
        # ==========================================
        # More specific toolbar button locators using data attributes or class names
        # Export button - first button in toolbar
        self.btn_export = "div.tabulator-button-container >> button.tabulator-page-size"
        self.btn_export_alt = "button[title*='Export'], button[title*='Download']"
        
        # Show Filters button - toggle filters visibility (uses data-id attribute)
        self.btn_show_filters = "[data-id='btnShowFilterDiv'] >> button"
        self.btn_show_filters_alt = "[title='Show Filters'] >> button"
        
        # Clear Filters button - clears all filter values (uses data-id attribute)
        self.btn_clear_filters = "[data-id='btnClearFilterDiv'] >> button"
        self.btn_clear_filters_alt = "[title='Clear Filters'] >> button"
        
        # Reset View button - resets sorting and filters (uses data-id attribute)
        self.btn_reset_view = "[data-id='btnResetViewDiv'] >> button"
        self.btn_reset_view_alt = "[title='Reset View'] >> button"
        
        # ==========================================
        # PAGINATION CONTROLS
        # ==========================================
        # Locator for rows per page dropdown - use more specific selector within pagination area
        self.combobox_rows_per_page = "div.tabulator-footer >> select.tabulator-page-size, div.tabulator-footer >> role=combobox"
        self.combobox_rows_per_page_alt = "select[aria-label*='Page'], select[aria-label*='Rows']"
        
        # Locator for First Page button
        self.btn_first_page = "role=button[name='First Page']"
        
        # Locator for Previous Page button
        self.btn_prev_page = "role=button[name='Prev Page']"
        
        # Locator for Show Page button (displays current page)
        self.btn_show_page = "role=button[name*='Show Page']"
        
        # Locator for Next Page button
        self.btn_next_page = "role=button[name='Next Page']"
        
        # Locator for Last Page button
        self.btn_last_page = "role=button[name='Last Page']"
        
        # ==========================================
        # FILTER INPUT FIELDS (visible after clicking Show Filters button)
        # ==========================================
        # Filter input fields for Name, Email, Role columns
        self.input_filter_name = "role=columnheader[name*='Name'] >> role=searchbox"
        self.input_filter_email = "role=columnheader[name*='Email'] >> role=searchbox"
        self.input_filter_role = "role=columnheader[name*='Role'] >> role=searchbox"
        
        # NOTE: Export button directly downloads file without format selection menu
        # Feature file TC_607981 expects CSV/XML/JSON format selection, but actual implementation
        # exports directly to Excel format. This is a gap between requirements and implementation.
        
        # ==========================================
        # UTILITY METHODS
        # ==========================================
    
    def get_user_row_by_name(self, name: str):
        """Get the row element for a specific user by name"""
        logger.info(f"Getting user row for name: {name}")
        row = self.page.get_by_role("gridcell", name=name).locator("..")
        logger.info(f"Successfully located row for user: {name}")
        return row
    
    def get_user_row_by_email(self, email: str):
        """Get the row element for a specific user by email"""
        logger.info(f"Getting user row for email: {email}")
        row = self.page.get_by_role("gridcell", name=email).locator("..")
        logger.info(f"Successfully located row for email: {email}")
        return row
    
    def check_user_by_name(self, name: str):
        """Check the checkbox for a specific user by name"""
        logger.info(f"Checking checkbox for user: {name}")
        row = self.get_user_row_by_name(name)
        checkbox = row.get_by_role("checkbox")
        checkbox.check()
        logger.info(f"Successfully checked checkbox for user: {name}")
    
    def get_all_user_names(self):
        """Get all user names from the table"""
        logger.info("Retrieving all user names from the table")
        cells = self.page.locator("role=gridcell").filter(has_text="@ey.com").locator("..")
        name_cells = cells.locator(">> nth=0")
        names = [cell.inner_text() for cell in name_cells.all()]
        logger.info(f"Retrieved {len(names)} user names from the table")
        return names
    
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
    
    def apply_name_filter(self, search_value):
        """Apply filter to Name column"""
        logger.info(f"Applying Name filter with value: {search_value}")
        self.enter_text(self.input_filter_name, search_value)
        logger.info(f"Name filter applied successfully")
    
    def apply_email_filter(self, search_value):
        """Apply filter to Email column"""
        logger.info(f"Applying Email filter with value: {search_value}")
        self.enter_text(self.input_filter_email, search_value)
        logger.info(f"Email filter applied successfully")
    
    def apply_role_filter(self, search_value):
        """Apply filter to Role column"""
        logger.info(f"Applying Role filter with value: {search_value}")
        self.enter_text(self.input_filter_role, search_value)
        logger.info(f"Role filter applied successfully")
    
    def apply_entity_filter(self, search_value):
        """Apply filter to Entity column"""
        logger.info(f"Applying Entity filter with value: {search_value}")
        self.enter_text(self.input_filter_entity, search_value)
        logger.info(f"Entity filter applied successfully")
    
    def clear_all_filters(self):
        """Click Clear Filters button"""
        logger.info("Clicking Clear Filters button")
        self.element_click(self.btn_clear_filters)
        logger.info("Clear Filters button clicked successfully")
    
    def reset_sorting(self):
        """Click Reset Sort button"""
        logger.info("Clicking Reset Sort button")
        self.element_click(self.btn_reset_sort)
        logger.info("Reset Sort button clicked successfully")
    
    def select_all_users(self):
        """Click Select All checkbox"""
        logger.info("Clicking Select All checkbox")
        self.element_click(self.checkbox_select_all)
        logger.info("Select All checkbox clicked successfully")
    
    def select_user_by_index(self, row_index):
        """Select a specific user row by index"""
        # Implementation will depend on actual locator pattern
        pass
    
    def click_column_header(self, column_name):
        """Click on a column header to sort"""
        logger.info(f"Clicking column header: {column_name}")
        if column_name.lower() == "name":
            self.element_click(self.header_name)
        elif column_name.lower() == "email":
            self.element_click(self.header_email)
        elif column_name.lower() == "role":
            self.element_click(self.header_role)
        elif column_name.lower() == "entity":
            self.element_click(self.header_entity)
        logger.info(f"Column header '{column_name}' clicked successfully")
    
    def download_users(self, format_type):
        """Download users in specified format (CSV, XML, JSON)"""
        logger.info(f"Initiating download in {format_type} format")
        self.element_click(self.btn_download)
        logger.info("Download button clicked, waiting for format dropdown")
        self.wait_for_element_visible(self.dropdown_download_format)
        
        if format_type.upper() == "CSV":
            logger.info("Selecting CSV format option")
            self.element_click(self.option_download_csv)
        elif format_type.upper() == "XML":
            logger.info("Selecting XML format option")
            self.element_click(self.option_download_xml)
        elif format_type.upper() == "JSON":
            logger.info("Selecting JSON format option")
            self.element_click(self.option_download_json)
        logger.info(f"Download format {format_type} selected successfully")
    
    def get_table_row_count(self):
        """Get the number of visible rows in the table"""
        logger.info("Counting visible table rows")
        count = self.page.locator(self.rows_existing_users).count()
        logger.info(f"Table has {count} visible rows")
        return count
    
    def verify_default_sort_by_name_asc(self):
        """Verify table is sorted by Name in ascending order"""
        # Get all name values and verify they are in ascending order
        pass
    
    def navigate_to_next_page(self):
        """Click Next Page button in pagination"""
        logger.info("Navigating to next page")
        self.element_click(self.btn_next_page)
        logger.info("Next page button clicked successfully")
    
    def navigate_to_previous_page(self):
        """Click Previous Page button in pagination"""
        logger.info("Navigating to previous page")
        self.element_click(self.btn_previous_page)
        logger.info("Previous page button clicked successfully")
    
    def navigate_to_page_number(self, page_num):
        """Navigate to specific page number"""
        # Implementation will depend on actual locator pattern
        pass
    
    def verify_max_records_per_page(self, expected_max=25):
        """Verify maximum records displayed per page"""
        logger.info(f"Verifying max records per page (expected: {expected_max})")
        row_count = self.get_table_row_count()
        is_valid = row_count <= expected_max
        logger.info(f"Row count: {row_count}, Max allowed: {expected_max}, Valid: {is_valid}")
        return is_valid
    
    def is_loading_visible(self):
        """Check if loading spinner is visible"""
        logger.info("Checking if loading spinner is visible")
        is_visible = self.page.locator(self.spinner_loading).is_visible()
        logger.info(f"Loading spinner visible: {is_visible}")
        return is_visible
    
    def wait_for_loading_to_complete(self):
        """Wait for loading spinner to disappear"""
        self.wait_for_element_invisibility(self.spinner_loading)
