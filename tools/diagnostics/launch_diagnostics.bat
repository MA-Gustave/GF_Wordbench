@echo off
setlocal
cd /d "%~dp0\..\.."
where pyw >nul 2>nul
if not errorlevel 1 (
  pyw "%~dp0\00-control_panel.pyw"
  exit /b %errorlevel%
)
py "%~dp0\00-control_panel.pyw"
