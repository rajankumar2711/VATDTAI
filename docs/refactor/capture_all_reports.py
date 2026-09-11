"""
Generate ALL three report types and capture each report WINDOW's DOM so we can design a
parameterised, reusable generate/read/export/close method.

For each report type it runs the confirmed enable-Generate sequence, captures the new
window, extracts {title, meta, columns, export options, close button}, and dumps full HTML.

Run:  python docs/refactor/capture_all_reports.py
Output:
  docs/refactor/all_reports_summary.txt
  docs/refactor/all_reports_dump/<type>.html
"""
import os
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("VAT_DTAI_ENV", "qa")

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout  # noqa: E402
from utilities.read_properties import Read_Configurations  # noqa: E402
from tests.step_defs.VAT_Common_Library import (  # noqa: E402
    perform_login, perform_client_selection, perform_dtai_navigation, dismiss_application_popup,
)

OUTDIR = Path(__file__).resolve().parent / "all_reports_dump"
SUMMARY = Path(__file__).resolve().parent / "all_reports_summary.txt"
_lines = []

REPORT_TYPES = ["Invoice Status Report", "Submission Report", "Reconciliation Report"]

# Extract the report window's structure using the generic vatdtai-report-* template.
EXTRACT_JS = r"""
() => {
    const norm = v => (v || '').replace(/\s+/g, ' ').trim();
    const title = (document.querySelector('.vatdtai-report-title') || {}).innerText || document.title || '';
    const meta = Array.from(document.querySelectorAll('.vatdtai-report-meta')).map(m => norm(m.innerText));
    const columns = Array.from(document.querySelectorAll('table.vatdtai-report-table thead th')).map(t => norm(t.innerText));
    // fallbacks in case the class names differ for other report types
    const anyHeaders = columns.length ? columns
        : Array.from(document.querySelectorAll('table thead th, table th, [role="columnheader"]')).map(t => norm(t.innerText)).filter(Boolean);
    const exportBtn = document.querySelector('#vatdtai-report-export') ? '#vatdtai-report-export' : null;
    const exportItems = Array.from(document.querySelectorAll('#vatdtai-report-export-menu [data-export], [data-export]'))
        .map(b => ({label: norm(b.innerText), fmt: b.getAttribute('data-export')}));
    const closeBtn = document.querySelector('#vatdtai-report-close') ? '#vatdtai-report-close' : null;
    const rowCount = document.querySelectorAll('table.vatdtai-report-table tbody tr, table tbody tr').length;
    return {
        title: norm(title),
        containerClassPresent: !!document.querySelector('.vatdtai-report-window'),
        meta, columns: anyHeaders, columnCount: anyHeaders.length,
        exportBtn, exportItems, closeBtn, rowCount,
        bodyLen: document.documentElement.outerHTML.length
    };
}
"""


def emit(title, payload):
    block = f"\n{'='*80}\n{title}\n{'='*80}\n"
    block += json.dumps(payload, indent=2, ensure_ascii=False) if isinstance(payload, (dict, list)) else str(payload)
    _lines.append(block)
    print(block)


def _safe(name):
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:60]


def goto_reports(page):
    for sel in ["role=tab[name='Reports' i]", "a:has-text('Reports')"]:
        loc = page.locator(sel).first
        if loc.count() > 0 and loc.is_visible(timeout=1500):
            loc.click(force=True)
            break
    page.wait_for_timeout(2000)


def dismiss_main_modal(page):
    for sel in ["div.modal-scrollable button:has-text('OK')", "button.btn-default:has-text('OK')",
                "button:has-text('OK')"]:
        try:
            b = page.locator(sel).first
            if b.count() and b.is_visible(timeout=800):
                b.click(force=True)
                page.wait_for_timeout(400)
        except Exception:
            pass


def generate_one(page, context, report_type):
    result = {"report_type": report_type}
    goto_reports(page)

    # select report type
    try:
        page.select_option("#vatdtai_reports_select", label=report_type)
    except Exception as e:
        result["error"] = f"select report type failed: {e}"
        return result
    page.wait_for_timeout(1500)

    card = page.locator(
        "xpath=//select[@id='vatdtai_reports_select']/ancestor::*[.//button[normalize-space()='Generate']][1]")

    # platform (if the platform select is visible for this type)
    platform_visible = page.evaluate("""() => {
        const s = document.getElementById('vatdtai_platform_select');
        if (!s) return false;
        const st = getComputedStyle(s);
        return st.display !== 'none' && st.visibility !== 'hidden' && s.offsetParent !== null;
    }""")
    result["platform_visible"] = platform_visible
    if platform_visible:
        try:
            page.select_option("#vatdtai_platform_select", value="GTES")
            page.wait_for_timeout(600)
            result["platform_selected"] = "GTES"
        except Exception as e:
            result["platform_error"] = str(e)

    # entity commit via dropdown
    try:
        entity = card.locator("input.textinput-group__textinput:not([disabled])").first
        entity.click()
        page.wait_for_timeout(700)
        all_opt = page.locator("ul.dropdown-menu:visible li, .dropdown-menu:visible li", has_text="All").first
        if all_opt.count():
            all_opt.click()
        page.wait_for_timeout(700)
    except Exception as e:
        result["entity_error"] = str(e)

    gen = card.locator("button.btn-primary", has_text="Generate").first

    # Date mode is per-type: Invoice Status uses the RANGE, Submission uses the SINGLE date.
    # Try range first; if Generate is still disabled, fall back to the single date field.
    def _gen_enabled():
        return bool(gen.count() and gen.is_enabled())

    try:
        page.fill("#vatdtai_reports_date_from", "2025-01-01")
        page.fill("#vatdtai_reports_date_to", "2026-10-10")
        page.wait_for_timeout(900)
        result["date_mode"] = "range"
        if not _gen_enabled():
            page.fill("#vatdtai_reports_date", "2025-06-15")
            page.wait_for_timeout(900)
            result["date_mode"] = "single"
    except Exception as e:
        result["date_error"] = str(e)

    result["generate_enabled"] = _gen_enabled()
    if not result["generate_enabled"]:
        result["note"] = "Generate not enabled; skipping"
        return result

    new_page = None
    try:
        with context.expect_page(timeout=9000) as pi:
            gen.click()
        new_page = pi.value
        new_page.wait_for_load_state("load", timeout=15000)
        # Wait past the 'Generating report...' placeholder until the real report renders.
        try:
            new_page.wait_for_selector(
                ".vatdtai-report-window, table.vatdtai-report-table", timeout=30000)
        except PWTimeout:
            result["load_wait"] = "timed out waiting for report window content"
        new_page.wait_for_timeout(1500)
        result["opened_new_window"] = True
        result["window_title"] = new_page.title()
        result["window_url"] = new_page.url
    except PWTimeout:
        result["opened_new_window"] = False

    if new_page is not None:
        try:
            info = new_page.evaluate(EXTRACT_JS)
            result.update(info)
            OUTDIR.mkdir(parents=True, exist_ok=True)
            (OUTDIR / f"{_safe(report_type)}.html").write_text(new_page.content(), encoding="utf-8")
            result["dump_file"] = f"{_safe(report_type)}.html"
        except Exception as e:
            result["extract_error"] = str(e)
        finally:
            try:
                new_page.close()
            except Exception:
                pass
            page.bring_to_front()
    else:
        dismiss_main_modal(page)

    page.wait_for_timeout(800)
    return result


def main():
    Read_Configurations.initialize("qa")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=False, args=["--start-maximized"])
        context = browser.new_context(no_viewport=True, accept_downloads=True)
        page = context.new_page()
        try:
            lp = perform_login(page, role="Admin")
            perform_client_selection(page, lp, "Client Belgium")
            perform_dtai_navigation(page, lp)
            dismiss_application_popup(page)

            for rt in REPORT_TYPES:
                try:
                    emit(f"REPORT: {rt}", generate_one(page, context, rt))
                except Exception:
                    import traceback
                    emit(f"REPORT FATAL: {rt}", traceback.format_exc())
                dismiss_main_modal(page)
        except Exception:
            import traceback
            emit("FATAL", traceback.format_exc())
        finally:
            SUMMARY.write_text("\n".join(_lines), encoding="utf-8")
            print(f"\n\nSummary: {SUMMARY}\nHTML dumps: {OUTDIR}")
            page.wait_for_timeout(1500)
            context.close(); browser.close()


if __name__ == "__main__":
    main()
