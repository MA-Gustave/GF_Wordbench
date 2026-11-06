@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
where py >nul 2>nul
if errorlevel 1 (set "PYTHON=python") else (set "PYTHON=py -3")
echo.
echo ===========================================================
echo ARS MAGNA DEFLUENS - 3 REPARATIONS GF - v0.2.3
echo ===========================================================
%PYTHON% -m gf_wordbench.practical.stabilization023 check
if errorlevel 1 exit /b 1
%PYTHON% -m gf_wordbench.practical.stabilization023 run
if errorlevel 1 (
 echo Certaines sondes ont echoue. Envoie quand meme le ZIP.
 exit /b 1
)
echo.
echo Termine. ZIP dans Downloads\Ars_Magna_Defluens\practical_pilot_runs
exit /b 0
