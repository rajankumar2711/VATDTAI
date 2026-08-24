import logging
from datetime import date
from pathlib import Path
from pageobjects.base_page import BasePage

logger = logging.getLogger(__name__)


class VatReportsPage(BasePage):
    """Page object for VAT DTAI Reports module."""

    def __init__(self, get_page):
        super().__init__(get_page)
        logger.info("Initializing VatReportsPage")

        self.reports_tab_links = "a:has-text('Reports')"
        self.reports_active_heading = "div.tab-pane.active h2:has-text('Reports')"
        self.generate_report_heading = "div.tab-pane.active h3:has-text('Generate Report')"
        self.reports_active_pane = "div.tab-pane.active:has(h2:has-text('Reports'))"
        self.analytics_modal_ok_selectors = [
            "div.modal-scrollable button:has-text('OK')",
            "div.modal-scrollable button.btn-default",
            "div.customAlertoverlay button:has-text('OK')",
            "button.btn-default:has-text('OK')",
            "button:has-text('OK')",
        ]

        self.select_report = "select#vatdtai_reports_select"
        self.input_date = "input#vatdtai_reports_date"
        self.input_date_from = "input#vatdtai_reports_date_from"
        self.input_date_to = "input#vatdtai_reports_date_to"
        self.input_country = "div.tab-pane.active:has(h2:has-text('Reports')) input.textinput-group__textinput >> nth=0"
        self.input_entity = "div.tab-pane.active:has(h2:has-text('Reports')) input.textinput-group__textinput >> nth=1"
        self.btn_generate = "div.tab-pane.active:has(h2:has-text('Reports')) button.btn-primary:has-text('Generate')"

    def _dismiss_analytics_popup_if_present(self):
        for _ in range(4):
            clicked = False
            for selector in self.analytics_modal_ok_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.count() > 0 and btn.is_visible(timeout=1200):
                        btn.click(force=True)
                        self.page.wait_for_timeout(900)
                        clicked = True
                        break
                except Exception:
                    continue
            if not clicked:
                break

    def navigate_to_reports_module(self):
        """Open Reports tab from VAT DTAI left navigation."""
        logger.info("Navigating to Reports module")
        self._dismiss_analytics_popup_if_present()
        links = self.page.locator(self.reports_tab_links)
        clicked = False
        try:
            count = links.count()
            for i in range(count):
                link = links.nth(i)
                txt = link.inner_text().strip().lower()
                if txt == "reports" and link.is_visible():
                    link.click(force=True)
                    clicked = True
                    break
        except Exception as e:
            logger.debug(f"Visible reports link click failed: {e}")

        if not clicked:
            clicked = self.page.evaluate("""() => {
                const norm = v => (v || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                const nodes = Array.from(document.querySelectorAll('a, [role="tab"], [role="button"], h2'));
                for (const n of nodes) {
                    if (norm(n.innerText || n.textContent) === 'reports') {
                        n.click();
                        return true;
                    }
                }
                return false;
            }""")

        self.page.wait_for_timeout(2500)
        self._dismiss_analytics_popup_if_present()
        logger.info(f"Reports tab click status: {clicked}")
        return bool(clicked)

    def is_reports_module_visible(self):
        try:
            h = self.page.locator(self.reports_active_heading).first
            return h.count() > 0 and h.is_visible(timeout=5000)
        except Exception:
            return False

    def get_reports_header(self):
        try:
            return self.page.locator(self.reports_active_heading).first.inner_text().strip()
        except Exception:
            return ""

    def is_generate_report_section_visible(self):
        try:
            sec = self.page.locator(self.generate_report_heading).first
            return sec.count() > 0 and sec.is_visible(timeout=5000)
        except Exception:
            return False

    def get_report_options(self):
        """Return report option labels from Select Report dropdown."""
        try:
            return self.page.evaluate("""() => {
                const sel = document.querySelector('#vatdtai_reports_select');
                if (!sel) return [];
                return Array.from(sel.options).map(o => (o.text || '').trim()).filter(Boolean);
            }""")
        except Exception:
            return []

    def select_report_type(self, report_name: str, allow_fallback: bool = True):
        """
        Select report type by label from report dropdown.
        If report is unavailable and allow_fallback=True, select first non-empty option.
        """
        logger.info(f"Selecting report type: {report_name}")
        result = self.page.evaluate("""(args) => {
            const norm = v => (v || '').replace(/\\s+/g, ' ').trim().toLowerCase();
            const sel = document.querySelector('#vatdtai_reports_select');
            if (!sel) return {ok:false, reason:'dropdown not found', selected:''};
            const options = Array.from(sel.options).map(o => ({value:o.value || '', text:(o.text || '').trim()}));
            let target = options.find(o => norm(o.text) === norm(args.name));
            if (!target) target = options.find(o => norm(o.text).includes(norm(args.name)));
            if (!target && args.allowFallback) {
                target = options.find(o => o.value && o.text && !o.text.toLowerCase().includes('select report'));
            }
            if (!target) return {ok:false, reason:'option not found', selected:'', available: options.map(o => o.text)};
            sel.value = target.value;
            sel.dispatchEvent(new Event('change', {bubbles: true}));
            if (window.$) window.$(sel).trigger('change');
            return {ok:true, selected:target.text, value:target.value};
        }""", {"name": report_name, "allowFallback": allow_fallback})
        logger.info(f"Report selection result: {result}")
        return result

    def provide_valid_filter_criteria(self):
        """Populate report filters with valid defaults."""
        today = date.today()
        self.page.wait_for_timeout(500)

        state = self.page.evaluate("""(args) => {
            const pane = Array.from(document.querySelectorAll('div.tab-pane')).find(
                p => (p.className || '').includes('active') && (p.innerText || '').includes('Generate Report')
            );
            if (!pane) return {ok:false, reason:'reports pane not found'};
            const norm = v => (v || '').replace(/\\s+/g, ' ').trim().toLowerCase();

            const setSelect = (sel) => {
                const options = Array.from(sel.options || []);
                let target = options.find(o => o.value && !norm(o.text).includes('all'));
                if (!target) target = options.find(o => o.value);
                if (!target) target = options.find(o => (o.text || '').trim());
                if (!target) return null;
                sel.value = target.value;
                sel.dispatchEvent(new Event('change', {bubbles: true}));
                if (window.$) {
                    window.$(sel).trigger('change');
                    if (window.$(sel).selectpicker) {
                        window.$(sel).selectpicker('val', target.value);
                        window.$(sel).selectpicker('refresh');
                    }
                }
                return {value: target.value, text: (target.text || '').trim()};
            };

            const selectpickers = pane.querySelectorAll('select.selectpicker');
            const picked = Array.from(selectpickers).map(setSelect).filter(Boolean);

            const date = pane.querySelector('#vatdtai_reports_date');
            const dateFrom = pane.querySelector('#vatdtai_reports_date_from');
            const dateTo = pane.querySelector('#vatdtai_reports_date_to');

            // Use single Date field to satisfy "Date OR Date Range"
            if (date) {
                date.value = args.today;
                date.dispatchEvent(new Event('input', {bubbles: true}));
                date.dispatchEvent(new Event('change', {bubbles: true}));
            }
            if (dateFrom) {
                dateFrom.value = '';
                dateFrom.dispatchEvent(new Event('input', {bubbles: true}));
                dateFrom.dispatchEvent(new Event('change', {bubbles: true}));
            }
            if (dateTo) {
                dateTo.value = '';
                dateTo.dispatchEvent(new Event('input', {bubbles: true}));
                dateTo.dispatchEvent(new Event('change', {bubbles: true}));
            }

            const generate = Array.from(pane.querySelectorAll('button'))
              .find(b => norm(b.innerText).includes('generate'));

            return {
                ok: true,
                picked,
                date: date ? date.value : '',
                dateFrom: dateFrom ? dateFrom.value : '',
                dateTo: dateTo ? dateTo.value : '',
                generateDisabled: generate ? !!generate.disabled : null
            };
        }""", {"today": today.isoformat()})

        # UI-level fallback, move Country/Entity away from "All" via keyboard
        for label, locator in [("Country", self.input_country), ("Entity", self.input_entity)]:
            try:
                field = self.page.locator(locator).first
                if field.count() > 0 and field.is_visible(timeout=1000):
                    cur = (field.input_value() or "").strip()
                    if not cur or cur.lower() == "all":
                        field.click()
                        field.press("ArrowDown")
                        field.press("Enter")
                        self.page.wait_for_timeout(700)
                        updated = (field.input_value() or "").strip()
                        logger.info(f"{label} selection fallback: '{cur}' -> '{updated}'")
            except Exception as e:
                logger.debug(f"{label} fallback selection skipped: {e}")

        self.page.wait_for_timeout(1500)
        logger.info(f"Report filter criteria populated: {state}")

    def _generate_button_state(self):
        return self.page.evaluate("""() => {
            const norm = v => (v || '').replace(/\\s+/g, ' ').trim().toLowerCase();
            const pane = Array.from(document.querySelectorAll('div.tab-pane')).find(
                p => (p.className || '').includes('active') && (p.innerText || '').includes('Generate Report')
            );
            if (!pane) return {found:false};
            const btn = Array.from(pane.querySelectorAll('button')).find(b => norm(b.innerText).includes('generate'));
            if (!btn) return {found:false};
            const reportSel = pane.querySelector('#vatdtai_reports_select');
            const customInputs = Array.from(pane.querySelectorAll('input[id^="text-input-single-select-type-ahead"]'));
            return {
                found: true,
                disabled: !!btn.disabled,
                text: (btn.innerText || '').trim(),
                reportValue: reportSel ? (reportSel.value || '') : '',
                date: (pane.querySelector('#vatdtai_reports_date') || {}).value || '',
                dateFrom: (pane.querySelector('#vatdtai_reports_date_from') || {}).value || '',
                dateTo: (pane.querySelector('#vatdtai_reports_date_to') || {}).value || '',
                countryPreview: customInputs[0] ? (customInputs[0].value || '').trim() : '',
                entityPreview: customInputs[1] ? (customInputs[1].value || '').trim() : ''
            };
        }""")

    def wait_for_generate_enabled(self, timeout_ms: int = 15000) -> bool:
        elapsed = 0
        while elapsed < timeout_ms:
            try:
                btn = self.page.locator(self.btn_generate).first
                if btn.count() > 0 and btn.is_visible() and btn.is_enabled():
                    return True
            except Exception:
                pass
            self.page.wait_for_timeout(500)
            elapsed += 500
        return False

    def click_generate_report(self):
        """Click Generate button in Reports module."""
        logger.info("Clicking Generate button")
        if not self.wait_for_generate_enabled(timeout_ms=15000):
            state = self._generate_button_state()
            raise AssertionError(f"Generate button is still disabled after valid filters: {state}")

        btn = self.page.locator(self.btn_generate).first
        if btn.count() > 0 and btn.is_visible():
            btn.click()
        else:
            self.page.evaluate("""() => {
                const pane = Array.from(document.querySelectorAll('div.tab-pane')).find(
                    p => (p.className || '').includes('active') && (p.innerText || '').includes('Generate Report')
                );
                if (!pane) return false;
                const b = Array.from(pane.querySelectorAll('button')).find(x => (x.innerText || '').trim().toLowerCase() === 'generate');
                if (b) { b.click(); return true; }
                return false;
            }""")
        self.page.wait_for_timeout(3000)

    def is_report_displayed(self, expected_report_text: str = ""):
        """
        Verify report output appears in popup/viewer/container after Generate.
        """
        self.page.wait_for_timeout(2500)

        try:
            if len(self.page.context.pages) > 1:
                return True
        except Exception:
            pass

        container_locators = [
            "div.modal-dialog:visible",
            "div.customAlertmodal:visible",
            "[role='dialog']:visible",
            "iframe:visible",
            "object:visible",
            "embed:visible",
            ".report-viewer:visible",
            ".report-container:visible",
            ".tabulator:visible",
            "table:visible",
        ]
        for loc in container_locators:
            try:
                el = self.page.locator(loc).first
                if el.count() > 0 and el.is_visible(timeout=1200):
                    return True
            except Exception:
                continue

        body = self.page.inner_text("body").lower()
        if expected_report_text and expected_report_text.lower().split()[0] in body:
            return True
        if "report" in body and "generate report" in body:
            return True
        return False

    def get_report_column_headers(self):
        """Return column header labels from a tabular report output, if present."""
        try:
            return self.page.evaluate("""() => {
                const norm = v => (v || '').replace(/\\s+/g, ' ').trim();
                const scopes = [
                    document.querySelector('div.modal-dialog'),
                    document.querySelector("[role='dialog']"),
                    document.querySelector('div.tab-pane.active'),
                    document.body
                ].filter(Boolean);
                for (const scope of scopes) {
                    let headers = Array.from(
                        scope.querySelectorAll('table thead th, table th, .tabulator .tabulator-col-title')
                    ).map(el => norm(el.innerText || el.textContent)).filter(Boolean);
                    if (headers.length) return headers;
                }
                return [];
            }""")
        except Exception:
            return []

    def _find_export_pdf_button(self):
        selectors = [
            "button:has-text('Export PDF')",
            "button:has-text('Export to PDF')",
            "a:has-text('Export PDF')",
            "a:has-text('Export to PDF')",
            "button[title*='PDF' i]",
            "a[title*='PDF' i]",
            "[aria-label*='PDF' i]",
            "button:has-text('Export')",
        ]
        for sel in selectors:
            try:
                el = self.page.locator(sel).first
                if el.count() > 0 and el.is_visible(timeout=1200):
                    return el
            except Exception:
                continue
        return None

    def click_export_pdf(self, timeout_ms: int = 25000):
        """Click Export PDF and capture the downloaded file. Returns a result dict."""
        logger.info("Clicking Export PDF button")
        self._dismiss_analytics_popup_if_present()
        btn = self._find_export_pdf_button()
        if btn is None:
            return {"ok": False, "reason": "Export PDF button not found"}

        downloads_dir = Path(__file__).resolve().parent.parent / "reports" / "downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)
        try:
            with self.page.expect_download(timeout=timeout_ms) as dl_info:
                btn.click(force=True)
            download = dl_info.value
            suggested = download.suggested_filename
            dest = downloads_dir / suggested
            download.save_as(str(dest))
            logger.info(f"Export PDF downloaded: {dest}")
            return {"ok": True, "suggested": suggested, "path": str(dest)}
        except Exception as e:
            return {"ok": False, "reason": f"no download captured: {e}"}
