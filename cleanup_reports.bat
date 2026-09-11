@echo off
setlocal
rem =====================================================================
rem  Report housekeeping
rem   - keeps the newest 5 run folders under reports\runs\
rem   - clears the live reports\allure-results collection
rem  Add  --purge-legacy --downloads  to also remove pre-consolidation
rem  clutter (old allure dirs, top-level traces/videos/logs, stray
rem  screenshots, root-level report html). Demo folders are never touched.
rem
rem  Preview first (safe):
rem     cleanup_reports.bat --dry-run
rem  Apply:
rem     cleanup_reports.bat --yes
rem =====================================================================

set PROJ=%~dp0
python "%PROJ%utilities\cleanup_reports.py" --keep 5 %*

echo.
pause
endlocal
