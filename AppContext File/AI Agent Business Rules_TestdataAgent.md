# AI Agent Business Rules QA Knowledge Base

## E-Invoicing Agent Validation, Prompt Engineering, XML Test Data, Ingestion Safety, and Expected Results

**Document purpose:** Future reference for AI engineers, prompt engineers, QA leads, automation engineers, and business-rule owners testing e-invoice validation agents across Belgium, France, and Poland.

**Covered source systems:**

- SAP IDoc, based on the `INVOIC02` and `IDOC` structure
- Custom ERP, based on the OAGIS-style `ProcessInvoice` structure

**Covered business rules:**

- BR1: Invoice completeness and XML readiness
- BR4: Free-text and XML character safety
- BR6: Invoice totals and mathematical integrity
- BR7: Invoice type classification and suggestion
- BR12: Customer type classification, B2B, B2G, and B2C
- BR13: Invoice-number sequence monitoring

---

# 1. Executive Summary

The primary objective is to create ingestion-passing e-invoice XML files that contain deliberate business-level anomalies for AI-agent testing.

A valid agent test file must satisfy two separate requirements:

1. The document must pass XML parsing and application ingestion.
2. The document must still contain one or more anomalies that the relevant business-rule agents should identify.

These requirements must never be confused.

A file rejected by ingestion does not test an AI agent because the invoice never reaches the agent.

The core test-data principle is:

```text
Preserve every XML tag and every ingestion-mandatory value.
Inject anomalies only into fields or relationships that survive ingestion.
```

Negative tests must be separated into two categories:

```text
Pre-ingestion negative tests
Agent-level negative tests
```

Pre-ingestion negative tests intentionally violate XML or mapper requirements. Agent-level tests preserve ingestion requirements and inject business-rule anomalies.

---

# 2. Fundamental Test Architecture

## 2.1 Validation layers

Every generated XML file should pass the following gates before being classified as agent test data.

### Gate 1: File integrity

Validate:

- File exists.
- File size is greater than zero.
- UTF-8 encoding is valid.
- Exactly one XML root element exists.
- XML parsing succeeds.
- The file is not truncated.
- The file is not replaced with an empty Document Center payload.

### Gate 2: XML structure

Validate:

- The complete source-template tag hierarchy is preserved.
- No XML tag is accidentally deleted.
- No XML tag is invented unless supported by the ingestion schema.
- Namespace declarations remain intact.
- Segment or element ordering remains compatible with the source template.
- Required attributes remain present.

### Gate 3: Ingestion contract

Validate:

- Every mandatory mapper field is populated.
- Mandatory party data is populated.
- Mandatory line data is populated.
- Mandatory totals are populated.
- Required dates and document identifiers are populated.
- Tax-category values belong to the approved source-system allowlist.

### Gate 4: Database constraints

Validate, when the constraint definitions are available:

- Tax-category check constraints
- Allowed document-type mappings
- Numeric precision and scale
- Country and currency formats
- Uniqueness constraints
- Required foreign-key or lookup values

### Gate 5: Agent anomaly integrity

Validate:

- Every file contains at least one expected agent finding.
- Each anomaly is intentionally created.
- Expected actual value matches the XML source value.
- Expected suggested value is deterministic.
- Multiple findings are separate rows or cards.
- The same field is not duplicated for one rule and logical entity.

---

# 3. Rule Ownership and Separation

Every business rule must have clear ownership. Overlapping agents create duplicate cards, contradictory suggestions, and hallucinations.

## BR1 owns

- Conditional completeness
- Required business evidence
- XML-readiness completeness after ingestion
- Missing conditional sections that the ingestion layer permits

## BR4 owns

- Unsafe or restricted characters in eligible text fields
- XML-invalid controls when such content can reach the validation layer
- Encoding corruption
- Non-breaking and invisible characters
- Deterministic text correction

## BR6 owns

- Line-extension calculations
- Net-total calculations
- Tax-total calculations
- Gross-total calculations
- Payable-amount calculations

## BR7 owns

- Invoice-type classification
- Document type versus financial behavior mismatch
- Suggested document type

## BR12 owns

- B2B, B2G, and B2C classification
- Buyer identifier quality
- Country and identifier consistency
- Government evidence sufficiency
- Placeholder or dummy identifiers

## BR13 owns

- Number-sequence gaps
- Chronology anomalies
- Duplicates within a stable sequence scope
- Pattern discontinuity within a valid monitoring population

Agents must not convert findings owned by another rule into duplicate findings.

---

# 4. BR1: Invoice Completeness and XML Readiness

## 4.1 Objective

BR1 evaluates whether the mapped invoice contains sufficient business information for downstream e-invoice generation.

BR1 must not be tested by removing data that the ingestion mapper requires to create the invoice record.

## 4.2 Critical lesson

Earlier test packs blanked values such as invoice number, seller name, buyer name, line number, quantities, item description, and totals. The ingestion service correctly rejected those files before the agent ran.

The corrected design principle is:

```text
If a field is mandatory for ingestion, never blank it in an agent-level BR1 XML.
```

## 4.3 Suitable ingestion-passing BR1 scenarios

Use conditional business evidence that can remain absent without breaking ingestion, for example:

- Reverse-charge context without sufficient legal-basis evidence
- Exemption context without supporting reason
- Correction invoice without an adequate related-document reference, if the mapper permits it
- Endpoint or routing evidence incomplete while mandatory buyer information is populated
- Conditional governmental evidence incomplete
- Conflicting repeated values that survive mapping
- Country-specific conditional evidence absent

## 4.4 Unsuitable agent-level BR1 scenarios

Do not blank:

- Invoice number
- Mandatory document type
- Mandatory issue date
- Mandatory supplier name or address
- Mandatory buyer name or address
- Mandatory line number
- Mandatory item identifier
- Mandatory line description
- Mandatory quantity
- Mandatory unit price
- Mandatory line tax
- Mandatory totals

These scenarios belong in a separate pre-ingestion rejection suite.

## 4.5 Expected output behavior

- Generate one finding per missing or inadequate conditional item.
- Do not combine multiple missing items into one finding.
- Do not invent a missing field.
- Use `Source validation required` when a safe business value cannot be derived.
- Do not produce suggestions that contain SQL, XML, or explanations.

---

# 5. BR4: Free-Text and XML Character Safety

## 5.1 Objective

BR4 validates permitted text fields for exact characters that may create XML, encoding, transmission, matching, or application policy risk.

BR4 must be evidence-gated and deterministic.

## 5.2 Primary anti-hallucination rule

```text
No exact character means no finding.
No exact Unicode code point means no finding.
No changed corrected value means no finding.
```

The agent must not infer hidden characters from visual appearance.

## 5.3 Eligible free-text fields

Typical eligible fields include:

- BuyerName
- BuyerTradingName
- BuyerStreet
- BuyerCity
- SellerName
- SellerTradingName
- SellerStreet
- SellerCity
- Description
- PaymentTermsText
- EYAIComments

Protected identifiers must not receive general free-text cleanup.

## 5.4 Protected fields

Examples:

- InvoiceId
- UUID
- BatchId
- SourceSystem
- DocumentTypeCode
- CurrencyCode
- Country codes
- Tax identifiers
- VAT numbers
- Purchase-order references
- Item identifiers
- TaxCategoryCode
- Payment codes
- IBAN
- SWIFT or BIC

Structured punctuation in identifiers can be legitimate.

## 5.5 Clean-value rule

A true free-text value should pass when the value contains only:

- Valid Unicode letters
- Numbers
- Normal spaces, U+0020
- Periods
- Commas
- Correctly encoded local-language letters and diacritics

Belgian, French, Polish, Dutch, German, and other supported European letters must not be flagged merely because the letters are non-ASCII.

Examples in prompts are calibration examples only. Never hardcode company names or exact strings as safe or unsafe values.

## 5.6 Character classes

### Invalid XML 1.0 characters

Examples include:

- U+0000
- U+0001 through U+0008
- U+000B
- U+000C
- U+000E through U+001F
- Isolated surrogate code points

Tab, line feed, and carriage return are valid XML 1.0 controls.

### Invisible or formatting characters

Examples include:

- U+00A0 non-breaking space
- U+200B zero-width space
- U+200C zero-width non-joiner
- U+200D zero-width joiner
- U+2060 word joiner
- U+FEFF embedded byte order mark
- Directional formatting marks

### Encoding corruption

Examples include:

- U+FFFD replacement character
- Mojibake
- Broken mixed encoding

The agent must not guess the intended value. Use `Source validation required` when restoration is unsafe.

### Application-restricted punctuation and symbols

Examples include:

- Ampersand
- Vertical bar
- Parentheses
- Brackets
- Braces
- Slash and backslash
- Colon and semicolon
- Hash
- At sign
- Percent sign
- Exclamation mark
- Hyphen and underscore, when restricted by the configured UI policy
- Curly quotation marks
- En dash and em dash
- Emoji and decorative symbols

Application-restricted punctuation is not automatically invalid XML. The prompt must distinguish XML validity from application policy.

## 5.7 Deterministic transformation examples

```text
A & B -> A and B
A&B -> A and B
Street One | Building Two -> Street One, Building Two
Standard service package (monthly) -> Standard service package monthly
“Consulting Services” -> Consulting Services
Premium service — launch -> Premium service launch
Deployment 🚀 service -> Deployment service
```

For non-breaking space:

```text
U+00A0 -> U+0020
```

## 5.8 XML serialization rule

The logical source value may contain an ampersand, but the serialized XML must remain well formed.

```xml
<NAME1>Global Retail &amp; Supply</NAME1>
```

After XML parsing, the mapped business value is:

```text
Global Retail & Supply
```

Never insert a raw ampersand into XML text. Never insert raw `<` into text content.

## 5.9 One field, one finding

If one field contains several suspicious characters:

- Identify all distinct characters.
- Identify all Unicode code points.
- Produce one corrected complete field value.
- Return one finding for that field.

Different impacted fields must remain separate findings.

## 5.10 Suggested-value contract

- `actual_value` must be the unchanged source value.
- `expected_value` must be the complete corrected value or `Source validation required`.
- `suggested_fix` must equal the corrected value when deterministic correction exists.
- Suggested value must never be blank.
- Suggested value must not be free-form rewriting.
- Do not translate, paraphrase, spell-correct, or replace a name.

## 5.11 Duplicate protection

Invoice-level uniqueness key:

```text
InvoiceId + BusinessRule + field_name
```

Line-level uniqueness key:

```text
InvoiceId + BusinessRule + stable LineItemId or LineId + field_name
```

Only `findings[]` should create actionable D&S cards. `checks[]` must remain diagnostic.

---

# 6. BR6: Invoice Totals and Mathematical Integrity

## 6.1 Objective

BR6 validates mathematical consistency without changing business classification.

## 6.2 Core equations

```text
LineExtensionAmount = Quantity × UnitPrice
```

```text
LineExtensionTotal = sum of line extension amounts
```

```text
TaxTotal = sum of line tax amounts
```

```text
TaxInclusiveTotal = TaxExclusiveTotal + TaxTotal
```

```text
PayableAmount = TaxInclusiveTotal - PrepaidAmount
```

Allowance and charge terms must be included if the schema provides those values.

## 6.3 Test scenarios

- Incorrect line extension amount
- Correct lines but stale line-extension total
- Incorrect tax total
- Correct net and tax with incorrect gross total
- Incorrect payable amount
- Multiple independent total anomalies
- Different errors in two different numeric fields

## 6.4 Finding behavior

- One finding per impacted numeric field
- Do not repeat the same field twice
- Do not combine `TaxTotal` and `TaxInclusiveTotal` into one finding
- Use exact current and calculated values
- Suggested value must be numeric only
- Remove insignificant trailing zeros

Example:

```text
Field: TaxInclusiveTotal
Current: 606.63
Suggested: 608.63
```

Do not output:

```text
608.6300
```

when trailing zeros are not required.

## 6.5 Taxable amount terminology

For e-invoice comparison, taxable amount represents the net or tax base.

---

# 7. BR7: Invoice Type Classification and Suggestion

## 7.1 Objective

BR7 determines whether the coded invoice type matches financial behavior and supporting context.

## 7.2 Inputs

Typical inputs include:

- DocumentTypeCode
- SAP `FKART_RL`
- Custom ERP `TransactionTypeCode`
- Quantity signs
- Line amount signs
- Net, tax, gross, and payable signs
- Related-document references
- Correction or cancellation context

## 7.3 Key scenarios

- Credit-note code with positive invoice behavior
- Standard invoice code with negative values
- Alternate type code inconsistent with financial behavior
- Missing or unsupported type code, only when ingestion permits the value
- Correction-type context without supporting relationship

## 7.4 Expected behavior

- Report actual type code.
- Suggest the appropriate supported type code.
- Do not hardcode country-specific codes without source mapping.
- Do not infer the type from one field alone when financial evidence is available.
- Avoid duplicate type suggestions.
- BR7 must remain separate from BR6 numeric findings.

---

# 8. BR12: Customer Type Classification

## 8.1 Objective

BR12 classifies the transaction as B2B, B2G, or B2C using evidence in the invoice.

## 8.2 General evidence

Possible evidence includes:

- Buyer name
- Buyer country
- Customer account identifier
- Buyer tax identifier
- VAT number
- Government identifier
- Routing or endpoint evidence
- Supplier and buyer relationship
- Invoice context

## 8.3 B2B

Typical evidence:

- Usable business customer identifier
- Country-consistent tax or VAT identifier
- Legal business name and address

Negative scenarios:

- Placeholder identifier such as `DUMMY` or `TEST`
- Invalid VAT format
- Identifier country prefix inconsistent with BuyerCountry
- Conflicting customer identifiers

## 8.4 B2G

Typical evidence:

- Government authority evidence
- Government identifier
- Public-sector routing or endpoint evidence

A name containing words such as public, ministry, municipality, authority, or government is not enough by itself.

Negative scenario:

```text
Public-sector appearing name with no authoritative government evidence
```

Expected result:

```text
INSUFFICIENT_GOVERNMENT_EVIDENCE
```

## 8.5 B2C

Typical evidence:

- Consumer context
- No reliable business or government identifier
- Customer record aligned with supported B2C rules

Do not classify B2C merely because a VAT number is absent if other business evidence exists.

## 8.6 Anti-hallucination controls

- Do not infer customer type from name alone.
- Do not invent an identifier.
- Do not treat examples as hardcoded rules.
- Use `NOT_VERIFIABLE` when evidence is insufficient.
- Return field-level findings separately.

---

# 9. BR13: Invoice-Number Sequence Monitoring

## 9.1 Objective

BR13 monitors invoice-number sequences within a stable and comparable population.

## 9.2 Applicability rule

When one XML file contains only one invoice, BR13 usually lacks a sequence population.

Expected single-file behavior:

```text
NOT_APPLICABLE
findings = []
```

BR13 should be evaluated when:

- One file contains multiple invoices, or
- Multiple invoices are intentionally evaluated as one batch or folder population

## 9.3 Stable monitoring scope

A sequence scope should consider compatible attributes such as:

- Country
- Source system
- Supplier or legal entity
- Invoice series or prefix
- Fiscal period
- Document family

Do not compare unrelated number formats.

## 9.4 Scenarios

- Sequence gap, for example 01008 followed by 01010
- Duplicate invoice number
- Out-of-sequence chronology, for example a higher number with an earlier issue date
- Prefix or pattern discontinuity
- Reset behavior across fiscal periods

## 9.5 Uniqueness conflict

If the test-data requirement mandates unique invoice numbers, duplicate-number tests must be placed in a dedicated BR13 duplicate suite. Do not silently violate the uniqueness requirement in the general pack.

---

# 10. SAP XML Reference and Ingestion Contract

## 10.1 Root structure

```text
INVOIC02
  IDOC
    EDI_DC40
    E1EDK01
    E1EDK03
    E1EDK02
    E1EDKA1
    E1EDKT1
    E1EDP01
    E1EDS01
```

All supplied template tags and segment attributes should remain intact.

## 10.2 Important SAP mappings

### Control record

```text
EDI_DC40/DOCNUM
EDI_DC40/SNDPOR
EDI_DC40/SNDPRN
EDI_DC40/RCVPRN
EDI_DC40/CREDAT
EDI_DC40/CRETIM
EDI_DC40/SERIAL
```

### Header

```text
E1EDK01/BELNR
E1EDK01/FKART_RL
E1EDK01/CURCY
E1EDK01/HWAER
E1EDK01/ZTERM
```

### Dates

```text
E1EDK03[IDDAT=012]/DATUM
E1EDK03[IDDAT=026]/DATUM
```

### Parties

```text
E1EDKA1[PARVW=LF] = supplier
E1EDKA1[PARVW=RE] = invoice recipient or buyer
E1EDKA1[PARVW=WE] = ship-to or delivery party
```

### Lines

```text
E1EDP01/POSEX
E1EDP01/MATNR
E1EDP01/MENGE
E1EDP01/MENEE
E1EDP01/NETWR
E1EDP01/MWSBT
E1EDP01/MWSKZ
E1EDP01/VPREI
E1EDP19[QUALF=001]/KTEXT
```

### Totals

```text
E1EDS01[SUMID=211]/SUMME = net or line-extension total
E1EDS01[SUMID=212]/SUMME = tax total
E1EDS01[SUMID=010]/SUMME = gross or payable-related total in the mapped implementation
```

## 10.3 Known mandatory SAP ingestion fields

The reported ingestion errors established that these values must remain populated:

```text
E1EDK01/BELNR
E1EDK01/FKART_RL
E1EDK03[IDDAT=012]/DATUM
E1EDKA1[PARVW=LF]/NAME1
E1EDKA1[PARVW=LF]/STRAS
E1EDKA1[PARVW=RE]/NAME1
E1EDKA1[PARVW=RE]/STRAS
E1EDKA1[PARVW=RE]/PSTLZ
E1EDKA1[PARVW=WE]/STRAS
E1EDKA1[PARVW=WE]/ORT01
E1EDKA1[PARVW=WE]/PSTLZ
E1EDKA1[PARVW=WE]/LAND1
E1EDP01/POSEX
E1EDP19[QUALF=001]/KTEXT
E1EDP01/MENGE
E1EDP01/MENEE
E1EDP01/VPREI
E1EDP01/MWSBT
E1EDS01[SUMID=211]/SUMME
E1EDS01[SUMID=212]/SUMME
E1EDS01[SUMID=010]/SUMME
```

## 10.4 SAP tax-category allowlist

Use only:

```text
A0
V0
V9
RC
```

Do not introduce another SAP tax-category source value unless the lookup and database constraint explicitly support it.

---

# 11. Custom ERP XML Reference and Ingestion Contract

## 11.1 Root structure

```text
ProcessInvoice
  ApplicationArea
  DataArea
    Invoice
      InvoiceHeader
      Supplier
      Buyer
      InvoiceLine
      InvoiceTotals
```

Namespaces, schema location, attributes, and every template tag should remain intact.

## 11.2 Important Custom ERP mappings

### Application area

```text
ApplicationArea/Sender/LogicalID
ApplicationArea/Sender/ReferenceID
ApplicationArea/CreationDateTime
ApplicationArea/BODID
```

### Header

```text
InvoiceHeader/DocumentID/ID
InvoiceHeader/AlternateDocumentID/ID
InvoiceHeader/TransactionTypeCode
InvoiceHeader/DocumentDateTime
InvoiceHeader/DueDateTime
InvoiceHeader/PaymentTerms
InvoiceHeader/Currency
InvoiceHeader/PurchaseOrderReference
```

### Parties

```text
Supplier/PartyIDs/ID
Supplier/PartyIDs/TaxID
Supplier/Name
Supplier/Location/Address
Buyer/PartyIDs/ID
Buyer/PartyIDs/TaxID
Buyer/Name
Buyer/Location/Address
```

### Lines

```text
InvoiceLine/LineNumber
InvoiceLine/Item/ItemID
InvoiceLine/Item/Description
InvoiceLine/Quantity
InvoiceLine/UnitPrice
InvoiceLine/ExtendedAmount
InvoiceLine/Tax/TaxTypeCode
InvoiceLine/Tax/Percent
InvoiceLine/Tax/TaxableAmount
InvoiceLine/Tax/TaxAmount
```

### Totals

```text
InvoiceTotals/SubTotalAmount
InvoiceTotals/TaxAmount
InvoiceTotals/TotalAmount
InvoiceTotals/PayableAmount
```

## 11.3 Known mandatory Custom ERP ingestion fields

```text
InvoiceHeader/DocumentID/ID
InvoiceHeader/TransactionTypeCode
InvoiceHeader/DocumentDateTime
Supplier/Name
Supplier/Location/Address/AddressLine
Buyer/Name
InvoiceLine/LineNumber
InvoiceLine/Item/ItemID
InvoiceLine/Item/Description
InvoiceLine/Quantity
InvoiceLine/UnitPrice
InvoiceTotals/PayableAmount
```

Keep Buyer address populated as a defensive ingestion requirement even if not present in every reported error.

## 11.4 Custom ERP tax-category allowlist

Use only:

```text
VAT
GST
EXEMPT
REVERSE
```

Do not introduce another Custom ERP tax-category source value unless the lookup and database constraint explicitly support it.

---

# 12. Tax-Code and Tax-Rate Guidance

Tax-category source values and numeric rates are separate concepts.

The approved source-value allowlists are authoritative:

```text
SAP: A0, V0, V9, RC
Custom ERP: VAT, GST, EXEMPT, REVERSE
```

The exact rate mapped to each source value must come from the environment lookup or source-system mapping. Do not assume a universal semantic meaning from the code name alone.

Before production use, validate:

- SourceSystem
- LookupType
- SourceValue
- Target TaxCategoryCode
- Applicable tax rate
- Country applicability
- Effective dates

If the database reports `CK_LineItem_TaxCategory`, inspect the check constraint and lookup table before generating additional codes.

---

# 13. Ingestion Failures Encountered and Lessons Learned

## 13.1 Missing mandatory values

Observed failures included missing:

- SAP invoice number
- SAP document type
- SAP supplier and buyer values
- SAP line identity and pricing values
- SAP summary totals
- Custom ERP DocumentID
- Custom ERP supplier and buyer name
- Custom ERP line values
- Custom ERP PayableAmount

Lesson:

```text
Do not use ingestion-mandatory fields as agent-level anomaly fields.
```

## 13.2 XML EntityName parser error

Likely cause:

```text
Raw ampersand inserted into XML text
```

Correction:

```xml
&amp;
```

Use an XML library or serializer instead of string concatenation.

## 13.3 Root element is missing

Possible causes:

- Empty file
- Truncated upload
- Failed Document Center download
- Non-XML content
- Zero-byte content

This is not an agent business-rule failure.

## 13.4 No data found in file

Possible causes:

- Parser did not recognize the source structure
- Required invoice envelope absent
- Wrong namespace or root
- Empty content
- Mapper found no invoice data

This is an ingestion or mapping failure, not a BR12 result.

## 13.5 Tax-category database constraint

Observed error:

```text
CK_LineItem_TaxCategory
```

Lesson:

```text
XML validity does not prove database compatibility.
```

Use only the approved source-value allowlists and validate target mappings.

## 13.6 Document Center failures

Observed issues included:

- Failed file download
- Document status `Ready` when `Unmapped` was expected
- Reprocessing an already-transitioned document

These are operational workflow issues.

Recommended controls:

- Compare SHA-256 before and after upload.
- Confirm file size after download.
- Use a fresh FileGUID for reruns.
- Ensure status is `Unmapped` before ingestion.
- Separate content defects from storage and workflow defects.

---

# 14. Test-Data Design for Breaking the Agent

## 14.1 General principles

- Every invoice field should be unique where practical.
- Every invoice number must be unique unless intentionally testing BR13 duplicates.
- SAP and Custom ERP should not use identical anomaly assignments for corresponding samples.
- Every file should contain one or more intentional findings.
- Multi-rule files should include independent anomalies.
- One issue must not accidentally trigger unsupported extra rules.
- Country data must be realistic and country-consistent except where the inconsistency is intentional.

## 14.2 Example SAP combinations

```text
BR1 + BR4
BR4 + BR6 + BR7
BR6 + BR7 + BR12
BR1 + BR4 + BR6 + BR7
BR4 + BR12
BR6 + BR12
BR1 + BR4 + BR12
BR4 + BR6
BR12 + BR13
BR6 + BR7 + BR13
```

## 14.3 Example Custom ERP combinations

```text
BR1 + BR4 + BR12
BR4 + BR6 + BR7 + BR12
BR1 + BR4 + BR6 + BR7
BR4 + BR6 + BR12
BR4 + BR6 + BR7
BR4 + BR12 + BR13
BR6 + BR7 + BR12 + BR13
```

## 14.4 Source-specific differentiation

SAP tests should use SAP fields and behavior:

- `FKART_RL`
- `MWSKZ`
- `NETWR`
- `MWSBT`
- `SUMID`
- Party roles `LF`, `RE`, and `WE`

Custom ERP tests should use Custom ERP fields and behavior:

- `TransactionTypeCode`
- `TaxTypeCode`
- `ExtendedAmount`
- `InvoiceTotals`
- `PartyIDs`
- OAGIS namespaces and nested elements

Do not mechanically copy the same bad value into both systems.

## 14.5 Country coverage

The final full test-data structure should support:

```text
Belgium/SAP/10 XML files
Belgium/CustomERP/10 XML files
France/SAP/10 XML files
France/CustomERP/10 XML files
Poland/SAP/10 XML files
Poland/CustomERP/10 XML files
```

Total:

```text
60 XML files
```

---

# 15. Master Expected-Results Workbook Design

One master workbook should cover the entire data pack.

## 15.1 Required sheets

### Expected Findings

One row per rule, field, and logical issue.

Recommended columns:

```text
SampleID
Country
SourceSystem
FileName
InvoiceId
ScenarioCombination
BusinessRule
Level
LineKey
ImpactedField
ActualValue
ExpectedValue
IssueType
SuggestedFix
Severity
```

### Test Catalog

One row per XML file.

Recommended columns:

```text
SampleID
Country
SourceSystem
FileName
InvoiceId
ScenarioCombination
ExpectedStatus
ExpectedFindingCount
TaxCategoryCode
TaxRate
XMLTagSignature
IngestionMandatoryFields
```

### BR13 Batch Expectations

Document:

- Monitoring scope
- Population size
- Observed sequence
- Gap
- Chronology anomaly
- Single-file expected behavior
- Batch expected behavior

### Ingestion Precheck

One row per file:

```text
FileName
XMLParse
TagSignature
MandatoryFields
MissingFields
TaxCategoryAllowlist
IngestionPrecheck
```

### Tax Code Audit

One row per file or line:

```text
SampleID
Country
SourceSystem
TaxCategoryCode
TaxRate
AllowlistStatus
```

### Validation Summary

Include:

- Total files
- Files per folder
- Unique invoice count
- XML parse failures
- Tag-signature mismatches
- Mandatory-field failures
- Tax allowlist failures
- Files without findings

### Read Me

Explain:

- Test design
- Ingestion boundary
- BR13 batch execution
- Tax allowlists
- Prompt and expected-result conventions

---

# 16. Agent Output and UI Contract

## 16.1 One finding per issue

Each distinct affected field must produce a separate finding.

Do not combine:

- Field names
- Actual values
- Expected values
- Suggested values

## 16.2 Multiple characters within one field

One field with several special characters produces one BR4 finding for that field.

## 16.3 Multiple numeric fields

Two incorrect totals produce two BR6 findings.

## 16.4 Suggested value

Suggested value must be:

- Complete
- Non-empty
- Deterministic
- Appropriate for UI display
- Free from SQL and code
- Free from explanations

## 16.5 Checks versus findings

```text
checks[] = diagnostic evidence
findings[] = actionable anomalies
```

Only `findings[]` should create D&S review cards.

## 16.6 Deduplication

Recommended persistence fingerprint:

```text
InvoiceId + BusinessRule + stable line key when applicable + field_name
```

For retry protection, the application should make this key idempotent.

---

# 17. Prompt Engineering Guardrails

## 17.1 Evidence before conclusion

The prompt must require exact source evidence before outputting a finding.

## 17.2 Deterministic transformations

The prompt should define explicit transformations rather than asking the model to rewrite text safely.

## 17.3 No hardcoded examples

Examples are illustrative only.

Never use:

- Exact-match safe lists
- Exact-match unsafe lists
- Invoice-specific exceptions
- Company-specific exceptions
- Test-data-specific exceptions

## 17.4 Field allowlists

Each prompt should define exactly which mapped fields are eligible.

## 17.5 Missing-field behavior

Do not invent a field that is absent from the input.

## 17.6 Multi-country behavior

Use country to prevent false positives and apply supported logic. Do not invent country requirements.

## 17.7 Duplicate suppression

Candidate findings should remain internal. Return final deduplicated findings only.

## 17.8 Self-check invariants

Before returning a finding, verify:

1. Exact source evidence exists.
2. Field is within rule scope.
3. Actual value is exact.
4. Expected value is complete.
5. Suggested value is non-empty.
6. Suggested value is deterministic or `Source validation required`.
7. Finding is not duplicated.
8. Finding does not belong to another rule.

---

# 18. Recommended Regression Test Matrix

## Prompt-level tests

- Clean values do not trigger findings.
- Exact special characters trigger BR4.
- Protected identifiers are not over-cleaned.
- Missing mandatory source fields are not invented.
- Multiple findings remain separate.
- Duplicate source rows do not create duplicate findings.
- Suggested values are stable across repeated runs.

## Ingestion-level tests

- XML parses.
- Tags match template.
- Mandatory mappings are populated.
- Tax-category values pass lookup and database constraints.
- File is retrieved correctly from Document Center.
- Status lifecycle is valid.

## UI-level tests

- One D&S card per final finding.
- Current value binds to exact source value.
- Suggested value binds to expected correction.
- Line-level findings bind to the correct line.
- No repeated field cards.
- No card is created from diagnostic checks.

## Batch-level tests

- BR13 gap detection
- BR13 chronology detection
- Stable scope partitioning
- No comparison across unrelated prefixes or suppliers
- Retry and idempotency behavior

---

# 19. Final Lessons Learned

1. XML parseability is not the same as ingestion success.
2. Ingestion success is not the same as database compatibility.
3. Mandatory ingestion fields cannot be used as agent-level missing-field tests.
4. BR1 must use conditional completeness scenarios for ingestion-passing agent tests.
5. Raw ampersands break XML. Serialize the value safely and validate the parsed business value.
6. Tax-category codes must come only from approved source-system lookups.
7. SQL check constraints must be treated as part of the test-data contract.
8. BR4 must require exact character and Unicode evidence to prevent hallucination.
9. BR6 must create one corrected numeric suggestion per affected field.
10. BR7 must compare document code with financial behavior.
11. BR12 must classify using evidence, not names alone.
12. BR13 requires a population, not a single isolated invoice.
13. SAP and Custom ERP should have different scenario assignments.
14. Every expected issue should have its own master-workbook row.
15. Only final findings should create UI anomaly cards.
16. A file-level ingestion precheck should be generated with every test-data pack.
17. Environment ingestion should be verified before declaring a pack ingestion-certified.

---

# 20. Future Generation Checklist

Before releasing a new test-data pack, confirm:

```text
[ ] Correct country and source-system folders exist
[ ] Required number of files exists in each folder
[ ] Every InvoiceId is unique
[ ] Every SAP DOCNUM is unique
[ ] Every Custom ERP ReferenceID and BODID is unique
[ ] Every XML parses successfully
[ ] Every template tag is retained
[ ] No mandatory ingestion field is blank
[ ] SAP tax category is one of A0, V0, V9, RC
[ ] Custom ERP tax category is one of VAT, GST, EXEMPT, REVERSE
[ ] Tax-rate mapping is validated against environment lookup
[ ] No raw XML-sensitive text corrupts the file
[ ] Every file contains intentional agent findings
[ ] SAP and Custom ERP scenario assignments differ
[ ] Every finding appears separately in the master workbook
[ ] BR4 actual and suggested values are exact
[ ] BR6 calculations have been independently recalculated
[ ] BR7 actual and suggested type codes are mapped correctly
[ ] BR12 evidence supports the expected classification or anomaly
[ ] BR13 scope and batch behavior are documented
[ ] Ingestion precheck passes for every agent-level file
[ ] Environment ingestion status is recorded after upload
```

---

# 21. Approved Tax-Category Memory

Use the following source values for future XML test-data generation unless the user explicitly updates the allowlist.

```text
Custom ERP TaxCategoryCode:
VAT
GST
EXEMPT
REVERSE
```

```text
SAP TaxCategoryCode:
A0
V0
V9
RC
```

Also preserve every XML tag from the supplied source template and keep ingestion-mandatory fields populated.

---

**End of knowledge base**

---

# 22. Second-Pass Robustness Addendum

This addendum captures important prompt and testing requirements that must not be lost in condensed rule summaries.

## 22.1 Universal row-collapse and logical-entity rules

Before any agent evaluates an invoice:

1. Group source records into one logical invoice.
2. Collapse exact repeated physical rows.
3. Treat repeated header values as one invoice-level value.
4. Identify lines using stable `LineItemId`, then `LineId`, or the source-system line key.
5. Collapse exact repeated logical lines.
6. Do not sum repeated invoice headers or totals.
7. Do not produce one finding per SQL result row.
8. Do not allow join multiplication to create duplicate findings.

If repeated header values conflict, do not select the first, last, minimum, maximum, or most frequent value without an explicit policy. Return a single conflict or source-validation finding.

## 22.2 Universal hallucination prevention hierarchy

Every rule should apply this order:

```text
Source evidence
Field eligibility
Applicability
Deterministic evaluation
Canonical issue selection
Dependent-finding suppression
Field-level deduplication
Final output validation
```

Never infer a value from:

- Country alone
- A company name alone
- Free-text similarity
- A calibration example
- Another invoice
- Another row
- A suggested value from another rule
- A value that is not present in agent input

If evidence is insufficient:

```text
NOT_VERIFIABLE
Source validation required
```

Do not create a confident correction.

## 22.3 Common prompt failures encountered

Past prompt behavior included:

- Flagging clean text even though no suspicious character existed
- Claiming hidden or non-breaking characters based only on visual spacing
- Generating a BR4 finding first and inventing a suggested value afterward
- Returning an unchanged value as the correction
- Returning blank suggested values
- Returning SQL, formulas, or explanations in suggested values
- Creating multiple findings for different characters in one field
- Repeating the same header finding for every joined line row
- Clubbing multiple affected fields into one finding
- Returning duplicate `DocumentTypeCode` findings under different issue names
- Cascading one incorrect upstream total into several dependent BR6 findings
- Concatenating amounts as text instead of adding decimals
- Guessing country-specific tax rates or tax-category meanings
- Guessing invoice type from one positive or negative amount
- Treating examples as hardcoded pass or fail strings
- Testing BR1 by blanking mapper-mandatory fields, causing ingestion rejection
- Using XML-invalid raw text that prevented the agent from receiving the invoice
- Declaring a locally parseable pack ingestion-certified without environment evidence

Every production prompt and QA suite should contain regression tests for these failures.

## 22.4 Output sanitation policy

When the configured UI-safe text policy is active, safely corrected BR4 free-text output should contain only:

- Unicode letters
- Numbers
- Normal spaces
- Period
- Comma

Configured transformations include:

```text
& -> and
| -> comma
parentheses -> remove marks and retain enclosed text
curly double quotes -> remove marks and retain enclosed text
curly apostrophe -> normal space when apostrophe is disallowed
em dash and en dash -> normal space
emoji -> remove
non-breaking space -> normal space
zero-width formatting characters -> remove
restricted punctuation -> normal space
```

Transformation order matters. Apply special replacements such as ampersand and vertical bar before the general restricted-character removal step.

After transformation:

1. Collapse repeated spaces.
2. Remove spaces before commas and periods.
3. Add one space after a comma when text follows.
4. Trim the result.
5. Validate the final allowlist.
6. Confirm the corrected value differs from the source value.

Do not output XML entity strings such as `&amp;`, `&lt;`, or `&gt;` as the business correction.

## 22.5 Character evidence contract

For every BR4 finding:

- `character_found` must identify exact characters or exact character descriptions.
- `unicode_code_point` must contain exact code points.
- `actual_value` must remain unchanged.
- `expected_value` must contain the complete corrected value.
- `suggested_fix` must equal `expected_value` for deterministic corrections.

If exact code-point evidence is unavailable, discard the candidate finding. Do not replace the missing evidence with a generic invisible-character claim.

## 22.6 BR6 decimal parsing and numeric output rules

BR6 must parse complete source values as decimals before arithmetic.

Never:

- Concatenate numeric strings
- Join numeric fragments
- Strip embedded decimal points
- Perform arithmetic on text
- Return a number containing more than one decimal point

Bad output:

```text
503.000105.6300
```

Correct output:

```text
608.63
```

Use full precision internally. For UI output:

- Remove insignificant trailing zeros.
- Preserve meaningful precision.
- Preserve negative signs.
- Normalize negative zero to zero.
- Do not add currency symbols or thousands separators unless explicitly required.

## 22.7 BR6 tolerances

Recommended baseline tolerances discussed for the prompt are:

```text
Line amount tolerance: 0.01
Line tax tolerance: 0.01
Invoice total tolerance: 0.02
Tax-rate tolerance: 0.01 percentage points
```

Do not multiply tolerance by line count unless an explicit configuration says so.

A variance within tolerance should produce `PASS`, not a correction.

Do not invent a rounding method. If the result materially depends on an unavailable rounding policy, return `NOT_VERIFIABLE` and `Source validation required`.

## 22.8 BR6 cascading dependency suppression

An upstream error must not automatically produce downstream findings.

Example:

```text
Computed line tax = 105
TaxTotal = 100
TaxExclusiveTotal = 500
TaxInclusiveTotal = 600
```

The current gross equation passes using source values:

```text
500 + 100 = 600
```

Expected output:

- Return a `TaxTotal` finding.
- Do not return a dependent `TaxInclusiveTotal` finding.

A downstream field should receive a separate finding only when the downstream value remains independently wrong after reliable upstream substitution.

Supporting checks may be marked `DEPENDENT` or `NOT_APPLICABLE`. Dependent checks must not create D&S cards.

## 22.9 BR6 sign-aware behavior

Preserve signs. Do not use absolute values to force a match.

A credit or reversal invoice may legitimately contain negative:

- Line values
- Net total
- Tax total
- Gross total
- Payable amount

Do not suggest changing a negative amount to positive unless reliable invoice context proves that the sign is incorrect.

Mixed signs require cautious evaluation. If positive and negative evidence conflict materially, use `LOGICAL_INCONSISTENCY` or `NOT_VERIFIABLE` rather than guessing.

## 22.10 BR6 price-basis limitation

`Quantity × UnitPrice` is authoritative only when UnitPrice represents one unit.

Do not invent:

- Price-base quantity
- Package multiplier
- Unit conversion factor
- Line allowance
- Line charge

If a missing price basis can explain the difference, do not return an exact numeric correction.

## 22.11 BR6 canonical field uniqueness

For header fields:

```text
InvoiceId + BusinessRule + field_name
```

For line fields:

```text
InvoiceId + BusinessRule + stable line key + field_name
```

When candidates for the same field disagree, return one conflict finding with `Source validation required` rather than multiple incompatible corrections.

## 22.12 BR7 evidence quality and single-finding contract

BR7 is normally a single-target rule. The actionable target is `DocumentTypeCode` or the mapped source document-type field.

For one invoice, return:

- Zero findings when type and behavior align
- Exactly one type finding when a reliable mismatch exists
- Exactly one source-validation finding when classification is unsafe

Do not return multiple type findings under different issue names.

Confident classification should use at least two reliable primary financial indicators, including at least one of:

- TaxExclusiveTotal
- TaxInclusiveTotal
- PayableAmount

Do not determine invoice type from:

- TaxTotal alone
- One line amount
- One negative adjustment
- Quantity alone
- UnitPrice alone
- Country alone
- Free-text description alone

## 22.13 BR7 edge cases

### Full prepayment

A positive invoice can have `PayableAmount = 0` when PrepaidAmount equals gross total. Do not classify the invoice as a credit note solely because payable is zero.

### Zero tax

Zero tax can occur for zero-rated, exempt, or reverse-charge transactions. Do not determine invoice type from zero tax alone.

### Mixed lines

A positive invoice can contain a negative adjustment line. A credit note can contain a positive adjustment line. Invoice-level totals are stronger evidence than one line.

### Conflicting repeated type codes

When repeated rows contain conflicting document-type codes:

- Do not choose the first or most frequent.
- Return one conflict or source-validation finding.
- Stop type classification when the source declaration is internally inconsistent.

## 22.14 BR7 source mappings

The correct source code depends on explicit source-system mapping.

Historical prompt examples used values such as:

```text
380 = standard invoice
381 = credit note
388 = alternate type requiring mapping review
```

SAP source templates may expose values such as `F2` or `G2` in `FKART_RL`, while Custom ERP may expose labels such as `Standard` or `CreditMemo`.

Do not mix these code systems. Use the mapping configured for the source system and schema version.

## 22.15 BR12 evidence hierarchy

Use structured evidence before free-text cues.

Suggested evidence order:

1. Explicit buyer country
2. Authoritative buyer account identifier
3. Tax or VAT identifier
4. Government-specific identifier or endpoint
5. Supported source-system classification
6. Name-based cues only as weak supporting evidence

Names such as authority, public service, ministry, or municipality are insufficient by themselves to prove B2G.

Do not infer B2C merely because a tax identifier is unavailable. Consider the complete structured evidence.

## 22.16 BR12 finding granularity

Return separate findings for separate evidence problems, for example:

- Placeholder customer identifier
- Invalid VAT format
- Identifier country mismatch
- Insufficient government evidence

Do not club these issues into one general customer-type finding.

## 22.17 BR13 scope partitioning

Do not compare every invoice in one upload indiscriminately.

Partition sequence populations using supported scope dimensions such as:

- SourceSystem
- Seller or legal entity
- Country
- Number prefix or series
- Fiscal period
- Document family

A gap between unrelated prefixes is not a valid BR13 anomaly.

Missing or unreliable scope evidence should yield `NOT_VERIFIABLE`, not a guessed sequence finding.

## 22.18 Multi-country safeguards

All prompts must support Belgium, France, and Poland without inventing country rules.

Country may select explicitly supplied configuration. Country alone must not be used to infer:

- Tax rate
- Tax-category meaning
- Exemption
- Reverse charge
- Rounding method
- Invoice type
- Price basis
- Sign convention
- Customer type

When country is missing, continue country-neutral checks where possible. Do not fail the whole invoice solely because country is unavailable.

A difference between seller and buyer countries is not automatically a BR6 or BR7 anomaly.

## 22.19 Prompt examples are non-binding

All company names, addresses, invoice numbers, amounts, and correction examples are illustrative.

The model must not:

- Build a safe-value list from examples
- Build an unsafe-value list from examples
- Treat an unlisted value as suspicious
- Automatically pass a listed value if the actual code points differ

Production decisions must use current source evidence.

## 22.20 Application-side controls that prompts cannot guarantee

Prompt logic alone cannot guarantee:

- Database idempotency
- D&S card uniqueness
- Document Center file integrity
- Workflow-status correctness
- Mapper behavior
- Check-constraint compatibility
- Correct retry replacement behavior

Required application controls include:

- Render anomaly cards only from `findings[]`.
- Ignore diagnostic checks for card creation.
- Add BusinessRule to every persisted finding.
- Enforce a unique finding fingerprint.
- Make inserts idempotent.
- Replace or version previous results on rerun.
- Verify uploaded and downloaded file hashes.
- Confirm the document is in the required pre-ingestion status.

## 22.21 Definition of ingestion-safe versus ingestion-certified

Use precise terminology:

### Locally ingestion-safe

The file:

- Parses as XML
- Matches the source-template tag signature
- Contains known mandatory fields
- Uses approved tax-category source values
- Passes local validation

### Environment ingestion-certified

The file has successfully passed:

- Document Center retrieval
- Environment mapper
- Database constraints
- Workflow-state checks
- Actual ingestion pipeline

Do not call a pack ingestion-certified based only on local XML checks.

---

# 23. Expanded Rule-by-Rule Release Checklist

## BR1

```text
[ ] No mapper-mandatory field is blanked
[ ] Conditional completeness anomaly survives ingestion
[ ] One finding per incomplete conditional item
[ ] No invented replacement value
[ ] Source validation required used when correction is not deterministic
```

## BR4

```text
[ ] Exact character exists in actual value
[ ] Exact Unicode code point is recorded
[ ] Protected identifiers are excluded from general cleanup
[ ] Deterministic transformation changes the value
[ ] Suggested value is complete and non-empty
[ ] One finding per field
[ ] Multiple fields remain separate
[ ] XML serialization remains well formed
[ ] No clean local-language text is flagged
```

## BR6

```text
[ ] Inputs parsed as decimals
[ ] Numeric strings are never concatenated
[ ] Tolerance is applied correctly
[ ] Signs are preserved
[ ] Price basis is known
[ ] Rounding method is not invented
[ ] Dependent findings are suppressed
[ ] Same field appears once per logical scope
[ ] Suggested numeric output has no insignificant trailing zeros
```

## BR7

```text
[ ] Source-system document-type mapping is explicit
[ ] At least two reliable primary indicators support classification
[ ] One isolated amount does not determine type
[ ] Full prepayment does not create false credit behavior
[ ] Zero tax does not determine type
[ ] Mixed lines are handled cautiously
[ ] At most one final type finding exists
```

## BR12

```text
[ ] Structured evidence is preferred
[ ] Name alone does not determine B2G
[ ] Missing VAT alone does not determine B2C
[ ] Placeholder identifiers are detected
[ ] Country-prefix mismatch is detected
[ ] Each evidence issue is a separate finding
```

## BR13

```text
[ ] A valid multi-invoice population exists
[ ] Scope dimensions are stable
[ ] Unrelated prefixes are not compared
[ ] Sequence gap and chronology are separate checks
[ ] Single-invoice files return NOT_APPLICABLE
[ ] Duplicate testing is isolated when global uniqueness is required
```

---

# 24. Knowledge-Base Governance

This knowledge base should be updated whenever any of the following changes:

- Source XML template
- Mapper-required fields
- Lookup tables
- Tax-category allowlist
- Document-type mapping
- Country-specific configuration
- Database check constraint
- Prompt output schema
- D&S deduplication key
- BR13 execution model
- Ingestion workflow status

Every revision should record:

- Change date
- Rule affected
- Source of truth
- Test files impacted
- Expected-results rows impacted
- Regression tests added

The most recent environment evidence takes precedence over earlier assumptions or generated examples.