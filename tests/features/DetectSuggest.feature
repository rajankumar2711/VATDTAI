@GIDEI @uat_only @DetectSuggest
Feature: VAT DTAI Detect and Suggest module (UAT only)
  As a Global Insights And Data Enrichment For e-Invoicing user
  I want the Detect and Suggest tab to present its PowerBI report with accurate metrics
  So that I can review AI outcomes on invoices and act on suggestions

  Background:
    Given I login as Admin user
    When I select the Client from dropdown and clicked on continue button
    And User clicks the Global Insights And Data Enrichment For e-Invoicing tile
    Then the Detect and Suggest report is loaded

  @TC_Detect_Suggest_Load @GIDEI_Smoke
  Scenario: PowerBI report is displayed on the Detect and Suggest tab
    Then the Detect and Suggest PowerBI report is present
    And all Detect and Suggest visuals are displayed

  @TC_Detect_Suggest_Metrics
  Scenario: Detect and Suggest KPI metrics are displayed appropriately
    Then the Invoices metric shows a numeric value
    And the Accepted, Overridden and Rejected cards show valid percentages with counts

  @TC_Detect_Suggest_DrillTargets
  Scenario Outline: Drill sources expose drill-through to all their invoice report pages
    Then the "<source>" offers drill-through to all its invoice report pages

    Examples:
      | source                |
      | AI Summary by Country |
      | Invoice Details Table |

  @TC_Detect_Suggest_DrillThrough
  Scenario Outline: Drill-through navigates to the target report page and back
    When I drill through the "<source>" to "<target>"
    Then the "<target>" report page is displayed
    When I click the back button
    Then the Detect and Suggest page is displayed again

    Examples:
      | source                | target             |
      | AI Summary by Country | Invoice History    |
      | AI Summary by Country | Invoice Details    |
      | AI Summary by Country | Summary Details    |
      | Invoice Details Table | Invoice History    |
      | Invoice Details Table | Invoice Details    |
      | Invoice Details Table | Summary Details    |
      | Invoice Details Table | Line Item Details  |
