@UserStory_595077 @MVP @UI_UX @DataIngestion @DI @P1
Feature: [MVP] [UI/UX] [DI] Create Data Ingestion Tab
  As a VAT DTAI authorized user
  I want to access and interact with the Data Ingestion module
  So that I can manage e-Invoice uploads and API details efficiently

  Background:
    Given I login as Admin user
    When I select the Client from dropdown and clicked on continue button
    When I navigate to VAT DTAI application
    And I click OK on the application popup

  @TC_604817 @AccessControl @Authorization @VAT_DTAI_Smoke
  Scenario: Verify access to Data Ingestion module for authorized roles
    When I access Data Ingestion module
    And the Data Ingestion module is visible and accessible to the user
    And Country field is displayed and read-only
    And Country assigned to Admin user is displayed


  @TC_604820 @UI @Sections
  Scenario: Verify presence of Batch e-Invoices and API Details sections
    When I access Data Ingestion module
    Then the Batch e-Invoices section is displayed
    And the API Details section is displayed as a separate section

  @TC_604822 @FileUpload @BatchProcessing @VAT_DTAI_Smoke
  Scenario Outline: Verify successful upload of valid e-Invoice transaction report
    When I access Data Ingestion module
    When I select Source System "<source_system>" from dropdown
    And I choose a valid e-Invoice transaction report file "<file_name>"
    And I click Upload button
    Then file upload completes successfully
    And a unique Batch ID is generated
    And a new record is displayed in Batch e-Invoices table with correct Batch ID, File Name, Source System, and Imported On values

    Examples:
      | source_system | file_name                                       |
      | Oracle        | Belgium Domestic Invoice.csv                   |
      | SAP           | Sample 2 — Belgium Reduced VAT (6%) — SAP.JSON |
      | MS D365       | Sample 1 — Belgium Domestic (21%).xml          |


  @TC_604824 @InvalidData @FileUpload @BatchProcessing
  Scenario Outline: Verify upload fails for invalid e-Invoice data (incorrect VAT rates, amounts, charges)
    When I access Data Ingestion module
    When I select Source System "<source_system>" from dropdown
    And I choose an invalid data file "<file_name>"
    And I click Upload button
    Then error message should be displayed indicating file upload failure "File not uploaded. Please retry."
    And no Batch ID is generated for invalid data
    And no new record is added to Batch e-Invoices table for invalid data

    Examples:
      | source_system | file_name                                        |
      | Oracle        | Belgium Wrong VAT rate 19%.csv                   |
      | SAP           | Credit note with positive amounts.csv            |
      | MS D365       | Export invoice wrongly charged Belgian VAT.csv   |
      | SAP           | Reverse charge missing for EU customer.csv       |

  @TC_604823 @InvalidFormat @FileUpload @BatchProcessing
  Scenario Outline: Verify upload fails for invalid e-Invoice file formats
    When I access Data Ingestion module
    When I select Source System "<source_system>" from dropdown
    And I choose an invalid format file "<file_name>"
    And I click Upload button
    Then file upload fails with error message
    And error message indicates only CSV, XML, JSON formats are accepted
    And no Batch ID is generated
    And no new record is added to Batch e-Invoices table

    Examples:
      | source_system | file_name                                                              |
      | Oracle        | Not accepted Image format.png                                          |
      | SAP           | PDF file.pdf                                                           |
      | MS D365       | VAT Test Plan_606766 _ [MVP] [UI_UX] [UM] User Management Updates.xlsx |
      | SAP           | DROID install - CLI Mode and IDE .docx                                 |

  @TC_604827 @TableDisplay @BatcheInvoices
  Scenario: Verify Batch e-Invoices table columns and country-specific data display
    When I access Data Ingestion module
    Then the table displays columns: Batch ID, File Name, Source System, and Imported On
    And only records for the user-assigned country "Belgium" are displayed
    And each Batch ID is unique and system generated
    And Imported On is displayed in expected datetime format

  @TC_604828 @TableDisplay @APIDetails @Hardcoded
  Scenario: Verify API Details table columns and country-specific data display
    When I access Data Ingestion module
    Then the table displays columns: Source System, Type, Rest API Actions, Status, and Created By
    And only API records for the user-assigned country "Belgium" are displayed
    And Created By is displayed in expected first and last name format
    And the table displays hardcoded API data for MVP across all countries
    And the same API details apply across all three countries

  @TC_604829 @DefaultSort @BatcheInvoices @APIDetails
  Scenario: Verify default sorting of Batch e-Invoices and API Details tables
    When I access Data Ingestion module
    Then the Batch e-Invoices table is sorted by Batch ID from latest to oldest
    When I open the API Details table
    Then the API Details table is sorted by Source System in ascending order

  @TC_604830 @Sorting @BatcheInvoices
  Scenario Outline: Verify sorting functionality on all columns in Batch e-Invoices table
    When I access Data Ingestion module
    When I click "<column>" column header repeatedly
    Then records are sorted correctly in ascending and descending order by "<column>"

    Examples:
      | column        |
      | Batch ID      |
      | File Name     |
      | Source System |
      | Imported On   |

  @TC_604831 @Sorting @APIDetails
  Scenario Outline: Verify sorting functionality on all columns in API Details table
    When I access Data Ingestion module
    When I click "<column>" column header repeatedly
    Then records are sorted correctly in ascending and descending order by "<column>"

    Examples:
      | column           |
      | Source System    |
      | Type             |
      | Rest API Actions |
      | Status           |
      | Created By       |

  @TC_604838 @Filters @ResetSort @BatcheInvoices
  Scenario: Verify Clear Filters and Reset Sort functionality in Batch e-Invoices table
    When I access Data Ingestion module
    When I apply one or more filters in Batch e-Invoices table with Source System = "SAP"
    Then filtered records are displayed
    When I click Clear Filters button
    Then all filters are cleared and the full record set is displayed
    When I apply sorting on Batch e-Invoices column "Imported On"
    Then sorting is applied successfully
    When I click Reset Sort button
    Then sorting resets to default order Batch ID latest to oldest

  @TC_604840 @Download @BatcheInvoices
  Scenario: Verify Download button functionality for Batch e-Invoices table
    When I access Data Ingestion module
    When I select first 2 records in Batch e-Invoices table
    Then selected records are highlighted for download
    When I click Download button
    Then selected records are downloaded successfully
    Then downloaded files are provided in the original uploaded file format csv or xlsx

  @TC_604841 @Download @APIDetails
  Scenario: Verify Download button functionality for API Details table
    When I access Data Ingestion module
    When I select 2 API records in API Details table
    Then selected API records are highlighted for download
    When I click Download button
    Then selected API records are downloaded successfully
    And downloaded details are provided in the original available format

  @TC_604843 @Delete @APIDetails @AuditTrail
  Scenario: Verify Delete button functionality and audit trail for API Details table
    When I access Data Ingestion module
    When I select API record "ERP Extract" in API Details table
    Then selected API record is highlighted for deletion
    When I click Delete button
    Then deletion confirmation prompt is displayed
    When I confirm the deletion
    Then selected API record is deleted successfully from the table
    And audit trail is maintained with deleted API record details, deleted by user, and timestamp
