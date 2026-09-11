"""One-off UAT exploration: launch gtpituat.ey.com, best-effort login, then wait
while the user completes MFA + client selection + navigation to the VAT DTAI
PowerBI dashboard, wait for the report to FULLY render, and dump:
  - page.html / every frame's DOM
  - iframes.json / frames.json
  - visuals.json      (each PowerBI visual: aria-label, title, text)
  - report_pages.json (PowerBI page/tab names, e.g. drill-through targets)
  - drillthrough.json (context-menu items from right-clicking the first card)
  - screenshots + locators_signals.json

Standalone on purpose: reads the UAT section of config.ini directly.
Run:  python docs/refactor/uat_capture_dashboard.py
"""

from __future__ import annotations

import json
import time
import configparser
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]  # .../Playwright_Python
SECTION = "GIDEI application details UAT"

cfg = configparser.RawConfigParser()
cfg.read(ROOT / "configuration" / "config.ini")
URL = cfg.get(SECTION, "VAT_DTAI_URL")
USER = cfg.get(SECTION, "VAT_DTAI_USERNAME")
PWD = cfg.get(SECTION, "VAT_DTAI_PASSWORD")
CHANNEL = cfg.get(SECTION, "channel", fallback="chrome")

OUT = ROOT / "reports" / "runs" / f"UAT_Capture_{datetime.now():%Y%m%d_%H%M%S}"
OUT.mkdir(parents=True, exist_ok=True)

WAIT_NAV_SECONDS = 420   # manual MFA + navigation window
WAIT_RENDER_SECONDS = 180  # PowerBI full render window


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def write(name: str, obj) -> None:
    (OUT / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def iframe_info(page):
    try:
        return page.eval_on_selector_all(
            "iframe",
            """els => els.map(e => ({src:e.src||'', id:e.id||'', name:e.name||'',
                title:e.title||'', cls:e.className||''}))""",
        )
    except Exception:
        return []


def powerbi_frame(page):
    for fr in page.frames:
        if "reportembed" in (fr.url or "").lower() or "app.powerbi" in (fr.url or "").lower():
            return fr
    return None


def _click_first(page, selectors, timeout=8000):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                loc.click(timeout=timeout)
                return sel
        except Exception:
            continue
    return None


def _wait_any_visible(page, selectors, timeout_s=60):
    """Poll each selector separately (mixing regex text= with CSS in one string breaks)."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    return sel
            except Exception:
                continue
        page.wait_for_timeout(1500)
    return None


def _select_ey_employee(page):
    """The EY SSO landing (/sso/) asks to choose account type before the MS login."""
    candidates = [
        "text=I am EY employee",
        "role=button[name=/EY employee/i]",
        "role=link[name=/EY employee/i]",
        "role=radio[name=/EY employee/i]",
        "button:has-text('EY employee')",
        "a:has-text('EY employee')",
        "text=/EY employee/i",
    ]
    clicked = _click_first(page, candidates, timeout=5000)
    if clicked:
        log(f"Selected 'I am EY employee' via {clicked}")
        page.wait_for_timeout(2500)
    return clicked


def best_effort_login(page):
    """Fill the Microsoft/EY SSO form using credentials from config.ini.
    Waits through the SAML/SSO redirects; MFA (if prompted) is completed by the user."""
    email_sel = "input[type='email'], input[name='loginfmt'], #i0116, input[type='text']:visible"

    # Handle the EY SSO account-type landing first: wait for either the
    # 'I am EY employee' option or the email field (whichever appears).
    ey_sel = "text=/EY employee/i"
    found = _wait_any_visible(page, [ey_sel, email_sel], timeout_s=60)
    if not found:
        log("Neither EY-employee option nor email field visible in 60s. Log in manually.")
        return
    try:
        (OUT / "sso_page.html").write_text(page.content(), encoding="utf-8")
    except Exception:
        pass
    _select_ey_employee(page)

    if not _wait_any_visible(page, [email_sel], timeout_s=45):
        log("Login email field not visible. Log in manually if needed.")
        return
    try:
        log("Entering username from config...")
        page.locator(email_sel).first.fill(USER)
        _click_first(page, ["#idSIButton9", "input[type='submit']",
                            "role=button[name='Next']", "role=button[name='Sign in']"])

        pwd_sel = "input[type='password'], input[name='passwd'], #i0118"
        page.wait_for_selector(pwd_sel, timeout=30000)
        log("Entering password from config...")
        page.locator(pwd_sel).first.fill(PWD)
        _click_first(page, ["#idSIButton9", "input[type='submit']",
                            "role=button[name='Sign in']", "role=button[name='Log in']"])
        log("Credentials submitted from config. Complete MFA in the browser if prompted.")

        # 'Stay signed in?' prompt - dismiss with No so nothing persists.
        page.wait_for_timeout(3000)
        _click_first(page, ["#idBtn_Back", "role=button[name='No']", "role=button[name='Skip']"], timeout=4000)
    except Exception as e:
        log(f"Auto-login step failed ({e}). Complete remaining login steps manually.")


def wait_for_pbi_iframe(page):
    log(f"Waiting up to {WAIT_NAV_SECONDS}s for the PowerBI iframe (complete MFA, select Client Belgium, "
        "open Consumption Tax -> VAT DTAI, land on the Dashboards tab)...")
    deadline = time.time() + WAIT_NAV_SECONDS
    last = ""
    while time.time() < deadline:
        try:
            cur = page.url
            fi = iframe_info(page)
            if cur != last:
                log(f"url: {cur} | iframes: {len(fi)}")
                last = cur
            if any("powerbi" in (f.get("src", "")).lower() for f in fi):
                log("PowerBI iframe present.")
                return True
        except Exception:
            pass
        page.wait_for_timeout(3000)
    return False


def wait_for_render(page):
    log(f"Waiting up to {WAIT_RENDER_SECONDS}s for PowerBI visuals to finish rendering...")
    deadline = time.time() + WAIT_RENDER_SECONDS
    while time.time() < deadline:
        fr = powerbi_frame(page)
        if fr:
            try:
                info = fr.evaluate(
                    """() => {
                        const vis = document.querySelectorAll('.visualContainer, visual-container, .visualContainerHost');
                        const body = (document.body && document.body.innerText || '').toLowerCase();
                        return {count: vis.length, loading: body.includes('loading data')};
                    }"""
                )
                if info and info.get("count", 0) > 0 and not info.get("loading"):
                    log(f"Visuals rendered: {info.get('count')} visual containers.")
                    page.wait_for_timeout(4000)
                    return fr
            except Exception:
                pass
        page.wait_for_timeout(3000)
    log("Render wait elapsed; capturing whatever is present.")
    return powerbi_frame(page)


def extract_visuals(fr):
    try:
        return fr.evaluate(
            """() => {
                const norm = s => (s||'').replace(/\\s+/g,' ').trim();
                const out = [];
                const nodes = document.querySelectorAll('.visualContainer, visual-container');
                nodes.forEach((v,i) => {
                    const titleEl = v.querySelector('.visualTitle, .preTextBox, [class*="title"]');
                    out.push({
                        index: i,
                        ariaLabel: norm(v.getAttribute('aria-label')),
                        role: v.getAttribute('role') || '',
                        title: norm(titleEl ? titleEl.innerText : ''),
                        text: norm(v.innerText).slice(0, 400)
                    });
                });
                return out;
            }"""
        )
    except Exception as e:
        return {"error": str(e)}


def extract_report_pages(fr):
    try:
        return fr.evaluate(
            """() => {
                const norm = s => (s||'').replace(/\\s+/g,' ').trim();
                const sels = "[role='tab'], .navigation-wrapper .tab, .pages .tab-inner, .pageButton, .tab-inner .text";
                const tabs = Array.from(document.querySelectorAll(sels))
                    .map(e => norm(e.getAttribute('aria-label') || e.innerText))
                    .filter(Boolean);
                return Array.from(new Set(tabs));
            }"""
        )
    except Exception as e:
        return {"error": str(e)}


def probe_drillthrough(page, fr):
    result = {}
    try:
        vc = fr.query_selector(".visualContainer")
        if not vc:
            result["note"] = "no .visualContainer to probe"
            return result
        box = vc.bounding_box()
        if not box:
            result["note"] = "no bounding box"
            return result
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.click(cx, cy)
        page.wait_for_timeout(600)
        page.mouse.click(cx, cy, button="right")
        page.wait_for_timeout(1200)
        menu = fr.evaluate(
            """() => {
                const norm = s => (s||'').replace(/\\s+/g,' ').trim();
                const sels = ".pbi-menu [role='menuitem'], [role='menu'] [role='menuitem'], .contextMenu li, drop-down-list-item, .menuItemContainer";
                return Array.from(new Set(Array.from(document.querySelectorAll(sels))
                    .map(e => norm(e.innerText)).filter(Boolean)));
            }"""
        )
        result["contextMenu"] = menu
        page.keyboard.press("Escape")
    except Exception as e:
        result["error"] = str(e)
    return result


def capture(page):
    log(f"Capturing DOM into: {OUT}")
    try:
        (OUT / "page.html").write_text(page.content(), encoding="utf-8")
    except Exception as e:
        log(f"page.html failed: {e}")

    write("iframes.json", iframe_info(page))

    frames_dump = []
    for i, fr in enumerate(page.frames):
        entry = {"index": i, "name": fr.name, "url": fr.url}
        try:
            html = fr.content()
            fname = f"frame_{i}.html"
            (OUT / fname).write_text(html, encoding="utf-8")
            entry["html_file"] = fname
            entry["html_len"] = len(html)
        except Exception as e:
            entry["error"] = str(e)
        frames_dump.append(entry)
    write("frames.json", frames_dump)

    fr = powerbi_frame(page)
    if fr:
        visuals = extract_visuals(fr)
        write("visuals.json", visuals)
        log(f"visuals captured: {len(visuals) if isinstance(visuals, list) else 'error'}")
        pages = extract_report_pages(fr)
        write("report_pages.json", pages)
        log(f"report pages: {pages}")
        write("drillthrough.json", probe_drillthrough(page, fr))
    else:
        log("No PowerBI frame found for structured extraction.")

    try:
        page.screenshot(path=str(OUT / "dashboard_full.png"), full_page=True)
        page.screenshot(path=str(OUT / "dashboard_viewport.png"))
    except Exception as e:
        log(f"screenshot failed: {e}")

    try:
        signals = page.evaluate(
            """() => {
                const txt = (el) => (el.innerText || el.textContent || '').replace(/\\s+/g,' ').trim();
                const take = (sel) => Array.from(document.querySelectorAll(sel)).map(txt).filter(Boolean).slice(0,50);
                return { url: location.href, title: document.title,
                    headings: take('h1,h2,h3'), tabs: take("[role='tab'], .nav-link") };
            }"""
        )
    except Exception as e:
        signals = {"error": str(e)}
    write("locators_signals.json", signals)
    log("=== CAPTURE COMPLETE ===")
    log(f"artifacts: {OUT}")


def main():
    log(f"UAT URL: {URL}  user: {USER}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel=CHANNEL, slow_mo=250,
                                    args=["--start-maximized"])
        context = browser.new_context(no_viewport=True, accept_downloads=True)
        page = context.new_page()
        log("Opening UAT URL ...")
        page.goto(URL, wait_until="domcontentloaded")
        best_effort_login(page)
        if wait_for_pbi_iframe(page):
            wait_for_render(page)
        else:
            log("PowerBI iframe not detected; capturing current page anyway.")
        capture(page)
        log("Keeping browser open 8s, then closing.")
        page.wait_for_timeout(8000)
        try:
            context.close()
            browser.close()
        except Exception:
            pass
    log("DONE.")


if __name__ == "__main__":
    main()
