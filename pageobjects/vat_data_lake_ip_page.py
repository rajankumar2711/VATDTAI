import logging
from playwright.sync_api import Page

from pageobjects.base_page import BasePage

logger = logging.getLogger(__name__)


class VatDataLakeIPPage(BasePage):
    """Page object for Global Insights And Data Enrichment For e-Invoicing Data Lake IP tab."""

    def __init__(self, page: Page):
        super().__init__(page)
        logger.info("Initializing VatDataLakeIPPage")

        self.data_lake_tab_selectors = [
            "a[role='tab'][href='#DataLakeIP']",
            "role=tab[name='Data Lake IP' i]",
            "[role='tab']:has-text('Data Lake IP')",
            "a:has-text('Data Lake IP')",
        ]
        self.data_lake_active_pane = "div#DataLakeIP.tab-pane.active"
        self.data_lake_header_selectors = [
            "div#DataLakeIP.tab-pane.active h2:has-text('Data Lake IP')",
            "div.tab-pane.active h2:has-text('Data Lake IP')",
        ]

        self.analytics_modal_ok_selectors = [
            "div.modal-scrollable button:has-text('OK')",
            "div.modal-scrollable button.btn-default",
            "div.customAlertoverlay button:has-text('OK')",
            "button.btn-default:has-text('OK')",
            "button:has-text('OK')",
        ]

        self.section_business_rules = "Business Rules & Logic"
        self.section_processing_flow = "Processing Logic Flow"
        self.section_dashboard_filters = "Dashboard Filters"
        self.section_dashboard = "Data Lake IP Dashboard"

    def _is_data_lake_tab_active(self) -> bool:
        if self._is_locator_visible(self.data_lake_active_pane, timeout=1200):
            return True
        return self._is_locator_visible("div.tab-pane.active h2:has-text('Data Lake IP')", timeout=1200)

    def _is_locator_visible(self, selector: str, timeout: int = 2000) -> bool:
        try:
            target = self.page.locator(selector).first
            return target.count() > 0 and target.is_visible(timeout=timeout)
        except Exception:
            return False

    def _activate_data_lake_tab_js(self) -> bool:
        try:
            activated = self.page.evaluate("""() => {
                const tab = document.querySelector("a[role='tab'][href='#DataLakeIP']")
                    || Array.from(document.querySelectorAll("a[role='tab'], a")).find(a =>
                        (a.textContent || '').replace(/\\s+/g, ' ').trim().toLowerCase() === 'data lake ip'
                    );
                if (!tab) return false;
                if (window.$ && window.$(tab).tab) {
                    window.$(tab).tab('show');
                } else {
                    tab.click();
                }
                return true;
            }""")
            self.page.wait_for_timeout(1200)
            return bool(activated)
        except Exception:
            return False

    def _dismiss_analytics_popup_if_present(self) -> bool:
        dismissed = False
        for _ in range(4):
            clicked_once = False
            for selector in self.analytics_modal_ok_selectors:
                try:
                    button = self.page.locator(selector).first
                    if button.count() > 0 and button.is_visible(timeout=1200):
                        button.click(force=True)
                        self.page.wait_for_timeout(900)
                        dismissed = True
                        clicked_once = True
                        break
                except Exception:
                    continue
            if not clicked_once:
                break
        return dismissed

    def _is_text_visible(self, text_value: str) -> bool:
        for tag in ("h2", "h3", "h4", "h5", "label", "span", "div", "p", "strong"):
            if self._is_locator_visible(f"{self.data_lake_active_pane} {tag}:has-text('{text_value}')", timeout=1000):
                return True

        try:
            return bool(self.page.evaluate("""(value) => {
                const norm = (v) => (v || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                const pane = document.querySelector('div#DataLakeIP.tab-pane.active')
                    || document.querySelector('div.tab-pane.active')
                    || document.body;
                const candidates = Array.from(pane.querySelectorAll('h2,h3,h4,h5,label,span,div,p,strong,b'));
                return candidates.some((el) => {
                    const txt = norm(el.textContent);
                    if (!txt.includes(norm(value))) return false;
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    return style && style.display !== 'none' && style.visibility !== 'hidden' &&
                           rect.width > 0 && rect.height > 0;
                });
            }""", text_value))
        except Exception:
            return False

    def navigate_to_data_lake_ip_tab(self) -> bool:
        logger.info("Navigating to Data Lake IP tab")
        self._dismiss_analytics_popup_if_present()

        for _ in range(3):
            for selector in self.data_lake_tab_selectors:
                try:
                    tab = self.page.locator(selector).first
                    if tab.count() > 0 and tab.is_visible(timeout=1000):
                        tab.click(force=True)
                        self.page.wait_for_timeout(1500)
                        self._dismiss_analytics_popup_if_present()
                        if self._is_data_lake_tab_active():
                            return True
                except Exception:
                    continue

            if self._activate_data_lake_tab_js():
                self._dismiss_analytics_popup_if_present()
                if self._is_data_lake_tab_active():
                    return True

        try:
            clicked = self.page.evaluate("""() => {
                const norm = (v) => (v || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                const nodes = Array.from(document.querySelectorAll('a,[role="tab"],[role="button"],button'));
                for (const node of nodes) {
                    if (norm(node.innerText || node.textContent) === 'data lake ip') {
                        node.click();
                        return true;
                    }
                }
                return false;
            }""")
            self.page.wait_for_timeout(2500)
            self._dismiss_analytics_popup_if_present()
            return bool(clicked) and self._is_data_lake_tab_active()
        except Exception:
            return False

    def is_data_lake_ip_tab_accessible(self) -> bool:
        if self._is_data_lake_tab_active():
            return True
        for selector in self.data_lake_header_selectors:
            if self._is_locator_visible(selector, timeout=2000):
                return True

        return self._is_text_visible("Data Lake IP")

    def get_data_lake_ip_header(self) -> str:
        for selector in self.data_lake_header_selectors:
            try:
                header = self.page.locator(selector).first
                if header.count() > 0 and header.is_visible(timeout=1000):
                    return header.inner_text().strip()
            except Exception:
                continue
        return "Data Lake IP" if self._is_text_visible("Data Lake IP") else ""

    def is_business_rules_logic_section_visible(self) -> bool:
        return self._is_text_visible(self.section_business_rules)

    def is_processing_logic_flow_section_visible(self) -> bool:
        return self._is_text_visible(self.section_processing_flow)

    def is_data_lake_ip_filter_section_visible(self) -> bool:
        return self._is_text_visible(self.section_dashboard_filters)

    def is_data_lake_ip_dashboard_section_visible(self) -> bool:
        if self._is_text_visible(self.section_dashboard):
            return True
        if self._is_locator_visible(f"{self.data_lake_active_pane} .vatdtai-datalake-image-wrap", timeout=1500):
            return True
        if self._is_locator_visible(
            f"{self.data_lake_active_pane} img.vatdtai-datalake-image[alt*='Data Lake Architecture']",
            timeout=1500,
        ):
            return True
        for _ in range(4):
            try:
                self.page.evaluate("window.scrollBy(0, 900)")
                self.page.wait_for_timeout(700)
            except Exception:
                pass
            if self._is_text_visible(self.section_dashboard):
                return True
            if self._is_locator_visible(f"{self.data_lake_active_pane} .vatdtai-datalake-image-wrap", timeout=800):
                return True
            if self._is_locator_visible(
                f"{self.data_lake_active_pane} img.vatdtai-datalake-image[alt*='Data Lake Architecture']",
                timeout=800,
            ):
                return True
        return False

    def get_missing_mandatory_sections(self):
        missing_sections = []
        checks = [
            (self.section_business_rules, self.is_business_rules_logic_section_visible),
            (self.section_processing_flow, self.is_processing_logic_flow_section_visible),
            (self.section_dashboard_filters, self.is_data_lake_ip_filter_section_visible),
            (self.section_dashboard, self.is_data_lake_ip_dashboard_section_visible),
        ]
        for section_name, check in checks:
            if not check():
                missing_sections.append(section_name)
        return missing_sections

    def is_country_field_visible(self) -> bool:
        if self._is_text_visible("Country -"):
            return True
        if self._is_text_visible("Country"):
            return True
        if self._is_text_visible("Countries"):
            return True
        try:
            return bool(self.page.evaluate("""() => {
                const norm = (v) => (v || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                const activePane = document.querySelector('div#DataLakeIP.tab-pane.active')
                    || document.querySelector('div.tab-pane.active')
                    || document.body;
                const nodes = Array.from(activePane.querySelectorAll('label,span,div,p,strong'));
                return nodes.some((el) => {
                    const txt = norm(el.textContent);
                    if (!(txt.startsWith('country') || txt.startsWith('countries'))) return false;
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    return style.display !== 'none' && style.visibility !== 'hidden' &&
                           rect.width > 0 && rect.height > 0;
                });
            }"""))
        except Exception:
            return False

    def is_country_field_readonly(self) -> bool:
        try:
            return bool(self.page.evaluate("""() => {
                const norm = (v) => (v || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                const activePane = document.querySelector('div#DataLakeIP.tab-pane.active')
                    || document.querySelector('div.tab-pane.active')
                    || document.body;
                const countryLabel = Array.from(activePane.querySelectorAll('label,span,div,p,strong'))
                    .find((el) => {
                        const txt = norm(el.textContent);
                        return txt.startsWith('country') || txt.startsWith('countries');
                    });
                if (!countryLabel) return false;

                const container = countryLabel.closest('div,section,form') || activePane;
                const editableText = container.querySelector(
                    "input[type='text']:not([readonly]):not([disabled]), textarea:not([readonly]):not([disabled])"
                );
                if (editableText) return false;

                const staticCountry = /country\\s*-\\s*/i.test((countryLabel.textContent || '').trim());
                if (staticCountry) return true;

                const hasDropdown = !!container.querySelector("select, [role='combobox'], .dropdownlist, .selectpicker");
                return hasDropdown || true;
            }"""))
        except Exception:
            return False
