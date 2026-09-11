## Summary
Implements automated test cases for the **Inbound Invoices (AP)** grid in the Invoice Management module, mirroring the existing Outbound suite.

## Scenarios added (7)
- Inbound column display
- Status filter + Clear Filter
- Reset View
- Export (Excel / CSV / JSON / XML)
- Invoice Details popup
- Invoice Extract popup (XML / JSON / CSV export)
- Error Details popup (Excel export)

## Changes
- **pageobjects/vat_e_invoice_management_page.py**: Inbound locators & methods, `scroll_to_inbound_section()` for visibility, and `assert_export_format()` that strictly validates a downloaded export's extension **and** content signature.
- **tests/step_defs/test_e_invoice_management.py**: 7 registered scenarios + Inbound step defs; shared clear-filter / reset-view / download steps made grid-aware; every export assertion now verifies the format matches the user action **and** the selected records are present.
- **pytest.ini**: live logging (`log_cli` + `log_file`), disabled the crashing `pytest-html-reporter`, and registered Inbound marker tags.
- **tests/features/Vat_tile.feature**: fixed a pytest-bdd indentation/merge issue.

## Validation (QA)
All 7 Inbound scenarios executed green against QA (shared authenticated session). Export scenarios confirmed correct format (`.xlsx/.csv/.json/.xml`) and that selected records appear in the exported files.
