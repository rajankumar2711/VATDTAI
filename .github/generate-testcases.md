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