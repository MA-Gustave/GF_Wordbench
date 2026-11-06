@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
title Ars Magna Defluens - Alignement RGL 14 langues
REM Modes: check / plan / apply / smoke / full / compare
REM All JSON plans and GF run archives are exported under Downloads.
set "MODE=%~1"
if not defined MODE set "MODE=check"
set "RGL=C:\mycode\Grammatical-Framework\gf-rgl"
set "OUT=%USERPROFILE%\Downloads\Ars_Magna_Defluens\alignment14"
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
if not exist "%OUT%" mkdir "%OUT%"
where py >nul 2>nul
if errorlevel 1 (set "PYTHON=python") else (set "PYTHON=py -3")
echo.
echo ============================================================== 
echo  ARS MAGNA DEFLUENS - ALIGNEMENT RGL - 14 LANGUES
 echo ============================================================== 
echo  Mode : %MODE%
echo.
if /i "%MODE%"=="check" (
  %PYTHON% -m gf_wordbench.practical.alignment14 verify --rgl-root "%RGL%" --report "%OUT%\alignment14_check.json"
  if errorlevel 1 goto :error
  goto :success
)
if /i "%MODE%"=="plan" (
  %PYTHON% -m gf_wordbench.practical.alignment14 plan --rgl-root "%RGL%" --report "%OUT%\alignment14_plan.json"
  if errorlevel 1 goto :error
  goto :success
)
if /i "%MODE%"=="apply" (
  %PYTHON% -m gf_wordbench.practical.alignment14 apply --rgl-root "%RGL%" --report "%OUT%\alignment14_apply.json"
  if errorlevel 1 goto :error
  goto :success
)
if /i "%MODE%"=="smoke" (
  %PYTHON% -m gf_wordbench.practical.alignment14 verify --rgl-root "%RGL%" --report "%OUT%\alignment14_preflight.json"
  if errorlevel 1 goto :error
  call "%~dp0Lancer_Campagne_Multilingue.bat" smoke Eng Fre Spa Ger Dut Swe Dan Nor Nno Fin Est Afr Ita Por
  if errorlevel 1 goto :error
  goto :success
)
if /i "%MODE%"=="compare" (
  %PYTHON% -m gf_wordbench.practical.alignment14 compare --rgl-root "%RGL%" --batch-dir "%USERPROFILE%\Downloads\Ars_Magna_Defluens\practical_pilot_runs" --report "%OUT%\alignment14_comparison.json"
  if errorlevel 1 goto :error
  goto :success
)
if /i "%MODE%"=="full" (
  %PYTHON% -m gf_wordbench.practical.alignment14 verify --rgl-root "%RGL%" --report "%OUT%\alignment14_preflight.json"
  if errorlevel 1 goto :error
  call "%~dp0Lancer_Campagne_Multilingue.bat" full Eng Fre Spa Ger Dut Swe Dan Nor Nno Fin Est Afr Ita Por
  if errorlevel 1 goto :error
  goto :success
)
echo Invalid mode. Use check, plan, apply, smoke, full, compare.
goto :error
:success
echo.
echo Finished. Reports: %OUT%
exit /b 0
:error
echo.
echo Error: prior reports and RGL sources were not changed.
exit /b 1
