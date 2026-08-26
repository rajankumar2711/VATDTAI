# Allure Reporting Integration Guide

## Overview
Allure Framework is a flexible lightweight multi-language test report tool that provides clear graphical reports and allows everyone participating in the development process to extract maximum of useful information from everyday execution of tests.

## Current Setup Status

### ✅ Configured Components
1. **allure-pytest plugin**: Installed (v2.15.3)
2. **pytest.ini configuration**: `--alluredir=reports/allure-results` added to collect test results
3. **conftest.py integration**: Automatic HTML report generation after test execution
4. **Requirements**: allure-pytest added to requirements.txt

### ⚠️ Required: Allure CLI Installation

The **Allure Command-Line tool** is required to generate HTML reports from JSON results.

## Allure CLI Installation

### Option 1: Using Scoop (Windows - Recommended)
```powershell
# Install Scoop if not already installed
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex

# Install Allure
scoop install allure
```

### Option 2: Manual Installation (Windows)
1. Download Allure from: https://github.com/allure-framework/allure2/releases/latest
2. Extract to a directory (e.g., `C:\allure`)
3. Add to PATH:
   - Right-click "This PC" → Properties → Advanced system settings
   - Environment Variables → System Variables → Path → Edit
   - Add: `C:\allure\bin`
4. Verify installation:
   ```powershell
   allure --version
   ```

### Option 3: Using npm (Cross-platform)
```bash
npm install -g allure-commandline
```

## Usage

### Running Tests with Allure Report Generation

**Standard command** (automatically generates all 4 reports):
```bash
pytest tests/step_defs/test_user_management.py -v --env=qa --html=reports/pytest_html_report.html --self-contained-html
```

This will automatically generate:
1. **Allure HTML Report**: `reports/allure-report/index.html` (if Allure CLI installed)
2. **Enterprise Test Report**: `reports/enterprise_test_report.html`
3. **Stakeholder Summary**: `reports/stakeholder_executive_summary.html`
4. **Pytest HTML Report**: `reports/pytest_html_report.html`

### Viewing Allure Report

**Option 1: Open directly in browser**
```powershell
Start-Process "reports/allure-report/index.html"
```

**Option 2: Serve with Allure (recommended for better experience)**
```bash
allure serve reports/allure-results
```
This opens a web server and displays the report in your browser with live reload.

**Option 3: Generate and open**
```bash
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

## Report Features

### Allure Report Includes:
- **Overview Dashboard**: Total tests, pass rate, execution time, trends
- **Suites**: Test organization by feature/module
- **Graphs**: 
  - Status breakdown (passed/failed/skipped)
  - Severity distribution
  - Duration trends
  - Timeline
- **Behaviors**: BDD-style features and stories
- **Test Cases**: Detailed test execution with:
  - Steps and sub-steps
  - Attachments (screenshots, logs, videos)
  - Parameters
  - Categories
  - History (if previous runs available)
- **Categories**: Defect classification
- **Timeline**: Concurrent test execution visualization

## Enhancing Tests with Allure Decorators

### Adding Allure Annotations to Tests

To get richer Allure reports, add decorators to your test files:

```python
import allure

@allure.feature("User Management")
@allure.story("User Access Control")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify Admin user can access User Management module")
def test_admin_access_user_management(authenticated_vat_page):
    with allure.step("Login as Admin user"):
        # test code
        pass
    
    with allure.step("Navigate to User Management"):
        # test code
        pass
    
    with allure.step("Verify access granted"):
        # test code
        pass
```

### Available Decorators:
- `@allure.feature("Feature Name")`: High-level feature grouping
- `@allure.story("Story Name")`: User story within feature
- `@allure.severity(level)`: Critical, Blocker, Normal, Minor, Trivial
- `@allure.title("Test Title")`: Custom test name in report
- `@allure.description("Description")`: Detailed test description
- `@allure.tag("tag1", "tag2")`: Custom tags for filtering
- `@allure.link(url, name)`: Link to external resource (Jira, etc.)
- `@allure.issue(url, name)`: Link to issue tracker
- `@allure.testcase(url, name)`: Link to test case in TMS

### Adding Attachments Dynamically:
```python
import allure

# Attach text
allure.attach("Error details", name="Error Log", attachment_type=allure.attachment_type.TEXT)

# Attach file
allure.attach.file("screenshot.png", name="Failure Screenshot", attachment_type=allure.attachment_type.PNG)

# Attach JSON
allure.attach(json.dumps(data), name="API Response", attachment_type=allure.attachment_type.JSON)
```

## CI/CD Integration

### Jenkins Example:
```groovy
stage('Run Tests') {
    steps {
        bat 'pytest tests/ -v --env=qa --html=reports/pytest_html_report.html --self-contained-html'
    }
}

stage('Generate Allure Report') {
    steps {
        allure([
            includeProperties: false,
            jdk: '',
            properties: [],
            reportBuildPolicy: 'ALWAYS',
            results: [[path: 'reports/allure-results']]
        ])
    }
}
```

### Azure DevOps Example:
```yaml
- task: CmdLine@2
  displayName: 'Run Tests'
  inputs:
    script: 'pytest tests/ -v --env=qa --html=reports/pytest_html_report.html --self-contained-html'

- task: PublishAllureReport@1
  displayName: 'Publish Allure Report'
  inputs:
    allureResultsPath: 'reports/allure-results'
    allureReportPath: 'reports/allure-report'
```

## Troubleshooting

### Issue: "Allure CLI not found"
**Solution**: Install Allure CLI using one of the methods above and verify with `allure --version`

### Issue: "allure-results folder is empty"
**Solution**: Ensure `--alluredir=reports/allure-results` is in pytest command or pytest.ini

### Issue: "Report shows old data"
**Solution**: Use `--clean` flag when generating:
```bash
allure generate reports/allure-results -o reports/allure-report --clean
```

### Issue: "No test results in report"
**Solution**: Check that:
1. Tests executed successfully
2. allure-pytest plugin is installed: `pip list | grep allure`
3. Allure results directory exists and contains JSON files

## Best Practices

1. **Clean results before new runs** to avoid mixing data:
   ```bash
   Remove-Item reports/allure-results/* -Force
   ```

2. **Use descriptive test names** and allure decorators for better report clarity

3. **Attach screenshots on failures** - already configured in conftest.py

4. **Add custom categories** for defect classification:
   Create `reports/allure-results/categories.json`:
   ```json
   [
     {
       "name": "UI Element Not Found",
       "matchedStatuses": ["failed"],
       "messageRegex": ".*locator.*timeout.*"
     },
     {
       "name": "Authentication Errors",
       "matchedStatuses": ["failed"],
       "messageRegex": ".*login.*failed.*"
     }
   ]
   ```

5. **Preserve history** by copying trend data:
   ```bash
   Copy-Item reports/allure-report/history reports/allure-results/history -Recurse -Force
   ```

## Summary

Your framework now supports **4 comprehensive reporting formats**:
1. ✅ **Allure Report** - Interactive web-based report (requires CLI installation)
2. ✅ **Enterprise Test Report** - Professional HTML report with quality assessment
3. ✅ **Stakeholder Summary** - Executive dashboard
4. ✅ **Pytest HTML Report** - Standard test results

All reports are generated automatically after each test run with **zero manual intervention** (except Allure CLI installation).
