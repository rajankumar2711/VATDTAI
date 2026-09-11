"""Page object for the VAT DTAI 'Detect and Suggest' module (UAT only).

Like the Dashboards tab, this module is an embedded PowerBI report living in an
iframe (src ~ app.powerbi.com/reportEmbed). It is a DIFFERENT report from the
Dashboards one and both report iframes co-exist in the app shell at the same
time, so the frame is selected by its reportId rather than by 'first PowerBI
frame'. Metrics are read from the frame's rendered text / card aria-labels.
"""

import re
import time
import logging

from pageobjects.base_page import BasePage

logger = logging.getLogger(__name__)


class DetectSuggestPage(BasePage):
    # The 'Detect and Suggest' tab inside the DTAI app shell (outside the PowerBI iframe).
    TAB_DETECT_SUGGEST = (
        "a[href='#DetectSuggest'][role='tab'], a[href='#DetectSuggest'], "
        ".nav-link:has-text('Detect and Suggest')"
    )

    # This module's PowerBI report id (distinct from the Dashboards report). Both report
    # iframes are present in the DOM simultaneously, so we always target this one.
    REPORT_ID = "b6f97be3-ed55-43a7-aae9-c1336b6dc97c"
    PBI_IFRAME = f"iframe[src*='{REPORT_ID}']"

    # Named visuals expected on the Detect and Suggest report (matched as substrings
    # against the rendered visual titles / frame text).
    EXPECTED_VISUALS = [
        "Detect and Suggest",
        "Select Invoices",
        "AI Outcome",
        "Invoices By Source System Type",
        "AI Summary by Country",
        "Accepted",
        "Overridden",
        "Rejected",
    ]

    # KPI cards that report a percentage plus a count.
    OUTCOME_CARDS = ["Accepted", "Overridden", "Rejected"]

    # Modern PowerBI visual container (this report renders with data-testid, not .visualContainer).
    VISUAL_SELECTOR = "[data-testid='visual-container'], .visualContainer, visual-container"

    # All PowerBI drill-through target pages seen across drill sources (used for menu detection).
    DRILLTHROUGH_TARGETS = ["Invoice History", "Invoice Details", "Summary Details", "Line Item Details"]

    # Data-point selectors per drill source kind.
    _DP_CHART = ('svg rect, svg path, svg circle, .column, .bar, .slice, .arc, '
                 '[class*="column"], [class*="bar"], [class*="slice"], [class*="arc"]')
    _DP_TABLE = ("[role='gridcell'], [role='cell'], [role='rowheader'], "
                 ".pivotTableCellWrap, [class*='bodyCell'], [class*='pivotTableCell']")

    # Visuals that expose drill-through, matched by a substring of their aria-label/text, plus
    # the data-point selector and the drill-through target pages each one offers. The table
    # additionally offers 'Line Item Details'. Friendly keys are what the feature references.
    DRILL_SOURCES = {
        "AI Summary by Country": {
            "match": "AI Summary by Country", "dp": _DP_CHART,
            "targets": ["Invoice History", "Invoice Details", "Summary Details"],
        },
        "Invoice Details Table": {
            "match": "Invoice_id", "dp": _DP_TABLE,
            "targets": ["Invoice History", "Invoice Details", "Summary Details", "Line Item Details"],
        },
    }

    # Cached per source across scenarios in a session: source -> {label, dp_index, targets}.
    _DRILL_POINTS = {}

    # PowerBI context menu / item selectors (rendered inside the report frame).
    _MENU_ITEM = ("[role='menuitem'], .pbi-menu-item, drop-down-list-item, "
                  ".menuItemContainer, .mat-menu-item, li")

    def __init__(self, get_page):
        super().__init__(get_page)

    # ------------------------------------------------------------------
    # Frame access
    # ------------------------------------------------------------------
    def _pbi_frame(self):
        """Return the Playwright Frame for THIS module's embedded PowerBI report, or None."""
        for fr in self.page.frames:
            if self.REPORT_ID in (fr.url or "").lower():
                return fr
        return None

    def open_detect_suggest_tab(self):
        """Ensure the 'Detect and Suggest' tab is active in the DTAI app shell."""
        try:
            tab = self.page.locator(self.TAB_DETECT_SUGGEST).first
            if tab.count() > 0 and tab.is_visible():
                tab.click()
                self.page.wait_for_timeout(2000)
        except Exception as e:
            logger.debug(f"Detect and Suggest tab click skipped: {e}")

    def wait_until_loaded(self, timeout_ms: int = 120000):
        """Wait for this module's PowerBI iframe to appear and its visuals to render."""
        self.page.wait_for_selector(self.PBI_IFRAME, timeout=timeout_ms)
        end = time.time() + timeout_ms / 1000
        while time.time() < end:
            fr = self._pbi_frame()
            if fr:
                try:
                    info = fr.evaluate(
                        """() => {
                            const vis = document.querySelectorAll(
                                "[data-testid='visual-container'], .visualContainer, visual-container");
                            const body = (document.body && document.body.innerText || '').toLowerCase();
                            return {count: vis.length, loading: body.includes('loading data')};
                        }"""
                    )
                    if info and info.get("count", 0) > 0 and not info.get("loading"):
                        self.page.wait_for_timeout(2500)
                        logger.info(f"[detect] PowerBI rendered: {info.get('count')} visuals")
                        return True
                except Exception:
                    pass
            self.page.wait_for_timeout(2000)
        logger.warning("[detect] PowerBI visuals did not confirm rendered within timeout")
        return False

    def is_powerbi_report_present(self) -> bool:
        return self.page.locator(self.PBI_IFRAME).count() > 0

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------
    def detect_text(self) -> str:
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
                    document.querySelectorAll(
                        "[data-testid='visual-container'], .visualContainer, visual-container").forEach(v => {
                        const t = v.getAttribute('aria-label') || '';
                        const inner = norm(v.innerText).slice(0, 120);
                        out.push(norm(t) || inner);
                    });
                    return out.filter(Boolean);
                }"""
            )
        except Exception:
            return []

    def missing_visuals(self) -> list:
        """Expected visuals that are not found in the rendered titles or frame text."""
        titles_blob = " | ".join(self.visual_titles()).lower()
        text_blob = self.detect_text().lower()
        missing = []
        for name in self.EXPECTED_VISUALS:
            n = name.lower()
            if n not in titles_blob and n not in text_blob:
                missing.append(name)
        return missing

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------
    def _cards(self) -> list:
        """Return [{aria, text}] for each KPI card cell in the report."""
        fr = self._pbi_frame()
        if not fr:
            return []
        try:
            return fr.evaluate(
                """() => {
                    const norm = s => (s||'').replace(/\\s+/g,' ').trim();
                    const seen = new Set();
                    const out = [];
                    document.querySelectorAll('.cardVisual').forEach(c => {
                        const aria = norm(c.getAttribute('aria-label') || '');
                        const text = norm(c.innerText || '');
                        if (!aria && !text) return;
                        const key = aria + '|' + text;
                        if (seen.has(key)) return; seen.add(key);
                        out.push({aria, text});
                    });
                    return out;
                }"""
            )
        except Exception as e:
            logger.warning(f"[detect] card read failed: {e}")
            return []

    def read_metrics(self) -> dict:
        """Parse the KPI cards: Invoices count and Accepted/Overridden/Rejected (pct + count).

        Primary source is the card cell aria-labels ("Invoices, 13 card" /
        "Accepted, 0.00% card"); we fall back to the rendered frame text
        ("13 Invoices 0.00% Accepted 0 ...") which is robust to DOM class changes.
        """
        cards = self._cards()
        metrics: dict = {"cards": cards}

        def card_for(label):
            for c in cards:
                if c.get("aria", "").lower().startswith(label.lower() + ","):
                    return c
            return None

        text = re.sub(r"\s+", " ", self.detect_text())

        # Invoices count.
        invoices = None
        inv = card_for("Invoices")
        if inv:
            m = re.search(r"invoices,\s*([\d,]+)", inv["aria"], re.I)
            invoices = m.group(1).replace(",", "") if m else None
        if invoices is None:
            m = re.search(r"([\d,]+)\s+Invoices\b", text, re.I)
            invoices = m.group(1).replace(",", "") if m else None
        metrics["invoices"] = invoices

        # Accepted / Overridden / Rejected: percentage + count.
        for label in self.OUTCOME_CARDS:
            pct = count = None
            c = card_for(label)
            if c:
                pm = re.search(rf"{label},\s*([\d.]+)\s*%", c["aria"], re.I)
                cm = re.search(r"(\d[\d,]*)\s*$", c["text"])
                pct = (pm.group(1) + "%") if pm else None
                count = cm.group(1).replace(",", "") if cm else None
            if pct is None or count is None:
                tm = re.search(rf"([\d.]+)\s*%\s*{label}\s*([\d,]+)", text, re.I)
                if tm:
                    pct = pct or (tm.group(1) + "%")
                    count = count or tm.group(2).replace(",", "")
            metrics[label.lower()] = {"pct": pct, "count": count}

        logger.info(f"[detect] metrics: {{invoices: {metrics.get('invoices')}, "
                    f"accepted: {metrics.get('accepted')}, overridden: {metrics.get('overridden')}, "
                    f"rejected: {metrics.get('rejected')}}}")
        return metrics

    # ------------------------------------------------------------------
    # Drill-through
    # ------------------------------------------------------------------
    def _ensure_frame(self, tries: int = 6):
        """Return the PBI frame, recovering the Detect and Suggest tab if the iframe detached."""
        fr = self._pbi_frame()
        if fr:
            return fr
        for _ in range(tries):
            try:
                self.open_detect_suggest_tab()
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

    def _visible_menu_items(self, fr) -> list:
        """Text of the currently visible context-menu items in the frame."""
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

    def _click_menu_item(self, fr, pattern: str, timeout_ms: int = 4000) -> bool:
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

    def _is_drill_page(self, text: str) -> bool:
        return any(t.lower() in (text or "").lower() for t in self.DRILLTHROUGH_TARGETS)

    def _all_visuals(self) -> list:
        """Enumerate every rendered visual with its DOM index, aria-label/title and box."""
        fr = self._pbi_frame()
        if not fr:
            return []
        try:
            return fr.evaluate(
                """(sel) => {
                    const norm = s => (s||'').replace(/\\s+/g,' ').trim();
                    const vis = el => {
                        const r = el.getBoundingClientRect();
                        const s = window.getComputedStyle(el);
                        return r.width>4 && r.height>4 && s.visibility!=='hidden' && s.display!=='none';
                    };
                    const out = [];
                    let i = 0;
                    document.querySelectorAll(sel).forEach(v => {
                        if (!vis(v)) { i++; return; }
                        const label = norm(v.getAttribute('aria-label') || '') || norm(v.innerText).slice(0, 90);
                        out.push({index: i, label: label});
                        i++;
                    });
                    return out;
                }""",
                self.VISUAL_SELECTOR,
            )
        except Exception as e:
            logger.warning(f"[detect] _all_visuals eval failed: {e}")
            return []

    def _visual_by_label(self, label_substr: str):
        for v in self._all_visuals():
            if label_substr.lower() in (v.get("label") or "").lower():
                return v
        return None

    def _datapoints_locator(self, v, dp_selector: str):
        fr = self._pbi_frame()
        cont = fr.locator(self.VISUAL_SELECTOR).nth(v["index"])
        return cont.locator(dp_selector)

    def _element_drill_targets(self, el) -> list:
        """Left-click a data-point ELEMENT to select it, right-click for the context menu,
        and return the drill-through target pages (or [])."""
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

    def _source_config(self, source: str) -> dict:
        cfg = self.DRILL_SOURCES.get(source)
        if not cfg:
            logger.error(f"[detect] unknown drill source '{source}'")
        return cfg or {}

    def expected_targets(self, source: str) -> list:
        return self._source_config(source).get("targets", [])

    def find_drill_point_for_card(self, source: str, refresh: bool = False):
        """Return a drill-through-capable data point for a drill source (chart or table)."""
        if not refresh and source in DetectSuggestPage._DRILL_POINTS:
            return DetectSuggestPage._DRILL_POINTS[source]
        cfg = self._source_config(source)
        if not cfg:
            return None
        v = self._visual_by_label(cfg["match"])
        if not v:
            logger.error(f"[detect] drill source not found: '{source}' (match '{cfg['match']}')")
            return None
        dp = self._datapoints_locator(v, cfg["dp"])
        try:
            n = min(dp.count(), 40)
        except Exception:
            n = 0
        for i in range(n):
            targets = self._element_drill_targets(dp.nth(i))
            self._close_menu()
            if targets:
                src = {"label": v["label"], "source": source, "dp_index": i, "targets": targets}
                DetectSuggestPage._DRILL_POINTS[source] = src
                logger.info(f"[detect] drill point for '{source}' dp#{i} targets={targets}")
                return src
        logger.error(f"[detect] no drill-through data point found on source '{source}' ({n} points)")
        return None

    def missing_drill_targets(self, source: str) -> list:
        """Expected drill-through target pages NOT offered by `source` ([] means all present)."""
        src = self.find_drill_point_for_card(source)
        offered = src["targets"] if src else []
        missing = []
        for t in self.expected_targets(source):
            if not any(t.lower() in o.lower() for o in offered):
                missing.append(t)
        return missing

    def drill_through(self, target_page: str, source: str) -> bool:
        """Drill through from `source` to `target_page`: element-click a data point to select it,
        right-click it, hover 'Drill through' and click the target page."""
        fr = self._ensure_frame()
        if not fr:
            logger.error("[detect] PowerBI frame not found for drill-through")
            return False
        cfg = self._source_config(source)
        if not cfg:
            return False
        self._close_menu()
        src = self.find_drill_point_for_card(source)
        if not src or "dp_index" not in src:
            logger.error(f"[detect] no drill-through data point found on source '{source}'")
            return False

        rx_target = re.compile(re.escape(target_page), re.I)
        for attempt in range(1, 5):
            try:
                self._close_menu()
                if attempt > 1:
                    src = self.find_drill_point_for_card(source, refresh=True)
                    if not src or "dp_index" not in src:
                        continue
                v = self._visual_by_label(cfg["match"])
                if not v:
                    continue
                el = self._datapoints_locator(v, cfg["dp"]).nth(src["dp_index"])
                el.scroll_into_view_if_needed(timeout=3000)
                el.click(timeout=3000)
                self.page.wait_for_timeout(350)
                el.click(button="right", timeout=3000)
                menu = []
                for _ in range(6):
                    self.page.wait_for_timeout(300)
                    menu = self._visible_menu_items(fr)
                    if menu:
                        break
                if not any(re.search(r"drill[\s\-]?through", it, re.I) for it in menu):
                    logger.warning(f"[detect] attempt {attempt}: 'Drill through' absent. Menu={menu}")
                    continue
                sub_items = []
                for _ in range(6):
                    self._hover_menu_item(fr, r"drill[\s\-]?through")
                    self.page.wait_for_timeout(500)
                    sub_items = self._visible_menu_items(fr)
                    if any(rx_target.search(s) for s in sub_items):
                        break
                if not any(rx_target.search(s) for s in sub_items):
                    logger.warning(f"[detect] attempt {attempt}: target '{target_page}' not in {sub_items}")
                    continue
                if not self._click_menu_item(fr, re.escape(target_page)):
                    logger.warning(f"[detect] attempt {attempt}: click '{target_page}' failed")
                    continue
                self.page.wait_for_timeout(4000)
                logger.info(f"[detect] drill-through -> '{target_page}' issued")
                return True
            except Exception as e:
                logger.warning(f"[detect] attempt {attempt} drill-through error (-> {target_page}): {e}")
                self.page.wait_for_timeout(800)
        logger.error(f"[detect] drill-through to '{target_page}' failed after retries")
        return False

    # ------------------------------------------------------------------
    # Report page detection / back navigation
    # ------------------------------------------------------------------
    def _back_button_candidates(self) -> list:
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
        """Click the PowerBI drill-through 'Back' button to return to the report page."""
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
                        loc.click(modifiers=["Control"])
                    self.page.wait_for_timeout(3000)
                    logger.info(f"[detect] clicked back via {sel}")
                    return True
            except Exception:
                continue
        logger.error(f"[detect] back button not found. candidates={self._back_button_candidates()}")
        return False

    def current_report_page(self) -> str:
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
        active = self.current_report_page().lower()
        if page_name.lower() in active:
            return True
        text = self.detect_text().lower()
        return page_name.lower() in text
