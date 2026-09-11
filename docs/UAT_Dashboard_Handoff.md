# UAT PowerBI Dashboard - Handoff

Last updated: 2026-08-28

## 1. Objective

Add a UAT-only automated suite for the VAT DTAI PowerBI Dashboard (not present in QA)
and establish a QA-vs-UAT execution strategy that does not break the existing QA flow.

Scope of the Dashboard feature:
- Verify the PowerBI report renders on the Dashboards tab.
- Verify all dashboard metrics are displayed appropriately.
- Verify drill-through from a dashboard card to Invoice history, Invoice details, Line items.

Follow-up (not started): build a "Detect and Suggest" module the same way (also UAT-only).

## 2. Current status

| Scenario | Marker | Status |
| --- | --- | --- |
| PowerBI dashboard report is displayed | TC_DASH_Load | PASS (live UAT) |
| All dashboard metrics are displayed appropriately | TC_DASH_Metrics | Fix applied, needs one live re-run to confirm |
| Card drill-through navigates to target page (x3) | TC_DASH_DrillThrough | BLOCKED - auto-detect probe not yet implemented |

Under `--env qa` all 5 dashboard tests auto-skip cleanly (no browser). Full suite collects 114 tests.

## 3. QA vs UAT execution strategy

- Single env switch: pytest `--env qa|uat`. conftest `pytest_configure` sets
  `os.environ["VAT_DTAI_ENV"]` from `--env`, so both the pytest layer and
  `VAT_Common_Library` read the same environment.
- `configuration/config.ini` has separate sections:
  - `[GIDEI application details QA]` -> url vatdtaiqa..., `HAS_POWERBI_DASHBOARD=false`
  - `[GIDEI application details UAT]` -> url gtpituat.ey.com, `HAS_POWERBI_DASHBOARD=true`
- `utilities/read_properties.py` `_env_mapping`: `qa -> GIDEI ... QA`, `uat -> GIDEI ... UAT`.
- Capability guard: `env_has_powerbi_dashboard()` in VAT_Common_Library; the dashboard
  "loaded" step skips if `HAS_POWERBI_DASHBOARD=false`.
- Markers `uat_only` / `qa_only` + conftest `pytest_collection_modifyitems` auto-skip hook.
  `Dashboard.feature` is tagged `@uat_only`.
- Launchers: `run_uat.bat` (defaults to `--env uat -m GIDEI`), `run_qa.bat` (`--env qa -m GIDEI`).
  Both pass through extra args, e.g. `run_uat.bat -m Dashboard`.

Run the dashboard tests live:
```
python -m pytest --env uat tests/step_defs/test_dashboard.py -p no:cacheprovider
```
The browser opens headed; complete MFA and (if prompted) Client Belgium selection manually.

## 4. Key UAT findings (important - UAT differs from QA)

UAT does NOT yet have the rebranded app name / e-invoice terminology (the app team is still
pushing those). The framework was made env-agnostic to tolerate both during the transition.

- Login flow differs: UAT lands on the EY SSO page and requires selecting
  "I am EY employee" BEFORE the Microsoft credential form. Handled in
  `launch_app_page.login_with_credentials` (`_select_ey_employee_if_present`) and in the
  env-agnostic state detection (`/sso`, `login.microsoftonline.com`, email inputs).
- Client selection differs: UAT has NO "Continue" button - selecting the workspace in the
  Bootstrap selectpicker auto-navigates. `select_workspace_and_continue` now tolerates a
  missing Continue button (only fails if genuinely still on the client-selection page).
- Home landing: UAT lands on the GTP startup page (hex `506167655445414d5353746172747570`);
  the DTAI tile only appears after clicking the "Consumption Tax" category. `is_on_home_page`
  and `wait_for_home` were fixed to accept the hex startup URL.
- App tile name in UAT (under Consumption Tax): **"Digital Tax Administration Insights - VAT"**
  (legacy name; QA uses "Global Insights And Data Enrichment For e-Invoicing"). The tile
  matcher in `navigate_to_dtai_vat_app` accepts both names plus "VAT DTAI".
- App page hex (name-agnostic): PageVATDTAI = `506167655445414d5356415444544149`.
  `verify_dtai_app_launched` now accepts this hex URL and the module tabs.
- Module tabs visible in UAT app shell: Dashboards, Data Lake IP, Data Ingestion,
  e-Invoice Management, Detect and Suggest, Reconciliation, Reports, User Management.

### PowerBI dashboard specifics
- The dashboard is an embedded PowerBI report in a cross-origin iframe
  (`iframe[src*=reportEmbed]`). reportId `bb1e3f22-24f3-4313-b6cd-75d00ccef853`.
- 30 visuals render. Metrics read live: Total Invoices = 20, Success Rate = 95.0%.
- "By Operational Status" visual exposes column values as bare-integer aria-labels
  (`'14','5','1'` => sum 20 = Total). `status_breakdown()` parses these; the reconciliation
  step sums all category values and compares to Total Invoices.
- Drill-through: right-clicking the **Total Invoices KPI card** shows a menu WITHOUT
  "Drill through" (only: Show keyboard shortcuts, Show screen reader tips, Skip to main
  content, Show data point as a table, Show as a table). So the KPI card is NOT the
  drill-through source. Decision: probe all visuals to auto-detect the visual whose
  right-click menu contains "Drill through"; all three targets come from that same visual.

## 5. What is done

- Env plumbing (read_properties mapping, config flags, VAT_DTAI_ENV, markers, auto-skip hook).
- Env-agnostic login (EY-employee SSO step), state detection, client-selection auto-nav,
  home detection, and DTAI tile navigation (both old + new app names).
- `pageobjects/dashboard_page.py` (DashboardPage): frame access, `open_dashboards_tab`,
  `wait_until_loaded`, `is_powerbi_report_present`, `visual_titles`, `read_metrics`,
  `status_breakdown` (bare-integer aria-label parsing), plus context-menu helpers
  (`_visible_menu_items`, `_open_context_menu`, `_click_menu_item`).
- `tests/features/Dashboard.feature` (@uat_only, 3 scenarios), `tests/step_defs/test_dashboard.py`.
- `run_uat.bat`, `run_qa.bat`.
- Metrics parsing fix (status breakdown from the correct visual) applied; needs one live re-run.

## 6. What is pending / next steps

1. Drill-through auto-detect (in progress in `dashboard_page.py`, drill section):
   - Add a probe that iterates visuals, right-clicks each (prioritize invoice tables:
     "Outbound Invoices (AR)", "Inbound Invoices (AP)"), and returns the first visual whose
     context menu contains "Drill through". Cache the result on a class attribute so the
     three drill-through examples do not each re-probe.
   - After clicking/hovering "Drill through", read the submenu and click the target page.
     Press Escape to close menus between probes.
   - Update the `When` step wording in `Dashboard.feature` and `test_dashboard.py` from
     `the "Total Invoices" card` to a source-agnostic phrasing (auto-detected visual),
     since the KPI card is not the drill source. Keep the scenario name unchanged.
   - Confirm `is_on_report_page` heuristic works after drill (the target page title text
     appears in the frame), or refine to check the report page tab/breadcrumb.
2. Live re-run to confirm metrics scenario passes with the new bare-integer parsing.
3. After Dashboard is green in UAT: re-verify QA still skips uat_only and full suite (114)
   still collects; confirm QA login/nav flow is unaffected.
4. Build "Detect and Suggest" module (UAT-only, same uat_only pattern).

## 7. Files created / modified

Created:
- `pageobjects/dashboard_page.py`
- `tests/features/Dashboard.feature`
- `tests/step_defs/test_dashboard.py`
- `run_uat.bat`, `run_qa.bat`
- `docs/refactor/uat_capture_dashboard.py` (standalone UAT capture helper)

Modified:
- `pageobjects/launch_app_page.py` (env-aware login, client-selection auto-nav, tile matcher,
  name-agnostic verify, diagnostic tile dump)
- `tests/step_defs/VAT_Common_Library.py` (env-agnostic login/state/home detection,
  `env_has_powerbi_dashboard`)
- `conftest.py` (VAT_DTAI_ENV wiring, uat_only/qa_only auto-skip hook)
- `utilities/read_properties.py` (qa/uat env mapping)
- `configuration/config.ini` (UAT section + HAS_POWERBI_DASHBOARD flags)
- `pytest.ini` (uat_only/qa_only + TC_DASH_* markers)

## 8. Cleanup notes

- Temp live-run logs to remove when done: `reports/uat_dashboard_run*.log`.
- Capture artifacts: `reports/runs/UAT_Capture_*` and the per-run `reports/runs/Dashboard_GIDEI_*`
  folders from the debugging runs can be pruned with `utilities/cleanup_reports.py`
  (keeps demo folders excluded; retention keep-N).

## 9. Handy references

- UAT url: https://gtpituat.ey.com/   (QA: vatdtaiqa...)
- Client used: Client Belgium
- PageSelectClient hex: `5061676553656c656374436c69656e74`
- PageTEAMSStartup hex: `506167655445414d5353746172747570`
- PageVATDTAI hex: `506167655445414d5356415444544149`
