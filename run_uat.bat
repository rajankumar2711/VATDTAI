@echo off
setlocal
rem =====================================================================
rem  Run the suite against the UAT environment (gtpituat.ey.com).
rem  uat_only scenarios (PowerBI Dashboard, Detect & Suggest) run here;
rem  qa_only scenarios are auto-skipped.
rem
rem  Examples:
rem    run_uat.bat                          (whole GIDEI suite in UAT)
rem    run_uat.bat -m Dashboard             (only Dashboard scenarios)
rem    run_uat.bat tests\step_defs\test_dashboard.py
rem =====================================================================
set PROJ=%~dp0
cd /d "%PROJ%"

if "%~1"=="" (
    python -m pytest --env uat -m GIDEI
) else (
    python -m pytest --env uat %*
)

echo.
pause
endlocal
