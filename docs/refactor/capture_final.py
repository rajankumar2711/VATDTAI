"""
Final capture: scope strictly to the Reports card, commit Report Type + Entity via
the real widgets, verify the hidden native <select> values actually change, set the
date, then Generate and capture the report iframe (#smartstreamlitViewer).

Run:  python docs/refactor/capture_final.py
Output: docs/refactor/report_final_dump.txt
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

OUT = Path(__file__).resolve().parent / "report_final_dump.txt"
_lines = []


def emit(title, payload):
    block = f"\n{'='*80}\n{title}\n{'='*80}\n"
    block += json.dumps(payload, indent=2, ensure_ascii=False) if isinstance(payload, (dict, list)) else str(payload)
    _lines.append(block)
    print(block)


# Snapshot the committed state the app's validator likely reads.
STATE_JS = r"""
() => {
    const norm = v => (v||'').replace(/\s+/g,' ').trim();
    const rep = document.getElementById('vatdtai_reports_select');
    // reports card = nearest ancestor containing the Generate button
    let card = rep; while (card && card.parentElement) { card = card.parentElement;
        if (Array.from(card.querySelectorAll('button')).some(b => norm(b.innerText)==='Generate')) break; }
    const combos = Array.from(card.querySelectorAll('input.textinput-group__textinput'));
    const gen = Array.from(card.querySelectorAll('button')).find(b => norm(b.innerText)==='Generate');
    const nativeByDataId = (di) => { const s = card.querySelector(`select[id="${di}"]`) || document.getElementById(di); return s ? s.value : '(select not found)'; };
    return {
        reportSelectValue: rep ? rep.value : null,
        combos: combos.map(c => ({id:c.id, disabled:c.disabled, value:c.value, dataTitle:c.getAttribute('data-title')||'', dataId:c.getAttribute('data-id')||'', nativeValue: nativeByDataId(c.getAttribute('data-id'))})),
        date: (document.getElementById('vatdtai_reports_date')||{}).value || '',
        dateFrom: (document.getElementById('vatdtai_reports_date_from')||{}).value || '',
        dateTo: (document.getElementById('vatdtai_reports_date_to')||{}).value || '',
        generateDisabled: gen ? !!gen.disabled : null
    };
}
"""


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

            emit("STATE @ default", page.evaluate(STATE_JS))

            page.select_option("#vatdtai_reports_select", label="Invoice Status Report")
            page.wait_for_timeout(1500)
            emit("STATE @ after report type", page.evaluate(STATE_JS))

            # Reports card locator via the report select ancestor holding Generate.
            card = page.locator("xpath=//select[@id='vatdtai_reports_select']/ancestor::*[.//button[normalize-space()='Generate']][1]")
            gen = card.locator("button.btn-primary", has_text="Generate").first

            # Entity combobox = the ENABLED textinput within the card (Country is disabled).
            entity = card.locator("input.textinput-group__textinput:not([disabled])").first
            emit("ENTITY LOCATOR", {"count": entity.count(),
                                    "value": entity.get_attribute("data-title") if entity.count() else None})
            entity.click()
            page.wait_for_timeout(800)
            # The open menu is a .dropdown-menu; pick 'All' scoped to a visible menu.
            all_opt = page.locator("ul.dropdown-menu:visible li, .dropdown-menu:visible li", has_text="All").first
            emit("ENTITY MENU 'All' option", {"count": all_opt.count()})
            if all_opt.count():
                all_opt.click()
            page.wait_for_timeout(1000)
            emit("STATE @ after entity commit", page.evaluate(STATE_JS))

            # Date range.
            page.fill("#vatdtai_reports_date_from", "2025-01-01")
            page.fill("#vatdtai_reports_date_to", "2026-10-10")
            page.wait_for_timeout(1200)
            emit("STATE @ after date range", page.evaluate(STATE_JS))

            # Also try the single date field in case range isn't the trigger.
            if page.evaluate(STATE_JS).get("generateDisabled"):
                page.fill("#vatdtai_reports_date", "2025-06-15")
                page.wait_for_timeout(1200)
                emit("STATE @ after single date too", page.evaluate(STATE_JS))

            if gen.count() and gen.is_enabled():
                gen.click()
                emit("GENERATE", "clicked")
                page.wait_for_timeout(7000)
                fr = next((f for f in page.frames if f.name == "smartstreamlitViewer"), None)
                emit("STREAMLIT IFRAME URL", fr.url if fr else "(none)")
                if fr and fr.url and fr.url != "about:blank":
                    emit("STREAMLIT REPORT CONTENT", fr.evaluate(r"""() => {
                        const norm = v => (v||'').replace(/\s+/g,' ').trim();
                        const headers = Array.from(document.querySelectorAll('table th,[role="columnheader"],.tabulator-col-title,thead td')).map(h=>norm(h.innerText)).filter(Boolean);
                        const buttons = Array.from(document.querySelectorAll('button,a[download],[data-testid],[title],[aria-label]')).map(b=>({text:norm(b.innerText),title:b.getAttribute('title')||'',testid:b.getAttribute('data-testid')||'',aria:b.getAttribute('aria-label')||'',download:b.getAttribute('download')||''})).filter(b=>b.text||b.title||b.testid||b.download||b.aria).slice(0,50);
                        return {headers, buttons, text: norm(document.body.innerText).slice(0,3000)};
                    }"""))
                else:
                    emit("TOP MODAL", page.evaluate(r"""() => { const norm=v=>(v||'').replace(/\s+/g,' ').trim(); const m=document.querySelector('div.modal-dialog,[role=dialog]'); return m?norm(m.innerText).slice(0,400):'(none)'; }"""))
            else:
                emit("RESULT", "Generate still disabled - see STATE snapshots for which field the validator is not accepting")
        except Exception:
            import traceback
            emit("FATAL", traceback.format_exc())
        finally:
            OUT.write_text("\n".join(_lines), encoding="utf-8")
            print(f"\n\nDump written to: {OUT}")
            page.wait_for_timeout(1500)
            context.close(); browser.close()


if __name__ == "__main__":
    main()
