"""
Capture Submission Report window columns via the reusable generate_report(...).
Submission uses a SINGLE date and requires platform=GTES.

Run:  python docs/refactor/capture_submission_cols.py
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
from pageobjects.vat_reports_page import VatReportsPage  # noqa: E402


def main():
    Read_Configurations.initialize("qa")
    out = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=False, args=["--start-maximized"])
        context = browser.new_context(no_viewport=True, accept_downloads=True)
        page = context.new_page()
        try:
            lp = perform_login(page, role="Admin")
            perform_client_selection(page, lp, "Client Belgium")
            perform_dtai_navigation(page, lp)
            dismiss_application_popup(page)

            rp = VatReportsPage(page)
            rp.generate_report("Submission Report", platform="GTES",
                               date_from="01/01/2025", date_to="10/10/2026", wait_ms=45000)
            out["report_window_is_none"] = rp.report_window is None
            pages_info = []
            for p in context.pages:
                try:
                    pages_info.append({"url": p.url, "title": p.title(), "closed": p.is_closed()})
                except Exception as e:
                    pages_info.append({"err": str(e)})
            out["pages"] = pages_info
            # Fall back to the last non-opener page if report_window wasn't captured.
            win = rp.report_window
            if win is None and len(context.pages) > 1:
                win = context.pages[-1]
                out["used_fallback_page"] = True
            if win is not None and not win.is_closed():
                win.wait_for_timeout(6000)
                out["win_title"] = win.title()
                out["win_url"] = win.url
                body = ""
                try:
                    body = win.inner_text("body")
                except Exception as e:
                    body = f"<err {e}>"
                out["win_body_text"] = body[:1500]
                html = win.content()
                (ROOT / "docs" / "refactor" / "submission_window.html").write_text(html, encoding="utf-8")
                out["win_html_len"] = len(html)
            out["displayed"] = rp.is_report_displayed("Submission Report")
            meta = rp.get_report_metadata()
            out["title"] = meta.get("title")
            out["country"] = meta.get("country")
            out["entity"] = meta.get("entity")
            cols = rp.get_report_column_headers()
            out["columns_count"] = len(cols)
            out["columns"] = cols
            page.wait_for_timeout(1500)
            rp.close_report()
        except Exception:
            import traceback
            out["FATAL"] = traceback.format_exc()
        finally:
            print("\n\n===== SUBMISSION CAPTURE =====")
            print(json.dumps(out, indent=2, ensure_ascii=False))
            (ROOT / "docs" / "refactor" / "submission_cols.json").write_text(
                json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
            page.wait_for_timeout(1000)
            context.close(); browser.close()


if __name__ == "__main__":
    main()
