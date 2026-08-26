# Quality Intelligence Suite — One‑Stop QA Platform (MSD)

> **Format:** Markdown (.md)
>
> **Purpose:** Define requirements and design intent for a Streamlit-based one‑stop QA platform that integrates with Azure DevOps (ADO) to deliver impact analysis, regression suite curation, traceability, bulk tagging, AI regression evaluation, **Web UI performance testing**, and leadership-friendly release readiness (Go/No‑Go).

---

## 1. Document Control

- **Document Title:** Quality Intelligence Suite — One‑Stop QA Platform (MSD)
- **Version:** v0.2
- **Author:** Rajan Kumar Manglani
- **Date:** <DD-MMM-YYYY>
- **Stakeholders:** QA Leads, QA Engineers, Dev Leads, Product Owners, Release Manager, Engineering Manager
- **Reviewers:** <names>
- **Approvers:** <names>

---

## 2. Problem Statement

QA teams operate under release time constraints and frequently **do not update regression suites** to reflect:

- the current **release scope** (ADO work items tagged with a release tag),
- the **bugs encountered** during the release cycle,
- and the evolving **test plan**.

This causes:

- **Bug leakage** to production,
- reduced **business confidence** before shipping,
- weak traceability across **scope → tests → results → defects**.

Additionally, performance issues often go undetected because UI performance testing is either manual, late, or not aligned to release impact, leading to **latency regressions** and poor user experience.

---

## 3. Goals / Objectives

### 3.1 Primary Goals

1. Provide a **one-stop QA platform** that consolidates release quality signals and creates confidence before production.
2. Perform **impact analysis** using release scope and cycle bugs.
3. Auto-generate an **updated regression suite** for each release (UI + API + Performance).
4. Ensure **traceability** across:
   - Release scope ↔ Regression tests
   - Cycle bugs ↔ Regression tests
   - Test plan ↔ Execution evidence
5. Provide **leadership-friendly** Go/No‑Go decisions backed by evidence.
6. Provide a **Bulk Tagging Assistant** that smartly assigns:
   - `Type_UI` / `Type_API` / `Type_Perf`
   - `Comp_*` component tags aligned to release impact (**Option B**)
   - Tier tags (`Tier0_Smoke`, `Tier1_Core`, `Tier2_Extended`) where relevant
7. Support both capabilities:
   - Use an **existing** ADO Regression Test Plan
   - **Auto-create** a new ADO Test Plan for a release, then create/update Tier suites
8. Add **Web UI Performance Testing** capability that simulates **full user actions** (login/click/navigation) with configurable **concurrency, ramp-up, and duration**, and produces baseline comparison and performance risk for release readiness.

### 3.2 Success Metrics (KPIs)

- Reduce regression suite drift incidents by **X%**
- Reduce escaped defects by **Y%**
- Reduce time to update regression suite by **Z hours per release**
- Increase traceability:
  - % scope items mapped to tests ≥ **90%**
  - % Sev1/Sev2 bugs mapped to regression tests ≥ **95%**
- Performance quality:
  - % releases with perf regression caught pre-prod ≥ **90%**
  - % runs with baseline comparison available ≥ **95%**
- Increase adoption: # teams using the platform each release

---

## 4. Non‑Goals

- Replacing existing automation frameworks (Playwright/Selenium/API harnesses)
- Building a separate test management system outside ADO
- Fully auto-writing all missing tests (the platform can recommend and create tasks, but it’s not required for MVP)
- Running extremely high-scale UI browser load (1000s of concurrent users) in MVP; this requires dedicated infra and will be addressed later via protocol-level load testing

---

## 5. Personas / Users

1. **QA Engineer** — needs curated regression suite aligned to scope/bugs and time constraints
2. **QA Lead** — needs coverage gaps, risk visibility, traceability, and audit-ready reports
3. **Engineering Lead** — wants fast insight into impacted areas, failures, and performance regressions
4. **Release Manager / Leadership** — wants a clear Go/No‑Go decision with evidence and mitigations

---

## 6. High‑Level Solution Overview

A Streamlit platform integrating with **Azure DevOps (ADO)** as the system of record:

- **Release scope**: ADO work items (stories/features) tagged with release tag (e.g., `Release_R12`)
- **Cycle bugs**: ADO bug work items tagged with the same release tag
- **Test cases**: ADO “Test Case” work items and/or test cases organized under ADO Test Plans & Suites

The platform hosts multiple agents/modules:

- Impact Analysis Agent
- Regression Suite Curator Agent
- Traceability Agent
- Release Readiness Go/No‑Go Agent
- AI Regression Evaluator Agent
- **Web UI Performance Testing Agent** (Browser Journey Load Runner + Performance Regression Sentinel)
- Bulk Tagging Assistant (Type + Component + Tier suggestions)
- Test Plan & Suite Manager (Existing vs Auto-Create)

---

## 7. User Journeys (End‑to‑End)

### 7.1 Primary Journey — Release Preparation

1. User selects **ADO Project + Release Tag**.
2. Platform fetches:
   - scope items
   - cycle bugs
   - test inventory
3. Impact Analysis Agent generates a **risk/impact map**.
4. Bulk Tagging Assistant suggests/fixes:
   - Type tags (UI/API/Perf)
   - Component tags aligned to impact (**Option B**)
   - Tier tags (optional)
5. Regression Suite Curator generates:
   - Tier0 Smoke, Tier1 Core, Tier2 Extended
   - UI + API + Perf coverage
   - traceability per test and coverage gaps
6. User reviews and applies human overrides (add/remove tests, change tier, add rationale).
7. Web UI Performance Testing:
   - user selects UI journey scenarios aligned to impact
   - configures concurrency/ramp/duration and runs locally (MVP)
   - receives perf report and baseline comparison
8. Test Plan & Suite Manager:
   - updates an **existing** regression plan OR
   - creates a **new** plan for the release and creates tier suites
9. Platform gathers execution evidence (MVP: uploaded results; V1+: CI integration).
10. Release Readiness Agent generates:
    - GO / GO WITH RISK / NO‑GO
    - leadership report export

---

## 8. Functional Requirements

### 8.1 Release Intake & Data Pull

- **FR‑1:** User inputs:
  - ADO Project
  - Release tag (e.g., `Release_R12`)
  - runtime budgets per tier (Tier0/Tier1/Tier2)
  - risk appetite (Conservative/Normal/Aggressive)
- **FR‑2:** Platform fetches from ADO:
  - Scope work items tagged with release tag
  - Bugs tagged with release tag
  - Test cases (work item type `Test Case`) and/or ADO Test Plan suite membership
  - (V1+) historical run metadata and flaky indicators
- **FR‑3 (MVP):** Support Offline Mode via CSV/JSON upload for demo and development.

### 8.2 Impact Analysis Agent

- **FR‑4:** Identify impacted components using:
  - scope tags
  - bug tags and severity
- **FR‑5:** Produce:
  - component risk map (0–100)
  - top risk drivers with evidence
  - impacted components list used by downstream suite selection and tagging assistant

### 8.3 Bulk Tagging Assistant (Smart Type + Component Tagging)

- **FR‑6:** Detect missing/inconsistent tags:
  - `Type_UI`, `Type_API`, `Type_Perf`
  - `Comp_*` component tags
  - Tier tags (`Tier0_Smoke`, `Tier1_Core`, `Tier2_Extended`)
- **FR‑7:** Suggest **Type** tags using:
  - deterministic heuristics from title/steps/description
  - (V1+) AI assist for ambiguous cases
- **FR‑8 (Option B):** Suggest **Component** tags using:
  - impacted components prior from impact analysis
  - keyword mapping against title/steps/description
  - reconciliation with existing component tags
- **FR‑9:** UI must show:
  - suggested tags
  - confidence
  - “why” evidence
  - editable overrides
  - bulk selection and preview
- **FR‑10 (V1+):** Apply tags back into ADO test case work items **without overwriting existing tags** (merge behavior).

### 8.4 Regression Suite Curator Agent

- **FR‑11:** Generate release-specific regression suite across:
  - UI
  - API
  - Performance
- **FR‑12:** Tiering:
  - Tier0 Smoke (short, critical)
  - Tier1 Core (risk-based)
  - Tier2 Extended (longer, selective)
- **FR‑13:** Suite selection uses:
  - release scope impact
  - bug hotspots (severity-weighted)
  - test tags (type/component/tier)
  - (V1+) historical failures, flakiness, runtime
- **FR‑14:** Traceability per test:
  - “Selected because it covers scope X / bug Y / component Z”
- **FR‑15:** Coverage gap detection:
  - scope items with no/low regression coverage are flagged
  - Sev1/Sev2 fixed bugs must map to at least one regression test or a documented waiver
- **FR‑16:** Human override:
  - add/remove tests
  - promote/demote tier
  - mandatory “reason” capture for audit

### 8.5 Test Plan & Suite Manager (Existing + Auto‑Create)

- **FR‑17:** Support both modes:
  - **Mode A:** Update an existing ADO Regression test plan
  - **Mode B:** Auto-create a new ADO test plan for the release
- **FR‑18:** For either mode, create/update tier suites:
  - `{ReleaseTag}/Tier0_Smoke`
  - `{ReleaseTag}/Tier1_Core`
  - `{ReleaseTag}/Tier2_Extended`
- **FR‑19:** Push curated suite into ADO:
  - add/remove test cases in tier suites
  - show diff preview before committing
- **FR‑20:** Maintain suite versioning:
  - store suite versions and diffs per release

### 8.6 Traceability Matrix

- **FR‑21:** Display:
  - Scope item → mapped tests (by tier)
  - Bug → mapped tests
  - coverage gaps highlighted
- **FR‑22:** Export traceability report (CSV/Markdown/PDF).

### 8.7 Execution Evidence

- **FR‑23 (MVP):** Accept uploaded results (CSV/JUnit XML export).
- **FR‑24 (V1+):** Pull results automatically from CI/test runs.
- **FR‑25:** Summarize:
  - pass/fail by tier and test type
  - failures by component
  - flaky indicators

### 8.8 Release Readiness Go/No‑Go Agent

- **FR‑26:** Deterministic gates:
  - any **open Sev1** bug → **NO‑GO** (configurable)
- **FR‑27:** Compute readiness score from:
  - defect risk
  - regression completeness
  - execution evidence
  - stability (flakiness)
  - performance risk (from perf module)
  - (optional) AI quality regressions
- **FR‑28:** Output:
  - verdict: GO / GO WITH RISK / NO‑GO
  - key risks with evidence
  - mitigations
  - exportable leadership summary

### 8.9 AI Regression Evaluator Agent

- **FR‑29:** Evaluate baseline vs current for:
  - correctness
  - groundedness (RAG)
  - hallucination rate
  - format adherence (JSON/schema)
  - safety compliance
  - robustness (paraphrase/metamorphic)
- **FR‑30:** Provide:
  - regression summary
  - failure clustering
  - top regressions
  - recommendations (prompt/RAG tuning)
- **FR‑31:** Feed AI regression results into Go/No‑Go (optional toggle).

### 8.10 Web UI Performance Testing (Browser Journey Load)

- **FR‑P1:** Provide a **Scenario Library** to create/edit **Web UI journey scenarios** consisting of ordered steps (e.g., open URL, fill input, click, wait for selector, assert text, think time).
- **FR‑P2:** Allow users to configure **load model inputs** from the UI:
  - concurrency (virtual users)
  - ramp-up duration
  - steady-state duration
  - ramp-down duration
  - iterations per user (optional) and think-time factor
- **FR‑P3:** Execute performance tests **locally from Streamlit (MVP)** using a headless browser runner that simulates **full user actions** (login/click/navigation).
- **FR‑P4:** Capture and store metrics per run:
  - journey duration distribution (p50/p95/p99)
  - step-level timings (p95 per step)
  - error rate (failed journeys / total)
  - throughput proxy (journeys/min)
  - artifacts (screenshots/traces on failure, optional)
- **FR‑P5:** Support **performance baselines** per scenario/environment and compare current runs against baseline.
- **FR‑P6:** Detect regressions using configurable thresholds (e.g., p95 increase > 10%, error rate increase > 1% absolute) and produce PASS/WARN/FAIL.
- **FR‑P7:** Produce an exportable **Performance Summary Report** (Markdown/CSV/JSON) suitable for leadership and audit.
- **FR‑P8:** Feed performance outcomes into **Release Readiness** scoring as a **Perf Risk** dimension.

### 8.11 Performance Regression Sentinel Agent

- **FR‑P9:** Auto-suggest which performance scenarios to run based on **release impact analysis** (impacted components and bug hotspots).
- **FR‑P10:** Generate evidence-based insights:
  - “What regressed?” (metric deltas)
  - “Where did it regress?” (component mapping)
  - “What to do next?” (recommended investigations and mitigations)

---

## 9. Non‑Functional Requirements (NFRs)

- **NFR‑1 Performance:** Pages should respond in <2s for typical datasets (use caching).
- **NFR‑2 Reliability:** Offline mode must work even without ADO connectivity.
- **NFR‑3 Security:** Secrets (PAT/OAuth tokens) must not be logged; store securely.
- **NFR‑4 Auditability:** Track all critical actions (tag updates, suite push, overrides, perf run configs, baseline updates).
- **NFR‑5 Explainability:** Every recommendation shows evidence + confidence.
- **NFR‑6 Scalability:** Support multi-team projects and thousands of test cases.
- **NFR‑7 Safety/Guardrails (Perf):** Enforce caps for concurrency and duration, require dry-run before high load, and warn/limit target environments.

---

## 10. Data Model (High Level)

- `Release(tag, project, date, budgets, risk_profile)`
- `ScopeItem(id, title, tags, components)`
- `Bug(id, title, severity, tags, components)`
- `TestCase(id, title, tags, type_tag, component_tags, tier, runtime, history)`
- `Link(scope_id ↔ test_id)`
- `Link(bug_id ↔ test_id)`
- `SuiteVersion(release_tag, version, created_by, diff, timestamp)`
- `PerfScenario(id, name, type, base_url, steps, component_tags, defaults)`
- `PerfRun(id, release_tag, scenario_id, env, config, metrics, artifacts, status, timestamp)`
- `PerfBaseline(scenario_id, env, metrics, updated_at, updated_by)`

---

## 11. UI / UX Requirements (Prototype)

### 11.1 Navigation

- Dashboard
- Release Intake
- Impact Analysis
- Bulk Tagging Assistant
- Regression Suite Builder
- **Performance Lab (Web UI Load)**
- **Perf Scenario Library**
- **Perf Runs & Regression Report**
- Test Plan & Suite Manager
- Traceability Matrix
- Execution Evidence
- Go/No‑Go
- AI Regression Evaluator
- Settings / Integrations

### 11.2 Key UI Components

- Impact risk heatmap (component vs risk)
- Bulk tagging grid with confidence + rationale + editable overrides
- Regression suite table with tier/type filters and “why included”
- **Performance Lab runner UI** (scenario selection + concurrency/ramp/duration + dry run)
- **Perf regression dashboard** (p50/p95/p99, error rate, baseline vs current)
- Traceability matrix (gaps highlighted)
- Diff preview before “Push to ADO”
- Export buttons (MD/PDF/CSV)

---

## 12. Integrations (Planned)

### 12.1 Azure DevOps

- Work Items: scope, bugs, test cases
- Tags update write-back to test case work items
- Test Plans: create/update plans and suites; add/remove test cases in suites

### 12.2 CI/CD (Future)

- Trigger regression pipelines
- Pull and trend test results, flakiness, and failures

### 12.3 AI/LLM (Optional)

- For ambiguous tagging and failure clustering
- For leadership narrative summaries (evidence-based)

### 12.4 Performance Execution

- **MVP:** Run **Web UI browser-journey performance tests locally** from Streamlit.
- **Future:** Trigger performance runs via CI/CD (e.g., ADO pipeline) and ingest artifacts/results for trend analysis.

---

## 13. Risks & Mitigations

- **Risk:** Inconsistent tagging across teams
  - **Mitigation:** Bulk Tagging Assistant + tag health dashboard
- **Risk:** Low trust in agent outputs
  - **Mitigation:** Evidence + confidence + human override + diff preview
- **Risk:** Overwriting tags in ADO
  - **Mitigation:** Always merge existing tags; never replace blindly
- **Risk:** Performance tests hard to map
  - **Mitigation:** Perf scenario tagging + impact-based auto-selection; require component tags and enforce review
- **Risk:** Accidental environment overload due to high concurrency/duration
  - **Mitigation:** Guardrails (caps, dry-run requirement, approval thresholds), environment allow-list, and clear warnings in the Performance Lab UI

---

## 14. Milestones / Delivery Plan

### MVP (UI Prototype)

- Offline mode with mock/CSV data
- Full navigation + visualizations
- Impact analysis + suite proposal + traceability + exports
- Bulk tagging UI (suggestions + preview; no write-back)
- **Performance Lab (MVP):** Scenario Library + local browser-journey runner + results dashboard + baseline compare (offline/demo mode supported)

### V1 (ADO Live)

- Pull scope/bugs/tests using ADO queries
- Apply tags back into ADO work items (merge behavior)
- Create/update ADO test plans and suites
- Push curated suite into ADO
- **Performance (V1):** Persist perf baselines per scenario/environment; attach perf reports to release readiness and enable trend view across releases

### V2 (Execution & Intelligence)

- CI integration for results ingestion
- Flakiness detection
- AI regression evaluator integrated into Go/No‑Go
- Suite health metrics + learning loop
- Performance trend dashboards and automated alerts

---

## 15. Acceptance Criteria

- Can generate regression suite for a release tag with:
  - UI/API/Perf coverage
  - Tier0/Tier1/Tier2
  - explainable selection reasoning
- Can show traceability matrix and highlight gaps
- Bulk tagging assistant can:
  - propose type tags
  - propose component tags aligned to release impact
  - allow editing and preview
  - apply changes in live mode (V1+)
- Test plan manager can:
  - update existing plan OR create a new plan for release
  - create tier suites and push tests into them
- Go/No‑Go report generated with clear evidence and export option
- Performance capability can:
  - create/edit Web UI journey scenarios
  - run locally with user-configured concurrency/ramp/duration
  - compute p50/p95/p99 journey times and error rate
  - compare against baseline and flag regressions
  - feed Perf Risk into Go/No‑Go

---

## 16. Appendix

### 16.1 Suggested Tag Taxonomy

- Release: `Release_R12`
- Type: `Type_UI`, `Type_API`, `Type_Perf`
- Perf Scenario: `PerfScenario_*` (optional), `Perf_Critical` (optional)
- Tier: `Tier0_Smoke`, `Tier1_Core`, `Tier2_Extended`
- Component: `Comp_Checkout`, `Comp_Payments`, `Comp_Search`, `Comp_Auth`, ...

### 16.2 Open Questions

- Component list source: static dictionary vs auto-discovery from scope tags
- Runtime estimation strategy for suite optimization
- Approval workflow: who can push updates to ADO
- UI perf runner scalability: when to add protocol-level load testing for very high concurrency