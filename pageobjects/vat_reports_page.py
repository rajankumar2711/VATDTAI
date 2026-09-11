import logging
import re
from datetime import date
from pathlib import Path
from pageobjects.base_page import BasePage

logger = logging.getLogger(__name__)


class VatReportsPage(BasePage):
    """Page object for Global Insights And Data Enrichment For e-Invoicing Reports module."""

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

        # Confirmed against QA DOM (2026-08-24). The Reports "Generate Report" form lives in
        # the MAIN document (NOT a tab-pane). All controls below are anchored to the reports
        # "card" = nearest ancestor of #vatdtai_reports_select that also holds Generate. The
        # form's <select>/<input> elements are driven via getElementById in JS (see the
        # evaluate() calls below), so no Python-side selectors are kept for them.
        self.reports_card = (
            "xpath=//select[@id='vatdtai_reports_select']"
            "/ancestor::*[.//button[normalize-space()='Generate']][1]"
        )
        # Country combobox is display-only (disabled, fixed to client country); Entity is the
        # enabled multiselect combobox that opens a .dropdown-menu of entities.
        self.input_country = self.reports_card + "//input[contains(@class,'textinput-group__textinput') and @disabled]"
        self.input_entity = self.reports_card + "//input[contains(@class,'textinput-group__textinput') and not(@disabled)]"
        # The Entity dropdown opens via its toggle anchor (Country's toggle is '.disabled').
        self.entity_toggle = self.reports_card + "//a[contains(@class,'dropdown-toggle') and not(contains(@class,'disabled'))]"
        self.btn_generate = self.reports_card + "//button[normalize-space()='Generate']"

        # The generated report opens in a NEW WINDOW/TAB (a new Page in the same context),
        # rendered from a generic, report-type-agnostic template. Confirmed against QA for
        # Invoice Status + Reconciliation; Submission uses the same template.
        self.report_window = None
        self.rw_container = "div.vatdtai-report-window"
        self.rw_title = "h1.vatdtai-report-title"
        self.rw_table = "table.vatdtai-report-table"
        self.rw_rows = "table.vatdtai-report-table tbody tr"
        # JSON-format reports (e.g. Submission Report) render a <pre> JSON view instead of a table.
        self.rw_json = "pre.vatdtai-report-json-view, .vatdtai-report-json-wrap"
        self.rw_export_btn = "#vatdtai-report-export"
        self.rw_close_btn = "#vatdtai-report-close"

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

    def _click_reports_tab(self) -> bool:
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
        return bool(clicked)

    def navigate_to_reports_module(self):
        """Open Reports tab from Global Insights And Data Enrichment For e-Invoicing left navigation. Retries the tab click when the
        report form/options do not load (navigation can land on a redirect page first).

        A previously generated report keeps the Generate button disabled until it is closed,
        so any open report window is closed first before (re)opening the module. The
        reports_page fixture is recreated per scenario in the shared session, so a window
        opened by a PREVIOUS test is not tracked by self.report_window; we therefore sweep the
        whole browser context and close any report window gracefully."""
        logger.info("Navigating to Reports module")
        closed = self._close_open_report_windows()
        if closed:
            logger.info(f"Closed {closed} leftover report window(s) before entering the Reports module")
        clicked = False
        for attempt in range(3):
            self._dismiss_analytics_popup_if_present()
            clicked = self._click_reports_tab() or clicked
            self.page.wait_for_timeout(2000)
            self._dismiss_analytics_popup_if_present()
            if self._wait_for_report_options(timeout_ms=8000):
                break
            logger.debug(f"navigate_to_reports_module: report options not ready (attempt {attempt + 1})")
        # Clear volatile criteria leaked from a previous scenario (shared session) so Generate
        # starts disabled until the current scenario supplies its own inputs.
        self._reset_report_form()
        logger.info(f"Reports tab click status: {clicked}")
        return bool(clicked)

    def _reset_report_form(self):
        """Reset the volatile Generate-Report inputs (date fields + Submission platform) to
        empty on module entry. The Option-B shared session reuses one browser session across
        scenarios, so criteria committed by a previous scenario leak into the next and can leave
        Generate enabled when a negative-state scenario expects it disabled. Dates are a required
        field for every report, so clearing them guarantees Generate starts disabled until the
        current scenario provides its own criteria. Report type and entity are left untouched so
        the default-page inspection steps still see rendered fields/values."""
        try:
            self.page.evaluate("""() => {
                const fire = (el, types) => {
                    if (!el) return;
                    types.forEach(t => el.dispatchEvent(new Event(t, {bubbles: true})));
                    if (window.$) window.$(el).trigger('change');
                };
                for (const id of ['vatdtai_reports_date', 'vatdtai_reports_date_from', 'vatdtai_reports_date_to']) {
                    const el = document.getElementById(id);
                    if (el) { el.value = ''; fire(el, ['input', 'change']); }
                }
                const plat = document.getElementById('vatdtai_platform_select');
                if (plat && plat.options.length) { plat.selectedIndex = 0; fire(plat, ['change']); }
            }""")
            self.page.wait_for_timeout(300)
        except Exception as e:
            logger.debug(f"_reset_report_form failed: {e}")

    def _wait_for_report_options(self, timeout_ms: int = 12000) -> bool:
        """Wait until the Select Report dropdown has real options (not just the placeholder).
        The reports form/options load asynchronously after the tab is opened."""
        elapsed = 0
        while elapsed < timeout_ms:
            try:
                count = self.page.evaluate("""() => {
                    const sel = document.getElementById('vatdtai_reports_select');
                    if (!sel) return 0;
                    return Array.from(sel.options).filter(o => o.value && o.value.trim()).length;
                }""")
                if count and count > 0:
                    return True
            except Exception:
                pass
            self.page.wait_for_timeout(500)
            elapsed += 500
        return False

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
        self._wait_for_report_options()
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
            // Reset the Submission Platform to its placeholder on every report-type change so a
            // platform selected in a prior scenario (shared session) does not leak in and enable
            // Generate before a platform is explicitly chosen for this report.
            const plat = document.getElementById('vatdtai_platform_select');
            if (plat && plat.options.length) {
                plat.selectedIndex = 0;
                plat.dispatchEvent(new Event('change', {bubbles: true}));
                if (window.$) window.$(plat).trigger('change');
            }
            return {ok:true, selected:target.text, value:target.value};
        }""", {"name": report_name, "allowFallback": allow_fallback})
        logger.info(f"Report selection result: {result}")
        return result

    def provide_valid_filter_criteria(self, date_from: str = "01/01/2025", date_to: str = "10/10/2026"):
        """Populate valid report filters (assumes a report type is already selected).
        Commits the Entity multiselect and applies dates (range with single-date fallback) so
        Generate becomes enabled. Country is fixed to the client country and needs no input.
        If the Submission Platform field is required and unset, defaults it to GTES."""
        # Submission Report needs a platform before Generate can enable.
        info = self._submission_platform_select()
        if info.get("found") and info.get("visible") and not (info.get("value") or "").strip():
            self.select_submission_platform("GTES")
        self.select_entity("All")
        self._apply_dates(date_from, date_to)
        self.page.wait_for_timeout(500)
        logger.info(f"Report filter criteria populated: {self._generate_button_state()}")

    def _generate_button_state(self):
        # The form lives in the main document; anchor on the reports card = nearest
        # ancestor of #vatdtai_reports_select that also holds the Generate button.
        return self.page.evaluate("""() => {
            const norm = v => (v || '').replace(/\\s+/g, ' ').trim();
            const rep = document.getElementById('vatdtai_reports_select');
            if (!rep) return {found:false};
            let card = rep;
            while (card && card.parentElement) {
                card = card.parentElement;
                if (Array.from(card.querySelectorAll('button')).some(b => norm(b.innerText) === 'Generate')) break;
            }
            if (!card) return {found:false};
            const btn = Array.from(card.querySelectorAll('button')).find(b => norm(b.innerText) === 'Generate');
            if (!btn) return {found:false};
            const combos = Array.from(card.querySelectorAll('input.textinput-group__textinput'));
            return {
                found: true,
                disabled: !!btn.disabled,
                text: norm(btn.innerText),
                reportValue: rep.value || '',
                date: (document.getElementById('vatdtai_reports_date') || {}).value || '',
                dateFrom: (document.getElementById('vatdtai_reports_date_from') || {}).value || '',
                dateTo: (document.getElementById('vatdtai_reports_date_to') || {}).value || '',
                countryPreview: combos[0] ? (combos[0].getAttribute('data-title') || combos[0].value || '').trim() : '',
                entityPreview: combos[1] ? (combos[1].getAttribute('data-title') || combos[1].value || '').trim() : ''
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

    def click_generate_report(self, wait_ms: int = 30000):
        """Click Generate and capture the report WINDOW.

        The report opens in a new window/tab (a new Page in the same context). We capture it
        via expect_page and wait past the 'Generating report...' placeholder until the report
        body renders. Falls back to same-page/iframe behavior if no new window appears.
        Returns the report Page (or None when the report stayed inline)."""
        logger.info("Clicking Generate button")
        if not self.wait_for_generate_enabled(timeout_ms=15000):
            state = self._generate_button_state()
            raise AssertionError(f"Generate button is still disabled after valid filters: {state}")

        btn = self.page.locator(self.btn_generate).first
        self.report_window = None
        try:
            with self.page.context.expect_page(timeout=8000) as new_page_info:
                if btn.count() > 0 and btn.is_visible():
                    btn.click()
                else:
                    self.page.locator(self.btn_generate).first.click(force=True)
            report_page = new_page_info.value
            report_page.wait_for_load_state("load", timeout=15000)
            # Wait past the 'Generating report...' placeholder until real content renders.
            try:
                report_page.wait_for_selector(
                    f"{self.rw_table}, {self.rw_json}", timeout=wait_ms)
            except Exception:
                logger.warning("Report window content did not render before timeout")
            report_page.wait_for_timeout(800)
            try:
                report_page.bring_to_front()
            except Exception:
                pass
            self.report_window = report_page
            self.maximize_report_window()
            logger.info(f"Report window captured: title='{report_page.title()}'")
        except Exception:
            logger.info("No new report window detected; using inline/iframe fallback")
            self.page.wait_for_timeout(3000)
        return self.report_window

    def maximize_report_window(self) -> bool:
        """Maximize the report pop-up window so its full content is visible. Uses the Chrome
        DevTools Protocol to maximize the OS window, with a window.resizeTo fallback."""
        if not self._report_window_open():
            return False
        win = self.report_window
        try:
            win.bring_to_front()
        except Exception:
            pass
        maximized = False
        try:
            session = self.page.context.new_cdp_session(win)
            win_info = session.send("Browser.getWindowForTarget")
            window_id = win_info["windowId"]
            # Reset to 'normal' first so a maximize request always registers.
            try:
                session.send("Browser.setWindowBounds",
                             {"windowId": window_id, "bounds": {"windowState": "normal"}})
            except Exception:
                pass
            session.send("Browser.setWindowBounds",
                         {"windowId": window_id, "bounds": {"windowState": "maximized"}})
            maximized = True
        except Exception as e:
            logger.debug(f"maximize_report_window: CDP maximize failed ({e}); trying resizeTo")
        if not maximized:
            try:
                win.evaluate("""() => {
                    try {
                        window.moveTo(0, 0);
                        window.resizeTo(screen.availWidth, screen.availHeight);
                    } catch (e) {}
                }""")
                maximized = True
            except Exception:
                pass
        try:
            win.wait_for_timeout(300)
        except Exception:
            pass
        logger.info(f"Report window maximized: {maximized}")
        return maximized

    def scroll_report(self) -> dict:
        """Scroll the generated report vertically and horizontally to verify scroll support.
        Works for tabular reports (table.vatdtai-report-table) and the JSON view
        (pre.vatdtai-report-json-view). Returns whether the scroll container actually moved."""
        pg = self._active_report_page()
        try:
            result = pg.evaluate(r"""() => {
                const sels = [
                    'pre.vatdtai-report-json-view',
                    '.vatdtai-report-json-wrap',
                    'table.vatdtai-report-table',
                    '.vatdtai-report-table',
                    'div.vatdtai-report-window'
                ];
                let el = null;
                for (const s of sels) {
                    const cand = document.querySelector(s);
                    if (cand && (cand.scrollHeight > cand.clientHeight + 2 ||
                                 cand.scrollWidth > cand.clientWidth + 2)) { el = cand; break; }
                }
                if (!el) el = document.scrollingElement || document.documentElement;
                if (!el) return {found: false};
                const canV = el.scrollHeight > el.clientHeight + 2;
                const canH = el.scrollWidth > el.clientWidth + 2;
                const startTop = el.scrollTop, startLeft = el.scrollLeft;
                el.scrollTop = el.scrollHeight;
                el.scrollLeft = el.scrollWidth;
                const afterTop = el.scrollTop, afterLeft = el.scrollLeft;
                const movedV = afterTop > startTop;
                const movedH = afterLeft > startLeft;
                // Return to the top so the report is left in a clean state.
                el.scrollTop = 0; el.scrollLeft = 0;
                const tag = el.tagName.toLowerCase() +
                    (el.className ? '.' + String(el.className).trim().split(/\s+/)[0] : '');
                return {found: true, target: tag,
                        canScrollVertical: canV, canScrollHorizontal: canH,
                        movedVertical: movedV, movedHorizontal: movedH};
            }""")
            logger.info(f"scroll_report -> {result}")
            return result or {"found": False}
        except Exception as e:
            logger.debug(f"scroll_report failed: {e}")
            return {"found": False, "error": str(e)}

    def _report_window_open(self) -> bool:
        try:
            return bool(self.report_window) and not self.report_window.is_closed()
        except Exception:
            return False

    def _is_report_page(self, pg) -> bool:
        try:
            return pg.locator(f"{self.rw_container}, {self.rw_table}, {self.rw_json}").first.count() > 0
        except Exception:
            return False

    def _close_report_window_gracefully(self, pg) -> bool:
        """Dismiss a single report window via its in-window Close control so the app notifies
        the opener and re-enables Generate. Force-closes only if the app leaves it open."""
        graceful = False
        try:
            pg.bring_to_front()
        except Exception:
            pass
        try:
            btn = pg.locator(self.rw_close_btn).first
            if btn.count() > 0 and btn.is_visible(timeout=1500):
                btn.click()
                waited = 0
                while waited < 6000:
                    try:
                        if pg.is_closed():
                            graceful = True
                            break
                    except Exception:
                        graceful = True
                        break
                    pg.wait_for_timeout(250)
                    waited += 250
            else:
                logger.debug("_close_report_window_gracefully: Close button not found/visible")
        except Exception as e:
            logger.debug(f"_close_report_window_gracefully: Close click failed: {e}")
        try:
            if not pg.is_closed():
                logger.warning("Report window still open after Close click; force-closing")
                pg.close()
        except Exception:
            pass
        return graceful

    def _close_open_report_windows(self) -> int:
        """Gracefully close ANY report window open in the shared browser context, regardless
        of whether this page-object instance created it. Returns the number closed.

        Essential for the shared session: reports_page is recreated per scenario, so a report
        window from a previous test is not referenced by self.report_window but still keeps the
        opener's Generate button disabled until it is closed via its own Close control."""
        closed = 0
        try:
            for pg in list(self.page.context.pages):
                if pg == self.page or pg.is_closed():
                    continue
                if not self._is_report_page(pg):
                    continue
                self._close_report_window_gracefully(pg)
                closed += 1
        except Exception as e:
            logger.debug(f"_close_open_report_windows failed: {e}")
        self.report_window = None
        if closed:
            try:
                self.page.bring_to_front()
                self.page.wait_for_timeout(700)
            except Exception:
                pass
        return closed

    def _active_report_page(self):
        """Return the report window when open, else the main page (inline/iframe fallback)."""
        return self.report_window if self._report_window_open() else self.page

    # Report types that require the Submission Platform field (defaults to GTES).
    PLATFORM_REQUIRED_TYPES = {"submission report"}

    def _apply_dates(self, date_from: str = None, date_to: str = None, single_date: str = None):
        """Apply the report date criteria. All three report types use a DATE RANGE
        (#vatdtai_reports_date_from / _to); only fall back to the single Date field when an
        explicit single_date is requested and no range is given. (A blind single-date fallback
        was removed: it masked the real 'report window still open' Generate lock and polluted
        the single-date field, leaving the range empty and Generate disabled.)"""
        if single_date and not (date_from or date_to):
            self.set_single_date(single_date)
            return
        self.set_date_range(date_from or "", date_to or "")
        self.wait_for_generate_enabled(timeout_ms=3000)

    def generate_report(self, report_type: str, platform: str = None,
                        date_from: str = None, date_to: str = None,
                        single_date: str = None, entity: str = "All",
                        allow_fallback: bool = False, wait_ms: int = 30000):
        """Parameterised, reusable generate flow for ALL report types.

        Steps: navigate -> select report type -> (platform if required) -> commit entity ->
        apply dates (range with single-date fallback) -> Generate + capture the report window.
        Returns the report Page (or None if the report rendered inline)."""
        self.navigate_to_reports_module()
        sel = self.select_report_type(report_type, allow_fallback=allow_fallback)
        assert sel.get("ok"), f"Could not select report type '{report_type}': {sel}"

        rt = (report_type or "").strip().lower()
        if rt in self.PLATFORM_REQUIRED_TYPES and not platform:
            platform = "GTES"
        if platform:
            assert self.select_submission_platform(platform), \
                f"Could not select Submission Platform '{platform}'"

        assert self.select_entity(entity), f"Could not commit Entity '{entity}'"
        self._apply_dates(date_from, date_to, single_date)
        return self.click_generate_report(wait_ms=wait_ms)

    def _report_frame(self):
        """Return the Streamlit report iframe's Frame once it has real content, else None.
        The generated report renders inside iframe#smartstreamlitViewer."""
        try:
            for fr in self.page.frames:
                if fr.name == "smartstreamlitViewer" and fr.url and fr.url != "about:blank":
                    return fr
        except Exception:
            pass
        return None

    def is_report_displayed(self, expected_report_text: str = ""):
        """
        Verify report output appears in the report window (preferred) or an inline container.
        """
        # Preferred: the report window rendered the generic report template.
        if self._report_window_open():
            try:
                el = self.report_window.locator(f"{self.rw_container}, {self.rw_table}, {self.rw_json}").first
                if el.count() > 0 and el.is_visible(timeout=2000):
                    return True
            except Exception:
                pass

        self.page.wait_for_timeout(2000)

        # A secondary page counts as "displayed" only when it actually holds the report
        # template. Relying on page count alone false-positives after a report is closed.
        try:
            for pg in self.page.context.pages:
                if pg == self.page or pg.is_closed():
                    continue
                try:
                    if pg.locator(f"{self.rw_container}, {self.rw_table}, {self.rw_json}").first.count() > 0:
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # Inline fallback (used only if the report ever renders in-page instead of a new
        # window): require a genuinely rendered report, not merely the always-present
        # #smartstreamlitViewer iframe or the static 'Generate Report' page text.
        frame = self._report_frame()
        if frame is not None:
            try:
                if (frame.inner_text("body") or "").strip():
                    return True
            except Exception:
                pass

        container_locators = [
            "div.modal-dialog:visible table",
            "[role='dialog']:visible table",
            f"{self.rw_container}:visible",
            ".report-viewer:visible table",
            ".report-container:visible table",
            ".tabulator:visible",
        ]
        for loc in container_locators:
            try:
                el = self.page.locator(loc).first
                if el.count() > 0 and el.is_visible(timeout=1000):
                    return True
            except Exception:
                continue

        return False

    def get_report_column_headers(self):
        """Return column header labels from the report table.
        Prefers the report window; falls back to the #smartstreamlitViewer iframe / inline."""
        header_js = """() => {
            const norm = v => (v || '').replace(/\\s+/g, ' ').trim();
            return Array.from(document.querySelectorAll(
                'table.vatdtai-report-table thead th, table thead th, table th, thead td, [role="columnheader"], .tabulator .tabulator-col-title'
            )).map(el => norm(el.innerText || el.textContent)).filter(Boolean);
        }"""
        if self._report_window_open():
            try:
                headers = self.report_window.evaluate(header_js)
                if headers:
                    return headers
            except Exception:
                pass
        frame = self._report_frame()
        if frame is not None:
            try:
                headers = frame.evaluate(header_js)
                if headers:
                    return headers
            except Exception:
                pass
        try:
            return self.page.evaluate("""() => {
                const norm = v => (v || '').replace(/\\s+/g, ' ').trim();
                const scopes = [
                    document.querySelector('div.modal-dialog'),
                    document.querySelector("[role='dialog']"),
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

    def click_export_pdf(self, timeout_ms: int = 25000):
        """Export the generated report as PDF and capture the downloaded file. Exports live in
        the report window's Export menu ([data-export='pdf']); delegates to the generic
        export_report so the smoke scenario uses the same window-aware path as every other
        export. Returns {ok, suggested, path} or {ok:False, reason}."""
        logger.info("Exporting report as PDF via the report window Export menu")
        return self.export_report("pdf", timeout_ms=timeout_ms)

    # ==========================================
    # GENERATE PAGE FIELD INSPECTION
    # ==========================================

    def get_generate_report_header(self):
        """Return the 'Generate Report' section heading text (empty if absent).
        The form is in the main document, so match by text rather than a tab-pane."""
        for sel in [self.generate_report_heading,
                    "h1:has-text('Generate Report'), h2:has-text('Generate Report'), "
                    "h3:has-text('Generate Report'), h4:has-text('Generate Report')"]:
            try:
                el = self.page.locator(sel).first
                if el.count() > 0 and el.is_visible(timeout=1000):
                    return el.inner_text().strip()
            except Exception:
                continue
        return ""

    def get_date_field_placeholders(self):
        """Return placeholder attributes of the report date input(s)."""
        try:
            return self.page.evaluate("""() => {
                const ids = ['vatdtai_reports_date', 'vatdtai_reports_date_from', 'vatdtai_reports_date_to'];
                const out = [];
                for (const id of ids) {
                    const el = document.getElementById(id);
                    if (el) out.push((el.getAttribute('placeholder') || '').trim());
                }
                return out;
            }""")
        except Exception:
            return []

    def _report_pane_input_value(self, index: int):
        """Return the trimmed display value of the Country (0) / Entity (1) combobox.
        These Carbon typeaheads carry the display value in data-title (the disabled Country
        input has no usable .value), so prefer that."""
        try:
            loc = self.input_country if index == 0 else self.input_entity
            field = self.page.locator(loc).first
            if field.count() > 0:
                return (field.get_attribute("data-title") or field.input_value() or "").strip()
        except Exception:
            pass
        return ""

    def get_country_field_value(self):
        return self._report_pane_input_value(0)

    def get_entity_field_value(self):
        return self._report_pane_input_value(1)

    def _entity_committed(self) -> bool:
        """True once the Entity multiselect has committed. The committed state is exactly what
        the Generate button reads: within the reports card (nearest ancestor of the report
        <select> that also holds Generate) the Entity combobox is the 2nd textinput
        (combos[0]=Country, combos[1]=Entity). Committed => its display leaves the 'All'
        placeholder (e.g. 'N of N selected'). Scanning the whole document is unreliable because
        an unrelated Client/Country field would be matched instead."""
        try:
            return bool(self.page.evaluate("""() => {
                const norm = v => (v || '').replace(/\\s+/g, ' ').trim();
                const rep = document.getElementById('vatdtai_reports_select');
                if (!rep) return false;
                let card = rep;
                while (card && card.parentElement) {
                    card = card.parentElement;
                    if (Array.from(card.querySelectorAll('button'))
                            .some(b => norm(b.innerText) === 'Generate')) break;
                }
                if (!card) return false;
                const combos = Array.from(
                    card.querySelectorAll('input.textinput-group__textinput'));
                const entity = combos[1];
                if (!entity) return false;
                const title = norm(entity.getAttribute('data-title') || entity.value);
                if (!title) return false;
                return title.toLowerCase() !== 'all';
            }"""))
        except Exception:
            return False

    def _open_entity_menu(self) -> bool:
        """Open the Entity multiselect dropdown; return True once its menu is visible."""
        field = self.page.locator(self.input_entity).first
        if field.count() == 0 or not field.is_visible(timeout=2000):
            return False
        toggle = self.page.locator(self.entity_toggle).first
        if toggle.count() > 0 and toggle.is_visible():
            toggle.click()
        else:
            field.click()
        try:
            self.page.wait_for_selector(
                "ul.dropdown-menu:visible li, .dropdown-menu:visible li",
                state="visible", timeout=4000)
            return True
        except Exception:
            return False

    def select_entity(self, value: str = "All"):
        """Commit the Entity value via its dropdown. Entity is a multiselect whose default
        display 'All' is NOT registered until the dropdown is opened and the option clicked
        (verified against QA: after selecting 'All' the field reads 'N of N selected' and the
        hidden native <select> gets a value, which is what enables Generate).

        On repeated generations (shared session) the widget retains its internal checkbox
        state while the display resets to 'All', so a single 'All' click can toggle the
        selection OFF. We therefore click 'All' repeatedly within the open menu until the
        hidden native <select> actually commits, reopening the menu if it closes."""
        menu_sel = "ul.dropdown-menu:visible li, .dropdown-menu:visible li"
        for attempt in range(4):
            try:
                if not self._open_entity_menu():
                    logger.debug(f"select_entity: menu did not open (attempt {attempt + 1})")
                    self.page.keyboard.press("Escape")
                    self.page.wait_for_timeout(400)
                    continue
                # Click the option up to 3 times within the open menu; a multiselect toggle
                # may need a second click to land on the fully-selected state.
                for click_i in range(3):
                    if self.page.locator(menu_sel).count() == 0:
                        if not self._open_entity_menu():
                            break
                    option = self.page.locator(menu_sel).filter(
                        has_text=re.compile(rf"^\s*{re.escape(value)}\s*$")).first
                    if option.count() == 0:
                        logger.debug(f"select_entity: option '{value}' not found in open menu")
                        break
                    option.click()
                    self.page.wait_for_timeout(700)
                    if self._entity_committed():
                        field = self.page.locator(self.input_entity).first
                        committed = field.get_attribute("data-title") or field.input_value()
                        logger.info(f"select_entity('{value}') -> committed display '{committed}'")
                        try:
                            self.page.keyboard.press("Escape")
                        except Exception:
                            pass
                        return True
                logger.debug(f"select_entity: commit not registered (attempt {attempt + 1}); retrying")
                try:
                    self.page.keyboard.press("Escape")
                    self.page.wait_for_timeout(300)
                except Exception:
                    pass
            except Exception as e:
                logger.debug(f"select_entity failed (attempt {attempt + 1}): {e}")
        return self._entity_committed()

    def set_single_date(self, value: str):
        """Populate the single Date field (used by report types that require Date, not Range)."""
        iso = self._normalize_iso(value)
        result = self.page.evaluate("""(val) => {
            const el = document.getElementById('vatdtai_reports_date');
            if (!el) return {ok:false};
            el.value = val;
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
            return {ok:true, value: el.value};
        }""", iso)
        self.page.wait_for_timeout(600)
        logger.info(f"set_single_date({iso}) -> {result}")
        return result

    def _normalize_iso(self, value: str) -> str:
        """Accept mm/dd/yyyy or yyyy-mm-dd and return yyyy-mm-dd for date input .value."""
        v = (value or "").strip()
        if not v:
            return ""
        if "/" in v:
            m, d, y = v.split("/")
            return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
        return v

    def set_date_range(self, date_from: str, date_to: str):
        """Populate the report date range. Uses from/to inputs when present, else the
        single date field. Values may be mm/dd/yyyy or yyyy-mm-dd."""
        iso_from = self._normalize_iso(date_from)
        iso_to = self._normalize_iso(date_to)
        result = self.page.evaluate("""(args) => {
            const fire = (el, val) => {
                if (!el) return false;
                el.value = val;
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
                return true;
            };
            const single = document.getElementById('vatdtai_reports_date');
            const from = document.getElementById('vatdtai_reports_date_from');
            const to = document.getElementById('vatdtai_reports_date_to');
            const used = {};
            if (from || to) {
                used.from = fire(from, args.from);
                used.to = fire(to, args.to);
            } else if (single) {
                used.single = fire(single, args.from);
            }
            return {
                used,
                single: single ? single.value : '',
                from: from ? from.value : '',
                to: to ? to.value : ''
            };
        }""", {"from": iso_from, "to": iso_to})
        self.page.wait_for_timeout(700)
        logger.info(f"set_date_range({iso_from}..{iso_to}) -> {result}")
        return result

    def apply_incomplete_criteria(self, condition: str):
        """Populate criteria that must leave Generate disabled, per a named condition.
        Recognized: 'start date is missing', 'end date is missing', 'date range is invalid',
        'platform is not selected'."""
        cond = (condition or "").strip().lower()
        self.select_entity("All")
        if "start date is missing" in cond:
            self.set_date_range("", "10/10/2026")
        elif "end date is missing" in cond:
            self.set_date_range("01/01/2025", "")
        elif "date range is invalid" in cond:
            # end earlier than start
            self.set_date_range("10/10/2026", "01/01/2025")
        elif "platform is not selected" in cond:
            # leave Submission Platform empty but fill the rest
            self.set_date_range("01/01/2025", "10/10/2026")
        else:
            logger.warning(f"apply_incomplete_criteria: unrecognized condition '{condition}'")
        self.page.wait_for_timeout(600)

    def is_generate_enabled(self) -> bool:
        state = self._generate_button_state()
        return bool(state.get("found") and not state.get("disabled"))

    def is_generate_disabled(self) -> bool:
        state = self._generate_button_state()
        return bool(state.get("found") and state.get("disabled"))

    # ==========================================
    # SUBMISSION PLATFORM (conditional field)
    # ==========================================

    def _submission_platform_select(self):
        # Confirmed id (QA): #vatdtai_platform_select (options GTES / Pagero), hidden until
        # the Submission Report type is selected.
        return self.page.evaluate("""() => {
            const target = document.getElementById('vatdtai_platform_select');
            if (!target) return {found:false, visible:false, options:[]};
            const style = window.getComputedStyle(target);
            const visible = style.display !== 'none' && style.visibility !== 'hidden' && target.offsetParent !== null;
            const options = Array.from(target.options).map(o => (o.text || '').trim()).filter(Boolean);
            return {found:true, visible, options, value: target.value || '', id: target.id || ''};
        }""")

    def is_submission_platform_visible(self) -> bool:
        info = self._submission_platform_select()
        return bool(info.get("found") and info.get("visible"))

    def get_submission_platform_options(self):
        info = self._submission_platform_select()
        return [o for o in info.get("options", []) if o.lower() != "select platform" and "select" not in o.lower()]

    def select_submission_platform(self, platform: str) -> bool:
        result = self.page.evaluate("""(args) => {
            const norm = v => (v || '').replace(/\\s+/g, ' ').trim().toLowerCase();
            const target = document.getElementById('vatdtai_platform_select');
            if (!target) return {ok:false, reason:'platform select not found'};
            const opt = Array.from(target.options).find(o => norm(o.text) === norm(args.platform))
                || Array.from(target.options).find(o => norm(o.text).includes(norm(args.platform)));
            if (!opt) return {ok:false, reason:'platform option not found', available: Array.from(target.options).map(o => o.text.trim())};
            target.value = opt.value;
            target.dispatchEvent(new Event('change', {bubbles: true}));
            if (window.$) window.$(target).trigger('change');
            return {ok:true, selected: opt.text.trim()};
        }""", {"platform": platform})
        self.page.wait_for_timeout(600)
        logger.info(f"select_submission_platform({platform}) -> {result}")
        return bool(result.get("ok"))

    # ==========================================
    # GENERATED REPORT METADATA + CLOSE
    # ==========================================

    def _report_scope_text(self) -> str:
        """Return the text of the most relevant report container. Prefers the report window,
        then the #smartstreamlitViewer iframe, then an inline container."""
        if self._report_window_open():
            try:
                txt = (self.report_window.inner_text("body") or "").strip()
                if txt:
                    return txt
            except Exception:
                pass
        frame = self._report_frame()
        if frame is not None:
            try:
                txt = (frame.inner_text("body") or "").strip()
                if txt:
                    return txt
            except Exception:
                pass
        for loc in ["div.modal-dialog", "[role='dialog']", ".report-viewer", ".report-container"]:
            try:
                el = self.page.locator(loc).first
                if el.count() > 0 and el.is_visible(timeout=1000):
                    return el.inner_text()
            except Exception:
                continue
        try:
            return self.page.inner_text("body")
        except Exception:
            return ""

    def get_report_metadata(self):
        """Parse Country / Entity / Date Range / Generated On + title from the report view."""
        text = self._report_scope_text()

        def grab(label):
            # Values may share a line, e.g. "Country: BE | Entity: All"; stop at a '|'
            # separator or the next known label so each field is isolated.
            m = re.search(rf"{label}\s*[:\-]\s*(.+)", text, re.I)
            if not m:
                return ""
            val = m.group(1).splitlines()[0]
            val = re.split(r"\s*\|\s*|\s{2,}(?=[A-Z][a-z]+\s*:)", val)[0]
            return val.strip()

        title = ""
        if self._report_window_open():
            try:
                el = self.report_window.locator(self.rw_title).first
                if el.count() > 0:
                    title = el.inner_text().strip()
            except Exception:
                pass
        if not title:
            try:
                for loc in ["div.modal-dialog h1, div.modal-dialog h2, div.modal-dialog h3, div.modal-dialog h4",
                            "[role='dialog'] h1, [role='dialog'] h2, [role='dialog'] h3, [role='dialog'] h4"]:
                    el = self.page.locator(loc).first
                    if el.count() > 0 and el.is_visible(timeout=800):
                        title = el.inner_text().strip()
                        break
            except Exception:
                pass

        return {
            "title": title,
            "country": grab("Country"),
            "entity": grab("Entity"),
            "platform": grab("Platform"),
            "date_range": grab("Date Range"),
            "generated_on": grab("Generated On"),
            "raw": text[:2000],
        }

    def get_report_output_format(self) -> str:
        """Return 'json' when the report window renders a JSON view (Submission Report),
        'table' when it renders a data table, else '' when neither is present yet."""
        pg = self._active_report_page()
        try:
            if pg.locator(self.rw_json).first.count() > 0:
                return "json"
        except Exception:
            pass
        try:
            if pg.locator(self.rw_table).first.count() > 0:
                return "table"
        except Exception:
            pass
        return ""

    def get_report_json_fields(self):
        """Return the top-level field names of a JSON-format report (Submission Report),
        as the union of keys across the first records. Empty list for tabular reports or
        when no JSON view is present."""
        pg = self._active_report_page()
        try:
            return pg.evaluate("""() => {
                const el = document.querySelector('pre.vatdtai-report-json-view');
                if (!el) return [];
                let data;
                try { data = JSON.parse(el.innerText || el.textContent || ''); }
                catch (e) { return []; }
                const arr = Array.isArray(data) ? data : [data];
                const keys = [];
                for (const rec of arr.slice(0, 50)) {
                    if (rec && typeof rec === 'object' && !Array.isArray(rec)) {
                        for (const k of Object.keys(rec)) if (!keys.includes(k)) keys.push(k);
                    }
                }
                return keys;
            }""") or []
        except Exception:
            return []

    def get_report_record_count(self) -> int:
        """Return the number of report records: table body rows for tabular reports, or the
        count of top-level JSON objects for JSON reports (Submission Report)."""
        pg = self._active_report_page()
        try:
            rows = pg.locator(self.rw_rows)
            if rows.count() > 0:
                return rows.count()
        except Exception:
            pass
        try:
            return int(pg.evaluate("""() => {
                const el = document.querySelector('pre.vatdtai-report-json-view');
                if (!el) return 0;
                try {
                    const data = JSON.parse(el.innerText || el.textContent || '');
                    return Array.isArray(data) ? data.length : (data ? 1 : 0);
                } catch (e) { return 0; }
            }"""))
        except Exception:
            return 0

    def close_report(self, use_close_button: bool = True) -> bool:
        """Close the generated report GRACEFULLY and return focus to the Generate Report page.

        The application re-enables the opener's Generate button only when the report is
        dismissed via its own in-window Close control (#vatdtai-report-close): that click
        notifies the opener before the window unloads. Force-killing the window (page.close)
        skips that notification and leaves Generate permanently disabled, blocking the next
        generation. We therefore sweep the shared browser context and close every report
        window via its Close control (force-closing only as a last resort). This also catches
        windows opened by a previous scenario, since reports_page is recreated per test. Falls
        back to an inline modal Close / Escape when the report was rendered inline."""
        if self._report_window_open() or any(
                self._is_report_page(pg) for pg in list(self.page.context.pages)
                if pg != self.page and not pg.is_closed()):
            closed = self._close_open_report_windows()
            logger.info(f"close_report: closed {closed} report window(s) gracefully")
            return True

        self._dismiss_analytics_popup_if_present()
        selectors = [
            "div.modal-dialog button:has-text('Close')",
            "[role='dialog'] button:has-text('Close')",
            "div.modal-dialog button[aria-label='Close']",
            "[role='dialog'] button[aria-label='Close']",
            "div.modal-dialog button.close",
            "[role='dialog'] .close",
            "button:has-text('Close')",
        ]
        for sel in selectors:
            try:
                el = self.page.locator(sel).first
                if el.count() > 0 and el.is_visible(timeout=1200):
                    el.click(force=True)
                    self.page.wait_for_timeout(1200)
                    return True
            except Exception:
                continue
        # Fallback: press Escape
        try:
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(800)
            return True
        except Exception:
            return False

    # ==========================================
    # GENERIC EXPORT (Excel / PDF / CSV / XML)
    # ==========================================

    def _find_export_button(self, fmt: str):
        key = (fmt or "").strip().lower()
        aliases = {
            "excel": ["Excel", "XLSX", "Export Excel", "Export to Excel"],
            "pdf": ["PDF", "Export PDF", "Export to PDF"],
            "csv": ["CSV", "Export CSV", "Export to CSV"],
            "xml": ["XML", "Export XML", "Export to XML"],
            "json": ["JSON", "Export JSON", "Export to JSON"],
        }.get(key, [fmt])
        selectors = []
        for a in aliases:
            selectors += [
                f"button:has-text('{a}')",
                f"a:has-text('{a}')",
                f"button[title*='{a}' i]",
                f"a[title*='{a}' i]",
                f"[aria-label*='{a}' i]",
                f"li:has-text('{a}')",
            ]
        for sel in selectors:
            try:
                el = self.page.locator(sel).first
                if el.count() > 0 and el.is_visible(timeout=800):
                    return el
            except Exception:
                continue
        return None

    _EXPORT_FMT_MAP = {"excel": "xlsx", "xlsx": "xlsx", "pdf": "pdf", "csv": "csv", "xml": "xml", "json": "json"}

    def export_report(self, fmt: str, timeout_ms: int = 25000):
        """Trigger an export in the requested format and capture the download.
        In the report window the exports live behind the 'Export' menu button as
        [data-export="xlsx|pdf|csv|xml"] items. Returns {ok, suggested, path} or {ok:False}."""
        logger.info(f"Exporting report as {fmt}")
        data_fmt = self._EXPORT_FMT_MAP.get((fmt or "").strip().lower(), (fmt or "").strip().lower())
        downloads_dir = Path(__file__).resolve().parent.parent / "reports" / "downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)

        # Preferred path: the report window's Export menu. The export handler may fire the
        # download on the report window OR on the opener (main) page, so listen on all pages.
        if self._report_window_open():
            win = self.report_window
            captured = []

            def _on_download(d):
                captured.append(d)

            pages = list(self.page.context.pages)
            for pg in pages:
                pg.on("download", _on_download)
            try:
                menu_btn = win.locator(self.rw_export_btn).first
                menu_btn.click()
                try:
                    win.wait_for_selector(
                        f"#vatdtai-report-export-menu.is-open [data-export='{data_fmt}'], "
                        f"[data-export='{data_fmt}']:visible",
                        state="visible", timeout=5000)
                except Exception:
                    win.wait_for_timeout(500)
                item = win.locator(f"[data-export='{data_fmt}']").first
                if item.count() == 0:
                    return {"ok": False, "reason": f"export item '{data_fmt}' not found in report window"}
                item.click()
                # Poll for the download event on any page.
                waited = 0
                while not captured and waited < timeout_ms:
                    win.wait_for_timeout(250)
                    waited += 250
                if not captured:
                    return {"ok": False, "reason": f"no download captured for {fmt} in report window"}
                download = captured[0]
                suggested = download.suggested_filename
                dest = downloads_dir / suggested
                download.save_as(str(dest))
                logger.info(f"{fmt} export downloaded: {dest}")
                return {"ok": True, "suggested": suggested, "path": str(dest)}
            except Exception as e:
                return {"ok": False, "reason": f"no download captured for {fmt} in report window: {e}"}
            finally:
                for pg in pages:
                    try:
                        pg.remove_listener("download", _on_download)
                    except Exception:
                        pass

        # Fallback: inline export controls on the main page.
        self._dismiss_analytics_popup_if_present()
        btn = self._find_export_button(fmt)
        if btn is None:
            menu = self.page.locator("button:has-text('Export'), a:has-text('Export')").first
            try:
                if menu.count() > 0 and menu.is_visible(timeout=1000):
                    menu.click()
                    self.page.wait_for_timeout(600)
                    btn = self._find_export_button(fmt)
            except Exception:
                pass
        if btn is None:
            return {"ok": False, "reason": f"export control for '{fmt}' not found"}
        try:
            with self.page.expect_download(timeout=timeout_ms) as dl_info:
                btn.click(force=True)
            download = dl_info.value
            suggested = download.suggested_filename
            dest = downloads_dir / suggested
            download.save_as(str(dest))
            logger.info(f"{fmt} export downloaded: {dest}")
            return {"ok": True, "suggested": suggested, "path": str(dest)}
        except Exception as e:
            return {"ok": False, "reason": f"no download captured for {fmt}: {e}"}
