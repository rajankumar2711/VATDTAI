"""
Live smoke of the REUSABLE VatReportsPage.generate_report(...) window handling.
Exercises the same page-object method for two report types and validates
window capture -> columns -> metadata -> export -> close.

Run:  python docs/refactor/smoke_generate_report.py
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
    results = {}
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
            jobs = [
                ("Invoice Status Report", {}),
                ("Reconciliation Report", {}),
                ("Submission Report", {"platform": "GTES"}),
            ]
            for rt, extra in jobs:
                entry = {}
                rp.generate_report(rt, date_from="01/01/2025", date_to="10/10/2026", **extra)
                entry["displayed"] = rp.is_report_displayed(rt)
                meta = rp.get_report_metadata()
                entry["title"] = meta.get("title")
                entry["country"] = meta.get("country")
                entry["entity"] = meta.get("entity")
                entry["platform"] = meta.get("platform")
                entry["format"] = rp.get_report_output_format()
                entry["columns_count"] = len(rp.get_report_column_headers())
                entry["records"] = rp.get_report_record_count()
                exp = rp.export_report("xlsx")
                entry["export_ok"] = exp.get("ok")
                entry["export_file"] = exp.get("suggested") or exp.get("reason")
                entry["closed"] = rp.close_report()
                results[rt] = entry
                page.wait_for_timeout(1000)
        except Exception:
            import traceback
            results["FATAL"] = traceback.format_exc()
        finally:
            print("\n\n===== SMOKE RESULTS =====")
            print(json.dumps(results, indent=2, ensure_ascii=False))
            page.wait_for_timeout(1000)
            context.close(); browser.close()


if __name__ == "__main__":
    main()
