"""
Debug the 2nd-cycle Reconciliation form state.
Generate Invoice Status, close, navigate to Reconciliation, and DUMP the reports-card DOM:
combobox data-titles, native selects, date inputs present, entity menu contents, and what
happens to the entity display before/after date entry.

Run:  python docs/refactor/debug_cycle2.py
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

CARD_STATE_JS = r"""() => {
    const norm = v => (v || '').replace(/\s+/g, ' ').trim();
    const rep = document.getElementById('vatdtai_reports_select');
    const card = rep ? rep.closest('.card, [class*="card"]') || document.body : document.body;
    const combos = Array.from(card.querySelectorAll('input.textinput-group__textinput')).map(inp => ({
        disabled: inp.disabled,
        dataTitle: inp.getAttribute('data-title'),
        dataId: inp.getAttribute('data-id'),
        value: inp.value,
        nativeValue: (() => { const n = document.getElementById(inp.getAttribute('data-id')); return n ? n.value : '__no_native__'; })(),
        nativeOptions: (() => { const n = document.getElementById(inp.getAttribute('data-id')); return n ? Array.from(n.selectedOptions).map(o => o.text).slice(0,5) : []; })(),
    }));
    return {
        reportValue: rep ? rep.value : '__no_rep__',
        dateSingle: !!document.getElementById('vatdtai_reports_date'),
        dateSingleVal: (document.getElementById('vatdtai_reports_date')||{}).value || '',
        dateFrom: !!document.getElementById('vatdtai_reports_date_from'),
        dateFromVal: (document.getElementById('vatdtai_reports_date_from')||{}).value || '',
        dateTo: !!document.getElementById('vatdtai_reports_date_to'),
        dateToVal: (document.getElementById('vatdtai_reports_date_to')||{}).value || '',
        combos,
    };
}"""

MENU_JS = r"""() => {
    const norm = v => (v || '').replace(/\s+/g, ' ').trim();
    const menus = Array.from(document.querySelectorAll('ul.dropdown-menu, .dropdown-menu'))
        .filter(m => m.offsetParent !== null);
    return menus.map(m => Array.from(m.querySelectorAll('li')).slice(0, 8).map(li => ({
        text: norm(li.innerText || li.textContent),
        cls: li.className,
        html: li.innerHTML.slice(0, 120),
    })));
}"""


def dump(page, label):
    print(f"\n----- {label} -----")
    print(json.dumps(page.evaluate(CARD_STATE_JS), indent=2, ensure_ascii=False))


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

            rp = VatReportsPage(page)

            # ---- Cycle 1: Invoice Status ----
            rp.generate_report("Invoice Status Report", date_from="01/01/2025", date_to="10/10/2026")
            print("\nCycle1 displayed:", rp.is_report_displayed("Invoice Status Report"))
            rp.close_report()
            page.wait_for_timeout(1500)

            # ---- Cycle 2: Reconciliation, step by step ----
            rp.navigate_to_reports_module()
            dump(page, "C2 after navigate (before select type)")

            rp.select_report_type("Reconciliation Report", allow_fallback=False)
            page.wait_for_timeout(800)
            dump(page, "C2 after select Reconciliation")

            # open entity menu and dump contents
            opened = rp._open_entity_menu()
            print("\nC2 entity menu opened:", opened)
            print(json.dumps(page.evaluate(MENU_JS), indent=2, ensure_ascii=False))

            # click 'All' once, dump
            import re as _re
            opt = page.locator("ul.dropdown-menu:visible li, .dropdown-menu:visible li").filter(
                has_text=_re.compile(r"^\s*All\s*$")).first
            print("\nC2 'All' option count:", opt.count())
            if opt.count():
                opt.click(); page.wait_for_timeout(600)
                dump(page, "C2 after 1st 'All' click")
                # second click
                if page.locator("ul.dropdown-menu:visible li").count():
                    opt2 = page.locator("ul.dropdown-menu:visible li").filter(
                        has_text=_re.compile(r"^\s*All\s*$")).first
                    if opt2.count():
                        opt2.click(); page.wait_for_timeout(600)
                        dump(page, "C2 after 2nd 'All' click")
                page.keyboard.press("Escape"); page.wait_for_timeout(400)
                dump(page, "C2 after Escape")

            # now dates
            rp.set_date_range("01/01/2025", "10/10/2026")
            dump(page, "C2 after set_date_range")
            print("\nC2 generate state:", json.dumps(rp._generate_button_state(), ensure_ascii=False))

            page.wait_for_timeout(3000)
        except Exception:
            import traceback
            print("\nFATAL:\n", traceback.format_exc())
        finally:
            page.wait_for_timeout(1000)
            context.close(); browser.close()


if __name__ == "__main__":
    main()
