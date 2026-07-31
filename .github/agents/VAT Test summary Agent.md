# VAT DTAI Release 1 – TSR Report Generation Prompt

## Role

You are a **Senior QA Analyst**. I want you to create a professional **Test Summary Report (TSR)** for **VAT DTAI Release 1** using the attached **SUTCC Test Summary Report** as the reference template.

---

## Reference Template Structure

Use the same structure as the reference template:

1. **US Summary Report**
2. **Bug Summary Report**

---

## Application Details

| Field | Value |
|---|---|
| Application Name | VAT DTAI |
| Release | Release 1.0 / 1st Release |
| Environment | UAT |

---

## Source Inputs

Use the following inputs to prepare the TSR:

1. VAT DTAI UAT testing document
2. ADO User Story URLs
3. ADO Bug URLs
4. ADO Test Plan / Test Suite URLs

---

## Important Instructions

- Do **not** hallucinate or assume any:
  - User Story ID
  - Bug ID
  - Test Case count
  - Execution count
  - Passed count
  - Failed count
  - ADO link
  - Status
  - Severity
  - QC Manager
- Use only the details available from the provided **VAT DTAI testing document** and **ADO URLs**.
- If any information is not available, use **"TBD"** or **"To be updated from ADO"**.
- Prepare the TSR in **Excel-ready table format**.

---

# A. Executive Summary

Prepare a short executive summary with the following details:

- Application Name
- Release
- Environment
- Testing Scope
- Overall QA Status
- Business Sign-off Recommendation
- Key Working Areas
- Key Open Issues / Pending Integrations

Mention that **VAT DTAI Release 1 is conditionally ready for Business review/sign-off for the working MVP scope**, subject to Business acceptance of known open defects and pending integrations.

---

# B. US Summary Report

Create a table using the below columns exactly:

| Release | Feature | US ID | Name | Test Cases | Test Cases Executed | Test Passed | Test Failed | Status | Links | QC Manager |
|---|---|---|---|---:|---:|---:|---:|---|---|---|
| Release 1.0 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

For each VAT DTAI module / feature, map the appropriate **ADO User Story** and **Test Plan** details.

## Functional Areas to be Covered

1. Dashboard Module
2. Data Lake IP
3. Data Ingestion
4. E-invoice Management
5. AI Review Required Pop-up
6. Detect & Suggest Module
7. Reconciliation
8. Reports
9. User Management

## Row-level Instructions

For each row:

- **Release** should be `Release 1.0`
- **Feature** should be the VAT DTAI functional module or linked ADO feature
- **US ID** should come from ADO story URL
- **Name** should come from ADO story title or UAT module name
- **Test Cases** should come from ADO Test Plan/Test Suite
- **Test Cases Executed** should come from ADO execution summary
- **Test Passed** should come from ADO execution summary
- **Test Failed** should come from ADO execution summary
- **Status** should be derived from test execution and known defects
- **Links** should include ADO Test Execution/Test Plan link
- **QC Manager** should be populated from available project data, otherwise use `TBD`

## Status Classification

Use the following status values:

- Passed
- Passed with Observation
- Partially Passed
- Pending
- Failed / Open Defect
- Not Executed
- TBD

---

# C. Bug Summary Report

Create a second table using the below columns exactly:

| Release | US ID | Bug ID | Description | Severity | Status | Environment |
|---|---|---|---|---|---|---|
| Release 1.0 | TBD | TBD | TBD | TBD | TBD | UAT |

Include all bugs from the provided **ADO bug URLs**.

At minimum, include the known bugs from the VAT DTAI testing document:

- **Bug 624928**: `[VAT] [RC] - Getting error "At least one Entity must be selected." while running reconciliation logic when user selects all filter criteria and selects Reconcile button.`
- **Bug 624354**: `[VAT][RM] E-Invoice Report – Wrong values displayed in SystemId column in E-invoice report.`

## Bug Row-level Instructions

For each bug:

- **Release** should be `Release 1.0`
- **US ID** should be mapped from ADO if available, otherwise `TBD`
- **Bug ID** should come from ADO
- **Description** should come from ADO bug title/description
- **Severity** should come from ADO
- **Status** should come from ADO
- **Environment** should be `UAT` unless ADO says otherwise

---

# D. Open Items / Pending Integrations

Create a third table using the below columns:

| Module | Open Item | Business Impact | Suggested Action | Release Impact |
|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD |

Include these known open/pending items:

- Data Lake IP dashboard filter is non-functional
- Data Lake IP Dashboard is image-based for now
- AI Review Required pop-up integration is pending
- Detect & Suggest agent is not configured appropriately in UAT
- Agent integration with Power BI is pending
- Inbound e-invoice grid is showing hardcoded MVP data
- Inbound e-invoice details are not displayed from Client E-invoice Number
- Inbound status hyperlink is missing for extract details
- Duplicate Status and E-invoice Number columns are shown under Inbound E-invoices AP
- Reconciliation fails when All entities are selected
- System ID column shows Source System in E-invoice Status Report

---

# E. QA Release Readiness Recommendation

Provide one clear recommendation from below:

- Ready for Business Sign-off
- Conditionally Ready for Business Sign-off
- Not Ready for Business Sign-off

## Recommended Wording

> VAT DTAI Release 1 is conditionally ready for Business review/sign-off for the working MVP scope. Core UAT flows are working for Dashboard drill-through, supported Data Ingestion, Outbound E-invoice filtering, selected-entity Reconciliation, and E-invoice Status Report exports. However, sign-off should explicitly call out known open defects and pending integrations around Data Lake IP filtering, AI Review Required pop-up, Detect & Suggest agent configuration, Inbound E-invoice behavior, All-entity Reconciliation, and System ID report values.

---

# F. Business Email Summary

Draft a concise business-facing email to share the TSR report with Business stakeholders.

The email should include:

- Purpose of sharing TSR
- Current UAT status
- Key working areas
- Open issues/pending integrations
- Request for Business review/sign-off
- Mention that open items will continue to be tracked through ADO

---

## Expected Final Output

The final TSR output should include:

1. Executive Summary
2. US Summary Report table
3. Bug Summary Report table
4. Open Items / Pending Integrations table
5. QA Release Readiness Recommendation
6. Business Email Summary

Ensure the output is professional, QA-complete, business-friendly, and ready to be copied into Excel or converted into a formal TSR document.