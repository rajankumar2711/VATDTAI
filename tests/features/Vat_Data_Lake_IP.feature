@GIDEI @MVP @UIUX @DL @P1
Feature: [MVP] [UI/UX] [DL] Data Lake Smoke Suite
  As a Global Insights And Data Enrichment For e-Invoicing authorized user
  I want to access and validate core Data Lake functionality
  So that I can certify module health after deployments
  
  Background:
    Given I login as Admin user
    When I select the Client from dropdown and clicked on continue button
    When I navigate to Global Insights And Data Enrichment For e-Invoicing application
    And I click OK on the application popup

  @TC_616426 @ModuleAccess @Admin @GIDEI_Smoke
  Scenario: Verify authorized Global Insights And Data Enrichment For e-Invoicing user can navigate to Data Lake IP tab and all mandatory page sections render successfully
    When I navigate to Data Lake IP tab
    Then Data Lake IP tab is accessible and displayed with header "Data Lake IP"
    Then Data Lake IP tab is showing 4 sections Business Rules & Logic section,Processing Logic Flow section,Dashboard Filters section and Data Lake IP Dashboard section.
    And Data Lake IP filter section is visible
    And Data Lake IP dashboard section is visible
    And Country field is displayed and read-only