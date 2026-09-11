"""
Focused probe for Submission Report: why does Generate not enable? Dump every form control
in the reports card after selecting the type + platform, snapshot committed state after each
step, and try to enable Generate. Also wait properly for the report window to finish loading.

Run:  python docs/refactor/capture_submission.py
Output: docs/refactor/submission_dump.txt
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

OUT = Path(__file__).resolve().parent / "submission_dump.txt"
_lines = []


def emit(title, payload):
    block = f"\n{'='*80}\n{title}\n{'='*80}\n"
    block += json.dumps(payload, indent=2, ensure_ascii=False) if isinstance(payload, (dict, list)) else str(payload)
    _lines.append(block)
    print(block)


# Dump every control inside the reports card + Generate state.
DUMP_JS = r"""
() => {
    const norm = v => (v || '').replace(/\s+/g, ' ').trim();
    const vis = el => { try { const s=getComputedStyle(el); return s.display!=='none'&&s.visibility!=='hidden'&&el.offsetParent!==null; } catch(e){ return false; } };
    const rep = document.getElementById('vatdtai_reports_select');
    let card = rep; while (card && card.parentElement) { card = card.parentElement;
        if (Array.from(card.querySelectorAll('button')).some(b => norm(b.innerText)==='Generate')) break; }
    if (!card) return {error:'no card'};
    const gen = Array.from(card.querySelectorAll('button')).find(b => norm(b.innerText)==='Generate');

    const selects = Array.from(card.querySelectorAll('select')).map(s => ({
        id:s.id, visible:vis(s), value:s.value,
        selectedText: s.selectedOptions.length ? norm(s.selectedOptions[0].text) : '',
        options: Array.from(s.options).map(o=>norm(o.text)).slice(0,12)
    }));
    const combos = Array.from(card.querySelectorAll('input.textinput-group__textinput')).map(c => ({
        id:c.id, visible:vis(c), disabled:c.disabled, dataTitle:c.getAttribute('data-title')||'',
        dataId:c.getAttribute('data-id')||'', nativeValue: (document.getElementById(c.getAttribute('data-id'))||{}).value || ''
    }));
    // any visible date inputs in the card
    const dates = Array.from(card.querySelectorAll('input[type="date"], input[id*="date" i]')).map(d => ({
        id:d.id, type:d.type, visible:vis(d), value:d.value
    }));
    // any other required-looking inputs
    const otherInputs = Array.from(card.querySelectorAll('input:not(.textinput-group__textinput)')).map(i => ({
        id:i.id, type:i.type, visible:vis(i), value:i.value, placeholder:i.placeholder||''
    })).filter(i => i.visible).slice(0, 15);
    // visible field labels for context
    const labels = Array.from(card.querySelectorAll('label')).map(l=>norm(l.innerText)).filter(Boolean).slice(0,20);

    return {
        reportValue: rep.value, generateDisabled: gen ? !!gen.disabled : null,
        selects, combos, dates, otherInputs, labels
    };
}
"""


def commit_entity(page, card):
    try:
        entity = card.locator("input.textinput-group__textinput:not([disabled])").first
        entity.click()
        page.wait_for_timeout(700)
        all_opt = page.locator("ul.dropdown-menu:visible li, .dropdown-menu:visible li", has_text="All").first
        if all_opt.count():
            all_opt.click()
        page.wait_for_timeout(700)
        return True
    except Exception:
        return False


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
            # Robust navigation: retry until the reports select is actually visible.
            for attempt in range(5):
                for sel in ["role=tab[name='Reports' i]", "a:has-text('Reports')", "text=Reports"]:
                    loc = page.locator(sel).first
                    if loc.count() > 0 and loc.is_visible(timeout=1500):
                        loc.click(force=True)
                        break
                page.wait_for_timeout(2000)
                rs = page.locator("#vatdtai_reports_select").first
                if rs.count() and rs.is_visible():
                    break
                emit(f"NAV retry {attempt+1}", "reports select not visible yet")
            page.wait_for_selector("#vatdtai_reports_select", state="visible", timeout=20000)

            page.select_option("#vatdtai_reports_select", label="Submission Report")
            page.wait_for_timeout(1500)
            emit("AFTER select Submission Report", page.evaluate(DUMP_JS))

            # Dump the platform control's real structure (native select vs custom combobox).
            emit("PLATFORM CONTROL STRUCTURE", page.evaluate(r"""() => {
                const norm = v => (v||'').replace(/\s+/g,' ').trim();
                const sel = document.getElementById('vatdtai_platform_select');
                const out = {nativeSelect:null, comboNearby:[]};
                if (sel) {
                    const st = getComputedStyle(sel);
                    out.nativeSelect = {
                        id:sel.id, tag:sel.tagName,
                        visible: st.display!=='none'&&st.visibility!=='hidden'&&sel.offsetParent!==null,
                        display: st.display, value: sel.value,
                        options: Array.from(sel.options).map(o=>norm(o.text)),
                        outerStart: sel.outerHTML.slice(0,300)
                    };
                    // look at siblings/parent for a visible custom widget bound to platform
                    let p = sel.parentElement;
                    for (let i=0;i<3 && p;i++){
                        const combos = Array.from(p.querySelectorAll('input.textinput-group__textinput, input[role="combobox"], .dropdown-toggle, button'))
                            .map(c=>({tag:c.tagName, id:c.id||'', cls:c.className, dataTitle:c.getAttribute&&c.getAttribute('data-title')||'', text:norm(c.innerText||c.value||'')}));
                        if (combos.length) out.comboNearby.push({level:i, parentCls:p.className, combos: combos.slice(0,8)});
                        p = p.parentElement;
                    }
                }
                return out;
            }"""))

            card = page.locator(
                "xpath=//select[@id='vatdtai_reports_select']/ancestor::*[.//button[normalize-space()='Generate']][1]")

            # select platform GTES
            try:
                page.select_option("#vatdtai_platform_select", label="GTES")
            except Exception as e:
                emit("platform select WARN", str(e))
            page.wait_for_timeout(1000)
            emit("AFTER platform=GTES", page.evaluate(DUMP_JS))

            commit_entity(page, card)
            emit("AFTER entity=All", page.evaluate(DUMP_JS))

            # try date range
            for did, val in [("vatdtai_reports_date_from", "2025-01-01"),
                             ("vatdtai_reports_date_to", "2026-10-10"),
                             ("vatdtai_reports_date", "2025-06-15")]:
                try:
                    el = page.locator(f"#{did}")
                    if el.count() and el.first.is_visible():
                        el.first.fill(val)
                except Exception:
                    pass
            page.wait_for_timeout(1000)
            emit("AFTER dates (range + single)", page.evaluate(DUMP_JS))

            gen = card.locator("button.btn-primary", has_text="Generate").first
            if gen.count() and gen.is_enabled():
                new_page = None
                try:
                    with context.expect_page(timeout=9000) as pi:
                        gen.click()
                    new_page = pi.value
                    new_page.wait_for_load_state("load", timeout=15000)
                    # WAIT for the report to finish loading (loading placeholder -> real content)
                    try:
                        new_page.wait_for_selector(".vatdtai-report-window, table.vatdtai-report-table",
                                                   timeout=20000)
                    except PWTimeout:
                        pass
                    new_page.wait_for_timeout(1500)
                    info = new_page.evaluate(r"""() => {
                        const norm = v => (v||'').replace(/\s+/g,' ').trim();
                        return {
                            title: norm((document.querySelector('.vatdtai-report-title')||{}).innerText || document.title),
                            meta: Array.from(document.querySelectorAll('.vatdtai-report-meta')).map(m=>norm(m.innerText)),
                            columns: Array.from(document.querySelectorAll('table.vatdtai-report-table thead th')).map(t=>norm(t.innerText)),
                            rowCount: document.querySelectorAll('table.vatdtai-report-table tbody tr').length,
                            exportItems: Array.from(document.querySelectorAll('[data-export]')).map(b=>b.getAttribute('data-export')),
                            bodyLen: document.documentElement.outerHTML.length
                        };
                    }""")
                    emit("SUBMISSION WINDOW", info)
                    Path(OUT.parent / "all_reports_dump").mkdir(parents=True, exist_ok=True)
                    (OUT.parent / "all_reports_dump" / "Submission_Report.html").write_text(
                        new_page.content(), encoding="utf-8")
                except PWTimeout:
                    emit("SUBMISSION", "Generate clicked but no new window")
                finally:
                    if new_page:
                        new_page.close(); page.bring_to_front()
            else:
                emit("RESULT", "Submission Generate still disabled - inspect DUMP snapshots above")
        except Exception:
            import traceback
            emit("FATAL", traceback.format_exc())
        finally:
            OUT.write_text("\n".join(_lines), encoding="utf-8")
            print(f"\n\nDump: {OUT}")
            page.wait_for_timeout(1500)
            context.close(); browser.close()


if __name__ == "__main__":
    main()
