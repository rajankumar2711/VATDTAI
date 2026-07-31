# E-Invoice Agent Business Rule Testing Guide

**Document purpose:** QA and integration testing guide for e-invoice validation agents created and executed through Visual Studio Code  
**Supported countries:** Belgium (`BE`), France (`FR`), Poland (`PL`)  
**Supported source systems:** SAP and Custom ERP / Oracle  
**Current business rules:** BR-1, BR-4, BR-6, BR-7, BR-12, BR-13  
**Document version:** 1.0  
**Test-data baseline:** `EInvoice_60_Samples_BE_FR_PL_SAP_CustomERP_v3.zip`  
**Expected-results baseline:** `EInvoice_Agent_Test_Master_60_Samples_v3.xlsx`

---

## 1. Objective

This guide defines how to configure, execute, and validate the following e-invoice agents:

1. **Business Rule 1:** Invoice Completeness and XML Readiness
2. **Business Rule 4:** Free-Text and XML Character Safety
3. **Business Rule 6:** Invoice Totals and Mathematical Integrity
4. **Business Rule 7:** Invoice Type Classification
5. **Business Rule 12:** Customer Type Classification
6. **Business Rule 13:** Invoice Number Sequence Monitoring

The test approach verifies that each agent:

- Detects the intended anomalies
- Returns all applicable findings for a single invoice
- Avoids false-positive results
- Preserves source evidence
- Reports actual and expected values
- Identifies an evidence-supported root cause
- Provides a specific correction recommendation
- Produces a stable machine-readable result
- Behaves consistently across Belgium, France, and Poland
- Behaves consistently for SAP and Custom ERP source formats

---

## 2. Repository Layout

Use the following recommended project structure in VS Code:

```text
einvoice-agent-testing/
├── README.md
├── prompts/
│   ├── Business_Rule_1_Invoice_Completeness_and_XML_Readiness_Prompt.txt
│   ├── Business_Rule_4_Free-Text_and_XML_Character_Safety_Prompt.txt
│   ├── Business_Rule_6_Invoice_Totals_and_Mathematical_Integrity_Prompt.txt
│   ├── Business_Rule_7_Invoice_Type_Classification_Prompt.txt
│   ├── Business_Rule_12_Customer_Type_Classification_Prompt.txt
│   └── Business_Rule_13_Invoice_Number_Sequence_Monitoring_Prompt.txt
├── test-data/
│   ├── Belgium/
│   │   ├── SAP/
│   │   └── CustomERP/
│   ├── France/
│   │   ├── SAP/
│   │   └── CustomERP/
│   └── Poland/
│       ├── SAP/
│       └── CustomERP/
├── expected results/
│   └── EInvoice_Agent_Test_Master_60_Samples_v3.xlsx
├── results/
│   ├── raw/
│   ├── normalized/
│   └── reports/
├── config/
│   ├── countries.json
│   ├── source_field_mapping.json
│   ├── business_rules.json
│   └── agent_runtime.json
├── src/
│   ├── loaders/
│   ├── agents/
│   ├── validators/
│   └── result_comparator/
└── tests/
    ├── unit/
    ├── integration/
    └── regression/
```

---

## 3. Prompt Files

Store the approved prompt files under `prompts/` using these exact names:

```text
Business_Rule_1_Invoice_Completeness_and_XML_Readiness_Prompt.txt
Business_Rule_4_Free-Text_and_XML_Character_Safety_Prompt.txt
Business_Rule_6_Invoice_Totals_and_Mathematical_Integrity_Prompt.txt
Business_Rule_7_Invoice_Type_Classification_Prompt.txt
Business_Rule_12_Customer_Type_Classification_Prompt.txt
Business_Rule_13_Invoice_Number_Sequence_Monitoring_Prompt.txt
```

Do not modify prompt text during test execution. Store the prompt version, checksum, configuration record ID, and active environment with each result.

---

## 4. Test Data Scope

The Version 3 data pack contains 60 XML files.

| Country | SAP | Custom ERP | Total |
|---|---:|---:|---:|
| Belgium | 10 | 10 | 20 |
| France | 10 | 10 | 20 |
| Poland | 10 | 10 | 20 |
| **Total** | **30** | **30** | **60** |

### 4.1 SAP tax categories

Only the following SAP source values are allowed:

```text
A0
V0
V9
RC
```

### 4.2 Custom ERP tax categories

Only the following Custom ERP source values are allowed:

```text
VAT
GST
EXEMPT
REVERSE
```

### 4.3 Tax rate coverage

The pack covers:

```text
21%
12%
6%
0% reverse charge
```

### 4.4 Source XML structure

- SAP test files retain the uploaded SAP `INVOIC02` hierarchy.
- Custom ERP files retain the uploaded Oracle/OAGIS `ProcessInvoice` hierarchy.
- XML element names, hierarchy, and ordering must remain unchanged.
- Test scenarios must be created by changing values, not by inventing unsupported tags.
- Empty values may be used inside retained elements where the scenario requires a missing value.

---

## 5. Test Strategy

Use four complementary test layers.

### 5.1 Positive controls

Positive controls validate that agents do not produce false-positive findings.

Examples:

- Valid 21% B2B invoice
- Valid B2G invoice that also has a VAT identifier
- Valid B2C invoice with explicit consumer evidence and no buyer VAT number
- Valid mathematical totals
- Valid source-system tax category
- Valid accented French or Polish characters
- Valid corrected invoice with original-document evidence
- Valid reverse-charge calculation with zero VAT

A positive control passes only when:

- No unexpected Critical or Medium finding is returned
- The final status is `PASS`
- All applicable checks are `PASS`
- Missing non-applicable fields are not incorrectly treated as failures

### 5.2 Atomic anomaly tests

Atomic tests target one primary rule to validate precision.

Examples:

- One malformed buyer VAT number
- One line amount mismatch
- One missing invoice type code
- One non-breaking space
- One missing correction reference
- One exact sequence gap

Atomic tests are recommended for unit and prompt regression testing.

### 5.3 Combined anomaly tests

Combined tests validate that one invoice can return multiple independent findings.

Example combination:

```text
Corrected invoice
+ missing original invoice reference
+ risky Unicode
+ tax-summary mismatch
+ missing government routing evidence
```

The agent must not stop after the first failure. All independent findings must be returned.

### 5.4 Negative assertions

A negative assertion states what the agent must **not** report.

Examples:

- Do not classify B2C from missing VAT alone
- Do not classify B2G from a government-like name alone
- Do not classify B2B solely from an endpoint
- Do not flag valid French or Polish diacritics
- Do not flag an XML-escaped ampersand as an unescaped character
- Do not report `PAYABLE_MISMATCH` when no mapped numeric prepaid field exists
- Do not count repeated invoice-line rows as duplicate invoices

Negative assertions are mandatory for false-positive testing.

---

## 6. Common Agent Input Contract

Normalize parsed source data into a common envelope before invoking an agent. Preserve original source field names and raw values as evidence.

```json
{
  "execution_id": "unique-run-id",
  "business_rule_id": "BR-6",
  "prompt_version": "1.0",
  "source_system": "SAP",
  "country": "BE",
  "profile": "configured-profile-or-unknown",
  "input_mode": "parsed_xml_rows",
  "source_file": "SAP_BE_05_SAP-BE-2026-01005.xml",
  "records": [],
  "field_mapping": {},
  "country_configuration": {},
  "runtime_options": {
    "strict_json": true,
    "include_all_checks": true,
    "include_evidence": true
  }
}
```

### 6.1 Input rules

- Do not discard the original XML or raw values.
- Do not silently normalize source values before preserving evidence.
- Do not merge different invoices.
- Collapse repeated line/header joins only when the logical identity is reliable.
- Keep source-system field mapping versioned.
- Pass country and profile configuration explicitly.
- If configuration is missing, expect `NOT_VERIFIABLE`, not speculative validation.

---

## 7. Common Agent Output Contract

Each invoice-level agent should return one JSON object per invoice group.

```json
{
  "execution_id": "unique-run-id",
  "business_rule_id": "BR-6",
  "prompt_version": "1.0",
  "batch_id": "batch-value-or-null",
  "invoice_id": "invoice-number",
  "country": "BE",
  "source_system": "SAP",
  "status": "PASS",
  "summary": "Concise evidence-based conclusion",
  "checks": [
    {
      "check_name": "Line amount validation",
      "status": "PASS",
      "actual_value": "100.00",
      "expected_value": "100.00",
      "rule_or_formula": "quantity x unit_price / price_base_quantity",
      "evidence_scope": "line values",
      "result_reason": "Line amount reconciles within tolerance."
    }
  ],
  "findings": [
    {
      "level": "Line:000010",
      "field_name": "line_extension_amount",
      "actual_value": "125.00",
      "expected_value": "100.00",
      "rule_or_formula": "2 x 50 / 1",
      "variance": "25.00",
      "tolerance": "0.01",
      "issue_type": "LINE_AMOUNT_MISMATCH",
      "severity": "Critical",
      "why_it_is_a_problem": "The declared line amount does not reconcile to quantity and unit price.",
      "most_likely_supported_root_cause": "Incorrect line amount or stale source calculation",
      "suggested_fix": "Correct the line amount or the underlying quantity/unit price.",
      "blocking_impact": "Blocks processing",
      "evidence_scope": "line values"
    }
  ]
}
```

### 7.1 Allowed check statuses

```text
PASS
FAIL
NOT_VERIFIABLE
NOT_APPLICABLE
```

### 7.2 Final status

```text
PASS
Review Needed
```

### 7.3 Output quality gates

Fail the agent test if the output:

- Is not valid JSON when strict JSON is required
- Omits invoice identification
- Omits applicable failed checks
- Invents unavailable evidence
- Provides a suggested correction without supporting evidence
- Uses an issue type outside the configured list
- Marks `PASS` while a Critical finding exists
- Marks an unresolved critical check `NOT_APPLICABLE`
- Reports vague fixes such as “check data” or “review manually”

---

# 8. Business Rule 1 Testing

## 8.1 Agent

**Invoice Completeness and XML Readiness**

## 8.2 Core testing objective

Verify that the invoice contains enough consistent information to form one unambiguous structured XML hierarchy.

## 8.3 Required checks

- Invoice grouping and identifiers
- Header completeness
- Seller completeness
- Buyer completeness
- At least one logical line
- Line identity and required content
- Tax dependencies
- Totals dependencies
- Payment and settlement dependencies
- Credit/correction/prepayment references
- Repeated header consistency
- Hierarchy and XML mapping readiness

## 8.4 Expected issue types

```text
MISSING_HEADER_DATA
MISSING_SELLER_DATA
MISSING_BUYER_DATA
MISSING_LINE_ITEMS
INVALID_FIELD_FORMAT
BROKEN_STRUCTURE
LOGICAL_INCONSISTENCY
HIERARCHY_ISSUE
MISSING_CONDITIONAL_SECTION
CONFLICTING_REPEATED_VALUES
XML_MAPPING_RISK
COUNTRY_NOT_DETERMINED
```

## 8.5 Recommended positive assertions

- A complete invoice with all required sections returns `PASS`.
- Empty optional fields do not block processing.
- A valid B2C invoice is not failed because it lacks a business-only identifier.
- Existing XML tags remain unchanged after ingestion.

## 8.6 Recommended anomaly assertions

- Reverse charge with no mapped legal basis returns `MISSING_CONDITIONAL_SECTION`.
- Corrected invoice without an original-document reference returns a missing dependency finding.
- A line without usable commercial content blocks XML readiness.
- Conflicting repeated seller IDs block processing.

---

# 9. Business Rule 4 Testing

## 9.1 Agent

**Free-Text and XML Character Safety**

## 9.2 Required checks

- Critical NULL/empty text
- XML-invalid controls
- Reserved-character handling
- Zero-width/invisible characters
- Non-breaking spaces
- Mojibake and encoding corruption
- Replacement character
- Emoji and decorative characters
- Private-use characters
- Risky punctuation
- Repeated-value normalization consistency

## 9.3 Expected issue types

```text
NULL_OR_EMPTY_TEXT
INVALID_XML_CHARACTER
UNESCAPED_XML_RESERVED_CHARACTER
INVALID_CONTROL_CHARACTER
ENCODING_CORRUPTION
RISKY_UNICODE_SYMBOL
ZERO_WIDTH_OR_INVISIBLE_CHARACTER
NON_BREAKING_SPACE
INCONSISTENT_TEXT_NORMALIZATION
COUNTRY_NOT_DETERMINED
```

## 9.4 Positive assertions

- `é`, `è`, `ą`, `ę`, `ł`, and other valid language characters are not flagged solely as non-ASCII.
- `AT&amp;T` in raw XML is not double-escaped.
- Valid XML text with ordinary punctuation passes.

## 9.5 Anomaly assertions

- U+00A0 returns `NON_BREAKING_SPACE`.
- U+200B returns `ZERO_WIDTH_OR_INVISIBLE_CHARACTER`.
- `SociÃ©tÃ©` returns `ENCODING_CORRUPTION`.
- Emoji in a critical business field returns `RISKY_UNICODE_SYMBOL`.

## 9.6 Important ingestion limitation

Do not inject XML 1.0-invalid control characters into a file that must pass XML parsing. Test those characters through a pre-serialization value harness or direct record input, not through an ingestible XML fixture.

---

# 10. Business Rule 6 Testing

## 10.1 Agent

**Invoice Totals and Mathematical Integrity**

## 10.2 Required checks

- Numeric parsing
- Unique-line aggregation
- Price-base quantity
- Quantity × unit price
- Line adjustments
- Line tax
- Tax summary by category/rate
- Header tax
- Net total
- Gross total
- Allowance and charge treatment
- Prepayment and payable
- Rounding placement
- Sign consistency
- Duplicate-line conflicts

## 10.3 Key formulas

```text
BaseLineAmount = quantity × unit_price ÷ price_base_quantity
```

```text
TaxExclusiveTotal = SumUniqueLineNet - AllowanceTotal + ChargeTotal + SupportedRounding
```

```text
TaxInclusiveTotal = TaxExclusiveTotal + TaxTotal
```

```text
PayableAmount = TaxInclusiveTotal - PrepaidAmount + PayableRoundingAmount
```

## 10.4 Tolerances

```text
Per-line amount: 0.01
Per-line tax: 0.01
Invoice/header: 0.02
Tax summary: 0.02
Tax rate: 0.01 percentage points
```

## 10.5 Expected issue types

```text
MISSING_CRITICAL_AMOUNT
INVALID_NUMERIC_VALUE
NET_TOTAL_MISMATCH
VAT_TOTAL_MISMATCH
GROSS_TOTAL_MISMATCH
PAYABLE_MISMATCH
LINE_AMOUNT_MISMATCH
LINE_TAX_MISMATCH
TAX_SUMMARY_MISMATCH
ROUNDING_DIFFERENCE
CONFLICTING_REPEATED_TOTALS
CONFLICTING_DUPLICATE_LINE
POTENTIAL_DUPLICATE_LINE
INCOMPLETE_VALIDATION_SCOPE
LOGICAL_INCONSISTENCY
COUNTRY_NOT_DETERMINED
```

## 10.6 Positive assertions

- Balanced line, tax, net, gross, and payable totals return `PASS`.
- Missing quantity does not fail the invoice when independent reconciliation succeeds.
- Valid negative credit-note amounts do not fail solely because they are negative.
- Prepaid amount reduces payable, not gross.

## 10.7 Anomaly assertions

- Changed line net with stale totals returns line and net mismatches.
- Changed line tax with stale header tax returns line/VAT mismatch.
- Header charge omitted from net/gross returns net and gross findings.
- Tax summary differing from line/header tax returns `TAX_SUMMARY_MISMATCH`.

---

# 11. Business Rule 7 Testing

## 11.1 Agent

**Invoice Type Classification**

## 11.2 Semantic types

```text
380 Commercial invoice
381 Credit note
384 Corrected invoice
386 Prepayment invoice
388 Tax invoice
Other configured type
UNDETERMINED
```

## 11.3 Required checks

- Declared code presence
- Code format and configured validity
- Code-label consistency
- Repeated value consistency
- Credit/refund/reversal evidence
- Correction/replacement evidence
- Original invoice reference
- Advance/prepayment evidence
- Tax-invoice purpose
- Financial sign consistency
- Country/profile eligibility
- Classification confidence

## 11.4 Expected issue types

```text
INVOICE_TYPE_CODE_MISSING
INVALID_OR_UNSUPPORTED_TYPE_CODE
INVOICE_TYPE_CODE_MISMATCH
INVOICE_TYPE_CODE_LABEL_CONFLICT
CONFLICTING_TYPE_SIGNALS
INSUFFICIENT_CLASSIFICATION_EVIDENCE
STANDARD_INVOICE_BEHAVIOR_MISMATCH
CREDIT_NOTE_BEHAVIOR_MISMATCH
CORRECTION_BEHAVIOR_MISMATCH
PREPAYMENT_BEHAVIOR_MISMATCH
TAX_INVOICE_BEHAVIOR_MISMATCH
CONFLICTING_REPEATED_TYPE_VALUES
RELATED_DOCUMENT_REFERENCE_MISSING
CONTRADICTORY_FINANCIAL_BEHAVIOR
PROFILE_ELIGIBILITY_NOT_VERIFIABLE
UNSUPPORTED_OR_UNMAPPED_DOCUMENT_TYPE
HISTORICAL_MAPPING_CONFLICT
```

## 11.5 Positive assertions

- A valid commercial sale supports 380.
- A valid government buyer does not affect invoice type by itself.
- A valid corrected invoice with original reference supports 384.
- A final invoice deducting an advance is not automatically classified as 386.

## 11.6 Anomaly assertions

- Code 381 with positive commercial behavior and no credit evidence returns mismatch findings.
- Corrected intent without original reference returns `RELATED_DOCUMENT_REFERENCE_MISSING`.
- Missing code remains `Review Needed`, even if a suggested code is available.
- Conflicting credit and correction evidence may return `UNDETERMINED`.

---

# 12. Business Rule 12 Testing

## 12.1 Agent

**Customer Type Classification**

## 12.2 Customer types

```text
B2B
B2G
B2C
UNDETERMINED
```

## 12.3 Required checks

- Declared customer type
- Buyer VAT/business/tax/registration identifiers
- Identifier format and scheme
- Government identifier and routing
- Explicit consumer evidence
- Seller and buyer country
- Domestic/cross-border context
- Country/profile requirements
- Confidence and contradiction analysis

## 12.4 Evidence controls

- B2G takes precedence over B2B only with authoritative or sufficiently strong public evidence.
- Missing VAT alone must never produce B2C.
- Endpoint alone must never produce B2B.
- Government keyword alone must never produce High/Medium B2G.
- Invalid VAT must not support B2B.

## 12.5 Expected issue types

```text
CUSTOMER_TYPE_UNDETERMINED
CUSTOMER_TYPE_MISMATCH
CONFLICTING_CUSTOMER_SIGNALS
CONFLICTING_REPEATED_CUSTOMER_FIELDS
PLACEHOLDER_OR_DUMMY_IDENTIFIER
MISSING_BUYER_IDENTIFIER
INVALID_BUYER_VAT_FORMAT
INVALID_BUYER_IDENTIFIER_FORMAT
IDENTIFIER_SCHEME_MISSING
IDENTIFIER_VALUE_MISSING
IDENTIFIER_SCHEME_MISMATCH
IDENTIFIER_SCHEME_NOT_CONFIGURED
IDENTIFIER_COUNTRY_MISMATCH
INSUFFICIENT_GOVERNMENT_EVIDENCE
MISSING_GOVERNMENT_ROUTING_FIELD
POSSIBLE_BUYER_SELLER_IDENTIFIER_COLLISION
B2B_STRUCTURE_MISMATCH
B2G_STRUCTURE_MISMATCH
B2C_STRUCTURE_MISMATCH
VAT_TREATMENT_MISMATCH
INCOMPLETE_VALIDATION_SCOPE
```

## 12.6 Positive assertions

- A government buyer with VAT and authoritative public evidence remains B2G.
- Explicit consumer evidence with no business/government contradiction supports B2C.
- Structurally usable business evidence supports B2B.

## 12.7 Anomaly assertions

- Placeholder VAT returns `PLACEHOLDER_OR_DUMMY_IDENTIFIER`.
- B2C declaration with strong business identifiers returns `CUSTOMER_TYPE_MISMATCH`.
- Government-like name without authoritative evidence returns `UNDETERMINED` or insufficient evidence.
- Missing scheme reduces evidence confidence and may return `IDENTIFIER_SCHEME_MISSING` or `NOT_VERIFIABLE`.

---

# 13. Business Rule 13 Testing

## 13.1 Agent

**Invoice Number Sequence Monitoring**

## 13.2 Execution model

This is a population-level agent. Do not run gap detection on each XML independently. Provide all comparable invoices in the same seller/series scope.

## 13.3 Required checks

- Logical document consolidation
- Business invoice-number field selection
- Seller/legal entity scope
- Document-family scope
- Series/prefix/period scope
- Population completeness
- Pattern and increment confidence
- Internal gaps
- Exact and conflicting duplicates
- Submission replay
- Chronology order
- Series resets and transitions

## 13.4 Expected issue types

```text
MISSING_INVOICE_NUMBER
INVALID_INVOICE_NUMBER
INVOICE_NUMBER_FIELD_CONFLICT
DUPLICATE_INVOICE_NUMBER
DUPLICATE_INVOICE_NUMBER_CONFLICT
REPEATED_SUBMISSION_EVENT
POSSIBLE_INVOICE_NUMBER_REUSE
SEQUENCE_GAP
POSSIBLE_SEQUENCE_GAP
DOCUMENTED_SEQUENCE_GAP
OUT_OF_SEQUENCE_DOCUMENT
UNEXPLAINED_SEQUENCE_RESET
SERIES_BOUNDARY_UNCLEAR
SERIES_PATTERN_CONFLICT
UNEXPLAINED_PATTERN_CHANGE
CONFLICTING_REPEATED_NUMBERING_DATA
INCOMPLETE_VALIDATION_SCOPE
```

## 13.5 Positive assertions

- Repeated line rows are consolidated into one logical invoice.
- Different seller scopes are not compared.
- Valid year or series boundaries do not create false gaps.
- Same-day invoices with date-only fields are not flagged as out of sequence.

## 13.6 Anomaly assertions

- A reliable sequence that skips one internal counter returns `SEQUENCE_GAP`.
- Same number with different buyer/date/amount returns `DUPLICATE_INVOICE_NUMBER_CONFLICT`.
- A lower sequence number issued later may return `OUT_OF_SEQUENCE_DOCUMENT` when chronology is reliable.
- Incomplete samples return `NOT_VERIFIABLE`, not fabricated missing numbers.

---

## 14. Recommended Test Execution Matrix

Execute every compatible test across:

```text
Country: BE, FR, PL
Source: SAP, Custom ERP
Agent: BR-1, BR-4, BR-6, BR-7, BR-12, BR-13
Mode: Positive, Atomic, Combined, Negative Assertion
Environment: Local, Lower Environment, Integrated VAT Platform
```

For BR-13, submit the complete country/source series as a population. For invoice-level agents, submit one logical invoice group at a time unless batch execution is explicitly supported.

---

## 15. Result Comparison Rules

Compare actual results against the master workbook.

### 15.1 True Positive

The agent returns the expected issue type against the expected invoice and evidence.

### 15.2 False Negative

An expected issue is missing from the result.

### 15.3 False Positive

The agent returns an issue that is listed under `Negative_Assertions`, or an unsupported issue without evidence.

### 15.4 Classification Error

The agent detects an anomaly but uses an incorrect issue type, severity, field, or final status.

### 15.5 Suggestion Error

The anomaly is correct, but the proposed value or correction:

- Changes business meaning
- Is unsupported by available evidence
- Recommends a numeric value when the authoritative amount is unknown
- Ignores country/profile configuration

---

## 16. Core QA Metrics

Calculate the following metrics per business rule, source system, and country.

```text
Precision = True Positives / (True Positives + False Positives)
Recall = True Positives / (True Positives + False Negatives)
False Positive Rate = False Positives / Negative Assertions Executed
Detection Rate = Test Cases with all expected findings / Executed Test Cases
JSON Compliance Rate = Valid JSON Results / Executed Test Cases
Evidence Completeness = Findings with required evidence / Total Findings
Suggestion Accuracy = Supported corrections / Total Corrections
```

Recommended release gates:

```text
Critical false negatives: 0
Critical false positives: 0
JSON compliance: 100%
Required-field output completeness: 100%
Prompt/version traceability: 100%
```

Set numeric precision/recall thresholds according to the project release policy.

---

## 17. Regression Test Checklist

Before approving a prompt version:

- [ ] Prompt checksum/version is recorded
- [ ] Correct prompt is loaded for the business rule
- [ ] Country configuration is loaded
- [ ] Source mapping is loaded
- [ ] SAP XML structure is preserved
- [ ] Custom ERP XML structure is preserved
- [ ] Positive controls pass
- [ ] All expected Critical findings are detected
- [ ] Combined scenarios return every independent finding
- [ ] Negative assertions do not trigger
- [ ] Actual and expected values are correct
- [ ] Formulas and tolerances are correct
- [ ] Root causes are evidence-supported
- [ ] Suggested fixes are specific and safe
- [ ] JSON schema is valid
- [ ] No unsupported issue type is returned
- [ ] No required check is omitted
- [ ] Final status follows severity rules
- [ ] Results are stored with execution metadata

---

## 18. Configuration Deployment Validation

The approved prompts must be tested after loading them into:

```text
BYODM
AIALWIN
[InvoiceDACPrompt]
```

### 18.1 Before update

- Export current prompt records
- Record environment, database, schema, table, and record key
- Record current version and checksum
- Validate maximum field length and Unicode support
- Confirm active/inactive behavior
- Prepare rollback scripts or records

### 18.2 After update

- Read back the stored prompt
- Compare stored text checksum with approved file
- Verify no truncation
- Verify line breaks, quotes, Unicode, and JSON instructions
- Verify one intended active record per scope
- Confirm country/source/profile mappings
- Run smoke tests
- Run all 60 XML regression tests
- Compare against `Expected_Findings` and `Negative_Assertions`

### 18.3 Deployment tracker fields

```text
Business Rule ID
Prompt File
Prompt Version
Prompt Checksum
Database
Schema
Table
Record Key
Country Scope
Source-System Scope
Target Environment
Backup Completed
Updated By
Updated Timestamp
Activation Status
Smoke-Test Status
Regression Status
Approval Status
Rollback Reference
```

---

## 19. Defect Reporting Template

Use the following format for agent defects:

```markdown
### Defect Title
[Agent] [Country] [Source] concise anomaly

### Business Rule
BR-X: Rule name

### Test Data
- File:
- Invoice ID:
- Country:
- Source system:
- Prompt version:

### Expected Result
- Expected status:
- Expected issue type:
- Expected actual value:
- Expected value or rule:
- Expected severity:
- Expected suggested fix:

### Actual Result
- Actual status:
- Actual issue type:
- Actual evidence:
- Actual suggested fix:

### Business Impact
Explain the XML, tax, reporting, classification, audit, or false-positive impact.

### Reproduction Steps
1. Load the specified prompt and configuration.
2. Submit the test XML or invoice population.
3. Capture the raw result.
4. Compare with the master workbook.

### Attachments
- Source XML
- Prompt file
- Raw output JSON
- Expected-results row
- Execution logs
```

---

## 20. Exit Criteria

Agent testing is complete only when:

- All six business-rule agents have completed positive, anomaly, and negative-assertion tests
- Belgium, France, and Poland are covered
- SAP and Custom ERP are covered
- All Critical expected findings are detected
- No Critical false positive remains open
- Output JSON passes schema validation
- Root causes and fixes are evidence-supported
- Prompt versions are traceable to deployed configuration
- Regression results are reviewed and approved
- Rollback information exists for deployed prompt records

---

## 21. Known Constraints

1. An agent cannot validate a field that is not present or mapped from the source system.
2. A free-text mention of a numeric value must not replace a dedicated mapped numeric field.
3. XML-invalid control characters cannot be embedded in XML fixtures that must remain parseable.
4. Format-valid VAT or business identifiers are not externally verified unless an authorized verification result is provided.
5. Country/profile-specific requirements must return `NOT_VERIFIABLE` when configuration is absent.
6. The number-sequence agent requires a population, not a single-invoice request.
7. Intentional duplicate invoice numbers must remain in the sequence test population.
8. Seller identifiers must remain stable inside one numbering series; otherwise, the sequence scope will split incorrectly.

---

## 22. Quick Start

1. Extract the six prompt files into `prompts/`.
2. Extract `EInvoice_60_Samples_BE_FR_PL_SAP_CustomERP_v3.zip` into `test-data/`.
3. Place `EInvoice_Agent_Test_Master_60_Samples_v3.xlsx` under `expected-results/`.
4. Configure the source-field mappings.
5. Run BR-1, BR-4, BR-6, BR-7, and BR-12 per logical invoice.
6. Run BR-13 per country/source numbering population.
7. Store raw JSON results.
8. Normalize results without changing evidence.
9. Compare findings and negative assertions with the master workbook.
10. Publish QA metrics and defects.

---

## 23. Final Testing Principle

> An agent passes testing only when the agent detects the intended anomaly, preserves the exact evidence, applies the correct issue type and severity, recommends a supported correction, returns the correct final status, and does not flag the documented negative assertions.
