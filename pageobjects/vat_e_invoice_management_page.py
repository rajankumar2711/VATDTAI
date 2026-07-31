import logging
from playwright.sync_api import Page
from pageobjects.base_page import BasePage

logger = logging.getLogger(__name__)


class VatEInvoiceManagementPage(BasePage):
    """
    Page Object Model for VAT DTAI e-Invoice Management Module.

    DOM observations (captured 2026-07-02):
    - Module tabs are plain <a> elements in a sidebar nav (not role=tab)
    - Active section container: div.vatdtai-eim-section
    - Uploaded e-Invoices table uses Tabulator (not <table>)
    - Filter dropdowns use Carbon Design single-select typeahead inputs
    - Date pickers are native <input type="date">
    """

    def __init__(self, page: Page):
        super().__init__(page)
        logger.info("Initializing VatEInvoiceManagementPage")

        # ==========================================
        # MODULE NAVIGATION
        # ==========================================
        self.tab_im_module = "a:has-text('e-Invoice Management')"

        # ==========================================
        # MODULE HEADER
        # ==========================================
        self.heading_im = "h2:has-text('e-Invoice Management')"

        # ==========================================
        # SECTION HEADINGS
        # ==========================================
        self.heading_uploaded          = "h3:has-text('Uploaded e-Invoices')"
        self.heading_filter_criteria   = "h3:has-text('Filter Criteria')"
        self.heading_outbound          = "h3:has-text('Outbound e-Invoices (AR)')"
        self.heading_inbound           = "h3:has-text('Inbound e-Invoices (AP)')"

        # ==========================================
        # UPLOADED e-INVOICES TABLE (Tabulator)
        # ==========================================
        # Scope all Tabulator queries to the IM section to avoid hitting
        # other modules' tables on the same page
        self.im_section_container      = "div.vatdtai-eim-section"
        self.uploaded_table_container  = "div.vatdtai-eim-section:has(h3:has-text('Uploaded e-Invoices'))"
        self.uploaded_table_rows       = (
            "div.vatdtai-eim-section:has(h3:has-text('Uploaded e-Invoices')) "
            ".tabulator-row"
        )
        self.uploaded_pagination       = (
            "div.vatdtai-eim-section:has(h3:has-text('Uploaded e-Invoices')) "
            "button.tabulator-page.active"
        )
        self.btn_refresh               = (
            "div.vatdtai-eim-section:has(h3:has-text('Uploaded e-Invoices')) "
            "button.btn-primary:has-text('Refresh')"
        )

        # ==========================================
        # FILTER CRITERIA
        # ==========================================
        # Country is read-only – displayed as a label value, no editable input
        self.label_country             = (
            "div.vatdtai-eim-section:has(h3:has-text('Filter Criteria')) "
            "label:has-text('Country')"
        )

        # Date range inputs (native <input type="date">)
        self.input_date_from           = "input#vatdtai_eim_date_from"
        self.input_date_to             = "input#vatdtai_eim_date_to"

        # Entity, Source System, Batch Number use Carbon single-select typeahead
        # Scoped by label proximity within the Filter Criteria section
        self.filter_section            = (
            "div.vatdtai-eim-section:has(h3:has-text('Filter Criteria'))"
        )
        # Positional: 1st typeahead = Entity, 2nd = Source System, 3rd = Batch Number
        self.input_entity              = (
            "div.vatdtai-eim-section:has(h3:has-text('Filter Criteria')) "
            "input.textinput-group__textinput >> nth=0"
        )
        self.input_source_system       = (
            "div.vatdtai-eim-section:has(h3:has-text('Filter Criteria')) "
            "input.textinput-group__textinput >> nth=1"
        )
        self.input_batch_number        = (
            "div.vatdtai-eim-section:has(h3:has-text('Filter Criteria')) "
            "input.textinput-group__textinput >> nth=2"
        )

        # Apply button (scoped to IM Filter Criteria)
        self.btn_apply                 = (
            "div.vatdtai-eim-section:has(h3:has-text('Filter Criteria')) "
            "button.btn-primary:has-text('Apply')"
        )

        # ==========================================
        # OUTBOUND / INBOUND TABLES (Tabulator)
        # ==========================================
        self.outbound_section          = "div.vatdtai-eim-section:has(h3:has-text('Outbound e-Invoices (AR)'))"
        self.inbound_section           = "div.vatdtai-eim-section:has(h3:has-text('Inbound e-Invoices (AP)'))"
        self.outbound_rows             = (
            "div.vatdtai-eim-section:has(h3:has-text('Outbound e-Invoices (AR)')) "
            ".tabulator-row"
        )
        self.inbound_rows              = (
            "div.vatdtai-eim-section:has(h3:has-text('Inbound e-Invoices (AP)')) "
            ".tabulator-row"
        )

        # ==========================================
        # OUTBOUND e-INVOICES (AR) GRID - AGENT STATUS TRACKING
        # (query VATDTAI_GetOutboundInvoices[dateFrom,dateTo,...]; driven by the
        # issue-date Filter Criteria. Fields: InvoiceId (Client e-Invoice Number),
        # Status, InvoiceUuid, LegalName, VatNumber, TaxExclusiveTotal,
        # TotalTaxAmount, DocumentTypeCode, SourceSystem.)
        # Status cell carries title attr = value ("Ready" | "Review Required" |
        # "Reviewed"); the visible label lives in span.vatdtai-status-clickable /
        # span.vatdtai-status-info.
        # ==========================================
        self.outbound_grid_container   = "#vatdtai_eim_outbound_grid"
        self.outbound_grid_table       = "#EimOutboundGrid"
        self.outbound_grid_rows        = "#EimOutboundGrid .tabulator-tableHolder .tabulator-row"
        self.outbound_page_size_select = "#EimOutboundGrid select.tabulator-page-size"
        self.outbound_next_page_btn    = "#EimOutboundGrid button.tabulator-page[data-page='next']"
        self.outbound_status_filter    = (
            "#EimOutboundGrid .tabulator-col[tabulator-field='Status'] input[type='search']"
        )
        self.outbound_invoice_filter   = (
            "#EimOutboundGrid .tabulator-col[tabulator-field='InvoiceId'] input[type='search']"
        )
        self.outbound_show_filters_btn = "#vatdtai_eim_outbound_grid [data-id='btnShowFilterDiv']"
        self._last_filter              = {}

        # ==========================================
        # UPLOADED e-INVOICES GRID (source of the Client Invoice Number)
        # (query VATDTAI_GetInvoices; fields InvoiceId=Client Invoice Number,
        # Status, Timestamp, BatchId=Batch Number; sorted newest-first)
        # ==========================================
        self.uploaded_grid_container   = "#vatdtai_eim_uploaded_grid"
        self.uploaded_grid_table       = "#EimUploadedGrid"
        self.uploaded_grid_rows        = "#EimUploadedGrid .tabulator-tableHolder .tabulator-row"
        self.uploaded_page_size_select = "#EimUploadedGrid select.tabulator-page-size"
        self.uploaded_next_page_btn    = "#EimUploadedGrid button.tabulator-page[data-page='next']"
        self.uploaded_show_filters_btn = "#vatdtai_eim_uploaded_grid [data-id='btnShowFilterDiv']"

    # ==========================================
    # NAVIGATION
    # ==========================================

    def navigate_to_module(self):
        """Click the e-Invoice Management sidebar link."""
        logger.info("Navigating to e-Invoice Management module...")
        tab = self.page.locator(self.tab_im_module).first
        tab.wait_for(state="visible", timeout=10000)
        tab.click()
        self.page.wait_for_timeout(3000)
        logger.info("[OK] Clicked e-Invoice Management tab")

    # ==========================================
    # MODULE VISIBILITY / HEADER
    # ==========================================

    def is_module_accessible(self) -> bool:
        """Return True if the e-Invoice Management heading is visible."""
        try:
            heading = self.page.locator(self.heading_im).first
            return heading.count() > 0 and heading.is_visible(timeout=5000)
        except Exception:
            return False

    def get_module_header_text(self) -> str:
        """Return the visible text of the module heading."""
        return self.page.locator(self.heading_im).first.inner_text().strip()

    # ==========================================
    # SECTION VISIBILITY
    # ==========================================

    def is_uploaded_section_visible(self) -> bool:
        try:
            el = self.page.locator(self.heading_uploaded).first
            return el.count() > 0 and el.is_visible(timeout=5000)
        except Exception:
            return False

    def is_outbound_section_visible(self) -> bool:
        try:
            el = self.page.locator(self.heading_outbound).first
            return el.count() > 0 and el.is_visible(timeout=5000)
        except Exception:
            return False

    def is_inbound_section_visible(self) -> bool:
        try:
            el = self.page.locator(self.heading_inbound).first
            return el.count() > 0 and el.is_visible(timeout=5000)
        except Exception:
            return False

    # ==========================================
    # COUNTRY FIELD (read-only)
    # ==========================================

    def is_country_field_visible(self) -> bool:
        try:
            el = self.page.locator(self.label_country).first
            return el.count() > 0 and el.is_visible(timeout=5000)
        except Exception:
            return False

    def is_country_field_readonly(self) -> bool:
        """
        Country is read-only: it is shown as a static label/text with no
        editable input adjacent to the 'Country' label.
        """
        try:
            # Confirm there is no enabled text input inside the filter section
            # next to the Country label
            section = self.page.locator(self.filter_section).first
            country_inputs = section.locator(
                "label:has-text('Country') ~ input:not([readonly]):not([disabled])"
            )
            return country_inputs.count() == 0
        except Exception:
            return True

    # ==========================================
    # UPLOADED TABLE
    # ==========================================

    def get_uploaded_row_count(self) -> int:
        """Return visible row count in the Uploaded e-Invoices Tabulator table."""
        try:
            rows = self.page.locator(self.uploaded_table_rows)
            self.page.wait_for_timeout(1000)
            return rows.count()
        except Exception:
            return 0

    def get_pagination_text(self) -> str:
        """Return pagination label text e.g. '1 / 110'."""
        try:
            return self.page.locator(self.uploaded_pagination).first.inner_text().strip()
        except Exception:
            return ""

    def click_refresh(self):
        """Click the Refresh button on the Uploaded e-Invoices section."""
        self.page.locator(self.btn_refresh).first.click()
        self.page.wait_for_timeout(2000)

    # ==========================================
    # FILTER CRITERIA
    # ==========================================

    def apply_filter_criteria(
        self,
        date_from: str = "",
        date_to: str = "",
        entity: str = "",
        source_system: str = "",
        batch_number: str = "",
    ):
        """
        Fill filter criteria and click Apply.

        Args:
            date_from: ISO date string YYYY-MM-DD or MM/DD/YYYY
            date_to:   ISO date string YYYY-MM-DD or MM/DD/YYYY
            entity:    Entity name to type into typeahead (empty = All)
            source_system: Source system name (empty = All)
            batch_number:  Batch number (empty = All)
        """
        logger.info(
            f"Applying filter: date_from={date_from} date_to={date_to} "
            f"entity={entity} source_system={source_system} batch={batch_number}"
        )
        self._last_filter = {
            "date_from": date_from, "date_to": date_to, "entity": entity,
            "source_system": source_system, "batch_number": batch_number,
        }
        if date_from:
            self.page.locator(self.input_date_from).fill(date_from)
        if date_to:
            self.page.locator(self.input_date_to).fill(date_to)
        if entity:
            self._fill_typeahead(self.input_entity, entity)
        if source_system:
            self._fill_typeahead(self.input_source_system, source_system)
        if batch_number:
            self._fill_typeahead(self.input_batch_number, batch_number)

        # Click Apply
        self.page.locator(self.btn_apply).first.click()
        self.page.wait_for_timeout(3000)
        logger.info("[OK] Filter applied")

    def _fill_typeahead(self, locator: str, value: str):
        """Clear a Carbon typeahead input and type a value, then select first suggestion."""
        el = self.page.locator(locator).first
        el.triple_click()
        el.type(value)
        self.page.wait_for_timeout(800)
        # Accept first suggestion with Enter or ArrowDown+Enter
        try:
            suggestion = self.page.locator(
                "ul[role='listbox'] li, [role='option']"
            ).first
            if suggestion.count() > 0 and suggestion.is_visible(timeout=1500):
                suggestion.click()
                return
        except Exception:
            pass
        el.press("Enter")

    # ==========================================
    # OUTBOUND / INBOUND TABLE RECORDS
    # ==========================================

    def get_outbound_row_count(self) -> int:
        try:
            rows = self.page.locator(self.outbound_rows)
            self.page.wait_for_timeout(1000)
            return rows.count()
        except Exception:
            return 0

    def get_inbound_row_count(self) -> int:
        try:
            rows = self.page.locator(self.inbound_rows)
            self.page.wait_for_timeout(1000)
            return rows.count()
        except Exception:
            return 0

    def are_outbound_records_visible(self) -> bool:
        """Return True if at least one row is present in the Outbound table."""
        return self.get_outbound_row_count() > 0

    def are_inbound_records_visible(self) -> bool:
        """Return True if at least one row is present in the Inbound table."""
        return self.get_inbound_row_count() > 0

    # ==========================================
    # UPLOADED e-INVOICES GRID - capture the Client Invoice Number(s)
    # dropped via Data Ingestion (matched to their upload batch).
    # ==========================================

    _READ_UPLOADED_JS = """
    () => {
      const rows = document.querySelectorAll('#EimUploadedGrid .tabulator-tableHolder .tabulator-row');
      const out = [];
      rows.forEach(r => {
        const cell = (f) => {
          const c = r.querySelector(`[tabulator-field='${f}']`);
          if (!c) return '';
          return (c.getAttribute('title') || c.textContent || '').trim();
        };
        out.push({
          invoice_id: cell('InvoiceId'),
          status: cell('Status'),
          timestamp: cell('Timestamp'),
          batch: cell('BatchId')
        });
      });
      return out;
    }
    """

    def set_uploaded_page_size(self, size: int = 100):
        """Set the Uploaded grid page size (5/10/25/50/100)."""
        try:
            self.page.locator(self.uploaded_page_size_select).first.select_option(str(size), timeout=6000)
            self.page.wait_for_timeout(1200)
        except Exception as e:
            logger.warning(f"[uploaded] could not set page size: {e}")

    def _read_current_uploaded_page(self):
        try:
            return self.page.evaluate(self._READ_UPLOADED_JS) or []
        except Exception as e:
            logger.warning(f"[uploaded] page read failed: {e}")
            return []

    def get_uploaded_rows(self, max_pages: int = 3):
        """Read Uploaded grid rows (page size 100, newest first)."""
        self.set_uploaded_page_size(100)
        collected = []
        pages = 0
        while pages <= max_pages:
            collected.extend(self._read_current_uploaded_page())
            nxt = self.page.locator(self.uploaded_next_page_btn).first
            try:
                if nxt.count() == 0 or nxt.get_attribute("disabled") is not None or not nxt.is_enabled():
                    break
                nxt.click(timeout=4000)
            except Exception:
                break
            self.page.wait_for_timeout(600)
            pages += 1
        return collected

    _UPLOADED_PENDING = ("in progress", "in-progress", "processing", "pending", "queued", "")

    def capture_uploaded_client_invoice_numbers(self, batch_ids=None, limit=None,
                                                include_pending=False):
        """
        Return the Client Invoice Numbers shown in the Uploaded e-Invoices grid for
        the invoices we just dropped. When batch_ids are supplied (from ingestion),
        only rows whose Batch Number starts with one of those ids are returned
        (the grid appends a hash suffix, e.g. BATCH_20260727115404_a75b427c).

        Rows still being processed show InvoiceId '-' / status 'In Progress' and are
        skipped unless include_pending=True. De-duplicated by (batch, invoice) so two
        distinct uploads are never collapsed. Newest-first.
        """
        rows = self.get_uploaded_rows()
        prefixes = [b for b in (batch_ids or []) if b]
        out, seen = [], set()
        for r in rows:
            inv = (r.get("invoice_id") or "").strip()
            batch = (r.get("batch") or "").strip()
            status = (r.get("status") or "").strip().lower()
            if prefixes and not any(batch.startswith(b) for b in prefixes):
                continue
            pending = inv in ("", "-") or status in self._UPLOADED_PENDING
            if pending and not include_pending:
                continue
            key = (batch, inv)
            if key in seen:
                continue
            seen.add(key)
            out.append(r)
            if limit and len(out) >= limit:
                break
        return out

    def get_existing_uploaded_invoice_numbers(self, max_pages: int = 60) -> set:
        """
        Read every resolved Client Invoice Number currently in the Uploaded e-Invoices
        grid (skips '-' / In Progress placeholders). Used as the authoritative
        'already dropped' set for the Data Ingestion de-duplication pre-flight.
        """
        rows = self.get_uploaded_rows(max_pages=max_pages)
        nums = set()
        for r in rows:
            inv = (r.get("invoice_id") or "").strip()
            if inv and inv != "-":
                nums.add(inv)
        logger.info(f"[uploaded] existing invoice numbers in grid: {len(nums)}")
        return nums

    def wait_uploaded_batches_terminal(self, batch_ids, expected_count=None,
                                       timeout_ms=600000, poll_ms=15000):
        """
        Poll the Uploaded e-Invoices grid until the invoices we dropped (matched by
        their upload batch) leave the 'In Progress' state and expose a real Client
        Invoice Number. Returns the captured terminal rows (best-effort at timeout).
        """
        import time
        deadline = time.time() + timeout_ms / 1000.0
        prefixes = [b for b in (batch_ids or []) if b]
        last = []
        while time.time() < deadline:
            self.navigate_to_module()
            ready = self.capture_uploaded_client_invoice_numbers(batch_ids=prefixes)
            last = ready
            enough = expected_count is None or len(ready) >= expected_count
            if ready and enough:
                logger.info(f"[uploaded] {len(ready)} invoice(s) reached terminal status")
                return ready
            remaining = int(deadline - time.time())
            logger.info(f"[uploaded] waiting for terminal status "
                        f"({len(ready)}/{expected_count or '?'} ready, ~{remaining}s left)")
            self.page.wait_for_timeout(poll_ms)
        logger.warning(f"[uploaded] timed out; {len(last)} invoice(s) ready")
        return last

    # ==========================================
    # OUTBOUND e-INVOICES (AR) GRID - AGENT STATUS TRACKING
    # (verify agent results here after applying the issue-date Filter Criteria)
    # ==========================================

    def set_outbound_page_size(self, size: int = 100):
        """Set the Outbound grid page size (10/25/50/100)."""
        try:
            self.page.locator(self.outbound_page_size_select).first.select_option(str(size), timeout=6000)
            self.page.wait_for_timeout(1500)
        except Exception as e:
            logger.warning(f"[outbound] could not set page size: {e}")

    _READ_ROWS_JS = """
    () => {
      const rows = document.querySelectorAll('#EimOutboundGrid .tabulator-tableHolder .tabulator-row');
      const out = [];
      rows.forEach(r => {
        const cell = (f) => {
          const c = r.querySelector(`[tabulator-field='${f}']`);
          if (!c) return '';
          return (c.getAttribute('title') || c.textContent || '').trim();
        };
        out.push({
          invoice_id: cell('InvoiceId'),
          status: cell('Status'),
          uuid: cell('InvoiceUuid'),
          customer_name: cell('LegalName'),
          customer_number: cell('VatNumber'),
          total_value: cell('TaxExclusiveTotal'),
          tax_value: cell('TotalTaxAmount'),
          document_type: cell('DocumentTypeCode'),
          source_system: cell('SourceSystem')
        });
      });
      return out;
    }
    """

    def _read_current_outbound_page(self):
        """Read all rows on the current page of the Outbound grid in a single JS call."""
        try:
            return self.page.evaluate(self._READ_ROWS_JS) or []
        except Exception as e:
            logger.warning(f"[outbound] page read failed: {e}")
            return []

    def get_all_outbound_rows(self, max_pages: int = 40):
        """Paginate the Outbound grid (page size 100) and return every row as a dict."""
        self.set_outbound_page_size(100)
        collected = []
        pages = 0
        while pages <= max_pages:
            collected.extend(self._read_current_outbound_page())
            nxt = self.page.locator(self.outbound_next_page_btn).first
            try:
                if nxt.count() == 0 or nxt.get_attribute("disabled") is not None or not nxt.is_enabled():
                    break
                nxt.click(timeout=4000)
            except Exception:
                break
            self.page.wait_for_timeout(700)
            pages += 1
        return collected

    def get_outbound_status_counts(self):
        """Return {status: count} across all pages of the Outbound grid."""
        counts = {}
        for r in self.get_all_outbound_rows():
            s = r["status"] or "(blank)"
            counts[s] = counts.get(s, 0) + 1
        return counts

    def refresh_outbound_grid(self):
        """
        Re-run the Outbound grid query WITHOUT losing the issue-date filter by
        re-clicking Apply (the date inputs retain their values). Navigating to the
        module would clear this filter-driven grid.
        """
        try:
            self.page.locator(self.btn_apply).first.click(timeout=6000)
            self.page.wait_for_timeout(3000)
        except Exception as e:
            logger.warning(f"[outbound] refresh (re-apply) failed: {e}")

    @staticmethod
    def _is_review_required(status: str) -> bool:
        return "review required" in (status or "").strip().lower()

    def _review_required_count(self, counts: dict) -> int:
        return sum(v for k, v in counts.items() if self._is_review_required(k))

    def wait_for_agent_completion(
        self,
        timeout_ms: int = 900000,
        poll_ms: int = 30000,
        min_wait_ms: int = 540000,
        pending_statuses=("processing", "in progress", "in-progress", "pending", "queued", "running", "analyzing"),
    ):
        """
        Wait for the validation agent to finish (it typically takes ~10 minutes).

        Strategy: sleep the minimum wait in chunks (the agent may keep rows 'Ready'
        then flip anomalies to 'Review Required' with no intermediate status), then
        re-apply the filter and read Outbound statuses; keep polling until the
        Review Required count is stable across two reads and nothing is pending,
        capped at timeout_ms. Returns the final {status: count}.
        """
        import time
        start = time.time()
        deadline = start + timeout_ms / 1000.0

        # Phase 1: minimum wait in visible chunks
        while (time.time() - start) * 1000 < min_wait_ms and time.time() < deadline:
            remaining = int(min_wait_ms / 1000 - (time.time() - start))
            logger.info(f"[agent-wait] minimum wait: ~{remaining}s remaining")
            self.page.wait_for_timeout(min(poll_ms, max(1000, remaining * 1000)))

        # Phase 2: refresh + read until stable / capped
        last_counts: dict = {}
        prev_review = None
        while time.time() < deadline:
            self.refresh_outbound_grid()
            counts = self.get_outbound_status_counts()
            last_counts = counts
            review_ct = self._review_required_count(counts)
            elapsed = int(time.time() - start)
            logger.info(f"[agent-wait] t+{elapsed}s outbound status counts: {counts} (review_required={review_ct})")
            still_pending = any(
                any(p in (status or "").lower() for p in pending_statuses)
                for status in counts
            )
            stable = prev_review is not None and review_ct == prev_review
            if not still_pending and stable:
                logger.info("[agent-wait] agent complete (no pending, review-required count stable)")
                return counts
            prev_review = review_ct
            self.page.wait_for_timeout(poll_ms)
        logger.warning(f"[agent-wait] timed out; last counts: {last_counts}")
        return last_counts

    def _click_show_filters_if_needed(self):
        try:
            inp = self.page.locator(self.outbound_status_filter).first
            if inp.count() > 0 and inp.is_visible(timeout=1500):
                return
        except Exception:
            pass
        try:
            btn = self.page.locator(self.outbound_show_filters_btn).first
            if btn.count() > 0 and btn.is_visible(timeout=1500):
                btn.click(timeout=4000)
                self.page.wait_for_timeout(800)
        except Exception:
            pass

    def _fill_header_filter(self, selector: str, value: str) -> bool:
        """Fill a Tabulator header-filter input defensively (never hangs on default 30s)."""
        try:
            self._click_show_filters_if_needed()
            inp = self.page.locator(selector).first
            if inp.count() == 0:
                logger.warning(f"[outbound] header filter not found: {selector}")
                return False
            inp.click(timeout=4000)
            inp.fill("", timeout=4000)
            if value:
                inp.type(value, delay=20)
                inp.press("Enter")
            else:
                inp.press("Enter")
            self.page.wait_for_timeout(2000)
            return True
        except Exception as e:
            logger.warning(f"[outbound] header filter fill failed ({selector}): {e}")
            return False

    def filter_outbound_by_status(self, status_text: str) -> bool:
        """Type a value into the Status column header filter of the Outbound grid."""
        return self._fill_header_filter(self.outbound_status_filter, status_text)

    def clear_outbound_status_filter(self):
        self._fill_header_filter(self.outbound_status_filter, "")

    def clear_outbound_invoice_filter(self):
        self._fill_header_filter(self.outbound_invoice_filter, "")

    def search_outbound_invoice(self, invoice_number: str):
        """
        Click the Search icon (Show Filters) and search the Outbound grid by Client
        e-Invoice Number, returning the matching row dict(s) on the current page.
        """
        self._fill_header_filter(self.outbound_invoice_filter, invoice_number)
        rows = self._read_current_outbound_page()
        exact = [r for r in rows if (r.get("invoice_id") or "").strip() == invoice_number.strip()]
        return exact or rows

    def get_review_required_invoices(self, status_text: str = "Review Required"):
        """Filter the Outbound grid to Review Required rows and return their row dicts."""
        self.filter_outbound_by_status(status_text)
        rows = [r for r in self.get_all_outbound_rows() if self._is_review_required(r.get("status"))]
        return rows

    def find_and_open_outbound_status(self, invoice_number: str, occurrence: int = 1,
                                      max_pages: int = 40):
        """
        Search-free lookup: paginate the Outbound grid (page size 100) and open the
        Status label of the `occurrence`-th row whose Client e-Invoice Number matches
        `invoice_number` (occurrence > 1 handles intentional duplicate invoice numbers,
        e.g. the BR13 duplicate-invoice test where two rows share one number).

        Review Required opens the 'D&S AI Agent - Anomaly Review' popup; Ready opens
        the 'Outbound e-Invoice Extract' popup (both dismissed by the caller via Done).
        Bypasses the flaky Tabulator header-filter search (whose input click times out
        even for present invoices). Returns (row_dict|None, opened:bool).
        """
        target = (invoice_number or "").strip()
        self.set_outbound_page_size(100)
        seen = 0
        pages = 0
        while pages <= max_pages:
            row_locs = self.page.locator(self.outbound_grid_rows)
            n = row_locs.count()
            for i in range(n):
                row = row_locs.nth(i)
                try:
                    id_cell = row.locator("[tabulator-field='InvoiceId']").first
                    if id_cell.count() == 0:
                        continue
                    cell_text = (id_cell.get_attribute("title")
                                 or id_cell.inner_text(timeout=1500) or "").strip()
                except Exception:
                    continue
                if cell_text != target:
                    continue
                seen += 1
                if seen < occurrence:
                    continue
                row_dict = {
                    "invoice_id": cell_text,
                    "status": self._cell_text(row, "Status"),
                    "source_system": self._cell_text(row, "SourceSystem"),
                    "customer_name": self._cell_text(row, "LegalName"),
                }
                opened = False
                try:
                    row.scroll_into_view_if_needed(timeout=3000)
                except Exception:
                    pass
                # Click the Status label for every found row. Review Required opens the
                # 'D&S AI Agent - Anomaly Review' popup; Ready opens the 'Outbound
                # e-Invoice Extract' popup (both dismissed by the caller via Done).
                try:
                    status_cell = row.locator("[tabulator-field='Status']").first
                    status_link = status_cell.locator(
                        ".vatdtai-status-clickable, .vatdtai-status-info"
                    ).first
                    target_el = status_link if status_link.count() > 0 else status_cell
                    target_el.click(timeout=4000)
                    self.page.wait_for_timeout(2500)
                    opened = True
                except Exception as e:
                    logger.warning(f"[outbound] status click failed for {target}: {e}")
                return row_dict, opened
            # advance to next page
            nxt = self.page.locator(self.outbound_next_page_btn).first
            try:
                if nxt.count() == 0 or nxt.get_attribute("disabled") is not None or not nxt.is_enabled():
                    break
                nxt.click(timeout=4000)
            except Exception:
                break
            self.page.wait_for_timeout(700)
            pages += 1
        return None, False

    @staticmethod
    def _cell_text(row, field: str) -> str:
        try:
            c = row.locator(f"[tabulator-field='{field}']").first
            if c.count() == 0:
                return ""
            return (c.get_attribute("title") or c.inner_text(timeout=1500) or "").strip()
        except Exception:
            return ""

    def open_outbound_status_for_invoice(self, invoice_id: str) -> bool:
        """
        Filter to a specific invoice and click its (clickable) Status label to open
        the review/anomaly detail view.
        """
        self._fill_header_filter(self.outbound_invoice_filter, invoice_id)
        rows = self.page.locator(self.outbound_grid_rows)
        if rows.count() == 0:
            return False
        try:
            status_cell = rows.first.locator("[tabulator-field='Status']").first
            status_link = status_cell.locator(
                ".vatdtai-status-clickable, .vatdtai-status-info"
            ).first
            if status_link.count() > 0:
                status_link.click(timeout=4000)
            else:
                status_cell.click(timeout=4000)
            self.page.wait_for_timeout(2500)
            return True
        except Exception as e:
            logger.warning(f"[outbound] status click failed: {e}")
            return False

    # Anomaly popup: "D&S AI Agent - Anomaly Review"
    # Each anomaly = .vatdtai-anomaly-card[data-field,data-current,data-suggested]
    _ANOMALY_JS = """
    () => {
      const root = document.querySelector('.vatdtai-anomaly-root');
      if (!root) return null;
      const title = (document.querySelector('.modal-title')?.textContent || '').trim();
      const intro = (root.querySelector('.vatdtai-anomaly-intro')?.textContent || '').trim();
      const btnInfo = (b) => ({
        text: (b.textContent || '').trim(),
        cls: b.className || '',
        disabled: (b.disabled === true) || b.classList.contains('disabled')
                  || b.getAttribute('aria-disabled') === 'true',
      });
      const cards = [];
      root.querySelectorAll('.vatdtai-anomaly-card').forEach(c => {
        const details = Array.from(c.querySelectorAll('.vatdtai-anomaly-detail'))
          .map(d => (d.textContent || '').trim()).filter(Boolean);
        cards.push({
          rule: (c.querySelector('.vatdtai-anomaly-title strong')?.textContent || '').trim(),
          field: c.getAttribute('data-field') || '',
          current: c.getAttribute('data-current') || '',
          suggested: c.getAttribute('data-suggested') || '',
          details: details,
          buttons: Array.from(c.querySelectorAll('button, a.btn')).map(btnInfo),
        });
      });
      const footer = document.querySelector('.modal-scrollable .modal-footer')
                     || document.querySelector('.modal.show .modal-footer')
                     || document.querySelector('.modal-footer');
      const footer_buttons = footer
        ? Array.from(footer.querySelectorAll('button, a.btn')).map(btnInfo) : [];
      return {title, intro, anomaly_count: cards.length, anomalies: cards,
              footer_buttons: footer_buttons};
    }
    """

    def capture_agent_anomalies(self) -> dict:
        """
        Capture the anomalies the agent lists in the 'D&S AI Agent - Anomaly Review'
        popup (opened by clicking a Review Required Status). Returns a structured dict:
        {title, intro, anomaly_count, anomalies:[{rule, field, current, suggested, details}]}.
        """
        try:
            self.page.wait_for_selector(".vatdtai-anomaly-root", timeout=6000)
        except Exception:
            logger.warning("[anomaly] anomaly popup did not appear")
        try:
            data = self.page.evaluate(self._ANOMALY_JS)
        except Exception as e:
            logger.warning(f"[anomaly] capture failed: {e}")
            data = None
        # One-time-ish DOM dump so we can build/verify Accept/Reject automation for the
        # 'D&S AI Agent - Anomaly Review' popup. Files land under screenshots/anomaly_dom/.
        try:
            import os as _os
            from datetime import datetime as _dt
            root = self.page.locator(".vatdtai-anomaly-root").first
            if root.count() > 0:
                _dir = "screenshots/anomaly_dom"
                _os.makedirs(_dir, exist_ok=True)
                ts = _dt.now().strftime("%H%M%S")
                # Dump the whole popup container (incl. footer with Accept/Reject),
                # not just the anomaly-root, so we can build the action automation.
                html = root.evaluate(
                    "el => (el.closest('.modal-scrollable, .modal-content, .modal, "
                    "[role=dialog]') || el.parentElement || el).outerHTML"
                )
                with open(f"{_dir}/anomaly_popup_{ts}.html", "w", encoding="utf-8") as f:
                    f.write(html)
        except Exception:
            pass
        return data or {"title": "", "intro": "", "anomaly_count": 0, "anomalies": [],
                        "footer_buttons": []}

    # ------------------------------------------------------------------
    # Anomaly Review ACTIONS - Accept / Reject AI suggestions
    #   Footer buttons: [data-bb-handler='0']=Accept, '1'=Reject, '2'=Done
    #   Per-suggestion checkbox: input.vatdtai-anomaly-cb[data-anomaly-idx=N]
    #   Select-all checkbox:      input.vatdtai-anomaly-selectall-cb
    # ------------------------------------------------------------------
    _ANOMALY_STATES_JS = """
    () => {
      const root = document.querySelector('.vatdtai-anomaly-root');
      if (!root) return null;
      const cards = [];
      root.querySelectorAll('.vatdtai-anomaly-card').forEach(c => {
        const cb = c.querySelector('input.vatdtai-anomaly-cb');
        cards.push({
          idx: cb ? cb.getAttribute('data-anomaly-idx') : null,
          title: (c.querySelector('.vatdtai-anomaly-title strong')?.textContent || '').trim(),
          checkbox_disabled: cb ? (cb.disabled === true) : null,
          card_disabled: c.classList.contains('disabled')
                         || c.getAttribute('aria-disabled') === 'true'
                         || c.getAttribute('data-actioned') === 'true',
          classes: c.className || '',
        });
      });
      const hist = Array.from(root.querySelectorAll('.vatdtai-decision-history li'))
        .map(li => (li.textContent || '').trim());
      return {suggestion_count: cards.length, cards: cards, decision_history: hist};
    }
    """

    def get_anomaly_suggestion_states(self) -> dict:
        """Per-suggestion state (idx, checkbox_disabled, card_disabled, classes) plus the
        Decision History list - used to assert a suggestion becomes disabled after action."""
        try:
            return self.page.evaluate(self._ANOMALY_STATES_JS) or {
                "suggestion_count": 0, "cards": [], "decision_history": []}
        except Exception as e:
            logger.warning(f"[anomaly] states read failed: {e}")
            return {"suggestion_count": 0, "cards": [], "decision_history": []}

    def anomaly_suggestion_count(self) -> int:
        return self.page.locator(".vatdtai-anomaly-root .vatdtai-anomaly-card").count()

    def anomaly_actionable_indices(self) -> list:
        """data-anomaly-idx values whose checkbox is still ENABLED (not yet actioned)."""
        states = self.get_anomaly_suggestion_states()
        return [str(c.get("idx")) for c in states.get("cards", [])
                if c.get("idx") is not None and not c.get("checkbox_disabled")]

    def anomaly_select_all(self):
        """Tick every ENABLED suggestion (Select All if it is itself enabled, else tick
        each actionable checkbox individually)."""
        sel = self.page.locator("input.vatdtai-anomaly-selectall-cb").first
        try:
            if sel.count() > 0 and sel.is_enabled() and not sel.is_checked():
                sel.check(timeout=3000)
                self.page.wait_for_timeout(200)
                return
        except Exception:
            pass
        for idx in self.anomaly_actionable_indices():
            self.anomaly_select_suggestion(idx)

    def anomaly_select_suggestion(self, idx) -> bool:
        """Check one suggestion by data-anomaly-idx. Returns False if it is disabled."""
        cb = self.page.locator(f"input.vatdtai-anomaly-cb[data-anomaly-idx='{idx}']").first
        try:
            if cb.count() == 0 or not cb.is_enabled():
                return False
            if not cb.is_checked():
                cb.check(timeout=3000)
            self.page.wait_for_timeout(200)
            return True
        except Exception as e:
            logger.warning(f"[anomaly] could not select suggestion {idx}: {e}")
            return False

    def anomaly_accept(self):
        """Click 'Accept AI Suggestion' for the currently-selected suggestion(s)."""
        self.page.locator("button[data-bb-handler='0']").first.click(timeout=5000)
        self.page.wait_for_timeout(1000)

    def anomaly_reject(self):
        """Click 'Reject AI Suggestion' for the currently-selected suggestion(s)."""
        self.page.locator("button[data-bb-handler='1']").first.click(timeout=5000)
        self.page.wait_for_timeout(1000)

    def open_first_review_required(self, invoice_numbers=None, min_suggestions: int = 1):
        """
        Scan the Outbound grid for a Review Required row (optionally limited to
        invoice_numbers) whose Anomaly Review popup has at least min_suggestions
        ACTIONABLE (not already-actioned/disabled) suggestions, open it, and return
        (invoice_number, occurrence, anomaly_data). Non-matching popups are closed as
        we scan. Returns (None, None, None) if none found.
        """
        wanted = set(invoice_numbers) if invoice_numbers else None
        rows = self.get_all_outbound_rows()
        seen = {}
        for r in rows:
            num = (r.get("invoice_id") or "").strip()
            if not num or (wanted and num not in wanted):
                continue
            seen[num] = seen.get(num, 0) + 1
            occ = seen[num]
            if not self._is_review_required(r.get("status")):
                continue
            _, opened = self.find_and_open_outbound_status(num, occurrence=occ)
            if not opened:
                continue
            data = self.capture_agent_anomalies()
            actionable = len(self.anomaly_actionable_indices())
            if actionable >= min_suggestions:
                data["actionable_count"] = actionable
                return num, occ, data
            self.close_anomaly_popup()
        return None, None, None

    def close_anomaly_popup(self):
        """
        Dismiss whichever Outbound popup is open via its 'Done' button - the
        'D&S AI Agent - Anomaly Review' popup (Review Required) and the
        'Outbound e-Invoice Extract' popup (Ready) both close on Done. Falls back to
        Close/OK/Escape and waits for the modal to disappear.
        """
        for sel in (
            ".modal-footer button[data-bb-handler='2']",
            ".modal.show .modal-footer button:has-text('Done')",
            ".modal-footer button:has-text('Done')",
            "button:has-text('Done')",
            ".modal-footer button:has-text('Close')",
            ".modal-footer button:has-text('OK')",
        ):
            try:
                b = self.page.locator(sel).first
                if b.count() > 0 and b.is_visible(timeout=1500):
                    b.click(timeout=3000)
                    break
            except Exception:
                continue
        else:
            try:
                self.page.keyboard.press("Escape")
            except Exception:
                pass
        # Ensure the modal is gone before the next scan so it cannot block clicks.
        try:
            self.page.wait_for_selector(".modal.show", state="hidden", timeout=5000)
        except Exception:
            pass
        self.page.wait_for_timeout(500)

    def capture_open_detail(self) -> dict:
        """
        Best-effort capture of whatever review/anomaly detail view opens after
        clicking a Review Required status. Returns visible text + inner HTML.
        """
        candidates = [
            ".modal.show",
            "div[role='dialog']",
            ".vatdtai-anomaly-root",
            ".vatdtai-eim-detail",
            ".vatdtai-eim-review",
        ]
        for sel in candidates:
            try:
                el = self.page.locator(sel).first
                if el.count() > 0 and el.is_visible():
                    return {
                        "selector": sel,
                        "text": el.inner_text().strip(),
                        "html": el.inner_html(),
                    }
            except Exception:
                continue
        try:
            el = self.page.locator(self.im_section_container).first
            return {"selector": self.im_section_container, "text": el.inner_text().strip(), "html": ""}
        except Exception:
            return {"selector": "", "text": "", "html": ""}
