@GIDEI @uat_only @Dashboard
Feature: VAT DTAI PowerBI Dashboard (UAT only)
  As a Global Insights And Data Enrichment For e-Invoicing user
  I want the Dashboards tab to present the PowerBI report with accurate metrics
  So that I can monitor e-invoicing operations and drill into invoice detail

  Background:
    Given I login as Admin user
    When I select the Client from dropdown and clicked on continue button
    And User clicks the Global Insights And Data Enrichment For e-Invoicing tile
    Then the VAT DTAI dashboard is loaded

  @TC_DASH_Load @GIDEI_Smoke
  Scenario: PowerBI dashboard report is displayed on the Dashboards tab
    Then the PowerBI report is present
    And all dashboard visuals are displayed

  @TC_DASH_Metrics
  Scenario: All dashboard metrics are displayed appropriately
    Then the Total Invoices metric shows a numeric value
    And the Success Rate metric shows a percentage value
    And the operational status breakdown reconciles with Total Invoices

  @TC_DASH_DrillTargets
  Scenario Outline: Operational cards expose drill-through to all invoice report pages
    Then the "<card>" card offers drill-through to all invoice report pages

    Examples:
      | card                       |
      | By Operational Status      |
      | Schema / Mapping Readiness |

  @TC_DASH_DrillThrough
  Scenario Outline: Card drill-through navigates to the target report page and back
    When I drill through the "By Operational Status" card to "<target>"
    Then the "<target>" report page is displayed
    When I click the back button
    Then the dashboard page is displayed again

    Examples:
      | target          |
      | Invoice History |
      | Invoice Details |
      | Summary Details |
