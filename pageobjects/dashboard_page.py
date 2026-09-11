"""Page Object for the VAT DTAI PowerBI Dashboard (UAT-only).

The dashboard is an embedded PowerBI report living in an iframe
(src ~ app.powerbi.com/reportEmbed). Playwright can read and drive that frame
even though it is cross-origin, so metrics are read from the frame's rendered
text and drill-through is performed via PowerBI's right-click context menu.
"""

import re
import time
import logging

from pageobjects.base_page import BasePage

logger = logging.getLogger(__name__)


class DashboardPage(BasePage):
    # The Dashboards tab inside the DTAI app shell (outside the PowerBI iframe).
    TAB_DASHBOARDS = "role=tab[name='Dashboards' i], .nav-link:has-text('Dashboards')"

    # PowerBI report iframe (embedded report).
    PBI_IFRAME = "iframe[src*='powerbi'], iframe[src*='reportEmbed']"

    # Named metric cards / visuals expected on the dashboard.
    EXPECTED_VISUALS = [
        "Total Invoices",
        "Success Rate",
        "Outbound (AR)/ Inbound (AP) Views",
        "Operational Pipeline View",
        "Schema / Mapping Readiness",
        "By Operational Status",
        "Outbound Invoices (AR)",
        "Inbound Invoices (AP)",
    ]

    # Actual PowerBI drill-through target pages (menu items are prefixed with a magnifier
    # emoji + bidi marks; we match on these substrings).
    DRILLTHROUGH_TARGETS = ["Invoice History", "Invoice Details", "Summary Details"]

    # Cards that expose drill-through (data-point visuals), matched by substring. The top
    # slicers/KPIs (Select Invoices, Country, Source System) are not drillable.
    DRILL_SOURCE_CARDS = [
        "Outbound (AR)/ Inbound (AP) Views",
        "Operational Pipeline View",
        "Schema / Mapping Readiness",
        "By Operational Status",
        "Outbound Invoices (AR)",
        "Inbound Invoices (AP)",
    ]

    # Cached per card across scenarios in a session: card -> {label, dp_index, targets}.
    _DRILL_POINTS = {}

    def __init__(self, get_page):
        super().__init__(get_page)

    # ------------------------------------------------------------------
    # Frame access
    # ------------------------------------------------------------------
    def _pbi_frame(self):
        """Return the Playwright Frame for the embedded PowerBI report, or None."""
        for fr in self.page.frames:
            url = (fr.url or "").lower()
            if "reportembed" in url or "app.powerbi" in url:
                return fr
        return None

    def open_dashboards_tab(self):
        """Ensure the Dashboards tab is active in the DTAI app shell."""
        try:
            tab = self.page.locator(self.TAB_DASHBOARDS).first
            if tab.count() > 0 and tab.is_visible():
                tab.click()
                self.page.wait_for_timeout(1500)
        except Exception as e:
            logger.debug(f"Dashboards tab click skipped: {e}")

    def wait_until_loaded(self, timeout_ms: int = 120000):
        """Wait for the PowerBI iframe to appear and its visuals to finish rendering."""
        self.page.wait_for_selector(self.PBI_IFRAME, timeout=timeout_ms)
        end = time.time() + timeout_ms / 1000
        while time.time() < end:
            fr = self._pbi_frame()
            if fr:
                try:
                    info = fr.evaluate(
                        """() => {
                            const vis = document.querySelectorAll('.visualContainer, visual-container');
                            const body = (document.body && document.body.innerText || '').toLowerCase();
                            return {count: vis.length, loading: body.includes('loading data')};
                        }"""
                    )
                    if info and info.get("count", 0) > 0 and not info.get("loading"):
                        self.page.wait_for_timeout(2500)
                        logger.info(f"[dashboard] PowerBI rendered: {info.get('count')} visuals")
                        return True
                except Exception:
                    pass
            self.page.wait_for_timeout(2000)
        logger.warning("[dashboard] PowerBI visuals did not confirm rendered within timeout")
        return False

    def is_powerbi_report_present(self) -> bool:
        return self.page.locator(self.PBI_IFRAME).count() > 0

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------
    def dashboard_text(self) -> str:
        fr = self._pbi_frame()
        if not fr:
            return ""
        try:
            return fr.inner_text("body")
        except Exception:
            return ""

    def visual_titles(self) -> list:
        """Titles/aria-labels of every rendered PowerBI visual."""
        fr = self._pbi_frame()
        if not fr:
            return []
        try:
            return fr.evaluate(
                """() => {
                    const norm = s => (s||'').replace(/\\s+/g,' ').trim();
                    const out = [];
                    document.querySelectorAll('.visualContainer, visual-container').forEach(v => {
                        const t = v.getAttribute('aria-label') || '';
                        const inner = norm(v.innerText).slice(0, 120);
                        out.push(norm(t) || inner);
                    });
                    return out.filter(Boolean);
                }"""
            )
        except Exception:
            return []

    def read_metrics(self) -> dict:
        """Parse the key KPI figures from the rendered dashboard text."""
        text = re.sub(r"\s+", " ", self.dashboard_text())
        metrics: dict = {}

        def find(pattern):
            m = re.search(pattern, text, re.I)
            return m.group(1).strip() if m else None

        metrics["total_invoices"] = find(r"Total Invoices\s*([0-9][0-9,\.]*)")
        metrics["success_rate"] = find(r"Success Rate\s*([0-9][0-9\.]*\s*%)")

        # The operational status breakdown must be read from the "By Operational Status"
        # visual only - words like "Ready" also appear in the Operational Pipeline visual,
        # so parsing the flat dashboard text double-counts.
        breakdown = self.status_breakdown()
        metrics["status_breakdown"] = breakdown
        metrics["status_review_required"] = breakdown.get("Review Required")
        metrics["status_ready"] = breakdown.get("Ready")
        metrics["status_error"] = breakdown.get("Error")
        return metrics

    def status_breakdown(self) -> dict:
        """Return {category: count} for the 'By Operational Status' visual, read from the
        data-point aria-labels inside that visual container (robust to any category set)."""
        fr = self._pbi_frame()
        if not fr:
            return {}
        try:
            data = fr.evaluate(
                """(title) => {
                    const norm = s => (s||'').replace(/\\s+/g,' ').trim();
                    const vs = Array.from(document.querySelectorAll('.visualContainer, visual-container'));
                    const target = vs.find(v => (norm(v.getAttribute('aria-label')||'') + ' ' + norm(v.innerText||''))
                        .toLowerCase().includes(title.toLowerCase()));
                    if (!target) return {found:false, aria:[], text:''};
                    const aria = Array.from(target.querySelectorAll('[aria-label]'))
                        .map(e => norm(e.getAttribute('aria-label'))).filter(Boolean);
                    return {found:true, aria: aria, text: norm(target.innerText)};
                }""",
                "By Operational Status",
            )
        except Exception as e:
            logger.warning(f"[dashboard] status_breakdown eval failed: {e}")
            return {}

        if not data or not data.get("found"):
            logger.warning("[dashboard] 'By Operational Status' visual not found for breakdown")
            return {}

        aria = data.get("aria", [])
        text = data.get("text", "")
        logger.info(f"[dashboard][diag] By Operational Status aria-labels: {aria}")
        breakdown: dict = {}

        # PowerBI exposes each column's value as a bare-integer aria-label (e.g. '14','5','1').
        values = [int(a.replace(",", "")) for a in aria if re.fullmatch(r"[0-9][0-9,]*", a.strip())]

        # Fallback: some builds embed "Category 14" pairs instead of bare numbers.
        if not values:
            for label in aria:
                m = re.search(r"([A-Za-z][A-Za-z /&\-]+?)\s*[:\.]?\s*([0-9][0-9,]*)\s*$", label.strip())
                if m and m.group(1).strip().lower() not in ("count", "total"):
                    breakdown[m.group(1).strip()] = int(m.group(2).replace(",", ""))
            if breakdown:
                logger.info(f"[dashboard][diag] parsed status breakdown: {breakdown}")
                return breakdown

        # Pair the values with known operational-status category names when present.
        known = ["Review Required", "Ready", "Error", "Submitted", "Processing",
                 "Rejected", "Accepted", "Failed", "Pending", "Cancelled", "Draft"]
        cats = [k for k in known if re.search(r"\b" + re.escape(k) + r"\b", text, re.I)]
        if cats and len(cats) == len(values):
            breakdown = {c: v for c, v in zip(cats, values)}
        else:
            breakdown = {f"status_{i + 1}": v for i, v in enumerate(values)}

        logger.info(f"[dashboard][diag] parsed status breakdown: {breakdown}")
        return breakdown

    # ------------------------------------------------------------------
    # Drill-through
    # ------------------------------------------------------------------
    def _visual_locator(self, visual_title: str):
        fr = self._pbi_frame()
        if not fr:
            return None
        return fr.locator(f".visualContainer:has-text(\"{visual_title}\")").first

    # Selectors for the PowerBI context menu / its items (rendered inside the report frame).
    _MENU_CONTAINER = ("[role='menu'], .pbi-menu, .pbi-context-menu, drop-down-list, "
                       ".dropdownContainer, .contextMenu, .mat-menu-panel")
    _MENU_ITEM = ("[role='menuitem'], .pbi-menu-item, drop-down-list-item, "
                  ".menuItemContainer, .mat-menu-item, li")

    def _visible_menu_items(self, fr):
        """Return a list of (text) for currently visible context-menu items in the frame."""
        try:
            return fr.evaluate(
                """(sel) => {
                    const norm = s => (s||'').replace(/\\s+/g,' ').trim();
                    const vis = el => {
                        const r = el.getBoundingClientRect();
                        const s = window.getComputedStyle(el);
                        return r.width>0 && r.height>0 && s.visibility!=='hidden' && s.display!=='none';
                    };
                    const out = [];
                    document.querySelectorAll(sel).forEach(e => {
                        if (vis(e)) { const t = norm(e.innerText||e.textContent); if (t) out.push(t); }
                    });
                    return Array.from(new Set(out)).slice(0, 40);
                }""",
                self._MENU_ITEM,
            )
        except Exception:
            return []

    def _ensure_frame(self, tries: int = 6):
        """Return the PBI frame, recovering the Dashboards tab if the iframe detached."""
        fr = self._pbi_frame()
        if fr:
            return fr
        for _ in range(tries):
            try:
                self.open_dashboards_tab()
            except Exception:
                pass
            self.page.wait_for_timeout(1500)
            fr = self._pbi_frame()
            if fr:
                return fr
        return None

    def _close_menu(self):
        """Dismiss any open context menu / submenu."""
        try:
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(150)
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(150)
        except Exception:
            pass

    def _all_visuals(self) -> list:
        """Enumerate every rendered visual with its index, aria-label title and bounding box
        (coordinates are relative to the PowerBI iframe's own viewport)."""
        fr = self._pbi_frame()
        if not fr:
            return []
        try:
            return fr.evaluate(
                """() => {
                    const norm = s => (s||'').replace(/\\s+/g,' ').trim();
                    const vis = el => {
                        const r = el.getBoundingClientRect();
                        const s = window.getComputedStyle(el);
                        return r.width>4 && r.height>4 && s.visibility!=='hidden' && s.display!=='none';
                    };
                    const out = [];
                    let i = 0;
                    document.querySelectorAll('.visualContainer, visual-container').forEach(v => {
                        if (!vis(v)) { i++; return; }
                        const r = v.getBoundingClientRect();
                        const label = norm(v.getAttribute('aria-label') || '') || norm(v.innerText).slice(0, 80);
                        out.push({index: i, label: label,
                                  x: r.x + r.width/2, y: r.y + r.height/2,
                                  w: Math.round(r.width), h: Math.round(r.height)});
                        i++;
                    });
                    return out;
                }"""
            )
        except Exception as e:
            logger.warning(f"[dashboard] _all_visuals eval failed: {e}")
            return []

    def _is_drill_page(self, text: str) -> bool:
        return any(t.lower() in (text or "").lower() for t in self.DRILLTHROUGH_TARGETS)

    def _visual_by_label(self, label_substr: str):
        for v in self._all_visuals():
            if label_substr.lower() in (v.get("label") or "").lower():
                return v
        return None

    def _click_menu_item(self, fr, pattern: str, timeout_ms: int = 4000) -> bool:
        """Click the first visible menu item whose text matches `pattern` (regex, case-insensitive)."""
        rx = re.compile(pattern, re.I)
        end = time.time() + timeout_ms / 1000
        while time.time() < end:
            item = fr.get_by_role("menuitem", name=rx).first
            try:
                if item.count() > 0 and item.is_visible():
                    item.click()
                    return True
            except Exception:
                pass
            # Fallback: any visible menu-item element containing the text.
            loc = fr.locator(self._MENU_ITEM).filter(has_text=rx).first
            try:
                if loc.count() > 0 and loc.is_visible():
                    loc.click()
                    return True
            except Exception:
                pass
            self.page.wait_for_timeout(300)
        return False

    def _hover_menu_item(self, fr, pattern: str, timeout_ms: int = 3000) -> bool:
        """Hover the first visible menu item whose text matches `pattern` (opens PBI flyouts)."""
        rx = re.compile(pattern, re.I)
        end = time.time() + timeout_ms / 1000
        while time.time() < end:
            item = fr.get_by_role("menuitem", name=rx).first
            try:
                if item.count() > 0 and item.is_visible():
                    item.hover()
                    return True
            except Exception:
                pass
            loc = fr.locator(self._MENU_ITEM).filter(has_text=rx).first
            try:
                if loc.count() > 0 and loc.is_visible():
                    loc.hover()
                    return True
            except Exception:
                pass
            self.page.wait_for_timeout(250)
        return False

    # ------------------------------------------------------------------
    # Drill-through
    # ------------------------------------------------------------------
    _DP_SELECTOR = ('svg rect, svg path, svg circle, .column, .bar, .slice, .arc, '
                    '[class*="column"], [class*="bar"], [class*="slice"]')

    def _datapoints_locator(self, v):
        """Playwright locator for the data-point elements inside a visual (by container index)."""
        fr = self._pbi_frame()
        cont = fr.locator(".visualContainer, visual-container").nth(v["index"])
        return cont.locator(self._DP_SELECTOR)

    def _element_drill_targets(self, el) -> list:
        """Left-click a data-point ELEMENT (proper SVG hit-testing) to select it, right-click it
        for the context menu, and return the drill-through target pages (or [])."""
        fr = self._pbi_frame()
        self._close_menu()
        try:
            bb = el.bounding_box()
            if not bb or bb["width"] < 3 or bb["height"] < 3:
                return []
            el.scroll_into_view_if_needed(timeout=2000)
            el.click(timeout=2500)
            self.page.wait_for_timeout(350)
            el.click(button="right", timeout=2500)
        except Exception:
            return []
        items = []
        for _ in range(6):
            self.page.wait_for_timeout(300)
            items = self._visible_menu_items(fr)
            if items:
                break
        if not any(re.search(r"drill[\s\-]?through", it, re.I) for it in items):
            return []
        for _ in range(6):
            self._hover_menu_item(fr, r"drill[\s\-]?through")
            self.page.wait_for_timeout(500)
            sub = self._visible_menu_items(fr)
            hits = [s for s in sub if self._is_drill_page(s)]
            if hits:
                return hits
        return []

    def missing_drill_targets(self, card: str) -> list:
        """Return the expected drill-through target pages NOT offered by `card` ([] means all
        present). Locates a drill point on the card and compares its submenu to
        DRILLTHROUGH_TARGETS."""
        src = self.find_drill_point_for_card(card)
        offered = src["targets"] if src else []
        missing = []
        for t in self.DRILLTHROUGH_TARGETS:
            if not any(t.lower() in o.lower() for o in offered):
                missing.append(t)
        return missing

    def find_drill_point_for_card(self, card: str, refresh: bool = False):
        """Return a drill-through-capable data point for a specific card, using element-based
        clicks on the SVG data points. Result stores the data-point index for reuse."""
        if not refresh and card in DashboardPage._DRILL_POINTS:
            return DashboardPage._DRILL_POINTS[card]
        v = self._visual_by_label(card)
        if not v:
            logger.error(f"[dashboard] card not found for drill: '{card}'")
            return None
        dp = self._datapoints_locator(v)
        try:
            n = min(dp.count(), 30)
        except Exception:
            n = 0
        for i in range(n):
            targets = self._element_drill_targets(dp.nth(i))
            self._close_menu()
            if targets:
                src = {"label": v["label"], "card": card, "dp_index": i, "targets": targets}
                DashboardPage._DRILL_POINTS[card] = src
                logger.info(f"[dashboard] drill point for '{card}' dp#{i} targets={targets}")
                return src
        logger.error(f"[dashboard] no drill-through data point found on card '{card}' ({n} points)")
        return None

    def drill_through(self, target_page: str, card: str = None) -> bool:
        """Drill through from `card` to `target_page`: element-click a data point to select it,
        right-click it for the context menu, hover 'Drill through' and click the target page."""
        fr = self._ensure_frame()
        if not fr:
            logger.error("[dashboard] PowerBI frame not found for drill-through")
            return False

        if not card:
            logger.error("[dashboard] drill_through requires a card (element-based drill)")
            return False
        self._close_menu()
        src = self.find_drill_point_for_card(card)
        if not src or "dp_index" not in src:
            logger.error(f"[dashboard] no drill-through data point found on card '{card}'")
            return False

        v = self._visual_by_label(card)
        if not v:
            logger.error(f"[dashboard] card '{card}' not found for drill-through")
            return False

        rx_target = re.compile(re.escape(target_page), re.I)
        for attempt in range(1, 5):
            try:
                self._close_menu()
                # Cross-filtering from earlier scenarios can detach the cached data point;
                # re-resolve it fresh on any retry so the click lands on a live element.
                if attempt > 1:
                    src = self.find_drill_point_for_card(card, refresh=True)
                    if not src or "dp_index" not in src:
                        continue
                el = self._datapoints_locator(v).nth(src["dp_index"])
                el.scroll_into_view_if_needed(timeout=3000)
                el.click(timeout=3000)              # select the data point
                self.page.wait_for_timeout(350)
                el.click(button="right", timeout=3000)  # open its context menu
                menu = []
                for _ in range(6):
                    self.page.wait_for_timeout(300)
                    menu = self._visible_menu_items(fr)
                    if menu:
                        break
                if not any(re.search(r"drill[\s\-]?through", it, re.I) for it in menu):
                    logger.warning(f"[dashboard] attempt {attempt}: 'Drill through' absent. Menu={menu}")
                    continue
                # Hover 'Drill through' and wait for the target pages to populate the flyout.
                sub_items = []
                for _ in range(6):
                    self._hover_menu_item(fr, r"drill[\s\-]?through")
                    self.page.wait_for_timeout(500)
                    sub_items = self._visible_menu_items(fr)
                    if any(rx_target.search(s) for s in sub_items):
                        break
                if not any(rx_target.search(s) for s in sub_items):
                    logger.warning(f"[dashboard] attempt {attempt}: target '{target_page}' not in "
                                   f"submenu {sub_items}")
                    continue
                if not self._click_menu_item(fr, re.escape(target_page)):
                    logger.warning(f"[dashboard] attempt {attempt}: click '{target_page}' failed")
                    continue
                self.page.wait_for_timeout(4000)
                logger.info(f"[dashboard] drill-through -> '{target_page}' issued")
                return True
            except Exception as e:
                logger.warning(f"[dashboard] attempt {attempt} drill-through error (-> {target_page}): {e}")
                self.page.wait_for_timeout(800)
        logger.error(f"[dashboard] drill-through to '{target_page}' failed after retries")
        return False

    # ------------------------------------------------------------------
    # Report page detection / back navigation
    # ------------------------------------------------------------------
    def _back_button_candidates(self) -> list:
        """List visible elements that look like a PowerBI 'Back' navigation control."""
        fr = self._pbi_frame()
        if not fr:
            return []
        try:
            return fr.evaluate(
                """() => {
                    const norm = s => (s||'').replace(/\\s+/g,' ').trim();
                    const vis = el => {
                        const r = el.getBoundingClientRect();
                        const s = window.getComputedStyle(el);
                        return r.width>0 && r.height>0 && s.visibility!=='hidden' && s.display!=='none';
                    };
                    const out = [];
                    document.querySelectorAll('[aria-label], [title], button, [role="button"]').forEach(e => {
                        if (!vis(e)) return;
                        const t = norm((e.getAttribute('aria-label')||'') + ' ' + (e.getAttribute('title')||'') + ' ' + (e.innerText||''));
                        if (/\\bback\\b/i.test(t)) out.push(norm(e.getAttribute('aria-label') || e.getAttribute('title') || e.innerText));
                    });
                    return Array.from(new Set(out)).slice(0, 20);
                }"""
            )
        except Exception:
            return []

    def go_back(self) -> bool:
        """Click the PowerBI drill-through 'Back' button to return to the dashboard page."""
        fr = self._pbi_frame()
        if not fr:
            return False
        selectors = [
            "role=button[name=/^back$/i]",
            "[aria-label='Back']",
            "[aria-label*='Back' i]",
            "[title*='Back' i]",
            "visual-container[aria-label*='Back' i]",
            ".visualContainer[aria-label*='Back' i]",
        ]
        for sel in selectors:
            try:
                loc = fr.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    try:
                        loc.click()
                    except Exception:
                        # PBI back buttons are action buttons that may require Ctrl+Click.
                        loc.click(modifiers=["Control"])
                    self.page.wait_for_timeout(3000)
                    logger.info(f"[dashboard] clicked back via {sel}")
                    return True
            except Exception:
                continue
        logger.error(f"[dashboard] back button not found. candidates={self._back_button_candidates()}")
        return False

    def current_report_page(self) -> str:
        """Best-effort name of the active PowerBI report page (from the page tabs/active tab)."""
        fr = self._pbi_frame()
        if not fr:
            return ""
        try:
            return fr.evaluate(
                """() => {
                    const norm = s => (s||'').replace(/\\s+/g,' ').trim();
                    const active = document.querySelector('.navigation-wrapper .selected, [role="tab"][aria-selected="true"], .pageTab.selected');
                    return active ? norm(active.innerText || active.getAttribute('aria-label')) : '';
                }"""
            ) or ""
        except Exception:
            return ""

    def is_on_report_page(self, page_name: str) -> bool:
        """The target drill-through page is displayed: match the active page tab, else the
        page title/heading text present in the frame."""
        active = self.current_report_page().lower()
        if page_name.lower() in active:
            return True
        text = self.dashboard_text().lower()
        return page_name.lower() in text
