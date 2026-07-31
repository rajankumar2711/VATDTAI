"""
Step Definitions for VAT DTAI e-Invoice Management Module
Connects Vat_e_invoice_management.feature with vat_e_invoice_management_page.py
"""
import logging
import os
import re
from typing import Dict, Any

import pytest
from playwright.sync_api import Page
from pytest_bdd import given, scenario, then, when, parsers

from pageobjects.vat_e_invoice_management_page import VatEInvoiceManagementPage
from pageobjects.vat_data_ingestion_page import VatDataIngestionPage
from pageobjects.launch_app_page import LaunchAppPage
from utilities import einvoice_agent_e2e as agent_e2e

# Import all common navigation step definitions (login, client selection, DTAI nav, popup)
from tests.step_defs.VAT_Common_Library import *

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(name)s - %(message)s")

_CLIENT_MARKERS = {
    "Client_Belgium": "Belgium",
    "Client_France": "France",
    "Client_Poland": "Poland",
}


# ==========================================
# FIXTURES
# ==========================================

@pytest.fixture()
def vat_context(get_page: Page, request) -> Dict[str, Any]:
    """
    Function-scoped context shared across steps in one scenario.

    The target Client workspace is derived from the scenario's @Client_* tag so the
    Background client-selection step (which reads vat_context['workspace']) picks the
    right country. Defaults to Belgium for scenarios without a client tag.
    """
    country = "Belgium"
    for marker in request.node.iter_markers():
        if marker.name in _CLIENT_MARKERS:
            country = _CLIENT_MARKERS[marker.name]
            break
    logger.info(f"Initializing VAT context for e-Invoice Management test (client={country})")
    return {
        "user_role": "Admin",
        "workspace": f"Client {country}",
        "country": country,
        "applied_filters": {},
    }


@pytest.fixture()
def im_page(get_page: Page) -> VatEInvoiceManagementPage:
    """Function-scoped fixture to provide e-Invoice Management page object."""
    return VatEInvoiceManagementPage(get_page)


@pytest.fixture()
def data_ingestion_page(get_page: Page) -> VatDataIngestionPage:
    """Function-scoped fixture to provide Data Ingestion page object (for the agent E2E)."""
    return VatDataIngestionPage(get_page)


# ==========================================
# SCENARIO DEFINITIONS
# ==========================================

@scenario(
    "../features/Vat_e_invoice_management.feature",
    "Verify access to Invoice Management module for Admin role under VAT DTAI app in GTP IT",
)
def test_invoice_management_access(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_e_invoice_management.feature",
    "Verify the application display the values in tables based on user selection made in filter criteria in Invoice Management module for Admin role under VAT DTAI app in GTP IT",
)
def test_invoice_management_filter(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_e_invoice_management.feature",
    "Belgium - validation agent flags Review Required invoices matching the expected results",
)
def test_agent_e2e_belgium(get_page, vat_context, im_page, data_ingestion_page):
    pass


@scenario(
    "../features/Vat_e_invoice_management.feature",
    "France - validation agent flags Review Required invoices matching the expected results",
)
def test_agent_e2e_france(get_page, vat_context, im_page, data_ingestion_page):
    pass


@scenario(
    "../features/Vat_e_invoice_management.feature",
    "Poland - validation agent flags Review Required invoices matching the expected results",
)
def test_agent_e2e_poland(get_page, vat_context, im_page, data_ingestion_page):
    pass


@scenario(
    "../features/Vat_e_invoice_management.feature",
    "Accept all AI suggestions moves a Review Required invoice to Reviewed",
)
def test_agent_accept_all(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_e_invoice_management.feature",
    "Reject all AI suggestions moves a Review Required invoice to Reviewed",
)
def test_agent_reject_all(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_e_invoice_management.feature",
    "Accepting one of multiple AI suggestions disables that suggestion",
)
def test_agent_accept_one(get_page, vat_context, im_page):
    pass


@scenario(
    "../features/Vat_e_invoice_management.feature",
    "Rejecting one of multiple AI suggestions disables that suggestion",
)
def test_agent_reject_one(get_page, vat_context, im_page):
    pass


# ==========================================
# WHEN STEPS (Navigation / Actions)
# ==========================================

@when("I navigate to Invoice Management module")
def step_navigate_to_im_module(get_page: Page, im_page: VatEInvoiceManagementPage):
    """Click the e-Invoice Management sidebar link and wait for module to load."""
    logger.info("[WHEN] Navigating to e-Invoice Management module")
    im_page.navigate_to_module()
    get_page.wait_for_timeout(2000)
    logger.info("[OK] e-Invoice Management module loaded")


@when("I apply valid filter criteria in Invoice Management module")
def step_apply_filter_criteria(
    get_page: Page,
    im_page: VatEInvoiceManagementPage,
    vat_context: Dict,
):
    """Apply a valid set of filter criteria in the Invoice Management module."""
    logger.info("[WHEN] Applying filter criteria in e-Invoice Management")
    # Use a wide date range so both tables return records
    date_from = "2025-01-01"
    date_to   = "2026-12-31"
    im_page.apply_filter_criteria(date_from=date_from, date_to=date_to)
    vat_context["applied_filters"] = {"date_from": date_from, "date_to": date_to}
    logger.info("[OK] Filter criteria applied")


# ==========================================
# AGENT E2E STEPS (Track B: ingest -> agent -> Review Required)
# ==========================================

def _navigate_to_data_ingestion(get_page: Page):
    """Click the Data Ingestion tab and wait for the upload section to load."""
    locators = [
        "role=tab[name='Data Ingestion' i]",
        "role=link[name='Data Ingestion' i]",
        "text=Data Ingestion",
    ]
    for loc in locators:
        try:
            el = get_page.locator(loc).first
            if el.count() > 0 and el.is_visible():
                el.click()
                break
        except Exception:
            continue
    for indicator in (
        "h5:has-text('Upload e-Invoices')",
        "h6:has-text('Upload e-Invoice Transaction Report')",
        "text=Source System",
    ):
        try:
            get_page.wait_for_selector(indicator, state="visible", timeout=10000)
            break
        except Exception:
            continue
    get_page.wait_for_timeout(2000)


_FILE_INPUT_SELECTORS = (
    "input[type='file'].dz-hidden-input",
    ".dz-hidden-input",
    "#vatdtai_importfiles_upload input[type='file']",
    "div.dropzone.dz-clickable input[type='file']",
    "input[type='file']:not(#chatSidecarFileInput)",
)
_UPLOAD_BTN_SELECTORS = (
    "button[data-id='vatdtai_import_upload_button']",
    "[data-id='vatdtai_import_upload_button']",
    "button.btn-primary:has-text('Upload')",
    "button:has-text('Upload')",
)


def _upload_one_file(get_page: Page, di_page: VatDataIngestionPage, source_system: str, file_path: str) -> Dict:
    """
    Upload a single file robustly:
      - select source system (reuse DI page object dropdown handling),
      - set the file directly on Dropzone's hidden input (no dropzone click => no
        auto-scroll, no file-chooser flakiness, no strict filename verification),
      - scroll the Upload button into view gracefully and click it.
    Returns {'clicked': bool, 'batch_id': str|None, 'message': str}.
    """
    result = {"clicked": False, "batch_id": None, "message": ""}

    di_page.select_source_system(source_system)

    # Set the file on the hidden input (does not scroll the page)
    file_set = False
    for sel in _FILE_INPUT_SELECTORS:
        try:
            inp = get_page.locator(sel).first
            if inp.count() > 0:
                inp.set_input_files(file_path)
                file_set = True
                break
        except Exception:
            continue
    if not file_set:
        result["message"] = "hidden file input not found"
        return result
    get_page.wait_for_timeout(1500)

    # Locate the Upload button, scroll into view gracefully, wait until enabled, click
    btn = None
    for sel in _UPLOAD_BTN_SELECTORS:
        loc = get_page.locator(sel).first
        if loc.count() > 0:
            btn = loc
            break
    if btn is None:
        result["message"] = "Upload button not found"
        return result
    try:
        btn.scroll_into_view_if_needed(timeout=5000)
    except Exception:
        pass
    for _ in range(15):
        try:
            if btn.is_enabled() and btn.get_attribute("disabled") is None:
                break
        except Exception:
            pass
        get_page.wait_for_timeout(1000)
    try:
        btn.click()
        result["clicked"] = True
    except Exception:
        try:
            btn.click(force=True)
            result["clicked"] = True
        except Exception as e:
            result["message"] = f"upload click failed: {str(e)[:160]}"
            return result

    get_page.wait_for_timeout(4000)
    page_text = get_page.inner_text("body")
    m = re.search(r"BATCH[-_][0-9a-zA-Z]+", page_text)
    if m:
        result["batch_id"] = m.group(0)
    elif not re.search(r"success|uploaded", page_text, re.I):
        result["message"] = result["message"] or "no batch id / success text detected"
    return result


@when("I ingest all e-invoice agent test-data files for the client")
def step_ingest_all_agent_files(
    get_page: Page,
    data_ingestion_page: VatDataIngestionPage,
    im_page: VatEInvoiceManagementPage,
    vat_context: Dict,
):
    """
    Drop each test-data XML via Data Ingestion. Singleton invoice numbers are
    de-duplicated against the Uploaded e-Invoices grid so one already present is NOT
    dropped again (already-present invoices are still verified later). Invoice numbers
    that appear in more than one test file are INTENTIONAL duplicates (BR13 - Invoice
    Number Sequence Monitoring) and every copy is always dropped so the duplicate
    condition is exercised. AGENT_E2E_FORCE_REDROP=1 drops everything.
    """
    country = vat_context.get("country", "Belgium")

    # Verify-only mode: skip ingestion and just verify specific invoices
    verify = [s.strip() for s in os.getenv("AGENT_E2E_INVOICES", "").split(",") if s.strip()]
    if verify:
        vat_context["verify_invoices"] = verify
        vat_context["ingestion_results"] = []
        vat_context["newly_dropped"] = []
        logger.info(f"[WHEN] Verify-only mode (AGENT_E2E_INVOICES): skipping ingestion; invoices={verify}")
        return

    files = agent_e2e.discover_country_files(country)
    system_filter = os.getenv("AGENT_E2E_SYSTEM", "").strip()
    if system_filter:
        files = [f for f in files if f["system_folder"].lower() == system_filter.lower()]
        logger.info(f"[WHEN] AGENT_E2E_SYSTEM={system_filter} -> {len(files)} file(s) after filter")
    max_files = int(os.getenv("AGENT_E2E_MAX_FILES", "0") or "0")
    if max_files > 0:
        files = files[:max_files]
        logger.info(f"[WHEN] AGENT_E2E_MAX_FILES={max_files} -> limiting ingestion")
    assert files, f"No test-data XML files found for country '{country}'"

    # Fresh-number mode: rewrite each XML with a run-unique invoice number so the agent
    # re-evaluates every scenario cleanly instead of reading stale statuses / duplicate
    # rows left by earlier runs that reused the same numbers. Intentional duplicates
    # keep sharing their (fresh) number.
    vat_context["fresh_alias"] = {}
    if os.getenv("AGENT_E2E_FRESH", "").strip().lower() in ("1", "true", "yes"):
        run_token = agent_e2e.new_run_token()
        files, alias = agent_e2e.make_fresh_files(files, run_token)
        vat_context["fresh_alias"] = alias
        vat_context["fresh_run_token"] = run_token
        logger.info(f"[WHEN] Fresh-number mode ON (token {run_token}): "
                    f"{len(files)} file(s) rewritten with run-unique invoice numbers")

    # Invoice numbers that appear in more than one file are INTENTIONAL duplicates
    # (e.g. BR13 - Invoice Number Sequence Monitoring: scenario 09 reuses scenario
    # 10's number to trigger DUPLICATE_INVOICE_NUMBER). Every copy must be dropped so
    # the duplicate condition is exercised - they are never de-duplicated away.
    from collections import Counter
    num_counts = Counter(f["invoice_number"] for f in files)
    dup_numbers = {n for n, c in num_counts.items() if c > 1}
    if dup_numbers:
        logger.info(f"[WHEN] Intentional duplicate invoice number(s) (drop every copy): "
                    f"{sorted(dup_numbers)}")

    force_redrop = os.getenv("AGENT_E2E_FORCE_REDROP", "").strip() in ("1", "true", "yes")

    # Pre-flight: read invoice numbers already present in the Uploaded grid
    existing = set()
    if not force_redrop:
        try:
            im_page.navigate_to_module()
            existing = im_page.get_existing_uploaded_invoice_numbers()
        except Exception as e:
            logger.warning(f"[WHEN] Could not read existing Uploaded invoice numbers: {e}")
    logger.info(f"[WHEN] {len(files)} files; {len(existing)} invoice(s) already in Uploaded grid; "
                f"force_redrop={force_redrop}")

    results = []
    dropped_numbers = set()
    dropped_files = 0
    target_numbers = []
    for idx, f in enumerate(files, start=1):
        num = f["invoice_number"]
        if num not in target_numbers:
            target_numbers.append(num)
        outcome = {
            "file_name": f["file_name"],
            "source_system": f["source_system"],
            "invoice_number": num,
            "uploaded": False,
            "skipped_already_present": False,
            "batch_id": None,
            "message": "",
        }
        # Only de-duplicate SINGLETON invoice numbers against the grid (idempotent
        # re-runs). Intentional duplicates (num in dup_numbers) always drop every
        # copy so the duplicate-invoice-number rule is exercised; they are never
        # skipped, even if a copy is already present.
        is_dup = num in dup_numbers
        already = (not is_dup) and (num in existing)
        if already and not force_redrop:
            outcome["skipped_already_present"] = True
            outcome["message"] = "already dropped (present in Uploaded grid)"
            logger.info(f"  ({idx}/{len(files)}) {f['file_name']} -> SKIP ({num} already dropped)")
            results.append(outcome)
            continue
        drop_note = " [duplicate copy]" if is_dup else ""
        logger.info(f"  ({idx}/{len(files)}) {f['file_name']} -> DROP source '{f['source_system']}'{drop_note}")
        try:
            _navigate_to_data_ingestion(get_page)
            up = _upload_one_file(get_page, data_ingestion_page, f["source_system"], f["path"])
            outcome["batch_id"] = up["batch_id"]
            outcome["message"] = up["message"]
            outcome["uploaded"] = bool(up["clicked"] and (up["batch_id"] or not up["message"]))
            if outcome["uploaded"]:
                dropped_numbers.add(num)
                dropped_files += 1
            else:
                logger.warning(f"    [!] Upload not confirmed for {f['file_name']}: {up}")
        except Exception as e:
            outcome["message"] = str(e)[:300]
            logger.warning(f"    [!] Upload failed for {f['file_name']}: {outcome['message']}")
        results.append(outcome)

    vat_context["ingestion_results"] = results
    vat_context["newly_dropped"] = sorted(dropped_numbers)
    vat_context["verify_invoices"] = target_numbers
    skipped = sum(1 for r in results if r["skipped_already_present"])
    logger.info(f"[OK] Ingestion: {dropped_files} file(s) dropped "
                f"({len(dropped_numbers)} unique invoice number(s)), "
                f"{skipped} skipped (already present); "
                f"{len(target_numbers)} unique invoice(s) to verify")
    agent_e2e.save_raw(country, "ingestion_results", results)


@when("I apply the agent issue-date filter in Invoice Management module")
def step_apply_agent_issue_date_filter(
    get_page: Page,
    im_page: VatEInvoiceManagementPage,
    vat_context: Dict,
):
    """Apply a wide issue-date range so the agent runs against all dropped invoices."""
    date_from = "2025-01-01"
    date_to = "2026-12-31"
    logger.info(f"[WHEN] Applying agent issue-date filter {date_from}..{date_to}")
    im_page.apply_filter_criteria(date_from=date_from, date_to=date_to)
    vat_context["applied_filters"] = {"date_from": date_from, "date_to": date_to}
    logger.info("[OK] Issue-date filter applied (agent triggered)")


@when("I wait for e-invoice ingestion to complete")
def step_wait_for_ingestion(
    get_page: Page,
    im_page: VatEInvoiceManagementPage,
    vat_context: Dict,
):
    """
    Phase 1 wait: until the invoices we dropped leave 'In Progress' in the Uploaded
    e-Invoices grid and reach a Ready/terminal status (ingestion complete) so their
    real Client Invoice Number is exposed. Skipped in verify-only mode / when nothing
    new was dropped.
    """
    newly_dropped = vat_context.get("newly_dropped", [])
    if not newly_dropped:
        logger.info("[WHEN] Nothing newly dropped (all already present) - skipping ingestion wait")
        vat_context["uploaded_ready"] = []
        return
    timeout_ms = int(os.getenv("AGENT_E2E_TIMEOUT_SEC", "900")) * 1000
    poll_ms = int(os.getenv("AGENT_E2E_POLL_SEC", "15")) * 1000
    batch_ids = [
        r.get("batch_id") for r in vat_context.get("ingestion_results", [])
        if r.get("batch_id") and r.get("uploaded")
    ]
    expected = len(newly_dropped) or None
    logger.info(f"[WHEN] Waiting for {expected or '?'} uploaded invoice(s) to reach Ready "
                f"(cap {timeout_ms//1000}s), batches={batch_ids}")
    ready = im_page.wait_uploaded_batches_terminal(
        batch_ids=batch_ids, expected_count=expected,
        timeout_ms=timeout_ms, poll_ms=poll_ms,
    )
    vat_context["uploaded_ready"] = ready
    logger.info(f"[OK] Ingestion complete; {len(ready)} invoice(s) Ready")


@when("I wait for the validation agent to finish processing")
def step_wait_for_agent(
    get_page: Page,
    im_page: VatEInvoiceManagementPage,
    vat_context: Dict,
):
    """
    Phase 2 wait: the validation agent runs ~5-10 minutes after ingestion. We first
    wait a passive MIN floor (AGENT_E2E_MIN_WAIT), then run a bounded stability poll
    that reloads the Outbound grid (a read-only GetOutboundInvoices query - it does
    NOT re-trigger the agent) until every dropped invoice appears with a terminal
    status, or the poll cap is reached. This replaces a blind sleep so we do not read
    results before the agent has finished. Skipped in verify-only mode / when nothing
    new was dropped. Set AGENT_E2E_AGENT_POLL=0 to keep the pure passive floor only.
    """
    newly_dropped = vat_context.get("newly_dropped", [])
    if not newly_dropped:
        logger.info("[WHEN] Nothing newly dropped - skipping agent wait (reading existing results)")
        return
    wait_sec = int(os.getenv("AGENT_E2E_MIN_WAIT", "600"))
    chunk = 30
    logger.info(f"[WHEN] Passive floor: waiting ~{wait_sec}s for the agent to run")
    elapsed = 0
    while elapsed < wait_sec:
        remaining = wait_sec - elapsed
        im_page.page.wait_for_timeout(min(chunk, remaining) * 1000)
        elapsed += min(chunk, remaining)
        logger.info(f"[agent-wait] passive floor ~{wait_sec - elapsed}s remaining")

    if os.getenv("AGENT_E2E_AGENT_POLL", "1").strip().lower() not in ("1", "true", "yes"):
        logger.info("[OK] Agent poll disabled; proceeding after passive floor")
        return

    targets = set(newly_dropped)
    poll_sec = int(os.getenv("AGENT_E2E_AGENT_POLL_SEC", "45"))
    cap_sec = int(os.getenv("AGENT_E2E_AGENT_POLL_CAP", "600"))
    pending = ("in progress", "in-progress", "processing", "pending", "queued", "running", "analyzing")

    def _terminal_numbers() -> set:
        im_page.refresh_outbound_grid()  # reload the read-only Outbound query
        by_num: Dict[str, list] = {}
        for r in im_page.get_all_outbound_rows():
            num = (r.get("invoice_id") or "").strip()
            if num:
                by_num.setdefault(num, []).append((r.get("status") or "").strip().lower())
        done = set()
        for inv in targets:
            statuses = by_num.get(inv, [])
            if statuses and any(s and not any(p in s for p in pending) for s in statuses):
                done.add(inv)
        return done

    logger.info(f"[WHEN] Bounded agent poll (cap {cap_sec}s) until {len(targets)} invoice(s) terminal")
    waited = 0
    while waited < cap_sec:
        done = _terminal_numbers()
        logger.info(f"[agent-wait] {len(done)}/{len(targets)} invoice(s) terminal in Outbound")
        if targets.issubset(done):
            logger.info("[OK] All dropped invoices reached a terminal status")
            return
        im_page.page.wait_for_timeout(poll_sec * 1000)
        waited += poll_sec
    logger.warning(f"[agent-wait] poll cap reached; proceeding (some invoices may read NOT_FOUND)")


# ==========================================
# THEN STEPS (Assertions)
# ==========================================

@then(parsers.parse('Invoice Management module is accessible and displayed with header "{header}"'))
@then('Invoice Management module is accessible and displayed with header "Invoice Management"')
def step_verify_module_header(get_page: Page, im_page: VatEInvoiceManagementPage, header: str = "Invoice Management"):
    """Verify the module heading matches the expected text."""
    logger.info(f"[THEN] Verifying module header = '{header}'")
    assert im_page.is_module_accessible(), \
        "e-Invoice Management module is not accessible (heading not visible)"
    actual = im_page.get_module_header_text()
    assert header.lower() in actual.lower(), \
        f"Expected header '{header}' but got '{actual}'"
    logger.info(f"[OK] Module header verified: '{actual}'")


@then("Outbound e-Invoices section is visible")
def step_verify_outbound_section(get_page: Page, im_page: VatEInvoiceManagementPage):
    """Verify the Outbound e-Invoices (AR) section heading is visible."""
    logger.info("[THEN] Verifying Outbound e-Invoices section is visible")
    assert im_page.is_outbound_section_visible(), \
        "Outbound e-Invoices (AR) section heading is not visible"
    logger.info("[OK] Outbound e-Invoices section is visible")


@then("Inbound e-Invoices section is visible")
def step_verify_inbound_section(get_page: Page, im_page: VatEInvoiceManagementPage):
    """Verify the Inbound e-Invoices (AP) section heading is visible."""
    logger.info("[THEN] Verifying Inbound e-Invoices section is visible")
    assert im_page.is_inbound_section_visible(), \
        "Inbound e-Invoices (AP) section heading is not visible"
    logger.info("[OK] Inbound e-Invoices section is visible")


@then("Country field is displayed and read-only")
def step_verify_country_readonly(get_page: Page, im_page: VatEInvoiceManagementPage):
    """Verify the Country label is displayed and has no editable input."""
    logger.info("[THEN] Verifying Country field is displayed and read-only")
    assert im_page.is_country_field_visible(), \
        "Country label is not visible in Filter Criteria section"
    assert im_page.is_country_field_readonly(), \
        "Country field appears to be editable (expected read-only)"
    logger.info("[OK] Country field is displayed and read-only")


@then("Outbound e-Invoices table displays records matching the applied criteria")
def step_verify_outbound_records(get_page: Page, im_page: VatEInvoiceManagementPage):
    """Verify at least one record is visible in the Outbound e-Invoices table."""
    logger.info("[THEN] Verifying Outbound e-Invoices table has records")
    row_count = im_page.get_outbound_row_count()
    logger.info(f"  Outbound row count: {row_count}")
    assert row_count > 0, \
        "Outbound e-Invoices table is empty - expected records matching the applied filter"
    logger.info(f"[OK] Outbound e-Invoices table has {row_count} record(s)")


@then("Inbound e-Invoices table displays records matching the applied criteria")
def step_verify_inbound_records(get_page: Page, im_page: VatEInvoiceManagementPage):
    """Verify at least one record is visible in the Inbound e-Invoices table."""
    logger.info("[THEN] Verifying Inbound e-Invoices table has records")
    row_count = im_page.get_inbound_row_count()
    logger.info(f"  Inbound row count: {row_count}")
    assert row_count > 0, \
        "Inbound e-Invoices table is empty - expected records matching the applied filter"
    logger.info(f"[OK] Inbound e-Invoices table has {row_count} record(s)")


@then("Review Required invoices match the expected results workbook")
def step_review_required_match_expected(
    get_page: Page,
    im_page: VatEInvoiceManagementPage,
    vat_context: Dict,
):
    """
    For each Client Invoice Number we dropped (captured from the Uploaded e-Invoices
    grid), search it in the Outbound (AR) grid via the Search icon, click its Status
    column to open the agent's Anomaly Review popup, capture ALL findings, store them,
    and compare the observed findings + review status against the master
    expected-results workbook - one invoice at a time.
    """
    country = vat_context.get("country", "Belgium")
    logger.info(f"[THEN] Per-invoice agent verification vs master tracker ({country})")

    # 1. Client Invoice Numbers we dropped (captured from the Uploaded grid once the
    #    agent finished); re-read if the wait step didn't stash them.
    batch_ids = [
        r.get("batch_id") for r in vat_context.get("ingestion_results", [])
        if r.get("batch_id")
    ]
    verify = vat_context.get("verify_invoices")
    if verify:
        captured = [{"invoice_id": inv, "status": "", "batch": ""} for inv in verify]
        logger.info(f"  Verify-only: {len(captured)} invoice(s) supplied via AGENT_E2E_INVOICES")
    else:
        captured = vat_context.get("uploaded_ready") or \
            im_page.capture_uploaded_client_invoice_numbers(batch_ids=batch_ids)
    agent_e2e.save_raw(country, "captured_uploaded", captured)
    logger.info(f"  Captured {len(captured)} Client Invoice Number(s) from Uploaded grid")
    assert captured, (
        "No Client Invoice Numbers captured from the Uploaded e-Invoices grid - "
        "ingestion may have failed."
    )

    # 2. Read the WHOLE Outbound grid ONCE (no Apply re-click so the agent stays
    #    triggered exactly once, and no flaky header-filter search). Build a map of
    #    Client e-Invoice Number -> [all matching rows] so intentional duplicates
    #    (two rows sharing one number) are both inspected.
    all_rows = im_page.get_all_outbound_rows()
    rows_by_num: Dict[str, list] = {}
    for r in all_rows:
        num = (r.get("invoice_id") or "").strip()
        if num:
            rows_by_num.setdefault(num, []).append(r)
    logger.info(f"  Outbound grid read once: {len(all_rows)} row(s), "
                f"{len(rows_by_num)} distinct invoice number(s)")

    target_numbers = []
    for row in captured:
        inv = (row.get("invoice_id") or "").strip()
        if inv and inv not in target_numbers:
            target_numbers.append(inv)

    # 3. Per invoice number: produce one observation per physical Outbound row
    #    (occurrence). Ready rows need no popup (status alone = clean/PASS); only
    #    Review Required rows are opened to capture the agent's findings.
    observations = []
    for inv in target_numbers:
        matches = rows_by_num.get(inv, [])
        if not matches:
            observations.append({
                "invoice_id": inv, "occurrence": 1, "source_system": None,
                "found": False, "observed_status": None, "observed_review": False,
                "anomaly_count": 0, "anomalies": [], "popup_title": "",
            })
            logger.info(f"    {inv}: found=False (not in Outbound grid)")
            continue
        for occ, m in enumerate(matches, start=1):
            observed_status = m.get("status")
            observed_review = im_page._is_review_required(observed_status)
            anomalies = {}
            if observed_review:
                # Open only this occurrence's Status to capture the Anomaly Review popup.
                _, opened = im_page.find_and_open_outbound_status(inv, occurrence=occ)
                if opened:
                    try:
                        anomalies = im_page.capture_agent_anomalies()
                    finally:
                        im_page.close_anomaly_popup()
            observations.append({
                "invoice_id": inv,
                "occurrence": occ,
                "source_system": m.get("source_system"),
                "found": True,
                "observed_status": observed_status,
                "observed_review": observed_review,
                "anomaly_count": anomalies.get("anomaly_count", 0),
                "anomalies": anomalies.get("anomalies", []),
                "popup_title": anomalies.get("title", ""),
            })
            logger.info(
                f"    {inv} (#{occ}): status='{observed_status}' "
                f"review={observed_review} anomalies={anomalies.get('anomaly_count', 0)}"
            )
    agent_e2e.save_raw(country, "observations", observations)

    # 4. Offline comparison against the master workbook + persist report
    report = agent_e2e.build_report(
        country=country,
        observations=observations,
        ingestion_results=vat_context.get("ingestion_results", []),
        alias_map=vat_context.get("fresh_alias", {}),
    )
    report_path = agent_e2e.save_report(report)
    excel_path = agent_e2e.update_actual_results_workbook(report)
    logger.info("\n" + agent_e2e.format_summary(report))
    logger.info(f"[OK] Report saved: {report_path}")
    logger.info(f"[OK] Actual result Excel updated: {excel_path}")

    s = report["summary"]
    assert s["processed_invoices"] > 0, (
        "No invoices processed - ingestion or capture failed. "
        f"See report: {report_path}"
    )
    # PASS = status Ready (no anomalies) OR Review Required with findings matching the
    # expected results; anything else FAILS.
    assert s["failed"] == 0, (
        f"{s['failed']} invoice(s) FAILED "
        f"({s['passed']} passed of {s['processed_invoices']} processed). "
        f"A failure means: Review Required with findings not matching the expected "
        f"results, an unexpected status, or the invoice was not found. "
        f"See Excel: {excel_path}"
    )
    logger.info(f"[OK] All {s['passed']} processed invoice(s) passed "
                "(Ready, or Review Required with findings matching expected)")


# ==========================================
# AGENT ACTION STEPS - Accept / Reject AI suggestions (TC1 / TC2)
# ==========================================
def _reviewed_status(status: str) -> bool:
    """A row is 'Reviewed' once its AI suggestions have been actioned (distinct from
    'Review Required', which also contains the word 'review')."""
    return bool(status) and status.strip().lower().startswith("reviewed")


def _outbound_status_of(im_page: VatEInvoiceManagementPage, inv: str, occurrence: int):
    """Re-read the Outbound grid and return the status for the Nth row of an invoice."""
    im_page.refresh_outbound_grid()
    seen = 0
    for r in im_page.get_all_outbound_rows():
        if (r.get("invoice_id") or "").strip() == inv:
            seen += 1
            if seen == occurrence:
                return r.get("status")
    return None


def _action_all_and_expect_reviewed(im_page: VatEInvoiceManagementPage, action: str):
    inv, occ, data = im_page.open_first_review_required(min_suggestions=1)
    if not inv:
        pytest.skip("No Review Required invoice with AI suggestions available to action")
    logger.info(f"[THEN] {action.upper()} ALL suggestions for {inv} (#{occ}); "
                f"{data.get('anomaly_count')} suggestion(s)")
    im_page.anomaly_select_all()
    (im_page.anomaly_accept if action == "accept" else im_page.anomaly_reject)()
    states = im_page.get_anomaly_suggestion_states()
    logger.info(f"[THEN] post-{action} decision history: {states.get('decision_history')}")
    im_page.close_anomaly_popup()
    status = _outbound_status_of(im_page, inv, occ)
    logger.info(f"[THEN] {inv} status after {action}-all: '{status}'")
    assert _reviewed_status(status), (
        f"Expected {inv} to become 'Reviewed' after {action}-all, but status is '{status}'")
    logger.info(f"[OK] {inv} moved to Reviewed after {action}-all")


def _action_one_and_expect_disabled(im_page: VatEInvoiceManagementPage, action: str):
    # Needs >= 2 ACTIONABLE (not already-disabled) suggestions so we can action one and
    # verify the other stays actionable.
    inv, occ, data = im_page.open_first_review_required(min_suggestions=2)
    if not inv:
        pytest.skip("No Review Required invoice with >= 2 actionable AI suggestions available")
    actionable = im_page.anomaly_actionable_indices()
    target = actionable[0]
    logger.info(f"[THEN] {action.upper()} ONE (idx {target}) of actionable {actionable} "
                f"for {inv} (#{occ})")
    assert im_page.anomaly_select_suggestion(target), f"Could not select suggestion {target}"
    (im_page.anomaly_accept if action == "accept" else im_page.anomaly_reject)()
    after = im_page.get_anomaly_suggestion_states()
    cards = after.get("cards", [])
    logger.info(f"[THEN] states after {action}-one: {cards}")
    actioned = next((c for c in cards if str(c.get("idx")) == str(target)), None)
    assert actioned is not None, "Could not read the actioned suggestion state"
    assert actioned.get("checkbox_disabled") or actioned.get("card_disabled"), (
        f"Actioned suggestion {target} should be disabled but was not: {actioned}")
    others = [c for c in cards if str(c.get("idx")) != str(target)]
    assert any(not (c.get("checkbox_disabled") or c.get("card_disabled")) for c in others), (
        "The remaining suggestion(s) should still be actionable but appear disabled")
    im_page.close_anomaly_popup()
    logger.info(f"[OK] {action}-one disabled suggestion {target}; others remain actionable")


@then("accepting all AI suggestions moves the invoice to Reviewed")
def step_accept_all_reviewed(get_page: Page, im_page: VatEInvoiceManagementPage, vat_context: Dict):
    _action_all_and_expect_reviewed(im_page, "accept")


@then("rejecting all AI suggestions moves the invoice to Reviewed")
def step_reject_all_reviewed(get_page: Page, im_page: VatEInvoiceManagementPage, vat_context: Dict):
    _action_all_and_expect_reviewed(im_page, "reject")


@then("accepting one AI suggestion disables it while the others remain actionable")
def step_accept_one_disabled(get_page: Page, im_page: VatEInvoiceManagementPage, vat_context: Dict):
    _action_one_and_expect_disabled(im_page, "accept")


@then("rejecting one AI suggestion disables it while the others remain actionable")
def step_reject_one_disabled(get_page: Page, im_page: VatEInvoiceManagementPage, vat_context: Dict):
    _action_one_and_expect_disabled(im_page, "reject")
