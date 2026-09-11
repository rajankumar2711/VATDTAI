@GIDEI @MVP @UIUX @VATTile
Feature: VAT Tile 
  As a Global Insights And Data Enrichment For e-Invoicing user
  I want to access Global Insights And Data Enrichment For e-Invoicing application through the VAT tile
  So that I can navigate to the dashboard and manage VAT data

  Background:
    Given I login as Admin user
    When I select the Client from dropdown and clicked on continue button
    Then I am on the GTP IT home page

  @TC_608001 @TileLaunch @Sections @GIDEI_Smoke
  Scenario: Verify Global Insights And Data Enrichment For e-Invoicing tile is visible under VAT Section
    Then VAT category sections are visible
    And Global Insights And Data Enrichment For e-Invoicing tile is visible
    And Global Insights And Data Enrichment For e-Invoicing tile description is visible

  @TC_608002 @TileLaunch @Dashboard
  Scenario: Verify Global Insights And Data Enrichment For e-Invoicing tile launches dashboard
    When Global Insights And Data Enrichment For e-Invoicing tile description is visible
    When User clicks the Global Insights And Data Enrichment For e-Invoicing tile
    Then Global Insights And Data Enrichment For e-Invoicing dashboard is displayed

  @TC_608003 @Navigation @Dashboard
  Scenario: Verify user can navigate back to GTP IT homepage from Global Insights And Data Enrichment For e-Invoicing
    When User clicks the Global Insights And Data Enrichment For e-Invoicing tile
    And User clicks Home navigation
    Then User is redirected to GTP IT homepage without re-authentication
