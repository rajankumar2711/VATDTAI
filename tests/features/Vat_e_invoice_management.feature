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
              And Country field is displayed and read-only
              And Filter criteria section,Outbound Invoice Template and Inbound Invoices (AP) sections are displayed on Invoice Management page
             Then Uploaded Transactions grid is displayed in sorted order by Timestamp column in descending order

        @ExportFunctionality @Admin @VAT_DTAI_Smoke
        Scenario: Verify export functionality in Invoice Management module for Admin role under VAT DTAI app in GTP IT
             When I navigate to Invoice Management module
              And I select few records from Uploaded Transactions grid
             Then I perform Download as Excel action on selected records and verify the downloaded file contains selected records in exported file
             Then I perform Download as CSV action on selected records and verify the downloaded file contains selected records in exported file
             Then I perform Download as JSON action on selected records and verify the downloaded file contains selected records in exported file
             Then I perform Download as XML action on selected records and verify the downloaded file contains selected records in exported file

        @FilterFunctionality @Admin @VAT_DTAI_Sanity
        Scenario: Verify Column level functionality in Invoice Management module for Admin role under VAT DTAI app in GTP IT
             When I navigate to Invoice Management module
              And I click on Status column to click on Filter Select status from dropdown and apply Filter
             Then User is able to filter the records based on selected status in status Column
              And I click on status column to click on Filter Select different status from dropdown and apply Filter
             Then User is able to filter the records based on other selected status in status Column
              And I click on Clear Filter option to clear the applied filter
             Then User is able to clear the applied filter and all records are displayed in Uploaded Transactions grid

        @TC_602537 @ApplyFilters @Outbound @Inbound @VAT_DTAI_Smoke
        Scenario: Verify the application display the values in tables based on user selection made in filter criteria in Invoice Management module for Admin role under VAT DTAI app in GTP IT
             When I navigate to Invoice Management module
             When I apply valid filter criteria in Invoice Management module
             Then Outbound Invoice Template and Inbound Invoices (AP) grid displays records matching the applied criteria

        @InboundInvoicedetails @VAT_DTAI_Smoke
        Scenario: Verify the application display the invoice details in Outbound invoice template in Invoice Management module for Admin role under VAT DTAI app in GTP IT
             When I navigate to Invoice Management module
              And I click on any Client invoice number column from Outbound Invoice Template grid
             Then the application displays the invoice details in Invoice details Pop up having EY logo with close button on top in Invoice Management module for Admin role under VAT DTAI app in GTP IT
             Then I verify Invoice Header, Buyer, Seller,Totals & Payment,Line Items and Tax Summary section are getting displayed in invoice details pop up.
              And I click on Close button to close the invoice details pop up and verify the Invoice Management module is displayed with Outbound Invoice Template and Inbound Invoices (AP) sections

        @OutboundInvoiceExtractdetails @VAT_DTAI_Sanity
        Scenario: Verify the application display the Outbound Invoice Extract in Outbound invoice template in Invoice Management module for Admin role under VAT DTAI app in GTP IT
             When I navigate to Invoice Management module
              And I Click on Status column to Filter Ready status records in Outbound Invoice Template grid
             Then I click on Ready status records from Outbound Invoice Template grid
             Then Outbound Invoice Extract pop up displayed having EY logo with Close button
             Then I verify Client Invoice Number,Invoice ID,Customer Name,System,Status,Invoice Total Value and Invoice Tax Value columns are displayed correctly in Outbound Invoice Extract
              And I click on XML button to export Outbound extract in XML format
             Then I verify the exported file contains the correct data in Outbound Invoice Extract in XML format
              And I click on JSON button to export Outbound extract in JSON format
             Then I verify the exported file contains the correct data in Outbound Invoice Extract in JSON format
              And I click on CSV button to export Outbound extract in CSV format
             Then I verify the exported file contains the correct data in Outbound Invoice Extract in CSV format
              And I click on close button to close the Outbound Invoice Extract pop up and verify the pop up is closed.

        @OutboundInvoiceErrorDetails @VAT_DTAI_Sanity
        Scenario: Verify the application display the Outbound Invoice Error details in Outbound invoice template in Invoice Management module for Admin role under VAT DTAI app in GTP IT
             When I navigate to Invoice Management module
              And I Click on Status column to Filter Error status records in Outbound Invoice Template grid
             Then I click on Error status records from Outbound Invoice Template grid
             Then Outbound Invoice Error Details pop up displayed having EY logo with Close button
             Then I verify Client Invoice Number,Invoice ID,System and Error Detail columns are displayed in Outbound Invoice Error Details pop up.
              And I click on Excel button to export the error details for invoice
             Then I verify the exported file contains the correct data in Outbound Invoice Error Details in Excel format
              And I click on close button to close the Outbound Invoice Error Details pop up and verify the pop up is closed.

        @OutboundExport @VAT_DTAI_Sanity
        Scenario: Verify the export functionality for Outbound Invoice template in Invoice Management module for Admin role under VAT DTAI app in GTP IT
             When I navigate to Invoice Management module
              And I select records from Outbound Invoice template
             Then I perform Download as Excel action on selected records and verify the downloaded file contains selected records in exported file
             Then I perform Download as CSV action on selected records and verify the downloaded file contains selected records in exported file
             Then I perform Download as JSON action on selected records and verify the downloaded file contains selected records in exported file
             Then I perform Download as XML action on selected records and verify the downloaded file contains selected records in exported file

        @OutboundFilter @ClearFilter @VAT_DTAI_Sanity
        Scenario: Verify the Column level filter, Clear Filter and Reset view functionality for Outbound Invoice template in Invoice Management module for Admin role under VAT DTAI app in GTP IT
             When I navigate to Invoice Management module
              And I click on Show Filter option in Outbound Invoice template grid
             Then User is able to filter the records with Ready status
              And I remove the Ready status records
             Then User is able to filter the records with Review required status
             Then User is able to filter the records with Custom ERP System column
              And I remove the records with Custom ERP System column
             Then User is able to filter the records with SAP System column
              And I click on Clear Filter option to clear the applied filter
             Then User is able to clear the applied filter and all records are displayed in Outbound Invoice template grid
              And I click on Reset View button to reset all filters applied
             Then User is able to reset all filters applied and all records are displayed in Outbound Invoice template grid

        @OutboundPagination @VAT_DTAI_Sanity
        Scenario: Verify the Pagination functionality for Outbound Invoice template in Invoice Management module for Admin role under VAT DTAI app in GTP IT
             When I navigate to Invoice Management module
              And I Click on Show to change the pagination size from 10 to 25 records in Outbound Invoice template grid
              And I click on Next button to navigate to next page in Outbound Invoice template grid
             Then User is able to navigate to next page in Outbound Invoice template grid
              And I click on Previous button to navigate to previous page in Outbound Invoice template grid
              And I Click on Show to change the pagination size from 25 to 50 records in Outbound Invoice template grid
              And I click on Next button to navigate to next page in Outbound Invoice template grid
             Then User is able to navigate to previous page in Outbound Invoice template grid
              And I click on Last button to navigate to last page in Outbound Invoice template grid
             Then User is able to navigate to last page in Outbound Invoice template grid
              And I click on First button to navigate to first page in Outbound Invoice template grid
             Then User is able to navigate to first page in Outbound Invoice template grid
