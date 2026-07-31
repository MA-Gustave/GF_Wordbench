@echo off
setlocal
cd /d "%~dp0\..\.."

where pyw >nul 2>nul
if errorlevel 1 goto console_fallback

pyw "%~dp0\00-control_panel.pyw"
set "CODE=%ERRORLEVEL%"
if "%CODE%"=="0" exit /b 0

echo.
echo GF Wordbench diagnostics failed to start under pyw.exe.
echo Retrying with a visible console to preserve the traceback.
echo.

:console_fallback
py "%~dp0\00-control_panel.pyw"
set "CODE=%ERRORLEVEL%"
if not "%CODE%"=="0" (
  echo.
  echo Diagnostic launcher exit code: %CODE%
  pause
)
exit /b %CODE%