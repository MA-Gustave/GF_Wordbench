@echo off
setlocal
cd /d "%~dp0\..\.."
py "%~dp0\run_safe_suite.py"
set "CODE=%ERRORLEVEL%"
echo.
echo Mini diagnostic suite exit code: %CODE%
pause
exit /b %CODE%
