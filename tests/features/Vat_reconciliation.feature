@VATDTAI @MVP @UIUX @RC @P1
Feature: [MVP] [UI/UX] [RC] Reconciliation Smoke Suite
  As a VAT DTAI authorized user
  I want to validate core Reconciliation workflows
  So that I can certify module health after deployments

  Background:
    Given I login as Admin user
    When I select the Client from dropdown and clicked on continue button
    When I navigate to VAT DTAI application
    And I click OK on the application popup

  @TC_613500 @ModuleAccess @VAT_DTAI_Smoke
  Scenario: Verify authorized VAT DTAI user can access Reconciliation module and reach batch reconciliation workflow
    When I navigate to Reconciliation module
    Then Reconciliation module is accessible and displayed
    And Reconciliation input panel is visible with mandatory selectors
    And Reconcile action is visible

  @TC_613503 @FileUpload @Reconcile @VAT_DTAI_Smoke
  Scenario: Verify user can execute reconciliation successfully with valid filters and valid GL ERP transaction files
    When I navigate to Reconciliation module
    When I upload valid GL transaction file and valid ERP transaction file
    And I apply valid reconciliation filters
    And I click Reconcile button
    Then reconciliation executes successfully
    And Reconciliation Details table is displayed

  @TC_626740 @ResultSummary @VAT_DTAI_Smoke
  Scenario: Verify Reconciliation Details summary table displays exactly Match and Mismatch rows
    When I navigate to Reconciliation module
    Then Reconciliation Details summary table displays Match and Mismatch rows
    And Match and Mismatch counts are shown as numeric values
