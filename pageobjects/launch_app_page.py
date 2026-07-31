import re
import logging
from pageobjects.base_page import BasePage
from conftest import get_page

# Configure logger for this module
logger = logging.getLogger(__name__)


class LaunchAppPage(BasePage):
    """
    Page Object Model for VAT DTAI Application Launch Flow
    Handles login, workspace selection, and VAT DTAI app navigation
    """
    
    def __init__(self, get_page):
        super().__init__(get_page)
        
        # ==========================================
        # LOGIN PAGE LOCATORS
        # ==========================================
        # Locator for username/email input field
        # Note: Microsoft login uses multiple text inputs, username is first
        self.input_username = "input[type='text']:visible >> nth=0"
        
        # Locator for password input field
        # Note: Password field appears after entering username
        self.input_password = "input[type='text']:visible >> nth=1"
        
        # Alternative locator for password field (if type='password')
        self.input_password_alt = "input[type='password']:visible"
        
        # Locator for Sign In button (supports multiple button text variations)
        self.btn_sign_in = "role=button[name='Sign In' i]"
        self.btn_login = "role=button[name='Login' i]"
        self.btn_log_in = "role=button[name='Log in' i]"
        
        # Locator for "Stay signed in?" prompt - No/Skip button
        self.btn_stay_signed_in_no = "role=button[name='No' i]"
        self.btn_stay_signed_in_skip = "role=button[name='Skip' i]"
        
        # ==========================================
        # WORKSPACE/CLIENT SELECTION LOCATORS
        # ==========================================
        # Locator for workspace dropdown/combobox
        # This appears after login and allows selecting client/workspace
        self.combobox_workspace = "role=combobox[name='dropdown']"
        
        # Alternative locator for workspace dropdown
        self.dropdown_workspace_alt = "role=combobox >> nth=0"
        
        # Locator for workspace dropdown option by text (use lambda for dynamic selection)
        self.workspace_option_by_text = lambda workspace_name: f"text={workspace_name}"
        
        # Locator for specific workspace option "Client Belgium"
        self.option_client_a_belgium = "text=Client Belgium"
        
        # Locator for Continue button after workspace selection
        # Note: This button might appear as "Continue", "Next", or similar text
        self.btn_continue = "role=button[name='Continue' i]"
        self.btn_next = "role=button[name='Next' i]"
        
        # ==========================================
        # HOME PAGE / GTP IT NAVIGATION LOCATORS
        # ==========================================
        # Locator for Home navigation link/button
        self.link_home = "role=link[name='Home' i]"
        self.btn_home = "role=button[name='Home' i]"
        
        # Locator for breadcrumb Home link
        self.breadcrumb_home = "role=listitem >> role=link[name='Home' i]"
        
        # ==========================================
        # VAT CATEGORY AND DTAI APP LOCATORS
        # ==========================================
        # Locator for "Compliance" section header
        self.heading_compliance = "text=Compliance"
        
        # Locator for "Sales & Use Tax" section
        self.text_sales_use_tax = "text=/Sales.*Use.*Tax/i"
        
        # Locator for "VAT Category" section
        self.heading_vat_category = "text=/VAT.*Category/i"
        
        # Locator for "Digital Tax Administration Insights-VAT" tile/card
        # Supports multiple text variations with different dashes
        self.tile_dtai_vat = "text=/Digital\\s+Tax\\s+Administration\\s+Insights.*VAT/i"
        
        # Alternative locators for DTAI VAT tile
        self.tile_dtai_vat_exact = "text=Digital Tax Administration Insights-VAT"
        self.tile_dtai_vat_ndash = "text=Digital Tax Administration Insights – VAT"
        self.tile_dtai_vat_mdash = "text=Digital Tax Administration Insights—VAT"
        
        # Locator for clickable DTAI tile container (card/button)
        # Use when tile text alone is not clickable
        self.card_dtai_vat = "a:has-text('Digital Tax Administration Insights'), button:has-text('Digital Tax Administration Insights')"
        
        # Locator for DTAI tile description text
        self.text_dtai_description = "text=/VAT compliance.*monitoring.*reporting/i"
        
        # ==========================================
        # POST-LAUNCH LOCATORS (DTAI APP HEADER)
        # ==========================================
        # Locator for DTAI main page header
        self.heading_dtai_main = "role=heading[level=3][name='Digital Tax Administration Insights']"
        
        # Locator for breadcrumb "DTAI VAT" link (confirms app launched)
        self.breadcrumb_dtai_vat = "role=link[name='DTAI VAT']"
        
        # Locator for EY Logo in header
        self.img_ey_logo = "img[alt='Ey Logo']"
        
        # Locator for workspace dropdown in DTAI app header (after launch)
        self.combobox_workspace_header = "role=combobox[name='dropdown']"
        
        # ==========================================
        # LOADING AND WAIT INDICATORS
        # ==========================================
        # Locator for loading spinner/text
        self.text_loading = "text=Loading"
        
        # Locator for main content area (to verify page loaded)
        self.main_content = "role=main"
        
        # ==========================================
        # UTILITY METHODS
        # ==========================================
    
    def login_with_credentials(self, username: str, password: str):
        """
        Perform login with username and password
        
        Args:
            username: User email/username
            password: User password
        """
        # Wait for login page to load
        self.wait_for_element_visible("input[type='text']:visible")
        
        # Enter username
        self.page.locator(self.input_username).fill(username)
        
        # Click Sign In / Next button
        sign_in_buttons = [self.btn_sign_in, self.btn_login, self.btn_log_in]
        for btn_locator in sign_in_buttons:
            btn = self.page.locator(btn_locator)
            if btn.count() > 0:
                btn.click()
                break
        
        # Wait for password field and enter password
        self.page.wait_for_timeout(1000)
        password_field = self.page.locator(self.input_password)
        if password_field.count() == 0:
            password_field = self.page.locator(self.input_password_alt)
        password_field.fill(password)
        
        # Click Sign In button again
        for btn_locator in sign_in_buttons:
            btn = self.page.locator(btn_locator)
            if btn.count() > 0:
                btn.click()
                break
        
        # Handle "Stay signed in?" prompt if appears
        self.page.wait_for_timeout(1000)
        no_btn = self.page.locator(self.btn_stay_signed_in_no)
        skip_btn = self.page.locator(self.btn_stay_signed_in_skip)
        if no_btn.count() > 0:
            no_btn.click()
        elif skip_btn.count() > 0:
            skip_btn.click()
    
    def select_workspace_and_continue(self, workspace_name: str = "Client Belgium"):
        """
        Select workspace from dropdown and click continue
        
        Args:
            workspace_name: Name of the workspace/client to select
        """
        logger.info(f"\n=== Starting workspace selection for: {workspace_name} ===")
        
        # Wait for page to settle
        self.page.wait_for_timeout(3000)
        
        # Debug: Check what's on the page
        page_text = self.page.inner_text("body")
        logger.info(f"Page content preview: {page_text[:500]}")
        
        selected_workspace = False

        # Use JavaScript to set the Bootstrap selectpicker value directly.
        # Bootstrap hides the underlying <select> from Playwright visibility checks,
        # so select_option() and visual click approaches fail to trigger the change event.
        try:
            logger.info("Selecting workspace via JavaScript (Bootstrap selectpicker)...")
            js_result = self.page.evaluate("""(workspaceName) => {
                var selects = document.querySelectorAll('select.selectpicker');
                if (selects.length === 0) {
                    return {success: false, reason: 'No select.selectpicker found'};
                }
                for (var s of selects) {
                    var options = Array.from(s.options);
                    var target = options.find(function(o) {
                        return o.text.trim().toLowerCase() === workspaceName.toLowerCase();
                    });
                    if (target) {
                        s.value = target.value;
                        // Native change event (bubbles to framework listeners)
                        s.dispatchEvent(new Event('change', {bubbles: true}));
                        // jQuery / Bootstrap selectpicker refresh if jQuery is available
                        if (window.$ && window.$(s).selectpicker) {
                            window.$(s).trigger('change');
                            window.$(s).selectpicker('val', target.value);
                            window.$(s).selectpicker('refresh');
                        }
                        return {success: true, value: target.value, text: target.text};
                    }
                }
                var allTexts = [];
                for (var s2 of selects) {
                    Array.from(s2.options).forEach(function(o) { if (o.text) allTexts.push(o.text); });
                }
                return {success: false, reason: 'Option not found', available: allTexts};
            }""", workspace_name)

            if js_result and js_result.get("success"):
                logger.info(f"JavaScript workspace selection succeeded: {js_result.get('text')} = {js_result.get('value')}")
                selected_workspace = True
                self.page.wait_for_timeout(1500)
            else:
                reason = js_result.get("reason") if js_result else "evaluate returned None"
                available = js_result.get("available", []) if js_result else []
                logger.warning(f"[WARNING] JavaScript workspace selection failed: {reason}. Available: {available}")

        except Exception as e:
            logger.warning(f"[WARNING] Workspace selection attempt failed: {e}")
            logger.warning("Continuing - session may already have a valid workspace context")
        
        # Now click the Continue button (this is required regardless of dropdown interaction)
        logger.info("Looking for Continue button...")
        continue_btn = self.page.locator(self.btn_continue).first
        
        if continue_btn.count() == 0:
            # Try alternative locators
            continue_btn = self.page.get_by_role("button", name="Continue")
        
        # Wait for Continue button to be enabled
        max_wait = 10
        for i in range(max_wait):
            if continue_btn.count() > 0:
                try:
                    if continue_btn.is_enabled():
                        logger.info(f"Continue button is enabled (attempt {i+1}/{max_wait})")
                        break
                except:
                    pass
            self.page.wait_for_timeout(500)
        
        if continue_btn.count() == 0:
            raise Exception("Continue button not found on page")
        
        if not continue_btn.is_enabled():
            logger.warning("[WARNING] Continue button is still disabled after workspace selection")
        
        # Click Continue
        logger.info("Clicking Continue button...")
        try:
            continue_btn.click(timeout=10000)
            logger.info("Continue button clicked successfully")
        except Exception as e:
            logger.warning(f"Continue click failed: {e}")
        
        # Wait for navigation
        self.page.wait_for_timeout(5000)
        
        # Debug: Check where we landed
        current_url = self.page.url
        print(f"After clicking Continue, current URL: {current_url}")
        
        # Check if we're already in DTAI app or on home page
        page_text = self.page.inner_text("body")
        if "User Management" in page_text or "Data Ingestion" in page_text:
            print("Already inside DTAI app after client selection")
        elif "Digital Tax Administration Insights" in page_text or "Compliance" in page_text:
            print("On GTP IT home page after client selection")
        else:
            print(f"Page content after Continue: {page_text[:300]}")
        
        print("=== Workspace selection complete ===\n")
        page_text = self.page.inner_text("body")
        if "User Management" in page_text or "Data Ingestion" in page_text or "DTAI" in page_text:
            print("Already inside DTAI app after client selection")
    
    def navigate_to_dtai_vat_app(self):
        """
        Navigate to VAT DTAI application from home page
        Steps:
        1. Wait for home page to fully load
        2. Click on "Consumption Tax" category
        3. Scroll to locate "Digital Tax Administration Insights" section
        4. Click on "Digital Tax Administration Insights - VAT" app
        """
        logger.info("\n=== Starting DTAI VAT app navigation ===")
        
        # Step 1: Wait for home page to fully load
        logger.info("Step 1: Waiting for home page to fully load...")
        self.page.wait_for_timeout(3000)
        
        try:
            self.page.wait_for_load_state("networkidle", timeout=10000)
            logger.info("[OK] Page loaded (networkidle)")
        except:
            logger.info("  Timeout on networkidle, continuing...")
        
        # Additional wait for dynamic content
        self.page.wait_for_timeout(2000)
        
        # Debug current state
        current_url = self.page.url
        page_text = self.page.inner_text("body")
        logger.info(f"Current URL: {current_url}")
        
        # Check if already in DTAI app
        if "User Management" in page_text and "Data Ingestion" in page_text:
            logger.info("Already inside DTAI VAT app, no navigation needed")
            return
        
        # Step 2: Click on "Consumption Tax" category
        logger.info("\nStep 2: Clicking on 'Consumption Tax' category...")
        
        consumption_tax_clicked = False
        
        # Try multiple approaches to find and click Consumption Tax
        # Approach 1: Look for exact text
        consumption_tax = self.page.get_by_text("Consumption Tax", exact=True)
        if consumption_tax.count() > 0:
            logger.info("Found 'Consumption Tax' - clicking...")
            consumption_tax.first.click()
            consumption_tax_clicked = True
            self.page.wait_for_timeout(2000)
        else:
            # Approach 2: Look for heading containing text
            consumption_tax = self.page.locator("h2, h3, h4").filter(has_text="Consumption Tax")
            if consumption_tax.count() > 0:
                logger.info("Found 'Consumption Tax' heading - clicking...")
                consumption_tax.first.click()
                consumption_tax_clicked = True
                self.page.wait_for_timeout(2000)
            else:
                # Approach 3: Use JavaScript to find and click
                clicked_js = self.page.evaluate("""() => {
                    const norm = (v) => (v || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                    const elements = Array.from(document.querySelectorAll('*'));
                    
                    for (const elem of elements) {
                        const text = norm(elem.innerText || elem.textContent);
                        if (text === 'consumption tax' || text === 'vat') {
                            console.log('Found Consumption Tax element:', elem);
                            elem.click();
                            return true;
                        }
                    }
                    return false;
                }""")
                
                if clicked_js:
                    consumption_tax_clicked = True
                    logger.info("[OK] Clicked 'Consumption Tax' using JavaScript")
                    self.page.wait_for_timeout(2000)
        
        if consumption_tax_clicked:
            logger.info("[OK] Successfully clicked Consumption Tax category")
        else:
            logger.info("[WARNING] Consumption Tax category not found or not clickable")
            logger.info("  Will search entire page for DTAI app")
        
        # Step 3: Scroll to locate "Digital Tax Administration Insights" section
        logger.info("\nStep 3: Scrolling to locate 'Digital Tax Administration Insights' section...")
        
        # Use JavaScript to find and scroll to DTAI section
        dtai_section_found = self.page.evaluate("""() => {
            const norm = (v) => (v || '').replace(/\\s+/g, ' ').trim().toLowerCase();
            
            // Look for section heading or container with DTAI text
            const elements = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, section, div[class*="section"]'));
            
            for (const elem of elements) {
                const text = norm(elem.innerText || elem.textContent);
                if (text.includes('digital tax administration insights') || 
                    text.includes('digital tax administration insight')) {
                    console.log('Found DTAI section:', elem);
                    elem.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    return { found: true, text: elem.innerText.substring(0, 100) };
                }
            }
            
            return { found: false };
        }""")
        
        if dtai_section_found and dtai_section_found.get('found'):
            logger.info(f"[OK] Found DTAI section: {dtai_section_found.get('text', '')[:50]}...")
            self.page.wait_for_timeout(1500)
        else:
            logger.info("  DTAI section heading not found, will search for DTAI app directly")
        
        # Step 4: Click on "Digital Tax Administration Insights - VAT" app
        logger.info("\nStep 4: Looking for 'Digital Tax Administration Insights - VAT' app...")
        
        # Use comprehensive JavaScript to find and click the DTAI VAT app
        dtai_clicked = self.page.evaluate("""() => {
            const norm = (v) => (v || '').replace(/\\s+/g, ' ').trim().toLowerCase();
            const isVisible = (el) => {
                if (!el) return false;
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return rect.width > 0 &&
                       rect.height > 0 &&
                       style.visibility !== 'hidden' &&
                       style.display !== 'none' &&
                       style.opacity !== '0';
            };
            
            const isExactDTAIVAT = (text) => {
                const t = norm(text);
                return /digital tax administration insights\s*-\s*vat/.test(t) ||
                       /digital tax administration insights\s+vat/.test(t);
            };
            
            // Search all clickable elements
            const selectors = [
                'a', 'button', '[role="button"]', '[role="link"]',
                '.card', '.tile', '[class*="card"]', '[class*="tile"]', '[class*="app"]',
                'div[onclick]', '[data-testid]'
            ];
            
            const candidates = Array.from(document.querySelectorAll(selectors.join(', ')));
            console.log(`Searching ${candidates.length} elements for DTAI VAT app`);

            const tryClick = (elem) => {
                if (!isVisible(elem)) return null;
                const text = elem.innerText || elem.textContent || '';
                const compactText = text.replace(/\\s+/g, ' ').trim();
                if (!compactText) return null;
                const clickable = elem.closest('a, button, [role="button"], [onclick]') || elem;
                if (!isVisible(clickable)) return null;
                if (clickable.disabled || clickable.getAttribute('aria-disabled') === 'true') return null;
                elem.scrollIntoView({ behavior: 'smooth', block: 'center' });
                clickable.click();
                return { success: true, text: compactText.substring(0, 140) };
            };

            // Click the best exact-title match (shortest visible candidate)
            const matches = [];
            for (const elem of candidates) {
                const text = elem.innerText || elem.textContent || '';
                const compact = (text || '').replace(/\\s+/g, ' ').trim();
                if (!compact) continue;
                if (!isExactDTAIVAT(compact)) continue;
                if (!isVisible(elem)) continue;
                const clickable = elem.closest('a, button, [role="button"], [onclick]') || elem;
                if (!isVisible(clickable)) continue;
                if (clickable.disabled || clickable.getAttribute('aria-disabled') === 'true') continue;
                matches.push({ elem, len: compact.length, text: compact });
            }
            matches.sort((a, b) => a.len - b.len);
            for (const m of matches) {
                const result = tryClick(m.elem);
                if (result) return result;
            }
            
            return { success: false, totalSearched: candidates.length };
        }""")
        
        if dtai_clicked and dtai_clicked.get('success'):
            logger.info(f"[OK] Successfully clicked DTAI VAT app")
            logger.info(f"  App text: {dtai_clicked.get('text', '')[:80]}...")
            self.page.wait_for_timeout(5000)
            
            # Verify navigation
            new_url = self.page.url
            new_page_text = self.page.inner_text("body")[:200]
            logger.info(f"Navigated to: {new_url}")
            logger.info(f"Page content: {new_page_text}...")
            logger.info("=== DTAI VAT app navigation complete ===\n")
        else:
            logger.info(f"[WARNING] Could not find or click DTAI VAT app")
            logger.info(f"  Searched {dtai_clicked.get('totalSearched', 0)} elements")
            
            # Take screenshot for debugging
            self.page.screenshot(path='reports/screenshots/dtai_app_not_found.png', full_page=True)
            logger.info(f"  Screenshot saved to: reports/screenshots/dtai_app_not_found.png")
            
            raise AssertionError("Digital Tax Administration Insights - VAT app not found on page")
    
    def verify_dtai_app_launched(self):
        """
        Verify that DTAI application has successfully launched
        Returns True if launched successfully, False otherwise
        """
        # Check for DTAI main heading
        heading = self.page.locator(self.heading_dtai_main)
        if heading.count() > 0:
            return True
        
        # Check for DTAI VAT breadcrumb
        breadcrumb = self.page.locator(self.breadcrumb_dtai_vat)
        if breadcrumb.count() > 0:
            return True
        
        return False
    
    def wait_for_page_ready(self, timeout_ms: int = 30000):
        """
        Wait for page to be fully loaded and ready
        
        Args:
            timeout_ms: Maximum time to wait in milliseconds
        """
        self.page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
        self.page.wait_for_load_state("networkidle", timeout=timeout_ms)
        
        # Wait for loading indicator to disappear
        loading = self.page.locator(self.text_loading)
        if loading.count() > 0:
            self.wait_for_element_invisibility(self.text_loading)
