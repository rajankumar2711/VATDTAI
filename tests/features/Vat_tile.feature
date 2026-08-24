@VATDTAI @MVP @UIUX @VATTile
Feature: VAT Tile 
  As a VAT DTAI user
  I want to access VAT DTAI application through the VAT tile
  So that I can navigate to the dashboard and manage VAT data

  Background:
    Given I login as Admin user
    When I select the Client from dropdown and clicked on continue button
    Then I am on the GTP IT home page

  @TC_608001 @TileLaunch @Sections @VAT_DTAI_Smoke
  Scenario: Verify DTAI VAT tile is visible under VAT Section
    Then VAT category sections are visible
    And DTAI VAT tile is visible
    And DTAI VAT tile description is visible

  @TC_608002 @TileLaunch @Dashboard
  Scenario: Verify DTAI VAT tile launches dashboard
    When DTAI VAT tile description is visible
    When User clicks the DTAI VAT tile
    Then VAT DTAI dashboard is displayed

  @TC_608003 @Navigation @Dashboard
  Scenario: Verify user can navigate back to GTP IT homepage from VAT DTAI
    When User clicks the DTAI VAT tile
    And User clicks Home navigation
    Then User is redirected to GTP IT homepage without re-authentication
