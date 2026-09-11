"""
Focused probe (v2): the Reports Country/Entity typeahead <input> is disabled
(display-only). Discover the real clickable toggle + option-list structure for
the Entity control, commit Entity=All, and check whether Generate enables.

Run:  python docs/refactor/capture_entity_dropdown.py
Output: docs/refactor/report_entity_dump.txt
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

OUT = Path(__file__).resolve().parent / "report_entity_dump.txt"
_lines = []


def emit(title, payload):
    block = f"\n{'='*80}\n{title}\n{'='*80}\n"
    block += json.dumps(payload, indent=2, ensure_ascii=False) if isinstance(payload, (dict, list)) else str(payload)
    _lines.append(block)
    print(block)


# Resolve the reports Country/Entity combobox inputs AND describe their container.
DESCRIBE_JS = r"""
() => {
    const norm = v => (v||'').replace(/\s+/g,' ').trim();
    let card = document.getElementById('vatdtai_reports_select');
    while (card && card.parentElement) {
        card = card.parentElement;
        const hasGen = Array.from(card.querySelectorAll('button')).some(b => norm(b.innerText)==='Generate');
        const combos = card.querySelectorAll('input.textinput-group__textinput, input[role="combobox"]');
        if (hasGen && combos.length >= 2) break;
    }
    const combos = Array.from(card.querySelectorAll('input.textinput-group__textinput, input[role="combobox"]'));
    const describe = (inp) => {
        // climb to the textinput-group wrapper
        let grp = inp;
        for (let i=0;i<5 && grp;i++){ if ((grp.className||'').includes('textinput-group')) break; grp = grp.parentElement; }
        const wrapper = grp || inp.parentElement;
        return {
            inputId: inp.id, disabled: inp.disabled, value: inp.value,
            dataTitle: inp.getAttribute('data-title')||'', dataId: inp.getAttribute('data-id')||'',
            ariaExpanded: inp.getAttribute('aria-expanded')||'',
            wrapperClass: wrapper ? wrapper.className : '',
            wrapperTag: wrapper ? wrapper.tagName : '',
            wrapperButtons: wrapper ? Array.from(wrapper.querySelectorAll('button,[class*="button"],svg,[class*="chevron"],[class*="icon"]'))
                .map(b => ({tag:b.tagName, class:b.className, aria:b.getAttribute('aria-label')||''})).slice(0,6) : [],
            wrapperHTML: wrapper ? wrapper.outerHTML.slice(0, 1600) : ''
        };
    };
    return combos.map(describe);
}
"""

MENU_DUMP_JS = r"""
() => {
    const norm = v => (v||'').replace(/\s+/g,' ').trim();
    const vis = el => { try { const s=getComputedStyle(el); return s.display!=='none'&&s.visibility!=='hidden'&&el.offsetParent!==null; } catch(e){ return false; } };
    const sels = ['[role="option"]','ul[role="listbox"] li','.textinput-group__list li','.textinput-group__list-item',
                  '[class*="list-box__menu-item"]','[class*="menu-item"]','.dropdown-menu li'];
    const seen = new Set(); const out = [];
    for (const sel of sels) {
        for (const el of document.querySelectorAll(sel)) {
            if (!vis(el)) continue;
            const key = norm(el.innerText)+'|'+el.className;
            if (seen.has(key)) continue; seen.add(key);
            out.push({sel, tag:el.tagName, role:el.getAttribute('role')||'', class:el.className, text:norm(el.innerText).slice(0,50)});
            if (out.length>=20) return out;
        }
    }
    return out;
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
            page.select_option("#vatdtai_reports_select", label="Invoice Status Report")
            page.wait_for_timeout(1200)

            desc = page.evaluate(DESCRIBE_JS)
            emit("COMBOBOX DESCRIPTIONS [0]=Country [1]=Entity", desc)

            gen = page.locator("button.btn-primary:has-text('Generate')").first
            entity_id = desc[1]["inputId"] if len(desc) > 1 else None

            if entity_id:
                # The input is likely disabled; click its wrapper to open the menu.
                wrapper = page.locator(f"#{entity_id}").locator(
                    "xpath=ancestor-or-self::*[contains(@class,'textinput-group')][1]")
                try:
                    wrapper.click(force=True)
                except Exception as exc:
                    emit("wrapper click WARN", str(exc))
                page.wait_for_timeout(800)
                emit("MENU after wrapper click", page.evaluate(MENU_DUMP_JS))

                # Fallback: click any chevron/button inside the wrapper.
                if not page.evaluate(MENU_DUMP_JS):
                    try:
                        wrapper.locator("button, svg, [class*='chevron'], [class*='icon']").first.click(force=True)
                        page.wait_for_timeout(800)
                    except Exception as exc:
                        emit("chevron click WARN", str(exc))
                    emit("MENU after chevron click", page.evaluate(MENU_DUMP_JS))

                # Click the 'All' option anywhere visible.
                picked = page.evaluate(r"""() => {
                    const norm = v => (v||'').replace(/\s+/g,' ').trim();
                    const vis = el => { try { const s=getComputedStyle(el); return s.display!=='none'&&s.visibility!=='hidden'&&el.offsetParent!==null; } catch(e){ return false; } };
                    const cands = Array.from(document.querySelectorAll('[role="option"], li, [class*="item"]'))
                        .filter(vis).filter(el => norm(el.innerText).toLowerCase()==='all');
                    if (cands.length){ cands[0].click(); return {ok:true, class:cands[0].className, tag:cands[0].tagName}; }
                    return {ok:false};
                }""")
                emit("ENTITY pick 'All'", picked)
                page.wait_for_timeout(1000)
                emit("GENERATE after Entity commit", {"enabled": gen.is_enabled() if gen.count() else None})

            # Dates then generate check.
            page.fill("#vatdtai_reports_date_from", "2025-01-01")
            page.fill("#vatdtai_reports_date_to", "2026-10-10")
            page.wait_for_timeout(1000)
            emit("GENERATE after dates", {"enabled": gen.is_enabled() if gen.count() else None})

            if gen.count() and gen.is_enabled():
                gen.click(force=True)
                emit("GENERATE", "clicked")
                page.wait_for_timeout(6000)
                fr = next((f for f in page.frames if f.name == "smartstreamlitViewer"), None)
                emit("STREAMLIT IFRAME URL", fr.url if fr else "(none)")
                if fr and fr.url and fr.url != "about:blank":
                    emit("STREAMLIT REPORT CONTENT", fr.evaluate(r"""() => {
                        const norm = v => (v||'').replace(/\s+/g,' ').trim();
                        const headers = Array.from(document.querySelectorAll('table th,[role="columnheader"],.tabulator-col-title')).map(h=>norm(h.innerText)).filter(Boolean);
                        const buttons = Array.from(document.querySelectorAll('button,a[download],[data-testid],[title]')).map(b=>({text:norm(b.innerText),title:b.getAttribute('title')||'',testid:b.getAttribute('data-testid')||'',download:b.getAttribute('download')||''})).filter(b=>b.text||b.title||b.testid||b.download).slice(0,40);
                        return {headers, buttons, text: norm(document.body.innerText).slice(0,2500)};
                    }"""))
            else:
                emit("RESULT", "Generate still disabled after Entity commit + dates")
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
