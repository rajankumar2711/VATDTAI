import logging
import re
from playwright.sync_api import Page

from pageobjects.base_page import BasePage

logger = logging.getLogger(__name__)


class VatReconciliationPage(BasePage):
    """Page object for VAT DTAI Reconciliation module."""

    def __init__(self, page: Page):
        super().__init__(page)
        logger.info("Initializing VatReconciliationPage")

        self.reconciliation_tab_selectors = [
            "a[role='tab']:has-text('Reconciliation')",
            "role=tab[name='Reconciliation' i]",
            "[role='tab']:has-text('Reconciliation')",
            "a:has-text('Reconciliation')",
        ]
        self.active_pane = "div.tab-pane.active"
        self.header_selectors = [
            "div.tab-pane.active h2:has-text('Reconciliation')",
            "div.tab-pane.active h3:has-text('Reconciliation')",
        ]
        self.reconcile_button_selectors = [
            "div.tab-pane.active button:has-text('Reconcile')",
            "button:has-text('Reconcile')",
        ]
        self.analytics_modal_ok_selectors = [
            "div.modal-scrollable button:has-text('OK')",
            "div.modal-scrollable button.btn-default",
            "div.customAlertoverlay button:has-text('OK')",
            "button.btn-default:has-text('OK')",
            "button:has-text('OK')",
        ]

    # ---------- helpers ----------
    def _is_locator_visible(self, selector: str, timeout: int = 2000) -> bool:
        try:
            target = self.page.locator(selector).first
            return target.count() > 0 and target.is_visible(timeout=timeout)
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
            if self._is_locator_visible(f"{self.active_pane} {tag}:has-text('{text_value}')", timeout=800):
                return True
        try:
            return bool(self.page.evaluate("""(value) => {
                const norm = (v) => (v || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                const pane = document.querySelector('div.tab-pane.active') || document.body;
                const nodes = Array.from(pane.querySelectorAll('h2,h3,h4,h5,label,span,div,p,strong,b'));
                return nodes.some((el) => {
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

    # ---------- navigation ----------
    def navigate_to_reconciliation_module(self) -> bool:
        logger.info("Navigating to Reconciliation module")
        self._dismiss_analytics_popup_if_present()

        for _ in range(3):
            for selector in self.reconciliation_tab_selectors:
                try:
                    tab = self.page.locator(selector).first
                    if tab.count() > 0 and tab.is_visible(timeout=1000):
                        tab.click(force=True)
                        self.page.wait_for_timeout(1500)
                        self._dismiss_analytics_popup_if_present()
                        if self.is_reconciliation_module_accessible():
                            return True
                except Exception:
                    continue

            try:
                clicked = self.page.evaluate("""() => {
                    const norm = (v) => (v || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                    const nodes = Array.from(document.querySelectorAll('a,[role="tab"],[role="button"],button'));
                    for (const node of nodes) {
                        if (norm(node.innerText || node.textContent) === 'reconciliation') {
                            node.click();
                            return true;
                        }
                    }
                    return false;
                }""")
                self.page.wait_for_timeout(2000)
                self._dismiss_analytics_popup_if_present()
                if clicked and self.is_reconciliation_module_accessible():
                    return True
            except Exception:
                pass
        return self.is_reconciliation_module_accessible()

    def is_reconciliation_module_accessible(self) -> bool:
        for selector in self.header_selectors:
            if self._is_locator_visible(selector, timeout=1500):
                return True
        return self._is_text_visible("Reconciliation")

    def get_reconciliation_header(self) -> str:
        for selector in self.header_selectors:
            try:
                header = self.page.locator(selector).first
                if header.count() > 0 and header.is_visible(timeout=1000):
                    return header.inner_text().strip()
            except Exception:
                continue
        return "Reconciliation" if self._is_text_visible("Reconciliation") else ""

    # ---------- input panel ----------
    def is_input_panel_visible(self) -> bool:
        """Verify the reconciliation input panel exposes mandatory selectors."""
        selector_controls = (
            f"{self.active_pane} select, "
            f"{self.active_pane} [role='combobox'], "
            f"{self.active_pane} input[type='file'], "
            f"{self.active_pane} .selectpicker, "
            f"{self.active_pane} input.textinput-group__textinput"
        )
        try:
            if self.page.locator(selector_controls).count() > 0:
                return True
        except Exception:
            pass
        return self._is_text_visible("Country") or self._is_text_visible("Source System")

    def is_reconcile_action_visible(self) -> bool:
        for selector in self.reconcile_button_selectors:
            if self._is_locator_visible(selector, timeout=1500):
                return True
        return False

    # ---------- reconciliation flow ----------
    def upload_gl_and_erp_files(self, gl_path: str, erp_path: str) -> dict:
        """Upload GL and ERP transaction files into available file inputs."""
        self._dismiss_analytics_popup_if_present()
        try:
            file_inputs = self.page.locator(f"{self.active_pane} input[type='file']")
            count = file_inputs.count()
        except Exception:
            count = 0

        if count == 0:
            return {"ok": False, "reason": "No file input controls found in Reconciliation panel"}

        try:
            if count >= 2:
                file_inputs.nth(0).set_input_files(gl_path)
                self.page.wait_for_timeout(1500)
                file_inputs.nth(1).set_input_files(erp_path)
            else:
                file_inputs.nth(0).set_input_files([gl_path, erp_path])
            self.page.wait_for_timeout(2500)
            return {"ok": True, "inputs": count}
        except Exception as e:
            return {"ok": False, "reason": f"file upload failed: {e}"}

    def apply_valid_filters(self) -> dict:
        """Best-effort population of reconciliation filter selectors."""
        self.page.wait_for_timeout(500)
        try:
            state = self.page.evaluate("""() => {
                const norm = v => (v || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                const pane = document.querySelector('div.tab-pane.active') || document.body;
                const picked = [];
                Array.from(pane.querySelectorAll('select')).forEach(sel => {
                    const options = Array.from(sel.options || []);
                    let target = options.find(o => o.value && !norm(o.text).includes('all') && !norm(o.text).includes('select'));
                    if (!target) target = options.find(o => o.value);
                    if (target) {
                        sel.value = target.value;
                        sel.dispatchEvent(new Event('change', {bubbles: true}));
                        if (window.$) window.$(sel).trigger('change');
                        picked.push((target.text || '').trim());
                    }
                });
                return {ok: true, picked};
            }""")
            self.page.wait_for_timeout(1000)
            return state or {"ok": True}
        except Exception as e:
            return {"ok": False, "reason": str(e)}

    def click_reconcile(self) -> dict:
        for selector in self.reconcile_button_selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.count() > 0 and btn.is_visible(timeout=1500):
                    if not btn.is_enabled():
                        return {"ok": False, "reason": "Reconcile button is disabled"}
                    btn.click(force=True)
                    self.page.wait_for_timeout(4000)
                    self._dismiss_analytics_popup_if_present()
                    return {"ok": True}
            except Exception:
                continue
        return {"ok": False, "reason": "Reconcile button not found"}

    def is_reconciliation_executed(self) -> bool:
        """Detect a reconciliation result surface after clicking Reconcile."""
        self.page.wait_for_timeout(1500)
        if self.is_reconciliation_details_table_displayed():
            return True
        return self._is_text_visible("Reconciliation Details") or self._is_text_visible("Match")

    def is_reconciliation_details_table_displayed(self) -> bool:
        table_selectors = [
            f"{self.active_pane} table:visible",
            f"{self.active_pane} .tabulator:visible",
            "div.modal-dialog table:visible",
        ]
        for selector in table_selectors:
            if self._is_locator_visible(selector, timeout=1500):
                return True
        return self._is_text_visible("Reconciliation Details")

    def summary_has_match_and_mismatch_rows(self) -> bool:
        return self._is_text_visible("Match") and self._is_text_visible("Mismatch")

    def get_match_mismatch_counts(self) -> dict:
        """Return numeric Match/Mismatch counts if present in the summary."""
        try:
            data = self.page.evaluate("""() => {
                const pane = document.querySelector('div.tab-pane.active') || document.body;
                const rows = Array.from(pane.querySelectorAll('tr, .tabulator-row, li, div'));
                const result = {};
                const grab = (label) => {
                    for (const row of rows) {
                        const txt = (row.innerText || '').replace(/\\s+/g, ' ').trim();
                        const re = new RegExp('^' + label + '\\\\b', 'i');
                        if (re.test(txt)) {
                            const m = txt.match(/(-?\\d[\\d,]*)/);
                            if (m) return m[1].replace(/,/g, '');
                        }
                    }
                    return null;
                };
                result.match = grab('Match');
                result.mismatch = grab('Mismatch');
                return result;
            }""")
            return data or {}
        except Exception:
            return {}

    @staticmethod
    def is_numeric(value) -> bool:
        if value is None:
            return False
        return bool(re.fullmatch(r"-?\d+", str(value).strip()))
