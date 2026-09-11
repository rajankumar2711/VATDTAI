@GIDEI @MVP @UIUX @RM @P1
Feature: [MVP] [UI/UX] [RM] Reports Smoke Suite
  As a Global Insights And Data Enrichment For e-Invoicing authorized user
  I want to validate core report generation flows
  So that I can certify report module health after deployments

  Background:
    Given I login as Admin user
    When I select the Client from dropdown and clicked on continue button
    When I navigate to Global Insights And Data Enrichment For e-Invoicing application
    And I click OK on the application popup

  @TC_624017 @InvoiceStatusReport @GIDEI_Smoke
  Scenario: Verify user can generate Invoice Status report successfully and the report is displayed in a popup or supported UI container
    When I navigate to Reports module
    When I select Invoice Status Report
    And I provide valid report filter criteria
    And I click Generate button
    Then Invoice Status report is displayed in popup or supported UI container and verify the all the columns appropriately
    When I click on Export PDF button
    Then Verify the export pdf file is downloaded successfully and verify file name

  @TC_626420 @SubmissionReport @GIDEI_Smoke
  Scenario: Verify Submission Report is generated in popup or approved UI container
    When I navigate to Reports module
    When I select Submission Report
    And I provide valid report filter criteria
    And I click Generate button
    Then Submission Report is displayed in popup or approved UI container

  @TC_626381 @ReconciliationReport @GIDEI_Smoke
  Scenario: Verify user can generate Reconciliation Report and view report in popup or approved UI container
    When I navigate to Reports module
    When I select Reconciliation Report
    And I provide valid report filter criteria
    And I click Generate button
    Then Reconciliation Report is displayed in popup or approved UI container

  # ---- Default Generate Report page + UI validation ----
  @TC_RPT_DefaultPage @UIUX @GIDEI_Smoke
  Scenario: Verify the default state of the Generate Report page
    When I navigate to Reports module
    Then the Report page header should be "Generate Report"
    And the Select Report dropdown should list all supported report types
    And the Country field should match the logged-in client's country
    And the Entity field should default to "ALL"
    And the report date fields should display the placeholder "mm/dd/yyyy"
    And the Generate button should be disabled

  # ---- Negative: Generate stays disabled with incomplete/invalid inputs ----
  @TC_RPT_GenerateDisabled @GIDEI_Sanity
  Scenario Outline: Verify Generate remains disabled when mandatory report information is incomplete
    When I navigate to Reports module
    And the user selects "<reportType>" as the report type
    And the user enters the report criteria for "<condition>"
    Then the Generate button should be disabled

    Examples:
      | reportType            | condition                |
      | Invoice Status Report | start date is missing    |
      | Invoice Status Report | end date is missing      |
      | Invoice Status Report | date range is invalid    |
      | Submission Report     | platform is not selected |
      | Reconciliation Report | end date is missing      |

  # ---- Positive: Generate becomes enabled with valid inputs ----
  @TC_RPT_GenerateEnabled @GIDEI_Smoke
  Scenario: Verify Generate is enabled for valid Invoice Status Report criteria
    When I navigate to Reports module
    And the user selects "Invoice Status Report" as the report type
    And the user selects "ALL" as the Entity
    And the user enters a date range from "01/01/2025" to "10/10/2026"
    Then the Generate button should be enabled

  # ---- Generate + metadata + columns for platform-less report types ----
  @TC_RPT_Generate @GIDEI_Smoke
  Scenario Outline: Generate and validate report metadata and columns
    When I navigate to Reports module
    And the user selects "<reportType>" as the report type
    And the user selects "ALL" as the Entity
    And the user enters a date range from "01/01/2025" to "10/10/2026"
    And the user generates the report
    Then the report title should be "<reportType>"
    And the report Country should match the logged-in client's country
    And the report Entity should be "All"
    And the report Date Range should match the selected date range
    And the Generated On value should match the report-generation time
    And the "<reportType>" should display its expected columns in the expected order

    Examples:
      | reportType            |
      | Invoice Status Report |
      | Reconciliation Report |

  # ---- Submission Platform conditional field behavior ----
  @TC_RPT_SubmissionPlatformVisibility @SubmissionReport @GIDEI_Sanity
  Scenario: Verify the Submission Platform field conditional behavior
    When I navigate to Reports module
    And the user selects "Invoice Status Report" as the report type
    Then the Submission Platform field should not be displayed
    When the user selects "Submission Report" as the report type
    Then the mandatory Submission Platform field should be displayed
    And the Submission Platform dropdown should list the GTES and Pagero platforms
    And the Generate button should remain disabled until a Submission Platform is selected
    When the user selects "Reconciliation Report" as the report type
    Then the Submission Platform field should not be displayed

  # ---- Submission Report generate + metadata + columns per platform ----
  @TC_RPT_SubmissionGenerate @SubmissionReport @GIDEI_Smoke
  Scenario Outline: Generate and validate the Submission Report per platform
    When I navigate to Reports module
    And the user selects "Submission Report" as the report type
    And the user selects "<platform>" as the Submission Platform
    And the user selects "ALL" as the Entity
    And the user enters a date range from "01/01/2025" to "10/10/2026"
    And the user generates the report
    Then the report title should be "Submission Report"
    And the report Country should match the logged-in client's country
    And the report Entity should be "All"
    And the report Date Range should match the selected date range
    And the Generated On value should match the report-generation time
    And the "Submission Report" should display its expected columns in the expected order

    Examples:
      | platform |
      | GTES     |
      | Pagero   |

  # ---- Export + validate: Invoice Status Report ----
  @TC_RPT_ExportInvoiceStatus @ExportFunctionality @GIDEI_Sanity
  Scenario Outline: Export and validate the Invoice Status Report
    Given an "Invoice Status Report" has been generated
    When the user exports the report as "<format>"
    Then a valid "<format>" report file should be downloaded
    And the exported report metadata should match the generated report
    And the exported report columns should match the UI report columns

    Examples:
      | format |
      | Excel  |
      | PDF    |
      | CSV    |
      | XML    |

  # ---- Export + validate: Submission Report per platform ----
  @TC_RPT_ExportSubmission @ExportFunctionality @SubmissionReport @GIDEI_Sanity
  Scenario Outline: Export and validate the Submission Report
    Given a Submission Report has been generated for "<platform>"
    When the user exports the report as "<format>"
    Then a valid "<format>" report file should be downloaded
    And the exported report metadata should match the generated report
    And the exported report columns should match the UI report columns

    # The Submission Report is a JSON-format report; its Export menu supports Excel, PDF, CSV
    # and JSON only (no XML).
    Examples:
      | platform | format |
      | GTES     | Excel  |
      | GTES     | PDF    |
      | GTES     | CSV    |
      | GTES     | JSON   |
      | Pagero   | Excel  |
      | Pagero   | PDF    |
      | Pagero   | CSV    |
      | Pagero   | JSON   |

  # ---- Export + validate: Reconciliation Report ----
  @TC_RPT_ExportReconciliation @ExportFunctionality @ReconciliationReport @GIDEI_Sanity
  Scenario Outline: Export and validate the Reconciliation Report
    Given a "Reconciliation Report" has been generated
    When the user exports the report as "<format>"
    Then a valid "<format>" report file should be downloaded
    And the exported report metadata should match the generated report
    And the exported report columns should match the UI report columns

    Examples:
      | format |
      | Excel  |
      | PDF    |
      | CSV    |
      | XML    |

  # ---- Close behavior per report type ----
  @TC_RPT_Close @GIDEI_Sanity
  Scenario Outline: Close the generated report and return to the Generate Report page
    Given a "<reportType>" has been generated
    When the user closes the generated report
    Then the generated report view should close
    And the Generate Report page should be displayed

    Examples:
      | reportType            |
      | Invoice Status Report |
      | Submission Report     |
      | Reconciliation Report |

  # ---- Regression: report pop-up scroll support per report type ----
  @TC_RPT_Scroll @Scroll @Regression @GIDEI_Regression
  Scenario Outline: Verify the generated report pop-up supports scrolling
    Given a "<reportType>" has been generated
    Then the generated report pop-up should support scrolling
    When the user closes the generated report
    Then the generated report view should close

    Examples:
      | reportType            |
      | Invoice Status Report |
      | Submission Report     |
      | Reconciliation Report |

  # ---- Generate stays disabled while a report pop-up is open ----
  @TC_RPT_GenerateLock @Regression @GIDEI_Sanity
  Scenario Outline: Verify Generate is disabled while a report pop-up is open and re-enables after closing
    Given a "<reportType>" has been generated
    Then the Generate button should be disabled while the report pop-up is open
    When the user closes the generated report
    Then the generated report view should close
    And the Generate Report page should be displayed

    Examples:
      | reportType            |
      | Invoice Status Report |
      | Submission Report     |
      | Reconciliation Report |
