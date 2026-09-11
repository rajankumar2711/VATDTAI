"""
Capture the GENERATED report output that renders inside the #smartstreamlitViewer
iframe: metadata, column headers, export controls, close control.

Run:  python docs/refactor/capture_report_generate.py
Output: docs/refactor/report_generated_dump.txt
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

OUT = Path(__file__).resolve().parent / "report_generated_dump.txt"
_lines = []


def emit(title, payload):
    block = f"\n{'='*80}\n{title}\n{'='*80}\n"
    block += json.dumps(payload, indent=2, ensure_ascii=False) if isinstance(payload, (dict, list)) else str(payload)
    _lines.append(block)
    print(block)


SET_FORM_JS = r"""
(args) => {
    const fire = (el, ev) => el && el.dispatchEvent(new Event(ev, {bubbles:true}));
    const sel = document.getElementById('vatdtai_reports_select');
    let ok = false;
    if (sel) {
        const opt = Array.from(sel.options).find(o => (o.text||'').trim() === args.report);
        if (opt) { sel.value = opt.value; fire(sel,'change'); if (window.$) window.$(sel).trigger('change'); ok = true; }
    }
    const setDate = (id, val) => { const d = document.getElementById(id); if (d){ d.value = val; fire(d,'input'); fire(d,'change'); } };
    setDate('vatdtai_reports_date_from', args.from);
    setDate('vatdtai_reports_date_to', args.to);
    return {ok, reportValue: sel ? sel.value : null};
}
"""

FRAME_REPORT_JS = r"""
() => {
    const norm = v => (v || '').replace(/\s+/g,' ').trim();
    const headers = Array.from(document.querySelectorAll(
        'table thead th, table th, [role="columnheader"], .tabulator .tabulator-col-title, [data-testid="stTable"] th'
    )).map(h => norm(h.innerText||h.textContent)).filter(Boolean);
    const buttons = Array.from(document.querySelectorAll('button, a, [role="button"], [download], [data-testid]'))
        .map(b => ({text:norm(b.innerText||b.textContent), id:b.id, class:b.className,
                    testid:b.getAttribute('data-testid')||'', title:b.getAttribute('title')||'',
                    href:b.getAttribute('href')||'', download:b.getAttribute('download')||''}))
        .filter(b => b.text || b.testid || b.title || b.download);
    return {url: location.href, headers, buttons, text: norm(document.body ? document.body.innerText : '').slice(0,3000)};
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

            gen = page.locator("button.btn-primary:has-text('Generate')").first

            def gen_state(tag):
                st = {"count": gen.count(), "enabled": gen.is_enabled() if gen.count() else None}
                emit(f"GENERATE BUTTON [{tag}]", st)
                return st.get("enabled")

            # Native select of report type.
            try:
                page.select_option("#vatdtai_reports_select", label="Invoice Status Report")
            except Exception as exc:
                emit("select_option WARN", str(exc))
            page.wait_for_timeout(1200)
            gen_state("after report type")

            # Resolve the reports Country/Entity typeahead combobox input ids by walking up
            # from #vatdtai_reports_select to the card that also holds the Generate button.
            ids = page.evaluate(r"""() => {
                const norm = v => (v||'').replace(/\s+/g,' ').trim();
                let card = document.getElementById('vatdtai_reports_select');
                while (card && card.parentElement) {
                    card = card.parentElement;
                    const hasGen = Array.from(card.querySelectorAll('button')).some(b => norm(b.innerText)==='Generate');
                    const combos = card.querySelectorAll('input.textinput-group__textinput, input[role="combobox"]');
                    if (hasGen && combos.length >= 2) break;
                }
                if (!card) return {error:'card not found'};
                const combos = Array.from(card.querySelectorAll('input.textinput-group__textinput, input[role="combobox"]'));
                return {
                    combos: combos.map(c => ({id:c.id, class:c.className, value:c.value,
                        label: (() => { const g=c.closest('div'); const l=g?g.querySelector('label'):null; return l?norm(l.innerText):''; })()}))
                };
            }""")
            emit("REPORTS CARD COMBOBOXES (order = Country, Entity)", ids)

            combos = ids.get("combos", []) if isinstance(ids, dict) else []
            country_id = combos[0]["id"] if len(combos) > 0 else None
            entity_id = combos[1]["id"] if len(combos) > 1 else None
            emit("RESOLVED IDS", {"country_id": country_id, "entity_id": entity_id})

            def open_and_dump_listbox(input_id, tag):
                if not input_id:
                    emit(f"LISTBOX [{tag}]", "no input id")
                    return
                page.locator(f"#{input_id}").click()
                page.wait_for_timeout(900)
                lb = page.evaluate(r"""() => {
                    const norm = v => (v||'').replace(/\s+/g,' ').trim();
                    const list = document.querySelector('ul[role="listbox"], .textinput-group__list, [role="listbox"]');
                    if (!list) return {found:false};
                    const items = Array.from(list.querySelectorAll('li, [role="option"]')).slice(0,15)
                        .map(li => ({text:norm(li.innerText), class:li.className, role:li.getAttribute('role')||''}));
                    return {found:true, listClass:list.className, itemCount:list.querySelectorAll('li,[role=option]').length, sample:items};
                }""")
                emit(f"LISTBOX [{tag}]", lb)

            # Explicitly (re)select Entity = All via the dropdown.
            open_and_dump_listbox(entity_id, "Entity dropdown opened")
            entity_pick = page.evaluate(r"""() => {
                const norm = v => (v||'').replace(/\s+/g,' ').trim();
                const list = document.querySelector('ul[role="listbox"], .textinput-group__list, [role="listbox"]');
                if (!list) return {ok:false};
                const opt = Array.from(list.querySelectorAll('li,[role="option"]')).find(li => norm(li.innerText).toLowerCase()==='all');
                if (opt) { opt.click(); return {ok:true, clicked:norm(opt.innerText)}; }
                return {ok:false};
            }""")
            emit("ENTITY SELECT 'All'", entity_pick)
            page.wait_for_timeout(1000)
            gen_state("after explicit Entity=All")

            # Date: single field first, then range fallback.
            try:
                page.fill("#vatdtai_reports_date", "2025-06-15")
            except Exception as exc:
                emit("fill single date WARN", str(exc))
            page.wait_for_timeout(1000)
            if not gen_state("after single date"):
                try:
                    page.fill("#vatdtai_reports_date", "")
                    page.fill("#vatdtai_reports_date_from", "2025-01-01")
                    page.fill("#vatdtai_reports_date_to", "2026-10-10")
                except Exception as exc:
                    emit("fill range WARN", str(exc))
                page.wait_for_timeout(1000)
                gen_state("after date range")

            if gen.count() and gen.is_enabled():
                gen.click(force=True)
                emit("GENERATE", "clicked")
            else:
                emit("WARN", "Generate still not enabled; capturing current state anyway")
            page.wait_for_timeout(5000)

            # Poll for the streamlit viewer iframe to load a real document.
            loaded_url = "about:blank"
            for _ in range(30):
                fr = next((f for f in page.frames if f.name == "smartstreamlitViewer"), None)
                if fr and fr.url and fr.url != "about:blank":
                    loaded_url = fr.url
                    break
                page.wait_for_timeout(1000)
            emit("STREAMLIT IFRAME URL", loaded_url)

            # Top-level modal (e.g. 'not configured') if any.
            emit("TOP-LEVEL MODAL", page.evaluate(r"""() => {
                const norm = v => (v||'').replace(/\s+/g,' ').trim();
                const m = document.querySelector('div.modal-dialog, [role=dialog], div.customAlertoverlay');
                return m ? norm(m.innerText).slice(0,600) : '(no modal)';
            }"""))

            # Dump each frame's report content.
            for fr in page.frames:
                try:
                    data = fr.evaluate(FRAME_REPORT_JS)
                except Exception as exc:
                    data = {"error": str(exc), "url": fr.url}
                data["_frame_name"] = fr.name
                emit(f"FRAME REPORT DUMP name='{fr.name or '(main)'}'", data)

            emit("OPEN TABS", [p.url for p in context.pages])
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
