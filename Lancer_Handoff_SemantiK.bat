@echo off
setlocal
cd /d "%~dp0"
set "ROOT=%USERPROFILE%\Downloads\Ars_Magna_Defluens"
set "OUTPUT=%ROOT%\semantik_handoff.json"
set "ARCHIVE=%~1"
if not defined ARCHIVE (
 for /f "delims=" %%f in ('dir /b /a-d /o-d "%ROOT%\practical_pilot_runs\defluens-batch-full-*.zip" 2^>nul') do (
  if not defined ARCHIVE set "ARCHIVE=%ROOT%\practical_pilot_runs\%%f"
 )
)
if not defined ARCHIVE (echo No full WordBench ZIP found in Downloads & exit /b 2)
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
py -3 -m gf_wordbench.practical.semantik_handoff --archive "%ARCHIVE%" --output "%OUTPUT%"
if errorlevel 1 exit /b 2
echo DEVELOPMENT handoff only: %OUTPUT%
exit /b 0
