@VATDTAI @MVP @UIUX @IM @P1
Feature: [MVP] [UI/UX] [IM] e-Invoice Management Smoke Suite
  As a VAT DTAI authorized user
  I want to access and validate core Invoice Management functionality
  So that I can certify module health after deployments

  Background:
    Given I login as Admin user
    When I select the Client from dropdown and clicked on continue button
    When I navigate to VAT DTAI application
    And I click OK on the application popup

  @TC_602480 @ModuleAccess @Admin @VAT_DTAI_Smoke
  Scenario: Verify access to Invoice Management module for Admin role under VAT DTAI app in GTP IT
    When I navigate to Invoice Management module
    Then Invoice Management module is accessible and displayed with header "Invoice Management"
    And Outbound e-Invoices section is visible
    And Inbound e-Invoices section is visible
    And Country field is displayed and read-only

  @TC_602537 @Filters @Outbound @Inbound @VAT_DTAI_Smoke
  Scenario: Verify the application display the values in tables based on user selection made in filter criteria in Invoice Management module for Admin role under VAT DTAI app in GTP IT
    When I navigate to Invoice Management module
    When I apply valid filter criteria in Invoice Management module
    Then Outbound e-Invoices table displays records matching the applied criteria
    And Inbound e-Invoices table displays records matching the applied criteria

  @TC_AGENT_BE @AgentE2E @Client_Belgium
  Scenario: Belgium - validation agent flags Review Required invoices matching the expected results
    When I ingest all e-invoice agent test-data files for the client
    And I navigate to Invoice Management module
    And I wait for e-invoice ingestion to complete
    And I apply the agent issue-date filter in Invoice Management module
    And I wait for the validation agent to finish processing
    Then Review Required invoices match the expected results workbook

  @TC_AGENT_FR @AgentE2E @Client_France
  Scenario: France - validation agent flags Review Required invoices matching the expected results
    When I ingest all e-invoice agent test-data files for the client
    And I navigate to Invoice Management module
    And I wait for e-invoice ingestion to complete
    And I apply the agent issue-date filter in Invoice Management module
    And I wait for the validation agent to finish processing
    Then Review Required invoices match the expected results workbook

  @TC_AGENT_PL @AgentE2E @Client_Poland
  Scenario: Poland - validation agent flags Review Required invoices matching the expected results
    When I ingest all e-invoice agent test-data files for the client
    And I navigate to Invoice Management module
    And I wait for e-invoice ingestion to complete
    And I apply the agent issue-date filter in Invoice Management module
    And I wait for the validation agent to finish processing
    Then Review Required invoices match the expected results workbook

  @TC_AGENT_ACCEPT_ALL @AgentAction @Client_Belgium
  Scenario: Accept all AI suggestions moves a Review Required invoice to Reviewed
    When I navigate to Invoice Management module
    And I apply the agent issue-date filter in Invoice Management module
    Then accepting all AI suggestions moves the invoice to Reviewed

  @TC_AGENT_REJECT_ALL @AgentAction @Client_Belgium
  Scenario: Reject all AI suggestions moves a Review Required invoice to Reviewed
    When I navigate to Invoice Management module
    And I apply the agent issue-date filter in Invoice Management module
    Then rejecting all AI suggestions moves the invoice to Reviewed

  @TC_AGENT_ACCEPT_ONE @AgentAction @Client_Belgium
  Scenario: Accepting one of multiple AI suggestions disables that suggestion
    When I navigate to Invoice Management module
    And I apply the agent issue-date filter in Invoice Management module
    Then accepting one AI suggestion disables it while the others remain actionable

  @TC_AGENT_REJECT_ONE @AgentAction @Client_Belgium
  Scenario: Rejecting one of multiple AI suggestions disables that suggestion
    When I navigate to Invoice Management module
    And I apply the agent issue-date filter in Invoice Management module
    Then rejecting one AI suggestion disables it while the others remain actionable
