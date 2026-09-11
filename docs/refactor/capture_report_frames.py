"""
Deeper discovery: enumerate DTAI module tabs, dump every frame (incl. the
Streamlit report iframe), dismiss the 'not configured' modal, and re-inspect.

Run:  python docs/refactor/capture_report_frames.py
Output: docs/refactor/report_frames_dump.txt
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
    perform_login,
    perform_client_selection,
    perform_dtai_navigation,
    dismiss_application_popup,
)

OUT = Path(__file__).resolve().parent / "report_frames_dump.txt"
_lines = []


def emit(title, payload):
    block = f"\n{'='*80}\n{title}\n{'='*80}\n"
    block += json.dumps(payload, indent=2, ensure_ascii=False) if isinstance(payload, (dict, list)) else str(payload)
    _lines.append(block)
    print(block)


FRAME_DUMP_JS = r"""
() => {
    const norm = v => (v || '').replace(/\s+/g, ' ').trim();
    const visible = (el) => {
        try { const s = getComputedStyle(el); return s.display!=='none' && s.visibility!=='hidden' && el.offsetParent!==null; }
        catch(e){ return false; }
    };
    const selects = Array.from(document.querySelectorAll('select')).map(s => ({
        id:s.id, name:s.name, class:s.className, visible:visible(s),
        options: Array.from(s.options).map(o => norm(o.text))
    }));
    const inputs = Array.from(document.querySelectorAll('input,[role="combobox"],[data-baseweb="select"]')).map(i => ({
        id:i.id, name:i.name, type:i.getAttribute('type')||i.tagName, class:i.className,
        placeholder:i.getAttribute('placeholder')||'', ariaLabel:i.getAttribute('aria-label')||'',
        role:i.getAttribute('role')||'', value:i.value||'', visible:visible(i)
    }));
    const buttons = Array.from(document.querySelectorAll('button,a.btn,[role="button"],[data-testid]')).map(b => ({
        text:norm(b.innerText||b.textContent), id:b.id, class:b.className,
        testid:b.getAttribute('data-testid')||'', title:b.getAttribute('title')||'',
        ariaLabel:b.getAttribute('aria-label')||'', disabled:!!b.disabled
    })).filter(b => b.text || b.testid || b.title || b.ariaLabel);
    const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,label')).map(h => norm(h.innerText)).filter(Boolean).slice(0,40);
    return {url: location.href, headings, selects, inputs, buttons, bodyText: norm(document.body ? document.body.innerText : '').slice(0,1200)};
}
"""


def dump_all_frames(page, tag):
    frames_info = []
    for fr in page.frames:
        try:
            data = fr.evaluate(FRAME_DUMP_JS)
        except Exception as exc:
            data = {"error": str(exc), "url": fr.url, "name": fr.name}
        data["_frame_name"] = fr.name
        frames_info.append(data)
    emit(f"FRAMES DUMP [{tag}] (count={len(page.frames)})", frames_info)


def main():
    Read_Configurations.initialize("qa")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=False, args=["--start-maximized"])
        context = browser.new_context(no_viewport=True, accept_downloads=True)
        page = context.new_page()
        try:
            launch_page = perform_login(page, role="Admin")
            perform_client_selection(page, launch_page, "Client Belgium")
            perform_dtai_navigation(page, launch_page)
            dismiss_application_popup(page)

            # Enumerate all module tabs / nav links at top level.
            tabs = page.evaluate(r"""() => {
                const norm = v => (v || '').replace(/\s+/g,' ').trim();
                const roleTabs = Array.from(document.querySelectorAll('[role="tab"]')).map(t => norm(t.innerText));
                const navLinks = Array.from(document.querySelectorAll('a')).map(a => norm(a.innerText)).filter(Boolean);
                return {roleTabs, navLinks: Array.from(new Set(navLinks)).slice(0,60)};
            }""")
            emit("DTAI MODULE TABS + NAV LINKS", tabs)

            # Click the Reports tab specifically (role=tab preferred).
            clicked = False
            for sel in ["role=tab[name='Reports' i]", "a:has-text('Reports')", "[role='tab']:has-text('Reports')"]:
                try:
                    loc = page.locator(sel).first
                    if loc.count() > 0 and loc.is_visible(timeout=1500):
                        loc.click(force=True)
                        clicked = sel
                        break
                except Exception:
                    continue
            emit("REPORTS TAB CLICK", {"clicked_selector": clicked})
            page.wait_for_timeout(4000)

            dump_all_frames(page, "after Reports click (modal may be present)")

            # Dismiss any 'not configured' / analytics modal, then re-inspect.
            for sel in ["div.modal-scrollable button:has-text('OK')", "button.btn-default:has-text('OK')",
                        "[role='dialog'] button:has-text('OK')", "button:has-text('OK')"]:
                try:
                    b = page.locator(sel).first
                    if b.count() > 0 and b.is_visible(timeout=1200):
                        b.click(force=True)
                        page.wait_for_timeout(800)
                except Exception:
                    continue
            page.wait_for_timeout(2500)
            emit("MODAL TEXT SNAPSHOT (top-level)", page.evaluate(r"""() => {
                const norm = v => (v || '').replace(/\s+/g,' ').trim();
                const m = document.querySelector('div.modal-dialog, [role=dialog], div.customAlertoverlay');
                return m ? norm(m.innerText).slice(0,500) : '(no modal)';
            }"""))
            dump_all_frames(page, "after dismissing modal")

        except Exception:
            import traceback
            emit("FATAL ERROR", traceback.format_exc())
        finally:
            OUT.write_text("\n".join(_lines), encoding="utf-8")
            print(f"\n\nDump written to: {OUT}")
            page.wait_for_timeout(1000)
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
