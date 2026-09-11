"""
Enterprise-Level Test Execution Report Generator
Generates comprehensive HTML reports with executive summary, 
module-wise results, failure analysis, and evidence artifacts.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
from html import escape as html_escape
import platform

logger = logging.getLogger(__name__)


class TestReportGenerator:
    """Generate comprehensive test execution reports"""

    MODULE_DISPLAY_NAMES = {
        "test_tile": "App Tile / Launch",
        "test_user_management": "User Management",
        "test_data_ingestion": "Data Ingestion",
        "test_data_lake_ip": "Data Lake IP",
        "test_invoice_management": "Invoice Management",
        "test_reconciliation": "Reconciliation",
        "test_reports": "Reports",
    }

    def _friendly_module_name(self, module_path: str) -> str:
        """Map a test-file path/nodeid to a business-friendly module name."""
        from pathlib import Path as _Path
        stem = _Path(str(module_path)).stem
        if stem in self.MODULE_DISPLAY_NAMES:
            return self.MODULE_DISPLAY_NAMES[stem]
        if stem.startswith("test_"):
            stem = stem[len("test_"):]
        return stem.replace("_", " ").strip().title() or str(module_path)

    def _relativize(self, url: str) -> str:
        """Reduce an absolute file:// evidence URL to a path relative to the run
        folder (e.g. traces/... or videos/...) so links survive the folder move."""
        if not url:
            return None
        for marker in ("/traces/", "/videos/"):
            idx = url.find(marker)
            if idx != -1:
                return url[idx + 1:]
        return url

    def _humanize_scenario(self, test_name: str) -> str:
        """Turn a pytest node/function name into a readable scenario label."""
        name = str(test_name)
        params = ""
        if "[" in name and name.endswith("]"):
            base, params = name.split("[", 1)
            params = " [" + params
            name = base
        if name.startswith("test_"):
            name = name[len("test_"):]
        return (name.replace("_", " ").strip().capitalize() + params).strip()

    
    def __init__(self, config, test_results: List[Dict], 
                 total_duration: float, environment: str = "QA",
                 related_links: Dict[str, str] = None):
        self.config = config
        self.test_results = test_results
        self.total_duration = total_duration
        self.environment = environment
        self.related_links = related_links or {}
        self.execution_timestamp = datetime.now()
        
    def generate_report(self, output_path: Path) -> str:
        """Generate complete HTML report"""
        html_content = self._build_html()
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write report
        output_path.write_text(html_content, encoding='utf-8')
        logger.info(f"Enterprise test report generated: {output_path}")
        
        return str(output_path)
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate test execution statistics"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["outcome"] == "passed")
        failed = sum(1 for r in self.test_results if r["outcome"] == "failed")
        skipped = sum(1 for r in self.test_results if r["outcome"] == "skipped")
        blocked = 0  # Can be enhanced with custom markers
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "blocked": blocked,
            "pass_rate": pass_rate,
            "avg_duration": self.total_duration / total if total > 0 else 0
        }
    
    def _get_module_statistics(self) -> List[Dict[str, Any]]:
        """Group results by module/feature"""
        module_map = defaultdict(lambda: {
            "passed": 0, "failed": 0, "skipped": 0, 
            "duration": 0.0, "tests": []
        })
        
        for result in self.test_results:
            module = result["module"]
            module_map[module]["tests"].append(result)
            module_map[module][result["outcome"]] += 1
            module_map[module]["duration"] += result["duration"]
        
        # Convert to sorted list
        modules = []
        for module_name, stats in sorted(module_map.items()):
            total_tests = stats["passed"] + stats["failed"] + stats["skipped"]
            pass_rate = (stats["passed"] / total_tests * 100) if total_tests > 0 else 0
            
            modules.append({
                "name": module_name,
                "total": total_tests,
                "passed": stats["passed"],
                "failed": stats["failed"],
                "skipped": stats["skipped"],
                "duration": stats["duration"],
                "pass_rate": pass_rate,
                "tests": stats["tests"]
            })
        
        return modules
    
    def _get_failed_tests(self) -> List[Dict[str, Any]]:
        """Extract failed test details for analysis"""
        return [r for r in self.test_results if r["outcome"] == "failed"]
    
    def _get_quality_assessment(self, pass_rate: float) -> Dict[str, str]:
        """Determine quality status and recommendation"""
        if pass_rate >= 95:
            status = "PASS"
            quality = "EXCELLENT"
            recommendation = "GO"
            confidence = "HIGH"
        elif pass_rate >= 80:
            status = "PARTIAL PASS"
            quality = "GOOD"
            recommendation = "CONDITIONAL GO"
            confidence = "MODERATE-HIGH"
        elif pass_rate >= 70:
            status = "PARTIAL PASS"
            quality = "MODERATE"
            recommendation = "CONDITIONAL GO"
            confidence = "MODERATE"
        else:
            status = "FAIL"
            quality = "POOR"
            recommendation = "NO GO"
            confidence = "LOW"
        
        return {
            "status": status,
            "quality": quality,
            "recommendation": recommendation,
            "confidence": confidence
        }
    
    def _build_html(self) -> str:
        """Build complete HTML report"""
        stats = self._calculate_statistics()
        modules = self._get_module_statistics()
        failed_tests = self._get_failed_tests()
        quality = self._get_quality_assessment(stats["pass_rate"])
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Execution Report - {self.execution_timestamp.strftime('%Y-%m-%d')}</title>
    {self._get_styles()}
</head>
<body>
    {self._build_header(modules)}
    {self._build_executive_summary(stats, quality)}
    {self._build_scope_section(modules)}
    {self._build_environment_section()}
    {self._build_framework_section()}
    {self._build_execution_summary(stats)}
    {self._build_module_results(modules)}
    {self._build_failed_analysis(failed_tests)}
    {self._build_evidence_section()}
    {self._build_logging_section()}
    {self._build_recommendations(quality, stats)}
    {self._build_footer()}
</body>
</html>"""
    
    def _get_styles(self) -> str:
        """CSS styles for the report"""
        return """<style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; 
            line-height: 1.6; 
            color: #1e1e1e; 
            background: #f5f7fa;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        /* Header */
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 30px 40px; 
            border-radius: 12px; 
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 32px; margin-bottom: 8px; }
        .header-meta { font-size: 14px; opacity: 0.95; }
        .header-links { font-size: 13px; margin-top: 10px; opacity: 0.95; }
        .header-links a { color: #fff; text-decoration: underline; }
        
        /* Section */
        .section { 
            background: white; 
            padding: 30px; 
            margin-bottom: 20px; 
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        }
        .section-title { 
            font-size: 24px; 
            font-weight: 700; 
            margin-bottom: 20px; 
            padding-bottom: 12px;
            border-bottom: 3px solid #667eea;
            color: #2d3748;
        }
        .section-subtitle { 
            font-size: 18px; 
            font-weight: 600; 
            margin-top: 24px;
            margin-bottom: 12px;
            color: #4a5568;
        }
        
        /* Stats Cards */
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 16px; 
            margin-bottom: 24px;
        }
        .stat-card { 
            background: linear-gradient(135deg, #f6f8fb 0%, #ffffff 100%);
            padding: 20px; 
            border-radius: 10px; 
            border: 1px solid #e2e8f0;
            transition: transform 0.2s;
        }
        .stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .stat-label { 
            font-size: 12px; 
            color: #718096; 
            text-transform: uppercase; 
            letter-spacing: 0.5px;
            font-weight: 600;
        }
        .stat-value { 
            font-size: 32px; 
            font-weight: 700; 
            margin-top: 8px;
        }
        .stat-value.pass { color: #48bb78; }
        .stat-value.fail { color: #f56565; }
        .stat-value.skip { color: #ed8936; }
        .stat-value.neutral { color: #4299e1; }
        
        /* Quality Badge */
        .quality-badge { 
            display: inline-block; 
            padding: 8px 16px; 
            border-radius: 20px; 
            font-weight: 600;
            font-size: 14px;
            margin: 8px 4px;
        }
        .badge-pass { background: #c6f6d5; color: #22543d; }
        .badge-partial { background: #feebc8; color: #7c2d12; }
        .badge-fail { background: #fed7d7; color: #742a2a; }
        .badge-go { background: #c6f6d5; color: #22543d; }
        .badge-nogo { background: #fed7d7; color: #742a2a; }
        .badge-conditional { background: #feebc8; color: #7c2d12; }
        
        /* Tables */
        table { width: 100%; border-collapse: collapse; margin: 16px 0; }
        th, td { 
            padding: 12px; 
            text-align: left; 
            border-bottom: 1px solid #e2e8f0;
            font-size: 14px;
        }
        th { 
            background: #f7fafc; 
            font-weight: 600; 
            color: #2d3748;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
        }
        tr:hover { background: #f7fafc; }
        
        /* Status Badges */
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        .status-passed { background: #c6f6d5; color: #22543d; }
        .status-failed { background: #fed7d7; color: #742a2a; }
        .status-skipped { background: #feebc8; color: #7c2d12; }
        
        /* Links */
        a { color: #667eea; text-decoration: none; font-weight: 500; }
        a:hover { text-decoration: underline; }
        
        /* Info Boxes */
        .info-box { 
            background: #ebf8ff; 
            border-left: 4px solid #4299e1;
            padding: 16px; 
            margin: 16px 0;
            border-radius: 6px;
        }
        .warning-box { 
            background: #fffaf0; 
            border-left: 4px solid #ed8936;
            padding: 16px; 
            margin: 16px 0;
            border-radius: 6px;
        }
        .success-box { 
            background: #f0fff4; 
            border-left: 4px solid #48bb78;
            padding: 16px; 
            margin: 16px 0;
            border-radius: 6px;
        }
        .error-box { 
            background: #fff5f5; 
            border-left: 4px solid #f56565;
            padding: 16px; 
            margin: 16px 0;
            border-radius: 6px;
        }
        
        /* Footer */
        .footer { 
            text-align: center; 
            padding: 30px; 
            color: #718096;
            font-size: 14px;
        }
        
        /* Code blocks */
        pre { 
            background: #2d3748; 
            color: #e2e8f0; 
            padding: 16px; 
            border-radius: 8px;
            overflow-x: auto;
            font-size: 13px;
            line-height: 1.5;
        }
        code { 
            background: #edf2f7; 
            padding: 2px 6px; 
            border-radius: 4px;
            font-size: 13px;
            color: #d53f8c;
        }
        
        /* Progress Bar */
        .progress-bar {
            width: 100%;
            height: 30px;
            background: #e2e8f0;
            border-radius: 15px;
            overflow: hidden;
            margin: 12px 0;
            position: relative;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #48bb78 0%, #38a169 100%);
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 14px;
        }
        
        /* Lists */
        ul { margin-left: 20px; }
        li { margin: 8px 0; }
        
        @media print {
            .section { page-break-inside: avoid; }
            .no-print { display: none; }
        }
    </style>"""
    
    def _build_header(self, modules: List[Dict[str, Any]] = None) -> str:
        """Build report header"""
        module_names = [self._friendly_module_name(m["name"]) for m in (modules or [])]
        if not module_names:
            module_label = "Test Suite"
        elif len(module_names) == 1:
            module_label = f"{module_names[0]} Module"
        else:
            module_label = ", ".join(module_names) + " Modules"
        link_specs = [
            ("Detailed HTML", self.related_links.get("detailed")),
            ("Allure", self.related_links.get("allure")),
            ("Allure (single-file)", self.related_links.get("allure_single")),
            ("Run log", self.related_links.get("run_log")),
        ]
        link_bits = [
            f"<a href='{html_escape(url)}'>{html_escape(label)}</a>"
            for label, url in link_specs if url
        ]
        links_line = (
            f"""
            <div class="header-links">Related artifacts: {' | '.join(link_bits)}</div>"""
            if link_bits else ""
        )
        return f"""
    <div class="header">
        <div class="container">
            <h1>🎯 AUTOMATION TEST EXECUTION REPORT</h1>
            <div class="header-meta">
                <strong>Global Insights And Data Enrichment For e-Invoicing - {html_escape(module_label)}</strong> | 
                Environment: {self.environment} | 
                Execution Date: {self.execution_timestamp.strftime('%B %d, %Y %H:%M:%S')} | 
                Framework: Playwright + Python + Pytest-BDD
            </div>{links_line}
        </div>
    </div>
    <div class="container">"""
    
    def _build_executive_summary(self, stats: Dict, quality: Dict) -> str:
        """Build executive summary section"""
        return f"""
    <div class="section">
        <h2 class="section-title">1. EXECUTIVE SUMMARY</h2>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Overall Status</div>
                <div class="stat-value neutral">{quality['status']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Pass Rate</div>
                <div class="stat-value pass">{stats['pass_rate']:.1f}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Quality Level</div>
                <div class="stat-value neutral">{quality['quality']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Confidence</div>
                <div class="stat-value neutral">{quality['confidence']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Recommendation</div>
                <div class="stat-value {'pass' if quality['recommendation'] == 'GO' else 'fail'}">{quality['recommendation']}</div>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: {stats['pass_rate']}%">
                {stats['passed']}/{stats['total']} Tests Passed
            </div>
        </div>
        
        <h3 class="section-subtitle">Quality Assessment</h3>
        {self._get_quality_message(quality, stats)}
        
        <h3 class="section-subtitle">Key Highlights</h3>
        {self._get_highlights(stats)}
    </div>"""
    
    def _get_quality_message(self, quality: Dict, stats: Dict) -> str:
        """Get quality assessment message box"""
        if quality['recommendation'] == 'GO':
            box_class = 'success-box'
        elif quality['recommendation'] == 'CONDITIONAL GO':
            box_class = 'warning-box'
        else:
            box_class = 'error-box'
        
        return f"""<div class="{box_class}">
            <strong>Quality Status: {quality['status']}</strong><br>
            The test execution achieved <strong>{stats['pass_rate']:.1f}% pass rate</strong> 
            ({stats['passed']} passed, {stats['failed']} failed, {stats['skipped']} skipped out of {stats['total']} total tests).
            <br><br>
            <strong>Release Recommendation: {quality['recommendation']}</strong>
            {' - Proceed with release for validated scenarios.' if quality['recommendation'] != 'NO GO' else ' - Address critical failures before release.'}
        </div>"""
    
    def _get_highlights(self, stats: Dict) -> str:
        """Get key highlights"""
        highlights = []
        
        if stats['passed'] > 0:
            highlights.append(f"✅ <strong>{stats['passed']} scenarios</strong> validated successfully")
        
        if stats['failed'] > 0:
            highlights.append(f"❌ <strong>{stats['failed']} scenarios</strong> require attention")
        
        if stats['skipped'] > 0:
            highlights.append(f"⚠️ <strong>{stats['skipped']} scenarios</strong> were skipped")
        
        highlights.append(f"⏱️ Total execution time: <strong>{self.total_duration:.1f} seconds</strong>")
        highlights.append(f"📊 Average test duration: <strong>{stats['avg_duration']:.2f} seconds</strong>")
        
        return "<ul>" + "".join(f"<li>{h}</li>" for h in highlights) + "</ul>"
    
    def _build_scope_section(self, modules: List[Dict[str, Any]] = None) -> str:
        """Build scope of testing section (driven by actual execution results)."""
        modules = modules or []

        # Modules actually exercised in this run
        if modules:
            module_names = [self._friendly_module_name(m["name"]) for m in modules]
            module_label = "Modules Under Test" if len(module_names) > 1 else "Module Under Test"
            modules_value = html_escape(", ".join(module_names))
        else:
            module_label = "Modules Under Test"
            modules_value = "No modules executed"

        # Per-module coverage with executed scenario names
        coverage_blocks = []
        if modules:
            for m in modules:
                friendly = html_escape(self._friendly_module_name(m["name"]))
                header = (
                    f"<p style=\"margin-top:12px;\"><strong>{friendly}</strong> &mdash; "
                    f"{m['total']} scenario(s) "
                    f"({m['passed']} passed, {m['failed']} failed, {m['skipped']} skipped)</p>"
                )
                items = []
                for t in m.get("tests", []):
                    outcome = t.get("outcome", "")
                    icon = "✅" if outcome == "passed" else ("❌" if outcome == "failed" else "⏭️")
                    label = html_escape(self._humanize_scenario(t.get("test_name", t.get("nodeid", ""))))
                    items.append(f"<li>{icon} {label}</li>")
                items_html = "".join(items) if items else "<li>No scenarios recorded</li>"
                coverage_blocks.append(f"{header}\n        <ul>{items_html}</ul>")
            coverage_html = "\n        ".join(coverage_blocks)
        else:
            coverage_html = "<p>No test coverage recorded for this run.</p>"

        # Configured browser for the cross-browser exclusion note
        try:
            from utilities.read_properties import Read_Configurations
            browser = Read_Configurations.get_value("browser") or "the configured browser"
        except Exception:
            browser = "the configured browser"

        return f"""
    <div class="section">
        <h2 class="section-title">2. SCOPE OF TESTING</h2>
        
        <h3 class="section-subtitle">Application Under Test</h3>
        <ul>
            <li><strong>Application:</strong> Global Insights And Data Enrichment For e-Invoicing</li>
            <li><strong>{module_label}:</strong> {modules_value}</li>
            <li><strong>Environment:</strong> {self.environment}</li>
            <li><strong>Test Type:</strong> Functional, Regression, UI Automation</li>
        </ul>
        
        <h3 class="section-subtitle">Test Coverage</h3>
        {coverage_html}
        
        <h3 class="section-subtitle">Exclusions</h3>
        <ul>
            <li>❌ API-level testing (separate test suite)</li>
            <li>❌ Performance and load testing</li>
            <li>❌ Security penetration testing</li>
            <li>❌ Cross-browser compatibility ({html_escape(browser)} only in this run)</li>
            <li>❌ Mobile responsive design validation</li>
        </ul>
    </div>"""
    
    def _build_environment_section(self) -> str:
        """Build environment details section"""
        try:
            from utilities.read_properties import Read_Configurations
            base_url = Read_Configurations.get_value("VAT_DTAI_URL")
            browser = Read_Configurations.get_value("browser")
        except:
            base_url = "Configuration not available"
            browser = "Chromium"
        
        return f"""
    <div class="section">
        <h2 class="section-title">3. TEST ENVIRONMENT DETAILS</h2>
        
        <table>
            <tr>
                <th style="width: 30%">Attribute</th>
                <th>Details</th>
            </tr>
            <tr>
                <td><strong>Environment</strong></td>
                <td>{self.environment}</td>
            </tr>
            <tr>
                <td><strong>Application URL</strong></td>
                <td>{html_escape(base_url)}</td>
            </tr>
            <tr>
                <td><strong>Browser</strong></td>
                <td>{html_escape(browser)}</td>
            </tr>
            <tr>
                <td><strong>OS</strong></td>
                <td>{platform.system()} {platform.release()}</td>
            </tr>
            <tr>
                <td><strong>Python Version</strong></td>
                <td>{platform.python_version()}</td>
            </tr>
            <tr>
                <td><strong>Execution Date/Time</strong></td>
                <td>{self.execution_timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
            </tr>
        </table>
    </div>"""
    
    def _build_framework_section(self) -> str:
        """Build framework overview section"""
        return """
    <div class="section">
        <h2 class="section-title">4. FRAMEWORK & TOOLING OVERVIEW</h2>
        
        <h3 class="section-subtitle">Framework Architecture</h3>
        <div class="info-box">
            <strong>Hybrid BDD Framework with Page Object Model</strong><br>
            Playwright (Browser Automation) → Python 3.10+ → Pytest + Pytest-BDD → 
            Gherkin Feature Files → Step Definitions → Page Objects → HTML Reports
        </div>
        
        <h3 class="section-subtitle">Key Technologies</h3>
        <ul>
            <li><strong>Automation Tool:</strong> Playwright (Cross-browser automation)</li>
            <li><strong>Language:</strong> Python 3.10+</li>
            <li><strong>Test Framework:</strong> Pytest 7.4.3 + Pytest-BDD 7.1.2</li>
            <li><strong>BDD:</strong> Gherkin syntax for business-readable scenarios</li>
            <li><strong>Design Pattern:</strong> Page Object Model (POM)</li>
            <li><strong>Reporting:</strong> Custom HTML + Pytest HTML + Allure (optional)</li>
            <li><strong>Logging:</strong> Python logging module (INFO level)</li>
        </ul>
        
        <h3 class="section-subtitle">Locator Strategy</h3>
        <ul>
            <li>🎯 <strong>Role-based selectors</strong> (ARIA roles for accessibility)</li>
            <li>🎯 <strong>Data attributes</strong> (data-id for stable locators)</li>
            <li>🎯 <strong>Fallback locators</strong> (Primary + alternative patterns)</li>
            <li>🎯 <strong>Zero XPath</strong> (CSS and role-based only)</li>
        </ul>
    </div>"""
    
    def _build_execution_summary(self, stats: Dict) -> str:
        """Build test execution summary section"""
        return f"""
    <div class="section">
        <h2 class="section-title">5. TEST EXECUTION SUMMARY</h2>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Tests</div>
                <div class="stat-value neutral">{stats['total']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Passed</div>
                <div class="stat-value pass">{stats['passed']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Failed</div>
                <div class="stat-value fail">{stats['failed']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Skipped</div>
                <div class="stat-value skip">{stats['skipped']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Duration</div>
                <div class="stat-value neutral">{self.total_duration:.1f}s</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Pass Rate</div>
                <div class="stat-value pass">{stats['pass_rate']:.1f}%</div>
            </div>
        </div>
        
        <h3 class="section-subtitle">Execution Timeline</h3>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Execution Start Time</td>
                <td>{self.execution_timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
            </tr>
            <tr>
                <td>Total Duration</td>
                <td>{self.total_duration:.2f} seconds ({self.total_duration/60:.1f} minutes)</td>
            </tr>
            <tr>
                <td>Average Test Duration</td>
                <td>{stats['avg_duration']:.2f} seconds</td>
            </tr>
        </table>
    </div>"""
    
    def _build_module_results(self, modules: List[Dict]) -> str:
        """Build module-wise results section"""
        module_rows = ""
        for module in modules:
            status_class = 'pass' if module['failed'] == 0 else 'fail'
            module_rows += f"""
            <tr>
                <td>{html_escape(module['name'])}</td>
                <td>{module['total']}</td>
                <td class="pass">{module['passed']}</td>
                <td class="fail">{module['failed']}</td>
                <td class="skip">{module['skipped']}</td>
                <td>{module['duration']:.2f}s</td>
                <td><span class="status-badge status-{'passed' if module['failed'] == 0 else 'failed'}">{module['pass_rate']:.1f}%</span></td>
            </tr>"""
        
        detail_blocks = ""
        for module in modules:
            friendly = html_escape(self._friendly_module_name(module["name"]))
            test_rows = ""
            for test in module["tests"]:
                scenario = html_escape(
                    self._humanize_scenario(test.get("test_name") or test.get("nodeid", ""))
                )
                outcome = str(test.get("outcome", "")).lower()
                badge = outcome if outcome in ("passed", "failed", "skipped") else "skipped"
                duration = test.get("duration", 0.0)
                trace_rel = self._relativize(test.get("trace_url"))
                video_rel = self._relativize(test.get("video_url"))
                trace = (
                    f"<a href='{html_escape(trace_rel)}' target='_blank'>Trace</a>"
                    if trace_rel else "-"
                )
                video = (
                    f"<a href='{html_escape(video_rel)}' target='_blank'>Video</a>"
                    if video_rel else "-"
                )
                test_rows += f"""
                <tr>
                    <td>{scenario}</td>
                    <td><span class="status-badge status-{badge}">{outcome.title()}</span></td>
                    <td>{duration:.2f}s</td>
                    <td>{trace}</td>
                    <td>{video}</td>
                </tr>"""
            detail_blocks += f"""
        <h3 class="section-subtitle">{friendly} - Scenario Details</h3>
        <table>
            <thead>
                <tr>
                    <th>Scenario</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Trace</th>
                    <th>Video</th>
                </tr>
            </thead>
            <tbody>{test_rows}
            </tbody>
        </table>"""

        return f"""
    <div class="section">
        <h2 class="section-title">6. MODULE-WISE TEST RESULTS</h2>
        
        <table>
            <thead>
                <tr>
                    <th>Module/Feature</th>
                    <th>Total</th>
                    <th>Passed</th>
                    <th>Failed</th>
                    <th>Skipped</th>
                    <th>Duration</th>
                    <th>Pass Rate</th>
                </tr>
            </thead>
            <tbody>
                {module_rows}
            </tbody>
        </table>
        {detail_blocks}
    </div>"""
    
    def _build_failed_analysis(self, failed_tests: List[Dict]) -> str:
        """Build failed test analysis section"""
        if not failed_tests:
            return f"""
    <div class="section">
        <h2 class="section-title">7. FAILED TEST CASE ANALYSIS</h2>
        <div class="success-box">
            <strong>🎉 Excellent!</strong> No test failures detected. All scenarios executed successfully.
        </div>
    </div>"""
        
        failure_rows = ""
        for idx, test in enumerate(failed_tests, 1):
            nodeid = test.get('nodeid', 'Unknown')
            test_name = nodeid.split("::")[-1] if "::" in nodeid else nodeid
            duration = test.get('duration', 0)
            error_msg = test.get('error_message', 'No error message available')
            
            failure_rows += f"""
            <div class="error-box" style="margin-bottom: 20px;">
                <h4 style="margin-bottom: 10px;">❌ Failure #{idx}: {html_escape(test_name)}</h4>
                <table style="margin-bottom: 10px;">
                    <tr>
                        <td style="width: 20%; font-weight: 600;">Test Case:</td>
                        <td>{html_escape(nodeid)}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: 600;">Duration:</td>
                        <td>{duration:.2f} seconds</td>
                    </tr>
                    <tr>
                        <td style="font-weight: 600;">Module:</td>
                        <td>{html_escape(test.get('module', 'Unknown'))}</td>
                    </tr>
                </table>
                <div style="margin-top: 12px;">
                    <strong>Error Message:</strong>
                    <pre style="margin-top: 8px; white-space: pre-wrap;">{html_escape(error_msg[:500])}</pre>
                </div>
                {self._get_trace_links(test)}
            </div>"""
        
        return f"""
    <div class="section">
        <h2 class="section-title">7. FAILED TEST CASE ANALYSIS</h2>
        
        <div class="warning-box">
            <strong>⚠️ {len(failed_tests)} Test(s) Failed</strong><br>
            Detailed analysis and error messages are provided below. Review failure evidence (traces, screenshots, logs) for root cause analysis.
        </div>
        
        {failure_rows}
    </div>"""
    
    def _get_trace_links(self, test: Dict) -> str:
        """Get trace and evidence links"""
        links = []
        
        if test.get('trace_url'):
            links.append(f"<a href='{test['trace_url']}' target='_blank'>📊 View Trace</a>")
        
        if test.get('video_url'):
            links.append(f"<a href='{test['video_url']}' target='_blank'>🎥 View Video</a>")
        
        if test.get('screenshot_url'):
            links.append(f"<a href='{test['screenshot_url']}' target='_blank'>📸 View Screenshot</a>")
        
        if links:
            return f"<div style='margin-top: 12px;'><strong>Evidence:</strong> {' | '.join(links)}</div>"
        
        return ""
    
    def _build_evidence_section(self) -> str:
        """Build evidence & artifacts section"""
        return """
    <div class="section">
        <h2 class="section-title">8. EVIDENCE & ARTIFACTS</h2>
        
        <h3 class="section-subtitle">Generated Artifacts</h3>
        <table>
            <tr>
                <th style="width: 30%">Artifact Type</th>
                <th>Location</th>
            </tr>
            <tr>
                <td>📊 <strong>HTML Test Report</strong></td>
                <td><code>reports/pytest_html_report.html</code></td>
            </tr>
            <tr>
                <td>📈 <strong>Executive Summary</strong></td>
                <td><code>reports/stakeholder_executive_summary.html</code></td>
            </tr>
            <tr>
                <td>📋 <strong>Enterprise Report</strong></td>
                <td><code>reports/enterprise_test_report.html</code> (This file)</td>
            </tr>
            <tr>
                <td>📸 <strong>Screenshots</strong></td>
                <td><code>screenshots/</code> (Captured on failure)</td>
            </tr>
            <tr>
                <td>📜 <strong>Console Logs</strong></td>
                <td>Embedded in HTML reports</td>
            </tr>
            <tr>
                <td>🗄️ <strong>Historical Data</strong></td>
                <td><code>archive/output_&lt;timestamp&gt;.json</code></td>
            </tr>
        </table>
        
        <h3 class="section-subtitle">Evidence Capture Strategy</h3>
        <ul>
            <li><strong>Screenshots:</strong> Automatically captured on test failure</li>
            <li><strong>Playwright Traces:</strong> Full execution traces with timeline and network</li>
            <li><strong>Console Logs:</strong> Python logging at INFO level, embedded in reports</li>
            <li><strong>Video Recording:</strong> Available for headed mode (disabled by default for performance)</li>
        </ul>
    </div>"""
    
    def _build_logging_section(self) -> str:
        """Build logging & debugging section"""
        return """
    <div class="section">
        <h2 class="section-title">9. LOGGING & DEBUGGING DETAILS</h2>
        
        <h3 class="section-subtitle">Logging Configuration</h3>
        <ul>
            <li><strong>Log Level:</strong> INFO (standard execution)</li>
            <li><strong>Format:</strong> <code>%(levelname)s - %(name)s - %(message)s</code></li>
            <li><strong>Integration:</strong> Pytest captures logs automatically in HTML reports</li>
            <li><strong>Location:</strong> Embedded in test reports + console output</li>
        </ul>
        
        <h3 class="section-subtitle">Log Levels Used</h3>
        <ul>
            <li>✅ <strong>INFO:</strong> Standard execution flow, action confirmations</li>
            <li>⚠️ <strong>WARNING:</strong> Fallback locator usage, non-critical issues</li>
            <li>❌ <strong>ERROR:</strong> Critical failures, exceptions</li>
            <li>🔍 <strong>DEBUG:</strong> Detailed troubleshooting (enable when needed)</li>
        </ul>
        
        <div class="info-box">
            <strong>💡 Debugging Tip:</strong> Each log message includes contextual information 
            ([WHEN], [THEN], [GIVEN]) and module names for quick issue identification. 
            Timestamps enable performance analysis and timeout debugging.
        </div>
    </div>"""
    
    def _build_recommendations(self, quality: Dict, stats: Dict) -> str:
        """Build recommendations section"""
        recommendations = []
        
        if stats['failed'] > 0:
            recommendations.append("🔴 <strong>High Priority:</strong> Address all failed test scenarios before release")
            recommendations.append("🔍 Review failure evidence (screenshots, traces, logs) for root cause analysis")
            recommendations.append("🐛 Create defect tickets for application issues identified")
        
        if stats['skipped'] > 0:
            recommendations.append("⚠️ <strong>Medium Priority:</strong> Investigate and re-enable skipped tests")
        
        if stats['pass_rate'] < 95:
            recommendations.append("📊 <strong>Coverage:</strong> Add tests for untested scenarios to improve confidence")
        
        recommendations.append("🚀 <strong>CI/CD:</strong> Integrate test execution into continuous deployment pipeline")
        recommendations.append("🔄 <strong>Automation:</strong> Implement test data setup fixtures for better test isolation")
        recommendations.append("⚡ <strong>Performance:</strong> Replace hardcoded waits with smart waits for faster execution")
        
        recs_html = "<ul>" + "".join(f"<li>{r}</li>" for r in recommendations) + "</ul>"
        
        return f"""
    <div class="section">
        <h2 class="section-title">10. RECOMMENDATIONS & NEXT STEPS</h2>
        
        <h3 class="section-subtitle">Immediate Actions</h3>
        {recs_html}
        
        <h3 class="section-subtitle">Release Decision</h3>
        {self._get_quality_message(quality, stats)}
    </div>"""
    
    def _build_footer(self) -> str:
        """Build report footer"""
        return f"""
    <div class="footer">
        <p><strong>Test Automation Framework</strong> | Playwright + Python + Pytest-BDD</p>
        <p>Report Generated: {self.execution_timestamp.strftime('%Y-%m-%d %H:%M:%S')} | 
        Confidential - For Internal Use Only</p>
    </div>
</div>
</body>
</html>"""
