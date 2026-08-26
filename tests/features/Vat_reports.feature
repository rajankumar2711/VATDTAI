@VATDTAI @MVP @UIUX @RM @P1
Feature: [MVP] [UI/UX] [RM] Reports Smoke Suite
  As a VAT DTAI authorized user
  I want to validate core report generation flows
  So that I can certify report module health after deployments

  Background:
    Given I login as Admin user
    When I select the Client from dropdown and clicked on continue button
    When I navigate to VAT DTAI application
    And I click OK on the application popup

  @TC_623984 @ModuleAccess @VAT_DTAI_Smoke
  Scenario: Verify authorized user can access Reports module and the Reports header is displayed correctly
    When I navigate to Reports module
    Then Reports module is accessible and displayed with header "Reports"
    And Generate Report section is visible

  @TC_624017 @EInvoiceStatusReport @VAT_DTAI_Smoke
  Scenario: Verify user can generate e-Invoice Status report successfully and the report is displayed in a popup or supported UI container
    When I navigate to Reports module
    When I select e-Invoice Status Report
    And I provide valid report filter criteria
    And I click Generate button
    Then e-Invoice Status report is displayed in popup or supported UI container and verify the all the columns appropriately
    When I click on Export PDF button
    Then Verify the export pdf file is downloaded successfully and verify file name
    

  @TC_626420 @SubmissionReport @VAT_DTAI_Smoke
  Scenario: Verify Submission Report is generated in popup or approved UI container
    When I navigate to Reports module
    When I select Submission Report
    And I provide valid report filter criteria
    And I click Generate button
    Then Submission Report is displayed in popup or approved UI container

  @TC_626381 @ReconciliationReport @VAT_DTAI_Smoke
  Scenario: Verify user can generate Reconciliation Report and view report in popup or approved UI container
    When I navigate to Reports module
    When I select Reconciliation Report
    And I provide valid report filter criteria
    And I click Generate button
    Then Reconciliation Report is displayed in popup or approved UI container
