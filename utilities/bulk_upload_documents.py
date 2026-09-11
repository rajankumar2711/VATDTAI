"""Standalone demo-seeding utility: bulk-upload e-Invoice documents into the
Data Ingestion module for a single client, one file at a time.

It is intentionally self-contained and is NOT part of the pytest suite, so it
cannot affect any existing test. It reuses (read-only) the framework's login
helpers and the Data Ingestion page object.

For the chosen client it walks these source folders under
tests/test_documents/<Country>/ and uploads every CSV/XML/JSON file found:
    CustomERP  -> source system "Custom ERP"
    SAP        -> source system "SAP"
    SAP_JSON   -> source system "SAP"

Records are KEPT (no cleanup) so they remain available for the demo. Files are
discovered dynamically, so dropping new files into the folders and re-running
picks them up with no code changes.

Run (headed Chrome; complete MFA + client selection in the browser if prompted):
    python utilities/bulk_upload_documents.py --client "Client Belgium"
    python utilities/bulk_upload_documents.py --client "Client France"
    python utilities/bulk_upload_documents.py --client "Client Poland"

Optional:
    --env uat            environment section to use (default: uat)
    --source SAP_JSON    only process one source folder
    --max 5              cap files per folder (default: 0 = all)
    --channel chrome     browser channel (default: chrome)
"""

from __future__ import annotations

import os
import re
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # utilities/ -> Playwright_Python
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright
from utilities.read_properties import Read_Configurations
from tests.step_defs.VAT_Common_Library import (
    perform_login,
    perform_client_selection,
    perform_dtai_navigation,
    dismiss_application_popup,
)
from pageobjects.vat_data_ingestion_page import VatDataIngestionPage

# Folder name -> Source System dropdown value
SOURCE_FOLDERS = [
    ("CustomERP", "Custom ERP"),
    ("SAP", "SAP"),
    ("SAP_JSON", "SAP"),
]
ACCEPTED_EXT = {".csv", ".xml", ".json"}
TEST_DOCS = ROOT / "tests" / "test_documents"


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def country_for_client(client: str) -> str:
    """'Client Belgium' -> 'Belgium'."""
    return client.replace("Client", "").strip()


def open_data_ingestion(page) -> bool:
    for loc in [
        "role=tab[name='Data Ingestion' i]",
        "role=link[name='Data Ingestion' i]",
        "text=Data Ingestion",
    ]:
        try:
            el = page.locator(loc).first
            if el.count() > 0 and el.is_visible():
                el.click()
                page.wait_for_timeout(3000)
                log(f"Opened Data Ingestion via: {loc}")
                return True
        except Exception:
            continue
    return False


def read_validation_message(page) -> str:
    """Return the text of any visible success/error toast or alert, else ''."""
    for sel in [".alert.alert-success", ".alert.alert-danger", ".toast", ".Toastify__toast", "[role=alert]"]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                txt = (el.inner_text() or "").strip()
                if txt:
                    return txt
        except Exception:
            continue
    return ""


def verify_new_batch_row(page, di, file_name, timeout_s=75):
    """Poll until the upload produces a new row in the Batch Transactions table.

    The app shows an "Uploading file..." spinner and only adds the row once the
    server accepts the file, so we poll (rather than check once) up to timeout_s.

    Returns (ok, batch_id, message):
      ok        - True if the uploaded file name (or its stem) appears in the grid
      batch_id  - the BATCH_/BATCH-#### id on the matched row (best-effort), else None
      message   - any success/error validation toast text captured
    """
    stem = Path(file_name).stem
    deadline = time.time() + timeout_s
    message = ""
    while time.time() < deadline:
        msg = read_validation_message(page)
        if msg:
            message = msg
            # Fail fast on an explicit error toast.
            if re.search(r"error|not\s+uploaded|invalid|fail", msg, re.I):
                return False, None, message

        try:
            grid_text = page.locator(di.grid_batch_einvoices).inner_text()
        except Exception:
            grid_text = page.inner_text("body")

        if (file_name in grid_text) or (stem and stem in grid_text):
            m = re.search(r"BATCH[-_]\w+", grid_text)
            return True, (m.group(0) if m else None), message

        # Still uploading / row not yet rendered - wait and retry.
        page.wait_for_timeout(2500)

    return False, None, message


def collect_existing_filenames(page, di):
    """Read every File Name already present in the Batch Transactions grid (all pages),
    so files that were uploaded before can be skipped (idempotent / no duplicates)."""
    names = set()
    try:
        grid = page.locator(di.grid_batch_einvoices)
        if grid.count() == 0:
            return names

        # Maximize page size to reduce paging (best-effort).
        try:
            combo = page.locator(di.combobox_rows_per_page_batch)
            if combo.count() > 0:
                for val in ["100", "50", "25", "20"]:
                    try:
                        combo.select_option(val)
                        page.wait_for_timeout(1200)
                        break
                    except Exception:
                        continue
        except Exception:
            pass

        # Start at first page.
        try:
            fp = page.locator(di.btn_first_page_batch)
            if fp.count() > 0 and fp.first.is_enabled():
                fp.first.click()
                page.wait_for_timeout(1000)
        except Exception:
            pass

        last_first_id = None
        for _ in range(80):
            cells = grid.locator(".tabulator-cell[tabulator-field='FileName']")
            for t in cells.all_inner_texts():
                t = t.strip()
                if t:
                    names.add(t)
            try:
                idcells = grid.locator(".tabulator-cell[tabulator-field='BatchId']")
                first_id = idcells.first.inner_text().strip() if idcells.count() > 0 else ""
            except Exception:
                first_id = ""
            nxt = page.locator(di.btn_next_page_batch).first
            if nxt.count() == 0 or nxt.is_disabled() or (first_id and first_id == last_first_id):
                break
            last_first_id = first_id
            try:
                nxt.click()
                page.wait_for_timeout(1000)
            except Exception:
                break

        # Return to first page for uploads.
        try:
            fp = page.locator(di.btn_first_page_batch)
            if fp.count() > 0 and fp.first.is_enabled():
                fp.first.click()
                page.wait_for_timeout(800)
        except Exception:
            pass
    except Exception as e:
        log(f"[prescan] could not read existing rows: {e}")
    return names


def clear_dropzone(page) -> None:
    """Best-effort: remove any staged file / dismiss any open dialog between uploads."""
    try:
        removes = page.locator(".dz-remove, a:has-text('Remove file')")
        for i in range(removes.count()):
            link = removes.nth(i)
            if link.is_visible():
                link.click()
                page.wait_for_timeout(300)
    except Exception:
        pass
    try:
        dialog = page.get_by_role("dialog")
        if dialog.count() > 0 and dialog.first.is_visible():
            for name in ["Close", "Cancel", "No"]:
                btn = dialog.get_by_role("button", name=name)
                if btn.count() > 0 and btn.first.is_visible():
                    btn.first.click()
                    page.wait_for_timeout(300)
                    break
            else:
                page.keyboard.press("Escape")
    except Exception:
        pass


def upload_folder(di, page, country, folder, source_system, max_files, out, start_index=1, existing=None):
    src = TEST_DOCS / country / folder
    existing = existing if existing is not None else set()
    stats = {"total": 0, "uploaded": 0, "failed": 0, "skipped": 0, "duplicates": 0, "failed_files": []}

    if not src.is_dir():
        log(f"[skip] folder not found: {src}")
        stats["missing"] = True
        return stats

    files = sorted([f for f in src.iterdir() if f.is_file()])
    if max_files:
        files = files[:max_files]
    stats["total"] = len(files)
    resume_note = f" (resuming at #{start_index})" if start_index > 1 else ""
    log(f"=== Folder '{folder}' -> source system '{source_system}': {len(files)} file(s){resume_note} ===")

    diag_captured = False
    for i, f in enumerate(files, 1):
        if i < start_index:
            stats["skipped"] += 1
            continue
        if f.suffix.lower() not in ACCEPTED_EXT:
            log(f"  [{i}/{len(files)}] SKIP unsupported extension: {f.name}")
            stats["skipped"] += 1
            continue
        if f.name in existing:
            log(f"  [{i}/{len(files)}] SKIP already uploaded: {f.name}")
            stats["duplicates"] += 1
            continue
        try:
            clear_dropzone(page)
            di.select_source_system(source_system)
            di.upload_file(str(f))
            di.click_upload_button()
            ok, batch_id, message = verify_new_batch_row(page, di, f.name)
            if ok:
                stats["uploaded"] += 1
                existing.add(f.name)
                log(f"  [{i}/{len(files)}] OK: {f.name}  batch_id={batch_id or 'n/a'}"
                    + (f"  msg={message}" if message else ""))
            else:
                stats["failed"] += 1
                stats["failed_files"].append({"file": f.name, "message": message or "no new row detected"})
                log(f"  [{i}/{len(files)}] FAIL (no new row): {f.name}  msg={message or 'none'}")
                if not diag_captured:
                    _capture_failure_diag(page, out, folder, f.name)
                    diag_captured = True
        except Exception as e:
            msg = read_validation_message(page)
            stats["failed"] += 1
            stats["failed_files"].append({"file": f.name, "message": (msg or str(e)[:200])})
            log(f"  [{i}/{len(files)}] FAIL: {f.name} -> {str(e)[:160]}" + (f"  msg={msg}" if msg else ""))
            if not diag_captured:
                _capture_failure_diag(page, out, folder, f.name)
                diag_captured = True
            clear_dropzone(page)
            page.wait_for_timeout(500)

    return stats


def _capture_failure_diag(page, out, folder, file_name):
    """Dump a screenshot + page HTML on the first failure of a folder for diagnosis."""
    try:
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", f"{folder}_{file_name}")
        page.screenshot(path=str(out / f"FAIL_{safe}.png"), full_page=True)
        (out / f"FAIL_{safe}.html").write_text(page.content(), encoding="utf-8")
        log(f"  [diag] captured screenshot + html for first failure: {safe}")
    except Exception as e:
        log(f"  [diag] capture failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Bulk-upload demo documents into Data Ingestion.")
    parser.add_argument("--client", default="Client Belgium",
                        help="Client Belgium | Client France | Client Poland")
    parser.add_argument("--env", default="uat", help="Config environment section (default: uat)")
    parser.add_argument("--source", default=None, help="Only this source folder (CustomERP|SAP|SAP_JSON)")
    parser.add_argument("--folders", default=None,
                        help="Comma-separated ordered folders to process (e.g. 'SAP,SAP_JSON'). Overrides --source.")
    parser.add_argument("--start-index", type=int, default=1, dest="start_index",
                        help="1-based file index to start at, applied to the FIRST folder processed (resume).")
    parser.add_argument("--max", type=int, default=0, help="Cap files per folder (0 = all)")
    parser.add_argument("--no-skip-existing", action="store_true", dest="no_skip_existing",
                        help="Upload every file even if it already exists in the table (allows duplicates).")
    parser.add_argument("--channel", default="chrome", help="Browser channel (default: chrome)")
    args = parser.parse_args()

    client = args.client
    country = country_for_client(client)
    # The login helper re-reads the environment from VAT_DTAI_ENV (defaulting to "qa"),
    # so set it here to keep the whole flow on the requested environment (e.g. uat).
    os.environ["VAT_DTAI_ENV"] = args.env
    Read_Configurations.initialize(args.env)

    src_map = dict(SOURCE_FOLDERS)
    folders = SOURCE_FOLDERS
    if args.folders:
        folders = []
        for name in [x.strip() for x in args.folders.split(",") if x.strip()]:
            match = next((k for k in src_map if k.lower() == name.lower()), None)
            if not match:
                log(f"Unknown folder '{name}' in --folders. Valid: {list(src_map)}")
                sys.exit(2)
            folders.append((match, src_map[match]))
    elif args.source:
        folders = [(f, s) for f, s in SOURCE_FOLDERS if f.lower() == args.source.lower()]
        if not folders:
            log(f"Unknown --source '{args.source}'. Valid: CustomERP, SAP, SAP_JSON")
            sys.exit(2)

    out = ROOT / "reports" / "runs" / f"UAT_BulkUpload_{country}_{datetime.now():%Y%m%d_%H%M%S}"
    out.mkdir(parents=True, exist_ok=True)

    try:
        target_url = Read_Configurations.get_value("VAT_DTAI_URL")
    except Exception:
        target_url = "(unknown)"
    log(f"Client: {client} | Country folder: {country} | Env: {args.env}")
    log(f"Target URL: {target_url}")
    log(f"Source folders: {[f for f, _ in folders]} | Max/folder: {args.max or 'all'}")
    log(f"Artifacts: {out}")

    summary = {"client": client, "country": country, "env": args.env,
               "started": datetime.now().isoformat(), "folders": {}}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel=args.channel, slow_mo=150,
                                    args=["--start-maximized"])
        context = browser.new_context(no_viewport=True, accept_downloads=True)
        page = context.new_page()

        log("=== Login + client selection + DTAI navigation (complete MFA in the browser if prompted) ===")
        launch_page = perform_login(page, role="Admin")
        perform_client_selection(page, launch_page, client)
        perform_dtai_navigation(page, launch_page)
        dismiss_application_popup(page)
        log(f"Ready. Current URL: {page.url}")

        if not open_data_ingestion(page):
            log("[WARN] Could not confirm Data Ingestion tab; attempting to continue.")
        page.wait_for_timeout(2000)

        di = VatDataIngestionPage(page)

        existing = set()
        if not args.no_skip_existing:
            log("Pre-scanning Batch Transactions for already-uploaded files...")
            existing = collect_existing_filenames(page, di)
            log(f"Found {len(existing)} file name(s) already in the table; those will be skipped.")

        for idx, (folder, source_system) in enumerate(folders):
            start = args.start_index if idx == 0 else 1
            stats = upload_folder(di, page, country, folder, source_system, args.max, out, start, existing)
            summary["folders"][folder] = stats

        summary["finished"] = datetime.now().isoformat()
        (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

        # Printed summary table
        log("================ BULK UPLOAD SUMMARY ================")
        log(f"Client: {client}  (country folder: {country})")
        grand_up = grand_fail = grand_skip = grand_dup = grand_tot = 0
        for folder, _ in folders:
            s = summary["folders"].get(folder, {})
            tot, up, fail = s.get("total", 0), s.get("uploaded", 0), s.get("failed", 0)
            skip, dup = s.get("skipped", 0), s.get("duplicates", 0)
            grand_tot += tot; grand_up += up; grand_fail += fail; grand_skip += skip; grand_dup += dup
            note = " (folder missing)" if s.get("missing") else ""
            log(f"  {folder:<10} total={tot:<4} uploaded={up:<4} failed={fail:<4} skipped={skip:<4} duplicates={dup:<4}{note}")
        log(f"  {'TOTAL':<10} total={grand_tot:<4} uploaded={grand_up:<4} failed={grand_fail:<4} skipped={grand_skip:<4} duplicates={grand_dup:<4}")
        log(f"Summary written to: {out / 'summary.json'}")
        log("====================================================")

        log("Keeping browser open 8s, then closing.")
        page.wait_for_timeout(8000)
        try:
            context.close()
            browser.close()
        except Exception:
            pass

    log("DONE.")


if __name__ == "__main__":
    main()
