"""
Click Generate and capture how the report surfaces: a NEW WINDOW/TAB (new Page in the
context) vs an in-page IFRAME (#smartstreamlitViewer). Dumps full HTML of every frame of
every open page + a summary, so we can decide iframe-handling vs window-handling.

Run:  python docs/refactor/capture_report_window.py
Output:
  docs/refactor/report_window_summary.txt
  docs/refactor/report_window_dump/<page>__<frame>.html
"""
import os
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("VAT_DTAI_ENV", "qa")

from playwright.sync_api import sync_playwright  # noqa: E402
from utilities.read_properties import Read_Configurations  # noqa: E402
from tests.step_defs.VAT_Common_Library import (  # noqa: E402
    perform_login, perform_client_selection, perform_dtai_navigation, dismiss_application_popup,
)

OUTDIR = Path(__file__).resolve().parent / "report_window_dump"
SUMMARY = Path(__file__).resolve().parent / "report_window_summary.txt"
_lines = []


def emit(title, payload):
    block = f"\n{'='*80}\n{title}\n{'='*80}\n"
    block += json.dumps(payload, indent=2, ensure_ascii=False) if isinstance(payload, (dict, list)) else str(payload)
    _lines.append(block)
    print(block)


def _safe(name):
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)[:80] or "unnamed"


def dump_context(context, tag):
    """Enumerate every page + every frame and write full HTML; return a structured summary."""
    OUTDIR.mkdir(parents=True, exist_ok=True)
    summary = []
    for pi, pg in enumerate(context.pages):
        page_entry = {"pageIndex": pi, "url": pg.url, "title": None, "frames": []}
        try:
            page_entry["title"] = pg.title()
        except Exception:
            pass
        for fr in pg.frames:
            info = {"name": fr.name or "(main)", "url": fr.url}
            try:
                html = fr.content()
                info["htmlLen"] = len(html)
                fname = f"{tag}__p{pi}__{_safe(fr.name or 'main')}.html"
                (OUTDIR / fname).write_text(html, encoding="utf-8")
                info["file"] = fname
                # quick signal of report-ish content
                low = html.lower()
                info["hasTable"] = ("<table" in low) or ("tabulator" in low) or ('role="columnheader"' in low)
                info["notConfigured"] = "analytic is not yet configured" in low
            except Exception as exc:
                info["error"] = str(exc)
            page_entry["frames"].append(info)
        summary.append(page_entry)
    return summary


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
            for sel in ["role=tab[name='Reports' i]", "a:has-text('Reports')"]:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible(timeout=1500):
                    loc.click(force=True); break
            page.wait_for_timeout(2500)

            # --- confirmed enable-Generate sequence ---
            page.select_option("#vatdtai_reports_select", label="Invoice Status Report")
            page.wait_for_timeout(1200)

            card = page.locator(
                "xpath=//select[@id='vatdtai_reports_select']/ancestor::*[.//button[normalize-space()='Generate']][1]")
            entity = card.locator("input.textinput-group__textinput:not([disabled])").first
            entity.click()
            page.wait_for_timeout(800)
            all_opt = page.locator("ul.dropdown-menu:visible li, .dropdown-menu:visible li", has_text="All").first
            if all_opt.count():
                all_opt.click()
            page.wait_for_timeout(800)

            page.fill("#vatdtai_reports_date_from", "2025-01-01")
            page.fill("#vatdtai_reports_date_to", "2026-10-10")
            page.wait_for_timeout(1000)

            gen = card.locator("button.btn-primary", has_text="Generate").first
            emit("PRE-GENERATE", {"pagesOpen": len(context.pages), "generateEnabled": gen.is_enabled() if gen.count() else None})

            if not (gen.count() and gen.is_enabled()):
                emit("ABORT", "Generate did not enable; cannot capture report surface")
                return

            # --- click Generate, watch for a NEW WINDOW/TAB ---
            new_page = None
            try:
                with context.expect_page(timeout=8000) as pinfo:
                    gen.click()
                new_page = pinfo.value
                new_page.wait_for_load_state("load", timeout=15000)
                emit("NEW WINDOW DETECTED", {"url": new_page.url})
            except Exception as exc:
                emit("NO NEW WINDOW (likely inline iframe)", str(exc))

            page.wait_for_timeout(6000)  # let streamlit/report settle

            emit("SURFACE VERDICT", {
                "pagesOpenAfter": len(context.pages),
                "newWindow": bool(new_page),
                "mainPageFrames": [{"name": f.name or "(main)", "url": f.url} for f in page.frames],
            })

            summary = dump_context(context, "gen")
            emit("FULL PAGE/FRAME SUMMARY", summary)

            # Explicit recommendation signal
            verdict = "WINDOW_HANDLING" if len(context.pages) > 1 else "IFRAME_HANDLING"
            emit("RECOMMENDATION", verdict)
        except Exception:
            import traceback
            emit("FATAL", traceback.format_exc())
        finally:
            SUMMARY.write_text("\n".join(_lines), encoding="utf-8")
            print(f"\n\nSummary: {SUMMARY}\nHTML dumps: {OUTDIR}")
            page.wait_for_timeout(2000)
            context.close(); browser.close()


if __name__ == "__main__":
    main()
