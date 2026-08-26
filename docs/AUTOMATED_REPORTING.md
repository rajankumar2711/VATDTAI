# Automated Test Reporting System

## Overview

The framework automatically generates comprehensive enterprise-level test execution reports after every test run. These reports provide both business and technical stakeholders with detailed insights into test results, failures, and quality assessments.

## Report Types Generated

### 1. **Enterprise Test Report** (NEW)
**Location:** `reports/enterprise_test_report.html`

**Sections:**
1. **Executive Summary** - Pass/Fail status, quality assessment, Go/No-Go recommendation
2. **Scope of Testing** - Test coverage, modules tested, exclusions
3. **Test Environment Details** - URL, browser, OS, Python version
4. **Framework & Tooling Overview** - Architecture, technologies, locator strategies
5. **Test Execution Summary** - Metrics, timeline, statistics
6. **Module-wise Test Results** - Per-module breakdown with pass rates
7. **Failed Test Case Analysis** - Detailed root cause analysis with error messages
8. **Evidence & Artifacts** - Screenshots, traces, videos, logs
9. **Logging & Debugging Details** - Log configuration and debugging tips
10. **Recommendations & Next Steps** - Prioritized action items

**Target Audience:** 
- Business Stakeholders (Sections 1-2)
- Test Managers (Sections 1, 5, 6, 10)
- Developers/QA Engineers (All sections)

### 2. **Stakeholder Executive Summary**
**Location:** `reports/stakeholder_executive_summary.html`

A concise dashboard view with:
- Test metrics cards (Total, Passed, Failed, Skipped)
- Module-wise results table
- Links to detailed reports and Allure results

### 3. **Pytest HTML Report**
**Location:** `reports/pytest_html_report.html`

Standard pytest-html output with:
- Test-by-test results
- Embedded logs
- Trace and video links

## Usage

### Run Tests with Automatic Reporting

```bash
# Run all tests and generate all reports
pytest tests/step_defs/test_user_management.py -v --env=qa --html=reports/pytest_html_report.html

# Run specific test with reporting
pytest tests/step_defs/test_user_management.py::test_admin_access_user_management -v --env=qa --html=reports/pytest_html_report.html

# Run with custom stakeholder report location
pytest tests/step_defs/test_user_management.py -v --env=qa --html=reports/pytest_html_report.html --stakeholder-summary=reports/custom_summary.html
```

### Report Generation Process

**Automatic Generation:**
1. Tests execute
2. pytest_runtest_makereport hook collects results during execution
3. Screenshots captured automatically on failure
4. pytest_terminal_summary hook generates reports after all tests complete
5. Enterprise report + Executive summary + HTML report all created

**No Manual Intervention Required!**

## Report Features

### Quality Assessment Logic

| Pass Rate | Status | Quality | Recommendation | Confidence |
|-----------|--------|---------|----------------|------------|
| ≥95% | PASS | EXCELLENT | GO | HIGH |
| 80-94% | PARTIAL PASS | GOOD | CONDITIONAL GO | MODERATE-HIGH |
| 70-79% | PARTIAL PASS | MODERATE | CONDITIONAL GO | MODERATE |
| <70% | FAIL | POOR | NO GO | LOW |

### Evidence Capture

**Automatic on Failure:**
- ✅ Full-page screenshots (PNG)
- ✅ Playwright traces (with timeline and network)
- ✅ Console logs (embedded in reports)
- ✅ Error messages and stack traces

**Storage Locations:**
- Screenshots: `screenshots/`
- Traces: (Playwright default location)
- Logs: Embedded in HTML reports

### Failure Analysis

For each failed test, the report includes:
- Test case name and module
- Execution duration
- Detailed error message (first 500 characters)
- Links to screenshot, trace, and video
- Root cause context (when available)

## Configuration

### Environment Selection

Use `--env` flag to specify environment:
- `qa` (default) - QA environment
- `uat` - UAT environment

Environment details are automatically pulled from `configuration/config.ini` and included in the report.

### Custom Report Paths

```bash
# Custom stakeholder summary location
pytest --stakeholder-summary=path/to/custom_report.html

# Custom pytest HTML report location
pytest --html=path/to/custom_pytest_report.html
```

### Screenshot Configuration

Screenshots are automatically captured on failure. Customize in `conftest.py`:

```python
# Full page screenshot (default)
page.screenshot(path=str(screenshot_path), full_page=True)

# Viewport only
page.screenshot(path=str(screenshot_path), full_page=False)
```

## Integration with CI/CD

### Jenkins Pipeline Example

```groovy
stage('Run Tests') {
    steps {
        bat 'pytest tests/step_defs/test_user_management.py -v --env=qa --html=reports/pytest_html_report.html'
    }
}

stage('Publish Reports') {
    steps {
        publishHTML([
            reportDir: 'reports',
            reportFiles: 'enterprise_test_report.html,stakeholder_executive_summary.html,pytest_html_report.html',
            reportName: 'Test Execution Reports',
            keepAll: true
        ])
    }
}
```

### Azure DevOps Pipeline Example

```yaml
- task: CmdLine@2
  displayName: 'Run Tests'
  inputs:
    script: |
      pytest tests/step_defs/test_user_management.py -v --env=qa --html=reports/pytest_html_report.html

- task: PublishBuildArtifacts@1
  displayName: 'Publish Test Reports'
  inputs:
    PathtoPublish: 'reports'
    ArtifactName: 'TestReports'
```

## Troubleshooting

### Report Not Generated

**Issue:** Enterprise report not created after test run

**Solutions:**
1. Check console output for error messages
2. Verify `utilities/report_generator.py` exists
3. Ensure `reports/` directory has write permissions
4. Check Python version (requires 3.10+)

### Screenshots Not Captured

**Issue:** Screenshots missing for failed tests

**Solutions:**
1. Verify `screenshots/` directory exists and is writable
2. Check page fixture is properly initialized
3. Ensure `authenticated_vat_page` fixture is used in test
4. Review logs for screenshot capture errors

### Missing Error Details

**Issue:** Failed test analysis shows "No error message available"

**Solutions:**
1. Check pytest version (requires 7.4.3+)
2. Verify `longrepr` attribute is accessible in report
3. Run with `-vv` for more verbose output
4. Check if test raises proper exceptions

## Best Practices

### For Test Authors

1. **Use Descriptive Test Names**
   ```python
   def test_admin_can_filter_users_by_name():  # Good
       pass
   
   def test_tc123():  # Bad - not descriptive
       pass
   ```

2. **Add Meaningful Assertions**
   ```python
   assert user_count == 5, f"Expected 5 users but found {user_count}"  # Good
   assert user_count == 5  # Bad - no context
   ```

3. **Log Key Actions**
   ```python
   logger.info("[WHEN] Clicking Show Filters button")
   user_mgmt_page.show_filters()
   logger.info("Filters displayed successfully")
   ```

### For Report Consumers

1. **Business Stakeholders:** Focus on Section 1 (Executive Summary)
2. **Test Managers:** Review Sections 1, 5, 6, 10 (Summary, Stats, Results, Recommendations)
3. **Developers:** Analyze Section 7 (Failed Test Analysis) and Evidence section
4. **DevOps:** Use reports for CI/CD quality gates

## Report Structure Reference

```
reports/
├── enterprise_test_report.html      ← Comprehensive 10-section report
├── stakeholder_executive_summary.html  ← Quick dashboard view
├── pytest_html_report.html          ← Standard pytest-html output
└── allure-results/                  ← Allure report data (if configured)

screenshots/
├── test_filtering_functionality_20240124_143022.png
├── test_pagination_max_records_20240124_143045.png
└── ...
```

## Customization

### Add Custom Sections to Enterprise Report

Edit `utilities/report_generator.py`:

```python
def _build_html(self) -> str:
    """Build complete HTML report"""
    return f"""<!DOCTYPE html>
    ...
    {self._build_executive_summary(stats, quality)}
    {self._build_custom_section()}  # Add your custom section
    {self._build_scope_section()}
    ...
    """

def _build_custom_section(self) -> str:
    """Your custom section"""
    return """
    <div class="section">
        <h2 class="section-title">Custom Section Title</h2>
        <p>Your custom content here</p>
    </div>"""
```

### Modify Quality Assessment Thresholds

Edit `_get_quality_assessment()` in `utilities/report_generator.py`:

```python
def _get_quality_assessment(self, pass_rate: float) -> Dict[str, str]:
    if pass_rate >= 98:  # Stricter threshold
        status = "PASS"
        # ...
```

### Custom CSS Styling

Modify `_get_styles()` in `utilities/report_generator.py`:

```python
def _get_styles(self) -> str:
    return """<style>
    /* Your custom CSS */
    .header { background: linear-gradient(135deg, #YOUR_COLOR 0%, #YOUR_COLOR 100%); }
    </style>"""
```

## Support

For issues or enhancement requests:
1. Check console logs for error messages
2. Review `conftest.py` pytest hooks
3. Verify `utilities/report_generator.py` configuration
4. Contact QA automation team

---

**Last Updated:** January 2024  
**Framework Version:** 1.0  
**Supported Python:** 3.10+  
**Supported Pytest:** 7.4.3+
