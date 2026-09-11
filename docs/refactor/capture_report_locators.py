"""
One-off discovery helper (NOT a test): launches the QA app, navigates to the
Reports module, and dumps the real DOM for every field the Reports automation
needs (report-type select, country/entity inputs, date fields, Submission
Platform select, Generate button, generated-report container, metadata, column
headers, close + export controls).

Run:  python docs/refactor/capture_report_locators.py
Output: docs/refactor/report_locators_dump.txt  (also echoed to stdout)
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
from pageobjects.vat_reports_page import VatReportsPage  # noqa: E402

OUT = Path(__file__).resolve().parent / "report_locators_dump.txt"
_lines = []


def emit(title, payload):
    block = f"\n{'='*80}\n{title}\n{'='*80}\n"
    if isinstance(payload, (dict, list)):
        block += json.dumps(payload, indent=2, ensure_ascii=False)
    else:
        block += str(payload)
    _lines.append(block)
    print(block)


# JS: describe every interactive field within the active Reports pane.
PANE_DUMP_JS = r"""
() => {
    const norm = v => (v || '').replace(/\s+/g, ' ').trim();
    const panes = Array.from(document.querySelectorAll('div.tab-pane'));
    const pane = panes.find(p => (p.className || '').includes('active') &&
        ((p.innerText || '').includes('Generate Report') || (p.innerText || '').includes('Reports')))
        || document.querySelector('div.tab-pane.active') || document.body;

    const labelFor = (el) => {
        // nearest preceding label / group label text
        let t = '';
        if (el.id) {
            const lbl = pane.querySelector(`label[for="${el.id}"]`);
            if (lbl) t = norm(lbl.innerText);
        }
        if (!t) {
            const grp = el.closest('div');
            if (grp) {
                const lbl = grp.querySelector('label');
                if (lbl) t = norm(lbl.innerText);
            }
        }
        return t;
    };
    const visible = (el) => {
        const s = window.getComputedStyle(el);
        return s.display !== 'none' && s.visibility !== 'hidden' && el.offsetParent !== null;
    };

    const headings = Array.from(pane.querySelectorAll('h1,h2,h3,h4')).map(h => norm(h.innerText)).filter(Boolean);

    const selects = Array.from(pane.querySelectorAll('select')).map(s => ({
        id: s.id, name: s.name, class: s.className, visible: visible(s),
        label: labelFor(s),
        options: Array.from(s.options).map(o => ({value: o.value, text: norm(o.text)}))
    }));

    const inputs = Array.from(pane.querySelectorAll('input')).map(i => ({
        id: i.id, name: i.name, type: i.type, class: i.className,
        placeholder: i.getAttribute('placeholder') || '',
        ariaLabel: i.getAttribute('aria-label') || '',
        value: i.value || '', visible: visible(i), label: labelFor(i)
    }));

    const buttons = Array.from(pane.querySelectorAll('button, a.btn, [role="button"]')).map(b => ({
        text: norm(b.innerText || b.textContent), id: b.id, class: b.className,
        title: b.getAttribute('title') || '', ariaLabel: b.getAttribute('aria-label') || '',
        disabled: !!b.disabled, visible: visible(b)
    })).filter(b => b.text || b.title || b.ariaLabel);

    return {headings, selects, inputs, buttons};
}
"""

# JS: describe the generated-report output (modal/dialog/iframe/table).
REPORT_DUMP_JS = r"""
() => {
    const norm = v => (v || '').replace(/\s+/g, ' ').trim();
    const scopes = [
        {name: 'modal-dialog', el: document.querySelector('div.modal-dialog')},
        {name: 'role=dialog', el: document.querySelector('[role="dialog"]')},
        {name: 'report-viewer', el: document.querySelector('.report-viewer, .report-container')},
        {name: 'active-pane', el: document.querySelector('div.tab-pane.active')},
    ].filter(s => s.el);

    const iframes = Array.from(document.querySelectorAll('iframe, embed, object')).map(f => ({
        tag: f.tagName, id: f.id, src: f.getAttribute('src') || f.getAttribute('data') || '',
        visible: window.getComputedStyle(f).display !== 'none'
    }));

    const out = {scopes: [], iframes, extraWindows: window.__extra || null};
    for (const s of scopes) {
        const el = s.el;
        const headers = Array.from(el.querySelectorAll(
            'table thead th, table th, .tabulator .tabulator-col-title'
        )).map(h => norm(h.innerText || h.textContent)).filter(Boolean);
        const buttons = Array.from(el.querySelectorAll('button, a.btn, [role="button"], .close, [aria-label]'))
            .map(b => ({
                text: norm(b.innerText || b.textContent), id: b.id, class: b.className,
                title: b.getAttribute('title') || '', ariaLabel: b.getAttribute('aria-label') || ''
            })).filter(b => b.text || b.title || b.ariaLabel || (b.class || '').includes('close'));
        out.scopes.push({
            scope: s.name,
            text: norm(el.innerText).slice(0, 1500),
            columnHeaders: headers,
            buttons
        });
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
            emit("STEP", "Login + client selection + DTAI navigation")
            launch_page = perform_login(page, role="Admin")
            perform_client_selection(page, launch_page, "Client Belgium")
            perform_dtai_navigation(page, launch_page)
            dismiss_application_popup(page)

            rp = VatReportsPage(page)
            emit("STEP", "Navigate to Reports module")
            rp.navigate_to_reports_module()
            page.wait_for_timeout(1500)

            emit("REPORTS HEADER", {
                "reports_module_visible": rp.is_reports_module_visible(),
                "header_text": rp.get_reports_header(),
                "generate_section_visible": rp.is_generate_report_section_visible(),
            })
            emit("REPORT TYPE OPTIONS (select#vatdtai_reports_select)", rp.get_report_options())
            emit("DEFAULT GENERATE PANE FIELDS", page.evaluate(PANE_DUMP_JS))

            # Reveal the Submission Platform field.
            emit("STEP", "Select 'Submission Report' to reveal Submission Platform field")
            rp.select_report_type("Submission Report", allow_fallback=False)
            page.wait_for_timeout(1200)
            emit("PANE FIELDS AFTER SELECTING SUBMISSION REPORT", page.evaluate(PANE_DUMP_JS))
            emit("SUBMISSION PLATFORM PROBE", {
                "visible": rp.is_submission_platform_visible(),
                "options": rp.get_submission_platform_options(),
            })

            # Generate an Invoice Status Report to capture output/metadata/columns/close/export.
            emit("STEP", "Select 'Invoice Status Report', fill valid criteria, Generate")
            rp.select_report_type("Invoice Status Report", allow_fallback=True)
            page.wait_for_timeout(800)
            rp.select_entity("ALL")
            rp.set_date_range("01/01/2025", "10/10/2026")
            emit("GENERATE BUTTON STATE (after valid criteria)", rp._generate_button_state())
            try:
                rp.click_generate_report()
            except Exception as exc:
                emit("GENERATE CLICK WARNING", str(exc))
            page.wait_for_timeout(2500)

            emit("REPORT OUTPUT / METADATA / COLUMNS / CONTROLS", page.evaluate(REPORT_DUMP_JS))
            emit("PARSED METADATA (current page-object logic)", rp.get_report_metadata())
            emit("COLUMN HEADERS (current page-object logic)", rp.get_report_column_headers())
            emit("OPEN TABS/PAGES", [p.url for p in context.pages])

        except Exception as exc:
            import traceback
            emit("FATAL ERROR", traceback.format_exc())
        finally:
            OUT.write_text("\n".join(_lines), encoding="utf-8")
            print(f"\n\nDump written to: {OUT}")
            page.wait_for_timeout(1500)
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
