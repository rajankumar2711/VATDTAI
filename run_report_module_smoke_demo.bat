@echo off
setlocal
rem =====================================================================
rem  Report Module - Smoke Suite demo runner
rem  Runs the Reports smoke cases (@GIDEI_Smoke). The framework now
rem  consolidates EVERY artifact into a single timestamped folder:
rem     reports\runs\Smoke_Suite_GIDEI_<YYYYMMDD_HHMMSS>\
rem  containing report.html, stakeholder_executive_summary.html,
rem  enterprise_test_report.html, allure-report\, allure-single-report.html,
rem  allure-results\, traces\, videos\, logs\, pytest_run.log and index.html.
rem  This script just launches the run and opens the resulting index.html.
rem =====================================================================

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; $proj='%~dp0'.TrimEnd('\'); Set-Location $proj; & python -m pytest tests/step_defs/test_reports.py -m GIDEI_Smoke --html (Join-Path $proj 'reports\report.html') --self-contained-html; $run = Get-ChildItem (Join-Path $proj 'reports\runs') -Directory | Sort-Object LastWriteTime | Select-Object -Last 1; if ($run) { Write-Host ''; Write-Host ('Consolidated run folder: ' + $run.FullName); Get-ChildItem $run.FullName | Format-Table Name,LastWriteTime -AutoSize; $idx = Join-Path $run.FullName 'index.html'; if (Test-Path $idx) { Start-Process $idx } }"

echo.
pause
endlocal
