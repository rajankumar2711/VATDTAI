@echo off
setlocal
rem =====================================================================
rem  Run the suite against the QA environment (default).
rem  qa_only scenarios run here; uat_only scenarios (PowerBI Dashboard,
rem  Detect & Suggest) are auto-skipped.
rem
rem  Examples:
rem    run_qa.bat                           (whole GIDEI suite in QA)
rem    run_qa.bat -m GIDEI_Smoke            (QA smoke suite)
rem    run_qa.bat tests\step_defs\test_reports.py
rem =====================================================================
set PROJ=%~dp0
cd /d "%PROJ%"

if "%~1"=="" (
    python -m pytest --env qa -m GIDEI
) else (
    python -m pytest --env qa %*
)

echo.
pause
endlocal
