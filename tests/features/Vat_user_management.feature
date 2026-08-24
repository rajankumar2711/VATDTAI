@VATDTAI @MVP @UIUX @UM @P1
Feature: VAT DTAI User Management - P1 Test Cases
  As a product owner
  I want role-based User Management capabilities in VAT DTAI
  So that Admin and Country Owner can access and manage user data efficiently

  Background:
    Given I login as Admin user
    When I select the Client from dropdown and clicked on continue button
    When I navigate to VAT DTAI application
    And I click OK on the application popup

  @TC_607973 @ModuleAccess @Admin @VAT_DTAI_Smoke
  Scenario: Verify access to User Management module by Admin
    When I navigate to User Management module
    Then User Management module is accessible and displayed with header "User Management"
    And Country field is displayed and read-only
    And Country assigned to Admin user is displayed
    And Existing Users section is visible with table columns Name, Email, Role and checkboxes

  @TC_607974 @ModuleAccess @CountryOwner
  Scenario: Verify access to User Management module by Country Owner
    When I navigate to User Management module
    Then User Management module is accessible and displayed with header "User Management"
    And Country field is displayed and read-only
    And Country assigned to Country Owner user is displayed

  @TC_607975 @DefaultSort @ExistingUsers
  Scenario: Verify default sorting of Existing Users table by Name ascending
    When I navigate to User Management module
    Then Existing Users table is sorted by Name in ascending order

  @TC_607976 @Sorting @ExistingUsers
  Scenario Outline: Verify sorting functionality on columns Name, Email, Role
    When I navigate to User Management module
    When I click on <column> column header once
    Then the table sorts by <column> in ascending order
    Examples:
      | column |
      | Name   |
      | Email  |
      | Role   |
   

  @TC_607977 @Filtering @Search @ExistingUsers
  Scenario Outline: Verify filtering/search functionality on Name, Email, Role
    When I navigate to User Management module
    When I enter search criteria <search_value> in <column> field
    Then the table displays only records matching the filter criteria for <column>

    Examples:
      | column | search_value     |
      | Name   | Rajan            |
      | Email  | @ey.com          |
      | Role   | Admin            |

  @TC_607978 @SelectAll @ExistingUsers
  Scenario: Verify Select All checkbox functionality
    When I navigate to User Management module
    Given the Existing Users table has multiple user records
    When I click Select All checkbox
    Then all rows in the Existing Users table are selected

  @TC_607979 @ClearFilters @ExistingUsers
  Scenario: Verify Clear Filters button functionality
    When I navigate to User Management module
    When I apply default Name and Role filters
    And I click Clear Filters button
    Then all applied filters are cleared
    And the table displays all user records without filtering

  @TC_607980 @ResetSort @ExistingUsers
  Scenario: Verify Reset Sort button functionality
    When I navigate to User Management module
    When I sort the table by Email column
    And I click Reset Sort button
    Then table sorting resets to default sorting by Name ascending

  @TC_607981 @Download @ExistingUsers
  Scenario Outline: Verify Download functionality in CSV, XML, JSON formats
    When I navigate to User Management module
    When I select one or more rows using checkboxes
    And I click Download button and select <format> format
    Then downloaded file contains selected user records in <format> format

    Examples:
      | format |
      | CSV    |
      | XML    |
      | JSON   |

  @TC_607982 @Pagination @ExistingUsers
  Scenario: Verify pagination displays maximum 25 records per page
    When I navigate to User Management module
    Then the table displays maximum 25 records per page
    And pagination controls are available to navigate between pages

  @TC_607983 @Scroll @ExistingUsers
  Scenario: Verify vertical and horizontal scroll functionality
    When I navigate to User Management module
    When I scroll vertically and horizontally
    Then vertical and horizontal scroll bars appear as needed
    And I can scroll to view all data
