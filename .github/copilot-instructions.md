
# Copilot Instructions for CatalystAI_Automation

## Project Architecture & Major Components
- **Purpose:** Automates API and UI testing for Catalyst AI and OrangeHRM using Python.
- **Key Directories:**
  - `api_models/`: Python classes for API request/response payloads. Each API has a dedicated file.
  - `api_test_helpers/`: Test data builders and HTTP helpers for API tests.
  - `configuration/`: Central config (`config.ini`) for environments, credentials, endpoints. Select environment via section headers (e.g., `[Catalyst application details UAT]`).
  - `endpoints/`: All API endpoint URLs. Never hardcode URLs elsewhere.
  - `pageobjects/`: Page Object Model for UI automation (Playwright/Selenium). Each page = one class.
  - `tests/`: Step definitions and test cases for API/UI flows. Follows BDD and pytest conventions.
  - `assets/`, `dataset/`, `reports/`, `screenshots/`, `archive/`: Supporting data, output, logs, and documentation.

## Critical Developer Workflows
- **Run tests:** Use `pytest` (see `pytest.ini`). Example: `pytest -v -m HealthCheck -k "Update_View_Counter" --env=uat --html=reports/pytest_html_report.html`.
- **Install dependencies:** `pip install -r requirements.txt`.
- **Debugging:** Review `output.json` and files in `reports/` for logs/results. Historical outputs in `archive/`.
- **Add new API:**
  1. Create model in `api_models/`
  2. Add endpoint in `endpoints/`
  3. Add test data/helper in `api_test_helpers/`
  4. Add/extend test in `tests/`
- **Add new UI flow:**
  1. Add page class in `pageobjects/`
  2. Reference config for browser settings
  3. Add/extend test in `tests/`

## Project-Specific Conventions
- **Config values:** Always use `configuration/config.ini` for secrets, endpoints, and environment selection. Never hardcode.
- **Endpoints:** All URLs must be defined in `endpoints/` modules.
- **Test data:** Use builders in `api_test_helpers/` for consistency.
- **Enums:** HTTP methods and other enums are in `Enums/`.
- **Output files:** Do not commit test data, logs, or output files (see `.gitignore`).

## Integration Points & External Dependencies
- **UI Automation:** Uses Playwright/Selenium (browser set in config).
- **Azure Blob Storage:** For file uploads (see `connection_string` in config).
- **Authentication:** Microsoft OAuth (see `TestAPIURL1` in config).

## Examples & Patterns
- **API test addition:**
  - Model: `api_models/create_user_request.py`
  - Endpoint: `endpoints/user_endpoints.py`
  - Helper: `api_test_helpers/create_user_test_data.py`
- **Switch environment:** Change section in `config.ini` or update config parser logic.

## Special Notes
- Never commit secrets or credentials. Use `config.ini` for local dev only.
- Keep all test data and output files out of version control.
- Follow the existing directory structure for all new features.
