import logging
import re
from pageobjects.base_page import BasePage
from conftest import get_page

# Configure logger for this module
logger = logging.getLogger(__name__)


class VatDataIngestionPage(BasePage):
    """
    Page Object Model for VAT DTAI Data Ingestion Module
    Based on User Story 595077: [MVP] [UI/UX] [DI] Create Data Ingestion Tab
    """
    
    def __init__(self, get_page):
        super().__init__(get_page)
        logger.info("Initializing VatDataIngestionPage")
        
        # ==========================================
        # MODULE NAVIGATION LOCATORS
        # ==========================================
        # Locator for Data Ingestion tab in the module navigation
        self.tab_data_ingestion_module = "role=tab[name='Data Ingestion']"
        
        # Locator for module header/title "Data Ingestion"
        self.heading_data_ingestion = "role=heading[level=2][name='Data Ingestion']"
        
        # ==========================================
        # UPLOAD E-INVOICES SECTION LOCATORS
        # ==========================================
        # Locator for "Upload e-Invoices" section header
        self.heading_upload_section = "role=heading[level=3][name='Upload e-Invoices']"
        
        # Locator for Country field label
        self.text_country_label = "text=Country"
        
        # Locator for Country field value
        self.text_country_value = "text=Belgium"
        
        # Locator for "Select Source System" heading
        self.heading_select_source_system = "role=heading[level=6][name='Select Source System']"
        
        # ==========================================
        # SOURCE SYSTEM DROPDOWN - BOOTSTRAP SELECTPICKER
        # ==========================================
        # Based on actual HTML structure from screenshots:
        # - Bootstrap selectpicker with class="selectpicker show-menu-arrow"
        # - Dropdown button/trigger to click
        # - Options are <li> elements with <span class="text">
        
        # Locators for the dropdown button/trigger (to open the menu)
        self.source_system_dropdown_locators = [
            # Bootstrap selectpicker button (most specific)
            "div.dropdown.dropdown--single-select button.dropdown-toggle",
            "button.selectpicker",
            "div[data-id*='sourceSystem'] button",
            # By select element (Bootstrap wraps this)
            "select.selectpicker",
            "select[data-id*='sourceSystem']",
            # Generic fallbacks
            ".bootstrap-select button.dropdown-toggle",
            "div.vatdtai-field:has-text('Select Source System') .dropdown-toggle",
            "button.dropdown-toggle >> nth=0",
        ]
        
        # ==========================================
        # SOURCE SYSTEM DROPDOWN OPTIONS
        # ==========================================
        # Option locators (parameterized by source system name)
        # Options are <li> elements inside <ul class="dropdown-menu inner">
        # EXACT text, scoped to the OPEN selectpicker menu first, so the source-system
        # option (e.g. "SAP") is not confused with buyer/client names that merely
        # contain the same word ("SAP Belgium Issuer NV", "Belgium Unique Buyer SAP 01").
        self.source_system_option_locators = lambda system: [
            f"div.dropdown.dropdown--single-select .dropdown-menu.show li span.text:text-is('{system}')",
            f".dropdown-menu.show li span.text:text-is('{system}')",
            f".dropdown-menu.show li a:has(span.text:text-is('{system}'))",
            # Exact text anywhere (menu may render without .show in some builds)
            f"li span.text:text-is('{system}')",
            f"ul.dropdown-menu.inner li span.text:text-is('{system}')",
            # Substring fallbacks (last resort)
            f"li span.text:has-text('{system}')",
            f"li:has-text('{system}')",
        ]
        
        # ==========================================
        # DROPZONE FILE UPLOAD LOCATORS
        # ==========================================
        # The upload area uses Dropzone.js with id="vatdtai_importFiles_upload"
        # Dropzone.js dynamically creates a hidden file input with class "dz-hidden-input"
        
        # Locators for the DROPZONE CLICKABLE AREA (to trigger file chooser)
        self.dropzone_clickable_area_locators = [
            # By dropzone ID (most specific)
            "#vatdtai_importFiles_upload",
            "div#vatdtai_importFiles_upload.dropzone.dz-clickable",
            "div.dropzone.dz-clickable",
            "div.vatdtai-field-dropzone .dropzone",
            # By visible text in dropzone
            "text=Drop file here or click to browse",
            # By context (under Upload e-Invoice Transaction Report heading)
            "h6:has-text('Upload e-Invoice Transaction Report') ~ * .dropzone",
        ]
        
        # Locators for the FILE INPUT element (Dropzone.js hidden input)
        # NOTE: Dropzone.js dynamically creates input with class "dz-hidden-input"
        self.input_file_upload_strategies = [
            # Dropzone.js hidden input (most reliable)
            "input[type='file'].dz-hidden-input",
            ".dz-hidden-input",
            # Inside dropzone container by ID
            "#vatdtai_importFiles_upload input[type='file']",
            "div.dropzone.dz-clickable input[type='file']",
            "div.vatdtai-field-dropzone input[type='file']",
            # By heading context
            "h6:has-text('Upload e-Invoice Transaction Report') ~ * input[type='file']",
            "role=heading[name='Upload e-Invoice Transaction Report'] ~ * >> input[type='file']",
            # By section context
            "div.vatdtai-upload-row input[type='file']",
            "role=heading[name='Upload e-Invoices'] ~ * >> input[type='file']",
            # Generic fallback (first file input, excluding chatSidecarFileInput)
            "input[type='file']:not(#chatSidecarFileInput)",
        ]
        
        # Locator for "Upload e-Invoice Transaction Report" heading
        self.heading_upload_transaction_report = "role=heading[level=6][name='Upload e-Invoice Transaction Report']"
        
        # Locator for file upload dropzone area (clickable)
        # Multiple strategies to find and click the dropzone
        self.dropzone_clickable_area_locators = [
            # By ID (most specific)
            "#vatdtai_importFiles_upload",
            "div#vatdtai_importFiles_upload.dropzone.dz-clickable",
            # By class combination
            "div.dropzone.dz-clickable",
            "div.vatdtai-field-dropzone .dropzone",
            # By text content
            "text=Drop file here or click to browse",
            # By heading context
            "h6:has-text('Upload e-Invoice Transaction Report') ~ * .dropzone",
        ]
        self.dropzone_file_upload = "#vatdtai_importFiles_upload"
        
        # Locator for Upload button
        # Multiple strategies based on actual HTML structure
        self.btn_upload_locators = [
            # Most specific - by data-id attribute
            "button[data-id='vatdtai_import_upload_button']",
            "[data-id='vatdtai_import_upload_button']",
            # By class combination
            "button.IBUTTON.vatdtai-btn-primary",
            "button.btn-primary:has-text('Upload')",
            # By accessible role and name
            "role=button[name='Upload']",
            # By text content
            "button:has-text('Upload')",
        ]
        # Default Upload button locator
        self.btn_upload = "button[data-id='vatdtai_import_upload_button']"
        
        # Locator for upload format info text
        self.text_accepted_formats = "text=Accepted formats: CSV, XML, JSON (one file at a time)"
        
        # ==========================================
        # BATCH E-INVOICES TABLE LOCATORS
        # ==========================================
        # Locator for "Batch e-Invoices" section header
        self.heading_batch_einvoices = "role=heading[level=3][name='Batch e-Invoices']"
        
        # Locator for Batch e-Invoices table grid
        self.grid_batch_einvoices = "role=grid >> nth=0"
        
        # Locators for table column headers
        self.columnheader_select_all_batch = "role=columnheader[name='Select all on this page'] >> nth=0"
        self.columnheader_batch_id = "role=columnheader[name='⋮ Batch ID']"
        self.columnheader_file_name = "role=columnheader[name='⋮ File Name']"
        self.columnheader_source_system_batch = "role=columnheader[name='⋮ Source System'] >> nth=0"
        self.columnheader_imported_on = "role=columnheader[name='⋮ Imported On']"
        self.columnheader_actions_batch = "role=columnheader[name='Actions'] >> nth=0"
        
        # Locator for all table rows in Batch table
        self.rows_batch_table = "role=grid >> nth=0 >> role=row"
        
        # Locator for row checkboxes in Batch table (use nth to get specific row)
        self.checkbox_batch_row_by_index = lambda idx: f"role=grid >> nth=0 >> role=gridcell[name='Select row'] >> nth={idx} >> role=checkbox"
        
        # Locator for Select All checkbox in Batch table
        self.checkbox_select_all_batch = "role=columnheader[name='Select all on this page'] >> nth=0 >> role=checkbox"
        
        # Locator for specific cell by column name (parameterized)
        self.gridcell_by_name = lambda name: f"role=gridcell[name*='{name}']"
        
        # Locator for delete buttons in Batch table
        self.btn_delete_batch_row = "role=grid >> nth=0 >> role=row >> [aria-label='Delete']"
        
        # ==========================================
        # BATCH TABLE - TOOLBAR CONTROLS
        # ==========================================
        # Locator for Export button (Batch table) - Using accessible name from snapshot
        self.btn_export_batch = "role=heading[name='Batch e-Invoices'] ~ * >> [aria-label='Export'] >> role=button"
        self.btn_export_batch_simple = "role=grid >> nth=0 ~ * >> [aria-label='Export'] >> role=button"
        
        # Locator for Refresh button (Batch table)
        self.btn_refresh_batch = "role=heading[name='Batch e-Invoices'] ~ * >> [aria-label='Refresh'] >> role=button"
        self.btn_refresh_batch_simple = "role=grid >> nth=0 ~ * >> [aria-label='Refresh'] >> role=button"
        
        # Locator for Show Filters button (Batch table)
        self.btn_show_filters_batch = "role=heading[name='Batch e-Invoices'] ~ * >> [aria-label='Show Filters'] >> role=button"
        self.btn_show_filters_batch_simple = "role=grid >> nth=0 ~ * >> [aria-label='Show Filters'] >> role=button"
        
        # Locator for Clear Filters button (Batch table)
        self.btn_clear_filters_batch = "role=heading[name='Batch e-Invoices'] ~ * >> [aria-label='Clear Filters'] >> role=button"
        self.btn_clear_filters_batch_simple = "role=grid >> nth=0 ~ * >> [aria-label='Clear Filters'] >> role=button"
        
        # Locator for Reset View button (Batch table)
        self.btn_reset_view_batch = "role=heading[name='Batch e-Invoices'] ~ * >> [aria-label='Reset View'] >> role=button"
        self.btn_reset_view_batch_simple = "role=grid >> nth=0 ~ * >> [aria-label='Reset View'] >> role=button"
        
        # Locators for pagination controls (Batch table)
        self.combobox_rows_per_page_batch = "role=combobox >> nth=0"
        self.btn_first_page_batch = "role=button[name='First Page'] >> nth=0"
        self.btn_prev_page_batch = "role=button[name='Prev Page'] >> nth=0"
        self.btn_show_page_batch = "role=button[name*='Show Page'] >> nth=0"
        self.btn_next_page_batch = "role=button[name='Next Page'] >> nth=0"
        self.btn_last_page_batch = "role=button[name='Last Page'] >> nth=0"
        
        # ==========================================
        # API DETAILS SECTION LOCATORS
        # ==========================================
        # Locator for "API Details" section header
        self.heading_api_details = "role=heading[level=3][name='API Details']"
        
        # Locator for API Details table grid
        self.grid_api_details = "role=grid >> nth=1"
        
        # Locators for API table column headers
        self.columnheader_select_all_api = "role=columnheader[name='Select all on this page'] >> nth=1"
        self.columnheader_api_source_system = "role=columnheader[name='⋮ Source System'] >> nth=1"
        self.columnheader_api_type = "role=columnheader[name='⋮ Type']"
        self.columnheader_api_rest_actions = "role=columnheader[name='⋮ REST API Actions']"
        self.columnheader_api_status = "role=columnheader[name='⋮ Status']"
        self.columnheader_api_created_by = "role=columnheader[name='⋮ Created By']"
        self.columnheader_api_created_on = "role=columnheader[name='⋮ Created On']"
        self.columnheader_actions_api = "role=columnheader[name='Actions'] >> nth=1"
        
        # Locator for all table rows in API Details table
        self.rows_api_table = "role=grid >> nth=1 >> role=row"
        
        # Locator for Select All checkbox in API table
        self.checkbox_select_all_api = "role=columnheader[name='Select all on this page'] >> nth=1 >> role=checkbox"
        
        # Locator for row checkboxes in API table
        self.checkbox_api_row_by_index = lambda idx: f"role=grid >> nth=1 >> role=gridcell[name='Select row'] >> nth={idx} >> role=checkbox"
        
        # Locator for delete buttons in API table
        self.btn_delete_api_row = "role=grid >> nth=1 >> role=row >> [aria-label='Delete']"
        
        # ==========================================
        # API TABLE - TOOLBAR CONTROLS
        # ==========================================
        # Locator for Export button (API table) - Using accessible name from snapshot
        self.btn_export_api = "role=heading[name='API Details'] ~ * >> [aria-label='Export'] >> role=button"
        self.btn_export_api_simple = "role=grid >> nth=1 ~ * >> [aria-label='Export'] >> role=button"
        
        # Locator for Refresh button (API table)
        self.btn_refresh_api = "role=heading[name='API Details'] ~ * >> [aria-label='Refresh'] >> role=button"
        self.btn_refresh_api_simple = "role=grid >> nth=1 ~ * >> [aria-label='Refresh'] >> role=button"
        
        # Locator for Show Filters button (API table)
        self.btn_show_filters_api = "role=heading[name='API Details'] ~ * >> [aria-label='Show Filters'] >> role=button"
        self.btn_show_filters_api_simple = "role=grid >> nth=1 ~ * >> [aria-label='Show Filters'] >> role=button"
        
        # Locator for Clear Filters button (API table)
        self.btn_clear_filters_api = "role=heading[name='API Details'] ~ * >> [aria-label='Clear Filters'] >> role=button"
        self.btn_clear_filters_api_simple = "role=grid >> nth=1 ~ * >> [aria-label='Clear Filters'] >> role=button"
        
        # Locator for Reset View button (API table)
        self.btn_reset_view_api = "role=heading[name='API Details'] ~ * >> [aria-label='Reset View'] >> role=button"
        self.btn_reset_view_api_simple = "role=grid >> nth=1 ~ * >> [aria-label='Reset View'] >> role=button"
        
        # Locators for pagination controls (API table)
        self.combobox_rows_per_page_api = "role=combobox >> nth=1"
        self.btn_first_page_api = "role=button[name='First Page'] >> nth=1"
        self.btn_prev_page_api = "role=button[name='Prev Page'] >> nth=1"
        self.btn_show_page_api = "role=button[name*='Show Page'] >> nth=1"
        self.btn_next_page_api = "role=button[name='Next Page'] >> nth=1"
        self.btn_last_page_api = "role=button[name='Last Page'] >> nth=1"
        
        # ==========================================
        # DELETE CONFIRMATION DIALOG
        # ==========================================
        # Delete confirmation dialog and buttons
        self.dialog_delete_confirmation = "role=dialog"
        self.heading_confirm_deletion = "role=heading[level=4][name='Confirm Deletion']"
        self.text_delete_confirmation = "text=Are you sure you want to delete this batch invoice?"
        self.btn_delete_confirm_yes = "role=button[name='Yes']"
        self.btn_delete_confirm_no = "role=button[name='No']"
        
        # Upload section - Accepted formats text (visible in dropzone)
        self.text_accepted_formats = "text=Accepted formats: CSV, XML, JSON"
        
        # ==========================================
        # SESSION TIMEOUT DIALOG
        # ==========================================
        # Session timeout/logout dialog locators
        self.session_timeout_dialog_text = "text=You have signed in from another browser window"
        self.session_timeout_ok_button = "button:has-text('Ok')"
    
    # ==========================================
    # SESSION MANAGEMENT METHODS
    # ==========================================
    def handle_session_timeout_if_present(self):
        """
        Check for and handle session timeout dialog if it appears.
        This dialog shows: "You have signed in from another browser window while THIS 
        browser window is still active. You have now been signed out this browser window."
        
        Returns:
            bool: True if dialog was found and handled, False otherwise
        """
        try:
            # Quick check for session timeout dialog (1 second timeout)
            if self.page.locator(self.session_timeout_dialog_text).count() > 0:
                logger.warning("⚠ Session timeout dialog detected!")
                
                # Take screenshot
                try:
                    self.page.screenshot(path=f"screenshots/session_timeout_detected.png", full_page=True)
                except:
                    pass
                
                # Click Ok button to dismiss
                self.page.locator(self.session_timeout_ok_button).click(timeout=5000)
                logger.info("✓ Session timeout dialog dismissed")
                
                # Wait for page to stabilize
                self.page.wait_for_timeout(2000)
                
                return True
        except Exception as e:
            logger.debug(f"No session timeout dialog found: {e}")
            
        return False
    
    # ==========================================
    # PAGE INTERACTION METHODS
    # ==========================================
    
    def select_source_system(self, source_system: str):
        """
        Select source system from Bootstrap selectpicker dropdown
        
        Args:
            source_system: Name of source system (e.g., "Oracle", "SAP", "MS D365")
        
        Returns:
            bool: True if selection successful, False otherwise
        
        Raises:
            Exception: If dropdown cannot be found or option cannot be selected
        """
        logger.info(f"Attempting to select source system: {source_system}")
        
        # SMART WAIT: Wait for dropdown to be visible and ready
        logger.info("Waiting for source system dropdown to be ready...")
        try:
            # Try multiple strategies to wait for dropdown
            wait_strategies = [
                "div.dropdown.dropdown--single-select button.dropdown-toggle",
                "button.selectpicker",
                "#vatdtai_importfiles_source >> button",
            ]
            
            dropdown_ready = False
            for strategy in wait_strategies:
                try:
                    self.page.wait_for_selector(strategy, state="visible", timeout=10000)
                    logger.info(f"✓ Dropdown ready using wait strategy: {strategy}")
                    dropdown_ready = True
                    break
                except Exception as e:
                    logger.debug(f"Wait strategy failed: {strategy} - {e}")
                    continue
            
            if not dropdown_ready:
                logger.warning("⚠ None of the wait strategies succeeded, but continuing...")
            
            # Additional stabilization wait
            self.page.wait_for_timeout(2000)
            
        except Exception as e:
            logger.warning(f"⚠ Wait for dropdown warning: {e}")
        
        # Take screenshot before attempting selection
        try:
            self.page.screenshot(path=f"screenshots/before_source_system_selection.png", full_page=True)
        except:
            pass
        
        # Step 1: Find and click the dropdown button to open the menu
        dropdown_element = None
        successful_locator = None
        
        logger.info("Step 1: Searching for dropdown button...")
        for locator in self.source_system_dropdown_locators:
            try:
                dropdown = self.page.locator(locator).first
                count = dropdown.count()
                
                logger.debug(f"Trying locator: {locator} - Count: {count}")
                
                if count > 0:
                    # Check if visible with timeout
                    try:
                        is_visible = dropdown.is_visible(timeout=2000)
                        if is_visible:
                            logger.info(f"✓ Found dropdown button using: {locator}")
                            dropdown_element = dropdown
                            successful_locator = locator
                            break
                        else:
                            logger.debug(f"  Element found but not visible")
                    except:
                        logger.debug(f"  Element visibility check timed out")
            except Exception as e:
                logger.debug(f"Locator failed: {locator} - {str(e)[:100]}")
                continue
        
        if not dropdown_element:
            # Take screenshot of failure
            logger.error("✗ Dropdown button NOT found - Taking diagnostic screenshot")
            try:
                self.page.screenshot(path=f"screenshots/dropdown_not_found.png", full_page=True)
                
                # Log page URL and title for debugging
                current_url = self.page.url
                page_title = self.page.title()
                logger.error(f"Current URL: {current_url}")
                logger.error(f"Page title: {page_title}")
                
                # Check if any buttons exist on the page
                all_buttons = self.page.locator("button")
                button_count = all_buttons.count()
                logger.error(f"Total buttons on page: {button_count}")
                
                # Log first 5 buttons
                for i in range(min(5, button_count)):
                    try:
                        btn = all_buttons.nth(i)
                        btn_text = btn.inner_text(timeout=1000)
                        btn_class = btn.get_attribute("class")
                        logger.error(f"  Button {i+1}: text='{btn_text[:50]}', class='{btn_class}'")
                    except:
                        pass
                        
            except Exception as e:
                logger.error(f"Failed to capture diagnostics: {e}")
            
            raise Exception("Source System dropdown button not found using any locator strategy")
        
        # Step 2: Click the dropdown button to open the menu
        logger.info(f"Clicking dropdown button with locator: {successful_locator}")
        dropdown_element.click()
        logger.info("✓ Dropdown button clicked - menu should be opening")
        
        # Wait for dropdown menu to appear (Bootstrap animation)
        self.page.wait_for_timeout(1000)
        
        # Take screenshot of opened dropdown
        try:
            self.page.screenshot(path=f"screenshots/dropdown_opened.png", full_page=True)
        except:
            pass
        
        # Step 3: Find and click the option from the opened menu
        option_selected = False
        successful_option_locator = None
        
        for locator in self.source_system_option_locators(source_system):
            try:
                option = self.page.locator(locator)
                count = option.count()
                
                if count > 0:
                    # Pick the FIRST VISIBLE match (an option in a closed picker is
                    # present in the DOM but not visible; skip those).
                    target = None
                    for i in range(count):
                        cand = option.nth(i)
                        try:
                            if cand.is_visible():
                                target = cand
                                break
                        except Exception:
                            continue
                    if target is not None:
                        logger.info(f"✓ Found visible option '{source_system}' using: {locator} (count: {count})")
                        successful_option_locator = locator
                        target.click()
                        option_selected = True
                        logger.info(f"✓ Clicked option '{source_system}'")
                        self.page.wait_for_timeout(500)
                        break
                    else:
                        logger.debug(f"Option matched but none visible: {locator}")
                else:
                    logger.debug(f"Option not found: {locator}")
            except Exception as e:
                logger.debug(f"Option locator failed: {locator} - {str(e)[:100]}")
                continue
        
        if not option_selected:
            # Take screenshot of failure
            try:
                self.page.screenshot(path=f"screenshots/option_not_found.png", full_page=True)
                # Also save HTML for debugging
                html_content = self.page.content()
                with open("screenshots/page_html.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
            except:
                pass
            raise Exception(f"Could not select option: {source_system}. Dropdown opened but option not found in menu.")
        
        # Wait for selection to take effect and menu to close
        self.page.wait_for_timeout(1000)
        
        # Take screenshot after selection
        try:
            self.page.screenshot(path=f"screenshots/after_source_system_selection.png", full_page=True)
        except:
            pass
        
        logger.info(f"✓ Successfully selected source system: {source_system} using option locator: {successful_option_locator}")
        
        # CRITICAL: Wait for dropzone to appear/be ready after source system selection
        # The dropzone state changes when source system is selected
        logger.info("Waiting for dropzone to become available after source system selection...")
        try:
            # Wait up to 15 seconds for dropzone to be visible
            self.page.wait_for_selector("#vatdtai_importFiles_upload", state="visible", timeout=15000)
            logger.info("✓ Dropzone is now visible")
            # Additional wait for Dropzone.js initialization
            self.page.wait_for_timeout(2000)
            logger.info("✓ Waited for Dropzone.js initialization")
        except Exception as e:
            logger.warning(f"⚠ Dropzone wait timeout (may still work): {e}")
        
        return True
    
    def upload_file(self, file_path: str):
        """
        Upload a file by clicking the dropzone and handling the file chooser.
        Uses Playwright's file chooser API to properly handle Dropzone.js file uploads.
        Includes robust verification that file was actually selected.
        
        Args:
            file_path: Absolute path to the file to upload
        
        Raises:
            Exception: If dropzone not clickable, file chooser fails, or file name doesn't appear
        """
        from pathlib import Path
        
        # CRITICAL: Check for session timeout dialog first
        if self.handle_session_timeout_if_present():
            logger.error("✗ Session timeout occurred - cannot proceed with file upload")
            raise Exception("Session expired - user was logged out")
        
        logger.info(f"Uploading file: {file_path}")
        file_name = Path(file_path).name
        logger.info(f"File name to verify: {file_name}")
        
        # Take screenshot before file selection
        try:
            self.page.screenshot(path=f"screenshots/before_file_selection.png", full_page=True)
        except:
            pass
        
        # STEP 1: Ensure dropzone is visible and ready
        logger.info("Step 1: Verifying dropzone is visible...")
        dropzone_visible = False
        for locator in self.dropzone_clickable_area_locators:
            try:
                dropzone = self.page.locator(locator).first
                if dropzone.count() > 0 and dropzone.is_visible(timeout=2000):
                    logger.info(f"✓ Dropzone is visible using: {locator}")
                    dropzone_visible = True
                    break
            except:
                continue
        
        if not dropzone_visible:
            logger.warning("⚠ Dropzone visibility check failed, but continuing...")
        
        # STEP 2: Click dropzone to trigger file chooser
        logger.info("Step 2: Clicking dropzone to open file chooser...")
        dropzone_element = None
        successful_dropzone_locator = None
        
        for locator in self.dropzone_clickable_area_locators:
            try:
                dropzone = self.page.locator(locator).first
                count = dropzone.count()
                
                if count > 0:
                    logger.info(f"✓ Found dropzone using: {locator}")
                    dropzone_element = dropzone
                    successful_dropzone_locator = locator
                    break
            except Exception as e:
                logger.debug(f"Dropzone locator failed: {locator} - {e}")
                continue
        
        if not dropzone_element:
            logger.error("✗ Dropzone element not found")
            try:
                self.page.screenshot(path=f"screenshots/dropzone_not_found.png", full_page=True)
            except:
                pass
            raise Exception("Dropzone clickable area not found using any locator strategy")
        
        # STEP 3: Set up file chooser handler and click dropzone
        logger.info(f"Step 3: Setting up file chooser handler...")
        try:
            # Use context manager to handle file chooser (short timeout so we can fall back fast)
            with self.page.expect_file_chooser(timeout=8000) as fc_info:
                logger.info(f"Clicking dropzone with locator: {successful_dropzone_locator}")
                dropzone_element.click()
                logger.info("✓ Dropzone clicked - waiting for file chooser...")
            
            # Get the file chooser
            file_chooser = fc_info.value
            logger.info("✓ File chooser appeared")
            
            # Set the file
            logger.info(f"Setting file: {file_path}")
            file_chooser.set_files(file_path)
            logger.info("✓ File set successfully")
            
        except Exception as e:
            # The dropzone click sometimes fails to open a chooser (state bleed / timing). Fall back
            # to setting the file directly on the Dropzone.js hidden input, which is more reliable.
            logger.warning(f"⚠ File chooser did not open ({e}); falling back to hidden-input set")
            try:
                self.page.screenshot(path=f"screenshots/file_chooser_failed.png", full_page=True)
            except:
                pass
            self.set_file_via_input(file_path)
        
        # STEP 4: ROBUST VERIFICATION - Wait for file to be processed by Dropzone.js
        logger.info("Step 4: Verifying file was accepted by Dropzone.js...")
        
        # Wait for Dropzone.js to process the file
        self.page.wait_for_timeout(2000)
        
        # Take screenshot after file selection
        try:
            self.page.screenshot(path=f"screenshots/after_file_selection_attempt.png", full_page=True)
        except:
            pass
        
        # Verify file name appears in dropzone or check for preview element
        max_wait_time = 10  # seconds
        verification_passed = False
        
        for attempt in range(max_wait_time):
            self.page.wait_for_timeout(1000)
            
            try:
                # Method 1: Check dropzone inner text for file name
                dropzone_text = self.page.locator("#vatdtai_importFiles_upload").inner_text(timeout=3000)
                if file_name in dropzone_text:
                    logger.info(f"✓✓✓ SUCCESS (Method 1): File name '{file_name}' appears in dropzone text!")
                    verification_passed = True
                    break
                
                # Method 2: Check for Dropzone.js preview elements
                preview_locators = [
                    f"#vatdtai_importFiles_upload .dz-filename:has-text('{file_name}')",
                    f"#vatdtai_importFiles_upload .dz-preview:has-text('{file_name}')",
                    f".dz-filename:has-text('{file_name}')",
                ]
                for preview_loc in preview_locators:
                    if self.page.locator(preview_loc).count() > 0:
                        logger.info(f"✓✓✓ SUCCESS (Method 2): File preview found with: {preview_loc}")
                        verification_passed = True
                        break
                
                if verification_passed:
                    break

                # Method 3: The dropzone visually truncates long file names (e.g. "Custom ER..."),
                # so a full-name match can fail even though the file was accepted. Treat the
                # presence of a preview/remove control as proof the file was accepted.
                accepted_signal_locators = [
                    "#vatdtai_importFiles_upload .dz-preview",
                    "#vatdtai_importFiles_upload .dz-filename",
                    "#vatdtai_importFiles_upload .dz-remove",
                    "#vatdtai_importFiles_upload [data-dz-remove]",
                    "#vatdtai_importFiles_upload >> text=Remove file",
                ]
                for accepted_loc in accepted_signal_locators:
                    if self.page.locator(accepted_loc).count() > 0:
                        logger.info(f"✓✓✓ SUCCESS (Method 3): File accepted signal found with: {accepted_loc}")
                        verification_passed = True
                        break

                if verification_passed:
                    break

                # Method 4: Confirm the file is held by the Dropzone.js hidden input.
                try:
                    input_has_file = self.page.evaluate(
                        """(name) => Array.from(document.querySelectorAll('input.dz-hidden-input'))
                            .some(i => i.files && Array.from(i.files).some(f => f.name === name))""",
                        file_name,
                    )
                    if input_has_file:
                        logger.info("✓✓✓ SUCCESS (Method 4): File present in dz-hidden-input.files")
                        verification_passed = True
                        break
                except Exception:
                    pass

                logger.info(f"  Attempt {attempt + 1}/{max_wait_time} - Still waiting for file to appear...")
                
            except Exception as e:
                logger.warning(f"Verification attempt {attempt + 1} error: {e}")
        
        # Final screenshot
        try:
            self.page.screenshot(path=f"screenshots/after_file_verification.png", full_page=True)
        except:
            pass
        
        if not verification_passed:
            logger.error(f"✗✗✗ FAILURE: File name '{file_name}' does NOT appear in dropzone after {max_wait_time} seconds")
            # Check if there's an error message in dropzone
            try:
                error_msg = self.page.locator(".dz-error-message").inner_text(timeout=2000)
                logger.error(f"  Dropzone error message: {error_msg}")
            except:
                pass
            
            raise Exception(
                f"File selection verification FAILED: File name '{file_name}' did not appear in dropzone.\n"
                f"This indicates the file was not properly accepted by Dropzone.js component."
            )
        
        logger.info(f"✓ File '{file_name}' successfully selected and verified in dropzone")

    def set_file_via_input(self, file_path: str):
        """Set a file directly on the Dropzone.js hidden input, triggering the component's
        client-side validation WITHOUT asserting acceptance.

        Used for negative (invalid-format) scenarios where the file is expected to be rejected,
        and as a reliable fallback when the OS file chooser fails to open.
        """
        from pathlib import Path
        file_name = Path(file_path).name
        logger.info(f"Setting file via hidden input (no acceptance assertion): {file_name}")
        for sel in [
            "#vatdtai_importFiles_upload input[type='file']",
            "input[type='file'].dz-hidden-input",
            "input[type='file']",
        ]:
            inp = self.page.locator(sel).first
            if inp.count() > 0:
                inp.set_input_files(file_path)
                self.page.wait_for_timeout(1500)
                logger.info(f"✓ File set via input using: {sel}")
                return True
        raise Exception("No file input element found to set the file")

    def click_upload_button(self):
        """
        Click the Upload button with smart wait for button to become enabled.
        
        Raises:
            Exception: If button not found or doesn't become enabled within timeout
        """
        logger.info("Clicking Upload button")
        
        # Try multiple locator strategies to find the Upload button
        upload_btn = None
        successful_locator = None
        
        for locator in self.btn_upload_locators:
            try:
                btn = self.page.locator(locator)
                count = btn.count()
                
                if count == 1:
                    logger.info(f"✓ Found Upload button using: {locator}")
                    upload_btn = btn
                    successful_locator = locator
                    break
                elif count > 1:
                    logger.debug(f"Locator {locator} matched {count} buttons (need exactly 1)")
                else:
                    logger.debug(f"Locator {locator} matched 0 buttons")
            except Exception as e:
                logger.debug(f"Locator {locator} failed: {e}")
                continue
        
        if not upload_btn:
            logger.error("✗ Upload button not found with any locator strategy")
            try:
                self.page.screenshot(path=f"screenshots/upload_button_not_found.png", full_page=True)
            except:
                pass
            raise Exception("Upload button not found")
        
        # SMART WAIT: Wait for Upload button to become enabled
        logger.info("Waiting for Upload button to become enabled...")
        max_wait = 10  # seconds
        button_enabled = False
        
        for attempt in range(max_wait):
            is_enabled = upload_btn.is_enabled()
            is_disabled = upload_btn.is_disabled()
            
            logger.info(f"Attempt {attempt + 1}/{max_wait} - Button enabled: {is_enabled}, disabled: {is_disabled}")
            
            if is_enabled and not is_disabled:
                logger.info("✓ Upload button is now ENABLED")
                button_enabled = True
                break
            
            self.page.wait_for_timeout(1000)
        
        # Take screenshot before clicking
        try:
            self.page.screenshot(path=f"screenshots/before_upload_button_click.png", full_page=True)
        except:
            pass
        
        if not button_enabled:
            logger.error(f"✗✗✗ Upload button did NOT become enabled after {max_wait} seconds")
            try:
                self.page.screenshot(path=f"screenshots/upload_button_disabled.png", full_page=True)
                btn_html = upload_btn.evaluate("el => el.outerHTML")
                logger.error(f"Button HTML: {btn_html}")
                
                # Check dropzone state
                dropzone_text = self.page.locator("#vatdtai_importFiles_upload").inner_text()
                logger.error(f"Dropzone text: {dropzone_text[:150]}")
            except:
                pass
            raise Exception(f"Upload button did not become enabled after {max_wait} seconds. "
                          "This indicates file selection failed or source system not selected.")
        
        # Click the button
        logger.info(f"✓ Clicking Upload button with locator: {successful_locator}")
        upload_btn.click()
        logger.info("✓ Upload button clicked successfully")
        
        # Wait for upload to process
        self.page.wait_for_timeout(2000)
        
        # Take screenshot after clicking
        try:
            self.page.screenshot(path=f"screenshots/after_upload_button_click.png", full_page=True)
        except:
            pass

    # ==========================================
    # BATCH TABLE CLEANUP (delete uploaded records / duplicates)
    # ==========================================
    def _batch_rows(self):
        """Locator for all rendered Tabulator rows in the Batch e-Invoices grid (first grid)."""
        return self.page.locator(self.grid_batch_einvoices).locator(".tabulator-row")

    def select_batch_rows_matching(self, text: str) -> int:
        """Tick the checkbox of every currently-rendered Batch row whose text contains `text`.
        Returns the number of rows selected in this pass."""
        rows = self._batch_rows()
        selected = 0
        for i in range(rows.count()):
            row = rows.nth(i)
            try:
                if text.lower() in (row.inner_text() or "").lower():
                    cb = row.locator("input[type='checkbox']").first
                    if cb.count() > 0 and not cb.is_checked():
                        row.scroll_into_view_if_needed()
                        cb.check()
                        selected += 1
            except Exception as e:
                logger.debug(f"[batch-cleanup] row {i} skipped: {e}")
        logger.info(f"[batch-cleanup] selected {selected} row(s) matching '{text}'")
        return selected

    def select_top_batch_row(self) -> bool:
        """Tick the checkbox of the first (newest) Batch row. Returns True if a row was selected."""
        rows = self._batch_rows()
        if rows.count() == 0:
            return False
        cb = rows.first.locator("input[type='checkbox']").first
        if cb.count() == 0:
            return False
        rows.first.scroll_into_view_if_needed()
        cb.check()
        return True

    def click_batch_delete_toolbar(self):
        """Click the Batch grid toolbar trash icon (the 1st trash icon; API's is the 2nd)."""
        self.page.locator("button:has(i.icon-trash-o)").nth(0).click(timeout=6000)
        self.page.wait_for_timeout(1000)

    def confirm_batch_deletion(self):
        """Confirm the delete in the confirmation dialog (Delete/Yes/Confirm/OK)."""
        dialog = self.page.locator("[role=dialog]").filter(has_text=re.compile("delete", re.I)).last
        dialog.wait_for(state="visible", timeout=8000)
        for name in ["Delete", "Yes", "Confirm", "OK"]:
            btn = dialog.get_by_role("button", name=name, exact=True)
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.click()
                self.page.wait_for_timeout(1500)
                logger.info(f"[batch-cleanup] confirmed deletion via '{name}'")
                return
        # Fallback: click the last button in the dialog (typically the primary action)
        dialog.get_by_role("button").last.click()
        self.page.wait_for_timeout(1500)
        logger.info("[batch-cleanup] confirmed deletion via fallback (last button)")

    def delete_all_batch_rows_matching(self, text: str, max_iterations: int = 10) -> int:
        """Delete every Batch e-Invoices row whose text contains `text` (clears duplicates too).
        Loops to handle Tabulator virtualization/pagination. Returns total rows deleted."""
        total = 0
        for _ in range(max_iterations):
            selected = self.select_batch_rows_matching(text)
            if selected == 0:
                break
            self.click_batch_delete_toolbar()
            self.confirm_batch_deletion()
            total += selected
            self.page.wait_for_timeout(1000)
        logger.info(f"[batch-cleanup] deleted {total} row(s) matching '{text}'")
        return total

    def delete_top_batch_row(self) -> bool:
        """Fallback cleanup: delete the newest (top) Batch row. Returns True if a delete happened."""
        if not self.select_top_batch_row():
            return False
        self.click_batch_delete_toolbar()
        self.confirm_batch_deletion()
        self.page.wait_for_timeout(1000)
        return True


