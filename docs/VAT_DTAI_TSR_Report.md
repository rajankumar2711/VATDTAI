# VAT DTAI Release 1.0, TSR Report (Updated 2026-07-14)

## A. Executive Summary

| Field | Value |
|---|---|
| Application Name | VAT DTAI |
| Release | Release 1.0 / 1st Release |
| Environment | UAT |
| Testing Scope | MVP functional coverage across Dashboard, Data Ingestion, E-invoice Management, Reconciliation, Reports, User Management, and related integrations |
| Overall QA Status | Conditionally Ready for Business Sign-off (working MVP scope), open defects and pending integrations remain |
| Business Sign-off Recommendation | Conditional sign-off for working MVP scope, with explicit acceptance of known open defects and pending integrations |
| Key Working Areas | Dashboard entry flow, supported Data Ingestion paths, Outbound E-invoice scenarios, selected-entity reconciliation, report export scenarios |
| Key Open Issues / Pending Integrations | Data Lake IP filtering and dashboard behavior, AI Review Required integration, Detect and Suggest setup, inbound invoice data behavior, all-entity reconciliation, report value discrepancies |

## A1. Current ADO Board Snapshot (VAT_DTAI)

| Item | Value |
|---|---|
| Project | TAX-ATTG-INDIRECT-APM0027765-VAT-Digital-Tax-Administration |
| Project URL | https://dev.azure.com/ATTG/TAX-ATTG-INDIRECT-APM0027765-VAT-Digital-Tax-Administration |
| Teams | TAX-ATTG-INDIRECT-APM0027765-VAT-Digital-Tax-Dev Team, TAX-ATTG-INDIRECT-APM0027765-VAT-Digital-Tax-Administration Team |
| Board item state summary | To be updated from ADO board query (board status API/CLI not available in current environment) |
| User story mapping source used in this TSR | Active Test Plan suite hierarchy (Functional Testing US-linked suites) |

## B. US Summary Report

| Release | Feature | US ID | Name | Test Cases | Test Cases Executed | Test Passed | Test Failed | Status | Links | QC Manager |
|---|---|---|---|---:|---:|---:|---:|---|---|---|
| Release 1.0 | Dashboard Module | 597767 | [MVP] [UI/UX] DTAI Tile on GTP IT | 6 | TBD | TBD | TBD | TBD | https://dev.azure.com/ATTG/TAX-ATTG-INDIRECT-APM0027765-VAT-Digital-Tax-Administration/_apis/testplan/Plans/598683/Suites/600224 | TBD |
| Release 1.0 | Data Lake IP | 603866 | [MVP] [UI/UX] [DL] Create Data Lake IP Tab | TBD | TBD | TBD | TBD | TBD | https://dev.azure.com/ATTG/TAX-ATTG-INDIRECT-APM0027765-VAT-Digital-Tax-Administration/_apis/testplan/Plans/598683 | TBD |
| Release 1.0 | Data Ingestion | 597153, 595077 | [MVP] [UI/UX] [DI] Upload Invoices; [MVP] [UI/UX] [DI] Create Data Ingestion Tab | TBD | TBD | TBD | TBD | TBD | https://dev.azure.com/ATTG/TAX-ATTG-INDIRECT-APM0027765-VAT-Digital-Tax-Administration/_apis/testplan/Plans/598683 | TBD |
| Release 1.0 | E-invoice Management | 597156, 597157, 597227, 600181, 600184, 603766, 603767 | [MVP] [UI/UX] [IM] Suite set (tab, outbound, inbound, details, status interactions) | TBD | TBD | TBD | TBD | TBD | https://dev.azure.com/ATTG/TAX-ATTG-INDIRECT-APM0027765-VAT-Digital-Tax-Administration/_apis/testplan/Plans/598683 | TBD |
| Release 1.0 | AI Review Required Pop-up | 627916 | [MVP] [UI/UX] [IM] Outbound e-Invoices - Review Required Popup | TBD | TBD | TBD | TBD | TBD | https://dev.azure.com/ATTG/TAX-ATTG-INDIRECT-APM0027765-VAT-Digital-Tax-Administration/_apis/testplan/Plans/598683 | TBD |
| Release 1.0 | Detect and Suggest Module | TBD | Detect and Suggest flow coverage | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Release 1.0 | Reconciliation | 602402, 602403, 602964, 605061, 605062, 605063, 624565 | [MVP] [RC] Reconciliation suite set | TBD | TBD | TBD | TBD | TBD | https://dev.azure.com/ATTG/TAX-ATTG-INDIRECT-APM0027765-VAT-Digital-Tax-Administration/_apis/testplan/Plans/598683 | TBD |
| Release 1.0 | Reports | 597552, 597555, 597556, 597557 | [MVP] [RM] Reports suite set | TBD | TBD | TBD | TBD | TBD | https://dev.azure.com/ATTG/TAX-ATTG-INDIRECT-APM0027765-VAT-Digital-Tax-Administration/_apis/testplan/Plans/598683 | TBD |
| Release 1.0 | User Management | 606766 | [MVP] [UI/UX] [UM] User Management Updates | TBD | TBD | TBD | TBD | TBD | https://dev.azure.com/ATTG/TAX-ATTG-INDIRECT-APM0027765-VAT-Digital-Tax-Administration/_apis/testplan/Plans/598683 | TBD |

## C. Bug Summary Report

| Release | US ID | Bug ID | Description | Severity | Status | Environment |
|---|---|---|---|---|---|---|
| Release 1.0 | TBD | 624928 | [VAT] [RC] Getting error "At least one Entity must be selected." while running reconciliation logic when all filters are selected | TBD | To be updated from ADO | UAT |
| Release 1.0 | TBD | 624354 | [VAT] [RM] E-Invoice Report, wrong values displayed in SystemId column | TBD | To be updated from ADO | UAT |

## D. Open Items / Pending Integrations

| Module | Open Item | Business Impact | Suggested Action | Release Impact |
|---|---|---|---|---|
| Data Lake IP | Dashboard filter is non-functional | Limits business drill-down and analysis | Fix filter logic and retest with business scenarios | Medium |
| Data Lake IP | Dashboard is image-based currently | Non-interactive user experience, reduced confidence in UAT | Replace static visuals with live integrated dashboard | Medium |
| E-invoice Management | AI Review Required pop-up integration pending | Review and decision workflow incomplete | Complete integration and run regression on outbound flows | High |
| Detect and Suggest | Agent not configured appropriately in UAT | Suggested actions may be unavailable or unreliable | Correct UAT configuration and validate with business data | High |
| Reporting/AI | Agent integration with Power BI pending | Reporting intelligence and analytics workflow incomplete | Complete integration, validate end-to-end output | Medium |
| E-invoice Management (Inbound) | Inbound grid shows hardcoded MVP data | UAT confidence reduced for inbound realism | Connect inbound grid to actual integration source | High |
| E-invoice Management (Inbound) | Inbound details not displayed from client e-invoice number | Users cannot validate full inbound invoice context | Fix lookup/mapping and verify linked details view | High |
| E-invoice Management (Inbound) | Inbound status hyperlink missing for extract details | Navigation gaps for case investigation | Add status drill-through and test for all statuses | Medium |
| E-invoice Management (Inbound) | Duplicate Status and E-invoice Number columns shown | UI confusion and reporting inconsistency | Remove duplicate columns and validate schema mapping | Medium |
| Reconciliation | Reconciliation fails when all entities are selected | Blocks broad reconciliation use case | Resolve defect, retest logic and performance | High |
| Reports | System ID column shows source system in E-invoice Status Report | Incorrect report interpretation risk | Correct mapping and re-validate report outputs | High |

## E. QA Release Readiness Recommendation

**Conditionally Ready for Business Sign-off**

VAT DTAI Release 1 is conditionally ready for Business review/sign-off for the working MVP scope. Core UAT flows are working for Dashboard drill-through, supported Data Ingestion, Outbound E-invoice filtering, selected-entity Reconciliation, and E-invoice Status Report exports. Sign-off should explicitly call out known open defects and pending integrations around Data Lake IP filtering, AI Review Required pop-up, Detect and Suggest configuration, inbound e-invoice behavior, all-entity Reconciliation, and System ID report values.

## F. Business Email Summary

Subject: VAT DTAI Release 1.0, UAT Test Summary Report for Business Review

Dear Business Stakeholders,

Please find the latest VAT DTAI Release 1.0 UAT Test Summary Report for your review. Current testing indicates the working MVP scope is progressing, and key functional flows are available for business validation.

At the same time, a defined set of open defects and pending integrations remain, primarily in Data Lake IP filtering, AI Review Required integration, Detect and Suggest setup, inbound e-invoice behavior, all-entity reconciliation, and selected reporting fields.

Based on current evidence, QA recommends **conditional business sign-off** for the working MVP scope, with explicit acknowledgement of these known open items. We will continue to track and update all open items through ADO until closure.

Regards,  
QA Team

## Appendix, ADO Test Plan Status Snapshot

| Field | Value |
|---|---|
| Test Plan ID | 598683 |
| Test Plan Name | VAT Test Plan |
| State | Active |
| Owner | Rajan Kumar Manglani |
| Last Updated | 2026-03-18T06:14:01.75Z |
| Root Suite | 598684 (VAT Test Plan) |
| Functional branch | Release Test Plan Execution > FY 2026 > Functional Testing |
| Functional US-linked child suites | 25 |
| Primary Test Plan Link | https://dev.azure.com/ATTG/TAX-ATTG-INDIRECT-APM0027765-VAT-Digital-Tax-Administration/_apis/testplan/Plans/598683 |
