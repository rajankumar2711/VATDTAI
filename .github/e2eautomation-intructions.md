Purpose

This document guides Copilot (or any automation agent) through the complete EY Tax Catalyst QA workflow:

Discover ADO projects and sprint teams

Identify current sprint for the Power K team

Retrieve user stories

Generate QA test cases and Playwright + pytest scripts

Execute and validate test results

⚙️ 1. Discover Azure DevOps (ADO) Projects

Command:

core_list_projects --top 100


Expected Format:

1. ${project_code_1} → ${project_name_1}
2. ${project_code_2} → ${project_name_2}
✅ Default project set to: ${default_project}

👥 2. Identify Power K Team and Current Sprint

Command:

core_list_project_teams --project "${default_project}" --top 100


Expected Format:

1. ${team_name_1}
2. ${team_name_2}
✅ Target team selected: ${selected_team}

Retrieve Current Sprint

Command:

work_list_team_iterations --project "${default_project}" --team "${selected_team}" --timeframe "current"


Expected Format:

Current iteration found:
Iteration Path: ${iteration_path}
Start Date: ${start_date}
End Date: ${end_date}
✅ Active iteration: ${iteration_name}

📋 3. Retrieve User Stories for Current Sprint

Command:

search_workitem \
  --project ["${default_project}"] \
  --workItemType ["User Story"] \
  --includeFacets false \
  --searchText "${iteration_path}"


Expected Format:

ID       Title
-----    -----------------------------------------------
${work_item_id_1}  ${work_item_title_1}
${work_item_id_2}  ${work_item_title_2}
✅ ${count} user stories retrieved.

🧩 4. Generate QA Test Cases for a User Story

Prompt:

Generate QA test cases for the user story "${work_item_title_1}" ensuring all acceptance criteria are covered.

Expected Format:

Test Case 1 – ${description_1}
Test Case 2 – ${description_2}
...
✅ ${count} test cases generated.

🧪 5. Generate Playwright + pytest Test Script

Copilot should produce a test file like:

import pytest
from playwright.sync_api import sync_playwright
from configuration.readconfig import ReadConfig

@pytest.mark.ui
def test_${function_name}():
    base_url = ReadConfig.get_application_url()
    username = ReadConfig.get_username()
    password = ReadConfig.get_password()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=False)
        context = browser.new_context()
        page = context.new_page()

        # --- Login ---
        page.goto(base_url)
        page.fill("input[type='email']", username)
        page.click("input[type='submit']")
        page.fill("input[type='password']", password)
        page.click("input[type='submit']")
        page.wait_for_load_state("networkidle")

        # --- Navigate to target page ---
        page.goto(f"{base_url}/company/${route}")
        popup = page.wait_for_selector("text=${selector_text}", timeout=10000)

        # --- Assertion ---
        assert popup.is_visible(), "${assert_message}"

        browser.close()


Expected Format:

✅ Script generated: ${temp_test_file}
✅ Dependencies detected: pytest, playwright, configuration/readconfig

▶️ 6. Execute the Test (Temporary Mode)

Command:

pytest ${temp_test_file} --headed --browser=msedge -v


Expected Format:

============================= test session starts =============================
collected ${num_tests} item(s)
${temp_test_file}::${test_function_name} ${status}
INFO Login successful for user ${username}
INFO Popup detected → ${selector_text}
============================== ${summary} ==============================
✅ Test execution successful.

🧹 7. Clean-Up and Validation

Command:

rm ${temp_test_file}


Expected Format:

🗑️ Temporary file deleted: ${temp_test_file}
✅ Environment restored to clean state.

✅ 8. Success Criteria
Check	Expected Outcome
Project retrieved	${default_project}
Team selected	${selected_team}
Iteration detected	${iteration_name}
User stories retrieved	≥ 1 matching item
Test cases generated	Covers all acceptance criteria
Playwright script executed	All assertions passed
Cleanup done	Temporary test file removed
🔐 Notes

Never hard-code credentials or URLs.

Use helpers under configuration/ and pageobjects/.

Execute only in UAT (https://catalyst-uat.ey.com).

On selector failure, capture HTML snapshot + console logs.

All temporary tests must run in non-headless Edge mode.